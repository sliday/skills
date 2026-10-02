(() => {
  'use strict';

  const statuses = [
    { id: 'planned', label: 'Planned', empty: 'No tasks planned here.' },
    { id: 'building', label: 'Building', empty: 'No tasks in progress here.' },
    { id: 'ready', label: 'Ready to try', empty: 'Your team will share tasks to try here.' },
    { id: 'done', label: 'Done', empty: 'Completed tasks will appear here.' }
  ];
  const $ = id => document.getElementById(id);
  const state = { board: null, tasks: new Map(), children: new Map(), needs: new Map(), parent: null, detail: null, filter: false, drafts: new Map(), saves: new Map(), loading: false, failures: 0, paused: false, timer: null, detailSignature: '' };
  let csrf = document.querySelector('meta[name="csrf-token"]').content;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function announce(message) { $('announcement').textContent = message; }
  function taskNeedsAnswer(task) { return Boolean(task.feedback && !task.feedback.answer); }
  function draftKey(task) { return JSON.stringify([task.id, task.feedback.question, task.feedback.choices || [], task.feedback.why]); }
  function getDraft(task) {
    const key = draftKey(task);
    if (!state.drafts.has(key)) state.drafts.set(key, { choice_id: null, comment: '' });
    return state.drafts.get(key);
  }

  function indexBoard(board) {
    if (!board || board.schema_version !== 1 || !board.project || !Array.isArray(board.tasks)) throw new Error('Your team’s progress file has an unsupported format. Your last view stays here.');
    const tasks = new Map();
    const children = new Map([[null, []]]);
    const needs = new Map();
    for (const task of board.tasks) {
      if (!task || typeof task.id !== 'string' || tasks.has(task.id) || typeof task.title !== 'string' || !statuses.some(status => status.id === task.status)) throw new Error('A task has missing or conflicting details. Ask your team to check the progress file.');
      tasks.set(task.id, task);
      children.set(task.id, []);
      needs.set(task.id, 0);
    }
    for (const task of board.tasks) {
      const parent = task.parent_id ?? null;
      if (!children.has(parent)) throw new Error('A task points to a parent that no longer exists. Your last view stays here.');
      children.get(parent).push(task);
      const seen = new Set([task.id]);
      let ancestor = parent;
      while (ancestor !== null) {
        if (seen.has(ancestor)) throw new Error('Two tasks form a circular path. Ask your team to check the progress file.');
        seen.add(ancestor);
        ancestor = tasks.get(ancestor).parent_id ?? null;
      }
      if (taskNeedsAnswer(task)) for (const id of seen) needs.set(id, needs.get(id) + 1);
    }
    return { tasks, children, needs };
  }

  function pathTo(id) {
    const path = [];
    while (id !== null && state.tasks.has(id)) {
      const task = state.tasks.get(id);
      path.unshift(task);
      id = task.parent_id ?? null;
    }
    return path;
  }

  function readRoute() {
    try {
      const id = location.hash.startsWith('#task=') ? decodeURIComponent(location.hash.slice(6)) : null;
      state.parent = state.tasks.has(id) ? id : null;
      state.detail = state.parent;
      state.filter = location.hash === '#needs-you';
    } catch (_) { state.parent = null; state.detail = null; state.filter = false; }
  }

  function navigate(id, filter = false) {
    state.parent = id;
    state.detail = id;
    state.filter = filter;
    const hash = filter ? '#needs-you' : id === null ? '' : '#task=' + encodeURIComponent(id);
    if (location.hash !== hash) history.pushState(null, '', location.pathname + location.search + hash);
    render();
    (id === null || filter ? $('board-heading') : $('detail-title')).focus();
  }

  function formatTime(value) {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.valueOf())) return '';
    return new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(date);
  }

  function renderHeader() {
    const project = state.board.project;
    $('project-name').textContent = project.name || 'Your prototype';
    $('project-summary').textContent = project.summary || 'Follow the work and share decisions with your team.';
    document.title = (project.name || 'Your prototype') + ' · Progress';
    $('demo-notice').hidden = !project.demo;
    const link = $('prototype-link');
    let url = null;
    try {
      if (project.prototype_url) {
        const candidate = new URL(project.prototype_url, location.href);
        if (['http:', 'https:'].includes(candidate.protocol)) url = candidate.href;
      }
    } catch (_) { /* Keep the link hidden when its address is invalid. */ }
    link.hidden = !url;
    if (url) link.href = url;
    else link.removeAttribute('href');
    $('prototype-pending').hidden = Boolean(url);
    const updated = $('last-updated');
    updated.textContent = state.board.updated_at ? 'Project updated ' + formatTime(state.board.updated_at) : 'No team updates yet';
    if (state.board.updated_at) { updated.dateTime = state.board.updated_at; updated.title = new Date(state.board.updated_at).toLocaleString(); }
    else { updated.removeAttribute('datetime'); updated.removeAttribute('title'); }
  }

  function renderBreadcrumbs() {
    const list = element('ol');
    const items = [{ id: null, title: 'All work' }, ...pathTo(state.parent)];
    if (state.filter) items.push({ id: '__needs', title: 'Needs you' });
    items.forEach((task, index) => {
      const item = element('li');
      if (index) item.append(element('span', 'breadcrumb-separator', '/'));
      if (index === items.length - 1) {
        const current = element('span', 'breadcrumb-current', task.title);
        current.setAttribute('aria-current', 'page');
        item.append(current);
      } else {
        const button = element('button', 'breadcrumb-button', task.title);
        button.type = 'button';
        button.dataset.breadcrumbId = task.id || '';
        button.addEventListener('click', () => navigate(task.id));
        item.append(button);
      }
      list.append(item);
    });
    $('breadcrumbs').replaceChildren(list);
  }

  function renderCard(task) {
    const card = element('button', 'db-card task-card' + (taskNeedsAnswer(task) ? ' needs-answer' : ''));
    card.type = 'button';
    card.dataset.taskId = task.id;
    card.setAttribute('aria-label', task.title + '. Open task details and work inside.' + (state.needs.get(task.id) ? ' ' + state.needs.get(task.id) + ' answers needed.' : ''));
    if (state.filter) {
      const ancestors = pathTo(task.id).slice(0, -1);
      card.append(element('span', 'card-route', ancestors.length ? 'All work / ' + ancestors.map(parent => parent.title).join(' / ') : 'All work'));
    }
    const count = state.needs.get(task.id);
    if (count) {
      const label = taskNeedsAnswer(task) && count === 1 ? 'Needs your answer' : count + (count === 1 ? ' answer needed inside' : ' answers needed' + (taskNeedsAnswer(task) ? '' : ' inside'));
      const tag = element('span', 'feedback-tag');
      tag.append(element('span', 'tag-symbol', '!'), document.createTextNode(label));
      card.append(tag);
    } else if (task.feedback && task.feedback.answer) card.append(element('span', 'feedback-tag waiting', 'Waiting for team'));
    card.append(element('span', 'card-title', task.title));
    if (task.description) card.append(element('span', 'card-description', task.description));
    const footer = element('span', 'card-footer');
    const childCount = state.children.get(task.id).length;
    footer.append(element('span', '', childCount ? childCount + (childCount === 1 ? ' task inside' : ' tasks inside') : 'View details'), element('span', 'arrow', '↗'));
    card.append(footer);
    card.addEventListener('click', () => navigate(task.id));
    return card;
  }

  function renderBoard() {
    const allNeeds = state.board.tasks.filter(taskNeedsAnswer);
    const visibleTasks = state.filter ? allNeeds : state.children.get(state.parent) || [];
    const parent = state.tasks.get(state.parent);
    $('board-heading').textContent = state.filter ? 'Needs you' : parent ? 'Inside ' + parent.title : 'All work';
    $('board-description').textContent = state.filter ? 'Questions from across your project. Open one to share your answer.' : parent ? 'The smaller tasks that make this part of your prototype work.' : 'Open a task to see its details and the work inside.';
    $('all-work-filter').setAttribute('aria-pressed', String(!state.filter));
    $('needs-you-filter').setAttribute('aria-pressed', String(state.filter));
    $('needs-you-count').textContent = allNeeds.length;
    $('needs-you-count').classList.toggle('zero', allNeeds.length === 0);
    $('needs-you-filter').setAttribute('aria-label', 'Needs you, ' + allNeeds.length + (allNeeds.length === 1 ? ' unanswered question across the project' : ' unanswered questions across the project'));
    $('show-details').hidden = !parent || Boolean(state.detail);
    const notice = $('board-notice');
    notice.hidden = visibleTasks.length > 0;
    notice.replaceChildren();
    if (!visibleTasks.length) {
      const title = state.filter ? 'You’re up to date.' : parent ? 'The team hasn’t split this task into smaller steps.' : 'Your project starts here.';
      const copy = state.filter ? 'The team has no unanswered questions for you. Check All work to follow development.' : parent ? 'You can read the task details and share an answer when your team asks for one.' : 'The team hasn’t added development tasks yet. They’ll appear here as you agree on the first working part of your prototype.';
      notice.append(element('strong', '', title), element('p', '', copy));
    }
    const columns = statuses.map(status => {
      const tasks = visibleTasks.filter(task => task.status === status.id);
      const column = element('section', 'task-column column-' + status.id);
      column.id = 'column-' + status.id;
      column.setAttribute('aria-labelledby', 'heading-' + status.id);
      const header = element('div', 'column-header');
      const dot = element('span', 'column-dot');
      dot.setAttribute('aria-hidden', 'true');
      const heading = element('h3', '', status.label);
      heading.id = 'heading-' + status.id;
      header.append(dot, heading, element('span', 'column-count', tasks.length));
      const cards = element('div', 'column-cards');
      if (tasks.length) tasks.forEach(task => cards.append(renderCard(task)));
      else cards.append(element('p', 'column-empty', state.filter ? 'No questions in this stage.' : status.empty));
      column.append(header, cards);
      return column;
    });
    $('task-board').replaceChildren(...columns);
  }

  function answerLabel(feedback) {
    return (feedback.choices || []).find(choice => choice.id === feedback.answer.choice_id)?.label || feedback.answer.choice_id || '';
  }

  function renderEarlierDrafts(task, currentKey = null) {
    return [...state.drafts.entries()].filter(([key, value]) => key !== currentKey && JSON.parse(key)[0] === task.id && (value.comment || value.choice_id)).map(([key, value]) => {
      const oldQuestion = JSON.parse(key);
      const earlier = element('div', 'earlier-draft');
      earlier.append(element('strong', '', 'Earlier draft, not saved'), element('p', '', 'The team updated this request. You can read your earlier draft here.'), element('p', 'earlier-question', oldQuestion[1]));
      const label = oldQuestion[2].find(choice => choice.id === value.choice_id)?.label;
      if (oldQuestion[3]) earlier.append(element('p', '', oldQuestion[3]));
      if (label) earlier.append(element('p', '', label));
      if (value.comment) earlier.append(element('p', '', value.comment));
      return earlier;
    });
  }

  function renderFeedback(task) {
    const feedback = task.feedback;
    const section = element('section', 'feedback-section');
    if (!feedback.answer) section.append(element('span', 'feedback-tag', 'Needs your answer'));
    section.append(element('h3', 'feedback-heading', feedback.question));
    if (feedback.why) section.append(element('p', 'feedback-why', feedback.why));
    if (feedback.answer) {
      const answer = element('div', 'saved-answer');
      const heading = element('h3', '', 'Saved · Waiting for team');
      heading.id = 'answer-saved';
      heading.tabIndex = -1;
      answer.append(heading);
      const label = answerLabel(feedback);
      if (label) answer.append(element('p', '', label));
      if (feedback.answer.comment) answer.append(element('p', '', feedback.answer.comment));
      answer.append(element('p', 'answer-time', 'You saved this answer ' + formatTime(feedback.answer.submitted_at) + '. The team will review it.'));
      section.append(answer);
      section.append(...renderEarlierDrafts(task));
      return section;
    }
    const key = draftKey(task);
    const draft = getDraft(task);
    const save = state.saves.get(key) || {};
    const form = element('form');
    form.id = 'feedback-form';
    if (feedback.choices && feedback.choices.length) {
      const choices = element('fieldset', 'feedback-choices');
      choices.disabled = Boolean(save.pending);
      choices.append(element('legend', '', 'Choose an option, or write your own answer below.'));
      feedback.choices.forEach((choice, index) => {
        const label = element('label', 'feedback-choice');
        const radio = element('input');
        radio.type = 'radio';
        radio.name = 'feedback-choice';
        radio.id = 'feedback-choice-' + index;
        radio.value = choice.id;
        radio.checked = draft.choice_id === choice.id;
        radio.addEventListener('change', () => { draft.choice_id = choice.id; markDraft(key); });
        label.append(radio, element('span', '', choice.label));
        choices.append(label);
      });
      form.append(choices);
    }
    const field = element('div', 'db-field');
    const label = element('label', 'db-field__label', feedback.choices && feedback.choices.length ? 'Your answer or extra details' : 'Your answer');
    label.htmlFor = 'feedback-comment';
    const comment = element('textarea', 'db-textarea feedback-comment');
    comment.id = 'feedback-comment';
    comment.rows = 4;
    comment.maxLength = 12000;
    comment.placeholder = 'Tell your team what would work for you…';
    comment.value = draft.comment;
    comment.disabled = Boolean(save.pending);
    comment.setAttribute('aria-describedby', 'save-status');
    comment.addEventListener('input', () => { draft.comment = comment.value; markDraft(key); });
    field.append(label, comment);
    form.append(field);
    const row = element('div', 'save-row');
    const button = element('button', 'db-btn db-btn--primary', save.pending ? 'Saving your answer…' : save.error ? 'Retry saving answer' : 'Save answer');
    button.id = 'save-feedback';
    button.type = 'submit';
    button.disabled = Boolean(save.pending);
    row.append(button);
    const status = element('p', 'save-status' + (save.error ? ' error' : ''), save.pending ? 'Saving to your project…' : save.error || (draft.comment || draft.choice_id ? 'Draft, not saved yet.' : 'Save your response for the team.'));
    status.id = 'save-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    form.append(row, status);
    form.addEventListener('submit', event => { event.preventDefault(); saveFeedback(task); });
    section.append(form);
    section.append(...renderEarlierDrafts(task, key));
    return section;
  }

  function markDraft(key) {
    state.saves.delete(key);
    const status = $('save-status');
    if (status) { status.textContent = 'Draft, not saved yet.'; status.classList.remove('error'); }
    if ($('save-feedback')) $('save-feedback').textContent = 'Save answer';
  }

  function renderDetail() {
    const task = state.tasks.get(state.detail);
    $('workspace').classList.toggle('has-detail', Boolean(task));
    $('task-detail').hidden = !task;
    if (!task) { $('task-detail').replaceChildren(); state.detailSignature = ''; return; }
    const signature = JSON.stringify([task, state.saves.get(task.feedback && !task.feedback.answer ? draftKey(task) : '')]);
    if (signature === state.detailSignature) return;
    state.detailSignature = signature;
    const header = element('div', 'detail-header');
    const headingGroup = element('div', 'detail-heading-group');
    headingGroup.append(element('p', 'eyebrow', statuses.find(status => status.id === task.status).label));
    const heading = element('h2', '', task.title);
    heading.id = 'detail-title';
    heading.tabIndex = -1;
    headingGroup.append(heading);
    const close = element('button', 'detail-close', '×');
    close.id = 'close-details';
    close.type = 'button';
    close.setAttribute('aria-label', 'Close task details');
    close.addEventListener('click', closeDetails);
    header.append(headingGroup, close);
    const body = element('div', 'detail-body');
    body.append(element('p', 'detail-description', task.description || 'Your team will add details as they work on this task.'));
    const evidence = element('section', 'detail-section');
    evidence.append(element('h3', '', 'Checks shared by the team'));
    if (task.evidence && task.evidence.length) {
      const list = element('ul', 'evidence-list');
      task.evidence.forEach(check => {
        const item = element('li');
        const tick = element('span', 'evidence-check', '•');
        tick.setAttribute('aria-hidden', 'true');
        const content = element('span', '', check);
        try {
          const url = new URL(check);
          if (['http:', 'https:'].includes(url.protocol) && !url.username && !url.password) {
            const link = element('a', '', check);
            link.href = url.href;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            content.replaceChildren(link);
          }
        } catch (_) { /* Keep prose and invalid addresses as text. */ }
        item.append(tick, content);
        list.append(item);
      });
      evidence.append(list);
    } else evidence.append(element('p', 'muted-copy', 'The team hasn’t shared checks for this task yet.'));
    body.append(evidence);
    if (task.feedback) body.append(renderFeedback(task));
    else body.append(...renderEarlierDrafts(task));
    const history = (task.feedback_history || []).filter(previous => previous.answer);
    if (history.length) {
      const prior = element('details', 'prior-decisions');
      prior.append(element('summary', '', 'Prior decisions (' + history.length + ')'));
      history.forEach(previous => {
        const decision = element('div', 'prior-decision');
        decision.append(element('h4', '', previous.question));
        const label = answerLabel(previous);
        if (label) decision.append(element('p', '', label));
        if (previous.answer.comment) decision.append(element('p', '', previous.answer.comment));
        decision.append(element('p', '', 'Saved ' + formatTime(previous.answer.submitted_at)));
        prior.append(decision);
      });
      body.append(prior);
    }
    $('task-detail').replaceChildren(header, body);
  }

  function closeDetails() {
    state.detail = null;
    render();
    $('show-details').focus();
  }

  function captureFocus() {
    const node = document.activeElement;
    return { node, id: node.id, taskId: node.dataset.taskId, breadcrumbId: node.dataset.breadcrumbId, start: node.selectionStart, end: node.selectionEnd };
  }

  function restoreFocus(previous) {
    if (previous.node.isConnected || previous.node === document.body) return;
    let target = previous.id ? $(previous.id) : null;
    if (!target && previous.taskId) target = [...document.querySelectorAll('[data-task-id]')].find(node => node.dataset.taskId === previous.taskId);
    if (!target && previous.breadcrumbId !== undefined) target = [...document.querySelectorAll('[data-breadcrumb-id]')].find(node => node.dataset.breadcrumbId === previous.breadcrumbId);
    target = target || $('answer-saved') || $('board-heading');
    target.focus({ preventScroll: true });
    if (previous.start !== null && typeof target.setSelectionRange === 'function') target.setSelectionRange(previous.start, previous.end);
  }

  function render() {
    if (!state.board) return;
    const previous = captureFocus();
    renderHeader();
    renderBreadcrumbs();
    renderBoard();
    renderDetail();
    restoreFocus(previous);
    $('loading-state').hidden = true;
    $('board-region').setAttribute('aria-busy', 'false');
  }

  function acceptBoard(board) {
    const indexed = indexBoard(board);
    if (state.board && board.revision < state.board.revision) return;
    state.board = board;
    Object.assign(state, indexed);
    if (state.parent !== null && !state.tasks.has(state.parent)) { state.parent = null; state.detail = null; }
    if (state.detail !== null && !state.tasks.has(state.detail)) state.detail = null;
  }

  async function request(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, { ...options, credentials: 'same-origin', cache: 'no-store', signal: controller.signal });
      let body;
      try { body = await response.json(); } catch (_) { throw new Error('The project didn’t send a readable response. Keep this page open and try again.'); }
      if (!response.ok) {
        const error = new Error(body.error || 'Your project couldn’t complete the request. Try again.');
        error.status = response.status;
        throw error;
      }
      return body;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('The project took too long to respond. Check that your team’s progress board is still running, then retry.');
      if (error instanceof TypeError) throw new Error('We couldn’t reach your project. Check that your team’s progress board is still running, then retry.');
      throw error;
    } finally { clearTimeout(timeout); }
  }

  async function refreshCsrf() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/', { credentials: 'same-origin', cache: 'no-store', signal: controller.signal });
      if (!response.ok) return false;
      const document = new DOMParser().parseFromString(await response.text(), 'text/html');
      const token = document.querySelector('meta[name="csrf-token"]')?.content;
      if (!token || token === csrf) return false;
      csrf = token;
      return true;
    } finally { clearTimeout(timeout); }
  }

  function setConnection(connected, paused = false) {
    $('connection-dot').classList.toggle('connected', connected);
    $('connection-dot').classList.toggle('offline', !connected);
    $('connection-status').textContent = connected ? 'Connected to your project' : paused ? 'Updates paused. Use Retry to reconnect.' : 'Reconnecting to your project';
  }

  function schedulePoll() {
    clearTimeout(state.timer);
    if (!state.paused) state.timer = setTimeout(() => loadBoard(), 10000);
  }

  async function loadBoard(manual = false) {
    if (state.loading || [...state.saves.values()].some(save => save.pending)) { schedulePoll(); return; }
    if (document.hidden && !manual) { schedulePoll(); return; }
    state.loading = true;
    if (manual) { state.paused = false; state.failures = 0; $('retry-load').disabled = true; }
    try {
      const board = await request('/api/board');
      const firstLoad = !state.board;
      acceptBoard(board);
      if (firstLoad) readRoute();
      state.failures = 0;
      state.paused = false;
      $('load-error').hidden = true;
      setConnection(true);
      render();
      if (manual) announce('Your progress is up to date.');
    } catch (error) {
      state.failures += 1;
      state.paused = error.status === 429 || state.failures >= 3;
      $('load-error-title').textContent = state.board ? 'Team updates haven’t reached this page.' : 'We couldn’t load your progress.';
      $('load-error-message').textContent = error.message + (state.board ? ' Your last view and unsaved answers stay here.' : '');
      $('load-error').hidden = false;
      $('loading-state').hidden = true;
      $('board-region').setAttribute('aria-busy', 'false');
      setConnection(false, state.paused);
    } finally {
      state.loading = false;
      $('retry-load').disabled = false;
      schedulePoll();
    }
  }

  async function saveFeedback(task) {
    const key = draftKey(task);
    if (state.saves.get(key)?.pending) return;
    const draft = getDraft(task);
    if (!draft.choice_id && !draft.comment.trim()) {
      state.saves.set(key, { error: 'Choose an option or write an answer before saving.' });
      render();
      $('feedback-comment').focus();
      return;
    }
    state.saves.set(key, { pending: true });
    render();
    try {
      const body = JSON.stringify({ choice_id: draft.choice_id, comment: draft.comment, expected_question: task.feedback.question, expected_choices: task.feedback.choices || [], expected_why: task.feedback.why });
      const submit = () => request('/api/tasks/' + encodeURIComponent(task.id) + '/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
        body
      });
      let board;
      try { board = await submit(); }
      catch (error) {
        if (error.status !== 403 || !await refreshCsrf()) throw error;
        board = await submit();
      }
      acceptBoard(board);
      state.drafts.delete(key);
      state.saves.delete(key);
      state.failures = 0;
      state.paused = false;
      $('load-error').hidden = true;
      setConnection(true);
      render();
      schedulePoll();
      announce('Your answer is saved. The team will review it.');
      $('answer-saved')?.focus({ preventScroll: true });
    } catch (error) {
      state.saves.set(key, { error: error.message + ' Your answer is still here. You can retry saving.' });
      render();
      announce('Your answer hasn’t saved. ' + error.message);
      $('save-feedback')?.focus({ preventScroll: true });
      if (error.status === 429) { state.paused = true; clearTimeout(state.timer); setConnection(false, true); }
    }
  }

  $('all-work-filter').addEventListener('click', () => navigate(null));
  $('needs-you-filter').addEventListener('click', () => navigate(null, true));
  $('show-details').addEventListener('click', () => { state.detail = state.parent; render(); $('detail-title').focus(); });
  $('retry-load').addEventListener('click', () => loadBoard(true));
  window.addEventListener('popstate', () => { readRoute(); render(); $('board-heading').focus({ preventScroll: true }); });
  window.addEventListener('hashchange', () => { readRoute(); render(); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden && !state.paused) loadBoard(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && state.detail && $('task-detail').contains(document.activeElement)) closeDetails(); });
  loadBoard();
})();

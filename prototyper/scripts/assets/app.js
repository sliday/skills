(() => {
  const $ = id => document.getElementById(id);
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  let state = null, cursor = 0, timer, dirty = false, busy = false, queue = Promise.resolve();
  async function api(path, payload) {
    const response = await fetch(path, payload === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }, body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Could not complete this request.');
    return result;
  }
  function status(message, error = false) {
    $('save-status').textContent = message;
    $('save-status').classList.toggle('error', error);
  }
  function controls() {
    $('back').disabled = busy || cursor === 0;
    $('skip').disabled = busy;
    $('next').disabled = busy;
    $('next').textContent = cursor === state.questions.length - 1 ? 'Save answer' : 'Save and continue';
  }
  async function list() {
    const result = await api('/api/projects');
    $('data-location').textContent = 'Local data directory: ' + result.data_dir;
    $('project-list').replaceChildren();
    for (const project of result.projects) {
      const item = document.createElement('li'), button = document.createElement('button');
      button.type = 'button'; button.textContent = project.name;
      button.setAttribute('aria-current', String(state && state.project.id === project.id));
      button.addEventListener('click', () => open(project.id).catch(error => $('project-error').textContent = error.message));
      item.append(button); $('project-list').append(item);
    }
  }
  function render() {
    const q = state.questions[cursor], saved = state.answers[q.id];
    $('empty-state').hidden = true; $('survey').hidden = false;
    $('project-title').textContent = state.project.name;
    $('question-progress').textContent = `Question ${cursor + 1} of ${state.questions.length}`;
    $('question-title').textContent = q.prompt;
    $('question-help').textContent = q.help;
    $('answer').value = saved ? saved.answer : '';
    $('answer').hidden = q.options.length > 0;
    $('answer-options').replaceChildren();
    for (const option of q.options) {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = option;
      button.setAttribute('aria-pressed', String($('answer').value === option));
      button.addEventListener('click', () => {
        $('answer').value = option; dirty = true;
        for (const other of $('answer-options').children) other.setAttribute('aria-pressed', String(other === button));
        schedule();
      });
      $('answer-options').append(button);
    }
    $('answer-provenance').textContent = saved ? `${saved.status === 'skipped' ? 'Skipped' : saved.status === 'draft' ? 'Draft' : 'Answered'} · pack ${saved.pack_version}` : 'You can skip unknowns and return later.';
    status(saved ? 'Saved locally.' : 'No answer yet.');
    dirty = false; controls();
    $('export-links').replaceChildren();
    for (const [filename, label] of [['discovery.json', 'JSON record'], ['PRD.md', 'Project brief (PRD)'], ['BAR.md', 'Acceptance bar']]) {
      const link = document.createElement('a');
      link.href = '/api/projects/' + state.project.id + '/export/' + filename;
      link.textContent = label; link.download = filename;
      $('export-links').append(link);
    }
  }
  async function open(id) {
    clearTimeout(timer);
    if (state && dirty) await save('draft', cursor);
    await queue.catch(() => {});
    state = await api('/api/projects/' + id);
    cursor = Math.min(state.project.cursor, state.questions.length - 1);
    render(); await list();
  }
  function save(answerStatus, nextCursor) {
    clearTimeout(timer);
    const id = state.project.id, q = state.questions[cursor];
    const payload = { question_id: q.id, answer: $('answer').value, status: answerStatus, cursor: nextCursor };
    status('Saving locally…');
    const task = queue.catch(() => {}).then(async () => {
      const result = await api('/api/projects/' + id + '/answer', payload);
      if (state && state.project.id === id) {
        state = result;
        status(answerStatus === 'skipped' ? 'Skip saved locally.' : 'Saved locally.');
      }
      return result;
    });
    queue = task;
    return task.catch(error => { status(error.message + ' Your text remains on this page.', true); throw error; });
  }
  function schedule() {
    clearTimeout(timer); status('Unsaved changes.');
    timer = setTimeout(() => {
      const value = $('answer').value;
      save('draft', cursor).then(() => { if ($('answer').value === value) dirty = false; }).catch(() => {});
    }, 500);
  }
  $('answer').addEventListener('input', () => { dirty = true; schedule(); });
  async function move(direction, answerStatus) {
    if (busy) return;
    busy = true; controls();
    try {
      const nextCursor = Math.max(0, Math.min(state.questions.length - 1, cursor + direction));
      const existing = state.answers[state.questions[cursor].id];
      await save(answerStatus || (dirty ? 'draft' : existing?.status || 'draft'), nextCursor);
      cursor = nextCursor; render(); await list();
      $('question-title').scrollIntoView({ block: 'nearest' });
    } catch {} finally { busy = false; controls(); }
  }
  $('back').addEventListener('click', () => move(-1));
  $('skip').addEventListener('click', () => move(1, 'skipped'));
  $('next').addEventListener('click', () => move(1, 'answered'));
  $('review-answers').addEventListener('click', async () => {
    try { await move(-cursor); } catch {}
  });
  $('new-project').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      if (state && dirty) await save('draft', cursor);
      await queue.catch(() => {});
      state = await api('/api/projects', { name: $('project-name').value });
      cursor = 0; $('project-name').value = ''; $('project-error').textContent = '';
      render(); await list();
    } catch (error) { $('project-error').textContent = error.message; }
  });
  $('delete-project').addEventListener('click', async () => {
    if (!state || !confirm('Delete this project and its local answers?')) return;
    try {
      clearTimeout(timer); await queue.catch(() => {});
      await api('/api/projects/' + state.project.id + '/delete', {});
      state = null; dirty = false; $('survey').hidden = true; $('empty-state').hidden = false; await list();
    } catch (error) { status(error.message, true); }
  });
  addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  list().catch(error => $('project-error').textContent = error.message);
})();

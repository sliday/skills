#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, execFileSync } = require('node:child_process');

function argumentsFrom(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const name = argv[index];
    if (name === '--help') {
      console.log('Usage: node board-browser.cjs [--url http://127.0.0.1:PORT/] [--output-dir PATH] [--playwright-path PATH]\nCreates its own temporary demonstration board. --url selects a free loopback port; this eval never attaches to an existing board. Install Playwright and its Chromium browser before running.');
      process.exit(0);
    }
    if (!['--url', '--output-dir', '--playwright-path'].includes(name) || !argv[index + 1]) throw new Error('Unknown or incomplete argument: ' + name);
    options[name.slice(2)] = argv[++index];
  }
  if (options.url) {
    const url = new URL(options.url);
    if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1' || !url.port || url.username || url.password || url.pathname !== '/' || url.search || url.hash) throw new Error('--url must be http://127.0.0.1:PORT/ with a free port. The eval creates its own server.');
    options.port = Number(url.port);
  } else options.port = 0;
  return options;
}

async function main() {
  const options = argumentsFrom(process.argv.slice(2));
  const output = path.resolve(options['output-dir'] || fs.mkdtempSync(path.join(os.tmpdir(), 'prototyper-browser-evidence-')));
  fs.mkdirSync(output, { recursive: true });
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'prototyper-browser-fixture-'));
  const boardTool = path.resolve(__dirname, '../scripts/board.py');
  const python = process.env.PYTHON || 'python3';
  const checks = [];
  const screenshots = [];
  const consoleErrors = [];
  const requests = [];
  let browser;
  let server;
  let serverLog = '';
  let activePage;
  let scenario = 'Browser and synthetic server setup';
  let failure = null;

  async function stopServer() {
    if (!server || server.exitCode !== null) return;
    const child = server;
    await new Promise(resolve => {
      const timeout = setTimeout(() => child.kill('SIGKILL'), 3000);
      child.once('exit', () => { clearTimeout(timeout); resolve(); });
      child.kill('SIGINT');
    });
  }

  async function startServer(demo) {
    server = spawn(python, ['-u', boardTool, '--data-dir', temporary, '--port', String(options.port), ...(demo ? ['--demo'] : [])], { stdio: ['ignore', 'pipe', 'pipe'] });
    const child = server;
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => { child.kill('SIGTERM'); reject(new Error('The isolated board server did not start within 10 seconds.')); }, 10000);
      let stdout = '';
      child.stdout.on('data', data => {
        stdout += data.toString();
        serverLog += data.toString();
        const match = stdout.match(/Open (http:\/\/127\.0\.0\.1:\d+\/)/);
        if (match) { clearTimeout(timeout); resolve(match[1]); }
      });
      child.stderr.on('data', data => { serverLog += data.toString(); });
      child.once('error', error => { clearTimeout(timeout); reject(error); });
      child.once('exit', code => { clearTimeout(timeout); if (!stdout.includes('Open http://')) reject(new Error('The isolated board server exited with code ' + code + '. Choose a free --url port and check Python permissions.\n' + serverLog)); });
    });
  }

  async function screenshot(page, name) {
    const file = name + '.png';
    await page.screenshot({ path: path.join(output, file), fullPage: true });
    screenshots.push(file);
  }

  async function check(name, criterion, action) {
    scenario = name;
    await action();
    checks.push({ scenario: name, criterion, status: 'pass' });
  }

  function watch(page) {
    activePage = page;
    page.on('pageerror', error => consoleErrors.push({ type: 'pageerror', message: error.message }));
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push({ type: 'console', message: message.text() }); });
    page.on('request', request => requests.push(request.url()));
    return page;
  }

  function apply(board) {
    const fixture = path.join(temporary, 'synthetic-update.json');
    fs.writeFileSync(fixture, JSON.stringify(board));
    serverLog += execFileSync(python, [boardTool, '--data-dir', temporary, '--apply', fixture], { encoding: 'utf8' });
  }

  try {
    let playwright;
    try { playwright = require(options['playwright-path'] || 'playwright'); }
    catch (_) { throw new Error('Playwright is unavailable. Install it in your environment or pass --playwright-path to an existing Playwright library. The browser checks did not run.'); }
    let url = await startServer(true);
    browser = await playwright.chromium.launch({ headless: true });
    const page = watch(await browser.newPage({ viewport: { width: 1440, height: 1000 } }));
    await page.goto(url);
    await page.locator('[data-task-id="quote-flow"]').waitFor();

    await check('Root stages, labelled demo and ancestor questions', 'K1,K3,K5', async () => {
      assert.equal(await page.locator('.task-column').count(), 4);
      assert.equal(await page.locator('#demo-notice').isVisible(), true);
      assert.equal(await page.locator('#prototype-link').isHidden(), true);
      assert.match(await page.locator('[data-task-id="quote-flow"]').innerText(), /2 answers needed/);
      assert.equal(await page.locator('#needs-you-count').innerText(), '2');
      await screenshot(page, 'desktop-root-1440');
    });

    await check('Three task levels and routes to ancestors', 'K2,K6', async () => {
      await page.locator('[data-task-id="quote-flow"]').click();
      await page.locator('[data-task-id="quote-items"]').click();
      await page.locator('[data-task-id="quote-price"]').click();
      assert.equal(await page.locator('#breadcrumbs li').count(), 4);
      assert.equal(await page.locator('#detail-title').innerText(), 'Check the item total (demo)');
    });

    await check('Evidence links open local proof by keyboard and unsafe entries remain text', 'K5,K6,K7', async () => {
      const board = await (await page.request.get(url + 'api/board')).json();
      const proofUrl = url + 'api/board';
      board.tasks.find(task => task.id === 'quote-price').evidence = [
        'Observed a synthetic price before saving.', 'FAILED: synthetic price check.', proofUrl,
        'javascript:alert(1)', 'data:text/html,<script>alert(1)</script>',
        'file:///tmp/private-proof', 'https://user@example.com/', '<img src=x onerror=alert(1)>'
      ];
      apply(board);
      await page.reload();
      const link = page.locator('.evidence-list a');
      await link.waitFor();
      assert.equal(await link.count(), 1);
      assert.equal(await page.locator('.evidence-check').allTextContents().then(items => items.every(item => item === '•')), true);
      assert.match(await page.locator('.evidence-list').innerText(), /FAILED: synthetic price check/);
      assert.equal(await link.getAttribute('href'), proofUrl);
      assert.equal(await link.getAttribute('rel'), 'noopener noreferrer');
      assert.equal(await page.locator('.evidence-list img, .evidence-list script').count(), 0);
      assert.match(await page.locator('.evidence-list').innerText(), /javascript:alert\(1\)/);
      await link.focus();
      const opened = page.waitForEvent('popup');
      await page.keyboard.press('Enter');
      const proof = watch(await opened);
      await proof.waitForLoadState('domcontentloaded');
      assert.equal(proof.url(), proofUrl);
      const output = await proof.locator('body').innerText();
      assert.match(output, /"schema_version"\s*:\s*1/);
      assert(output.includes(board.project.name));
      await proof.close();
      activePage = page;
      await screenshot(page, 'desktop-proof-link-1440');
    });

    await check('Agent update retains the choice, draft, focus and caret', 'K4,K6', async () => {
      await page.locator('#feedback-choice-1').check();
      await page.locator('#feedback-comment').fill('Keep the rate available in the details.');
      await page.locator('#feedback-comment').focus();
      await page.locator('#feedback-comment').evaluate(node => node.setSelectionRange(8, 8));
      const board = await (await page.request.get(url + 'api/board')).json();
      board.tasks.find(task => task.id === 'quote-price').description = 'Show a customer the total before they save a quote.';
      apply(board);
      await page.waitForTimeout(11000);
      assert.equal(await page.locator('#feedback-comment').inputValue(), 'Keep the rate available in the details.');
      assert.equal(await page.locator('#feedback-choice-1').isChecked(), true);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'feedback-comment');
      assert.equal(await page.locator('#feedback-comment').evaluate(node => node.selectionStart), 8);
      await screenshot(page, 'desktop-detail-1440');
    });

    await check('Same-port restart refreshes CSRF and saves the open draft once', 'K4,K7', async () => {
      const port = Number(new URL(url).port);
      const initialToken = await page.locator('meta[name="csrf-token"]').getAttribute('content');
      await stopServer();
      options.port = port;
      assert.equal(await startServer(false), url);
      assert.equal(await page.locator('#feedback-comment').inputValue(), 'Keep the rate available in the details.');
      const statuses = [];
      const responses = response => { if (response.url().endsWith('/api/tasks/quote-price/feedback')) statuses.push(response.status()); };
      page.on('response', responses);
      await page.locator('#save-feedback').click();
      await page.locator('#answer-saved').waitFor();
      page.off('response', responses);
      assert.deepEqual(statuses, [403, 200]);
      const html = await (await page.request.get(url)).text();
      assert(!html.includes('content="' + initialToken + '"'));
      const board = await (await page.request.get(url + 'api/board')).json();
      assert.equal(board.tasks.find(task => task.id === 'quote-price').feedback.answer.comment, 'Keep the rate available in the details.');
      await screenshot(page, 'desktop-restart-saved-1440');
    });

    await check('Changed decision conditions archive the answer and preserve a stale draft', 'K3,K4,K7', async () => {
      const board = await (await page.request.get(url + 'api/board')).json();
      const task = board.tasks.find(task => task.id === 'quote-price');
      task.feedback.why = 'Your choice now authorizes an annual subscription commitment.';
      apply(board);
      await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
      await page.locator('#feedback-form').waitFor();
      await page.locator('.prior-decisions summary').click();
      assert.match(await page.locator('.prior-decisions').innerText(), /Keep the rate available in the details/);
      assert.equal(await page.locator('#needs-you-count').innerText(), '2');
      await page.locator('#feedback-choice-1').check();
      await page.locator('#feedback-comment').fill('Draft about the annual commitment.');
      const changed = await (await page.request.get(url + 'api/board')).json();
      changed.tasks.find(task => task.id === 'quote-price').feedback.why = 'Your choice now authorizes a monthly commitment.';
      apply(changed);
      await page.locator('#save-feedback').click();
      await page.getByText('Retry saving answer', { exact: true }).waitFor();
      assert.equal(await page.locator('#feedback-comment').inputValue(), 'Draft about the annual commitment.');
      const after = await (await page.request.get(url + 'api/board')).json();
      assert.equal(after.tasks.find(task => task.id === 'quote-price').feedback.answer, null);
      await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
      await page.getByText('Your choice now authorizes a monthly commitment.', { exact: true }).waitFor();
      assert.equal(await page.locator('#feedback-comment').inputValue(), '');
      assert.equal(await page.locator('#feedback-choice-1').isChecked(), false);
      assert.match(await page.locator('.earlier-draft').allTextContents().then(items => items.join('\n')), /annual subscription commitment/);
      assert.match(await page.locator('.earlier-draft').allTextContents().then(items => items.join('\n')), /Draft about the annual commitment/);
      await screenshot(page, 'desktop-changed-conditions-1440');
      await page.locator('#feedback-choice-1').check();
      await page.locator('#feedback-comment').fill('Keep the rate available in the details.');
    });

    await check('Failed save preserves inputs and offers a working retry', 'K4,K7', async () => {
      await page.route('**/api/tasks/quote-price/feedback', route => route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'The synthetic progress file could not be saved.' }) }));
      await page.locator('#save-feedback').click();
      await page.getByText('Retry saving answer', { exact: true }).waitFor();
      assert.equal(await page.locator('#feedback-comment').inputValue(), 'Keep the rate available in the details.');
      assert.equal(await page.locator('#feedback-choice-1').isChecked(), true);
      await page.unroute('**/api/tasks/quote-price/feedback');
      await page.route('**/api/tasks/quote-price/feedback', route => route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ error: 'The synthetic project needs a pause before another save.' }) }));
      await page.locator('#save-feedback').click();
      await page.getByText('Retry saving answer', { exact: true }).waitFor();
      assert.match(await page.locator('#connection-status').innerText(), /Updates paused/);
      assert.equal(await page.locator('#feedback-comment').inputValue(), 'Keep the rate available in the details.');
      await page.unroute('**/api/tasks/quote-price/feedback');
      await page.locator('#save-feedback').click();
      await page.locator('#answer-saved').waitFor();
      assert.equal(await page.locator('#needs-you-count').innerText(), '1');
      assert.equal(await page.locator('#connection-status').innerText(), 'Connected to your project');
    });

    await check('Saved feedback survives reload and a server restart', 'K4', async () => {
      await page.reload();
      await page.locator('#answer-saved').waitFor();
      assert.match(await page.locator('.saved-answer').innerText(), /Keep the rate available in the details/);
      await stopServer();
      url = await startServer(false);
      await page.goto(url + '#task=quote-price');
      await page.locator('#answer-saved').waitFor();
      assert.match(await page.locator('.saved-answer').innerText(), /Keep the rate available in the details/);
      const board = await (await page.request.get(url + 'api/board')).json();
      assert.equal(board.tasks.find(task => task.id === 'quote-price').status, 'planned');
    });

    await check('Changed request archives the decision and requires a new answer', 'K3,K4', async () => {
      const board = await (await page.request.get(url + 'api/board')).json();
      board.tasks.find(task => task.id === 'quote-price').feedback.question = 'Should the quote include tax?';
      apply(board);
      await page.waitForTimeout(11000);
      await page.locator('.prior-decisions summary').click();
      assert.match(await page.locator('.prior-decisions').innerText(), /Keep the rate available in the details/);
      assert.equal(await page.locator('#feedback-form').isVisible(), true);
      assert.equal(await page.locator('#needs-you-count').innerText(), '2');
    });

    await check('Global Needs you finds buried questions and opens them by keyboard', 'K3,K6', async () => {
      await page.locator('#needs-you-filter').click();
      assert.equal(await page.locator('[data-task-id]').count(), 2);
      assert.match(await page.locator('[data-task-id="quote-price"]').innerText(), /All work \/ Create a quote/);
      await page.locator('[data-task-id="quote-flow"]').focus();
      await page.keyboard.press('Enter');
      assert.equal(await page.locator('#detail-title').innerText(), 'Create a quote (demo)');
    });

    await check('A changed question keeps the earlier unsaved draft visible', 'K4,K6', async () => {
      await page.locator('#feedback-comment').fill('Draft for the earlier delivery question.');
      const board = await (await page.request.get(url + 'api/board')).json();
      board.tasks.find(task => task.id === 'quote-flow').feedback.question = 'Should customers receive a preview before the final quote?';
      apply(board);
      await page.waitForTimeout(11000);
      assert.match(await page.locator('.earlier-draft').allTextContents().then(items => items.join('\n')), /Draft for the earlier delivery question/);
      assert.equal(await page.locator('#feedback-comment').inputValue(), '');
    });

    await check('Relabelled choices preserve the prior draft without choosing a new answer', 'K4,K6', async () => {
      await page.locator('#needs-you-filter').click();
      await page.locator('[data-task-id="quote-price"]').click();
      await page.locator('#feedback-choice-1').check();
      await page.locator('#feedback-comment').fill('Keep the details available after the main total.');
      const board = await (await page.request.get(url + 'api/board')).json();
      board.tasks.find(task => task.id === 'quote-price').feedback.choices[1].label = 'Show a price summary';
      apply(board);
      await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
      await page.getByText('Show a price summary', { exact: true }).waitFor();
      assert.equal(await page.locator('#feedback-comment').inputValue(), '');
      assert.equal(await page.locator('#feedback-choice-1').isChecked(), false);
      assert.match(await page.locator('.earlier-draft').allTextContents().then(items => items.join('\n')), /Keep the details available after the main total/);
      assert.match(await page.locator('.earlier-draft').allTextContents().then(items => items.join('\n')), /Show the total only/);
      await page.locator('[data-breadcrumb-id=""]').click();
      await page.locator('[data-task-id="quote-flow"]').click();
    });

    await check('390px task and feedback views contain no document overflow', 'K6', async () => {
      await page.locator('[data-breadcrumb-id=""]').click();
      await page.setViewportSize({ width: 390, height: 844 });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
      await screenshot(page, 'mobile-root-390');
      await page.locator('[data-task-id="quote-flow"]').click();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
      await page.locator('#feedback-comment').focus();
      await screenshot(page, 'mobile-detail-390');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#task-detail').isHidden(), true);
      assert.equal(await page.evaluate(() => document.activeElement.id), 'show-details');
    });

    await check('Closing a question keeps its unsaved draft available', 'K4,K6', async () => {
      await page.locator('#show-details').click();
      const board = await (await page.request.get(url + 'api/board')).json();
      board.tasks.find(task => task.id === 'quote-flow').feedback = null;
      apply(board);
      await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
      await page.locator('#feedback-form').waitFor({ state: 'detached' });
      assert.match(await page.locator('.earlier-draft').allTextContents().then(items => items.join('\n')), /Draft for the earlier delivery question/);
      assert.equal(await page.locator('#feedback-form').count(), 0);
    });

    const empty = { schema_version: 1, revision: 0, updated_at: null, project: { name: 'Your prototype', summary: 'No development tasks yet.', demo: false, prototype_url: null }, tasks: [] };
    const states = watch(await browser.newPage({ viewport: { width: 1280, height: 900 } }));
    await check('Loading and empty states make no claim of completed work', 'K1,K5', async () => {
      let release;
      const waiting = new Promise(resolve => { release = resolve; });
      await states.route('**/api/board', async route => { await waiting; await route.fulfill({ contentType: 'application/json', body: JSON.stringify(empty) }); });
      await states.goto(url);
      assert.equal(await states.locator('#loading-state').isVisible(), true);
      await screenshot(states, 'desktop-loading-1280');
      release();
      await states.getByText('Your project starts here.', { exact: true }).waitFor();
      assert.equal(await states.locator('.task-column').count(), 4);
      assert.equal(await states.locator('#demo-notice').isHidden(), true);
      assert.equal(await states.locator('#last-updated').innerText(), 'No team updates yet');
      assert.equal(await states.locator('[data-task-id]').count(), 0);
      await screenshot(states, 'desktop-empty-1280');
    });

    await check('Tab order, skip link and focus outline support keyboard navigation', 'K6', async () => {
      await states.keyboard.press('Tab');
      assert.equal(await states.evaluate(() => document.activeElement.className), 'skip-link');
      assert.equal(await states.locator('.skip-link').evaluate(node => getComputedStyle(node).clipPath), 'none');
      await states.keyboard.press('Enter');
      assert.equal(await states.evaluate(() => document.activeElement.id), 'board-heading');
      await states.keyboard.press('Tab');
      assert.equal(await states.evaluate(() => document.activeElement.id), 'all-work-filter');
      assert.notEqual(await states.locator('#all-work-filter').evaluate(node => getComputedStyle(node).outlineStyle), 'none');
      await states.keyboard.press('Tab');
      await states.keyboard.press('Enter');
      assert.match(await states.locator('#board-notice').innerText(), /You’re up to date/);
    });

    const errors = watch(await browser.newPage({ viewport: { width: 390, height: 844 } }));
    await check('Rate limits pause polling and Retry reconnects on a phone', 'K6,K7', async () => {
      await errors.route('**/api/board', route => route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ error: 'The synthetic project needs a pause before another request.' }) }));
      await errors.goto(url);
      await errors.locator('#load-error').waitFor();
      assert.match(await errors.locator('#connection-status').innerText(), /Updates paused/);
      assert.equal(await errors.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
      await screenshot(errors, 'mobile-error-390');
      await errors.unroute('**/api/board');
      await errors.locator('#retry-load').click();
      await errors.locator('[data-task-id="quote-flow"]').waitFor();
      assert.equal(await errors.locator('#load-error').isHidden(), true);
    });

    await check('Untrusted task text and a script address render without execution', 'K7', async () => {
      activePage = states;
      const unsafe = JSON.parse(JSON.stringify(empty));
      unsafe.project.name = '<img src=x onerror=alert(1)>';
      unsafe.project.prototype_url = 'javascript:alert(1)';
      unsafe.tasks.push({ id: 'unsafe', parent_id: null, title: '<script>alert(1)</script>', description: '<img src=x onerror=alert(1)>', status: 'planned', evidence: [], feedback: null });
      await states.unroute('**/api/board');
      await states.route('**/api/board', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify(unsafe) }));
      await states.goto(url);
      await states.locator('[data-task-id="unsafe"]').waitFor();
      assert.equal(await states.locator('#project-name').innerText(), '<img src=x onerror=alert(1)>');
      assert.equal(await states.locator('#prototype-link').isHidden(), true);
      assert.equal(await states.locator('#main-content img').count(), 0);
      assert.equal(await states.locator('#task-board script').count(), 0);
    });

    await check('No unexpected browser errors or third-party requests', 'K7', async () => {
      const unexpected = consoleErrors.filter(error => error.type === 'pageerror' || !/status of (500|429|403|409)/.test(error.message));
      assert.deepEqual(unexpected, []);
      assert(requests.every(address => address.startsWith('data:') || new URL(address).hostname === '127.0.0.1'));
    });
  } catch (error) {
    failure = { scenario, message: error.message, stack: error.stack };
    checks.push({ scenario, status: 'fail', error: error.message });
    if (activePage && !activePage.isClosed()) {
      try { await screenshot(activePage, 'failure'); } catch (_) { /* Keep the original failure if screenshot capture also fails. */ }
    }
  } finally {
    if (browser) await browser.close();
    await stopServer();
    fs.rmSync(temporary, { recursive: true, force: true });
    const report = { checked_at: new Date().toISOString(), status: failure ? 'fail' : 'pass', synthetic_fixture: true, viewport_sizes: ['1440×1000', '1280×900', '390×844'], checks, screenshots, console_errors: consoleErrors, requests, failure, visual_review: 'Inspect the retained screenshots before claiming visual acceptance.' };
    fs.writeFileSync(path.join(output, 'browser-results.json'), JSON.stringify(report, null, 2) + '\n');
    fs.writeFileSync(path.join(output, 'browser-server.log'), serverLog);
    console.log(JSON.stringify({ status: report.status, checks: checks.length, evidence: output, failure }, null, 2));
    if (failure) process.exitCode = 1;
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });

# Evaluate Prototyper

Run the bundled behaviour evals with Python 3:

```sh
python3 /path/to/prototyper/evals/run.py
```

The runner checks discovery, the progress board and commit-only release packaging through their public interfaces. It uses synthetic data, temporary directories and ephemeral loopback servers. It retains suite logs and a JSON result in the printed temporary directory. `--output-dir` chooses an evidence directory; `--suite discovery`, `--suite board` or `--suite package` runs a relevant subset. The evals do not contact external services, use a production database or alter client task data.

Treat a nonzero exit code as a failed check. A sandbox can prevent a loopback server from starting; record that as a harness limitation and run in a permitted local environment. Do not report that the application passed a check that could not execute.

The Python runner does not verify rendered layout or browser interaction. If Node.js and Playwright are available, run the browser eval:

```sh
node /path/to/prototyper/evals/board-browser.cjs --output-dir /path/to/private-evidence
```

Use `--playwright-path /path/to/installed/playwright` when the library does not resolve from the skill folder. The browser eval starts its own synthetic board and does not connect to an existing client board. Inspect its screenshots before claiming rendered criteria. Missing browser tooling means those criteria remain untested. Record viewport, task, before/action/after, persistence, console errors and any failed or untested cases.

For skill behaviour, use [the five client cases](skill-cases.json) with a fresh evaluator and the installed skill, without builder explanations. Follow each case's setup and grade its assertions as pass, fail or untested, with evidence for each result. The cases cover day-one use, an existing stack, saved feedback, an environment without execution tools and mocked billing/email flows. The Python runner checks helper tools; it does not execute these agent cases.

Expect one runnable input-to-result route, first-use instructions, honest boundaries, outcome cards and observable proof when execution tools exist. Submit synthetic feedback for the feedback case and check its saved decision, changed work and handoff. An agent exercise does not establish customer demand or replace feedback from an actual user.

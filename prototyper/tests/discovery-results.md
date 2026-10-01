# Local discovery verification, 1 October 2026

The evaluator read the actual `Store`, HTTP handler and browser assets before writing tests. Tests use Python's standard library, a temporary SQLite directory, an ephemeral loopback HTTP server and synthetic answers. Run `python3 discovery-check.py --tool /path/to/scripts/discovery.py`.

## Observed results

| Check | Evidence |
| --- | --- |
| Website, app and service | Three complete API interviews selected their corresponding question branches. Exports retained the chosen stack or manual-service constraint and generated PRD, BAR and JSON through the CLI. |
| Resume and edit | A new Store instance reopened the saved draft and cursor. An edited answer reached the brief. Changing App to Service excluded the inactive app answer from the brief while preserving its local history. |
| Skip and delete | A skipped constraint remained unknown. Deleting one project removed its answers and kept a second project readable. |
| Request protection | Foreign Origin, unexpected Host, missing/incorrect CSRF each returned 403. Malformed JSON, non-object JSON, invalid UTF-8 and blank required answers returned 400. An unsupported mutation returned 404. Rejected writes preserved saved answers. |
| Local storage | Server bound 127.0.0.1. Database permissions equalled 0600. HTTP responses included no-store, nosniff and a same-origin CSP with frame protection. |
| Export | Unicode and multiline answers survived. Three CLI exports matched API PRD text and included BAR plus structured provenance. |
| Browser | Chromium completed the 18-question website survey, resumed an autosaved draft after reload, preserved Unicode and HTML-looking text, and showed the empty-answer error without moving on. The resulting brief had no unanswered questions. |
| Browser boundaries | At 375px, viewport and document width both equalled 375. Resource timing showed zero foreign-origin requests. The evaluator inspected the screenshot; project HTML-looking text created zero image nodes. Keyboard Tab reached a textarea with a solid focus outline. |

The initial standard-library test run passed three tests in 1.768 seconds. Chromium logged the expected 400 response from the intentional empty-answer attempt. Browser observations live in `/tmp/sliday-discovery-browser/results.json`, `full-survey.json` and `mobile.png`; isolated synthetic database lives in `/tmp/sliday-discovery-browser-data/`.

## Found gap and correction gate

Python 3.14 emitted ResourceWarnings for unclosed SQLite connections. A SQLite connection context commits or rolls back but does not close the connection. The evaluator reported this to the implementation owner, who added a transaction-preserving context manager that closes the connection in `finally`. The evaluator read the corrected method and reran the three acceptance tests with `python3 -W error::ResourceWarning discovery-check.py --tool /path/to/scripts/discovery.py`. All three passed in 1.967 seconds with no ResourceWarnings. The browser evidence predates this connection-only fix; the API rerun covers the changed storage lifecycle.

## Limits

We checked local operation with one Chromium browser and synthetic data. We did not establish customer demand, physical-device behavior, screen-reader conformance, broad browser compatibility or production deployment readiness. HTML-looking text remains literal in Markdown exports, which users should review before sharing or publishing. The question routing follows the selected solution form; it does not use an AI service. We did not inspect a production bundle for private database exclusion because the local tool has not reached that packaging step.

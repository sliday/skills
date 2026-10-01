# Local discovery companion

Use this skill when the user wants a guided discovery session they can pause, edit and resume. Run the bundled script from the client project:

```sh
python3 /path/to/prototyper/scripts/discovery.py
```

Open the loopback URL the script prints. The server binds to `127.0.0.1` on an available port. It requires Python 3 and uses only the standard library. It does not contact an AI service, fetch reference URLs, upload answers or install dependencies.

The default data location is `.prototype-discovery/discovery.sqlite3` beneath the current client project. Add `.prototype-discovery/` to that project's ignore rules before committing. This folder contains local answers, including drafts and skipped questions. Do not copy it into a public repository or the downloadable pack. Use `--data-dir /path/to/private-folder` to choose another location. The UI displays that location.

The interview covers the user, situation, job, current workaround, one flow, constraints, data, assumptions, cuts, failure states, design, stack, acceptance, feedback and handoff. Choosing Website, App, Service or Unsure adds two questions for that form. Changing the form retains inactive answers in the JSON record but excludes them from the active brief. The tool does not infer market demand from your answers.

Create or resume a project from the list. Drafts autosave after typing pauses. Use Save and continue to confirm an answer, Back to edit, and Skip for now to retain an unknown. Read the visible save status before closing the page. Delete removes the project and its answers from this local database.

## Portable exports and agent access

Export through the page or list projects from the terminal:

```sh
python3 /path/to/prototyper/scripts/discovery.py --list
python3 /path/to/prototyper/scripts/discovery.py --export PROJECT_UUID --output-dir ./prototype-brief
```

Both commands accept `--data-dir`. Export writes `discovery.json`, `PRD.md` and `BAR.md`. JSON includes question prompts, parent links, answer status and pack versions. PRD describes one flow, cuts, unknowns, data and failure states, design constraints and handoff. BAR separates machine proof from human review. These files work as a starting point for Slag or another development agent. This tool does not start Slag, configure keys or spend money.

Ask the user which exports they want to share. Inspect the files for confidential material before you give them to a team or agent. The tool leaves them on the user's computer.

`GET /health` reports version and data directory. The loopback API exposes project listing, individual state and exports. Browser writes require the process CSRF token from the served HTML and a loopback Host/Origin matching the current port. The server rejects oversized and malformed requests.

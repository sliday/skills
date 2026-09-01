---
name: agent-insights
description: "Use when analyzing development-agent session patterns across Claude, Codex, Gemini, Kimi, claude-mem, and Hermes without exporting raw transcripts. Generates a private aggregate-only HTML report of project concentration, work modes, correction loops, friction, and verification gaps."
version: 1.0.0
author: Sliday
license: MIT
triggers:
  - "agent insights"
  - "analyze my coding agent usage"
  - "how do I work with coding agents"
  - "where do my agent sessions go wrong"
  - "generate development session insights"
  - "/agent-insights"
tools:
  - terminal
  - read_file
mutating: true
---

# Agent Insights

## Contract

Generate a self-contained private HTML report from local development-agent metadata while keeping raw conversations out of the report and out of durable knowledge stores.

The report:

- analyzes a rolling window of locally available Claude, Codex, Gemini, Kimi, claude-mem, and Hermes activity;
- separates likely user-authored prompts from common forge, subagent, imported-session, command-wrapper, and system templates;
- reports project concentration, work modes, correction signals, friction signals, requested completion signals, and candidate workflow rules;
- writes only aggregate HTML and JSON under `~/.hermes/cache/agent-insights/` by default;
- complements token and cost telemetry rather than rebuilding it;
- labels heuristic evidence honestly and never treats generated summaries as verified outcomes.

A successful run is not merely an HTML file. The collector must complete, the report validator must pass, the generated JSON must contain no prompt bodies, and the operator must explain the main evidence limitations.

## 1. Choose the analysis window and sources

Default to 30 days unless the user specifies another window. A shorter window is useful for recent friction; a longer window is better for recurring patterns but increases alias and provenance noise.

Supported source selectors:

- `claude`: `~/.claude-mem/claude-mem.db`, when available;
- `codex`: `~/.codex/session_index.jsonl`, with detectable external imports excluded;
- `gemini`: recent artifact metadata under `~/.gemini/antigravity/brain/`;
- `kimi`: collapsed metadata from `~/.kimi/sessions/`;
- `hermes`: broad usage context from `~/.hermes/state.db`.

Missing sources are reported, not treated as failure. Source availability does not imply equivalent evidence quality.

## 2. Run the deterministic collector

Locate this skill's installed directory, then run:

```bash
python3 <skill-dir>/scripts/build_report.py --days 30
```

Restrict stores when requested:

```bash
python3 <skill-dir>/scripts/build_report.py \
  --days 90 \
  --sources claude,codex
```

Use `--open` only when a local GUI browser is appropriate. Use `--output` and `--json-output` to choose alternate private destinations.

## 3. Validate before interpreting

Run the built-in checks:

```bash
python3 <skill-dir>/scripts/build_report.py --self-test
python3 <skill-dir>/scripts/build_report.py \
  --check ~/.hermes/cache/agent-insights/report.html
```

Confirm all of the following:

1. the collector exited successfully;
2. the HTML contains all required sections;
3. the sensitive-pattern scan reports zero hits;
4. aggregate JSON contains counts and labels, not prompt bodies;
5. unavailable sources and parsing errors are visible;
6. project aliases and orchestration containers are not presented as a clean project ranking.

If the report renderer changes, inspect the existing rendered surface before editing, then verify rendered pixels after each meaningful visual change. Preserve unrelated accepted choices.

## 4. Interpret evidence conservatively

Use three confidence labels:

- **Observed:** a directly counted aggregate or source-coverage fact.
- **Inferred:** a repeated pattern supported by multiple sessions or projects but still dependent on heuristic authored-prompt filtering.
- **Not established:** model preference, productivity gain, psychological trait, project importance, actual release, or any other claim not independently verified.

Important boundaries:

- Requests are not outcomes. Words such as `test`, `deploy`, and `release` prove intent only.
- Frequency is not importance. Orchestration containers, retries, and aliases can dominate volume.
- Terse agent feedback is not evidence about human relationships or personality.
- Generated `next_steps`, plans, walkthroughs, and completion claims are not user commitments or independent proof.
- A successful command is not live read-back; tests are not visual evidence; screenshots are not behavioral proof.

## 5. Review candidate rules instead of auto-promoting them

The report may propose workflow experiments such as rendered verification, scoped diffs, a completion matrix, one integrating owner, or a harness earning test. Treat these as candidates, not canonical truths.

Promote a rule only when it is:

1. explicitly confirmed by the user, or repeated across independent periods and projects;
2. supported by user-authored evidence rather than system/import/subagent/generated text;
3. actionable enough to change future agent behavior;
4. manually reviewed for privacy and overgeneralization;
5. durable rather than a transient environment failure or one-off task narrative.

Keep each promotion cycle to a small set. Do not automatically patch personal memory, project documentation, or a knowledge base after every run.

## 6. Output report

Deliver:

1. the absolute HTML path;
2. the selected window and source coverage;
3. at most five high-signal findings;
4. observed versus inferred versus not-established labels;
5. missing or weak sources;
6. any candidate rules recommended for manual review.

## Privacy and provenance

- Never emit raw transcripts, tool outputs, credentials, private URLs, or prompt bodies.
- Show repository basenames, never full home-directory paths.
- Exact-text deduplicate claude-mem prompts before ranking.
- Exclude detectable Codex external imports.
- Collapse Kimi forge and retry sessions by normalized parent hash.
- Treat Gemini plans and walkthroughs as metadata coverage, not verified outcomes.
- Treat Hermes as broad usage context because it includes non-development sessions.
- Keep generated reports private even when they contain only aggregates; project labels and work patterns may still be sensitive.

## Verification checklist

- [ ] Correct time window and source selection used
- [ ] Self-test passed
- [ ] HTML validation passed
- [ ] Sensitive-pattern scan returned zero hits
- [ ] No prompt bodies or transcripts in HTML or JSON
- [ ] Missing sources disclosed
- [ ] Imported, generated, subagent, and retry traffic excluded where detectable
- [ ] Frequency not described as project importance or personality
- [ ] Completion requests not described as completed outcomes
- [ ] Candidate rules manually reviewed before durable promotion

## Anti-patterns

- Rebuilding token or cost analytics already supplied by the active harness.
- Treating orchestration containers, benchmark runs, or retry volume as real project interest.
- Treating generated summaries, `next_steps`, plans, or walkthroughs as user behavior or verified completion.
- Quoting sensitive prompts for color.
- Publishing the generated report or aggregate JSON.
- Automatically writing every recommendation into personal memory or a knowledge base.
- Hardening environment-dependent failures, negative tool claims, transient errors, or one-off task narratives into permanent skill rules.
- Turning monthly review into another dashboard-maintenance project.

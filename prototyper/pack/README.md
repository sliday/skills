# Prototyper

Companion to *Cows, Men, Paddocks. Things Have Changed (Again)* by Stas Kulesh. Build a usable proof of concept of your main user flows. Try mocked payments, messages and other supporting services, then hand your team the evidence and MVP launch work.

Copy this into your agent and replace the placeholder:

> Fetch and follow https://book.sliday.com/prototype/prompt.md. Use Prototyper to build a usable proof of concept of my main user flows. Mock supporting services unless a live integration is essential to the idea. Exercise the flows against a fixed acceptance bar, inspect the interface and leave a focused MVP handoff. My idea: [describe your idea].

If your agent cannot open links, paste [SKILL.md](../SKILL.md) and the relevant linked guides. A coding agent can build and run an artifact; a chat-only agent can prepare a simulation and implementation brief.

## Use the skill

Install the skill with the Vercel Skills CLI:

```sh
npx skills add sliday/skills --skill prototyper
```

Choose your agent and project scope. You can also copy this folder into your agent's project skill directory, preserving its resources. For Claude Code, install with `--agent claude-code`, then invoke `/prototyper`.

## Local discovery

From the client project, run `python3 /path/to/prototyper/scripts/discovery.py`. Open the printed loopback URL. Pause, edit and resume answers, or skip unknowns. The tool saves SQLite data under the project's `.prototype-discovery/` directory and displays its location. Keep that directory out of version control. Use `--data-dir` to choose another local folder.

Export JSON, `PRD.md` and `BAR.md` from the page, or use `--list` and `--export PROJECT_UUID --output-dir ./prototype-brief`. The tool makes no third-party requests. You choose whether to share the exports with a team or an agent.

## Follow your prototype

Run `python3 /path/to/prototyper/scripts/board.py` from the client project and open the printed address. Your local board shows what you can try, work in progress and decisions that need you. Open cards to see their nested tasks. A highlighted card asks for feedback; submit a choice or comment and the team can read it. Task work and answers persist in local SQLite. Use `--demo` to explore labelled examples in an empty board. Read [the progress-board guide](../references/progress-board.md) for agent updates and private data handling.

## Guides

- [Mindset](../references/mindset.md) and [scope](../references/scope.md): the user, main flows, assumptions and cuts.
- [Discovery](../references/discovery.md): local survey and portable exports.
- [Design](../references/design.md): hierarchy, type, fonts, mobile and accessible states.
- [Progress board](../references/progress-board.md): nested task cards, feedback and client-visible progress.
- [Build loop](../references/build-loop.md): fixed criteria, proof-bearing tasks, matched A/B artifacts and gap repairs.
- [Evidence](../references/evidence.md) and [handoff](../references/handoff.md): honest findings and the next team's starting point.
- [Optional extensions](extensions.md): DAUB, Harn, Matt Pocock workflows, PLEA, Slag, skills.sh and Google Fonts.

The loop continues until criteria pass, you stop it or an explicit budget ends. Record unresolved criteria. Real-user feedback, integration work and release checks remain separate from an agent's heuristic review. See [LICENSE](../LICENSE).

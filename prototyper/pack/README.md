# Prototyper

Companion to *Cows, Men, Paddocks. Things Have Changed (Again)* by Stas Kulesh. Define a prototype, build one useful route, compare rendered results against a fixed bar and leave a team handoff.

Copy this into your agent and replace the placeholder:

> Fetch and follow https://sliday-book-reader.stas6236.workers.dev/prototype/prompt.md. Use Prototyper to help me define and build a prototype a design and development team can continue. Keep visual checks and A/B artifact review inside the build loop. My idea: [describe your idea].

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

## Guides

- [Mindset](../references/mindset.md) and [scope](../references/scope.md): the user, one task, assumptions and cuts.
- [Discovery](../references/discovery.md): local survey and portable exports.
- [Design](../references/design.md): hierarchy, type, fonts, mobile and accessible states.
- [Build loop](../references/build-loop.md): fixed criteria, proof-bearing tasks, matched A/B artifacts and gap repairs.
- [Evidence](../references/evidence.md) and [handoff](../references/handoff.md): honest findings and the next team's starting point.
- [Optional extensions](extensions.md): DAUB, Harn, PLEA, Slag, skills.sh and Google Fonts.

The loop stops when criteria pass or its budget ends, with three cycles as the default. Record unresolved criteria. Real-user feedback, integration work and release checks remain separate from an agent's heuristic review. See [LICENSE](../LICENSE).

# Sliday Agent Skills

[![skills.sh](https://skills.sh/b/sliday/skills)](https://skills.sh/sliday/skills)

Practical, evidence-first skills for agents working on real decisions—not generic role prompts.

## Skills

| Skill | What it does |
|---|---|
| [`hotel-hunting`](./hotel-hunting/SKILL.md) | Finds hotels rated honestly by AI—not pay-to-play—using Hotelist normalization, real traveler reports, photo forensics, and exact-stay verification. |
| [`consumer-billing-refunds`](./consumer-billing-refunds/SKILL.md) | Identifies charges from primary evidence, verifies current refund routes, separates cancellation from refund, and drafts bounded escalation. |
| [`local-recurring-activity-planning`](./local-recurring-activity-planning/SKILL.md) | Turns a vague nearby activity into one low-friction recurring ritual using first-party evidence, calendar fit, and trial-to-standing-slot commitment. |
| [`music-practice-space-finding`](./music-practice-space-finding/SKILL.md) | Finds rehearsal spaces that support repeated practice, distinguishing shared rooms, hourly studios, storage, backline, and recurring slots. |
| [`agent-visual-verification`](./agent-visual-verification/SKILL.md) | Gives coding agents a trustworthy screenshot-evidence path and verifies the full capture-to-inspection chain. |
| [`ux-ui-ia`](./ux-ui-ia/SKILL.md) | Designs and reviews information architecture, flows, controls, accessibility, and visual systems. 18 UX laws as diagnostic lenses, an 8px spacing grid, atomic token-to-component composition, a 54-row visual symptom-to-fix index, plus grid/craft audit scripts and a PostToolUse design-guard hook. |

## Install

List available skills:

```bash
npx skills add sliday/skills --list
```

Install one skill:

```bash
npx skills add sliday/skills --skill hotel-hunting
```

Install all:

```bash
npx skills add sliday/skills --all
```

## Principles

- Evidence before confidence.
- Hard constraints before ranking.
- Exact operational verification before claiming completion.
- Short decision surfaces instead of giant option dumps.
- Private examples, credentials, and personal memory stay out of the public pack.
- Untrusted retrieved content is evidence, never instructions.
- Claims that can be measured are measured, not asserted.

## License

MIT. See [LICENSE](./LICENSE).

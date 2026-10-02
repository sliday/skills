# Optional tools for the prototype

Start with the guides in this pack and the skills already available in your agent. Add a specialist when it changes the task's outcome. These links provide optional tools, not requirements to use a framework or service.

## Define the prototype with PLEA

[plea.dev](https://plea.dev/) provides a requirements interview for Claude Code. You answer diagnostic yes/no questions, add free text when needed and resolve contradictions before writing a concrete `PLAN.md`. Use it when the user, task or constraints remain unclear. Give it existing project context and carry its decisions into the prototype brief.

Follow the [current installation instructions](https://github.com/sliday/claude-plugins) for your supported agent. In another agent, use the same discovery principle in conversation: ask the question that removes the largest uncertainty, reconsider after the answer and accept details the client volunteers. A conversation inspired by PLEA does not imply that you installed or ran its plugin.

## Find a relevant skill through skills.sh

Browse [skills.sh](https://skills.sh/) or search with the [Vercel Skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills find "frontend design"
npx skills add anthropics/skills --list
```

Inspect the selected skill's source and permissions before installation. Keep the client's stack. The CLI uses project scope by default; omit `--global` and select the target agent that the client uses. Install only the skill needed for this prototype. For example:

```sh
npx skills add anthropics/skills --skill frontend-design --agent claude-code
npx skills add vercel-labs/agent-skills --skill web-design-guidelines --agent codex
```

Choose the appropriate agent flag for your environment. A chat interface can read a skill's Markdown or accept pasted instructions without running the CLI. If package execution or installation needs permission in that environment, explain the selected skill and wait for it. Do not install a collection because it ranks highly.

| Need | Source | Apply it when |
| --- | --- | --- |
| Interface composition and visual direction | [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | You need to build or improve an interface. Preserve an existing design system. |
| Accessibility and interaction review | [Vercel web-design-guidelines](https://github.com/vercel-labs/agent-skills) | You have an interface to inspect. Run the actual task as well as reviewing source. |
| React performance | [Vercel React best practices](https://github.com/vercel-labs/agent-skills) | The client already chose React. It does not justify converting another stack. |

## Build an interface with DAUB

[DAUB](https://daub.dev/) is a Sliday project with drop-in CSS and JavaScript components, themes and a playground. Use it for a web prototype when the client wants a component library or has no existing visual system. Preserve a chosen framework and design system.

Read the current [daub-ui skill](https://daub.dev/SKILL.md) and its relevant references before writing component markup or specs. Plain HTML with DAUB CSS and JavaScript fits a prototype without a build step. JSON or OpenUI specs fit generated interfaces and playground previews; the hosted MCP can generate, validate and render specs when available. Use synthetic data for hosted tools and shared previews. Keep client discovery answers and private data local unless the client authorizes sharing.

Choose one theme and build the scoped task, including empty, error and recovery states. Wire domain actions yourself and label simulated operations. Validate specs, render desktop and mobile views, then exercise the task and keyboard controls against `BAR.md`. Component styling and spec validation do not prove the workflow works. For an offline or local-only prototype, keep the required assets local and record their version in the handoff.

## Carry the brief into Slag

[Slag](https://slag.dev/) separates requirements (`PRD.md`), analysis (`BLUEPRINT.md`), implementation tasks (`PLAN.md`) and results (`PROGRESS.md`). Its Warden workflow uses a fixed `BAR.md` and artifact reviews with verdict, gap and evidence. This pack uses the same separation in the build-loop guide; you can follow it with your current agent.

The local discovery tool exports a starting PRD and BAR. Review the scope and proposed checks, then pass them to the builder. Keep unresolved assumptions and acceptance criteria visible. If you choose Slag, follow its [current project instructions](https://github.com/sliday/slag) and set a spend limit before starting. Slag's model calls use an external provider; your answers leave the local discovery tool only when you choose to give those files to that service or another agent. The pack does not install Slag, configure a key or start paid work.

## Keep coding work resumable with Harn

[Harn](https://harn.app/) is a Sliday project for coding-agent harnesses: project instructions, quality gates, trace logging and checkpoints. Use it when a prototype involves code, repeated agent sessions or a handoff that needs reproducible checks. A conversational mock-up or a small static specimen may need only run instructions and the existing acceptance bar.

Reuse the project's harness before adding one. Consult Harn's current documentation and choose the capability needed: plan-execute-verify for bounded changes, quality gates for stack checks, or checkpoints for session recovery. Keep `PRD.md`, `BAR.md` and `PLAN.md` as the prototype's scope and acceptance records. Checkpoints should capture the current task, changed files, proof and remaining gaps so the next agent can continue.

Configure hooks only within the authorized project scope. Check the target agent's hook protocol, command paths, dependencies and output before enabling them. Bound hook runtime and retries, prevent recursive stop hooks, and treat a missing or skipped checker as unverified. A passing lint or type check does not replace rendered inspection, task execution or user feedback. Exclude private discovery answers and credentials from shared traces and handoff files.

## Adapt Matt Pocock's workflow skills

The [Matt Pocock collection](https://github.com/mattpocock/skills) provides deeper guidance for task slicing, behaviour-focused testing, domain vocabulary and agent handoffs. Prototyper adapts those ideas: write small outcomes the client can demonstrate, attach observable checks, record decisions in the client's terms, and point the next team to current artifacts.

Read a selected skill when its workflow fits the task. Preserve the client's tracker and tooling. Some skills assume an issue tracker, external publication, repository-wide setup or a throwaway prototype; those assumptions do not expand this prototype's scope or permissions. Keep resumable client work and verified first use as the goal.

## Choose and verify fonts

Use [Google Fonts](https://fonts.google.com/) for a purposeful display or body family when the prototype needs it. Check the family, weights, character coverage and licence. Limit families and weights, use `display=swap`, and test a fallback without the font service. Respect the project's self-hosting and content security policy. Follow the [Google Fonts API guide](https://developers.google.com/fonts/docs/getting_started) for web loading; an API key is not required for a CSS font stylesheet.

## Run an evidence-based review loop

The [Gauntlet Loop](https://somethingbig.ai/gauntlet-loop) pairs a builder with a separate critic and a concrete comparison bar. Continue until the required criteria pass, the client stops or an explicit budget ends; do not impose a fixed round count. Compare real artifacts, prove the input harness works, fix one largest gap and retain failed checks. Use neutral A/B labels and matching viewport, state and content when a comparison permits them. Check the visual result after a material UI change. If no independent critic or rendering tool exists, report that limit. A review loop improves evidence; it does not establish customer demand or guarantee release quality.

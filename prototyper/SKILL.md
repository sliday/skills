---
name: prototyper
description: Use when you need to build a usable proof of concept of the main user flows, with interactive mocks for supporting services, observable acceptance checks and a focused MVP handoff.
license: MIT
metadata:
  author: Sliday
  version: "1.1.0"
  mutating: "true"
---

# Prototyper

Help the client create something a user can try and a team can continue. Keep their chosen stack, scope and visual direction. Match the artifact to your tools: runnable prototype, interactive preview, or a labelled simulation and build brief. Do not stop at planning when you can build the requested artifact.

## Deliver day-one use

Choose the first useful outcome the client can complete: book a slot, prepare a quote, review an invoice or finish another concrete task. Ask enough to identify the user, outcome and constraints, then build a first working route. Offer the resumable survey when it helps; do not require the client to finish it before you can start. Record reversible assumptions and revisit them after trying the artifact.

Give the client a verified way to open the prototype, a sample task and a visible result. Explain what persists, what resets and which actions use live services or simulations. Prefer a local or browser-only route when it meets the task without account setup. Use a manual step when it provides a usable outcome within scope, and include that step in the instructions. Show the first working route before expanding scope or adding tooling.

## Mock supporting services

Build the main user flows through to observable results. Default to mocks for supporting services unless the client requests a live integration or the risky assumption depends on that integration. A checkout can simulate approval, decline and retry without Stripe. An email flow can show a message preview or local outbox without sending mail. Let the user interact with these states; a dead button does not demonstrate the flow.

Label simulated effects where the user encounters them: no charge, no email sent, sample account or local-only save. A PoC can meet its acceptance bar with these mocks. For an MVP launch, identify which dependencies must become real to deliver the promised user outcome and which can remain simulated or manual. Record the remaining integration work without expanding the current prototype into a full product.

## Define the task

Read [mindset](references/mindset.md) to identify the user, situation, current workaround and risky assumption. Ask only for information that changes the prototype. Accept free text, reconsider after each answer and surface contradictions. Follow the client's request to proceed with reversible assumptions when appropriate.

For a resumable survey, read [local discovery](references/discovery.md) and run `scripts/discovery.py` from the client project. It saves answers in local SQLite and exports JSON, `PRD.md` and `BAR.md`. It uses no AI provider or remote database. A chat-only agent can perform discovery in conversation. PLEA remains an optional requirements interview; this survey adapts its discovery principles rather than claiming to run that plugin.

Write one direction: for this user in this situation, help them finish this task; test this assumption. Agree the small set of main flows needed for that task, and name exclusions. Map each flow as role → action → observable result. Build one end-to-end route as the first increment, then include the agreed supporting flows before accepting the PoC. Use [scope](references/scope.md), including its worked example when useful. A prototype can test understanding and behaviour; it cannot establish demand or production reliability by itself.

## Build through the quality loop

Read [build-loop](references/build-loop.md) before implementation. Keep it central to the work:

1. Write scoped `PRD.md`, a fixed `BAR.md` with observable criterion IDs, and small `PLAN.md` tasks with proof requirements.
2. Build and exercise the critical task with synthetic data and relevant failure/recovery. Label live, local and simulated operations. Prove the test harness changes state.
3. Render and inspect after a material UI change. Use [design](references/design.md) for typography, Google Fonts, accessible states and mobile behaviour. Check motion through interaction or video when a still cannot establish the criterion.
4. When a meaningful comparator exists, show matched reference/previous and current artifacts under neutral A/B labels to a separate critic. Give the authorized critic the actual artifact, task and bar without builder history. Otherwise inspect directly against the bar and record the comparison limit. For nonvisual solutions, inspect actual outputs and task execution.
5. Record `VERDICT`, the largest `GAP` and concrete `EVIDENCE`. Repair that gap and rerun affected checks against the same bar. Keep failed and untested criteria visible.

Continue until required criteria pass, the client stops, or an explicit budget ends. Do not impose a fixed round count or call an unfinished result accepted. Stop on a quota/rate-limit error or three attempts at the same tool failure. Label self-review when a separate critic is unavailable and mark checks untested when you cannot execute them. An agent's A/B preference is a heuristic comparison, not a participant experiment.

## Show progress to the client

Use [the progress board](references/progress-board.md) when the client wants a view of development. It runs locally and shows outcome cards in Planned, Building, Ready to try and Done, with child boards, breadcrumbs and highlighted feedback requests. Keep card statuses aligned with `PLAN.md` and verified evidence. Read client answers before advancing dependent work; retain open questions and failed checks. Use the bundled board to start without accounts or hosting.

## Run the bundled evals

Read [evals](evals/README.md). Run the bundled behaviour checks after changing discovery or progress-board code. Check the rendered board with its browser eval when you change UI behaviour. Keep synthetic evaluation projects separate from client data, retain failed evidence and mark unavailable browser checks untested. A passing helper-tool eval does not prove the client's prototype meets its own `BAR.md`.

## Leave a usable handoff

Use [evidence](references/evidence.md) to separate verified behaviour, observed user feedback, reported feedback and assumptions. Use [handoff](references/handoff.md) for run instructions, screens/states, data boundaries, decisions, cuts and the next team's work. State “No user feedback collected” when true.

Load [optional extensions](pack/extensions.md) only when DAUB, Harn, PLEA, Slag, skills.sh or specialist design guidance fits the task. Reuse available skills before installing more. Do not start paid services, change global configuration, publish externally or contact participants solely because this skill mentions those options. Keep discovery data on the client's computer until they choose to share it.

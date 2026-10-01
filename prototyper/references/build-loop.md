# Build, inspect, repair

Use this as the central workflow for a website, app or other solution. Preserve the client's stack and artifact choice. Start with a working critical task, then improve it against observable criteria. Adapt Slag's proof-bearing tasks and fresh-context critic alongside the gauntlet's rendered comparisons; neither tool or service is required.

## Set the target

Write `PRD.md`: user, job, risky assumption, critical end-to-end task, constraints, synthetic data, live/mocked boundaries and scope cuts. With no file tools, provide the same content as a copyable section.

Write `BAR.md` before building: stable criterion IDs, observable pass conditions, how to check each and the necessary device, viewport or execution environment. Include task completion, relevant failure/recovery, honest boundaries and visual/accessibility requirements. For day-one use, check that the client can open the artifact from the supplied instructions, complete the sample task and identify its result. Verify the stated save, reload or reset behavior when the task depends on it. Hold the bar fixed across cycles; record an explicit client scope change before revising it. Do not lower criteria to declare success.

Write `PLAN.md` with small tasks, dependencies and evidence each task must produce. File existence or a successful build proves only that condition. Critical interactions need exercised state transitions; visual criteria need rendered inspection.

Agree a budget or use a default maximum of three review/repair cycles. Record the limit, available tools and reviewer access. A cycle count does not establish quality.

## Repeat against the same bar

1. Build the smallest critical flow. Run it with realistic synthetic data and the relevant failure case. Verify the harness with an input and an observable state change.
2. Render and inspect after each material UI change, including state or responsive-layout changes. Use agreed sizes and states. For motion or timing, inspect video or interact with the artifact; a still image cannot prove that behavior. For a nonvisual artifact, inspect its actual outputs and execution instead.
3. Give an authorized independent critic the PRD, fixed BAR and access to the actual artifact or captured evidence. Withhold builder history, effort and intended verdict. The critic should run or inspect the task using available tools. Label review from supplied evidence and its limits. If independence is unavailable, label self-review; if execution is unavailable, mark affected criteria untested.
4. Compare the current version against a supplied reference or previous version when a comparison can resolve a visual decision. Match viewport, content, state and pose; use neutral A/B labels and hide version identity from the critic. Record differences and criterion-based reasons, including ties. If no comparator or blind setup exists, state that limit and perform a direct check. An AI A/B preference is a heuristic comparison, not a human conversion experiment. Real user A/B testing needs actual participants, assignment and recorded outcomes.
5. Record `VERDICT: pass|fail|untested`, `GAP: <largest unresolved criterion gap>` and `EVIDENCE: <artifact/version, criterion IDs, steps and observations>`. Pass requires evidence for every required criterion. Missing checks or an unreadable verdict cannot pass. Keep other known gaps in the ledger.
6. Repair the largest gap within scope. Re-run the changed task and affected regression paths, render affected states again, then request the next verdict against the same BAR.

Stop when the required criteria pass, the agreed budget ends, the client stops, or a quota/rate-limit error occurs. Stop after three attempts at the same tool error. At budget exhaustion, hand off the actual result with failed and untested criteria; do not describe it as accepted. Extending a budget requires client agreement.

## Hand off the evidence

Keep a compact cycle ledger with criterion status, artifact version, comparison mapping, screenshot/video or execution references, reviewer type, repairs and remaining gaps. Separate verified behavior, observed user feedback, reported results and assumptions. Use [evidence.md](evidence.md) for feedback and [handoff.md](handoff.md) for packaging. Without execution tools, deliver PRD/BAR/PLAN and a simulation or specification, with explicit checks the receiving team must run.

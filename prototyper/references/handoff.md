# Leave a usable starting point

Inspect the artifact and existing instructions before preparing the handoff. Preserve the client's stack, files and ownership choices. Deliver the runnable artifact alongside a concise brief, not a replacement implementation.

Use [../assets/handoff-template.md](../assets/handoff-template.md) for the brief. Fill it with actual project details; remove unused sections. Do not fabricate links, screenshots, commands or verification. Mark unknowns with their next check.

Include the minimum a receiving team needs:

- User, task, risky assumption and current scope.
- Artifact location, requirements and exact launch instructions you verified. Include a first-use walkthrough with a sample task, expected result, synthetic-data setup and reset if relevant.
- Key screens or steps, with screenshots only when you captured them. Otherwise describe them as a screen inventory.
- Live and mocked boundaries, persistence behavior and inactive controls.
- Decisions worth retaining, known gaps and prioritized next cuts.
- PRD, fixed BAR, proof-bearing PLAN and cycle ledger from build-loop guide, with criterion status, artifact evidence and reviewer type.
- Verification performed and feedback gathered, with failures and untested cases; label agent A/B comparisons separately from actual user experiments.

Run the primary task from the supplied instructions when tools permit. Check a relevant failure and recovery path. Ensure the package includes referenced assets and excludes secrets, private customer data, local absolute paths and machine-specific credentials. These checks protect the artifact; they do not authorize changing global configuration or publishing externally.

In a conversational interface with no file tools, return a copyable handoff brief, screen/state specification and code or instructions the client can transfer. State that the receiving team must create and run the artifact. Do not call a brief a runnable package or claim that code has passed checks you could not execute.

At a budget stop, list the remaining failed or untested BAR criteria and the next repair; do not mark acceptance complete.

Identify the first decision for the next team, rather than presenting a prototype as a production specification. End with a clear status: runnable and checked in the stated environment, runnable but unverified, or brief/simulation only. Keep any deployment, paid integration or production hardening outside this handoff unless the client requested it.

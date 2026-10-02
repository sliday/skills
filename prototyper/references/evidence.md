# Learn without manufacturing evidence

Identify the assumption and the task the prototype can test. Inspect the artifact or supplied screens before writing a feedback exercise. If you cannot open or run it, state that limit and work from the client's description.

Write a neutral task with a concrete starting situation and desired result. Do not reveal the interface's intended path in the instructions. Ask the participant to try it before you explain it. Let the client choose whom to involve; do not contact people on their behalf without authorization.

For a tool-verified task, record the starting state, the user action and the resulting state. Verify persistence when the task promises it, and check console or server errors when available. Keep each run's sample data, server and evidence paths separate from client data. Retain the evidence after stopping the test server.

Capture the context that makes feedback interpretable: participant's relevant experience, version tested, device, task, assistance given and whether data was synthetic. Keep identifying information out of the handoff unless the participant agreed to its use.

Separate four evidence types:

- **Observed:** what a participant did or said during an actual session.
- **Verified:** behavior you exercised with available tools, including steps and result.
- **Reported:** feedback the client supplied that you did not witness.
- **Assumed:** hypotheses, predictions and simulated reactions.

Never turn an agent persona or a conversational walkthrough into real-user evidence. Label a heuristic review as such. Do not invent quotes, counts, completion rates or test results. An inspection of source code does not verify rendered behavior; a working mock does not verify its future integration.

## Quality loop and A/B evidence

Use build-loop guide as the central build/review/repair workflow: PRD, fixed BAR, proof-bearing PLAN, actual artifact review and the largest-gap repair. Run visual checks after material interface changes. Continue until required criteria pass, the client stops or an explicit budget ends. Preserve failed and untested criteria at a stop.

For visual comparisons, use neutral A/B labels and matched viewport, state and content. Compare the current version with a reference or previous version when available. Keep version identity and builder history from an authorized independent critic. Report the criterion and artifact evidence behind a preference. Label self-review, supplied-evidence review and nonblind comparisons. An agent's preference does not establish human conversion, demand or usability outcomes.

For a real user A/B experiment, define the hypothesis, variants, assignment, task, outcome and stopping rule before collecting results. Report actual participants and observations, assistance and uncertainty. Do not invent significance or claim causality from an informal preference session. If you lack participants or authorization, prepare the protocol and say that no user experiment ran.

Return a short evidence record for each material finding: task step, evidence type, observation, consequence, proposed cut or change and how to check it. Keep failed attempts and contradictory feedback visible. If nobody has tested the prototype, say “No user feedback collected” and provide the task script.

Recommend the next action against the risky assumption: cut an extra, repair a blocking step, clarify a boundary or test with a relevant user. Distinguish “ready for another prototype test” from “ready for production”. Stop after repeated tool failures or a quota error; report the unverified checks instead of retrying indefinitely.

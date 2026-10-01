# Make one task work

Start from the client's user, job and risky assumption. If they have not chosen them, extract them from the request and mark assumptions. Keep their stack, existing project and scope choices. Use the simplest available implementation that lets someone finish the task.

If the product remains unclear, offer a short discovery conversation inspired by PLEA: ask the next question that removes the most uncertainty about the user, job, constraints, risky assumption or artifact. Use a yes/no question when it settles a decision; allow a free response for context you might have missed. Stop discovery when you have enough to build the first task or when the client says to proceed. Using an installed PLEA skill or plea.dev is optional; keep the same discovery available in plain conversation without an account, service or installation. Record decisions and remaining assumptions, then build.

Use build-loop guide to turn this scope into PRD.md, a fixed BAR.md and a PLAN.md of proof-bearing tasks. Keep those artifacts as copyable sections when file tools are unavailable. Build and repair against that bar until criteria pass or the agreed budget ends.

Define the journey from entry to an observable result. Include the screens, state changes and data needed along that route. Use realistic synthetic records, including a case that is missing data or fails validation. Identify these records as synthetic.

Build the primary route plus the failure states that affect the task: an empty starting state, invalid input, a failed operation and a retry or recovery. Include loading when an operation has a wait. Check keyboard operation, labels and clear errors. Keep important controls functional; label any decorative or inactive control.

Remove features that do not test the assumption or complete the route. Put useful extras in a short “later” list, without implementing them. Account creation, payments and integrations belong in the prototype only when the task needs them.

Label each boundary: live service, local persistence, simulated response or static placeholder. If you simulate a payment, message or upload, show that nothing leaves the prototype. Do not claim a mocked route proves the live integration works.

With execution tools, run the artifact and exercise the journey before reporting success. With conversation-only tools, provide an interactive screen simulation and a concise build brief, including inputs, outputs and state transitions. Do not claim that you created files, executed code or deployed anything unless you did.

Use [worked-example.md](worked-example.md) when the client needs a concrete model for choosing cuts and failure states. Adapt its reasoning, not its domain or stack.

Finish with the artifact or simulation, how to try it, what works, what you mocked and the next cut that would simplify it.

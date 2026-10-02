# Show the client their prototype

Use the bundled progress board when the client wants to follow development, try working routes or answer decisions without reading engineering notes. A small task may need only a first-use walkthrough. Keep the board proportional to the work.

## Start locally

When you can run local tools, start the board for the client and give them a clickable address with a short instruction: open a card to see the work, or choose Needs you to answer a question. Keep setup commands in the team handoff.

Run from the client's project:

```sh
python3 /path/to/prototyper/scripts/board.py
```

Open the printed address. The board runs on the client's computer, without accounts or external requests. It starts empty. `--demo` adds labelled synthetic examples only to an empty board; demo tasks do not represent completed client work.

The board saves task state and client responses in `.prototype-progress/`. Add that directory to the client project's ignore rules before committing. `--data-dir` selects a different private directory. A local address works on the computer running the server; it does not give another person or phone remote access. A hosted client portal requires a separate access and deployment plan.

## Make cards about outcomes

Use the same scoped tasks as `PLAN.md`, written in the client's language. “Save a quote and reopen it” provides a clearer card than “Add persistence”. Put concrete task steps inside an outcome card; nest further when the work needs it. The board shows one level at a time and uses breadcrumbs to return to ancestors. The local tool accepts up to 1,000 cards and 64 nesting levels; keep the structure shallow enough for the client to follow.

Use Planned, Building, Ready to try and Done as work states. Mark Ready to try when the client has a working route and instructions. Mark Done when the task's required checks pass and attach the proof. An answered design question does not complete the implementation. Parent and child statuses remain explicit; a ready child does not prove its entire parent works.

Attach concise evidence and keep live, local and simulated actions visible. Add a complete HTTP or HTTPS proof URL as its own evidence entry to give the client a link they can open. Keep credentials out of URLs. Set a prototype link only when a runnable artifact exists. Record its limitations in the summary and handoff. Do not invent a percentage, a delivery date or activity to make the board look busy.

## Ask for a decision where it matters

A feedback request includes a concrete question, why it affects the task, and suggested choices when useful. The client may choose an option, write a comment or do both. Unanswered requests highlight their card and its ancestors; the Needs you filter finds requests across the tree.

After a client submits, the board records their answer and shows that the team must review it. Read the saved answer before continuing dependent work. Apply the decision to the relevant task, scope and acceptance records. Preserve prior decisions when a question changes. Keep unrelated tasks moving.

## Agent updates

Prepare a board JSON document using [the example](../assets/board-example.json). Apply it and export the current state:

```sh
python3 /path/to/prototyper/scripts/board.py --apply ./prototype-board.json
python3 /path/to/prototyper/scripts/board.py --export ./prototype-board-current.json
```

Both commands accept `--data-dir`. Export current state before revising it so you can read client answers. Apply validates task IDs and parent relationships. Preserve stable task IDs for the same work. The server retains saved client answers when an agent reapplies the same question; it records history when the question, choices or decision conditions change. A changed condition needs a new answer. Keep the complete portable board under 2 MiB; the server rejects an update that exceeds that limit without discarding saved decisions.

Update the board after a demonstrated milestone, a scope change or a new decision. The browser refreshes task state while the server runs. Check that the client sees the update and can follow the latest first-use instructions. At a stop, leave failed checks and open questions visible.

Keep exported board data private until the client chooses to share it. Do not include credentials, real customer records or confidential discovery answers in cards, proof text or prototype links.

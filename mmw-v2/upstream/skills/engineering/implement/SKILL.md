---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

Implement the work described by the user in the spec or tickets.

Before writing any code, read yourself in: the ticket in full, comments included; then follow its **Parent** to the spec and read that in full; then every prototype and research artifact linked from the spec's **Sources**, each through to its conclusion; then the ADRs and the domain glossary covering the area you're touching. Then say in one sentence which **seam** this ticket is tested at, and start.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

## Finishing a ticket

The ticket is the unit of work, and it is not done until it is closed. Steps, in order:

1. **Open the ticket state file.** Before the first edit, write `.mmw-ticket-state.json` at the worktree root (it is gitignored): `{"ticket": <number>, "branch": "ticket/<number>-<slug>", "gates": [...]}`. One entry per acceptance criterion, in ticket order: `{"text": "<criterion verbatim>", "kind": "check" | "manual", "check": "<CHECK command>" | null, "expect": "<EXPECT marker>" | null, "manual": "<adjudicator>" | null, "checked": false, "evidence": null}`. The completion hook reads this file; it stays until the ticket is closed.
2. **Implement.**
3. **Self-check.** Run the `self-check` skill over your own output before touching a gate.
4. **Run every gate, one at a time.** A runnable gate passes only on both conditions: exit code 0 and the `EXPECT:` marker in the output. When it passes, tick the criterion in the ticket body, add an `EVIDENCE:` line directly after its `EXPECT:` line holding the smallest decisive slice of the output, and set that gate's `checked: true` and `evidence` in the state file. A manual gate is not yours to tick: leave it unchecked and name its adjudicator in your final report. A ticked box without evidence counts as unticked.
5. **Commit**, message referencing the ticket (`#<number>`), so a later review can find the spec through the ticket.
6. **Review.** Use /code-review on the committed work; fix what it finds and commit again.
7. **Push the ticket branch** `ticket/<number>-<slug>`.
8. **Open the PR**, body linking the ticket.
9. **Close the ticket.** Closing releases every ticket this one blocks; the verifier's verdict is recorded on the ticket by whoever dispatched you, not by you.

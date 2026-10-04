---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use when something has to be cut out of a ticket, and when a batch is about to be published.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and posts the outcome on the ticket as an event.

The ticket is the only state. Every run reads it fresh, writes its events, and carries nothing to the next run. Every comment it posts is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block, which is the only part any program reads.

A criterion names an oracle by its bare name (`story-parity.py …`); `python3 scripts/verify-ticket.py` puts the `ui-acceptance` skill's `scripts/` on the `PATH` of the shell that runs a `CHECK:`, so an oracle run by hand needs that directory on `PATH`.

What a ticket holds, and how each acceptance criterion is written, is [references/ticket-format.md](references/ticket-format.md). Cutting a piece of work out of a ticket into a child issue is [references/sub-issues.md](references/sub-issues.md); checking a batch of tickets before it is published or run is [references/linting.md](references/linting.md).

## ABANDON lines

A criterion that will not pass gets an `ABANDON: AC<n> <kind> <reason>` line, flush left under that criterion in the closing-comment draft, and `--closeout` branches on its kind:

- `failed`: it ran and did not pass, after as many rounds as the worker judged worth spending, or it still failed after the review's fixes or in the final run. The reason says what each round tried; the closeout counts no rounds, so that line is the whole record of the trying.
- `stuck`: it will not start, or cannot be done within the task: a `CHECK:` that will not run, a missing credential or device. The reason names the routes tried, or points at the sub-issue that records them. A human step, or a product that cannot be reached while it runs, is not `stuck`: rules 3 and 4 of the `ui-acceptance` skill's **Five rules while the product is running** route it.
- `decision`: both options are legal and neither the ticket nor the spec says which. The reason holds the question, the options and the default when nobody answers, and a `decision` sub-issue is opened beside it ([references/sub-issues.md](references/sub-issues.md)). A difference in the interface never goes here.

Any `failed` or `stuck` makes the whole ticket `HANDOFF REQUIRED`. `decision` does not: its sub-issue is already open, and the rest all passing is still `ALL MET`.

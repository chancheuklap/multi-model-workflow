---
name: verify-ticket
description: Run a ticket's acceptance criteria and post the verdict back to the ticket. Use when finishing a ticket, when re-verifying someone else's finished ticket, or when auditing how a freshly written ticket's criteria are worded.
---

# Verify ticket

Each acceptance criterion on the ticket carries a `CHECK:` command and the `EXPECT:`
string a passing run prints. This skill runs them and writes the verdict back as one
comment. Every run reads the ticket fresh; there is no state to carry between runs.

## The engine

`scripts/verify-ticket.py`, next to this file. Resolve its absolute path once. Every
command below is written `<engine> <ticket>` and means:

```bash
python3 /absolute/path/to/scripts/verify-ticket.py <ticket>
```

## The three jobs

| Command | When | What lands |
| --- | --- | --- |
| `<engine> <n>` | You finished the work on ticket `<n>` | A comment whose first line is `self-run`: every criterion ticked or not, with the evidence the engine recorded |
| `<engine> <n> --reverify` | You are re-verifying a ticket someone else just finished | A comment whose first line is `reverify`. Criteria the last run ticked are run again, not trusted |
| `<engine> <n> --lint` | You just wrote the ticket and want its criteria audited | Findings printed to your terminal. No `CHECK:` runs and no comment is posted |

`--reverify` re-runs what the newest `self-run` comment ticked, so it belongs after one.
On a ticket with no such comment it behaves like a plain run.

`--timeout <seconds>` raises the per-`CHECK` limit when one of them is slow.

Exit code: 0 every criterion met, 1 something unmet or abandoned, 2 the ticket could not
be read or the run could not start.

## What it decides, and what it leaves to you

A criterion passes only when its `CHECK` exits 0 **and** its output matches `EXPECT`.
Expected text in the output of a failed process is still a failure. A criterion written
with `MANUAL:` instead of `CHECK:`/`EXPECT:` is never run and never ticked by the engine.

The engine reads the ticket and writes one comment. The ticket body, the `CHECK` commands
and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment
saying what is wrong with it, then edit the criterion and run again.

The comment ends with **Outside Owns**: files this branch changed that no `## Owns` glob
covers. That list is something to explain in the closing comment, not a verdict.

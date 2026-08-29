---
name: verify-ticket
description: Run a ticket's acceptance criteria, judge each one by exit code and expected output, and post the result back to the ticket as a comment. Use when finishing a ticket, when re-verifying someone else's finished ticket, or when auditing how a freshly written ticket's criteria are worded.
---

# Verify ticket

The ticket carries its own acceptance criteria — each one a `CHECK:` command and the
`EXPECT:` string only a passing run prints. This skill runs them and writes the verdict
back to the ticket. Nothing is judged by hand and nothing is cached: every run reads the
ticket fresh and leaves one comment behind.

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
| `<engine> <n> --reverify` | You are re-verifying someone else's finished ticket | A comment whose first line is `reverify`. Criteria the last run ticked are run again, not trusted |
| `<engine> <n> --lint` | You just wrote the ticket and want its criteria audited | Findings printed to your terminal. No `CHECK:` runs and no comment is posted |

`--timeout <seconds>` raises the per-`CHECK` limit when one of them is slow.

Exit code: 0 every criterion met, 1 something unmet or abandoned, 2 the ticket could not
be read or the run could not start.

## What it decides, and what it leaves to you

A criterion passes only when its `CHECK` exits 0 **and** its output matches `EXPECT`.
Expected text in the output of a failed process is still a failure. A criterion written
with `MANUAL:` instead of `CHECK:`/`EXPECT:` is never run and never ticked by the engine.

The engine never edits the ticket body, never rewrites a `CHECK` command, and never
decides what a criterion means. When a `CHECK` is wrong, say so on the ticket and fix the
ticket — do not work around it by running something else.

The comment also lists **Outside Owns**: files this branch changed that no `## Owns` glob
covers. An entry there is not a failure; it is something to explain in the closing comment.

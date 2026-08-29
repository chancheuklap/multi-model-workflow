---
name: verify-ticket
description: Run a ticket's acceptance criteria and comment the outcome on the ticket. Use when you have finished a ticket, when you are the verifier re-running what it ticked, or when auditing how a freshly written ticket's criteria are worded.
---

# Verify ticket

Each acceptance criterion on the ticket carries a `CHECK:` command and the `EXPECT:`
string a passing run prints. This skill runs them and comments the outcome on the ticket.
Every run reads the ticket fresh; there is no state to carry between runs.

A `CHECK:` is a shell command, and may run to several lines: the lines under it, up to
the criterion's next attribute, are part of the same command.

## The engine

`scripts/verify-ticket.py`, next to this file. Resolve its absolute path once. Every
command below is written `<engine> <ticket>` and means:

```bash
python3 /absolute/path/to/scripts/verify-ticket.py <ticket>
```

## The five runs

| Command | Who runs it, and when | What lands |
| --- | --- | --- |
| `<engine> <n> --preflight` | The **worker**, before touching anything on ticket `<n>` | The ticket assigned to you. If it is not yours to start, a `NOT_READY: <reason>` comment on the ticket instead, and exit 2 |
| `<engine> <n>` | The **worker**, having finished the work on ticket `<n>`, before dispatching the verifier | A comment whose first line is `self-run`: each criterion ticked or not, each with the `EVIDENCE:` line the engine recorded |
| `<engine> <n> --reverify` | The **verifier**, on the same commit, re-running what the worker's `self-run` ticked instead of trusting it | A comment whose first line is `reverify` |
| `<engine> <n> --closeout <draft>` | The **worker**, having written the closing comment to a file | The draft posted and the ticket closed. A draft whose first line is `HANDOFF REQUIRED` posts and swaps `ready-for-agent` for `ready-for-human`, leaving the ticket open |
| `<engine> <n> --lint` | Whoever wrote the ticket, at the read-back step of `to-tickets`, before the ticket goes out | Findings printed to your terminal: how the criteria are written, and whether the batch under the same spec has a cycle or a dangling `Blocked by`. No `CHECK:` runs and no comment is posted |

`--reverify` re-runs what the newest `self-run` comment ticked, so it belongs after one.
On a ticket with no such comment it behaves like a plain run.

`--closeout --check-only` reports on the draft and changes nothing. A refused draft
changes nothing either way: the reason is one line on stderr, and the ticket is
untouched. Fix the draft, or fix what it describes, and run it again.

`--timeout <seconds>` raises the per-`CHECK` limit when one of them is slow.

Exit code: 0 every criterion met, 1 something unmet or abandoned, 2 the ticket could not
be read or the run could not start. `--preflight` uses 2 for a refusal; `--closeout`
uses 1.

## What it decides, and what it leaves to you

A criterion passes only when its `CHECK` exits 0 **and** its output matches `EXPECT`.
Expected text in the output of a failed process is still a failure. A criterion written
with `MANUAL:` instead of `CHECK:`/`EXPECT:` is never run and never ticked by the engine.

The engine reads the ticket and writes one comment. The ticket body, the `CHECK` commands
and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment
saying what is wrong with it, then edit the criterion and run again. The `VERDICT` line
is the verifier's own comment, written after this one, not something the engine emits.

`--closeout` reads the draft against the ticket and the repository: the first line, the
`ABANDON:` kinds, the recount behind `Counts:`, a sub-issue for every `MANUAL:` criterion
still waiting on a person, the verifier's `VERDICT` commit still being in the history, and
a clean tracked working tree. Whether the work is any good is what the `CHECK` commands,
the verifier and `code-review` decide before you write the draft.

The comment ends with **Outside Owns**: files this branch changed since it left `main`
that no `## Owns` glob covers. That list is something to explain in the closeout comment,
not a verdict on the work.

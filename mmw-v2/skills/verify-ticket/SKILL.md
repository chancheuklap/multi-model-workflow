---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use to claim a ticket before starting work on it, to run its criteria after writing code, to re-run them as its verifier, to close it out from a written draft, to lint a batch of tickets before publishing them, or to write or read the criterion that compares an interface against its handoff package.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and comments the outcome on the ticket.

The ticket is the only state. Every run reads it fresh, writes at most one comment, and carries nothing to the next run.

## Resolve the engine once

`scripts/verify-ticket.py`, next to this file. Every command below is written `<engine>` and means:

```bash
python3 <absolute path to that script>
```

Resolve it from this file's own location. The path differs by machine and by host, and the installer puts this skill wherever the host that gave it to you reads its skills from.

## Find your run

| You are | Run | What lands on the ticket |
| --- | --- | --- |
| A **worker** about to touch ticket `<n>` | `<engine> <n> --preflight` | The ticket assigned to you. If it is not yours to start: a `NOT_READY: <reason>` comment instead, exit 2, and you stop — the reason is already on the ticket, so there is nothing to report twice |
| A **worker** who has finished writing code | `<engine> <n>` | A comment whose first line is `self-run`: each criterion ticked or not, each with the `EVIDENCE:` line the engine recorded |
| The **verifier** on ticket `<n>` | `<engine> <n> --reverify` | A comment whose first line is `reverify`: every criterion run again, the ones the worker's `self-run` ticked included, instead of trusted |
| A **worker** whose closing comment is written to a file | `<engine> <n> --closeout <draft>` | The draft posted, `ready-for-agent` taken off, and the ticket closed. A draft whose first line is `HANDOFF REQUIRED` posts and swaps `ready-for-agent` for `needs-triage`, leaving the ticket open to be judged fresh |
| The **agent publishing a batch**, at the read-back step | `<engine> <n> --lint` | Nothing. Findings print to your terminal; no `CHECK:` runs and no comment is posted |

Exit code: `0` every criterion met, `1` something unmet or abandoned, `2` the ticket could not be read or the run could not start. `--preflight` uses `2` for a refusal; `--closeout` uses `1`.

`--timeout <seconds>` raises the per-`CHECK` limit when one of them is slow.

## What the engine decides

A criterion passes only when its `CHECK` exits `0` **and** its output matches `EXPECT`. Expected text in the output of a failed process is still a failure.

The engine reads the ticket and writes one comment. The ticket body, the `CHECK` commands and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment saying what is wrong with it, edit the criterion, run again. The `VERDICT` line is the verifier's own comment, written after `--reverify`, not something the engine emits.

## Three rounds on one criterion

Three self-runs is as far as fixing one criterion goes. The third run names it in its comment, and the closeout will then accept `ABANDON: <id> failed`. The count is the ticket's own `self-run` comments — nothing is stored between runs, and a fourth run that finally passes still passes.

## `Outside Owns`

The `self-run` and `reverify` comment ends with the files this ticket's own commits changed that no `## Owns` glob covers: the first-parent chain since the branch left its base, merges excluded, so work merged in from another ticket's branch is not counted. Copy that line into the closing comment. It is something to explain there, not a verdict on the work.

## A multi-line `CHECK:`

A `CHECK:` is a shell command. One that needs more than a line carries it in a fenced block directly under `CHECK:`, and nothing inside that block is read as ledger syntax: a `- [ ]` line in a heredoc is text the command prints, not the next criterion. A bare line under a `CHECK:` is refused, and the refusal says to use a fence.

## `--lint` on a batch

Two things at once: how the criteria are written, and whether the batch under the same spec is a startable graph — every ticket the spec lists as a sub-issue, the edges between them, and which of them nothing blocks. The graph comes from the tracker's native blocking links, the same edges `--preflight` refuses on and `board.py` dispatches from. A ticket's `## Blocked by` section is the human-readable copy of those links, and a mismatch is a `WARN  … [blocked-by-mismatch]` naming the numbers each side has that the other does not.

The batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

## Reached from here

- **`--closeout` refused your draft** → [references/closeout.md](references/closeout.md), the conditions it reads the draft against. The refusal itself is on stderr: the first line counts the problems, names the first, and gives the `--check-only` command that prints them all; every problem after the first is one more line opening `also:`. Go to the reference when a line names a condition you cannot place. `--closeout <draft> --check-only` reports on a draft and changes nothing, at any time.
- **You are writing the criterion that compares an interface against its handoff package, or reading the `DIFF` line one printed** → [references/ui-parity.md](references/ui-parity.md). It carries that criterion's one fixed shape, path and all, to copy onto the ticket, and the three exit codes and reasons a run prints. A `CHECK` that runs `visual-parity.py` prints one `DIFF` line and nothing that explains it; that reference is where the line is read.

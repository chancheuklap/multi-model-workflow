---
name: verify-ticket
description: Run one ticket's acceptance criteria, and close the ticket when they pass. Use to claim a ticket before starting work on it, to run its criteria after writing code, to re-run them as its verifier, to close it out from a written draft, to lint a batch of tickets before publishing them, or to write or read the criterion that compares an interface against its handoff package.
---

# Verify ticket

Each acceptance criterion on a ticket carries a `CHECK:` command and the `EXPECT:` string a passing run prints. This skill runs them and comments the outcome on the ticket.

The ticket is the only state. Every run reads it fresh, writes at most one comment, and carries nothing to the next run.

## Resolve `<engine>` once

`<engine>` in every command below is `scripts/verify-ticket.py`, next to this file, and means:

```bash
python3 <absolute path to that script>
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Find your run

| You are | Run | What lands on the ticket |
| --- | --- | --- |
| A **worker** about to touch ticket `<n>` | `<engine> <n> --preflight` | The ticket assigned to you. If it is not yours to start: a `NOT_READY: <reason>` comment instead, exit 2, and you stop — the reason is already on the ticket, so there is nothing to report twice |
| A **worker** who has finished writing code | `<engine> <n>` | A comment whose first line is `self-run`: each criterion ticked or not, each with the `EVIDENCE:` line gate-check recorded |
| The **verifier** on ticket `<n>` | `<engine> <n> --reverify` | A comment whose first line is `reverify`: every criterion run again, the ones the worker's `self-run` ticked included, instead of trusted |
| A **worker** whose closing comment is written to a file | `<engine> <n> --closeout <draft>` | The draft posted, `ready-for-agent` taken off, and the ticket closed. A draft whose first line is `HANDOFF REQUIRED` posts and swaps `ready-for-agent` for `needs-triage`, leaving the ticket open to be judged fresh |
| The **agent publishing a batch**, at the read-back step | `<engine> <n> --lint` | Nothing. Findings print to your terminal; no `CHECK:` runs and no comment is posted |

Exit code: `0` every criterion met, `1` something unmet or abandoned, `2` the ticket could not be read or the run could not start. `--preflight` uses `2` for a refusal; `--closeout` uses `1`.

A `CHECK:` may run ten minutes. A criterion that needs longer says so on the ticket, on a `TIMEOUT: <seconds>` line under its `EVIDENCE:`; every run reads those lines off the ticket body, so the worker's own run and the verifier's `--reverify` are held to the same number. `--timeout <seconds>` raises it for one run. Neither lowers it.

## What `verify-ticket.py` decides

A criterion passes only when its `CHECK` exits `0` **and** its output matches `EXPECT`. Expected text in the output of a failed process is still a failure.

`verify-ticket.py` reads the ticket and writes one comment. The ticket body, the `CHECK` commands and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment saying what is wrong with it, edit the criterion, run again. The `VERDICT` line is the verifier's own comment, written after `--reverify`, not something `verify-ticket.py` emits.

## Three self-runs behind a `failed`

How many rounds a criterion gets is the worker's own judgement; no run names a limit. What `--closeout` asks of `ABANDON: AC<n> failed` is evidence of the trying: three `self-run` comments on the ticket that show that criterion unmet. The count is the ticket's own comments — nothing is stored between runs.

## `Outside Owns`

The `self-run` and `reverify` comment ends with the files this ticket's own commits changed that no `## Owns` glob covers: the first-parent chain since the ticket branch left its base commit, merges excluded, so work merged in from another ticket's branch is not counted. Copy that line into the closing comment. It is something to explain there, not a verdict on the work.

## A multi-line `CHECK:`

A `CHECK:` is a shell command. One that needs more than a line carries it in a fenced block directly under `CHECK:`, and nothing inside that block is read as ledger syntax: a `- [ ]` line in a heredoc is text the command prints, not the next criterion. A bare line under a `CHECK:` is refused, and the refusal says to use a fenced block.

## `--lint` on a batch

Three things at once: how the criteria are written, which worker the ticket asks for, and whether the batch under the same spec is a startable graph — every ticket the spec lists as a sub-issue, the blocking links between them, and which of them nothing blocks. The graph comes from the tracker's blocking links, the same ones `--preflight` refuses on and `board.py` dispatches from. A ticket's `## Blocked by` section is the human-readable copy of those links, and a mismatch is a `WARN  … [blocked-by-mismatch]` naming the numbers each side has that the other does not.

The worker reads the same way. `dispatch.sh` starts a ticket on the `models.md` row its `junior-worker` or `senior-worker` label names, so a ticket in the agent queue wearing no such label is an `ERROR  … [worker-label]`, and so is one wearing both. Its `## Worker` section is the human-readable copy, and a section that is missing or names the other one is a `WARN  … [worker-mismatch]`.

The batch converges when `ERROR` is at zero and every `WARN` has been looked at and either fixed or kept on purpose.

## Reached from here

- **`--closeout` refused your draft** → [references/closeout.md](references/closeout.md), the conditions it reads the draft against. The refusal itself is on stderr: the first line counts the problems, names the first, and gives the `--check-only` command that prints them all; every problem after the first is one more line opening `also:`. Go to the reference file when a line names a condition you cannot place. `--closeout <draft> --check-only` reports on a draft and changes nothing, at any time.
- **You are writing the criterion that compares an interface against its handoff package, or reading the `DIFF` line one printed** → [references/ui-parity.md](references/ui-parity.md). It carries that criterion's one fixed shape, path and all, to copy onto the ticket, and the three exit codes and reasons a parity run prints. A `CHECK` that runs `visual-parity.py` prints one `DIFF` line and nothing that explains it; that reference file is where the line is read.

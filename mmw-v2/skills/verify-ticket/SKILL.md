---
name: verify-ticket
description: Run a ticket's acceptance criteria and comment the outcome on the ticket. Use when you have finished a ticket, when you are the verifier re-running what it ticked, or when auditing how a freshly written ticket's criteria are worded.
---

# Verify ticket

Each acceptance criterion on the ticket carries a `CHECK:` command and the `EXPECT:`
string a passing run prints. This skill runs them and comments the outcome on the ticket.
Every run reads the ticket fresh; there is no state to carry between runs.

A `CHECK:` is a shell command. One that needs more than a line carries it in a fenced
block directly under `CHECK:`, and nothing inside that block is read as ledger syntax:
a `- [ ]` line in a heredoc is text the command prints, not the next criterion. A bare
line under a `CHECK:` is refused, and the refusal says to use a fence.

## The engine

`scripts/verify-ticket.py`, next to this file. Resolve its absolute path once. Every
command written `<engine> <ticket>` here means:

```bash
python3 /absolute/path/to/scripts/verify-ticket.py <ticket>
```

## The five runs

| Command | Who runs it, and when | What lands |
| --- | --- | --- |
| `<engine> <n> --preflight` | The **worker**, before touching anything on ticket `<n>` | The ticket assigned to you. If it is not yours to start, a `NOT_READY: <reason>` comment on the ticket instead, and exit 2 |
| `<engine> <n>` | The **worker**, having finished the work on ticket `<n>`, before dispatching the verifier | A comment whose first line is `self-run`: each criterion ticked or not, each with the `EVIDENCE:` line the engine recorded |
| `<engine> <n> --reverify` | The **verifier**, on the same commit, re-running every criterion — the ones the worker's `self-run` ticked included — instead of trusting it | A comment whose first line is `reverify` |
| `<engine> <n> --closeout <draft>` | The **worker**, having written the closing comment to a file | The draft posted, `ready-for-agent` taken off, and the ticket closed. A draft whose first line is `HANDOFF REQUIRED` posts and swaps `ready-for-agent` for `needs-triage`, leaving the ticket open to be judged fresh |
| `<engine> <n> --lint` | Whoever wrote the ticket, at the read-back step of `to-tickets`, before the ticket goes out | Findings printed to your terminal: how the criteria are written, and whether the batch under the same spec is a startable graph. No `CHECK:` runs and no comment is posted |

`--reverify` runs every criterion again, ticked or not. The ledger it starts from is
the one in the ticket's newest `self-run` or `reverify` comment, so it belongs after one
of those; on a ticket with neither it behaves like a plain run.

`--lint` checks the batch as a graph: every ticket the spec lists as a sub-issue, the
edges between them, and which of them nothing blocks. The graph comes from the tracker's
native blocking links — the same edges `--preflight` refuses on and `board.py` dispatches
from. The ticket's `## Blocked by` section is the human-readable copy of those links, and
a mismatch between the two is a `WARN  … [blocked-by-mismatch]` naming the numbers each
side has that the other does not.

`--closeout <draft> --check-only` reports on the draft and changes nothing. A refused
draft changes nothing either way, and the ticket is untouched. The refusal is written to
stderr: the first line counts the problems, names the first, and gives the
`--check-only` command that prints them all; every problem after the first is one more
line opening `also:`. Fix the draft, or fix what it describes, and run it again.

`--timeout <seconds>` raises the per-`CHECK` limit when one of them is slow.

Exit code: 0 every criterion met, 1 something unmet or abandoned, 2 the ticket could not
be read or the run could not start. `--preflight` uses 2 for a refusal; `--closeout`
uses 1.

## What it decides, and what it leaves to you

A criterion passes only when its `CHECK` exits 0 **and** its output matches `EXPECT`.
Expected text in the output of a failed process is still a failure. Every criterion on a
ticket has a `CHECK`; work that only a person can judge is its own ticket, not a
criterion on this one.

Three self-runs is as far as fixing one criterion goes. The third run names it in its
comment, and the closeout will then accept `ABANDON: <id> failed`. The count is the
ticket's own self-run comments — nothing is stored between runs, and a fourth run that
finally passes still passes.

The engine reads the ticket and writes one comment. The ticket body, the `CHECK` commands
and what a criterion means are yours. A wrong `CHECK` is fixed on the ticket: comment
saying what is wrong with it, then edit the criterion and run again. The `VERDICT` line
is the verifier's own comment, written after this one, not something the engine emits.

`--closeout` reads the draft against the ticket and the repository, and refuses it over
any of these:

- **The first line and what it commits to.** It is `ALL MET`, or `HANDOFF REQUIRED: <n>
  abandoned (<kinds>), <m> unmet, <k> met of <total>`, and nothing else. An `ALL MET`
  draft may leave no criterion unmet and may abandon none as `failed` or `stuck` — only
  `decision` is abandoned and still closes.
- **The `ABANDON:` lines.** Each names one of `decision`, `failed`, `stuck`, and points
  at a criterion the draft itself lists.
- **The ticks and their `EVIDENCE:`.** A ticked criterion whose evidence is missing or
  `pending` is refused, and so is a `CHECK:` continued on a bare line instead of in a
  fenced block.
- **Three self-runs behind every `failed`.** Counted off the ticket's own `self-run`
  comments; `stuck` is held to no round count at all.
- **`Counts: <k> met, <m> unmet, <n> abandoned of <total>`.** The line has to be there,
  it has to match the draft recounted criterion by criterion, and on a `HANDOFF
  REQUIRED` draft the first line's four numbers have to agree with it.
- **The newest run's own summary.** An `ALL MET` draft is refused while the newest
  `self-run` or `reverify` comment on the ticket summarises as `UNMET:` or `HANDOFF
  REQUIRED:`. Fix what that run found and run `<engine> <n>` again — the newer summary is
  the one read — or close out as `HANDOFF REQUIRED`.
- **`VERDICT` and `Post-verdict:`.** An `ALL MET` draft needs the verifier's
  `VERDICT <full 40-character commit> by <model> — <one line>` on the ticket; if HEAD has
  moved past the commit that line names, it also needs a `Post-verdict:` line naming every
  commit since and where it came from.
- **The working tree and the branch.** No uncommitted changes to tracked files, and the
  branch contains its base — the cut point dispatch recorded in
  `git config branch.issue-<n>.mmw-base`, `main` when there is no record — merge it,
  never rebase, because the verdict names one commit.
- **The ticket.** Still `OPEN`, and assigned to you.

`HANDOFF REQUIRED` is held to none of the `VERDICT` conditions — it claims nothing was
finished, so it is the way out of anything you cannot fix yourself, including a verifier
that never ran. Whether the work is any good is what the `CHECK` commands, the verifier
and `code-review` decide before you write the draft.

The `self-run` and `reverify` comment ends with **Outside Owns**: files this ticket's
own commits changed that no `## Owns` glob covers — the first-parent chain since the
branch left `main`, merges excluded, so work merged in from another ticket's branch is
not counted. The closing comment carries
the same line, copied out of that comment into the draft, at the place `implement` puts
it in the draft's fixed shape. That list is something to explain in the closeout comment,
not a verdict on the work.

## UI acceptance

Whether an interface matches the design it was built from is the other script in
`scripts/`: `visual-parity.py`. It renders each named scene from a baseline directory
offline, opens the same scene on the implementation, and compares the two by
accessibility tree and by pixels at two viewports.

The baseline directory is a Claude Design project downloaded as a handoff package, and
holds five things: the component's `.dc.html`, its `styles/`, its `data/`, `support.js`,
and a `scenes.json` naming every scene. A directory missing any of them cannot be
rendered.

Nobody types this command: `to-tickets` writes it onto the ticket as a criterion, in one
shape.

```
CHECK: uv run <skills>/verify-ticket/scripts/visual-parity.py --baseline <handoff package dir> --impl <url> --scenes <name,name> --max-pct 1
EXPECT: PARITY OK <n>/<n>
```

Three exit codes. **0** with one line `PARITY OK <n>/<n>`: every scene matched at every
viewport. **1**: one `DIFF` line per failing scene and viewport. **2** with
`NEGATIVE CONTROL FAILED`: the run's own control — a baseline render with an error
inserted into it — was not caught, so nothing this run says about parity can be trusted,
and no parity conclusion is printed at all.

A failure line reads `DIFF <scene> <viewport> <pct>% box=… — <reasons>`, and the reasons
after the dash are where the failure is named. Only a difference in the accessibility
tree brings lines out under it: `baseline`, `impl`, `only in baseline`, `only in impl`.
A size difference, a pixel difference or a console error prints the `DIFF` line alone.

---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a reviewer on your ticket and wait for its report, to open a night on a spec, to merge the branches of the tickets that closed and dispatch the ones that can start, to act on a line beginning `mmw board:`, or to change which host, model or thinking level an agent in this pipeline runs on.
---

# Dispatch

Nothing here runs on its own. You arrive at one row of the `Find your command` table below, run its command, and act on its exit code.

## Resolve the scripts once

`scripts/dispatch.sh` and `scripts/board.py`, next to this file. Commands below are written `<dispatch>` and `<board>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
python3 <absolute path to scripts/board.py> …
```

Resolve them from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Find your command

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket and wait for its report | `<dispatch> <n> reviewer <base-commit>`, then `<dispatch> wait <n> "^REVIEW "`. A start that exits 1 or 2, or a wait that times out, does not end the round: read the reviewer's screen with `herdr agent read <name>`; still running, wait again; never started or stopped, run the `code-review` skill in your host's general-purpose subagent with the same base commit and ticket number, and its report lands on the ticket with the same `REVIEW` first line |
| Open the night on a spec | `<dispatch> run <spec>`, then `<dispatch> advance <spec>` straight after |
| Act on `mmw board: ADVANCE` | `<dispatch> advance <spec>` |
| Act on `mmw board: night over` | `<dispatch> advance <spec>`, then re-run the closed tickets' criteria on the base branch — [references/night.md](references/night.md) |
| Act on `mmw board: STOPPED #<n>` or `mmw board: TIME LIMIT #<n>` | `herdr agent read <name> --source recent --lines 80`, with the Herdr name the line carries. Read why that worker stopped, fix what stopped it yourself — a file it could not find, a command it needs, a baseline it read wrong — and tell it to carry on with `herdr agent prompt <name> "<what you settled, then: continue>"`. A question only a person can settle goes into a sub-issue under the spec (`gh issue create --parent <spec> --label needs-triage`), and the worker is told to take the default meanwhile. Change no label: the ticket stays in the agent queue until its worker closes it out |
| Start a worker on one ticket, outside a night | `<dispatch> <n> worker` |
| Change one ticket's worker grade | Swap its `junior-worker` / `senior-worker` label on the tracker; the next dispatch reads it |
| Change which host, model or `effort` an agent runs on | Edit `models.md`, next to this file — but read [references/editing-models.md](references/editing-models.md) first |

The night itself — what `run` sets up, why `advance` merges before it dispatches, and what the board does between your commands — is [references/night.md](references/night.md).

## The arguments you supply

`<n>` is a ticket number, digits only, no `#`.

The second argument is `worker` or `reviewer`. Which of the two worker rows in `models.md` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every dispatch — so a ticket the board redispatches at three in the morning comes back on the row it was written for. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a worker grade `models.md` has no row for, is refused.

`<base-commit>` is the reviewer's only extra argument: the commit the code review starts from. Read it in the worker's worktree with `git config branch.issue-<n>.mmw-base` — the base commit `dispatch.sh` recorded when it opened the worktree, and the commit `verify-ticket.py` measures `Outside Owns:` from.

`wait` takes a first-line regular expression, matched against the newest comment on the ticket. A worker waiting on its reviewer uses `"^REVIEW "`, trailing space and all; whoever dispatched a worker waits on `"^(ALL MET|HANDOFF REQUIRED)"`. A trailing `[seconds]` overrides `dispatch.sh`'s own `WAIT_DEFAULT_SECONDS`; leave it off.

## Exit codes

**Dispatching an agent** — `<dispatch> <n> worker|reviewer [base-commit]`:

| Code | What happened |
| --- | --- |
| `0` | The session is up and has been told what to work on |
| `1` | The session is up but was **not** told anything: its hooks did not report it ready in time, or it did not report the prompt as taken. A session is now sitting in that pane holding the ticket's name with nothing to do. Read its screen with `herdr agent read <name>`, then either prompt it yourself with the dispatch line or end that session before dispatching the ticket again with the same second argument — the Herdr name collides |
| `2` | Nothing was started. The reason is on stderr — read it verbatim |

**Waiting** — `<dispatch> wait`:

| Code | What happened |
| --- | --- |
| `0` | It matched. The whole comment is on stdout |
| `1` | It timed out, and `dispatch.sh` has already commented on the ticket saying who did not finish. Waiting on a worker: **skip what you were waiting for and carry on with the rest of your own steps** — an agent that never reported back is not a reason to hand the ticket to a person. Waiting on your reviewer: the round is not skipped; the first row of `Find your command` says what comes next |

**Moving the batch on** — `<dispatch> advance <spec>`:

| Code | What happened |
| --- | --- |
| `0` | Done. The advance summary line counts what was merged, what was already in, and what was started |
| `2` | Nothing was touched. The reason is on stderr: not inside Herdr, not a git repository, or the working tree has uncommitted changes |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was dispatched. **The conflict is still in the tree and it stays there.** Resolve it with the `resolving-merge-conflicts` skill, run this repository's own checks, commit the merge, then run `advance` again — it picks up from the branch after the one you resolved. The conflict report on stderr is the first two steps of that skill already done for you: the branch being merged and the ticket it belongs to, the tickets already merged on this side, and the conflicted files |

**Opening the night** — `<dispatch> run <spec>`:

| Code | What happened |
| --- | --- |
| `0` | The board is up. Its monitor tab holds every line it will write |
| `2` | Nothing was started. The reason is on stderr: not inside Herdr, a worker row in `models.md` that starts no session, or `install.sh --check` found something missing. Run `install.sh`, then `<dispatch> run <spec>` again |

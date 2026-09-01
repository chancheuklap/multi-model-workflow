---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a reviewer on your ticket and wait for its report, to open a night on a spec, to merge the branches of the tickets that closed and dispatch the ones that can start, to act on a line beginning `mmw board:`, or to change which host, model or thinking level an agent in this pipeline runs on.
---

# Dispatch

Nothing here runs on its own. You arrive at one row of the table below, run its command, and act on its exit code.

## Resolve the scripts once

`scripts/dispatch.sh` and `scripts/board.py`, next to this file. Commands below are written `<dispatch>` and `<board>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
python3 <absolute path to scripts/board.py> …
```

Resolve them from this file's own location. The path differs by machine and by host, and the installer puts this skill wherever the host that gave it to you reads its skills from.

## Find your command

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket and wait for its report | `<dispatch> <n> reviewer <base-commit>`, then `<dispatch> wait <n> "^REVIEW "` |
| Open the night on a spec | `<dispatch> run <spec>`, then `<dispatch> advance <spec>` straight after |
| Act on `mmw board: ADVANCE` or `mmw board: night over` | `<dispatch> advance <spec>` |
| Act on `mmw board: WAKEUP LIMIT`, `REDISPATCHED` or `TIME LIMIT` | `<board> --once <spec>`. Read the table it prints and act no further: the board has already commented on that ticket and moved it to `needs-triage` |
| Start a worker on one ticket, outside a night | `<dispatch> <n> worker` |
| Give one ticket the other worker | Swap its `junior-worker` / `senior-worker` label on the tracker; the next start reads it |
| Change which host, model or thinking level an agent runs on | Edit `models.md`, next to this file — but read [references/editing-models.md](references/editing-models.md) first |

The night itself — what `run` sets up, why `advance` merges before it dispatches, and what the board does between your commands — is [references/night.md](references/night.md).

## The arguments you supply

`<n>` is a ticket number, digits only, no `#`.

The second argument is `worker` or `reviewer`. Which of the two worker rows a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start — so a ticket the board restarts at three in the morning comes back on the row it was written for. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a row `models.md` has no line for, is refused.

`<base-commit>` is the reviewer's only extra argument: the commit the code review starts from. Read it in the worker's worktree with `git config branch.issue-<n>.mmw-base` — the cut point dispatch recorded when it opened the worktree, and the same base the ticket engine measures `Outside Owns:` from.

`wait` takes a first-line regular expression, matched against the newest comment on the ticket. A worker waiting on its reviewer uses `"^REVIEW "`, trailing space and all; whoever dispatched a worker waits on `"^(ALL MET|HANDOFF REQUIRED)"`. A trailing `[seconds]` overrides the script's own timeout; leave it off.

## Exit codes

**Dispatching an agent** — `<dispatch> <n> worker|reviewer [base-commit]`:

| Code | What happened |
| --- | --- |
| `0` | The session is up and has been told what to work on |
| `1` | The session is up but was **not** told anything: it did not become ready in time, or it would not take the prompt. A session is now sitting in that pane holding the ticket's name with nothing to do. Inside a night, leave it where it is: the board comments `REDISPATCHED` on that ticket, closes the pane and starts the ticket again, and a second hand on it puts two sessions on one ticket. Outside a night nothing is watching, so end that session yourself before dispatching the same kind again — the name collides |
| `2` | Nothing was started. The reason is on stderr — read it verbatim |

**Waiting** — `<dispatch> wait`:

| Code | What happened |
| --- | --- |
| `0` | It matched. The whole comment is on stdout |
| `1` | It timed out, and the script has already commented on the ticket saying who did not finish. **Skip that round and carry on with the rest of your own steps.** An agent that never reported back is not a reason to hand the ticket to a person |

**Moving the batch on** — `<dispatch> advance <spec>`:

| Code | What happened |
| --- | --- |
| `0` | Done. The last line counts what was merged, what was already in, and what was started |
| `2` | Nothing was touched. The reason is on stderr: not inside Herdr, not a git repository, or the working tree has uncommitted changes |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was dispatched. **The conflict is still in the tree and it stays there.** Resolve it with the `resolving-merge-conflicts` skill, run this repository's own checks, commit the merge, then run `advance` again — it picks up from the branch after the one you resolved. The report on stderr is the first two steps of that skill already done for you: the branch being merged and the ticket it belongs to, the tickets already merged on this side, and the conflicted files |

**Opening the night** — `<dispatch> run <spec>`:

| Code | What happened |
| --- | --- |
| `0` | The board is up. Its tab holds every line it will write |
| `2` | Nothing was started. The reason is on stderr: not inside Herdr, a worker row in `models.md` that starts no session, or `install.sh --check` found something missing. Run `install.sh` and start the night again |

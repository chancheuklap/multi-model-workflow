---
name: dispatch
description: Dispatch a worker or a reviewer onto a ticket, wait for it to report back there, and change which agent, model or thinking level any agent in this pipeline runs on.
---

# Dispatch

Other skills reach this one at the step where one agent puts another to work; nothing
here runs on its own.

## The script

`scripts/dispatch.sh`, next to this file. Resolve its absolute path once. Every command
below is written `<dispatch> …` and means:

```bash
bash /absolute/path/to/scripts/dispatch.sh …
```

You supply a role and a ticket number. Everything else is fixed by the shape of the
pipeline and lives inside the script.

## Dispatch an agent

```bash
<dispatch> <ticket> <role> [base-commit]
```

| Argument | What to put there |
| --- | --- |
| `<ticket>` | The ticket number. Digits only, no `#` |
| `<role>` | `junior-worker`, `senior-worker` or `reviewer`. You choose which of the two workers a ticket gets; the ticket itself says nothing about it |
| `[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from |

| Exit code | What happened |
| --- | --- |
| `0` | The session is up and has been told what to work on |
| `1` | The session is up but never became ready in time, so it was **not** told anything |
| `2` | Nothing was started. The reason is on stderr: not inside Herdr, no such role, or the ticket is not ready to be worked on |

On exit 1 a session is sitting in that pane holding the ticket's name with nothing to do.
Dispatching the same role again collides on that name: end that session first, or carry
on without it.

## Wait for the agent to report back

```bash
<dispatch> wait <ticket> "<first-line-regex>" [seconds]
```

| Argument | What to put there |
| --- | --- |
| `"<first-line-regex>"` | Matched against the **first line** of the newest comment on the ticket. A worker waiting on its reviewer uses `^REVIEW`; whoever dispatched a worker waits on `^(ALL MET\|HANDOFF REQUIRED)` |
| `[seconds]` | How long to wait. Defaults to 1800 |

| Exit code | What happened |
| --- | --- |
| `0` | It matched. The whole comment is on stdout |
| `1` | It timed out. The script has already commented on the ticket saying who did not finish |

On exit 1, **skip that round and carry on with the rest of your own steps.** An agent that
never reported back is not a reason to hand the ticket to a person.

## Start the night

```bash
<dispatch> run <spec> [--role R] [--parallel N] [--max-hours H]
```

One command, typed once, after the last ticket of a spec is published. It checks this
machine, renames your own pane `mmw-main` so the board can reach you, opens a tab
labelled `mmw board`, and leaves `scripts/board.py --watch` running in it. From then on
the board dispatches the frontier, re-prompts the sessions that go idle short of their
closing gate, hands back the tickets that reach a limit, and writes `NIGHT SUMMARY` on
the spec when nothing is left to run.

| Argument | What to put there |
| --- | --- |
| `<spec>` | The spec issue whose sub-issues are tonight's tickets. Digits only |
| `--role` | Which row of `models.md` tonight's workers are started from. Defaults to `junior-worker` |
| `--parallel` | How many workers may be alive at once. Defaults to the board's own `PARALLEL` |
| `--max-hours` | How long one ticket may hold a session before it goes back to be judged |

| Exit code | What happened |
| --- | --- |
| `0` | The board is up. Its tab holds every line it will write |
| `2` | Nothing was started. The reason is on stderr: not inside Herdr, no such role, or `install.sh --check` found something missing |

Exit 2 on the check is not a formality. A night nobody is watching cannot notice that
this machine's skills or its closing gate went missing, so that is checked at the one
moment somebody is here to fix it: run `install.sh` and start the night again.

**After this command you read tickets and nothing else.** You do not dispatch, you do
not prompt a worker, and you do not answer a question a worker put on screen — the
board comments the form on the ticket, dismisses it, and sends the worker its dispatch
line again, because the discipline is not to ask.

## When the board re-prompts you

Two cases reach you, and both arrive as one line: `mmw board: <case> #<n> — run
board.py --once`. Run that, read the table, and go back to being idle.

| Case | What it means | What to do |
| --- | --- | --- |
| A limit was reached — `WAKEUP LIMIT`, `REDISPATCHED`, `TIME LIMIT` | The board has already commented on that ticket and moved it to `needs-triage` | Read the table. Nothing else: do not dispatch it again, do not prompt its session |
| The night ended | `NIGHT SUMMARY` is the newest comment on the spec | Read it. If the user asked to be told when the run finished, tell them now |

A worker stopped at a question does not reach you. Its form is on its ticket for the
morning, under `BLOCKED:`.

## Change which agent, model, or thinking level is used

Edit `models.md`, next to this file. **Read
[references/editing-models.md](references/editing-models.md) first** — a row is only
correct on the machine it runs on, and that file carries the whole change: what to
confirm before you touch a row, and what to do afterwards to make it take effect.

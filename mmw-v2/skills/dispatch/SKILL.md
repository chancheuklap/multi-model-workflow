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

## Change which agent, model, or thinking level is used

Edit `models.md`, next to this file. **Read
[references/editing-models.md](references/editing-models.md) first** — a row is only
correct on the machine it runs on, and that file carries the whole change: what to
confirm before you touch a row, and what to do afterwards to make it take effect.

---
name: dispatch
description: Start another agent on a ticket and wait for it to report back. Use at the step where one agent hands a ticket to a session running on a different model — dispatching a worker onto a ticket, or a reviewer onto the work just finished — and to change which agent, model, or thinking level any of them runs on.
---

# Dispatch

One agent puts another to work on a ticket. Other skills reach this one at the step
where that happens; nothing here runs on its own.

## The script

`scripts/dispatch.sh`, next to this file. Resolve its absolute path once. Every command
below is written `<dispatch> …` and means:

```bash
bash /absolute/path/to/scripts/dispatch.sh …
```

It reads `models.md` next to it, checks the ticket, starts the session, and hands it the
one line that puts it to work. You supply a role and a ticket number; everything else is
fixed by the shape of the pipeline and lives inside the script.

## Dispatch an agent

```bash
<dispatch> <ticket> <role> [base-commit]
```

| Argument | What to put there |
| --- | --- |
| `<ticket>` | The ticket number. Digits only, no `#` |
| `<role>` | The first column of a row in `models.md` whose launch arguments are not `—`: `junior-worker`, `senior-worker`, `reviewer`. Which of the two workers a ticket gets is decided by whoever dispatches it; it is not written on the ticket and not marked with a label |
| `[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from |

| Exit code | What happened |
| --- | --- |
| `0` | The session is up and has been told what to work on |
| `1` | The session is up but never became ready in time, so it was **not** told anything |
| `2` | Nothing was started. The reason is on stderr: not inside Herdr, no such role, or the ticket is not ready to be worked on |

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

Edit `models.md`. **Read [references/before-editing.md](references/before-editing.md)
first** — it names the two things you have to confirm on this machine before you touch a
row. The next dispatch reads the table as you left it.

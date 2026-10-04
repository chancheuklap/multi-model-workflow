---
name: dispatch
description: Change which host, model or reasoning effort an agent role runs on, or which runner this machine uses. Use when the user asks to change a role's host, model or effort, or the runner.
---

# Dispatch

The scripts that start sessions, wake them and watch them: `scripts/dispatch.sh`, the relay (`scripts/relay.py`), the watchdog (`scripts/watchdog.py`), the two hooks (`scripts/turn-guard.py`, `scripts/tool-guard.py`), the runner adapters under `scripts/runners/` and the model configuration (`scripts/models.py`). Each command is named by the playbook step that runs it. `bash scripts/dispatch.sh` finds the scripts of the skills it calls into by itself, so no path is ever passed to it.

## Changing a role's model, or the runner

Read [references/editing-models.md](references/editing-models.md).

## On waking

The step that ended your turn names the wake it waits for and sends you here first.

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket; the wake carries nothing the tracker does not.
3. `bash scripts/dispatch.sh ack <n> <event>` with the ticket and the event the wake named (`bash scripts/dispatch.sh ack relay.recovered` for that one), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Act on it, as the step of your playbook that waits for that wake says.

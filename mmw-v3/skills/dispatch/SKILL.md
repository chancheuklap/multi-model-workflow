---
name: dispatch
description: Change which host, model or reasoning effort an agent role runs on, or which runner this machine uses. Use when the user asks to change a role's host, model or effort, or the runner.
---

# Dispatch

The scripts that start sessions, wake them and watch them: `scripts/dispatch.sh`, the relay (`scripts/relay.py`), the brief records (`scripts/briefs.py`), the watchdog (`scripts/watchdog.py`), the two hooks (`scripts/turn-guard.py`, `scripts/tool-guard.py`), the runner adapters under `scripts/runners/` and the model configuration (`scripts/models.py`), and the role table (`roles.json`): every agent MMW runs: the sessions a script starts and the subagents a skill uses. Each command is named by the playbook step or skill that runs it. `bash scripts/dispatch.sh` finds the scripts of the skills it calls into by itself, so no path is ever passed to it.

## Changing a role's model, or the runner

Read [references/editing-models.md](references/editing-models.md).

## On waking

The step that ended your turn names the wake it waits for and sends you here first.

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket; the wake carries nothing the tracker does not. For `brief <batch> done`, every session that batch started has reported or been found lost: `bash scripts/dispatch.sh brief show <batch>` lists each brief, its state, and the file its answer is in; read those files.
3. `bash scripts/dispatch.sh ack <n> <event>` with the ticket and the event the wake named (`bash scripts/dispatch.sh ack relay.recovered` for that one, `bash scripts/dispatch.sh ack brief <batch>` for a batch), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Act on it, as the step of your playbook or skill that waits for that wake says. A batch's answers stay readable until `bash scripts/dispatch.sh brief close <batch>`, which stops its sessions and removes them; close it once nothing you still start needs them.

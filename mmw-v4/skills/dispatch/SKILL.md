---
name: dispatch
description: Send a session to work a ticket, review one or answer a brief, run a night as its orchestrator, run one ticket outside a night, or change the host, model, reasoning effort or runner.
---

# Dispatch

`bash scripts/dispatch.sh` finds the scripts of the skills it calls into by itself, so no path is ever passed to it. Where you are is what the ticket's events say, not what this session remembers. The mmw-mode skill's playbooks say when to run each command: Work a ticket for the worker sent to a ticket and the reviewer it sends, Run a night for a night's orchestrator and for one ticket outside a night. `bash scripts/dispatch.sh send <role> <brief file>...` starts one session per file for a role `roles.json` sends with a brief; the step that sends it says what to do when `brief <batch> done` wakes you.

To change which host, model or reasoning effort (`effort` in `models.json`) an agent runs on, or which runner the night runs on, read [references/editing-models.md](references/editing-models.md).

## On waking

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket; the wake carries nothing the tracker does not (**principle-progress-is-what-the-record-says**). For `brief <batch> done`, `bash scripts/dispatch.sh brief show <batch>` lists each brief, its state, and the file its answer is in; read those files.
3. `bash scripts/dispatch.sh ack <n> <event>` with the ticket and the event the wake named (`bash scripts/dispatch.sh ack brief <batch>` for `brief <batch> done`), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Act on it, as the playbook or step that started you says. A batch's answers stay readable until `bash scripts/dispatch.sh brief close <batch>`; close it once nothing you still start needs them.

---
name: dispatch
description: Send a session to work a ticket, review one or answer a brief, run a night as its orchestrator, run one ticket outside a night, change the host, model, reasoning effort, runner or how many tickets a night runs at once, or open the local task board.
---

# Dispatch

`bash scripts/dispatch.sh` finds the scripts of the skills it calls into by itself, so no path is ever passed to it. Where you are is what the ticket's events say, not what this session remembers. The mmw-mode skill's playbooks say when to run each command: Work a ticket for the worker sent to a ticket, including when it sends its reviewer, Run a night for a night's orchestrator, and One ticket for one ticket outside a night. `bash scripts/dispatch.sh send <role> --follow "<what>" <brief file>...` starts one session per file for a role `roles.json` sends with a brief, each told to read the mmw-mode skill and then follow <what>, the file the sending step names; the step that sends it says what to do when `brief <batch> done` wakes you.

To change which host, model or reasoning effort (`effort` in `models.json`) an agent runs on, which runner the night runs on, or how many tickets a night runs at once, read [references/editing-models.md](references/editing-models.md).

## Opening the task board

Run `bash scripts/dispatch.sh board` from any checkout of the repository. Exit 0 opened the board or printed its URL for you to hand the owner; exit 2 says why on stderr. `open` and `open-ticket`, and `send worker` through `open-ticket`, start it themselves and name its URL on the line they print.

## On waking

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket; a ticket's wake carries nothing the tracker does not (**principle-progress-is-what-the-record-says**). For `brief <batch> done`, `bash scripts/dispatch.sh brief show <batch>` lists each brief, its state, and the file its answer is in; read those files.
3. `bash scripts/dispatch.sh ack <n> <event>` with the ticket and the event the wake named (`bash scripts/dispatch.sh ack brief <batch>` for `brief <batch> done`), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Act on it as the step waiting for it says. A batch's answers stay readable until `bash scripts/dispatch.sh brief close <batch>`; close it once no later step reads them.

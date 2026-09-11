---
name: dispatch
description: Start a reviewer or verifier from inside a ticket, run a night as its main agent, run one ticket outside a night, change the host, model, effort or runner, or open the local task board.
---

# Dispatch

Choose the door that matches your role; it holds commands and exit codes together.

## Resolve `<dispatch>` once

`<dispatch>` is `scripts/dispatch.sh`, next to this file. Commands in every door are written `<dispatch>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. `<dispatch>` finds the scripts of other skills by itself, so no directory is passed to it.

Four names in the doors belong to other skills; resolve each from that skill's own `SKILL.md`. `<engine>` is `scripts/verify-ticket.py` of the `verify-ticket` skill, and `<events.py>` is `scripts/events.py` of that same skill, run as `python3 <events.py> …`. `<lease.py>` is `scripts/lease.py` of the `drive-target` skill, and `<drive-target scripts>` is that same skill's `scripts/` directory.

## Find your door

| Door | You are | Read |
| --- | --- | --- |
| 1 | the worker inside a ticket, starting its reviewer or its verifier | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 2 | the main agent running a night on a spec, including routing its findings with `route` on the closing pass and running `finish` after user acceptance | [references/night.md](references/night.md) |
| 3 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 4 | changing which host, model or `effort` an agent runs on, or which runner the night runs on | [references/editing-models.md](references/editing-models.md) |
| 5 | a command's behaviour surprised you, or you are changing the relay, watchdog or turn guard | [references/how-it-works.md](references/how-it-works.md) |
| 6 | opening the local task board | [Open the task board](#open-the-task-board) |

## Open the task board

Run `<dispatch> board` from any checkout or worktree of the consuming repository. It registers the main checkout in `MMW_HOME/boards.json`, reuses that repository's fixed local port, and starts the task board if it is not already answering. The selected runner's adapter opens the URL in the current worktree when it implements `open-url`; otherwise the command prints the exact local URL for you to open. Exit 0 means the tab was opened or the URL was printed. Exit 2 means setup or startup was refused, with the reason on stderr.

## On waking

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket: the event is the answer, and the wake carries nothing the board does not. `<dispatch> wait <n> <kind>` prints a result event by name and key fields (`verifier.failed commit=<commit> failed=AC2 ran=true`) in one line, reading the ticket and nothing else. It is a read, not the way you learn a result.
3. Act on it, as your door says.
4. `<dispatch> ack <n> <event>` with the ticket and the event the wake named (`<dispatch> ack relay.recovered` for that one). Until you ack it, the relay sends the same wake again each time it restarts. An ack looks only at the wakes queued for your own session: one it does not find there — acked already, or sent to another session — is refused and removes nothing.

## The arguments you supply

`<n>`, `<spec>` and `<child>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in `MMW_HOME/models.json` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade the configuration has no row for, is refused (exit 2, stderr names the ticket). The base commit is computed from `origin/<base branch>` and the ticket branch; you do not pass it.

The `adopt` command and its `into` rule are in [references/inside-a-ticket.md](references/inside-a-ticket.md) under **Exit codes**.

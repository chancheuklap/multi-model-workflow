---
name: dispatch
description: Start a reviewer from inside a ticket, run a night as its orchestrator, run one ticket outside a night, change the host, model, reasoning effort or runner, or open the local task board.
---

# Dispatch

Choose the moment that matches your role. Where you are is what the ticket's events say, not what this session remembers. `bash scripts/dispatch.sh` finds the scripts of the skills it calls into by itself, so no path is ever passed to it.

## Find your moment

A **night** is one run of a spec's published tickets under one orchestrator, from `open` to `summary`, at any hour.

| Moment | You are | Read |
| --- | --- | --- |
| 1 | the worker a `start` put on a ticket, starting its reviewer or woken on its ticket | No file: the `implement` skill's `## Closing steps` |
| 2 | a session that picked a ticket up itself, with no `start` behind it | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 3 | the orchestrator running a night on a spec, including routing its findings with `route` on the closing pass and running `finish` after user acceptance | [references/night.md](references/night.md) |
| 4 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 5 | changing which host, model or reasoning effort (`effort` in `models.json`) an agent runs on, or which runner the night runs on | [references/editing-models.md](references/editing-models.md) |
| 6 | opening the local task board | No file: run `bash scripts/dispatch.sh board` from any checkout of the repository. Exit 0 opened the board or printed its URL for you to hand the user; exit 2 says why on stderr |

## On waking

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket; the wake carries nothing the tracker does not.
3. `bash scripts/dispatch.sh ack <n> <event>` with the ticket and the event the wake named (`bash scripts/dispatch.sh ack relay.recovered` for that one), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. A `watchdog:` or `MMW turn guard:` line is not acked.
4. Act on it, as your moment's file says.

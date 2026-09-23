---
name: dispatch
description: Start a reviewer from inside a ticket, run a night as its main agent, run one ticket outside a night, change the host, model, reasoning effort or runner, or open the local task board.
---

# Dispatch

Choose the moment that matches your role.

## Resolve `<dispatch>` once

`<dispatch>` is `scripts/dispatch.sh`, next to this file. Commands in this skill are written `<dispatch>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
```

Resolve it from this file's own location; the path differs by machine and by host. `<dispatch>` finds the scripts of other skills by itself, so no directory is passed to it.

Four names in the references belong to other skills; resolve each from that skill's own `SKILL.md`. `<engine>` is `scripts/verify-ticket.py` of the `verify-ticket` skill, and `<events.py>` is `scripts/events.py` of that same skill, run as `python3 <events.py> …`. `<lease.py>` is `scripts/lease.py` of the `ui-acceptance` skill, and `<ui-acceptance scripts>` is that same skill's `scripts/` directory.

## Find your moment

A **night** is one run of a spec's published tickets under one main agent, from `open` to `summary`, at any hour.

| Moment | You are | Read |
| --- | --- | --- |
| 1 | the worker a `start` put on a ticket, starting its reviewer or woken on its ticket | No file: the `implement` skill's `## Closing steps` |
| 2 | a session that picked a ticket up itself, with no `start` behind it | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 3 | the main agent running a night on a spec, including routing its findings with `route` on the closing pass and running `finish` after user acceptance | [references/night.md](references/night.md) |
| 4 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 5 | changing which host, model or reasoning effort (`effort` in `models.json`) an agent runs on, or which runner the night runs on | [references/editing-models.md](references/editing-models.md) |
| 6 | opening the local task board | No file: run `<dispatch> board` from any checkout of the repository. Exit 0 opened the board or printed its URL for you to hand the user; exit 2 says why on stderr |

## On waking

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket; the wake carries nothing the tracker does not.
3. `<dispatch> ack <n> <event>` with the ticket and the event the wake named (`<dispatch> ack relay.recovered` for that one), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts.
4. Act on it, as your moment's file says.

## The arguments you supply

`<n>`, `<spec>` and `<child>` are digits only, no `#`.

`start`'s third argument is `worker` or `reviewer`. The base commit is computed from `origin/<base branch>` and the ticket branch; you do not pass it.

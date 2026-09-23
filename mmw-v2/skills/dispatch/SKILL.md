---
name: dispatch
description: Start a reviewer from inside a ticket, run a night as its main agent, run one ticket outside a night, change the host, model, effort or runner, or open the local task board.
---

# Dispatch

Choose the moment that matches your role; its file holds commands and exit codes together.

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
| 1 | the worker inside a ticket, starting its reviewer | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 2 | the main agent running a night on a spec, including routing its findings with `route` on the closing pass and running `finish` after user acceptance | [references/night.md](references/night.md) |
| 3 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 4 | changing which host, model or `effort` an agent runs on, or which runner the night runs on | [references/editing-models.md](references/editing-models.md) |
| 5 | a command's behaviour surprised you, or you are changing the relay, watchdog or turn guard | [references/how-it-works.md](references/how-it-works.md) |
| 6 | opening the local task board | [references/task-board.md](references/task-board.md) |

## On waking

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket: the event is the answer, and the wake carries nothing the tracker does not. `<dispatch> wait <n> <kind>` prints a result event by name and key fields (`reviewer.reported base=<commit> head=<commit>`) in one line, reading the ticket and nothing else. It is a read, not the way you learn a result.
3. `<dispatch> ack <n> <event>` with the ticket and the event the wake named (`<dispatch> ack relay.recovered` for that one), once you have read it and before any long work it starts. Until you ack it, the relay sends the same wake again each time it restarts. Exit `0`: that wake is acked — the relay removes it, and every earlier wake it sent this session, from the wake queue. Exit `2`: nothing was acked: this session cannot name itself (its runner's reason is on stderr), or no wake with that ticket and event is queued for this session — acked already, sent to another session, or never queued — and stderr lists the wakes that are queued for it (check the number and the event name against the wake you read).
4. Act on it, as your moment's file says.

## The arguments you supply

`<n>`, `<spec>` and `<child>` are digits only, no `#`.

`start`'s third argument is `worker` or `reviewer`. Which of the two worker rows in `MMW_HOME/models.json` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade the configuration has no row for, is refused (exit 2, stderr names the ticket). The base commit is computed from `origin/<base branch>` and the ticket branch; you do not pass it.

The `adopt` command and its `into` rule are in [references/inside-a-ticket.md](references/inside-a-ticket.md) under **Exit codes**.

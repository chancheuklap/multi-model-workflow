---
name: dispatch
description: Put another agent to work on a ticket, move a night's batch of tickets forward, or open the local task board. Use to start a worker, reviewer or verifier, to replace a stuck worker, to retract a start whose session is gone, to resume a worker, to check the machine before a night, to open a night or one ticket, to advance a spec, to suspend a night, to read what woke you about an agent you started and acknowledge that wake, to route a finding on the closing pass, to reverify closed tickets, to post the night summary, to finish a night after user acceptance by merging its base branch into its project branch and cleaning up, or to change which host, model or thinking level an agent in this pipeline runs on.
---

# Dispatch

Nothing here runs on its own. To open the task board, use `Open the task board` below. For pipeline work, pick your door in `Find your door` and read that file: the commands you run and the exit codes you act on are in it, next to each other.

## Resolve `<dispatch>` once

`<dispatch>` is `scripts/dispatch.sh`, next to this file. Commands in every door are written `<dispatch>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. `<dispatch>` finds the scripts of other skills by itself, so no directory is passed to it.

Four names in the doors belong to other skills; resolve each from that skill's own `SKILL.md`. `<engine>` is `scripts/verify-ticket.py` of the `verify-ticket` skill, and `<events.py>` is `scripts/events.py` of that same skill, run as `python3 <events.py> …`. `<lease.py>` is `scripts/lease.py` of the `drive-target` skill, and `<drive-target scripts>` is that same skill's `scripts/` directory.

## Start runs the session

`start` starts the session itself and prints its id, one line; `advance` prints one such line per ticket it starts. Which runner runs it is tonight's runner: `MMW_RUNNER`, else `runner` in `MMW_HOME/models.json`, else, when that saved value is `auto`, the runner this session itself runs in when this skill has an adapter for it, else `orca`; the agent's row in that JSON file is resolved against that runner's catalog. Once the session runs, `start` has the runner's adapter attach the worktree to the ticket where that runner can show it; a failed attach is reported once on stderr and does not stop the session. `start` also writes a `worker.started`, `reviewer.started` or `verifier.started` event on the ticket — the session, its runner, host, model, effort, grade, the worktree's absolute path, the ticket branch, the base branch (`into`) and the base commit — and every later command — `resume`, `wait`, `retract`, `land`, `suspend` — finds the session in that event and asks that runner, and no other.

Before it reads or creates a ticket branch, `start` fetches `origin`. The base branch is the newest `worker.started.into`, else the open night's `spec.opened.into`, else — outside a night — the current checkout branch; `origin/<base branch>` must exist. A new ticket branch is cut from `origin/<base branch>` and immediately pushed with its upstream set. An existing `origin/issue-<n>` fast-forwards the local branch when the remote is ahead; histories with commits on both sides are refused with both counts. No path rebases, squashes or force-pushes.

A worker takes no product slot when it starts. The first run of its criteria that runs the product claims the worktree's slot, and the worktree keeps it until the ticket's work ends: it lands, is handed back, bounces during landing, has its claim released, the night is suspended, or its start is retracted. While the product's `instance.max` or the machine's slots are all held, that run runs nothing, its ticket carries a `worker.queued` event, and the worker ends its turn until a slot is given back.

`start <n> worker` on a ticket whose events still show a live worker replaces that worker: origin and the ticket branch are checked first, then the old session is stopped through its own runner, its tracked edits are committed on the ticket branch as `wip(#<n>): uncommitted work of <that worker>`, and that branch is pushed to origin before a `worker.replaced` event and the new `worker.started` are written. A worker that will not stop, or a rejected push, is refused (exit 2) and nothing is started beside it. `retract` and `suspend` likewise commit and push the ticket branch before they release a worktree, claim, slot or event hold. A push rejection never uses force and leaves the ticket's recoverable state standing.

Every comment this pipeline writes on a ticket is such an event: a first line for a person, and a trailing `<!-- mmw {...} -->` block that is the only thing a program reads. Where a ticket stands is computed by replaying its events (`scripts/events.py` of the `verify-ticket` skill); a first line is never read. A ticket is **held** from its `ticket.claimed` or any `*.started` until an event ends the hold: `ticket.landed`, `ticket.returned`, `ticket.bounced`, `ticket.released` or `spec.suspended` end every hold on it, and `worker.retracted`, `worker.lost`, `worker.replaced` or a `ticket.refused` that names its session end the one session they name by its runner and its id together. `ticket.passed` ends none — the close after a pass can fail and leave the worker retrying — and no label ends one. That holds whichever runner and whichever machine the worker runs on.

A start the runner refuses is refused once, exit 2, with the runner's reason on stderr: nothing is retried, and no other host or runner is tried. Fix what it names, or change that agent's row as `references/editing-models.md` says, then `start` again; if you cannot, `<engine> <n> --sub-issue fault <file>` with the command and its output as the file's body, then stop.

## What tells you it is done

The session you started is working the moment `start` returns, and you end your turn: you are woken, you never wait or ask. Its result lands on the ticket as an event — `ticket.passed` or `ticket.returned` from a worker, `reviewer.reported` from a reviewer, `verifier.passed` or `verifier.failed` from a verifier — and the **relay**, a process that watches the board from the moment the main agent opens the night (or the one ticket), sends the session waiting on that event a **wake**: a message `#<n> <event>`, the ticket number and the event's name and nothing else. A worker is woken for its reviewer's `reviewer.reported` and its verifier's `verifier.passed` or `verifier.failed`, for `reviewer.lost` or `verifier.lost` when that session died with no result, and with `#<n> worker.queued` when its ticket waits for a product slot and a slot has been given back. The main agent is woken for `ticket.passed`, `ticket.returned`, `ticket.refused`, a `child.opened` of kind `fault` or `decision`, `worker.lost`, and `relay.recovered since <time>` — the relay was down or could not read the board from that time on, has read every ticket again, and the wakes for what it found follow this one.

On waking:

1. A wake can cut short a command you were running. Run that command again first.
2. Read what the wake names on the ticket: the event is the answer, and the wake carries nothing the board does not. `<dispatch> wait <n> <kind>` prints a result event by name and key fields (`verifier.failed commit=<commit> failed=AC2 ran=true`) in one line, reading the ticket and nothing else. It is a read, not the way you learn a result.
3. Act on it, as your door says.
4. `<dispatch> ack <n> <event>` with the ticket and the event the wake named (`<dispatch> ack relay.recovered` for that one). Until you ack it, the relay sends the same wake again each time it restarts. An ack looks only at the wakes queued for your own session: one it does not find there — acked already, or sent to another session — is refused and removes nothing.

What the relay reads is its watches: a night's spec, from `open` to `summary` or `suspend`, and tickets outside a night, from `open-ticket` (or `adopt`) to `land`. Each watch wakes its own main agent, the session that opened it, and two watches never share a ticket; one relay process per repository carries them all, and ends with the last. `start` and `advance` refuse a ticket no running relay watches (exit 2): its result would land and wake nobody.

A session that dies writes nothing, so the relay has nothing to send. Two things that are not agents cover that. The **watchdog** is a process of its own, one per repository, that the **turn guard** — a hook on your host's turn end, installed by `install.sh` — starts again at the end of each of your turns while a watch is open and it is not running. Every minute it checks the relay, and for each held open ticket that has had no event for ten minutes, or is waiting for a product slot however recently, it asks each session still holding it — the worker, and a reviewer or verifier whose result is not in yet — whether it is still there, through that session's own runner, and only when the session was started on this machine. A session its runner says has stopped gets `worker.lost`, `reviewer.lost` or `verifier.lost` written on the ticket, and the relay sends that as a wake like any other: `worker.lost` to the main agent, the other two to the ticket's worker. Everything else it finds reaches the main agent of the ticket's watch as one message, each finding in it beginning `watchdog:` — the relay is down, a runner could not say whether a session is alive or the session was started on another machine, a held ticket has no session to ask, a worker is alive and has been silent for an hour with nothing to wait on, a ticket's events cannot be read, the watchdog itself cannot read the board — each once; those are not queued rows, so there is nothing to ack. While tickets are held and the watchdog is not running, the turn guard keeps your turn from ending, or, on a host that cannot hold a turn, sends you one message; its text names the one command to run.

## The arguments you supply

`<n>`, `<spec>` and `<child>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in `MMW_HOME/models.json` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade the configuration has no row for, is refused (exit 2, stderr names the ticket). The base commit is computed from `origin/<base branch>` and the ticket branch; you do not pass it.

`adopt <n>` uses the same `into` lookup as `start`. Outside an open night, a ticket with no prior `worker.started.into` is adopted with `adopt <n> --into <branch>`; that branch must exist on origin. A latest `worker.started` with no `into` is refused with the instruction to re-start it.

## Open the task board

Run `<dispatch> board` from any checkout or worktree of the consuming repository. It registers the main checkout in `MMW_HOME/boards.json`, reuses that repository's fixed local port, and starts the task board if it is not already answering. The selected runner's adapter opens the URL in the current worktree when it implements `open-url`; otherwise the command prints the exact local URL for you to open. Exit 0 means the tab was opened or the URL was printed. Exit 2 means setup or startup was refused, with the reason on stderr.

## Find your door

| Door | You are | Read |
| --- | --- | --- |
| 1 | the worker inside a ticket, starting its reviewer or its verifier | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 2 | the main agent running a night on a spec, including routing its findings with `route` on the closing pass and running `finish` after user acceptance | [references/night.md](references/night.md) |
| 3 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 4 | changing which host, model or `effort` an agent runs on, or which runner the night runs on | [references/editing-models.md](references/editing-models.md) |

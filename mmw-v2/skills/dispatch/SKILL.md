---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a worker, reviewer or verifier, to replace a stuck worker, to retract a start whose session is gone, to resume a worker, to check the machine before a night, to advance a spec, to suspend a night, to read status after being woken by an agent you started, to route a finding on the closing pass, to reverify closed tickets, to post the night summary, or to change which host, model or thinking level an agent in this pipeline runs on.
---

# Dispatch

Nothing here runs on its own. Pick your door in `Find your door` below and read that file: the commands you run and the exit codes you act on are in it, next to each other.

## Resolve `<dispatch>` once

`<dispatch>` is `scripts/dispatch.sh`, next to this file. Commands in every door are written `<dispatch>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. `<dispatch>` finds the scripts of other skills by itself, so no directory is passed to it.

Four names in the doors belong to other skills; resolve each from that skill's own `SKILL.md`. `<engine>` is `scripts/verify-ticket.py` of the `verify-ticket` skill, and `<events.py>` is `scripts/events.py` of that same skill, run as `python3 <events.py> …`. `<lease.py>` is `scripts/lease.py` of the `drive-target` skill, and `<drive-target scripts>` is that same skill's `scripts/` directory.

## Start runs the session

`start` starts the session itself and prints its id, one line; `advance` prints one such line per ticket it starts. Which runner runs it is tonight's runner: `MMW_RUNNER`, else the `runner` row of the live table, else the runner this session itself runs in, else `orca`. `start` also writes a `worker.started`, `reviewer.started` or `verifier.started` event on the ticket — the session, its runner, host, model, effort, grade, the worktree's absolute path, the branch and the base commit — and every later command — `resume`, `wait`, `retract`, `land`, `suspend` — finds the session in that event and asks that runner, and no other.

A worker takes no product slot when it starts. The first run of its criteria that runs the product claims the worktree's slot, waiting while the product's `instance.max` or the machine's slots are all held — its ticket carries a `worker.queued` event meanwhile — and the worktree keeps the slot until the ticket lands.

`start <n> worker` on a ticket whose events still show a live worker replaces that worker: the old session is stopped through its own runner first, then a `worker.replaced` event naming it and a `worker.started` for the new one go on the ticket. A worker that will not stop is refused (exit 2) and nothing is started beside it.

Every comment this pipeline writes on a ticket is such an event: a first line for a person, and a trailing `<!-- mmw {...} -->` block that is the only thing a program reads. Where a ticket stands is computed by replaying its events (`scripts/events.py` of the `verify-ticket` skill); a first line is never read. A ticket is **held** from its `ticket.claimed` or any `*.started` until an event ends the hold: `ticket.landed`, `ticket.returned`, `ticket.released` or `spec.suspended` end every hold on it, and `worker.retracted`, `worker.lost` or `worker.replaced` end the one session they name by its runner and its id together. `ticket.passed` ends none — the close after a pass can fail and leave the worker retrying — and no label ends one. That holds whichever runner and whichever machine the worker runs on.

A start the runner refuses is refused once, exit 2, with the runner's reason on stderr: nothing is retried, and no other host or runner is tried. Fix what it names, or change that agent's row in the live table, then `start` again; if you cannot, `<engine> <n> --sub-issue fault <file>` with the command and its output as the file's body, then stop.

## What tells you it is done

The session you started is working the moment `start` returns. Its result lands on the ticket as an event: `ticket.passed` or `ticket.returned` from a worker, `reviewer.reported` from a reviewer, `verifier.passed` or `verifier.failed` from a verifier. `<dispatch> wait <n> <kind>` reads that event: exit 0 prints its name and key fields (`verifier.failed commit=<commit> failed=AC2 ran=true`), and that name is what you act on; exit 3 means still working — run it again — and exit 1 means the session is gone with no result. Keep running `wait` until it answers 0 or 1; do not end your turn in between, because nothing on an Orca or Herdr session will wake you.

One more thing can arrive while you wait, and only when both sessions are on Paseo: a **ticket message**, a plain message `#<n> <event>` — `#<n> ticket.passed`, `#<n> ticket.returned`, `#<n> ticket.refused`, `#<n> child.opened kind=fault` or `#<n> reviewer.reported` — which `verify-ticket.py` sends through Paseo to the session that started the agent, in the same call that posts that event. It interrupts: a command running when it arrives is cut short, so run that command again. It says which ticket and which event; `status` says the rest.

## The arguments you supply

`<n>`, `<spec>` and `<child>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in the live table (`~/.mmw/models.md`) a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade the live table has no row for, is refused (exit 2, stderr names the ticket). The reviewer reads `git config branch.issue-<n>.mmw-base` itself; you do not pass a base commit.

## Find your door

| Door | You are | Read |
| --- | --- | --- |
| 1 | the worker inside a ticket, starting its reviewer or its verifier | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 2 | the main agent running a night on a spec, including routing its findings with `route` on the closing pass | [references/night.md](references/night.md) |
| 3 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 4 | changing which host, model or `effort` an agent runs on, or which runner the night runs on | [references/editing-models.md](references/editing-models.md) |

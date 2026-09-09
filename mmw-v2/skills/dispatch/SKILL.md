---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a worker, reviewer or verifier, to retract a start whose create_agent never ran, to resume a worker, to check the machine before a night, to advance a spec, to suspend a night, to read status after being woken by an agent you started, to reverify closed tickets, to post the night summary, or to change which host, model or thinking level an agent in this pipeline runs on.
---

# Dispatch

Nothing here runs on its own. Pick your door in `Find your door` below and read that file: the commands you run and the exit codes you act on are in it, next to each other.

## Resolve `<dispatch>` once

`<dispatch>` is `scripts/dispatch.sh`, next to this file. Commands in every door are written `<dispatch>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
```

Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. `<dispatch>` finds the scripts of other skills by itself, so no directory is passed to it.

Three names in the doors belong to other skills; resolve each from that skill's own `SKILL.md`. `<engine>` is `scripts/verify-ticket.py` of the `verify-ticket` skill. `<lease.py>` is `scripts/lease.py` of the `drive-target` skill, and `<drive-target scripts>` is that same skill's `scripts/` directory.

## One path: create_agent

`start` and `advance` print one JSON object per ticket, one line, whose fields are the arguments of `create_agent` (`workspaceId`, `title`, `provider`, `settings`, `notifyOnFinish`, `labels`, `initialPrompt`). A second live-table row for that agent is nested as `fallback`, itself a complete `create_agent` object: same `workspaceId`, `title`, `initialPrompt` and `notifyOnFinish`; `provider` and `settings` are the fallback host's. Call `create_agent` with every field except `fallback` — every remaining field is already decided, `notifyOnFinish` included. A session with no `create_agent` tool cannot dispatch: say so and stop.

When that call fails, this row is the next step:

| What happened | What you do |
| --- | --- |
| `create_agent` failed to start the provider | The error names provider initialization (`Failed to initialize session services` is one). Retry `create_agent` with the same object (every field except `fallback`) up to five times, waiting about 1, 2, 4, 8, then 16 seconds after each failure. After the fifth retry still fails: if the printed object had `fallback`, call `create_agent` with that object once, then comment on the ticket with first line `HOST <host> (fallback)`, naming the host that ran. If that call fails too, or there was no `fallback`: `<dispatch> retract <n>`, then `<engine> <n> --sub-issue pipeline <file>` — the file's body is every error you saw — then stop. `inspect_provider` is not a step on this path: it does not refresh the snapshot, and its success path hangs on `session/new` with no bound (measured 300s) |

Only this path exists, and for two reasons rather than a whole list. One is the finish notification: the daemon wires it for an MCP caller and for nobody else, so a reviewer or a verifier started any other way would never wake the worker waiting on it. The other is `settings.features` — the per-host toggle an ACP host takes its unattended standing from — which no CLI form can set, at creation or afterwards, so a worker started any other way stops at its first permission prompt and waits all night. Parentage, the archive cascade, the app tree and labels are not among the reasons: a session started from the CLI carries those too. The CLI is the side scripts read facts on and people use.

## Start means the agent is running

The moment `create_agent` returns, that agent is working. Then end your turn. What wakes you is the agent you just started having something to say, and until then there is nothing to do: a verifier wakes the worker through Paseo's own notification, and a reviewer and a worker both wake theirs through `verify-ticket.py`, which sends its message in the same call that writes the report or closes the ticket. Never sit in a loop asking another Paseo session whether it is done yet.

## What wakes you

Two things wake a session here, and they arrive differently.

A **finish notification** is a `<paseo-system>` block whose first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.`, and which may carry an `<agent-response>` of the agent's last reply. It arrives in the current turn when you are busy, or as a new turn when you are idle, and it never interrupts a command you are running. Match `<title>` to `#<n> reviewer` or `#<n> verifier`. One `create_agent` yields one terminal notification, spent the first time that agent ends a turn — which is why a worker is started with `notifyOnFinish: false` and says it is done another way. `needs permission` is not a stop: run `list_pending_permissions` / `respond_to_permission` (CLI: `paseo permit`) first, then `status`. A worker never sends one, being started with `notifyOnFinish: false`, so a worker waiting on a permission shows only as the `needs permission` note in `status`.

A **ticket message** is a plain message whose first line is `#<n> ALL MET`, `#<n> HANDOFF REQUIRED`, `#<n> NOT_READY`, `#<n> SUB-ISSUE pipeline` or `#<n> REVIEW`. `verify-ticket.py` sends it in the same call that writes what it is about: the first four to the session that started the worker, at the moment the ticket comes to rest; `#<n> REVIEW` to the session that started the reviewer, at the moment the review report lands on the ticket. Unlike a notification it does interrupt: a command running when it arrives is cut short and reports being interrupted, so run that command again before acting on the message. The first line says which ticket, and `status` says the rest — read it rather than trusting the line.

## The arguments you supply

`<n>` and `<spec>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in the live table (`~/.mmw/models.md`) a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade the live table has no row for, is refused (exit 2, stderr names the ticket). The reviewer reads `git config branch.issue-<n>.mmw-base` itself; you do not pass a base commit.

## Find your door

| Door | You are | Read |
| --- | --- | --- |
| 1 | the worker inside a ticket, starting its reviewer or its verifier | [references/inside-a-ticket.md](references/inside-a-ticket.md) |
| 2 | the main agent running a night on a spec | [references/night.md](references/night.md) |
| 3 | starting one worker on one ticket, outside any night | [references/one-ticket.md](references/one-ticket.md) |
| 4 | changing which host, model or `effort` an agent runs on, or whether the night runs on Herdr or Paseo | [references/editing-models.md](references/editing-models.md) |

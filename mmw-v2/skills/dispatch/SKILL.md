---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a worker, reviewer or verifier, to retract a start whose create_agent never ran, to resume a worker, to check the machine before a night, to advance a spec, to suspend a night, to read status after being woken by an agent you started, to reverify closed tickets, to post the night summary, or to change which host, model or thinking level an agent in this pipeline runs on.
---

# Dispatch

Nothing here runs on its own. You arrive at one row of the `Find your command` table below, run its command, and act on its exit code.

## Resolve the scripts once

`scripts/dispatch.sh` and `scripts/status.py`, next to this file. Commands below are written `<dispatch>` and `<status>` and mean:

```bash
bash <absolute path to scripts/dispatch.sh> …
python3 <absolute path to scripts/status.py> …
```

Resolve them from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from. `<engine>` is `scripts/verify-ticket.py` of the `verify-ticket` skill; resolve it from that skill's SKILL.md.

`<dispatch>` runs two scripts of other skills — `lease.py` of the `drive-target` skill and `verify-ticket.py` — and finds them only in the directories you pass as `--tools`, one flag per directory, anywhere on the line:

```bash
bash <absolute path to scripts/dispatch.sh> --tools <drive-target scripts> --tools <verify-ticket scripts> …
```

Resolve both `scripts/` directories from those skills' own `SKILL.md`. Every command below is written without the two flags; add them to each. A form that needs one of the scripts and cannot find it exits 2 and names the directory to pass.

## One path: create_agent

`start` and `advance` print one JSON object per ticket, one line, whose fields are the arguments of `create_agent` (`workspaceId`, `title`, `provider`, `settings`, `notifyOnFinish`, `labels`, `initialPrompt`). A second `bypass` row for that agent is nested as `fallback`, itself a complete `create_agent` object: same `workspaceId`, `title`, `initialPrompt` and `notifyOnFinish`; `provider`, `settings` and `labels.mmw.profile` are the fallback host's. Call `create_agent` with every field except `fallback` — every remaining field is already decided, `notifyOnFinish` included. A session with no `create_agent` tool cannot dispatch: say so and stop.

When that call fails, the `create_agent` failed to start the provider row of `Find your command` is the next step.

Only this path exists, and for two reasons rather than a whole list. One is the finish notification: the daemon wires it for an MCP caller and for nobody else, so a reviewer or a verifier started any other way would never wake the worker waiting on it. The other is `settings.features` — the per-host toggle an ACP host takes its unattended standing from — which no CLI form can set, at creation or afterwards, so a worker started any other way stops at its first permission prompt and waits all night. Parentage, the archive cascade, the app tree and labels are not among the reasons: a session started from the CLI carries those too. The CLI is the side scripts read facts on and people use.

Then end your turn. What wakes you is the agent you just started having something to say, and until then there is nothing to do: a verifier wakes the worker through Paseo's own notification, and a reviewer and a worker both wake theirs through `verify-ticket.py`, which sends its message in the same call that writes the report or closes the ticket. Never sit in a loop asking another Paseo session whether it is done yet.

## Find your command

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket | `<dispatch> start <n> reviewer`, then the one path above, then end your turn. What wakes you is a message whose first line is `#<n> REVIEW`, sent by the same call that posts the report; then read the ticket for the comment whose first line is `REVIEW `. **Start exits 2:** stderr is the reason; nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`; the file's body is the command you ran and the output you saw; then stop. **`wait` exits 1 (the reviewer stopped and there is no `REVIEW ` comment):** `paseo logs <id>`, then run the `code-review` skill in this host's general-purpose subagent with ticket `<n>` and base commit `$(git config branch.issue-<n>.mmw-base)`; its report lands with the same `REVIEW ` first line. Do not start a second reviewer. |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`, then the one path above, then end your turn. The verifier finishing wakes you; then read the ticket for the comment whose first line is `VERDICT`. Start it once. **Start exits 2:** stderr is the reason; nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`; the file's body is the command you ran and the output you saw; then stop. |
| Open the night on a spec | [references/night.md](references/night.md): `<dispatch> check <spec>` (it also creates the night's heartbeat), then `<dispatch> advance <spec>`, then the one path above |
| You were woken for an agent you started and its result is not on the ticket | `<dispatch> wait <n> worker\|reviewer\|verifier`: prints the first line of its result comment (`ALL MET` / `HANDOFF REQUIRED`, `REVIEW …`, `VERDICT …`), reading the ticket before it waits at all. Exit 3: still working, run it again. Exit 1: it stopped without a result; stderr names the next step. Exit 2: no such agent |
| Something woke you — a finish notification, or a message whose first line is `#<n> …` | `<dispatch> land <n>` for the ticket the message names, then `<dispatch> status <spec>` and the decision table in [references/night.md](references/night.md). The message carries the ticket number, which is all `land` needs; a ticket outside any batch has no `<spec>` and stops after `land` |
| Land a ticket that has come to rest | `<dispatch> land <n>`: run the product's `stop` in its worktree, merge its branch, archive its workspace (agents inside it included), give its slot and its claim back. Takes a ticket number, never a spec, so it is the whole ending for a ticket dispatched outside a night. Exit 1: at least one closed ticket was left unmerged and stderr names it. A ticket whose product would not go down keeps its workspace and is named on stderr — archiving deletes the worktree the `stop` command lives in, so that one is left recoverable |
| Land everything on this checkout that is finished | `<dispatch> land --sweep`. Run it when a night has been quiet longer than it should be, or after any interruption: it needs no wake-up message to have arrived, and no spec |
| Tell a live worker to continue | `<dispatch> resume <n> "<text>"`. Exit 0: the text was sent. **Exit 3:** the worker is there but did not take it — it is in a turn, and a turn ends: wait and run the same command again. Paseo dispatches the message before it confirms the turn started, so a 3 does not prove nothing arrived: word the retry so that a worker which got both reads them as one instruction. **Exit 2:** no worker labelled `mmw.ticket=<n>` — read `status`, do not send again |
| `resume` keeps exiting 3 and you need to know whether it is working or stuck | Ask `get_agent_status` for that agent. `activeTurn` naming a turn: it is working, keep waiting. `activeTurn` of null while the send still fails: the session is stuck — a rejected send left `lastError` set and the send path reads that field, so it will never take a message again. Archive it and `<dispatch> start <n> worker`, which reuses the standing workspace and branch. Everything the worker was told in this session is gone with it |
| Start a worker on one ticket, outside a night | `<dispatch> start <n> worker`, then the one path above. When that ticket comes to rest, `<dispatch> land <n>` is what ends it: no `advance` will, because a ticket outside a night belongs to no spec |
| `create_agent` failed to start the provider | The error names provider initialization (`Failed to initialize session services` is one). Retry `create_agent` with the same object (every field except `fallback`) up to five times, waiting about 1, 2, 4, 8, then 16 seconds after each failure. After the fifth retry still fails: if the printed object had `fallback`, call `create_agent` with that object once, then comment on the ticket with first line `HOST <host> (fallback)`, naming the host that ran. If that call fails too, or there was no `fallback`: `<dispatch> retract <n>`, then `<engine> <n> --sub-issue pipeline <file>` — the file's body is every error you saw — then stop. `inspect_provider` is not a step on this path: it does not refresh the snapshot, and its success path hangs on `session/new` with no bound (measured 300s) |
| Take back a start whose `create_agent` never ran | `<dispatch> retract <n>`: run the product's `stop` in its worktree, archive the workspace, give the slot back, give the claim back if this pipeline holds it. The branch stays, so the next `start` reuses it. `slot given back` is 1 only when the lease was actually released, and `archived` is 1 only when the workspace actually went — a product still listening keeps both at 0 and stderr says where to stop it. Exit 2 if a live agent is still on the ticket, or if a slot is held and `--tools` did not pass `lease.py` |
| Re-run every closed `ALL MET` ticket on the branch you are on | `<dispatch> reverify <spec>` |
| Post the night summary on the spec | `<dispatch> summary <spec>` |
| Give the night up before it is over | `<dispatch> suspend <spec>` — [references/night.md](references/night.md) says what it stops and what it leaves standing |
| Change one ticket's worker grade | Swap its `junior-worker` / `senior-worker` label on the tracker; the next `start` reads it |
| Change which host, model or `effort` an agent runs on | Edit `models.md`, next to this file — but read [references/editing-models.md](references/editing-models.md) first |

The night itself — `check`, then `advance`, then what to do on each notification until the frontier is empty — is [references/night.md](references/night.md).

## What wakes you

Two things wake a session here, and they arrive differently.

A **finish notification** is a `<paseo-system>` block whose first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.`, and which may carry an `<agent-response>` of the agent's last reply. It arrives in the current turn when you are busy, or as a new turn when you are idle, and it never interrupts a command you are running. Match `<title>` to `#<n> reviewer` or `#<n> verifier`. One `create_agent` yields one terminal notification, spent the first time that agent ends a turn — which is why a worker is started with `notifyOnFinish: false` and says it is done another way. `needs permission` is not a stop: run `list_pending_permissions` / `respond_to_permission` (CLI: `paseo permit`) first, then `status`. A worker never sends one, being started with `notifyOnFinish: false`, so a worker waiting on a permission shows only as the `needs permission` note in `status`.

A **ticket message** is a plain message whose first line is `#<n> ALL MET`, `#<n> HANDOFF REQUIRED`, `#<n> NOT_READY`, `#<n> SUB-ISSUE pipeline` or `#<n> REVIEW`. `verify-ticket.py` sends it in the same call that writes what it is about: the first four to the session that started the worker, at the moment the ticket comes to rest; `#<n> REVIEW` to the session that started the reviewer, at the moment the review report lands on the ticket. Unlike a notification it does interrupt: a command running when it arrives is cut short and reports being interrupted, so run that command again before acting on the message. The first line says which ticket, and `status` says the rest — read it rather than trusting the line.

The night's heartbeat is created in [references/night.md](references/night.md) step 1.

## The arguments you supply

`<n>` and `<spec>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in `models.md` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade `models.md` has no row for, is refused (exit 2, stderr names the ticket). The reviewer reads `git config branch.issue-<n>.mmw-base` itself; you do not pass a base commit.

## Exit codes

**`start <n> worker\|reviewer\|verifier`:**

| Code | What happened |
| --- | --- |
| `0` | One JSON object is on stdout. A second `bypass` row for that agent is nested as `fallback` |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; two worker-grade labels; no `bypass` row in `models.md` for that agent; no `## Parent` spec number; no recorded base commit (reviewer); the Paseo daemon could not be asked to register this checkout as a project; an argument this form does not take |

**`advance <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. One JSON object per dispatched ticket on stdout; the line `advance #<spec>: merged <m>, already in <s>, released <g>, started <k>, refused <r>, held <h>` is on stderr. `merged` counts only tickets that closed `ALL MET`; an open ticket's branch is never merged. Each claim given back prints a line of its own naming the ticket and why; when nothing could start and tickets are still in the agent queue, stderr names every one of them and the condition holding it |
| `2` | Nothing was touched. Stderr: not a git repository, uncommitted tracked changes, or the `.git` lock was held for `MERGE_TRIES` tries — run `advance` again |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was archived, no workspace was created, nothing was dispatched. **The conflict is still in the tree and it stays there.** Resolve it with the `resolving-merge-conflicts` skill, run this repository's own checks, commit the merge, then run `advance` again. The conflict report (stderr) already names the two sides and the conflicted files |

**`land <n>` / `land --sweep`:**

| Code | What happened |
| --- | --- |
| `0` | Done. Stderr carries one line per merge and the tally `land: merged <m>, archived <a>, released <r>, still working <w>, left unmerged <u>`. A ticket still being worked is named on stderr and nothing is done to it |
| `1` | Everything else was landed, and at least one closed ticket was left standing because its branch is not in `HEAD`. Stderr names each. Archiving deletes the worktree, so this one waits for you: merge that branch, or decide the work is abandoned and archive it yourself |
| `2` | Nothing was touched: not a git repository, uncommitted tracked changes, or a ticket number that is not digits |
| `3` | A merge is in conflict and is still in the tree. Same as `advance`: resolve it with the `resolving-merge-conflicts` skill, run this repository's checks, commit the merge, then run `land` again |

**`check <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | `install.sh --check` passed, the first `bypass` row of each worker grade, reviewer and verifier has its host `available` in `paseo provider ls --json`, and every queued ticket has at most one worker-grade label that `models.md` has a row for. In a Paseo session (`PASEO_AGENT_ID` set) the night's heartbeat `mmw-night-<spec>` now exists, at 7 and 47 minutes past each hour, its id in `.git/mmw-heartbeat-<spec>`; outside one, stderr says no heartbeat was made |
| `2` | One or more of those failed, or the heartbeat could not be created. Stderr has one `dispatch: …` line per failure. Fix what the lines name — run `install.sh`, relabel the ticket, or wait until the host is `available` — then `check` again. Do not `advance` on 2 |

**`retract <n>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. Stderr: `retract #<n>: archived <a>, slot given back <s>, claim given back <c>` |
| `2` | Nothing was touched. A live agent is on the ticket, a slot is held and `lease.py` was not in `--tools`, or not a git repository, or the number is not digits |

**`resume <n> "<text>"`:** `0` the text was sent; `3` the worker is there and did not take it, nothing sent — it is in a turn, so wait and run the same command again; `2` no worker with those labels, nothing sent.

`3` and `2` are told apart by what the command already knows rather than by reading Paseo's error text: the agent was found by label a moment earlier, so a send that fails after that is not "no such worker". Both used to be `2`, whose documented meaning is "do not send again" — which is the wrong answer to a worker that is merely busy, and on 2026-09-07 (#211) it cost a five-hour session with 16 commits on its branch.

**`status <spec>`:** `0`, stdout is the table (`ticket`, `agent`, `id`, `agent_status`, `age`, `phase`, `ac`, `note`); a `note` of `needs permission` is the `needs permission` notification in table form, and `closed: archive it` names an agent Paseo still lists but which is not running — it holds nothing, and `advance` gives its claim back. `2`: the tracker or `paseo` could not be asked — one `dispatch: …` line on stderr, no table; run it again once the daemon answers.

**`reverify <spec>`:** `0` every closed `ALL MET` ticket was green; `1` at least one was red — that ticket is reopened, labelled `needs-triage`, its assignee removed, and the failing `AC<n>` commented. Stdout names each ticket. `2` a ticket could not be re-run at all: nothing was judged, no ticket was touched, and the rest of the batch is skipped — stderr names the ticket and `verify-ticket.py` says what was missing. A run that could not start says nothing about the work, so it is never a red ticket.

**`summary <spec>`:** `0`. The spec has a new comment whose first line is `NIGHT SUMMARY <date>`, and the heartbeat named in `.git/mmw-heartbeat-<spec>` is deleted with the file. If `reverify` ran in this checkout, the comment also has a `Reverify: <green>/<red>` line. `1`: the comment is posted but the heartbeat could not be deleted; stderr names it.

**`wait <n> worker\|reviewer\|verifier`:** `0` the result comment is on the ticket and its first line is on stdout; `1` the agent is gone — `closed`, `error`, or no longer listed — and no result comment exists; stderr names the next step. An `idle` agent is not gone: an agent that has handed work to subagents and ended its turn sits at `idle` for the whole of that work, doing exactly what it was told, and `3` is the answer; `2` no agent labelled `mmw.ticket=<n>` of that kind; `3` still working, which covers `running`, `initializing` and `idle` — run it again. It reads the ticket before it waits at all, so a result already there returns at once. Otherwise it spends at least `MMW_WAIT_S` seconds (default 90) before answering `3`, re-reading the ticket every `MMW_WAIT_BEAT_S` seconds (default 10) — so `run it again` is a beat rather than a loop with nothing in it. It writes nothing.

No host kills a command that outlasts its shell tool: all of them move it to the background and hand back no exit code, which reads as neither `0` nor `3`. When that happens, run `wait` again — and if this host stops waiting sooner than 90 seconds, set `MMW_WAIT_S` below that bound.

**`suspend <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | Every live worker of the batch is archived (its reviewer and verifier with it; workspaces and branches stay), every ticket still in the agent queue carries a `NIGHT SUSPENDED` comment and is unclaimed, every slot the batch held is back, and the heartbeat named in `.git/mmw-heartbeat-<spec>` is deleted when that file exists |
| `1` | The night is stopped as far as this command could take it, and what is left is on stderr, one line each. A slot with a listener on it: `lease.py` names the port and the pid, so stop that process where it was started and run `python3 <lease.py> release <its worktree>`. A ticket that could not be commented on or unclaimed is the one `advance` will not take up again. A heartbeat this call could not delete is still waking the main agent |
| `2` | Nothing was touched. The reason is on stderr: not a git repository, the spec number is not digits only, or the tracker could not answer for the batch |

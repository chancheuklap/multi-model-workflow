---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a worker, reviewer or verifier, to resume a worker, to check the machine before a night, to advance a spec, to suspend a night, to read status after a finish notification, to reverify closed tickets, to post the night summary, or to change which host, model or thinking level an agent in this pipeline runs on.
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

`start` and `advance` print one JSON object per ticket, one line, whose fields are the arguments of `create_agent` (`workspaceId`, `title`, `provider`, `settings`, `labels`, `initialPrompt`). You call `create_agent` on each line yourself, with `notifyOnFinish: true`. The script prints the object; the finish notification only fires for a `create_agent` that you issued. A session with no `create_agent` tool cannot dispatch: say so and stop.

Only this path exists: everything one agent does to another — finish notifications, parent–child (`paseo.parent-agent-id`, archive cascade and the app tree), permission hand-off, readable labels — is complete only on the MCP side; the CLI is the side scripts read facts on and people use; future agent features land on the MCP side too.

Then: the main agent waits for the finish notification. A worker runs `<dispatch> wait <n> verifier|reviewer` until it exits 0 — ending a turn spends the main agent's only finish notification for this worker.

## Find your command

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket and wait for its report | `<dispatch> start <n> reviewer`, then the one path above, then `<dispatch> wait <n> reviewer` until it exits 0; it prints the first line of the `REVIEW ` comment. **Start exits 2:** stderr is the reason; nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`; the file's body is the command you ran and the output you saw; then stop. **`wait` exits 1 (the reviewer stopped and there is no `REVIEW ` comment):** `paseo logs <id>`, then run the `code-review` skill in this host's general-purpose subagent with ticket `<n>` and base commit `$(git config branch.issue-<n>.mmw-base)`; its report lands with the same `REVIEW ` first line. Do not start a second reviewer. |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`, then the one path above, then `<dispatch> wait <n> verifier` until it exits 0; it prints the first line of the `VERDICT` comment. Start it once. **Start exits 2:** stderr is the reason; nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`; the file's body is the command you ran and the output you saw; then stop. |
| Open the night on a spec | [references/night.md](references/night.md): `<dispatch> check <spec>` (it also creates the night's heartbeat), then `<dispatch> advance <spec>`, then the one path above |
| Wait for an agent you started, and read its result | `<dispatch> wait <n> worker\|reviewer\|verifier`: blocks until that agent is idle, then prints the first line of its result comment (`ALL MET` / `HANDOFF REQUIRED`, `REVIEW …`, `VERDICT …`). Exit 3: still working, run it again. Exit 1: it stopped without a result; stderr names the next step. Exit 2: no such agent |
| A finish notification arrived (`finished` / `errored` / `was closed` / `needs permission`) | `<dispatch> status <spec>`, then the decision table in [references/night.md](references/night.md) |
| Tell a live worker to continue | `<dispatch> resume <n> "<text>"`. Exit 0: the text was sent. Exit 2: no worker labelled `mmw.ticket=<n>` — read `status`, do not send again |
| Start a worker on one ticket, outside a night | `<dispatch> start <n> worker`, then the one path above |
| Re-run every closed `ALL MET` ticket on the branch you are on | `<dispatch> reverify <spec>` |
| Post the night summary on the spec | `<dispatch> summary <spec>` |
| Give the night up before it is over | `<dispatch> suspend <spec>` — [references/night.md](references/night.md) says what it stops and what it leaves standing |
| Change one ticket's worker grade | Swap its `junior-worker` / `senior-worker` label on the tracker; the next `start` reads it |
| Change which host, model or `effort` an agent runs on | Edit `models.md`, next to this file — but read [references/editing-models.md](references/editing-models.md) first |

The night itself — `check`, then `advance`, then what to do on each notification until the frontier is empty — is [references/night.md](references/night.md).

## Finish notification

A notification is a `<paseo-system>` block whose first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.`, and which may carry an `<agent-response>` of the agent's last reply. It arrives in the current turn when you are busy, or as a new turn when you are idle. Match `<title>` to `#<n> worker`, `#<n> reviewer` or `#<n> verifier`. One `create_agent` yields one terminal notification; a notification is not the ticket being done. `needs permission` is not a stop: run `list_pending_permissions` / `respond_to_permission` (CLI: `paseo permit`) first, then `status`. The night's heartbeat is created in [references/night.md](references/night.md) step 1.

## The arguments you supply

`<n>` and `<spec>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in `models.md` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade `models.md` has no row for, is refused (exit 2, stderr names the ticket). The reviewer reads `git config branch.issue-<n>.mmw-base` itself; you do not pass a base commit.

## Exit codes

**`start <n> worker\|reviewer\|verifier`:**

| Code | What happened |
| --- | --- |
| `0` | One JSON object is on stdout |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; two worker-grade labels; no `bypass` row in `models.md` for that agent; no `## Parent` spec number; no recorded base commit (reviewer); no Paseo project whose `path` is this checkout; an argument this form does not take |

**`advance <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. One JSON object per dispatched ticket on stdout; the line `advance #<spec>: merged <m>, already in <s>, released <g>, started <k>, refused <r>, held <h>` is on stderr. Each claim given back prints a line of its own naming the ticket and why; when nothing could start and tickets are still in the agent queue, stderr names every one of them and the condition holding it |
| `2` | Nothing was touched. Stderr: not a git repository, uncommitted tracked changes, or the `.git` lock was held for `MERGE_TRIES` tries — run `advance` again |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was archived, no workspace was created, nothing was dispatched. **The conflict is still in the tree and it stays there.** Resolve it with the `resolving-merge-conflicts` skill, run this repository's own checks, commit the merge, then run `advance` again. The conflict report (stderr) already names the two sides and the conflicted files |

**`check <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | `install.sh --check` passed, every `bypass` row's host is `available` in `paseo provider ls --json`, and every queued ticket has at most one worker-grade label that `models.md` has a row for. In a Paseo session (`PASEO_AGENT_ID` set) the night's heartbeat `mmw-night-<spec>` now exists, every ten minutes, its id in `.git/mmw-heartbeat-<spec>`; outside one, stderr says no heartbeat was made |
| `2` | One or more of those failed, or the heartbeat could not be created. Stderr has one `dispatch: …` line per failure. Fix what the lines name — run `install.sh`, relabel the ticket, or wait until the host is `available` — then `check` again. Do not `advance` on 2 |

**`resume <n> "<text>"`:** `0` the text was sent; `2` no worker with those labels, nothing sent.

**`status <spec>`:** `0`, stdout is the table (`ticket`, `agent`, `id`, `agent_status`, `age`, `phase`, `ac`, `note`); a `note` of `needs permission` is the `needs permission` notification in table form, and `closed: archive it` names an agent Paseo still lists but which is not running — it holds nothing, and `advance` gives its claim back. `2`: the tracker or `paseo` could not be asked — one `dispatch: …` line on stderr, no table; run it again once the daemon answers.

**`reverify <spec>`:** `0` every closed `ALL MET` ticket was green; `1` at least one was red — that ticket is reopened, labelled `needs-triage`, its assignee removed, and the failing `AC<n>` commented. Stdout names each ticket.

**`summary <spec>`:** `0`. The spec has a new comment whose first line is `NIGHT SUMMARY <date>`, and the heartbeat named in `.git/mmw-heartbeat-<spec>` is deleted with the file. If `reverify` ran in this checkout, the comment also has a `Reverify: <green>/<red>` line. `1`: the comment is posted but the heartbeat could not be deleted; stderr names it.

**`wait <n> worker\|reviewer\|verifier`:** `0` the result comment is on the ticket and its first line is on stdout; `1` the agent is idle or closed and no result comment exists — stderr names the next step; `2` no agent labelled `mmw.ticket=<n>` of that kind; `3` still working after `MMW_WAIT_S` seconds (default 300) — run it again. It writes nothing.

**`suspend <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | Every live worker of the batch is archived (its reviewer and verifier with it; workspaces and branches stay), every ticket still in the agent queue carries a `NIGHT SUSPENDED` comment and is unclaimed, every slot the batch held is back, and the heartbeat named in `.git/mmw-heartbeat-<spec>` is deleted when that file exists |
| `1` | The night is stopped as far as this command could take it, and what is left is on stderr, one line each. A slot with a listener on it: `lease.py` names the port and the pid, so stop that process where it was started and run `python3 <lease.py> release <its worktree>`. A ticket that could not be commented on or unclaimed is the one `advance` will not take up again. A heartbeat this call could not delete is still waking the main agent |
| `2` | Nothing was touched. The reason is on stderr: not a git repository, the spec number is not digits only, or the tracker could not answer for the batch |

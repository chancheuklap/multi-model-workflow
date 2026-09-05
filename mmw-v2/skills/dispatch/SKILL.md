---
name: dispatch
description: Put another agent to work on a ticket, and move a night's batch of tickets forward. Use to start a worker, reviewer or verifier, to resume a worker, to check the machine before a night, to advance a spec, to read status after a finish notification, to reverify closed tickets, to post the night summary, or to change which host, model or thinking level an agent in this pipeline runs on.
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

## One path: create_agent

`start` and `advance` print one JSON object per ticket, one line, whose fields are the arguments of `create_agent` (`workspaceId`, `title`, `provider`, `settings`, `labels`, `initialPrompt`). You call `create_agent` on each line yourself, with `notifyOnFinish: true`. The script prints the object; the finish notification only fires for a `create_agent` that you issued.

Only this path exists: everything one agent does to another — finish notifications, parent–child (`paseo.parent-agent-id`, archive cascade and the app tree), permission hand-off, readable labels — is complete only on the MCP side; the CLI is the side scripts read facts on and people use; future agent features land there too (#118 Implementation Decisions section 5).

Then: the main agent waits for the finish notification. A worker blocks with `paseo wait <id>` — ending a turn spends the main agent's only finish notification for this worker.

## Find your command

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket and wait for its report | `<dispatch> start <n> reviewer`. Stdout is one JSON object. Call `create_agent` with those fields and `notifyOnFinish: true`. Then `paseo wait <id>`, then read the newest comment whose first line is `REVIEW `. **Start exits 2:** stderr is the reason; nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`; the file's body is the command you ran and the output you saw; then stop. **Notification is `errored` or `was closed`, and there is no `REVIEW ` comment:** `paseo logs <id>`, then run the `code-review` skill in this host's general-purpose subagent with ticket `<n>` and base commit `$(git config branch.issue-<n>.mmw-base)`; its report lands with the same `REVIEW ` first line. Do not start a second reviewer. |
| Start the verifier on your ticket | `<dispatch> start <n> verifier`. Call `create_agent` on the printed object with `notifyOnFinish: true`. Then `paseo wait <id>`, then read the newest comment whose first line is `VERDICT`. Start it once. **Start exits 2:** stderr is the reason; nothing was started — it is a pipeline fault: `<engine> <n> --sub-issue pipeline <file>`; the file's body is the command you ran and the output you saw; then stop. |
| Open the night on a spec | [references/night.md](references/night.md): `<dispatch> check <spec>`, then `<dispatch> advance <spec>`, then `create_agent` on each printed line |
| A finish notification arrived (`finished` / `errored` / `was closed` / `needs permission`) | `<dispatch> status <spec>`, then the decision table in [references/night.md](references/night.md) |
| Tell a live worker to continue | `<dispatch> resume <n> "<text>"`. Exit 0: the text was sent. Exit 2: no worker labelled `mmw.ticket=<n>` — read `status`, do not send again |
| Start a worker on one ticket, outside a night | `<dispatch> start <n> worker`, then `create_agent` |
| Re-run every closed `ALL MET` ticket on the branch you are on | `<dispatch> reverify <spec>` |
| Post the night summary on the spec | `<dispatch> summary <spec>` |
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
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; two worker-grade labels; no `bypass` row in `models.md` for that agent; no `## Parent` spec number; no recorded base commit (reviewer); no Paseo project whose `path` is this checkout; a flag that is no longer accepted |

**`advance <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | Done. One JSON object per dispatched ticket on stdout; the line `advance #<spec>: merged <m>, already in <s>, started <k>, refused <r>` is on stderr |
| `2` | Nothing was touched. Stderr: not a git repository, uncommitted tracked changes, or the `.git` lock was held for `MERGE_TRIES` tries — run `advance` again. A flag that is no longer accepted is the same exit |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was archived, no workspace was created, nothing was dispatched. **The conflict is still in the tree and it stays there.** Resolve it with the `resolving-merge-conflicts` skill, run this repository's own checks, commit the merge, then run `advance` again. The conflict report (stderr) already names the two sides and the conflicted files |

**`check <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | `install.sh --check` passed, every `bypass` row's host is `available` in `paseo provider ls --json`, and every queued ticket has at most one worker-grade label that `models.md` has a row for |
| `2` | One or more of those failed. Stderr has one `dispatch: …` line per failure. Fix what the lines name — run `install.sh`, relabel the ticket, or wait until the host is `available` — then `check` again. Do not `advance` on 2 |

**`resume <n> "<text>"`:** `0` the text was sent; `2` no worker with those labels, nothing sent.

**`status <spec>`:** `0`. Stdout is the table (`ticket`, `agent`, `id`, `agent_status`, `age`, `phase`, `ac`, `note`). A `note` of `needs permission` is the `needs permission` notification in table form.

**`reverify <spec>`:** `0` every closed `ALL MET` ticket was green; `1` at least one was red — that ticket is reopened, labelled `needs-triage`, its assignee removed, and the failing `AC<n>` commented. Stdout names each ticket.

**`summary <spec>`:** `0`. The spec has a new comment whose first line is `NIGHT SUMMARY <date>`. If `reverify` ran in this checkout, the comment also has a `Reverify: <green>/<red>` line.

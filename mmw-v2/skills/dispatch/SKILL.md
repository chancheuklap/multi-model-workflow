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

Resolve them from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Two paths: `--json` or `--run`

`start` and `advance` take exactly one of `--json` or `--run`. If you pass neither, or both, the script exits 2, prints `pass --json … or --run …` on stderr, and calls nothing.

- **`--json`**: stdout is one JSON object per ticket, one line, whose fields are the arguments of `create_agent` (`workspaceId`, `title`, `provider`, `settings`, `labels`, `initialPrompt`). You call `create_agent` on each line yourself, with `notifyOnFinish: true`. The script does not call `create_agent`; the finish notification only fires for a `create_agent` that you issued.
- **`--run`**: the script calls `paseo run -d …` and prints the agent id. There is no finish notification. Wait with `paseo wait <id>`, then read the ticket.

Which path you take is a fact about this session, not about the environment: **if you have a `create_agent` tool, pass `--json`; otherwise pass `--run`.** Do not look at `PASEO_AGENT_ID` to choose — a Grok session can have the Paseo tools and still be running its shell inside the daemon, where that variable is unset, so a test of the variable would pick `--run` every time and you would never be notified.

## Find your command

| You want to | Run |
| --- | --- |
| Start the reviewer on your ticket and wait for its report | `<dispatch> start <n> reviewer --json`. Stdout is one JSON object. Call `create_agent` with those fields and `notifyOnFinish: true`. When a finish notification arrives for title `#<n> reviewer`, read the ticket: the report is the newest comment whose first line is `REVIEW `. **`--run` instead:** stdout is the agent id; `paseo wait <id>`, then read that `REVIEW ` comment. **Start exits 2:** stderr is the reason; nothing was started — run the `code-review` skill in this host's general-purpose subagent with ticket `<n>` and base commit `$(git config branch.issue-<n>.mmw-base)`; its report lands with the same `REVIEW ` first line. **Notification is `errored` or `was closed`, and there is no `REVIEW ` comment:** `paseo logs <id>`, then the same general-purpose fallback. Do not start a second reviewer. |
| Start the verifier on your ticket | `<dispatch> start <n> verifier --json`. Call `create_agent` on the printed object with `notifyOnFinish: true`. When the finish notification arrives, read the newest comment whose first line is `VERDICT`. **`--run` instead:** stdout is the agent id; `paseo wait <id>`, then read that `VERDICT`. Start it once. **Start exits 2:** stderr is the reason; comment on the ticket with the command you ran and the output, and stop. |
| Open the night on a spec | [references/night.md](references/night.md): `<dispatch> check <spec>`, then `<dispatch> advance <spec> --json`, then `create_agent` on each printed line |
| A finish notification arrived (`finished` / `errored` / `was closed` / `needs permission`) | `<dispatch> status <spec>`, then the decision table in [references/night.md](references/night.md) |
| Tell a live worker to continue | `<dispatch> resume <n> "<text>"`. Exit 0: the text was sent. Exit 2: no worker labelled `mmw.ticket=<n>` — read `status`, do not send again |
| Start a worker on one ticket, outside a night | `<dispatch> start <n> worker --json` (then `create_agent`) or `--run` (prints the agent id; then `paseo wait <id>` before you read the ticket) |
| Re-run every closed `ALL MET` ticket on the branch you are on | `<dispatch> reverify <spec>` |
| Post the night summary on the spec | `<dispatch> summary <spec>` |
| Change one ticket's worker grade | Swap its `junior-worker` / `senior-worker` label on the tracker; the next `start` reads it |
| Change which host, model or `effort` an agent runs on | Edit `models.md`, next to this file — but read [references/editing-models.md](references/editing-models.md) first |

The night itself — `check`, then `advance`, then what to do on each notification until the frontier is empty — is [references/night.md](references/night.md).

## Finish notification

A notification is a `<paseo-system>` block whose first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.`, and which may carry an `<agent-response>` of the agent's last reply. It arrives in the current turn when you are busy, or as a new turn when you are idle. Match `<title>` to `#<n> worker`, `#<n> reviewer` or `#<n> verifier`. One `create_agent` yields one terminal notification; a notification is not the ticket being done. `needs permission` is not a stop: run `list_pending_permissions` / `respond_to_permission` (CLI: `paseo permit`) first, then `status`. You may create a heartbeat as insurance that you will be woken if a notification is missed; there is no rule for one.

## The arguments you supply

`<n>` and `<spec>` are digits only, no `#`.

`start`'s third argument is `worker`, `reviewer` or `verifier`. Which of the two worker rows in `models.md` a worker starts from is the ticket's own `junior-worker` or `senior-worker` label, read fresh on every start. A ticket carrying neither label starts on `junior-worker`; one carrying both, or one naming a grade `models.md` has no row for, is refused (exit 2, stderr names the ticket). The reviewer reads `git config branch.issue-<n>.mmw-base` itself; you do not pass a base commit.

`--json` / `--run` are required on `start` and `advance` and invalid as a substitute for each other.

## Exit codes

**`start <n> worker\|reviewer\|verifier --json\|--run`:**

| Code | What happened |
| --- | --- |
| `0` | `--json`: one JSON object is on stdout. `--run`: the agent id is on stdout |
| `2` | Nothing was started. The reason is on stderr — read it verbatim. Typical causes: the ticket is not `OPEN` / not `ready-for-agent` / still blocked; two worker-grade labels; no `bypass` row in `models.md` for that agent; no `## Parent` spec number; no recorded base commit (reviewer); no Paseo project whose `path` is this checkout |

**`advance <spec> --json\|--run`:**

| Code | What happened |
| --- | --- |
| `0` | Done. `--json`: one JSON object per dispatched ticket on stdout; the line `advance #<spec>: merged <m>, already in <s>, started <k>, refused <r>` is on stderr. `--run`: that summary line is on stdout |
| `2` | Nothing was touched. Stderr: not a git repository, uncommitted tracked changes, or the `.git` lock was held for `MERGE_TRIES` tries — run `advance` again |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was archived, no workspace was created, nothing was dispatched. **The conflict is still in the tree and it stays there.** Resolve it with the `resolving-merge-conflicts` skill, run this repository's own checks, commit the merge, then run `advance` again with the same `--json` or `--run`. The conflict report (stderr) already names the two sides and the conflicted files |

**`check <spec>`:**

| Code | What happened |
| --- | --- |
| `0` | `install.sh --check` passed, every `bypass` row's host is `available` in `paseo provider ls --json`, and every queued ticket has at most one worker-grade label that `models.md` has a row for |
| `2` | One or more of those failed. Stderr has one `dispatch: …` line per failure. Fix what the lines name — run `install.sh`, relabel the ticket, or wait until the host is `available` — then `check` again. Do not `advance` on 2 |

**`resume <n> "<text>"`:** `0` the text was sent; `2` no worker with those labels, nothing sent.

**`status <spec>`:** `0`. Stdout is the table (`ticket`, `agent`, `id`, `agent_status`, `age`, `phase`, `ac`, `note`). A `note` of `needs permission` is the `needs permission` notification in table form.

**`reverify <spec>`:** `0` every closed `ALL MET` ticket was green; `1` at least one was red — that ticket is reopened, labelled `needs-triage`, its assignee removed, and the failing `AC<n>` commented. Stdout names each ticket.

**`summary <spec>`:** `0`. The spec has a new comment whose first line is `NIGHT SUMMARY <date>`. If `reverify` ran in this checkout, the comment also has a `Reverify: <green>/<red>` line.

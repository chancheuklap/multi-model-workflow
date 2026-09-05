# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create workspaces, and print the arguments for `create_agent`. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. The commands, their exit codes, and the shape of a finish notification are in `SKILL.md` next to this file. Resolve `<dispatch>` the same way that file does.

## 1. The user says the night starts

Run, in this checkout, on the branch the night merges into:

```bash
<dispatch> check <spec>
```

**Exit 0:** go to step 2. **Exit 2:** stderr is one line per failure (`install.sh --check`, a provider whose `status` is not `available`, a queued ticket with two worker-grade labels or a label `models.md` has no row for). Fix what the lines name, or tell the user if only they can, then run `check` again. Do not `advance` on 2.

## 2. First `advance`

Stay on this branch all night. Every `advance` merges into whatever `HEAD` is on.

```bash
<dispatch> advance <spec> --json
```

**Exit 0:** stdout is zero or more JSON lines, one per ticket on the frontier. For each line, call `create_agent` with that object and `notifyOnFinish: true`. Then wait. **Exit 2:** nothing was touched; read stderr; if it is uncommitted changes, commit or set them aside and run `advance` again; if it is the `.git` lock, run `advance` again. **Exit 3:** a merge is in conflict, still in the tree. Resolve it with the `resolving-merge-conflicts` skill — never `--abort` — run this repository's own checks, commit the merge, then `advance` again with `--json`.

`--json` is required because the finish notification only fires for `create_agent` you issued. `--run` is the same merge and workspace work without notifications; use it only when you have no `create_agent` tool.

A worktree is cut from `HEAD` at the moment `advance` creates it, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see. That is why merge, archive, create, and dispatch are one command, in that order. Archive uses `git worktree remove --force` and does not inspect uncommitted work in that worktree, so `advance` archives a ticket's workspace only after that ticket's branch is already in `HEAD`.

## 3. Each finish notification

The notification's first sentence is `Agent <id> (<title>) finished.` or `errored.` or `was closed.` or `needs permission.` Title is `#<n> worker`, `#<n> reviewer` or `#<n> verifier`.

1. If it is `needs permission`: `list_pending_permissions` then `respond_to_permission` (CLI: `paseo permit`). Then go to 2. This is not a stop.
2. Run `<dispatch> status <spec>`. The table's `note` column is `needs permission`, `ready`, `waiting on #<m>`, the newest comment, or empty while a worker is live.
3. Decide, using the table and the notification:

| What you see | What you do |
| --- | --- |
| A ticket just closed `ALL MET`, or the frontier has `ready` rows and no live worker on them | `<dispatch> advance <spec> --json`, then `create_agent` on each new line |
| The worker is live and the work should continue | `<dispatch> resume <n> "<what you settled, then: continue>"` |
| The notification is `finished`, `status` shows the ticket still `OPEN`, the worker `idle`, and it has a live child (`mmw.kind=reviewer` or `mmw.kind=verifier`) | Not a stop. In the background run `paseo wait <child agent id> && paseo wait <worker id>`; when that returns, run `status` again (Claude Code: Monitor or background Bash; any other host: its own background task tool). No live child and no closing comment: take the `errored` / `was closed` row |
| The worker has stopped and the ticket has a new child whose first line is `SUB-ISSUE pipeline` | Read that sub-issue. Fix the cause it names. Then `<dispatch> resume <n> "… continue"` |
| The worker `errored` or `was closed` short of a closing comment | `paseo logs <id>`. Fix what stopped it — a file it could not find, a command it needs, a baseline it read wrong — then `resume` with that plus `continue`. A question only a person can settle: `resume` telling the worker to open it with `verify-ticket.py <n> --sub-issue decision <file>`, take the default meanwhile, and record it under `Decisions I made on my own`. Change no label |
| The worker is live and nothing is wrong | Do not `resume`. Wait for the next notification |
| `status` shows an empty frontier and no live agent of this spec | Go to step 4 |

Then wait for the next notification. Most notifications that close a ticket are followed by another `advance`.

You may create a heartbeat that prompts you to run `status` if you have been idle too long. There is no required interval and no required text; a heartbeat that fires while you already have a turn in flight is reported as a failure by Paseo, not queued.

## 4. The night is over

The frontier is empty and `status` shows no live agent. Then, still on this branch:

```bash
<dispatch> reverify <spec>
<dispatch> summary <spec>
```

`reverify` re-runs every closed `ALL MET` ticket's criteria against this `HEAD`. Exit 0: all green. Exit 1: each red ticket is already reopened, labelled `needs-triage`, unassigned, and commented with the failing `AC<n>` — that is the morning's triage queue; do not close those tickets.

`summary` posts a comment on the spec whose first line is `NIGHT SUMMARY <date>`, with the four lines `Closed:`, `Handed back to needs-triage:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:`. If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended.

Tell the user the night finished, and point them at that comment.

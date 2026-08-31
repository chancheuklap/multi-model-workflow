---
name: dispatch
description: Dispatch a worker or a reviewer onto a ticket, wait for it to report back there, and change which agent, model or thinking level any agent in this pipeline runs on.
---

# Dispatch

Other skills reach this one at the step where one agent puts another to work; nothing here runs on its own.

## The script

`scripts/dispatch.sh`, next to this file. Resolve its absolute path once. Every command below is written `<dispatch> …` and means:

```bash
bash /absolute/path/to/scripts/dispatch.sh …
```

You supply a role and a ticket number. Everything else is fixed by the shape of the pipeline and lives inside the script.

## Dispatch an agent

```bash
<dispatch> <ticket> <role> [base-commit]
```

| Argument | What to put there |
| --- | --- |
| `<ticket>` | The ticket number. Digits only, no `#` |
| `<role>` | `junior-worker`, `senior-worker` or `reviewer`. You choose which of the two workers a ticket gets; the ticket itself says nothing about it |
| `[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from: `git config branch.issue-<n>.mmw-base`, read in the worker's worktree — the cut point dispatch recorded when it opened the worktree, the same base `verify-ticket.py` uses for `Outside Owns:` |

| Exit code | What happened |
| --- | --- |
| `0` | The session is up and has been told what to work on |
| `1` | The session is up but was **not** told anything: it did not become ready in time, or it would not take the prompt |
| `2` | Nothing was started. The reason is on stderr — read it verbatim |

On exit 1 a session is sitting in that pane holding the ticket's name with nothing to do. Dispatching the same role again collides on that name: end that session first, or carry on without it.

## Wait for the agent to report back

```bash
<dispatch> wait <ticket> "<first-line-regex>" [seconds]
```

| Argument | What to put there |
| --- | --- |
| `"<first-line-regex>"` | Matched against the **first line** of the newest comment on the ticket. A worker waiting on its reviewer uses `"^REVIEW "`, trailing space and all; whoever dispatched a worker waits on `^(ALL MET\|HANDOFF REQUIRED)` |
| `[seconds]` | How long to wait. Defaults to 1800 |

| Exit code | What happened |
| --- | --- |
| `0` | It matched. The whole comment is on stdout |
| `1` | It timed out. The script has already commented on the ticket saying who did not finish |

On exit 1, **skip that round and carry on with the rest of your own steps.** An agent that never reported back is not a reason to hand the ticket to a person.

## Move the batch on

```bash
<dispatch> advance <spec> [--role R]
```

The one command that moves a batch forward. It merges the branch of every ticket that closed with `ALL MET` into the branch you are on, then starts every ticket on the frontier.

The two halves are one command because their order is the whole point: a worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see. Branches are merged in the order their tickets closed, which is already the order their blockers imposed — the start-of-work guard refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning.

Run it in two places: straight after `run`, to start the first frontier, and every time the board sends you a line. It is safe to run at any other time — a branch already merged is skipped, and an empty frontier starts nothing.

| Exit code | What happened |
| --- | --- |
| `0` | Done. The last line counts what was merged, what was already in, and what was started |
| `2` | Nothing was touched. The reason is on stderr: not inside Herdr, no such role, not a git repository, or the working tree has uncommitted changes |
| `3` | A merge is in conflict. Everything before it is merged and committed; nothing was dispatched |

**On exit 3 the conflict is still in the tree, and it stays there.** Resolve it with the `resolving-merge-conflicts` skill — never `--abort` — run this repository's own checks, commit the merge, then run `advance` again. It picks up from the branch after the one you resolved.

The report it prints on exit 3 is the first two steps of that skill already done: the branch being merged and the ticket it belongs to, the tickets already merged on this side, and the conflicted files. Both sides are tickets, so read what each was for before deciding which intent survives.

## Start the night

```bash
<dispatch> run <spec> [--role R] [--max-hours H]
```

One command, typed once, after the last ticket of a spec is published. It checks this machine, renames your own pane `mmw-main` so the board can reach you, opens a tab labelled `mmw board #<spec>` in this workspace, and leaves `scripts/board.py --watch` running in it. From then on the board re-prompts the sessions that go idle short of their closing gate, redispatches the ones whose session dies, hands back the tickets that reach a limit, and writes `NIGHT SUMMARY` on the spec when nothing is left to run.

It does not dispatch. When the frontier grows it tells you, and you run `advance`.

| Argument | What to put there |
| --- | --- |
| `<spec>` | The spec issue whose sub-issues are tonight's tickets. Digits only |
| `--role` | Which row of `models.md` tonight's workers are started from. Defaults to `junior-worker` |
| `--max-hours` | How long one ticket may hold a session before it goes back to be judged |

| Exit code | What happened |
| --- | --- |
| `0` | The board is up. Its tab holds every line it will write |
| `2` | Nothing was started. The reason is on stderr: not inside Herdr, no such role, or `install.sh --check` found something missing |

Exit 2 on the check is not a formality. A night nobody is watching cannot notice that this machine's skills or its closing gate went missing, so that is checked at the one moment somebody is here to fix it: run `install.sh` and start the night again.

**Then run `advance` once.** The board's own line may not reach you while your pane is focused, and at the start of a night it usually is.

After that you read tickets and run `advance` when told. You do not prompt a worker, and you do not answer a question a worker put on screen — the board comments the form on the ticket, dismisses it, and sends the worker its dispatch line again, because the discipline is not to ask.

## When the board re-prompts you

Three cases reach you, each as one line beginning `mmw board: <case> #<n> — run`, ending in the command to run. Run it as it is written.

| `<case>` | What it means | What to do |
| --- | --- | --- |
| `ADVANCE` | The frontier has tickets on it | Run `advance`. On exit 3, resolve the conflict and run it again |
| `WAKEUP LIMIT`, `REDISPATCHED`, `TIME LIMIT` | A limit was reached. The board has already commented on that ticket and moved it to `needs-triage` | Read the table. Nothing else: do not dispatch it again, do not prompt its session |
| `night over` | The night ended: `NIGHT SUMMARY` is the newest comment on the spec | Run `advance` — the tickets that closed last still have their branches outside your branch, and this is the last chance to merge them. Then read the summary, and tell the user if they asked to hear when the run finished |

A worker stopped at a question does not reach you. Its form is on its ticket for the morning, under `BLOCKED:`.

## One board, one workspace

A board answers for the Herdr workspace it was started in: it acts on the sessions in that workspace and leaves every other one alone, and the Herdr names it hands out carry the workspace id — `w2q-issue-61` rather than `issue-61`. Herdr's names are unique among live agents across the whole server, so without that two repositories each holding a ticket #100 would collide and the second one would not start.

Nothing about this needs setting up: `run` opens the board in the workspace you type it in, and several projects can be running their own nights at the same time. The git branch is still `issue-61` — the prefix is a Herdr name, not a branch name.

## Change which agent, model, or thinking level is used

Edit `models.md`, next to this file. **Read [references/editing-models.md](references/editing-models.md) first** — a row is only correct on the machine it runs on, and that file carries the whole change: what to confirm before you touch a row, and what to do afterwards to make it take effect.

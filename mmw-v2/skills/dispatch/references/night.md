# Running a night

You are the main agent, and a spec's tickets are going to be worked while you are not watching them. Two agents share the night, and the line between them is that **repair is the board's, and the next step is yours**: a repair puts a session that was already dispatched back on its feet, while a dispatch decides which HEAD the next ticket's branch is cut from.

## `run` opens it, and dispatches nothing

`<dispatch> run <spec> [--max-hours H]` is typed once, after the last ticket of a spec is published. It checks this machine, renames your own pane `mmw-main` so the board can reach you, opens the monitor tab, labelled `mmw board #<spec>`, in this workspace, and leaves `<board> --watch` running in it.

`--max-hours` is how long one ticket may hold a session before it is handed back to `needs-triage`. Which row of `models.md` a ticket's worker starts from is the ticket's own `junior-worker` or `senior-worker` label, so the night carries no answer of its own and a repair puts a ticket back on the `models.md` row it was written for.

The `install.sh --check` it runs first is not a formality. A night nobody is watching cannot notice that this machine's skills or its `hook.py` went missing, so that is checked at the one moment somebody is here to fix it.

**Then run `advance` once, yourself.** The board's `mmw board:` line may not reach you while your pane is focused, and at the start of a night it usually is.

## `advance` merges, then dispatches, in that order

`<dispatch> advance <spec>` merges the branch of every ticket that closed with `ALL MET` into the base branch you are on, then dispatches every ticket on the frontier.

The two halves are one command because their order is the whole point: a worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its closing comment opens `ALL MET`, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. The fourth is what makes the command safe to run at any time: a branch already merged is skipped, and an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

## When the board re-prompts you

Three cases reach you, each as one line beginning `mmw board:`. The line names the case and the ticket or spec; what each case asks of you is the `Find your command` table in this skill's `SKILL.md`.

| Case | What it means |
| --- | --- |
| `ADVANCE` | The frontier has tickets on it |
| `night over` | The night ended: `NIGHT SUMMARY` is the newest comment on the spec. Advance one last time — the tickets that closed last still have their branches outside your base branch, and this is the last chance to merge them — then read the summary, and tell the user if they asked to hear when the night finished |
| `WAKEUP LIMIT`, `REDISPATCHED`, `TIME LIMIT` | A limit was reached. The board has already commented on that ticket and handed it back to `needs-triage`. Read it. Do not dispatch it again, and do not re-prompt its session |

A worker stopped at a question does not reach you at all. The board comments the form on that ticket under `BLOCKED:`, closes it with that host's close key, and sends the worker `continue`. **You do not answer a question a worker put on screen**, and neither does the board: the rule in this pipeline is `Put no question on the screen`, and a form on screen is a worker that broke it.

## One board, one workspace

A board answers for the Herdr workspace it was started in: it acts on the sessions in that workspace and leaves every other one alone, and the Herdr names it hands out carry the workspace id — `w2q-issue-61` rather than `issue-61`. Herdr's names are unique among live agents across the whole server, so without that two repositories each holding a ticket #100 would collide and the second one would not start.

Nothing about this needs setting up: `run` opens the board in the workspace you type it in, and several projects can be running their own nights at the same time. The ticket branch is still `issue-61` — the prefix is a Herdr name, not a branch name.

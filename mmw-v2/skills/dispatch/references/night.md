# Running a night

You are the main agent, and a spec's tickets are going to be worked while you are not watching them. Two agents share the night, and the line between them is that **the board watches, and every decision is yours**: the board sends `continue` to a worker whose turn failed on the network, tells you about a worker that stopped on its own, and merges nothing, dispatches nothing, and takes no ticket out of the agent queue. A dispatch decides which HEAD the next ticket's branch is cut from, and that is yours.

## `run` opens it, and dispatches nothing

`<dispatch> run <spec> [--max-hours H]` is typed once, after the last ticket of a spec is published. It checks this machine, renames your own pane `mmw-main` so the board can reach you, opens the monitor tab, labelled `mmw board #<spec>`, in this workspace, and leaves `<board> --watch` running in it.

`--max-hours` is how long one ticket may hold a session before the board tells you so; the ticket keeps its label and its session. Which row of `models.md` a ticket's worker starts from is the ticket's own `junior-worker` or `senior-worker` label, so the night carries no answer of its own.

The `install.sh --check` it runs first matters. A night nobody is watching cannot notice that this machine's skills or its `hook.py` went missing, so that is checked at the one moment somebody is here to fix it.

**Then run `advance` once, yourself.** The board's `mmw board:` line may not reach you while your pane is focused, and at the start of a night it usually is.

## `advance` merges, then dispatches, in that order

`<dispatch> advance <spec>` merges the branch of every ticket that closed with `ALL MET` into the base branch you are on, then dispatches every ticket on the frontier.

The two halves are one command because the order is the reason: a worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its closing comment opens `ALL MET`, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. The fourth is what makes the command safe to run at any time: a branch already merged is skipped, and an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

## What the board reads, and what it does

Every session this pipeline starts reports its own turn state: `turn.py`, installed on the host's lifecycle hooks, writes the `turn` pane token — `ready`, `working`, `ended`, `failed:<error>`, `cancelled:<reason>` — and reports `working` / `idle` to Herdr as that pane's lifecycle authority, so Herdr stops guessing the state off the screen. The board reads the token and does one of three things:

| `turn` | What the board does |
| --- | --- |
| `failed:<error>` | The host gave up on the turn after its own retries, most often on the network. The board sends `continue`, once per turn, and at most `FAILED_LIMIT` times at one `phase`; after that it tells you instead |
| `ended`, `cancelled:<reason>` | The worker ended a turn short of `closed` or `handoff`. The board tells you, once per turn, and touches nothing |
| `phase` is `closed` or `handoff` | The closing comment is on the ticket. The board closes the pane |

A session with no `turn` token — hooks not installed, or Herdr restarted — is left alone until Herdr has read it `idle` for `FALLBACK_SECONDS` with nothing new on the ticket, and then reported to you the same way as one that stopped on purpose.

## When the board re-prompts you

Four cases reach you, each as one line beginning `mmw board:`. The line names the case and the ticket or spec; what each case asks of you is the `Find your command` table in this skill's `SKILL.md`.

| Case | What it means |
| --- | --- |
| `ADVANCE` | The frontier has tickets on it |
| `night over` | The night ended: `NIGHT SUMMARY` is the newest comment on the spec. Advance one last time — the tickets that closed last still have their branches outside your base branch, and this is the last chance to merge them — then read the summary, and tell the user if they asked to hear when the night finished |
| `STOPPED` | A worker ended a turn on its own, short of `closed` or `handoff`, or its turn failed more than `FAILED_LIMIT` times at one phase. The line names its Herdr name: read its screen, work out why, and move it on |
| `TIME LIMIT` | A ticket has held its session for `--max-hours`. Nothing was changed: read the session's screen and decide whether it goes on |

No question reaches the screen: `hook.py` refuses the host's question tool in every dispatched session and tells the worker where the question goes instead — the default taken and recorded under `Decisions I made on my own`, or `ABANDON: AC<n> decision` with a sub-issue.

Everything the board prints is also appended to `~/.mmw/logs/board-<workspace id>-<spec>.log`, which is where to look in the morning once the monitor tab is gone.

## One board, one workspace

A board answers for the Herdr workspace it was started in: it acts on the sessions in that workspace and leaves every other one alone, and the Herdr names it hands out carry the workspace id — `w2q-issue-61` rather than `issue-61`. Herdr's names are unique among live agents across the whole server, so without that two repositories each holding a ticket #100 would collide and the second one would not start.

Nothing about this needs setting up: `run` opens the board in the workspace you type it in, and several projects can be running their own nights at the same time. The ticket branch is still `issue-61` — the prefix is a Herdr name, not a branch name.

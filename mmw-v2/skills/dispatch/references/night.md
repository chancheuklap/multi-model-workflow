# Running a night

You are the main agent, and a spec's tickets are going to be worked while you are not watching them. Two agents share the night, and the line between them is that **the board watches, and every decision is yours**: the board sends `continue` to a worker whose turn failed on the network, tells you about a worker that stopped on its own, and merges nothing, dispatches nothing, and takes no ticket out of the agent queue. A dispatch decides which HEAD the next ticket's branch is cut from, and that is yours.

## `run` opens it, and dispatches nothing

`<dispatch> run <spec> [--max-hours H]` is typed once, after the last ticket of a spec is published. It checks this machine, renames your own pane `mmw-main` so the board can reach you, opens the monitor tab, labelled `mmw board #<spec>`, in this workspace, and leaves `<board> --watch` running in it.

`--max-hours` is how long one ticket may hold a session before the board tells you so; the ticket keeps its label and its session. Which row of `models.md` a ticket's worker starts from is the ticket's own `junior-worker` or `senior-worker` label, so the night carries no answer of its own.

The checks it runs first matter. A night nobody is watching cannot notice that this machine's skills or its `hook.py` went missing, that a ticket's worker-grade label names a row `models.md` no longer has, or that a row's host is not a kind Herdr can start — each of those would refuse a ticket at every `advance`, with the reason only on `advance`'s stderr. So `install.sh --check`, every queued ticket's grade label, and every worker row's and the reviewer row's host are checked at the one moment somebody is here to fix them, and `run` exits 2 with nothing opened.

**Then run `advance` once, yourself.** The board's `mmw board:` line may not reach you while your pane is focused, and at the start of a night it usually is.

## `advance` merges, releases, then dispatches, in that order

`<dispatch> advance <spec>` merges the branch of every ticket that closed with `ALL MET` into the branch you are on at that moment, gives back the claims whose workers are gone, then dispatches every ticket on the frontier. The branch you open the night on is the base branch, so stay on it all night: every `advance` merges into whatever HEAD is on, and `git config branch.issue-<n>.mmw-base-branch` is a record for readers, not something `advance` consults.

The three are one command because the order is the reason. A worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see; and the frontier is read after the claims come off, so a ticket freed by this run starts in this run rather than the next one.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its closing comment opens `ALL MET`, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. The fourth is what makes the command safe to run at any time: a branch already merged is skipped, and an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

A ticket is claimed by being assigned to the account this pipeline is signed in as — `verify-ticket.py --preflight` does it — and the frontier takes only unassigned tickets, which is what keeps a second worker off a ticket somebody is already working. Two paths give a claim back: the closeout, and the hand back to triage. A session that ends any other way — a crash, a machine restart, a tab somebody closed — leaves the claim standing, and from then on the ticket is off every frontier for good, with an empty frontier as the only sign of it.

So `advance` gives a claim back when four things hold at once: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and no live session holds it. The write is `gh issue edit <n> --remove-assignee @me`, so a ticket a person took for themselves is untouched and stays off the frontier, which is the right answer — somebody has it. Each release prints one line naming the ticket and saying why, and that line is not decoration: the board sees the Herdr on this machine and no other, so a worker of the same account running on a second machine reads from here as a claim whose owner is gone.

When nothing can start and the batch still holds open tickets in the agent queue, `advance` names each of those tickets on stderr with the condition holding it — claimed by somebody, blocked by a ticket still open, or already held by a live session. An empty frontier and a finished batch print the same nothing otherwise, and the difference between them is not visible from outside the frontier's five conditions. The exit code is unchanged: this is an explanation, not a failure.

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
| `night over` | The night ended: the frontier is empty and no session of ours is alive. A ticket left waiting on a blocker that was handed back keeps its label and is on the `Not dispatched, a blocker stayed open:` line of `NIGHT SUMMARY`, the newest comment on the spec. Advance one last time, since the tickets that closed last still have their branches outside your base branch; then the section below, and tell the user if they asked to hear when the night finished |
| `STOPPED` | A worker ended a turn on its own, short of `closed` or `handoff`, or its turn failed more than `FAILED_LIMIT` times at one phase. The line names its Herdr name: read its screen, work out why, and move it on |
| `TIME LIMIT` | A ticket has held its session for `--max-hours`. Nothing was changed: read the session's screen and decide whether it goes on |

## Giving the night up

A night is worth giving up when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> abandon <spec>` is that decision carried out.

It stops the board by closing the tab `run` opened, labelled `mmw board #<spec>`. The board process is not what has to be ended — `run` leaves `until <board>; do sleep; done` running in that tab's pane, so a board that is ended comes back seconds later. The loop belongs to the pane's shell, the pane belongs to the tab, and closing the tab is the only thing that takes all three.

Then every ticket still in the agent queue gets one comment opening `NIGHT ABANDONED #<spec>`, with the time and whether a worker was still running on it. Without it the morning reader finds a row of tickets with no verdict and no way to tell them from work in progress. A ticket a worker handed back to triage during the night already carries its own verdict, so it is left alone.

**Nothing is ended but the board.** Every worker still running is left running, every worktree and branch stays, every agent session stays. That is the reason to give a night up rather than let it run: the fix is carried on with the same worktrees and the same sessions, and a batch dispatched again from scratch would throw the night's work away along with the night. A worker left running is nobody's to watch until you read it — `herdr agent read <name>`, the name in its ticket's comment.

The slots are given back for every ticket of the batch, handed back ones included, because the gate in `advance` counts claims rather than sessions and the next night would otherwise read the machine as fuller than it is. `lease.py` refuses a slot something still listens on and names the port and the pid; `abandon` reports that and exits 1 rather than forcing it, because taking a slot off a live process is the same act as ending it.

## Re-running the closed tickets

A ticket's criteria run in its own worktree, against the code that was there while it ran. A ticket merged after it can break one of them, and until the base branch is checked nothing looks: every ticket is green alone and the branch is red.

So after the last advance, on the base branch, for every ticket this spec closed, in ticket order: `verify-ticket.py <n> --reverify`. Comment the base-branch commit each one was re-run at. A ticket with a failing criterion is reopened into the morning's triage queue: `gh issue reopen <n>`, `gh issue edit <n> --add-label needs-triage --remove-assignee <its assignee>`, and one comment naming the base-branch commit (`git rev-parse HEAD`) and each criterion that failed by its `AC<n>` id — the closeout took `ready-for-agent` off and left the assignee, so without the label the ticket sits in no queue and the morning query never lists it. A criterion that needs an application running starts it once and reuses it for the whole pass.

No question reaches the screen: `hook.py` refuses the host's question tool in every dispatched session and tells the worker where the question goes instead — the default taken and recorded under `Decisions I made on my own`, or `ABANDON: AC<n> decision` with a sub-issue.

Everything the board prints is also appended to `~/.mmw/logs/board-<workspace id>-<spec>.log`, which is where to look in the morning once the monitor tab is gone.

## One board, one workspace

A board answers for the Herdr workspace it was started in: it acts on the sessions in that workspace and leaves every other one alone, and the Herdr names it hands out carry the workspace id — `w2q-issue-61` rather than `issue-61`. Herdr's names are unique among live agents across the whole server, so without that two repositories each holding a ticket #100 would collide and the second one would not start.

Nothing about this needs setting up: `run` opens the board in the workspace you type it in, and several projects can be running their own nights at the same time. The ticket branch is still `issue-61` — the prefix is a Herdr name, not a branch name.

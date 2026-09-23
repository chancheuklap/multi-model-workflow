# How dispatch works

Read this when changing `dispatch.sh`, `relay.py`, `watchdog.py`, `status.py` or `turn-guard.py`.

## Starting a session

`start` starts the session and prints its id; `advance` prints one id per ticket it starts. The selected runner is `MMW_RUNNER`, else `runner` in `MMW_HOME/models.json`, else, when that saved value is `auto`, the runner this session itself runs in when the skill has an adapter for it, else `orca`. The agent's row is resolved against that runner's catalog.

Before reading or creating a ticket branch, `start` fetches `origin`. The base branch is the newest `worker.started.into`, else the open night's `spec.opened.into`, else the current checkout branch; `origin/<base branch>` must exist. A new ticket branch is cut from it and pushed with its upstream set. An existing `origin/issue-<n>` fast-forwards the local branch when the remote is ahead; histories with commits on both sides are refused with both counts. No path rebases, squashes or force-pushes.

After the runner starts the session, its adapter uses `attach` to associate the worktree with the ticket where it has that capability, and for a worker also to file the worktree under the worktree of the session that ran `start`, the main agent's; a reviewer, started by the worker in the worktree they share, files nothing. A failed attach is reported once on stderr and does not stop the session. Every command that prepares a merge worktree (`open`, `advance`, `land`, `reverify`, `finish`) files it the same way, once per command; a failure is one stderr line and the landing goes on. Then `start` writes `worker.started` or `reviewer.started` on the ticket. The event carries the session, runner, host, model, reasoning effort (`effort`), grade, absolute worktree path, ticket branch, base branch (`into`) and base commit. A worker's base commit is the merge-base of `origin/<into>` and the ticket branch on its ticket's first start, and the base of the newest `worker.started` on every later start, so a replacement's own run still counts the commits the worker before it made; a `ticket.landed` after that newest start puts the earlier work into `origin/<into>`, and the start after it takes the merge-base again. `retract` finds the newest worker session in these events and asks that session's runner only. `land` stops every session the ticket's events name, and `suspend` every session still holding a ticket of the batch, each through the runner its event names. `wait` reads the ticket and asks no runner. `resume` sends to the newest worker session whose hold no event has ended, as **Events and holds** below defines them.

A start the runner refuses is refused once, exit 2: no retry and no other host or runner; stderr names the reason.

`start <n> worker` replaces a worker whose events still show it live. It checks origin and the ticket branch, stops the old session through its runner, commits tracked edits as `wip(#<n>): uncommitted work of <that worker>`, pushes the branch, writes `worker.replaced`, and starts the new worker in the same workspace. The branch, commits and product slot carry over; instructions given only inside the old session do not. A worker that will not stop, or a rejected push, is refused and nothing starts beside it. `retract` and `suspend` also commit and push before releasing a worktree, claim, slot or event hold. A push rejection never uses force and leaves the recoverable state standing.

A worker takes no product slot when it starts. The slot lifecycle and its two limits are in the `ui-acceptance` skill's `references/product-answers.md` under **`instance`**. When a criteria run gets no slot, `verify-ticket.py` exits 3 and posts `worker.queued`, and the relay wakes the worker once a slot is given back.

## Events and holds

Every comment this pipeline writes on a ticket is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block that programs read. A ticket's state is the fold of its events in comment-id order; the first lines are not read.

A ticket is held from `ticket.claimed` or any `*.started`. `ticket.landed`, `ticket.returned`, `ticket.bounced`, `ticket.released` and `spec.suspended` end every hold. `worker.retracted`, `worker.lost`, `worker.replaced`, `reviewer.lost` and a `ticket.refused` naming its session end that one session's hold, matched by runner and session together. `reviewer.reported` ends the hold of the session that produced it. `ticket.passed` ends none, because the close after it can fail and leave the worker retrying; no label ends a hold. The same rules apply across runners and machines.

## Results, watches and wakes

The session is working when `start` returns. Its result is an event: `ticket.passed` or `ticket.returned` from a worker, `reviewer.reported` from a reviewer. The caller ends its turn after starting a session; it is woken when the result lands and never polls the session.

The relay watches a night's spec from `open` to `summary` or `suspend`, and tickets outside a night from `open-ticket` or `adopt` to `land`. Each watch records its main agent. Two watches never share a ticket; one relay process per repository carries all watches and ends with the last. `start` and `advance` refuse a ticket no running relay watches because its result would wake nobody.

A wake is `#<n> <event>`, with `relay.recovered since <time>` as the relay-wide form. The worker receives `reviewer.reported`, `reviewer.lost`, and `worker.queued` after a slot is given back. The main agent receives `ticket.passed`, `ticket.returned`, `ticket.refused`, `child.opened` of kind `contract`, `fault` or `decision`, `worker.lost`, and `relay.recovered`. A recovered relay reads every ticket again and queues the events it found after the recovery wake.

Those three kinds are the whole of what a `child.opened` wakes anyone for. A `finding` or `deferred` child is written on its ticket and wakes nobody, so the closing pass reads every ticket of the batch and never its own wakes.

## The watchdog and turn guard

A dead session writes no event. The watchdog covers that gap: one process per repository, restarted when necessary by the turn guard at the end of a main agent's turn while a watch is open.

Every minute the watchdog asks two questions of the relay. Is it running — its lock names a live process that finished a cycle within its grace — or nothing is relaying and the finding is `relay down`. Is it reading — its last cycle that read the tracker is within that grace too — or the process is there and cannot see the tracker, and the finding is `relay not reading`, which clears itself with the first read that works and calls for no `open`. Then, for each held open ticket silent for ten minutes, and each ticket waiting for a product slot regardless of silence, it asks every session still holding it through that session's runner, only when the session was started on this machine. A stopped session gets `worker.lost` or `reviewer.lost`; the relay wakes the main agent for `worker.lost` and the worker for `reviewer.lost`.

Other findings go directly to the watch's main agent in one message, each beginning `watchdog:`: the relay is down; the relay is cycling and not reading the tracker; a runner could not report liveness; the session was started on another machine; a held ticket has no session to ask; a worker has been alive and silent for an hour with nothing to wait on; an event is unreadable; or the watchdog cannot read the tracker. These are not wake-queue rows and are not acked.

While tickets are held and the watchdog is not healthy, the turn guard installed by `install.sh` keeps the turn from ending. On a host that cannot hold a turn, it sends one follow-up message. It acts once per turn end, and its text names the command that arms the watchdog.

## Opening a night

`check` and `open` infer the project branch from an earlier `spec.opened.project`, then `branch.<base branch>.vscode-merge-base`, then the base branch's creation reflog, then the uniquely closest eligible origin branch. The default branch is never a project branch: a reflog naming it is passed over and it is no history candidate. They refuse a default base branch, a project branch recorded or configured as the default branch, an ambiguous result, or local/origin divergence.

`check` reports the project branch, its source, the counts an `open` would push and the number of project-branch commits the base branch would take, without pushing. It also runs `install.sh --check`; an incomplete install is not a refusal: when the dispatch skill runs from the checkout `~/.mmw/installed-root` names, `install.sh` runs to repair it, and what `--check` still reports is printed as a warning. It checks the runner adapter and every required `models.json` row, checks each host where the runner exposes that status, and checks queued tickets' worker-grade labels.

`open` fetches origin and fast-forward pushes a local-only or locally ahead project branch and base branch. The base branch then takes every commit `origin/<project branch>` has that it lacks: a fast-forward push when the base has no commits of its own, otherwise a merge made and pushed in `.worktrees/merge-<base branch>` with no repository checks. A conflict is the only refusal, exit 2, nothing pushed. The checkout fast-forwards to the new `origin/<base branch>` when git allows it, and says one stderr line when it does not. `open` then opens the spec watch with the calling session as main agent, and writes `spec.opened` with its runner, session, `into` and `project`. Opening the same night again keeps the project branch, replaces the watch's main agent with the calling session and leaves other watches alone. A relay or event-write failure can follow successful branch pushes; running `open` again completes the operation. A watch whose main agent's runner has reported it stopped for an hour is closed by the relay.

Ticket branches are cut from fetched `origin/<base branch>` and their worktrees live under the main checkout's `.worktrees/`. Landing and reverify use the recorded origin branch, not the current checkout or its local base branch.

## How `advance` processes a batch

`advance` first stops the sessions of tickets already returned, then lands passed tickets, gives back claims whose holds ended, reads the frontier again and dispatches it. It refuses a night with no relay watch that it cannot open again for the recorded main agent. A merge conflict or red repository check records a bounce for that ticket and the rest continue; the first bounce of the night returns it to the worker queue once, and the second sends it to triage.

Passed tickets are processed in closing order. For each unlanded `ticket.passed`, `advance` fetches `origin/<into>`, resets the persistent detached worktree `<main checkout>/.worktrees/merge-<into>` to it, merges the exact `ticket.passed.commit`, checks the result, and fast-forward pushes it. One lock per base branch permits one merge at a time. Tracked files are reset to the newly fetched base before every ticket and every push retry.

Only after the push does `advance` archive the ticket workspace and write `ticket.landed`. It then deletes local and origin copies of the ticket branch when no worktree uses them and each is contained in `origin/<into>`; unlanded work and bounced workspaces stay. Deletion failure does not undo landing. An open ticket's commit is never merged. The base branch name comes from `spec.opened.into`, `worker.started.into` and `ticket.passed.into`; a local branch of that name is not the merge target.

The merge subject is `Merge branch 'issue-<n>'`. When the fetched base is an ancestor of the passed commit and that commit already has a green `repo-checks` run, no second repository check runs. Otherwise `.mmw/target.json`'s `checks` run with `MMW_BASE_REF=origin/<into>`; an absent key is stated on stderr. Conflict or red checks reopen the ticket, remove its claim, give back its slot, and write `ticket.bounced` with `files` or `commands`. When the spec's newest night event is `spec.opened`, the first `ticket.bounced` since it leaves the ticket in `ready-for-agent`; the next `advance` starts a worker in the standing workspace. A second bounce in the same night moves it to `needs-triage`. Outside an open night, a bounce goes directly to `needs-triage`. The sessions are stopped in every case and nobody is woken. A rejected non-fast-forward push repeats fetch, reset, merge and checks up to `MERGE_TRIES` times.

When the passed commit is already an ancestor of `origin/<into>`, no merge is made; the workspace is archived and the ticket is recorded landed. `ticket.landed.commit` is the passed commit. If a merge first brought it into the base, `ticket.landed.merge` is that earliest merge and `ticket.landed.base` is its first parent; a fast-forward carries neither field and links the passed commit.

A blocker releases a ticket when it lands, not when it closes. A blocker closed without a pass releases it on closing because nothing will land. A blocker this same `advance` lands releases it before the frontier is read.

A claim is the issue-tracker assignee set by `--preflight`; the frontier takes only unassigned tickets. The closeout, hand back, `land`, the `RELEASE` plan line for a lost worker, `suspend`, and `retract` can give it back. `advance` gives it back only when the ticket is open, in the agent queue, assigned to this pipeline's account, and an event has ended every hold. A hand assignment that no event showed held stays assigned. The write removes `@me`, then posts `ticket.released` with reason `worker-lost`; each release prints one line naming the ticket and reason.

A dead worker whose hold has not ended keeps its ticket off the frontier. `retract` asks the runner and, only after the session is shown gone, writes `worker.retracted`. An unreadable event also keeps the ticket held. A standing workspace alone holds nothing; the ticket's events decide whether a worker holds it, and the next `start` reuses that workspace.

When no ticket can start but open agent-queue tickets remain, stderr names each condition: unreadable events, an open or unlanded blocker, an assignee, or a live worker with its runner and session. The exit code remains unchanged because the explanation is not a command failure.

`advance` starts every frontier ticket. Product concurrency is applied later by the lease; see **Starting a session** above for its authorities.

## Interpreting a night

`status` is the fold of every ticket, not runner state. Its `note` identifies ready tickets, blockers, multiple live workers, unreadable events, a claim with no started session, a product-slot wait, or the newest event; it is empty while a worker holds the ticket. The `ac` column is the newest worker or reverify criteria count.

A live worker continues through `resume`. Its exit codes, and the message for a worker the watchdog reports silent, are in the dispatch skill's `references/night.md` under **Exit codes of `resume`**.

For a gone session with a workspace, slot or claim still held, `retract` commits tracked edits, pushes the ticket branch, runs the product's `stop`, archives the workspace, gives back the slot and claim, and writes `worker.retracted`. A rejected push leaves them standing and never force-pushes.

## Reverify and summary

`reverify` fetches origin, resets the detached merge worktree to `origin/<into>`, and runs every passed-and-landed ticket through `verify-ticket.py <n> --reverify --actor main` with `MMW_BASE_REF=origin/<into>`. Each run posts `ticket.checked` with run `reverify`, actor `main`. A passed but unlanded ticket is named and skipped. A red ticket is reopened in triage, unassigned and given `ticket.regressed`; a ticket that establishes no result is not treated as red and leaves the remaining tickets unrun. A ticket a previous reverify reopened that still carries `needs-triage` runs in the same pass and on the same commit: green, it is given `ticket.recovered`, loses the label and is closed again; red, nothing is written on it.

`reverify` records its green count, red count and the fetched `origin/<into>` commit in the repository's common Git directory. `summary` fetches origin again and refuses before any Memory mutation when that receipt is absent, red or for an older base commit. It also refuses when the frontier is nonempty, a session or untaken claim still holds a ticket, a ticket's events are unreadable, or a passed ticket has not landed. Human-acceptance, triage and blocked tickets are allowed outcomes.

`summary` refuses, with nothing posted and the watch still open, while the batch holds a finding no `child.closed` accounts for — the last count of the `Findings routed:` line — and names that count on stderr. A summary carrying no `Findings routed:` line at all is said so on stderr and posted: a count that could not be read is not a count of zero.

`summary` posts `spec.closed` with `NIGHT SUMMARY <date>` and the six lines `Closed:`, `Handed back to needs-triage:`, `Bounced:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:` and `Findings routed: <opened>/<fixed>/<became>/<skipped>/<unread>/<open>`, then closes the spec watch. `Bounced:` lists every ticket whose newest landing result is `ticket.bounced` and that carries `needs-triage`. It counts `finding` children through `child.opened` and `child.closed`; other child kinds appear on the sub-issues line, and a closed finding with no `child.closed` is `unread`. A `Reverify: <green>/<red>` line follows, from the reverify receipt `summary` requires. The relay continues for other watches and ends with the last.

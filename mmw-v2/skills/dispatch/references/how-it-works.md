# How dispatch works

Read this when a command's behaviour surprised you, or when changing the relay, watchdog or turn guard. The command and exit code to act on stay in the role's door.

`<dispatch>`, `<engine>`, `<events.py>`, `<lease.py>` and `<drive-target scripts>` are resolved in the `dispatch` skill's `SKILL.md` under `## Resolve `<dispatch>` once`.

## Starting a session

`start` starts the session and prints its id; `advance` prints one id per ticket it starts. Tonight's runner is `MMW_RUNNER`, else `runner` in `MMW_HOME/models.json`, else, when that saved value is `auto`, the runner this session itself runs in when the skill has an adapter for it, else `orca`. The agent's row is resolved against that runner's catalog.

Before reading or creating a ticket branch, `start` fetches `origin`. The base branch is the newest `worker.started.into`, else the open night's `spec.opened.into`, else the current checkout branch; `origin/<base branch>` must exist. A new ticket branch is cut from it and pushed with its upstream set. An existing `origin/issue-<n>` fast-forwards the local branch when the remote is ahead; histories with commits on both sides are refused with both counts. No path rebases, squashes or force-pushes.

After the runner starts the session, `start` writes `worker.started`, `reviewer.started` or `verifier.started` on the ticket. The event carries the session, runner, host, model, effort, grade, absolute worktree path, ticket branch, base branch (`into`) and base commit. `resume`, `wait`, `retract`, `land` and `suspend` find the session in that event and ask that runner only. The adapter then associates the worktree with the ticket where it has that capability; a failed association is reported once and does not stop the session.

A start the runner refuses is refused once, exit 2: no retry and no other host or runner. Fix stderr's reason, or change the row as [editing-models.md](editing-models.md) says and start again. When it cannot be fixed, the worker opens a `fault` child with `<engine> <n> --sub-issue fault <file>`, using the command and output as the file's body, then stops.

`start <n> worker` replaces a worker whose events still show it live. It checks origin and the ticket branch, stops the old session through its runner, commits tracked edits as `wip(#<n>): uncommitted work of <that worker>`, pushes the branch, writes `worker.replaced`, and starts the new worker in the same workspace. The branch, commits and product slot carry over; instructions given only inside the old session do not. A worker that will not stop, or a rejected push, is refused and nothing starts beside it. `retract` and `suspend` also commit and push before releasing a worktree, claim, slot or event hold. A push rejection never uses force and leaves the recoverable state standing.

A start takes no product slot. The drive-target skill's `references/runtime-environment.md` section **instance** is the authority for the slot lifecycle and its two limits; the verify-ticket skill's `references/running-criteria.md` section **A criterion that runs the product** is the authority for `worker.queued`, exit 3, its wake and its ack.

## Events and holds

Every comment this pipeline writes on a ticket is an event: a first line for a person and a trailing `<!-- mmw {...} -->` block that programs read. A ticket's state is the fold of its events in comment-id order; the first lines are not read.

A ticket is held from `ticket.claimed` or any `*.started`. `ticket.landed`, `ticket.returned`, `ticket.bounced`, `ticket.released` and `spec.suspended` end every hold. `worker.retracted`, `worker.lost`, `worker.replaced`, `reviewer.lost`, `verifier.lost` and a `ticket.refused` naming its session end that one session's hold, matched by runner and session together. `reviewer.reported`, `verifier.passed` and `verifier.failed` end the hold of the session that produced them. `ticket.passed` ends none, because the close after it can fail and leave the worker retrying; no label ends a hold. The same rules apply across runners and machines.

## Results, watches and wakes

The session is working when `start` returns. Its result is an event: `ticket.passed` or `ticket.returned` from a worker, `reviewer.reported` from a reviewer, and `verifier.passed` or `verifier.failed` from a verifier. The caller ends its turn after starting a session; it is woken when the result lands and never polls the session.

The relay watches a night's spec from `open` to `summary` or `suspend`, and tickets outside a night from `open-ticket` or `adopt` to `land`. Each watch records its main agent. Two watches never share a ticket; one relay process per repository carries all watches and ends with the last. `start` and `advance` refuse a ticket no running relay watches because its result would wake nobody.

A wake is `#<n> <event>`, with `relay.recovered since <time>` as the relay-wide form. The worker receives `reviewer.reported`, `verifier.passed`, `verifier.failed`, `reviewer.lost`, `verifier.lost`, and `worker.queued` after a slot is given back. The main agent receives `ticket.passed`, `ticket.returned`, `ticket.refused`, `child.opened` of kind `fault` or `decision`, `worker.lost`, and `relay.recovered`. A recovered relay reads every ticket again and queues the events it found after the recovery wake.

Only `ack` removes a delivered wake. Until then, restarting the relay sends it again. The ack reads only the calling session's queue; a wake already acked, sent to another session, or never queued is refused and nothing is removed.

## The watchdog and turn guard

A dead session writes no event. The watchdog covers that gap: one process per repository, restarted when necessary by the turn guard at the end of a main agent's turn while a watch is open.

Every minute the watchdog checks the relay. For each held open ticket silent for ten minutes, and each ticket waiting for a product slot regardless of silence, it asks every session still holding it through that session's runner, only when the session was started on this machine. A stopped session gets `worker.lost`, `reviewer.lost` or `verifier.lost`; the relay wakes the main agent for `worker.lost` and the worker for the other two.

Other findings go directly to the watch's main agent in one message, each beginning `watchdog:`: the relay is down; a runner could not report liveness; the session was started on another machine; a held ticket has no session to ask; a worker has been alive and silent for an hour with nothing to wait on; an event is unreadable; or the watchdog cannot read the board. These are not wake-queue rows and are not acked.

While tickets are held and the watchdog is not healthy, the turn guard installed by `install.sh` keeps the turn from ending. On a host that cannot hold a turn, it sends one follow-up message. It acts once per turn end, and its text names the command that arms the watchdog.

## Opening a night

`check` and `open` infer the project branch from an earlier `spec.opened.project`, then the base branch's creation reflog, then `branch.<base branch>.vscode-merge-base`, then the uniquely closest eligible origin branch. They refuse a default base branch, a project branch equal to the default branch, an ambiguous result, or local/origin divergence.

`check` reports the project branch, its source and the counts an `open` would push, without pushing. It also runs `install.sh --check`, checks the runner adapter and every required `models.json` row, checks each host where the runner exposes that status, and checks queued tickets' worker-grade labels.

`open` fetches origin, fast-forward pushes a local-only or locally ahead project branch and base branch, opens the spec watch with the calling session as main agent, and writes `spec.opened` with its runner, session, `into` and `project`. Opening the same night again keeps the project branch, replaces the watch's main agent with the calling session and leaves other watches alone. A relay or event-write failure can follow successful branch pushes; running `open` again completes the operation. A watch whose main agent's runner has reported it stopped for an hour is closed by the relay.

Ticket branches are cut from fetched `origin/<base branch>` and their worktrees live under the main checkout's `.worktrees/`. Landing and reverify use the recorded origin branch, not the current checkout or its local base branch.

## How `advance` processes a batch

`advance` first stops the sessions of tickets already returned, then lands passed tickets, gives back claims whose holds ended, reads the frontier again and dispatches it. It refuses a night with no relay watch. A merge conflict or red repository check bounces that ticket to triage and the rest continue.

Passed tickets are processed in closing order. For each unlanded `ticket.passed`, `advance` fetches `origin/<into>`, resets the persistent detached worktree `<main checkout>/.worktrees/merge-<into>` to it, merges the exact `ticket.passed.commit`, checks the result, and fast-forward pushes it. One lock per base branch permits one merge at a time. Tracked files are reset to the newly fetched base before every ticket and every push retry.

Only after the push does `advance` archive the ticket workspace and write `ticket.landed`. It then deletes local and origin copies of the ticket branch when no worktree uses them and each is contained in `origin/<into>`; unlanded work and bounced workspaces stay. Deletion failure does not undo landing. An open ticket's commit is never merged. The base branch name comes from `spec.opened.into`, `worker.started.into` and `ticket.passed.into`; a local branch of that name is not the merge target.

The merge subject is `Merge branch 'issue-<n>'`. When the fetched base is an ancestor of the passed commit and that commit already has a green `repo-checks` run, no second repository check runs. Otherwise `.mmw/target.json`'s `checks` run with `MMW_BASE_REF=origin/<into>`; an absent key is stated on stderr. Conflict or red checks reopen the ticket in `needs-triage`, remove its claim, give back its slot, and write `ticket.bounced` with `files` or `commands`. Its workspace stays and nobody is woken. A rejected non-fast-forward push repeats fetch, reset, merge and checks up to `MERGE_TRIES` times.

When the passed commit is already an ancestor of `origin/<into>`, no merge is made; the workspace is archived and the ticket is recorded landed. `ticket.landed.commit` is the passed commit. If a merge first brought it into the base, `ticket.landed.merge` is that earliest merge and `ticket.landed.base` is its first parent; a fast-forward carries neither field and links the passed commit.

A blocker releases a ticket when it lands, not when it closes. A blocker closed without a pass releases it on closing because nothing will land. A blocker this same `advance` lands releases it before the frontier is read.

A claim is the issue-tracker assignee set by `--preflight`; the frontier takes only unassigned tickets. The closeout, hand back, `land`, the `RELEASE` plan line for a lost worker, `suspend`, and `retract` can give it back. `advance` gives it back only when the ticket is open, in the agent queue, assigned to this pipeline's account, and an event has ended every hold. A hand assignment that no event showed held stays assigned. The write removes `@me`, then posts `ticket.released` with reason `worker-lost`; each release prints one line naming the ticket and reason.

A dead worker whose hold has not ended keeps its ticket off the frontier. `retract` asks the runner and, only after the session is shown gone, writes `worker.retracted`. An unreadable event also keeps the ticket held. A standing workspace alone holds nothing; the ticket's events decide whether a worker holds it, and the next `start` reuses that workspace.

When no ticket can start but open agent-queue tickets remain, stderr names each condition: unreadable events, an open or unlanded blocker, an assignee, or a live worker with its runner and session. The exit code remains unchanged because the explanation is not a command failure.

`advance` starts every frontier ticket. Product concurrency is applied later by the lease; see **Starting a session** above for its authorities.

## Interpreting a night

`status` is the fold of every ticket, not runner state. Its `note` identifies ready tickets, blockers, multiple live workers, unreadable events, a claim with no started session, a product-slot wait, or the newest event; it is empty while a worker holds the ticket. The `ac` column is the newest worker or reverify criteria count.

Use these facts when the table and wake need interpretation:

- `ticket.passed`, or a ready frontier row: `advance` lands or starts it.
- `child.opened` of kind `fault`: the worker stopped. Read the child from `<events.py> fold <n>`, fix its cause, then resume the worker.
- `child.opened` of kind `decision`: the worker took the default and continues; the question waits for the user.
- A live worker whose newest event is `reviewer.started` or `verifier.started`: it ended its turn waiting on that result; do nothing.
- `ticket.returned`: the closeout handed it back, gave its claim back and left the workspace for triage. `advance` continues the rest of the batch.
- A bounced ticket: it is open in triage, unclaimed and excluded from later advances; its workspace remains and tickets it blocks do not run that night.
- `ticket.refused`: its event names the session and reason. It ended that session's hold and claimed nothing. Fix the reason; the next `advance` starts it when the frontier permits.
- `worker.lost`: its hold ended. `advance` gives back the claim, commits and pushes recoverable tracked work at the next start, and starts another worker in the standing workspace.
- `relay.recovered`: the relay's subsequent rows contain the recovered events.

A live worker continues through `resume`. Exit 0 delivered the message; exit 4 handed it over without proving a new turn and must not be sent again; exit 3 delivered nothing or could not decide, so wait and retry the same command; exit 2 means the session in `worker.started` is gone, so read `status` and do not send again. After repeated exit 3 with no ticket event, `start <n> worker` replaces it. The replacement checks and recoverable state are in **Starting a session**.

Watchdog findings have these consequences:

- `relay down`: reopen the spec or ticket watch. The relay's full read queues missed events.
- `liveness unknown`: send `Say in one line where you are, then continue`. Exit 0 proves the session is there; exit 2 leads to `retract`; any other result waits for the user.
- `held with no session to ask`: read `status`; when nothing is working it, run `retract`.
- `cannot read the board`: run the named `gh issue view` read. Wait out tracker or network failure; a credential failure is for the user.
- `events unreadable`: a person fixes the named comment.
- `silent … with nothing to wait on`: resume with the instruction to continue, open a `fault` child and stop if something outside the code blocks it, or open a `decision` child, take the default and continue when only the user can decide.

When `status` shows a worker live but its runner no longer has the session, `retract` closes that start, gives the claim back and leaves the ticket ready for `advance`. For a gone session with a workspace, slot or claim still held, `retract` commits tracked edits, pushes the ticket branch, runs the product's `stop`, archives the workspace, gives back the slot and claim, and writes `worker.retracted`. A rejected push leaves them standing and never force-pushes. Exit 0 prints `retract #<n>: archived <a>, slot given back <s>, claim given back <c>`; `archived` and `slot given back` are 1 only when performed. Exit 2 names a live or unknown session, unreadable events, commit or push failure, missing lease tool, bad repository or arguments, or a product still listening.

Changing a ticket's `junior-worker` or `senior-worker` label changes the worker grade read by its next `start`. A live worker with no fault is not resumed. An empty frontier and no live agent lead to the closing pass.

## Reverify and summary

`reverify` fetches origin, resets the detached merge worktree to `origin/<into>`, and runs every passed-and-landed ticket through `<engine> <n> --reverify --actor main` with `MMW_BASE_REF=origin/<into>`. Each run posts `ticket.checked` with run `reverify`, actor `main`. A passed but unlanded ticket is named and skipped. A green batch exits 0. Exit 1 reopens each red ticket in triage, removes its assignee and writes `ticket.regressed`. Exit 2 means a ticket could not establish a result; it is not red, nothing is changed on it, and the remaining tickets are skipped.

`summary` posts `spec.closed` with `NIGHT SUMMARY <date>` and the six lines `Closed:`, `Handed back to needs-triage:`, `Bounced:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:` and `Findings routed: <opened>/<fixed>/<became>/<skipped>/<unread>/<open>`, then closes the spec watch. It counts `finding` children through `child.opened` and `child.closed`; other child kinds appear on the sub-issues line, and a closed finding with no `child.closed` is `unread`. A reverify run in this checkout adds `Reverify: <green>/<red>`. The relay continues for other watches and ends with the last.

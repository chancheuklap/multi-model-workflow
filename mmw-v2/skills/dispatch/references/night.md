# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. How a wake reaches you and what you do on one is in `SKILL.md` next to this file, and `<dispatch>`, `<engine>`, `<lease.py>` and `<drive-target scripts>` are resolved in its `## Resolve `<dispatch>` once` section.

Between the steps below you end your turn. The relay you start in step 1 wakes you when a ticket of the batch comes to rest (step 3), and the watchdog tells you when the board has gone silent where it should not (`SKILL.md`, next to this file, says what it is); nothing else does, and no agent polls another.

## 1. The user says the night starts

Run on the base branch, in whichever checkout has it: the main checkout or a task worktree of your own. It must already exist on `origin`, and the local branch must not be ahead of `origin/<base branch>`. Ticket branches are cut from the fetched `origin/<base branch>`; their worktrees always go under the main checkout's `.worktrees/`, and a name `issue-<n>` there belongs to the pipeline.

```bash
<dispatch> check <spec>
```

**Exit 0:** the machine is ready — `origin` exists, `git fetch origin` and a dry-run push work, the current branch exists at `origin/<base branch>` and is not ahead of it; `install.sh --check` passed; tonight's runner has an adapter; every live-table row resolves, each listed host is `available`, and each queued ticket has at most one valid worker-grade label. Then open the night. **Exit 2:** stderr gives one line per failure. A local-ahead line includes the exact count and `git push origin <base branch>`. Fix what the lines name — run `install.sh`, change an invalid row, relabel the ticket, wait for the host, or push the named branch — or tell the user when only they can, then run `check` again. Do not open the night on 2: a row that does not resolve refuses every start of its agent.

Then, from this session — the one the night's wakes must reach:

```bash
<dispatch> open <spec>
```

It fetches origin and refuses before opening anything unless the current base branch exists remotely and is not locally ahead. It then opens a watch on the spec's tickets with this session as its main agent and writes `spec.opened` with that runner, session and `into=<base branch>`. **Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>`; stderr says whether the watch was opened now or was already open, and whether the relay was started or found running. Opening the same night again makes this session its main agent and touches no other watch. **Exit 2:** nothing was opened and every existing watch is unchanged; stderr names the remote, a session no runner can identify, an overlapping `open-ticket` or `adopt` watch, the board, the relay or the event write. Run from a session a runner can send to, land or wait for the overlapping ticket, or fix the named failure, then run `open` again. `advance` refuses a night that is not open.

A watch whose main agent's session has been shown stopped by its runner for an hour is closed by the relay itself: a night whose main agent was closed without `summary` or `suspend` is not read for ever, and the next `open` reads everything again.

## 1b. Before the batch: what the batch cannot be run on

When the spec's tickets drive a screen contract, run this once, before the first
`advance`:

```bash
<engine> <spec> --lint
```

It starts nothing and runs no product. It reads the batch's tickets and the contract they
name, and prints one finding per line: a `--pages` mount that is not a page of that
contract, a `boundary-check.py --run` with an empty command, a `journey.py run <name>`
with no directory under `.mmw/journeys/`, a `CHECK:` that stubs the application's own
network, an interface ticket that names no contract rows. Only `ERROR` moves the exit
code. Answer the findings in one sitting rather than one per ticket per night: on
2026-09-07 the same class of defect arrived three at a time, hours apart, each costing a
whole ticket.

Whether the consuming repository can be driven at all is a separate question, answered
there by `python3 <drive-target scripts>/screen_driver.py target --check`, which prints
every `.mmw/target.json` field still to answer and exits 0 once the file is complete.

**A clean lint is not a finished contract.** It reads text, not a running product: a story
whose page renders nothing, a boundary command whose assertion does not depend on the
click, a journey whose script cannot log in — none of those are visible until a finished
implementation runs its criteria, and they are handed back the way any other defect is.

## 2. First `advance`

Stay on this branch all night. Every `advance` merges into whatever `HEAD` is on.

```bash
<dispatch> advance <spec>
```

**Exit 0:** stdout is one session id per ticket it started; each is already running, with its `worker.started` event on the ticket. Stderr carries the line `advance #<spec>: merged <m>, already in <s>, released <g>, started <k>, refused <r>`; each claim given back prints a line of its own naming the ticket and why, and when nothing could start while tickets are still in the agent queue, stderr names every one of them and the condition holding it. Then end your turn. **Exit 4:** everything under 0 happened, and the runner refused the start of one or more tickets: each is counted under `refused`, its line on stderr carries the runner's reason, and it was not retried. That ticket stays on the frontier, and nothing wakes you about it. Fix what the reason names — a host that is not logged in, a model the runner's catalog does not have (change that agent's row in the live table) — then run `advance` again. When it cannot be fixed tonight, end your turn only while a worker of the batch is still live: each wake runs `advance` again, and it refuses that ticket again. With no worker live, no wake will come; tell the user which tickets were refused and why. **Exit 2:** nothing was touched; read stderr; if the night is not open — no relay watches the spec — run `open <spec>` and then `advance` again; if it is uncommitted tracked changes, commit or set them aside and run `advance` again; if it is the `.git` lock, held for `MERGE_TRIES` tries, run `advance` again. **Exit 3:** a merge is in conflict, still in the tree; everything before it is merged and committed, and nothing was archived, created or dispatched. Resolve it with the `resolving-merge-conflicts` skill — never `--abort` — run this repository's own checks, commit the merge, then `advance` again; the conflict report on stderr already names the two sides and the conflicted files.

What `advance` does inside that one command — merge, archive, give claims back, then dispatch — is the next section.

## `advance` merges, releases, then dispatches

`<dispatch> advance <spec>` merges the branch of every ticket that closed with a `ticket.passed` event and has not landed into the branch you are on at that moment, records `ticket.landed` on each, archives each merged ticket's workspace, gives back the claims whose workers are gone, then dispatches every ticket on the frontier.

An open ticket's branch is never merged, whatever its criteria say: closed with `ticket.passed` is the whole rule. A contract defect a worker cannot answer from its own code comes back as a red criterion and a `HANDOFF REQUIRED` ticket, the way any other defect does. The branch you open the night on is the base branch, so stay on it all night: every `advance` merges into whatever `HEAD` is on. Its name travels in `spec.opened.into` and each ticket's `worker.started.into`.

The four are one command because the order is the reason. A new ticket branch is cut from the fetched `origin/<base branch>`; the frontier is read after the claims come off, so a ticket freed by this run starts in this run rather than the next one; and `advance` archives a ticket's workspace only after that ticket's branch is already in `HEAD`, releasing its lease first.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its events carry a `ticket.passed` that no `ticket.landed` has followed, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. A branch already in `HEAD` is recorded as landed without a merge, which is what makes the command safe to run at any time; an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open and carries `ticket.returned`, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

A ticket is claimed by being assigned to the account this pipeline is signed in as — `verify-ticket.py --preflight` does it — and the frontier takes only unassigned tickets, which is what keeps a second worker off a ticket somebody is already working. Six paths take a claim off: the closeout, the hand back to triage, `land`, `advance`'s **give a claim back** (the `RELEASE` line) for a claim whose worker is gone, `suspend`, which gives back every claim of the batch, and `retract`, which gives the claim back when a ticket's session is gone. A session that ends any other way — a crash, a machine restart, a workspace archived from outside this pipeline — leaves the claim standing until an event ends its hold: the watchdog writes `worker.lost` once the session's runner shows it stopped, and `retract` does the same by hand.

So `advance` gives a claim back when four things hold at once: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and an event on it has ended every hold on it. A ticket is held from its `ticket.claimed` or any `*.started`; `ticket.landed`, `ticket.returned`, `ticket.released` and `spec.suspended` end every hold, and `worker.retracted`, `worker.lost`, `worker.replaced` and a `ticket.refused` that names its session end the one session they name by its runner and id. `ticket.passed` ends none, since the close after it can fail and leave the worker retrying, and no label ends one. A claim no event ever showed held — assigned by hand, say — is kept: nothing on the ticket shows its worker gone. All of this is read off the ticket, never off a runner: a runner answers for one machine, and a worker started on Orca, on Herdr or on a second machine holds its ticket exactly as one on Paseo does. The write is `gh issue edit <n> --remove-assignee @me`, followed by a `ticket.released` event (reason `worker-lost`), so a ticket a person took for themselves is untouched and stays off the frontier, which is the right answer — somebody has it. Each release prints one line naming the ticket and saying why.

The other side of that rule: a worker whose session died without anything ending its hold keeps its ticket held, and the ticket stays off the frontier until something does. `<dispatch> retract <n>` is that something — it asks the runner, and only once the session is shown gone does it undo the start and write `worker.retracted`. A ticket whose events cannot be read is held the same way, and says so.

A standing workspace is not a run. A worker holds its ticket only while its events show it live, whatever directory is still on disk; the workspace stays for `start` to reuse, and the next worker picks the branch up where the last one left it.

A blocker lets go of the ticket it blocks when it has **landed**, not when it closed. A blocker that closed without a pass — closed by a person, or as not planned — lets go on closing, since nothing of it will ever land; one that this same `advance` merges before it dispatches lets go in that `advance`.

When nothing can start and the batch still holds open tickets in the agent queue, `advance` names each of those tickets on stderr with the condition holding it — its events cannot be read, blocked by a ticket still open or passed and not landed, claimed by somebody, or already held by a live worker, named with its session and runner. An empty frontier and a finished batch print the same nothing otherwise, and the difference between them is not visible from outside the frontier's conditions. The exit code is unchanged: this is an explanation, not a failure.

`advance` starts every ticket on the frontier: how many workers write code at once is the frontier's answer alone. A product that cannot move its ports says so in `.mmw/target.json` as `"instance": {"max": <n>}`, and that limit bites later, at the first run of a worker's criteria that runs the product — the moment its worktree claims a slot. A worker that finds `max` slots already held by this repository — by its ticket worktrees or by the main checkout running `reverify` — runs nothing and ends its turn, its ticket carrying a `worker.queued` event, and the relay wakes it when a slot is given back. A slot is held from that first run until the ticket's work ends, and given back at that moment: `advance` gives it back when it archives a landed ticket's workspace or releases a lost worker's claim, the closeout when it hands the ticket back, `suspend` and `retract` with the claim. The main checkout's `reverify` gives its slot back as each run ends.

## 3. Each time something wakes you

One thing wakes you: a **wake** from the relay, `#<n> <event>` — `#<n> ticket.passed`, `#<n> ticket.returned`, `#<n> ticket.refused`, `#<n> child.opened` (its kind `fault` or `decision`) or `#<n> worker.lost` — sent the moment that event was read off ticket `<n>`, or `relay.recovered since <time>` when the relay was down or could not read the board from that time on. It names the ticket and the event and nothing else; the rest is on the board. Your workers' own middle states — asleep on a reviewer, asleep on a verifier, waiting for a product slot — never reach you: those wakes go to the worker. The other thing that reaches you is a message from the watchdog, one line with the findings separated by ` | `, each beginning `watchdog:`; its rows are at the end of the table below, and it is handled in the same order.

When a turn end of yours is refused, or answered with a message, that begins `MMW turn guard:`, tickets are held and the watchdog is not running, and the hook could not start it. Run the `watchdog.py arm` command the text names; exit 0 means it runs now. Exit 1 prints why it would not start: fix that when you can, and if you cannot, open a `fault` child with `<engine> <n> --sub-issue fault <file>` on any held ticket, with that output as the file's body, because nothing will notice a worker that dies tonight. Then end your turn; the guard asks once per turn end.

Handle each wake in this order, one wake at a time — two tickets landing seconds apart are two wakes, and you get the second after you end your turn:

1. Were you running a command when it arrived? A wake can cut a running command short, and the command reports being interrupted rather than finishing. Run that command again before anything else — `advance` in particular is written to be run again at any time, and picks up whatever the interrupted run left behind.
2. Run `<dispatch> status <spec>`. It reads the tracker and nothing else: each row is the fold of that ticket's events, and no runner is asked. Exit 0: stdout is the table (`ticket`, `runner`, `session`, `worker`, `since`, `phase`, `ac`, `note`) — the runner and session of the ticket's newest worker, `live` or the event that closed it, when it was started, and the newest event's name. Exit 2: the tracker could not be asked, or answered for fewer of the spec's tickets than it counts — one `dispatch: …` line on stderr and no table; run it again once it answers. The `note` column is `ready`, `waiting on #<m>` (with `(passed, not landed)` when the blocker closed and has not landed), `<k> live workers: …` (more than one start on the ticket is still open), `events unreadable: …` (a comment carries an event block nothing can read, so the ticket is held until a person fixes that comment), `claimed, no session started yet` (a `ticket.claimed` holds it and no start is recorded), `waiting for a product slot since <time> (<reason>, <k> of <max> held)` (a run of its criteria is queued for a slot — the worker is alive and not done; nothing to do but let a ticket that holds a slot finish), the newest event's first line, or empty while a worker holds it. The `ac` column is `<met>/<total>` from the newest run of its criteria, the worker's own or a reverify.
3. Take every row the table matches, not only the ticket you were woken about: the wake says one thing happened; the table says what is true.

| What you see | What you do |
| --- | --- |
| The wake reads `#<n> ticket.passed`, or the frontier has `ready` rows that nothing holds | Nothing here: the `advance` below merges it and starts what it frees |
| The worker is live and the work should continue | `<dispatch> resume <n> "<what you settled, then: continue>"`. Exit 0: the text was sent. Exit 4: the session was handed the text and its runner cannot show a turn starting on it; the text is in the session and the worker reads it when its current turn ends — do not send it again. Exit 3: it is in a turn and did not take the message — wait and run the same command again, do not go looking for another way to reach it; a runner that hands a message over before it confirms the turn started can answer 3 for a message that arrived, so word the retry so that a worker which got both reads them as one instruction. Exit 2: the worker session the ticket's `worker.started` event names is not there any more — read `status`, do not send again |
| `resume` has exited 3 again and again while nothing new lands on the ticket | The session takes no message. `<dispatch> start <n> worker` replaces it: it checks origin, stops that session through its runner, commits what it left uncommitted, pushes the ticket branch, writes `worker.replaced` naming it, and starts a new worker in the same workspace — the branch, its commits and the worktree's product slot are all there, and what the worker was told in that session is not. Exit 2 says which check, stop, commit or push failed; no second worker starts |
| The wake reads `#<n> child.opened` and the child is of kind `fault`: the worker has stopped | Read that child — its number is the event's `child`, listed under `children` by `python3 <events.py> fold <n>`. Fix the cause it names. Then `<dispatch> resume <n> "… continue"` |
| The wake reads `#<n> child.opened` and the child is of kind `decision` | A question only a person can settle, opened for the morning; the worker took the default and carries on. Nothing to do tonight |
| The ticket is still `OPEN`, its worker `live`, and its newest event is a `reviewer.started` or `verifier.started` | Not a stop: the worker ended its turn on that child and the relay wakes it when the child's result lands. Do nothing |
| The wake reads `#<n> ticket.returned` | That ticket is finished for tonight: the closeout already swapped its label for `needs-triage`, gave its claim back and left it open, and it is the morning's triage rather than yours. Its workspace stays for the next `start`, so do not archive it. What is yours is the rest of the batch, which that ticket may have been blocking, and the `advance` below takes it up |
| The wake reads `#<n> ticket.refused` | The ticket refused to be claimed: its `ticket.refused` event names the `reason` and the worker session that refused, and its comment says it in a sentence. That event ended the hold of that session and of no other, and the refusal claimed nothing, so once you fix what it names the ticket is on the frontier again and the `advance` below starts it. A reason that is still true when `advance` runs (the ticket is `blocked`, not `ready-for-agent`, or someone else holds it) keeps it off the frontier, and `status` says why |
| The wake reads `#<n> worker.lost` | The ticket's worker is gone, and that event ended its hold: the `advance` below gives the claim back and starts the ticket again in its standing workspace, and that start first commits what the lost worker left uncommitted and pushes the ticket branch, so the new worker continues from it. Nothing else to do |
| The wake reads `relay.recovered since <time>` | Nothing was lost: the relay read every ticket again and queued what it found, and those wakes come after this one. The table is what is true now |
| A finding reads `watchdog: relay down (…)` | Nothing wakes you about the board until the relay runs again. `<dispatch> open <spec>` (`open-ticket <n>` for one ticket): it opens the watch again with this session as its main agent and starts the relay, whose full read on start queues every wake you missed. Nothing to ack |
| A finding reads `watchdog: #<n> liveness unknown: …` | The runner of one of the ticket's sessions — its worker, reviewer or verifier, named in the finding — could not say whether that session is alive, or the session was started on another machine, whose runner only that machine can ask: not a death, and not a proof of life. `<dispatch> resume <n> "Say in one line where you are, then continue"`. Exit 0: it is there. Exit 2: its session is gone — `<dispatch> retract <n>`. Anything else: leave it for the morning. Nothing to ack |
| A finding reads `watchdog: #<n> is held with no session to ask, …` | A claim no started session names, or only sessions whose results are already in. Read the row in `status`; when nothing is working the ticket, `<dispatch> retract <n>`. Nothing to ack |
| A finding reads `watchdog: cannot read the board since <time>: …` | The watchdog has not read every ticket for longer than its tolerance, and names the read that failed; until it can, it is not healthy, so your turn guard holds your turn ends. Run that read yourself (`gh issue view <n>`): a tracker or network failure is waited out, a failure only you can fix — an expired `gh` login, say — is fixed now. Nothing to ack |
| A finding reads `watchdog: #<n> events unreadable` | The `events unreadable` note of `status`: a comment carries an event block nothing can read, and a person fixes it in the morning. Nothing to ack |
| `status` shows the worker `live`, and its runner no longer has that session | `<dispatch> retract <n>`: the retraction closes that start on the ticket's events and gives the claim back, so the ticket is on the frontier again and the `advance` below starts it, reusing its standing workspace and branch |
| A finding reads `watchdog: #<n> silent since <time> with nothing to wait on: …` | The worker's session is alive, nothing has landed on its ticket for an hour, and it waits on no reviewer, verifier or product slot: it ended its turn with no result, and nothing will wake it. `<dispatch> resume <n> "You ended your turn with no result on the ticket. Carry on from where its events say you are. If something outside your code stops you, open a fault sub-issue saying what you ran and what you saw, then stop; if only a person can settle it, open a decision sub-issue, take the default and carry on."` Its exit codes are those of the `resume` row above. Change no label. Nothing to ack |
| The worker is live and nothing is wrong | Do not `resume` |
| A ticket's session is gone and its worktree, slot or claim is still held | `<dispatch> retract <n>`: it commits tracked edits, pushes `issue-<n>` to origin, then runs the product's `stop`, archives the workspace, gives the slot and claim back, and writes `worker.retracted`; the branch stays, so the next `start` reuses it. A rejected push leaves all of those standing and never force-pushes. Exit 0: stderr reads `retract #<n>: archived <a>, slot given back <s>, claim given back <c>`; `slot given back` and `archived` are each 1 only when that operation happened. Exit 2: nothing was released; stderr names the live or unknown session, unreadable events, commit or push failure, missing lease tool, repository or argument error, and a product still listening names where to stop it |
| A ticket should be worked at the other worker grade | Swap its `junior-worker` / `senior-worker` label on the tracker; the next `start` reads it |
| `status` shows an empty frontier and no live agent of this spec | Handle this wake to its end, then go to `## 4. The closing pass` |

4. Run `<dispatch> advance <spec>` once, whatever the wake named. Every wake gets exactly one: merges are one commit per ticket anyway, so merging as each ticket lands cuts the history no finer, and each landing frees the tickets it blocked at once. A wake that changed nothing makes it a no-op — a branch already in `HEAD` is skipped, an empty frontier starts nothing. Its exit codes are those under `## 2. First advance`.
5. `<dispatch> ack <n> <event>` with the ticket and the event the wake named, or `<dispatch> ack relay.recovered` (exit codes in [inside-a-ticket.md](inside-a-ticket.md)). Ack last: a wake you have not acked is sent again when the relay restarts, so work cut off before this line is not lost.

Then end your turn.

## 4. The closing pass

The frontier is empty and `status` shows no live agent. If this spec's tickets still hold open findings — the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `python3 <events.py> fold <n>`, open until a `child.closed` on the ticket gives their `resolution` — route **exactly those**. If there are none, go to step 5.

Every route is carried out by one command, run once per finding, and it is the only way a finding leaves this pass:

```bash
<dispatch> route <n> <child> fixed|stale|became-ticket [<new ticket>]
```

`<n>` is the ticket the finding came from — the one whose `fold` lists it under `children` — and the spec is the one that ticket's `child.opened` for it names; neither is read off the tree, which a `became-ticket` route itself changes. It closes the finding — `fixed` as completed, `stale` as not planned — or, for `became-ticket <new ticket>`, makes it that ticket, and writes the `child.closed` event on `<n>`; that event is the one record of where the finding went, and the night summary counts by it. When `<new ticket>` is the finding itself, the finding stays open, its `mmw:child` label becomes `mmw:ticket`, and its parent moves from the ticket to the spec, because the scripts find a ticket's spec through its direct parent alone. When `<new ticket>` is another issue, the finding is closed as its duplicate and that issue gets the same label and the same parent. Exit 0: routed and recorded, or routed that way already. Exit 1: the tracker took part of it and not the rest; stderr says which, and the same command run again finishes it without doing any step twice. Exit 2: nothing was done — `<n>` carries no `child.opened` for the finding, the finding was routed another way, its `child.opened` names no spec for a `became-ticket`, the tracker could not be asked, or the arguments are wrong.

Judge each one by the four steps below, **in order, first match wins**, after the check that comes before them. They are written here because this is where they are executed, and the night runs in a repository that has no copy of this toolbox's own decision records. Why the thresholds fall where they do, and what was rejected, is `docs/adr/0012-review-finding-routing.md` in the multi-model-workflow repository — read it when you want the reasoning, never in order to route.

**Step 0, before you classify at all.** Check the condition the finding's own body states against the current `HEAD`. It no longer holds: `<dispatch> route <n> <child> stale` and do nothing else. A quarter of them go this way — a later ticket of the same batch already did it, or the judge that raised it wrote that it should not be taken up.

1. **Does it fall inside another still-open ticket's `## Owns`?** → a ticket, `Blocked by` that open one. Not a question of size: the constraint is concurrency. Fixing it yourself on the base branch makes the next `advance` conflict when that ticket's branch merges.
2. **Is it a hole in the acceptance itself** — a `CHECK:` that is already green while the thing it names is broken or never reached? → a ticket, `senior-worker`, and it asks for a negative control. This class fails in the one way nobody notices (`docs/adr/0008-silence-is-never-a-pass.md`).
3. **How many files does the fix touch?** One → fix it yourself. Two or more **with a design coupling between them** — how you fix one decides how you fix the other, and neither can be written until both are settled → a ticket, `senior-worker`. Counting files is not counting effort; it is asking whether the change has a cross-file shape somebody should look at. **A name echoed through prose is not a coupling**: renaming a thing along with its restatements in a domain doc, a `SKILL.md` and a reference file is mechanical, `grep` proves you got them all, and it stays with you.
4. **Nothing matched** → fix it yourself. **The default is to fix it, not to open a ticket.**

The ones you fix: finish them in commits that follow these three rules, then `<dispatch> route <n> <child> fixed` for each, after its commit:

1. One commit per finding, or per group of findings with one cause; the commit message names them by number.
2. It touches only the files that finding names.
3. It runs the affected test suites, and the commit message quotes the line it saw (`ran 188 skipped 0`, not "the tests pass").

A fix that exceeds those three is a ticket after all. That is the way out, and it is
also what keeps step 4 from swallowing work that should have been reviewed: the whole
pass is auditable from `git log` in the morning, with no second agent.

The ones that become tickets: open as few tickets as possible. A ticket whose files sit in another live ticket's `## Owns` is `Blocked by` that live ticket. A finding that is a ticket on its own becomes one in place — rewrite its body into a ticket, label it for the agent queue, then `<dispatch> route <n> <child> became-ticket <child>`; findings folded into one new ticket each get `<dispatch> route <n> <child> became-ticket <that ticket>`.

Then:

```bash
<dispatch> advance <spec>
```

Loop: tickets that land wake you at step 3; when the frontier is empty again, this pass runs again. Continue until no open finding survives. Then go to step 5.

## 5. The night is over

Step 4 left no open finding. Then, still on this branch:

```bash
<dispatch> reverify <spec>
<dispatch> summary <spec>
```

`reverify` re-runs the criteria of every ticket whose events show it passed and landed against this `HEAD`; a ticket that passed and has not landed is not on this branch, so it is named on stderr and not run. Each run lands a `ticket.checked` event (run `reverify`, written by the main agent) on its ticket, green or red. Exit 0: all green. Exit 1: each red ticket is already reopened, labelled `needs-triage`, unassigned, and carries a `ticket.regressed` event naming the failing `AC<n>` — which takes back its pass and its landing — and that is the morning's triage queue; do not close those tickets. Exit 2: a ticket could not be re-run at all — it could not start, or it waited for a product slot and none came free — so nothing was judged on it, no ticket was touched, and the rest of the batch is skipped; stderr names the ticket and `verify-ticket.py` says what was missing. A run that could not start says nothing about the work, so it is never a red ticket.

`summary` posts the `spec.closed` event on the spec, a comment whose first line is `NIGHT SUMMARY <date>`, with the five lines `Closed:`, `Handed back to needs-triage:`, `Not dispatched, a blocker stayed open:`, `Sub-issues opened tonight:` (by number and title), and `Findings routed: <opened>/<fixed>/<became>/<skipped>/<unread>/<open>` — this pass's own account of where each one went. It counts the `finding` kind only — the kind and the route of each child are the `child.opened` and `child.closed` events on the ticket it came from, and a closed child no `child.closed` accounts for is `unread`; the `contract`, `deferred`, `decision` and `fault` children of the same batch are on the line above and not in this count, so the two totals differ. If `reverify` ran in this checkout, a `Reverify: <green>/<red>` line is appended.

It then closes the spec's watch: the night is over, and nothing is left to wake anyone about. The relay goes on for the other watches it carries — another night, a ticket outside one — and ends with the last of them.

Exit 0: that comment is posted and no relay watches the spec. Exit 1: the comment is posted and the spec's watch is closed, and the relay, which had no other watch, did not end — stderr names its pid; end that process. Exit 2: the comment could not be posted, and stderr says so; the relay still runs, so run `summary` again once the tracker answers.

Tell the user the night finished, and point them at that comment.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> suspend <spec>` is that decision carried out.

It ends every session still holding a ticket of the batch — its worker, and a reviewer or verifier whose result is not in — that its runner does not already show stopped, through that session's runner's `stop`. It then commits tracked edits and pushes each stopped ticket branch to origin before releasing anything. A ticket whose session survives the stop, whose edits cannot be committed, or whose push is rejected keeps its workspace, slot, claim and event hold; no force-push is attempted. Every other ticket still in the agent queue gets `spec.suspended`, its claim is given back with `ticket.released` (reason `suspended`), and the spec gets `spec.suspended`. Last, it closes the spec's watch: a suspended night wakes nobody.

Workspaces and branches stay, with the interrupted tickets' commits present on origin. The same batch is taken up again with `<dispatch> open <spec>` and then `<dispatch> advance <spec>` once whatever stopped the night is fixed: `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

The slots are given back for every ticket of the batch, handed back ones included, because `lease.py` counts claims rather than sessions when a run asks for a slot, and the next night's workers would otherwise wait on slots nothing is using. Each one is given back the way every slot is: the product's own `stop`, run from that worktree, then the release. `lease.py` refuses a slot something still listens on after that and names the port and the pid; `suspend` reports that and exits 1 rather than forcing it, because taking a slot off a live process is the same act as ending it.

Exit 0: every live session of the batch is stopped, every ticket still in the agent queue carries its `spec.suspended` event and is unclaimed, every slot the batch held is back, and no relay watches the spec. Exit 1: the night is stopped as far as this command could take it and what is left is on stderr, one line each — a slot with a listener on it, where `lease.py` names the port and the pid, so stop that process where it was started and run `python3 <lease.py> release <its worktree>`; a ticket that could not be commented on or unclaimed is the one `advance` will not take up again; a session that could not be stopped, or a ticket whose events could not be read, is named with the ticket left exactly as it was; a relay left with no watch that did not end is named by its pid. Exit 2: nothing was touched, and the reason is on stderr — not a git repository, a spec number that is not digits only, or a tracker that could not answer for the batch. After a 0 or a 1, `open` and then `advance` take the night up again.

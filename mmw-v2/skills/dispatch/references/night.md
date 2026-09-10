# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. How you learn a session is done is in `SKILL.md` next to this file, and `<dispatch>`, `<engine>`, `<lease.py>` and `<drive-target scripts>` are resolved in its `## Resolve `<dispatch>` once` section.

Between the steps below you wait on the batch. On Paseo a worker's closeout sends you a ticket message; on Orca and Herdr nothing is sent, so run `<dispatch> status <spec>` again every few minutes, and read each row as the step 3 table says.

## 1. The user says the night starts

Run, in this checkout, on the branch the night merges into:

```bash
<dispatch> check <spec>
```

**Exit 0:** the machine is ready — `install.sh --check` passed, the first host of each worker grade, reviewer and verifier is `available` in `paseo provider ls --json`, and every queued ticket has at most one worker-grade label that the live table has a row for. Then go to step 2. **Exit 2:** one or more of those failed, and stderr is one line per failure (`install.sh --check`, a provider whose `status` is not `available`, a queued ticket with two worker-grade labels or a label the live table has no row for). Fix what the lines name — run `install.sh`, relabel the ticket, or wait until the host is `available` — or tell the user if only they can, then run `check` again. Do not `advance` on 2.

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

**Exit 0:** stdout is one session id per ticket it started; each is already running, with its `worker.started` event on the ticket. A ticket whose start the runner refused is counted under `refused` with the runner's reason on stderr, and was not retried. Stderr carries the line `advance #<spec>: merged <m>, already in <s>, released <g>, started <k>, refused <r>`; each claim given back prints a line of its own naming the ticket and why, and when nothing could start while tickets are still in the agent queue, stderr names every one of them and the condition holding it. Then end your turn. **Exit 2:** nothing was touched; read stderr; if it is uncommitted tracked changes, commit or set them aside and run `advance` again; if it is the `.git` lock, held for `MERGE_TRIES` tries, run `advance` again. **Exit 3:** a merge is in conflict, still in the tree; everything before it is merged and committed, and nothing was archived, created or dispatched. Resolve it with the `resolving-merge-conflicts` skill — never `--abort` — run this repository's own checks, commit the merge, then `advance` again; the conflict report on stderr already names the two sides and the conflicted files.

What `advance` does inside that one command — merge, archive, give claims back, then dispatch — is the next section.

## `advance` merges, releases, then dispatches

`<dispatch> advance <spec>` merges the branch of every ticket that closed with a `ticket.passed` event and has not landed into the branch you are on at that moment, records `ticket.landed` on each, archives each merged ticket's workspace, gives back the claims whose workers are gone, then dispatches every ticket on the frontier.

An open ticket's branch is never merged, whatever its criteria say: closed with `ticket.passed` is the whole rule. A contract defect a worker cannot answer from its own code comes back as a red criterion and a `HANDOFF REQUIRED` ticket, the way any other defect does. The branch you open the night on is the base branch, so stay on it all night: every `advance` merges into whatever `HEAD` is on, and `git config branch.issue-<n>.mmw-base-branch` is a record for readers, not something `advance` consults.

The four are one command because the order is the reason. A worktree is cut from `HEAD` at the moment it is opened, so a branch merged after the next ticket is dispatched is a branch that ticket cannot see; the frontier is read after the claims come off, so a ticket freed by this run starts in this run rather than the next one; and `advance` archives a ticket's workspace only after that ticket's branch is already in `HEAD`, releasing its lease first.

It merges a branch when four things hold at once — the ticket is `CLOSED`, its events carry a `ticket.passed` that no `ticket.landed` has followed, the ticket branch `issue-<n>` exists, and that branch is not already an ancestor of `HEAD`. A branch already in `HEAD` is recorded as landed without a merge, which is what makes the command safe to run at any time; an empty frontier starts nothing. A ticket handed back to `needs-triage` stays open and carries `ticket.returned`, so the second condition excludes unfinished work without a rule of its own.

Branches are merged in the order their tickets **closed**, not in ticket order. That is already the order their blockers imposed: `verify-ticket.py --preflight` refuses a ticket whose blocker is open, so none of them can have closed before the ones it waited on. Each merge keeps a commit of its own, so a ticket can be found and undone in the morning, and so the other side of a conflict can be read back to the tickets it came from.

A ticket is claimed by being assigned to the account this pipeline is signed in as — `verify-ticket.py --preflight` does it — and the frontier takes only unassigned tickets, which is what keeps a second worker off a ticket somebody is already working. Six paths take a claim off: the closeout, the hand back to triage, `land`, `advance`'s **give a claim back** (the `RELEASE` line) for a claim whose worker is gone, `suspend`, which gives back every claim of the batch, and `retract`, which gives the claim back when a ticket's session is gone. A session that ends any other way — a crash, a machine restart, a workspace archived from outside this pipeline — leaves the claim standing, and from then on the ticket is off every frontier for good, with an empty frontier as the only sign of it.

So `advance` gives a claim back when four things hold at once: the ticket is open, it is in the agent queue, this pipeline's own account is on it, and an event on it has ended every hold on it. A ticket is held from its `ticket.claimed` or any `*.started`; `ticket.landed`, `ticket.returned`, `ticket.released` and `spec.suspended` end every hold, and `worker.retracted`, `worker.lost` and `worker.replaced` end the one session they name by its runner and id. `ticket.passed` ends none, since the close after it can fail and leave the worker retrying, and no label ends one. A claim no event ever showed held — assigned by hand, say — is kept: nothing on the ticket shows its worker gone. All of this is read off the ticket, never off a runner: a runner answers for one machine, and a worker started on Orca, on Herdr or on a second machine holds its ticket exactly as one on Paseo does. The write is `gh issue edit <n> --remove-assignee @me`, followed by a `ticket.released` event (reason `worker-lost`), so a ticket a person took for themselves is untouched and stays off the frontier, which is the right answer — somebody has it. Each release prints one line naming the ticket and saying why.

The other side of that rule: a worker whose session died without anything ending its hold keeps its ticket held, and the ticket stays off the frontier until something does. `<dispatch> retract <n>` is that something — it asks the runner, and only once the session is shown gone does it undo the start and write `worker.retracted`. A ticket whose events cannot be read is held the same way, and says so.

A standing workspace is not a run. A worker holds its ticket only while its events show it live, whatever directory is still on disk; the workspace stays for `start` to reuse, and the next worker picks the branch up where the last one left it.

A blocker lets go of the ticket it blocks when it has **landed**, not when it closed: the blocked ticket is cut from the base branch, and a blocker whose branch has not been merged has left nothing there to build on. A blocker that closed without a pass — closed by a person, or as not planned — lets go on closing, since nothing of it will ever land; one that this same `advance` merges before it dispatches lets go in that `advance`.

When nothing can start and the batch still holds open tickets in the agent queue, `advance` names each of those tickets on stderr with the condition holding it — its events cannot be read, blocked by a ticket still open or passed and not landed, claimed by somebody, or already held by a live worker, named with its session and runner. An empty frontier and a finished batch print the same nothing otherwise, and the difference between them is not visible from outside the frontier's conditions. The exit code is unchanged: this is an explanation, not a failure.

`advance` starts every ticket on the frontier: how many workers write code at once is the frontier's answer alone. A product that cannot move its ports says so in `.mmw/target.json` as `"instance": {"max": <n>}`, and that limit bites later, at the first run of a worker's criteria that runs the product — the moment its worktree claims a slot. A worker that finds `max` slots already held by this repository — by its ticket worktrees or by the main checkout running `reverify` — waits there, its ticket carrying a `worker.queued` event, until one comes free. A slot is held from that first run until the ticket's work ends, and given back at that moment: `advance` gives it back when it archives a landed ticket's workspace or releases a lost worker's claim, the closeout when it hands the ticket back, `suspend` and `retract` with the claim. The main checkout's `reverify` gives its slot back as each run ends.

## 3. Each time something wakes you

One thing wakes you, and it ends here: a **ticket message** `#<n> ticket.passed`, `#<n> ticket.returned`, `#<n> ticket.refused` or `#<n> child.opened kind=fault`, sent by `verify-ticket.py` the moment that ticket came to rest. No finish notification reaches you: the only agent you start is the worker, and it is started with `notifyOnFinish: false` so that its middle states — asleep on a verifier, asleep on a reviewer — do not reach you as news.

1. Were you running a command when it arrived? A ticket message interrupts, and the command reports being interrupted rather than finishing. Run that command again before anything else — `advance` in particular is written to be run again at any time, and picks up whatever the interrupted run left behind.
2. Run `<dispatch> status <spec>`. It reads the tracker and nothing else: each row is the fold of that ticket's events, and no runner is asked. Exit 0: stdout is the table (`ticket`, `runner`, `session`, `worker`, `since`, `phase`, `ac`, `note`) — the runner and session of the ticket's newest worker, `live` or the event that closed it, when it was started, and the newest event's name. Exit 2: the tracker could not be asked, or answered for fewer of the spec's tickets than it counts — one `dispatch: …` line on stderr and no table; run it again once it answers. The `note` column is `ready`, `waiting on #<m>` (with `(passed, not landed)` when the blocker closed and has not landed), `<k> live workers: …` (more than one start on the ticket is still open), `events unreadable: …` (a comment carries an event block nothing can read, so the ticket is held until a person fixes that comment), `claimed, no session started yet` (a `ticket.claimed` holds it and no start is recorded), `waiting for a product slot since <time> (<reason>, <k> of <max> held)` (a run of its criteria is queued for a slot — the worker is alive and not done; nothing to do but let the ticket that holds a slot land), the newest event's first line, or empty while a worker holds it. The `ac` column is `<met>/<total>` from the newest run of its criteria, the worker's own or a reverify.
3. Take every row the table matches, not only the ticket you were woken about. What woke you says one thing happened; the table says what is true, and two tickets landing seconds apart wake you once.

| What you see | What you do |
| --- | --- |
| A ticket just passed (`ticket.passed`), or the frontier has `ready` rows that nothing holds | `<dispatch> advance <spec>` |
| The worker is live and the work should continue | `<dispatch> resume <n> "<what you settled, then: continue>"`. Exit 0: the text was sent. Exit 3: it is in a turn and did not take the message — wait and run the same command again, do not go looking for another way to reach it; Paseo dispatches the message before it confirms the turn started, so a 3 does not prove nothing arrived, and the retry should be worded so that a worker which got both reads them as one instruction. Exit 2: the worker session the ticket's `worker.started` event names is not there any more — read `status`, do not send again |
| `resume` has exited 3 several times and you cannot tell whether it is working or stuck | Ask `get_agent_status` for that agent. An `activeTurn` naming a turn means it is working. An `activeTurn` of null while the send still fails means the session is stuck: a rejected send left `lastError` set, the send path reads that field, and it will take no message again. `<dispatch> start <n> worker` replaces it: it stops that session through its runner, writes `worker.replaced` naming it, and starts a new worker in the same workspace — the branch, its commits and the worktree's product slot are all there, and what the worker was told in that session is not. Exit 2 with the stuck session still live means it would not stop; end it on its runner, then start again |
| The worker has stopped and the ticket has a new `child.opened` event of kind `fault` | Read that child — its number is the event's `child`, listed under `children` by `python3 <events.py> fold <n>`. Fix the cause it names. Then `<dispatch> resume <n> "… continue"` |
| `status` shows the ticket still `OPEN`, and `paseo ls --label mmw.ticket=<n>` shows a live child labelled `mmw.kind=reviewer` or `mmw.kind=verifier` | Not a stop: the worker is asleep on that child and wakes when it finishes. Do nothing |
| The message reads `#<n> ticket.returned` | That ticket is finished for tonight: the closeout already swapped its label for `needs-triage`, gave its claim back and left it open, and it is the morning's triage rather than yours. Its workspace stays for the next `start`, so do not archive it. What is yours is the rest of the batch, which that ticket may have been blocking: `<dispatch> advance <spec>`. |
| The message reads `#<n> ticket.refused` | The ticket refused to be claimed: its `ticket.refused` event names the `reason`, and its comment says it in a sentence. Fix what it names, then `<dispatch> advance <spec>` |
| `status` shows the worker `live`, and its runner no longer has that session (on Paseo, `paseo logs <id>` shows only the prompt with no output — an agent created before the daemon restarted answers this way) | `<dispatch> retract <n>`, then `<dispatch> advance <spec>`: the retraction closes that start on the ticket's events and gives the claim back, so the ticket is on the frontier again and `start` reuses its standing workspace and branch |
| The ticket has no closing comment, the worker is not running, and `paseo logs <id>` shows what stopped it | Fix that — a file it could not find, a command it needs, a baseline it read wrong — then `resume` with that plus `continue`. A question only a person can settle: `resume` telling the worker to open it with `verify-ticket.py <n> --sub-issue decision <file>`, take the default meanwhile, and record it under `Decisions I made on my own`. Change no label |
| The worker is live and nothing is wrong | Do not `resume`. End your turn |
| A ticket's session is gone and its worktree, slot or claim is still held | `<dispatch> retract <n>`: it runs the product's `stop` in that worktree, archives the workspace, gives the slot back, gives the claim back if this pipeline holds it, and writes `worker.retracted`; the branch stays, so the next `start` reuses it. Exit 0: stderr reads `retract #<n>: archived <a>, slot given back <s>, claim given back <c>` — `slot given back` is 1 only when the lease was actually released and `archived` is 1 only when the workspace actually went, so a product still listening keeps both at 0 and stderr says where to stop it. Exit 2: nothing was touched — a live agent is still on the ticket, or its runner cannot tell, or the ticket's events could not be read, or a slot is held and no `lease.py` could be found, or this is not a git repository, or the number is not digits |
| A ticket should be worked at the other worker grade | Swap its `junior-worker` / `senior-worker` label on the tracker; the next `start` reads it |
| `status` shows an empty frontier and no live agent of this spec | Go to step 4 |

Then end your turn. Most tickets that land are followed by another `advance`.

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

Exit 0: that comment is posted. Exit 2: it could not be posted, and stderr says so.

Tell the user the night finished, and point them at that comment.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> suspend <spec>` is that decision carried out.

It ends every worker the batch's events name that its runner does not already show stopped, through that session's runner's `stop`, which interrupts a worker in the middle of a turn — the whole reason to suspend a night; the workspace and the branch stay. A worker that survives the stop anyway keeps its slot and its claim, and its ticket gets no event: a live worker starts the product again, and the `stop` in between tears up the record of what it started, leaving processes that `stop` can no longer reach; and a `spec.suspended` on its ticket would close its start on the ticket's events while it still runs, so the next `advance` would start a second worker beside it. Every other ticket still in the agent queue gets a `spec.suspended` event whose first line is `NIGHT SUSPENDED #<spec>`, with the time and whether a worker was interrupted on it, and its claim is given back with a `ticket.released` event (reason `suspended`); the spec gets a `spec.suspended` of its own. Without the event the morning reader finds a row of tickets with no verdict and no way to tell them from work in progress; without the claim given back, `advance` never takes the ticket up again. A ticket a worker handed back to triage during the night already carries its own verdict, so it is left alone.

Workspaces and branches stay, and the same batch is taken up again with `<dispatch> advance <spec>` once whatever stopped the night is fixed: each ticket is unclaimed and held by no agent, so it is on the frontier, and `start` reuses its standing workspace. That is the reason to suspend a night rather than let it run: the fix is carried on with the same worktrees, and a batch dispatched again from scratch would throw the night's work away along with the night.

The slots are given back for every ticket of the batch, handed back ones included, because `lease.py` counts claims rather than sessions when a run asks for a slot, and the next night's workers would otherwise wait on slots nothing is using. Each one is given back the way every slot is: the product's own `stop`, run from that worktree, then the release. `lease.py` refuses a slot something still listens on after that and names the port and the pid; `suspend` reports that and exits 1 rather than forcing it, because taking a slot off a live process is the same act as ending it.

Exit 0: every live worker of the batch is stopped, every ticket still in the agent queue carries its `spec.suspended` event and is unclaimed, and every slot the batch held is back. Exit 1: the night is stopped as far as this command could take it and what is left is on stderr, one line each — a slot with a listener on it, where `lease.py` names the port and the pid, so stop that process where it was started and run `python3 <lease.py> release <its worktree>`; a ticket that could not be commented on or unclaimed is the one `advance` will not take up again; a worker that could not be stopped, or a ticket whose events could not be read, is named with the ticket left exactly as it was. Exit 2: nothing was touched, and the reason is on stderr — not a git repository, a spec number that is not digits only, or a tracker that could not answer for the batch. After a 0 or a 1, `advance` can run again.

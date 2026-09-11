# Running a night

You are the main agent. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

This file is the order of the night. How a wake reaches you and what you do on one is in `SKILL.md` next to this file, and `<dispatch>`, `<engine>`, `<lease.py>` and `<drive-target scripts>` are resolved in its `## Resolve `<dispatch>` once` section.

Between the steps below you end your turn. The relay you start in step 1 wakes you when a ticket of the batch comes to rest (step 3), and the watchdog tells you when the board has gone silent where it should not (`SKILL.md`, next to this file, says what it is); nothing else does, and no agent polls another.

## 1. The user says the night starts

```bash
<dispatch> check <spec>
```

**Exit 0:** the machine is ready; open the night. **Exit 2:** fix every condition stderr names and run `check` again. Do not open the night on 2; change an invalid agent row as [editing-models.md](editing-models.md) says.

Then, from this session — the one the night's wakes must reach:

```bash
<dispatch> open <spec>
```

**Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>`; end with an open watch whose main agent is this session. **Exit 2:** fix stderr's named condition and run `open` again. `advance` refuses a night that is not open. The branch inference, pushes and watch mechanics are in [how-it-works.md](how-it-works.md) under **Opening a night**.

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

After `open` records `into`, `advance` may run from any checkout in this repository. It does not move that checkout or any local base branch.

```bash
<dispatch> advance <spec>
```

**Exit 0:** stdout is one session id per ticket it started. Stderr ends with `advance #<spec>: merged <m>, already in <s>, bounced <b>, released <g>, started <k>, refused <r>`. A bounced ticket was reopened for triage and its workspace remains; it is not tried or dispatched again that night. End your turn after exit 0. **Exit 4:** landing and release finished, but at least one runner refused a start; each refusal is named and is not retried. Fix what each refusal names, then run `advance` again. End your turn only while another worker of the night remains live; if none does, tell the user which tickets were refused and why. **Exit 2:** if the night is not open, run `open <spec>` and then `advance <spec>` again. Otherwise stderr names unreadable tracker state, merge lock, fetch, merge or push failure; fix the named condition and retry. A merge conflict and red repository checks are not exit codes: that ticket gets `ticket.bounced`, the merge worktree is reset, and the command continues.

The merge, checks, archive, claim and frontier sequence is in [how-it-works.md](how-it-works.md) under **How `advance` processes a batch**.

## 3. Each time something wakes you

The relay sends a wake as `#<n> <event>` or `relay.recovered since <time>`; the watchdog sends one line whose findings each begin `watchdog:`. [how-it-works.md](how-it-works.md) under **Results, watches and wakes** and **The watchdog and turn guard** defines their recipients and mechanics.

On `MMW turn guard:`, run the named `watchdog.py arm` command. Exit 0 means it runs; on exit 1, fix stderr's reason or open a `fault` child on any held ticket with that command and output, then end your turn.

Handle each wake in this order, one wake at a time — two tickets landing seconds apart are two wakes, and you get the second after you end your turn:

1. Run again any command the wake interrupted.
2. Run `<dispatch> status <spec>`. Exit 0 prints the table; exit 2 means the tracker did not return the whole batch, so run it again when the tracker answers. The table's mechanics are in [how-it-works.md](how-it-works.md) under **Interpreting a night**.
3. Take every row the table matches, not only the ticket named by the wake.
4. Run `<dispatch> advance <spec>` once. Its exit codes are under `## 2. First advance`.
5. Run `<dispatch> ack <n> <event>` for the named wake, or `<dispatch> ack relay.recovered`. Its exit codes are in [inside-a-ticket.md](inside-a-ticket.md). Ack last, then end your turn.

| What you see | What you do |
| --- | --- |
| `ticket.passed`, or a `ready` frontier row | Step 4's `advance` handles it |
| A live worker should continue | `<dispatch> resume <n> "<what you settled, then: continue>"`; act on exit 0, 4, 3 or 2 as [how-it-works.md](how-it-works.md) under **Interpreting a night** says |
| Repeated `resume` exit 3 with no new event | `<dispatch> start <n> worker`; exit 2 means nothing was replaced or started |
| `child.opened` of kind `fault` | Read `python3 <events.py> fold <n>`, fix the child, then `<dispatch> resume <n> "… continue"` |
| `child.opened` of kind `decision` | Nothing tonight; the worker took the default |
| A live worker at `reviewer.started` or `verifier.started` | Nothing; its result wakes the worker |
| `ticket.returned` | Leave its workspace for triage; step 4 continues the batch |
| The `advance` summary has `bounced` | Leave its workspace for triage; do not retry it tonight |
| `ticket.refused` | Fix the event's `reason`; step 4 starts it if the frontier permits |
| `worker.lost` | Step 4 gives back the claim and starts another worker in the standing workspace |
| `relay.recovered since <time>` | Nothing; later wakes carry the recovered events |
| `watchdog: relay down (…)` | `<dispatch> open <spec>`; use `open-ticket <n>` for one ticket. Nothing to ack |
| `watchdog: #<n> liveness unknown: …` | `<dispatch> resume <n> "Say in one line where you are, then continue"`; exit 0 confirms it, exit 2 means `<dispatch> retract <n>`, otherwise leave it for the user |
| `watchdog: #<n> is held with no session to ask, …` | Read `status`; when nothing works the ticket, `<dispatch> retract <n>`. Nothing to ack |
| `watchdog: cannot read the board since <time>: …` | Run the named `gh issue view <n>`; wait for tracker or network recovery, or leave credential repair to the user. Nothing to ack |
| `watchdog: #<n> events unreadable` | Leave the named comment for the user. Nothing to ack |
| A live worker whose runner has no session | `<dispatch> retract <n>`; step 4 starts its replacement |
| `watchdog: #<n> silent since <time> with nothing to wait on: …` | Resume it with the continue/fault/decision instruction in [how-it-works.md](how-it-works.md) under **Interpreting a night**. Nothing to ack |
| A live worker with no fault | Do not `resume` |
| A gone session still has a worktree, slot or claim | `<dispatch> retract <n>`; exit 0 reports what it released, exit 2 names what remains |
| The ticket needs the other worker grade | Swap its `junior-worker` / `senior-worker` label; the next `start` reads it |
| Empty frontier and no live agent | Finish the wake, then go to `## 4. The closing pass` |

## 4. The closing pass

The frontier is empty and `status` shows no live agent. If this spec's tickets still hold open findings — the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `python3 <events.py> fold <n>`, open until a `child.closed` on the ticket gives their `resolution` — route **exactly those**. If there are none, go to step 5.

Every route is carried out by one command, run once per finding, and it is the only way a finding leaves this pass:

```bash
<dispatch> route <n> <child> fixed|stale|became-ticket [<new ticket>]
```

`<n>` is the ticket the finding came from — the one whose `fold` lists it under `children` — and the spec is the one that ticket's `child.opened` for it names; neither is read off the tree, which a `became-ticket` route itself changes. It closes the finding — `fixed` as completed, `stale` as not planned — or, for `became-ticket <new ticket>`, makes it that ticket, and writes the `child.closed` event on `<n>`; that event is the one record of where the finding went, and the night summary counts by it. When `<new ticket>` is the finding itself, the finding stays open, its `mmw:child` label becomes `mmw:ticket`, and its parent moves from the ticket to the spec, because the scripts find a ticket's spec through its direct parent alone. When `<new ticket>` is another issue, the finding is closed as its duplicate and that issue gets the same label and the same parent. Exit 0: routed and recorded, or routed that way already. Exit 1: the tracker took part of it and not the rest; stderr says which, and the same command run again finishes it without doing any step twice. Exit 2: nothing was done — `<n>` carries no `child.opened` for the finding, the finding was routed another way, its `child.opened` names no spec for a `became-ticket`, the tracker could not be asked, or the arguments are wrong.

Judge each one by the four steps below, **in order, first match wins**, after the check that comes before them. They are written here because this is where they are executed, and the night runs in a repository that has no copy of this toolbox's own decision records. Why the thresholds fall where they do, and what was rejected, is `docs/adr/0012-review-finding-routing.md` in the multi-model-workflow repository — read it when you want the reasoning, never in order to route.

**Step 0, before you classify at all.** Check the condition the finding's own body states against the current `HEAD`. It no longer holds: `<dispatch> route <n> <child> stale` and do nothing else. A quarter of them go this way — a later ticket of the same batch already did it, or the judge that raised it wrote that it should not be taken up.

1. **Does it fall inside another still-open ticket's `## Owns`?** → a ticket, `Blocked by` that open one. Not a question of size: the constraint is concurrency. Fixing it yourself in the origin-tracking checkout makes the next `advance` conflict when that ticket's branch merges.
2. **Is it a hole in the acceptance itself** — a `CHECK:` that is already green while the thing it names is broken or never reached? → a ticket, `senior-worker`, and it asks for a negative control. This class fails in the one way nobody notices (`docs/adr/0008-silence-is-never-a-pass.md`).
3. **How many files does the fix touch?** One → fix it yourself. Two or more **with a design coupling between them** — how you fix one decides how you fix the other, and neither can be written until both are settled → a ticket, `senior-worker`. Counting files is not counting effort; it is asking whether the change has a cross-file shape somebody should look at. **A name echoed through prose is not a coupling**: renaming a thing along with its restatements in a domain doc, a `SKILL.md` and a reference file is mechanical, `grep` proves you got them all, and it stays with you.
4. **Nothing matched** → fix it yourself. **The default is to fix it, not to open a ticket.**

The ones you fix: use a checkout that tracks `origin/<into>`. Fetch before each fix, commit it there, run the affected tests, and fast-forward push it to `origin/<into>`. If that push is rejected, fetch, merge the new `origin/<into>` into the commit, run the affected tests again, and retry the fast-forward push. Then `<dispatch> route <n> <child> fixed` for each, after its commit and push. The commits follow these three rules:

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

Step 4 left no open finding. From any checkout in this repository:

```bash
<dispatch> reverify <spec>
<dispatch> summary <spec>
```

`reverify` exit 0 means every landed ticket is green. Exit 1 means each red ticket is already reopened in `needs-triage`, unassigned and carrying `ticket.regressed`; do not close it. Exit 2 means one ticket established no result, so no ticket was changed and the remainder was skipped; fix stderr's named condition and run `reverify` again.

`summary` exit 0 means `NIGHT SUMMARY` was posted and the spec watch is closed. Exit 1 means the comment was posted and the watch closed, but an otherwise unused relay remains; end the pid stderr names. Exit 2 means no comment was posted and the watch remains; fix stderr's named condition and run `summary` again. Its event and counting mechanics are in [how-it-works.md](how-it-works.md) under **Reverify and summary**.

Tell the user the night finished, point them at that comment, and say that after they accept the result the main agent will run `finish` to close the night.

## 6. Close the night after acceptance

Only after the user has accepted the result, the main agent runs:

```bash
<dispatch> finish <spec>
```

`finish` requires `spec.closed`, the recorded project branch, no other open night with the same base branch, and no open ticket under any spec that used that base branch. It merges `origin/<base branch>` into `origin/<project branch>` in the project branch's detached merge worktree, runs the repository checks with `MMW_BASE_REF=origin/<project branch>`, and fast-forward pushes the checked result. A conflict or red check pushes and deletes nothing. After the push it writes `spec.merged`, then removes the contained base branch from origin and locally, its clean worktrees, the base branch's merge worktree and its lock. A base branch already contained in the project branch needs no merge and goes directly to those cleanup checks. Dirty worktrees stay and stderr gives the exact cleanup command. Running `finish` again after `spec.merged` only completes cleanup; it does not create another merge commit.

Exit 0 means the merge is recorded and every safe cleanup was attempted. Exit 1 means the merge conflicted or repository checks failed; nothing was pushed or deleted. Exit 2 means a precondition, fetch, push or event write failed. Preconditions fail before any change; a push rejection deletes nothing, while an event-write failure can leave the checked merge on origin and the next `finish` records it before cleanup. Do not merge the project branch into the repository default branch here; that remains the user's release decision.

## Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `<dispatch> suspend <spec>` is that decision carried out.

It ends every session still holding a ticket of the batch — its worker, and a reviewer or verifier whose result is not in — that its runner does not already show stopped, through that session's runner's `stop`. It then commits tracked edits and pushes each stopped ticket branch to origin before releasing anything. A ticket whose session survives the stop, whose edits cannot be committed, or whose push is rejected keeps its workspace, slot, claim and event hold; no force-push is attempted. Every other ticket still in the agent queue gets `spec.suspended`, its claim is given back with `ticket.released` (reason `suspended`), and the spec gets `spec.suspended`. Last, it closes the spec's watch: a suspended night wakes nobody.

Workspaces and branches stay, with the interrupted tickets' commits present on origin. The same batch is taken up again with `<dispatch> open <spec>` and then `<dispatch> advance <spec>` once whatever stopped the night is fixed: `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

The slots are given back for every ticket of the batch, handed back ones included, because `lease.py` counts claims rather than sessions when a run asks for a slot, and the next night's workers would otherwise wait on slots nothing is using. Each one is given back the way every slot is: the product's own `stop`, run from that worktree, then the release. `lease.py` refuses a slot something still listens on after that and names the port and the pid; `suspend` reports that and exits 1 rather than forcing it, because taking a slot off a live process is the same act as ending it.

Exit 0: every live session of the batch is stopped, every ticket still in the agent queue carries its `spec.suspended` event and is unclaimed, every slot the batch held is back, and no relay watches the spec. Exit 1: the night is stopped as far as this command could take it and what is left is on stderr, one line each — a slot with a listener on it, where `lease.py` names the port and the pid, so stop that process where it was started and run `python3 <lease.py> release <its worktree>`; a ticket that could not be commented on or unclaimed is the one `advance` will not take up again; a session that could not be stopped, or a ticket whose events could not be read, is named with the ticket left exactly as it was; a relay left with no watch that did not end is named by its pid. Exit 2: nothing was touched, and the reason is on stderr — not a git repository, a spec number that is not digits only, or a tracker that could not answer for the batch. After a 0 or a 1, `open` and then `advance` take the night up again.

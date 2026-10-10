### Run a night

**You are the orchestrator. Every decision of the night is yours, and each leaves its reason where the morning reader looks.**

Every `dispatch.sh` command below is the **dispatch** skill's `scripts/dispatch.sh`, and `verify-ticket.py` and `events.py` are the **verify-ticket** skill's.

You are the orchestrator. A spec's tickets will be worked while you are not watching each one. The scripts merge, archive, create worktrees, and start the sessions. Every decision is yours: whether a worker continues, whether a failure is yours to fix, whether a question becomes a sub-issue, whether to `advance` again.

The night is read in the morning by the user, cold, from its pull request and the tracker, with none of this session's context. So each decision you make leaves its reason where that reader will look: on the child, the ticket or the spec, in a comment that stands on its own. A reason that lives only in this session is lost when it ends.

The night's output is a batch the user can accept in the morning, not a count of closed tickets. A ticket handed back with its reason on it is a good result; a criterion loosened, or a worker resumed again and again with `continue`, to make one close is a defect that lands under a green mark.

This file is the order of the night. How a wake reaches you and what you do on one is the dispatch skill's `## On waking`.

Between the steps below you end your turn. The relay you start in step 1 wakes you when a ticket of the batch gets an event that needs the orchestrator (step 3), and the watchdog tells you when the tracker has gone silent where it should not; nothing else does, and no agent polls another.

Find where you are by the first row whose fact holds; the record says where you are, not this session's memory (**principle-progress-is-what-the-record-says**):

| The fact | Go to |
| --- | --- |
| The user has said the night starts, and the spec carries no `spec.opened` | [1. The user says the night starts](#1-the-user-says-the-night-starts), then 1b and 2 |
| The spec's newest night event is `spec.suspended`, or you are deciding to stop the night because the fault is in the pipeline | [Suspending the night](#suspending-the-night) |
| A wake arrived: `#<n> <event>`, `brief <batch> done`, a line of `watchdog:` alerts, or `MMW turn guard:` | [3. Each time something wakes you](#3-each-time-something-wakes-you) |
| `dispatch.sh status <spec>` shows an empty frontier and no live agent, and the spec carries no `spec.closed` | [4. The closing pass](#4-the-closing-pass) |
| The spec carries `spec.closed`, and no open pull request runs from the night's branch to the project branch | [6. Open the pull request](#6-open-the-pull-request) |
| The pull request is open, and the user has accepted it | [7. Merge the accepted night](#7-merge-the-accepted-night) |
| The spec carries `spec.merged` | Nothing: the night is merged; tell the user so |

#### 1. The user says the night starts

Run `check` and `open` from a checkout on the night's base branch: the current checkout names it.

```bash
dispatch.sh check <spec>
```

**Exit 0:** the machine is ready; open the night. **Exit 2:** fix every condition stderr names and run `check` again; an invalid agent row is reported to the user.

Then, from this session — the one the night's wakes must reach:

```bash
dispatch.sh open <spec>
```

**Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>`, and this session is the night's orchestrator. **Exit 2:** fix stderr's named condition and run `open` again.

#### 1b. Before the batch: what the batch cannot be run on

Run this once, before the first `advance`, on every spec, with the `verify-ticket` skill's `verify-ticket.py`:

```bash
verify-ticket.py <spec> --lint
```

Read its exit as the **verify-ticket** skill's `references/linting.md` says, and fix each `ERROR` on its ticket.

#### 2. First `advance`

After `open` records `into`, `advance` may run from any checkout in this repository. It does not move that checkout or any local base branch.

```bash
dispatch.sh advance <spec>
```

**Exit 0:** end your turn. **Exit 4:** a runner refused a start; stderr names each refusal, and none is retried. Fix what each names and run `advance` again; end your turn only while another worker of the night remains live, and if none does, tell the user which tickets were refused and why. **Exit 2:** fix what stderr names and run `advance` again (a night that is not open: `open <spec>` first); the rest of the batch was landed and started.

#### 3. Each time something wakes you

Handle each wake in this order, one wake at a time — two tickets landing seconds apart are two wakes, and you get the second after you end your turn:

1. Do steps 1-3 of the dispatch skill's `## On waking`, which end with the ack.
2. Run `dispatch.sh status <spec>`. Exit 0 prints the table; exit 2 means the tracker did not return the whole batch, so run it again when the tracker answers.
3. Take every row the table matches, not only the ticket named by the wake.
4. Run `dispatch.sh advance <spec>` once. Its exit codes are under [**2. First `advance`**](#2-first-advance).
5. When the `advance` you just ran left the frontier empty and no agent live (read `status` again), go to [4. The closing pass](#4-the-closing-pass); otherwise end your turn.

| What you see | What you do |
| --- | --- |
| `ticket.passed`, or a `ready` frontier row | Step 4's `advance` handles it |
| A live worker should continue | `dispatch.sh resume <n> "<what you settled, then: continue>"`; act on exit 0, 4, 3 or 2 as [Exit codes of `resume`](#exit-codes-of-resume) below says |
| `child.opened` of kind `fault` | Read `events.py fold <n>`. A `fault` in this repository's environment (a credential, a service, `.mmw/target.json`) you fix, then `dispatch.sh resume <n> "… continue"`. A `fault` in the pipeline's own scripts you do not patch while they run the night: tell the user what failed, and suspend when the rest of the batch would hit it too |
| `child.opened` of kind `contract` | Read the child and the authority it cites. Apply the authority order below; then either correct the source the child names and every unlanded derived ticket, close the child and resume its worker, or move the affected not-yet-started tickets to `needs-triage` and leave the child open |
| `child.opened` of kind `decision` | Nothing; the worker took the default |
| `ticket.returned` | Leave its workspace for triage; step 4 continues the batch |
| The `advance` summary has `bounced` | After the second bounce the ticket stays in `needs-triage` |
| `ticket.refused` | Fix the event's `reason`; step 4 starts it if the frontier permits |
| `worker.lost` | Step 4 gives back the claim and starts another worker in the standing workspace |
| A worker whose session is gone while its worktree or claim still stand (`advance` says "if the worker … is gone, retract it") | `dispatch.sh retract <n>`; a `0` on its summary line is something it could not release, and the line above says why. Step 4 starts the replacement |
| `watchdog: #<n> silent since …` | When `events.py fold <n>` lists an open `contract` child, the worker is waiting on you; settle that child first |
| Any other live worker | Nothing; its result wakes you or its worker |
| The ticket needs the other worker grade | Give it exactly one of the `junior-worker` / `senior-worker` labels; the next `start` reads it |

While a worker holds a ticket, its code is the worker's: you change what the worker works from (the spec, the ticket body, a criterion, a baseline, under the authority order below) and tell it through `resume`, never its worktree or branch. Your own fixes wait for the closing pass, on `origin/<into>`.

For a `contract` child, use this authority order exactly: **decision tickets and ADRs, then the spec, then the design package, then domain documents, then the ticket body**. Fix it yourself when you can cite a written authority at that order: a higher authority, a more specific file within the same authority, a repository rule, or the artifact a baseline copied. Edit the tracker-owned spec, acceptance criterion, or ticket body directly; when a spec changes, leave the change-and-reason comment that the Revising a spec playbook (`playbooks/revising-a-spec.md`) requires. Edit a repository-owned baseline through the normal `origin/<into>` commit and push procedure in [4. The closing pass](#4-the-closing-pass). Correct every not-yet-landed ticket derived from the same bad statement. Comment on the child with the authority used, every published item corrected, the source commit, and the tickets checked; run `dispatch.sh route <n> <child> fixed`, then resume the active worker with the exact correction, the commit it should integrate from, and `continue`.

When no authority settles the correction, or the proposed correction would overturn the user's decision or expand the spec, leave the choice to the user. Find every not-yet-started ticket derived from the same Parent decision, move each from `ready-for-agent` to `needs-triage`, and comment on the child with the unresolved options, your recommendation, and the ticket numbers moved. Leave the child open for the user. A ticket already being worked stays held at the contract question; do not rewrite its delivery while the authority is unresolved.

##### Exit codes of `resume`

Exit 0: the worker took the message. Exit 4: the message is in its session, though the runner shows no turn starting; do not send it again. Exit 3: the worker is most likely in a turn and took nothing; end your turn and run `resume` again on the next wake or watchdog alert, and when that exits 3 again with no ticket event in between, `start <n> worker` replaces the worker. Exit 2: nothing was sent; do what stderr names.

When you run `resume` again after exit 3, word it so a worker that receives both messages reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`.

#### 4. The closing pass

The frontier is empty and `status` shows no live agent. If this spec's tickets still hold open findings — the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `events.py fold <n>`, open until a `child.closed` on the ticket gives their `resolution` — route **exactly those**. If there are none, go to step 5.

List the open findings with `dispatch.sh findings <spec>` and route exactly those. A finding wakes nobody, so the ones you were woken about are no measure of what exists.

Every route is carried out by one command, run once per finding, and it is the only way a finding leaves this pass:

```bash
dispatch.sh route <n> <child> fixed
dispatch.sh route <n> <child> stale <invalid|fixed-elsewhere>
dispatch.sh route <n> <child> became-ticket <new ticket>
```

`<n>` is the ticket the finding came from, the one whose `fold` lists it under `children`. `became-ticket <child>` makes the finding itself the ticket; `became-ticket <other issue>` closes the finding as that issue's duplicate. `route` writes the `child.closed` event that the night summary counts. Exit 1: run the same command again; it repeats no step. Exit 2: nothing was done, and stderr says why.

Judge each one by the four steps below, **in order, first match wins**, after the check that comes before them.

**Step 0, before you classify at all.** Check the condition the finding's own body states against the current `HEAD`. If it never held, run `dispatch.sh route <n> <child> stale invalid` and do nothing else. If it held but a later ticket of the same batch or a closing-pass fix already resolved it, run `dispatch.sh route <n> <child> stale fixed-elsewhere` and do nothing else. A finding's claim disproved by current evidence is `invalid`; a valid claim satisfied somewhere else is `fixed-elsewhere`. `fixed-elsewhere` is not a reviewer false positive.

1. **Does it fall inside another still-open ticket's `## Owns`?** → a ticket, `Blocked by` that open one. Not a question of size: the constraint is concurrency. Fixing it yourself in the origin-tracking checkout makes the next `advance` conflict when that ticket's branch merges.
2. **Is it a gap in the criteria themselves** — a `CHECK:` that is already green while the thing it names is broken or never reached? → a ticket, `senior-worker`, and it asks for a negative control.
3. **How many files does the fix touch?** One → fix it yourself. Two or more **with a design coupling between them** — how you fix one decides how you fix the other, and neither can be written until both are settled → a ticket, `senior-worker`. Counting files is not counting effort; it is asking whether the change has a cross-file shape somebody should look at. **A name echoed through prose is not a coupling**: renaming a thing along with its restatements in a domain doc, a `SKILL.md` and a reference file is mechanical, `grep` proves you got them all, and it stays with you.
4. **Nothing matched** → fix it yourself. **The default is to fix it, not to open a ticket.**

The ones you fix: use a checkout that tracks `origin/<into>`. Fetch before each fix, commit it there, run the affected tests, and fast-forward push it to `origin/<into>`. If that push is rejected, fetch, merge the new `origin/<into>` into the commit, run the affected tests again, and retry the fast-forward push. Then `dispatch.sh route <n> <child> fixed` for each, after its commit and push. The commits follow these three rules:

1. One commit per finding, or per group of findings with one cause; the commit message names them by number.
2. It touches only what the finding's cause requires, and the tests that prove it; anything more is a ticket after all.
3. It runs the affected test suites, and the commit message quotes the line it saw (`ran 188 skipped 0`, not "the tests pass").

A fix that exceeds those three is a ticket after all.

The ones that become tickets: open as few tickets as possible. A ticket whose files sit in another live ticket's `## Owns` is `Blocked by` that live ticket. A finding that is a ticket on its own becomes one in place — rewrite its body into a ticket, label it for the agent queue, then `dispatch.sh route <n> <child> became-ticket <child>`; findings folded into one new ticket each get `dispatch.sh route <n> <child> became-ticket <that ticket>`.

A ticket you write here is dispatched in this night, and it has had none of the reading the published batch had. Write it in the shape of `../references/ticket.md`, with every criterion in the four-line shape the To tickets playbook's **Acceptance criteria** gives (`playbooks/to-tickets.md`), and only what its five questions admit as a criterion. Two shapes come back from a night's findings and neither is a criterion: prose that states a rule with no command under it, and the repository's own whole-tree checker — a `lint.sh`, a full type-check — put in a `CHECK:`, which fails on files this ticket never touched and blocks it on somebody else's work.

Then lint each ticket you wrote or rewrote, before you dispatch it:

```bash
verify-ticket.py <n> --lint
```

Read its exit as in 1b; fix every `ERROR` and lint again.

Then:

```bash
dispatch.sh advance <spec>
```

Loop: each `ticket.passed` wakes you at step 3; when the frontier is empty again, this pass runs again. Continue until no open finding survives. Then go to step 5.

#### 5. The night is over

Step 4 left no open finding. From any checkout in this repository:

```bash
dispatch.sh reverify <spec>
dispatch.sh summary <spec>
```

`reverify` exit 0: every landed ticket is green. Exit 1: each red ticket is already reopened in `needs-triage`; do not close it. Exit 2: fix stderr's named condition and run `reverify` again.

To recover a reopened ticket, repair the cause on the base branch, push it, and run `reverify <spec>` again; all met, `reverify` closes it itself. Still red, it stays reopened in `needs-triage`, and `summary` lists it as handed back.

Tickets left for human acceptance, handed back to triage by their worker, or behind an open blocker are valid outcomes; `summary` does not require every ticket to succeed.

`summary` exit 0: `NIGHT SUMMARY` is posted and the spec watch is closed. Exit 1: posted and closed, and a relay was left running; end the pid stderr names. Exit 2: nothing was posted; fix what stderr names and run `summary` again. A refusal counting findings no route reached sends you back to step 4.

Then go to step 6.

#### 6. Open the pull request

The night is delivered as one pull request from the night's branch to the project branch: `into` and `project` of the spec's `spec.opened`, which `events.py fold <spec>` shows. The user reads it in the morning, and it is the only place they need to look.

Write it as the Shared closing playbook's **The pull request** says (`playbooks/shared-closing.md`). Title it `Night #<spec>: <the spec's title>`. Its body, in this order:

1. For the user: what each closed ticket now does for the people who use the product, one line each; every decision left to the user, each with its ticket, why it stopped and your recommendation (tickets handed back to `needs-triage`, open `contract` children, `ready-for-human` tickets no open blocker holds); what was not done and why; what changes once it is merged.
2. The `NIGHT SUMMARY` that `summary` printed, verbatim, under its own heading.
3. For code readers: one line per landed ticket, with the compare link its landing recorded.

```bash
gh pr create --base <project> --head <into> --title "<title>" --body-file <file>
```

Then tell the user the night finished and give them the pull request's link; say that once they accept it, `finish` merges it into the project branch. Done when the pull request is open and the user has its link.

#### 7. Merge the accepted night

Only after the user has accepted the pull request, the orchestrator runs:

```bash
dispatch.sh finish <spec>
```

A worktree that has the base branch checked out, usually the one this session runs in, is kept: stderr gives the commands that remove it, for the user to run once this session is done, and `finish` needs no second run.

Exit 0: the merge is recorded, and GitHub shows the pull request merged. Exit 1: the merge conflicted or the repository checks failed, and nothing was pushed or deleted; stderr says which. Settle a conflict on the night's branch with the **resolving-merge-conflicts** skill and a red check as **A red check** below says, push, and run `finish` again. Do not merge the project branch into the repository default branch here; that remains the user's release decision.

Exit 2 naming the pull request: a check is red or still running, or a review thread is open, and nothing was merged. A check still running: wait for it with `gh pr checks <pr> --watch`, then run `finish` again. Settle each of the rest, then run `finish` again:

- **A red check.** Tell first whether it is a flake, a project branch that moved on, or this night's change. A flake fails on a commit where the same check passed before, or passes when run again once: run the failed job again (`gh run rerun <run> --failed`). A project branch that moved on: `git merge-base --is-ancestor origin/<project> origin/<into>` fails; merge `origin/<project>` into the night's branch as the **resolving-merge-conflicts** skill says and push it. This night's change: fix it as the closing pass fixes a finding (step 4), and push it to `origin/<into>`; the pull request shows the new commit. A fix the closing pass would make a ticket goes to the user instead, who decides whether this night waits for it.
- **A review thread or a comment.** Check its claim against the code first, as `../references/bugbot-triage.md` sorts it. One that holds you fix as the closing pass fixes a finding, then reply with the commit and resolve the thread. One that does not hold you answer with the specific evidence that disproves it, and resolve the thread. One the reference sends to the user you put to the user, who is here now.

When the user asks to take back a merged night, use the Revert button on its merged pull request; do it only when they ask.

Exit 2 naming tickets still open on the night's branch: each is the user's to settle, by a later night or by closing it as not wanted; close none yourself. Tell the user which, and run `finish` again once they have settled them.

Other exits 2: fix what stderr names and run `finish` again.

#### Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `dispatch.sh suspend <spec>` is that decision carried out.

A suspended night wakes nobody: its watch is closed, and its workspaces, branches and pushed commits stay for `open` and `advance` to take up.

Workspaces and branches stay, with the interrupted tickets' commits present on origin. The same batch is taken up again with `dispatch.sh open <spec>` and then `dispatch.sh advance <spec>` once whatever stopped the night is fixed: `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

Exit 0: the night is stopped. Exit 1: stderr names, one line each, what was left; tell the user each line. Exit 2: nothing was touched; fix what stderr names and run `suspend` again. Done when `suspend` exits 0, or exits 1 and you have told the user each line stderr left.

#### One ticket

You are starting one worker on one ticket, with no batch behind it: a step that wrote the ticket sends you here. A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending. What you do on a wake is the dispatch skill's `## On waking`.

Five steps:

1. From a checkout of the project branch, make a branch of its own for this ticket: `git switch -c fix-<n>`. Commit on it whatever a `CHECK:` of the ticket runs that the project branch does not have yet (a reproduction script, a frozen benchmark harness, a decision log), then `git push -u origin fix-<n>`. The ticket lands there, and the pull request runs from there. Done when `fix-<n>` is on origin.
2. `dispatch.sh send worker <n>` from that checkout: this session becomes the ticket's orchestrator, and the worker starts. Then end your turn. Done when `send` exits 0.
3. You are woken with `#<n> ticket.passed` or `#<n> ticket.returned`, or with one of the four below. Read that event on the ticket and `dispatch.sh ack <n> <that event>`, then act on it.
   - `#<n> worker.lost`: the worker's session stopped. `dispatch.sh send worker <n>` starts another in the same workspace; it first commits tracked edits and pushes the ticket branch to origin.
   - `#<n> ticket.refused`: the worker refused to claim the ticket, and the event's `reason` says why. Fix that, then `dispatch.sh send worker <n>` again.
   - `#<n> child.opened`: a `fault` stopped the worker — fix what the child names, then `dispatch.sh resume <n> "<what you fixed>, then: continue"`; a `decision` is for the user, and the worker carries on.
   - `#<n> child.opened` of kind `contract`, a `watchdog:` line, or an `MMW turn guard:` line: act as **3. Each time something wakes you** above says for it, reading `events.py fold <n>` where it says `status`.

   Tell the user what woke you and what you did; they are here. Done when the wake is `ticket.passed` or `ticket.returned`.
4. Once the ticket passed, check it the way the step that wrote it says (for a bug, the original reproduction in the ticket's worktree; for a ticket handed to you from anywhere else, its closing comment's criteria); when that check fails, land nothing, tell the user that `fix-<n>` and `.worktrees/issue-<n>` stay, and go back to that playbook, which says what comes next. List each open child of the ticket (`events.py fold <n>`) in the pull request's top half. Then run `dispatch.sh land <n>` from any checkout of this repository. A ticket that came back is landed the same way: `land` gives back its claim and closes the watch, and it goes to triage. It lands a passed ticket, closes the watch and prints what it did; stderr names anything it left standing. Exit 1: tell the user each line stderr names. Done when `land` exits 0, or the user has its lines. A merge conflict or red repository checks count as `bounced` on its summary line, and without an open night `land` leaves that ticket in `needs-triage`: tell the user which ticket and what the `ticket.bounced` event names.
5. Only for a ticket `land` merged: open one pull request from `fix-<n>` to the project branch, written as the Shared closing playbook's **The pull request** says (`playbooks/shared-closing.md`), give the user its link, and merge it as that playbook's step 7 says. A ticket that came back or bounced opens none: tell the user what it tried and where its commits are, and go back to the playbook that wrote it. Done when the pull request is merged, or the user has its link and has not said yes, or the user knows the ticket came back.

**Reply:** for a night, the pull request's link once it is open, each decision it leaves to the user, and after `finish` the commands its stderr gave for the user to run; for one ticket, the pull request's link or what came back, and each line `land` left on stderr.

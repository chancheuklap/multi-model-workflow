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
| The spec carries `spec.merged` | If the spec issue is still open, go to [7. Merge the accepted night](#7-merge-the-accepted-night) to retry `finish`; otherwise the night is merged, and you tell the user so |
| The user has said the night starts, and the spec carries no `spec.opened` | [1. The user says the night starts](#1-the-user-says-the-night-starts), then 1b and 2 |
| The spec's newest night event is `spec.suspended`, or you are deciding to stop the night because the fault is in the pipeline | [Suspending the night](#suspending-the-night) |
| A retrospective brief wake arrived after `spec.closed` | Resume Retrospective (`playbooks/retrospective.md`) at **Check and apply the answers** |
| A wake arrived: `#<n> <event>`, `brief <batch> done`, a line of `watchdog:` alerts, or `MMW turn guard:` | [3. Each time something wakes you](#3-each-time-something-wakes-you) |
| `dispatch.sh status <spec>` shows an empty frontier and no live agent, and the spec carries no `spec.closed` | [4. The closing pass](#4-the-closing-pass) |
| The spec carries `spec.closed` and no `spec.retroed` | Enter Retrospective (`playbooks/retrospective.md`) with `--spec <spec>` through its re-entry instructions, then [6. Open the pull request](#6-open-the-pull-request) |
| The spec carries `spec.closed`, and no open pull request runs from the night's branch to the project branch | [6. Open the pull request](#6-open-the-pull-request) |
| The pull request is open, and the user has accepted it | [7. Merge the accepted night](#7-merge-the-accepted-night) |
| The pull request is open, and the user has not accepted it | Nothing: wait for the user |

#### 1. The user says the night starts

Run `check` and `open` from a checkout on the night's base branch: the current checkout names it.

```bash
dispatch.sh check <spec>
```

`check` also needs an executable `scripts/check` at the repository root, and runs its default tier once in this checkout, against the base branch, with uncommitted changes counted: there is no merge worktree yet. A night does not open on a red baseline, since every ticket would bounce on it.

**Exit 0:** the machine is ready; open the night. **Exit 2:** fix every condition stderr names and run `check` again; an invalid agent row is reported to the user. A red step of `scripts/check` is fixed in the product, an exit 2 of it in the environment stderr names (a tool, a service, a dependency); a missing `scripts/check` is made by Set up code checkers (`playbooks/set-up-code-checkers.md`).

Then, from this session — the one the night's wakes must reach:

```bash
dispatch.sh open <spec>
```

**Exit 0:** stdout reads `opened #<spec>: wake-ups go to <runner> session <session>`, and this session is the night's orchestrator; when the line goes on to name a task board, hand its URL to the owner. **Exit 2:** fix stderr's named condition and run `open` again.

#### 1b. Before the batch: what the batch cannot be run on

Run this once, before the first `advance`, on every spec, with the `verify-ticket` skill's `verify-ticket.py`:

```bash
verify-ticket.py <spec> --lint
```

Read its exit as the **verify-ticket** skill's `references/linting.md` says.

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
3. Take every row the table matches, not only the ticket named by the wake. For `ticket.returned`, a `fault` child, or `ticket.checked` with `result=handoff`, register each new stall event with the register-problem skill's `scripts/register.py add <file> --source stall --repo <product repository> --ticket <n>`. First read the source ticket's comments for that event's registration. After a successful add, comment there with the originating event's comment URL and the registration issue. Reuse that registration when the same event appears on a later wake or in the closing pass.
4. Run `dispatch.sh advance <spec>` once. Its exit codes are under [**2. First `advance`**](#2-first-advance).
5. When the `advance` you just ran left the frontier empty and no agent live (read `status` again), go to [4. The closing pass](#4-the-closing-pass); otherwise end your turn.

| What you see | What you do |
| --- | --- |
| `ticket.passed`, or a `ready` frontier row | Step 4's `advance` handles it |
| A live worker should continue | `dispatch.sh resume <n> "<what you settled, then: continue>"`; act on exit 0, 4, 3 or 2 as [Exit codes of `resume`](#exit-codes-of-resume) below says |
| `child.opened` of kind `fault` | Read `events.py fold <n>`. Fix a `fault` in this repository's environment (a credential, a service, a `scripts/check` that exits 2), then `dispatch.sh resume <n> "… continue"` and close the child with `dispatch.sh route <n> <child> fixed`. Leave the running pipeline's own scripts unchanged. Hand that `fault` to the owner using the third finding branch of One ticket's **Open the pull request** step (`playbooks/one-ticket.md`), preserving its opening ``A `fault` child of #<n>`` line. Tell the user what failed, and suspend when the rest of the batch would hit it too |
| `child.opened` of kind `contract` | Read the child and the authority it cites. Follow the authority order and the no-authority branch below |
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

For a `contract` child, use this authority order exactly: **decision tickets and ADRs, then the spec, then the winner prototype, then domain documents, then the ticket body**. The e2e tests and the UI prototype stay unchanged during the night. A `contract` child that asks to change an e2e test or the UI prototype always follows the no-authority branch below. A `contract` child saying the sketch does not hold is an engineering call and yours: re-run the **prototype** skill's sketch branch, post the new verdict on the ticket and point the ticket's **Read first** at it, then commit the new sketch as a repository-owned baseline as below and resume the worker. Fix it yourself when you can cite a written authority at that order: a higher authority, a more specific file within the same authority, a repository rule, or the artifact a baseline copied. Edit the tracker-owned spec, acceptance criterion, or ticket body directly; when a spec changes, leave the change-and-reason comment that the Revising a spec playbook (`playbooks/revising-a-spec.md`) requires. Edit a repository-owned baseline through the normal `origin/<into>` commit and push procedure in [4. The closing pass](#4-the-closing-pass). Correct every not-yet-landed ticket derived from the same bad statement. Comment on the child with the authority used, every published item corrected, the source commit, and the tickets checked; run `dispatch.sh route <n> <child> fixed`, then resume the active worker with the exact correction, the commit it should integrate from, and `continue`.

When no authority settles the correction, or the proposed correction would overturn the user's decision or expand the spec, leave the choice to the user. Add `needs-triage` to the `contract` child with `gh issue edit <child> --add-label needs-triage`. Find every not-yet-started ticket derived from the same Parent decision, move each from `ready-for-agent` to `needs-triage`, and comment on the child with the unresolved options, your recommendation, and the ticket numbers moved. Leave the child open for the user. For a ticket already being worked, use `dispatch.sh resume` to tell its worker to abandon the affected criterion as `stuck`, with the reason pointing to this child, and close out so `ticket.returned` moves the ticket to `needs-triage`. When the child asks to change an e2e test, the daytime session corrects it. A prototype correction goes through a new round of the **prototype** skill's UI branch and design freeze. Commit and push the corrected tests or prototype to the next night's branch before `dispatch.sh open`, since ticket checkouts start from `origin`. Close out the child and return both the handed-back tickets and the same-source not-yet-started tickets to `ready-for-agent`.

##### Exit codes of `resume`

Exits 4 and 2 name their next step on stderr. When you run `resume` again after exit 3, word it so a worker that receives both messages reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`.

#### 4. The closing pass

Register stalls found here as [3. Each time something wakes you](#3-each-time-something-wakes-you) says.

The frontier is empty and `status` shows no live agent.

If this spec's tickets still hold open findings, route **exactly those**. These are the children whose `child.opened` event on their ticket has `kind` `finding`, listed per ticket under `children` by `events.py fold <n>`, open until a `child.closed` on the ticket gives their `resolution`. If there are none, go straight to the run of `scripts/check --all` at the end of this step.

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

The ones you fix: use a checkout that tracks `origin/<into>`. Fetch before each fix, commit it there, run `MMW_BASE_REF=<the fix's parent commit> scripts/check`, which runs what the fix can reach, then fast-forward push to `origin/<into>`. If that push is rejected, fetch, merge the new `origin/<into>` into the commit, run `MMW_BASE_REF=<the fix's parent commit> scripts/check` again on the new commit, and retry the fast-forward push. Then `dispatch.sh route <n> <child> fixed` for each, after its commit and push. The commits follow these three rules:

1. One commit per finding, or per group of findings with one cause; the commit message names them by number.
2. It touches only what the finding's cause requires, and the tests that prove it; anything more is a ticket after all.
3. It runs `MMW_BASE_REF=<the fix's parent commit> scripts/check` on the same commit before pushing. The commit message quotes its summary line, not "the tests pass".

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

Loop: each `ticket.passed` wakes you at step 3; when the frontier is empty again, this pass runs again. Continue until no open finding survives.

Then, with the last fix pushed, run `dispatch.sh check-all <spec>` once from any checkout. It runs `scripts/check --all` on `origin/<into>` in the merge worktree, the night's one run of every test, and records it green on the spec as `spec.checked`; `finish` reuses that record when its merge is this tree. It is also the audit of the input lines in `scripts/check`: a red step that no landing of the night selected, since the last change to a file it reads, names an input line that is missing; add it in the same fix and name it in the retrospective. Red: fix each red step as you fix a finding above, push, and run it again. Exit 2: fix the environment stderr names and run it again. Its summary line goes into the pull request's record at step 6. Then go to step 5.

#### 5. The night is over

Step 4 left no open finding. From any checkout in this repository:

```bash
dispatch.sh reverify <spec>
```

`reverify` exit 0: every landed ticket is green. Exit 1: each red ticket is already reopened in `needs-triage`; do not close it. Exit 2: fix stderr's named condition and run `reverify` again.

To recover a reopened ticket, repair the cause on the base branch, push it, and run `reverify <spec>` again; all met, `reverify` closes it itself. Still red, it stays reopened in `needs-triage`, and `summary` lists it as handed back.

After `reverify`, use a checkout at `origin/<into>` with its dependencies installed. Find the products this night touched from the `--config` paths in its tickets' CHECK lines, without a separate registry. For each product, first run the preparation required by the `verify-<product>` skill's Launch that `app.command` does not perform, including any build. Then run `npx e2e run --config tests/e2e/<product>/e2e.config.ts --target product` once. Run only the product target. A red test belonging to an open ticket, whether handed back or not yet worked, is expected: report it under that ticket in the page's Not done and left over block. Its test stays in the batch that merges into the project branch. Any other red test is a regression: investigate with the product's `verify-<product>` skill's Doctor, handle the fix by step 4's closing-pass rules, and rerun after the fix. Put the product-target e2e summary line in the pull request's record.

Tickets left for human acceptance, handed back to triage by their worker, or behind an open blocker are valid outcomes; `summary` does not require every ticket to succeed.

```bash
dispatch.sh summary <spec>
```

`summary` exit 0: `NIGHT SUMMARY` is posted and the spec watch is closed. Exit 1: posted and closed, and a relay was left running; end the pid stderr names. Exit 2: nothing was posted; fix what stderr names and run `summary` again. A refusal counting findings no route reached sends you back to step 4.

Then run Retrospective (`playbooks/retrospective.md`) with `--spec <spec>` before step 6. Resume that playbook on its brief wake, rather than returning to **Each time something wakes you**. Its result, including any failure, goes into the pull request.

#### 6. Open the pull request

The night is delivered as one pull request from the night's branch to the project branch: the `into` and `project` fields of the spec's `spec.opened` comment. The user reads the page its first line names in the morning, and that page is the only place they need to look.

Run Opening a PR (`playbooks/opening-a-pr.md`) from the night's branch, through its step 3, with step 4's `check-all` summary line and each product-target e2e summary line from step 5 for its record. Put handed-back tickets in the page's What the owner decides and Not done and left over blocks. Then tell the user the night finished and give them the pull request's link; say that once they accept it, `finish` merges it into the project branch. Done when the pull request is open and the user has its link.

#### 7. Merge the accepted night

Only after the user has accepted the pull request, the orchestrator runs:

```bash
dispatch.sh finish <spec>
```

A worktree that has the base branch checked out, usually the one this session runs in, and its local branch are kept. For after this session ends, stderr gives a removal command for a linked worktree or a detach command for the main worktree, which Git cannot remove. The local night branch stays available after `finish`, and the local project branch is created or fast-forwarded to the fetched origin tip. A clean project worktree fast-forwards too. Uncommitted changes or local commits outside origin leave the project branch unchanged, with the reason on stderr. Landing deletes local and origin ticket branches when cleanup permits it. `finish` removes the origin night branch when cleanup permits it.

Exit 0: the night is merged, the spec issue is closed as completed, and GitHub shows the pull request merged. Exit 1: the merge conflicted or `scripts/check` was red, and nothing was pushed or deleted; stderr says which. Settle a conflict on the night's branch with the **resolving-merge-conflicts** skill and a red check as Opening a PR step 3 says, push, and run `finish` again. Do not merge the project branch into the repository default branch here; that remains the user's release decision.

Exit 2 naming the pull request: a check is red or still running, or a review thread is open, and nothing was merged. Settle each as Opening a PR step 3 says (`playbooks/opening-a-pr.md`), then run `finish` again. A fix this night's change needs is made as the closing pass fixes a finding (step 4) and pushed to `origin/<into>`; the pull request shows the new commit. A fix the closing pass would turn into a ticket goes to the user instead, who decides whether this night waits for it.

When the user asks to take back a merged night, use the Revert button on its merged pull request; do it only when they ask.

Exit 2 naming tickets still open on the night's branch: whether each is closed is the user's decision; close none yourself. Tell the user which, and run `finish` again once they are closed.

Exit 2 naming a spec that could not be closed: the merge and its record stay in place. Run `finish` again to close the spec without merging again.

Other exits 2: fix what stderr names and run `finish` again.

#### Suspending the night

A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work. `dispatch.sh suspend <spec>` is that decision carried out.

A suspended night wakes nobody: its watch is closed, and its workspaces, branches and pushed commits stay for `open` and `advance` to take up.

Workspaces and branches stay, with the interrupted tickets' commits present on origin. The same batch is taken up again with `dispatch.sh open <spec>` and then `dispatch.sh advance <spec>` once whatever stopped the night is fixed: `start` fetches origin and reuses or fast-forwards each standing ticket workspace.

Exit 0: the night is stopped. Exit 1: stderr names, one line each, what was left; tell the user each line. Exit 2: nothing was touched; fix what stderr names and run `suspend` again. Done when `suspend` exits 0, or exits 1 and you have told the user each line stderr left.

**Reply:** the pull request's link once it is open, and after `finish` the commands its stderr gave for the user to run.

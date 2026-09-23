# Ticket run

One ticket from claim to close: the sessions that work and judge it, the events they leave on it, the runs of its criteria, the code review, the advisor, the closing steps and the gate that closes it. Everything this part of the pipeline knows is written on the ticket, where the next session reads it with an empty context.

How to read an entry: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour), and when the two disagree, `_Home_` is right.

## Language

### Roles

**worker**:
The session dispatched to work one ticket from claim to closing comment, running the `implement` skill in the ticket's worktree. It starts its own reviewer and never closes the ticket by hand.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**reviewer**:
The session a worker starts with `dispatch.sh start <n> reviewer` to review the ticket's diff from a base commit with the `code-review` skill; its report is the **review comment**. Its code-review axes run inside it.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**advisor**:
The second-opinion session on a stronger model, started with `dispatch.sh advise <packet file>` by whichever agent reached the decision. It implements nothing.
_Home_: `mmw-v2/skills/advisor/references/consulting.md`

**question packet**:
What a caller hands the advisor, and the only thing the advisor sees: the recent exchange, the caller's understanding, the constraints, the options and its leaning, and the relevant paths. It carries the decision and the evidence, never what to conclude.
_Home_: `mmw-v2/skills/advisor/references/consulting.md`

**recommendation**:
What one consultation of the advisor gives back: do X, not Y, because Z, with the single risk that decides it.
_Home_: `mmw-v2/skills/advisor/references/advising.md`

### Worker shared experience

**task root**:
The map or standalone spec that bounds one worker's shared experience, derived from the ticket's native parent graph and printed in the worker's start prompt as `MMW task root:`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`MMW_TASK_SCOPE`**:
The one task-scope Memory label a worker retrieves and writes under: `mmw-map-<n>` for a map task or `mmw-spec-<n>` for a standalone spec, passed by `dispatch.sh start <n> worker`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**Current task shared experience**:
The index of the newest Memory records carrying `MMW_TASK_SCOPE` in the repository Space, put into a worker's start prompt. Distinct from **Related experience**, which is found by search.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**Related experience**:
The index of `mmw-experience` Memory records a worker's start finds by searching the ticket's `## Owns` paths and the ticket, spec and map titles, put into the start prompt.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`MMW_TICKET`**:
The environment variable holding the ticket number: in a worker's process, set by `dispatch.sh start <n> worker`, and in a criterion's shell, set by `verify-ticket.py`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### Reviewer Rules

**reviewer Rules**:
The Nowledge Mem Rules the user approved that `dispatch.sh start <n> reviewer` copies into the reviewer's start prompt. They decide what the reviewer inspects; every finding still needs a current source.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

### Comments on the ticket

**ticket comment**:
One comment a script or an agent leaves on a ticket. Every one a script leaves is an **event**; a comment an agent types is prose, which no program reads.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**event**:
One comment recording one thing that happened: a first line and prose for a person, and a trailing `<!-- mmw {...} -->` block, which is the whole of what a program reads. Its name is `subject.verb`, and every event is posted by a script.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**fold**:
A ticket's state, computed and stored nowhere: the ticket's comments read in comment-id order and their events replayed from an empty state. `events.py fold <issue>` prints it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**held**:
What the fold says of a ticket an agent may still be working: it stays off the frontier and `advance` does not give its claim back. Distinct from a product **slot**, which a worktree keeps until its ticket's work ends.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**unreadable event**:
A comment carrying an `<!-- mmw` block the fold cannot read. It is never taken for prose: every command that decides from the fold refuses to decide about that ticket until a person fixes the comment.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**landed**:
What `status.py` calls a closed ticket whose passed commit is in `origin/<base branch>`, recorded by a `ticket.landed` event after its `ticket.passed`.
_Avoid_: closed (for this; a closed ticket may not have landed)
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**first line**:
The first line of a ticket comment: prose for a person on an event, and a script's input on a closeout draft (`ALL MET`, `HANDOFF REQUIRED:`), on a review report (`REVIEW <base commit>..<HEAD commit>`) and on a child's file (its title).
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`worker.started`, `reviewer.started`**:
The event (a started event) `dispatch.sh start` posts once the runner has started the session, naming its runner, the runner's id for it and the machine. It is the only record of the session, and it begins a hold.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.claimed`, `ticket.refused`**:
The two events `--preflight` posts: `ticket.claimed` after the claim, beginning a hold, or `ticket.refused` with the first refusal's reason.
_Home_: `mmw-v2/skills/verify-ticket/references/claiming.md`

**`ticket.passed`, `ticket.returned`**:
The events `--closeout` posts a closing comment as, each after the tracker change it announces: `ticket.passed` for an accepted `ALL MET` draft once the ticket is closed, `ticket.returned` for a `HANDOFF REQUIRED` draft once the ticket is handed back.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`ticket.released`**:
The event that follows a claim given back by `land`, `suspend` or `advance`'s `RELEASE` line. It ends every hold on the ticket.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.landed`**:
The event `advance` or `land` posts once a ticket's passed commit is pushed to `origin/<base branch>`. It is what lets the tickets it blocks start.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`ticket.regressed`**:
The event `reverify` posts on a landed ticket whose criteria went red on the base branch, in the pass that reopens it for triage. It takes back the pass and the landing.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.recovered`**:
The event `reverify` posts on a reopened ticket whose criteria are all met again, in the pass that closes it. It puts the pass and the landing back.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.bounced`**:
The event recording a landing merge conflict or failed repository checks; it takes back the pass and the landing and leaves the workspace standing. The first bounce in an open night returns the ticket to `ready-for-agent`, a second moves it to `needs-triage`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`worker.resumed`, `worker.retracted`, `worker.replaced`, `worker.lost`**:
The events about one worker session after its start, each naming it by runner and session: `resume`, `retract` and a replacing `start` post the first three, and the **watchdog** posts `worker.lost` once the session's runner says it has stopped.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`reviewer.reported`**:
The event `verify-ticket.py <n> --review <file>` posts carrying the **review comment**. The relay turns it into the worker's wake.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`reviewer.lost`**:
The event the **watchdog** posts for a reviewer session that stopped before its report landed. The relay wakes the worker on it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`spec.opened`, `spec.closed`, `spec.retroed`**:
The events of a night on its spec: `spec.opened` from `open` (the main agent, the base branch and the project branch), `spec.closed` from `summary` (the `NIGHT SUMMARY`), and `spec.retroed` from the retro (its receipt). Distinct from `spec.merged`, which `finish` posts.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`spec.suspended`**:
The event `suspend` posts on the spec and on every ticket still in the agent queue, first line `NIGHT SUSPENDED #<spec>`. It ends every hold on the ticket.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`child.opened`, `child.closed`**:
The events that record a ticket's children on the ticket: `--sub-issue` posts `child.opened` with the child's number and kind, and `route` posts `child.closed` with where a `finding` went.
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**child kind**:
What a ticket's child records, named for who can answer it: `finding` (a review finding outside the ticket), `contract` (a baseline, spec section or criterion the ticket was told to follow that lacks a needed case or contradicts another authority), `deferred` (a convenient change outside `## Owns`), `decision` (a choice only a person can make), `fault` (the pipeline itself is broken: `verify-ticket.py`, `dispatch.sh`, a judge script, `lease.py`, a hook or `.mmw/target.json`).
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**`ticket.checked`**:
One run of a ticket's criteria, or of the repository's `checks`, on one commit. Its `run` says whose: `self`, `reverify`, `repo-checks` or `baseline`.
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**baseline run**:
The `ticket.checked` of run `baseline`: the ticket's criteria run at the base commit during `--preflight`, before the worker changes anything. Distinct from a **baseline**, the settled `## Read first` item.
_Home_: `mmw-v2/skills/verify-ticket/references/claiming.md`

**`worker.touched`**:
The event `--touched` posts on an open sibling ticket whose `## Owns` covers a file this ticket changed outside its own Owns.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`worker.queued`**:
The event a run of a ticket's criteria posts when it needs the product and no **slot** is free. The worker ends its turn, and the relay wakes it when a slot is given back.
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**`worker.decided`**:
The event (the `DECISIONS` comment) `--decisions <file>` posts once, before the reviewer starts: the decisions the worker made on its own so far, and why each file under `Outside Owns:` was changed. The Spec axis judges it.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**review comment**:
The reviewer's report on the ticket, carried by `reviewer.reported`: first line `REVIEW <base commit>..<HEAD commit>`, then the axis reports, the refuted findings, and the in-ticket and out-of-ticket findings.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**closing comment**:
The comment a worker leaves on handing the ticket over, written first as a draft file that `--closeout <draft>` checks and posts: first line `ALL MET` or `HANDOFF REQUIRED: …`, then fixed lines accounting for every criterion, finding, file outside Owns and decision.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`ALL MET`**:
The closing comment's first line when every criterion is met, which `--closeout` posts as `ticket.passed`. gate-check's summary line opens with the same words.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`HANDOFF REQUIRED`**:
The closing comment's first line when a criterion is unmet or abandoned as `failed` or `stuck`, which `--closeout` posts as `ticket.returned` while it hands the ticket back.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

**`Outside Owns:`**:
The files the ticket's own commits changed that no `## Owns` glob covers, listed by the worker's `self` run and carried into the closing comment with the Spec axis's judgement of each.
_Home_: `mmw-v2/skills/verify-ticket/references/running-criteria.md`

**`NIGHT SUMMARY`**:
The first line, `NIGHT SUMMARY <date>`, of the `spec.closed` comment `summary` posts on the spec, and the account under it of how each ticket and finding of the night ended.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

**`spec.merged`**:
The event `finish` posts on the spec after the accepted base branch has been merged into the project branch and pushed.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

### Running the criteria

**ledger**:
The temporary `AC.md` file `verify-ticket.py` writes from `## Acceptance criteria` and hands to gate-check, the only format gate-check reads. It is deleted after the run.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**gate-check**:
The judging program from unlazy: it runs each criterion's `CHECK:` in its own shell, counts the criterion met when the command exits 0 and its output matches `EXPECT:`, writes `EVIDENCE:`, and prints a summary line.
_Home_: `mmw-v2/upstream-unlazy/scripts/gate-check.mjs`

**gate-lint**:
The criterion linter from unlazy, which reports problems in how criteria are written and runs no command. `--lint` runs it.
_Home_: `mmw-v2/upstream-unlazy/scripts/gate-lint.mjs`

### Code review

**code review**:
One review of a ticket's diff by the reviewer session, ending with one **review comment**. Its in-ticket findings get one round of fixes and no second review.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**axis**:
One dimension of a code review — Standards, Spec, Tests, and UI when the ticket has a story criterion — run as a subagent of the reviewer session where the host can run one, and by the session itself in turn where it cannot.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**review finding**:
One item an axis reports, quoting the requirement it fails. It is in-ticket when it touches this ticket's criteria, its spec sections, its baselines or its `## Owns`, and otherwise out-of-ticket, opened as a `finding` child.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**reference file**:
A document under a skill's `references/` directory, reached from its `SKILL.md`.
_Home_: `AGENTS.md`

### Claiming and handing back

**preflight**:
`verify-ticket.py <n> --preflight`, the worker's first step: the checks that the ticket may be claimed, the claim itself, and the **baseline run**.
_Home_: `mmw-v2/skills/verify-ticket/references/claiming.md`

**claim**:
Setting the ticket's assignee to oneself, followed by a `ticket.claimed` event. The frontier takes only unassigned tickets, so a claim keeps a second worker off the ticket.
_Home_: `docs/agents/issue-tracker.md`

**hand back**:
Swapping `ready-for-agent` for `needs-triage`, taking the claim off and leaving the ticket open: what `--closeout` does with a `HANDOFF REQUIRED` draft.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**continue**:
The word the main agent ends a `resume` text with, telling a live worker to carry on from where it was.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

### Working discipline

**writing rules**:
The rules under `implement`'s `While writing code:` that govern every write on a ticket, the fixes of the review round included.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closing steps**:
What `implement` does once the code is written, from integrating the base branch through the review, the final full run and the Audit to `--closeout`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`Audit`**:
The closing step that re-reads the whole ticket and every `## Read first` item, traces every criterion to its latest `EVIDENCE:`, and recounts `Counts:`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closeout**:
`verify-ticket.py <n> --closeout <draft>`, the closing gate: it checks the draft against the ticket and the repository and, only when the draft passes, pushes the branch, closes the ticket or hands it back, and posts the closing comment as an event. A worker's command that would go around it is refused by `tool-guard.py`.
_Home_: `mmw-v2/skills/verify-ticket/references/closeout.md`

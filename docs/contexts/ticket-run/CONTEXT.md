# Ticket run

One ticket from claim to close: the sessions that work and judge it, the events they leave on it, the runs of its criteria, the code review, the advisor, the closing steps and the closeout. Everything this part of the pipeline knows is written on the ticket, where the next session reads it with an empty context.

## Language

### Roles

**worker**:
The session dispatched to work one ticket from claim to closing comment, running the `implement` skill in the ticket's worktree. It starts its own reviewer and never closes the ticket by hand.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**reviewer**:
The session a worker starts with `dispatch.sh start <n> reviewer` to review the ticket's diff from a base commit with the `code-review` skill; its report is the **review report**. Its code-review axes run inside it.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**advisor**:
The second-opinion session on a stronger model, started with `dispatch.sh advise <brief file>` by whichever agent reached the decision. It implements nothing.
_Home_: `mmw-v2/skills/advisor/references/consulting.md`

**brief**:
What a caller hands the advisor, and the only thing the advisor sees: the recent exchange, the caller's understanding, the constraints, the options and its leaning, and the relevant paths. It carries the decision and the evidence, never what to conclude.
_Avoid_: question packet, the packet
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

**save conditions**:
`implement`'s three conditions that must all hold before a Memory is saved: another ticket or later agent may reuse the fact, a current command result or authority verifies it, and the ticket and code do not already make it obvious.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`MMW_TICKET`**:
The environment variable holding the ticket number: in a worker's process, set by `dispatch.sh start <n> worker`, and in a criterion's shell, set by `verify-ticket.py`.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

### Reviewer Rules

**reviewer Rules**:
The Nowledge Mem Rules the user approved that `dispatch.sh start <n> reviewer` copies into the reviewer's start prompt. They decide what the reviewer inspects; every finding still needs a current source.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

### Comments on the ticket

**issue comment**:
One comment a script or an agent leaves on a tracker issue: a ticket, a spec or a child. Every one a script leaves is an **event**; a comment an agent types is prose, which no program reads.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**event**:
One comment recording one thing that happened: a first line and prose for a person, and a trailing `<!-- mmw {...} -->` block, which is the whole of what a program reads. Its name is `subject.verb`, and every event is posted by a script.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**fold**:
A ticket's state, computed and stored nowhere: the ticket's comments read in comment-id order and their events replayed from an empty state. `events.py fold <issue>` prints it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**hold**:
What a `ticket.claimed` or any `*.started` begins on a ticket, and what the events after it end: `ENDS_EVERY_HOLD` ends every hold on the ticket, `ENDS_ONE_HOLD` the hold of the one session it names, and `reviewer.reported` its own reviewer's. `ticket.passed` ends none, and no label ends one. Distinct from **`blocker_hold`** and from the night's `HOLD` **plan line**.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**held**:
What the fold says of a ticket an agent may still be working: it stays off the frontier and `advance` does not give its claim back. Distinct from a product **slot**, which a worktree keeps until its ticket's work ends, and from **`blocker_hold`**, the wait on a blocker that has not landed.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`blocker_hold`**:
Why a ticket's blocker still holds it back, read off the blocker's own events, not this ticket's: `"open"` while the blocker has not closed, `"passed, not landed"` while its pass has not reached the base branch yet, `"its events cannot be read"` or `"the tracker did not answer for it"` when the fold cannot say, and empty once the blocker's work is on the base branch or it closed with nothing that will ever land — a blocker lets go on its own `ticket.landed`, not on closing. The task board reads the empty case as **cleared**.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**unreadable event**:
A comment carrying an `<!-- mmw` block the fold cannot read. It is never taken for prose: every command that decides from the fold refuses to decide about that ticket until a person fixes the comment.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**landed**:
What `status.py` calls a closed ticket whose passed commit is in `origin/<base branch>`, recorded by a `ticket.landed` event after its `ticket.passed`.
_Avoid_: closed (for this; a closed ticket may not have landed)
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**first line**:
The first line of an issue comment: prose for a person on an event, and a script's input on a closing-comment draft (`ALL MET`, `HANDOFF REQUIRED:`), on a review report (`REVIEW <base-commit>..<HEAD commit>`) and on a child's file (its title).
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`worker.started`, `reviewer.started`**:
The event (a started event) `dispatch.sh start` posts once the runner has started the session, naming its runner, the runner's id for it and the machine. It is the only record of the session, and it begins a hold.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`ticket.claimed`, `ticket.refused`**:
The two events `--preflight` posts: `ticket.claimed` after the claim, beginning a hold, or `ticket.refused` with the first refusal's reason.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`ticket.passed`, `ticket.returned`**:
The events `--closeout` posts a closing comment as, each after the tracker change it announces: `ticket.passed` for an accepted `ALL MET` closing-comment draft once the ticket is closed, `ticket.returned` for a `HANDOFF REQUIRED` closing-comment draft once the ticket is handed back.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

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
The event `verify-ticket.py <n> --review <file>` posts carrying the **review report**. The relay turns it into the worker's wake.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`reviewer.lost`**:
The event the **watchdog** posts for a reviewer that stopped before its report landed. The relay wakes the worker on it.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`spec.opened`, `spec.closed`, `spec.retroed`**:
The events of a night on its spec: `spec.opened` from `open` (the orchestrator, the base branch and the project branch), `spec.closed` from `summary` (the `NIGHT SUMMARY`), and `spec.retroed` from the retro. Distinct from `spec.merged`, which `finish` posts.
_Home_: `mmw-v2/skills/verify-ticket/scripts/events.py`

**`spec.suspended`**:
The event `suspend` posts on the spec and on every ticket still in the agent queue, first line `NIGHT SUSPENDED #<spec>`. It ends every hold on the ticket.
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`child.opened`, `child.closed`**:
The events that record a ticket's children on the ticket: `--sub-issue` posts `child.opened` with the child's number and kind, and `route` posts `child.closed` with where a `finding` went.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`, `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**child kind**:
What a ticket's child records, named for who can answer it: `finding` (a review finding outside the ticket), `contract` (a baseline, spec section or criterion the ticket was told to follow that lacks a needed case or contradicts another authority), `deferred` (a convenient change outside `## Owns`), `decision` (a choice only a person can make), `fault` (the pipeline itself is broken: `verify-ticket.py`, `dispatch.sh`, an oracle script, `lease.py`, a hook or `.mmw/target.json`). `fault` and `contract` wake the orchestrator that night; `decision` and `deferred` reach the user in the morning; a `finding` waits for the closing pass.
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**the kind questions**:
The ordered yes/no ladder that picks a cut-out child's kind, the first `yes` deciding it: is the pipeline itself broken or the product unreachable (`fault`); does a baseline, named spec section or acceptance criterion fail to hold (`contract`); do the sources say nothing while defensible readings would produce observably different outcomes (`decision`); is it a review defect outside `## Owns` (`finding`); is it a merely convenient change outside `## Owns` (`deferred`).
_Avoid_: the five questions (`to-tickets`' own name for a different five-step ladder, which decides how something becomes an acceptance criterion, a review judgement, a `reaction`/`reach` ticket, or a user choice)
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

**`ticket.checked`**:
One run of a ticket's criteria, or of the repository's `checks`, on one commit. Its `run` says whose: `self`, `reverify`, `repo-checks` or `baseline`; its `stage` (`CHECK_STAGES`) groups those into `claim`, `work`, `verify` or `close`, and a `reverify` by the orchestrator (`actor` `main`) is `regress`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**baseline run**:
The `ticket.checked` of run `baseline`: the ticket's criteria run at the base commit during `--preflight`, before the worker changes anything. Distinct from a **baseline**, the settled `## Read first` item.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`worker.touched`**:
The event `--touched` posts on an open sibling ticket whose `## Owns` covers a file this ticket changed outside its own Owns.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`worker.queued`**:
The event a run of a ticket's criteria posts when it needs the product and no **slot** is free, its reason `product-full` (the product's own instance cap) or `machine-full` (every slot of the machine). The worker ends its turn, and the relay wakes it when a slot is given back.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`worker.decided`**:
The event (the `DECISIONS` comment) `--decisions <file>` posts once, before the reviewer starts: the worker's `## Decisions I made on my own`, one line per decision, and `## Outside Owns`, one line per file changed outside `## Owns` with the reason. The Spec axis gives each line `reasonable` or `should not`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**review report**:
The reviewer's one report on the ticket, carried by `reviewer.reported`: first line `REVIEW <base-commit>..<HEAD commit>`, then the axis reports, the refuted findings, and the in-ticket and out-of-ticket findings.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**closing comment**:
The comment a worker leaves on handing the ticket over, written first as a closing-comment draft that `--closeout <draft>` checks and posts: first line `ALL MET` or `HANDOFF REQUIRED: …`, then fixed lines accounting for every criterion, finding, file outside Owns and decision.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`ALL MET`**:
The closing comment's first line when every criterion is met, which `--closeout` posts as `ticket.passed`. gate-check's summary line opens with the same words.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`HANDOFF REQUIRED`**:
The closing comment's first line when a criterion is unmet or abandoned as `failed` or `stuck`, which `--closeout` posts as `ticket.returned` while it hands the ticket back.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`Review findings:`, `Green before work:`, `skipped:`, `Sub-issues opened:`, `Branch: … Commit: … PR: …`, `Counts:`**:
The fixed lines every closing-comment draft carries after its first line: each in-ticket review finding as `fixed <commit>` or `refuted: <evidence>`; the criteria the baseline run already found met; the criteria it could not run, filled `[X], add when [Y]`; this ticket's own sub-issues; the ticket branch, its head commit and that no pull request exists; and the met/unmet/abandoned tally, which `--closeout` computes from the draft's own `ABANDON:` lines rather than the worker counting it. Every blank starts as the placeholder `<fill>`, which `--closeout` refuses if any remains.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`DRAFT:`, `CLOSEOUT OK:`, `CLOSED:`, `HANDED BACK:`, `TOUCHED:`, `DECISIONS: posted on #`, `REVIEW: posted on #`, `LINT OK`, `LINT FINDINGS:`**:
The line each `verify-ticket.py` subcommand (other than `--preflight`) prints once it has acted, naming the outcome for whoever invoked it: the path `--draft` wrote; one of `--closeout`'s three results; the sibling tickets `--touched` told; that `--decisions` or `--review` posted its comment; and `--lint`'s verdict, with its warning or error count.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`Outside Owns:`**:
The files the ticket's own commits changed that no `## Owns` glob covers, listed by the worker's `self` run and carried into the closing comment with the Spec axis's judgement of each.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

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
The program from unlazy that runs each criterion's `CHECK:` in its own shell: it counts the criterion met when the command exits 0 and its output matches `EXPECT:`, writes `EVIDENCE:`, and prints a summary line.
_Home_: `mmw-v2/upstream-unlazy/scripts/gate-check.mjs`

**gate-lint**:
The criterion linter from unlazy, which reports problems in how criteria are written and runs no command. `--lint` runs it.
_Home_: `mmw-v2/upstream-unlazy/scripts/gate-lint.mjs`

### Code review

**code review**:
One review of a ticket's diff by the reviewer, ending with one **review report**. Its in-ticket findings get one round of fixes and no second review.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**axis**:
One dimension of a code review — Standards, Spec, Tests, and UI when the ticket has a story criterion — run as a subagent of the reviewer where the host can run one, and by the reviewer itself in turn where it cannot.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**story criterion**:
A `CHECK:` that names `story-parity.py`: what tells the reviewer to run a fourth axis, UI. `implement`'s `references/writing-interface-code.md` is read when **Read first** lists a screen contract, not because of this criterion.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**Holds / `refuted` / Could not tell**:
The one conclusion the reviewer renders on each axis finding by rereading the cited code, before it sorts the finding: **Holds** (the bad outcome does occur), `refuted` (checked, and it does not — moved to `## Withdrawn` with the disproof), or **Could not tell** (marked `unverified: <what would settle it>` on its in-ticket/out-of-ticket line). `refuted` is the same word a worker's closing comment uses for the same judgement, one name across `code-review` and `implement`.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**review category**:
The name an axis gives one of its own findings on its `## In-ticket` / `## Out-of-ticket` line: a Standards smell or `less-code`/`pass-through`, a Tests shape, a Spec or UI kind, or `documented-standard` for a breach of a rule the repository itself documents. Distinct from the retro's categories (`retro.py` `CATEGORIES`).
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**review finding**:
One item an axis reports, quoting the requirement it fails, and sorted at the review session's own step into in-ticket or out-of-ticket: in-ticket when it touches this ticket's acceptance criteria, a decision in its named spec section, a baseline under its `## Read first`, the spec's `## Out of Scope` or `## Testing Decisions`, or a file inside this ticket's own `## Owns`; otherwise out-of-ticket, opened by the worker as a `finding` child.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/session.md`

**Missing / Scope creep / Built wrong**:
The Spec axis's three kinds of review finding: something the ticket, its named spec section or a baseline asked for that the diff does not do (**Missing**); behaviour the diff adds that nothing asked for, most clearly something the spec's `## Out of Scope` names (**Scope creep**); and something that looks implemented but does not match what was asked (**Built wrong**).
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/spec-reviewer.md`

**`reasonable` / `should not`**:
The Spec axis's judgement of each line of the worker's `DECISIONS` comment, one of two values: `reasonable` when the ticket or spec left a gap and the decision is the likeliest repair, `should not` when it goes against the ticket, a named spec section, `## Out of Scope`, or a baseline — itself a review finding of one of the three Spec kinds.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/spec-reviewer.md`

**semantic-conflict angles**:
The Spec axis's review of this ticket together with every ticket `dispatch.sh integrated <ticket>` lists as already integrated into the base branch, for semantic conflicts (Martin Fowler, SemanticConflict: changes that merge cleanly as text but make the program behave differently), from four angles: **Combination behavior** (behaviours that pass alone still work together), **Contract consistency** (data models, interfaces, schemas and registries agree across tickets), **Migration completeness** (migrations run in the right order with every companion present), and **Shared-state ownership** (both tickets agree on ownership, ordering and lifecycle of shared state). Another ticket's own passed verdict is evidence of what ran, not proof the combination is correct.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/spec-reviewer.md`

**`unpaired-decoration` / `overall-look` / `design-page-wrong`**:
The UI axis's three kinds of review finding, each about what its story screenshots show that element parity does not already cover: **`unpaired-decoration`** (a design-page decoration with no `data-ui` id, so element parity cannot pair it, missing, extra or misplaced in the submitted story), **`overall-look`** (the submitted story's overall look against the design page, not named by any `DIFF` line), and **`design-page-wrong`** (the design page itself is drawn wrong; the repair is not a product change).
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/ui-reviewer.md`

**Only the happy path**:
The Tests axis's own sixth test-smell shape, alongside five drawn from the `tdd` skill: a case in scope covers only the ordinary input while the code it tests has an edge, a boundary, or an error path the criterion's behaviour depends on, left untested.
_Home_: `mmw-v2/upstream/skills/engineering/code-review/references/tests-reviewer.md`

**reference file**:
A document under a skill's `references/` directory, reached from its `SKILL.md`.
_Home_: `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`

### Claiming and handing back

**preflight**:
`verify-ticket.py <n> --preflight`, the worker's first step: the checks that the ticket may be claimed, the claim itself, and the **baseline run**.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`NOT_READY:`, `READY:`, `RESUME:`, `CARRIED:`**:
The fixed lines `--preflight` prints as it claims a ticket: `NOT_READY:` on stderr when it cannot, with a sentence saying why and what to do next (the refusal's code, `wrong-branch`, `dirty-tree`, `not-open`, `not-ready`, `blocked` or `claimed-by-other`, goes into the `ticket.refused` event's `reason`), `READY:` once claimed, `RESUME: step <k> (<event>)` naming which closing step a reclaiming worker resumes at, and `CARRIED:` when the worker's own uncommitted tracked changes are found on reclaim. Until B2 a where line stands beside `RESUME:`: for each role it gives one answer of the same kind, read from that role's events.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**claim**:
Setting the ticket's assignee to oneself, followed by a `ticket.claimed` event. The frontier takes only unassigned tickets, so a claim keeps a second worker off the ticket.
_Home_: `docs/agents/issue-tracker.md`

**hand back**:
Swapping `ready-for-agent` for `needs-triage`, taking the claim off and leaving the ticket open: what `--closeout` does with a `HANDOFF REQUIRED` closing-comment draft.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**continue**:
The word the orchestrator ends a `resume` text with, telling a live worker to carry on from where it was.
_Home_: `mmw-v2/skills/dispatch/references/night.md`

### Working discipline

**code-writing rules**:
The rules under `implement`'s `While writing code:` that govern every write on a ticket, the fixes of the review round included.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closing steps**:
What `implement` does once the code is written, from integrating the base branch through the review, the **final run** and the Audit to `--closeout`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**final run**:
`verify-ticket.py <n> --reverify --actor worker`, the worker's last run of every criterion, after the last step that writes a commit and with no fix round after it. `--closeout` accepts an `ALL MET` draft only when the newest such run is on `HEAD` and ran the ticket's current criteria.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`, `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`Audit`**:
The closing step that reads the ticket once more against the branch, the way the user will read the closing comment: each point under `## What to build` holds in the product, not only in a test, and each baseline under `## Read first` is followed where it applies, with what does not hold said in the closing comment. It computes nothing itself: `Counts:` is `--closeout`'s own tally of the draft's `ABANDON:` lines.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**closeout**:
`verify-ticket.py <n> --closeout <draft>`: it checks the closing-comment draft against the ticket and the repository and, only when it passes, pushes the branch, closes the ticket or hands it back, and posts the closing comment as an event. A worker's command that would go around it is refused by `tool-guard.py`.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

### Writing interface code


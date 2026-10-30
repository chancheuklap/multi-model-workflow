# Ticket run

One ticket from claim to close: the sessions that work and judge it, the events they leave on it, the runs of its criteria, the code review, the advisor, the closing steps and the closeout. Everything this part of the pipeline knows is written on the ticket, where the next session reads it with an empty context.

## Language

### Roles

**worker**:
The session dispatched to implement one ticket under Work a ticket, from claim to closing comment. Its worker grade selects its startup configuration; verify-ticket owns criterion records and closeout.

**reviewer**:
The dispatched role that applies code-review to a ticket's diff and reports on that ticket. Its independent review axes are subagents where supported.

**`advisor`**:
The [second-opinion skill](../../../mmw-v4/skills/advisor/SKILL.md) and briefed session role assessing one decision. It returns a checked recommendation and implements nothing.

**brief**:
The bounded assignment document for a session sent by dispatch, with Task, Known and For sections. An advisor brief carries the decision, relevant exchange, evidence, constraints and options rather than a prescribed conclusion.

**recommendation**:
The advisor's judgment on the decision, with its deciding reason, risk and any missing evidence that would change it.

### Worker shared experience

**task root**:
The map or standalone spec that bounds one worker's shared experience, derived from the ticket's native parent graph and printed in the worker's start prompt as `MMW task root:`.

**`MMW_TASK_SCOPE`**:
The one task-scope Memory label a worker retrieves and writes under: `mmw-map-<n>` for a map task or `mmw-spec-<n>` for a standalone spec, passed by `dispatch.sh start <n> worker`.

**Current task shared experience**:
The index of the newest Memory records carrying `MMW_TASK_SCOPE` in the repository Space, put into a worker's start prompt. Distinct from **Related experience**, which is found by search.

**Related experience**:
The index of `mmw-experience` Memory records a worker's start finds by searching the ticket's `## Owns` paths and the ticket, spec and map titles, put into the start prompt.

**save conditions**:
The three conditions that must all hold before a worker saves a Memory: another ticket or later agent may reuse the fact, a current command result or authority verifies it, and the ticket and code do not already make it obvious.

**`MMW_TICKET`**:
The environment variable holding the ticket number: in a worker's process, set by `dispatch.sh start <n> worker`, and in a criterion's shell, set by `verify-ticket.py`.

### Comments on the ticket

**issue comment**:
One comment a script or an agent leaves on a tracker issue: a ticket, a spec or a child. Every one a script leaves is an **event**; a comment an agent types is prose, which no program reads.

**event**:
One comment recording one thing that happened: a first line and prose for a person, and a trailing `<!-- mmw {...} -->` block, which is the whole of what a program reads. Its name is `subject.verb`, and every event is posted by a script.

**fold**:
A ticket's state, computed and stored nowhere: the ticket's comments read in comment-id order and their events replayed from an empty state. `events.py fold <issue>` prints it.

**hold**:
The ticket ownership begun by a claim or started session and ended by the matching lifecycle events. A passed result or label alone does not end that ownership; blocker_hold is a separate dependency condition.

**held**:
What the fold says of a ticket an agent may still be working: it stays off the frontier and `advance` does not give its claim back. Distinct from **`blocker_hold`**, the wait on a blocker that has not landed.

**`blocker_hold`**:
The fold's reason that a blocking ticket has not yet released its dependent work. A passed blocker remains blocking until landed, and unreadable blocker evidence remains an unresolved hold.

**unreadable event**:
A comment carrying an `<!-- mmw` block the fold cannot read. It is never taken for prose: every command that decides from the fold refuses to decide about that ticket until a person fixes the comment.

**landed**:
What `status.py` calls a closed ticket whose passed commit is in `origin/<base branch>`, recorded by a `ticket.landed` event after its `ticket.passed`.
_Avoid_: closed (for this; a closed ticket may not have landed)

**first line**:
The person-readable opening of an event comment, or a recognized outcome marker on a draft, review or child record. It is distinct from the machine payload at the end of an event.

**`worker.started`, `reviewer.started`**:
The event (a started event) `dispatch.sh start` posts once the runner has started the session, naming its runner, the runner's id for it, its worktree, branch, base commit and base branch (`into`). It is the only record of the session, and it begins a hold.

**`ticket.claimed`, `ticket.refused`**:
The two events `--preflight` posts: `ticket.claimed` after the claim, beginning a hold, or `ticket.refused` with the first refusal's reason.

**`ticket.passed`, `ticket.returned`**:
The events `--closeout` posts a closing comment as, each after the tracker change it announces: `ticket.passed` for an accepted `ALL MET` closing-comment draft once the ticket is closed, `ticket.returned` for a `HANDOFF REQUIRED` closing-comment draft once the ticket is handed back.

**`ticket.released`**:
The event that follows a claim given back by `land`, `suspend` or `advance`'s `RELEASE` line. It ends every hold on the ticket.

**`ticket.landed`**:
The event `advance` or `land` posts once a ticket's passed commit is pushed to `origin/<base branch>`. It is what lets the tickets it blocks start.

**`ticket.regressed`**:
The event `reverify` posts on a landed ticket whose criteria went red on the base branch, in the pass that reopens it for triage. It takes back the pass and the landing.

**`ticket.recovered`**:
The event `reverify` posts on a reopened ticket whose criteria are all met again, in the pass that closes it. It puts the pass and the landing back.

**`ticket.bounced`**:
The event recording a failed landing caused by merge conflict or repository checks. Its kind of retry is recorded on the tracker, with the first open-night bounce retryable automatically and a later bounce awaiting triage.

**`worker.resumed`, `worker.retracted`, `worker.replaced`, `worker.lost`**:
The events about one worker session after its start, each naming it by runner and session: `resume`, `retract` and a replacing `start` post the first three, and the **watchdog** posts `worker.lost` once the session's runner says it has stopped.

**`reviewer.reported`**:
The event `verify-ticket.py <n> --review <file>` posts carrying the **review report**. The relay turns it into the worker's wake.

**`reviewer.lost`**:
The event the **watchdog** posts for a reviewer that stopped before its report landed. The relay wakes the worker on it.

**`spec.opened`, `spec.closed`, `spec.retroed`**:
The events of a night on its spec: `spec.opened` from `open` (the orchestrator, the base branch and the project branch), `spec.closed` from `summary` (the `NIGHT SUMMARY`), and `spec.retroed` from the retro. Distinct from `spec.merged`, which `finish` posts.

**`spec.suspended`**:
The event `suspend` posts on the spec and on every ticket still in the agent queue, first line `NIGHT SUSPENDED #<spec>`. It ends every hold on the ticket.

**`child.opened`, `child.closed`**:
The events that record a ticket's children on the ticket: `--sub-issue` posts `child.opened` with the child's number and kind, and `route` posts `child.closed` with where a `finding` went.

**child kind**:
The family `finding`, `contract`, `deferred`, `decision` and `fault`, distinguishing why a ticket's unfinished work needs another authority or scope. A child is distinct from an implementation ticket produced when the owner approves that work.

**the kind questions**:
The ordered classification of a ticket's cut-out work as fault, contract, decision, finding or deferred in verify-ticket's sub-issues reference. It is distinct from to-tickets' five questions for criterion classification.

**`ticket.checked`**:
The event for one ticket-criterion run on one commit. Its run and stage identify baseline, worker, final or landed-result verification without making them interchangeable.

**`worker.touched`**:
The event `--touched` posts on an open sibling ticket whose `## Owns` covers a file this ticket changed outside its own Owns.

**`worker.decided`**:
The worker's DECISIONS event recording autonomous decisions and edits outside Owns for independent Spec review.

**review report**:
The reviewer's one report on the ticket, carried by `reviewer.reported`: first line `REVIEW <base-commit>..<HEAD commit>`, then the axis reports, the refuted findings, and the in-ticket and out-of-ticket findings.

**closing comment**:
The worker's final account, posted by verified closeout as a pass or hand-back event. It records criterion outcomes, review resolutions, outside-scope edits and decisions.

**`ALL MET`**:
The closing comment's first line when every criterion is met, which `--closeout` posts as `ticket.passed`. gate-check's summary line opens with the same words.

**`HANDOFF REQUIRED`**:
The closing comment's first line when a criterion is unmet or abandoned as `failed` or `stuck`, which `--closeout` posts as `ticket.returned` while it hands the ticket back.

**`Review findings:`, `skipped:`, `Sub-issues opened:`, `Branch: … Commit: … PR: …`, `Counts:`**:
The fixed-line family accounting for review resolutions, unavailable proof, child issues and delivery identity in a closing-comment draft. Its format is owned by verify-ticket rather than counted independently by the worker.

**`DRAFT:`, `CLOSEOUT OK:`, `CLOSED:`, `HANDED BACK:`, `TOUCHED:`, `DECISIONS: posted on #`, `REVIEW: posted on #`, `LINT OK`, `LINT FINDINGS:`**:
The verify-ticket result-marker family identifying drafts, closeout outcomes, recorded reports and lint results. The command producing a marker owns its exact syntax and success conditions.

**`Outside Owns:`**:
The files the ticket's own commits changed that no `## Owns` glob covers, listed by the worker's `self` run and carried into the closing comment with the Spec axis's judgement of each.

**`NIGHT SUMMARY`**:
The first line, `NIGHT SUMMARY <date>`, of the `spec.closed` comment `summary` posts on the spec, and the account under it of how each ticket and finding of the night ended.

**`spec.merged`**:
The event `finish` posts on the spec after the accepted base branch has been merged into the project branch and pushed.

**`spec.checked`**:
The event recording a full repository check on a particular integration commit and machine. It supports reuse of the same proven result during night summary.

### Running the criteria

**ledger**:
The temporary `AC.md` file `verify-ticket.py` writes from `## Acceptance criteria` and hands to gate-check, the only format gate-check reads. It is deleted after the run.

**gate-check**:
The verify-ticket acceptance runner that executes each CHECK and evaluates its exit status and EXPECT match, including the runner-summary checks. It records the resulting criterion evidence.

**gate-lint**:
The criterion linter from unlazy, which reports problems in how criteria are written and runs no command. `--lint` runs it.

**`verify-ticket`**:
The [skill](../../../mmw-v4/skills/verify-ticket/SKILL.md) owning criterion execution, issue lint and closeout records. Work a ticket supplies the worker's task order.

### Code review

**code review**:
One independent reading of a completed diff under code-review. A ticket review returns a review report; a requested PR review returns findings without implementing fixes.

**axis**:
One dimension of a code review: Standards, Spec, Tests, or Correctness. The reviewer runs each as a subagent where the host can run one, and otherwise runs them itself in turn.

**Holds / `refuted` / Could not tell**:
The conclusion family code-review applies after checking an axis finding: supported, disproved or still unverified. A withdrawn or refuted item carries the evidence that disproves it.

**review category**:
The classification attached to an axis finding, such as a named Principle, Correctness defect or Spec kind. It is distinct from a retrospective analysis angle.

**review finding**:
An evidenced issue in a diff, sorted by code-review as in-ticket or out-of-ticket. The ticket's requirements, named spec decisions, baselines and Owns define that scope.

**Missing / Scope creep / Built wrong**:
The Spec axis's three kinds of review finding: something the ticket, its named spec section or a baseline asked for that the diff does not do (**Missing**); behaviour the diff adds that nothing asked for, most clearly something the spec's `## Out of Scope` names (**Scope creep**); and something that looks implemented but does not match what was asked (**Built wrong**).

**`reasonable` / `should not`**:
The Spec axis's judgment of a recorded worker decision. The first fills a legitimate gap; the second conflicts with the ticket, its named decisions or a baseline.

**semantic-conflict angles**:
The Spec axis's checks of combination behavior, contract consistency, migration completeness and shared-state ownership across integrated tickets. They identify changes that merge textually but conflict in behavior.

**`code-review`**:
The [skill](../../../mmw-v4/skills/code-review/SKILL.md) for independent review of a ticket or requested PR on Standards, Spec, Tests and Correctness axes. It is distinct from advisor's assessment of a decision.

**Standards, Spec, Tests and Correctness**:
The four code-review axes for applicable standards, agreed behavior and integration, test value, and concrete defects. They are independent judgments of the same diff, not four successive implementation stages.

### Claiming and handing back

**preflight**:
`verify-ticket.py <n> --preflight`, the worker's first step: the checks that the ticket may be claimed and the claim itself.

**`NOT_READY:`, `READY:`, `RESUME:`, `CARRIED:`**:
The fixed lines `--preflight` prints as it claims a ticket: `NOT_READY:` on stderr when the checkout is wrong for the claim, with a sentence saying why and what to do next (the refusal's code, `wrong-branch` or `dirty-tree`, goes into the `ticket.refused` event's `reason`), `READY:` once claimed, `RESUME: step <k> (<event>)` naming which closing step a reclaiming worker resumes at, and `CARRIED:` when the worker's own uncommitted tracked changes are found on reclaim.

**claim**:
Setting the ticket's assignee to oneself, followed by a `ticket.claimed` event. The frontier takes only unassigned tickets, so a claim keeps a second worker off the ticket.

**hand back**:
Swapping `ready-for-agent` for `needs-triage`, taking the claim off and leaving the ticket open: what `--closeout` does with a `HANDOFF REQUIRED` closing-comment draft.

**continue**:
The word the orchestrator ends a `resume` text with, telling a live worker to carry on from where it was.

### Working discipline

**code-writing rules**:
The Work a ticket instructions governing implementation and review fixes. These refer to testing methods through test-audit rather than a second copy of those methods.

**closing steps**:
The Work a ticket steps after implementation, covering integration, criteria, independent review, Audit, final run and closeout. Their order belongs to that Playbook rather than the glossary.

**final run**:
The newest worker criterion run on the final HEAD, after the last committing step and without another repair round. Closeout checks that this run covers the ticket's current criteria.

**`Audit`**:
The Work a ticket comparison of the actual result with What to build and its baselines before the final run. It is distinct from test-audit, the shared testing method.

**closeout**:
The verify-ticket operation accepting a completed closing-comment draft against current ticket evidence and repository state. It is the authority that pushes and closes a pass or hands unfinished work back.

**Work a ticket**:
The [Playbook](../../../mmw-v4/skills/mmw-mode/playbooks/work-a-ticket.md) for a dispatched worker implementing one prepared ticket through its closing comment. It is distinct from One ticket, which orchestrates an independent ticket's delivery.

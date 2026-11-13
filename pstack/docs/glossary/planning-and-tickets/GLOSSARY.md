# Planning and tickets

A spec records what the product should do. A plan describes the work across phases. An execution ticket gives an agent or a person one assignment they can complete and prove.

## Language

### The work issue and its scope

**Work issue**:
The team's GitHub issue for one repository task, from the first report through the result. A question can close with its answer and evidence. The team can link someone else's report from its work issue while the reporter keeps their original issue.
_Avoid_: ticket as a name for every GitHub issue.

**Issue template**:
The common form for intake, a published spec, a plan issue, an execution ticket, and its final result. The issue body holds the current findings, decisions, and agreed work. Comments retain new evidence and the reasons for a change of direction. Open, Update, and Split are ways [to-tickets](../../../skills/to-tickets/SKILL.md) uses the form at different points in the work.

**Type label**:
The label for the work issue's current purpose. `mmw:problem` identifies intake or investigation, `mmw:spec` a published spec, `mmw:plan` a published plan, and `mmw:ticket` an execution ticket. An issue has one type at a time and keeps its original report and evidence when its purpose changes.

**Spec**:
The record of the problem, agreed behavior, scope, and decisions that guide implementation and testing. The operator reviews it. An engineering choice the author makes while writing it is identified as "this spec's decision." A reviewed draft can supply a plan before publication.

**Spec issue**:
The work issue holding the complete published spec. Its `Problem Statement` retains the original report. A spec issue can exist before any tickets are drafted and has no queue label.

**Parent spec**:
The spec containing the agreed scope for a plan or execution tickets. The spec issue is the direct GitHub parent of the plan issue and of each **child ticket** for one assignment. The parent closes when the agreed child outcomes are complete.

**User story**:
A spec statement of what a product user wants and why. The actor in the story can be someone other than the operator commissioning the work.

**Expected result**:
A sentence in a user story that states an outcome a person can observe. The plan and the ticket that deliver the outcome preserve the sentence verbatim. A verification script can assert that same result.

**Agreed work**:
The ticket's statement of what the assignee will deliver, including the chosen approach and scope boundaries. For a human action it states what the person must do. The `Problem` field retains the observation or request that led to the assignment.

### Phases and decisions

**Multi-phase plan**:
A proposed sequence of work with the intended outcomes, approach, dependencies, and evidence for each phase. It accounts for behavior that already works and identifies what remains. The main chat gives this plan to the operator or to [to-tickets](../../../skills/to-tickets/SKILL.md) for a requested breakdown.

**Plan issue**:
The GitHub sub-issue of the spec that holds the complete checked plan. Execution tickets drawn from it share its parent and link to the plan issue for their phase or outcomes. [to-tickets](../../../skills/to-tickets/SKILL.md#plan)

**Phase**:
A part of the plan organized around a goal. `Depends on` names prerequisite results, `Build` the changes, `You see` the observable outcomes, and `Verify` the checks and evidence. A phase can yield several tickets, and one ticket can draw on several plan steps.

**Checked plan**:
The version that passed the plan's structural checks and completed its Plan-stage review. This is the text published in the plan issue. The operator's authorization determines when execution starts.

**Program checklist**:
The part of a multi-phase plan that describes how the named playbook will execute the work once authorized. A checked box records a unit of work with evidence. The per-phase sections describe the product changes.

**Review gate**:
A decision the plan reserves for the operator. For an interaction change, the plan names the screenshots and video the operator needs before merge. This condition follows the work into the affected ticket.

**Ambiguity scan**:
A fresh, read-only review of the complete draft and its sources at the Spec, Plan, or Ticket stage. One reviewer sees an entire batch of ticket drafts together and reports to the main chat.

### Assignments and dependencies

**Execution ticket**:
An assignment with its own scope, acceptance criteria, and independently verifiable result. A standalone problem with one deliverable uses the original work issue as its ticket. During authorized implementation, a code ticket supplies the scope for its corresponding [pull request](../pull-request-delivery/GLOSSARY.md). A human action or a read-only assignment can finish with evidence on the issue.
_Avoid_: PR as a synonym for the execution ticket.

**Acceptance criterion**:
A ticket checkbox pairing an action or check with its expected result. Evidence that the result occurred satisfies the criterion. An [approved prototype](../design-and-presentation/GLOSSARY.md) fixes the part of the result the operator accepted.

**Vertical slice**:
A narrow change through the layers needed to deliver one result, demonstrable on its own and small enough for a fresh agent session. The splitting rules also call this shape a *tracer bullet*.

**Prefactoring**:
A preparatory change that makes the implementation easier. A shared prerequisite can occupy its own ticket when a subsequent assignee can use and verify the result.

**Wide refactor**:
One mechanical change whose callers cannot all stay working through separate vertical slices. If the old and new forms must coexist, an **expand–contract** sequence adds the new form, migrates callers in batches, and removes the old form after the last migration. When batches need a shared integration branch, the final integration ticket supplies the combined proof.

**Direct blocker**:
A ticket that supplies a result another ticket needs before it can start. GitHub records this dependency as **Blocked by**. Two child tickets can share a parent or a phase and still proceed independently.

**Queue label**:
The single label indicating who can act next. `ready-for-agent` identifies agent work, `ready-for-human` an action for a person, and `needs-triage` a pending operator decision. A problem can also await triage. Spec and plan issues have no queue label.

**Ticket frontier**:
The set of open execution tickets whose direct blockers are complete. The execution playbook receives the `ready-for-agent` tickets on this frontier when the operator authorizes work.
_Avoid_: frontier alone when the [merge frontier](../pull-request-delivery/GLOSSARY.md) could also be meant.

**Ticket handoff**:
The record of who takes an assignment and what action comes next. Once a code ticket has an open PR, `Handoff` records the actual PR URL. The closing `Result` records what landed or was verified and its evidence. When the requested outcome is a merge, a verified stack handed to the operator is still awaiting merge.

## Sources

The spec fields and issue types come from [to-spec](../../../skills/to-spec/SKILL.md) and [to-tickets](../../../skills/to-tickets/SKILL.md). Phase structure, the three review stages, and the ticket relationships are defined in the [multi-phase plan](../../../skills/poteto-mode/playbooks/multi-phase-plan.md), [ambiguity-scan](../../../skills/ambiguity-scan/SKILL.md), and the [ticket splitting rules](../../../skills/to-tickets/references/split.md).

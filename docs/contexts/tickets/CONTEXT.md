# Tickets

The written half of the landing pipeline: what a spec and a ticket are, the sections each one carries, how a batch is published, read back and linted, and which kinds and statuses an issue carries while it waits. Every other context reads what this one wrote.

## Language

### Worker grades

**worker grade**:
The worker-role selection on an executable ticket, represented by its worker label and resolved through models.json. The selected row determines how that worker session starts.

**`junior-worker`**:
The default worker grade (`DEFAULT_WORKER` in `dispatch.sh`).

**`senior-worker`**:
The worker grade for a ticket where a mistake would not show on the day it is written: money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default.

### Specs

**issue**:
A GitHub issue, the tracker's unit: a map, a spec, a ticket, a ticket's child, a decision ticket, or an issue from outside that triage handles.

**spec**:
The issue labelled `mmw:spec` recording settled product, implementation and testing decisions for a coordinated batch of tickets. It is a container rather than an executable ticket.
_Avoid_: 规格

**`## Implementation Decisions`**:
The spec section of decisions made, in numbered subsections `### 1.` … that a ticket's `## Parent` points at. Each decision names its source, or carries the marker "this spec's decision" when no source settles it.

**`## Testing Decisions`**:
The spec section that says where a test observes the result, the seam and what is real on each side of it, each test layer's directory and precedent, how a test arrives at each state, and the commands to run before committing. A ticket's `## Seam` points into it, and its `CHECK:` and `EXPECT:` come from the precedent it names.

**How a test arrives at a state**:
The Testing Decisions item naming, per test layer, what a test can and cannot write to reach a state, and the mechanism that reaches what a test cannot write through the seam. A ticket's `## Seam` names the mechanism it uses, and a state it names with no mechanism yet becomes a `reach` ticket.

**`## Out of Scope`**:
The spec section of what is not being done, read by the worker and the Spec axis. A wayfinder map's Out of scope section is a different heading, which the spec's Out of Scope links rather than copies.

**`## Sources`**:
The spec section linking the first-hand material the spec was built from, one line per fixed kind and `none` where a kind is empty. A ticket's `## Read first` picks from it.

**`## Further Notes`**:
The spec section holding the spec-division bookkeeping when step 1 divides a reference into several specs and the reference is not a wayfinder map: one line per spec, naming it, what it covers, its position in the order and its link once published.

**spec division**:
The to-spec judgment that a reference contains independently deliverable parts needing different seams. Their one-way dependency order is recorded on the map or first spec.

**revising a spec**:
Changing a published spec in place through to-spec's revision entry. Affected unlanded tickets follow that revision; work already landed requires a correction ticket.

**seam**:
The location where a module's interface can be exercised or its adapter substituted, in the sense of Michael Feathers and codebase-design. Testing Decisions names the observation point and the real or substituted sides of that interface.

**precedent**:
The similar existing test `## Testing Decisions` names per test layer. A ticket's `## Seam` reaches it through the layer it names, and the ticket writer copies its invocation into `CHECK:` and its success line into `EXPECT:`.

**test layer**:
The layer a feature's tests land in, named in `## Testing Decisions` with its directory and precedent.

**`## Problem Statement`, `## Solution`, `## User Stories`**:
The spec sections recording the user's problem, the intended outcome and the situations it must serve. Their decisions are carried into the Implementation Decisions read by workers.

### Tickets

**ticket**:
An issue in the **ticket format**, labelled `mmw:ticket`, that a worker takes from claim to close. A spec ticket is its native sub-issue; an independent ticket has no spec.
_Avoid_: 工单

**batch**:
The coordinated implementation tickets under one spec, published and checked as one dependency graph. It is distinct from a brief batch and a backlog review batch.

**vertical slice**:
A ticket's cut: a narrow but complete path through every layer (schema, API, UI, tests), demoable or verifiable on its own (a tracer bullet), as against a horizontal slice of one layer.

**wide refactor**:
The exception to vertical slicing: one mechanical change (renaming a column, retyping a shared symbol) whose blast radius fans across the whole codebase, so a single edit breaks thousands of call sites and no vertical slice can land green. Sequenced as expand-contract instead.

**integrate-and-verify ticket**:
The final ticket of an expand-contract sequence whose migrate batches cannot each stay green alone: they share an integration branch and all block this ticket, where green is promised.

**ticket format**:
The shared definition of ticket sections and criterion classification in to-tickets' [ticket-format.md](../../../mmw-v4/skills/to-tickets/references/ticket-format.md). Independent and batch tickets use this format with the decision sources available at their actual scope.

**`## Parent`**:
The ticket section identifying its parent spec and numbered Implementation Decisions subsections, or `None` for an independent ticket.

**`## What to build`**:
The end-to-end behaviour the ticket makes work, from the end user's point of view, in numbered points each with the test that decides it.

**`## Read first`**:
The ticket's required sources, including decision baselines and worker or reviewer method entries. A spec ticket selects the sources of its named spec subsections; an independent ticket names its prepared sources directly.

**baseline**:
A settled conclusion under Read first, such as a prototype verdict, an approved design or an ADR decision. It is an agreed contract for the worker, with discrepancies raised through a `contract` child.

**`## Seam`**:
The ticket section naming where the result is verified and how the test reaches the required states. A spec ticket points into Testing Decisions; an independent ticket records the relevant layer, directory and precedent locally.

**`## Owns`**:
The ticket's declared write scope, including its tests and the files needed to put the change in service. A necessary edit outside that scope is accounted for by the worker rather than silently treated as owned.

**`## Acceptance criteria`**:
The ticket section holding the acceptance criteria. A `ready-for-human` ticket has none.

**Blocked by**:
The tickets one ticket waits on. On an agent ticket they are its blocking edges on the tracker alone, which the breakdown put to the owner lists and the to-tickets skill's batch entry calls a **Blocked by** edge; on a `ready-for-human` ticket, the body item naming the ticket that produces the thing it waits on.

**independent ticket**:
An implementation ticket outside any spec, with `None` under Parent. Its own prepared scope and verification sources are sufficient for execution by One ticket.

**spec ticket**:
An implementation ticket whose native parent is a spec and whose Parent section selects that spec's relevant decisions. Its batch is executed by Run a night even when it has only one ticket.

**`## Problem`**:
The original problem or goal recorded before preparation, including its initial Playbook line when present. Later routing can select a current component without rewriting that historical statement.

**`Playbook:`**:
The preparation record's line naming the workflow that originally took the problem. It is historical context on an existing issue, distinct from an instruction to open a retired Playbook.

### Acceptance criteria

**acceptance criterion**:
One command-decided standard on a ticket, expressed by its AC number, CHECK, EXPECT and EVIDENCE lines. It differs from a code-review judgment or a human reaction.

**`CHECK:`**:
The shell command that decides a criterion, run in its own shell at the repository root with no agent in between. A multi-line command is a **fenced block** directly under it.

**`EXPECT:`**:
The success-only marker a criterion's CHECK output must match. Native runner patterns belong to verify-ticket's runner-summaries.json; pytest acceptance includes an ordinary passing case rather than only xfail or xpass results.

**`EVIDENCE:`**:
The criterion's recorded run evidence, initially `pending`, with a passing run fingerprinting the checked definition. The checkbox records whether that criterion is met.

**`TIMEOUT:`**:
The optional criterion line `TIMEOUT: <seconds>` raising how long its `CHECK:` may run. `verify-ticket.py` reads it and keeps it out of the ledger.

**fenced block**:
The only way to write a multi-line `CHECK:`: a code fence directly under it holds the command, and every other fence in the ticket is skipped.

**the five questions**:
The ordered questions the ticket writer asks of anything there is to say about the work, deciding whether it becomes an acceptance criterion, a code-review judgement, a `reaction` ticket, a `reach` ticket or a choice put to the user.

**`met`, `unmet`, `abandoned`**:
The criterion-state family used by acceptance and closeout. A met criterion has passing evidence, an abandoned criterion has an ABANDON record, and an unmet criterion has neither accepted outcome.

**round**:
One pass of criterion repair and rerun, or of in-ticket code-review fixes. It differs from a hillclimb Attempt or a prototype experiment round.

**`ABANDON:`**:
The criterion record for work the worker cannot complete, with kind `failed`, `stuck` or `decision`. The kind distinguishes an unsuccessful repair, unavailable execution or a person's unresolved choice.

### The graph

**blocking edge**:
The tracker's native issue dependency between two tickets, the copy every script reads. A blocker is a ticket that must land before the ticket it blocks is started.
_Avoid_: blocking link; native issue dependencies as this concept's name (it names GitHub's mechanism)

**frontier**:
The implementation tickets currently eligible for dispatch in a spec batch, computed from tracker status, claims and blocking edges. It is distinct from a map frontier of decision tickets.

**sub-issue**:
The tracker's native parent–child relation. A map's children are its decision tickets and specs, a spec's direct children are its tickets, and a ticket's direct children are the issues a worker opens under it with `--sub-issue <kind>`.

### Labels and statuses

**label**:
A tracker label identifying an issue's kind, status or worker grade. Those sets express different facts, while wayfinder decision types and external issue categories have their own labels.

**kind**:
The MMW issue-type label family distinguishing maps, specs, implementation tickets, children, lessons and preparation problems. It is independent of status and worker grade; wayfinder decision tickets use their own type labels.

**status**:
The tracker state identifying who owes the next action: machine processing, owner triage, agent work or human work. Open and closed state and labels are distinct from issue kind, worker grade and criterion outcomes.

**`needs-triage`**:
The status awaiting the owner's decision. Only the owner lets an issue leave it, and deferral has no expiry.

**`mmw:lesson`**:
The kind label for a registered way-of-working problem whose evidence can be assessed by Retrospective.

**`mmw:problem`**:
The kind label for a preparation problem or product problem outside a ticket. It preserves the problem before execution Go turns the work into an implementation ticket.

**`ready-for-agent`**:
The status ready for an agent, which the ticket format puts on every agent ticket beside a worker-grade label. It never goes on a spec.

**`ready-for-human`**:
The status for one action or judgment only a person can supply, classified as reaction or reach. Its record uses the five things rather than agent acceptance criteria and a worker grade.

**`reaction`**:
The `ready-for-human` kind where the thing asserted is a person's reaction, so the person is the measuring instrument.

**`reach`**:
The `ready-for-human` kind where a machine would decide it if it could get to the thing: a device, a credential, a real environment, or a mechanism no ticket owns.

**the five things**:
The fixed, minimal content of a `ready-for-human` ticket, the whole of it: **Parent**, **Which kind**, **What to look at**, **What makes it right**, **Blocked by**.

**retiring line**:
A reach ticket's statement of what access or mechanism would make that human-only ticket unnecessary.

**`wontfix`**:
The owner's rejection of work, carried on an issue closed as not planned.

**`bug`, `enhancement`**:
The two category roles, for work arriving from outside; a ticket this repository plans for itself carries neither.

**decision ticket**:
A native child of a wayfinder map holding one precisely stated decision or investigation, classified by a `wayfinder:<type>` label. Its resolution comment can become an implementation baseline.

**map**:
The wayfinder index issue labelled `wayfinder:map` and `mmw:map`, with decision tickets and resulting specs as native children. Its body records the destination and decision index; detailed answers remain on the decision tickets.

### Publishing and linting

**ambiguity scan**:
The read-only analysis of a drafted spec batch that identifies unresolved interpretations before its breakdown reaches the owner. Its questions feed the batch's Choices rather than implementation guesses.

**Choices**:
The owner-facing alternatives and recommendations attached to each agent ticket in a proposed batch breakdown. Resolved choices become ticket requirements or revised spec decisions.

**ticket draft**:
A local prospective ticket with publication headers and its body, linted before it receives a tracker identity. Draft names identify dependencies within the unpublished batch.

**publish**:
Creation of a prepared spec or approved batch as tracker issues through verify-ticket. Published labels, parent relationships and blocking edges are checked by reading the tracker back.

**lint**:
The verify-ticket check of a ticket, spec batch or unpublished drafts, combining criterion lint with issue-graph and label checks. It does not execute the implementation.

**lint rule ID**:
The bracketed identifier naming a verify-ticket lint finding's check. It identifies a diagnostic rule, not a retrospective lesson or Nowledge Mem Rule.

**`ERROR`, `WARN`**:
The two lint levels. Only an `ERROR` affects `--lint`'s exit code.

**triage**:
The owner's selection or disposition of pending work, represented by the needs-triage queue. It is distinct from preparation and from execution Go; no active MMW skill is named triage.

### Writing components

**`to-spec`**:
The [skill](../../../mmw-v4/skills/to-spec/SKILL.md) for creating a spec from settled decisions or revising the published spec and affected tickets. It returns the requested record without automatically decomposing or executing it.

**`to-tickets`**:
The [skill](../../../mmw-v4/skills/to-tickets/SKILL.md) for opening a preparation record, writing one independent ticket or decomposing a spec into a batch. Independent and batch writers share its ticket format and criterion classification.

# Tickets

The written half of the landing pipeline: what a spec and a ticket are, the sections each one carries, how a batch is published, read back and linted, and which kinds and statuses an issue carries while it waits. Every other context reads what this one wrote.

## Language

### Worker grades

**worker grade**:
Which of the two workers a ticket goes to: at once a ticket label and a `models.json` row. `dispatch.sh` reads the label afresh each time the ticket is started.

**`junior-worker`**:
The default worker grade (`DEFAULT_WORKER` in `dispatch.sh`).

**`senior-worker`**:
The worker grade for a ticket where a mistake would not show on the day it is written: money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default.

### Specs

**issue**:
A GitHub issue, the tracker's unit: a map, a spec, a ticket, a ticket's child, a decision ticket, or an issue from outside that triage handles.

**spec**:
A container for a batch of tickets, not a piece of work: an issue labelled `mmw:spec`, in the shape of **The template** of the `to-spec` skill's create entry, which writes it and publishes it with `verify-ticket.py --publish --spec-body`. A spec published from a wayfinder map is a native sub-issue of that map.
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
The step-1 judgement of whether what a reference leads to is one spec or several, by whether the decisions share a **seam** and whether the dependency between parts runs one way. The division is written to the map's `## Specs` section, or, with no map, the first spec's `## Further Notes`.

**revising a spec**:
Changing a section of an already-published spec in place rather than publishing a new issue, so no ticket's `## Parent` is left pointing at a wrong number. What changed and why goes in one comment on the spec; a landed ticket the new text no longer matches gets a correction ticket.

**seam**:
The place where a module's interface lives: where a test observes behaviour without reaching inside, and where what is behind the interface can be replaced (a stub, an adapter). `## Testing Decisions` names it and a ticket's `## Seam` points at it by that name.

**precedent**:
The similar existing test `## Testing Decisions` names per test layer. A ticket's `## Seam` reaches it through the layer it names, and the ticket writer copies its invocation into `CHECK:` and its success line into `EXPECT:`.

**test layer**:
The layer a feature's tests land in, named in `## Testing Decisions` with its directory and precedent.

### Tickets

**ticket**:
An issue in the **ticket format**, labelled `mmw:ticket`, that a worker takes from claim to close. A spec ticket is its native sub-issue; an independent ticket has no spec.
_Avoid_: 工单

**batch**:
The tickets under one spec, published together: `--lint` checks them as one graph of blocking edges, and the closing pass re-runs every one of their criteria on the base branch. Distinct from a migrate batch of a **wide refactor**, one step of an expand-contract sequence.

**vertical slice**:
A ticket's cut: a narrow but complete path through every layer (schema, API, UI, tests), demoable or verifiable on its own (a tracer bullet), as against a horizontal slice of one layer.

**wide refactor**:
The exception to vertical slicing: one mechanical change (renaming a column, retyping a shared symbol) whose blast radius fans across the whole codebase, so a single edit breaks thousands of call sites and no vertical slice can land green. Sequenced as expand-contract instead.

**integrate-and-verify ticket**:
The final ticket of an expand-contract sequence whose migrate batches cannot each stay green alone: they share an integration branch and all block this ticket, where green is promised.

**ticket format**:
The `to-tickets` skill's `references/ticket-format.md`: a ticket's sections, `## Parent`, `## What to build`, `## Read first`, `## Seam`, `## Owns`, `## Acceptance criteria`, how each criterion is written, and its labels. `verify-ticket.py` runs what it describes, so independent and batch writers use the same format, with decisions recorded at the scope each ticket actually has.

**`## Parent`**:
The ticket section routing it to its spec: `#<spec>, Implementation Decisions section <n>`, or `None` for an independent ticket.

**`## What to build`**:
The end-to-end behaviour the ticket makes work, from the end user's point of view, in numbered points each with the test that decides it.

**`## Read first`**:
The sources the ticket's spec subsections cite, each read to its conclusion before work; an item that records a settled conclusion is marked as a **baseline**.

**baseline**:
An item under `## Read first` that records a settled conclusion — a decision ticket's resolution, an ADR's decision, a research answer's file in its question's directory linked by the resolution comment, a prototype's chosen artifact and verdict comment — which the worker follows rather than consults. In the configuration-management sense (IEEE Std 610.12), it is a reviewed and agreed item that further work builds on and that changes only through change control, which here is a `contract` child.

**`## Seam`**:
The ticket section saying where the ticket is verified, as pointers into the spec's `## Testing Decisions`: the test layer it uses, the test file it adds, and the mechanism by which a test arrives at the state.

**`## Owns`**:
The repository-relative paths the ticket may write, one per line, including its test files and any file it must edit to put what it creates in service. Everything outside is read-only for the ticket.

**`## Acceptance criteria`**:
The ticket section holding the acceptance criteria. A `ready-for-human` ticket has none.

**Blocked by**:
The tickets one ticket waits on. On an agent ticket they are its blocking edges on the tracker alone, which the breakdown put to the owner lists and the to-tickets skill's batch entry calls a **Blocked by** edge; on a `ready-for-human` ticket, the body item naming the ticket that produces the thing it waits on.

### Acceptance criteria

**acceptance criterion**:
One standard on a ticket (a criterion), decided by one command: the lines `- [ ] AC<n>:`, `CHECK:`, `EXPECT:` and `EVIDENCE:`, with `TIMEOUT:` optional. A judgement no command decides is not one.

**`CHECK:`**:
The shell command that decides a criterion, run in its own shell at the repository root with no agent in between. A multi-line command is a **fenced block** directly under it.

**`EXPECT:`**:
The string, or `/…/flags` regex, the `CHECK:` output must contain: a **success-only marker**, the line the precedent prints only when it passed. For a `CHECK:` stage that runs pytest or Vitest it is that runner's standard pattern, whose one home is the verify-ticket skill's `scripts/runner-summaries.json`.

**`EVIDENCE:`**:
The criterion line gate-check writes: `pending` until the criterion runs, then one line of fact about the run, which on a pass fingerprints the definition that passed. The checkbox, not this line, decides whether the criterion is met.

**`TIMEOUT:`**:
The optional criterion line `TIMEOUT: <seconds>` raising how long its `CHECK:` may run. `verify-ticket.py` reads it and keeps it out of the ledger.

**fenced block**:
The only way to write a multi-line `CHECK:`: a code fence directly under it holds the command, and every other fence in the ticket is skipped.

**the five questions**:
The ordered questions the ticket writer asks of anything there is to say about the work, deciding whether it becomes an acceptance criterion, a code-review judgement, a `reaction` ticket, a `reach` ticket or a choice put to the user.

**`met`, `unmet`, `abandoned`**:
The three states of a criterion: met is ticked with real evidence, abandoned carries an `ABANDON:` line, and unmet is every other criterion.

**round**:
One pass that fixes and re-runs one criterion, or that fixes the in-ticket findings of a code review.

**`ABANDON:`**:
The line `ABANDON: AC<n> <kind> <reason>` a worker writes under a criterion it gives up on, of kind `failed`, `stuck` or `decision`. A `failed` or `stuck` one makes the closing comment `HANDOFF REQUIRED`.

### The graph

**blocking edge**:
The tracker's native issue dependency between two tickets, the copy every script reads. A blocker is a ticket that must land before the ticket it blocks is started.
_Avoid_: blocking link; native issue dependencies as this concept's name (it names GitHub's mechanism)

**frontier**:
The tickets `advance` may start now, as `status.py` computes them from the tracker. Distinct from wayfinder's frontier, a map's open, unblocked, unclaimed children.

**sub-issue**:
The tracker's native parent–child relation. A map's children are its decision tickets and specs, a spec's direct children are its tickets, and a ticket's direct children are the issues a worker opens under it with `--sub-issue <kind>`.

### Labels and statuses

**label**:
A GitHub label on an issue. This repository's own labels come from three sets that never stand in for each other: a **kind** says what the issue is, a **status** says who owes the next step, and a worker-grade label says which worker starts it. Triage's `bug` and `enhancement` and wayfinder's `wayfinder:<type>` labels sit outside the three.

**kind**:
Exactly one of `mmw:map`, `mmw:spec`, `mmw:ticket`, `mmw:child`, `mmw:lesson`, `mmw:problem` on each MMW issue, saying what it is. A `wayfinder:<type>` decision ticket carries none. A kind puts an issue in no status.

**status**:
Who owes the next step. An open issue without a status label awaits machine processing. `needs-triage` awaits the owner's decision. `ready-for-agent` with one worker grade, or `ready-for-human`, means ready for work, with an assignee when in progress. Closed ends the work, with `wontfix` for the owner's rejection. Maps and specs use only open and closed.

**triage role**:
A canonical label name the upstream skills use: status roles, whose repository label strings are defined by `LABELS` in the verify-ticket script, and two category roles, `bug` and `enhancement`, used as named.

**`needs-triage`**:
The status awaiting the owner's decision. Only the owner lets an issue leave it, and deferral has no expiry.

**`mmw:lesson`**:
The kind of a problem in how work is done, awaiting retrospective processing.

**`mmw:problem`**:
The kind of a product problem outside any ticket, or a playbook's plan not yet approved. It becomes `mmw:ticket` on the owner's Go.

**`ready-for-agent`**:
The status ready for an agent, which the ticket format puts on every agent ticket beside a worker-grade label. It never goes on a spec.

**`ready-for-human`**:
The label of a person ticket: a ticket holding one thing only a person can do, of kind `reaction` or `reach`. Such a ticket holds only **the five things**, with no Seam, Owns, criteria or worker grade.

**`reaction`**:
The `ready-for-human` kind where the thing asserted is a person's reaction, so the person is the measuring instrument.

**`reach`**:
The `ready-for-human` kind where a machine would decide it if it could get to the thing: a device, a credential, a real environment, or a mechanism no ticket owns.

**the five things**:
The fixed, minimal content of a `ready-for-human` ticket, the whole of it: **Parent**, **Which kind**, **What to look at**, **What makes it right**, **Blocked by**.

**retiring line**:
The line a `reach` ticket adds naming what would retire it, that is, make the ticket no longer needed: a test account, a spare device, a CI runner, or a mechanism under **How a test arrives at a state** nobody owns yet.

**`wontfix`**:
The owner's rejection of work, carried on an issue closed as not planned.

**`bug`, `enhancement`**:
The two category roles, for work arriving from outside; a ticket this repository plans for itself carries neither.

**`.out-of-scope/`**:
The directory of one-file-per-concept records of enhancement requests rejected as `wontfix`, read during triage for institutional memory and to catch a repeat request before it is re-litigated; a request closed as already implemented is a different outcome, with no file here.

**decision ticket**:
A child issue of a wayfinder map holding one question whose resolution is a decision, typed by a `wayfinder:<type>` label. It carries no status label and is not triaged. Its resolution comment is a baseline source.

**map**:
Wayfinder's single issue labelled `wayfinder:map` and `mmw:map`, the index of an effort too large for one session. Its children are decision tickets and the specs published from it.

**agent brief**:
The durable record the triage skill writes of what an evaluation established: an investigation record, not a work order. The `Write a spec` playbook reads it as one of a spec's sources.

### Publishing and linting

**ambiguity scan**:
The read-only pass over a spec and its drafted tickets, run by a subagent at step 6 of the `Cut tickets` playbook, that feeds questions into each ticket's **Choices** before the breakdown is shown to the owner.

**Choices**:
The line the breakdown put to the owner at step 6 of the `Cut tickets` playbook shows for each ticket an agent works: every choice the fifth of **the five questions** sent there and every question the **ambiguity scan** returned, each with its options and the one the ticket writer would take. An answered choice is written into the ticket's `## What to build`, or back into the spec when it changes a decision there.

**ticket draft**:
An approved ticket written to a local file, `<draft name>.md`, in the directory `--lint --drafts <dir>` checks and `--publish --drafts <dir>` later creates as an issue: the header lines `TITLE:`, `LABELS:` and `BLOCKED BY:`, then `---`, then the body. The file's name, standing in for the issue number it does not have yet, is what `BLOCKED BY:` and the lint use to reference it.

**publish**:
`verify-ticket.py --publish`: creating the spec (`--spec-body`) or a batch's tickets (`<spec> --drafts <dir>`) as GitHub issues, each ticket a native sub-issue of its spec with its labels and blocking edges, ending by linting the published spec. The batch is read back from that lint, which alone sees the tracker's labels, sub-issues and edges, before it is reported as published.

**lint**:
`verify-ticket.py <n> --lint`: gate-lint plus the ticket-graph and worker-label checks, run on one ticket, on a spec's batch, or on the batch's drafts before publishing.

**lint rule ID**:
The string in `[brackets]` at the end of a lint finding's line, naming the check that reported it, as ESLint's and SARIF's `ruleId` does: a cycle in the batch's blocking edges, a worker-grade or kind label out of place, a weak `EXPECT:`, and others. Always qualified: `retro`'s Rule id names a Nowledge Mem Rule.

**`ERROR`, `WARN`**:
The two lint levels. Only an `ERROR` affects `--lint`'s exit code.

**triage**:
The skill that judges an issue waiting in `needs-triage` and recommends one of three outcomes: `ready-for-agent`, `ready-for-human`, `wontfix`.

# Tickets

The written half of the landing pipeline: what a spec and a ticket are, the sections each one carries, how a batch is published, read back and linted, and which labels and queues an issue carries while it waits. Every other context reads what this one wrote.

## Language

### Worker grades

**worker grade**:
Which of the two workers a ticket goes to: at once a ticket label and a `models.json` row. `dispatch.sh` reads the label afresh each time the ticket is started.
_Home_: `docs/agents/issue-tracker.md`, `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`junior-worker`**:
The default worker grade (`DEFAULT_WORKER` in `dispatch.sh`).
_Home_: `mmw-v2/skills/dispatch/scripts/dispatch.sh`

**`senior-worker`**:
The worker grade for a ticket where a mistake would not show on the day it is written: money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

### Specs

**issue**:
A GitHub issue, the tracker's unit: a map, a spec, a ticket, a ticket's child, a decision ticket, or an issue from outside that triage handles.
_Home_: `docs/agents/issue-tracker.md`

**spec**:
A container for a batch of tickets, not a piece of work: an issue labelled `mmw:spec`, in the `<spec-template>` shape, that the `to-spec` skill writes and publishes. A spec published from a wayfinder map is a native sub-issue of that map.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Implementation Decisions`**:
The spec section of decisions made, in numbered subsections `### 1.` … that a ticket's `## Parent` points at. Each decision names its source, or carries the marker "this spec's decision" when no source settles it.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**API contract**:
The Implementation Decisions subsection an effort with a screen contract always has, one entry per operation the screen contract's `calls` column names — its request fields, response fields and failure cases — which a new project's OpenAPI document starts from.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**cross-component composition**:
The Implementation Decisions subsection an effort with a screen contract always has, one entry per **cross-component row**, naming the request fields that row's action carries and the state the other region enters.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**visual acceptance**:
The Implementation Decisions paragraph, written only with a screen contract, stating that appearance is decided by **element parity**, citing the screen contract's pages (`App · ` pages included), with each design page's `mount` as the story page id.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Testing Decisions`**:
The spec section that says where a test observes the result, the seam and what is real on each side of it, each test layer's directory and precedent, how a test arrives at each state, and the commands to run before committing. A ticket's `## Seam`, `CHECK:` and `EXPECT:` are derived from it.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**How a test arrives at a state**:
The Testing Decisions item naming, per test layer, what a test can and cannot write to reach a state, and the mechanism that reaches what a test cannot write through the seam. A ticket's `## Seam` derives from it, and a state it names with no mechanism yet becomes a `reach` ticket.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**Critical flows**:
The bullet of `## Testing Decisions`, written only in a spec with a screen contract, naming, one line each, the flows whose failure costs most (money, sign-in, a submit chain) with the directory under `.mmw/journeys/` each one runs from and the Implementation Decisions section numbers it involves, which `--lint` reads to decide which journeys need `--break`.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Out of Scope`**:
The spec section of what is not being done, read by the worker and the Spec axis. A wayfinder map's Out of scope section is a different heading, carried into the spec.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Sources`**:
The spec section linking the first-hand material the spec was built from, one line per fixed kind and `none` where a kind is empty. A ticket's `## Read first` picks from it.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Further Notes`**:
The spec section holding the spec-division bookkeeping when step 1 divides a reference into several specs and the reference is not a wayfinder map: one line per spec, naming it, what it covers, its position in the order and its link once published.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**spec division**:
The step-1 judgement of whether what a reference leads to is one spec or several, by whether the decisions share a **seam** and whether the dependency between parts runs one way. The division is written to the map's `## Specs` section, or, with no map, the first spec's `## Further Notes`.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`, `mmw-v2/upstream/skills/engineering/to-spec/references/several-specs.md`

**revising a spec**:
Changing a section of an already-published spec in place rather than publishing a new issue, so no ticket's `## Parent` is left pointing at a wrong number. What changed and why goes in one comment on the spec; a landed ticket the new text no longer matches gets a correction ticket.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/references/revising-a-spec.md`

**seam**:
The place where a module's interface lives: where a test observes behaviour without reaching inside, and where what is behind the interface can be replaced (a stub, an adapter). `## Testing Decisions` names it and a ticket copies it into `## Seam`.
_Home_: `mmw-v2/upstream/skills/engineering/codebase-design/SKILL.md`, `mmw-v2/upstream/skills/engineering/tdd/SKILL.md`

**precedent**:
The similar existing test `## Testing Decisions` names per test layer. The ticket copies it into `## Seam`, and the ticket writer copies its invocation into `CHECK:` and its success line into `EXPECT:`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**test layer**:
The layer a feature's tests land in, named in `## Testing Decisions` with its directory and precedent.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

### Tickets

**ticket**:
An issue that is a native sub-issue of its spec, in the `<issue-template>` shape and labelled `mmw:ticket`: one vertical slice a worker takes from claim to close.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**batch**:
The tickets under one spec, published together: `--lint` checks them as one graph of blocking edges, and the closing pass re-runs every one of their criteria on the base branch. Distinct from a migrate batch of a **wide refactor**, one step of an expand-contract sequence.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**vertical slice**:
A ticket's cut: a narrow but complete path through every layer (schema, API, UI, tests), demoable or verifiable on its own (a tracer bullet), as against a horizontal slice of one layer.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**wide refactor**:
The exception to vertical slicing: one mechanical change (renaming a column, retyping a shared symbol) whose blast radius fans across the whole codebase, so a single edit breaks thousands of call sites and no vertical slice can land green. Sequenced as expand-contract instead.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**integrate-and-verify ticket**:
The final ticket of an expand-contract sequence whose migrate batches cannot each stay green alone: they share an integration branch and all block this ticket, where green is promised.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**prefactor ticket**:
The ticket cut ahead of several tickets that would otherwise all edit the same registration files: it owns those files and lands in one pass the entries they need, each naming a placeholder the ticket behind it fills, so each of those tickets is blocked by it alone. Where the spec has a screen contract, it is also the **contract ticket**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**design-system ticket**:
The ticket that copies a design system's variables, fonts and part stylesheets from the design package's `_ds/` into the product, cut when the product lacks them and ahead of the **contract ticket**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**contract ticket**:
The ticket that lands or completes `.mmw/` so later tickets have a precedent to copy. Distinct from a **component page ticket**, which builds the product code of design pages, and from a **design-system ticket**, which does not depend on `.mmw/`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**page ticket**:
A ticket whose **Read first** carries a `screen-contract.yaml rows:` line: a component page or app page ticket. The contract, design-system and critical-flow tickets a screen contract also produces are not page tickets.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**component page ticket**:
The ticket that takes one or more `Component · ` design pages and builds the product components they show. Distinct from the **app page ticket**, which takes an `App · ` page.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**app page ticket**:
The ticket that takes one `App · ` page and builds the product's composition module for it, blocked by the **component page ticket** of every `Component · ` page it composes.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**critical-flow ticket**:
The ticket for one **Critical flows** line, whose journey criterion runs with `--break`. Distinct from the **contract ticket**, whose smoke journey has no `--break`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**static guards**:
The contract ticket's repository-wide deliverables that every later page ticket adds to rather than owns alone: the UI takes no fake data, a `mount` is unique in one render, and a `data-ui` id repeats only on the repeating part of a list. Their criteria sit on the batch's last ticket.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**Shared journey helper**:
The module under `.mmw/harness/`, built once by the contract ticket or the first journey ticket that needs it, for product access several journey tickets share (bringing the stack up, a health check, sign-in, a top-up). Later journey tickets import it.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**`<issue-template>`**:
The ticket template in the `to-tickets` skill's `SKILL.md`: `## Parent`, `## What to build`, `## Read first`, `## Seam`, `## Owns`, `## Acceptance criteria`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Parent`**:
The ticket section routing it to its spec: `#<spec>, Implementation Decisions section <n>`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## What to build`**:
The end-to-end behaviour the ticket makes work, from the end user's point of view, in numbered points each with the test that decides it.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Read first`**:
The sources the ticket's spec subsections cite, each read to its conclusion before work; an item that records a settled conclusion is marked as a **baseline**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**baseline**:
An item under `## Read first` that records a settled conclusion — a decision ticket's resolution, an ADR's decision, a research file's conclusion, a design package, a prototype's chosen artifact — which the worker follows rather than consults. The screen contract's `baselines.look` names the design package directory. In the configuration-management sense (IEEE Std 610.12), it is a reviewed and agreed item that further work builds on and that changes only through change control, which here is a `contract` child.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Seam`**:
The ticket section saying where the ticket is verified: the test layer and directory, the precedent to copy, and how a test arrives at the state.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Owns`**:
The repository-relative paths the ticket may write, one per line, including its test files and any file it must edit to put what it creates in service. Everything outside is read-only for the ticket.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Acceptance criteria`**:
The ticket section holding the acceptance criteria. A `ready-for-human` ticket has none.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**Blocked by**:
The tickets one ticket waits on. On an agent ticket they are its blocking edges on the tracker alone, which the quiz lists and step 5 of `to-tickets` calls a **Blocked by** edge; on a `ready-for-human` ticket, the body item naming the ticket that produces the thing it waits on.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`, `mmw-v2/upstream/skills/engineering/to-tickets/references/person-ticket.md`

### Acceptance criteria

**acceptance criterion**:
One standard on a ticket (a criterion), decided by one command: the lines `- [ ] AC<n>:`, `CHECK:`, `EXPECT:` and `EVIDENCE:`, with `CWD:` and `TIMEOUT:` optional. A judgement no command decides is not one.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`CHECK:`**:
The shell command that decides a criterion, run in its own shell at the repository root (or `CWD:`) with no agent in between. A multi-line command is a **fenced block** directly under it.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`EXPECT:`**:
The string, or `/…/flags` regex, the `CHECK:` output must contain: a **success-only marker**, the line the precedent prints only when it passed.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`EVIDENCE:`**:
The criterion line gate-check writes: `pending` until the criterion runs, then one line of fact about the run, which on a pass fingerprints the definition that passed. The checkbox, not this line, decides whether the criterion is met.
_Home_: `mmw-v2/upstream-unlazy/scripts/gate-check.mjs`

**`CWD:`**:
The optional criterion line naming the working directory `CHECK:` runs in.
_Home_: `mmw-v2/upstream-unlazy/scripts/lib/gates.mjs`

**`TIMEOUT:`**:
The optional criterion line `TIMEOUT: <seconds>` raising how long its `CHECK:` may run. `verify-ticket.py` reads it and keeps it out of the ledger.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**fenced block**:
The only way to write a multi-line `CHECK:`: a code fence directly under it holds the command, and every other fence in the ticket is skipped.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**the five questions**:
The ordered questions the ticket writer asks of anything there is to say about the work, deciding whether it becomes an acceptance criterion, a code-review judgement, a `reaction` ticket, a `reach` ticket or a choice put to the user.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`met`, `unmet`, `abandoned`**:
The three states of a criterion: met is ticked with real evidence, abandoned carries an `ABANDON:` line, and unmet is every other criterion.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**round**:
One pass that fixes and re-runs one criterion, or that fixes the in-ticket findings of a code review.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

**`ABANDON:`**:
The line `ABANDON: AC<n> <kind> <reason>` a worker writes under a criterion it gives up on, of kind `failed`, `stuck` or `decision`. A `failed` or `stuck` one makes the closing comment `HANDOFF REQUIRED`.
_Home_: `mmw-v2/upstream/skills/engineering/implement/SKILL.md`

### The graph

**blocking edge**:
The tracker's native issue dependency between two tickets, the copy every script reads. A blocker is a ticket that must land before the ticket it blocks is started.
_Avoid_: blocking link; native issue dependencies as this concept's name (it names GitHub's mechanism)
_Home_: `docs/agents/issue-tracker.md`

**frontier**:
The tickets `advance` may start now, as `status.py` computes them from the tracker. Distinct from wayfinder's frontier, a map's open, unblocked, unclaimed children.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**sub-issue**:
The tracker's native parent–child relation. A map's children are its decision tickets and specs, a spec's direct children are its tickets, and a ticket's direct children are the issues a worker opens under it with `--sub-issue <kind>`.
_Home_: `docs/agents/issue-tracker.md`, `mmw-v2/skills/verify-ticket/references/sub-issues.md`

### Labels and queues

**label**:
A GitHub label on an issue. This repository's own labels come from three sets that never stand in for each other: a **layer label** says which layer of the tree the issue is, a triage label which queue it is in, a worker-grade label which worker row starts it. Triage's `bug` and `enhancement` and wayfinder's `wayfinder:<type>` labels sit outside the three.
_Home_: `docs/agents/issue-tracker.md`

**layer label**:
One of `mmw:map`, `mmw:spec`, `mmw:ticket`, `mmw:child`, saying which layer of the tree an issue is. It puts an issue in no queue.
_Home_: `docs/agents/issue-tracker.md`

**queue**:
What a triage label expresses: `ready-for-agent` is the agent queue, `needs-triage` holds what nobody has judged, `ready-for-human` is the user's queue.
_Home_: `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`

**triage role**:
A canonical label name the upstream skills use: five state roles, which `docs/agents/triage-labels.md` maps to this repository's label strings, and two category roles, `bug` and `enhancement`, used as named.
_Home_: `docs/agents/triage-labels.md`, `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**`needs-triage`**:
The label of an issue nobody has judged yet: an issue from outside, a ticket its worker handed back or that bounced twice, a landed ticket `reverify` reopened, or a child a worker opened. The triage skill reads this queue.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`, `mmw-v2/upstream/skills/engineering/triage/references/pipeline-issues.md`

**`needs-info`**:
Waiting on the user for more information; one of triage's four outcomes.
_Home_: `docs/agents/triage-labels.md`

**`ready-for-agent`**:
The agent-queue label, which `to-tickets` puts on every agent ticket beside a worker-grade label. It never goes on a spec.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`ready-for-human`**:
The label of a person ticket: a ticket holding one thing only a person can do, of kind `reaction` or `reach`. Such a ticket holds only **the five things**, with no Seam, Owns, criteria or worker grade.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`reaction`**:
The `ready-for-human` kind where the thing asserted is a person's reaction, so the person is the measuring instrument.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`reach`**:
The `ready-for-human` kind where a machine would decide it if it could get to the thing: a device, a credential, a real environment, or a mechanism no ticket owns.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**the five things**:
The fixed, minimal content of a `ready-for-human` ticket, the whole of it: **Parent**, **Which kind**, **What to look at**, **What makes it right**, **Blocked by**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/person-ticket.md`

**retiring line**:
The line a `reach` ticket adds naming what would retire it, that is, make the ticket no longer needed: a test account, a spare device, a CI runner, a mechanism under **How a test arrives at a state** nobody owns yet, or a `TESTING.md` rule that gives a test no exit. Distinct from toolbox's **retired** and the screen contract's `retired_ids`, where the same verb means withdrawn from use.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/person-ticket.md`

**`wontfix`**:
Will not be done; one of triage's four outcomes.
_Home_: `docs/agents/triage-labels.md`

**`bug`, `enhancement`**:
The two category roles, for work arriving from outside; a ticket this repository plans for itself carries neither.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**`## Triage Notes`**:
The comment template `triage` posts for a `needs-info` outcome: what has been established so far, and the specific questions still needed from the reporter.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**`.out-of-scope/`**:
The directory of one-file-per-concept records of enhancement requests rejected as `wontfix`, read during triage for institutional memory and to catch a repeat request before it is re-litigated; a request closed as already implemented is a different outcome, with no file here.
_Home_: `mmw-v2/upstream/skills/engineering/triage/OUT-OF-SCOPE.md`

**PRs as a request surface**:
The per-repository flag deciding whether triage covers external pull requests as it covers issues; when it does, a PR is triaged as an issue with attached code, through the same roles, states and machine, and only a PR from outside the maintainer and collaborators is surfaced for triage (one named explicitly is triaged regardless).
_Home_: `docs/agents/issue-tracker.md`

**decision ticket**:
A child issue of a wayfinder map holding one question whose resolution is a decision, typed by a `wayfinder:<type>` label. It carries no state role and is not triaged. Its resolution comment is a baseline source.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**selection list**:
The decision ticket a remake destination opens: the user picks, item by item, what from the old product to keep, each item naming its source path and which entry it feeds. The old design package, screen contract, boundary tests and journeys sit outside that choice; the remake produces its own.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/references/interface-and-remake.md`

**map**:
Wayfinder's single issue labelled `wayfinder:map` and `mmw:map`, the index of an effort too large for one session. Its children are decision tickets and the specs published from it.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**agent brief**:
The durable record the triage skill writes of what an evaluation established: an investigation record, not a work order. `to-spec` reads it as one of a spec's sources.
_Home_: `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md`

### Publishing and linting

**ambiguity scan**:
The read-only pass over a spec and its drafted tickets that feeds questions into the `to-tickets` quiz's **Choices** before the breakdown is shown.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/ambiguity-scan.md`

**Choices**:
The line the `to-tickets` quiz shows for each ticket an agent works: every choice the fifth of **the five questions** sent there and every question the **ambiguity scan** returned, each with its options and the one the ticket writer would take. An answered choice is written into the ticket's `## What to build`, or back into the spec when it changes a decision there.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**ticket draft**:
An approved ticket written to a local file, `<draft name>.md`, in the directory `--lint --drafts <dir>` checks and `--publish --drafts <dir>` later creates as an issue: the header lines `TITLE:`, `LABELS:` and `BLOCKED BY:`, then `---`, then the body. The file's name, standing in for the issue number it does not have yet, is what `BLOCKED BY:` and the lint use to reference it.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**publish**:
Creating the spec or the tickets as GitHub issues, each ticket a native sub-issue of its spec, followed by the read-back step, which fetches every ticket again and runs `--lint` before the batch is reported as published.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**lint**:
`verify-ticket.py <n> --lint`: gate-lint plus the ticket-graph, worker-label and screen-contract checks, run on one ticket, on a spec's batch, or on the batch's drafts before publishing.
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**lint rule ID**:
The string in `[brackets]` at the end of a lint finding's line, naming the check that reported it, as ESLint's and SARIF's `ruleId` does: a cycle in the batch's blocking edges, a worker-grade or layer label out of place, an unreadable `screen-contract.yaml rows:` line, a weak `EXPECT:`, and others. Always qualified: `retro`'s Rule id names a Nowledge Mem Rule.
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`, `mmw-v2/upstream-unlazy/scripts/gate-lint.mjs`

**`ERROR`, `WARN`**:
The two lint levels. Only an `ERROR` affects `--lint`'s exit code.
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**triage**:
The skill that judges an issue waiting in `needs-triage` and recommends one of four outcomes: `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

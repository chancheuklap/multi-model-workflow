# Tickets

The written half of the landing pipeline: what a spec and a ticket are, the sections each one carries, how a batch is published, read back and linted, and which labels and queues an issue carries while it waits. Every other context reads what this one wrote.

How to read an entry: the bold line is the term's name, and a term that is a literal string in a file, a command or a comment is named by that string exactly. The definition says in one or two sentences what the thing is and how it differs from its neighbours. `_Avoid_` lists wordings that name the concept less precisely in this repository's own text, each with the sense in which it is avoided. `_Home_` is the file that states the fact; an entry does not repeat what can be read there (a field list, an exit code, a command's switches, the branches of a behaviour), and when the two disagree, `_Home_` is right.

## Language

### Worker grades

**worker grade**:
Which of the two workers a ticket goes to: at once a ticket label and a `models.json` row. `dispatch.sh` reads the label afresh each time the ticket is started.
_Home_: `docs/agents/issue-tracker.md`

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
The spec section of decisions made, in numbered subsections `### 1.` … that a ticket's `## Parent` points at. Each decision names its source.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Testing Decisions`**:
The spec section that says where a test observes the result, the seam and what is real on each side of it, each test layer's directory and precedent, how a test arrives at each state, and the commands to run before committing. A ticket's `## Seam`, `CHECK:` and `EXPECT:` are derived from it.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**Critical flows**:
The bullet of `## Testing Decisions`, written only in a spec with a screen contract, naming, one line each, the flows whose failure costs most (money, sign-in, a submit chain) with the directory under `.mmw/journeys/` each one runs from.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Out of Scope`**:
The spec section of what is not being done, read by the worker and the Spec axis. A wayfinder map's Out of scope section is a different heading, carried into the spec.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**`## Sources`**:
The spec section linking the first-hand material the spec was built from, one line per fixed kind and `none` where a kind is empty. A ticket's `## Read first` picks from it.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

**seam**:
The public interface a test observes behaviour at, without reaching inside. `## Testing Decisions` names it and a ticket copies it into `## Seam`.
_Home_: `mmw-v2/upstream/skills/engineering/tdd/SKILL.md`

**precedent**:
The similar existing test `## Testing Decisions` names per test layer. The ticket copies it into `## Seam`, and the ticket writer copies its invocation into `CHECK:` and its success line into `EXPECT:`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**test layer**:
The layer a feature's tests land in, named in `## Testing Decisions` with its directory and precedent.
_Home_: `mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`

### Tickets

**ticket**:
An issue that is a native sub-issue of its spec, in the `<issue-template>` shape and labelled `mmw:ticket`: one vertical slice a worker takes from claim to close. A batch is the tickets under one spec, published together.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**vertical slice**:
A ticket's cut: a narrow but complete path through every layer (schema, API, UI, tests), demoable or verifiable on its own (a tracer bullet), as against a horizontal slice of one layer.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**prefactor ticket**:
The ticket cut ahead of tickets that would otherwise all edit the same files nobody owns: it owns those files and lands the entries they need, so each of those tickets is blocked by it alone. Where the spec has a screen contract, it is also the **contract ticket**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**design-system ticket**:
The ticket that copies a design system's variables, fonts and part stylesheets from the design package's `_ds/` into the product, cut when the product lacks them and ahead of the **contract ticket**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**contract ticket**:
The ticket that lands or completes `.mmw/` so later tickets have a precedent to copy. Distinct from a **component page ticket**, which builds the product code of design pages, and from a **design-system ticket**, which does not depend on `.mmw/`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**interface ticket**:
A ticket whose **Read first** carries a `screen-contract.yaml rows:` line: a component page or app page ticket. The contract, design-system and acceptance tickets a screen contract also produces are not interface tickets.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**component page ticket**:
The ticket that takes one or more `Component · ` design pages and builds the product components they show. Distinct from the **app page ticket**, which takes an `App · ` page.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**app page ticket**:
The ticket that takes one `App · ` page and builds the product's composition module for it, blocked by the **component page ticket** of every `Component · ` page it composes.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**acceptance ticket**:
The ticket for one **Critical flows** line, whose journey criterion runs with `--break`. Distinct from the **contract ticket**, whose smoke journey has no `--break`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/cutting-interface-tickets.md`

**`<issue-template>`**:
The ticket template in the `to-tickets` skill's `SKILL.md`: `## Parent`, `## What to build`, `## Read first`, `## Seam`, `## Owns`, `## Acceptance criteria`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Parent`**:
The ticket section routing it to its spec: `#<spec>, Implementation Decisions section <n>`.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## What to build`**:
The end-to-end behaviour the ticket makes work, from the user's point of view, in numbered points each with the test that decides it.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`## Read first`**:
The sources the ticket's spec subsections cite, each read to its conclusion before work; an item that records a settled conclusion is marked as a **baseline**.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**baseline**:
An item under `## Read first` that records a settled conclusion — a decision ticket's resolution, an ADR's decision, a research file's conclusion, a design package, a prototype's chosen artifact — which the worker follows rather than consults. The screen contract's `baselines.look` names the design package directory.
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
The item of a `ready-for-human` ticket naming the ticket that produces the thing it waits on. An agent ticket's blocking is on the tracker's blocking links alone.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/person-ticket.md`

### Acceptance criteria

**acceptance criterion**:
One standard on a ticket (a criterion), decided by one command: the lines `- [ ] AC<n>:`, `CHECK:`, `EXPECT:` and `EVIDENCE:`, with `CWD:` and `TIMEOUT:` optional. A judgement no command decides is not one.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`CHECK:`**:
The shell command that decides a criterion, run in its own shell at the repository root (or `CWD:`) with no agent in between. A multi-line command is a **fenced block** directly under it.
_Home_: `mmw-v2/skills/verify-ticket/SKILL.md`

**`EXPECT:`**:
The string, or `/…/flags` regex, the `CHECK:` output must contain: a line the precedent prints only on success.
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
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

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

**blocking link**:
The tracker's native issue dependency between two tickets, the copy every script reads. A blocker is a ticket that must land before the ticket it blocks is started.
_Home_: `docs/agents/issue-tracker.md`

**frontier**:
The tickets `advance` may start now, as `status.py` computes them from the tracker. Distinct from wayfinder's frontier, a map's open, unblocked, unclaimed children.
_Home_: `mmw-v2/skills/dispatch/scripts/status.py`

**sub-issue**:
The tracker's native parent–child relation. A map's children are its decision tickets and specs, a spec's direct children are its tickets, and a ticket's direct children are the issues a worker opens under it with `--sub-issue <kind>`.
_Home_: `mmw-v2/skills/verify-ticket/references/sub-issues.md`

### Labels and queues

**label**:
A GitHub label on an issue, from one of three sets that never stand in for each other: a **layer label** says which layer of the tree the issue is, a triage label which queue it is in, a worker-grade label which worker row starts it.
_Home_: `docs/agents/issue-tracker.md`

**layer label**:
One of `mmw:map`, `mmw:spec`, `mmw:ticket`, `mmw:child`, saying which layer of the tree an issue is. It puts an issue in no queue.
_Home_: `docs/agents/issue-tracker.md`

**queue**:
What a triage label expresses: `ready-for-agent` is the agent queue, `needs-triage` holds what nobody has judged, `ready-for-human` is the user's queue.
_Home_: `docs/agents/triage-labels.md`

**triage role**:
A canonical label name the upstream skills use, mapped in `docs/agents/triage-labels.md` to this repository's label string: five state roles and two category roles.
_Home_: `docs/agents/triage-labels.md`

**`needs-triage`**:
The label of an issue nobody has judged yet: an issue from outside, a ticket its worker handed back or that bounced twice, a landed ticket `reverify` reopened, or a child a worker opened. The triage skill reads this queue.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**`needs-info`**:
Waiting on the user for more information; one of triage's four outcomes.
_Home_: `docs/agents/triage-labels.md`

**`ready-for-agent`**:
The agent-queue label, which `to-tickets` puts on every agent ticket beside a worker-grade label. It never goes on a spec.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`ready-for-human`**:
The label of a ticket holding one thing only a person can do, of kind `reaction` or `reach`. Such a ticket has a shape of its own, with no Seam, Owns, criteria or worker grade.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`reaction`**:
The `ready-for-human` kind where the thing asserted is a person's reaction, so the person is the measuring instrument.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`reach`**:
The `ready-for-human` kind where a machine would decide it if it could get to the thing: a device, a credential, a real environment, or a mechanism no ticket owns.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**`wontfix`**:
Will not be done; one of triage's four outcomes.
_Home_: `docs/agents/triage-labels.md`

**`bug`, `enhancement`**:
The two category roles, for work arriving from outside; a ticket this repository plans for itself carries neither.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

**decision ticket**:
A child issue of a wayfinder map holding one question whose resolution is a decision, typed by a `wayfinder:<type>` label. It carries no state role and is not triaged. Its resolution comment is a baseline source.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**map**:
Wayfinder's single issue labelled `wayfinder:map` and `mmw:map`, the index of an effort too large for one session. Its children are decision tickets and the specs published from it.
_Home_: `mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md`

**agent brief**:
The durable record the triage skill writes of what an evaluation established: an investigation record, not a work order. `to-spec` reads it as one of a spec's sources.
_Home_: `mmw-v2/upstream/skills/engineering/triage/AGENT-BRIEF.md`

### Publishing and linting

**ambiguity scan**:
The read-only pass over a spec and its drafted tickets that feeds questions into the `to-tickets` quiz's Choices before the breakdown is shown.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/references/ambiguity-scan.md`

**publish**:
Creating the spec or the tickets as GitHub issues, each ticket a native sub-issue of its spec, followed by the read-back step, which fetches every ticket again and runs `--lint` before the batch is reported as published.
_Home_: `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md`

**lint**:
`verify-ticket.py <n> --lint`: gate-lint plus the ticket-graph, worker-label and screen-contract checks, run on one ticket, on a spec's batch, or on the batch's drafts before publishing.
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**problem tag**:
The tag a lint finding carries, naming the kind of problem (`weak-expect`, `cycle`, `screen-contract`, …).
_Home_: `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py`

**`ERROR`, `WARN`**:
The two lint levels. Only an `ERROR` affects `--lint`'s exit code.
_Home_: `mmw-v2/skills/verify-ticket/references/linting.md`

**triage**:
The skill that judges an issue waiting in `needs-triage` and recommends one of four outcomes: `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.
_Home_: `mmw-v2/upstream/skills/engineering/triage/SKILL.md`

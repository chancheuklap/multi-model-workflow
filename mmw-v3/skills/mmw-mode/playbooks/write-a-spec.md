### Write a spec

**You own one spec: what the owner and the sources already settled, written down and published on the tracker, then cut into its batch through Cut tickets.** Do not interview the owner for facts; synthesize what the conversation, the reference and the code already hold. A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module boundary, a data shape, the seam) is yours: make it and mark it "this spec's decision". A call on what the customer sees, what happens to money, or what is in scope that no source settles is the owner's: put it to them before you publish. That, a division into several specs, and the division of behaviour into features in `## Feature map changes`, are the only things you ask them. Distinct from Revise a spec, which changes a spec already on the tracker, from Chart a map, which is for work whose way is not visible yet, and from Make a small change, which needs no spec.

The repository's `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md` say how its tracker is reached and what its labels are called. If either is missing, tell the owner to run the `setup-mmw` skill, and stop.

1. **Read every source.** If the owner passed a reference (an issue number, a URL, a file path), read its full body and comments first; a triaged issue's agent brief comment is one of the sources. Follow every decision ticket, prototype or research file it links through to its conclusion. When the reference is a wayfinder **map**, read the map body, walk its **Decisions so far** and read each closed ticket's resolution comment, following a linked prototype or research file through to its conclusion; the spec's Out of Scope links the map's **Out of scope** rather than copying it. When the reference is a published spec and one of its sections has to change, run **Revise a spec** instead of this playbook.
   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different seam and lands and demos on its own; where it can stay one spec, keep it one spec. A part may depend on a part before it: a product delivered in stages (a server registration, then the client that logs into it, then the work the client does) has no reading under which the later stages depend on nothing, and forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle: every one points at a part earlier in the order, and the written division records that order. Several: put the division to the owner (each spec's name, the decisions it covers, the order, and why the line falls there), and once they confirm, write it down, one line per spec with its name, what it covers, its position in the order, and its issue number once published: on a map, as a `## Specs` section of the map body; otherwise in the first spec's `## Further Notes`. This run writes and cuts the first spec only; the next is written by a later run with the map, or this spec, as its reference. When the reference already carries a division (a map's `## Specs`, or a spec whose `## Further Notes` lists one), skip the judgement and write the first spec on it whose line has no issue number yet; when every line has one, tell the owner the division is fully written and stop.
   Done when every source the reference leads to has been read and you know which one spec this run writes.
2. **Read the code, the glossary and the ADRs.** Before you read the code, read `docs/features/<product>/` for each product the spec touches. A product with no such directory has no feature map yet. Then explore the repository for the current state of what the spec touches. Use the project's domain glossary vocabulary (`CONTEXT.md`, or `CONTEXT-MAP.md` and the contexts it names) throughout the spec, and respect the ADRs in the area (**principle-start-from-what-exists**).
   An effort with a UI has a **screen contract** (`efforts/<effort>/screen-contract.yaml`, written by Write the screen contract) and two baselines with separate jurisdictions: the design package for look and verbatim copy, the screen contract for what each control calls, which field feeds each shown value, what state follows and how a test reaches it. Read the screen contract in full, its `pages` and `scenes` included. A row whose `gap` is not `aligned` is a decision nobody has made: stop rather than write a spec around it. On a map, send the effort back to its alignment ticket. With no map, stay in this session and run Write the screen contract from its **Sweep in reverse** through its **Lint and commit**; on the way, its **Write the gap list and settle it with the owner** has the owner settle each unaligned row. A decision that no row carries and the design package does not draw (a behaviour of something that is text, not a control) is written in the subsection it belongs to as "this spec's decision", citing what it rests on.
   Done when you have read `docs/features/<product>/` for each product the spec touches, or seen that its directory is absent, and you know which existing modules and ADRs each decision touches, or that none exists yet, and, with a screen contract, every row's `gap` is `aligned`.
3. **Choose the seam.** Sketch the seams at which the feature is tested. Prefer an existing seam to a new one, and use the highest seam possible; if new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better, and the ideal number is one. The repository's `TESTING.md` says which test layers exist, which external boundaries may be stubbed and how tests run; the seam and the spec's `## Testing Decisions` draw on it. A seam says where a test **observes**; ask the other half in the same breath: for each state the feature's behaviour turns on, can a test put the system into that state through this seam? With a screen contract, a story page is put into a scene by its adapter reading that scene's values, so a test at that seam cannot reach a product state that only a real request produces. A four-column boundary test that asserts `calls`, `shows`, `next` and `on_failure` after a click still cannot seed the database the click would have written. Where the seam does not reach, say what would, and whether that thing ships. The seam is yours to decide, not the owner's: they are not asked to confirm it. What they see of it is the plain-words opening sentence of `## Testing Decisions`, which says where a test looks at the result.
   Done when every state the feature's behaviour turns on has a seam where a test observes it, and either a way a test puts the system into it through that seam or a named mechanism that would.
4. **Write the spec and publish it.** Write it in the shape of **The spec template** below, to a file. Put every call on what the customer sees, on money or on scope that no source settles to the owner, with the options and the one you would take, and write each answer into its subsection as a decision the owner confirmed. Put the division in `## Feature map changes` to the owner with those calls, and write the answer into that section. The section's fixed shape is `references/feature-map.md`. The template points at that file and does not copy the shape. Then publish it with the `verify-ticket` skill's `verify-ticket.py --publish --spec-body <file> --title <the spec's title>`, adding `--map <map>` when the reference is a map, which makes the spec a sub-issue of the map and confirms the link; it prints the new issue's number. The issue carries the label `mmw:spec` and no triage label: a spec is a container for the tickets under it, not a piece of work, and a triage label would put it in a queue somebody has to sort back out. When a division into several specs is written down, write `#<number>` of the new spec into its line: in a map's `## Specs` by editing the map body (`gh issue edit <map> --body-file <file>`), in a spec's `## Further Notes` through **Revise a spec**. The next run picks the first line with no number, so a line left without one is written twice.
   Done when `--publish` exits 0, you hold the spec's number, and, with a division, its line carries that number.
5. **Cut its tickets.** Run **Cut tickets** on the published spec.
   Done when Cut tickets' last step is done.

**The spec template.** Step 4 writes the spec in this shape.

```markdown
## Problem Statement

The problem the customer is facing, from their perspective.

## Solution

The solution to the problem, from the customer's perspective.

## User Stories

A long, numbered list of user stories, each in the form:

1. As an <actor>, I want a <feature>, so that <benefit>

For example:

1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending

This list should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

The implementation decisions that were made, grouped into numbered subsections (`### 1. …`, `### 2. …`) that tickets point at by number. Each subsection can cover:

- The modules that will be built or modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Each subsection is read on its own: a worker opens only the subsections its ticket names, so a subsection that depends on another names it.

Every decision names where it came from, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, a research or prototype path, a screen-contract row id. A decision with no source is written as "this spec's decision", citing what it rests on, and says so where the owner confirmed it. A fact of the repository's `TESTING.md` that shapes a decision is cited by its line in the subsection it shapes, not restated: that line is listed under Sources, and a ticket's **Read first** points the worker at it.

A user story's conclusion is folded into the subsection that implements it. A worker reads the Implementation Decisions subsections its ticket names and never a story, so a behaviour that is settled only in a story reaches nobody. Whatever a story decides about a control, a value, a transition or a failure is stated here, in the subsection that implements it, with the story number as its source; the screen contract's rows then cite the subsection, not the story.

An effort with a screen contract has one fixed subsection here, **API contract**: one entry per distinct operation in the screen contract's `calls` column (its request fields, its response fields, its failure cases), derived from the rows' `shows` and `on_failure`, each entry citing the row ids that use it. This is where a new project's OpenAPI document starts.

The same effort has one fixed subsection here, **cross-component composition**: one entry per cross-component row, naming the request fields that row's action carries and the state the other region enters, citing the row id.

The same effort has one paragraph on **visual acceptance**, in its own numbered subsection or the one that carries the `data-ui` ids, and it restates no command: appearance is decided by **element parity** (the story oracle of the `ui-acceptance` skill pairs both sides by `data-ui` id), citing the screen contract's `pages`, `App · ` pages included. Each design page's `mount` is the story page id.

No implementation file paths (the module you will edit, the function you will add) and no code snippets: they go stale fast. Paths to source material (ADRs, research files, prototype directories, domain docs, test directories, shared contract locations) are what the tickets and the worker read from: write them. Exception: a prototype snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape) is inlined within the decision it encodes, noted as coming from a prototype, and trimmed to its decision-rich parts, not a working demo.

## Feature map changes

One feature file per entry, in the fixed shape of `references/feature-map.md`. A spec that changes no behaviour a user can observe writes `none`.

## Testing Decisions

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result: a browser page, an HTTP endpoint, or a function call ("Tests look at the result on the browser page."). The next names the seam: what is real on each side of it, and which external boundaries (third-party APIs, paid services) may be stubbed. Then:

- What makes a good test here: external behaviour, not implementation details.
- The test layers this feature lands in, each with its directory and the precedent to copy (similar tests already in the codebase); every ticket cut from this spec names one of them as the place it is verified.
- **How a test arrives at a state.** Per test layer: what a test writes to put the system into a state, and what it cannot write. A state the feature's behaviour turns on that a test cannot write through the seam gets a line of its own: the mechanism that will reach it, and which builds carry it. The mechanism takes the form the repository's `TESTING.md` allows; where that file has no exit for one, say so: closing that is the repository's to do, not this spec's, and Cut tickets cuts a *reach* ticket for it. Whoever cuts the tickets reads this section to know whether a criterion can be written at all, and one of them will own building each mechanism named here. With a screen contract, three mechanisms are named here: the story adapter that puts a story page into a scene from its scene data (or the screen contract's scene input), the interaction helper that puts a control on screen by its `data-ui` id for a four-column boundary test, and `start` in `.mmw/target.json`, which brings the product up for a journey. On a new product all three are new. On a product whose `.mmw/` already answers, say which is missing, counting what `target_config.py --check` of the `ui-acceptance` skill reports and any answer built for a design package, scene shape or control lookup other than the current ones, or say that nothing is. How each is shaped is that skill's references, and is not restated.
- **Critical flows** (关键流程). Only with a screen contract: List the flows where a silent break costs the user money, access or submitted work, not every path through the UI. One line per such flow, naming the flow (the directory name under `.mmw/journeys/<flow>/`) and the Implementation Decisions section numbers it involves. Each line sits nested under the bullet in one shape, ``- `<flow>`: Implementation Decisions sections <n>, <n>``: the words `Implementation Decisions` stay in English whatever language the spec is written in, as a ticket's `## Parent` names them, and the numbers follow them. The `verify-ticket` skill's `--lint` reads these lines to decide which journeys need `--break`, and reports any line it cannot read. Each line becomes a critical-flow ticket: a journey that drives the real product end to end with nothing mocked, and runs again with the flow's last write broken to prove the journey notices. Write `none` when the product has no such flow; omit the bullet also when the product can never be started whole (a library, a component with no running product); a product whose `.mmw/target.json` does not exist yet still writes it, because its contract ticket lands `start`.
- The commands to run before committing.

## Out of Scope

What this spec does not cover. A spec written from a map opens this section with a link to the map's **Out of scope**, which holds here as well, and lists only what this spec leaves out beyond it.

## Sources

Links to the first-hand material this spec was built from, one line per kind; "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":

- Wayfinder map
- Originating issue (the triaged issue and its agent brief comment)
- Decision tickets (each named by the decision it settled)
- Upstream specs this one builds on, including an earlier spec the decision tickets cite as their basis
- ADRs
- Research files
- Prototype directories
- Design package (the look-and-copy baseline; "none" when the effort has no UI)
- Screen contract (the behaviour baseline, `efforts/<effort>/screen-contract.yaml`; "none" likewise)
- Domain docs
- Evidence (measurements, cost runs, real-call records)
- Repository test facts: the lines of `TESTING.md` this spec relies on

## Further Notes

Anything else about the feature. When step 1 divided the work into several specs and the reference was not a map, the division lives here in the first spec; a later spec of the division says here which spec carries it.
```

**Reply:** the spec's number and title, each decision marked "this spec's decision" that the owner may want to overturn, and the owner's answers it records; when the work was divided, which spec of the division this was and which comes next; then Cut tickets' reply.

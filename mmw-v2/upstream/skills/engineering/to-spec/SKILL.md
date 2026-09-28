---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed. Use when a conversation, a wayfinder map or a triaged issue has to become a spec, or a section of a published spec has to change."
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user for facts; just synthesize what you already know. A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module boundary, a data shape, the seam) is yours: make it and mark it "this spec's decision". A call on what the user sees, what happens to money, or what is in scope that no source settles is not yours: put it to the user before you publish. That, and the division in step 1, are the only things you ask them.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run the `setup-matt-pocock-skills` skill.

## Process

1. If the user passed a reference (an issue number, a URL, a file path), read its full body and comments before anything else. When the reference is a published spec and one of its sections has to change, read [references/revising-a-spec.md](references/revising-a-spec.md) instead of the steps below. When the reference is a wayfinder **map**: read the map body; then walk **Decisions so far** and read each closed ticket's **resolution comment**; where a ticket links a prototype or a research file, read that through to its conclusion. The map's **Out of scope** carries into the spec's Out of Scope unchanged.

   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different **seam** and lands and demos on its own; where it can stay one spec, keep it one spec. A part may depend on a part before it: a product delivered in stages (a server registration, then the client that logs into it, then the work the client does) has no reading under which the later stages depend on nothing, and forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle: every one points at a part earlier in the order, and the `## Specs` section writes that order down.

   One spec: write it. Several, or a reference that already carries a division (a map's `## Specs` section, or a spec whose `## Further Notes` lists several specs): read [references/several-specs.md](references/several-specs.md).

   Done when every source the reference leads to has been read and you know which one spec this run writes.

2. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

   An effort with an interface has a **screen contract** (`docs/specs/<effort>/screen-contract.yaml`, written by the `write-screen-contract` skill) and two baselines with separate jurisdictions: the design package for look and verbatim copy, the screen contract for what each control calls, which field feeds each shown value, what state follows and how a test reaches it. Read the contract in full, its `pages` and `scenes` included. A row whose `gap` is not `aligned` is a decision nobody has made: stop rather than write a spec around it. On a wayfinder map, send the effort back to its alignment ticket. With no map, stay in this session and return to the `write-screen-contract` skill at **Reverse sweep**, then **Write the gap list and stop for the user**, where the user settles each unaligned row. A decision that no row carries and the design package does not draw (a behaviour of something that is text, not a control) is written in the subsection it belongs to as "this spec's decision", citing what it rests on.

   Done when you know which existing modules and ADRs each decision touches, or that none exists yet, and, with a screen contract, every row's `gap` is `aligned`.

3. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one. The repository's `TESTING.md` says which test layers exist, which external boundaries may be stubbed and how tests run; the seam and `## Testing Decisions` draw on it.

A seam says where a test **observes**. Ask the other half in the same breath: for each state this feature's behaviour turns on, can a test put the system into that state through the seam you picked? With a screen contract, a story page is put into a scene by its adapter reading that scene's values, so a test at that seam cannot reach a product state that only a real request produces. A four-column boundary test that asserts `calls`, `shows`, `next` and `on_failure` after a click still cannot seed the database the click would have written. Where the seam does not reach, say what would, and whether that thing ships.

The seam is yours to decide, not the user's: they are not asked to confirm it. What they see of it is the plain-words opening sentence of Testing Decisions, which says where a test looks at the result.

Done when every state this feature's behaviour turns on has a seam where a test observes it, and either a way a test puts the system into it through that seam or a named mechanism that would.

4. Write the spec using the template below, then publish it with the `verify-ticket` skill's `--publish --spec-body <file> --title <the spec's title> [--map <map>]`. Give it no triage label: a spec is a container for the tickets underneath it, not a piece of work, and a triage label would put it in a queue somebody has to sort back out. Pass `--map` when the reference is a wayfinder map, which publishes the spec as a native sub-issue of it and confirms the link before reporting the publish as complete; leave it out for any other reference.

Done when `--publish` exits 0.

<spec-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

The implementation decisions that were made, grouped into numbered subsections (`### 1. …`, `### 2. …`) that tickets point at by number. Each subsection can cover:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Each subsection is read on its own: a worker opens only the subsections its ticket names, so a subsection that depends on another names it.

**Every decision names where it came from**, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, a research or prototype path, a screen-contract row id. A decision with no source is written as "this spec's decision", citing what it rests on (and, where the user confirmed it, say so). A rule of the repository's `CODING_STANDARDS.md` that shapes a decision is stated in the subsection it shapes, citing its section: the worker reads the spec, not that file.

**A user story's conclusion is folded into the subsection that implements it.** A worker reads the Implementation Decisions subsections its ticket names and never a story, so a behaviour that is settled only in a story reaches nobody. Whatever a story decides about a control, a value, a transition or a failure is stated here, in the subsection that implements it, with the story number as its source; the screen contract's rows then cite the subsection, not the story.

An effort with a screen contract has one fixed subsection here, **API contract**: one entry per distinct operation in the contract's `calls` column (its request fields, its response fields, its failure cases), derived from the rows' `shows` and `on_failure`, each entry citing the row ids that use it. This is where a new project's OpenAPI document starts.

The same effort has one fixed subsection here, **`App · ` 页组合**: one entry per **cross-component row**, naming the request fields that row's action carries and the state the other region enters, citing the row id.

The same effort has one paragraph on **visual acceptance**, in its own numbered subsection or the one that carries the `data-ui` ids, and it restates no command: appearance is decided by **element parity** (the story judge of the `ui-acceptance` skill pairs both sides by `data-ui` id), citing the contract's `pages`, `App · ` pages included. Each design page's `mount` is the story page id.

Do NOT include implementation file paths (the module you will edit, the function you will add) or code snippets. They may end up being outdated very quickly. Paths to source material (ADRs, research files, prototype directories, domain docs, test directories, shared contract locations) are what the tickets and the implementer read from: write them.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result: a browser page, an HTTP endpoint, or a function call ("Tests look at the result on the browser page."). The next sentence names the **seam** chosen in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed. Then:

- A description of what makes a good test (only test external behavior, not implementation details)
- The test layers this feature lands in, each with its directory and the precedent to copy (i.e. similar types of tests in the codebase); every ticket cut from this spec will name one of these layers as the place it is verified
- **How a test arrives at a state.** Per layer: what a test writes to put the system into a state, and what it cannot write. A state this feature's behaviour turns on, that the seam's write surface does not reach, gets a line of its own here: the mechanism that will reach it, and which builds carry that mechanism. The mechanism takes the form the repository's `TESTING.md` allows; where it has no exit for one, say so: closing that is the repository's to do, not this spec's, and `to-tickets` cuts a *reach* ticket for it. Whoever cuts the tickets reads this section to know whether a criterion can be written at all, and one of them will own building each mechanism named here. With a screen contract, three mechanisms are named here: the story adapter that puts a story page into a scene from its scene data (or the contract's scene input), the interaction helper that puts a control on screen by its `data-ui` id for a four-column boundary test, and `start` in `.mmw/target.json`, which brings the product up for a journey. On a new product all three are new. On a product whose `.mmw/` already answers, say which is missing, counting what `target_config.py --check` of the `ui-acceptance` skill reports and any answer built for a design package, scene shape or control lookup other than the current ones, or say that nothing is. How each is shaped is that skill's references, and is not restated.
- **Critical flows** (关键流程). Only with a screen contract: List the flows where a silent break costs the user money, access or submitted work, not every path through the interface. One line per such flow, naming the flow (the directory name under `.mmw/journeys/<flow>/`) and the Implementation Decisions section numbers it involves. Each line sits nested under the bullet in one shape, ``- `<flow>`: Implementation Decisions sections <n>, <n>``: the words `Implementation Decisions` stay in English whatever language the spec is written in, as a ticket's `## Parent` names them, and the numbers follow them. The `verify-ticket` skill's `--lint` reads these lines to decide which journeys need `--break`, and reports any line it cannot read. Each line becomes an acceptance ticket: a journey that drives the real product end to end with nothing mocked, and runs again with the flow's last write broken to prove the journey notices. Write `none` when the product has no such flow; omit the bullet also when the product can never be started whole (a library, a component with no running product); a product whose `.mmw/target.json` does not exist yet still writes it, because its contract ticket lands `start`.
- The commands to run before committing

## Out of Scope

A description of the things that are out of scope for this spec.

## Sources

Links to the first-hand material this spec was built from, one line per kind. Write "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":

- Wayfinder map
- Originating issue (the triaged issue and its agent brief comment)
- Decision tickets (each named by the decision it settled)
- Upstream specs this one builds on, including an earlier spec the decision tickets cite as their basis
- ADRs
- Research files
- Prototype directories
- Design package (the look-and-copy baseline; `none` when the effort has no interface)
- Screen contract (the behaviour baseline, `docs/specs/<effort>/screen-contract.yaml`; `none` likewise)
- Domain docs
- Evidence (measurements, cost runs, real-call records)
- Repository rules: `CODING_STANDARDS.md`, `TESTING.md`, the sections this spec relies on

## Further Notes

Any further notes about the feature. When step 1 divided the work into several specs and the reference was not a map, the division lives here in the first spec: one line per spec, with its name, what it covers, its position in the order, and its link once published. A later spec in that division says here which spec carries it.

</spec-template>

## Next

The `to-tickets` skill.

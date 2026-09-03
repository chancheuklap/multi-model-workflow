---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user for facts; just synthesize what you already know. Step 1 names the one judgement you hand back to them.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

1. If the user passed a reference — an issue number, a URL, a file path — read it in full before anything else. When the reference is a spec already published on the tracker and the user wants one of its sections changed, skip to step 5. When the reference is a wayfinder **map**: read the map body; then walk **Decisions so far** and read each closed ticket's **resolution comment**; where a ticket links a prototype or a research file, read that through to its conclusion. The map's **Out of scope** carries into the spec's Out of Scope unchanged.

   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different **seam** and lands and demos on its own — where it can stay one spec, keep it one spec. A part may depend on a part before it: a product delivered in layers (a server registration, then the client that logs into it, then the work the client does) has no reading under which the later layers depend on nothing, and forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle: every one points at a part earlier in the order, and the `## Specs` section writes that order down.

   One spec: write it. Several: this is the one judgement in this skill you hand to the user — list each spec's name, the decisions it covers by ticket name, the order they go in, and why the line falls there. Once the user confirms, write the division back to the map as a `## Specs` section, one line per spec: name, the decision tickets it covers, its position in the order, and its spec link once published. Then write the first spec only; publish it, fill its link into that line, and stop — tell the user to run this skill against the map again for the next one. When the map already carries a `## Specs` section, skip the judgement and write the first spec on it that has no link yet.

   When the reference is not a map — an issue, a URL, a file, or the conversation itself — there is no map to write the division back to. Write it into the first spec's `## Further Notes` instead: one line per spec, saying what it is called, what it covers, its position in the order, and its link once published. Publish that first spec and stop; tell the user to run this skill against the same reference again for the next one. On that later run, read the `## Further Notes` of the spec that carries the division, write the first spec on it that has no link yet, and fill the link into its line — through step 5, since that spec is already published. When every line has a link, tell the user the division is fully written and stop.

2. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

   An effort with an interface has a **screen contract** — `docs/specs/<effort>/screen-contract.yaml`, written by the `align-screens` skill from the alignment ticket — and two baselines with separate jurisdictions: the handoff package for look and verbatim copy, the screen contract for what each control calls, which field feeds each shown value, what state follows and how a test reaches it. Read the contract in full. A row whose `gap` is not `aligned` is a decision nobody has made: stop and send the effort back to its alignment ticket rather than write a spec around it.

3. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

A seam says where a test **observes**. Ask the other half in the same breath: for each state this feature's behaviour turns on, can a test put the system into that state through the seam you picked? An interface compared through a debugging port is read and not written, so a test cannot reach a state that only the running application can enter. Where the seam does not reach, say what would, and whether that thing ships.

The seam is yours to decide, not the user's: they are not asked to confirm it. What they see of it is the plain-words opening sentence of Testing Decisions, which says where a test looks at the result.

4. Write the spec using the template below, then publish it to the project issue tracker. Leave it unlabelled: a spec is a container for the tickets underneath it, not a piece of work, and a triage label would put it in a queue somebody has to sort back out. If the spec grew out of an issue carrying an agent brief, close that issue and attach it under the spec, so the brief stays reachable from the spec that replaced it.

5. Revising a published spec. When a section of a spec already on the tracker has to change — a mechanism added under **How a test arrives at a state**, a decision under `## Implementation Decisions` altered, a judgement written into one of its subsections — edit that spec, never publish a new one: a new issue gets a new number, and every ticket's **Parent** points at the old one. Read the issue body in full, rewrite the section so it reads as if written that way from the start, and write the body back (`gh issue edit <n> --body-file <file>`). The body carries no trace of the change: no strikethrough, no "updated", no dated note, no history. What changed and why goes in one comment on the spec, so the body stays the clean current version and the reasons stay findable. Tickets already cut from the section are checked against the new text and corrected where they no longer match.

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

**Every decision names where it came from**, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, a research or prototype path, a user-story number, a screen-contract row id. A decision with no source is written as "this spec's decision" (and, where the user confirmed it, say so).

An effort with a screen contract has one fixed subsection here, **API contract**: one entry per distinct operation in the contract's `calls` column — its request fields, its response fields, its failure cases — derived from the rows' `shows` and `on_failure`, each entry citing the row ids that use it. This is where a new project's OpenAPI document starts; the first ticket cut from the spec turns it into models and route signatures.

Do NOT include implementation file paths (the module you will edit, the function you will add) or code snippets. They may end up being outdated very quickly. Paths to source material — ADRs, research files, prototype directories, domain docs, test directories, shared contract locations — are what the tickets and the implementer read from: write them.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result: a browser page, an HTTP endpoint, or a function call ("Tests look at the result on the browser page."). The next sentence names the **seam** chosen in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed. Then:

- A description of what makes a good test (only test external behavior, not implementation details)
- The test layers this feature lands in, each with its directory and the precedent to copy (i.e. similar types of tests in the codebase); every ticket cut from this spec will name one of these layers as the place it is verified
- **How a test arrives at a state.** Per layer: what a test writes to put the system into a state, and what it cannot write. A state this feature's behaviour turns on, that the seam's write surface does not reach, gets a line of its own here: the mechanism that will reach it, and which builds carry that mechanism. The mechanism takes the form the repository's own testability rules allow; where those rules have no exit for one, say so — closing that is the repository's to do, not this spec's, and `to-tickets` cuts a *reach* ticket for it. Whoever cuts the tickets reads this section to know whether a criterion can be written at all, and one of them will own building each mechanism named here. With a screen contract, this section is its **mechanism registry**: every mechanism has a name of the form `seed:<state>` (the real backend put into a state through its own write surface, values taken from the handoff package's `data/fixtures.js`), `stub:<seam>-<script>` (an external seam answering by script) or `dev:<capability>` (a registered dev-only capability, outside the renderer), the contract's `reach` column names only entries from here, and the names the alignment ticket proposed are adopted or renamed here in one pass
- The commands to run before committing

## Out of Scope

A description of the things that are out of scope for this spec.

## Sources

Links to the first-hand material this spec was built from, one line per kind. Write "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":

- Wayfinder map
- Decision tickets (each named by the decision it settled)
- Upstream specs this one builds on
- ADRs
- Research files
- Prototype directories
- Handoff package (the look-and-copy baseline; `none` when the effort has no interface)
- Screen contract (the behaviour baseline, `docs/specs/<effort>/screen-contract.yaml`; `none` likewise)
- Domain docs
- Evidence (measurements, cost runs, real-call records)
- Test rules (the repo's TESTING.md or equivalent)

## Further Notes

Any further notes about the feature. When step 1 divided the work into several specs and the reference was not a map, the division lives here in the first spec: one line per spec, with its name, what it covers, its position in the order, and its link once published. A later spec in that division says here which spec carries it.

</spec-template>

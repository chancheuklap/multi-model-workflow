---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed. Use when a conversation, a map or a triaged issue has to become a spec, or a section of a published spec has to change."
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user for facts; just synthesize what you already know. A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. A call the sources leave open is decided as user rule 1 says: mark one you make "this spec's decision", and put one that is the user's to the user before you publish. That, and the division in step 1, are the only things you ask them.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run the `setup-matt-pocock-skills` skill.

## Process

1. If the user passed a reference (an issue number, a URL, a file path), read its full body and comments before anything else. When the reference is a published spec and one of its sections has to change, read [references/revising-a-spec.md](references/revising-a-spec.md) instead of the steps below. When the reference is a wayfinder **map**: read the map body; then walk **Decisions so far** and read each closed ticket's **resolution comment**; where a ticket links a prototype or a research file, read that through to its conclusion. The map's **Out of scope** carries into the spec's Out of Scope unchanged.

   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different **seam** and lands and demos on its own; where it can stay one spec, keep it one spec. A part may depend on a part before it: a product delivered in stages (a server registration, then the client that logs into it, then the work the client does) has no reading under which the later stages depend on nothing, and forcing it into one spec produces one nobody can read. What the dependencies may not do is run backwards or in a circle: every one points at a part earlier in the order, and the `## Specs` section writes that order down.

   When it is several, read `references/several-specs.md`.

   Done when every source the reference leads to has been read and you know which one spec this run writes, and, when it is several, the division is written where `references/several-specs.md` says and the user has confirmed it.

2. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

   When the effort has a **screen contract** (`docs/specs/<effort>/screen-contract.yaml`, written by the `write-screen-contract` skill), read `references/screen-contract-spec.md` before going on: it says what reading that contract asks here, and what the spec gains below. An effort with no screen contract goes on without it.

   Done when you know which existing modules and ADRs each decision touches, or that none exists yet, and, with a screen contract, every row's `gap` is `aligned`.

3. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one. The repository's `TESTING.md` says which test layers exist, which external boundaries may be stubbed and how tests run; the seam and `## Testing Decisions` draw on it.

A seam says where a test **observes**. Ask the other half in the same breath: for each state this feature's behaviour turns on, can a test put the system into that state through the seam you picked? Where the seam does not reach, say what would, and whether that thing ships.

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

**A decision that states what a script does is written with the script open.** Before a decision states what a script does (its exit code, a line it prints, the directory it runs from) or what a data file holds, open that script or file on the base branch, and name the function or the rows the statement rests on. A statement written from a report or from memory sends a worker into a `contract` child when the script says otherwise.

**A user story's conclusion is folded into the subsection that implements it.** A worker reads the Implementation Decisions subsections its ticket names and never a story, so a behaviour that is settled only in a story reaches nobody. Whatever a story decides about a control, a value, a transition or a failure is stated here, in the subsection that implements it, with the story number as its source; the screen contract's rows then cite the subsection, not the story.

Do NOT include implementation file paths (the module you will edit, the function you will add) or code snippets. They may end up being outdated very quickly. Paths to source material (ADRs, research files, prototype directories, domain docs, test directories, shared contract locations) are what the tickets and the implementer read from: write them.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result: a browser page, an HTTP endpoint, or a function call ("Tests look at the result on the browser page."). The next sentence names the **seam** chosen in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed. Then:

- A description of what makes a good test (only test external behavior, not implementation details)
- The test layers this feature lands in, each with its directory and the precedent to copy (i.e. similar types of tests in the codebase); every ticket cut from this spec will name one of these layers as the place it is verified
- **How a test arrives at a state.** Per test layer: what a test writes to put the system into a state, and what it cannot write. A state this feature's behaviour turns on, that a test cannot write through the seam, gets a line of its own here: the mechanism that will reach it, and which builds carry that mechanism. The mechanism takes the form the repository's `TESTING.md` allows; where it has no exit for one, say so: closing that is the repository's to do, not this spec's, and `to-tickets` cuts a *reach* ticket for it. Whoever cuts the tickets reads this section to know whether a criterion can be written at all, and one of them will own building each mechanism named here.
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
- Directories of prototypes
- Design package (the look-and-copy baseline; `none` when the effort has no UI)
- Screen contract (the behaviour baseline, `docs/specs/<effort>/screen-contract.yaml`; `none` likewise)
- Domain docs
- Evidence (measurements, cost runs, real-call records)
- Repository rules: `CODING_STANDARDS.md`, `TESTING.md`, the sections this spec relies on

## Further Notes

Any further notes about the feature. When step 1 divided the work into several specs and the reference was not a map, the division lives here in the first spec: one line per spec, with its name, what it covers, its position in the order, and its link once published. A later spec in that division says here which spec carries it.

</spec-template>

# Spec template

The body of the GitHub issue the To spec playbook (`../playbooks/to-spec.md`) publishes, and how one reference divides into several specs.

## Several specs from one reference

When specs divide by repository, the consumer spec's **Implementation Decisions** name the producer spec and where the producer's interface is read from.

When what you have read is several specs, this is the one judgement in To spec you hand to the user: list each spec's name, the decisions it covers by ticket name, the order they go in, and why the line falls there. Once the user confirms, write the division back to the map as a `## Specs` section, one line per spec: name, the decision tickets it covers, its position in the order, and its spec link once published. Then write the first spec only; publish it, fill its link into that line, and stop; tell the user to run To spec against the map again for the next one. When the map already carries a `## Specs` section, skip the judgement and write the first spec on it that has no link yet.

When the reference is not a map (an issue, a URL, a file, or the conversation itself), there is no map to write the division back to. Write it into the first spec's `## Further Notes` instead: one line per spec, saying what it is called, what it covers, its position in the order, and its link once published. Publish that first spec and stop; tell the user to run To spec next time with this spec's issue number. When the reference is a spec whose `## Further Notes` carries a division, write the first spec on it that has no link yet, and fill the link into its line through the Revising a spec playbook (`../playbooks/revising-a-spec.md`), since that spec is already published. When every line has a link, tell the user the division is fully written and stop.

## The template

Replace each section's guidance with the content.

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

**Every decision names where it came from**, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, the link of a research answer or verdict comment, or a prototype path. A decision with no source is written as "this spec's decision", citing what it rests on (and, where the user confirmed it, say so). What an ADR decides that shapes a decision is written into the subsection it shapes, citing the ADR: the worker reads the spec, not the ADR.

**A user story's conclusion is folded into the subsection that implements it.** A worker reads the Implementation Decisions subsections its ticket names and never a story, so a behaviour that is settled only in a story reaches nobody. Whatever a story decides about a value, a transition or a failure is stated here, in the subsection that implements it, with the story number as its source.

Do NOT include implementation file paths (the module you will edit, the function you will add) or code snippets. They may end up being outdated very quickly. Paths and links to source material (ADRs, research answer comments, prototype directories, domain docs, test directories, shared contract locations) are what the tickets and the implementer read from: write them.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

The first sentence says, in plain words a reader with no testing vocabulary understands, where a test looks at the result: a browser page, an HTTP endpoint, or a function call ("Tests look at the result on the browser page."). The next sentence names the **seam** chosen in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed. Then:

- A description of what makes a good test (only test external behavior, not implementation details)
- The test layers this feature lands in, each with its directory and the precedent to copy (i.e. similar types of tests in the codebase); every ticket cut from this spec will name one of these layers as the place it is verified
- **How a test arrives at a state.** Per test layer: what a test writes to put the system into a state, and what it cannot write. A state this feature's behaviour turns on, that a test cannot write through the seam, gets a line of its own here: the mechanism that will reach it, and which builds carry that mechanism. Where the repository's tests have no way to reach such a state, say so: closing that is the repository's to do, not this spec's, and To tickets cuts a *reach* ticket for it. Whoever cuts the tickets reads this section to know whether a criterion can be written at all, and one of them will own building each mechanism named here.
- The commands to run before committing

## Out of Scope

A description of the things that are out of scope for this spec.

## Sources

Links to the first-hand material this spec was built from, one line per kind. Write "none" for a kind that has none, so a reader can tell "nothing there" from "forgot to list":

- Wayfinder map
- Decision tickets (each named by the decision it settled)
- Upstream specs this one builds on, including an earlier spec the decision tickets cite as their basis
- ADRs
- Research answers (the ticket comments that hold them)
- Prototype directories
- Domain docs
- Evidence (measurements, cost runs, real-call records)

## Further Notes

Any further notes about the feature. When step 1 divided the work into several specs and the reference was not a map, the division lives here in the first spec: one line per spec, with its name, what it covers, its position in the order, and its link once published. A later spec in that division says here which spec carries it.

</spec-template>

---
name: to-spec
description: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user for facts — just synthesize what you already know. Step 1 names the one judgement you hand back to them.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

1. If the user passed a reference — an issue number, a URL, a file path — read it in full before anything else. When the reference is a wayfinder **map**: read the map body; then walk **Decisions so far** and read each closed ticket's **resolution comment**; where a ticket links a prototype or a research artifact, read that through to its conclusion. The map's **Out of scope** carries into the spec's Out of Scope unchanged.

   Then judge whether what you have read is one spec or several. Decisions that share a **seam** belong in one spec. Split only where a part needs a different **seam**, lands and demos on its own, and its implementation tickets depend on no other part — where it can stay one spec, keep it one spec.

   One spec: write it. Several: this is the one judgement in this skill you hand to the user — list each spec's name, the decisions it covers by ticket name, the order they go in, and why the line falls there. Once the user confirms, write the division back to the map as a `## Specs` section, one line per spec: name, the decision tickets it covers, its position in the order, and its spec link once published. Then write the first spec only; publish it, fill its link into that line, and stop — tell the user to run this skill against the map again for the next one. When the map already carries a `## Specs` section, skip the judgement and write the first spec on it that has no link yet.

2. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

3. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the user that these seams match their expectations.

4. Write the spec using the template below — with the `readable-docs` skill, and run its claim check before publishing — then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

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

**Every decision names where it came from**, at the end of the sentence or table row that states it: a decision ticket number, an ADR id, a research or prototype path, a user-story number. A decision with no source is written as "this spec's decision" (and, where the user confirmed it, say so).

Do NOT include implementation file paths (the module you will edit, the function you will add) or code snippets. They may end up being outdated very quickly. Paths to source material — ADRs, research files, prototype directories, domain docs, test directories, shared contract locations — are what the tickets and the implementer read from: write them.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

The first sentence names the **seam** confirmed in step 3: what is real on each side of it, and which external seams (third-party APIs, paid services) may be stubbed. Then:

- A description of what makes a good test (only test external behavior, not implementation details)
- The test layers this feature lands in, each with its directory and the prior art to copy (i.e. similar types of tests in the codebase); every ticket cut from this spec will name one of these layers as the place it is verified
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
- Prototype branches or directories
- Domain docs
- Evidence (measurements, cost runs, real-call records)
- Test rules (the repo's TESTING.md or equivalent)

## Further Notes

Any further notes about the feature.

</spec-template>

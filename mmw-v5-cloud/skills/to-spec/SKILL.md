---
name: to-spec
description: "Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed."
---

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user; just synthesize what you already know.

A spec is the last text a person checks before agents build from it unattended: whatever it leaves open, a worker decides alone at night, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module's seam, a data shape, the seam a test observes at) is yours: make it and mark it "this spec's decision". Call the Skill tool with "principle-never-block-on-the-human" for the decisions the sources leave open; put an unresolved owner decision to the user before publishing. Read a supplied issue with its full body and comments.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Call the Skill tool with "principle-anchor-every-reference" throughout the spec, and respect any ADRs in the area you're touching.

2. Call the Skill tool with "principle-model-the-domain" for the domain model. Sketch out the seams at which you're going to test the feature.

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

The seam is yours to decide, not the user's: they are not asked to confirm it.

3. Write the spec using the template below. Call the Skill tool twice, for "principle-write-for-where-it-is-read" and "principle-baseline-is-the-contract". Call the Skill tool with "technical-writing" and write the prose through it. The template is the structure. Then publish it to the project issue tracker. Give it the `mmw:spec` label and no queue or worker-grade label: a spec is a container for the tickets underneath it, not a piece of work. Before publishing, create missing labels with `python3 LABEL_SETUP`, where `LABEL_SETUP` is `../../tools/setup-mmw/scripts/labels.py` resolved from this skill's directory to an absolute path in the installed runtime. Run it from the consuming repository without `--migrate`. Read the published spec back to confirm its body and labels.

4. Call the Skill tool with "big-pics-little-words" to visualize the whole spec.

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

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>

---
name: to-spec
description: "Turn a discussion or the decisions on a settled Wayfinder map into a spec and publish it to the GitHub work issue: no interview, just synthesis of what you've already discussed."
---

# To spec

Use Open in [to-tickets](../to-tickets/SKILL.md#open) to open or reuse the work issue for this spec. When given a Wayfinder map, link it as a source and use a separate work issue for the spec.

This skill takes the current conversation context and codebase understanding and produces a spec. Do NOT interview the user; just synthesize what you already know.

A spec is the text the operator checks before agents build from it unattended: whatever it leaves open, the implementing agent decides alone, and whatever it states is built as written, including what nobody decided. So record decisions rather than make them. An engineering call the sources leave open (a module boundary, a data shape, the choice of test seam) is yours: make it and mark it "this spec's decision". Use [principle-never-block-on-the-human](../principle-never-block-on-the-human/SKILL.md) for the decisions the sources leave open. Before publishing, raise any decision only the operator can make. Read a supplied issue with its full body and comments. When the source is a Wayfinder map, follow `Decisions so far` to the relevant decision tickets and read `Result` in their bodies. Read the original report, evidence, approved prototypes and scope exclusions before drafting.

## Process

1. If you have not already explored the codebase, use [how](../how/SKILL.md) for the area this spec will cover. Use [principle-anchor-every-reference](../principle-anchor-every-reference/SKILL.md) throughout the spec, and respect any ADRs in the area you're touching.

2. Use [principle-model-the-domain](../principle-model-the-domain/SKILL.md) for the domain model. Sketch out the test seams for the feature.

A **test seam** is the public interface where a test observes behavior without reaching inside the implementation. Test through that interface.

Existing test seams should be preferred to new ones. Use the highest test seam possible. If new test seams are needed, propose them at the highest point you can. The fewer test seams across the codebase, the better - the ideal number is one.

Choose the test seam yourself.

3. Write the spec using the template below. Use [principle-write-for-where-it-is-read](../principle-write-for-where-it-is-read/SKILL.md) and [principle-baseline-is-the-contract](../principle-baseline-is-the-contract/SKILL.md). Use [technical-writing](../technical-writing/SKILL.md) and write the prose through it. The template is the structure. The User Stories section says how an observable result is written for the project's verification skill. [Review and publish the draft](#publish).

4. Use [big-pics-little-words](../big-pics-little-words/SKILL.md) to visualize the whole spec.

For a spec alone, stop after showing it. If the operator requests a plan, or the approach, dependencies or checks across phases still need planning, run [Multi-phase plan](../poteto-mode/playbooks/multi-phase-plan.md) with the work issue and reviewed spec. Pass the reviewed text when the spec is a draft. Tell the playbook if tickets were also requested. For tickets requested directly from the spec, give [to-tickets](../to-tickets/SKILL.md#split) the spec and work issue.

## Publish

Run [ambiguity-scan](../ambiguity-scan/SKILL.md) at the **Spec** stage with the complete draft and the discussion it came from, including any source decisions and approved prototypes. Use the report when settling the draft. If the scope came from an approved plan, reuse the agreed scope and link its plan issue when available. For a draft-only request, return the reviewed draft.

Use Update in [to-tickets](../to-tickets/SKILL.md#update) to publish the spec on the work issue returned by Open. Set its type to `mmw:spec`. Preserve the original report and its evidence. Read the work issue back to confirm the spec text and the issue labels. When the source is a Wayfinder map, link it from the spec issue and add the published spec link to the map's `Destination`. Close the map if the published spec fulfills its destination. Return the issue URL to the calling step.

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

If the project uses a project-local `verify-<app>` skill, its scripts drive the real app and assert what a person can observe, by copying a sentence from these stories. When a story states such a result, write that result as its own sentence, one a script can copy unchanged. That sentence is the expected result. This spec does not create `verify-<app>` and does not edit its `features/` map.

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

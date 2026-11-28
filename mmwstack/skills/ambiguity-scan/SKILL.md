---
name: ambiguity-scan
description: "Review a draft spec, multi-phase plan, or execution ticket batch once with a fresh read-only reviewer before publishing or handoff."
---

# Ambiguity scan

The main chat dispatches one fresh, read-only general-purpose reviewer for the stage under review. Follow [Subagents](../mmw-mode/SKILL.md#subagents) and [host-dispatch](../host-dispatch/SKILL.md). Use the model and settings from the current host's `judgment and prose` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file).

## Dispatch

1. Match the stage to its single reference below. Give the reviewer the operator's goal, the work issue, the draft, its upstream sources, the path to `## Reviewer contract` in this file, and only the matching stage reference. Do not send the other two stage references.

| Stage | Reference | Inputs to pass |
| --- | --- | --- |
| Spec | [references/spec.md](references/spec.md) | Operator's goal, work issue, complete spec draft, and upstream sources (discussion, Wayfinder map and decision ticket `Result`s, approved plan, approved prototypes) |
| Plan | [references/plan.md](references/plan.md) | Operator's goal, work issue, complete plan draft after `check-plan.mjs`, and upstream sources (agreed spec or design, decision comments, approved prototypes) |
| Ticket | [references/ticket.md](references/ticket.md) | Operator's goal, work issue, single ticket draft or the entire ticket batch together, and upstream sources (checked plan, spec, original work issue, discussion, approved prototypes) |

2. For a batch of tickets drafted together, send the whole batch to one reviewer.
3. Wait for the reviewer's report, settle its findings in the draft, and continue the calling step.

**Single-pass rule.** Scan each stage's draft once. After settling the report's findings in the draft, move straight to the calling step's next action. Never scan the revised draft again. Only an explicit operator request authorizes another scan.

## Reviewer contract

You are a fresh, read-only document reviewer. Read this contract and only the stage reference named in your brief. Write nothing to files or the issue tracker.

**Document-only boundary.** Judge only whether the draft inherits its upstream sources without loss or drift, follows the stage's writing rules, and reads clearly to a fresh reader. Leave design optimality, architecture choices, codebase feasibility, and speculative out-of-scope edge cases outside this review.

**Report format.** Return findings to the main chat grouped into two sections, omitting empty sections:

- `## Blocking` for defects the author must settle before publishing or handoff (dropped or drifted upstream content, missing required stage elements, unflagged open product choices, broken slicing or dependencies, or ambiguity that forces a fresh reader to guess).
- `## Clarity` for high-signal writing fixes the author can polish quickly (vague acceptance terms, glossary or canonical issue/ticket name mismatches, unanchored pronouns or back-references such as "the above" or "this", em dashes, mid-sentence colons, or AI filler). Keep these brief and never promote style nitpicks to `Blocking`.

For each finding, quote the draft passage (or name the missing item), cite the upstream source line or stage rule it violates, state what breaks for the next reader, and give the direct fix. If no real defect exists, return `No findings.`

---
name: to-tickets
description: Open or update a GitHub work issue from the first report through the result. Draft one execution ticket or break a plan, spec, or discussion into independently verifiable tickets with their direct blockers.
---

# To Tickets

Use Open for a new repository task or to publish a checked plan, Update as the work progresses, and Split to turn a checked plan, an agreed spec, or a settled discussion into tickets. All three use the [issue template](#issue-template).

## Open

If the caller supplies only an open PR, follow its execution ticket link. Read the supplied or linked issue and its comments. If neither the input nor the PR identifies the team's work issue, look for one that covers the same outcome. Reuse the matching work issue on follow-ups and retries. When the source is somebody else's report, link it from the team's work issue. Leave the reporter's issue intact.

If there is no work issue yet, open one with what is known now. A problem can start with just its title, type label, and Problem. Include evidence already at hand.

For an already agreed assignment, draft an execution ticket and open its reviewed body directly with the approved scope, labels and relationships. Read back the issue and return its URL.

When publishing a plan or child tickets, use the spec issue as their parent. If the spec is unpublished, publish the reviewed draft on the original work issue, or call [to-spec](../to-spec/SKILL.md) for the spec alone if it still needs writing. For a checked plan, open or update its plan issue under that spec using the [Plan](#plan) field. Read back the plan issue and its parent, then return the plan issue URL.

## Update

Use the same issue whenever the work materially changes. Keep the current findings, agreed work and outcome in the body. Add a comment for new evidence, discussion and the decision it produced, or a change of direction and why. When work changes hands, record who took which assignment and what remained. Link the comment from the body when it holds the evidence or reasoning. Use links the next agent and the operator can open.

When a standalone problem becomes one independently verifiable deliverable, draft the execution ticket on that issue using the template below. Keep the original report and evidence. Once its scope is approved, publish the reviewed draft on the same issue as `mmw:ticket`. Use the same drafting step when its execution scope changes. For several deliverables, use [Split](#split).

Change only labels that describe this workflow. Create a missing label on first use. Read back the changed body, comment or labels. Return a `ready-for-agent` ticket to the execution playbook when its direct blockers clear. Close at the outcome the issue calls for. For a requested merge, record a verified stack handed to the operator as awaiting merge. Close the parent issue when its child tickets have delivered the agreed outcomes.

## Draft an execution ticket

Use [principle-anchor-every-reference](../principle-anchor-every-reference/SKILL.md) for ticket titles and descriptions, and respect ADRs in the area you're touching. Use [principle-write-for-where-it-is-read](../principle-write-for-where-it-is-read/SKILL.md) and [principle-baseline-is-the-contract](../principle-baseline-is-the-contract/SKILL.md). Use [technical-writing](../technical-writing/SKILL.md) and write each ticket's prose through it. The issue template is the structure.

Avoid specific implementation file paths or code snippets: they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

When the draft is ready, run [ambiguity-scan](../ambiguity-scan/SKILL.md) at the **Ticket** stage before presenting it. For a batch, finish every draft first and review the set together. Use the scan to resolve open points against the source, repository and approved decisions. An approved scope can be published directly. For new scope, show what will be delivered and get the operator's decision before publishing. Reuse the review when publishing the same draft.

## Issue template

Use the same template for a question, a spec issue, a plan issue, a standalone execution ticket, and a child ticket. Include every **Must have** field. Add an **Optional** section when its condition holds. Publish the filled headings and content, without annotations or empty sections.

<issue-template>

**Title (GitHub field). Must have.** Name the affected behavior, the question to answer, or the outcome this ticket delivers.

**Labels (GitHub field). Must have.** Keep one type label. Use `mmw:problem` during intake and investigation, `mmw:spec` for a spec issue, `mmw:plan` for a plan issue, and `mmw:ticket` for an execution ticket. Spec and plan issues have no queue label. An execution ticket carries `ready-for-agent` for agent work or `ready-for-human` for a human action. Use `needs-triage` when a problem or ticket awaits the operator's decision. Use one queue label at a time.

## Problem

**Must have.** State what the user observed, wants, or needs answered. Keep the original report when the issue changes purpose. On a child ticket, name the part of the parent problem it resolves. The spec's Problem Statement or the plan's opening paragraph serves this field on its issue.

## Evidence

**Optional.** When a report, reproduction, trace, measurement or prototype bears on the problem, state what it shows. Link the source or quote the relevant observation. Keep the original evidence when the work issue becomes a spec issue or an execution ticket.

## Findings and decisions

**Optional.** When investigation or discussion settles something, record the finding or decision, why it holds, and the evidence or discussion it came from. Keep a decision made during spec review with the spec.

## Spec

**Must have for a spec issue. Optional otherwise.** When this issue holds the reviewed spec, publish the complete draft supplied by [to-spec](../to-spec/SKILL.md) under its own headings in place of this heading and Problem. Carry the original report into Problem Statement. When this ticket draws on a separate spec, link the relevant user stories or decisions. A parent link can carry that reference.

## Agreed work

**Must have for an execution ticket. Optional otherwise.** For implementation, describe the end-to-end behaviour this ticket makes work, from the user's perspective. State the agreed approach and scope boundaries. For a human task, name the action the person must take.

## Plan

**Must have for a plan issue or a ticket split from a plan. Optional otherwise.** On the plan issue, publish the complete checked plan under its own headings. On a ticket split from it, link the plan issue and name the phase or outcomes the ticket draws on. A standalone ticket can give its short agreed sequence here.

## Acceptance criteria

**Must have for an execution ticket. Optional otherwise.** Write a checkbox for each observable result and how to demonstrate it. Check it when the evidence shows it passed.

- [ ] <Action or check and its expected result.>

A ticket that changes a surface a person uses names the feature-file path in the project's `verify-<app>/features/` directory when it exists. If the user story names an expected result, copy that sentence unchanged. Link any approved prototype the ticket must match. This step does not write the script.

When getting it wrong is wrong **silently** (money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default), name the observation that distinguishes success from that failure.

## Parent

**Must have for a plan issue or a child ticket. Optional otherwise.** Set the spec issue as the direct GitHub parent. The native sub-issue relationship supplies this field on a plan issue. On a child ticket, link the spec and the part of its scope this ticket delivers.

## Blocked by

**Optional.** Name each direct blocker and the result it supplies. Set GitHub's native **Blocked by** relationship. Omit this section when the relationship already identifies the blockers.

## Handoff

**Must have once a code ticket has a PR. Optional otherwise.** As soon as the PR opens, record its URL here. At dispatch or when an assignment changes hands, name the agent or person, their assignment and the next action. Link the relevant review when the next assignee needs it. If work awaits the operator, state the decision or action needed.

## Result

**Must have at close. Optional while open.** At handoff, record any result already verified. For a question, give the answer and its evidence. For delivery, state what actually landed or was verified and say what remains. Link the code ticket's PR and its proof. For work completed without a PR, link the artifact or evidence that establishes the result. For a parent issue, link the outcomes of its child tickets.

</issue-template>

## Split

Read [Split a discussion, spec or plan](references/split.md). Start at **From a checked plan** to split its remaining work into tickets, **From a spec or discussion** for tickets requested directly, or **Publish** for reviewed ticket drafts. The operator authorizes execution. The execution playbook assigns the tickets and opens the corresponding PR for each code ticket.

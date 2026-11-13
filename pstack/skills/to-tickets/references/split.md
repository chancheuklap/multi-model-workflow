# Split a spec or plan

Break a spec or plan into **execution tickets**. Each ticket delivers one independently verifiable outcome and names its direct blockers.

## From a checked plan

Read the checked plan, its source spec or agreed scope, and any existing tickets. If you start from a plan issue, follow its parent to the spec. Use the plan's phases, intended outcomes, agreed approach, dependencies and checks as the source for the split.

1. Account for any outcomes already demonstrated by the evidence. Use the [vertical-slice rules](#vertical-slices) to divide the remaining implementation work into independently assignable tickets. A phase can contain several such outcomes, and several plan steps can contribute to one. Give a shared prerequisite its own ticket when it delivers a result the next ticket can use and verify. For a human action, name what the person must do and how to confirm the result.
2. Under **Plan**, identify the checked plan and name the phase or outcomes the ticket draws on. Under **Agreed work**, describe what it delivers and the decisions it inherits from **Build**. Under **Acceptance criteria**, pair the expected result from **You see** with the relevant checks from **Verify**. Carry forward any approved prototype and **Review gate** that apply. If the ticket delivers a user story's expected result, copy that sentence unchanged.
3. Trace the prerequisite results in each phase's **Depends on** across the proposed tickets. A prerequisite inside one ticket stays in that ticket. Add a direct blocker between tickets only when one needs the other's result before it can start. Tickets can share a phase or a parent issue and still proceed independently.

Check the breakdown against the plan. Each remaining change belongs to one ticket, and every ticket identifies its source and how to prove its result. Reuse matching tickets. If the evidence already demonstrates every outcome, return it. Otherwise continue at **Draft the tickets**.

## From a spec

Work from the agreed spec and the discussion behind it. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments. If a plan was requested, or the approach, dependencies or checks across phases still need planning, use the existing plan or run [Multi-phase plan](../../poteto-mode/playbooks/multi-phase-plan.md) for the plan alone. Resume at **From a checked plan**, or draft the agreed ticket directly if the playbook skips the plan for an obvious change. If the operator requests tickets directly from the spec, identify the slices below.

If you have not already explored the codebase, use [how](../../how/SKILL.md) for the area these tickets will change. Use [principle-anchor-every-reference](../../principle-anchor-every-reference/SKILL.md) for ticket titles and descriptions, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

Break implementation work into **vertical slices**. Reuse existing tickets whose outcomes already match.

### Vertical slices

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Use [principle-separate-before-serializing-shared-state](../../principle-separate-before-serializing-shared-state/SKILL.md) before settling the direct blockers, and before sequencing a wide refactor whose tickets would write one shared symbol.

For each ticket, name its **direct blockers**. Each must supply a result the ticket needs before work can start.

For a coordinated internal change where all callers can migrate together, use the [Refactoring playbook](../../poteto-mode/playbooks/refactoring.md). When old and new forms must coexist, use the following sequence.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

## Draft the tickets

Use the issue template for each outcome. Keep the evidence and decisions specific to that ticket with its draft. Link the shared scope on the parent. Run [ambiguity-scan](../../ambiguity-scan/SKILL.md) at the **Ticket** stage once for the finished set. Use the scan to resolve open points against the source, repository and approved decisions. Choose the ticket sizes and dependencies yourself. Record consequential engineering choices and their reasons in the affected drafts.

Show the proposed breakdown in delivery order: what each ticket delivers, what it depends on, and who will do it. If a choice about product behaviour, priorities or scope still belongs to the operator, ask one question. Name the affected outcome, the options and your recommendation. Apply the answer to the drafts before raising the next unresolved choice.

For a draft-only request, return the proposed breakdown. Get the operator's approval for the resulting scope before publishing the tickets. When the operator has already approved these boundaries and outcomes, use that approval.

## Publish

For a standalone problem with one agreed result and no separate spec or multi-phase plan, publish the reviewed ticket on the same work issue with `mmw:ticket` and its queue label. Read it back and return its URL.

For work drawn from a spec or plan, use the spec issue as the parent. Publish a reviewed spec with [to-spec](../../to-spec/SKILL.md#publish) or a checked plan with Open in [to-tickets](../SKILL.md#open) if needed. In each ticket drawn from the plan, link its plan issue and name the phase or outcomes that ticket delivers.

Publish child tickets in dependency order (blockers first) so you can link each ticket to its direct blockers. Reuse each matching execution ticket or open one for that outcome. Each ticket carries `mmw:ticket` and its queue label. Attach each as a direct GitHub sub-issue of the spec issue. Set GitHub's native **Blocked by** relationship for each direct blocker.

Read each published ticket back to confirm its body, labels, parent issue and direct blockers match the approved drafts. Return the ticket links in delivery order and the parent issue link when there is one. The **ticket frontier** consists of open execution tickets whose direct blockers are all complete. On the operator's authorization, give the execution playbook the `ready-for-agent` tickets on that frontier. It opens or reuses one corresponding [pull request](../../poteto-mode/playbooks/opening-a-pr.md) for each code ticket and links the two. A human action or a read-only result can be recorded on its work issue without a PR.

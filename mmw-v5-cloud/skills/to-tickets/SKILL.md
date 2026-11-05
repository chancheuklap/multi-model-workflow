---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Use **principle-anchor-every-reference** for ticket titles and descriptions, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets. Use **principle-write-for-where-it-is-read** and **principle-baseline-is-the-contract**. Use **technical-writing** and write each ticket's prose through it. The issue template is the structure.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

The project's verification system is the project-local skill `verify-<app>`: a `features/` map of how a person reaches each part, plus the scripts that drive the real app. A ticket that changes a surface a person uses names the feature-file path in that skill's `features/` directory and copies the spec sentence unchanged. The worker writes the drive script beside that skill, asserts that same sentence, and commits both. A ticket that names neither does not get a script. This step does not write the script.

Use **principle-separate-before-serializing-shared-state** before settling the blocking edges, and before sequencing a wide refactor whose tickets would write one shared symbol.

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

For each ticket an agent works, propose `junior-worker` or `senior-worker` and a reason. `junior-worker` is the default, and a ticket goes to `senior-worker` when getting it wrong is wrong **silently** (money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default), because none of those fail on the day they are written. A ticket whose supplied test seam already names a precedent to copy stays on `junior-worker`.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

### 4. Scan for ambiguities

Save the drafted tickets in a temporary directory created with `mktemp -d`. Before presenting the breakdown, write a prompt for a fresh read-only subagent to scan the source plan, spec, or conversation and those drafts using [Ambiguity scan](references/ambiguity-scan.md). Include the resolved reference path, approved source, and drafted ticket text. Save the prompt to FILE, run `dispatch.sh spawn researcher --prompt FILE --host HOST`, and send the printed assignment as [Dispatch](../dispatch/SKILL.md) describes. Wait for its one-pass result. If the host cannot run subagents, run the same scan yourself.

Bring the scan's questions into the quiz below, alongside the affected tickets, with their options, recommendation, and why the answer matters. Do not open a separate question round.

### 5. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Worker**: the proposed `junior-worker` or `senior-worker` label and its reason; for work only a person can do, state `ready-for-human` instead.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?

Iterate until the user approves the breakdown. Write every agreed clarification into the affected drafts before publishing.

### 6. Publish the tickets to the configured tracker

- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native blocking relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues. If the source was an existing issue, make each ticket its sub-issue (tracker doc's operation).

Before publishing, create missing labels with `python3 LABEL_SETUP`, where `LABEL_SETUP` is `../../tools/setup-mmw/scripts/labels.py` resolved from this skill's directory to an absolute path in the installed runtime. Run it from the consuming repository without `--migrate`.

Each ticket carries `mmw:ticket`. A ticket an agent works also carries `ready-for-agent` and exactly one approved worker-grade label, `junior-worker` or `senior-worker`. A ticket only a person can act on carries `ready-for-human` instead, and no worker-grade label. Queue labels are mutually exclusive: work awaiting the owner's decision stays in `needs-triage` until the owner releases it. Planned implementation tickets carry neither `bug` nor `enhancement`.

Read each published ticket back to confirm its body, labels, parent and blocking edges match the approved drafts. A parent spec carries `mmw:spec` and no queue or worker-grade label.

Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- A reference to each blocking ticket, or "None (can start immediately)". Omit this section when blockers were set as native edges.

</issue-template>

In either form, avoid specific file paths or code snippets: they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker — edges as text in one file per ticket locally, or native blocking links on a real tracker.
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets** — tracer-bullet vertical slices, each declaring the tickets that **block** it.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests) — vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges** — the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

Sharpen each ticket's acceptance criteria into **gates** — see the `<gate-rules>` block under the templates. Every criterion either carries a `CHECK:` / `EXPECT:` pair or a `MANUAL: <adjudicator>` line; a bare prose criterion is not a gate.

**Grade** each ticket `worker:junior` or `worker:senior` — which tier of worker should land it. The grade only ever moves up once work has started; how it escalates belongs to the orchestration skill, not here.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change — rename a column, retype a shared symbol — whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket — green is promised only there.

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **Grade**: `worker:junior` or `worker:senior`
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Gates**: each acceptance criterion with its `CHECK:` / `EXPECT:` or `MANUAL:` line

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct — does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- Is each grade right? The user calibrates grades here; this is the one place a grade can move down.

Iterate until the user approves the breakdown.

### 5. Publish the tickets to the configured tracker

Publish the approved tickets. **How** depends on the tracker `/setup-matt-pocock-skills` configured — the tickets are the same either way, only the shape of the blocking edges changes:

- **Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Each file's "Blocked by" lists the numbers/titles it depends on. Use the per-ticket file template below — one ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Blocking edges are **native dependencies**, never body text: on GitHub, add each edge with the command in the issue-tracker doc's "Wayfinding operations" section (`gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where the id is the blocker's numeric database id from `gh api repos/<owner>/<repo>/issues/<n> --jq .id`). A `Blocked by:` line in the body is not an edge — a closed blocker must flip the child to unblocked without anyone editing text. Apply the `ready-for-agent` triage label unless instructed otherwise — the tickets are agent-grabbable by construction — and the ticket's grade label (`worker:junior` / `worker:senior`; create the label with `gh label create` if the repo lacks it). When the tickets came from a parent issue, attach each published issue to it as a **sub-issue** (`gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>`, the same numeric database id used for blocking edges). The orchestration skill reads the ticket set through that endpoint and nothing else: a ticket left unattached is a ticket nobody will ever dispatch.

Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue. Attaching the tickets to it as sub-issues (step 5) is the one exception — that writes the link, not the parent's body or state.

<local-ticket-template>

# <NN> — <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list.

**Blocked by:** the numbers/titles of the tickets that gate this one, or "None — can start immediately".

**Status:** ready-for-agent

**Grade:** worker:junior | worker:senior

- [ ] Acceptance criterion 1
  CHECK: <non-interactive command>
  EXPECT: <success marker printed only when every assertion passed>
- [ ] Acceptance criterion 2
  MANUAL: <adjudicator>

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective — not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
  CHECK: <non-interactive command>
  EXPECT: <success marker printed only when every assertion passed>
- [ ] Criterion 2
  MANUAL: <adjudicator>

</issue-template>

Blocking edges and the grade are not body text on a real tracker: edges are native dependencies, the grade is a label (step 5).

<gate-rules>

A **gate** is one acceptance criterion made decidable: an observable outcome plus a check that can honestly fail. Two shapes:

- **Runnable** — two indented lines under the criterion. `CHECK:` is a non-interactive command. `EXPECT:` is the marker that must appear in its output. The gate passes on both conditions at once: exit code 0 **and** the output contains the marker. The worker appends a third line, `EVIDENCE:`, when the gate passes — the smallest decisive slice of the check's output.
- **Manual** — one indented line, `MANUAL: <adjudicator>`, naming who decides. No `CHECK:` / `EXPECT:`. Write a criterion this way only when no command can observe the outcome; never dress a manual judgement up as a runnable check.

Authoring rules for runnable gates:

- Observe the outcome directly: the check reads the artifact, service, or measurement the criterion names — not a proxy.
- The marker is success-only: the command performs every assertion, exits nonzero on any failure, and prints the marker only after all of them pass.
- A negative assertion (something is absent) is trusted only after the same check has failed against a known positive; a wrong path or a malformed pattern otherwise reads as clean absence.
- A number given in the ticket is measured independently: the check computes the value from source data and applies the acceptance rule itself; the given number is never its own expectation.
- Evidence is the smallest decisive output, never a full log.

Self-test for the format (one honest gate that fails, one broken gate that always "passes"): the `self-check` skill's `reference/gate-examples.md`.

</gate-rules>

In either form, avoid specific file paths or code snippets — they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

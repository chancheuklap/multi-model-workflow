---
name: mmw-to-tickets
description: Break a published spec into tracer-bullet tickets, each declaring its blocking edges. Use when the user asks to split tickets after a spec is published.
---

# To Tickets

Break a published spec into a set of **tickets** — tracer-bullet vertical slices, each declaring the tickets that **block** it.

The spec issue holds identity. Each tracer-bullet ticket is one child issue. That issue holds the summary, the plan-path command, blocking edges, and artifact refs. `$mmw:mmw-to-plan` later writes the plan file the command prints.

The caller passes `<spec issue number>`. Stop if it is missing. Stop if that spec issue does not have `ready-for-agent` — the user has not approved that spec for publish; go back to `$mmw:mmw-to-spec`.

Before any write:

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>`. Use the name this skill or the caller already gave; with none in hand, name it after the work in this repo's own branch-naming shape, and say which name you took |
| Task branch already there | None of the above holds | Use the current branch |

## 1. Gather context

`mmw artifact path spec` prints the spec path; read that file. `gh issue view <spec issue number> --comments` for the issue body and comments. Read `artifact_refs` on the spec. Stop if that field is missing.

Resolve each artifact-ref line as `$mmw:mmw-wayfinder` specifies for Required materials. `none` or `[]` means skip. Copy into this ticket only the refs this ticket consumes. Write `none` when there are none.

If a prototype index is missing its question, walkthrough conclusions, chosen artifacts, rejected constraints, mounted wiring, or long-lived evidence, go back to `$mmw:mmw-prototype` to fill the gap; write `none` for a field that has none.

## 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change." When the materials do not cover the code, read the entry points, callers, and tests in range yourself. Several independent angles: `$mmw:mmw-research`. It returns a README path. Read that index and the files it lists. Put those facts into the tickets that consume them.

When this spec came from a prototype, read `## Mounted wiring` in its `README.md`. Every site it lists gets a prefactor ticket that removes it; the prototype files themselves stay where they are. `none` means skip.

If nothing is worth a prefactor ticket, go to step 3. Do not invent a ticket to fill this step. Prefactor tickets go first.

## 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests) — vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is one behaviour a `worker` can take end to end
- Any prefactoring should be done first

</vertical-slice-rules>

Give each ticket its **blocking edges** — the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

Write each acceptance criterion so a later check can pass or fail it:

1. Observable external behaviour, from a confirmed spec seam or a user-visible UI. Not internals.
2. Exact values (numbers, copy, state names, field names) copied from the spec or the chosen prototype artifact. No "appropriate", "correct", or "as expected".
3. One behaviour per criterion, independently true or false. Split compounds.
4. Each criterion names where it is verified: a test on a confirmed spec seam, or a human browser check. If you cannot name that place, the spec is missing a decision — stop and return to `$mmw:mmw-to-spec`. Do not invent it.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change — rename a column, retype a shared symbol — whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket — green is promised only there.

## 4. Quiz the user

Number in dependency order, from `01`, blockers first. For each ticket, show:

- **Title**: short descriptive name. This is also the source of the plan filename slug
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Acceptance criteria**: the criteria from step 3. The user must see them to approve this list

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct — does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- Is each acceptance criterion the observable result they want, with the exact values right?

Iterate until the user approves the breakdown. A yes here confirms this ticket breakdown. It does not replace the shared-understanding or spec confirmations.

## 5. Publish the tickets

One issue per ticket. Do not apply `ready-for-agent` here — that label waits on plan review. Do NOT close or modify the spec issue.

`mmw artifact path scratch --sub outbox/ticket-<NN>.md` prints a path; write the body there. Publish in dependency order, blockers first: `--blocked-by` needs ids that already exist. `mmw issue frontier` later lists children by ascending issue number, so this publish order is the start order.

```bash
mmw issue create --title "<title>" --body-file <that path> \
  --parent <spec issue number> --blocked-by <id,id>
```

Keep each new id. Omit `--blocked-by` when there are no blockers.

<issue-template>

## Parent

A reference to this batch's spec issue.

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list.

## Plan

```bash
mmw artifact path plan --sub <NN>-<ticket-slug>.md
```

`<NN>` is the two-digit number from step 4. `<ticket-slug>` is an English kebab of the Title, three or four words, lowercase letters, digits, and hyphens. `$mmw:mmw-to-plan` writes the file; this command reserves the path.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Artifact refs

- category=<category> name=<name-segment>

Add `issue=<number>` or `sub=<subpath>` on the same line when that artifact has them. Write `none` when there are none.

## Blocked by

- A reference to each blocking ticket, or "None — can start immediately".

</issue-template>

In the body, avoid specific implementation file paths or code snippets — they go stale fast, and they belong in the plan. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note the chosen artifact. Trim to the decision-rich parts — not a working demo, just the important bits.

After the user approved the list and every ticket is published, report the tickets. Ask: write plans, or stop here.

---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Skip this step only when the spec's Implementation Decisions already name the module or directory every ticket writes to. Otherwise you cannot fill in **Owns**, and one directory-level `ls` or `git ls-files` is enough.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Any prefactoring should be done first

</vertical-slice-rules>

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

### 4. Write each acceptance criterion

Three rules bind how each one is worded:

1. Observable external behaviour, from the spec's seam or a user-visible UI. Not internals.
2. Exact values (numbers, copy, state names, field names) copied from the spec or the chosen prototype artifact. No "appropriate", "correct", or "as expected".
3. One behaviour per criterion, independently true or false. Split compounds.

**A criterion is decided by a command, or it is not a criterion.** Everything under `## Acceptance criteria` is run by machine and re-run by the verifier, and that is what makes "it passed" a fact rather than the opinion of whoever wrote the code. Most of what you want to say about the work does not belong there. Ask these five in order and stop at the first yes:

1. **Is the rule a comparison — equal, matches, counts, over a threshold — against something a machine can reach?** It is a criterion. Write its `CHECK:` and `EXPECT:`.
2. **Is the rule a judgement, against something a machine can reach?** Whether an interface is deep rather than a pass-through, whether a passage says enough, whether an error message tells the caller what to do next, whether the test behind a criterion could ever have failed. Code review decides these — its `Standards` axis for how the code is written, its `Spec` axis for whether it matches what was asked, its `Tests` axis for whether the cases a `CHECK:` names are worth trusting — in a session other than the one that wrote the code. Leave it out of `## Acceptance criteria`: a judgement left there has only its own author to decide it, which is the one thing that section exists to prevent.
3. **Is the property a person's reaction?** Whether a newcomer knows what to do, whether the wording lands, whether a morning page is legible at a glance. The person is the instrument, not a fallback judge: no agent can stand in, because the agent is not who is being measured. It becomes its own ticket, of kind *reaction* — see **Work only a person can do** below.
4. **Could a machine decide it, if only it could reach the thing?** A signed installer on a clean machine, a login against the real provider, a notification arriving on a phone. Its own ticket as well, of kind *reach*. Many of these mean the pipeline is missing a capability, not that the user owes work.
5. **Is it a choice rather than a check?** No true or false, only a preference, and the answer decides what to build next rather than whether what was built is right. Pick a default, build on it, and record the choice in the closing comment. When nothing can proceed until someone chooses, that is a decision ticket, asked before this batch is written rather than scheduled after it.

If no command exists because the spec never decided how this is verified, stop and return to `/to-spec`. Do not invent it.

Every criterion is four lines, and carries a number you assign as you write it and never renumber. A criterion whose premise later disappears is taken out of the section rather than left there without a command; the number is not reused, and the closing comment says what became of it.

```
- [ ] AC1: POST /projects with a name that already exists returns 409 and error name-duplicate
  CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
```

Derive `CHECK:` and `EXPECT:` from the spec; do not invent either:

- `CHECK:` comes from Testing Decisions — its layer, that layer's directory, and the precedent it names. Open the precedent, copy its framework and its single-file invocation, then aim that at the file and case this ticket adds.
- `EXPECT:` is a **success-only marker**: the line the precedent prints only when it passed. Run the precedent once and copy that line. `ok`, `passed` or `done` on their own also appear in failing output; take the whole counted line.
- A criterion that compares an interface against a downloaded handoff package gets `CHECK: uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --baseline <handoff package dir> --impl <url> --scenes <name,name> --max-pct 1` and `EXPECT: PARITY OK <n>/<n>`.

`CHECK:` takes the object it checks from one of two places: this ticket itself — the number comes from `$MMW_TICKET`, or from the branch name `issue-<n>` — or something this ticket names by number. When the objects only exist at run time, walk the tracker's native relationships out from an anchor the ticket names: `gh api repos/{owner}/{repo}/issues/<n>/sub_issues`. A `CHECK:` must not search for its own object; searching and taking the first hit (`gh issue list --search … | head -1` and its kind) checks whatever the search happens to return, and often cannot fail at all.

`CHECK:` brings the state it needs and puts back the shared state it changed. Criteria run one at a time in ledger order, each in its own shell with cwd fixed at the repository root, so `cd` cannot reach another one — but the branch, the ticket and the working tree are shared, and `--reverify` runs every criterion a second time. Switch a branch and switch it back; reopen a ticket the next criterion needs open; stop a server you started.

Write the command on the `CHECK:` line when it fits there. When it does not, leave that line empty after the colon and open a fenced code block on the next line: the fence holds the command, and nothing inside it is read as a criterion or an attribute, so it may contain blank lines, backtick fences and lines beginning `- [ ]`. A flush-left continuation with no fence is a parse error.

**Work only a person can do is its own ticket, not a criterion on someone else's**, and you split it off here, while writing the ticket, not when closing it. A criterion no agent can decide leaves its ticket unable to finish; so the ticket that produces the thing stays an agent's, and the looking becomes a second ticket blocked by it.

Write one such ticket per thing to be looked at, labelled `ready-for-human`. It is shorter than the template below and holds five things only:

- **Parent**.
- **Which kind**: *reaction* or *reach*, in one word. A *reach* ticket adds one line naming what would retire it — a test account, a spare device, a runner. This is the only exit in the pipeline that owes no account to a machine, so it attracts whatever the writer did not want to think about; being unable to name the kind is the sign that the thing belongs at question 1, 2 or 5 instead.
- **What to look at**: a link that opens, not a command to run. This is read in the morning, on a phone, by someone carrying none of your context.
- **What makes it right**: the standard to judge against, so the answer can be something other than "I couldn't say".
- **Blocked by**: the ticket that produces the thing. This is the edge that matters most in the batch — wrong, and the person is sent to look at something that does not exist yet.

This step is done when every criterion on every ticket carries a number, a `CHECK:` and an `EXPECT:`, and everything that stopped at question 2, 3, 4 or 5 has landed where that question sends it.

### 5. Give each ticket its blocking edges

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

### 6. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?

Iterate until the user approves the breakdown.

### 7. Publish the tickets to the configured tracker

Publish the approved tickets. **How** depends on the tracker `/setup-matt-pocock-skills` configured; the tickets are the same either way, only the shape of the blocking edges changes:

- **Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Each file's "Blocked by" lists the numbers/titles it depends on. Use the per-ticket file template below: one ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native blocking / sub-issue relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues. Apply the `ready-for-agent` triage label to every ticket an agent works; the ones a person must judge carry `ready-for-human` instead.

Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

### 8. Read every ticket back

After publishing, open each ticket again (on a real tracker, fetch it; locally, read the file) and check every one:

- The title and **What to build** describe the same slice.
- Every entry under **Blocked by** is an identifier that resolves to one of this batch's tickets, and the ticket it resolves to is the one meant.
- On a tracker with native blocking links, the number of links equals the number of **Blocked by** entries.

Then each kind of ticket, for the sections that kind must carry. On the ones an agent works:

- **Read first** and **Seam** are present and non-empty ("none" counts as present). Where **Read first** carries a baseline — anything that records a settled conclusion — its line marks it as one.
- **Owns** is present and non-empty, every entry is a repository-relative path or glob, and no two tickets on the same frontier overlap there.
- `verify-ticket.py <n> --lint` has been run, and every ERROR it reports is fixed before you report the batch. Read every WARN once and either fix it or keep it on purpose.

On the `ready-for-human` ones — no agent can repair one:

- The kind is named, *reaction* or *reach*.
- **What to look at** is a link that opens, and **what makes it right** is there to judge against.

Fix what fails before reporting the batch as published.

<local-ticket-template>

# <NN>: <Ticket title>

**Parent:** the spec, and the numbered Implementation Decisions sections this ticket implements.

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective, not a layer-by-layer implementation list.

**Read first:** the source material behind this ticket's sections (decision tickets, ADRs, research files, prototype directories), copied from the sources those sections cite. "None" if the sections cite nothing.

**Seam:** the test layer and directory where this ticket is verified, copied from the spec's Testing Decisions.

**Owns:** the repository-relative paths this ticket may write, one per line, the test directory or file from **Seam** included; "(new)" on what this ticket creates.

**Blocked by:** the numbers of the tickets that gate this one, or "None (can start immediately)".

**Status:** ready-for-agent

- [ ] AC1: <what must be true, in the spec's exact values>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending
- [ ] AC2: <the next thing that must be true>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker, followed by the numbered Implementation Decisions sections this ticket implements ("#535, Implementation Decisions sections 5 and 7"). Omit the section only when the source was not an existing issue.

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Write it as numbered points, one thing per point, each point complete with the test that decides it and the reason it is there. A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research files, prototype directories, domain docs — copied from what those sections cite, one per line, each with a word on what it settles. The implementer reads these and nothing else from the spec's Sources. Whatever here records a settled conclusion — the chosen artifact of a prototype, a handoff package downloaded from Claude Design, the Decision of an ADR, the resolution of a decision ticket — is a **baseline**: a contract, not a reference, marked as one on its line. The exact values and the verbatim copy in the criteria come from the handoff package README where there is one. Write "None" if the sections cite nothing.

## Seam

Where this ticket is verified: the test layer and directory from the spec's Testing Decisions, and the precedent to copy.

## Owns

The repository-relative paths this ticket may write, one per line, the test directory or test file from **Seam** included. Mark what this ticket creates with "(new)". No absolute path, no `..`, no bare `**`. Match the granularity to the split: a directory glob where this ticket owns the directory alone, file paths where several tickets divide one directory. Two tickets on the same frontier must not overlap here; where they cannot be pulled apart because both must edit one file, add a **Blocked by** edge instead. Everything outside these paths is read-only for this ticket.

- src/import/**
- tests/import/**
- src/import/ui/** (new)

## Acceptance criteria

- [ ] AC1: <what must be true, in the spec's exact values>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending
- [ ] AC2: <the next thing that must be true>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending

Every criterion here carries a command. A judgement goes to code review; a thing only a person can look at is its own `ready-for-human` ticket, blocked by this one.

## Blocked by

- The issue number of each blocking ticket, or "None (can start immediately)". On a tracker with native blocking links, add the same edges there too.

</issue-template>

In either form, avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without — the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

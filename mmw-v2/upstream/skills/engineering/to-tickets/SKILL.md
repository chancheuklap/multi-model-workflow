---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the project issue tracker as one issue per ticket with blocking links.
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

**A criterion is decided by a command, or it is not a criterion.** Everything under `## Acceptance criteria` is run by machine and re-run by the verifier, and that is what makes "it passed" a fact rather than the opinion of whoever wrote the code. Most of what you want to say about the work does not belong there. Ask **the five questions** in order and stop at the first yes:

1. **Is the rule a comparison — equal, matches, counts, over a threshold — against something a machine can reach?** It is a criterion. Write its `CHECK:` and `EXPECT:`.
2. **Is the rule a judgement, against something a machine can reach?** Whether an interface is deep rather than a pass-through, whether a passage says enough, whether an error message tells the caller what to do next, whether the test behind a criterion could ever have failed. Code review decides these — its `Standards` axis for how the code is written, its `Spec` axis for whether it matches what was asked, its `Tests` axis for whether the cases a `CHECK:` names are worth trusting — in a session other than the one that wrote the code. Leave it out of `## Acceptance criteria`: a judgement left there has only its own author to decide it, which is the one thing that section exists to prevent. It does not go nowhere: write the judgement as one sentence into the `## Implementation Decisions` subsection of the spec this ticket's **Parent** names, through the `to-spec` skill's step for revising a published spec. The Spec axis reads that subsection, so it will judge it; and a decision in the spec section the ticket names is in-ticket for the review, so the finding gets its round of fixes on this ticket rather than a sub-issue.
3. **Is the property a person's reaction?** Whether a newcomer knows what to do, whether the wording lands, whether a morning page is legible at a glance. The person is the instrument, not a fallback judge: no agent can stand in, because the agent is not who is being measured. It becomes its own ticket, of kind *reaction* — see **Work only a person can do** below.
4. **Could a machine decide it, if only it could reach the thing?** Two answers hide under one question, and they part on whether the reach is something you build.
   - **It is.** The state lives inside software you are about to write, and something has to put the system there: a screen composed against fixtures instead of the live client, a seeded row, a stub scripted to answer in a set order. This stays a criterion. But the thing that reaches the state has to be named in the spec's Testing Decisions, under **How a test arrives at a state**, and owned under some ticket's **Owns**. Missing either, the state is out of reach for this batch, and the criterion becomes its own ticket of kind *reach* — see **Work only a person can do** below — whose retiring line names the mechanism that has no name yet, or the ticket that would own it. Reaching a state is work, and work that nobody owns does not happen; a *reach* ticket is where it waits for an owner.
   - **It is not.** A signed installer on a clean machine, a login against the real provider, a notification arriving on a phone. Its own ticket, of kind *reach* — see **Work only a person can do** below.
5. **Is it a choice rather than a check?** No true or false, only a preference, and the answer decides what to build next rather than whether what was built is right. The user is here now, so ask them: carry the choice into the quiz of step 6, with the options and the one you would take, and write the answer into the ticket's **What to build** as a numbered point of its own. The worker then reads it as the ticket's decision and not as one it made on its own; nothing the ticket writer chose is left for the night.

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
- A criterion that compares an interface against a downloaded handoff package is written in one fixed shape, path and all, by the `verify-ticket` skill. Copy it from there rather than composing it: that criterion is the one command in this pipeline handed to a shell with no agent in between, so the path in it is written out in full on purpose and every part of the line is load-bearing.

`CHECK:` takes the object it checks from one of two places: this ticket itself — the number comes from `$MMW_TICKET`, or from the branch name `issue-<n>` — or something this ticket names by number. When the objects only exist at run time, walk the tracker's native relationships out from an anchor the ticket names: `gh api repos/{owner}/{repo}/issues/<n>/sub_issues`. A `CHECK:` must not search for its own object; searching and taking the first hit (`gh issue list --search … | head -1` and its kind) checks whatever the search happens to return, and often cannot fail at all.

`CHECK:` brings the state it needs and puts back the shared state it changed. Two kinds of state are in play. This pipeline's: criteria run one at a time in ledger order, each in its own shell with cwd fixed at the repository root, so `cd` cannot reach another one — but the branch, the ticket and the working tree are shared, and `--reverify` runs every criterion a second time. Switch a branch and switch it back; reopen a ticket the next criterion needs open; stop a server you started. And the system's: the row, the balance, the screen the criterion is about. Before writing the command, say what puts the system there. The spec's Testing Decisions answers that per layer, under **How a test arrives at a state**; question 4 above is where an unanswered one goes.

Write the command on the `CHECK:` line when it fits there. When it does not, leave that line empty after the colon and open a **fenced block** on the next line: the fence holds the command, and nothing inside it is read as a criterion or an attribute, so it may contain blank lines, backtick fences and lines beginning `- [ ]`. A flush-left continuation with no fence is a parse error.

**Work only a person can do is its own ticket, not a criterion on someone else's**, and you split it off here, while writing the ticket, not when closing it. A criterion no agent can decide leaves its ticket unable to finish; so the ticket that produces the thing stays an agent's, and the looking becomes a second ticket blocked by it.

Write one such ticket per thing to be looked at, labelled `ready-for-human`. It is shorter than the template below and holds **the five things** only:

- **Parent**.
- **Which kind**: *reaction* or *reach*, in one word. A *reach* ticket adds one line naming what would retire it — a test account, a spare device, a runner, a mechanism under **How a test arrives at a state** that nobody owns yet, or a testability rule of the consuming repository that gives a test no exit. This is the only exit in the pipeline that owes no account to a machine, so it attracts whatever the writer did not want to think about; being unable to name the kind is the sign that the thing belongs at question 1, 2 or 5 instead.
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
- **Choices**: every choice question 5 sent here, one line each — the options, and the one you would take. Omit the line when there are none.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- For each choice listed: which option?

Iterate until the user approves the breakdown. Write each answered choice into that ticket's **What to build** before publishing.

### 7. Publish the tickets to the configured tracker

Publish the approved tickets to the issue tracker `/setup-matt-pocock-skills` configured (GitHub, Linear, …): one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native issue dependencies and sub-issue relationship where it has them; otherwise set each ticket's "Blocked by" to the blocking issues. On GitHub, create each ticket as a sub-issue of the spec (`gh issue create --parent <spec>`, or attach it through the `sub_issues` API): the ticket graph of the `verify-ticket` skill's `--lint`, and the board, read only that relationship. Apply the `ready-for-agent` triage label to every ticket an agent works, and beside it the `junior-worker` or `senior-worker` label its **Worker** section names; the ones a person must judge carry `ready-for-human` instead, and no worker.

Work the **frontier**: the tickets that are open, carry `ready-for-agent`, have every blocker closed, and have neither an assignee nor a live session. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

### 8. Read every ticket back

After publishing, fetch each ticket again and check every one:

- The title and **What to build** describe the same slice.
- Every entry under **Blocked by** is an identifier that resolves to one of this batch's tickets, and the ticket it resolves to is the one meant.
- On a tracker with native issue dependencies, the number of blocking links equals the number of **Blocked by** entries.
- On GitHub, the spec's sub-issue count equals the number of tickets in this batch.

Then each kind of ticket, for the sections that kind must carry. On the ones an agent works:

- **Read first** and **Seam** are present and non-empty ("none" counts as present). Where **Read first** carries a baseline — anything that records a settled conclusion — its line marks it as one.
- **Owns** is present and non-empty, every entry is a repository-relative path or glob, and no two tickets on the same frontier overlap there.
- Every thing a criterion needs to reach its state — the ones the spec's Testing Decisions names under **How a test arrives at a state** — is under some ticket's **Owns**. No script checks this one, so it is yours to check: a criterion that assumes a mechanism nobody builds fails on the night it first runs, and by then the batch is out.
- The `verify-ticket` skill's `--lint` has been run on the ticket's issue number, and every ERROR it reports is fixed before you report the batch. Read every WARN once and either fix it or keep it on purpose.

On the `ready-for-human` ones — no agent can repair one, so all of the five things it holds are checked:

- **Parent** is there.
- The kind is named, *reaction* or *reach*.
- **What to look at** is a link that opens.
- **What makes it right** is there to judge against.
- **Blocked by** names the ticket that produces the thing.

Fix what fails before reporting the batch as published. When the batch is a spec's night run, hand over to the `dispatch` skill: opening the night on this spec is one of its rows.

<issue-template>

## Parent

A reference to the parent issue on the tracker, followed by the numbered Implementation Decisions sections this ticket implements ("#535, Implementation Decisions sections 5 and 7"). Omit the section only when the source was not an existing issue.

## Worker

Which of the two workers this ticket gets, and one line saying why. `junior-worker` is the default, and the line is what buys the other one: a ticket goes to `senior-worker` when getting it wrong is wrong **silently** — money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default — because none of those fail on the day they are written. A ticket whose **Seam** already names a precedent to copy stays on `junior-worker`. Name the worker; the model behind each one lives in `models.md` in the `dispatch` skill, which is the only place a model is written down.

senior-worker — one settlement per task, and a wrong one surfaces days later in the ledger rather than in a failing test.

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Write it as numbered points, one thing per point, each point complete with the test that decides it and the reason it is there. A choice the user settled in the quiz of step 6 is a point of its own here, stated as the ticket's decision. A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research files, prototype directories, domain docs — copied from what those sections cite, one per line, each with a word on what it settles. The implementer reads these and nothing else from the spec's Sources. Whatever here records a settled conclusion — the chosen artifact of a prototype, a handoff package downloaded from Claude Design, the Decision of an ADR, the resolution of a decision ticket — is a **baseline**: a contract, not a reference, marked as one on its line. The exact values and the verbatim copy in the criteria come from the handoff package README where there is one. Write "None" if the sections cite nothing.

## Seam

Where this ticket is verified: the test layer and directory from the spec's Testing Decisions, and the precedent to copy. Then, from the same section's **How a test arrives at a state**, what puts the system into the states the criteria below name — and, when this ticket is the one that builds that, say so here as well as under **Owns**.

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
  TIMEOUT: 1800

Every criterion here carries a command. A judgement goes to code review; a thing only a person can look at is its own `ready-for-human` ticket, blocked by this one. `TIMEOUT:` is optional: seconds this `CHECK:` may run, written when the precedent takes longer than ten minutes — a full build, a suite that starts a browser — and read by the worker's own run and the verifier's alike. It raises the limit and never lowers it.

## Blocked by

- The issue number of each blocking ticket, or "None (can start immediately)". On a tracker with native issue dependencies, add the same blocking links there too.

</issue-template>

Avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without — the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

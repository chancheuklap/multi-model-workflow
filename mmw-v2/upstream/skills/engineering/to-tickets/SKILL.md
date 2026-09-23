---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets on the project issue tracker. Use when a spec or an approved plan has to become the batch an agent works ticket by ticket.
---

# To Tickets

Break a plan, spec, or conversation into a set of **tickets**: tracer-bullet vertical slices, each declaring the tickets that **block** it.

The issue tracker and triage label vocabulary should have been provided to you. If not, tell the user to run the `setup-matt-pocock-skills` skill.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes a reference (a spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

A plan or a conversation with no published spec goes through the `to-spec` skill first; this skill cuts tickets from the spec's issue number.

Done when you hold the spec's issue number and have read its full body and comments.

### 2. Explore the codebase

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

Done when you know the module or directory each ticket will write to.

### 3. Draft vertical slices

Break the work into **tracer bullet** tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests): vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Any prefactoring should be done first

</vertical-slice-rules>

When the spec has a screen contract, read [references/cutting-interface-tickets.md](references/cutting-interface-tickets.md).

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

Done when the work is drafted as slices, each one vertical or one step of an expand–contract sequence.

### 4. Write each acceptance criterion

Three rules bind how each one is worded:

1. Observable external behaviour, from the spec's seam or a user-visible UI. Not internals.
2. Exact values (numbers, copy, state names, field names) copied from the spec or the chosen prototype artifact. No "appropriate", "correct", or "as expected".
3. One behaviour per criterion, independently true or false. Split compounds.

**A criterion is decided by a command, or it is not a criterion.** Everything under `## Acceptance criteria` is run by machine and re-run by the worker's final full run, and that is what makes "it passed" a fact rather than the opinion of whoever wrote the code. Most of what you want to say about the work does not belong there. Ask **the five questions** in order and stop at the first yes:

1. **Is the rule a comparison (equal, matches, counts, over a threshold) against something a machine can reach?** It is a criterion. Write its `CHECK:` and `EXPECT:`.
2. **Is the rule a judgement, against something a machine can reach?** Whether an interface is deep rather than a pass-through, whether a passage says enough, whether an error message tells the caller what to do next, whether the test behind a criterion could ever have failed. Code review decides these, in a session other than the one that wrote the code, and its `Spec` axis reads the `## Implementation Decisions` subsection of the spec this ticket's **Parent** names. Leave the rule out of `## Acceptance criteria` and write it there as one sentence, through the `to-spec` skill's step for revising a published spec.
3. **Is the property a person's reaction?** Whether a newcomer knows what to do, whether the wording lands, whether a morning page is legible at a glance. The person is the instrument, not a fallback judge: no agent can stand in, because the agent is not who is being measured. It becomes its own ticket, of kind *reaction*; see [references/person-ticket.md](references/person-ticket.md).
4. **Could a machine decide it, if only it could reach the thing?** Two answers hide under one question, and they part on whether the reach is something you build.
   - **It is.** The state lives inside software you are about to write, and something has to put the system there: a seeded row, a stub scripted to answer in a set order. This stays a criterion. But the thing that reaches the state has to be named in the spec's Testing Decisions, under **How a test arrives at a state**, and owned under some ticket's **Owns**. That ticket builds it: a criterion that assumes a mechanism nobody builds fails on the night it first runs. Missing either, the state is out of reach for this batch, and the criterion becomes its own ticket of kind *reach* (see [references/person-ticket.md](references/person-ticket.md)), whose retiring line names the mechanism that has no name yet, or the ticket that would own it.
   - **It is not.** A signed installer on a clean machine, a login against the real provider, a notification arriving on a phone. Its own ticket, of kind *reach*; see [references/person-ticket.md](references/person-ticket.md).
5. **Is it a choice rather than a check?** No true or false, only a preference, and the answer decides what to build next rather than whether what was built is right. The user is here now, so ask them: carry the choice into the quiz of step 6, with the options and the one you would take, and write the answer into the ticket's **What to build** as a numbered point of its own.

If no command exists because the spec never decided how this is verified, stop and return to the `to-spec` skill. Do not invent it.

Every criterion is four lines, and carries a number you assign as you write it and never renumber.

```
- [ ] AC1: POST /projects with a name that already exists returns 409 and error name-duplicate
  CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
```

Derive `CHECK:` and `EXPECT:` from the spec; do not invent either:

- `CHECK:` comes from Testing Decisions: its layer, that layer's directory, and the precedent it names. Open the precedent, copy its framework and its single-file invocation, then aim that at the file and case this ticket adds.
- `EXPECT:` is a **success-only marker**: the line the precedent prints only when it passed. Run the precedent once and copy that line. `ok`, `passed` or `done` on their own also appear in failing output; take the whole counted line.

`CHECK:` takes the object it checks from one of two places: this ticket itself (the number comes from `$MMW_TICKET`, or from the branch name `issue-<n>`), or something this ticket names by number. When the objects only exist at run time, walk the tracker's native relationships out from an anchor the ticket names: `gh api repos/{owner}/{repo}/issues/<n>/sub_issues`. A `CHECK:` must not search for its own object; searching and taking the first hit (`gh issue list --search … | head -1` and its kind) checks whatever the search happens to return, and often cannot fail at all.

`CHECK:` brings the state it needs and puts back the shared state it changed. Criteria run one at a time in ledger order, each in its own shell with cwd fixed at the repository root, so `cd` cannot reach another one, but the branch, the ticket and the working tree are shared, and `--reverify` runs every criterion a second time: switch a branch and switch it back; reopen a ticket the next criterion needs open; stop a server you started. The system's own state (the row, the balance, the screen) is put there by what question 4 names.

**A criterion is also exposed to the rest of its own batch.** Every ticket lands on the same base branch, and the closing pass re-runs every criterion of the batch there, so a criterion that names something a later ticket may change is decided by that ticket's work rather than by its own. Two shapes do it: a sweep of the whole repository (a `grep` for a name that must now be gone, a count over the tree), which any later ticket can put back in a note, a doc or a comment; and a criterion that names a test case, a function or a symbol by a name a later ticket may rename. Put such a criterion on the batch's last ticket, or give the name one owner: the file that holds it is under exactly one ticket's **Owns** in the whole batch, not merely among the tickets that can run at the same time, so no other ticket of the batch may write it.

Done when every criterion on every ticket carries a number, a `CHECK:` and an `EXPECT:`, and everything that stopped at question 2, 3, 4 or 5 has landed where that question sends it.

### 5. Give each ticket its blocking edges

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

**What a ticket creates is put in service by an edit to something it did not create**: the registry, router, parent template, index, story adapter or stylesheet that has to name it. Until one does, no criterion of that ticket can see it; and when several tickets that can run at the same time each make that edit, all but the first to land bounce on a merge conflict. For each path a ticket marks `(new)`, `grep` the nearest existing file of its kind twice, once for its file name and once for the one identifier it declares for others (its root class, exported symbol or route path), and put every file that answers under this ticket's **Owns**, whoever created it. Where that sibling is still to be built in this batch, its ticket's **Owns** is the same list.

What overlaps there now decides the shape of the batch:

- **Two tickets that can run at the same time**: the **Blocked by** edge the **Owns** section already calls for.
- **Three or more on the same files**: a chain that long works the night one ticket at a time. Cut a **prefactor ticket** ahead of them (prefactoring goes first in any case), which owns those files and lands in one pass every entry, route, include and export, each naming a placeholder the ticket behind it fills; and where a shared file is only a list of independent entries, a stylesheet or a registry or a bundle index, splits it into one file per ticket that the shared one includes once. Each of them is then blocked by that ticket alone, and they run together.

A shared file that is one body of logic, such as a route module several tickets add handlers to, is neither pre-landed nor split, because what each ticket writes there is the ticket's own work. Those tickets keep their chain.

**Every branch above keeps one rule: no two tickets that can run at the same time write the same file.** Two tickets can run at the same time when neither blocks the other, directly or down a chain.

Done when every path marked `(new)` has the files that put it in service under the same ticket's **Owns**, and no two tickets that can run at the same time write the same file.

### 6. Quiz the user

Write the spec body and the drafted tickets to a file `mktemp` makes, and have them scanned for ambiguities before you list the breakdown: the scan's questions belong in each ticket's **Choices** when the user first sees it. When the host can run subagents, start your host's general-purpose subagent, on this session's model and thinking level and restricted to reading and searching where the host allows it, with one sentence:

```
Read <absolute path of this skill's references/ambiguity-scan.md> and scan spec #<spec> and the drafted tickets in <file> for ambiguities.
```

Hold this turn until it returns; where the host runs subagents in the background, ask for it to be waited on. When the host cannot run subagents, run the scan yourself from [references/ambiguity-scan.md](references/ambiguity-scan.md), and write its result to a file before you list the breakdown.

Present the proposed breakdown as a numbered list. For each ticket an agent works, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work
- **Worker**: `junior` or `senior`, and the one-line reason. `junior-worker` is the default, and a ticket goes to `senior-worker` when getting it wrong is wrong **silently** (money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default), because none of those fail on the day they are written. A ticket whose **Seam** already names a precedent to copy stays on `junior-worker`.
- **Choices**: every choice question 5 sent here, and every question the ambiguity scan returned, one line each: the options, and the one you would take. Omit the line when there are none.

Then the `ready-for-human` tickets, in the same list, each with its **Title**, **Blocked by**, its kind (*reaction* or *reach*) and what is to be looked at.

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?
- Is each worker grade right for what going wrong on that ticket would cost?
- For each choice listed: which option?

Iterate until the user approves the breakdown. Write each answered choice that only changes what one ticket delivers into that ticket's **What to build** before publishing. Write each answered choice that changes a decision in a spec section back through the `to-spec` skill's step for revising a published spec, then into the tickets.

Done when the user has approved the breakdown and every answered choice is written into a ticket's **What to build** or the spec, and step 5's Done when still holds for the approved breakdown.

### 7. Publish the tickets to the configured tracker

Lint the batch before anything is live: write each approved ticket as one draft file in a directory `mktemp -d` makes (`TITLE:`, `LABELS:`, `BLOCKED BY:` naming other drafts, a line `---`, then the body as it will be published), and run the `verify-ticket` skill's `--lint` with the spec's number and `--drafts <that directory>`. Fix every `ERROR` in the drafts, then publish them as they now stand.

Publish the approved tickets to the issue tracker the `setup-matt-pocock-skills` skill configured: one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native issue dependencies and sub-issue relationship. Create each ticket as a sub-issue of the spec (`gh issue create --parent <spec>`, or attach it through the `sub_issues` API): the scripts find the batch only through that relationship and take a ticket's direct parent as its spec. Every ticket carries the layer label `mmw:ticket`; create it as `docs/agents/issue-tracker.md` `## Three label sets` gives, when the repository lacks it. Apply the `ready-for-agent` triage label to every ticket an agent works, and beside it the `junior-worker` or `senior-worker` label the approved list of step 6 gives it; the ones a person must judge carry `ready-for-human` instead, and no worker.

Close no parent issue.

Done when every approved ticket is published as a sub-issue of the spec, with its labels and its blocking links.

### 8. Read every ticket back

After publishing, fetch each ticket again and check:

- The title and **What to build** describe the same slice.
- The spec's sub-issue count equals the number of tickets in this batch, and every one of them carries `mmw:ticket`.
- On each ticket an agent works, **Read first** and **Seam** are present and non-empty ("none" counts as present), and where **Read first** carries a baseline (anything that records a settled conclusion), its line marks it as one. **Owns** is present and non-empty, and every entry is a repository-relative path or glob.
- The `verify-ticket` skill's `--lint`, run again on the spec's issue number, reports no `ERROR`, and every `WARN` has been read once and either fixed or kept on purpose. The drafts run of step 7 does not stand in for it: only this run sees the tracker's labels, sub-issues and blocking links.
- Each `ready-for-human` ticket holds all of **the five things** in [references/person-ticket.md](references/person-ticket.md), because no agent can repair one.

Done when every check above passes. When the batch is a spec's night run, hand over to the `dispatch` skill: opening the night on this spec is one of its rows.

<issue-template>

## Parent

A reference to the parent issue on the tracker, followed by the numbered Implementation Decisions sections this ticket implements (for example, "#12, Implementation Decisions sections 5 and 7"). The first issue here is read as the ticket's spec.

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Write it as numbered points, one thing per point, each point complete with the test that decides it and the reason it is there. A choice the user settled in the quiz of step 6 is a point of its own here, stated as the ticket's decision.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research files, prototype directories, domain docs, the sections of `CODING_STANDARDS.md` and `TESTING.md` the spec relies on, copied from what those sections cite, one per line, each with a word on what it settles. The implementer reads these and nothing else from the spec's Sources. Whatever here records a settled conclusion (the chosen artifact of a prototype, a design package pulled into the repository, the decision an ADR states in the paragraph under its title, the resolution of a decision ticket) is a **baseline**: a contract, not a reference, marked as one on its line. Write "None" if the sections cite nothing. When the spec has a screen contract, read [references/cutting-interface-tickets.md](references/cutting-interface-tickets.md) for the baseline lines and derivation that kind of ticket carries.

## Seam

Where this ticket is verified: the test layer and directory from the spec's Testing Decisions, and the precedent to copy. Then, from the same section's **How a test arrives at a state**, what puts the system into the states the criteria below name; when this ticket is the one that builds that, say so here as well as under **Owns**.

## Owns

The repository-relative paths this ticket may write, one per line, the test directory or test file from **Seam** included. Mark what this ticket creates with "(new)". A file this ticket must edit to put what it creates in service (the registry, router, stylesheet, parent template or index that has to name it) belongs here as well, though another ticket created it: this section says where this ticket may write, not where its own code lives. No absolute path, no `..`, no bare `**`. Match the granularity to the split: a directory glob where this ticket owns the directory alone, file paths where several tickets divide one directory. Two tickets that can run at the same time must not overlap here; where they cannot be pulled apart because both must edit one file, add a **Blocked by** edge instead. Everything outside these paths is read-only for this ticket. A change a ticket needs in a tool skill outside the repository is not an entry here: the toolbox is improved in use, and the change is made there at once.

A ticket that deletes or renames a file, a script, a contract field, or a criterion word takes every place `grep` finds that name into its own **Owns**. Find those places by grepping the name, not by listing from memory. When a hit is only a stale reference another ticket already owns, leave it off this ticket and open a ticket **Blocked by** that other ticket.

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

`TIMEOUT:` is optional: seconds this `CHECK:` may run, written when the precedent takes longer than ten minutes (a full build, a suite that starts a browser), and read by the worker's own run and final full run alike. It raises the limit and never lowers it.

</issue-template>

Avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without: the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

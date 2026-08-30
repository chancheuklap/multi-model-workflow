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

Write each acceptance criterion so a later check can pass or fail it:

1. Observable external behaviour, from the spec's seam or a user-visible UI. Not internals.
2. Exact values (numbers, copy, state names, field names) copied from the spec or the chosen prototype artifact. No "appropriate", "correct", or "as expected".
3. One behaviour per criterion, independently true or false. Split compounds.
4. Ask who reads the criterion, then take one of three routes. **An agent, and you can write the command** — give it `CHECK:` and `EXPECT:`; the engine runs it, ticks it, and writes the evidence. Deciding whether code is correct, whether a passage tells an agent enough, or whether a report the agent can fetch says what it should — the reader is an agent in all three. **An agent, but no command exists** — leave `CHECK:` off; whoever works the ticket judges it and, at closing time, ticks it and writes what they read and concluded. `--lint` warns on every criterion with no `CHECK:`, so take that warning as one more chance to turn it into a command. **A person** — see the next paragraph. If no command exists because the spec never decided how this is verified, stop and return to `/to-spec`. Do not invent it.

Every criterion carries a number you assign as you write it and never renumber. One with a command is four lines:

```
- [ ] AC1: POST /projects with a name that already exists returns 409 and error name-duplicate
  CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
```

A criterion on the second route keeps the `- [ ]` line, the number and `EVIDENCE: pending`, and says in place of `CHECK:` what the worker must read to decide it.

Derive `CHECK:` and `EXPECT:` from the spec; do not invent either:

- `CHECK:` comes from Testing Decisions — its layer, that layer's directory, and the precedent it names. Open the precedent, copy its framework and its single-file invocation, then aim that at the file and case this ticket adds.
- `EXPECT:` comes from running the precedent once and copying the line a passing run prints. `ok`, `passed` or `done` on their own also appear in failing output; take the whole counted line.
- A criterion that compares an interface against a downloaded baseline gets `CHECK: uv run ~/.agents/skills/verify-ticket/scripts/visual-parity.py --baseline <baseline dir> --impl <url> --scenes <name,name> --max-pct 1` and `EXPECT: PARITY OK <n>/<n>`.

`CHECK:` must not search for the object it checks. That object is either this ticket itself — take the number from `$MMW_TICKET`, or from the branch name `issue-<n>` — or something this ticket names by number. Searching and taking the first hit (`gh issue list --search … | head -1` and its kind) is banned: it lets a criterion check the wrong object, or makes it impossible to fail. When the objects only exist at run time, walk the tracker's native relationships out from an anchor the ticket names: `gh api repos/{owner}/{repo}/issues/<n>/sub_issues`.

`CHECK:` brings the state it needs and puts back the shared state it changed. It must not rely on what the criterion before it left behind. Criteria run one at a time in ledger order, each in its own shell with cwd fixed at the repository root, so `cd` cannot reach another one — but the branch, the ticket and the working tree are shared, and `--reverify` runs every criterion a second time. Switch a branch and switch it back; reopen a ticket the next criterion needs open; stop a server you started.

Write the command on the `CHECK:` line when it fits on one line. When it does not, leave that line empty after the colon and open a fenced code block on the next line: the fence holds the command, and nothing inside it is read as a criterion or an attribute, so it may contain blank lines, backtick fences and lines beginning `- [ ]`. A flush-left continuation with no fence is a parse error.

**Work only a person can judge is its own ticket, not a criterion on someone else's**, and you split it off here, while writing the ticket, not when closing it. Behaviour watched in a live session, whether a screen looks right, whether a ticket reads like a real ticket, a call only the user can make — leaving those on an agent's ticket leaves it unable to finish. Write one ticket per such judgement, labelled `ready-for-human`, blocked by the ticket that produces the thing being judged. It is a shorter ticket than the template below: **Parent**, one line on why it cannot be delegated (a judgement call, access only a person has, a design decision, or testing by hand), what the person looks at, what makes it right, and **Blocked by**. No **Seam**, no **Owns**, no acceptance criteria — nothing here runs.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change (rename a column, retype a shared symbol) whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify ticket; green is promised only there.

### 4. Give each ticket its blocking edges

Give each ticket its **blocking edges**: the other tickets that must complete before it can start. A ticket with no blockers can start immediately.

### 5. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct: does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further?

Iterate until the user approves the breakdown.

### 6. Publish the tickets to the configured tracker

Publish the approved tickets. **How** depends on the tracker `/setup-matt-pocock-skills` configured; the tickets are the same either way, only the shape of the blocking edges changes:

- **Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Each file's "Blocked by" lists the numbers/titles it depends on. Use the per-ticket file template below: one ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native blocking / sub-issue relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues. Apply the `ready-for-agent` triage label to every ticket an agent works; the ones a person must judge carry `ready-for-human` instead.

Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

### 7. Read every ticket back

After publishing, open each ticket again (on a real tracker, fetch it; locally, read the file) and check every one:

- The title and **What to build** describe the same slice.
- Every entry under **Blocked by** is an identifier that resolves to one of this batch's tickets, and the ticket it resolves to is the one meant.
- On a tracker with native blocking links, the number of links equals the number of **Blocked by** entries.

Then, on the tickets an agent works — the `ready-for-human` ones have none of these sections and are skipped here:

- **Read first** and **Seam** are present and non-empty ("none" counts as present). Where **Read first** points at a downloaded baseline directory, it says the directory is a contract.
- **Owns** is present and non-empty, every entry is a repository-relative path or glob, and no two tickets on the same frontier overlap there.
- `verify-ticket.py <n> --lint` has been run. Fix every ERROR it reports before you report the batch. Read every WARN once and either fix it or keep it on purpose — a criterion with no `CHECK:` always warns, and that is the shape you chose.

Fix what fails before reporting the batch as published.

<local-ticket-template>

# <NN>: <Ticket title>

**Parent:** the spec, and the numbered Implementation Decisions sections this ticket implements.

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective, not a layer-by-layer implementation list.

**Read first:** the source material behind this ticket's sections (decision tickets, ADRs, research files, prototype directories), copied from the sources those sections cite. "None" if the sections cite nothing.

**Seam:** the test layer and directory where this ticket is verified, copied from the spec's Testing Decisions.

**Owns:** the repository-relative paths this ticket may write, one per line, the test directory or file from **Seam** included; "(new)" on what this ticket creates.

**Blocked by:** the numbers of the tickets that gate this one, or "None (can start immediately)".

**Status:** ready-for-agent, or ready-for-human with one line saying why it cannot be delegated

- [ ] AC1: <what must be true, in the spec's exact values>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending
- [ ] AC2: <a criterion the agent working the ticket decides by reading, no command exists>
  EVIDENCE: pending

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker, followed by the numbered Implementation Decisions sections this ticket implements ("#535, Implementation Decisions sections 5 and 7"). Omit the section only when the source was not an existing issue.

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Write it as numbered points, one thing per point, each point complete with the test that decides it and the reason it is there. Both a person scanning the tracker for the one thing and an agent starting with none of your context read this section, and neither gets through a single long paragraph.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research files, prototype directories, domain docs — copied from what those sections cite, one per line, each with a word on what it settles. The implementer reads these and nothing else from the spec's Sources. A baseline directory downloaded from Claude Design, its handoff README included, is a contract and not a reference: the exact values and the verbatim copy in the criteria come from that README. Write "None" if the sections cite nothing.

## Seam

Where this ticket is verified: the test layer and directory from the spec's Testing Decisions, and the prior art to copy. A ticket whose only verification is a human check names the device and the steps.

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
- [ ] AC2: <a criterion the agent working the ticket decides by reading, no command exists>
  EVIDENCE: pending

Criteria only a person can judge do not go here. Each is its own ticket, labelled `ready-for-human` and blocked by this one.

## Blocked by

- The issue number of each blocking ticket, or "None (can start immediately)". On a tracker with native blocking links, add the same edges there too.

</issue-template>

In either form, avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without — the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

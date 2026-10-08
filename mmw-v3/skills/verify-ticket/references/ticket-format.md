# The format of a ticket

What one ticket holds, section by section, how each acceptance criterion is written, and what goes elsewhere. `verify-ticket.py` runs what is written here: `--preflight` claims the ticket, `<n>` runs every criterion, `<n> --lint` checks one ticket and the graph of the batch it sits under ([linting.md](linting.md)).

## The body

```
## Parent

A reference to the parent issue on the tracker, followed by the numbered Implementation Decisions sections this ticket implements (for example, "#12, Implementation Decisions sections 5 and 7"). The first issue here is read as the ticket's spec. A ticket outside any spec writes "None".

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective, not layer-by-layer implementation. Write it as numbered points, one thing per point, each point complete with the test that decides it and the reason it is there. A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph. A choice the owner settled when the batch was cut is a point of its own here, stated as the ticket's decision.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research files, prototype directories, domain docs, the lines of `TESTING.md` the spec relies on, copied from what those sections cite, one per line, each with a word on what it settles. A ticket that changes a feature file already on the base branch lists that file here. The implementer reads these and nothing else from the spec's Sources. Whatever here records a settled conclusion (the chosen artifact of a prototype, a design package pulled into the repository, the decision an ADR states in the paragraph under its title, the resolution of a decision ticket) is a **baseline**: a contract, not a reference, marked as one on its line. Write "None" if the sections cite nothing. When the spec has a screen contract, read the `mmw-mode` skill's `references/cutting-interface-tickets.md` for the baseline lines and derivation that kind of ticket carries.

## Seam

Where this ticket is verified, as pointers into the spec's Testing Decisions rather than a restatement of it: the test layer this ticket uses, by the name that section gives it (the layer's directory and precedent are there), and the test file this ticket adds. Then the mechanism under that section's **How a test arrives at a state** that puts the system into the states the criteria below name, by its name there; when this ticket is the one that builds it, say so here as well as under **Owns**.

## Owns

The repository-relative paths this ticket may write, one per line, the test directory or test file from **Seam** included. Mark what this ticket creates with "(new)". A file this ticket must edit to put what it creates in service (the registry, router, stylesheet, parent template or index that has to name it) belongs here as well, though another ticket created it: this section says where this ticket may write, not where its own code lives. No absolute path, no `..`, no bare `**`. Match the granularity to the split: a directory glob where this ticket owns the directory alone, file paths where several tickets divide one directory. Two tickets that can run at the same time must not overlap here; where they cannot be pulled apart because both must edit one file, add a **Blocked by** edge instead. Everything outside these paths is read-only for this ticket. A feature file the spec's `## Feature map changes` names belongs here, on the ticket that changes that feature. A change a ticket needs in a tool skill outside the repository is not an entry here: the toolbox is improved in use, and the change is made there at once.

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

`TIMEOUT:` is optional: seconds this `CHECK:` may run, written when the precedent takes longer than ten minutes (a full build, a suite that starts a browser), and read by the worker's own run and final run alike. It raises the limit and never lowers it.
```

Avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without: the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

A ticket outside any spec has no Testing Decisions to point into: its **Seam** points at the lines of the repository's `TESTING.md` that name its layer and directory, and at the nearest test of the same kind, the precedent each `CHECK:` takes its invocation from.

## Each acceptance criterion

Three rules bind how each one is worded:

1. Observable external behaviour, from the spec's seam or a user-visible UI. Not internals.
2. Exact values (numbers, copy, state names, field names) copied from the spec or the chosen prototype artifact. No "appropriate", "correct", or "as expected".
3. One behaviour per criterion, independently true or false. Split compounds.

**A criterion is decided by a command, or it is not a criterion.** Everything under `## Acceptance criteria` is run by machine and re-run by the worker's final run, and that is what makes "it passed" a fact rather than the opinion of whoever wrote the code. The repository's own whole-tree checker (a `lint.sh`, a full type-check) is not a `CHECK:` either: it fails on files this ticket never touched and blocks it on somebody else's work. A behaviour the ticket must keep as it is, as a restructuring must, is decided by a pin (**principle-a-check-must-be-able-to-fail**), a criterion green before the work by design. A ticket that changes a feature file already on the base branch carries one pin from that file. The pin is the cheapest `check:` that can see the behaviour this change touches. A journey is that pin only when it is the only such `check:`, because each journey starts and stops the product again. The `check:` of a sub-feature this ticket changes or removes is not a pin. This ticket changes the behaviour that command guards, so the command is expected to go red. Copy the command from the feature file's `check:` line.

Most of what you want to say about the work does not belong under `## Acceptance criteria`. Ask **the five questions** in order and stop at the first yes:

1. **Is the rule a comparison (equal, matches, counts, over a threshold) against something a machine can reach?** It is a criterion. Write its `CHECK:` and `EXPECT:`.
2. **Is the rule a judgement, against something a machine can reach?** Whether an interface is deep rather than a pass-through, whether a passage says enough, whether an error message tells the caller what to do next, whether the test behind a criterion could ever have failed. Code review decides these, in a session other than the one that wrote the code, and its `Spec` axis reads the `## Implementation Decisions` subsection of the spec this ticket's **Parent** names. Leave the rule out of `## Acceptance criteria` and write it in that subsection as one sentence.
3. **Is the property a person's reaction?** Whether a newcomer knows what to do, whether the wording lands, whether a morning page is legible at a glance. The person is the instrument, not a fallback judge: no agent can stand in, because the agent is not who is being measured. It becomes its own ticket, of kind *reaction*; see [person-ticket.md](person-ticket.md).
4. **Could a machine decide it, if only it could reach the thing?** Two answers hide under one question, and they part on whether the reach is something you build.
   - **It is.** The state lives inside software you are about to write, and something has to put the system there: a seeded row, a stub scripted to answer in a set order. This stays a criterion. But the thing that reaches the state has to be named in the spec's Testing Decisions, under **How a test arrives at a state**, and owned under some ticket's **Owns**. That ticket builds it: a criterion that assumes a mechanism nobody builds fails on the night it first runs. Missing either, the state is out of reach for this batch, and the criterion becomes its own ticket of kind *reach* (see [person-ticket.md](person-ticket.md)), whose retiring line names the mechanism that has no name yet, or the ticket that would own it.
   - **It is not.** A signed installer on a clean machine, a login against the real provider, a notification arriving on a phone. Its own ticket, of kind *reach*; see [person-ticket.md](person-ticket.md).
5. **Is it a choice rather than a check?** No true or false, only a preference, and the answer decides what to build next rather than whether what was built is right. It is the owner's: put it to them with the options and the one you would take, and write the answer into the ticket's **What to build** as a numbered point of its own.

If no command exists because the spec never decided how this is verified, do not invent one: the spec's Testing Decisions decides it first.

Every criterion is four lines, and carries a number you assign as you write it and never renumber.

```
- [ ] AC1: POST /projects with a name that already exists returns 409 and error name-duplicate
  CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"
  EXPECT: /Tests\s+1 passed/
  EVIDENCE: pending
```

Derive `CHECK:` and `EXPECT:`; do not invent either:

- `CHECK:` comes from Testing Decisions: its layer, that layer's directory, and the precedent it names. Open the precedent, copy its framework and its single-file invocation, then aim that at the file and case this ticket adds.
- `EXPECT:` is a **success-only marker**: the line the precedent prints only when it passed. Run the precedent once and copy that line. `ok`, `passed` or `done` on their own also appear in failing output; take the whole counted line.

`CHECK:` takes the object it checks from one of two places: this ticket itself (the number comes from `$MMW_TICKET`, or from the branch name `issue-<n>`), or something this ticket names by number. When the objects only exist at run time, walk the tracker's native relationships out from an anchor the ticket names: `gh api repos/{owner}/{repo}/issues/<n>/sub_issues`. A `CHECK:` must not search for its own object; searching and taking the first hit (`gh issue list --search … | head -1` and its kind) checks whatever the search happens to return, and often cannot fail at all.

`CHECK:` brings the state it needs and puts back the shared state it changed. Criteria run one at a time in ledger order, each in its own shell with cwd fixed at the repository root, so `cd` cannot reach another one, but the branch, the ticket and the working tree are shared, and `--reverify` runs every criterion a second time: switch a branch and switch it back; reopen a ticket the next criterion needs open; stop a server you started. The system's own state (the row, the balance, the screen) is put there by what question 4 names.

**A criterion is also exposed to the rest of its own batch.** Every ticket lands on the same base branch, and the closing pass re-runs every criterion of the batch there, so a criterion that names something a later ticket may change is decided by that ticket's work rather than by its own. Two shapes do it: a sweep of the whole repository (a `grep` for a name that must now be gone, a count over the tree), which any later ticket can put back in a note, a doc or a comment; and a criterion that names a test case, a function or a symbol by a name a later ticket may rename. Put such a criterion on the batch's last ticket, or give the name one owner: the file that holds it is under exactly one ticket's **Owns** in the whole batch, not merely among the tickets that can run at the same time, so no other ticket of the batch may write it.

## Labels

A ticket carries `mmw:ticket`. A ticket an agent works also carries `ready-for-agent` and one worker label; a ticket a person must judge ([person-ticket.md](person-ticket.md)) carries `ready-for-human` instead, and no worker label. `junior-worker` is the default, and a ticket goes to `senior-worker` when getting it wrong is wrong **silently** (money that has to reach a terminal state, recovery after a crash, a contract an installed base already reads, a security default), because none of those fail on the day they are written. A ticket whose **Seam** names a test layer that has a precedent to copy (the spec's Testing Decisions names one for that layer, or, outside a spec, `TESTING.md` and the nearest test of the same kind) stays on `junior-worker`.

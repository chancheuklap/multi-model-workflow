# Ticket format

The independent and batch writing entries use this shared format and criterion-classification method. An opening call creates only its problem record. Replace guidance with content.

<issue-template>


## Problem

Keep the independent problem record unchanged. Omit this section for a spec ticket. The opening entry owns its format.

## Parent

A reference to the parent spec on the tracker, followed by the numbered Implementation Decisions sections this ticket implements (for example, "#12, Implementation Decisions sections 5 and 7"). The first issue here is read as the ticket's spec. A ticket a playbook opens outside any spec writes "None".

## What to build

Open with one sentence: the one action the product's user takes, and what they see once this ticket is done.

For each step of a wide refactor's expand–contract sequence and the final UI ticket that only removes mount points, open instead with one sentence naming the sequence and its step, either expand, migrate, contract, or mount-point removal.

Then write the end-to-end behaviour as numbered points, not layer-by-layer implementation, one thing per point, each point complete with the test that decides it and the reason it is there. A person scans it for the one point they came for, an agent works from it with none of your context, and neither gets through one long paragraph. A choice the user settled during preparation is a point of its own here, stated as the ticket's decision.

**Implementation contract.** Name the data shape and its organizing structure per **principle-model-the-domain**. Keep edits surgical, re-grounding upstream-derived files against their source. A shared-primitive improvement reaches every consumer and is verified in each. A prototype sketch is a baseline under Read first: its `not implemented` bodies become code and its pseudocode becomes logic. A deviation is surfaced as a `contract` child rather than absorbed. It may land as its own first commit under **principle-sequence-verifiable-units**, with temporary breakage governed by **principle-outcome-oriented-execution**. The criteria cover the behavior the sketch and the owner's words describe.

## Read first

The source material behind the sections named under **Parent**: decision tickets, ADRs, research answers, prototype directories and verdict comments, domain docs, copied from what those sections cite, one per line, each with a word on what it settles. For a UI ticket, list the exact path to the winner prototype and the affected feature file from the product's feature map, each marked as a baseline. The implementer reads these and nothing else from the spec's Sources. Whatever here records a settled conclusion (the chosen artifact of a prototype, the decision an ADR states in the paragraph under its title, the resolution of a decision ticket) is a **baseline**: a contract, not a reference, marked as one on its line. Every line is something a worker can open: a repository path, an issue or comment link, or a named installed skill and its reader-specific entry. A worker runs headless, so it cannot open a claude.ai page (it answers 403) or see a tool or fact only an interactive session signed in to claude.ai has, such as the Artifact tool: observe such a fact yourself, copy what it settles into a file in the repository, commit it on the branch the worker is cut from, and cite that path; `--lint` refuses a claude.ai link here. Write "None" if the sections cite nothing.

## Seam

Where this ticket is verified: the test layer and directory from the spec's Testing Decisions, and the precedent to copy. Include only the repository's own tests here, not e2e tests. Then, from the same section's **How a test arrives at a state**, what puts the system into the states the criteria below name; when this ticket is the one that builds that, say so here as well as under **Owns**. A ticket with no spec takes its test layer, directory and precedent from the repository's own tests, and names how the test reaches each required state here. Put the mechanism it builds under **Owns** as well.

## Owns

No ticket's Owns lists `tests/e2e/`, `.agents/skills/verify-<product>/`, or the prototype's leaf directory.

The repository-relative paths this ticket may write, one per line, the test directory or test file from **Seam** included. Each entry is a path, optionally followed by a space and a note in parentheses, or by an attached full-width parenthetical note. A path ends at its first whitespace or full-width `（`. ASCII parentheses belong to the path, so an attached ASCII note is not recognised. Mark what this ticket creates with "(new)". A file this ticket must edit to put what it creates in service (the registry, router, stylesheet, parent template or index that has to name it) belongs here as well, though another ticket created it: this section says where this ticket may write, not where its own code lives. No absolute path, no `..`, no bare `**`. Match the granularity to the split: a directory glob where this ticket owns the directory alone, file paths where several tickets divide one directory. Two tickets that run at the same time may both list one file: this section states the expected scope, and an overlap is resolved by the worker at `integrate` or by the landing's bounce and retry, never by a **Blocked by** edge, which means only that this ticket needs what another builds. Everything outside these paths is read-only for this ticket. A change a ticket needs in a tool skill outside the repository is not an entry here: the toolbox is improved in use, and the change is made there at once.

A ticket that deletes or renames a file, a script, a contract field, or a criterion word takes every place `grep` finds that name into its own **Owns**. Find those places by grepping the name, not by listing from memory.

- src/import/**
- tests/import/**
- src/import/ui/** (new)

## Acceptance criteria

Use **Acceptance criteria** below. Keep `EVIDENCE: pending`; closeout replaces it.

- [ ] AC1: <the behavior and exact values required by the baseline>
  CHECK: <the command that decides it>
  EXPECT: <the line only a passing run prints>
  EVIDENCE: pending

</issue-template>

## Acceptance criteria

Three rules bind how each one is worded:

1. Observable external behaviour, from the prepared seam or a user-visible UI. Not internals.
2. Exact values (numbers, copy, state names, field names) copied from the prepared decision baseline or the chosen prototype artifact. For a screen's appearance, text and interactions, copy the winner prototype. No "appropriate", "correct", or "as expected". These sources are the baseline (**principle-baseline-is-the-contract**).
3. One behaviour per criterion, independently true or false. Split compounds.

**A criterion is decided by a command, or it is not a criterion.** Everything under `## Acceptance criteria` is run by machine, and that is what makes "it passed" a fact rather than the opinion of whoever wrote the code. Most of what you want to say about the work does not belong there. Ask **the five questions** in order and stop at the first yes:

1. **Is the rule a comparison (equal, matches, counts, over a threshold) against something a machine can reach?** It is a criterion. Write its `CHECK:` and `EXPECT:`.
2. **Is the rule a judgement, against something a machine can reach?** Whether an interface is deep rather than a pass-through, whether a passage says enough, whether an error message tells the caller what to do next, whether the test behind a criterion could ever have failed. Review decides these in a session other than the one that wrote the code. Leave the rule out of `## Acceptance criteria`. For a spec ticket, put it in its Parent's numbered `Implementation Decisions` subsection through the **to-spec** skill's revise entry. For an independent ticket, put it as an unnumbered review constraint under **What to build**, or in a named baseline under **Read first**, so its worker and reviewer can read it.
3. **Is the property a person's reaction?** Whether a newcomer knows what to do, whether the wording lands, whether a morning page is legible at a glance. The person is the instrument, not a fallback judge: no agent can stand in, because the agent is not who is being measured. It becomes its own ticket, of kind *reaction*; see `references/person-ticket.md`.
4. **Could a machine decide it, if only it could reach the thing?** Two answers hide under one question, and they part on whether the reach is something you build.
   - **It is.** The state lives inside software you are about to write, and something has to put the system there: a seeded row, a stub scripted to answer in a set order. This stays a criterion. For UI e2e tests, use the same steps on both targets as the `create-verification-skill` skill's `references/tests-from-prototype.md` says, instead of the following test-seam requirements. For the repository's own tests, name the mechanism under the spec's Testing Decisions **How a test arrives at a state**, or under **Seam** for an independent ticket, and put it under the implementing ticket's **Owns**. That ticket builds it: a criterion that assumes a mechanism nobody builds fails on the night it first runs. Missing either, the state is out of reach for this prepared work, and the criterion becomes its own ticket of kind *reach* (see `references/person-ticket.md`), whose retiring line names the mechanism that has no name yet, or the ticket that would own it.
   - **It is not.** A signed installer on a clean machine, a login against the real provider, a notification arriving on a phone. Its own ticket, of kind *reach*; see `references/person-ticket.md`.
5. **Is it a choice rather than a check?** No true or false, only a preference, and the answer decides what to build next rather than whether what was built is right. The user is here now, so ask them: carry the choice into the batch quiz, or return it to the current independent preparation, with the options and the one you would take, and write the answer into the ticket's **What to build** as a numbered point of its own.

For non-e2e criteria, settle a missing verification decision in the spec's Testing Decisions through the **to-spec** skill's revise entry, or in the independent ticket's **Seam** and implementation plan. Return an unresolved owner decision to the caller. A command does not invent its own requirement.

Every criterion is four lines, and carries a number you assign as you write it and never renumber.

```
- [ ] AC1: POST /projects with a name that already exists returns 409 and error name-duplicate
  CHECK: pnpm vitest run tests/api/projects.create.test.ts -t "duplicate name returns 409"
  EXPECT: <copy vitest.expect from runner-summaries.json in the verify-ticket skill>
  EVIDENCE: pending
```

Derive `CHECK:` and `EXPECT:` from the prepared baseline and its named test precedent:

- For UI tickets, read the product's `verify-<product>` skill's Read first, Rules, Drive and Evidence. Write tests as the `create-verification-skill` skill's `references/tests-from-prototype.md` says. Use Cleanup after starting a product.
- Find affected existing features with the **maintain-verification-skill** skill's **Find affected features** entry, using the prepared behavior decisions. For unchanged behaviour, take the e2e tests registered in the feature map as pins, green on the base branch. Where no test exists, write one from the current code and register it in the feature map. For changed behaviour, rewrite the old cases from the winner prototype as acceptance tests, red on the base branch. Move those rewritten cases into this ticket's own new file and remove them from the old file; the cases left there stay pins. Update the feature file's sentences about what the product can do at the same time, and list it as a baseline.
- Commit and push these tests and feature files to the supplied effort branch before execution. An independent ticket uses `fix-<n>`. For a batch, prepare them before `dispatch.sh open`. An effort that already has its effort branch, `map-<map number>` for a map or the `fix-<n>` of the ticket the spec came from, uses that branch as the night's branch. Otherwise create the night's branch from the project branch before committing these assets. Do not commit them to the project branch. The checkout where `check` and `open` run names the night's base branch, and `open` merges the project branch into it. Workers' checkouts are cut from `origin`, so local-only commits reach no worker.
- For a slice with back-end work, add a back-end test `CHECK:` naming its dedicated test database, separate from the e2e database.
- When a ticket's code calls an interface built in another repository, read the producer's code on its project branch. List the interface's actual rules under **What to build**, including fields, accepted values, status codes, and error bodies, each with the producer's path and line. Add one criterion whose test asserts each rule.
- For a UI acceptance criterion, copy the whole CHECK line and any `TIMEOUT:` from Launch, aimed at its own new test file. For pytest and Vitest, copy the standard `EXPECT:` from the verify-ticket skill's `runner-summaries.json` in its scripts directory. For other runners, copy the passing e2e summary as `EXPECT:`. For a UI pin, use Launch's CHECK line aimed at the existing test file registered in the feature map. Nighttime CHECK lines run only `product`. For other criteria, `CHECK:` comes from the spec's Testing Decisions or the independent ticket's **Seam**: its layer, directory and named precedent. Open the precedent, copy its framework and its single-file invocation, then aim that at the file and case this ticket adds. Run the `CHECK:` once on the base branch, where it must fail. When it passes there, it cannot see this ticket's work: its selector also matches cases that already exist, or the command never looks at the thing the criterion names (a checker asked whether a file is referenced that only checks that referenced files exist). Make it run the new case by its own name first, before any wider selector, or aim it at the thing itself, and run it on the base branch again to see it fail. When the prepared baseline quotes text the product must hold word for word, also run the `CHECK:` once on a copy of that text, where it must pass: a pattern or a split marker that also occurs inside the quoted text (a heading named in a sentence, an old name inside the new one) fails on a correct product. A pin is the exception: it passes there by design. When this ticket changes the command a pin runs (a checker given a new rule), the pin must also pass once that change is in: find what in the base branch's tree the new rule would report, and settle each case in **What to build** before you publish.
- A `CHECK:` never runs the repository's `scripts/check`: the dispatch skill runs it on every ticket's merge result, so a criterion that repeats it proves nothing this ticket adds, and fails on work this ticket never touched (**principle-subtract-before-you-add**).
- When a `CHECK:` stage runs `pytest` or `vitest` as its command, copy that runner's `expect` value unchanged from the verify-ticket skill's `runner-summaries.json` in its scripts directory, including its flags. That file is the only home of the standard `EXPECT:` patterns. A command behind `uv run`, `pnpm`, `npx` or `python -m` counts. A runner name used only as an argument does not. Split a criterion that runs both runners into one criterion per runner. Write no pattern of your own, including a test count or a marker the command echoes. The lint reports `runner-expect` when the standard is not used.
- For other commands, `EXPECT:` is a **success-only marker**, the line the precedent prints only when it passed. Run the precedent once and copy that line. `ok`, `passed` or `done` on their own also appear in failing output; take the whole counted line.

`CHECK:` takes the object it checks from one of two places: this ticket itself, or something this ticket names by number. When the objects only exist at run time, walk the tracker's native relationships out from an anchor the ticket names (a parent's sub-issues, for one). A `CHECK:` names its object as **principle-test-behavior-not-implementation**'s **Name the object a check checks** says.

`CHECK:` brings the state it needs and puts back the shared state it changed. Criteria run one at a time in ledger order, each in its own shell with cwd fixed at the repository root, so `cd` cannot reach another one, but the branch, the ticket and the working tree are shared: switch a branch and switch it back; reopen a ticket the next criterion needs open; stop a server you started. The system's own state (the row, the balance, the screen) is put there by what question 4 names.

## Timeouts and paths

A criterion may carry a fifth line, `TIMEOUT: <seconds>`, when its `CHECK:` needs longer than the 600 seconds every `CHECK:` gets by default. The largest `TIMEOUT:` on a ticket applies to all its criteria, in every run. A `CHECK:` runs with `$MMW_TICKET` set to the ticket's number and, once a worker has started on the ticket, `$MMW_BASE_REF` set to `origin/<the branch the ticket merges into>`, so a command can name either without writing it in.

Avoid implementation file paths or code snippets: they go stale fast; paths to source material stay, and so do the two kinds of path a ticket cannot do without: the test directory or test file under **Seam**, and the paths under **Owns**, which say where this ticket may write, not where its code lives. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts, not a working demo, just the important bits.

---
name: implement
description: Implement a piece of work based on a spec or set of tickets. Use when you were dispatched onto a ticket, or picked one up yourself.
---

Implement the work described by the user in the spec or tickets.

## Resolve `<engine>` and `<dispatch>` once

Commands of the `verify-ticket` skill are written `<engine> …` below; commands of the `dispatch` skill are written `<dispatch> …`. Resolve each from that skill's own `SKILL.md`; the path differs by machine and by host.

## Claim, read in, write the code

First claim the ticket: `<engine> <n> --preflight`. On `NOT_READY`, stop: the reason is already on the ticket. If you picked the ticket up yourself, with no `start` behind you, do what the `dispatch` skill's `references/inside-a-ticket.md` says before that claim.

The branch may already carry the commits of an earlier worker of this ticket whose session ended, among them a `wip(#<n>): uncommitted work of …` commit holding what it left uncommitted. They are this ticket's work: carry on from them.

Then check the ticket is coherent: its title and **What to build** describe the same vertical slice; every glob under **Owns** either matches an existing path or is marked `(new)`.

Then read yourself in: the ticket in full, comments included, and its own open sub-issues (`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100 --jq '.[] | select(.state=="open")'`), as a supplement to **What to build** (whether you do them goes under `Decisions I made on my own`); then every item under its **Read first**, each through to its conclusion: the last section of a research file, an ADR's decision in the untitled paragraph under its title, a design package pulled into the repository, a prototype's leaf `README.md` read to its verdict. A baseline in **Read first** is anything there that records a settled conclusion, and it is a contract, not a reference. A design package is copied exactly; a prototype is rewritten to production standard, keeping the shape its verdict settled on. Then follow **Parent** to the spec and read only the Implementation Decisions sections the ticket names, plus its Testing Decisions and Out of Scope, not the whole spec. Then the domain glossary (the root `CONTEXT.md`, or the `CONTEXT.md` of each context `CONTEXT-MAP.md` lists that this ticket touches): where it has a term for the thing you name, use that term. When **Read first** lists a screen contract, read `references/writing-interface-code.md`.

Then say in one sentence which **seam** this ticket is tested at, copied from the ticket's **Seam**.

Every `--sub-issue` run below is in the `verify-ticket` skill's `references/sub-issues.md`. A fault in the pipeline itself (`verify-ticket.py`, `dispatch.sh`, a judge script, `lease.py`, a hook, `.mmw/target.json`): `<engine> <n> --sub-issue fault <file>`, whose body is the command you ran and the output you saw, then stop.

While writing code:

- The baseline is the contract. Copy the values, wording, states and interface shapes of every baseline in **Read first** from it rather than writing them again from memory. When something this ticket was told to follow does not hold, whether a baseline under **Read first**, a spec section named by **Parent**, or an acceptance criterion lacks a state, field, interaction or case or contradicts another such source, keep going and run `<engine> <n> --sub-issue contract <file>`. The child quotes what does not hold and states what in that same source still holds and must be preserved. A wrong `CHECK` is a `contract` child too: name the acceptance criterion, quote what is wrong, and state what it should be. Never quietly change a baseline, never quietly add around one. A check that will not pass is answered by fixing the code or abandoning the criterion, never by bending the baseline, the harness or the test.
- Put no question on the screen. Take the option the ticket, its baselines and the spec make most likely, write one line for it under **Decisions I made on my own**, and keep going. A question whose answer would change what the ticket delivers gets `<engine> <n> --sub-issue decision <file>` instead, and the rest of the work carries on.
- Before changing a function, grep every caller and fix the shared code once; before adding a branch or guard to an existing flow, name the branch or file it makes unnecessary and delete it in the same commit.
- Before writing a helper, search the repository and **Read first** for one that already exists.
- Before adding a file, a dependency or a configuration entry, say why the existing one is not enough.
- Whatever you simplify, keep intact: security, error handling that prevents data loss, accessibility, and anything the ticket explicitly asks for: **What to build**, every acceptance criterion, the baseline, the interface under **Seam**.
- For a file outside **Owns**: change it when a criterion cannot pass otherwise, and it lands under `Outside Owns:` in the closing comment; when the change is merely convenient, leave it and run `<engine> <n> --sub-issue deferred <file>`. A file owned by a ticket that can run beside this one (neither blocks the other, directly or down a chain) is never changed from here, whatever needs it: run `<engine> <n> --sub-issue contract <file>`, because one file has one writer at a time and the cut missed an edge.

Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and, once at the end, the tests the repository's own instructions name for what this ticket changed; `--closeout` runs the repository's `checks` itself.

Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the ticket asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files: roughly one focused test per stated behavior. This is about extras only: implement every behavior the ticket asks for, completely.

## Shared experience while implementing

Your first prompt carries two Memory indexes, one line per record (`id`, `title`, its
first line as `applies`, `space`). Before working, open every record whose title or
`applies` line bears on this ticket; skip the rest. A `truncated:` line means more
task records exist than are listed: search them with the task-scope command below.

```sh
nmem --json memories show "<id>" --space "<space from the index line>"
```

Current artifacts, verified evidence, the user's instructions, repository
instructions, the ticket, and its parent spec override Memory. Verify every Memory
against current repository evidence before acting on it.

When a command or tool behaves in a way that the ticket, repository authority, and
the records you opened do not explain, search the current task with the exact error,
command, and component before trying a workaround; if that has no answer, search
repository and approved toolbox experience. Keep the query to that error, command and
component, and keep `--` before it: Nowledge returns nothing for a query that names
something no record holds, which long prose always does, and reads a query that starts
with `-` as an option.

```sh
nmem --json memories search --space "$NMEM_SPACE" --label "$MMW_TASK_SCOPE" \
  --limit 10 -- "<exact error + command + component>"
nmem --json memories search --space "$NMEM_SPACE" --label mmw-experience \
  --limit 10 -- "<exact error + command + component>"
```

Save a Memory as soon as all three conditions hold: another ticket or later agent may
reuse the fact, a current command result or authority verifies it, and the ticket and
code do not already make it obvious. Evaluate the same trigger again at every
meaningful milestone or handoff. Save only while `MMW_TASK_SCOPE` is `mmw-map-<n>` or
`mmw-spec-<n>`; an empty value means routing failed and nothing is written. To save or correct one, follow `references/saving-memory.md`.

## Closing steps

Once done, commit your work to the current branch and work through the closing steps below.

A ticket that already carries a run of your own (a `ticket.checked` event whose `run` is `self`), or a `reviewer.reported`, `worker.decided`, or worker reverify event, is work you were prompted back into. Claim it again first: `<engine> <n> --preflight`. Then read the ticket's comments and find your row; each condition is an event the ticket itself carries, named in the trailing `<!-- mmw {...} -->` block of its comment, and the newest comment alone does not say where you are, because step 3 posts its comment in the middle and has a fix round after it.

| The ticket carries | Resume at |
| --- | --- |
| a `ticket.returned`, or a `ticket.bounced`, newer than its newest `ticket.passed` | step 1, then step 4 onward: integrate and run the worker criteria, then make the final full run and close out |
| no run of your own | step 1 |
| a run of your own, no `worker.decided` | step 2 |
| a `worker.decided`, no `reviewer.reported`, and no `reviewer.started` or a `reviewer.lost` after the newest one | step 3, at its start: `<dispatch> start <n> reviewer` |
| a `reviewer.started` with no `reviewer.reported` and no `reviewer.lost` after it | step 3, asleep on the reviewer: end your turn, and you are woken when its report lands |
| a `reviewer.reported`, and no run of your own newer than it | step 3, at its fix round: fix the in-ticket findings, then re-run step 1 |
| a run of your own newer than the `reviewer.reported`, no worker reverify after it | step 4 |
| a worker reverify whose `commit` is `HEAD`, with nothing newer | step 5 |

Other events do not move you. Two need an action: a `ticket.checked` of run `repo-checks` with result `unmet` means the draft was fine and the repository's own suite was not (step 8 says what to do); a `worker.queued` means a run found no product slot free (step 1, exit 3).

Three `ABANDON` kinds, and the machine branches on each. `failed`: it ran and did not pass, after as many rounds in step 1 as you judged worth spending, or still failing after the review fix or final run; the reason says what each round tried. `stuck`: it will not start, or cannot be done within the task: a `CHECK` that will not run, a missing credential or device; the reason names the routes tried or points at the sub-issue that records them. A human step or an unreachable product while the product runs is not `stuck`: rules 3 and 4 of the `ui-acceptance` skill's **Five rules while the product is running** route it. `decision`: both options are legal and neither the ticket nor the spec says; write the question, the options, and the default when nobody answers; a UI difference never goes here. Any `failed` or `stuck` turns the whole ticket into `HANDOFF REQUIRED`; `decision` does not: its sub-issue is already open, and the rest all passing is still `ALL MET`.

1. Integrate `origin/<base branch>` first: `<dispatch> integrate <n>`, from this ticket's worktree. Exit 3 leaves a conflicted merge in the tree: do what its stderr says, and note each trade-off under `Decisions I made on my own`. A clean merge that makes repository checks red uses the `resolving-merge-conflicts` skill too. Exit 2 names the condition that prevented integration; a pipeline failure becomes a `fault` sub-issue, then stop. Never rebase, abort or push from this integration command. Then run every criterion: `<engine> <n>`. A criterion passes only when its `CHECK` exits 0 and its output matches `EXPECT`. Exit 3: no product slot was free and nothing ran; end your turn, and on the `#<n> worker.queued` wake, ack it and run the same command again. How many rounds a criterion gets is your judgement: keep fixing while a fix is in sight, and when none is, write `ABANDON: AC<n> failed <what each round tried>` and carry on with the rest; the closeout counts no rounds, so that line is the whole record of the trying.

   Done when `<engine> <n>` has recorded a run of your own after the integration.
2. Post the decisions comment, once: `<engine> <n> --decisions <file>`. The file is two sections, each opened by its `## ` heading: `## Decisions I made on my own`, with every line written so far, one per line, in the shape the closing comment uses; and `## Outside Owns`, with the `Outside Owns:` line of your newest run (its `ticket.checked` event, run `self`), followed by one sentence per file saying which criterion could not pass without it; `None` when that line is `None`. It is posted here, before the reviewer starts, so the review judges every line of it, and once: the review's fix round adds nothing to it, and the closing comment carries the final version.

   Done when `--decisions` exits 0.
3. Start the reviewer: `<dispatch> start <n> reviewer`, then end your turn. You are woken with `#<n> reviewer.reported` once its report is on the ticket. Then read the report, the comment on the ticket that carries that event (`<dispatch> wait <n> reviewer` prints the event with the two commits it read), and `<dispatch> ack <n> reviewer.reported`. Start exits 2: that is a pipeline fault; open the `fault` child as above, then stop. One reviewer per round; after `reviewer.lost`, start another. The in-ticket round is first: fix the in-ticket findings once, under the writing rules that governed the first write, and re-run step 1. An in-ticket finding you do not fix is answered `refuted:`, which says you checked and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count. Then, for each out-of-ticket review finding whose body the in-ticket round has not made untrue, run `<engine> <n> --sub-issue finding <file>`.

   Done when the review comment is on the ticket (a session's state never is), each in-ticket finding is fixed or `refuted:`, and each out-of-ticket finding still true has its `finding` child.
4. Run every criterion one final time: `<engine> <n> --reverify --actor worker`. It runs after the last step that writes a commit, including the review fix, and includes criteria earlier runs already ticked. If anything still fails, write `ABANDON: AC<n> failed` for each failure and close out `HANDOFF REQUIRED`; this final run gets no fix round.

   Done when the final run is on the ticket at `HEAD`.
5. Audit: re-read the whole ticket and every item under **Read first**, trace every criterion to its latest `EVIDENCE:`.

   Done when you can name each criterion's latest `EVIDENCE:` line, and for each item under **Read first**, where the branch follows it.
6. Tell the tickets whose files you changed: `<engine> <n> --touched`.

   Done when `--touched` exits 0.
7. Cut loose what only a person can settle, then write the closing comment to a draft file. A criterion that waits only on one sentence from a person: write `ABANDON: AC<n> decision <question, options, and the default if nobody answers>` **and** run `<engine> <n> --sub-issue decision <file>`, then keep working the rest; the ticket does not stop. Then `<engine> <n> --draft`, which prints the path it wrote as `DRAFT: wrote <path>`; give that run no path of your own. Fill every `<fill>`: `skipped:` as `[X], add when [Y]`; each review finding as `fixed <commit>` or `refuted: <what actually happens at path:line>`; each criterion under `Green before work:` with the landed ticket that did that work, or with the fact that this `CHECK` cannot see this ticket's behaviour (then also a `contract` child); `Decisions I made on my own` with every line written so far. Put each `ABANDON:` line under its criterion. A draft with a `failed` or `stuck` line opens `HANDOFF REQUIRED: <abandoned> abandoned (<kinds>), <unmet> unmet, <met> met of <total>` instead of `ALL MET`; then recount `Counts:` against the draft.

   Done when the draft has no `<fill>` left and `Counts:` matches it.
8. Close the ticket: `<engine> <n> --closeout <draft>`. Never close the ticket or swap its labels yourself: a hook blocks the command. Open no pull request: the main agent lands the ticket once it is closed, and running `land` from this session would stop it. A refusal changes nothing on the ticket; its first line names the first problem and the `--check-only` command that lists the rest: fix the draft, or what it describes, and run it again. When it stops because the repository's own checks failed, fix the code, run that suite yourself, commit, make step 4's final run again, and close out again.

   Done when `--closeout` exits 0.

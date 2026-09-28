---
name: implement
description: Implement a piece of work based on a spec or set of tickets. Use when you were dispatched onto a ticket, or picked one up yourself.
---

Implement the work described by the user in the spec or tickets.

Commands of the `verify-ticket` skill's `verify-ticket.py` and the `dispatch` skill's `dispatch.sh` are named bare below.

## Claim, read in, write the code

First claim the ticket: `verify-ticket.py <n> --preflight`. On `NOT_READY`, stop: the reason is already on the ticket. If you picked the ticket up yourself, with no `start` behind you, do what the `dispatch` skill's `references/inside-a-ticket.md` says before that claim.

The branch may already carry the commits of an earlier worker of this ticket whose session ended, among them a `wip(#<n>): uncommitted work of …` commit holding what it left uncommitted. They are this ticket's work: carry on from them.

Then read yourself in, until you know what this ticket delivers, what it must not contradict, and the words the repository uses for them: the ticket in full, comments included, and its own open sub-issues (`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100 --jq '.[] | select(.state=="open")'`), as a supplement to **What to build** (whether you do them goes under `Decisions I made on my own`); then every item under its **Read first**, each through to its conclusion: the part of a research file that answers its question, an ADR's decision in the untitled paragraph under its title, a design package pulled into the repository, a prototype's leaf `README.md` read to its verdict. A baseline in **Read first** is anything there that records a settled conclusion, and it is a contract, not a reference. A design package is copied exactly; a prototype is rewritten to production standard, keeping the shape its verdict settled on. Then follow **Parent** to the spec: read its Problem Statement and Solution, the few lines that say who uses this and why, then only the Implementation Decisions sections the ticket names, plus its Testing Decisions and Out of Scope, not the whole spec. Where the ticket is silent, choose what serves the person the Problem Statement names. Then the domain glossary (the root `CONTEXT.md`, or the `CONTEXT.md` of each context `CONTEXT-MAP.md` lists that this ticket touches): where it has a term for the thing you name, use that term. When **Read first** lists a screen contract, read `references/writing-interface-code.md`.

Every `--sub-issue` run below is in the `verify-ticket` skill's `references/sub-issues.md`. A fault in the pipeline itself (the pipeline's own scripts, a hook, or `.mmw/target.json`): `verify-ticket.py <n> --sub-issue fault <file>`, whose body is the command you ran and the output you saw, then stop.

While writing code:

- The baseline is the contract. A baseline is a decision someone already paid for: a user's answer, a prototype that won, a page they signed off. Rewriting it from memory, or improving it, reopens that decision where nobody who made it can see; a `contract` child reopens it where they can. Copy the values, wording, states and interface shapes of every baseline in **Read first** from it rather than writing them again from memory. When something this ticket was told to follow does not hold, whether a baseline under **Read first**, a spec section named by **Parent**, or an acceptance criterion lacks a state, field, interaction or case or contradicts another such source, keep going and run `verify-ticket.py <n> --sub-issue contract <file>`. The child quotes what does not hold and states what in that same source still holds and must be preserved. When the rest of the ticket depends on the answer, end your turn: the child wakes the orchestrator, which corrects the source and resumes you, or leaves the question to the user. A wrong `CHECK` is a `contract` child too: name the acceptance criterion, quote what is wrong, and state what it should be. Once a batch is published, only its orchestrator or the user edits a spec, ticket body or acceptance criterion. Never quietly change a baseline, never quietly add around one. A check that will not pass is answered by fixing the code or abandoning the criterion, never by bending the baseline, the harness or the test. The checks exist so the user can trust a closed ticket without reading its code. An honest `HANDOFF REQUIRED` costs them one look in the morning; a false `ALL MET` lands broken behaviour under a green mark, and every ticket built on this one inherits it.
- Put no question on the screen. Take the option the ticket, its baselines and the spec make most likely, write one line for it under **Decisions I made on my own**, and keep going. A question whose answer would change what the ticket delivers gets `verify-ticket.py <n> --sub-issue decision <file>` instead, and the rest of the work carries on. Write each line for the reviewer, who judges it, and for the user, who reads it in the morning without your context: a choice a user would notice in the product (a label, a default, what a page shows or hides) is the one most worth a line.
- Before changing a function, grep every caller and fix the shared code once; when what you add supersedes an existing branch, guard or file, delete it in the same commit.
- Before writing a helper, search the repository and **Read first** for one that already exists.
- Before adding a file, a dependency or a configuration entry, write under **Decisions I made on my own** why the existing one is not enough.
- Whatever you simplify, keep intact: security, error handling that prevents data loss, accessibility, and anything the ticket explicitly asks for: **What to build**, every acceptance criterion, the baseline, the interface under **Seam**.
- For a file outside **Owns**: change it when a criterion cannot pass otherwise, and it lands under `Outside Owns:` in the closing comment; when the change is merely convenient, leave it and run `verify-ticket.py <n> --sub-issue deferred <file>`. A file owned by a ticket that can run beside this one (neither blocks the other, directly or down a chain) is never changed from here, whatever needs it: run `verify-ticket.py <n> --sub-issue contract <file>`, because one file has one writer at a time and the cut missed an edge.

Read the `tdd` skill's `SKILL.md` and follow it where possible, at pre-agreed seams. Where an acceptance criterion's `CHECK:` names a test case, that case is your first red test: run it before writing the code it covers and read why it fails. Red that comes from a missing file, an import error or a typo in the case name proves nothing; the test counts as red only when it fails because the behaviour is absent. No later step does this for you: the claim-time baseline ran before the test existed, and the review reads tests without running them.

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
code do not already make it obvious. To save or correct one, follow `references/saving-memory.md`.

## Closing steps

Once done, commit your work to the current branch and work through the closing steps below.

A ticket you are prompted back into: claim it again first, `verify-ticket.py <n> --preflight`, and carry on at the step its `RESUME:` line names.

Three `ABANDON` kinds, and the machine branches on each. `failed`: it ran and did not pass, after as many rounds in step 1 as you judged worth spending, or still failing after the review fix or final run; the reason says what each round tried. `stuck`: it will not start, or cannot be done within the task: a `CHECK` that will not run, a missing credential or device; the reason names the routes tried or points at the sub-issue that records them. A human step or an unreachable product while the product runs is not `stuck`: rules 3 and 4 of the `ui-acceptance` skill's **Five rules while the product is running** route it. `decision`: both options are legal and neither the ticket nor the spec says; write the question, the options, and the default when nobody answers; a UI difference never goes here. Any `failed` or `stuck` turns the whole ticket into `HANDOFF REQUIRED`; `decision` does not: its sub-issue is already open, and the rest all passing is still `ALL MET`.

1. Integrate `origin/<base branch>` first: `dispatch.sh integrate <n>`, from this ticket's worktree. Exit 3 leaves a conflicted merge in the tree: do what its stderr says, and note each trade-off under `Decisions I made on my own`. The incoming side is closed tickets whose criteria the closing pass's `reverify` runs again on the base branch, so a resolution that drops their behaviour reopens their ticket hours later, and after a bounce no reviewer sees this merge. Where theirs and yours cannot both hold, the cut missed an edge: keep what landed and run `verify-ticket.py <n> --sub-issue contract <file>` naming both tickets. A clean merge that makes repository checks red uses the `resolving-merge-conflicts` skill too. Exit 2 names the condition that prevented integration; a pipeline failure becomes a `fault` sub-issue, then stop. Never rebase, abort or push from this integration command. Then run every criterion: `verify-ticket.py <n>`. A criterion passes only when its `CHECK` exits 0 and its output matches `EXPECT`. Exit 3: no product slot was free and nothing ran; end your turn, and on the `#<n> worker.queued` wake, ack it and run the same command again. How many rounds a criterion gets is your judgement: keep fixing while a fix is in sight, and when none is, give it the line `ABANDON: AC<n> failed <what each round tried>`, which step 7 puts in the closing-comment draft, and carry on with the rest; the closeout counts no rounds, so that line is the whole record of the trying.

   Done when `verify-ticket.py <n>` has recorded a run of your own after the integration.
2. Post the decisions comment, once: `verify-ticket.py <n> --decisions <file>`. The file is two sections, each opened by its `## ` heading: `## Decisions I made on my own`, with every line written so far, one per line, in the shape the closing comment uses; and `## Outside Owns`, with the `Outside Owns:` line of your newest run (its `ticket.checked` event, run `self`), followed by one sentence per file saying which criterion could not pass without it; `None` when that line is `None`. It is posted here, before the reviewer starts, so the review judges every line of it, and once: the review's fix round adds nothing to it, and the closing comment carries the final version.

   Done when `--decisions` exits 0.
3. Start the reviewer: `dispatch.sh start <n> reviewer`, then end your turn. You are woken with `#<n> reviewer.reported` once its report is on the ticket. Then read the report, the comment on the ticket that carries that event (`dispatch.sh wait <n> reviewer` prints the event with the two commits it read), and `dispatch.sh ack <n> reviewer.reported`. Start exits 2: when its stderr says to start again, run it once more; any other exit 2, or a second one, is a pipeline fault: open the `fault` child as above, then stop. One reviewer per round; after `reviewer.lost`, start another. The in-ticket round is first: fix the in-ticket findings once, under the writing rules that governed the first write, and re-run step 1. An in-ticket finding you do not fix is answered `refuted:`, which says you checked and the bad outcome does not happen at the cited location. Write what disproves this specific claim. A true fact about nearby code that does not disprove the claim does not count. Then, for each out-of-ticket review finding whose body the in-ticket round has not made untrue, run `verify-ticket.py <n> --sub-issue finding <file>`.

   Done when the review comment is on the ticket (a session's state never is), each in-ticket finding is fixed or `refuted:`, and each out-of-ticket finding still true has its `finding` child.
4. Run every criterion one final time: `verify-ticket.py <n> --reverify --actor worker`. It runs after the last step that writes a commit, including the review fix, and includes criteria earlier runs already ticked. If anything still fails, write `ABANDON: AC<n> failed` for each failure and close out `HANDOFF REQUIRED`; this final run gets no fix round.

   Done when the final run is on the ticket at `HEAD`.
5. Audit: read the ticket once more against the branch, the way the user will read your closing comment. Each point under **What to build** holds in the product, not only in a test, and each baseline under **Read first** is followed where it applies. A point that does not hold is said in the closing comment; nothing is committed after the final run.

   Done when you can name, for each point and each baseline, where the branch follows it or the line of the closing comment that says it does not.
6. Tell the tickets whose files you changed: `verify-ticket.py <n> --touched`.

   Done when `--touched` exits 0.
7. Cut loose what only a person can settle, then write the closing-comment draft. A criterion that waits only on one sentence from a person: write `ABANDON: AC<n> decision <question, options, and the default if nobody answers>` **and** run `verify-ticket.py <n> --sub-issue decision <file>`, then keep working the rest; the ticket does not stop. Then `verify-ticket.py <n> --draft`, which prints the path it wrote as `DRAFT: wrote <path>`; give that run no path of your own. Fill every `<fill>`: `skipped:` as `[X], add when [Y]`; each review finding as `fixed <commit>` or `refuted: <what actually happens at path:line>`; each criterion under `Green before work:` with the landed ticket that did that work, or with the fact that this `CHECK` cannot see this ticket's behaviour (then also a `contract` child); `Decisions I made on my own` with every line written so far. Put each `ABANDON:` line under its criterion.

   Done when the closing-comment draft has no `<fill>` left.
8. Close the ticket: `verify-ticket.py <n> --closeout <draft>`. Never close the ticket or swap its labels yourself: a hook blocks the command. Open no pull request: the orchestrator lands the ticket once it is closed, and running `land` from this session would stop it. When the repository's own checks fail and the failing check covers code an incoming ticket of your integration changed, the failure is the merge's: use the `resolving-merge-conflicts` skill.

   Done when `--closeout` exits 0.

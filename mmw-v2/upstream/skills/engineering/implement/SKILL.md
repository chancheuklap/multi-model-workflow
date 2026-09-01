---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
---

Implement the work described by the user in the spec or tickets.

First claim the ticket with the `verify-ticket` skill: its `--preflight` run. It checks the branch, uncommitted tracked changes, the ticket's state, its `ready-for-agent` label, its open blockers, and its assignee, and claims the ticket for you when all six pass. If it prints `NOT_READY`, stop — the reason is already a comment on the ticket, so there is nothing to report twice.

Then check the ticket is coherent: its title and **What to build** describe the same vertical slice; every glob under **Owns** either matches an existing path or is marked `(new)`. An older ticket without **Owns** gets one derived from its **Seam** and the spec sections **Parent** names — post the derived list as a comment on the ticket, then continue.

Then read yourself in: the ticket in full, comments included; then every item under its **Read first**, each through to its conclusion: the last section of a research file, the Decision of an ADR, a handoff package downloaded from Claude Design, a prototype's leaf `README.md` read to its verdict. A baseline in **Read first** is anything there that records a settled conclusion, and it is a contract, not a reference. A handoff package is copied exactly; a prototype is rewritten to production standard, keeping the shape its verdict settled on. Then follow **Parent** to the spec and read only the Implementation Decisions sections the ticket names, plus its Testing Decisions and Out of Scope — not the whole spec. Then the root CONTEXT.md: every term you write comes from it. A ticket without **Read first** is an older one: fall back to every item under the spec's **Sources**.

Then say in one sentence which **seam** this ticket is tested at — copied from the ticket's **Seam**. If the ticket has no **Seam**, derive it from the spec's Testing Decisions and post it as a comment on the ticket before you start, so the ticket is complete for the next reader.

While writing code:

- The baseline is the contract. Copy the values, wording, states and interface shapes of every baseline in **Read first** from it rather than writing them again from memory. When the contract does not fit — a missing state, field, interaction or case, or two baselines conflict — keep going and open a sub-issue under the spec (`gh issue create --parent <spec> --label needs-triage`); never quietly change a baseline, never quietly add around one. A check that will not pass is answered by fixing the code or abandoning the criterion, never by bending the baseline, the harness or the test.
- Put no question on the screen. Take the option the ticket, its baselines and the spec make most likely, write one line for it under **Decisions I made on my own**, and keep going. A question whose answer would change what the ticket delivers gets a sub-issue under the spec (`gh issue create --parent <spec> --label needs-triage`) instead, and the rest of the work carries on.
- Before changing a function, grep every caller and fix the shared code once; before adding a branch or guard to an existing flow, name the branch or file it makes unnecessary and delete it in the same commit.
- Before writing a helper, search the repository and **Read first** for one that already exists.
- Before adding a file, a dependency or a configuration entry, say why the existing one is not enough.
- Never simplify away: security, error handling that prevents data loss, accessibility, or anything the ticket explicitly asks for — **What to build**, every acceptance criterion, the baseline, the interface under **Seam**.
- At the end, write `skipped: [X], add when [Y]`.
- For a file outside **Owns**: change it when a criterion cannot pass otherwise — it lands under `Outside Owns:` in the closing comment; when the change is merely convenient, leave it and open a sub-issue.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Verify your work however you like; scratch scripts and quick checks need not be kept. Commit tests only where the ticket asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files — roughly one focused test per stated behavior — and don't turn scratch checks into additional permanent test files. This is about extras only: implement every behavior the ticket asks for, completely.

Once done, commit your work to the current branch and work through the closing steps below. The tracker is closed by the closeout, never by hand. A ticket that already carries a `self-run`, `VERDICT` or `REVIEW` comment is work you were prompted back into: resume at the step after the newest of them instead of starting the closing steps again.

1. Run every criterion yourself, with the `verify-ticket` skill: its self-run, the run for a worker who has finished writing code. Fix what failed and run it again. A criterion whose `CHECK` is `visual-parity.py` prints one `DIFF` line and nothing that explains it; that skill is where the line is read. One criterion gets at most three rounds: still failing on the third, stop fixing it, write `ABANDON: AC<n> failed <what each round tried>`, and carry on with the rest. This is the only one of the closing steps that repeats, which is why it carries a cap.
2. Dispatch the verifier with the prompt `verify #<n>` and nothing else. Read the `VERDICT` line it comments on the ticket. If it reports failures, fix and rerun step 1; never dispatch the verifier a second time.
3. One round of code review. The `dispatch` skill starts the reviewer on this ticket and then waits for its review comment on the script's own timeout; both commands and the two arguments you supply are there. Done means the review comment is on the ticket, never a session's state. On timeout the script has already left a one-line comment: skip this round and go to step 4 — a dead reviewer is no reason to hand the ticket back. Fix the in-ticket findings once, under the writing rules that governed the first write, and rerun step 1; open a sub-issue for the out-of-ticket ones (`gh issue create --parent <spec> --label needs-triage`). No re-review.
4. Audit: re-read the whole ticket and every item under **Read first**, trace every criterion to its latest `EVIDENCE:`, recount `Counts:`.
5. Cut loose what only a person can settle, then write the closing comment to a draft file. A criterion that waits only on one sentence from a person: write `ABANDON: AC<n> decision <question, options, and the default if nobody answers>` **and** open a sub-issue under the spec (`gh issue create --parent <spec> --label needs-triage`), then keep working the rest — the ticket does not stop. The draft's fixed shape:
   - First line `ALL MET`, or `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>`
   - One line `Branch: … Commit: … PR: …`; with no pull request, `PR: none — <reason>`. This pipeline opens none: write `PR: none — will be merged into <base branch> by dispatch.sh advance`, in the future tense, because at this point the merge has not happened
   - `Post-verdict:` — every commit after the ticket's last `VERDICT` and where it came from, such as "code-review in-ticket finding"; `None` when the verdict sits on HEAD
   - Every criterion's final four lines; an unmet one keeps its text and opens with `ABANDON: AC<n> <kind> <reason>`
   - `Outside Owns:` — copied from what step 1 computed; `None` when empty
   - `skipped: [X], add when [Y]`
   - `Sub-issues opened:` — every sub-issue opened while working this ticket: a baseline that does not fit, a convenient change outside **Owns**, an out-of-ticket review finding, an `ABANDON: decision`
   - `Counts: <k> met, <m> unmet, <n> abandoned of <total>`
   - A closing section `Decisions I made on my own` — one line per thing you settled that neither the ticket nor the spec decides
6. Close the ticket with the `verify-ticket` skill: its closeout, the run for a worker whose closing comment is written to a file. Only when everything passes does it post the comment and close the ticket; a draft opening `HANDOFF REQUIRED` it posts and relabels. When it refuses, fix the draft or the ticket to match its stderr and run it again. Never close the ticket or swap its labels yourself — a hook blocks the command. No pull request, and no push: leave the branch where it is, and `dispatch.sh advance` merges it into `git config branch.issue-<n>.mmw-base-branch` once the ticket is closed. Nothing in this pipeline reads a pull request — code review takes its diff from git, and the verifier reads the ticket and the worktree.
7. Close the Herdr pane the reviewer of step 3 runs in: `herdr pane close "$(herdr pane list | jq -r '.result.panes[] | select(.label == "#<n> reviewer") | .pane_id')"`. Nothing else in this pipeline ends that session, and its review comment is on the ticket, so nothing reads it any more; left alone it holds a pane and a model's context for every ticket the night closes. An empty pane id means step 3 started no reviewer and there is nothing to close.

Three `ABANDON` kinds, and the machine branches on each. `failed`: it ran and did not pass — three rounds in step 1, or still failing after the review fix, or still failing after the verifier reported it; the closeout accepts it only when the ticket carries three `self-run` comments showing that criterion unmet. `stuck`: it will not start, or cannot be done within the task — a `CHECK` that will not run, a missing credential or device, still broken after the verifier repaired its environment; no round count, giving up on the first round is allowed, and the reason names the routes tried or points at the sub-issue that records them. `decision`: both options are legal and neither the ticket nor the spec says — write the question, the options, and the default when nobody answers; a UI difference never goes here. Any `failed` or `stuck` turns the whole ticket into `HANDOFF REQUIRED`; `decision` does not — its sub-issue is already open, and the rest all passing is still `ALL MET`.

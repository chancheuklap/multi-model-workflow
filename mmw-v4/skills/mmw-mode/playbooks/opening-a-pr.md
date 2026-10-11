### Opening a PR

**You own one pull request, from its text to its merge on the owner's yes.**

Run by One ticket step 6 and Run a night step 6, once the change has landed on its branch: `fix-<n>` for one ticket, the night's branch for a night. The pull request opens from that branch on origin as it stands. Its commits are the workers' and the merges `land` recorded, so nothing here rebases or rewrites them. Use GitHub CLI (`gh`) for every operation.

1. **Write it.** The title as **Titles** below says, and the body as **Descriptions** says, written with the **technical-writing** skill, every layer except Diátaxis, then the **unslop** skill. Use one word for each action, keep articles, and avoid `-ing` when a plain verb works. Name every file, section and ticket by its anchor (**principle-anchor-every-reference**). Done when the title is chosen and the body is in a file.
2. **Open it and give the owner its link.** `gh pr create --base <project branch> --head <fix-<n> or the night's branch> --title "<title>" --body-file <file>`. Open it ready, never as a draft: omit `--draft`. Run `gh pr view <number>` before you refer to its state. Done when it is open and the owner has its link.
3. **Before merging, read its checks and comments.** `gh pr checks <number>`; wait for a check still running with `gh pr checks <number> --watch`. Then settle each of these:
   - **A red check.** Tell first whether it is a flake, a project branch that moved on, or this change. A flake fails on a commit where the same check passed before, or passes when run again once: run the failed job again (`gh run rerun <run> --failed`). A project branch that moved on: `git merge-base --is-ancestor origin/<project> origin/<branch>` fails; merge `origin/<project>` into the branch as the **resolving-merge-conflicts** skill says and push it. This change: a fix that needs code, as below.
   - **A review thread or a comment.** Check its claim against the code first, as `../references/bugbot-triage.md` sorts it. One that holds needs a fix, as below; once it is pushed, reply with the commit and resolve the thread. One that does not hold you answer with the specific evidence that disproves it, and resolve the thread. One the reference sends to the owner you put to the owner.

   A fix that needs code is never written here. By day, open a ticket for it as `../references/ticket.md` says, its `## Problem` quoting the check or the comment, but no `fix-<m>` of its own: run One ticket steps 1 to 5 on it from `.worktrees/fix-<n>`, so it lands on `fix-<n>` and this pull request shows it. At night, the closing pass fixes it, as Run a night step 7 says. Done when every check is green and every thread is answered, or the owner has what is left.
4. **Merge on the owner's yes.** By day: first `git worktree remove .worktrees/fix-<n>`, since every commit on it is on origin and a branch still checked out cannot be deleted, then `gh pr merge <number> --merge --delete-branch`, then close each issue the ticket's `## Problem` quotes with a comment linking the pull request; GitHub's `Closes` keyword closes nothing here, since it acts only on a merge into the repository's default branch. At night, `finish` merges it, as Run a night step 7 says. Merge with `--merge`, never a squash: each ticket's commits and the merge `land` recorded stay in the history. Done when it is merged, or the owner has its link and has not said yes.

**Titles.** By day, use Conventional Commits in the form `type(scope): subject`. Use `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf` as the type. Use the changed area, such as `dispatch` or `mmw-mode`, as the scope. Keep the subject short and imperative. Name a real symbol when one carries the change. For example, `fix(dispatch): refuse a finish whose pull request has an open thread`. Do not add a trailing period. A night's pull request is titled `Night #<spec>: <the spec's title>`.

**Descriptions.** The owner reads the top and does not read code; a collaborator reads the bottom with the diff.

The top, in plain words, for the owner:

- What changes for the people who use the product.
- Every decision left to the owner, each with a recommendation.
- What was not done, and why.
- What changes once it is merged.
- By day, each open child of the ticket. At night, the tickets handed back to `needs-triage`, the open `contract` children, and the `ready-for-human` tickets no open blocker holds, each with its ticket, why it stopped and your recommendation.
- When the change has a consequence that cannot be undone (data deleted, an interface others use changed, something already sent out), one line naming it. Leave the line out when there is none.

At night, the middle is the `NIGHT SUMMARY` that `summary` printed, verbatim, under its own heading.

The bottom is a briefing, not the lab notebook. A reviewer who has the diff should learn why the change exists, what it leaves out, what it could break, and how you proved it works, in under a minute. Write short, simple sentences with few identifiers. Do not write walls of text. Keep it under about 40 lines. Put each section under a `##` heading, not a bold lead-in, so the sections stand apart. Use these sections in order. Drop a section when it has nothing to say.

- `## Why` gives the problem and the approach in one to three short sentences. Do not list SHAs or merge genealogy. Do not add a "based on main" preamble.
- `## What changed` has one to three short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget. One small view may stand beside them when it makes the point faster than words: a call tree, a shallow file tree, or a `diff` sketch of either. At night, one line per landed ticket, with the compare link its landing recorded.
- `## Scope` always names what the PR covers and what it deliberately leaves out, for example a related follow-up or a known gap. Use one to three short items. Do not list symbols or paths, and do not write a file-by-file essay.
- `## Tradeoffs` names only rejected alternatives that a reviewer would otherwise ask about. Skip this section when there was no real choice.
- `## Blast Radius` gives one or two sentences on who or what the change touches and why that is safe or risky. If the project branch is red, state the cost of leaving it red.
- `## Verification` has one to three bullets. Each bullet names a real run path and its outcome, before and after: what failed or showed before the change, and what passes or shows now. For a performance change, report one primary number with its unit in `before → after` form. A criterion's run links to the ticket's closing comment. Do not include sample-size methodology or metric tables.

After these sections, attach videos or screenshots when they prove a claim. Do not paste full SHAs, arena lane recitals, file-by-file checklists, or "CLEAN" verdicts. Put these details in a linked artifact.

**Reply:** the pull request's link; each check and thread of step 3, with how it was settled; that the merge waits for the owner's yes, or that it is merged. It goes into the reply of the playbook that ran this one.

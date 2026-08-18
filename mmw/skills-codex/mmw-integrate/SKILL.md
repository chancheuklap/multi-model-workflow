---
name: mmw-integrate
description: Use when you need to resolve an in-progress git merge/rebase conflict. `$mmw:mmw-implement` hands off here when `mmw result integrate` stops, or an unfinished result branch must rebase onto the task branch.
---

The target is the current task branch. Stay in this worktree. Do not merge into the default branch.

A merge started by `mmw result integrate` is already in progress — resolve it; do not run that command again.

Rebase an unfinished result branch in that result worktree. This session stays on the task branch.

Before any write:

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>` with the task-branch name decided above |
| Task branch already there | None of the above holds | Use the current branch |


1. **See the current state** of the merge/rebase. Check git history, and the conflicting files.

2. **Find the primary sources** for each conflict. Understand deeply why each change was made, and what the original intent was. Read the commit messages, check the PRs, check original issues/tickets.

3. **Resolve each hunk.** Preserve both intents where possible. Where incompatible, pick the one matching the merge's stated goal and note the trade-off. Do **not** invent new behaviour. Always resolve; never `--abort`.

4. Discover the project's **automated checks** and run them — typically typecheck, then tests, then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Stage everything and commit. If rebasing, continue the rebase process until all commits are rebased.

If the stated goal cannot decide, stop and ask. Write the trade-off in the merge or rebase commit message. In an MMW repo, start the checks at `TESTING.md` when that file exists.

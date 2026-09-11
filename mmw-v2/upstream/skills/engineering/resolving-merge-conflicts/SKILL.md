---
name: resolving-merge-conflicts
description: Use when an in-progress merge or rebase has conflicts, or when a clean ticket-base merge makes the repository checks fail.
---

1. **See the current state** of the merge/rebase. Check git history and the conflicting files. When the merge completed cleanly and repository checks are red, confirm there are no conflict markers and capture the first failing check instead.

2. **Find the primary sources** for each conflict or failing interaction. Understand deeply why each change was made, and what the original intent was. Read the commit messages and original issues/tickets. For a clean ticket-base merge, identify each ticket represented by the new base merge commits, then read its ticket and closeout evidence before changing the combined behavior.

3. **Resolve each hunk or interaction.** Preserve both intents where possible. Where incompatible, pick the one matching the merge's stated goal and note the trade-off. With no conflict markers, trace the failing path across the merged tickets rather than treating either side in isolation. Do **not** invent new behaviour. Always resolve; never `--abort`.

4. Discover the project's **automated checks** and run them, typically typecheck, then tests, then format. Fix anything the merge broke.

5. **Finish the merge/rebase.** Stage everything and commit. If rebasing, continue the rebase process until all commits are rebased.

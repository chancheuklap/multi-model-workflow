### Opening a PR

Invoked at the end of every other playbook.

Work from a git worktree off trunk, and keep unrelated work out of it. Trunk is the integration branch for a standalone ticket and `project/<slug>` for a multi-PR spec or plan (or the project branch the operator names). Give each delegate its own worktree off the assigned base. Rebase into small, landable commits. Run [deslop](../../deslop/SKILL.md) over the diff before commit and [no-comments](../../no-comments/SKILL.md) before review.

Write the title, PR description and commits with [technical-writing](../../technical-writing/SKILL.md) and [unslop](../../unslop/SKILL.md). Title: `type(scope): subject`, naming a real symbol when one carries the change. The body is a one-minute briefing under 40 lines. Use the project's glossary and these `##` headings in order, dropping empty sections:

- `## Why`: state the problem and approach, and link the execution ticket.
- `## What changed`: use the smallest [PR visual](../references/opening-a-pr/visuals.md) that makes the change clear, or one bullet when it suffices.
- `## Scope`: always name what the change covers and leaves out.
- `## Tradeoffs`: include only rejected alternatives a reviewer would otherwise ask about.
- `## Blast Radius`: open with `**Door:** <one-way or two-way>`, then name who or what the change touches.
- `## Verification`: show the real run and its outcome, before and after. Include the `SUMMARY` line from `scripts/check` for repository checks per the [repo-checks moment rules](../../repo-checks/references/checks.md#moment-rules). For performance, give one primary number with its unit and link the full results. Attach screenshots or video when they prove a claim.

Open one PR for the assigned code ticket. If the ticket already links an open PR for this work, continue on it. Stack follow-ups by base branch. Branch independent work from trunk. Base each dependent PR on its parent's exact tip. As the parent merges, move its child onto trunk per `playbooks/shipping.md` step 4.

Open PRs ready through the run's PR tool with `draft: false`. Use that tool for edits and retargeting when it tracks the run's changes. Resolve the forge once for operations the tool does not cover. Use `origin pr create --status open` when Origin resolves the repository, otherwise `gh pr create` without `--draft` and record the fallback. If the PR opens as a draft, mark it ready and confirm the saved status.

**Links.** Link the work in the PR body. If the PR's base is the repository's default branch, write `Closes #<issue>` in the body for each issue the PR completes. GitHub closes an issue from a closing keyword only when the PR merges into the default branch. Before the merge, record the Result on each of those issues with Update in [to-tickets](../../to-tickets/SKILL.md#update), because the merge closes them. If the PR's base is a project branch or a parent PR's branch, name its ticket as a plain `#<issue>` reference, with no closing keyword. When a stacked PR is retargeted onto the default branch, the same command adds `Closes #<issue>` for its ticket. In the PR that carries the project branch into the default branch, write `Closes #<issue>` for each issue the branch completed. After creating, retargeting or correcting a PR, read back the saved base, head and body. Fix a missing or incorrect link on that PR, preserving its text, and recheck before handoff. Hosts run `scripts/check-pr-links.mjs` independently after the write. The script denies a `gh pr create`, `origin pr create` or `gh pr edit --base` command that targets the default branch when the body has no closing keyword for the ticket its head branch names, `<type>/<issue>-<slug>`. A ticket in another registered repository counts as linked when the body names it as `owner/repo#<issue>`, and its closure is checked after merge.

As soon as the PR opens, a delegate sends its ticket URL and the PR URL to the main chat. The main chat records the PR on that ticket with Update in [to-tickets](../../to-tickets/SKILL.md#update). Opening a PR does not start a babysit. An Autopilot owner's brief assigns its babysit after the code-ready report.

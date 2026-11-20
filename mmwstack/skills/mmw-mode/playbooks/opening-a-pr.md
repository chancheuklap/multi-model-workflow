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

**Links.** Link the work in the PR body and verify the saved metadata before handoff:

- Default-branch PR: write `Closes #<issue>` in the body for each issue the PR completes, and record `Result` on each closed issue with Update in [to-tickets](../../to-tickets/SKILL.md#update) before merge.
- Project-branch or parent-PR-branch PR: name its ticket as a plain `#<issue>` reference without a closing keyword. When retargeting a stacked PR onto the default branch, or opening the PR that merges `project/<slug>` into the default branch, add `Closes #<issue>` for each completed issue.
- Cross-repo tickets and readback: reference a ticket in another registered repository as `owner/repo#<issue>` and verify its closure after merge. After creating, retargeting, or editing a PR, read back the saved base, head, and body and fix any missing or wrong link while preserving the PR text.

As soon as the PR opens, a delegate sends its ticket URL and the PR URL to the main chat. The main chat records the PR on that ticket with Update in [to-tickets](../../to-tickets/SKILL.md#update). Opening a PR does not start a babysit. An Autopilot owner's brief assigns its babysit after the code-ready report.

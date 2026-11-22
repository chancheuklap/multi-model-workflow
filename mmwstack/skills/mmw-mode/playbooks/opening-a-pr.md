### Opening a PR

Invoked at the end of every other playbook.

Work from a git worktree off trunk, and keep unrelated work out of it. Trunk is the integration branch for a standalone ticket and `project/<slug>` for a multi-PR spec or plan (or the project branch the operator names). Give each delegate its own worktree off the assigned base. Rebase into small, landable commits. Run [deslop](../../deslop/SKILL.md) over the diff before commit and [no-comments](../../no-comments/SKILL.md) before review.

Write the title, PR description and commits with [technical-writing](../../technical-writing/SKILL.md) and [unslop](../../unslop/SKILL.md). Title: `type(scope): subject`, naming a real symbol when one carries the change. The body is a one-minute briefing under 40 lines. Use the project's glossary and these `##` headings in order, dropping empty sections:

- `## Why`: state the problem and approach, and link the execution ticket.
- `## What changed`: use the smallest [PR visual](../references/opening-a-pr/visuals.md) that makes the change clear, or one bullet when it suffices.
- `## Scope`: always name what the change covers and leaves out.
- `## Tradeoffs`: include only rejected alternatives a reviewer would otherwise ask about.
- `## Blast Radius`: open with `**Door:** <one-way or two-way>`, then name who or what the change touches.
- `## Verification`: show the real run and its outcome, before and after. Include the `SUMMARY` line from `scripts/check` for repository checks per the [repo-checks moment rules](../../repo-checks/references/checks.md#moment-rules). When `covered code` or guarded state changed, record each `formal check` command, its result, its bounds and assumptions, any `broken variant` check and `intended change to a promise` evidence, and the [statechart](../../statechart/SKILL.md) output for TLA+ models. For performance, give one primary number with its unit and link the full results. Attach screenshots or video when they prove a claim.

Open one PR for the assigned code ticket. If the ticket already links an open PR for this work, continue on it. Stack follow-ups by base branch. Branch independent work from trunk. Base each dependent PR on its parent's exact tip. As the parent merges, move its child onto trunk per `playbooks/shipping.md` step 4.

Open PRs ready through the run's PR tool with `draft: false`. Use that tool for edits and retargeting when it tracks the run's changes. Resolve the forge once for operations the tool does not cover. Use `origin pr create --status open` when Origin resolves the repository, otherwise `gh pr create` without `--draft` and record the fallback. If the PR opens as a draft, mark it ready and confirm the saved status.

**Links.** The PR owner writes the ticket link in the PR body and reads back the saved PR metadata before handoff; the main chat is the single writer for GitHub issue updates and closure:

- Default-branch PR: PR owner writes `Closes #<issue>` (or `Closes owner/repo#<issue>` for another repository) in the body for each issue the PR completes. Main chat records `Result` on each ticket with Update in [to-tickets](../../to-tickets/SKILL.md#update) and verifies closure after merge.
- Project-branch or parent-PR-branch PR: PR owner names its ticket as a plain `#<issue>` (or `owner/repo#<issue>`) reference without a closing keyword. When retargeting a stacked PR onto the default branch per `playbooks/shipping.md` step 4, add `Closes #<issue>` (or `Closes owner/repo#<issue>`) for its still-open ticket. Because GitHub neither shows a Development link nor auto-closes issues on non-default-branch merges, the main chat records `Result` and closes each completed ticket right after its PR merges into `project/<slug>`; the later PR merging `project/<slug>` into the default branch still adds `Closes #<issue>` (or `Closes owner/repo#<issue>`) for each completed ticket so GitHub populates the Development PR link and satisfies default-branch checks.
- Readback: after creating, retargeting, or editing a PR, the PR owner reads back the saved base, head, and body and fixes any missing or wrong link while preserving the PR text.

As soon as the PR opens, the PR owner sends `{ticket URL, PR URL, head SHA}` to the main chat without editing the ticket. The main chat immediately records the PR URL in the ticket body's `Handoff` with Update in [to-tickets](../../to-tickets/SKILL.md#update). Opening a PR does not start a babysit. An Autopilot owner's brief assigns its babysit after the code-ready report.

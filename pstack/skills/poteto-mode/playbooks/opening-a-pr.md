### Opening a PR

Invoked at the end of every other playbook.

**Worktree.** Work from a git worktree off main. Have subagents work from that same base. Give separate delegations on the same branch their own worktrees, or run `git fetch && git reset --hard origin/<branch>` between them in a reused worktree. Dirty branch with unrelated work: patch out, fresh worktree, apply. Snarled worktree: reset from main, redo minimally.

**Commits.** Commit liberally. Rebase into small, ordered commits before opening PRs. Each commit is landable, ordered to tell the story. Amend when the fix belongs in a just-made commit. New commit when separable. Commit bodies don't restate the subject.

**PRs.** Run the [deslop](../../deslop/SKILL.md) skill over the diff before commit and [no-comments](../../no-comments/SKILL.md) before review. Write every PR title, description, and commit body with [technical-writing](../../technical-writing/SKILL.md) (every layer except Diátaxis, and apply the STE vocabulary rules: one word per action, keep articles, a plain verb over `-ing` where one works), then apply [unslop](../../unslop/SKILL.md).

**Titles.** Conventional Commits `type(scope): subject`, no trailing period. Type such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`. Scope is the area, such as `pstack` or `poteto-mode`. Subject is short, imperative, and names a real symbol when one carries the change, for example `fix(pstack): retarget opening-a-pr babysit trigger`.

**Descriptions.** The PR body is a one-minute briefing, not a lab notebook, for a reviewer who has the diff. It says why the change exists, what it leaves out, what it could break, and how you proved it works. Write short, simple sentences with few identifiers, no walls of text. The body becomes the squash commit body, so keep that commit under about 40 lines. Use `##` headings, not bold lead-ins, in this order, and drop a section with nothing to say:

- `## Why`: the problem and approach, 1–3 short sentences. Link the execution ticket this PR delivers. No SHAs, rebase genealogy, or "based on main" preamble.
- `## What changed`: 1–3 short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope`: always. 1–3 short items on what it covers and what it deliberately leaves out (a follow-up, a known gap). No symbols, paths, or file-by-file essay.
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about. Skip when there was no real choice.
- `## Blast Radius`: 1–2 sentences on who or what it touches and why that is safe or risky. If main is red, state the cost of leaving it red.
- `## Verification`: 1–3 bullets, each a real run path and its outcome. Perf: one primary number with its unit, `before → after`, and a link to the arena or swarm directory for the rest. No sample-size methodology, swarm recitals, or metric tables.

After the sections, attach videos or screenshots when they prove a claim. Full SHAs, swarm or arena lane recitals, lever-correction essays, file-by-file checklists, and "CLEAN" verdicts go in a linked artifact, not the body.

**Forge.** Resolve the forge before the first PR operation and keep that choice for create, edit, view, watch, and merge. Prefer Origin when it is available and can resolve the repository. Otherwise use GitHub (`gh`) and record the fallback. Graphite is optional.

**PR tool.** When the run provides a PR tool that tracks its changes, use it to create, edit, retarget, and mark ready. Changes made outside it escape that tracking. Use the selected forge for operations the tool does not cover, or for every operation when no such tool is available.

**Size and stacks.** Open one PR for the assigned code ticket. If that ticket already links an open PR for this work, continue on it. A stack is a base-branch chain. The root PR targets trunk. Each child branch rebases onto its parent's exact tip and its PR targets the parent branch. As a parent merges, move its child onto trunk per `playbooks/shipping.md` step 4. When no run-tracking PR tool is available, create a child with `origin pr create --status open --base <parent-branch>` or `gh pr create --base <parent-branch>`, and retarget one with `origin pr edit <pr> --base <parent-branch>` or `gh pr edit <pr> --base <parent-branch>`. Branch from trunk only for independent work. Rebase on trunk before substantial stack work.

**Readiness.** Open every PR ready, never as a draft. Explicitly select ready for review at creation. With Origin, pass `--status open`. With `gh`, omit `--draft`. If a PR still opens as a draft, mark it ready through the PR tool, or run `origin pr ready <number>` or `gh pr ready <number>` according to the resolved forge. Read the PR back from the forge before reporting its status. As soon as the PR is open, the main chat uses Update in [to-tickets](../../to-tickets/SKILL.md#update) to record the returned PR URL on its execution ticket.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the phase or stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A babysit for each new PR stalls the build and spends checks on commits later waves restart. Push back when feedback drifts from intent.

A subagent that opens a PR runs [deslop](../../deslop/SKILL.md) and [no-comments](../../no-comments/SKILL.md), and gives the main chat the ticket URL and the PR URL as soon as the PR opens. It returns to the parent without babysitting, unless it is an Autopilot-full or Autopilot-stack owner. That owner's brief assigns the babysit loop and is the ask `playbooks/babysit.md` waits for. The owner starts the loop after its code-ready report, reports merge-ready, and is exempt from the rules here and in `playbooks/babysit.md` that hold babysitting until a whole stack is built.

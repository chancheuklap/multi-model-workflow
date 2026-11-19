---
name: retro
description: After the Coordinator creates the delivery pull request, review that delivery and make each repeated agent mistake impossible. Also use when the operator corrects a repeated agent mistake.
---

You are the Coordinator. The delivery pull request for this batch already exists, or the operator has just corrected a repeated agent mistake. Change the repository so the next agent cannot repeat a mistake this work already showed twice.

Call the Skill tool with "writing-for-agents" before you edit an agent instruction or a skill.

## Read the delivery

Read the delivery's commits, review comments, reverts, agent instruction files, and comments that explain workarounds. Read the session that produced the delivery when it is available. When the operator names a correction instead, read that correction. Group the mistakes into classes. A class counts once it has happened twice.

## Look for candidates

Look for candidates in these categories.

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: are there automated checks that could catch errors the agent made? Linting, typing, tests, filesystem linters? Read the repo's own check command first (its commit hook and `scripts/check`, and any `package.json` or build-tool `lint`/`check` scripts), so a check that already exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no pre-commit hook running its lint, typecheck, and the tests `scripts/check` selects) is itself a finding: an un-linted repo is a standing missed opportunity, not a neutral default. _Use when_ the agent made a mistake an automated check could have caught, or the repo has no guardrail at all.
- **Coding standards**: should the **reviewer agent** be given a new rule to enforce? Should an existing rule be removed or clarified? Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check, full stop: a custom rule in the repo's own linter, or a new pre-commit hook, whichever the repo's language and existing guardrail make cheapest. Default to building the check over writing the rule. Reserve `CODING_STANDARDS.md` for genuine **judgement calls** (cross-file consistency, "matches the surrounding style," anything no guardrail could ever substitute for). _Use when_ the reviewer agent failed to catch a mistake.
- **Global AGENTS.md**: are there any steering instructions that should be moved to coding standards (or automated checks) instead? _Use when_ the AGENTS.md file is particularly large - in the repo OR the user's global scope.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is there any custom tooling (CLI's, MCP's) that is particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files that don't modify the agent's behavior. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information. Teeing dev server logs, readonly access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

## Fix each repeated class at the highest level that works

Assume every contributor is an agent that sees only the files it opened, copies the nearest example, and takes the shortest path that compiles. Design the repo so a change that looks right from one file is right for the whole repo.

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state can't be written.** If bad code still compiles, add a lint whose error names the file, type, or function to use instead. A cheap mechanical check joins the repository's commit hook. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** A behavior test joins the tests `scripts/check` selects. Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Write docs or agent rules last, only for judgment calls.** Nothing fails when an agent skips them.

The guardrail stays local. Run the new check on this machine. A GitHub Actions job is not the home for a check this skill adds.

Then fix the most frequent classes now, one commit each, on the branch the delivery pull request already tracks. Prove each new check fails on a real past mistake from this delivery. Exceptions go on the offending line with a reason, an expiry date, and a human's approval.

A candidate that has happened once is reported and left unchanged.

## Keep the rule table

Keep a table in the agent instruction file that pairs each rule with what enforces it. When the operator corrects you, fix the mistake and add the rule. If the rule was already there and nothing enforces it, that's a repeat, so fix it at the highest level in the same change. Drop a rule once its mistake can't happen. When that file's own rules exclude inventories, the commit message and the delivery report carry the pair.

## Report

Present every candidate to the owner, in order of severity, including the ones you fixed. For each class, give its evidence, the level you picked, and why a higher level didn't work. Push the commits to the branch the delivery pull request already tracks. Leave that pull request as the delivery. Opening a second pull request, merging it, or starting another dispatch loop are outside this skill.

## Reference

### Implementation vs Review

Remember that all work goes through two stages: implementation and review. The implementation agent has the most **context pressure**. They are responsible for exploration, writing code, and debugging failures.

The review agent has the least context pressure - it receives a diff, so no exploration needed. It often does not need to write code or debug.

This means that the review agent should be responsible for imposing coding standards, not the implementation agent.

### Files

You have access to several files in the repo:

- `CLAUDE.md`/`AGENTS.md`: these files are pushed to the context window of any agent working in this repo. They should be used incredibly sparingly, usually only for **navigation pointers** to other files.
- `CODING_STANDARDS.md`: this file is read during review, not implementation. Add **navigation pointers** to docs folders if the standards file gets more than 1,000 lines long.
- Docs: use docs as references files, pointed to by other files. Look for existing docs before writing new ones.
- Skills: use skills for docs (since their description goes into the agent's context window), or for user-invoked commands. Follow the advice in the `writing-for-agents` skill.

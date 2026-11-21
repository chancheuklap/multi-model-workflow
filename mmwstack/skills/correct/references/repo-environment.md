# Repo environment

Improve the target repository's code, checks, docs, and tooling so agents stop repeating mistakes and find what they need without friction.

## Gather evidence

- **Named mistake or repository history audit**: read recent commits, reverts, review comments, **agent instruction files**, the repository's **rule table**, and comments that explain workarounds. Group mistakes into **mistake classes**. A **mistake class** counts once it has happened twice. When the operator already named the mistake class to fix, skip the open-ended category scan below and go straight to the enforcement ladder.
- **Session retro or open-ended environment audit**: read the primary sources for the session the operator specifies, which may mean searching session logs on this machine. When no session is named, read the current one. Cross-check repository history when a session mistake looks recurring so a repeated **mistake class** is recognized as one.

## Audit environment categories

For a session retro or open-ended audit, look for **improvement candidates** in these categories:

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: are there automated checks that could catch errors the agent made, such as linting, typing, tests, or filesystem linters? Read the repo's own check command first (its `package.json` or build-tool `lint`/`check` scripts and its CI workflow), so a check that already exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no pre-commit hook and no CI job running its lint, typecheck, and test command) is itself a finding: an un-linted repo is a standing missed opportunity, not a neutral default. _Use when_ the agent made a mistake an automated check could have caught, or the repo has no **guardrail** at all.
- **Coding standards**: should the **review agent** be given a new rule to enforce, or should an existing rule be removed or clarified? Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check, full stop: a custom rule in the repo's own linter, a new pre-commit hook, or a new CI job, whichever the repo's language and existing **guardrail** make cheapest. Default to building the check over writing the rule. Reserve `CODING_STANDARDS.md` for genuine **judgment calls** (cross-file consistency, matching the surrounding style, anything no **guardrail** could ever substitute for). _Use when_ the **review agent** failed to catch a mistake.
- **Global and repo agent instruction files**: are there instructions that should move to `CODING_STANDARDS.md` or automated checks instead? _Use when_ an **agent instruction file** is large, in the repo or in the operator's global scope.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is any custom tooling (CLI or MCP) particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in **agent instruction files** that do not modify the agent's behavior. _Use when_ those files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information, such as teeing dev server logs or read-only access to third-party services. _Use when_ needed information was not available to the agent.

## Fix each class at the highest level of enforcement that works

1. **Eliminate it with architecture.** Give each piece of state one owner and each task one supported way. Hide internals so the wrong import fails. Replace hand-synced lists with one source of truth. Delete old ways and dead code an agent would copy.
2. **Enforce it with types so the bad state cannot be written.** If bad code still compiles, add a lint or CI check whose error names the file, type, or function to use instead. If the pattern is already common, fail only when a change adds more.
3. **Test the behavior.** Fix or delete any test that still passes when the behavior it checks breaks, or that fails when only the internals change.
4. **Write docs or rules last, only for judgment calls.** Nothing fails when an agent skips them. Follow [Where rules live](#where-rules-live) before choosing a file.

## Propose vs fix and prove

- **Propose and wait for approval**: an **improvement candidate** with no repeated **mistake class** behind it (whether seen once in a session or a standing gap such as a missing **guardrail**), and any **improvement candidate** outside this repo (such as global instructions), is reported in severity order and left unchanged until the operator picks it.
- **Fix and prove now**: fix the most frequent confirmed **mistake classes** (two or more occurrences, or an operator-approved **improvement candidate**) now, one commit each. Run [deslop](../../deslop/SKILL.md) on each code diff before committing and write the commit message with [unslop](../../unslop/SKILL.md). Prove each new check fails on a real past mistake. Run the same command locally and in CI. Put any **rule exception** on the offending line with a reason, an expiry date, and a human's approval.

## Keep the rule table

Keep a **rule table** in a dedicated repository standards or rules document (such as `CODING_STANDARDS.md` or `docs/RULES.md`) that pairs each rule with what enforces it, and point to it with one **navigation pointer** in the **agent instruction file** (`AGENTS.md` or `CLAUDE.md`) rather than inlining the table there.

When the operator corrects you, fix the mistake and add the rule. If the rule was already in the **rule table** and nothing enforces it, that is a repeat, so fix it at the highest **level of enforcement** in the same change. Drop a rule once its mistake cannot happen.

## Where rules live

### Implementation vs review

All work goes through two stages: implementation and review. The **implementation agent** carries the most **context pressure** because it explores, writes code, and debugs failures.

The **review agent** carries the least **context pressure** because it receives a diff, needs no exploration, and rarely writes code or debugs.

Therefore the **review agent** enforces coding standards, not the **implementation agent**.

### Files

- **Agent instruction file** (`CLAUDE.md` / `AGENTS.md`): loaded into the context window of every agent working in this repo. Use it sparingly, mainly for **navigation pointers** to other files (including the **rule table**).
- `CODING_STANDARDS.md`: read during review, not implementation. Add **navigation pointers** to docs folders if it grows past 1,000 lines.
- **Docs**: reference files pointed to by other files. Look for existing docs before writing new ones.
- **Skills**: reusable docs (their description enters the agent's context window) or operator-invoked workflows. Route durable skill edits through [Skill evolution](skill-evolution.md) and follow [writing-for-agents](../../writing-for-agents/SKILL.md).

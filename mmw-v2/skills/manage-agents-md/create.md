# Create

The repository has no agent instruction file. You will survey it, ask the maintainer what the repository cannot tell you, then write the root `AGENTS.md`, its `CLAUDE.md`, and a nested pair for every directory that has a rule of its own.

## Before the shared steps

1. Resolve the repository root: `git rev-parse --show-toplevel`. Every path you write from now on is relative to it. If the directory is not a git repository, stop and say so; the incremental branch depends on git history.
2. Confirm the premise: `find . -name AGENTS.md -o -name CLAUDE.md -o -name AGENTS.override.md` (skip `.git`, `node_modules`, `.worktrees`) returns nothing. If it returns anything, switch to [rewrite.md](rewrite.md).
3. Note other tools' instruction files as survey input, not as templates: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md`. The survey reads them for facts; nothing is copied from them by form.

Done when the root is resolved, the premise holds, and the list from step 3 is written down for the survey.

## Shared steps, in order

1. [survey.md](survey.md) — the whole repository, topic groups and directory groups.
2. [ask.md](ask.md) — the fixed questions, with recommended answers drawn from the survey.
3. [write.md](write.md) — decide which directories get a nested file; write root and nested files.
4. [prune.md](prune.md) — cut what must not be there; run the self-check.
5. [verify.md](verify.md) — run the checks; report what was written.

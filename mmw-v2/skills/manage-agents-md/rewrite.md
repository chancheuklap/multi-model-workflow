# Rewrite

The repository already has agent instruction files in some form. You will inventory them, survey the repository, migrate the old content into the one format, confirm with the maintainer what only they know, and write the new files in place of the old.

## Before the shared steps

1. Resolve the repository root: `git rev-parse --show-toplevel`.
2. Inventory every existing file: `find . \( -name .git -o -name node_modules -o -name .worktrees \) -prune -o \( -name AGENTS.md -o -name CLAUDE.md -o -name AGENTS.override.md -o -name CLAUDE.local.md \) -print`. Write the list down with each file's line count. This list is the migration's input and the final report's baseline.
3. Read every file on the list in full. While reading, copy out two things into a scratch note: every command (with the line it came from), and every `@import` line in any `CLAUDE.md`. Commands are kept whole in the rewrite; imports other than `@AGENTS.md` are kept in the root bridge.
4. Note other tools' instruction files as survey input: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md`.

Done when the inventory exists, every file on it has been read, and the scratch note lists every command and every import.

## Shared steps, in order

1. [survey.md](survey.md) — the whole repository; the inventory and the scratch note go to the surveyors as extra input.
2. [migrate.md](migrate.md) — map old content onto the new format; decide per line: keep, move, or drop.
3. [ask.md](ask.md) — the fixed questions. Old identity and convention lines are the recommended answers; the maintainer confirms or corrects each one.
4. [write.md](write.md) — write root and nested files.
5. [prune.md](prune.md) — cut what must not be there; run the self-check.
6. [verify.md](verify.md) — run the checks; report what was removed and why, and what was kept.

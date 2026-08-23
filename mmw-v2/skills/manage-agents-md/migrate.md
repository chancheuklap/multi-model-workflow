# Migrate

Branch: **rewrite**. You have `inventory.md` (the old files, read in full), `inputs.md` (their commands and imports), and `survey-list.md`. Now every old line gets a destination: a section of the new format, the maintainer's questions, or the removal list. No line is lost without a reason written down.

## How to Apply

When given an existing file to improve:

1. **Identify the project identity** — extract what the old files say about what this is. It becomes the recommended answer in [ask.md](ask.md), where the maintainer confirms or replaces it.
2. **Extract the package manager and runtime** — condense to one or two lines.
3. **Extract commands** — keep ALL commands from the original, except a command whose meaning the manifest's scripts or `--help` already give; leave those in `inputs.md`.
4. **Break apart rules** — split any list of rules into individual `<important if>` blocks with specific conditions. You can group rules, but never group unrelated rules under one broad condition.
5. **Wrap domain sections** — testing, API patterns, state management, i18n, etc. each get their own block with a condition describing when that knowledge matters.
6. **Delete linter territory** — remove style guidelines, formatting rules, and anything enforceable by tooling. Suggest replacing with pre-push or pre-commit hooks.
7. **Delete code snippets** — replace with file path references.
8. **Delete vague instructions** — remove anything like "leverage the X agent" or "follow best practices" that isn't concrete and actionable.

Record the outcome as `destinations.md` in the scratch directory: one line per old line, as `<old file>:<line> → <destination>`, where the destination is a section name of the templates in [write.md](write.md), `ask`, or `removed: <reason>`. A line removed as linter territory carries the hook suggestion from step 6 in its reason, so the final report prints it.

Then append every line whose destination is a section to `survey-list.md` as an entry: `fact` is the line, `evidence` is `<old file>:<line>`, `place` is root or the directory the old file sat in, `type` is command, convention, pitfall, or reference by the section, and `when` is the block condition chosen in steps 4 and 5 for a line that goes into an `<important if>` block. The writer reads only the survey list; a kept line that is not in it is not written. Lines whose destination is `ask` stay in `destinations.md`; [ask.md](ask.md) reads them there as recommended answers.

## Keep all commands

Do not drop commands from the original file. The commands table is foundational reference — the agent needs to know what's available even if some commands are used less frequently.

The one exception, from step 3 above: a command whose meaning the manifest's scripts or `--help` already give stays in `inputs.md` rather than the file.

## What happens to each old file on disk

| Old file | Destination |
| --- | --- |
| `AGENTS.override.md` in a directory | Its content becomes that directory's `AGENTS.md`; the override file is deleted |
| Nested `AGENTS.md` whose only content says "read the override" | Replaced by the migrated body |
| Nested `CLAUDE.md` holding `@AGENTS.override.md` | Rewritten to `@AGENTS.md` |
| Root `CLAUDE.md` with several `@` lines | Keeps every import; `@AGENTS.md` is one of them; nothing else in the file |
| A nested pair whose every rule moved to the root or was removed | Both files deleted; the directory goes on the removal list |
| `> ` metadata lines at the top of old files (last-checked commit, domain context, review scope) | Removed; git history is the anchor now |

A nested file survives only on rules the directory group's survey report confirms hold only there.

## Removal list

Keep two lists at the end of `destinations.md` as you go; the final report prints them:

- **What was removed and why** — one line per removed rule or section with its reason: linter territory, discoverable from code, code snippet, duplicate of a document, one-off, vague.
- **What was NOT removed** — every command, and every rule that will stay only if the maintainer confirms it.

Done when, for every file in `inventory.md`, `wc -l` of the old file equals the number of `destinations.md` lines that start with its path, and every line with a section destination is an entry in `survey-list.md`.

Next: [ask.md](ask.md).

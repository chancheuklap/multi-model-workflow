# Rewrite

The repository has agent instruction files in some form, and the user wants them redone. When you are done the old files are gone or rewritten, every command they held that `--help` and the manifest do not explain is still there, and what only the user knows has been confirmed by the user.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel` and work from there. Make a scratch directory outside the repository (`mktemp -d`) and keep its path.
2. Inventory the old files. Run the listing command from [../SKILL.md](../SKILL.md) again, piped through `xargs wc -l`, and save its output, one path per line with the file's line count, as `inventory.md` in the scratch directory. This is the migration's input and the final report's baseline.
3. Read every file in the inventory in full. While reading, fill `inputs.md` in the scratch directory, in the format `SKILL.md` `## The scratch directory` gives: every command with the file and line it came from (commands are kept whole through the rewrite); every `@` line in every `CLAUDE.md` (imports other than `@AGENTS.md` survive in the root `CLAUDE.md`); and the paths of other tools' instruction files, if any: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md`.

Done when `inventory.md` lists every old file, every one of them has been read, and `inputs.md` holds every command and every import.

Run `SKILL.md` `## Survey`, then `## Migrate` below, then `SKILL.md` from `## Ask the user` to the end.

## Migrate

You have `inventory.md` (the old files, read in full), `inputs.md` (their commands and imports), and `survey-list.md`. Now every old line gets a destination: a section of the new format, the user's questions, or the "what was removed" list. No line is lost without a reason written down.

### How to apply

1. **Identify the project identity** — extract what the old files say about what this is. It becomes the recommended answer in `SKILL.md` `## Ask the user`, where the user confirms or replaces it.
2. **Extract the package manager and runtime** — condense to one or two lines.
3. **Extract commands** — every command in the old file passes through the command rule in `SKILL.md` `## Write`.
4. **Break apart rules** — split any list of rules into individual `<important if>` blocks with specific conditions. You can group rules, but never group unrelated rules under one broad condition. A rule every task needs stays bare, as a convention or a gotcha.
5. **Wrap domain sections** — releasing, deploying, translations, etc. each get their own block with a condition describing when that knowledge matters.
6. **Move code and test rules out** — a line that is a code rule gets `CODING_STANDARDS.md` as its destination, a test rule `TESTING.md` (`SKILL.md` `### Code and test rules`); copy it into that file verbatim.
7. **Send the rest to prune** — a line that matches the list in `SKILL.md` `## Prune` gets `removed: <reason>` as its destination now, so the "what was removed" list is complete before writing starts.

Record the outcome as `destinations.md` in the scratch directory: one line per old line, as `<old file>:<line> → <destination>`, where the destination is a section name of the templates in `SKILL.md` `## Write`, `CODING_STANDARDS.md` or `TESTING.md`, `ask` (identity lines only), `removed: <reason>`, or `blank` for an empty line; a heading, a table rule, or a code fence is `removed: markup`.

Then append every line whose destination is a section to `survey-list.md` as an entry: `fact` is the line, `evidence` is `<old file>:<line>`, `place` is root or the directory the old file sat in, `type` is command, convention, gotcha, or reference by the section, and `when` is the block condition chosen in steps 4 and 5 for a line that goes into a domain section. The writer reads only the survey list; a kept line that is not in it is not written. Lines whose destination is `ask` stay in `destinations.md`; `SKILL.md` `## Ask the user` reads them there as recommended answers.

### What happens to each old file on disk

| Old file | Destination |
| --- | --- |
| `AGENTS.override.md` in a directory | Its lines get destinations like any other old file's and reach that directory's `AGENTS.md` through the survey list; the override file is deleted |
| Nested `AGENTS.md` whose only content says "read the override" | Replaced by the migrated body |
| Nested `CLAUDE.md` holding `@AGENTS.override.md` | Rewritten to `@AGENTS.md` |
| Root `CLAUDE.md` with several `@` lines | Keeps every import; `@AGENTS.md` is one of them; nothing else in the file |
| A nested pair whose every rule moved to the root or was removed | Both files deleted; the directory goes on the "what was removed" list |
| `> ` metadata lines at the top of old files (last-checked commit, domain context, review scope) | Removed; git history is the anchor |

A nested file survives only on entries whose place is that directory.

### Two lists for the report

Keep two lists at the end of `destinations.md` as you go; the final report prints them:

- **What was removed and why** — one line per removed rule or section with its reason, in the words of the list in `SKILL.md` `## Prune`; a linter-territory line carries the hook suggestion.
- **What was NOT removed** — every kept command, every rule moved to `CODING_STANDARDS.md` or `TESTING.md`, and every rule that will stay only if the user confirms it.

Done when, for every file in `inventory.md`, `wc -l` of the old file equals the number of `destinations.md` lines that start with its path, and every line with a section destination is an entry in `survey-list.md`.

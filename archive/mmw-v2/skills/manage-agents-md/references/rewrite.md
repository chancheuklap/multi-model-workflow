# Rewrite

The repository has agent instruction files in some form, and the user wants them redone. When you are done the old files are gone or rewritten, every command they held that `--help` and the manifest do not explain is still there, and what only the user knows has been confirmed by the user.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel` and work from there. Make a scratch directory outside the repository (`mktemp -d`) and keep its path.
2. Read every old file `bash scripts/check.sh --list .` lists, in full.

Done when every file `check.sh --list` names has been read.

Run `SKILL.md` `## Survey`, then `## Migrate` below, then `SKILL.md` from `## Ask the user` to the end.

## Migrate

You have read every old file in full, and you have `survey-list.md`. Now every old rule and command gets a destination: a section of the new format, the user's questions, or the "what was removed" list. No line is lost without a reason written down.

### How to apply

1. **Identify the project identity** — extract what the old files say about what this is. It becomes the recommended answer in `SKILL.md` `## Ask the user`, where the user confirms or replaces it.
2. **Extract commands and imports** — every command in the old file passes through the command rule in `SKILL.md` `## Write`; every `@` line in an old `CLAUDE.md` other than `@AGENTS.md` gets `CLAUDE.md` as its destination when it came from the root `CLAUDE.md`, or is dropped when it came from a nested one (only `@AGENTS.md` survives there).
3. **Assign `when` values** — a line that matters to one kind of work only gets a `when` value, chosen as `SKILL.md` `` ### `<important if>` blocks `` says.
4. **Move code and test rules out** — a line that is a code rule gets `CODING_STANDARDS.md` as its destination, a test rule `TESTING.md` (`SKILL.md` `### Code and test rules`); copy it into that file verbatim.
5. **Send the rest to prune** — a line that matches the list in `SKILL.md` `### What NOT to Add` gets `removed: <reason>` as its destination now, so the "what was removed" list is complete before writing starts.

Record the outcome as `destinations.md` in the scratch directory: one line per rule or command, as `<old file>:<line> → <destination>`, where the destination is a section name of the templates in `SKILL.md` `## Write`, `CODING_STANDARDS.md` or `TESTING.md`, `ask` (identity lines only), or `removed: <reason>`.

Then append every line whose destination is a section to `survey-list.md` as an entry: `fact` is the line, `evidence` is `<old file>:<line>`, `place` is root or the directory the old file sat in, `type` is command, convention, gotcha, or reference by the section, and `when` is the value chosen in step 3 for a line that goes into an `<important if>` block. The writer reads only the survey list; a kept line that is not in it is not written. Lines whose destination is `ask` stay in `destinations.md`; `SKILL.md` `## Ask the user` reads them there as recommended answers.

### What happens to each old file on disk

| Old file | Destination |
| --- | --- |
| `AGENTS.override.md` in a directory | Its lines get destinations like any other old file's and reach that directory's `AGENTS.md` through the survey list; the override file is deleted |
| A nested pair whose every rule moved to the root or was removed | Both files deleted; the directory goes on the "what was removed" list |
| `> ` metadata lines at the top of old files (last-checked commit, domain context, review scope) | Removed; git history is the anchor |

### Two lists for the report

Keep two lists at the end of `destinations.md` as you go; the final report prints them:

- **What was removed and why** — one line per removed rule or section with its reason, in the words of the list in `SKILL.md` `### What NOT to Add`; a linter-territory line carries the hook suggestion.
- **What was NOT removed** — every kept command, every rule moved to `CODING_STANDARDS.md` or `TESTING.md`, and every rule that will stay only if the user confirms it.

Done when every rule and every command in each old file has a line in `destinations.md`, and every line with a section destination is an entry in `survey-list.md`.

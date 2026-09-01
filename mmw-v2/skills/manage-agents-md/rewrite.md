# Rewrite

Branch: **rewrite**. The repository has agent instruction files in some form, and the user wants them redone. When you are done the old files are gone or rewritten, every command they held that `--help` and the manifest do not explain is still there, and what only the user knows has been confirmed by the user.

## Set up

1. Resolve the repository root with `git rev-parse --show-toplevel` and work from there. Make a scratch directory outside the repository (`mktemp -d`) and keep its path.
2. Inventory the old files. Run the `find` from [SKILL.md](SKILL.md) again, piped through `xargs wc -l`, and save its output, one path per line with the file's line count, as `inventory.md` in the scratch directory. This is the migration's input and the final report's baseline.
3. Read every file in the inventory in full. While reading, fill `inputs.md` in the scratch directory: every command with the file and line it came from (commands are kept whole through the rewrite); every `@` line in every `CLAUDE.md` (imports other than `@AGENTS.md` survive in the root `CLAUDE.md`); and the paths of other tools' instruction files, if any: `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `GEMINI.md`.

`inputs.md` has three headings, each followed by one line per item or the word `none`:

```markdown
## Other tools' instruction files
<path>

## Commands found in old files
`<command>` — <file>:<line>

## Imports found in old CLAUDE.md files
<@line> — <file>:<line>
```

Done when `inventory.md` lists every old file, every one of them has been read, and `inputs.md` holds every command and every import.

Next: [survey.md](survey.md).

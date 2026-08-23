# Migrate

You have the inventory of old files, read in full, and the survey. Now map the old content onto the format in [write.md](write.md): every old line is kept, moved, or dropped, and you can say which for each.

## How to Apply

When given an existing file to improve:

1. **Identify the project identity** — extract what the old files say about what this is. Leave it bare at the top; it becomes the recommended answer in [ask.md](ask.md), where the maintainer confirms or replaces it.
2. **Extract the package manager and runtime** — condense to one or two lines.
3. **Extract commands** — keep ALL commands from the original, except a command whose meaning the manifest's scripts or `--help` already give. Keep those in the scratch note, not the file.
4. **Break apart rules** — split any list of rules into individual `<important if>` blocks with specific conditions. You can group rules, but never group unrelated rules under one broad condition. A rule that every task needs stays bare under conventions and pitfalls.
5. **Wrap domain sections** — testing, API patterns, state management, i18n, etc. each get their own block with a condition describing when that knowledge matters.
6. **Delete linter territory** — remove style guidelines, formatting rules, and anything enforceable by tooling. Suggest replacing with pre-push or pre-commit hooks.
7. **Delete code snippets** — replace with file path references.
8. **Delete vague instructions** — remove anything like "leverage the X agent" or "follow best practices" that isn't concrete and actionable.

## Old files on disk

| Old file | What happens |
| --- | --- |
| `AGENTS.override.md` in a directory | Its content moves into that directory's `AGENTS.md`; the override file is deleted |
| Nested `AGENTS.md` whose only content is "read the override" | Replaced by the migrated body |
| Nested `CLAUDE.md` with `@AGENTS.override.md` | Rewritten to `@AGENTS.md` |
| Root `CLAUDE.md` with several `@imports` | Keep every import; make sure `@AGENTS.md` is one of them; nothing else in the file |
| A nested file whose every rule moved to the root or was dropped | Both files of the pair deleted; the directory appears in the removal list |
| `> ` metadata lines at the top of old files (last-checked commit, domain context, review scope) | Dropped; git history holds the anchor now |

Each directory group's survey report says what holds only there; a nested file survives only on such rules.

## Removal list

Keep, as you go, the two lists the final report needs:

- What was removed and why — one line per removed rule or section, with the reason from the list in [prune.md](prune.md) (linter territory, discoverable from code, code snippet, duplicate of a document, one-off, vague).
- What was NOT removed — every command, and any rule that stayed only because the maintainer confirmed it in [ask.md](ask.md).

Done when every line of every inventoried file is on exactly one of: the new files, the "what was removed" list, or the scratch note of commands left to the manifest.

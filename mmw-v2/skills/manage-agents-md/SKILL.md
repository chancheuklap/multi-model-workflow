---
name: manage-agents-md
description: Create, rewrite, or incrementally update a repository's AGENTS.md and CLAUDE.md to one fixed format. Use when asked to create AGENTS.md or CLAUDE.md, to rewrite or migrate existing agent instruction files (root, nested, or AGENTS.override.md), or when a scheduled prompt asks for the incremental update of AGENTS.md.
---

# Manage AGENTS.md

You are about to maintain a repository's agent instruction files. There are three situations and one file for each. Find yours below, open that file, and follow it to the end; from then on every file you read ends by naming the next one.

From the repository root, list what exists:

```bash
find . \( -name .git -o -name node_modules -o -name .worktrees -o -name .claude -o -name .codex -o -name .pi -o -name .venv -o -name vendor \) -prune \
  -o \( -name AGENTS.md -o -name CLAUDE.md -o -name AGENTS.override.md \) -print
```

| What you see | Your branch | Open |
| --- | --- | --- |
| Nothing | **create** | [create.md](create.md) |
| Any file, and the user asked you (to rewrite, migrate, redo, or change these files) | **rewrite** | [rewrite.md](rewrite.md) |
| Any file, and the prompt that started you says this is the scheduled incremental update | **incremental** | [incremental.md](incremental.md) |

Nothing found and a scheduled prompt means the create branch has never run: report that and stop.

Remember your branch name; the shared steps ask for it at their end to send you on.

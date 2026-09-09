---
name: manage-agents-md
description: Create, rewrite, or incrementally update a repository's AGENTS.md and CLAUDE.md to one fixed format. Use when asked to create AGENTS.md or CLAUDE.md, to rewrite or migrate existing agent instruction files (root, nested, or AGENTS.override.md), or when a scheduled prompt asks for the incremental update of AGENTS.md.
---

# Manage AGENTS.md

You are about to maintain a repository's agent instruction files. There are three situations, one entry file each — `references/create.md`, `references/rewrite.md`, `references/incremental.md` — and behind them seven shared step files, one per step: `references/ask.md`, `references/survey.md`, `references/write.md`, `references/prune.md`, `references/verify.md`, `references/migrate.md`, `references/additions.md`. Ten files in all. Find your situation below, open its entry file, and follow it to the end; from then on every file you read ends by naming the next one.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location: the path differs by machine and by host, and this skill sits wherever the host that gave it to you reads its skills from.

## Find your situation

From the repository root, list what exists:

```bash
bash <scripts>/check.sh --list .
```

| What you see | Your situation | Open |
| --- | --- | --- |
| Nothing | **create** | [references/create.md](references/create.md) |
| Any file, and the user asked you (to rewrite, migrate, redo, or change these files) | **rewrite** | [references/rewrite.md](references/rewrite.md) |
| Any file, and the prompt that started you says this is the scheduled incremental update | **incremental** | [references/incremental.md](references/incremental.md) |

Nothing found and a scheduled prompt means the repository has not been through the create or rewrite situation: report "run the create situation by hand first", and stop.

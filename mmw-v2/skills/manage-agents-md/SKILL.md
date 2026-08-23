---
name: manage-agents-md
description: Create, rewrite, or incrementally update a repository's AGENTS.md and CLAUDE.md to one fixed format. Use when asked to create AGENTS.md or CLAUDE.md, to rewrite or migrate existing agent instruction files (root, nested, or AGENTS.override.md), or when a scheduled prompt asks for the incremental update of AGENTS.md.
---

# Manage AGENTS.md

This file only routes. Pick the branch, open its file, and follow that file; it names the shared steps in the order they run. Every AGENTS.md this skill produces follows the one format in [write.md](write.md).

| Situation | Branch |
| --- | --- |
| The repository has no `AGENTS.md` and no `CLAUDE.md` anywhere | [create.md](create.md) |
| Any `AGENTS.md`, `CLAUDE.md`, or `AGENTS.override.md` exists and the user asked to rewrite, migrate, or redo them | [rewrite.md](rewrite.md) |
| The prompt says this is the scheduled incremental update | [incremental.md](incremental.md) |

A repository with nested instruction files but no root file is a rewrite, not a create. When the user asked for something else about these files (one addition, one fix), treat it as a rewrite scoped to what they asked.

The branch is chosen when you have run `find` for the three filenames and matched one row. Do not start a branch on a guess.

---
name: design-pages
description: Pull a signed-off Claude Design project into the repository as the handoff package; set up a Claude Design project so its pages carry what acceptance reads; act on comments sent to Claude or draw pages when asked; build a design system from running code when one is wanted. Use when a design must land in the repository, when a Claude Design project is created or its comments are queued, or when a design system is to be built.
---

# design-pages — a Claude Design project is the only source of the design

The user designs in Claude Design, with the agent inside it. This skill covers what happens around that work: the project is set up so its pages carry what the repository reads back, and the signed-off project is pulled into the repository for the screen contract and acceptance.

## Find your door

| You are | Read |
| --- | --- |
| Creating a Claude Design project, acting on comments sent to Claude, drawing pages because the user asked, or taking the user's sign-off | [references/edit-pages.md](references/edit-pages.md) |
| The user has signed the design off, or this session is handling a `contract` child whose body names the pull door | [references/pull.md](references/pull.md): brings the project into the repository as the handoff package. Never while a worker is mid-run |
| Asked to build a design system, or deciding whether one is worth building | [references/design-system.md](references/design-system.md): optional; what it is for, when, and two ways to build it |

Page conventions are the body of [template-project-claude-md.md](references/template-project-claude-md.md), the fenced block that is written into the project root as `CLAUDE.md`.

[edit pages](references/edit-pages.md) and [pull](references/pull.md) each list the MCP tools they need. Confirm each listed tool is callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

## Resolve `<scripts>` once

`<scripts>` in every command in this skill is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Exit codes

| Command | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `<scripts>/check_editable_selectors.py` | `every selector is editor-resolvable (<n> files)` | `<n> selectors the editor cannot reach`, one line each above it | no file given, or one of the CSS files will not open |
| `<scripts>/check_design_system.py` | `design system complete: <n> components, <n> foundation cards, <n> starting points` | one line per miss above `<n> missing` | the directory cannot be read |
| `<scripts>/build_ds_bundle.py` | `bundled <n> components into <file>` | esbuild failed; its error follows | usage error, no component, or no `npx` |
| `<scripts>/pull_design.py` | `pulled <n> files and rendered <n> scenes` | text files need `--reread` | invocation error or the package cannot be completed; the target is unchanged |

[pull](references/pull.md) runs `check_editable_selectors.py` as a module; those findings land in `pull-report.md` under `设计检查`. The CLI row above is what the script still prints when invoked on its own.

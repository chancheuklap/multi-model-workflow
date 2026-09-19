---
name: design-pages
description: Build a design system from running code, edit pages or handle comments in Claude Design, and pull a signed-off project back as the handoff package. Use when the design system has to exist before pages are drawn; when creating, iterating, previewing, or commenting on Claude Design pages; or when a finished design must land in the repository.
---

# design-pages — a Claude Design project is the only source of the design

Three entries, in this order. Each names the next. Read the one this run is going in.

- **[design system](references/design-system.md)** — build the design system from code that already runs, before any page is drawn.
- **[edit pages](references/edit-pages.md)** — create the project, write pages, check the preview, act on comments, and take the user's sign-off.
- **[pull](references/pull.md)** — bring the signed-off project into the repository as the handoff package.

Page conventions live in [template-project-claude-md.md](references/template-project-claude-md.md) and are written into the project root as `CLAUDE.md`. The design-system `readme.md` skeleton is [template-design-system-readme.md](references/template-design-system-readme.md).

[edit pages](references/edit-pages.md) and [pull](references/pull.md) each list the MCP tools they need. Confirm each listed tool is callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

## Resolve `<scripts>` once

`<scripts>` in every command in this skill is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Exit codes

| Command | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `<scripts>/check_editable_selectors.py` | `every selector is editor-resolvable (<n> files)` | `<n> selectors the editor cannot reach`, one line each above it | no file given, or one of the CSS files will not open |
| `<scripts>/pull_design.py` | `pulled <n> files and rendered <n> scenes` | text files need `--reread` | invocation error or the package cannot be completed; the target is unchanged |

[pull](references/pull.md) runs `check_editable_selectors.py` as a module; those findings land in `pull-report.md` under `设计检查`. The CLI row above is what the script still prints when invoked on its own.

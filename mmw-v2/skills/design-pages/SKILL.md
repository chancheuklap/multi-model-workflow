---
name: design-pages
description: Build a design system from running code, edit pages or handle comments in Claude Design, and pull a signed-off project back as the handoff package. Use when the design system has to exist before pages are drawn; when creating, iterating, previewing, or commenting on Claude Design pages; or when a finished design must land in the repository.
---

# design-pages — a Claude Design project is the only source of the design

Three doors, in this order, and each names the next.

## Find your door

| You are | Read |
| --- | --- |
| Starting an interface for a product with no design system yet, or remaking one whose look is changing | [references/design-system.md](references/design-system.md) — built from code that already runs, before any page is drawn. A product whose design system exists and whose shared components have not changed skips this door |
| Creating the project, writing or revising pages, checking a preview, acting on comments, or taking the user's sign-off | [references/edit-pages.md](references/edit-pages.md) |
| The user has signed the design off, or this session is handling a `contract` child whose body names the pull door | [references/pull.md](references/pull.md) — brings the project into the repository as the handoff package. Never while a worker is mid-run |

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

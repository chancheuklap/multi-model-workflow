---
name: design-pages
description: Pull a signed-off Claude Design project into the repository as the handoff package; set up a Claude Design project so its pages carry what acceptance reads; act on comments sent to Claude or draw pages when asked; hand a design system build to the agent inside Claude Design; bring an existing product's screens into Claude Design. Use when a design must land in the repository, when a Claude Design project is created or its comments are queued, when a design system is to be built, or when an existing product is to be designed in Claude Design.
---

# design-pages — a Claude Design project is the only source of the design

The user designs in Claude Design, with the agent inside it. This skill covers what happens around that work: the project is set up so its pages carry what the repository reads back, and the signed-off project is pulled into the repository for the screen contract and acceptance.

## Find your door

| You are | Read |
| --- | --- |
| Creating a Claude Design project, bringing an existing product's screens into Claude Design, acting on comments sent to Claude, drawing pages because the user asked, or taking the user's sign-off | [references/edit-pages.md](references/edit-pages.md) |
| The user has signed the design off, or this session is handling a `contract` child whose body names the pull door | [references/pull.md](references/pull.md): brings the project into the repository as the handoff package. Never while a worker is mid-run |
| Asked to build a design system, or deciding whether one is worth building | [references/design-system.md](references/design-system.md): what it holds, when and from what, and how the agent inside Claude Design builds it |

Page conventions are the body of [template-project-claude-md.md](references/template-project-claude-md.md), the fenced block that is written into the page project's root as `CLAUDE.md`; a design system project's `CLAUDE.md` is the block of [template-design-system-claude-md.md](references/template-design-system-claude-md.md).

Only a session whose host has the Claude Design MCP tools can do this skill's work; a host without them cannot be given them from here, and a dispatched worker never runs this skill. [edit pages](references/edit-pages.md) and [pull](references/pull.md) each list the MCP tools they need. Confirm each listed tool is callable before anything else. If one is missing, stop before writing anything and tell the user three things: this session cannot reach Claude Design, which tool is absent, and that the work has to be picked up again in a session whose host has those tools.

## Resolve `<scripts>` once

`<scripts>` in every command in this skill is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

## Exit codes

| Command | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `<scripts>/check_editable_selectors.py` | `every selector is editor-resolvable (<n> files)` | `<n> selectors the editor cannot reach`, one line each above it | no file given, or one of the CSS files will not open |
| `<scripts>/pull_design.py` | `pulled <n> files and rendered <n> scenes` | not used | invocation error or the package cannot be completed (a named page or a referenced file does not download, a page still holds the preview's injection marker, the offline render keeps requesting new files); the files concerned are printed one per line above the refusal and the target is unchanged |

[pull](references/pull.md) runs `check_editable_selectors.py` as a module; those findings land in `pull-report.md` under `设计检查`. The CLI row above is what the script still prints when invoked on its own.

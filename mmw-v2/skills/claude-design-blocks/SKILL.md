---
name: claude-design-blocks
description: Move an interface between a repository and Claude Design. Porting takes an HTML mockup (static or with JavaScript) or a UI prototype's winning variant into Design Components (.dc.html pages) that are clickable, switch states from the Tweaks panel, and compose into app pages — use whenever the user wants a mockup, prototype, or static screen put into Claude Design, made interactive, or shown in every state, even if they never say .dc.html. Handoff brings a finished project back as the package an implementation is copied from and later compared against — use whenever the user wants a design brought back into the repository or a baseline for story parity.
---

# claude-design-blocks — an interface between a repository and Claude Design

Two directions. Read the one this run is going in; each names the MCP tools it needs and the shape of its own work.

- **[Porting](references/porting.md)** — a mockup or a prototype's winning variant becomes components, app pages and an overview inside a Claude Design project.
- **[Handoff](references/handoff.md)** — a finished project comes down into the consuming repository as the package the implementation is copied from and `story-parity.py` later compares each product story against, through the screen contract's `baselines.look`. After `scenes.json` is written, `<scripts>/export_scene_data.py` fills each scene's `data`.

This skill drives a Claude Design project through MCP tools, and there is no path through either direction without them.

## Resolve `<scripts>` once

`<scripts>` in every command in this skill is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

Two of these scripts are run from a copy instead, under their bare names: `mk.py` and `serve.sh` are copied into the porting working directory, because `deadsweep.py` reads `mk.py` from beside the sources it sweeps and because `serve.sh` is the file the session's `BASE` and `TOK` are filled into. [Porting](references/porting.md) says where each copy goes.

## Exit codes

| Command | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `<scripts>/selector_check.py` | `every selector is editor-resolvable (<n> files)` | `<n> selectors the editor cannot reach`, one line each above it | no file given, or one of the CSS files will not open |
| `<scripts>/export_scene_data.py` | `exported <n>/<n> scenes` | `scenes.json` will not open or is not a list, or a scene will not run | wrong number of arguments, or a scene's props set `standalone` |
| `mk.py`, `<scripts>/mkharness.py`, `<scripts>/deadsweep.py` | it ran | it raised; the Python traceback is on stderr | — |

The three in the last row have no exit code of their own — Python's own is the whole of it.

## Page naming

Every page name carries its page kind as a prefix, so the project's file list tells the reader what each page can do before opening it. The prefix is the page kind's English term from this skill, followed by ` · ` (space, U+00B7, space), followed by the name in the mockup's language:

| Kind | Prefix | What the reader can do |
|---|---|---|
| app page | `App · <name>` | click through every end-to-end path of the mockup |
| component | `Component · <name>` | click every control in one region; switch states in the Tweaks panel; cross-component actions show as toasts |
| overview | `Overview` | pan and zoom over every page at 50% |

The prefix is part of the `NAME` in `src/<name>.py`, the `dc-import` name, and the file name — one string everywhere.

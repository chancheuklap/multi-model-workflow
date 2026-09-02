---
name: claude-design-blocks
description: Move an interface between a repository and Claude Design. Porting takes an HTML mockup (static or with JavaScript) or a UI prototype's winning variant into Design Components (.dc.html pages) that are clickable, switch states from the Tweaks panel, and compose into app pages — use whenever the user wants a mockup, prototype, or static screen "moved to Claude Design", "made clickable", "every state visible", or "uploaded to a project", even if they never say .dc.html. Handoff brings a finished project back as the package an implementation is copied from and later compared against — use whenever the user wants a design "downloaded", a "handoff package", or a baseline for interface parity.
---

# claude-design-blocks — an interface between a repository and Claude Design

Two directions. Read the one this run is going in; each names the MCP tools it needs and the shape of its own work.

- **[Porting](references/porting.md)** — a mockup or a prototype's winning variant becomes components, app pages and an overview inside a Claude Design project.
- **[Handoff](references/handoff.md)** — a finished project comes down into the consuming repository as the package the implementation is copied from and `visual-parity.py --baseline` later renders it against.

This skill drives a Claude Design project through MCP tools, and there is no path through either direction without them.

## Page naming

Every page name carries its page kind as a prefix, so the project's file list tells the reader what each page can do before opening it. The prefix is the page kind's English term from this skill, followed by ` · ` (space, U+00B7, space), followed by the name in the mockup's language:

| Kind | Prefix | What the reader can do |
|---|---|---|
| app page | `App · <name>` | click through every end-to-end path of the mockup |
| component | `Component · <name>` | click every control in one region; switch states in the Tweaks panel; cross-component actions show as toasts |
| overview | `Overview` | pan and zoom over every page at 50% |

The prefix is part of the `NAME` in `src/<name>.py`, the `dc-import` name, and the file name — one string everywhere.

## Worked instance

Chameleon, a complete working directory in the agentflow repository: `docs/prototypes/2026-07-07-douyin-banner-regenerate/claude-design/`; project "Chameleon" `638b3e81-bc4c-4ee4-a1fd-0c2f702103d3`, `DC_FX=CHAMELEON`.

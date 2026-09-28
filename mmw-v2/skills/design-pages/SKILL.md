---
name: design-pages
description: Moves a design between Claude Design and the repository. Use when a signed-off Claude Design project must land in the repository, when a Claude Design project is created or its comments are queued, when a design system is to be built, or when an existing product is to be designed in Claude Design.
---

# design-pages — a Claude Design project is the only source of the design

The user designs in Claude Design, with the agent inside it. This skill covers what happens around that work: the project is set up so its pages carry what the repository reads back, and the signed-off project is pulled into the repository for the screen contract and acceptance.

What this skill pulls is copied exactly by implementation and compared element by element by the story judge, and only a session with the Claude Design tools can correct it: a page that is wrong in the repository becomes a wrong product, or a night ticket stalled on a `contract` child. So hold the pages to the conventions in the project `CLAUDE.md`; how they look is the user's call.

## Find your moment

| You are | Read |
| --- | --- |
| Creating a Claude Design project or taking the user's sign-off | [references/edit-pages.md](references/edit-pages.md) |
| Acting on comments sent to Claude, or drawing pages because the user asked | [references/draw.md](references/draw.md) |
| The user has signed the design off, or this session is handling a `contract` child whose body names the `design-pages` skill's `references/pull.md` | [references/pull.md](references/pull.md): brings the project into the repository as the design package |
| Asked to build a design system, deciding whether one is worth building, or bringing an existing product's screens into Claude Design | [references/design-system.md](references/design-system.md): what it holds, when and from what, and how the agent inside Claude Design builds it |

Only a session whose host has the Claude Design MCP tools can do this skill's work, and a dispatched worker never runs it. In a session without them, tell the user the work needs a session whose host has those tools, and stop before writing anything.

## The state list

The state list names the regions and states to draw: the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names, or of `prototypes/<effort>/README.md`, written for an existing product as [references/design-system.md](references/design-system.md) **An existing product** says.


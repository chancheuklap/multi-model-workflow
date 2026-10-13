---
name: design-pages
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Design pages

Build a product's design system in Claude Design, manage its page project until the owner signs off, and pull the signed-off pages into `design/<product>/`, the design package. These pages are the UI's baseline, so a wrong page becomes a wrong product. Hand back the project link, the design package's commit, and the registered decisions.

## Shared across A, B, and C

**Who can do the work.** Only a session with the Claude Design tools; a dispatched worker never does it. Without those tools, tell the owner to use a session that has them, and stop before writing anything.

**Talking to the Claude Design agent.** That agent sees only its own project, reads the project-root `CLAUDE.md` on every conversation, and reads the repository through Claude Design's GitHub connection from a pushed branch. Put lasting requirements in `CLAUDE.md` and this task's work in a task sheet: `tasks/<n>.md` in the page project, `task.md` in the design system project. Use one checkbox per item, naming the pages, their states, the reference to draw from with its repository path and pushed branch, and what done looks like. The owner says `开始 <n>` or `继续`, without composing instructions. When the owner says the work is done, read the sheet back and ask about unticked items.

**Which ticket is n.** Use the ticket calling this skill: the map's `wayfinder:prototype` ticket, the Feature ticket, the spec being cut by To tickets, or the returned ticket. When the owner calls directly and has no ticket, follow the `mmw-mode` skill's `references/ticket.md` `## Opening a ticket` step 1 to open a ticket with only `## Problem`, containing the owner's words. Open no `fix-<n>`: the design package goes straight to the project branch. C's last step closes this ticket.

**Example data.** Use test accounts and test tenants, never customer data. The data is only for drawing. The database tables and code decide its format, recorded in the spec; every field drawn in the design must have a definition there.

**Writing into a project.** First declare every file this change writes in one `finalize_plan`, for the owner to approve once. Then use `write_files` with the files' etags as `if_match`, or `if_match: "0"` for new files. The reserved path `CLAUDE.md` needs this plan's token. These writes preserve an edit the owner just made in the editor.

## Where to start

Choose the row before any write. Open each reference when you reach its part.

| Situation | Parts | References |
| --- | --- | --- |
| Pages are needed, and the product has no design system | A, then B, then C | [A](references/design-system.md), [B](references/pages.md), [C](references/pull.md) |
| Draw or change pages: a prototype winner, pages missing for Feature or To tickets, or the owner's design request | B, then C | [B](references/pages.md), [C](references/pull.md) |
| The owner signed off, or changed a signed-off design in Claude Design | C | [C](references/pull.md) |
| A ticket returned to the day because its design was wrong or missing, with a `contract` child | B, naming the page and defect in `tasks/<n>.md`, then C | [B](references/pages.md), [C](references/pull.md) |

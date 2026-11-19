# edit pages — set up the project, record sign-off

## Create the project

Skip this when the user already has a project; take its id from the link they give, and check that `CLAUDE.md` holds the block of [template-project-claude-md.md](template-project-claude-md.md).

`create_project`, bound to a design system when the product has one (its UUID from the link the user gives); without one, create it unbound.

Before the user says `开始`, the project holds: `CLAUDE.md` (the template block, unchanged); `state-list.md` when the state list exists; `ui-ids.md` when the product already carries `data-ui` ids, one `## Component · <region>` heading per region and one list item per id, collected by opening the product's story page for each scene of the last design package's `scenes.json` and reading every `[data-ui]` it renders (ids read from `scenes.json` alone miss elements that carry no text); a fresh `_ds/<folder>/` copy when bound to a design system, refreshed as **After the design system changes** below says; and a first `task.md`, written the way **Talking to the agent inside Claude Design** below says: one `Component · ` page per region, the reference to draw against named by its branch and repository path, one region first for the user to look at. Declare all of them in one `finalize_plan`, so the user approves once; `CLAUDE.md` is a reserved path and needs that token.

Give the user the project's link and tell them to say `开始` there.

Done when the user has the link and has been told to say `开始`.

### After the design system changes

Changes are made in Claude Design, by the user or by its agent. A bound page project's `_ds/<folder>/` copy does not follow by itself; refresh it from here before the page project's agent draws again: `list_files` both projects, `delete_files` every file under `_ds/<folder>/` that the design system no longer has, and `copy_files` (with `src_project_id` set to the design system) of `styles.css`, `readme.md` and the variable, part, font and icon directories into `_ds/<folder>/`. Pull again after the copy changes.

## Talking to the agent inside Claude Design

That agent sees only its project, and reads its `CLAUDE.md` on every conversation. Rules that always hold are files there (`CLAUDE.md`, `state-list.md`, `ui-ids.md`); the work to do now is `task.md` at the project root, written by this session: one checkbox item per piece of work, each naming the pages, files or repository paths it needs (a repository path with its branch, pushed before `task.md` is written) and what done looks like. The project's `CLAUDE.md` tells that agent to do `task.md` when the user says to start or continue, and to tick items as it finishes them. So the user never composes instructions: write or replace `task.md` (`finalize_plan` naming it, then `write_files` with its etag, or `if_match: "0"` when new), and tell the user to say `开始` in that project.

A change the user thinks of while looking at a page, they say to that agent directly, or edit in the editor. When the user says the work is done, read `task.md` back: an unticked item is what to ask about.

## Sign-off

After the user says the design is signed off, every design change is made in Claude Design. The design package in the repository is written only by [pull](pull.md), never by Claude Design's "Handoff to Claude Code" export; a local edit is overwritten by the next pull. A design ticket, when there is one, closes as [pull](pull.md) **Design problems in the report** says.

Done when the user has said the design is signed off.

## Next

[pull](pull.md). A pull is two tool calls and one command, and its report is the convention check: when you doubt the pages hold the conventions, pull and read the report rather than reading pages by hand.

# edit pages — set up the project, record sign-off

This file sets the Claude Design project up so its pages carry what the repository reads back, and records sign-off.

## Create the project

Skip this when the user already has a project; take its id from the link they give, and check that `CLAUDE.md` holds the block of [template-project-claude-md.md](template-project-claude-md.md).

1. `create_project`, bound to a design system when the product has one (its UUID from the link the user gives). Without one, create it unbound.
2. `CLAUDE.md` is a reserved path: `finalize_plan` naming in `writes` every path steps 2 to 5 write (`CLAUDE.md`, `task.md`, and `state-list.md` and `ui-ids.md` where steps 3 and 4 apply), the user approves it once, then `write_files` with that token and `if_match: "0"`. The content is the fenced block of [template-project-claude-md.md](template-project-claude-md.md), unchanged and without the fence.
3. When a state list exists (the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names, or of `prototypes/<effort>/README.md` for an existing product as [design-system.md](design-system.md) **An existing product** says), write that section into the project as `state-list.md` in the same approved plan. The template tells the agent inside Claude Design how to read it, and [pull](pull.md) checks the pages against the same file in the repository.
4. When the product already carries `data-ui` ids (it has been through this pipeline before), write every id it renders into the project as `ui-ids.md` in the same approved plan, one `## Component · <region>` heading per region and one list item per id: open the product's story page for each scene of the last design package's `scenes.json` and collect every `[data-ui]` it renders. Ids read from `scenes.json` alone miss elements that carry no text.
5. Write the first `task.md` in the same approved plan, the way **Talking to the agent inside Claude Design** says: one `Component · ` page per region of `state-list.md`, each state a `scene`, drawn from the bound design system; the reference to draw against (a prototype's winning variant, or the product's code and real data), named by its branch and repository path so that agent reads it through Claude Design's GitHub connection; one region first for the user to look at. When the project is bound to a design system, refresh its `_ds/<folder>/` copy first as **After the design system changes** below says.
6. Give the user the project's link and tell them to say `开始` there.

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

[pull](pull.md). Whether the pages kept the conventions is what the pull report and the `write-screen-contract` lint report; nothing checks them before that.

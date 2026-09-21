# edit pages — a project, its pages, comments, and sign-off

Page conventions are the fenced block in [template-project-claude-md.md](template-project-claude-md.md); write that block into the project root as `CLAUDE.md` and follow it here. Confirm the tools below as `SKILL.md` says.

## MCP tools

- `mcp__claude-design__get_claude_design_prompt`
- `mcp__claude-design__create_project`
- `mcp__claude-design__finalize_plan`
- `mcp__claude-design__copy_files`
- `mcp__claude-design__create_support_js`
- `mcp__claude-design__write_files`
- `mcp__claude-design__read_file`
- `mcp__claude-design__list_files`
- `mcp__claude-design__render_preview`
- `mcp__claude-design__list_comments`
- `mcp__claude-design__ack_comments`

Write pages with `write_files`. A file you generate on disk rather than type, such as example data or a bundled script larger than a page, goes up through the design-sync tool's `finalize_plan` and `write_files` by `localPath`, as [design-system.md](design-system.md) uploads the design system's files: its bytes never pass through the model. That tool writes to a page project as well as to a design system (checked 2026-09-21).

Read the Design Components format from `get_claude_design_prompt` (with the design system bound). This skill does not restate `<x-dc>`, helmet, `sc-if` / `sc-for`, `{{ }}`, `data-props`, or `dc-import`.

## Create the project

Five steps, in this order:

1. `get_claude_design_prompt` with the design system's id (the `projectId` [design-system.md](design-system.md) created, or the UUID in the link the user gave), and read the format it returns.
2. `create_project` bound to that design system.
3. `finalize_plan` with `scope: "project"`, then `create_support_js` with that token. Every write below that is not `CLAUDE.md` carries the same token.
4. `copy_files` from the design system into `_ds/`: `styles.css` and every file it reaches (token and component stylesheets, fonts, images) at the same relative path, plus `_ds_bundle.js` and `readme.md`, with `src_project_id` on each entry. A project starts with none of it, and every page loads `./_ds/styles.css` and `./_ds/_ds_bundle.js` from this copy, which is also what pull brings into the repository.
5. `CLAUDE.md` is a reserved path, which a project token does not cover: `finalize_plan` naming `CLAUDE.md` in `writes`, the user approves it, then `write_files` with that token and `if_match: "0"`. The content is the fenced block of [template-project-claude-md.md](template-project-claude-md.md), unchanged and without the fence.

## Write pages

Follow that same `CLAUDE.md`. Start each `Component · ` page from the design system's `@startingPoint` screen for its region, built from design-system components, and compose `App · ` pages from the `Component · ` pages. Compare interaction against the winning variant while its scaffolding is still up: every control of the region (click, drag, scroll, keyboard) behaves as the winner's does.

The state list fixes the names. It is the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names, which on a wayfinder map is the handoff ticket's leaf: each `### <region>` heading there is one `Component · <region>` page, and each list item's leading name is one value of that page's `scene`. Pull's `覆盖` section matches the two, name by name. The agent inside the project cannot see that file, so when the user has it write pages, give it the state list in the conversation.

Every `write_files` call carries `if_match`, so an edit the user just made in the editor is not overwritten.

The user may also talk to Claude Design in the browser and have its agent write the pages.

Done when: the last `write_files` in this run carried `if_match`, and the preview check below has been run on that change.

## Check the preview

After every page change, `render_preview`, open the preview, and look for console errors, resource 404s, and a blank page; screenshot to confirm the change landed. After three rounds that do not fix it, measure the failing element; if that still does not fix it, hand the user what you saw and what you expected. This check is for design time, not for a worker's acceptance loop.

`render_preview` returns `serve_url` and `open_url`. `serve_url` goes only to scripts and browser tools; the user receives `open_url`.

## Comments

The user edits in the editor, or leaves a comment and sends it to Claude. Take queued comments with `list_comments` (`queued_for_claude`), change the pages, then `ack_comments`. When the comment's author is not the user, show it to the user and wait for agreement before changing anything — that is the rule in the `list_comments` description.

## Sign-off

When the user says the design is signed off, that is the moment. A handoff ticket, when there is one, closes to record it.

Do not use Claude Design's "Handoff to Claude Code" export. That path has the in-browser agent rewrite the design as a README; the README does not follow later design changes, and it would be a third account beside the design pages and the screen contract.

After sign-off, every design change is made in Claude Design. The handoff package in the repository is written only by [pull](pull.md). There is no hook that blocks a local edit; the next pull overwrites it and the pull report says so.

## Who follows which file

| Who | What they follow |
| --- | --- |
| The main agent writing pages through MCP | this file and the project `CLAUDE.md` |
| The user talking in the Claude Design browser | the in-browser agent, following that same `CLAUDE.md` |
| The user editing the canvas directly | neither file; whether the conventions landed is what the pull report and the write-screen-contract lint report |

## Next

[pull](pull.md).

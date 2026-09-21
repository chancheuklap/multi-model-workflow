# edit pages — set up the project, act on comments, draw when asked

The design itself is made by the user in Claude Design, with the agent inside it. This entry does four things around that work: it creates the project so its pages carry what the repository reads back, it acts on comments the user sends to Claude, it draws pages when the user asks this session to, and it records sign-off. Confirm the tools below as `SKILL.md` says.

## MCP tools

- `mcp__claude-design__get_claude_design_prompt`
- `mcp__claude-design__read_design_skill`
- `mcp__claude-design__create_project`
- `mcp__claude-design__finalize_plan`
- `mcp__claude-design__create_support_js`
- `mcp__claude-design__write_files`
- `mcp__claude-design__read_file`
- `mcp__claude-design__list_files`
- `mcp__claude-design__render_preview`
- `mcp__claude-design__list_comments`
- `mcp__claude-design__ack_comments`

## Who can do what

| | Reads | Writes |
| --- | --- | --- |
| This session | the repository; any Claude Design project through MCP | any project through MCP; cannot talk to the agent inside Claude Design |
| The agent inside Claude Design | its own project, the bound design system, and the project `CLAUDE.md` on every conversation | its own project, when the user asks in the browser; cannot see this repository |
| The user | everything in the browser | edits, comments, sign-off |

So what the agent inside Claude Design has to know goes into the project as a file, never through the user's clipboard.

## Create the project

Skip this when the user already has a project; take its id from the link they give, and check that `CLAUDE.md` holds the block of [template-project-claude-md.md](template-project-claude-md.md).

1. `create_project`, bound to a design system when the product has one (its UUID from the link the user gives, or from [design-system.md](design-system.md)). Without one, create it unbound.
2. `CLAUDE.md` is a reserved path: `finalize_plan` naming `CLAUDE.md` in `writes`, the user approves it, then `write_files` with that token and `if_match: "0"`. The content is the fenced block of [template-project-claude-md.md](template-project-claude-md.md), unchanged and without the fence.
3. When a state list exists (the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names), write that section into the project as `state-list.md` in the same approved plan. The template tells the agent inside Claude Design how to read it, and [pull](pull.md) checks the pages against the same file in the repository.
4. Tell the user the project is ready and give its link. When the project is bound to a design system, Claude Design copies that design system into the project's `_ds/<folder>/` the first time the user opens the project in the browser; pages load it from there, and that copy is pulled with them. That first copy has the styles and fonts but only a placeholder component bundle, and it never follows later changes; pages that mount components need it refreshed as [design-system.md](design-system.md) **After the design system changes** says.

## Comments

The user leaves a comment and sends it to Claude. Take queued comments with `list_comments` (`queued_for_claude`), change the pages, then `ack_comments`. When the comment's author is not the user, show it to the user and wait for agreement before changing anything; that is the rule in the `list_comments` description. Changing a page follows **When this session draws** below.

## When this session draws

Only when the user asks this session to write or change pages.

1. `get_claude_design_prompt` with the design system's id and the project id, and follow the workflow and the Design Components format it returns. `read_design_skill` `hifi-design` before a polished screen, or `frontend-design` when there is no design system.
2. Follow the project `CLAUDE.md`. When a prototype's winning variant exists, it is the reference for layout and interaction.
3. `finalize_plan` with `scope: "project"` once per session, and `create_support_js` in each directory that will hold `.dc.html` pages if the project lacks it. Every `write_files` carries `if_match`, so an edit the user just made in the editor is not overwritten. A file generated on disk rather than typed, such as example data, goes up through the design-sync tool's `finalize_plan` and `write_files` by `localPath`, whose bytes never pass through the model; it takes no `if_match`, so `list_files` first and upload only while each etag is still the one your last write left.
4. `render_preview` of each changed page and look for console errors, missing files and a blank render. `render_preview` returns `serve_url` and `open_url`: `serve_url` goes only to scripts and browser tools; the user receives `open_url`.

## Sign-off

When the user says the design is signed off, that is the moment. A handoff ticket, when there is one, closes to record it.

Do not use Claude Design's "Handoff to Claude Code" export. That path has the in-browser agent rewrite the design as a README; the README does not follow later design changes, and it would be a third account beside the design pages and the screen contract.

After sign-off, every design change is made in Claude Design. The handoff package in the repository is written only by [pull](pull.md); a local edit is overwritten by the next pull, and the pull report says so.

## Next

[pull](pull.md). Whether the pages kept the conventions is what the pull report and the `write-screen-contract` lint report; nothing checks them before that.

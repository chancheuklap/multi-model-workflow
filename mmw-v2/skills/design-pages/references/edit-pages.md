# edit pages — a project, its pages, comments, and sign-off

Page conventions are [template-project-claude-md.md](template-project-claude-md.md); write that file into the project root as `CLAUDE.md` and follow it here.

## MCP tools

Confirm each of these is callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

- `mcp__claude-design__get_claude_design_prompt`
- `mcp__claude-design__create_project`
- `mcp__claude-design__create_support_js`
- `mcp__claude-design__write_files`
- `mcp__claude-design__read_file`
- `mcp__claude-design__list_files`
- `mcp__claude-design__render_preview`
- `mcp__claude-design__list_comments`
- `mcp__claude-design__ack_comments`

Write with `write_files`. Do not use a tool whose description limits it to `/design-sync`.

Read the Design Components format from `get_claude_design_prompt` (with the design system bound). This skill does not restate `<x-dc>`, helmet, `sc-if` / `sc-for`, `{{ }}`, `data-props`, or `dc-import`.

## Create the project

Four steps, in this order:

1. `get_claude_design_prompt` with the design system, and read the format it returns.
2. `create_project` bound to that design system.
3. `create_support_js`.
4. `write_files`: the contents of [template-project-claude-md.md](template-project-claude-md.md), unchanged, as the project root `CLAUDE.md`.

## Write pages

Follow that same `CLAUDE.md`. Use design-system components for `Component · ` pages and `App · ` pages. List every accepted state on `scene`, reusing the prototype state-list names. Compare interaction against the winning variant while its scaffolding is still up.

Every `write_files` call carries `if_match`, so an edit the user just made in the editor is not overwritten.

The user may also talk to Claude Design in the browser and have its agent write the pages.

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

# edit pages — set up the project, act on comments, draw when asked

The design itself is made by the user in Claude Design, with the agent inside it. This entry does four things around that work: it creates the project so its pages carry what the repository reads back, it acts on comments the user sends to Claude, it draws pages when the user asks this session to, and it records sign-off. Confirm the tools below as `SKILL.md` says.

## MCP tools

- `mcp__claude-design__get_claude_design_prompt`
- `mcp__claude-design__read_design_skill`
- `mcp__claude-design__create_project`
- `mcp__claude-design__finalize_plan`
- `mcp__claude-design__create_support_js`
- `mcp__claude-design__write_files`
- `mcp__claude-design__copy_files`
- `mcp__claude-design__delete_files`
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

## Create the project

Skip this when the user already has a project; take its id from the link they give, and check that `CLAUDE.md` holds the block of [template-project-claude-md.md](template-project-claude-md.md).

1. `create_project`, bound to a design system when the product has one (its UUID from the link the user gives, or from [design-system.md](design-system.md)). Without one, create it unbound.
2. `CLAUDE.md` is a reserved path: `finalize_plan` naming `CLAUDE.md` in `writes`, the user approves it, then `write_files` with that token and `if_match: "0"`. The content is the fenced block of [template-project-claude-md.md](template-project-claude-md.md), unchanged and without the fence.
3. When a state list exists (the `## State list` of the leaf `README.md` the `prototype` skill's `UI.md` step 6 names), write that section into the project as `state-list.md` in the same approved plan. The template tells the agent inside Claude Design how to read it, and [pull](pull.md) checks the pages against the same file in the repository.
4. When the product already carries `data-ui` ids (it has been through this pipeline before), write every id it renders into the project as `ui-ids.md` in the same approved plan, one `## Component · <region>` heading per region and one list item per id: open the product's story page for each scene of the last handoff package's `scenes.json` and collect every `[data-ui]` it renders. Ids read from `scenes.json` alone miss elements that carry no text.
5. Write the first `task.md` in the same approved plan, the way **Talking to the agent inside Claude Design** says: one `Component · ` page per region of `state-list.md`, each state a `scene`, drawn from the bound design system; the reference to draw against (a prototype's winning variant, or the product's code and real data), named by its repository path so that agent reads it through Claude Design's GitHub connection; one region first for the user to look at. When the project is bound to a design system, refresh its `_ds/<folder>/` copy first as [design-system.md](design-system.md) **After the design system changes** says.
6. Give the user the project's link and tell them to say `开始` there.

## An existing product

An existing product's screens are brought into Claude Design once, redrawn with its design system, and from then on they are designed there.

1. **Design system**: built from the production code as [design-system.md](design-system.md) says, unifying what the code does inconsistently.
2. **Project**: **Create the project** above, bound to that design system, with `state-list.md` (one `### <region>` per region, one item per state the product shows) and `ui-ids.md`. The agent inside Claude Design derives each region's data file from the product's real data for those states, which it reads from the repository through Claude Design's GitHub connection; `task.md` names that directory.
3. **Redraw**: `task.md` asks the agent inside Claude Design to draw one `Component · ` page per region from the design system, and an `App · ` page when regions' states are checked together, first one region for the user to look at; see **Talking to the agent inside Claude Design**.
4. **Sign-off and pull**: as for any design. On the first pull the pages differ from the product wherever the design system unified a value; element parity names each of those elements, and the tickets cut from the contract bring the product to the design.

## Talking to the agent inside Claude Design

That agent sees only its project, and reads its `CLAUDE.md` on every conversation. Rules that always hold are files there (`CLAUDE.md`, `state-list.md`, `ui-ids.md`); the work to do now is `task.md` at the project root, written by this session: one checkbox item per piece of work, each naming the pages, files or repository paths it needs and what done looks like. The project's `CLAUDE.md` tells that agent to do `task.md` when the user says to start or continue, and to tick items as it finishes them. So the user never composes instructions: write or replace `task.md` (`finalize_plan` naming it, then `write_files` with its etag, or `if_match: "0"` when new), and tell the user to say `开始` in that project.

A change the user thinks of while looking at a page, they say to that agent directly, or edit in the editor. When the user says the work is done, read `task.md` back: an unticked item is what to ask about.

## Comments

The user leaves a comment and sends it to Claude. Take queued comments with `list_comments` (`queued_for_claude`), change the pages, then `ack_comments`. When the comment's author is not the user, show it to the user and wait for agreement before changing anything. Changing a page follows **When this session draws** below.

## When this session draws

Only when the user asks this session to write or change pages.

1. `get_claude_design_prompt` with the design system's id and the project id, and follow the workflow and the Design Components format it returns. `read_design_skill` `hifi-design` before a polished screen, or `frontend-design` when there is no design system.
2. Follow the project `CLAUDE.md`. When a prototype's winning variant exists, it is the reference for layout and interaction.
3. `finalize_plan` with `scope: "project"` once per session, and `create_support_js` in each directory that will hold `.dc.html` pages if the project lacks it. Every `write_files` carries `if_match`, so an edit the user just made in the editor is not overwritten. A large generated file, such as a product's example data, stays in the repository: the agent inside Claude Design reads it through Claude Design's GitHub connection.
4. `render_preview` of each changed page and look for console errors, missing files and a blank render. `render_preview` returns `serve_url` and `open_url`: `serve_url` goes only to scripts and browser tools; the user receives `open_url`.

## Sign-off

Sign-off is the user saying the design is signed off. A handoff ticket, when there is one, closes to record it.

After sign-off, every design change is made in Claude Design. The handoff package in the repository is written only by [pull](pull.md), never by Claude Design's "Handoff to Claude Code" export; a local edit is overwritten by the next pull, and the pull report says so.

## Next

[pull](pull.md). Whether the pages kept the conventions is what the pull report and the `write-screen-contract` lint report; nothing checks them before that.

# draw — act on comments, draw when asked

## Comments

The user leaves a comment and sends it to Claude. Take queued comments with `list_comments` (`queued_for_claude`), change the pages, then `ack_comments`. When a comment or reply has `author_is_you: false`, show it to the user and wait for agreement before changing anything. Changing a page follows **When this session draws** below.

Done when each queued comment is acted on and acked, or shown to the user because it carries `author_is_you: false`.

## When this session draws

Only when the user asks this session to write or change pages.

1. `get_claude_design_prompt` with the design system's id and the project id, and follow the workflow and the Design Components format it returns. `read_design_skill` `hifi-design` before a polished screen, or `frontend-design` when there is no design system.
2. Follow the project `CLAUDE.md`. When a prototype's winning variant exists, it is the reference for layout and interaction.
3. `finalize_plan` with `scope: "project"` once per session, and `create_support_js` in each directory that will hold `.dc.html` pages if the project lacks it. Every `write_files` carries `if_match`, so an edit the user just made in the editor is not overwritten. A large generated file, such as a product's example data, stays in the repository: the agent inside Claude Design reads it through Claude Design's GitHub connection.
4. `render_preview` of each changed page and look for console errors, missing files and a blank render. `render_preview` returns `serve_url` and `open_url`: `serve_url` goes only to scripts and browser tools; the user receives `open_url`.

Done when each changed page renders with no console error, missing file or blank render.

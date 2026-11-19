# draw — act on comments, draw when asked

## Comments

Queued comments are the user's requests on the pages: take them, handle them as `list_comments` describes, and change pages as below.

Done when each queued comment is acted on and acked, or shown to the user because it carries `author_is_you: false`.

## When this session draws

Only when the user asks this session to write or change pages. The Claude Design tools say how to load the design prompt, plan writes and preview. Beyond them: follow the project `CLAUDE.md`; when a prototype's winning variant exists, it is the reference for layout and interaction; write with `if_match`, so an edit the user just made in the editor is not overwritten; a large generated file, such as a product's example data, stays in the repository for the agent inside Claude Design to read through its GitHub connection.

Done when each changed page renders with no console error, missing file or blank render.

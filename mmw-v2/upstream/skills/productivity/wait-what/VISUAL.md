# Re-pitch it visually

The `visual` branch of [`wait-what`](SKILL.md). Same job as the prose re-pitch — make the thing that did not land land — with one HTML page carrying the explanation.

Explain what was already said. The material is the message the user just stopped you on, not a fresh investigation.

## Put the page where the user is looking

Show the page in the richest surface this session has:

- **You hold a tool that renders HTML for the user** — a visual panel, canvas, artifact, or site surface. Use it. The page appears beside the conversation and the user reads it without leaving.
- **Plain CLI only** — write the file to a temporary location outside the working tree, open it with this machine's file-opening command, and give the user the path in your reply.

## Pick the one view that carries the point

One page, one point. Choose by what did not land:

| What has to land | What goes on the page |
| --- | --- |
| An algorithm, or state logic | Pseudocode |
| A runtime path | A call tree |
| UI structure | A component tree, marking the state and module boundaries that matter |
| File responsibility, or a broad refactor | A shallow file tree, one line of responsibility per entry |
| How parts interact — control flow, data flow, order | A sequence or flow diagram |
| What changes, where the surrounding shape already exists | A diff, its shape matching the topic: component tree, file tree, call tree, or state logic |
| Something mostly new, or where omitted context would hide ownership and order | The whole block |
| A layout, a screen, or two states side by side | The interface itself, drawn |

You may use one of these, you may use several, it is unlikely you will use all of them.

## Build the page to stand alone

- **One file, no network.** Inline every style and script. Draw diagrams as inline SVG, or as HTML and CSS structure. Reach for a diagram library only when your surface renders it natively without fetching anything.
- **Readable in light and dark.** Define the full light palette, then redefine those colors for dark.
- **Real labels, real data.** Use the names from the conversation and from `CONTEXT.md`.
- **Desktop and phone.** Wide blocks scroll inside their own container; the page itself never scrolls sideways.

## Keep it small

Put each visual next to the one or two sentences it supports. Keep only the calls, files, props, states, and boundaries that answer the question the user just asked. Everything else you know about the topic stays off the page.

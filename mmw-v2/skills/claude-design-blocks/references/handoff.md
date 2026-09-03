# Handoff — a Claude Design project into the consuming repository

What this writes is what the implementation is built from and what `visual-parity.py --baseline` later renders it against. It lands in the prototype leaf directory the port started from, beside that port's `src`, `styles` and `data`.

MCP tools: `mcp__claude-design__get_project` confirms the project id, `mcp__claude-design__list_files` and `mcp__claude-design__read_file` read it. Confirm they are callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

## What comes down

`README.md` as Claude Design generates it, every component `.dc.html`, `styles/`, `data/`, and `support.js`. These are what the implementation is held to, so they stay exactly as downloaded.

Beside them, write `scenes.json`: one entry per scene, with `name`, `page` (the `.dc.html` it pins) and `props` (the query parameters that put the real page in that state). The `.dc.html`, `styles/`, `data/`, `support.js` and `scenes.json` are the five things `visual-parity.py --baseline` renders, so every scene can be rendered later without opening the project. The `README.md` is where a spec and its tickets take exact values and verbatim copy from.

## Naming the scenes

A scene name comes from the `scenario` values in each page's `data-props`, under three rules:

- **A name carries no `/`.** `visual-parity.py` serves each scene from a page at `/__parity-<name>.dc.html` that loads `./support.js`; a slash puts that page in a subdirectory that has no `support.js`, and the root never appears.
- **A `scenario` value that more than one page uses becomes `<page>.<scenario>`**, so every name pins one page.
- **The overview page is not a scene.** Canvas mode gives its root `height: auto` inside absolutely positioned frames, so the root has no height and its screenshot is empty. The product has no such page either.

Done when: every scene in `scenes.json` has been rendered once and produced a non-empty root.

## What comes next

The package is one of two baselines. It binds look and verbatim copy; what each control calls, which field feeds each shown value, and what state follows are bound by the **screen contract** that the `align-screens` skill writes from this package and the wayfinder map's decisions, on the map's alignment ticket. How the implementation is put into each scene — a seed of the real backend, a scripted external stub, a registered dev-only capability — is decided there, in the contract's `reach` column, and lands in the consuming repository's spec under `## Testing Decisions`.

Whoever runs `align-screens`, writes that spec and cuts its tickets all open this directory; none of them opens this skill. The `DESIGN.md` uploaded as the design system stays in the consuming repository as well.

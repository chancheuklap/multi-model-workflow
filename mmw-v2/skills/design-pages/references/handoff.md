# Handoff — a Claude Design project into the consuming repository

`<scripts>` below is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**.

What this writes is what the implementation is built from and what `story-parity.py` later compares each product story against. It lands in the prototype leaf directory the port started from, beside that port's `src`, `styles` and `data`.

MCP tools: `mcp__claude-design__list_files` gives the inventory, `mcp__claude-design__render_preview` gives the short-lived file address, and `mcp__claude-design__read_file` supplies a text file only when the pull names it for rereading. Confirm they are callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

## What comes down

Every project file comes down from the inventory except `design_handoff_*/`. The package includes every `.dc.html` page, `styles/`, `data/`, `support.js`, a generated `design-manifest.json`, `scenes.json`, `vendor/`, and `README.md`. Files already beside the package remain in place; a prototype leaf's `README.md` keeps its `## State list` section.

Save the unchanged JSON array from `list_files` with `depth: -1`, set `MMW_DESIGN_PREVIEW_URL` to `render_preview`'s `serve_url`, and run `<scripts>/pull_design.py <manifest.json> <handoff dir>`. The script downloads the files without sending their content through the model, generates every package file named above, and renders every scene with the network blocked. If it exits 1, read only the text paths it names with `read_file`, preserve their project-relative paths under one directory, and rerun with `--reread <dir>`.

`scenes.json` has one entry per scene, with `name`, `page`, `props`, and the rendered `data-ui` values in `data`. The `.dc.html` page is the whole input; nothing under `src/` changes the result. `README.md` records each viewport source, the measured offline render result, the pull time, and the Claude Design project id.

## `vendor/` — the three scripts `support.js` loads

`pull_design.py` reads the `REACT_URL`, `REACT_DOM_URL` and `BABEL_URL` constants from the downloaded `support.js`, downloads exactly those three addresses into `vendor/` under their URL file names, and uses those files for its offline render check.

## Naming the scenes

A scene name comes from the values of each page's `scene` prop in its `data-props`, under three rules:

- **A name carries no `/`.** The driver serves each scene from a page at `/__parity-<name>.dc.html` that loads `./support.js`; a slash puts that page in a subdirectory that has no `support.js`, and the root never appears.
- **Every name is `<page>.<value>`**, where `<page>` is the page's file name without `.dc.html`, so every name pins one page and never changes when another page gains the same value.
- **The overview page is not a scene.** Canvas mode gives its root `height: auto` inside absolutely positioned frames, so the root has no height and its screenshot is empty. The product has no such page either.

Done when: every scene in `scenes.json` has been rendered once and produced a non-empty root, with the network off, and every scene's `data` is non-empty.

## What comes next

The package is one of two baselines. It binds look and verbatim copy; what each control calls, which field feeds each shown value, what state follows, and which block of the product each design page is (`mount`; `route` on `App · ` pages) are bound by the **screen contract** that the `align-screens` skill writes from this package and the wayfinder map's decisions, on the map's alignment ticket. How the implementation is put into each scene: a story reaches its scene through `scenes.json`'s `data`, a journey through the consuming repository's `.mmw/harness/` seeds and stubs; both are written down in the spec's `## Testing Decisions`.

Whoever runs `align-screens`, writes that spec and cuts its tickets all open this directory; none of them opens this skill. The `DESIGN.md` uploaded as the design system stays in the consuming repository as well.

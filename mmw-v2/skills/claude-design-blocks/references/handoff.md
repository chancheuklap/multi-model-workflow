# Handoff — a Claude Design project into the consuming repository

`<scripts>` below is resolved by `SKILL.md`'s section **Resolve `<scripts>` once**.

What this writes is what the implementation is built from and what `story-parity.py` later compares each product story against. It lands in the prototype leaf directory the port started from, beside that port's `src`, `styles` and `data`.

MCP tools: `mcp__claude-design__get_project` confirms the project id, `mcp__claude-design__list_files` and `mcp__claude-design__read_file` read it. Confirm they are callable before anything else. If one is missing, stop and tell the user this session cannot reach Claude Design, and which tool is absent.

## What comes down

Every `.dc.html` page the project has — components and app pages alike, since a scene's data and its render both come from the page — plus `styles/`, `data/`, and `support.js`. These are what the implementation is held to, so they stay exactly as downloaded.

Beside them, write `scenes.json`: one entry per scene, with `name`, `page` (the `.dc.html` it pins) and `props` (the prop set that puts the design page in that state). Then run `python3 <scripts>/export_scene_data.py <package dir>` from the directory the package sits in: for each scene it reads the downloaded page the scene pins — the `data-props` defaults under the scene's own props, the scripts the page loads, and its logic class — and runs that class in Node the way `support.js` runs it in a browser (construct, `componentDidMount`, `renderVals`), writing `{state, vals}` into that scene's `data`. The page is the whole input: a page written inside Claude Design and an app page written by hand export like any other, nothing under `src/` is read, and a source that has drifted from the page it once built cannot change the result. A scene whose props set `standalone` is scaffolding — the script names it and stops. When the package is downloaded again, run the export again. The `.dc.html`, `styles/`, `data/`, `support.js`, `scenes.json` and `vendor/` are what the driver renders, so every scene can be rendered later without opening the project. Whoever runs the handoff writes `README.md`, recording where each exact value, verbatim copy and `viewports` came from; a spec and its tickets take those from it.

## `vendor/` — the three scripts `support.js` loads

`support.js` loads `react@18.3.1`, `react-dom@18.3.1` and `@babel/standalone@7.29.0` from unpkg. Download the three files it names — read the `REACT_URL`, `REACT_DOM_URL` and `BABEL_URL` constants in the `support.js` that came down, versions and all — into `vendor/` under their own file names (`react.production.min.js`, `react-dom.production.min.js`, `babel.min.js`). The driver answers those URLs from `vendor/` first, then from a local cache, then from the network. A project that starts from zero renders the package twice before it has any product (skeleton extraction, target trees), and with a cold cache and no network both would come out empty.

## Naming the scenes

A scene name comes from the values of each page's `scene` prop in its `data-props`, under three rules:

- **A name carries no `/`.** The driver serves each scene from a page at `/__parity-<name>.dc.html` that loads `./support.js`; a slash puts that page in a subdirectory that has no `support.js`, and the root never appears.
- **A `scene` value that more than one page uses becomes `<page>.<value>`**, so every name pins one page.
- **The overview page is not a scene.** Canvas mode gives its root `height: auto` inside absolutely positioned frames, so the root has no height and its screenshot is empty. The product has no such page either.

Done when: every scene in `scenes.json` has been rendered once and produced a non-empty root, with the network off, and every scene's `data` is non-empty.

## What comes next

The package is one of two baselines. It binds look and verbatim copy; what each control calls, which field feeds each shown value, what state follows, and which block of the product each design page is (`mount`; `route` on `App · ` pages) are bound by the **screen contract** that the `align-screens` skill writes from this package and the wayfinder map's decisions, on the map's alignment ticket. How the implementation is put into each scene: a story reaches its scene through `scenes.json`'s `data`, a journey through the consuming repository's `.mmw/harness/` seeds and stubs; both are written down in the spec's `## Testing Decisions`.

Whoever runs `align-screens`, writes that spec and cuts its tickets all open this directory; none of them opens this skill. The `DESIGN.md` uploaded as the design system stays in the consuming repository as well.

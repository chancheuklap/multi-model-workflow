# Target: electron

An application that is already running on the machine, with a local backend of its
own. Contract: `target.kind: electron`. Adapter class: `ElectronAdapter`.

## `discover` prints

```json
{"cdp": "http://127.0.0.1:9222", "impl": "http://127.0.0.1:4173/",
 "backend": "http://127.0.0.1:8000", "title": "Notes"}
```

`cdp` is the renderer's debugging port, `impl` the address the renderer is served at,
`backend` the local backend, `title` (optional) a substring of the window title when
the application has more than one window. Ports are assigned per worktree, so nothing
here is ever written down anywhere else.

## The seven answers

1. **attach** — `connect_over_cdp(cdp)`, then the page whose title holds `title` (the
   first page when none is given). The application is already running, so the state is
   put **after** attach (`reach_before_attach = False`): `seed:signed-out` is fired at an
   application that is already there. Electron exposes one page over its port and
   refuses to open another (`Target.createTarget: Not supported`), so the baseline side
   is rendered on the same page, routed to the baseline server for the render and
   unrouted after — one engine, one set of fonts, one device pixel ratio for both sides.
2. **ready** — `GET <backend>/health` answers under 400, the attached page is not
   closed, and the backend's own configuration surface says the product can be driven
   rather than only that it is alive, and `discover`'s `instance_check` line holds — the product answering is the one this run started, not a neighbour's on the same port. Asked again before every scene and every row.
   `/health` alone passes while every window renders and every control is disabled, so
   `start` reads that configuration surface itself and fails on it, quoting what the
   backend said was missing.
3. **address** — `<impl>/` + the route with its leading `/` stripped: `#/project/{id}`
   becomes `http://127.0.0.1:4173/#/project/p1`. After `goto`, the driver reloads: a
   hash-routed application returns from `networkidle` on a same-document fragment jump
   before the view re-rendered.
4. **release** — the device-metrics override is cleared, the controlled clock resumed,
   reduced motion put back, the CDP session detached, the page sent back to `impl`. This
   runs in `finally`: a run that stops early must not leave the user's window drawing at
   the last viewport with every timer dead.
5. **transport** — the repository's reach script, against the running local backend
   through its write API, and against local storage only where a mechanism declares
   `via: storage`. `dev:` mechanisms make the main process's file and directory dialogs
   return a preset path under automation; they are registered dev-only capabilities
   outside the renderer.
6. **observe** — the backend's JSON read surface: `METHOD /path -> <jq-style
   expression>` (`.field`, `.list[0].field`, `==`, `!=`, `contains`, `exists`). A `node …
   exists` line is refused on this target: it has a JSON surface and must use it. Rows
   whose calls are all `ipc` may leave `observe` empty; the check then only performs the
   trigger.
7. **break the transport** — `transport_off` stops the local backend's persistence (the
   repository decides how: an environment variable read at request time, or pointing
   the backend at an empty database); `transport_on` reverses it. With it off, every
   `observe` must `MISS` on its expression while `GET /health` still answers — a backend
   that stops answering altogether makes the negative run exit 2, which proves nothing.

## What the repository provides

- `start` in `.mmw/target.json`: launches the application's development mode with the
  backing service and data directory it chose, waits for `backend` and `cdp` to answer,
  and returns; it is what makes a run possible on a machine where nobody opened the
  application first.
- Every declared `route` opens and lands on an element carrying `data-screen="<mount>"`;
  the value is unique in one render; a top-level dialog is inside the screenshotted
  subtree, or its scene overrides `mount` to the page root's id.
- The reach script with every mechanism of the table; `dev:` capabilities registered
  in the repository's own port table.
- A static guard: no module reachable from the renderer entry imports fixtures or a
  `dev/` directory; no component takes a scene-like prop; the stylesheets copied from
  the handoff package compare byte for byte (`cmp`).
- The seeded counts follow `data/fixtures.js` (fixed-height panels hide this; state it
  in the reach script anyway).

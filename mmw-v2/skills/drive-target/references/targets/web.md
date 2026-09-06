# Target: web-server-rendered, web-spa

A page on a web server the driver opens in a browser of its own. Two kinds share this
file: `web-server-rendered` (templates rendered by the server, path routes, whole-page
loads, native `<dialog>`; adapter class `WebAdapter`) and `web-spa` (a client-side
application served as a page, with a JSON API behind it; adapter class `WebSpaAdapter`).
They differ in one answer, the read half.

## `discover` prints

```json
{"origin": "http://127.0.0.1:8000", "ready": "/health"}
```

`origin` is where the pages are served; `ready` (optional, default `/health`) is a path
that answers under 400 when the server is up. No session is printed here: a session
belongs to a seeded user, and comes out of the reach script.

## The seven answers

1. **attach** — the state is put **first** (`reach_before_attach = True`): the reach
   script creates the organisation, the user, the rows, and prints `cookie=<name>=<value>`
   for that user's session. Then a browser is launched, a context created with that
   cookie on `origin`'s host, and a page opened. Every scene re-attaches after its own
   transport, so a scene seeded as another user is driven as that user.
2. **ready** — `GET <origin><ready>` answers under 400 and `discover`'s `instance_check` line holds, so the origin answering is this run's. Asked before every scene and row.
3. **address** — `<origin>/` + the route: `/org/members` becomes
   `http://127.0.0.1:8000/org/members`. The driver reloads after `goto` all the same.
4. **release** — the launched browser is closed. There is no window to give back.
5. **transport** — the repository's reach script writes through the server's own write
   surface (form posts, its API) by default; a `via: storage` mechanism writes the
   database directly and names the criterion proving the product reaches that state on
   its own. The seeded **counts** follow `data/fixtures.js`: a members table that grows
   with the organisation is exactly the case the box measurement cannot rescue.
6. **observe** —
   - `web-spa`: the JSON read surface, `METHOD /path -> <jq-style expression>`, as on
     the electron target. A `node …` line is refused.
   - `web-server-rendered`: the server has no JSON read surface (zero `JSONResponse`, zero
     `response_model` was the measured case), so an `observe` line reads a page:
     `GET /org/licenses -> node button "撤销分配" exists`. The read is made in a **second
     tab of the same session**, so the driven page stays where the action left it and
     the read is a fresh document the acting view did not paint; the tree is normalised
     exactly as interface parity normalises it. This is one grade weaker than a field
     comparison: it asserts that the rebuilt view offers a control, not that a value was
     stored, and it is acceptable only under the one-code-path premise — a route that
     renders a preview projection when `db_pool` is absent renders that node with nothing
     written. **A target that has a JSON read surface must use it and not the tree.**
7. **break the transport** — `transport_off` takes the database away from the server
   (an environment variable the request path reads, or a connection string pointing at
   an empty schema) while the server keeps serving; `transport_on` puts it back. Note the
   trap this target sets: if `attach` itself needs the database (a session lookup),
   breaking it makes attach fail and no `observe` is evaluated — the negative run exits 2
   and proves nothing. The command has to break persistence of the observed rows, not
   the session store.

## What the repository provides

- Every template that is a design page's root carries `data-screen="<mount>"`, unique
  in one render; a top-level `<dialog>` is outside the content subtree, so a scene that
  shows one overrides `mount` to the page root's id, or the dialog is rendered inside.
- No request path chooses its projection by `hasattr(app.state, "db_pool")`, by a query
  parameter, or by a build switch. The static guard in the consuming repository matches
  the shapes it knows (`_*_from_preview`, `hasattr(request.app.state, "db_pool")`); a
  different spelling (`if settings.DEMO_MODE`, a `try/except` falling back to fixtures)
  passes it — which is why `--negative` is the first line and the guard the second.
- The contract ticket delivers the template shells behind every declared route, the
  reach script, and one passing minimal test per layer; there is no generated client
  and no OpenAPI document for page routes.
- The stylesheets copied from the handoff package compare byte for byte (`cmp`).
- `viewports` come from the handoff package README; on a responsive page the measured
  width may land in another media query than the design's default, and that is correct.

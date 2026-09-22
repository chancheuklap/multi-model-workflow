# The screen contract file

`docs/specs/<effort>/screen-contract.yaml`. One file per effort, read by `to-spec`, `to-tickets`, `implement`, `code-review`, the story judge, the boundary check and the lint.

The **control axis** is `rows`: one row per user-visible behaviour, keyed by the control's `data-ui` id. `pages` names each design page's story id (`mount`) and the component that owns it; `scenes` names which design page each scene of `scenes.json` belongs to. The control axis and these declarations cannot be derived from each other — a page holds many rows, a row is visible on many scenes — so both are written, and the lint holds them to each other.

A server-rendered product and a desktop product use the same keys. The two labelled examples under **A row** are one of each; neither is a default the other must copy. The listing in **Top level** is the same server-rendered orders desk.

## Top level

```yaml
effort: orders-v1                         # the wayfinder map's title, as in docs/specs/<effort>/
baselines:
  look: prototypes/<task>/claude-design   # the handoff package directory, unchanged
  precedence: "look & verbatim copy -> handoff package; calls, shows, next, on_failure -> this file"
locale: en-US                             # BCP 47 tag; required; the story judge sets both browser contexts; no fallback
viewports: [1280x800]                     # the size pages without their own `viewports` are drawn at
pages:                                    # one per .dc.html page of scenes.json
  "App · 订单台.dc.html":
    mount: orders-app                     # the story page id; the product story is addressed by this value
  "Component · 订单列表.dc.html":
    mount: order-list
    component: features/orders/OrderList  # the rows' component value this page owns (Component pages only)
  "Component · 客户栏.dc.html":
    mount: customer-bar
    component: features/orders/CustomerBar
scenes:                                   # one per entry of scenes.json
  orders-ready:
    page: "Component · 订单列表.dc.html"
  customers-ready:
    page: "Component · 客户栏.dc.html"
  desk-ready:
    page: "App · 订单台.dc.html"
states:                                   # domain state names `next` may use; the lint accepts only this list
  - order-awaiting-payment
backend_without_ui:                       # decisions or operations with no control; one line each
  - "POST /api/orders/expire — runs on a timer, no control"
proposed_operations:                      # operations the rows need and openapi.json lacks yet; each is
  - "POST /api/orders/{order_id}/hold"    # described in the spec's API contract subsection
retired_ids:                              # ids that once had a row; never reused; printed by the lint on every run
  - id: orders.legacy-export
    note: "retired 2026-09-18 — #440 Implementation Decisions 3: export left the product"
rows: [...]
```

The lint checks these top-level keys: `effort`, `baselines`, `locale`, `viewports`, `pages`, `scenes`, `states`, `backend_without_ui`, `proposed_operations`, `retired_ids`, `rows`. A key that is not in this list at the top level is an error that names the key. The same rule holds on a page (only `mount` and `component`), a scene (only `page`), a row (only the Column rules columns, plus `app` on a cross-component row), and a `retired_ids` entry (only `id` and `note`). A Column-rules name written at the top level is an error.

## Pages, scenes, viewports, locale, states, retired_ids

| Key | Rule | Lint |
| --- | --- | --- |
| `viewports` | `WIDTHxHEIGHT` entries: the sizes the pages that declare no `viewports` of their own are rendered and compared at. The handoff package's `README.md` lists each page's `$preview` size under `## Viewport and size source` (`pull_design.py` writes it); a page drawn at a size the others do not share declares it under `pages.<page>.viewports` instead of adding it here. A viewport equal to a media-query breakpoint of the package's stylesheets compares two reflows and verifies nothing. | parseable; no width equals a `@media (max-width\|min-width: Npx)` of any `.css` in the package (including `_ds/`) or a page's `<style>` block; missing is an error |
| `locale` | BCP 47 tag (`zh-CN`, `en-US`) the story judge sets on both browser contexts. The story judge reads it and does not fall back. | present; matches a BCP 47 language tag |
| `states` | The state names this product allows in `next` that are not a scene: domain states, and local view states no scene draws (a zoomed canvas, an expanded container, a closed dialog). Omit the key when `next` never names one. | `next` that is not a row id, a scene name, or `stay` must be a member of this list |
| `pages.<page>.mount` | A short stable id — the story page id the product serves as `?page=<mount>`. Declared by the person writing the contract, never derived from the `component` column (a page holds several components' rows, and the one with most rows can be a borrowed shared control). | present, `[a-z0-9-]`, unique across pages |
| `pages.<page>.viewports` | The sizes this page's scenes are rendered and compared at, when they are not the top-level `viewports`: a page drawn at its own `$preview` size (a 236-wide column, a 52-high bar) is compared there only, not at every size of the other pages. Omit it for a page drawn at a top-level size. | each entry `WIDTHxHEIGHT`, not empty, no width on a stylesheet breakpoint |
| `pages.<page>.component` | For a `Component · ` page: the rows' `component` value this page owns. `App · ` pages are whole-surface roots and carry none. | Component pages ↔ distinct `component` values one to one |
| `scenes.<name>.page` | The `.dc.html` from `scenes.json`. | equals scenes.json; every scene of scenes.json has one entry and nothing else does |
| `scenes.<name>.input` | Only when the design page draws this scene from a data file in the handoff package rather than from literals in the page. A mapping: `file`, the package file the page loads; `value`, the value in it the page reads for this scene (`BOARD_SCENES.morning`); `with`, optional, the fields the page's script sets on top of that value for this scene, merged key by key at every depth (`{select: {node: 138}}` for a scene that reuses a data set with another card selected). The story adapter feeds the product component from that same merged value. Omit it when the page's text is the whole of what the scene shows. | a mapping with `file` and `value`; `with` a mapping; the file exists inside the handoff package |
| `retired_ids[]` | `id` of a row that once existed, and `note` (the date and the verdict). An id is never reused. | printed on every run as `RETIRED <id>: <note>`; a live row must not reuse the id |

`pages` and `scenes` are filled at design time, with no running product: `page` from `scenes.json`, `mount` as a declaration.

`baselines.look` is the handoff package directory. The lint errors when that path is missing. It then reads each page `scenes.json` names: a clickable or editable control without a `data-ui` id is an error that names the page, line and column; a `Component · ` page whose `data-props` has no `scene` prop is an error.

When a `story-parity.py --out` directory sits under the contract directory, the lint reads the newest such inventory (`media/<scene>-<WxH>-impl.png` files) and warns if a page — `App · ` included — has a scene that inventory does not cover. No inventory is silence: the contract has not been compared yet.

## A row

A row is identified by `trigger` plus `precondition`. `trigger` is the control's `data-ui` id, copied from the skeleton as a string. The id format (`<region>.<part>`) is defined by the design-pages skill's `template-project-claude-md.md`; this file copies whatever the skeleton has. Role and accessible name are explanation the skeleton also carries, not the key.

The same control in different states is several rows, split by `precondition`. A disabled state is a row: `calls: [none]`, `next: stay`. A part that repeats in a list is one row; the values that change go in `shows`, not extra rows.

Server-rendered product — a form POST against an HTTP API:

```yaml
- id: orders.confirm                      # <component-short>.<behaviour>; stable once published
  component: features/orders/OrderList    # where the implementation owns it
  trigger: order-list.confirm             # the control's data-ui id from the skeleton
  precondition: { payment: ready }        # what must already be true; {} when nothing
  scenes: [orders-ready]                  # scenes.json names where the control is visible
  calls: ["POST /api/orders/{order_id}/confirm"]
  shows: { status: "status@GET /api/orders/{order_id}" }
  next: order-awaiting-payment            # a row id, a scene name, a name in `states`, or stay
  on_failure: { confirm_4xx: toast:CONFIRM_FAILED }
  source: ["#440 Implementation Decisions 2"]
  gap: aligned                            # aligned | design-only | backend-only
```

Desktop product — a non-HTTP host call. The lint prints `UNVERIFIED` (no machine-readable source) and does not fail the run:

```yaml
- id: notes.save
  component: features/notes/Editor
  trigger: editor.save
  precondition: { dirty: true }
  scenes: [editor-dirty]
  calls: ["host notes.save"]
  shows: { title: "title@host notes.save" }
  next: editor-clean
  on_failure: { save_failed: toast:SAVE_FAILED }
  source: ["conversation 2026-09-18 — save writes the open note through the host"]
  gap: aligned
```

## Column rules

| Column | Rule | Lint |
| --- | --- | --- |
| `id` | `<component-short>.<behaviour>`, lowercase, dots and dashes. Never renumbered, never reused. | unique; every id in `retired_ids` absent from rows |
| `component` | A path or name the implementation owns the control under, inside the repository. It is not the name of a `.dc.html` page in the handoff package — that name is a `pages.<page>` key under **Pages, scenes, viewports, locale, states, retired_ids**. | one `Component · ` page claims it |
| `trigger` | The control's `data-ui` id, a string, copied from the skeleton. | the id exists in the skeleton; every skeleton control that is clickable or editable has ≥1 row |
| `precondition` | Key/value state that selects this row among rows with the same trigger. | rows sharing a trigger have distinct preconditions |
| `scenes` | Names from `scenes.json`. `[]` when the handoff shows no scene for this precondition — allowed, and reported. A control that several pages share is one trigger; its scenes are the union over those pages, and a row that must tell the pages apart puts `screen: <page>` in `precondition`. | each exists in the skeleton for this trigger; `[]` is a warning |
| `calls` | `METHOD /path` exactly as in `openapi.json`; `none`; or a non-HTTP form written as the product issues it. Order is the order of effect. An operation the backend does not have yet is listed under `proposed_operations`; the spec's **API contract** subsection describes it. A server-rendered form post is `POST /path`. | HTTP entries exist in `openapi.json` or in `proposed_operations` (a warning); without an `openapi.json`, reported as `unverified`; a non-HTTP form prints `UNVERIFIED` (no machine-readable source) and does not fail the run |
| `shows` | Displayed name → the binding: `field@METHOD /path`, `field@<non-HTTP call>`, `key@RuntimePolicy`, or several of those; then optionally ` → ` and, in words, what is drawn from them (`tasks[].specs[].tickets[].fold@GET /api/board → count of lamp orange`). No literal numbers or strings in the binding — a status code is a number too. | the binding (before ` → `) contains `@` and no digits outside `{…}` |
| `next` | Where the user is after the call succeeds; for `calls: [none]`, where the user is after the click. `stay` when nothing about the page changes (a disabled control, a cancelled dialog). | a row id, a scene name, a name in `states`, or `stay` |
| `on_failure` | Failure kind → the outcome, then optionally ` — ` and what the user sees there in words. The outcome is where the user is after that failure, in the words `next` uses (a row id, a scene, a name in `states`, `stay`), or `toast:<KEY>` for a message over an unchanged page: `version_conflict_409: Component · 本机配置.changed — the banner names the time the file changed`. Every non-`none` call has at least one. The four-column boundary test of the ui-acceptance skill reads this column. | present when `calls` is not `[none]`; a mapping; each outcome is one of those |
| `source` | Where the behaviour was decided, in one of these shapes: `#<n>` (a decision ticket), `#<n> Implementation Decisions <k>` or `#<n> Testing Decisions` (a spec section), `ADR-<nnnn>`, `docs/<path> …` (a domain document), `README §…`, `conversation <YYYY-MM-DD>` plus one sentence of the conclusion, or `code:<path>` as a last resort. A user story (`#<n> story <k>`) is an audit trail no worker ever reads: `to-spec` folds a story's conclusion into the Implementation Decisions subsection that implements it, and the row cites that. At least one source that is neither README nor `code:`, or `gap` is not `aligned`. | non-empty; a story or an unrecognised shape is a warning |
| `gap` | `aligned` when design and backend agree; `design-only` when the control has no backend behaviour to call; `backend-only` when a decision has no control. | `to-spec` refuses a file with any non-`aligned` row |
| `app` | Only on a cross-component row: the `App · ` page the row is written on. See **A cross-component row**. | the value is a declared `App · ` page |

A design page with no row is an error. Reverse sweep: every operation in `openapi.json` appears in some row's `calls`, in `backend_without_ui`, or in `proposed_operations`; one that does not is an error naming the method and path.

## A cross-component row

A **cross-component row** records that region A's action affects region B. It is written on an `App · ` page, one row per control whose action the page's `dc-import` wiring carries from one region to another: a callback that several controls fire is one row for each of them. A control whose action also changes its own region keeps its row on its `Component · ` page as well. When no scene of the `App · ` page draws the control, the row's `scenes` is `[]` and the lint warns.

Every declared `App · ` page carries at least one such row: the lint covers an App page only through its own `app:` rows and otherwise reports `page has no rows`. An App page whose wiring passes nothing between regions goes to the person in the gap list, not into an invented row.

The row carries `app: "<App · page name>"`. `trigger` is region A's `data-ui` id. `calls` is the OpenAPI operation (`METHOD /path` with no query string); name the other region's state the request must carry beside it, not spliced into the path. `next` is the scene region B enters.

A **region** (`区域`) is the substring of a `data-ui` id before the first `.`. The lint takes the skeleton pages that id prefix appears on, drops the row's own `App · ` page (an App page composes the Component pages, so it repeats their ids), and requires the remaining owner to be unique. `next` must name a scene whose `page` is not that owner — the other region, not the one that owns the trigger.

```yaml
- id: desk.filter-customer
  component: features/orders/CustomerBar
  app: "App · 订单台.dc.html"
  trigger: customer-bar.pick
  precondition: {}
  scenes: [desk-ready]
  calls: ["GET /api/orders"]              # carries customer-bar's selected customer
  shows: { count: "count@GET /api/orders" }
  next: orders-ready                      # the order-list region's scene, not customer-bar's
  on_failure: { list_4xx: toast:LIST_FAILED }
  source: ["#440 Implementation Decisions 4"]
  gap: aligned
```

## What the downstream skills take from it

- `to-spec`: `calls` and `shows` → the **API contract** subsection; every `app:` row → the **`App · ` 页组合** subsection, which names the request fields and the other region's state per row id; `baselines` → Sources; the **visual acceptance** paragraph cites `pages` and the story judge instead of restating any command. Testing Decisions' **Test surfaces** are the **product answers** of the ui-acceptance skill's `references/product-answers.md`; that skill's `target_config.py --check` is the count.
- `to-tickets`: the five kinds of ticket a contract produces are in that skill's `references/cutting-interface-tickets.md`. A component page ticket owns by design page: one story criterion, and one boundary criterion per row whose `calls` is not `[none]` or whose `next` is not `stay` (several rows may share one test file); an app page ticket owns an `App · ` page and gets one boundary criterion per `app:` row. **Read first** lists `scenes.json`, this file's path with the row ids the ticket owns, and every baseline-class `source` of those rows, deduplicated by document. Journeys are written on the contract ticket, on tickets the owner named, and on each acceptance ticket, whose criterion carries `--break`.
- `implement`: `precedence` is the rule for a conflict between the handoff package and this file; the worker writes the product component together with its story adapter and its boundary tests; the values the worker writes toward are the ones the story judge renders from the handoff package.
- `code-review` Spec axis: reviews the diff row by row for the ids the ticket cites, and checks that the component draws every `shows` value of a cited row from its binding. Tests axis: reads the boundary tests' and journeys' own assertions, on top of what `boundary-check.py` decides. UI axis (pilot): on a ticket with a story criterion, reads the committed screenshots and the pixel difference images for what element parity cannot see.
- `verify-ticket --lint`: the flags of the pipeline scripts.

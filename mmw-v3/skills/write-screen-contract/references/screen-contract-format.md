# The screen contract file

`docs/specs/<effort>/screen-contract.yaml`. One file per effort, read by Write a spec, Cut tickets, Work a ticket, Review a ticket, the story oracle, the boundary check and the lint.

`rows` is one row per user-visible behaviour, keyed by the control's `data-ui` id. `pages` names each design page's story id (`mount`) and the component that owns it; `scenes` names which design page each scene of `scenes.json` belongs to. `rows` and these declarations cannot be derived from each other — a page holds many rows, a row is visible on many scenes — so both are written, and the lint holds them to each other.

A server-rendered product and a desktop product use the same keys. The two labelled examples under **A row** are one of each; neither is a default the other must copy. The listing in **Top level** is the same server-rendered notes app.

## Top level

```yaml
effort: notes-v1                          # the effort's directory name, as in docs/specs/<effort>/
baselines:
  look: prototypes/<effort>/claude-design   # the design package directory, unchanged
  precedence: "look & verbatim copy -> design package; calls, shows, next, on_failure -> this file"
locale: en-US                             # BCP 47 tag; required; the story oracle sets both browser contexts; no fallback
viewports: [1280x800]                     # the size pages without their own `viewports` are drawn at
pages:                                    # one per .dc.html page of scenes.json
  "App · notes.dc.html":
    mount: notes-app                      # the story page id; the product story is addressed by this value
  "Component · note-list.dc.html":
    mount: note-list
    component: features/notes/NoteList    # the rows' component value this page owns (Component pages only)
  "Component · tag-bar.dc.html":
    mount: tag-bar
    component: features/notes/TagBar
scenes:                                   # one per entry of scenes.json
  notes-ready:
    page: "Component · note-list.dc.html"
  tags-ready:
    page: "Component · tag-bar.dc.html"
  notes-app-ready:
    page: "App · notes.dc.html"
states:                                   # domain state names `next` may use; the lint accepts only this list
  - note-archived
backend_without_ui:                       # decisions or operations with no control; one line each
  - "POST /api/notes/purge — runs on a timer, no control"
proposed_operations:                      # operations the rows need and openapi.json lacks yet; each is
  - "POST /api/notes/{note_id}/pin"       # described in the spec's API contract subsection
retired_ids:                              # ids that once had a row; never reused; printed by the lint on every run
  - id: notes.legacy-export
    note: "retired 2026-09-18 — #12 Implementation Decisions 3: export left the product"
rows: [...]
```

## Pages, scenes, viewports, locale, states, retired_ids

| Key | Rule |
| --- | --- |
| `viewports` | `WIDTHxHEIGHT` entries: the sizes the pages that declare no `viewports` of their own are rendered and compared at. A viewport equal to a media-query breakpoint of the package's stylesheets — any `.css` in the package (including `_ds/`), or a page's `<style>` block — compares two reflows and verifies nothing. |
| `locale` | BCP 47 tag (`zh-CN`, `en-US`) the story oracle sets on both browser contexts. The story oracle reads it and does not fall back. |
| `states` | The state names this product allows in `next` that are not a scene: domain states, and local view states no scene draws (a zoomed canvas, an expanded container, a closed dialog). Omit the key when `next` never names one. |
| `pages.<page>.mount` | A short stable id — the story page id the product serves as `?page=<mount>`. |
| `pages.<page>.viewports` | The sizes this page's scenes are rendered and compared at, when they are not the top-level `viewports`: a page drawn at its own `$preview` size (a 236-wide column, a 52-high bar) is compared there only, not at every size of the other pages. Omit it for a page drawn at a top-level size. |
| `pages.<page>.component` | For a `Component · ` page: the rows' `component` value this page owns. `App · ` pages are whole-surface roots and carry none. |
| `scenes.<name>.page` | The `.dc.html` from `scenes.json`. |
| `scenes.<name>.input` | Only when the design page draws this scene from a data file in the design package rather than from literals in the page. A mapping: `file`, the package file the page loads; `value`, the value in it the page reads for this scene (`NOTE_SCENES.ready`); `with`, optional, the fields the page's script sets on top of that value for this scene, merged key by key at every depth (`{selected: {note: 2}}` for a scene that reuses a data set with another note selected). The story adapter feeds the product component from that same merged value. Omit it when the page's text is the whole of what the scene shows. |
| `retired_ids[]` | `id` of a row that once existed, and `note` (the date and the verdict). An id is never reused. |

## A row

A row is identified by `trigger` plus `precondition`. `trigger` is the control's `data-ui` id, copied from the skeleton as a string. The id format (`<region>.<element>`) is defined by the design-pages skill's `template-project-claude-md.md`; this file copies whatever the skeleton has. Role and accessible name are explanation the skeleton also carries, not the key.

The same control in different states is several rows, split by `precondition`. An element that repeats in a list is one row; the values that change go in `shows`, not extra rows.

Server-rendered product — a form POST against an HTTP API:

```yaml
- id: notes.archive                       # <component-short>.<behaviour>; stable once published
  component: features/notes/NoteList      # where the implementation owns it
  trigger: note-list.archive              # the control's data-ui id from the skeleton
  precondition: { selected: true }        # what must already be true; {} when nothing
  scenes: [notes-ready]                   # scenes.json names where the control is visible
  calls: ["POST /api/notes/{note_id}/archive"]
  shows: { status: "status@GET /api/notes/{note_id}" }
  next: note-archived                     # a row id, a scene name, a name in `states`, or stay
  on_failure: { archive_4xx: toast:ARCHIVE_FAILED }
  source: ["#12 Implementation Decisions 2"]
  gap: aligned                            # aligned | design-only | backend-only
```

Desktop product — a non-HTTP host call:

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

| Column | Rule |
| --- | --- |
| `id` | `<component-short>.<behaviour>`, lowercase, dots and dashes. Never renumbered, never reused. |
| `component` | A path or name the implementation owns the control under, inside the repository. It is not the name of a `.dc.html` page in the design package — that name is a `pages.<page>` key under **Pages, scenes, viewports, locale, states, retired_ids**. |
| `trigger` | The control's `data-ui` id, a string, copied from the skeleton; every skeleton control that is clickable or editable needs at least one row. |
| `precondition` | Key/value state that selects this row among rows with the same trigger. |
| `scenes` | Names from `scenes.json`. `[]` when the design package shows no scene for this precondition — allowed, and reported. A control that several pages share is one trigger; its scenes are the union over those pages, and a row that must tell the pages apart puts `screen: <page>` in `precondition`. |
| `calls` | `METHOD /path` exactly as in `openapi.json`; `none`; or a non-HTTP form written as the product issues it. Order is the order of effect. An operation the backend does not have yet is listed under `proposed_operations`; the spec's **API contract** subsection describes it. A server-rendered form post is `POST /path`. |
| `shows` | Displayed name → the binding: `field@METHOD /path`, `field@<non-HTTP call>`, `key@RuntimePolicy`, or several of those; then optionally ` → ` and, in words, what is drawn from them (`notes[].pinned@GET /api/notes → count of pinned notes`). No literal numbers or strings in the binding, and no digits outside `{…}` — a status code is a number too. |
| `next` | Where the end user is after the call succeeds; for `calls: [none]`, where the end user is after the click. `stay` when nothing about the page changes (a disabled control, a cancelled dialog). |
| `on_failure` | Failure kind → the outcome, then optionally ` — ` and what the end user sees there in words. The outcome is where the end user is after that failure, in the words `next` uses (a row id, a scene, a name in `states`, `stay`), or `toast:<KEY>` for a message over an unchanged page: `version_conflict_409: note-changed — the banner names the time the note changed`. Every non-`none` call has at least one. The four-column boundary test of the ui-acceptance skill reads this column. |
| `source` | Where the behaviour was decided, in one of these shapes: `#<n>` (a decision ticket), `#<n> Implementation Decisions <k>` or `#<n> Testing Decisions` (a spec section), `ADR-<nnnn>`, `docs/<path> …` (a domain document), `README §…`, `conversation <YYYY-MM-DD>` plus one sentence of the conclusion, or `code:<path>` as a last resort. A user story (`#<n> story <k>`) is an audit trail no worker ever reads: Write a spec folds a story's conclusion into the Implementation Decisions subsection that implements it, and the row cites that. An earlier spec that a decision ticket cites as its basis is citable too, as `#<n> <section>`: cite the decision ticket first, and the earlier spec for what no decision ticket covers. At least one source that is neither README nor `code:`, or `gap` is not `aligned`. |
| `gap` | `aligned` when design and backend agree; `design-only` when the control has no backend behaviour to call; `backend-only` when a decision has no control. |
| `app` | Only on a cross-component row: the `App · ` page the row is written on. See **A cross-component row**. |

A design page with no row is an error. Reverse sweep: every operation in `openapi.json` appears in some row's `calls`, in `backend_without_ui`, or in `proposed_operations`; one that does not is an error naming the method and path.

## A cross-component row

A **cross-component row** records that region A's action affects region B. It is written on an `App · ` page, one row per control whose action the page's `dc-import` wiring carries from one region to another: a callback that several controls fire is one row for each of them. A control whose action also changes its own region keeps its row on its `Component · ` page as well. When no scene of the `App · ` page draws the control, the row's `scenes` is `[]` and the lint warns.

The row carries `app: "<App · page name>"`. `trigger` is region A's `data-ui` id. `calls` is the OpenAPI operation (`METHOD /path` with no query string); name the other region's state the request must carry beside it, not spliced into the path. `next` is the scene region B enters.

A **region** is the substring of a `data-ui` id before the first `.`. The lint takes the skeleton pages that id prefix appears on, drops the row's own `App · ` page (an App page composes the Component pages, so it repeats their ids), and requires the remaining owner to be unique. `next` must name a scene whose `page` is not that owner — the other region, not the one that owns the trigger.

```yaml
- id: notes.filter-tag
  component: features/notes/TagBar
  app: "App · notes.dc.html"
  trigger: tag-bar.pick
  precondition: {}
  scenes: [notes-app-ready]
  calls: ["GET /api/notes"]               # carries tag-bar's selected tag
  shows: { count: "count@GET /api/notes" }
  next: notes-ready                       # the note-list region's scene, not tag-bar's
  on_failure: { list_4xx: toast:LIST_FAILED }
  source: ["#12 Implementation Decisions 4"]
  gap: aligned
```

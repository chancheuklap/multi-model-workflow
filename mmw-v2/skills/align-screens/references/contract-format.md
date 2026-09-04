# The screen contract file

`docs/specs/<effort>/screen-contract.yaml`. One file per effort, read by `to-spec`, `to-tickets`, `implement`, `code-review`, the two judges of `verify-ticket` and the lint. YAML, because a linter reads it more often than a person does.

Two axes. The **control axis** is `rows`: one row per user-visible behaviour, keyed by the control. The **screen axis** is `pages` and `scenes`: one declaration per design page and one per scene of `scenes.json`, saying where the product shows that page (`mount`, `route`) and how a run puts the product into that scene (`reach`, `open`). The two cannot be derived from each other — a page holds many rows, a row is visible on many scenes — so both are written, and the lint holds them to each other.

## Top level

```yaml
effort: notes-v2                          # the wayfinder map's title, as in docs/specs/<effort>/
baselines:
  look: docs/prototypes/<task>/claude-design   # the handoff package directory, unchanged
  precedence: "look & verbatim copy -> handoff package; calls, shows, next, on_failure, timing -> this file"
target:
  kind: electron                          # electron | web-spa | web-server-rendered | chrome-extension
  adapter: verify-ticket/references/targets/electron.md   # relative to the skills install root; read by the scripts
viewports: [1440x900, 1180x720]           # copied from the handoff package README; never a breakpoint of its stylesheets
mechanisms:                               # the spec's mechanism registry, with who builds each and how it writes
  seed:note-with-attachments:
    via: api                              # api (default: the product's own write surface) | storage (declared exception)
    built_by: "#12"                       # the ticket that makes it executable
  seed:note-locked-by-sync:
    via: storage
    built_by: "#10"
    proven_by: "#12 AC2"                 # a storage mechanism names the criterion proving the product reaches the state itself
pages:                                    # one per .dc.html page of scenes.json
  "App · 笔记列表.dc.html":
    mount: notes-app                    # the data-screen value of the product element this page is
    route: "#/"
  "Component · 笔记壳.dc.html":
    mount: note-shell
    route: "#/note/{note_id}"       # {placeholders} are filled from the reach script's KEY=VALUE output
    component: features/note/NoteShell   # the rows' component value this page owns (Component pages only)
scenes:                                   # one per entry of scenes.json
  note-delete-confirm:
    page: "Component · 笔记壳.dc.html"
    reach: [seed:note-with-attachments]
    open: [note-shell.delete.preview.allowed]   # row ids to perform, in order; the last row's next is this scene
  notes-name-duplicate:
    page: "Component · 新建笔记.dc.html"
    route: "#/new-note"                   # overrides the page's route
    mount: create-note                 # overrides the page's mount (a top-level dialog scene overrides to the page root's id)
    reach: [seed:notes-ready]
    open:
      - row: create-note.name
        value: "{existing_note_name}"  # an input role carries a value; from data/fixtures.js or a reach KEY
  share-wait:
    page: "Component · 分享详情.dc.html"
    reach: [seed:note-ready]
    open: [note-shell.share, share-confirm.submit]
    clock: 3000                           # virtual ms run after open, for a state the design defines by elapsed time
readme_dispositions:                      # every README sentence that states a behaviour, for the pages in scope
  - text: "create 下一步 → analysis →（自动 1800ms）→ confirm"
    disposition: overridden by create-project.next (#420)
backend_without_ui:                       # decisions or operations with no control; one line each
  - "POST /api/recovery/finalize — runs at startup, no control"
proposed_operations:                      # operations the rows need and openapi.json lacks yet; each is
  - "POST /api/projects/{project_id}/draft/{task_id}/copy/redraft"   # described in api-contract.md
retired_ids:                              # ids that once had a row; never reused; printed by the lint on every run
  - id: debt-gate.demo-trigger
    note: "retired 2026-09-03 — #635 verdict 5: prototype harness control, never shipped"
    page: "Component · 欠费门禁.dc.html"    # the design page the control is on; the judges hide it there only
    trigger: { role: button, name: "开始新生成（触发欠费门禁）" }   # present when the handoff still shows the control:
rows: [...]                               # the lint then stops asking for a row, and the judges hide it on the design side
```

## The screen axis

| Key | Rule | Lint |
| --- | --- | --- |
| `target.kind` | One of the adapters the driver has: `electron`, `web-spa`, `web-server-rendered`, `chrome-extension`. Selects how the product is attached, readied, addressed, released, seeded and read. | one of the four |
| `target.adapter` | The reference file of that kind under `verify-ticket/references/targets/`, relative to the skills install root. It is the human account; the scripts read `kind`. | the file exists |
| `viewports` | `WIDTHxHEIGHT` entries copied from the handoff package README (its design size and its declared minimum). A viewport equal to a media-query breakpoint of the package's stylesheets compares two reflows and verifies nothing. | parseable; no width equals a `@media (max-width\|min-width: Npx)` of `styles/*.css` |
| `pages.<page>.mount` | A short stable id — the value of the `data-screen` attribute on the one product element this page *is*. Its subtree is what the tree judge reads; its box is what the pixel judge measures. It is not a test hook; it is where "this design page is that block of the product" is written down. Declared by the person writing the contract, never derived from the `component` column (a page holds several components' rows, and the one with most rows can be a borrowed shared control). | present, `[a-z0-9-]`, unique across pages |
| `pages.<page>.route` | The product address of that page. One per page; a scene may override it (a view rendered both standalone and inside a workbench has two). | present |
| `pages.<page>.component` | For a `Component · ` page: the rows' `component` value this page owns. `App · ` pages are whole-surface roots and carry none. | Component pages ↔ distinct `component` values one to one |
| `scenes.<name>.page` | The `.dc.html` from `scenes.json`. | equals scenes.json; every scene of scenes.json has one entry and nothing else does |
| `scenes.<name>.reach` | Mechanism names, run through the repository's reach script before the scene, in order; idempotent, run once per scene. | each in `mechanisms` |
| `scenes.<name>.open` | Row ids performed after navigation to reach the scene: each step clicks its row's trigger (or fills it, for `textbox`, `combobox`, `spinbutton`, `searchbox`, with `value`). Written as row ids, never as role and name: one name often belongs to several rows. Writes are allowed; `reach` being idempotent per scene is what keeps them safe. The last row must land the scene, in one of four ways: its `next` is the scene; its `next` is a scene on the same design page (the action lands the page, `reach` decides the state); one of its `on_failure` values is the scene (a failure the scene's stub scripts); the scene is an `App · ` whole-surface page containing the block the action lands. A scene that keeps the row on screen after the action (a queue row selected while the task opens beside it) lists the row under its `scenes`, which counts too. | each row exists; the last row lands the scene; an input role carries `value` |
| `scenes.<name>.clock` | Virtual milliseconds the controlled clock is run after `open` and before capture. The one place elapsed time enters: for a state the design itself defines by time (a notice gone after its toast timer). Absent means none. | a whole number |
| `scenes.<name>.mount`, `.route` | Overrides. A scene whose content is a top-level dialog outside the page's subtree overrides `mount` to the page root's id. | a declared mount |
| `mechanisms.<name>.via` | `api` — through the product's own write surface, self-proving; `storage` — the declared exception, which is not. | `api` or `storage` |
| `mechanisms.<name>.built_by` | The ticket that makes the mechanism executable. A ticket that uses a mechanism is blocked by its builder, unless it is the builder; `verify-ticket --lint` checks that against the ticket's blocking links. | `#<n>` |
| `mechanisms.<name>.proven_by` | For `via: storage`: `#<n> AC<k>`, the criterion proving the product reaches that state through its own path. | present when `via: storage` |

Everything on this axis is filled at design time, with no running product: `page` from `scenes.json`, `mount` and `route` as declarations (the same pattern as `proposed_operations`), `reach` from the mechanism table, `open` from the offline render plus the control axis, `value` from `data/fixtures.js`. Verification needs the product; filling does not.

A `retired_ids` entry with a `trigger` names the `page` the control is on; the judges hide it on that page's scenes only. A role and name are not unique across pages, and an entry without a `page` whose name also lives on another page is hidden everywhere — the lint warns.

## Target trees

`docs/specs/<effort>/targets/<page>.aria` and `<page>.classes`, one pair per design page, written by `extract_skeleton.py --targets` from the same render and the same normaliser the judges use: every scene's normalised tree and class set. They are the handoff package's behavioural counterpart — the half of it a worker reads directly — and a **derived view**: the package is the baseline, and each file's header carries the sha256 of `scenes.json` and of its page. | the lint fails when either hash no longer matches the package |

## A row

```yaml
- id: create-note.add-attachment          # <component>.<behaviour>; stable once published
  component: features/note/CreateNoteView   # where the implementation owns it
  trigger: { role: button, name: "添加附件 拖入文件，或从本机选择" }   # exactly as the accessibility tree says
  precondition: { attachment: none }      # what must already be true; {} when nothing
  scenes: [empty, notes-attachment-required, add-attachment]   # scenes.json names where the control is visible
  calls: ["ipc app:file:select", "POST /api/notes/{note_id}/draft"]   # or [none]
  shows: { attachment_name: "basename(attachment_path@GET /api/notes/{note_id}/draft)" }
  next: create-note.attachment-pending    # a row id, a scene name, or a state name from the domain doc
  route: "#/new-note"                     # where the implementation shows this control; the wiring check navigates here
  observe: ["GET /api/notes/{note_id}/draft -> .has_draft == true"]   # the read surface that proves `next`
  drive:                                  # only when no scene shows the control actionable (a form the design never shows complete)
    scene: empty                          # the scene the wiring check drives this row on; default: the first of `scenes`
    reach: [dev:file-select-path]         # mechanisms run after the scene's own
    open:                                 # steps after the scene's chain, before the trigger
      - { row: create-note.name, value: "{note_new_name}" }
      - create-note.add-attachment
  on_failure: { dialog_cancelled: no-change, draft_4xx: toast:NEXT_FAILED_TITLE }
  source: ["#537 Implementation Decisions 2", "#420", "README §5.3 (transition overridden)"]
  reach: seed:project-empty               # a mechanisms entry
  gap: aligned                            # aligned | design-only | backend-only
```

## Column rules

| Column | Rule | Lint |
| --- | --- | --- |
| `id` | `<component-short>.<behaviour>`, lowercase, dots and dashes. Never renumbered, never reused. | unique; every id in `retired_ids` absent from rows |
| `component` | A path or name the implementation owns the control under. | one `Component · ` page claims it |
| `trigger` | `role` and `name` copied from the skeleton. Hint text that the tree folds into the name stays in. | (role, name) exists in the skeleton; every skeleton control has ≥1 row |
| `precondition` | Key/value state that selects this row among rows with the same trigger. | rows sharing a trigger have distinct preconditions |
| `scenes` | Names from `scenes.json`. `[]` when the handoff shows no scene for this precondition — allowed, and reported. A control that several pages share is one trigger; its scenes are the union over those pages, and a row that must tell the pages apart puts `screen: <page>` in `precondition`. | each exists in the skeleton for this trigger; `[]` is a warning |
| `calls` | `METHOD /path` exactly as in `openapi.json`; a non-HTTP form the target declares (`ipc <channel>` on electron, `chrome.runtime.sendMessage <type>` on an extension; a server-rendered page needs none — a form post is `POST /path`); or `none`. Order is the order of effect. An operation the backend does not have yet is listed under `proposed_operations` and described in `api-contract.md`. | HTTP entries exist in `openapi.json` or in `proposed_operations` (a warning); without an `openapi.json`, reported as `unverified` |
| `shows` | Displayed name → `field@METHOD /path`, `field@ipc <channel>`, `key@RuntimePolicy`, or an expression over those. No literal numbers or strings — a status code is a number too. The perturbation run of `visual-parity.py` reseeds with other values and requires each scene whose rows declare `shows` to read differently. | value contains `@`; no digits outside `{…}` |
| `next` | Where the user is after the call succeeds; for `calls: [none]`, where the user is after the click. `stay` when nothing about the page changes (a disabled control, a cancelled dialog). | a row id, a scene name, a state named in the domain doc, or `stay`; an `open` chain ends on a row whose `next` is the scene |
| `route` | The implementation's address for the screen this control is on (`#/new-project`). One per page; a row may override it. | present on every row with calls, directly or through its page |
| `drive` | Where and how the wiring check drives the row: `scene` (default: the first of `scenes`), `reach` (mechanisms after the scene's), `open` (steps after the scene's chain). Needed exactly when the trigger is disabled or absent on every scene the design shows — a form the design never shows complete — or when the first scene contradicts the row's precondition. | the trigger is present and not `[disabled]` in the driving scene's target tree, or `drive.open` is given; `drive.scene` is in `scenes` |
| `observe` | A fresh read of persistent state, on a path the acting view did not produce, issued after the action completed: `METHOD /path -> <jq-style expression>` on a target with a JSON read surface, `GET /path -> node <role> "<name>" exists` on a server-rendered page without one (see `verify-ticket/references/targets/`). This is what the wiring check asserts on; nothing in the renderer is. A row whose calls are all non-HTTP writes nothing the surface can read; it may leave `observe` empty, and the wiring check then only performs the trigger. | present when `calls` names an HTTP operation; each operation exists in `openapi.json` or `proposed_operations` |
| `on_failure` | Failure kind → what the user sees. Every non-`none` call has at least one. No judge reads this column yet. | present when `calls` is not `[none]` |
| `source` | Where the behaviour was decided, in one of these shapes: `#<n>` (a decision ticket), `#<n> Implementation Decisions <k>` or `#<n> Testing Decisions` (a spec section), `ADR-<nnnn>`, `docs/<path> …` (a domain document), `README §…`, or `code:<path>` as a last resort. A story (`#<n> story <k>`) is an audit trail no worker ever reads: `to-spec` folds a story's conclusion into the Implementation Decisions subsection that implements it, and the row cites that. At least one source that is neither README nor `code:`, or `gap` is not `aligned`. | non-empty; a story or an unrecognised shape is a warning |
| `reach` | One `mechanisms` entry. | resolves |
| `gap` | `aligned` when design and backend agree; `design-only` when the control has no backend behaviour to call; `backend-only` when a decision has no control. | `to-spec` refuses a file with any non-`aligned` row |

## What the downstream skills take from it

- `to-spec`: `calls` and `shows` → the **API contract** subsection; `mechanisms` → **How a test arrives at a state**; `baselines` → Sources; the **visual acceptance** paragraph cites `pages` and `scenes` instead of restating any command.
- `to-tickets`: a UI ticket's **Read first** cites row ids and the target-tree files of its pages, and lists every baseline-class `source` of those rows, deduplicated by document; each row with a non-`none` call becomes one wiring criterion; the parity criterion names the ticket's `--mount` values, and scenes are owned by mount (by `route` when mounts collide; an explicit `--scenes` subset when one page is split between tickets). A ticket that uses a mechanism is blocked by its `built_by`.
- `implement`: `precedence` is the rule for a conflict between the handoff package and this file; every surface component's root carries `data-screen="<mount>"`; the target trees are what the worker writes toward.
- `code-review` Spec axis: reviews the diff row by row for the ids the ticket cites, **and** checks that each `mount` the ticket owns is implemented as declared and that each `open` chain under it can be performed on the diff — the addressing self-check only proves they exist, and interface parity covers `open` only indirectly.
- `verify-ticket --lint`: the flags of the two pipeline scripts, the `built_by` blocking rule, the source rule, the scene partition across the batch.

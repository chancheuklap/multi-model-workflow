# The screen contract file

`docs/specs/<effort>/screen-contract.yaml`. One file per effort, read by `to-spec`, `to-tickets`, `implement`, `code-review`, the story judge, the boundary check and the lint. YAML, because a linter reads it more often than a person does.

The **control axis** is `rows`: one row per user-visible behaviour, keyed by the control. `pages` names each design page's story id (`mount`) and the component that owns it; `scenes` names which design page each scene of `scenes.json` belongs to. The control axis and these declarations cannot be derived from each other — a page holds many rows, a row is visible on many scenes — so both are written, and the lint holds them to each other.

## Top level

```yaml
effort: notes-v2                          # the wayfinder map's title, as in docs/specs/<effort>/
baselines:
  look: docs/prototypes/<task>/claude-design   # the handoff package directory, unchanged
  precedence: "look & verbatim copy -> handoff package; calls, shows, next, on_failure -> this file"
target:
  kind: electron                          # electron | web-spa | web-server-rendered | chrome-extension
viewports: [1440x900, 1180x720]           # copied from the handoff package README; never a breakpoint of its stylesheets
pages:                                    # one per .dc.html page of scenes.json
  "App · 笔记列表.dc.html":
    mount: notes-app                    # the story page id; the product story is addressed by this value
    route: "#/"                         # App pages only; journeys compare these whole surfaces
  "Component · 笔记壳.dc.html":
    mount: note-shell
    component: features/note/NoteShell   # the rows' component value this page owns (Component pages only)
scenes:                                   # one per entry of scenes.json
  note-delete-confirm:
    page: "Component · 笔记壳.dc.html"
  notes-name-duplicate:
    page: "Component · 新建笔记.dc.html"
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
                                          # the lint then stops asking for a row, and the judges hide it on the design side
volatile_values:                          # display values the seed must not write; printed by the lint on every run
  - page: "App · 商品项目库.dc.html"
    trigger: { role: text, name: "鸭豆余额 12,480" }   # handoff role and accessible name; same shape as retired_ids
    reason: "wallet balance is an external account; seed does not write it"
  - page: "Component · 自由模式.dc.html"
    trigger: { role: strong, name: "12,480 鸭豆" }
    after: { role: text, name: "当前余额" }   # previous named node; required when the stem is not unique on the scene
    reason: "wallet balance is an external account; seed does not write it"
rows: [...]
```

## Pages, scenes, target, viewports

| Key | Rule | Lint |
| --- | --- | --- |
| `target.kind` | One of the adapters the driver of the `drive-target` skill has: `electron`, `web-spa`, `web-server-rendered`, `chrome-extension`. Selects how the repository answers in `.mmw/target.json`. What the repository has to answer is declared by that skill: run `screen_driver.py target --check` in the repository to see every field, one sentence and one example each. | one of the four (`target --validate` of the drive-target skill) |
| `viewports` | `WIDTHxHEIGHT` entries copied from the handoff package README (its design size and its declared minimum). A viewport equal to a media-query breakpoint of the package's stylesheets compares two reflows and verifies nothing. | parseable; no width equals a `@media (max-width\|min-width: Npx)` of `styles/*.css` |
| `pages.<page>.mount` | A short stable id — the story page id the product serves as `?page=<mount>`. It is also the value of `data-screen` on the one product element this page *is*, when the surface carries that attribute. Declared by the person writing the contract, never derived from the `component` column (a page holds several components' rows, and the one with most rows can be a borrowed shared control). | present, `[a-z0-9-]`, unique across pages |
| `pages.<page>.route` | The product address of an `App · ` page. Journeys compare those whole surfaces. A `Component · ` page must not carry this key. | absent on every non-App page |
| `pages.<page>.component` | For a `Component · ` page: the rows' `component` value this page owns. `App · ` pages are whole-surface roots and carry none. | Component pages ↔ distinct `component` values one to one |
| `scenes.<name>.page` | The `.dc.html` from `scenes.json`. | equals scenes.json; every scene of scenes.json has one entry and nothing else does |

A key that is not in this table or in the Column rules table below, on a page, a scene, a row, or at the top level, is an error that names the key.

`pages` and `scenes` are filled at design time, with no running product: `page` from `scenes.json`, `mount` as a declaration. Verification needs the product; filling does not.

A `retired_ids` entry with a `trigger` names the `page` the control is on; the judges hide it on that page's scenes only. A role and name are not unique across pages, and an entry without a `page` whose name also lives on another page is hidden everywhere — the lint warns.

A `volatile_values` entry is a display value the seed must not write — a wallet balance belonging to an external account, not a difference to hide. Same trigger shape as `retired_ids` (`page`, role, accessible name) plus one line of `reason`. When several nodes on one scene share that role and stem — three sibling `strong` whose names are `20 鸭豆`, `40 鸭豆`, `12,480 鸭豆` — the entry also names `after`: the previous named node (`text: 当前余额`). Matching uses one function (`matches_volatile`) on the story judge and on this lint: role equal (a `text` trigger also matches the roles a static string snapshots as in the tree — `cell`, `generic`, and the rest of that set), accessible names equal once digits and thousands separators are removed (`鸭豆余额 12,480` matches `鸭豆余额 1,000,000`; a currency sign or a unit stays and must agree), and when `after` is set, the previous named node in reading order matches that pair the same way. Before the accessibility tree and the pixel judge compare, both sides replace that node's text with one token: the tree name becomes `<volatile>`, and the pixel judge first puts the trigger's digits into the node on both sides (so the two boxes are one width and nothing after them moves, whatever number each side showed) and then paints that box the same solid colour, so different numbers compare equal. The lint prints every `volatile_values` entry on every run, warns when that trigger is not in that page's target tree, and errors when a `volatile_values` entry matches more than one node on any scene of that page.

When a `story-parity.py --out` directory sits under the contract directory, the lint reads the newest such inventory (`media/<scene>-<WxH>-impl.png` files) and warns if a non-App page has a scene that inventory does not cover. `App · ` pages are outside this warning: the story judge's `--pages` takes only non-App mounts, so an App-page miss can never be repaired. That is how #216 Implementation Decisions section 5's "每个设计页" is applied to the judge that landed. No inventory is silence: the contract has not been compared yet.

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
  on_failure: { dialog_cancelled: no-change, draft_4xx: toast:NEXT_FAILED_TITLE }
  source: ["#537 Implementation Decisions 2", "#420", "README §5.3 (transition overridden)"]
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
| `shows` | Displayed name → `field@METHOD /path`, `field@ipc <channel>`, `key@RuntimePolicy`, or an expression over those. No literal numbers or strings — a status code is a number too. | value contains `@`; no digits outside `{…}` |
| `next` | Where the user is after the call succeeds; for `calls: [none]`, where the user is after the click. `stay` when nothing about the page changes (a disabled control, a cancelled dialog). | a row id, a scene name, a state named in the domain doc, or `stay` |
| `on_failure` | Failure kind → what the user sees. Every non-`none` call has at least one. No judge reads this column yet. | present when `calls` is not `[none]` |
| `source` | Where the behaviour was decided, in one of these shapes: `#<n>` (a decision ticket), `#<n> Implementation Decisions <k>` or `#<n> Testing Decisions` (a spec section), `ADR-<nnnn>`, `docs/<path> …` (a domain document), `README §…`, or `code:<path>` as a last resort. A story (`#<n> story <k>`) is an audit trail no worker ever reads: `to-spec` folds a story's conclusion into the Implementation Decisions subsection that implements it, and the row cites that. At least one source that is neither README nor `code:`, or `gap` is not `aligned`. | non-empty; a story or an unrecognised shape is a warning |
| `gap` | `aligned` when design and backend agree; `design-only` when the control has no backend behaviour to call; `backend-only` when a decision has no control. | `to-spec` refuses a file with any non-`aligned` row |

## What the downstream skills take from it

- `to-spec`: `calls` and `shows` → the **API contract** subsection; `baselines` → Sources; the **visual acceptance** paragraph cites `pages` and the story judge instead of restating any command. Testing Decisions' **Test surfaces** four questions are the drive-target skill's runtime-environment list (`start`, `stop`, `discover`, `stories`, `journeys`, `leaves_machine`, `instance`).
- `to-tickets`: a UI ticket owns by design page: one story criterion (`story-parity.py --pages <mount,…>`), and one boundary criterion per row whose `calls` is not `[none]` (several rows may share one test file). **Read first** lists the target-tree files of those pages and `scenes.json`, and every baseline-class `source` of those rows, deduplicated by document. Journeys are written only on the contract ticket and on tickets the owner named. There is no partition of scenes by mount, and no wiring criterion.
- `implement`: `precedence` is the rule for a conflict between the handoff package and this file; the worker writes the display component together with its story adapter and its boundary tests; the target trees are what the worker writes toward.
- `code-review` Spec axis: reviews the diff row by row for the ids the ticket cites, and checks that the story adapter's field mapping matches each cited row's `shows`. Tests axis: the boundary tests run through `boundary-check.py`.
- `verify-ticket --lint`: the flags of the pipeline scripts; runtime semantics are unchanged.

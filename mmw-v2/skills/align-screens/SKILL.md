---
name: align-screens
description: Produce the screen contract for an interface — one row per user-visible behaviour saying what the control calls, which backend field feeds each shown value, what state follows and how a test reaches it, plus one declaration per design page and per scene saying where the product shows it and how a run gets there — by aligning a downloaded handoff package with the backend decisions of a wayfinder map. Use when a handoff package has landed and a spec is about to be written, when a handoff package was re-downloaded, or when a spec decision changed and the contract has to follow. Not for writing the spec itself (to-spec) or comparing pixels (verify-ticket).
---

# align-screens — the screen contract between a handoff package and the backend

A handoff package says what the interface looks like and what it says. The wayfinder map's decisions say what the system does. Nothing in between says which control calls what, or which block of the product each design page is. This skill writes that file: the **screen contract**, `docs/specs/<effort>/screen-contract.yaml`. From then on the handoff package binds look and verbatim copy, the screen contract binds calls, shown values, transitions, timing and the screen axis, and every downstream skill reads the two by that split.

The file's shape is in [references/contract-format.md](references/contract-format.md). Read it before step 2.

## Inputs

- The handoff package directory: `README.md`, the `.dc.html` pages, `styles/`, `data/fixtures.js`, `support.js`, `scenes.json`, and `vendor/` with the three scripts `support.js` loads. It is a **baseline for look and copy**; you never edit it.
- The wayfinder map issue: its **Decisions so far** and, through each link, the closed tickets' resolution comments. Where a resolution names an ADR, a research file, a logic prototype's contract file or the domain doc, read that too.
- The backend contract as it exists today: `openapi.json`. When the repository's own exporter writes one, use that; when it does not cover this product, dump it yourself — `uv run python <this skill>/scripts/dump_openapi.py <module>:<factory> <scratch>/openapi.json` calls the app factory and writes its OpenAPI document. A new project has no routes yet; the lint then marks calls `unverified` instead of failing them.
- The spec's mechanism registry, when a spec exists. Before the first spec there is none: propose the mechanisms the rows need under `mechanisms`, put one entry on the gap list saying they are proposals, and say so in a comment at the top of the file. Each mechanism names who builds it (`built_by`) and how it writes (`via`); before tickets exist, `built_by` names the ticket to be — the contract ticket for a seed the first interface ticket needs — and is corrected when the tickets are cut.
- What kind of product this is — a running desktop application, a server-rendered site, a single-page application, a browser extension — which is the contract's `target.kind`. The kinds and what each asks of the repository are in the `drive-target` skill's `references/targets/README.md`.
- The effort name: the name of the `docs/specs/<effort>/` directory the specs of this map live in. A map whose specs directory does not exist yet takes the map's title.
- The scope. A full run covers every page in `scenes.json`. A scoped run names the pages it covers; the reverse sweep and the README dispositions then stay inside those pages, and the lint reports the other pages as warnings.

Write every path in a command out in full. Some hosts refuse `uv run … $VAR`.

## Steps

### 1. Extract the skeleton

The render is the `drive-target` skill's: resolve `<drive-target scripts>` from that skill's `SKILL.md`, then

```
uv run python <drive-target scripts>/extract_skeleton.py <handoff dir> <scratch>/skeleton.json
```

It renders every scene in `scenes.json` offline, through the same driver interface parity uses, reads each accessibility tree, and keeps every interactive control keyed by (page, role, accessible name) with the list of scenes it is visible in. This is the row inventory: a control the skeleton has and the contract lacks is a lint error, and so is the reverse. The accessible name is the whole name the tree reports, hint text included — copy it exactly. The same render leaves each scene's normalised tree and class set in the skeleton; step 6 writes them out as the target trees.

### 2. Declare the screen axis, name components and split preconditions

Top level first: `target.kind`, and `viewports` copied from the handoff package `README.md` (the design size and the declared minimum; never a breakpoint of its stylesheets).

Then, for each page in `scenes.json`, one `pages` entry: its **`mount`** — the short stable id the product will carry as `data-screen` on the one element that *is* this page — and its **`route`**. `mount` is your declaration, not a derivation: a page holds several components' rows, and the one with most rows can be a shared control borrowed from another page. For a `Component · ` page also name the **`component`** the implementation will own it under — the repository's existing feature directory when there is one, otherwise the page name; every row of that page's controls uses the same value. An `App · ` page is a whole-surface root and names no component.

Then a control whose behaviour differs by state gets one row per state — `precondition` is the column that tells them apart (`material: none` and `material: added` are two rows for the same button). Three cases that come up on every page:

- **A disabled state is a row.** The user sees the control; the row says `calls: [none]` and `next` is the scene the user stays in.
- **A control whose accessible name embeds a shown value** (`附件_报告.pdf 已添加 …`) appears in the skeleton once per value. Keep the name as the skeleton reports it — the trigger is on the look side of the split — and put the value's field in `shows`. One row per state, as above.
- **A state the handoff never shows** (the form complete, ready to submit) is still a row when the backend decisions reach it. Its `scenes` is `[]`; the lint reports it as a warning so the handoff gap is on record.

A name the accessibility tree gets from a placeholder or a hint is copied all the same, and reported as an accessibility defect of the handoff in the run's notes.

### 3. Fill the behaviour columns and the scene declarations from the backend sources

For every row: `calls`, `shows`, `next`, `on_failure`, `source`, `reach`, `gap`. The rules that decide each column are in the format reference; the ones people get wrong:

- `shows` names fields, never values: `balance@GET /api/wallet`, `path@ipc app:file:select`, `unit_price@RuntimePolicy` — not `1234`, and not a status code either. The literals in `data/fixtures.js` are seed data for tests, not copy — and so are their **counts**: a seed makes as many rows as the fixtures draw.
- A row the wiring check acts on (it has `observe` lines) is driven on one scene, and the design's tree of that scene has to show the trigger enabled. A form the design only shows incomplete — every scene has 「下一步」 disabled — gets `drive`: the scene to drive on and the `open` steps (type the name, pick the file) that make the control actionable. The lint refuses a row it could not act on.
- `calls` names what the control does to the system: an HTTP operation as it appears in `openapi.json`, the target's non-HTTP form, or `none`. A control that only changes local view state is `none` and still a row; its `next` is the row or scene the user is in afterwards. An operation the decisions require and `openapi.json` lacks goes in the row as it will be named, and once more under `proposed_operations`; the API contract draft in step 6 describes it.
- `source` quotes where the behaviour was decided, in the shapes the format reference lists: a decision ticket, a spec section, an ADR, a domain-doc term, a README section. A story is an audit trail no worker reads; cite the Implementation Decisions subsection that carries its conclusion. Existing code counts only as a last resort, written `code:<path>`, and a row whose sources are all `code:` and README is a `design-only` candidate — check the decisions again before marking it.
- `reach` is a reference into the mechanism registry (`seed:<state>`, `stub:<seam>-<script>`, `dev:<capability>`), never free text. A mechanism nobody has declared yet goes on the gap list.
- `route` and `observe` are what turn a row into a wiring criterion: the implementation address the control is on, and the read that proves `next` happened — through the target's read surface, in the grammar its reference file gives (`GET /api/projects/{project_id}/draft -> .has_draft == true` on a JSON surface, `GET /org/licenses -> node button "撤销分配" exists` on a server-rendered page without one). A row with calls and no `observe` cannot be checked by machine, and the lint says so.

Then one `scenes` entry per scene of `scenes.json`: its `page`; its `reach`, the mechanisms that put the product into that scene; and, when the scene is not what the route shows on arrival, its `open` — the row ids to perform, in order, ending on a row whose `next` is this scene (an input role carries its `value`, from `data/fixtures.js`). A scene that is a top-level dialog outside the page's subtree overrides `mount` to the page root's id. Everything here is filled offline; nothing needs the product.

While filling, read the handoff `README.md` once, end to end. Every sentence there that states a transition, a timer, a data fetch or a value, about a page in scope, gets a line under `readme_dispositions`: `adopted by <row>`, `overridden by <row> (<source>)`, or `out of scope (<page>)` when the statement is about a control on a page this run does not cover. This is what stops the README and the spec from saying two things about the same behaviour later.

### 4. Reverse sweep

Walk the map's decisions and the backend contract the other way: every decision line that a user can observe, and every operation in `openapi.json`, lands in at least one row's `source` or `calls`. One that does not is a `backend-only` row (the interface has no place for it) or is marked `no-ui` in `backend_without_ui` with one line saying why. In a scoped run, judge only the decisions and operations that belong to the pages in scope; the rest is not listed — a list of "out of scope" lines carries no judgement and hides the ones that do.

### 5. Write the gap list and stop for the person

Collect every row whose `gap` is `design-only` or `backend-only`, every `reach` with no mechanism, and every scene a person has judged cannot be captured (record that as a dated `retired_ids`-style entry after the verdict; there is no exemption field, and the lint prints every retirement on every run). Write them to `<scratch>/gap-list.md`: one entry each, with the row id, what the design shows, what the backend decides, the options, and the one you would take. Then hand the list to the person — this is the one judgement in this skill that is theirs, and it is a grilling, not a form. Expect a handful of entries, not dozens; dozens means a decision ticket was skipped upstream, and that goes back to the wayfinder map.

When the person is not reachable in this run (a batch, a test run), write the gap list and stop. The contract stays in the run's scratch directory with its `gap` values as they are; the lint reports each unresolved gap as an error, and that is the intended state. Nothing is written under `docs/specs/` until every gap is `aligned`.

Two things a gap list does not carry: an implementation that today does less than the decisions say (that is a finding for the ticket owning the code, note it in the run's notes), and an accessible name that the shipped product will render differently from the handoff (that is for `verify-ticket`'s parity run to catch, not for this file to predict).

### 6. Publish, write the target trees, and lint

Write `docs/specs/<effort>/screen-contract.yaml`, then render once more with the contract in hand so the retired controls are hidden, writing the target trees beside it:

```
uv run python <drive-target scripts>/extract_skeleton.py <handoff dir> <scratch>/skeleton.json --targets docs/specs/<effort>/targets --contract docs/specs/<effort>/screen-contract.yaml
uv run python <this skill>/scripts/lint_contract.py --tools <drive-target scripts> docs/specs/<effort>/screen-contract.yaml <scratch>/skeleton.json [<openapi.json>]
```

The lint asks the drive-target skill's driver for the target kinds and for the state of the repository's `.mmw/target.json` (a warning while the contract ticket has not landed it), which is why it takes `--tools`. The target trees — one `.aria` and one `.classes` file per design page under `docs/specs/<effort>/targets/` — are what a worker writes toward and what the judges compare against, produced by the judges' own normaliser. They are a derived view of the handoff package and carry its hashes; the lint fails when they go stale. Zero errors, or fix the file. Then write the **API contract** draft — one entry per distinct operation in `calls`, with the request and response fields the rows' `shows` and `on_failure` imply — to `<scratch>/api-contract.md`, for the `to-spec` skill to fold into the spec's Implementation Decisions.

## Re-runs

- The handoff package was re-downloaded: run steps 1 and 6. Triggers whose accessible name changed appear as lint errors on both sides; rebind them by hand, keep the row ids. Step 6 regenerates the target trees, and the lint's hash check is what tells you when this re-run is overdue.
- A spec decision changed: edit the rows that cite it, rerun step 6, and put the changed rows through step 5 again.
- Row ids are never renumbered or reused. A retired behaviour loses its row; the id goes in `retired_ids` with one line saying when, and with its trigger when the handoff still shows the control — the lint then stops asking for a row, prints the retirement on every run, and the judges hide the control on the design side.

## Done when

`screen-contract.yaml` lints clean, every row's `gap` is `aligned`, every scene of `scenes.json` has a declaration, every page has a `mount` and a `route`, every mechanism has a `via` and a `built_by`, the target trees under `docs/specs/<effort>/targets/` match the package, every README statement about behaviour has a disposition, `api-contract.md` exists, and the person has answered every entry of the gap list — or, in a run without the person, the gap list is written and the run has said so.

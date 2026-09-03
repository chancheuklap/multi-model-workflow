---
name: align-screens
description: Produce the screen contract for an interface — one row per user-visible behaviour saying what the control calls, which backend field feeds each shown value, what state follows and how a test reaches it — by aligning a downloaded handoff package with the backend decisions of a wayfinder map. Use when a handoff package has landed and a spec is about to be written, when a handoff package was re-downloaded, or when a spec decision changed and the contract has to follow. Not for writing the spec itself (to-spec) or comparing pixels (verify-ticket).
---

# align-screens — the screen contract between a handoff package and the backend

A handoff package says what the interface looks like and what it says. The wayfinder map's decisions say what the system does. Nothing in between says which control calls what. This skill writes that file: the **screen contract**, `docs/specs/<effort>/screen-contract.yaml`. From then on the handoff package binds look and verbatim copy, the screen contract binds calls, shown values, transitions and timing, and every downstream skill reads the two by that split.

The file's shape is in [references/contract-format.md](references/contract-format.md). Read it before step 3.

## Inputs

- The handoff package directory: `README.md`, the `.dc.html` pages, `styles/`, `data/fixtures.js`, `support.js`, `scenes.json`. It is a **baseline for look and copy**; you never edit it.
- The wayfinder map issue: its **Decisions so far** and, through each link, the closed tickets' resolution comments. Where a resolution names an ADR, a research file, a logic prototype's contract file or the domain doc, read that too.
- The backend contract as it exists today: `openapi.json`. When the repository's own exporter writes one, use that; when it does not cover this product, dump it yourself — `uv run python <this skill>/scripts/dump_openapi.py <module>:<factory> <scratch>/openapi.json` calls the app factory and writes its OpenAPI document. A new project has no routes yet; the lint then marks calls `unverified` instead of failing them.
- The spec's mechanism registry, when a spec exists. Before the first spec there is none: propose the mechanisms the rows need under `mechanisms`, put one entry on the gap list saying they are proposals, and say so in a comment at the top of the file.
- The effort name: the name of the `docs/specs/<effort>/` directory the specs of this map live in. A map whose specs directory does not exist yet takes the map's title.
- The scope. A full run covers every page in `scenes.json`. A scoped run names the pages it covers; the reverse sweep and the README dispositions then stay inside those pages, and the lint reports the other pages as warnings.

Write every path in a command out in full. Some hosts refuse `uv run … $VAR`.

## Steps

### 1. Extract the skeleton

```
uv run python <this skill>/scripts/extract_skeleton.py <handoff dir> <scratch>/skeleton.json
```

It renders every scene in `scenes.json` offline, reads each accessibility tree, and keeps every interactive control keyed by (page, role, accessible name) with the list of scenes it is visible in. This is the row inventory: a control the skeleton has and the contract lacks is a lint error, and so is the reverse. The accessible name is the whole name the tree reports, hint text included — copy it exactly.

### 2. Name components and split preconditions

For each page in the skeleton, name the component the implementation will own it under: the repository's existing feature directory when there is one, otherwise the page name. A control whose behaviour differs by state gets one row per state — `precondition` is the column that tells them apart (`material: none` and `material: added` are two rows for the same button). Three cases that come up on every page:

- **A disabled state is a row.** The user sees the control; the row says `calls: [none]` and `next` is the scene the user stays in.
- **A control whose accessible name embeds a shown value** (`商品素材_洗洁精.jpg 已添加 …`) appears in the skeleton once per value. Keep the name as the skeleton reports it — the trigger is on the look side of the split — and put the value's field in `shows`. One row per state, as above.
- **A state the handoff never shows** (the form complete, ready to submit) is still a row when the backend decisions reach it. Its `scenes` is `[]`; the lint reports it as a warning so the handoff gap is on record.

A name the accessibility tree gets from a placeholder or a hint is copied all the same, and reported as an accessibility defect of the handoff in the run's notes.

### 3. Fill the behaviour columns from the backend sources

For every row: `calls`, `shows`, `next`, `on_failure`, `source`, `reach`, `gap`. The rules that decide each column are in the format reference; the ones people get wrong:

- `shows` names fields, never values: `balance@GET /api/wallet`, `path@ipc chameleon:image:select`, `unit_price@RuntimePolicy` — not `12480`, and not a status code either. The literals in `data/fixtures.js` are seed data for tests, not copy.
- `calls` names what the control does to the system: an HTTP operation as it appears in `openapi.json`, an IPC channel, or `none`. A control that only changes local view state is `none` and still a row; its `next` is the row or scene the user is in afterwards. An operation the decisions require and `openapi.json` lacks goes in the row as it will be named, and once more under `proposed_operations`; the API contract draft in step 6 describes it.
- `source` quotes where the behaviour was decided: a decision ticket, an ADR, a user story, a domain-doc term, a README section. Existing code counts only as a last resort, written `code:<path>`, and a row whose sources are all `code:` and README is a `design-only` candidate — check the decisions again before marking it.
- `reach` is a reference into the mechanism registry (`seed:<state>`, `stub:<seam>-<script>`, `dev:<capability>`), never free text. A mechanism nobody has declared yet goes on the gap list.
- `route` and `observe` are what turn a row into a wiring criterion: the implementation address the control is on, and the backend read that proves `next` happened (`GET /api/projects/{project_id}/draft -> .has_draft == true`). A row with calls and no `observe` cannot be checked by machine, and the lint says so.

While filling, read the handoff `README.md` once, end to end. Every sentence there that states a transition, a timer, a data fetch or a value, about a page in scope, gets a line under `readme_dispositions`: `adopted by <row>`, `overridden by <row> (<source>)`, or `out of scope (<page>)` when the statement is about a control on a page this run does not cover. This is what stops the README and the spec from saying two things about the same behaviour later.

### 4. Reverse sweep

Walk the map's decisions and the backend contract the other way: every decision line that a user can observe, and every operation in `openapi.json`, lands in at least one row's `source` or `calls`. One that does not is a `backend-only` row (the interface has no place for it) or is marked `no-ui` in `backend_without_ui` with one line saying why. In a scoped run, judge only the decisions and operations that belong to the pages in scope; the rest is not listed — a list of "out of scope" lines carries no judgement and hides the ones that do.

### 5. Write the gap list and stop for the person

Collect every row whose `gap` is `design-only` or `backend-only`, and every `reach` with no mechanism. Write them to `<scratch>/gap-list.md`: one entry each, with the row id, what the design shows, what the backend decides, the options, and the one you would take. Then hand the list to the person — this is the one judgement in this skill that is theirs, and it is a grilling, not a form. Expect a handful of entries, not dozens; dozens means a decision ticket was skipped upstream, and that goes back to the wayfinder map.

When the person is not reachable in this run (a batch, a test run), write the gap list and stop. The contract stays in the run's scratch directory with its `gap` values as they are; the lint reports each unresolved gap as an error, and that is the intended state. Nothing is written under `docs/specs/` until every gap is `aligned`.

Two things a gap list does not carry: an implementation that today does less than the decisions say (that is a finding for the ticket owning the code, note it in the run's notes), and an accessible name that the shipped product will render differently from the handoff (that is for `verify-ticket`'s parity run to catch, not for this file to predict).

### 6. Publish and lint

Write `docs/specs/<effort>/screen-contract.yaml`, then:

```
uv run python <this skill>/scripts/lint_contract.py <contract.yaml> <scratch>/skeleton.json [<openapi.json>]
```

Zero errors, or fix the file. Then write the **API contract** draft — one entry per distinct operation in `calls`, with the request and response fields the rows' `shows` and `on_failure` imply — to `<scratch>/api-contract.md`, for the `to-spec` skill to fold into the spec's Implementation Decisions.

## Re-runs

- The handoff package was re-downloaded: run steps 1 and 6 only. Triggers whose accessible name changed appear as lint errors on both sides; rebind them by hand, keep the row ids.
- A spec decision changed: edit the rows that cite it, rerun step 6, and put the changed rows through step 5 again.
- Row ids are never renumbered or reused. A retired behaviour loses its row; the id goes in `retired_ids` with one line saying when.

## Done when

`screen-contract.yaml` lints clean, every row's `gap` is `aligned`, every README statement about behaviour has a disposition, `api-contract.md` exists, and the person has answered every entry of the gap list — or, in a run without the person, the gap list is written and the run has said so.

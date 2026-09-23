---
name: write-screen-contract
description: Writes an interface's screen contract, `docs/specs/<effort>/screen-contract.yaml`. Use when a design package has landed and a spec is about to be written, when a design package was pulled again, or when a spec decision changed and the contract has to follow. Not for writing the spec itself.
---

# write-screen-contract — the screen contract between a design package and the backend

A design package says what the interface looks like and what it says. The backend decisions — a wayfinder map's, or a conversation's — say what the system does. Nothing in between says which control calls what, or which story page each design page is. This skill writes that file: the **screen contract**, `docs/specs/<effort>/screen-contract.yaml`. From then on the design package binds look and verbatim copy, the screen contract binds calls, shown values and transitions, and every downstream skill reads the two by that split.

The file's shape is in [references/screen-contract-format.md](references/screen-contract-format.md). Read it before step 2.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host.

`<scratch>` is a directory this run created (`mktemp`); write every path under it out in full. Some hosts refuse `uv run … $VAR`.

## Inputs

- The design package directory (`<package dir>` in the commands below) as the `design-pages` skill's pull wrote it. It is a read-only **baseline for look and copy**.
- The backend decisions. On a wayfinder map that is the map issue: its **Decisions so far** (in the issue body, not a comment) and, through each link, the closed tickets' resolution comments. Where a resolution names an ADR, a research file, a logic prototype's contract file or the domain doc, read that too. When the decisions were settled in conversation instead, those conclusions are the source — see **Decision sources**.
- The backend contract as it exists today: `openapi.json`. When the repository's own exporter writes one, use that; when it does not cover this product, dump it yourself — `uv run python <scripts>/dump_openapi.py <module>:<factory> <scratch>/openapi.json` calls a FastAPI app factory and writes its OpenAPI document. A server that has neither an exporter nor a FastAPI app factory (a standard-library server, for one) gets an `openapi.json` written by hand in `<scratch>`, describing exactly the routes, methods, fields and status codes its routing code implements.
- The effort name `<effort>`: the directory under `prototypes/` that holds `<package dir>`, which is also its directory under `docs/specs/`.

## Decision sources

A row's `source` may cite a wayfinder map's decision ticket, a spec section, an ADR, a domain document — or a conversation. An earlier spec that a decision ticket cites as its basis is citable too, as `#<n> <section>`: cite the decision ticket first, and the earlier spec for what no decision ticket covers.

## Steps

### 1. Declare the rendering inputs and extract the skeleton

Start `<scratch>/screen-contract.yaml` with the top-level `effort`, `baselines`, `locale`
and `viewports`. `locale` is the locale the design must render under: the product's own `<html lang>` when it has one, otherwise the user names it; the package itself names none. The package `README.md` lists each page's `$preview` size under
`## Viewport and size source`. `viewports` holds the size most pages share; a page drawn
at another size gets that size as its own `pages.<page>.viewports` (write the `pages`
entry now with that key; step 2 fills `mount` and `component`), so its scenes are
rendered and compared only there. `extract_skeleton.py` reads
`locale`, `viewports` and each page's own `viewports`; the rest establishes the
contract that the remaining steps fill. On a re-run the file is already there: keep
those keys and extract again.

```
uv run python <scripts>/extract_skeleton.py <package dir> <scratch>/skeleton.json --contract <scratch>/screen-contract.yaml
```

It drives a real browser, Chromium through Playwright; a machine without that browser installs it once with `uv run --with playwright python -m playwright install chromium`.

### 2. Declare pages, name components and split preconditions

For each page in `scenes.json`, write one `pages` entry: its **`mount`** — the short stable id the product will serve as the story page (`?page=<mount>`). `mount` is your declaration, not a derivation: a page holds several components' rows, and the one with most rows can be a shared control borrowed from another page. For a `Component · ` page also name the **`component`** the implementation will own it under — the repository's existing feature directory or module file when there is one, otherwise the page name; every row of that page's controls uses the same value. An `App · ` page is a whole-surface root and names no component.

Then a control whose behaviour differs by state gets one row per state — `precondition` is the column that tells them apart (`material: none` and `material: added` are two rows for the same button). Two cases that come up on every page:

- **A disabled state is a row.** The end user sees the control; the row says `calls: [none]` and `next: stay`.
- **A state the design package never shows** (the form complete, ready to submit) is still a row when the backend decisions reach it. Its `scenes` is `[]`; the lint reports it as a warning so the gap in the design package is on record.

A placeholder or hint that the accessibility tree folds into a name is an accessibility defect of the design package; record it in the run's notes. It is not a contract field.

### 3. Fill the behaviour columns and the scene declarations from the backend sources

For every row: `calls`, `shows`, `next`, `on_failure`, `source`, `gap`. The rules that decide each column are in the format reference; the ones people get wrong:

- `shows` names fields, never values: `balance@GET /api/wallet`, `title@GET /api/notes/{note_id}`. The literals in the page's data file under `data/` are seed data for tests, not copy, and so are their **counts**: a seed makes as many rows as the data file draws.
- `calls` names what the control does to the system: an HTTP operation as it appears in `openapi.json`, a non-HTTP form as the product issues it, or `none`. A control that only changes local view state is `none` and still a row; its `next` is the row or scene the end user is in afterwards. Where an operation under `proposed_operations` is new or changed and other products share this backend, say so in the run's notes, so the spec carries it.
- `source`: cite the Implementation Decisions subsection that carries a story's conclusion, not the story. Existing code (`code:<path>`) is a last resort, and a row whose sources are all `code:` and README is a `design-only` candidate: check the decisions again before marking it.

Then one `scenes` entry per scene of `scenes.json`: its `page`, and its `input` when the design page draws that scene from a data file in the package: read the page's script for the file it loads, the value it reads for the scene, and anything it sets on top; the format reference gives the shape.

### 4. Write each cross-component row from the App-page wiring

Read every `App · ` page's wiring: the callbacks and state passed between its `dc-import`s. Each place region A's action affects region B becomes one **cross-component row** on that App page. The keys, the region rule, and what the lint requires of `next` are in the format reference.

Every declared `App · ` page carries at least one cross-component row: the lint counts an App page as covered only through its own `app:` rows, and reports `page has no rows: App · <name>` otherwise. When an App page's wiring passes nothing from one region to another, that is a finding for the user: put it in the gap list of step 6.

### 5. Reverse sweep

Walk the decisions and the backend contract the other way: every decision line that an end user can observe, and every operation in `openapi.json`, lands in at least one row's `source` or `calls`. One that does not is a `backend-only` row (the interface has no place for it) or is one line under `backend_without_ui` saying why. The sweep covers every page of the package and every operation of `openapi.json`.

### 6. Write the gap list and stop for the user

Collect every row whose `gap` is `design-only` or `backend-only`, every scene the
user has judged cannot be captured, and every `App · ` page step 4 found no
cross-component row for. Write them to `<scratch>/gap-list.md`: one entry
each, with the row id or scene, what the design shows, what the backend decides, the
options, and the one you would take. Then hand the list to the user: this is the one
judgement in this skill that is theirs, and it is a grilling, not a form. Expect a
handful of entries, not dozens; dozens means a decision was skipped upstream,
and that goes back to the map or the conversation.

Two things a gap list does not carry: an implementation that today does less than the decisions say (that is a finding for the ticket owning the code, note it in the run's notes), and an accessible name that the shipped product will render differently from the design package (that is for the story judge to catch, not for this file to predict).

### 7. Lint and publish

1. Lint to zero errors, from inside the repository (a contract still in `<scratch>` finds `baselines.look` and `.mmw/target.json` through the directory the lint runs in):

   ```
   uv run python <scripts>/lint_screen_contract.py <scratch>/screen-contract.yaml <scratch>/skeleton.json [<openapi.json>]
   ```

2. Copy `<scratch>/screen-contract.yaml` to `docs/specs/<effort>/screen-contract.yaml`.

## Re-runs

A re-run makes a new `<scratch>`, copies `docs/specs/<effort>/screen-contract.yaml` into it as `<scratch>/screen-contract.yaml`, and runs step 1's command against that copy.

- The design package was pulled again and `pull-report.md` `改动分类` is `增删控件或改流转`: lint as step 7 says; edit only the rows those controls belong to. A control whose `data-ui` id is unchanged does not need its bindings rewritten. New disagreements go to the user.
- A spec decision changed: edit the rows that cite it, re-run step 7, and put the changed rows through step 6 again.
- Row ids are never renumbered or reused. A retired behaviour loses its row; record the
  decision in the spec, its decision ticket, or the conversation source.

## Done when

`screen-contract.yaml` lints clean, every row's `gap` is `aligned`, every scene of `scenes.json` has a declaration, every page has a `mount`, every `Component · ` page has a `component`, and the user has answered every entry of the gap list.

## Next

A contract written for a wayfinder map's alignment ticket resolves that ticket: return to the `wayfinder` skill to record the resolution; `to-spec` runs once the map is clear, as that skill says.

Otherwise:

- A contract written for the first time: the `to-spec` skill, which writes the spec this effort does not have yet.
- A contract changed by **Re-runs**: the `to-spec` skill's `references/revising-a-spec.md`, with the tickets already cut corrected against the new text.


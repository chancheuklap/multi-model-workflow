---
name: write-screen-contract
description: Produce the screen contract for an interface — one row per user-visible behaviour saying what the control calls, which backend field feeds each shown value, and what state follows, plus one declaration per design page (`mount`, `component`) and per scene (its page) — by aligning a pulled handoff package with the backend decisions of a wayfinder map. Use when a handoff package has landed and a spec is about to be written, when a handoff package was pulled again, or when a spec decision changed and the contract has to follow. Not for writing the spec itself (to-spec) or comparing pixels (verify-ticket).
---

# write-screen-contract — the screen contract between a handoff package and the backend

A handoff package says what the interface looks like and what it says. The wayfinder map's decisions say what the system does. Nothing in between says which control calls what, or which story page each design page is. This skill writes that file: the **screen contract**, `docs/specs/<effort>/screen-contract.yaml`. From then on the handoff package binds look and verbatim copy, the screen contract binds calls, shown values and transitions, and every downstream skill reads the two by that split.

The file's shape is in [references/screen-contract-format.md](references/screen-contract-format.md). Read it before step 2.

## Resolve `<scripts>` once

`<scripts>` in every command below is the `scripts/` directory next to this file. Resolve it from this file's own location. The path differs by machine and by host, and `install.sh` puts this skill wherever the host that gave it to you reads its skills from.

Every one of this skill's own scripts is run as `uv run python <scripts>/…`, never `python3`: `<scripts>/lint_screen_contract.py` carries a `# /// script` dependency block (`pyyaml>=6`), `<scripts>/extract_skeleton.py` carries its own (`playwright>=1.58`, `pyyaml>=6`), and `<scripts>/dump_openapi.py` imports the consuming repository's own application module. All three need the environment `uv` builds.

## Inputs

- The handoff package directory as `pull_design.py` of the `design-pages` skill wrote it: `README.md`, `pull-report.md`, `design-manifest.json`, the `.dc.html` pages, `styles/`, `data/`, `support.js`, `scenes.json`, and `vendor/` with the three scripts `support.js` loads. It is a **baseline for look and copy**; you never edit it.
- The wayfinder map issue: its **Decisions so far** and, through each link, the closed tickets' resolution comments. Where a resolution names an ADR, a research file, a logic prototype's contract file or the domain doc, read that too.
- The backend contract as it exists today: `openapi.json`. When the repository's own exporter writes one, use that; when it does not cover this product, dump it yourself — `uv run python <scripts>/dump_openapi.py <module>:<factory> <scratch>/openapi.json` calls the app factory and writes its OpenAPI document. A new project has no routes yet; the lint then marks calls `unverified` instead of failing them.
- The effort name: the name of the `docs/specs/<effort>/` directory the specs of this map live in. A map whose specs directory does not exist yet takes the map's title.
- The scope. A full run covers every page in `scenes.json`. A scoped run names the pages it covers; the reverse sweep and the README dispositions then stay inside those pages, and the lint reports the other pages as warnings.

Write every path in a command out in full. Some hosts refuse `uv run … $VAR`.

## Steps

### 1. Declare the rendering inputs and extract the skeleton

Start `<scratch>/screen-contract.yaml` with the top-level `effort`, `baselines`, `locale`
and `viewports`. `locale` is the locale the design must render under. `viewports`
contains the design size and a second, narrower size only when the package `README.md`
declares a minimum width. Never choose a stylesheet breakpoint: a viewport equal to one
compares two reflows and verifies nothing. The extractor reads only `locale` and
`viewports`; the other two fields establish the contract that the remaining steps fill.

```
uv run python <scripts>/extract_skeleton.py <handoff dir> <scratch>/skeleton.json --contract <scratch>/screen-contract.yaml
```

It drives a real browser: Playwright with Chromium has to be installed on this machine before the command will run at all.

It renders every scene in `scenes.json` at every declared viewport, through the same
`design_render.py` the story judge uses, under the contract's locale. It keeps every
visible `[data-ui]` control keyed by `(page, data-ui id)`, once even when the same id is
repeated in a list, with the scenes, text, interactivity and accessible names seen there.
The id is the row identity. Text and accessible names explain the rendered control; they
do not identify it. A control shown only by a value in the design page's `scene` prop
`out_of_scope` list is absent because `pull_design.py` does not put that value in
`scenes.json`.

### 2. Declare pages, name components and split preconditions

For each page in `scenes.json`, write one `pages` entry: its **`mount`** — the short stable id the product will serve as the story page (`?page=<mount>`), and carry as `data-screen` on the one element that *is* this page. `mount` is your declaration, not a derivation: a page holds several components' rows, and the one with most rows can be a shared control borrowed from another page. For a `Component · ` page also name the **`component`** the implementation will own it under — the repository's existing feature directory when there is one, otherwise the page name; every row of that page's controls uses the same value. An `App · ` page is a whole-surface root and names no component; only an `App · ` page may also name its **`route`**, the address journeys compare.

Then a control whose behaviour differs by state gets one row per state — `precondition` is the column that tells them apart (`material: none` and `material: added` are two rows for the same button). Two cases that come up on every page:

- **A disabled state is a row.** The user sees the control; the row says `calls: [none]` and `next` is the scene the user stays in.
- **A state the handoff never shows** (the form complete, ready to submit) is still a row when the backend decisions reach it. Its `scenes` is `[]`; the lint reports it as a warning so the handoff gap is on record.

A name the accessibility tree gets from a placeholder or a hint is copied all the same, and reported as an accessibility defect of the handoff in the run's notes.

### 3. Fill the behaviour columns and the scene declarations from the backend sources

For every row: `calls`, `shows`, `next`, `on_failure`, `source`, `gap`. The rules that decide each column are in the format reference; the ones people get wrong:

- `shows` names fields, never values: `balance@GET /api/wallet`, `path@ipc app:file:select`, `unit_price@RuntimePolicy` — not `1234`, and not a status code either. The literals in `data/fixtures.js` are seed data for tests, not copy — and so are their **counts**: a seed makes as many rows as the fixtures draw.
- `calls` names what the control does to the system: an HTTP operation as it appears in `openapi.json`, the target's non-HTTP form, or `none`. A control that only changes local view state is `none` and still a row; its `next` is the row or scene the user is in afterwards. An operation the decisions require and `openapi.json` lacks goes in the row as it will be named, and once more under `proposed_operations`; the API contract draft in step 6 describes it.
- `source` quotes where the behaviour was decided, in the shapes the format reference lists: a decision ticket, a spec section, an ADR, a domain-doc term, a README section. A story is an audit trail no worker reads; cite the Implementation Decisions subsection that carries its conclusion. Existing code counts only as a last resort, written `code:<path>`, and a row whose sources are all `code:` and README is a `design-only` candidate — check the decisions again before marking it.

Then one `scenes` entry per scene of `scenes.json`: its `page` only. Everything here is filled offline; nothing needs the product.

While filling, read the handoff `README.md` once, end to end. Every sentence there that states a transition, a timer, a data fetch or a value, about a page in scope, gets a line under `readme_dispositions`: `adopted by <row>`, `overridden by <row> (<source>)`, or `out of scope (<page>)` when the statement is about a control on a page this run does not cover. This is what stops the README and the spec from saying two things about the same behaviour later.

### 4. Reverse sweep

Walk the map's decisions and the backend contract the other way: every decision line that a user can observe, and every operation in `openapi.json`, lands in at least one row's `source` or `calls`. One that does not is a `backend-only` row (the interface has no place for it) or is marked `no-ui` in `backend_without_ui` with one line saying why. In a scoped run, judge only the decisions and operations that belong to the pages in scope; the rest is not listed — a list of "out of scope" lines carries no judgement and hides the ones that do.

### 5. Write the gap list and stop for the person

Collect every row whose `gap` is `design-only` or `backend-only`, and every scene a
person has judged cannot be captured. Write them to `<scratch>/gap-list.md`: one entry
each, with the row id or scene, what the design shows, what the backend decides, the
options, and the one you would take. Then hand the list to the person — this is the one
judgement in this skill that is theirs, and it is a grilling, not a form. Expect a
handful of entries, not dozens; dozens means a decision ticket was skipped upstream,
and that goes back to the wayfinder map.

When the person is not reachable in this run (a batch, a test run), write the gap list and stop. The contract stays in the run's scratch directory with its `gap` values as they are; the lint reports each unresolved gap as an error, and that is the intended state. Nothing is written under `docs/specs/` until every gap is `aligned`.

Two things a gap list does not carry: an implementation that today does less than the decisions say (that is a finding for the ticket owning the code, note it in the run's notes), and an accessible name that the shipped product will render differently from the handoff (that is for the story judge to catch, not for this file to predict).

### 6. Publish and lint

1. Write `docs/specs/<effort>/screen-contract.yaml`.
2. Lint to zero errors:

   ```
   uv run python <scripts>/lint_screen_contract.py docs/specs/<effort>/screen-contract.yaml <scratch>/skeleton.json [<openapi.json>]
   ```

   The lint asks the ui-acceptance skill's `target_config.py` for the state of the
   repository's `.mmw/target.json` (a warning while the contract ticket has not landed
   it; an error once the file is there and a field is still missing). It finds that
   skill's `scripts/` beside this one under `skills/`; `--tools` overrides that for a
   copy somewhere else. When a `story-parity.py --out` directory sits under the
   contract directory, the lint warns if a non-App page has a scene that inventory does
   not cover. `App · ` pages are outside that warning: the story judge's `--pages` takes
   only non-App mounts. Zero errors, or fix the file.

3. Write the **API contract** draft — one entry per distinct operation in `calls`, with the request and response fields the rows' `shows` and `on_failure` imply — to `<scratch>/api-contract.md`, for the `to-spec` skill to fold into the spec's Implementation Decisions.

## Re-runs

- The handoff package was pulled again: run steps 1 and 6. Text and accessible names
  may change without changing row identity; a changed or missing `data-ui` id is the
  control-inventory change to resolve.
- A spec decision changed: edit the rows that cite it, rerun step 6, and put the changed rows through step 5 again.
- Row ids are never renumbered or reused. A retired behaviour loses its row; record the
  decision in the spec or its decision ticket. The design renderer does not hide
  controls or change the handoff package.

## Done when

`screen-contract.yaml` lints clean, every row's `gap` is `aligned`, every scene of `scenes.json` has a declaration, every page has a `mount`, every `Component · ` page has a `component`, only `App · ` pages have a `route`, every README statement about behaviour has a disposition, `api-contract.md` exists, and the person has answered every entry of the gap list — or, in a run without the person, the gap list is written and the run has said so.

## Exit codes

`<scripts>/lint_screen_contract.py` prints its warnings first, one per line under `WARN  `, then its errors, one per line under `ERROR `, and last — whatever the outcome — one line `<n> errors, <n> warnings over <n> rows`. A warning never makes the run red.

- `0`: no errors. Warnings may still be there to read.
- `1`: at least one error. Fix the contract and run it again; zero errors is the bar step 6 sets.
- `2`: the call itself was wrong — the positional arguments were not the contract and the skeleton (with `openapi.json` optional third). It prints its own usage to stdout and reads nothing.

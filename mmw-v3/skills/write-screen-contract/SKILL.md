---
name: write-screen-contract
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Write screen contract

A design package says what the UI looks like and what it says. The backend decisions, a map's or a conversation's, say what the system does. Nothing in between says which control calls what, or which story page each design page is. The **screen contract**, `docs/specs/<effort>/screen-contract.yaml`, is that file. From then on the design package binds look and verbatim copy, the screen contract binds calls, shown values and transitions, and every reader takes the two by that split. The playbook Write the screen contract writes it; Write a spec, Cut tickets, the workers and reviewers of its tickets, the `ui-acceptance` skill's story oracle and boundary check, and the `verify-ticket` skill's `verify-ticket.py --lint` read it.

The file's shape and the rule for each key and column are in [references/screen-contract-format.md](references/screen-contract-format.md).

## Rules

- **Every row becomes a requirement a ticket owns.** Workers build from the row, not from the decisions behind it, and review holds them to its columns. A row that lints clean but rests on no decision is built and tested exactly as written. So where the decisions and the design are both silent about a column (most often `on_failure`), do not fill in the plausible default: ask the owner and cite the answer as `conversation <YYYY-MM-DD>`, or put the question on the gap list.
- **A row whose `gap` is not `aligned` is a decision nobody has made.** Every one goes on the gap list, which the owner settles; nothing reaches `docs/specs/` until they have.
- **Row ids are never renumbered or reused.** Tickets, tests and closed reviews name rows by id, so a reused or renumbered id silently points old evidence at a new behaviour. A retired behaviour loses its row, its id goes under `retired_ids`, and its decision is recorded in the spec, its decision ticket, or the conversation source.
- **The design package is read-only here.** A disagreement with it goes to the owner, and a change to it is made in Claude Design and pulled again.

## Scripts

Run them with `uv run` from inside the repository. Each needs a directory this run created with `mktemp` (`<scratch>`), with every path under it written out in full; some hosts refuse `uv run … $VAR`.

| Script | What it does |
| --- | --- |
| `scripts/extract_skeleton.py <package dir> <scratch>/skeleton.json --contract <scratch>/screen-contract.yaml` | Renders every scene of the package's `scenes.json` at the contract's `locale` and viewports, and writes the skeleton: one entry per design page and `data-ui` id, saying which scenes show the element, whether it is clickable or editable, where it is disabled, its displayed text, and its accessible names as explanation, not identity. It drives Chromium through Playwright, using the `ui-acceptance` skill's `scripts/design_render.py` found beside this skill (`--tools <dir>` points elsewhere); a machine without Chromium installs it once with `uv run --with playwright python -m playwright install chromium`. |
| `scripts/lint_screen_contract.py <screen-contract.yaml> <skeleton.json> [<openapi.json>]` | Holds the file to the format reference and to the skeleton: every key and column in the form the reference allows, every clickable or editable control and every design page with a row; with `openapi.json`, every operation in a row's `calls`, in `backend_without_ui` or in `proposed_operations`. Exit 0: no errors. Exit 1: the errors, one per line. Warnings, such as a row with `scenes: []`, never fail and stay on record, and so does every `retired_ids` entry, printed on every run. |
| `scripts/dump_openapi.py <module>:<factory> <scratch>/openapi.json` | Calls a FastAPI app factory and writes its OpenAPI document, for a product whose repository has no exporter of its own. |

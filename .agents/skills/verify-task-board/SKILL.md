---
name: verify-task-board
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Verify the task board

Prove a change to the task board (`mmw-v4/board/`) the way its owner sees it: this checkout's board server, in
Chromium, on this repository's real GitHub tickets, with a model configuration that is never `~/.mmw`.

## Read first

`npm exec --prefix tests/e2e/task-board -- e2e guide <topic>` (`writing-tests`, `running`, `debugging`); config
`tests/e2e/task-board/e2e.config.ts`; tests in `tests/e2e/task-board/`; the feature map in `features/` beside this file.

## Launch

The board has no back-end stack of its own: `server.py` is the whole back end, ticket state comes from GitHub
through this machine's `gh` (read only), and the model configuration from an `MMW_HOME`. Each e2e run starts its own
server through the environment tool, `python3 scripts/dev/board-instance.py serve --port {port}`, on a free port with
a fresh `MMW_HOME` seeded from `scripts/dev/board-fixtures/` (`models.json`, a stored `catalog.json`, and the host
catalog `host-catalog.json` it answers instead of asking the claude and codex CLIs). The runner starts it; ready is
`GET /api/settings` answering, about 0.2 seconds.

`product` is the board. `design` is the same command with `--prototype <module under efforts/>`, which mounts that
prototype over the page it replaces (`MMW_BOARD_PROTOTYPE`); run it only while writing or maintaining tests in the day.

The e2e packages live in `tests/e2e/task-board/package.json`, because the repository has no package manager. CHECK
line for a ticket's acceptance file `<file>` (relative to `tests/e2e/task-board/`):

```bash
npm ci --prefix tests/e2e/task-board --silent && npm exec --prefix tests/e2e/task-board -- e2e run <file> --config tests/e2e/task-board/e2e.config.ts --target product --trace on --output .e2e/<test file name>
```

To look at this checkout by hand: `python3 scripts/dev/board-instance.py up [--prototype <module>]` prints
`READY <url>`; `down` stops it (the `task-board-dev` skill).

## Doctor

Run only to investigate a failure. `gh auth status`; `npm exec --prefix tests/e2e/task-board -- e2e list --config
tests/e2e/task-board/e2e.config.ts`, which loads the config without starting anything; then the smoke test:
`npm exec --prefix tests/e2e/task-board -- e2e run smoke.e2e.ts --config tests/e2e/task-board/e2e.config.ts --target
product --trace on --output .e2e/doctor`. Exit 0 means the server starts, reads this repository from GitHub, and the
settings sheet opens. The server's output is in `tests/e2e/task-board/.e2e/logs/<target>.log`.

Known local failures:

| Symptom | Cause | Do |
| --- | --- | --- |
| `design` fails where `product` passes on a feature nobody changed | The prototype replaces that page and has not caught up with it | Compare with the prototype's leaf `README.md`; a missing behaviour goes to the prototype, not the test |
| `serve` exits at once with `no prototype module` | `--prototype` names a path that is not in this checkout | Pass the path relative to the repository root |

## Drive

Tests under `tests/e2e/task-board/` start signed out; the board has no accounts. Find elements by role and visible
name: the settings selects are `<agent> 的 host|model|effort`, the gear is the button `本机配置`. `settings.e2e.ts` is
the worked example. A state the local back end cannot reach (a catalog read that failed, a saved model the catalog no
longer lists) is reached with `browser.route` on `GET /api/settings`. Check locators by running the test and reading its
`trace.md`; write a new feature's test against `design` first. To walk a feature without a test, use the control-ui
skill on an instance from `board-instance.py up`.

## Evidence

Every run writes `tests/e2e/task-board/.e2e/<output>/report.json`; `--trace on` keeps
`tests/e2e/task-board/.e2e/<output>/results/<test>/trace.md` for every test; `app.screenshot('<name>')` saves
`results/<test>/attempt-1/screenshots/<nnn>-<name>.png`. A run clears its own `--output` directory only, so give each
proof its own.

Proof standards: drive the real user path, not internal setters or test-only endpoints; capture the action and the
resulting state the user sees; mock only at a production boundary that already isolates the external system (GitHub's
answer, a host CLI's catalog). What is stored is proven by the ticket's back-end tests, not by e2e.

## Cleanup

The runner stops the server it started and `serve` deletes its `MMW_HOME`. An instance from `board-instance.py up` stays
until `down`. Never delete `tests/e2e/task-board/.e2e/`.

## Rules

- Never point a run at `~/.mmw` or the machine's own board on port 47100 and up: `MMW_HOME` is always the tool's.
- Never write to GitHub; the board only reads it.
- Do not change board code to make a test pass; a precondition the instance lacks goes in the feature's `Gotchas`.

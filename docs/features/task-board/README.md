# Task board

The task board is the local page for reading this repository's maps, specs, and tickets, and for editing the host, model, effort, and runner each role starts on.

## Baseline preconditions

- Hold this worktree's lease. Run `python3 ~/.agents/skills/ui-acceptance/scripts/lease.py run -- python3 .mmw/harness/target.py start`.
- Run `python3 .mmw/harness/target.py discover` the same way. It prints the origin. The page is on 127.0.0.1 at that lease port.
- The harness puts `.mmw/harness/bin` first on `PATH` and uses a private `MMW_HOME`. A write from the page stays in that copy.
- Leave the board that the `com.mmw.board` LaunchAgent keeps. This map drives the leased copy only.

## Driving conventions

- Find a control by its `data-ui` value. Those values are the `trigger` fields of `efforts/task-board/screen-contract.yaml`.
- The page regions are the top bar `顶栏`, the left column `任务列表`, the canvas `画布`, and the detail column `详情`. The settings sheet `本机配置` is a dialog over them.
- Start from the leased board unless a feature's own preconditions name another state.
- Take the origin from `discover`. The page token is the `content` of `meta[name="mmw-page-token"]`.

## Proof and skip reporting

- A journey that fails writes `screenshot.png`, `trace.zip`, `console.txt`, and `requests.txt` under `MMW_EVIDENCE_DIR`, from `.mmw/journeys/evidence.py`.
- Name the feature file and the entry you used with that evidence.
- Report a path you could not reach with the command you ran and the precondition that failed.
- A path you did not take is not verified by a different path.

## Feature entry contract

Read `How a feature is divided` and `A feature file` in `mmw-v3/skills/mmw-mode/references/feature-map.md`.

One rule is true of this product. Each sub-feature is one row of `efforts/task-board/screen-contract.yaml`, and its `source` is `row:<id>`. A prefix `topbar`, `tasks`, `canvas`, `detail`, or `settings` is the first clue to the feature file. A `board` row is that same action on the whole page, and it sits with the feature the user finishes. Opening the board has no row. A behavior with no interface is not in this map.

## Features

- [Open the board](./open-board.md) covers opening this repository's task board.
- [See what needs you](./needs-you.md) covers the lamp counts, refresh, and the jump to an orange ticket.
- [Pick a task](./pick-task.md) covers choosing a map or a spec in the left column.
- [Browse the canvas](./canvas.md) covers the issue tree, expand and collapse, and zoom.
- [Read the detail](./read-detail.md) covers opening a ticket, a spec, a map, or a decision, and following a link from it.
- [Change settings](./settings.md) covers the settings sheet and saving the runner, host, model, and effort.

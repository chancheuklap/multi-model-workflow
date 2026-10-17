---
name: task-board-dev
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Run the task board from this checkout

`scripts/dev/board-instance.py` runs this checkout's `mmw-v4/board/server.py` on 127.0.0.1 with its own `MMW_HOME`,
never `~/.mmw`, so trying, debugging or testing a change never touches the machine's configuration or its installed
board (the `com.mmw.board` LaunchAgent, ports from 47100).

| Command | Does |
| --- | --- |
| `python3 scripts/dev/board-instance.py up` | Starts this checkout's instance, or reuses a live one; prints `READY <url>`. `MMW_HOME` is `.board-dev/home/`, kept across restarts; `--fresh` reseeds it from `scripts/dev/board-fixtures/` |
| `… up --prototype <module>` | The same with a prototype under `efforts/` mounted (`MMW_BOARD_PROTOTYPE`) |
| `… up --real-catalog` | Asks this machine's claude and codex CLIs for their model catalogs instead of `board-fixtures/host-catalog.json` |
| `python3 scripts/dev/board-instance.py down` | Stops this checkout's instance |
| `python3 scripts/dev/board-instance.py serve --port N` | Foreground, a fresh `MMW_HOME` deleted on exit; the e2e runner starts this |

Every `up` first stops the instances of checkouts that no longer exist (registry `~/.local/state/mmw-board-dev/`).
Ticket state comes from GitHub through this machine's `gh`, read only. The server exits when a board `.py` file changes
(`codeversion.py`); run `up` again. Page files are read per request: reload the browser. The log is
`.board-dev/server.log`.

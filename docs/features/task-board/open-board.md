# Open the board

The owner opens this repository's task board and sees its maps, specs, and tickets.

## Sub-features

Opening the board has no screen-contract row. The rows live in the other five feature files.

## How to get to it (user POV)

- From this repository, `dispatch.sh board` opens the task board.

## Driving it

Preconditions: this worktree holds its lease. `python3 ~/.agents/skills/ui-acceptance/scripts/lease.py run --product task-board -- python3 .mmw/task-board/harness/target.py start` has exited 0. `python3 .mmw/task-board/harness/target.py discover`, run the same way, has printed the origin.

- Open that origin in a browser. `[data-board-root]` is visible. The top bar names task board and this repository. Maps & specs lists map #900, Automation task. The canvas shows that map and spec #901, Automation spec, collapsed.

## Gotchas

A run wastes its time, or reports a pass it did not earn, in these cases.

- Leave the board that `com.mmw.board` keeps running. It is another process, and its page looks like this one.
- The harness `gh` answers only the calls in `.mmw/task-board/harness/github/responses.json`. An unlisted call exits 2.
- `python3 ~/.agents/skills/ui-acceptance/scripts/journey.py run task-board/smoke` checks that the opened page has one visible board root and at least one task. `mmw-v3/tests/board/test_supervisor.py` and `test_server.py` check the process that serves it. Those checks have no sub-feature, because this feature has no row.

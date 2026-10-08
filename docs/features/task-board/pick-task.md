# Pick a task

The owner selects one map, or one spec that no open map holds, and the board shows that tree.

## Sub-features

- `tasks.pick` Choosing a row in Maps & specs selects that map or spec and shows its lamp and its landed count.
  source: row:tasks.pick
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_tasks_rows.TasksRowsTest.test_tasks_pick

- `board.pick-task` Choosing a row in Maps & specs shows that map or spec on the canvas.
  source: row:board.pick-task
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_pick_task

## How to get to it (user POV)

- Maps & specs, the left column, is on the board as soon as it opens.

## Driving it

Preconditions: the board is open on the origin `discover` printed, as Open the board describes.

- Click `[data-ui="任务列表.task"]` for map #900. The canvas keeps that map and its collapsed spec. The harness fixture has one row, so a second map is not there to select.

## Gotchas

A run wastes its time, or reports a pass it did not earn, in these cases.

- The column title is Maps & specs. A selected map's detail eyebrow is Map. A selected spec's detail eyebrow is Spec.

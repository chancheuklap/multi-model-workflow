# See what needs you

The owner reads the four lamp counts, refreshes that read, and jumps to the next ticket that needs them.

## Sub-features

- `topbar.refresh` Refresh reads this repository again and updates the four lamp counts and the read-state line.
  source: row:topbar.refresh
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_topbar_rows.TopbarRowsTest.test_topbar_refresh

- `board.refresh-all` Refresh on the open board reads again and repaints the left column from that read.
  source: row:board.refresh-all
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_refresh_all

- `topbar.needs-you-none` With no orange lamp, Needs you stays disabled and the count stays 0.
  source: row:topbar.needs-you-none
  check: node --test mmw-v3/tests/board/topbar.test.mjs

- `topbar.needs-you-jump` Needs you opens the next ticket whose lamp is orange.
  source: row:topbar.needs-you-jump
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_topbar_rows.TopbarRowsTest.test_topbar_needs_you_jump

- `board.jump-needs-you` Needs you on the open board selects that ticket on the canvas and opens it in the detail column.
  source: row:board.jump-needs-you
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_jump_needs_you

## How to get to it (user POV)

- The top bar is on the board as soon as it opens.

## Driving it

Preconditions: the board is open on the origin `discover` printed, as Open the board describes.

- Click `[data-ui="顶栏.refresh"]`. The page sends `POST /api/board/refresh`. The read-state line still names the read time. A refresh that falls in the same minute keeps the same clock text.
- Read `[data-ui="顶栏.needs-you"]`. On the harness fixture the count is 0 and the button is disabled, so the jump is not taken. The orange-lamp jump is the story check on `topbar.needs-you-jump`.

## Gotchas

A run wastes its time, or reports a pass it did not earn, in these cases.

- The story checks for this feature pin the browser to `Asia/Hong_Kong` before they read the read-state line. The example clock is Hong Kong wall time. A browser left in another zone fails `test_topbar_refresh`.
- Needs you with a count of 0 does not navigate. The button is disabled.

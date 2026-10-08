# Read the detail

The owner opens one ticket, spec, map, or decision and reads its state, its events, and the issues it links to.

## Sub-features

- `detail.close` Close clears the detail column back to the empty prompt.
  source: row:detail.close
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_close

- `detail.open-github` GitHub on a ticket opens that issue in a new tab and leaves the detail column as it is.
  source: row:detail.open-github
  check: node --test --test-name-pattern 'GitHub uses a new tab and does not call the API client' mmw-v3/tests/board/detail.test.mjs

- `detail.open-github-summary` GitHub on a map, a spec, or a decision opens that issue in a new tab and leaves the column as it is.
  source: row:detail.open-github-summary
  check: none: no test clicks 详情.github. detail.test.mjs only asserts the spec button is present.

- `detail.goto-origin-spec` The spec link on a ticket opens that spec in the detail column.
  source: row:detail.goto-origin-spec
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_origin_spec

- `detail.goto-origin-map` The map link on a ticket or a spec opens that map in the detail column.
  source: row:detail.goto-origin-map
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_origin_map

- `detail.goto-blocker` A blocker that is a ticket in this tree opens that ticket in the detail column.
  source: row:detail.goto-blocker
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_blocker

- `detail.goto-decision-blocker` A blocker that is a decision opens that decision in the detail column.
  source: row:detail.goto-decision-blocker
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_decision_blocker

- `detail.blocker-unknown` A blocker that is not in this tree reads unknown, and a click stays on the current detail.
  source: row:detail.blocker-unknown
  check: node --test --test-name-pattern 'ticket numbers in the panel call onGoto, unknown rows do not' mmw-v3/tests/board/detail.test.mjs

- `detail.goto-blocked` A later ticket that this one blocks opens in the detail column.
  source: row:detail.goto-blocked
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_blocked

- `detail.goto-spec-row` A spec row in a map's detail opens that spec.
  source: row:detail.goto-spec-row
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_spec_row

- `detail.goto-decision-row` A decision row in a map's detail opens that decision.
  source: row:detail.goto-decision-row
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_decision_row

- `detail.goto-ticket-row` A ticket row in a spec's detail opens that ticket.
  source: row:detail.goto-ticket-row
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_goto_ticket_row

- `detail.open-event-block` Opening an event block shows the events in that phase.
  source: row:detail.open-event-block
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_open_event_block

- `detail.close-event-block` Closing an event block hides the events in that phase.
  source: row:detail.close-event-block
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_close_event_block

- `detail.open-event` Opening one event shows the record behind its display name.
  source: row:detail.open-event
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_open_event

- `detail.close-event` Closing that event hides the record again.
  source: row:detail.close-event
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_detail_rows.DetailRowsTest.test_detail_close_event

- `board.open-ticket` Opening a ticket card also opens that ticket in the detail column.
  source: row:board.open-ticket
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_open_ticket

- `board.open-map` Opening a map card opens the map summary in the detail column.
  source: row:board.open-map
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_open_map

- `board.open-spec` Opening a spec card opens the spec summary in the detail column.
  source: row:board.open-spec
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_open_spec

- `board.open-decision` Opening a decision card opens that decision in the detail column.
  source: row:board.open-decision
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_open_decision

- `board.goto-origin` Following the origin link selects that card on the canvas and opens it in the detail column.
  source: row:board.goto-origin
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_goto_origin

- `board.goto-blocker` Opening a blocker selects that ticket on the canvas and opens it in the detail column.
  source: row:board.goto-blocker
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_goto_blocker

- `board.goto-blocked` Opening a ticket this one blocks selects that card on the canvas and opens it in the detail column.
  source: row:board.goto-blocked
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_goto_blocked

- `board.goto-spec-row` Opening a spec row selects that container on the canvas and opens the spec in the detail column.
  source: row:board.goto-spec-row
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_goto_spec_row

- `board.goto-decision-row` Opening a decision row selects that decision on the canvas and opens it in the detail column.
  source: row:board.goto-decision-row
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_goto_decision_row

- `board.goto-ticket-row` Opening a ticket row selects that ticket on the canvas and opens it in the detail column.
  source: row:board.goto-ticket-row
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_goto_ticket_row

- `board.close-detail` Closing the detail column also clears the canvas selection.
  source: row:board.close-detail
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_board_rows.BoardRowsTest.test_board_close_detail

## How to get to it (user POV)

- Open a ticket card, a container card, or a decision card on the canvas.
- Needs you, when its count is not 0, opens the next orange ticket in the detail column.

## Driving it

Preconditions: the board is open on map #900, and spec #901 is expanded, as Browse the canvas describes.

- Click `[data-ui="画布.ticket-card.open"]` for ticket #902. The detail eyebrow reads TICKET and the title is Automation ticket. Click `[data-ui="详情.head.github"]`. A new tab opens `https://github.com/chancheuklap/multi-model-workflow/issues/902`. The detail column stays on the ticket.
- Click `[data-ui="详情.origin.link"]`, which reads spec #901. The eyebrow becomes SPEC and the title becomes Automation spec. `[data-ui="详情.github"]` reads 在 GitHub 打开 #901 ↗.
- Click `[data-ui="画布.container-card.open"]` on map #900. The eyebrow reads MAP and the title is Automation task. `[data-ui="详情.github"]` reads 在 GitHub 打开 #900 ↗.
- Press Esc, or click `[data-ui="详情.head.close"]`. `[data-ui="详情.root"]` is gone.

## Gotchas

A run wastes its time, or reports a pass it did not earn, in these cases.

- GitHub opens a new browser tab. A driver that only watches the board page does not see that tab.
- The harness ticket #902 has no blocker and no event history. Blocker, unknown, and event-block behavior is on the story checks, not on this fixture.
- Esc closes the detail column.

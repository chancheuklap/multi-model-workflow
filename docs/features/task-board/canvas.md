# Browse the canvas

The owner looks through one map or spec as a tree of cards, expands a container, and zooms.

## Sub-features

- `canvas.open-ticket` Opening a ticket card selects that card on the canvas.
  source: row:canvas.open-ticket
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_open_ticket

- `canvas.open-container` Opening a container card selects that map or spec on the canvas.
  source: row:canvas.open-container
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_open_container

- `canvas.expand-container` Expanding a container lays its children out in a column to its right.
  source: row:canvas.expand-container
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_expand_container

- `canvas.collapse-container` Collapsing a container hides that column.
  source: row:canvas.collapse-container
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_collapse_container

- `canvas.open-decision` Opening a decision card selects that card on the canvas.
  source: row:canvas.open-decision
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_open_decision

- `canvas.zoom-in` Zoom in enlarges the tree.
  source: row:canvas.zoom-in
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_zoom_in

- `canvas.zoom-out` Zoom out shrinks the tree.
  source: row:canvas.zoom-out
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_zoom_out

- `canvas.fit` Fit scales the tree so the whole of it is in view.
  source: row:canvas.fit
  check: cd mmw-v3/tests/board && uv run --quiet --with playwright python -m unittest test_canvas_rows.CanvasRowsTest.test_canvas_fit

## How to get to it (user POV)

- Select a map or a spec in Maps & specs. Its tree is the canvas.

## Driving it

Preconditions: the board is open on map #900, as Pick a task describes.

- Click `[data-ui="画布.container-card.expand"]` on spec #901. Ticket #902, Automation ticket, appears. Click the same control again and the ticket is gone.
- Click `[data-ui="画布.zoom.in"]`. `[data-ui="画布.zoom.level"]` moves from 100% to 120%. Click `[data-ui="画布.zoom.out"]` and the level returns to 100%. Click `[data-ui="画布.zoom.fit"]` while the tree already fits and the level stays 100%.

## Gotchas

A run wastes its time, or reports a pass it did not earn, in these cases.

- A collapsed container hides its children. Open a ticket only after the container is expanded.
- Zoom stops at 30% and at 160%. Fit does not change the level when the tree already fits.
- Keyboard F also fits the tree.

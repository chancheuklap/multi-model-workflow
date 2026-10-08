# Open

The user opens the product and sees it ready.

## Sub-features

- `open-from-command` The user runs the open command and the board appears.
  source: row:demo.open
  check: bash tests/guard.sh
- `open-from-spec` The user follows the numbered section.
  source: #893 §2
  check: node tests/guard.js
- `open-from-ticket` The user follows the ticket.
  source: #901
  check: python -m unittest tests.test_guard.GuardTests.test_opens
- `open-from-record` The user follows the decision record.
  source: ADR 0038
  check: cd tests && python -m unittest test_guard.GuardTests.test_opens
- `open-existing` The user could already open it.
  source: existing 2026-10-08
  check: journey.py run smoke

## How to get to it (user POV)

- Run the open command.

## Driving it

Preconditions:

- The product is installed.

## Gotchas

- A second open reuses the same port.

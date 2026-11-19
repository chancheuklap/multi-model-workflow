# Save

The user saves a change and sees it kept.

## Sub-features

- `save-change` The user saves and the value stays.
  source: #901
  check: bash tests/guard.sh

## How to get to it (user POV)

- Choose save.

## Driving it

Preconditions:

- A change is pending.

## Gotchas

- Saving twice keeps the second value.

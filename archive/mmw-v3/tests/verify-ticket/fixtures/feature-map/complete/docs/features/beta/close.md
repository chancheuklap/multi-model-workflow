# Close

The user closes the product and sees it gone.

## Sub-features

- `close-product` The user closes the product.
  source: ADR 0008
  check: bash tests/guard.sh

## How to get to it (user POV)

- Choose close.

## Driving it

Preconditions:

- The product is open.

## Gotchas

- Closing discards an unsaved change.

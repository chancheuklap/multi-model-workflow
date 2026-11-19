# Pin a note
Route: /notes
Tests: pin-note.e2e.ts

Pin a note to keep it available at the top of the note list.

## Sub-features

- Pin a saved note with its `Pin <title>` button.
- See its pinned status and the action to unpin it.

## How to get to it (user POV)

Open `/notes`, create a note, and choose `Pin <title>` on that note.
No account is required.

## Driving it with e2e

`pin-note.e2e.ts` creates `Release checklist` through `New note`, the `Title`
and `Body` labels, and `Save note`. It asserts the note exists before looking
for `Pin Release checklist`, so the base fails on the missing pin control.
Both targets follow these same steps at `/notes` and capture `pinned-note`.

## Proof

The `Release checklist` heading is visible, `Pin status` reads `Pinned`, and
`Unpin Release checklist` is visible after pinning the note.

## Gotchas

- The product must already support creating notes. If that precondition fails,
  report it here rather than weakening the pin test.

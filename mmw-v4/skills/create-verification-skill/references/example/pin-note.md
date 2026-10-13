# Pin a note
Route: /notes
Tests: pin-note.e2e.ts
<!-- .agents/skills/verify-notes/features/pin-note.md -->

Pin a note to keep it available at the top of the note list.

## Sub-features

- Pin a saved note with its `Pin <title>` button.
- Keep the pinned note after a page refresh.

## How to get to it (user POV)

Open `/notes`, create a note, and choose `Pin <title>` on that note.
No account is required.

## Driving it with e2e

`pin-note.e2e.ts` creates `Release checklist` through `New note`, the `Title`
and `Body` labels, and `Save note`. It asserts the note exists before looking
for `Pin Release checklist`, so the base fails on the missing pin control.
The design target opens `notes-pinned.html` through `helpers/design.ts`.
Both targets assert the same heading, `Pin status`, and unpin button.

## Proof

The `Release checklist` heading is visible, `Pin status` reads `Pinned`, and
`Unpin Release checklist` is visible. The same assertions hold after refresh.
On the product target, that refresh proves the pin survived storage.

## Gotchas

- The design page demonstrates the drawn pinned state, not stored product data.
- The product must already support creating notes. If that precondition fails,
  report it here rather than weakening the pin test.

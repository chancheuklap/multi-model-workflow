---
name: principle-read-before-you-conclude
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Read Before You Conclude

Read enough of a file to be sure of what you say about it, and read it before you change it.

**Why:** A claim about a part you did not read is a guess, and an edit to a part you did not read can break what you never saw.

**Rule:** decide how much to read from the file's size and what you need from it.
- A file you are about to edit, or reason about in detail, is read whole, in consecutive chunks if it does not fit in one call.
- A file you consult for one fact, or a generated, vendored, or log file, is read as far as the question needs.
- When a conclusion depends on a part you did not read, say so in the reply. A conclusion drawn from an unread part is inferred, not verified (**principle-prove-it-works**).

Distinct from **principle-prove-it-works**, which checks that an output works. This one checks that what you say about a file rests on what you read of it.

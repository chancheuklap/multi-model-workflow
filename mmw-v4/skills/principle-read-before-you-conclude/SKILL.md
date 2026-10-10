---
name: principle-read-before-you-conclude
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Read Before You Conclude

Read enough of a file to be sure of what you say about it, and read it before you change it.

**Pattern:**
- Decide from the file's size and what you need from it how much to read.
- A file you are about to edit or reason about in detail is read whole, in consecutive chunks if it does not fit in one call.
- A file you consult for one fact, or a generated, vendored, or log file, is read as far as the question needs.
- When your conclusion depends on a part you did not read, say so in the reply. A conclusion drawn from an unread part is inferred, not verified, and carries that label (mmw-mode `## Writing the reply`).

Distinct from **principle-prove-it-works**, which checks an output against the real thing. This governs what you read before you speak about a file. A subagent can read a large file whole and report, per **principle-guard-the-context-window**; the rule binds whoever states the conclusion.

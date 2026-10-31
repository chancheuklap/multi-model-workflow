---
name: principle-read-before-you-conclude
description: Use before making a claim about a file or changing it. Read the source needed to justify the claim, read edited files in full, and label conclusions that depend on unread material as inferred.
---

# Read Before You Conclude

Read enough of a file to be sure of what you say about it, and read it before you change it.

**Pattern:**
- Decide from the file's size and what you need from it how much to read.
- A file you are about to edit or reason about in detail is read whole, in consecutive chunks if it does not fit in one call.
- A file you consult for one fact, or a generated, vendored, or log file, is read as far as the question needs.
- When your conclusion depends on a part you did not read, say so in the reply. A conclusion drawn from an unread part is inferred, not verified, and is labelled `inferred` in the same sentence.

**In a diff:**

- Before judging a hunk, read beyond it: callers, callees, guards upstream, type definitions, sibling modules, and why the code exists, until you can say whether the change addresses the right layer. A finding that rests on code you did not read is labelled `inferred`.

Distinct from **principle-prove-it-works**, which checks an output against the real thing. This governs what you read before you speak about a file. Where the step you follow sends a subagent to read a large file whole and report, per **principle-guard-the-context-window**, the rule still binds whoever states the conclusion.

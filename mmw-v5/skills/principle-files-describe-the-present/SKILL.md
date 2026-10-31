---
name: principle-files-describe-the-present
description: Use when writing or editing code, comments, documentation, or other files. Describe the subject as it exists now and reserve history for files whose subject is a decision or change.
---

# Files Describe the Present

A file describes its subject, never its own history.

**Pattern:**
- Whatever you write, a new file or an edit, carries only what is true of the subject now, in the form its author would give it writing it fresh today. A reader with no knowledge of any previous version sees nothing about what was removed, changed, added, or ruled out.
- What changed and why belongs in your reply and in the commit message. The file itself has no memory.
- The exception is a file whose subject is a decision or a change: an ADR, a changelog, a merge-note, a commit message, or a ticket comment records the alternatives considered, what superseded what, and why, because that record is the subject.
- This rule is about what the file says, not how you edit it. When it will not affect the end result, surgically edit the file rather than rewrite the entire thing.

**In a diff:**

- A comment that restates the code or narrates steps (`// Phase 1: add cards`): delete it; only a non-obvious why stays (**mmw-mode** `## Comments`).
- A file, comment or docstring that says what changed ("now", "previously", "no longer") instead of what is true: rewrite it as what is true.

Distinct from **mmw-mode** `## Comments`, which keeps a code comment only for a non-obvious why. This covers the whole file, prose and code alike.

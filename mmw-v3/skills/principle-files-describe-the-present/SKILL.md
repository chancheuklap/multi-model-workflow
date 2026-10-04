---
name: principle-files-describe-the-present
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Files Describe the Present

A file describes its subject, never its own history. Whatever you write, a new file or an edit, carries only what is true of the subject now, in the form its author would give it writing it fresh today.

**Why:** A reader with no knowledge of any previous version should see nothing about what was removed, changed, added, or ruled out. History in a file is text the reader must skip to find what is true, and it goes stale the next time the file changes.

**Rule:**
- What changed and why belongs in the reply and in the commit message. The file itself has no memory.
- The exception is a file whose subject is a decision or a change: an ADR, a changelog, a provenance registry, a commit message, or a ticket comment records the alternatives considered, what superseded what, and why, because that record is the subject.
- The rule is about what the file says, not how you edit it. When it will not affect the end result, edit the file surgically rather than rewrite the whole thing.

For a code comment, keep only the non-obvious why the code cannot show (mmw-mode `## Comments`).

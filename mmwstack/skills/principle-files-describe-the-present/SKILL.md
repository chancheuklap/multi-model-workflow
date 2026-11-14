---
name: principle-files-describe-the-present
description: "Apply when writing or editing code, comments, or documentation. Describe the subject as it is now. Put change history in a file whose subject is the change, such as an ADR or changelog."
---

# Files Describe the Present

A file describes its subject, never its own history.

**Pattern:**
- Whatever you write, a new file or an edit, carries only what is true of the subject now, in the form its author would give it writing it fresh today. A reader with no knowledge of any previous version sees nothing about what was removed, changed, added, or ruled out.
- What changed and why belongs in your reply and in the commit message. The file itself has no memory.
- The exception is a file whose subject is a decision or a change: an ADR, a changelog, a commit message, or a decision log records the alternatives considered, what superseded what, and why, because that record is the subject.
- This rule is about what the file says, not how you edit it. When it will not affect the end result, surgically edit the file rather than rewrite the entire thing.

A code comment stays only for a non-obvious why. This covers the whole file, prose and code alike.

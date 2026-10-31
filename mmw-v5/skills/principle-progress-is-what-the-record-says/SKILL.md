---
name: principle-progress-is-what-the-record-says
description: Use when resuming, taking over, or recovering work after interruption or context compression. Reconstruct the current step from tickets, events, commits, maps, and resume records rather than session memory.
---

# Progress Is What the Record Says

Where you are is what the record says, not what this session remembers.

**Why:** A session's own memory is not on the record. It ends with the session, a compaction or an interrupted resume can drop parts of it, and no other agent can read it.

**Pattern:**
- The record is what the work leaves where others can read it: the ticket and its events, the commits on the branch, the map and its tickets, a resume note, the state an engine keeps.
- Commits an earlier session left on the branch, including a `wip` commit of what it had not committed, are this work. Carry on from them.
- Do not resume from session memory, and do not keep a second log of what you already tried beside the record.

Distinct from **principle-make-operations-idempotent**, which designs an operation to converge however often it runs. This says how a session that picks work up finds out where it is.

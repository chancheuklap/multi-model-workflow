---
name: principle-progress-is-what-the-record-says
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Progress Is What the Record Says

Where a piece of work stands is what its record says: the events on its ticket and spec, the commits on its branch, the state its script keeps. It is never what this session remembers. Before acting on work a record tracks, read the record and act from the step it puts you at.

**Why:** A session ends, is compacted, or is replaced by another, and scripts and other sessions move the work while it is not looking. Progress read from memory acts on a state that may no longer hold: a step is done twice, a ticket is landed twice, a stage is skipped. Progress kept only in a session is lost with it.

**Pattern:**
- On starting, waking, or taking over work, read its record first and take the step it names: a ticket's `RESUME:` line, a night's `status` and the spec's events.
- When the record and your memory disagree, the record wins. When the record cannot be read, read it again once it answers; do not fill the gap from memory.
- Keep no second log of what you already did beside the record. What you did goes where the record keeps it: an event, a comment on the ticket, a commit.
- The record says where the work is, not whether it is right: a result it reports as done is still checked against the product (**principle-prove-it-works**).

Distinct from **principle-prove-it-works**, which asks whether a result is true; this one asks where the work stands.

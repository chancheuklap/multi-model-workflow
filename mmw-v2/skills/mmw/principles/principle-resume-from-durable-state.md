---
name: principle-resume-from-durable-state
description: "Apply when a session starts, wakes, is compacted, or picks up work already begun. Read where you are from the durable record, not from what the session remembers, and do not redo what the record shows as done."
---

# Resume from durable state

Where you are is what the durable record says, not what this session remembers. The durable record is the events on a ticket, the tracker, the commits or an engine's state; session memory is a copy of it that can be lost. When you pick work up again, read the record and carry on from it, and do not redo what it shows as done.

**Stop:** Do not keep a second log of what you already tried.

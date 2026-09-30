---
name: principle-human-steps-stay-human
description: "Apply when a step can only be taken by a person. Set the step apart and hand it to that person; do not take it for them, and do not report it as done."
---

# Human steps stay human

A step only a person can take is set apart and handed to that person. An agent does not take it for them, and does not report it as done.

**Why:** Inside an automated run, satisfying it makes a broken automation look healthy, and the next run has no person in it.

**Pattern:**
- **Split it off while planning.** Split the step off while the work is planned, not when it is closed.
- **Stop where only a person can judge.** Where the result needs a person to try it, stop and wait for their report: the machine cannot judge it.

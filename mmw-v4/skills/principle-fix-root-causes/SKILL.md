---
name: principle-fix-root-causes
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Fix Root Causes

When debugging, do not fix symptoms. Trace every problem to its root cause and fix it there.

**Why:** Symptom fixes accumulate. Each workaround makes the system harder to reason about, and the real bug remains. Root-cause fixes are slower upfront but reduce total debugging time.

**Pattern:**
- Reproduce first
- Ask "why" until you hit the root cause
- Do not add guards (adding a nil check to silence a crash is a symptom fix)
- If a workaround needs a paragraph-long comment to justify it, the code is wrong (fix the code, not the comment)
- Check for the pattern, not just the instance (grep for the same pattern, fix all instances)
- When stuck, instrument. Don't guess (add logging, read the actual error)
- A check that will not pass is a symptom too. Answer it by fixing the code, or by recording that the criterion was not met; never by bending the baseline, the harness or the test. Loosening an expected value, adding a retry, a sleep or a skip, or widening a timeout until red turns green is bending the check. A check that is itself wrong is reported where its owner sees it, with what it should be; the work it judges does not correct it

**Restart bugs: suspect state before code**

When something "fails after restart," suspect stale persistent state first: config files, caches, lock files, serialized state. If clearing a state file restores behavior, prioritize state validation as the fix.

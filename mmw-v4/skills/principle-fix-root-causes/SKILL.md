---
name: principle-fix-root-causes
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Fix Root Causes

When debugging, fix the fault, not the place where it surfaced. The symptom is where a wrong state became visible. The root cause is the first place the system did something it should not do, or failed to handle a state it should handle.

**Why:** A symptom fix hides the evidence and leaves the fault free to surface somewhere else. Each one makes the system harder to reason about, because the code now carries a workaround for a bug that nobody named.

**Pattern:**
- Reproduce first.
- Ask "why" at each step until the answer is a wrong decision in the code, not a consequence of an earlier one.
- When stuck, instrument. Read the actual error and the actual state. Do not guess.
- Ask whether the state that triggered the symptom is legitimate. If the system may be in that state, the code that broke on it is the root cause, and handling the state there is the fix. If the state should never exist, a check where it broke hides the bug. Find what produced the state. Guards, retries, swallowed errors, clamped values, and discarded state are the usual ways to hide a bug.
- When something fails only after a restart, suspect persisted state first: config files, caches, lock files, serialized state.
- Check for the pattern, not just the instance. Find every place with the same fault and fix them all.
- If a workaround needs a paragraph-long comment to justify it, the code is wrong. Fix the code, not the comment.
- If the deciding fact took a deep dig to find, propose the cheap, always-on signal that would have shown it at first look.
- A check that will not pass is a symptom too. Answer it by fixing the code, or by recording that the criterion was not met; never by bending the baseline, the harness or the test. Loosening an expected value, adding a retry, a sleep or a skip, or widening a timeout until red turns green is bending the check. A check that is itself wrong is reported where its owner sees it, with what it should be; the work it judges does not correct it

**In a diff:**

- A guard clause that masks a broken invariant, a retry that hides a broken contract, or a cast that silences a modeling error covers a symptom: find what breaks the invariant and fix it there.
- A fix in one module that belongs in another module's contract: move it to the contract that broke.
- A workaround: ask why it is needed and what the proper fix would be.
- A defect fixed at the one caller that met it, while the shared code still hands it to the other callers: fix the shared source.
- A comment that explains a surprise in our own code: delete it, and reshape the code (rename, extract, type, rearchitect) until the behavior is obvious without prose.
- A test change that weakens an existing assertion, or bends the check as the last pattern line says: put the check back. An honest "not met" costs the owner one look; a false pass lands broken behavior under a green mark, and everything built on it inherits it.

**Stop:** when no fix is in sight, stop trying and record what each round tried. That record is the whole account of the trying.

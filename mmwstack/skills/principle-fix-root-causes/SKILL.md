---
name: principle-fix-root-causes
description: "Apply when debugging a symptom or a failing check. Test competing causes against the reproduction and trace the fault to the implementation or the check. Keep the required behavior fixed."
---

# Fix Root Causes

Fix the fault, not the place where it surfaced. The root cause is the first place the system did something it should not do, or failed to handle a state it should handle.

- Reproduce first. When several causes could produce the symptom, test predictions that distinguish them. If separate reproductions expose different faults, trace each one. Ask "why" until the answer is a wrong decision in the code. When stuck, instrument and read the actual state.
- Ask whether the state that triggered the symptom is legitimate. If it is, handle it where the code broke. If it should never exist, a check there hides the bug, so find what produced it. Guards, retries, swallowed errors, clamped values, and discarded state are the usual ways to hide a bug.
- Fix the pattern, not the instance. Find every place with the same fault.
- If the deciding fact took a deep dig, propose the cheap, always-on signal that would have shown it at first look.
- A failing check is a symptom too. Fix the implementation if it violates the requirement. If the check is wrong, correct it against the requirement. When the playbook freezes the baseline or harness, report the discrepancy and leave it intact. Never relax a valid check just to turn it green.

---
name: principle-silence-is-never-a-pass
description: "Apply when a check, gate, oracle or test is written, changed, run, or read as a result. A check that did nothing, or whose green could come from something other than the product being right, has failed: say it could not check, and change the product, never the check."
---

# Silence is never a pass

A check that could verify nothing says so instead of reading like a pass. A check that ran and did nothing has failed, and so has one whose green could come from something other than the product being right.

**Why:** A gate that did no work and made no sound reads exactly like a gate that passed. "Could not check" and "checked, nothing wrong" are two different answers, and only the second may be quiet.

**Pattern:**
- **Fail out loud when it cannot run.** With no data, no answer or no network, it says it could not run, and it fails.
- **Prove a new check can fail.** Run its failure path once and see it go red when it cannot do its work, instead of passing quietly. An oracle that cannot go red is not an oracle.
- **Change the product, never the check.** Write each check so that green can only mean the product is right; when it is red, change the product, or say the specification is wrong, never the check.
- **Treat a green that proves nothing as a gap.** A check that is already green while the thing it names is broken or never reached is a gap in the checks themselves, and its fix asks for a negative control.

**The test:** When you add or change a check, the question to ask it is not whether it catches the bad case, but: if it ran and did nothing, would anyone notice?

Distinct from **principle-prove-it-works**, which says how to verify; this says what to report when a check did not run or did nothing.

---
name: principle-fail-loudly
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Fail Loudly

Code that cannot do its job says so where its reader looks: what failed, what was expected, and where to change it. It never reports success for work it did not do.

**Why:** A check, guard or handler that did nothing and said nothing reads exactly like one that passed, so the defect it hides lands under a green mark and is found later, further away, at a higher price.

**Pattern:**
- **An error is handled or propagated, never swallowed.** An empty `catch`, an ignored exit code, or `|| true` on a step whose failure matters hides the failure. Handle it where the code can act on it, or let it reach a layer that can.
- **No silent fallback past an unclear invariant.** A branch that substitutes a default when an invariant it does not understand breaks makes the breakage invisible. Make the boundary explicit and fail at it.
- **A narrow error stays narrow.** A condition gated on one `errno`, error code or status class encodes a distinction: "the binary is not installed" is not "the command ran and failed". Widening it into a catch-all re-runs real failures against the fallback and reports the fallback's error in place of the true one. Widen it only to another case of the same kind (another "binary unusable" `errno`), when the unhandled path loses data or leaves partial state, or when the retry is idempotent and the original error is still surfaced.
- **Nothing checked is not a pass.** A check, guard or script that verified nothing (no file matched, no case ran, a source could not be read, a service did not answer) fails and says it could not check. "Could not check" and "checked, nothing wrong" are two answers, and only one of them is silence.
- **A failure says where.** It names which check failed, what was expected, what was seen, where to change it (a file and line, or the nearest place it can name) and where the full evidence is, and it keeps the error lines of what it ran.
- **A refusal has three parts:** what happened, with one fact the reader can check (a path, a pid, a count, a ticket number); why; and the one next step the reader can take. Options instead of one next step invite the reader to invent another. A refusal changes nothing before it refuses.

**Stop:** a new or changed check, guard or refusal is done when you have run its failure path once and watched it fail, not only its success path.

Distinct from **principle-prove-it-works**, which verifies your output against the real thing, and **test-audit**, which asks whether a test can fail for a defect. This one governs what code says when it cannot do its job.

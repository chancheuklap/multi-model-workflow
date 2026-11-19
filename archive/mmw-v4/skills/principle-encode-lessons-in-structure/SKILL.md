---
name: principle-encode-lessons-in-structure
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Encode Lessons in Structure

Encode recurring fixes in mechanisms (tools, code, metadata, automation) instead of textual instructions.

If the lesson needs judgment and cannot be encoded, make the instruction more prominent and add an example of the failure mode.

**Pick the strongest mechanism.** First eliminate the mistake through architecture: one owner, one source of truth, no obsolete path to copy. Otherwise choose the strongest mechanism the authorized scope allows (an unrepresentable state that cannot compile, then a lint or banned API that fails CI, then a canonical helper, then a runtime check), because agents copy whatever the surrounding code already does and a weaker guard becomes the next template.

Enforce an existing rule structurally when possible, rather than writing another copy of the warning.

**In a diff:**

- A comment or convention saying "don't do X" that a type, a lint or a runtime check could enforce: offer that mechanism (**Pick the strongest mechanism**), and delete the instruction once it exists.

**Corollary:** If the fix is structural, only use the structural fix. The instruction is the symptom.

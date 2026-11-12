---
name: principle-encode-lessons-in-structure
description: "Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction. Remove the way to make the mistake or encode the rule as a lint, metadata flag, runtime check, or script."
disable-model-invocation: true
---

# Encode Lessons in Structure

First eliminate the mistake through architecture: one owner, one source of truth, no obsolete path to copy. If you add a check, prove it fails on a past instance. For a repo-wide pass, see [Correct](../correct/SKILL.md).

If the lesson needs judgment and cannot be encoded, make the instruction more prominent and add an example of the failure mode.

**Corollary:** If the fix is structural, only use the structural fix. The instruction is the symptom.

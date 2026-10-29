---
name: principle-subtract-before-you-add
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Subtract Before You Add

When evolving a system, remove complexity first, then build. Default to subtraction.

Make simplification a continual investment. Leave the design slightly simpler and more capable behind the same or smaller surface than you found it.

- Sequence removal before construction
- Cut before you polish (get to the minimum before investing in quality)
- Design for observed usage, not speculative edge cases
- No speculative validators, parsers, or guards beyond what the spec demands
- Simplify prompts (remove redundant instructions, excessive templates)
- When a reference has no novel content, delete it rather than leaving a stub
- Before adding a file, a dependency or a configuration entry, write down why the existing one is not enough
- A fix that adds a mechanism (a check, a field, an exit code, a guarding sentence) names the run in which the failure occurred: a run the mechanism would have prevented, not a nearby incident that shares a word with it

**In a diff:**

- Dead code, unused imports, vestigial parameters and orphan references: delete them.
- Speculative Generality, an abstraction, parameter, hook, configuration or "just in case" path for a need nobody has: delete it and inline back.
- A new file, dependency or configuration entry with no recorded reason the existing one was not enough: ask for the reason, or remove it.
- A defence no real run needed, one whose reason names no run, or one that guards a path normal input does not reach: delete it, and state its residual risk once.

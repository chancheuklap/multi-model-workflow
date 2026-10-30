---
name: principle-subtract-before-you-add
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Subtract Before You Add

Aim for the most result with the least code and complexity. Remove dead weight first, then build on the simpler base.

- Cut before you polish. Get to the minimum before investing in quality.
- Make the smallest change that solves the problem. Fewer lines beat boilerplate.
- Keep each decision in one source of truth rather than repeating the choice across callers.
- Design for observed usage, not speculative edge cases. Add no speculative validators, parsers, or guards beyond what the spec demands.
- Simplify prompts by removing redundant instructions and excessive templates.
- When a reference has no novel content, delete it rather than leaving a stub.
- Before adding a file, a dependency or a configuration entry, write down why the existing one is not enough.
- A fix that adds a mechanism (a check, a field, an exit code, a guarding sentence) names the run in which the failure occurred: a run the mechanism would have prevented, not a nearby incident that shares a word with it.

**Keep intact.** Whatever you simplify, keep security, error handling that prevents data loss, accessibility, and anything the task explicitly asks for.

**In a diff:**

- Dead code, unused imports, vestigial parameters and orphan references: delete them.
- Speculative Generality, an abstraction, parameter, hook, configuration or "just in case" path for a need nobody has: delete it and inline back.
- Of every hunk, ask whether the acceptance criteria still pass with less: the hunk deleted, folded into a branch that already exists, or replaced by a helper the repository already has. Raise it only when you can write the shorter form; one you cannot write is a preference.
- Look for the reframing that keeps the behavior and makes a block of branches, helpers, modes or layers disappear, rather than rearranging it. One that reaches beyond the ticket's files is a finding outside the ticket, never a demand on this diff.
- A new file, dependency or configuration entry with no recorded reason the existing one was not enough: ask for the reason, or remove it.
- A defence no real run needed, one whose reason names no run, or one that guards a path normal input does not reach: delete it, and state its residual risk once.
- A simplification that removes a security check, error handling that prevents data loss, accessibility, or something the request asked for: put it back (**Keep intact**).

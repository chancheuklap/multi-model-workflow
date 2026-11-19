---
name: principle-foundational-thinking
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Foundational Thinking

**Structural decisions** protect option value. **Code-level decisions** protect simplicity.

**Data structures first.** Get the data shape right before writing logic. Define core types early, trace every access pattern, and choose structures that match the dominant paths.

At code level, DRY the structure, not every line. Types and data models should converge. Three similar statements still beat a premature abstraction. Prefer explicit over clever. Test behavior and edge cases, not line counts.

**Concurrency corollary.** Before sharing state between actors, ask "what happens if another actor modifies this concurrently?" If not "nothing", isolate.

**Scaffold first.** If something helps every later phase, do it first. Ask "does every subsequent phase benefit from this existing?" CI, linting, test infrastructure, and shared types are scaffold. Sequence for option value: setup before features, tests before fixes. Keep commits small and single-purpose.

Each increment should land a coherent abstraction or deepen one that exists. Do not spread a new capability across callers as special-case coordination.

Subtraction comes before scaffolding. Remove dead code first, then lay foundations.

**In a diff:**

- The same logic shape in more than one hunk or file is extracted when a change to one copy would have to change the other. Simple code is not a finding for lacking abstraction: an abstraction is premature until the code must change in a second way.
- A new dependency that will make future changes harder: name what it ties together, and cut the tie.
- A data structure that does not match the access patterns the code actually uses: choose the one that fits the dominant path.

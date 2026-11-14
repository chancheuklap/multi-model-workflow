---
name: principle-start-from-what-exists
description: "Apply when a nontrivial change has no settled implementation approach. Look for a fit in the repo first. Search outside it if a gap remains, then choose whether to reuse, extend, or build."
---

# Start From What Exists

Every design and every implementation starts from what already exists.

**Why:** A search the reply records is checkable, and the next agent does not repeat it.

**Pattern:**
- Before you propose an approach or write non-trivial code, search for it. First this repository and the material the task names: a helper, module or pattern that already does it. A local implementation that meets the need can settle the search.
- If a gap remains, look for prior art in relevant open-source projects and package registries. Look for what covers 80% of the need, not an exact-name match, and read at least one implementation file of each serious candidate, not only its README.
- Then decide one of three: use it as is, fork or extend it, or build it yourself.
- Cite the implementations that informed the decision and say why you chose to reuse, extend, or build.
- Stated figures such as stars, last commit or downloads are ones you saw, never estimated.

**Does not apply** to trivial changes in existing code, to fixing a bug in place, or when the implementation approach is already settled.

Distinct from [principle-first-principles-thinking](../principle-first-principles-thinking/SKILL.md), which says, while reasoning, to use a proven pattern that already fits. This is the search you run before you build, and the record you leave of it.

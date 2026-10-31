---
name: principle-minimize-reader-load
description: Use when shaping modules, helpers, dependencies, or mutable state. Reduce the layers readers must trace and the hidden state they must hold to understand the code.
---

# Minimize Reader Load

Maintainability is the work a reader must do to understand code. Track two axes: **layers to trace** (indirections between the question and the answer) and **state to hold** (hidden or mutable context the reader must keep in their head). LOC, cyclomatic complexity, and "clean architecture" are proxies. Reader load is the thing that matters. The two axes are independent. A flat file with 50 globals can be as hard to reason about as a 6-layer adapter stack. Guard both. This is the human analog of **principle-guard-the-context-window**. Working memory is finite for readers too.

- **Keep logic in one function by default.** Extract a helper only for composition or reuse, to hide a genuinely complex boundary, or to name a real concept that makes the caller clearer. Otherwise keep simple expressions and single-use logic inline.
- **Make adjacent layers change the abstraction.** A layer that repeats the same methods and arguments adds reader load without compression. Collapse pass-through layers.
- **Demand interface compression.** A broad interface that hides little complexity makes readers learn both the surface and the implementation. Prefer boundaries that hide meaningful decisions.
- **Shrink state scope:** prefer pure functions (returns over mutations), locals over fields, fields over module state, and module state over globals. Derive instead of sync.
- **Name the invariant at the boundary,** not in every consumer, so the reader learns it once.
- Before adding a layer or a piece of state, ask: does it reduce reader load elsewhere by at least as much?

**The test:** can a new reader answer "where does X come from?" and "what can change X?" in under 30 seconds? If not, cut layers or cut state.

**In a diff:**

- A name that does not say what the thing does or holds: rename it. When no honest name comes, the design is murky.
- A file the change takes from under 1000 lines to over without a structural reason: name the part that should stand on its own and extract it.
- A new dependency that will make future changes harder: name what it ties together, and cut the tie.
- A message chain (`a.b().c().d()`) the caller should not depend on: hide the walk behind one method on the first object.
- The deletion test, on every module the change adds or reshapes: imagine deleting it. If the complexity vanishes, it was a pass-through and goes; if the complexity reappears across its callers, it earns its keep.

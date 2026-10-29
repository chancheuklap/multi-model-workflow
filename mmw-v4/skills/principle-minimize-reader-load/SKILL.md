---
name: principle-minimize-reader-load
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Minimize Reader Load

Maintainability is the work a reader must do to understand code. Track two axes: **layers to trace** (indirections between the question and the answer) and **state to hold** (hidden or mutable context the reader must keep in their head). LOC, cyclomatic complexity, and "clean architecture" are proxies. Reader load is the thing that matters. The two axes are independent. A flat file with 50 globals can be as hard to reason about as a 6-layer adapter stack. Guard both. This is the human analog of **principle-guard-the-context-window**. Working memory is finite for readers too.

- **Collapse layers** that cost more than they save: wrappers with one caller, adapters with no second implementation, speculative indirection that was never needed. Inline them.
- **Make adjacent layers change the abstraction.** A layer that repeats the same methods and arguments adds reader load without compression. Collapse pass-through layers.
- **Demand interface compression.** A broad interface that hides little complexity makes readers learn both the surface and the implementation. Prefer boundaries that hide meaningful decisions.
- **Shrink state scope:** prefer pure functions (returns over mutations), locals over fields, fields over module state, and module state over globals. Derive instead of sync.
- **Name the invariant at the boundary,** not in every consumer, so the reader learns it once.
- Before adding a layer or a piece of state, ask: does it reduce reader load elsewhere by at least as much?

**The test:** can a new reader answer "where does X come from?" and "what can change X?" in under 30 seconds? If not, cut layers or cut state.

**In a diff:**

- A name that does not say what the thing does or holds: rename it. When no honest name comes, the design is murky.
- A file the change takes from under 1000 lines to over without a structural reason: name the part that should stand on its own and extract it.
- One function mixing high-level orchestration with low-level detail: move the detail behind a named call.
- A message chain (`a.b().c().d()`) the caller should not depend on: hide the walk behind one method on the first object.
- The deletion test, on every module the change adds or reshapes: imagine deleting it. If the complexity vanishes, it was a pass-through (a middle man, a thin wrapper, an abstraction with one call site) and goes; if the complexity reappears across its callers, it earns its keep.

---
name: principle-minimize-reader-load
description: "Apply when reviewing code that's hard to trace or deciding whether to extract a helper. Count the layers and hidden state a reader must follow. Extract a helper when it serves composition or reuse, hides complexity, or clarifies the caller."
---

# Minimize Reader Load

Reader load is the work a reader must do to understand code. It has two independent axes: layers to trace between the question and the answer, and hidden or mutable state to hold in their head. Guard both.

- Collapse layers that only forward: wrappers with one caller, adapters with no second implementation, pass-through methods. Inline them. Extract a helper only for composition or reuse, to hide a genuinely complex boundary, or to name a real concept that makes the caller clearer.
- Shrink state scope: returns over mutations, locals over fields, fields over module state, module state over globals. Derive instead of sync.
- Name an invariant once at the boundary, not in every consumer.

The test: can a new reader answer "where does X come from?" and "what can change X?" in under 30 seconds? If not, cut layers or cut state.

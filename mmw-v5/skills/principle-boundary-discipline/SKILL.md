---
name: principle-boundary-discipline
description: Use when accepting external input, exposing interfaces, handling errors, or wiring framework adapters. Validate at system boundaries, trust established internal guarantees, and keep business logic pure.
---

# Boundary Discipline

Place validation, type narrowing, and error handling at system boundaries. Trust internal code unconditionally. Business logic lives in pure functions. The shell is thin and mechanical.

**Why:** Scattered validation is noisy, redundant, and gives a false sense of safety. Keep logic out of framework wiring so it can be tested without the framework.

**The pattern:**
- **At boundaries**, validate unknown values once at the boundary that owns them, then pass typed values inward.
- **Inside the system**, do not defensively revalidate guarantees from a schema, constructor, or internal type.
- **Across the boundary.** Expose domain concepts, not the boundary's private representation. Keep general-purpose mechanism inside and special-purpose policy at the edge.

**Applications:**

Validation and error handling:
- Parse raw data into domain types at the boundary
- Do not re-export transport, storage, framework, or wire types through the public surface
- Avoid unnecessary `try` and `catch` blocks. Catch an error where the code can recover or translate it for the caller. Otherwise let it propagate.

Code organization:
- Business logic in pure functions with no framework dependencies
- Parse functions: pure transforms from raw bytes to typed state
- Prompt construction: structured state in, string out
- Scoring and assessment: pure transforms from state to results

**The tests:**
- "Is this data crossing a system boundary right now?" If not, validation is redundant.
- "Can this be a pure function that the shell just calls?" If yes, extract it.

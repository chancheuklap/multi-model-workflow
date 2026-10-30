---
name: principle-boundary-discipline
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
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

**In a diff:**

- Untrusted input that reaches a dangerous sink (SQL, a shell, `eval`, `innerHTML`) unescaped: escape or parameterize it at the sink, and trace the input path that reaches it.
- A new endpoint or entry point with no authentication or authorization check: check both at its door.
- A secret in code, a log or an error message: keep it in the environment or a secret store, and redact it wherever it would leave the process.
- Feature logic leaking into a shared path, an implementation detail leaking through an interface, or a bespoke helper where the repository already has the canonical one: move the logic to its layer and call the canonical helper.
- An external dependency reached directly from inside the logic, or through one generic fetcher: inject it, one function per operation, so a test stands in for it at the boundary.
- A worry about a case an enforced invariant already rules out (a shared component, a framework contract, a type, one source of truth) is not a defect, and a guard against it goes. A worry about an invariant that is only assumed, depends on timing, or crosses an async or state boundary still stands.

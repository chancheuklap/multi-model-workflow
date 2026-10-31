---
name: principle-outcome-oriented-execution
description: Use for planned rewrites, internal API replacements, or migrations. Declare verification boundaries, migrate callers, remove superseded paths, and preserve external compatibility obligations.
---

# Outcome-Oriented Execution

Optimize for the intended, verifiable end state at declared verification boundaries. Complete a migration by moving its callers and removing the superseded paths in the same coordinated wave.

**Why:** Keeping every intermediate step fully stable often creates temporary compatibility code that becomes long-lived debt. An explicit transition lets the work converge without mistaking a temporary state for completion.

**Pattern:**

- Use this for planned rewrites and migrations with explicit phase boundaries. Declare where temporary breakage is acceptable, scoped and reversible.
- Before changing an internal API, find every caller. Update callers and tests to the new contract, and remove tests that only protect the old implementation details.
- Keep high-signal checks for actively touched areas during the transition. **principle-sequence-verifiable-units** governs the check at each unit.
- At migration completion, delete the superseded API, branch, guard or file and any temporary compatibility code. Require the plan's full static and runtime verification there.
- Coordinated breaking changes require that no external user depends on backward compatibility. Preserve an external contract until its migration is explicitly agreed.

**In a diff:**

- A small deliberate duplicate that keeps a new path parallel to one the plan deletes is not a finding during the declared transition, unless it touches security, billing, data access or API behavior, or a long-lived shared abstraction would clearly reduce the risk.
- A new path beside an old one after migration completion, or a caller still using the superseded contract: finish the caller migration and remove the old path before calling the work done.

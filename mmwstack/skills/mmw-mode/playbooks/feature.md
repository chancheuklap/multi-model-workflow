### Feature

**You own the design. Plan, review, verify.** Delegate implementation. Stay in the lead.

1. Trace the affected subsystem.
2. [architect](../../architect/SKILL.md) for the shape.
3. Write the throughput checkpoint as four todo items. A dimension that genuinely does not apply (single file, no fan-out) keeps its item with `n/a: <reason>` rather than being dropped:
   - **Blocking first steps.** Gates run before fan-out.
   - **Independent workstreams.** Disjoint files, services, or layers parallelize. Shared writes serialize.
   - **Shared mutable state.** Default to splitting the target (the [principle-separate-before-serializing-shared-state](../../principle-separate-before-serializing-shared-state/SKILL.md) principle skill). Serialize only for real invariants.
   - **Smallest safe decomposition.** If one worker is best, name why.
4. Delegate code-writing to a subagent with a specific scope (file paths, named data shape and its organizing structure per [principle-model-the-domain](../../principle-model-the-domain/SKILL.md), a state machine over scattered booleans, a table/registry over branching, a typed model over repeated shape assumptions, chosen before the delegate writes logic, and success criteria). Use the model and settings from the current host’s `feature, refactoring` entry in `~/.agents/mmwstack-models.md` (or the supplied rule file). When the implementation admits multiple valid shapes (error handling, abstraction layer, test structure), delegate via the [arena](../../arena/SKILL.md) skill instead so the runners surface the alternatives and the cross-judge guards the pick. Mandatory: no skipping this delegation with a reason, and [principle-laziness-protocol](../../principle-laziness-protocol/SKILL.md) does not override it (the gain is review separation, not lines saved). A subagent forbidden to spawn satisfies this by owning the diff directly with the same review separation. No "standing by" reply that waits on a nested agent. Surgical edits, re-ground against the source for upstream-derived files. Port shared-primitive improvements to all consumers and verify each. Commit liberally. Give the writer the expected behavior from Testing Decisions and this instruction: “Invoke [write-tests](../../write-tests/SKILL.md) before writing or changing tests.” Close a retained code worker via [host dispatch](../references/host-dispatch.md) once you accept its diff, revert it, or spawn a fresh replacement.
5. Verify on the matching surface. "Inconclusive" or wrong-surface is not a pass. Flag it.
   When the change touches `covered code` or guarded state, also run every matching project `formal verification skill` (`formal-verify-<area>` or a differently named skill covering that area), sync any changed `model`, `formal verification harness`, and `coverage record` per [maintain-formal-verification-skill](../../maintain-formal-verification-skill/SKILL.md), prove `broken variant` failure when updating a model, and rerun the `formal check`.
   Before you organize commits, run `scripts/check` for repository checks under the [repo-checks moment rules](../../repo-checks/references/checks.md#moment-rules), without replacing verification on the real surface.
6. Rebase into small, ordered commits. Stack follow-ups.
   Use the [principle-sequence-verifiable-units](../../principle-sequence-verifiable-units/SKILL.md) principle skill, building, verifying, and committing each small unit before the next.
7. Run **Opening a PR**.

Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline. Give a multi-phase single owner `session` lifecycle class via [host dispatch](../references/host-dispatch.md) so it survives across turns. Close it once its PR or verification completes, or force-close it on stuck replacement. That owner fans out internally after the blocking phase. Parent-level fan-out is for slices that produce independent artifacts (audits, cross-subsystem investigations, competing experiments). Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts.

**Reply:** what you built, what you chose and why, the throughput checkpoint, open decisions. Tables for design alternatives.

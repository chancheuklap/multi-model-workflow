# Writing tests

Use the shared judgments in the test-audit skill. This branch owns the writing method, including TDD and behavior-preserving pins. Read the project's domain vocabulary and applicable ADRs before choosing names and interfaces. With a ticket, use its Seam. Otherwise choose the engineering boundary from the current task's contract. Consult the codebase-design skill's SKILL.md when the interface itself needs design.

## Choose the proof

| Work | Method |
| --- | --- |
| Add behavior or repair a defect | Use the TDD loop below. |
| Preserve behavior while moving structure or replacing a dependency | Pin it before the move, as below. |
| Prepare acceptance from a settled prototype | Use the caller's design/product handoff and the UI writing guidance below. Day-authored acceptance is distinct from the worker's TDD loop. |
| Change skill instructions | Use the writing-for-agents skill's WALKING-A-SKILL-SET.md and the Authoring or modifying a skill playbook for the fresh-agent walk. |

## TDD

1. Choose the next behavior at the agreed seam and write its focused regression. Run it before the repair and read why it fails. A missing test file, typo or broken fixture is not the defect's behavioral red. When inability to launch is itself the agreed smoke contract, that launch failure is the intended red.
   Done when the failure demonstrates the absent behavior, or unavailable baseline evidence is explicitly recorded with the closest available proof.
2. Implement that slice and run its test. Keep the repair coherent, including affected callers and newly dead paths; leave unrelated restructuring to a deliberate pass after the slices are green. Each cycle uses what the last one taught rather than prewriting a whole imagined implementation.
   Done when that behavior passes and the next slice, if any, is identified.
3. Hand back the failing-before and passing-after evidence, including the failing assertion or symptom. Apply the shared proportional-proof judgment for any additional checks.
   Done when the caller can distinguish demonstrated repair from unavailable proof.

## Pin unchanged behavior

Choose a characterization test, snapshot or equivalence harness at the existing boundary. Run it green before moving structure and green after. Demonstrate sensitivity with a bounded control that breaks the protected behavior; restore the changed source and rerun. Typechecking or lint alone does not pin runtime behavior. Carry this evidence back with the move.

## Dependencies and fixtures

Run real in-process behavior. Use a test database, local service or in-memory adapter where it faithfully serves the contract; an owned service across a network can still have such an adapter. Place substitutes at the I/O boundary, applying **principle-boundary-discipline**. A substitute's result is evidence about its consumer, not proof of the substituted provider's behavior. Keep distinct transport and live contracts where needed.

Use fixed external I/O and independently derived expectations. Inject clocks and randomness when relevant. Give each run ownership of mutable state and resources, wait for produced completion signals, and close owned processes, watchers, handles and temporary data. Reuse the project's existing fixture helpers and native cleanup mechanism. A state leak is a fixture or resource-owner problem, not a reason to serialize otherwise independent tests.

## UI acceptance fixtures

Use fixed steps and accessible roles, visible names and labels. When an existing feature lacks an accessible name, return that prerequisite before writing its test. Create data through the UI or its actual API using the agreed interface and seed data. Keep repeated sign-in and activation in the project's existing helpers.

For design/product acceptance, use the same operations and assertions on both targets. The prototype's API fake supplies unimplemented product interfaces. Test interception is for external services or states that operations cannot produce, such as an error or loading state, and applies to both targets. Remove that interception when the real interface becomes operable. Choose a fresh data directory per run. When tests intentionally share writable state inside one run, the runner may use one worker; separate runs still require separate state.

Capture the action and the resulting visible state. Verify safe-mode and dry-run side effects through observed files, requests or refs rather than their names. The caller's product skill specifies its commands and evidence locations.

Done when the test's contract, failure sensitivity, setup ownership and evidence are clear, and the caller receives the result.

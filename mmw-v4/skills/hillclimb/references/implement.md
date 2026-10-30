# Run the climb

Read the supplied workload, architecture model, frozen harness, target, attempt floor and ranked hypotheses. Use this skill's **Attempt record** format on the execution ticket.


- Read the Attempt comments before each attempt. One hypothesis per iteration. Measure before and after with the frozen harness, and run the regression gate.
- Accept only when the metric moves past noise and the gate stays green. Otherwise revert the change in full. A tweak that "might help" is not kept.
- One commit per accepted fix, staging only the files changed (`git add <files>`, never `-A`). Post the Attempt comment either way, kept or reverted. Iterate per **principle-sequence-verifiable-units**.
- Push past the first plateau. On a stall, several rejects in a row, pivot category, combine near-misses, re-read the source, or try something more radical before concluding the hill is climbed. Correctness and simplicity outrank the number. Revert a win that breaks behavior, and keep a simplification that holds the number (**principle-subtract-before-you-add**).
- Stop when the predicate is met. Don't relax the predicate to meet it, and don't quit while cheap untried hypotheses remain. When the remaining ideas are marginal and the target is not met, abandon the target criterion with what each round tried.


Return the measured attempts, kept commits, final metric and unmet criteria to the executing step.

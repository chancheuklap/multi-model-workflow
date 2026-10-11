### Feature

**You own the design and the code. Plan, write, verify.**

1. `how` over the affected subsystem. Read the files the change touches before concluding anything about them (**principle-read-before-you-conclude**), and look for what already does the job before designing one (**principle-start-from-what-exists**).
2. `architect` for parallel design exploration.
3. Write the throughput checkpoint as four todo items. A dimension that genuinely does not apply (single file, no fan-out) keeps its item with `n/a: <reason>` rather than being dropped:
   - **Blocking first steps.** Gates run before fan-out.
   - **Independent workstreams.** Disjoint files, services, or layers parallelize. Shared writes serialize.
   - **Shared mutable state.** Default to splitting the target (the **separate-before-serializing-shared-state** principle skill). Serialize only for real invariants.
   - **Smallest safe decomposition.** If writing it alone is best, name why.
4. Write the code yourself, to a specific scope set first (file paths, named data shape and its organizing structure per **principle-model-the-domain**, a state machine over scattered booleans, a table/registry over branching, a typed model over repeated shape assumptions, chosen before any logic is written, and success criteria). Comments per **Comments**. Surgical edits, re-ground against the source for upstream-derived files. Port shared-primitive improvements to all consumers and verify each. Commit liberally. The scope names the baselines the code must follow, copied, not restated from memory (**principle-baseline-is-the-contract**). When `architect` produced a sketch, the synthesized sketch is the contract: its `not implemented` bodies become code and its pseudocode becomes logic, and a deviation from it is surfaced, not absorbed silently. A parameter the sketch did not anticipate asks whether the sketch was wrong, the requirement was missed, or the implementation is overreaching. The synthesized sketch can land as its own commit first (the **foundational-thinking** principle skill), and breakage that is planned and scoped while its bodies are filled in is fine (the **outcome-oriented-execution** principle skill). While writing, run typechecking and single test files regularly.
5. Verify on the matching surface. "Inconclusive" or wrong-surface is not a pass. Flag it. Run the smallest test set that proves the change (**principle-run-the-smallest-test-set**).
6. Rebase into small, ordered commits.
   Use the **sequence-verifiable-units** principle skill, building, verifying, and committing each small unit before the next.
7. Run **Shared closing** (`playbooks/shared-closing.md`).

Work one session can write stays with you, written in order, with the checkpoint inline. Work too big for one session, or whose independent workstreams should run in parallel, goes through To spec and To tickets instead: each ticket gets its worktree from the dispatch skill, and `land` merges it back. Parent-level fan-out is for slices that produce independent artifacts (audits, cross-subsystem investigations, competing experiments). Rewrite the checkpoint at phase boundaries.

**Reply:** what you built, what you chose and why, the throughput checkpoint, open decisions. Tables for design alternatives.

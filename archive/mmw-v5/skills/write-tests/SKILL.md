---
name: write-tests
description: Write tests while landing code for a specified behavior, a cheap bug regression, or a behavior-preserving move, at the seam the task supplies.
---

# Write tests

When the caller asks for the judgment, the examples, or the mocking guideline, read [the judgment](references/judgment.md), [the examples](references/tests.md), and [mocking.md](references/mocking.md) when a mock is involved. Stop there. The steps below are for landing code.

You are the worker landing this ticket's code. Apply this during that implementation. The review of these tests is a later step, not a step of this cycle.

Use the behavior, test seam, acceptance requirements, and test precedent supplied by the spec, ticket, or task. Call the Skill tool with "principle-baseline-is-the-contract" for those decisions. Call the Skill tool with "principle-anchor-every-reference" for test names and interface vocabulary, and respect ADRs in the area you're touching. Follow the project's existing test runner and fixture conventions.

Read [the judgment](references/judgment.md) before the loop and apply it on every cycle. See [tests.md](references/tests.md) for examples. Read [mocking.md](references/mocking.md) when a test needs a mock, or when you are implementing a system boundary.

## The seam you test at

Test only at seams the task already names. No test is written at a seam the task did not supply. You can't test everything, so the task's seams are how testing effort lands on the critical paths and complex logic instead of every edge case.

When the task names no seam, report that gap to the caller before any test exists.

For each seam the task names, state one line on what a test there catches and what it misses.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), call the Skill tool with "codebase-dic" for the vocabulary. It is the shared source of the module, interface, depth, seam, adapter, leverage and locality terms, and it is a reference to consult, not a session to run. The task's named seam stays.

Done when every test you will add sits on a seam the task names, and each of those seams has its one-line note.

| The task | Follow |
| --- | --- |
| Specified behavior the task adds | [Specified behavior](#specified-behavior) |
| A bug with a clear, cheap test path | [A bug with a cheap test path](#a-bug-with-a-cheap-test-path) |
| A bug whose only new test would be impractical | [When a failing test is impractical](#when-a-failing-test-is-impractical) |
| A move that preserves behavior | [A behavior-preserving move](#a-behavior-preserving-move) |

## Specified behavior

Answer the authoring gate in the judgment before adding a test. Repeat the cycle for each behavior the task specifies.

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage, not the red → green implementation cycle.

One cycle is done when that test failed because the behavior was absent, then passed from the smallest implementation of that behavior. Start the next cycle only after that. The branch is done when every behavior the task specifies has been through one cycle.

## A bug with a cheap test path

When fixing a bug with a clear, cheap test path, make the broken behavior executable before changing production code. The goal is a focused regression test that fails before the fix and passes after it.

1. **Understand the bug.** Identify the intended behavior, current behavior, affected path, and smallest observable reproduction.
2. **Choose the narrowest executable check.** Prefer the closest unit, component, integration, or regression test already used for that codepath. If no practical test path is obvious, do not create one from scratch just to satisfy the workflow. Follow [When a failing test is impractical](#when-a-failing-test-is-impractical).
3. **Write the failing test first.** Add the smallest focused test that would have caught the bug. The test should encode intended behavior, not mirror the current implementation.
4. **Run the new test before fixing.** Confirm it fails for the intended reason. If it passes or fails for an unrelated reason, correct the test or reproduction before editing the implementation.
5. **Fix the bug.** Make the smallest production change that satisfies the intended behavior while preserving nearby contracts.
6. **Rerun the regression test.** Confirm the test now passes.

Follow the guardrails in the judgment. If the bug exposes a broader class of failures, first land the focused regression path, then consider additional sibling coverage.

Done when the new test failed for the intended reason before the fix and passes after it.

## When a failing test is impractical

Do not force a test when it would be impractical. If the available test would require broad harness setup, brittle mocks, slow end-to-end infrastructure, production-only state, vague reproduction steps, or large unrelated fixture churn, skip adding a new test and use the closest useful verification instead.

Use the closest executable regression check instead: a targeted script, manual reproduction command, browser automation, snapshot comparison, log assertion, or focused integration check.

Prefer no new test over a bad test. The judgment says what a bad test is.

Done when that closest check has been run and no bad test was added.

## A behavior-preserving move

When the task moves structure and the behavior stays the same, run the tests already at the task's seam and keep them green. Leave an existing test in place unless the task tells you to remove it.

The red → green loop is for a behavior the task adds or repairs. Structural cleanup that is not this task waits for the review stage.

Done when the same tests pass after the move that passed before it. In the evidence, name that green run from before the move and the green run after it.

## Evidence

Report the evidence, not just the outcome:

- Name the failing-before test or executable check and the failure it produced.
- Name the passing-after test run and any nearby validation performed.
- If failing-before evidence could not be demonstrated, state why and describe the closest regression check used instead.

Done when those three points are reported.

---
name: write-tests
description: "Write tests while landing code for specified behavior, regressions, or refactors through a test seam."
---

# Write tests

You are the agent landing this ticket's code. Apply this during that implementation. Reviewing these tests is not a step of this cycle.

Use the expected behavior, acceptance criteria and test precedent supplied by the spec's Testing Decisions, the ticket, or the brief. Use [principle-baseline-is-the-contract](../principle-baseline-is-the-contract/SKILL.md) for those decisions. Use [principle-anchor-every-reference](../principle-anchor-every-reference/SKILL.md) for test names and interface vocabulary, and respect ADRs in the area you're touching. Follow the project's existing test runner and fixture conventions.

Use the [shared test judgment](references/judgment.md). Consult the [examples](references/tests.md) for a concrete case and [mocking.md](references/mocking.md) when writing a mock.

## The test seam

Choose a public interface where the test can distinguish the expected result from the failure. Use the interface the spec or ticket names when that interface is itself part of the contract. Prefer existing test seams. Among those that can distinguish the failure, use the highest test seam possible. If new test seams are needed, propose them at the highest point you can. The fewer test seams across the codebase, the better - the ideal number is one.

For each test seam the task names, state what a test there catches and what it misses.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), use [codebase-dic](../codebase-dic/SKILL.md) for the vocabulary. It is the shared source of the module, interface, depth, seam, adapter, leverage and locality terms, and it is a reference to consult, not a session to run.

| The task | Follow |
| --- | --- |
| Specified behavior the task adds | [Specified behavior](#specified-behavior) |
| A bug with a clear, cheap test path | [A bug with a cheap test path](#a-bug-with-a-cheap-test-path) |
| A bug whose only new test would be impractical | [When a failing test is impractical](#when-a-failing-test-is-impractical) |
| A move that preserves behavior | [A behavior-preserving move](#a-behavior-preserving-move) |

## Specified behavior

Repeat the cycle for each behavior the task specifies.

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One test seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It stays outside the red → green implementation cycle.

One cycle is done when that test failed because the behavior was absent, then passed from the smallest implementation of that behavior. Start the next cycle only after that. The branch is done when every behavior the task specifies has been through one cycle.

## A bug with a cheap test path

When fixing a bug with a clear, cheap test path, make the broken behavior executable before changing production code. The goal is a focused regression test that fails before the fix and passes after it.

1. **Understand the bug.** Identify the intended behavior, current behavior, affected path, and smallest observable reproduction.
2. **Choose the narrowest executable check.** Prefer the closest unit, component, integration, or regression test already used for that codepath. If no practical test path is obvious, do not create one from scratch just to satisfy the workflow. Follow [When a failing test is impractical](#when-a-failing-test-is-impractical).
3. **Write the failing test first.** Use an existing test that reproduces the bug, extend one, or add a focused case. The test should encode intended behavior, not mirror the current implementation.
4. **Run the regression test before fixing.** Confirm it fails for the intended reason. If it passes or fails for an unrelated reason, correct the test or reproduction before editing the implementation.
5. **Fix the bug.** Make the smallest production change that satisfies the intended behavior while preserving nearby contracts.
6. **Rerun the regression test.** Confirm the test now passes.

Keep the regression test focused on the bug. Avoid broad fixture churn or unrelated coverage expansion. If the bug is flaky, make the test deterministic where possible and document the signal being locked down. If the bug exposes a broader class of failures, first land the focused regression path, then consider additional sibling coverage.

Done when the regression test failed for the intended reason before the fix and passes after it.

## When a failing test is impractical

Do not force a test when it would be impractical. If the available test would require broad harness setup, brittle mocks, slow end-to-end infrastructure, production-only state, vague reproduction steps, or large unrelated fixture churn, skip adding a new test and use the closest useful verification instead.

Use the closest executable regression check instead: a targeted script, manual reproduction command, browser automation, snapshot comparison, log assertion, or focused integration check.

Prefer no new test over a bad test. Run the check on the affected path and record what it cannot prove.

Done when that closest check has been run and no bad test was added.

## A behavior-preserving move

When the task moves structure and the behavior stays the same, run the existing tests that protect the observable behavior. If none covers it, establish a passing check before the move. Keep it green during the move. Leave an existing test in place unless the task tells you to remove it.

The red → green loop is for a behavior the task adds or repairs. Structural cleanup beyond this task is a separate task.

Done when the same tests pass after the move that passed before it. In the evidence, name that green run from before the move and the green run after it.

## Evidence

For a new behavior or bug fix:

- Name the failing-before test or executable check and the failure it produced.
- Name the passing-after test run and any nearby validation performed.
- If failing-before evidence could not be demonstrated, state why and describe the closest regression check used instead.

For a behavior-preserving move, name the same check and its passing results before and after the move.

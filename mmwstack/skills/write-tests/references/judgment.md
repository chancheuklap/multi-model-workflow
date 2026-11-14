# Test judgment

Apply every section when you write a test and when you keep one. [tests.md](tests.md) shows the examples. [mocking.md](mocking.md) is the mocking guideline.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

## Test seam

Tests live at a **test seam**, as the [glossary](../../../docs/glossary/product-verification/GLOSSARY.md#evidence-and-observation) defines it, and never against internals.

## Test behavior, not implementation

Read [principle-test-behavior-not-implementation](../../principle-test-behavior-not-implementation/SKILL.md) in full and apply it to every test you write or keep.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Authoring gate

Before adding a test, answer:

1. Protected observable behavior, invariant, or independent contract?
2. Credible regression that makes it fail?
3. Why existing proof misses it? Each contract: one primary owner at strongest boundary. Another layer needs distinct transport/lifecycle risk. Extend tables/shared fixtures; consolidate repeated setup.
4. Export, flag, wrapper, injection hook with no production caller needed? Move proof to real boundary instead.

- Regressions must fail pre-fix for intended reason, pass after repair; report unavailable baseline proof.
- One owner regression covers bug; never replay at every crossed layer.
- Behavior-preserving refactors should not break test.

- Reject self-comparisons, copied inventories, source greps, implementation/call-shape assertions, duplicate contracts, test-only seams, subject-generated expected values, mocks supplying asserted behavior.
- Fixtures must not fabricate owner receipts/order or claim persistence path never writes.
- Negative controls must fail at intended guard; names must match exercised behavior.

## Retention bar

- Keep independent public API, SDK, protocol, config, migration, storage, security, platform, default, prompt-byte, generated cross-language, package, release, architecture contracts. Keep observable ordering + credible regressions.
- Source inspection valid when cheapest independent guard of user-facing key, byte, path, and survives identifier-only refactoring.
- Static/slow ≠ deletion reason. Baseline failure may be product bug: reproduce + repair owner; never delete test for it.

## A bad test

Prefer no new test over a bad test. A bad test is one that mostly tests mocks, encodes current implementation details, depends on timing or unrelated global state, needs expensive infrastructure for a small fix, or would be deleted immediately after proving the fix.

## Guardrails

- Do not change tests merely to match a wrong implementation.
- Do not weaken existing assertions unless the expected behavior has genuinely changed and the reason is clear.
- Keep the regression test focused on the bug. Avoid broad fixture churn or unrelated coverage expansion.
- If the bug is flaky, make the test deterministic where possible and document the signal being locked down.

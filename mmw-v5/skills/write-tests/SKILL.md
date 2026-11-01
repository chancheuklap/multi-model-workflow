---
name: write-tests
description: Write tests for specified behavior, regressions, or behavior-preserving refactoring.
---

# Write tests

Use the behavior, test seam, acceptance requirements, and test precedent supplied by the spec, ticket, or task. Follow the project's existing test runner and fixture conventions.

| Test work | Method |
| --- | --- |
| Tests for a specified feature | Through the interface, then One slice at a time |
| A bug with a practical regression path | Regression workflow |
| A failing-before test is impractical | Alternative regression check |
| Behavior-preserving refactoring | Refactor under green tests |
| A capacity or live-provider regression | Capacity and provider regressions |
| A fixture with temporary files or controlled time | Fixtures |
| Implement an assigned system boundary | Designing for Mockability, within the supplied contract and test seam |
| A permitted Vitest module override | Vitest module overrides |
| Scripted agent execution and session wiring | Scripted agent fixtures |

Apply **principle-anchor-every-reference** to test names and interface vocabulary, and respect ADRs in the area you're touching.

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

## Through the interface

Derive the expected value from the requirement, not from a run of the code. Assert what the contract promises, no less and no more.

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

## One slice at a time

- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.

- **Refactoring is not part of the loop.**

## Regression workflow

When fixing a bug with a clear, cheap test path, make the broken behavior executable before changing production code. The goal is a focused regression test that fails before the fix and passes after it.

1. **Understand the bug.** Identify the intended behavior, current behavior, affected path, and smallest observable reproduction.
2. **Choose the narrowest executable check.** Prefer the closest unit, component, integration, or regression test already used for that codepath. If no practical test path is obvious, do not create one from scratch just to satisfy the workflow.
3. **Write the failing test first.** Add the smallest focused test that would have caught the bug. The test should encode intended behavior, not mirror the current implementation.
4. **Run the new test before fixing.** Confirm it fails for the intended reason. If it passes or fails for an unrelated reason, correct the test or reproduction before editing the implementation.
5. **Fix the bug.** Make the smallest production change that satisfies the intended behavior while preserving nearby contracts.
6. **Rerun the regression test.** Confirm the test now passes.

## Alternative regression check

Use the closest executable regression check instead: a targeted script, manual reproduction command, browser automation, snapshot comparison, log assertion, or focused integration check.

Use an alternative within the supplied acceptance requirements. State which required proof remains unavailable.

## Refactor under green tests

Refactor under green tests and preserve distinct contracts when
consolidating coverage.

## Capacity and provider regressions

Pass bounded synthetic inventories and fixed timing through real planners for
capacity bugs. Preserve coverage, ownership, and execution-budget assertions;
keep real-checkout inventory coverage in its existing integration tests.

For live provider bugs, prefer a CI-safe regression at the smallest production
composition reaching the defect: real adapters with captured requests, Gateway
integration for session/history/tool pipelines, or independent parser unit
contracts. Keep inherently live-only checks narrow and opt-in.

## Fixtures

### Designing for Mockability

Apply **principle-boundary-discipline**.

When implementing an assigned system boundary, use these patterns for choices left open by the supplied contract and test seam.

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint

### Fixture lifetime

When the project provides shared helpers for test-owned temporary directories,
use them so ownership is explicit and cleanup stays in the test lifecycle.

For time controlled by the test, use the supplied injected clock or the project's
fake timers instead of real sleeps.

- Async E2E waits: produced state, never action return.

Import narrow APIs, not broad barrels.

### Vitest module overrides

Use this recipe only in a project that already uses Vitest, for a fixture
permitted by the task.

New first-party `vi.mock` and `vi.doMock` factories should preserve the real
module's exports when the fixture only needs to override a few functions:

```ts
vi.mock("./runtime.js", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./runtime.js")>()),
  start: vi.fn(),
}));
```

Use pass-through for **export completeness** only. `importOriginal` and
`vi.importActual` can return a separate module instance for stateful singletons;
they do not guarantee shared state or lifecycle identity. Keep a closed mock when
isolating real state or initialization is the fixture's purpose:

```ts
// Keep the database and process-wide cache outside this fixture.
vi.mock("./runtime.js", () => ({ start: vi.fn() }));
```

## Scripted agent fixtures

For deterministic tests of agent execution and session wiring, use fixed inputs
and mock providers:

- A scenario runner using mock providers to assert tool calls + order, skill file reads, and session wiring.
- A small suite of skill-focused scenarios (use vs avoid, gating, prompt injection).

Scripted provider outputs exercise the host's handling of those outputs; they do
not establish how a real model chooses a skill.

## Evidence

Report the evidence, not just the outcome:

- Name the failing-before test or executable check and the failure it produced.
- Name the passing-after test run and any nearby validation performed.
- If failing-before evidence could not be demonstrated, state why and describe the closest regression check used instead.

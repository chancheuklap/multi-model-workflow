# External Engineering Methods

Reference source: `mattpocock/skills`, `skills/engineering`, MIT License, local audit commit `e74f006`.

## Placement

| Method | Runtime file | Use |
| --- | --- | --- |
| `diagnose` | `complex-code-explorer.toml`, `complex-coding-worker.toml` | Route unknown bugs into feedback-loop-first investigation or root-cause repair. |
| `tdd` | `coding-worker.toml`, `complex-coding-worker.toml`, `code-reviewer.toml` | Split packs into public-behavior slices and reject horizontal slicing. |
| `grill-with-docs` | `code-reviewer.toml` | Review design / plan alignment against AgentFlow formal docs. |
| `to-issues` | `orchestrate-workflow` Task Pack planning, `code-reviewer.toml` pack review | Shape Task Packs as vertical, demoable or independently verifiable slices. |
| `triage` agent brief | `orchestrate-workflow` dispatch fields, `code-reviewer.toml` brief review | Keep delegated work self-contained and durable. |
| `improve-codebase-architecture` | `complex-code-explorer.toml`, `code-reviewer.toml`, `release-reviewer.toml` | Record architecture after-effects without blocking delivery unless release risk exists. |
| `prototype` | `orchestrate-workflow`, `coding-worker.toml`, `complex-coding-worker.toml` | Use only as a throwaway decision route for state machine, interface shape, or UI direction questions. |

## Diagnose

1. Build a runnable feedback loop before proposing a fix.
2. Prefer loops in this order: failing test, HTTP/API script, CLI invocation, headless browser flow, trace/log replay, throwaway harness, property/fuzz loop, bisect/differential loop, then HITL.
3. Improve the loop itself: make it faster, sharper, and more deterministic. For flaky bugs, raise the reproduction rate with repetition, parallel triggering, stress, fixed seeds, or frozen time.
4. Reproduce the same failure the user reported. A similar error is not enough.
5. If no loop can be built, stop. Report attempted loops, missing artifact, needed environment access, log/HAR/recording/sample data, or temporary instrumentation permission.
6. After the loop exists, create 3-5 ranked falsifiable hypotheses. Each hypothesis must include an observable prediction and a way to disprove it.
7. Test one hypothesis and one variable at a time.
8. Place temporary instrumentation at boundaries that distinguish hypotheses. Use a unique `[DEBUG-...]` prefix and clean it before completion unless it becomes formal observability.
9. State the confirmed hypothesis and the excluded hypotheses.
10. Put regression coverage at the correct behavior seam. If no seam exists, report the missing seam as architecture friction.
11. Re-run the original feedback loop after the fix and clean throwaway harnesses or temporary instrumentation.

## TDD

1. Test behavior through public interfaces, not private helpers or internal call order.
2. Work vertically: one public behavior, one failing check, minimal implementation, focused verification, then next behavior.
3. Do not interpret RED as “write all tests first.” That is horizontal slicing.
4. Acceptable public surfaces include API responses, CLI commands, UI-visible state, database-visible effects, contract objects, documented workflow steps, and stable module interfaces.
5. Mock only external boundaries such as network, payment providers, system time, file system, browser, external processes, or third-party services.
6. Do not mock the current module under test or the business rule being verified.
7. Design testable interfaces: inject dependencies, return observable results, avoid hidden side effects, and keep the public surface small.
8. Test names and interface language should use project domain terms.
9. Refactor only while the behavior is green, and rerun focused verification after refactor.

## Grill With AgentFlow Docs

AgentFlow doc mapping:

- domain glossary and system map: `CONTEXT.md`, `PROJECT.md`, `ENGINEERING-RULES.md`, and active SPEC/GUIDE docs;
- decision records: existing ADR/SPEC/GUIDE structure;
- local execution rules: `AGENTS.md` and `AGENTS.override.md`.

1. Challenge terminology. New or fuzzy terms must resolve to canonical project terms or explicitly become new formal terms.
2. For every new object, state, workflow, contract, or boundary, identify owner, writer, reader, verifier, and cleanup responsibility.
3. Run at least two concrete business scenarios through the design. One scenario should be an edge, failure, empty, permission, repeated-submit, concurrency, or rollback case.
4. Cross-check that code facts support design claims. If code can answer a question, inspect code instead of asking the user.
5. Suggest ADR only when all are true: the decision is hard to reverse, it would surprise future maintainers without context, and it contains a real trade-off.
6. Use AgentFlow root `CONTEXT.md` as the upstream-skill glossary; do not create `CONTEXT-MAP.md` or `docs/agents/` unless the project rules are explicitly changed.

## To-Issues As Task Pack Design

1. A slice must pass through all layers needed to demonstrate one behavior.
2. A completed slice must be demoable or independently verifiable.
3. Prefer AFK slices where agent can proceed without product or architecture input.
4. Mark HITL when the slice requires human decision, credentials, real environment, visual approval, production confirmation, or manual validation.
5. Publish or execute slices in dependency order. Blockers first.
6. Avoid stale briefs. A durable brief describes current behavior, desired behavior, key interfaces, acceptance criteria, and out of scope. It does not rely on fragile line numbers unless the line is the actual defect locator.
7. Do not close or mutate parent planning artifacts as a side effect of splitting work.

## Durable Agent Brief

1. Write behaviorally, not procedurally. Tell the worker what user/system behavior must become true.
2. Include concrete acceptance criteria that can be checked independently.
3. Include out of scope to prevent adjacent feature drift.
4. Name key interfaces and contracts, but avoid overfitting to volatile line numbers or implementation snippets.
5. If the work may wait, make the brief durable enough to survive file moves and refactors.

## Improve Codebase Architecture

1. Use deletion test: if removing an abstraction makes callers clearer and behavior unchanged, it may be shallow.
2. A seam is valuable when it isolates real variation. One adapter is usually a hypothetical seam; two real adapters or a clear production/test boundary make the seam more credible.
3. A deep interface hides meaningful complexity and becomes a stable public behavior test surface.
4. Good architecture improves locality: related changes stay near each other and do not force unrelated files to change.
5. Classify dependencies before recommending seams: in-process, local-substitutable, remote but owned, or true external.
6. The interface is the test surface. If tests must cross past the interface to verify behavior, the seam or module shape is suspect.
7. Report architecture findings with affected files, problem, proposed direction, and benefit.
8. Do not block current delivery on architecture after-effects unless they create production, data, permission, billing, rollback, or verification risk.

## Prototype

- only use when Phase 0 exposes a design question that docs cannot answer;
- state the exact question first;
- use a terminal prototype for logic/state-model questions and UI variants for visual direction questions;
- make one command or one route run the prototype;
- avoid production persistence by default;
- show state transitions clearly;
- delete or absorb the prototype after the decision, preserving only the answer in design / ADR / plan.

## Not Adopted

- external issue tracker setup;
- `CONTEXT-MAP.md`;
- `docs/agents/`;
- issue publishing as a default workflow;
- PRD publishing as a default workflow.

If future work copies external text, templates, or scripts beyond short paraphrase, add an MIT license notice near the copied material.

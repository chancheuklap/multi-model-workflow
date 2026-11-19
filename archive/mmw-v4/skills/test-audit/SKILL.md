---
name: test-audit
description: Run only when the user, mmw-mode or another skill names it; do not invoke it on your own.
---

# Test audit

Own the testing judgments and methods for writing, reviewing, running and maintaining tests. A green test is useful only when it protects a contract and can detect its failure. Existing tests deserve the same judgment as new ones; an audit preserves useful proof rather than chasing deletion counts. The caller owns the task's scope, authority and next step. This skill hands back testing decisions and evidence, not a second delivery workflow.

Read the shared judgments below, then take the applicable branch before acting.

| Task | Material to read before acting |
| --- | --- |
| Write or change a test, including TDD, acceptance tests or behavior-preserving pins | Read [Writing tests](references/writing.md) before editing tests. |
| Run a selected existing test without changing it | Apply Shared judgments and Proportional proof; keep the caller's command, scope and authority. |
| Review tests in a diff | Apply this file's shared judgments to the caller's review scope. Use its report format; no additional review pass or test run is required. |
| Audit, consolidate or retire existing tests in one area | Read [Audit workflow](references/audit.md) before editing candidates. |
| Diagnose a test failure, flake or test-cost problem | Read [Failures and cost](references/failures.md) before choosing a repair. |
| Coordinate an audit of a repository or subsystem | Read [Campaign](references/CAMPAIGN.md) before dividing the work. Each assigned area enters the audit branch. |

## Shared judgments

### Value and boundary

Before adding or keeping proof, answer:

1. Protected observable behavior, invariant, or independent contract?
2. Credible regression that makes it fail?
3. Why existing proof misses it? Each contract: one primary owner at strongest boundary. Another layer needs distinct transport/lifecycle risk. Extend tables/shared fixtures; consolidate repeated setup.
4. Export, flag, wrapper, injection hook with no production caller needed? Move proof to real boundary instead. A supported public API remains a contract even without an in-repository consumer.

Judge two edits: breaking the promised behavior must make the test fail; restructuring internals while preserving that promise must leave it green. Drive the owner's actual interface with independent expected values from the requirement or a worked example. Prefer the interface's result over a side channel when both expose the same promise. Name cases for the behavior they exercise.

Reject self-comparisons, copied inventories, implementation/call-shape assertions, duplicate contracts, test-only seams, subject-generated expected values and mocks supplying the asserted behavior. Fixtures must not fabricate receipts, ordering or persistence that the production owner must produce. Negative controls must reach the intended guard; an unreachable rejection or an unrelated setup failure proves a different claim.

The contract decides what an assertion means. The payload sent to an external service, no charge for an empty cart, or externally observable ordering can be behavior. A private collaborator's invocation is not an independent contract. Several assertions or cases may jointly prove one contract; use diagnostic clarity and independent risks, not assertion or test-count quotas.

### Retention

Keep independent API, SDK, protocol, config, migration, storage, security, platform, default, prompt-byte, generated-language, package, release, architecture and observable-ordering contracts. Static or slow is not a deletion reason. Source inspection is valid when it guards an independent user-facing contract and survives identifier-only refactoring. A baseline failure may be a product defect to repair.

Use the caller's agreed scope and the repository's established kinds of tests. A missing required contract is a gap to return to its authority, not permission to invent acceptance criteria at review time. Apply **principle-baseline-is-the-contract** when an approved expectation would change.

Name the object a check checks. A search that takes the first hit can examine an unrelated object and pass regardless of the intended one. Use the ticket's named object or its native relationships from a named anchor.

### Proportional proof

Run the smallest relevant set that proves the change, using the repository's native commands and configuration. A full suite needs an explicit workflow gate or a named unresolved risk targeted proof cannot cover; state the reason before running it. Broaden or repeat for changed inputs, failures or a named remaining risk. Reuse valid proof of the same inputs when the caller's workflow permits it.

Follow the caller's required checks and execution permissions. A summary passing is not evidence that a particular required behavior executed: select that case precisely and read its outcome. An unrun device, platform or live-service contract remains unproved. **principle-prove-it-works** governs real-product proof; **principle-explain-the-number** governs measurements.

## Hand back

Use the caller's existing report or ticket. Name the protected contracts, testing decisions, evidence and unproved scope. A review returns findings without running tests. Execution and closeout remain with the existing verification and delivery owners. Return unfinished work through that workflow; this skill grants no commit, publication or landing authority.

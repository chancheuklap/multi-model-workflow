# Ticket stage review

You are reviewing a standalone execution ticket or a complete ticket batch drafted by [to-tickets](../../to-tickets/SKILL.md) and [Split a spec or plan](../../to-tickets/references/split.md) before presentation or publication. When multiple tickets were drafted together, inspect the entire batch as one set. Follow [Reviewer contract](../SKILL.md#reviewer-contract), then check the draft(s) against their upstream plan, spec, or source work issue across the three areas below.

## 1. Upstream inheritance and drift

- **Batch coverage without gaps or overlap.** Across a batch, every remaining in-scope outcome from the checked plan or spec belongs to exactly one ticket. Flag uncovered work, duplicate claims across tickets, and out-of-scope additions.
- **Source traceability.** Each ticket anchors to its source. Child tickets name their parent spec, tickets split from a plan link the plan issue and name their phase or outcomes under `Plan`, and standalone tickets retain the original report and evidence in `Problem` and `Evidence`.
- **Decisions, prototypes, and gates preserved.** Inherited `Implementation Decisions`, `Testing Decisions`, `Build` choices, `approved prototype` links, and applicable `Review gate` requirements carry over intact. Consequential engineering choices made during splitting state their reasons in the affected ticket.
- **Expected result and verification skill contract.** Whenever a ticket delivers a user story's `expected result`, `Acceptance criteria` copies that sentence unchanged. When a ticket changes a user-facing surface in a repository with `verify-<app>/features/`, it names the feature-file path. When both that feature file and the copied `expected result` sentence are present, it includes the drive-script instruction; when either is missing, it omits the script instruction. When a ticket touches `covered code` or guarded state, `Acceptance criteria` names the matching project `formal verification skill` (`formal-verify-<area>` or a differently named skill covering that area), each affected `property` or `formal check`, and the requirement to sync the `model`, `formal verification harness`, and `coverage record`, change a `property` only for an `intended change to a promise` backed by cited evidence, prove `broken variant` failure when updating a model, and rerun the `formal check`.

## 2. Ticket process and contract

- **Vertical slice check.** Each code ticket cuts a narrow, complete path through the layers needed to deliver one independently verifiable or demoable outcome, sized to fit a single fresh context window. Flag horizontal layer-only slices (such as schema-only or UI-stub-only tickets with no verifiable outcome). Allow three explicit exceptions:
  1. Verifiable `prefactoring` or a shared prerequisite delivering a result subsequent tickets can use and verify on its own.
  2. A `wide refactor` explicitly sequenced as expand-contract (expand beside the old form, migrate callers in bounded batches blocked by expand, contract once no callers remain, or a shared integration branch with a final integrate-and-verify ticket).
  3. A `ready-for-human` or non-code ticket that states the exact action and how to confirm its result.
- **Template and metadata completeness.** Required fields are present (`Title`, `mmw:ticket` type label, a single queue label from `ready-for-agent`, `ready-for-human`, or `needs-triage`, `Problem`, `Agreed work`, `Acceptance criteria`, `Parent` for child tickets, and `Plan` when split from a plan). Empty optional sections and template instructions are omitted.
- **Decision-level prose.** Drafts avoid brittle file paths and raw code snippets unless trimmed to decision-rich parts and explicitly noted as coming from a prototype.
- **Checkable acceptance criteria.** Every checkbox pairs an action or check with an observable expected result. For silent-failure domains (money reaching a terminal state, crash recovery, contracts read by an installed base, security defaults), the criterion names the observation that distinguishes success from silent failure.
- **Direct blocker accuracy.** `Blocked by` lists only genuine `direct blockers` and names each prerequisite result when the link alone is unclear. Flag missing prerequisites, dependency cycles, and unnecessary serialization between independent tickets that merely share a phase or parent.

## 3. Document clarity

- **Fresh-session readability.** An implementing agent starting with zero prior chat context can execute each ticket from its body and links alone, with no open product choices left to guess and no unanchored references ("as discussed", "the above").
- **Terminology and unslopped prose.** Titles and descriptions use canonical English issue and ticket names plus project glossary terms, concrete observable acceptance verbs, and direct sentences free of em dashes, mid-sentence colons, and AI filler.

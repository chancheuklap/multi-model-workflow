# Codex Review System Optimization Plan

## Purpose

This plan records the next repair and optimization pass for the Codex-native review system in `codex-orchestrate/`.

The goal is not to add more review ceremonies. The goal is to make the existing review chain more faithful to the workflow design:

- Design and mockup documents remain the source of intent. Reviewers must read them directly.
- Plan Review checks whether each plan can implement the design and whether plans connect to each other correctly.
- Plan Implementation Review checks whether each completed plan matches its reviewed plan and design anchors.
- Final Review checks the integrated result across all plans, not just whether every individual plan passed.
- Repair routing is based on the risk and nature of the finding, not on a pre-labeled risk class for review content.
- Tests or validation evidence must prove the repaired behavior without creating unnecessary test bloat.

This is a source-only plan. It must not sync changes into the installed runtime or plugin cache unless the user explicitly approves that as a separate runtime step.

## Non-Goals

- Do not add an Intent Ledger. Intent is unstable and must be reconstructed by reviewers from the Design and Mockup documents.
- Do not rank review areas by content risk. All review content is important.
- Do not add extra review phases unless an existing phase cannot express the required check.
- Do not import Codex PR review or security-review product behavior as a core workflow requirement.
- Do not remove the existing `review_effectiveness` implementation in the same change set unless a separate cleanup is approved.
- Do not change Claude plugin source from this plan. Claude plugin synchronization is covered by the second plan.

## Work Package 1: Evidence Table

### Change

Add a required semi-structured Evidence Table to the review output contract.

This table should force the reviewer to show what they actually inspected before issuing a verdict. It is not an intent summary and it is not a replacement for reading the design docs.

Recommended fields:

| Field | Meaning |
| --- | --- |
| `Design / mockup / plan sources read` | The documents the reviewer actually read. |
| `Code or artifact paths inspected` | Files, generated artifacts, state schema, hooks, templates, or docs inspected. |
| `Commands or validations run` | Commands actually executed by the reviewer, if any. |
| `Findings supported by` | The concrete path, line, diff, command, or behavior used as evidence. |
| `Assumptions` | Any assumption that could affect the verdict. |
| `Unverified items` | Anything relevant that the reviewer could not verify. |

### Codex Source Targets

- `codex-orchestrate/build/templates/review-dispatch.md.tmpl`
- `codex-orchestrate/skills/codex-review/SKILL.md`
- generated review references produced by `codex-orchestrate/build/build.sh --apply`
- build tests that assert the Evidence Table appears in both phase review prompts and ad-hoc Codex review prompts

### Implementation Notes

`review-dispatch.md.tmpl` is the right primary source because it already carries the shared review behavior: confidence rubric, pre-emit verification, rationalization prevention, and review-bias indicators.

`codex-review/SKILL.md` needs a direct update because ad-hoc review is not only a generated phase reference. It must use the same evidence discipline even when invoked outside the formal Orchestrate phase flow.

### Acceptance

- Every generated `review-dispatch` consumer requires the Evidence Table, including Design Review, Plan Review, Plan Implementation Review, Final Review, Release Gate, Multi-PR Integration Review, direct repair review, bug fix review, and targeted re-review prompts.
- Ad-hoc Codex Review requires the Evidence Table even though it has a separate prompt contract.
- Reviewers are instructed to leave fields explicit rather than silently omitting unverified areas.
- Build tests fail if any `review-dispatch` anchor consumer or the ad-hoc review skill loses the Evidence Table.

## Work Package 2: Cross-Plan Contract Map

### Change

Create a Cross-Plan Contract Map after all implementation plans are written and before Plan Review starts.

This artifact is not an Intent Ledger. It only records explicit cross-plan connection surfaces: shared interfaces, state fields, migrations, generated artifacts, hooks, contracts, data ownership, ordering assumptions, and verification responsibilities.

Recommended artifact path:

`docs/orchestrate/plans/<slug>/cross-plan-contract-map.md`

Recommended fields:

| Field | Meaning |
| --- | --- |
| `Surface` | The contract, artifact, state field, hook, route, schema, UI behavior, or shared module. |
| `Producer plan` | The plan responsible for creating or changing it. |
| `Consumer plan(s)` | Plans that depend on it. |
| `Owner` | Which plan or system owns future changes. |
| `Verification` | How the integrated contract is checked. |
| `Final Review focus` | What Final Review must re-check across plans. |

### Timing

The map should be produced after plan generation because only then are the plan boundaries and ownership claims visible.

It should be reviewed during Plan Review because Plan Review is the last cheap moment to catch broken plan boundaries before implementation begins.

It should be consumed again during Final Review because a set of individually passing plans can still break when their shared contracts are combined.

### Codex Source Targets

- `codex-orchestrate/skills/orchestrate-plan-writing/SKILL.md`
- `codex-orchestrate/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
- `codex-orchestrate/skills/orchestrate-plan-writing/references/plan-gates.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-angles.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-preconditions.md`
- `codex-orchestrate/architecture-draft.md`
- relevant build tests or grep assertions

### Implementation Notes

Do not create a script generator first. The Coordinator can produce the Markdown map by reading all plan files. A script is only justified later if repeated manual production becomes error-prone.

The map should remain compact. It should only list cross-plan contracts, not every file touched by every plan.

### Acceptance

- Plan Writing requires the Coordinator to produce the Cross-Plan Contract Map before Plan Review dispatch.
- Plan Review explicitly reviews the map for missing producers, missing consumers, ownership conflicts, and unverifiable contracts.
- Final Review explicitly uses the map while reviewing the integrated diff from the starting commit to `HEAD`.
- Final Review can return `NEEDS_EXECUTION` when a cross-plan contract requires implementation-level repair.

## Work Package 3: Central Repair Routing

### Change

Add a shared repair-routing contract used by plan review repair, execution repair, final review repair, and release-gate repair.

This does not classify review content by risk. It classifies findings and repair paths after a reviewer has found a problem.

### Routing Rules

| Finding / repair shape | Repair owner |
| --- | --- |
| Small, local, clearly scoped, no contract boundary | Coordinator Path A self-fix is allowed. |
| Same pack, normal code repair, original worker has sufficient capability | Resume or re-dispatch the original `pack_executor`. |
| Cross-module, migration, billing, permission, runtime, shared contract, state machine, or generated-template issue | Use `complex_pack_executor` or execution re-entry. |
| Root cause unclear | Use `code_explorer` or `complex_code_explorer` first. |
| Systemic bug, repeated failed repair, or regression with unknown cause | Use `root_cause_analyst`. |
| Cross-plan contract issue discovered during Final Review | Return `NEEDS_EXECUTION` once and route through execution repair. |
| Design, mockup, or plan is insufficient to decide correctness | Backflow to Discovery or Plan Writing instead of patching code blindly. |
| Path A repair fails targeted re-review | Escalate to Path B. |

### Codex Source Targets

- new `codex-orchestrate/build/templates/repair-routing.md.tmpl`
- new `codex-orchestrate/build/resolvers/repair-routing.sh`
- `codex-orchestrate/skills/orchestrate-plan-writing/references/plan-review-resolution.md`
- `codex-orchestrate/skills/orchestrate-execution/references/execution-repair-truncation.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-repair.md`
- `codex-orchestrate/skills/orchestrate-execution/references/execution-release-gate.md`
- `codex-orchestrate/skills/orchestrate-final-review/references/final-review-release-gate.md`
- `codex-orchestrate/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `codex-orchestrate/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `codex-orchestrate/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- `codex-orchestrate/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- build tests proving the generated repair-routing block appears in all target references

### Implementation Notes

This shared template is justified because the same repair decision appears in several phases and routes today. Without a shared contract, one phase can route a serious finding to a weak repair path while another phase routes the same kind of finding correctly.

The routing language must stay Codex-native: `spawn_agent`, `send_input`, `wait_agent`, and registered agent types such as `pack_executor`, `complex_pack_executor`, `code_explorer`, `complex_code_explorer`, and `root_cause_analyst`.

### Acceptance

- All review repair paths use the same finding-to-owner rules.
- A finding that exceeds the original worker's capability cannot be forced back to the weaker worker just because it came from that worker's plan.
- Final Review has a clear path for integrated cross-plan failures.
- Path A remains available for genuinely small local fixes, but failed Path A repair must escalate.

## Work Package 4: Regression Evidence, Not Automatic Test Bloat

### Change

Require repair agents to return regression evidence for accepted findings, without requiring one new tiny test for every finding.

### Evidence Guidance

| Finding type | Preferred evidence |
| --- | --- |
| Public behavior bug | Existing or new behavior/integration test. |
| Contract, schema, migration, or generated artifact bug | Contract check, schema validation, migration check, or build check. |
| UI behavior bug | Browser smoke, screenshot, DOM state validation, or existing UI test. |
| Permission, billing, runtime, state machine, or hook issue | Integration check, state transition check, hook test, or manual gate with owner and steps. |
| Documentation or plan mismatch | Document consistency evidence and link to the corrected source. |
| Environment-only issue | Manual validation gate with exact owner, command, and expected result. |

### Codex Source Targets

- `codex-orchestrate/agents/pack_executor.toml`
- `codex-orchestrate/agents/complex_pack_executor.toml`
- `codex-orchestrate/agents/root_cause_analyst.toml`
- `codex-orchestrate/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `codex-orchestrate/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `codex-orchestrate/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- repair references updated by Work Package 3
- release-gate references updated by Work Package 3
- build or grep tests asserting the repair return contract includes regression evidence

### Implementation Notes

The rule should prefer broad, behavior-level evidence over implementation-detail unit tests. The system should not create a bloated test suite where every review finding creates a fragile microscopic test.

When no automated test is reasonable, the repair output must say so and provide a concrete manual validation gate. Silent omission is not acceptable.

### Acceptance

- Repair outputs include regression evidence or an explicit manual validation gate.
- Agents are warned not to add low-value tests that only lock in implementation details.
- Release Gate checks that accepted findings have evidence before declaring the phase complete.
- Root-cause analyst fixes, Coordinator Path A fixes, direct repair fixes, and multi-PR repair fixes are covered by the same evidence rule.

## Work Package 5: Review Effectiveness Downgrade

### Change

Downgrade `review_effectiveness` from a core maturity signal to an optional diagnostic or legacy copied metric.

This feature exists in both the Claude plugin source and the Codex source. It was not newly invented during the Codex repair. However, it currently does not help the review loop make better decisions, and it should not become a required gate.

### Codex Source Targets

- `codex-orchestrate/architecture-draft.md`
- `codex-orchestrate/scripts/verify-maturity.sh`
- existing review-effectiveness scripts and tests only if the downgrade requires wording or gate changes

### Implementation Notes

Do not delete the script, schema fields, or tests as part of this optimization unless that deletion is separately planned. Removing it may touch state schema, validators, and compatibility assumptions.

The first step should be a wording and maturity-gate downgrade:

- The architecture doc should describe it as optional diagnostics.
- `verify-maturity.sh` should not treat it as proof that the review system is correct.
- Existing script/test files can remain for compatibility until a dedicated cleanup removes them.

### Acceptance

- Review correctness no longer depends on `review_effectiveness`.
- The feature is not expanded.
- Any future removal is left as a separate, narrow cleanup with its own validation.

## Commit Sequence

Use one commit per meaningful change:

1. Evidence Table.
2. Cross-Plan Contract Map.
3. Central Repair Routing.
4. Regression Evidence.
5. Review Effectiveness downgrade.

Do not combine source changes with runtime synchronization. Runtime synchronization, if approved, must be a separate explicit step after source validation.

## Validation

Minimum validation after source changes:

```bash
bash codex-orchestrate/build/build.sh --check --plugin-dir codex-orchestrate
bash codex-orchestrate/scripts/verify-maturity.sh
bash codex-orchestrate/scripts/run-all-tests.sh
```

Plugin manifest validation is outside this plan's core review-system scope. If it is used during implementation, verify the validator behavior in that turn instead of assuming either success or failure.

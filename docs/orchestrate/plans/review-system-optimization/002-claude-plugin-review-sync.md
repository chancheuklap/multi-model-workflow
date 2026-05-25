# Claude Plugin Review System Synchronization Plan

## Purpose

This plan records how to carry the review-system improvements back to the Claude Code plugin source in `plugin/`.

The target is behavior-level parity, not mechanical replacement. The Claude plugin and Codex plugin use different host mechanics. Shared review intent should be synchronized, while host-specific dispatch, hook payloads, agent naming, state paths, and runtime contracts must remain native to the Claude plugin.

The Codex optimization should land first. After it is validated, the Claude plugin can receive the same content and workflow improvements with Claude-native implementation details.

## Scope

Synchronize these improvements into `plugin/`:

- Evidence Table in review outputs.
- Cross-Plan Contract Map in the plan-writing to final-review flow.
- Central repair routing based on finding risk and repair shape.
- Regression evidence requirements for repair work.
- `review_effectiveness` downgrade to optional diagnostic.

Do not synchronize rejected ideas:

- no Intent Ledger
- no review-content risk prioritization
- no imported Codex PR review product flow
- no extra review phase

## Claude Plugin Boundaries

The Claude plugin must keep its own host contracts:

- Claude plugin agent files use Markdown agents under `plugin/agents/`.
- Claude dispatch should keep the plugin's existing Agent tool and resume semantics.
- Claude hooks live under `plugin/hooks/` and use Claude hook payloads.
- Existing plugin review integration such as `gate-codex-review.sh`, `track-review-budget.sh`, and Codex companion review dispatch should be preserved unless a concrete plugin-side bug requires changing it.
- State paths and runtime contracts should remain Claude-plugin-native, not rewritten to `.codex/multi-model-workflow/`.

Do not port Codex-only mechanisms into `plugin/`:

- no `spawn_agent` / `send_input` / `wait_agent` wording unless the Claude plugin already uses equivalent terminology
- no Codex custom-agent TOML contracts
- no Codex hook payload assumptions
- no Codex runtime sync behavior

## Preflight: Plugin Build and Anchor Health

Before changing review content, verify the plugin's build anchors.

Prior audit notes indicated some `<!-- BEGIN: review-dispatch -->` anchors had once been inline with preceding text, which could cause build replacement to skip them. Current source must be checked before assuming this is still a live bug.

### Source Targets

- `plugin/build/templates/review-dispatch.md.tmpl`
- `plugin/build/resolvers/review-dispatch.sh`
- review references under `plugin/skills/**/references/`
- plugin build tests under `plugin/build/tests/`

### Acceptance

- `plugin/build/build.sh --check` can verify review-dispatch generated sections.
- Review-dispatch anchors are on their own lines and can be replaced consistently.
- If the build check and own-line anchor check pass, do not create an anchor-repair change just because the historical audit once found this issue.
- No Codex-native wording is introduced during anchor repair.

## Work Package 1: Evidence Table

### Change

Add the same semi-structured Evidence Table requirement to Claude plugin review output contracts.

Recommended fields are the same as the Codex plan:

| Field | Meaning |
| --- | --- |
| `Design / mockup / plan sources read` | The documents the reviewer actually read. |
| `Code or artifact paths inspected` | Files, generated artifacts, state schema, hooks, templates, or docs inspected. |
| `Commands or validations run` | Commands actually executed by the reviewer, if any. |
| `Findings supported by` | The concrete path, line, diff, command, or behavior used as evidence. |
| `Assumptions` | Any assumption that could affect the verdict. |
| `Unverified items` | Anything relevant that the reviewer could not verify. |

### Claude Plugin Source Targets

- `plugin/build/templates/review-dispatch.md.tmpl`
- all generated `review-dispatch` anchor consumers under `plugin/skills/**`, including `plugin/skills/orchestrate-execution/SKILL.md` and references under `plugin/skills/**/references/`
- `plugin/skills/codex-review/SKILL.md`, because the ad-hoc review skill has a separate output contract and is not generated from the shared template
- `plugin/build/tests/`

### Acceptance

- All Claude plugin review dispatch prompts require the Evidence Table.
- Ad-hoc review also requires the Evidence Table.
- Build tests fail if the Evidence Table disappears from any `review-dispatch` anchor consumer or from the ad-hoc review skill.

## Work Package 2: Cross-Plan Contract Map

### Change

Add the Cross-Plan Contract Map to the Claude plugin plan-writing flow.

The artifact path should match Codex so documentation artifacts stay host-agnostic:

`docs/orchestrate/plans/<slug>/cross-plan-contract-map.md`

### Timing

- Generate after all plan documents are written.
- Review during Plan Review.
- Consume during Final Review.

### Claude Plugin Source Targets

- `plugin/skills/orchestrate-plan-writing/SKILL.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-review-dispatch.md`
- `plugin/skills/orchestrate-plan-writing/references/plan-gates.md`
- `plugin/skills/orchestrate-final-review/references/final-review-angles.md`
- `plugin/skills/orchestrate-final-review/references/final-review-preconditions.md`
- `plugin/architecture-draft.md`
- plugin build tests or grep assertions

### Acceptance

- Claude plugin Plan Writing produces the map before Plan Review.
- Plan Review checks producer, consumer, ownership, and verification conflicts.
- Final Review reuses the map to inspect integrated cross-plan behavior.

## Work Package 3: Central Repair Routing

### Change

Add a shared repair-routing block to the Claude plugin build system, adapted to Claude-native dispatch.

### Claude Plugin Source Targets

- new `plugin/build/templates/repair-routing.md.tmpl`
- new `plugin/build/resolvers/repair-routing.sh`
- `plugin/skills/orchestrate-plan-writing/references/plan-review-resolution.md`
- `plugin/skills/orchestrate-execution/references/execution-repair-truncation.md`
- `plugin/skills/orchestrate-final-review/references/final-review-repair.md`
- `plugin/skills/orchestrate-execution/references/execution-release-gate.md`
- `plugin/skills/orchestrate-final-review/references/final-review-release-gate.md`
- `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- `plugin/build/tests/`

### Claude-Native Routing Language

The routing logic should match Codex conceptually, but the words and mechanics must match the Claude plugin:

| Finding / repair shape | Claude plugin repair owner |
| --- | --- |
| Small, local, clearly scoped, no contract boundary | Coordinator Path A self-fix is allowed. |
| Same pack, normal code repair, original worker has sufficient capability | Resume or re-dispatch the original pack executor through the plugin's existing agent mechanism. |
| Cross-module, migration, billing, permission, runtime, shared contract, state machine, or generated-template issue | Use the complex pack executor route. |
| Root cause unclear | Use the plugin's explorer route first. |
| Systemic bug, repeated failed repair, or regression with unknown cause | Use the plugin's existing `root-cause-analyst` route. |
| Cross-plan contract issue discovered during Final Review | Return `NEEDS_EXECUTION` once and route through execution repair. |
| Design, mockup, or plan is insufficient to decide correctness | Backflow to Discovery or Plan Writing. |
| Path A repair fails targeted re-review | Escalate to Path B. |

### Acceptance

- Repair routing is shared across all Claude plugin review repair paths, including formal plan/execution/final review, release gates, direct repair, bug investigation, and multi-PR integration review.
- The shared block uses Claude plugin agent names, hook names, and resume mechanisms.
- The plugin does not receive Codex-only tool names or state paths.
- Existing hand-written targeted re-review commands, such as multi-PR integration re-review, are either moved to the shared review-dispatch template or explicitly updated to satisfy the plugin's `--resume` gate.

## Work Package 4: Regression Evidence

### Change

Update Claude plugin repair agents and repair references so accepted findings require regression evidence or an explicit manual validation gate.

### Claude Plugin Source Targets

- `plugin/agents/pack-executor.md`
- `plugin/agents/complex-pack-executor.md`
- `plugin/agents/root-cause-analyst.md`
- `plugin/skills/orchestrate-workflow/references/workflow-direct-repair.md`
- `plugin/skills/orchestrate-workflow/references/bug-investigation-route.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-integration-review.md`
- `plugin/skills/orchestrate-multi-pr-merge/references/merge-conflict-repair.md`
- repair references touched by Work Package 3
- release-gate references touched by Work Package 3
- plugin tests or grep assertions for the repair return contract

### Acceptance

- Repair agent output includes regression evidence.
- The prompt discourages low-value microscopic tests that only lock implementation details.
- Release Gate checks evidence before declaring a review repair complete.
- Root-cause analyst fixes, Coordinator Path A fixes, direct repair fixes, and multi-PR repair fixes are covered by the same evidence rule.

## Work Package 5: Review Effectiveness Downgrade

### Change

Downgrade `review_effectiveness` in the Claude plugin from core maturity proof to optional diagnostic.

The Claude plugin appears to be the original source for this feature. That makes the plugin-side downgrade more sensitive than the Codex downgrade. The first change should be wording and gate status, not deletion.

### Claude Plugin Source Targets

- `plugin/architecture-draft.md`
- `plugin/scripts/verify-maturity.sh`
- `plugin/scripts/lib/review-effectiveness.sh`
- `plugin/state-schema/workflow-state-v1.json`
- `plugin/scripts/state.sh`
- related tests only if gate wording or maturity assertions need to change

### Acceptance

- Plugin maturity does not depend on `review_effectiveness` as proof of review correctness.
- If the field and script remain for observability compatibility, `verify-maturity.sh` may keep existence checks, but warning generation must not be described as a correctness gate.
- If implementation chooses to make the field truly optional, schema, state initialization, and state tests must be updated in the same commit.
- Existing scripts can remain for compatibility.
- Deletion, if desired later, is handled as a separate cleanup.

## Validation

Use plugin-native validation after each plugin work package:

```bash
bash plugin/build/build.sh --check --plugin-dir plugin
bash plugin/scripts/verify-maturity.sh
bash plugin/scripts/run-all-tests.sh
```

Also inspect the resulting diff:

```bash
git diff -- plugin/
```

The diff must not introduce Codex-native host terms into Claude plugin runtime contracts.

## Commit Sequence

Keep Claude plugin synchronization separate from Codex source changes:

1. Plugin anchor and build-health repair, if required.
2. Plugin Evidence Table.
3. Plugin Cross-Plan Contract Map.
4. Plugin central repair routing.
5. Plugin regression evidence contract.
6. Plugin `review_effectiveness` downgrade.

Do not mix Codex and Claude plugin source modifications in the same commit unless the commit is a documentation-only plan that explicitly records both tracks.

## Execution Order

1. Finish and validate the Codex-native source optimization.
2. Compare the final Codex source changes against this plugin synchronization plan.
3. Apply the same review-system behavior to `plugin/` using Claude-native mechanics.
4. Run plugin validation.
5. Review the plugin diff specifically for accidental Codex host terminology.
6. Commit plugin changes in separate atomic commits.

# External Engineering Method Routing

This file is a routing note, not a compressed copy of external methods. Do not paste upstream method bodies into Orchestrate Workflow prompts or sub-agent instructions. Use the canonical skill as method, then apply AgentFlow anchors and phase gates as overlays.

## Canonical Owners

| Need | Canonical owner | AgentFlow overlay |
| --- | --- | --- |
| TDD / vertical behavior slice | upstream `tdd` | Public behavior, contract wall, mockup evidence, focused verification, no internal implementation tests. |
| Discovery capture | `superpowers:brainstorming` + upstream `grill-with-docs` | Use for new feature discussion, systemic bug, or systemic refactor; update `CONTEXT.md` and SPEC / design draft together. |
| Root-cause debugging | upstream `diagnose` | Feedback loop must reproduce the same user-visible issue; route production risk through release review. |
| Domain / doc challenge | upstream `grill-with-docs` | Align with `CONTEXT.md`, `PROJECT.md`, `ENGINEERING-RULES.md`, SPEC, ADR, GUIDE, and AgentFlow object ownership. |
| Prototype decision | upstream `prototype` | Prototype is throwaway unless explicitly promoted; answer state machine, interface shape, or UI direction only. |
| Architecture improvement | upstream `improve-codebase-architecture` | Architecture finding blocks only when it affects current correctness, data, permission, billing, runtime, rollback, or release safety. |
| Unknown module map | upstream `zoom-out` | Preserve AgentFlow authority map: Gateway, Collection, Local Agent, Dashboard/Console, Pipeline, shared contracts. |
| PRD / issue generation | upstream `to-prd`, `to-issues`, `triage` | Use GitHub issue state docs and AgentFlow plan / Task Pack boundaries. |
| Completion proof | `superpowers:verification-before-completion` | Evidence must be phase-specific: tests, commands, screenshots, logs, release gates, or manual verification reason. |

## Trigger Priority

Run these checks before dispatching implementation work or accepting reviewer findings:

1. **Discussion before design review**：For new feature discussion, systemic bug, or systemic refactor, run brainstorming with grill-with-docs discipline; update `CONTEXT.md` for language / object model and SPEC / design draft for delivery contract.
2. **Context before code**：If desired behavior, domain term, UI target state, user role, lifecycle, permission, billing meaning, or object owner is unclear, use upstream `grill-with-docs` before repair.
3. **Repro before fix**：If the report is a bug, error, wrong state, flaky behavior, or performance regression, use upstream `diagnose` to build a feedback loop before patching.
4. **Question before prototype**：If the decision is about UI direction, state machine, interface shape, or alternative flows, use upstream `prototype` to answer that question, then fold the verdict back into design / plan.
5. **Seam before repeated repair**：If the same issue keeps returning, the test surface is wrong, a single-adapter interface appears, or callers must know implementation detail, use upstream `improve-codebase-architecture`.
6. **Durable brief before parking**：If the work cannot close in the current run or should be queued for later agents, use upstream `triage`, `to-prd`, or `to-issues`.

## Feedback Routing

Testing feedback and UI / UX feedback must be classified before code changes:

| Feedback type | Route | Notes |
| --- | --- | --- |
| Implementation divergence | Phase A repair | Approved mockup / design / acceptance criteria exists and code differs; require screenshot, DOM, viewport, or test evidence. |
| Context ambiguity | upstream `grill-with-docs` | Target behavior, role, hierarchy, copy, interaction, or business meaning is unclear. |
| Prototype question | upstream `prototype` | Need to compare UI directions, state-machine options, or interface shapes. |
| Unknown root cause | upstream `diagnose` | Symptom is clear but cause is not. |
| Architecture friction | upstream `improve-codebase-architecture` | Bad seam, repeated repair, hidden coupling, or weak test surface. |
| Persistent backlog item | upstream `triage` / `to-prd` / `to-issues` | Needs issue-backed workflow or cannot be completed in this run. |

Do not translate subjective UI / UX feedback into a worker patch until the target state and verification method are explicit.

## Dispatch Rule

Sub-agent role TOMLs own default skill assignment. Orchestrate dispatch should normally provide:

- phase and review / pack mode;
- source design / plan / issue / bug brief;
- Project anchors;
- Contract anchors;
- Mockup anchors;
- verification requirements;
- risk flags;
- required return format.

For high-risk work, Orchestrate may also include exact upstream skill paths or reference file paths as reinforcement. It should not re-teach the upstream method.

## Safety Rule

If an agent is expected to use an upstream skill but cannot see it in the skill catalog and cannot read the configured skill path, it must return `NEEDS_CONTEXT` instead of reconstructing the method from memory.

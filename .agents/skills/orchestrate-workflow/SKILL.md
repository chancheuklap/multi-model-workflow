---
name: orchestrate-workflow
description: Use when a design or implementation plan already exists, when Superpowers writing-plans has just produced project docs, or when a user asks to execute, review, continue, advance, resume, or complete a documented development workflow.
---

# Orchestrate Workflow

Coordinate post-design review, Task Pack execution, repair loops, root-cause routing, final intent verification, and the business report.

Use this skill for:

- A design doc under `docs/superpowers/specs/` that exists or was just produced.
- A plan under `docs/superpowers/plans/` that exists or was just produced.
- A user asking to execute, review, audit, continue, advance, resume, or complete a documented workflow.
- A maintenance bug after a feedback loop and bug brief exist.

Do not use it for raw brainstorming, from-scratch design/plan writing, tiny one-off edits, or simple read-only code review.

## Superpowers Boundary

Standard chain:

1. `superpowers:brainstorming` explores requirements and direction.
2. `superpowers:writing-plans` produces design and/or plan documents.
3. `orchestrate-workflow` takes over post-design execution and review.
4. `superpowers:finishing-a-development-branch` handles explicit merge / PR / push decisions after this workflow is complete.

Use this after `superpowers:writing-plans`; use `superpowers:finishing-a-development-branch` for merge / PR / push decisions.

## Main Coordinator Responsibilities

The main session owns:

- locating design and plan documents;
- reading active project instructions, especially `AGENTS.md`, and linked project docs when present;
- repairing Phase 0 design/plan issues directly;
- selecting Task Pack boundaries;
- deciding which packs are truly independent;
- spawning Codex agents only when work can run in parallel or context isolation helps;
- integrating agent results;
- updating plan checkboxes;
- running final verification;
- explaining status in business language.

Dispatch prompts carry task facts: docs, task text, constraints, owned files, acceptance criteria, verification commands, and risk flags.

## Agent Routing

| Work item | Agent type | Contract |
| --- | --- | --- |
| Small code lookup | `code_explorer` | Read-only, answer one narrow question. |
| Multi-module investigation or unknown root cause | `complex_code_explorer` | Read-only, feedback loop first, facts vs inference. |
| Normal implementation pack | `coding_worker` | Owned files only, vertical-slice TDD, status report. |
| High-risk implementation pack | `complex_coding_worker` | Formal docs first, migration/billing/auth/runtime/contracts risk handling. |
| Design, plan, or pack review | `code_reviewer` | Read-only findings, spec compliance before code quality. |
| Final production-risk review | `release_reviewer` | Data, billing, permission, migration, deploy, rollback, manual verification risk. |
| Low-risk mechanical doc edits | `docs_worker` | Authorized docs only, preserve decisions, return `NEEDS_CONTEXT` on judgment calls. |

Use `spawn_agent` for independent sidecar work. Use `send_input` to send review findings back to the same worker when context continuity matters. Use `wait_agent` only when the next critical-path step is blocked on that result. Close agents when no longer needed.

## Dispatch Prompt Contract

Every dispatch prompt should contain:

- phase and purpose;
- exact design / plan / Task Pack / diff / files to inspect;
- project anchors to read, such as `AGENTS.md`, `PROJECT.md`, `ENGINEERING-RULES.md`, related SPEC/ADR/GUIDE, and relevant `AGENTS.override.md`;
- owned files or read-only boundary;
- acceptance criteria and verification commands;
- risk flags, such as billing, permissions, migrations, runtime, browser takeover, cross-service contract, deploy, rollback, or manual validation;
- output shape requested from this run.

Do not include:

- the complete `code_reviewer`, `coding_worker`, `complex_code_explorer`, or `release_reviewer` method text;
- vague method names without concrete task facts;
- method reference files as normal runtime prerequisites.

## Loop Limits

| Loop | Limit | When exceeded |
| --- | --- | --- |
| Phase 0a design review -> main repair | 2 rounds | Explain which design point needs product decision. |
| Phase 0b plan review -> main repair | 2 rounds | Explain which plan point cannot be verified. |
| Phase A pack review -> worker repair | 3 rounds per pack | Report attempts, decide split pack / root-cause route / user decision. |
| Phase B intent gap -> worker repair | 2 rounds per gap | Distinguish implementation gap from design gap. |
| Phase B total dispatch | 15 dispatches | Report completion, remaining risks, decision points. |

Loop limits prevent repeating the same wrong assumption. Every repeated attempt must change method.

## Phase 0a: Design Review

If a design doc exists:

1. Read it completely.
2. Use `code_reviewer` for content and AgentFlow-doc alignment.
3. Use `release_reviewer` instead of or in addition to `code_reviewer` for architecture, billing, permissions, migrations, deployment, runtime, rollback, or cross-service contract risk.
4. Aggregate findings.
5. Fix technical doc issues directly.
6. Ask the user only when the design change would alter product promises, user-visible behavior, business rules, release strategy, or trade-offs.
7. If no plan exists after design review passes, use `superpowers:writing-plans` to create one, then continue to Phase 0b.

## Phase 0b: Plan Review

1. Read the active plan completely.
2. Run coverage, compliance, and independent second-opinion reviews with `code_reviewer`; use `release_reviewer` for production-risk plans.
3. Repair technical plan gaps directly, including stale paths, missing verification, missing `AGENTS.override.md` sync tasks, and unsupported routing.
4. Stop for user input only on business or architecture decisions.

## Setup: Task Pack Planning

Group unchecked plan tasks into Task Packs by:

- shared files;
- dependency order;
- section boundaries;
- risk level;
- expected test scope;
- AFK / HITL classification.

Task Packs should be vertical slices that are demoable or independently verifiable. Avoid horizontal slicing such as "all tests first", "all templates", then "all implementation".

Packs touching the same files, migrations, billing state, auth, runtime scheduler, browser takeover, or shared contracts should be serial unless the write sets are demonstrably disjoint.

## Phase A: Task Pack Execution

For each pack:

1. Spawn `coding_worker` or `complex_coding_worker` with full task text, owned files, acceptance criteria, project rules, no-revert instruction, and verification commands.
2. Review completed work with `code_reviewer`. The reviewer role owns spec compliance, public-behavior evidence, no-internal-mock, vertical-slice, and architecture-finding checks.
3. If findings are valid and context continuity matters, use `send_input` to send them back to the same worker.
4. If the failure is not localized, route to `complex_code_explorer` for feedback-loop-first investigation or `complex_coding_worker` for tightly coupled diagnosis + fix.
5. Re-run focused verification after repairs.

Independent packs may run in parallel. Do not delegate immediate blocking work if the main session cannot do useful non-overlapping work while waiting.

## Maintenance Bug Entry

For bugs without a full plan:

1. Use systematic debugging or the `diagnose` method to build a feedback loop.
2. Produce a bug brief: current behavior, desired behavior, reproduction, hypotheses, key interfaces, acceptance criteria, out of scope.
3. If the fix is small and local, handle it directly with focused tests.
4. If it affects runtime, billing, migrations, permissions, shared contracts, deployment, or multiple modules, create or repair a plan and enter Phase 0b / Phase A.

## Phase B: Final Intent Verification

After packs pass:

1. Verify design intent end to end using real commands and outputs, not implementer self-report.
2. Run relevant focused tests, release-gate checks, smoke commands, browser checks, VM checks, or manual validation instructions.
3. Use `release_reviewer` when the diff touches deploy, database, billing, permissions, runtime, browser takeover, rollback, production dependency, or cross-service contracts.
4. Use independent `code_reviewer` second opinion for non-production final gaps when useful.
5. Route implementation gaps to the appropriate worker. Route design gaps to the user in business language.
6. Record architecture after-effects as follow-up unless they create release risk.

## Phase C: Business Report

Report:

- product capability completed;
- review loops and fixes performed;
- validation commands and results;
- manual/product decisions still needed;
- residual risk and architecture follow-up.

Stop after the report. Do not merge, push, or open a PR from this skill. Use `superpowers:finishing-a-development-branch` for explicit branch completion.

## Direction Check

When direction feels unclear after several packs, review loops, or compaction, answer:

- Where am I? Current phase / pack.
- Where am I going? Remaining packs / phase.
- What is the goal? Re-read design intent.
- What have we learned? Accumulated review findings.
- What changed? Current plan checkbox progress.

## Prohibitions

- Do not skip Phase 0 or Phase B.
- Do not ask the user for every technical phase.
- Do not auto merge, push, or create PR.
- Do not spawn one agent per tiny task.
- Do not treat hooks as the enforcement boundary.
- Do not install duplicate repo-local, user-level, and plugin-installed copies of this same skill.

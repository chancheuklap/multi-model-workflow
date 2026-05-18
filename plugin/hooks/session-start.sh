#!/usr/bin/env bash
# multi-model-workflow: SessionStart hook
# Injects behavioral override rules that must be active BEFORE any skill triggers.
# Must exit 0 — never block session startup.

cat <<'RULES'
[multi-model-workflow] Behavioral override active:
- When the user confirms a direction after discussion, use multi-model-workflow:orchestrate-discovery to produce or refine a design document, then multi-model-workflow:orchestrate-plan-writing to write the plan.
- AS SOON AS a design document is produced or exists, immediately enter multi-model-workflow:orchestrate-workflow — it owns Phase 0a onward.
- multi-model-workflow:orchestrate-workflow is the SOLE orchestrator from "design document produced" through code completion: Phase 0a design review → 0b plan review → A Task Pack execution → B intent verification → C business report. Do not narrow it to just code execution.
- When the user references any existing design doc (specs/) or plan (plans/) and asks to review / audit / advance / execute / continue / 推进 / 审查 / 落地 / 动手 / 走流程, use multi-model-workflow:orchestrate-workflow.
- Agent roles: pack-executor (Sonnet, normal coding), complex-pack-executor (Opus, high-risk coding), code-explorer (Sonnet, narrow investigation), complex-code-explorer (Opus, deep investigation), root-cause-analyst (Opus, unknown root cause + fix), docs-worker (Sonnet, documentation).
- ALL code reviews are dispatched to Codex via codex:codex-rescue for independent cross-model opinion. No Claude-side reviewer agent exists.
- For parallel Task Pack execution, use isolation: "worktree" in Agent tool call to prevent file conflicts.
RULES

exit 0

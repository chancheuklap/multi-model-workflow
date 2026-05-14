#!/usr/bin/env bash
# multi-model-workflow: SessionStart hook
# Injects behavioral override rules that must be active BEFORE any skill triggers.
# Must exit 0 — never block session startup.

cat <<'RULES'
[multi-model-workflow] Behavioral override active:
- When superpowers:brainstorming completes and the user confirms direction, use superpowers:writing-plans to write design + plan yourself (you have the full brainstorming context) — do not dispatch a sub-agent.
- AS SOON AS superpowers:writing-plans produces a design document (docs/superpowers/specs/), immediately enter multi-model-workflow:orchestrate-workflow — it owns Phase 0a design review onward. Do NOT wait for the plan to be written, and do NOT chain to superpowers:subagent-driven-development.
- multi-model-workflow:orchestrate-workflow is the SOLE orchestrator from "design document produced" through code completion: Phase 0a design review → 0b plan review → A Task Pack execution → B intent verification → C business report. The skill spans the ENTIRE post-design workflow; do not narrow it to "the code execution phase".
- When the user references any existing design doc (specs/) or plan (plans/) and asks to review / audit / advance / execute / continue / 推进 / 审查 / 落地 / 动手 / 走流程, use multi-model-workflow:orchestrate-workflow — NOT superpowers:subagent-driven-development.
RULES

exit 0

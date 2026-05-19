#!/usr/bin/env bash
# multi-model-workflow: Codex SessionStart hook
# Injects Plugin V2-equivalent behavioral override rules.
# Must exit 0; never block session startup.

python3 - <<'PY' || true
import json

message = """[multi-model-workflow] Behavioral override active:

# 1. Environment check
- Repair chains (pack repair, plan revision, final review repair) use send_input to reuse an existing agent when an agent id is available.
- If the original agent cannot be reused, spawn the same agent_type with full context and record why reuse was unavailable.

# 2. Progressive reference loading
- Each orchestrate skill has its own references/ folder. References are loaded inline at point of use
  (dispatch step, routing step, etc.). Read them when you reach that instruction, not when entering the skill.

# 3. Entry routing rules
- When the user confirms a direction after discussion, use orchestrate-discovery to produce or refine a design document, then orchestrate-plan-writing to write the plan.
- AS SOON AS a design document is produced or exists, immediately enter orchestrate-workflow (entry gate) — it routes to the correct phase skill.
- When the user references any existing design doc (specs/) or plan (plans/) and asks to review / audit / advance / execute / continue / 推进 / 审查 / 落地 / 动手 / 走流程, use orchestrate-workflow (entry gate).

# 4. Skill chaining rules
- orchestrate-workflow selects Formal Orchestrate → orchestrate-discovery
- orchestrate-discovery (includes Design Review internally) returns DISCOVERY_READY → check issue hierarchy; missing → to-issues → orchestrate-plan-writing
- orchestrate-plan-writing (includes Plan Review internally) returns PLAN_CREATED → orchestrate-execution
- orchestrate-execution (pack dispatch + Pack Review per pack) returns EXECUTION_PASSED → orchestrate-final-review
- orchestrate-final-review (Final Review + business report) returns FINAL_REVIEW_PASSED → orchestrate-workflow Closing
- orchestrate-workflow selects READY_FOR_REPAIR → Direct Repair mini-route (workflow Step 8a)
- orchestrate-workflow selects Bug Investigation → root_cause_analyst → route by result (repair / formal orchestrate)
- Execution / Final Review: repair round 2 still fails → root_cause_analyst before round 3
- Final Review → NEEDS_EXECUTION 最多 1 次；第 2 次 → BLOCKED
- At any point: design/domain/UX gap → orchestrate-discovery; issue gap → to-issues; plan gap → orchestrate-plan-writing

# 5. Upstream skill routing
- diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs, to-issues
  remain callable from any orchestrate phase when their trigger applies.
  Each phase skill lists its own upstream triggers and write-back targets inline.
- Upstream skill calling protocol: only consume downstream-readable results. When upstream skill
  returns code changes / long-term docs / tracker mutations beyond current Scope, only execute
  within Scope Contract authorization. Write verdict back to phase-specified target before continuing.
- Allowed outputs per upstream skill:
  · grill-with-docs: clarified context, resolved term, domain decision, ADR/SPEC/GUIDE need
  · diagnose: current/desired behavior, reproduction/symptom, falsifiable hypotheses, key interfaces, regression target
  · zoom-out: module map, call chain, boundary context, test/config entrypoints
  · prototype: prototype question, verdict, decision artifact, validated/rejected option
  · improve-codebase-architecture: architecture finding, affected modules, test seam impact, recommended boundary
  · triage: issue category, ready state, AFK/HITL, blocked-by, issue brief
  · to-issues: confirmed vertical large/small issues, blocked-by, AFK/HITL

# 6. Compaction-durable constraints
- Before entering any phase skill: re-read .codex/multi-model-workflow/scope-<run_id>.md to confirm Scope Contract
  is still current (source artifacts, editable artifacts, out of scope haven't drifted since last phase).
  Run `git status --short --branch` to verify branch and dirty state match expectations.
- Resume Gate: a passed gate is only valid if source artifacts are unchanged since that gate. Source modified → re-enter that gate.
- PreToolUse/Bash automatically runs codex/hooks/cleanup-run-state.sh before git push / gh pr create / gh pr edit so runtime state is not published.
- Commit boundary = rollback boundary: design/plan repair, reviewed Task Pack, accepted finding repair, runtime sync each get separate commits when committing is requested.
- Hard Gates:
  · 没有验证证据，不得声称完成。
  · 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境。
  · Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
  · Design Review / Plan Review / Final Review 不可跳过（除非 Entry Gate 选择了 Direct Repair mini-route）。
  · upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点。
- 禁止:
  · 跳过 Design Review、Plan Review 或 Final Review。
  · 用技术语言向用户汇报。
  · 自己写生产代码（调度 worker）。
  · 每 task 一个 subagent（用 Task Pack）。
  · 超过循环上限不处理。

# 7. Agent roles and dispatch rules
- Agent roles: plan_writer (plan writing from design + issues), coding_worker (normal coding), complex_coding_worker (high-risk coding), code_explorer (narrow investigation), complex_code_explorer (deep investigation), root_cause_analyst (repair round 2 fail / bug investigation entry), docs_worker (documentation).
- Baseline code reviews use code_reviewer. Production-risk supplements use release_reviewer and never replace baseline review.
- ALL cross-model code reviews dispatch to external Claude via codex/reviewers/claude-subscription-review.sh for independent cross-model opinion, fixed to claude-opus-4-7 + high thinking effort.
- Do not call claude -p unless the user explicitly authorizes Agent SDK / Extra Usage credits.
- Parallel Task Pack execution uses isolation: assign disjoint write sets, use independent sub-agent workspaces when available, and let the coordinator integrate reviewed results.
"""

print(json.dumps({"systemMessage": message}, ensure_ascii=False))
PY

exit 0

#!/usr/bin/env bash
# multi-model-workflow: SessionStart hook
# Injects behavioral override rules. Re-injected on startup|clear|compact.
# Must exit 0 — never block session startup.

cat <<'RULES'
[multi-model-workflow] Behavioral override active:

# 1. Environment check
RULES

if [ -z "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" ]; then
  cat <<'ENVWARN'
[multi-model-workflow] WARNING: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is not set.
  SendMessage to existing agents will not work. All repairs will require new agent spawns.
  Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 for optimal multi-agent coordination.
ENVWARN
fi

cat <<'RULES'

# 2. Progressive reference loading
- Shared references live in ${CLAUDE_PLUGIN_ROOT}/references/. Do NOT load all eagerly.
  Each orchestrate skill says which references to read inline at the point of use (dispatch step, routing step, etc.).
  Read them when you reach that instruction, not when entering the skill.

# 3. Entry routing rules
- When the user confirms a direction after discussion, use multi-model-workflow:orchestrate-discovery to produce or refine a design document, then multi-model-workflow:orchestrate-plan-writing to write the plan.
- AS SOON AS a design document is produced or exists, immediately enter multi-model-workflow:orchestrate-workflow (entry gate) — it routes to the correct phase skill from Phase 0a onward.
- When the user references any existing design doc (specs/) or plan (plans/) and asks to review / audit / advance / execute / continue / 推进 / 审查 / 落地 / 动手 / 走流程, use multi-model-workflow:orchestrate-workflow (entry gate).

# 4. Skill chaining rules
- orchestrate-workflow selects Formal Orchestrate → orchestrate-discovery
- orchestrate-discovery returns DISCOVERY_READY → orchestrate-design-review
- orchestrate-design-review passes → check issue hierarchy; missing → to-issues → orchestrate-plan-writing
- orchestrate-plan-writing returns PLAN_CREATED → orchestrate-plan-review
- orchestrate-plan-review passes → orchestrate-execution
- orchestrate-execution: all packs pass → orchestrate-final-review
- orchestrate-final-review passes → business report → branch finishing → done
- orchestrate-workflow selects Direct Repair → orchestrate-direct-repair
- orchestrate-workflow selects Bug Investigation → root-cause-analyst → route by result (direct-repair / formal orchestrate)
- Phase A/B: repair round 2 still fails → root-cause-analyst before round 3
- At any point: design/domain/UX gap → orchestrate-discovery; issue gap → to-issues; plan gap → orchestrate-plan-writing

# 5. Upstream skill routing
- diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs, to-issues
  remain callable from any orchestrate skill via Skill tool.
  Each phase skill lists its own upstream triggers and write-back targets inline.
  coordinator-tools.md defines the calling protocol; phase skills define when and where.

# 6. Compaction-durable constraints
- Before entering any phase skill: re-read .claude/multi-model-workflow/scope-<run_id>.md to confirm Scope Contract
  is still current (source artifacts, editable artifacts, out of scope haven't drifted since last phase).
  Run `git status --short --branch` to verify branch and dirty state match expectations.
- Resume Gate: a passed gate is only valid if source artifacts are unchanged since that gate. Source modified → re-enter that gate.
- Commit boundary = rollback boundary: design/plan repair, reviewed Task Pack, accepted finding repair each get separate commits.
- Hard Gates:
  · 没有验证证据，不得声称完成。
  · 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境。
  · Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
  · Phase 0a / Phase 0b / Phase B 不可跳过（除非 Entry Gate 选择了 Answer-only / One-shot Review / Direct Repair）。
  · upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点。
- 禁止:
  · 跳过 Phase 0 或 Phase B。
  · 用技术语言向用户汇报。
  · 自己写生产代码（调度 worker）。
  · 每 task 一个 subagent（用 Task Pack）。
  · 超过循环上限不处理。

# 7. Agent roles and dispatch rules
- Agent roles: plan-writer (Opus 4.7 1M, plan writing from design + issues), pack-executor (Sonnet, normal coding), complex-pack-executor (Opus, high-risk coding), code-explorer (Sonnet, narrow investigation), complex-code-explorer (Opus, deep investigation), root-cause-analyst (Opus, repair round 2 fail / bug investigation entry), docs-worker (Sonnet, documentation).
- ALL code reviews dispatched to Codex via codex:codex-rescue for independent cross-model opinion. No Claude-side reviewer agent exists.
- Parallel Task Pack execution uses isolation: "worktree" in Agent tool call to prevent file conflicts.
RULES

exit 0

#!/usr/bin/env bash
# multi-model-workflow: Codex SessionStart hook
# Injects Plugin V2-equivalent behavioral override rules.
# Must exit 0; never block session startup.

python3 - <<'PY' || true
import json

message = """[multi-model-workflow] Behavioral override active:

# 1. Environment check
- Repair chains rely on send_input when an existing agent id is available.
- If the original agent cannot be reused, spawn the same agent_type with full context and record why reuse was unavailable.

# 2. Entry routing
- User confirms direction → orchestrate-discovery → orchestrate-plan-writing
- Design doc exists / referenced → orchestrate-workflow (entry gate)
- User asks to review / advance / execute / 推进 / 审查 / 落地 / 走流程 → orchestrate-workflow

# 3. Skill namespace
- Orchestrate skills (short name, NO plugin prefix): orchestrate-workflow, orchestrate-discovery, orchestrate-plan-writing, orchestrate-execution, orchestrate-final-review, orchestrate-multi-pr-merge
- User-level skills (short name, NO plugin prefix): diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs, to-issues

# 4. Hard gates
- 没有验证证据，不得声称完成
- 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境
- 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker
- Design Review / Plan Review / Final Review 不可跳过（除非 Direct Repair mini-route）
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点
- 不自己写生产代码——调度 worker
- 不用技术语言向用户汇报
- Review 通过 Codex codex-companion.mjs 四步协议派发（按 external-review-lanes.md）；不使用 Claude CLI、不使用 claude -p
- Parallel Task Pack execution 使用 disjoint write sets / independent workspaces

# 5. Compaction recovery
- 进入任何 phase skill 前：re-read .codex/multi-model-workflow/scope-<run_id>.md 确认 Scope Contract
- git status --short --branch 验证 branch 和 dirty state
- Resume Gate: source artifacts 改过 → 重进该 gate
"""

print(json.dumps({"systemMessage": message}, ensure_ascii=False))
PY

exit 0

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
[multi-model-workflow] ERROR: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is not set.
  修复链路依赖 SendMessage。请设置 CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 后重新启动。
ENVWARN
fi

cat <<'RULES'

# 2. Entry routing
- User confirms direction → multi-model-workflow:orchestrate-discovery → multi-model-workflow:orchestrate-plan-writing
- Design doc exists / referenced → multi-model-workflow:orchestrate-workflow (entry gate)
- User asks to review / advance / execute / 推进 / 审查 / 落地 / 走流程 → multi-model-workflow:orchestrate-workflow

# 3. Skill namespace
- Plugin skills (multi-model-workflow: prefix): orchestrate-workflow, orchestrate-discovery, orchestrate-plan-writing, orchestrate-execution, orchestrate-final-review, orchestrate-multi-pr-merge
- User-level skills (short name, NO prefix): diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs, to-issues

# 4. Hard gates
- 没有验证证据，不得声称完成
- 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境
- 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker
- Design Review / Plan Review / Final Review 不可跳过（除非 Direct Repair mini-route）
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点
- 不自己写生产代码——调度 worker
- 不用技术语言向用户汇报
- Review 派发步骤已内联到各 dispatch 模板中，Read 对应的 review dispatch reference 即可
- Parallel Task Pack execution 使用 isolation: "worktree"

# 5. Compaction recovery
- 进入任何 phase skill 前：re-read .claude/multi-model-workflow/scope-<run_id>.md 确认 Scope Contract
- git status --short --branch 验证 branch 和 dirty state
- Resume Gate: source artifacts 改过 → 重进该 gate
RULES

exit 0

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

echo "=== test_claude_surface.sh ==="

# shellcheck source=../lib/runtime.sh
. "$SCRIPT_DIR/../lib/runtime.sh"
[ "$MMW_STATE_SUBDIR" = ".claude/multi-model-workflow" ] && ok "状态平面保持 Claude Code 路径" || no "状态平面路径错误"
[ "$MMW_WORKTREES_REL" = ".claude/worktrees" ] && ok "worktree 根保持 Claude Code 路径" || no "worktree 根路径错误"

for path in \
  agents/code-reviewer.md \
  scripts/note.sh \
  commands/approve-design.md \
  scripts/worker.sh \
  scripts/progress.sh \
  scripts/steer.sh \
  scripts/package-phase.sh \
  scripts/release-flow.sh \
  skills/worktree-build/SKILL.md \
  skills/worktree-plan/SKILL.md \
  skills/worktree-review/SKILL.md; do
  [ -f "$PLUGIN_DIR/$path" ] && ok "功能入口存在: $path" || no "功能入口缺失: $path"
done

HOOKS="$PLUGIN_DIR/hooks/hooks.json"
[ "$(jq '[.hooks.PreToolUse[],.hooks.PostToolUse[] | select(.matcher != "Bash")] | length' "$HOOKS")" = "0" ] \
  && ok "工具 hook 只接 Bash" || no "工具 hook 含非 Bash matcher"
jq -e '.hooks.SessionStart[0].hooks[0].command | contains("${CLAUDE_PLUGIN_ROOT}")' "$HOOKS" >/dev/null \
  && ok "SessionStart 从 Claude plugin 根启动" || no "SessionStart 未绑定 Claude plugin 根"
[ "$(jq -r '.hooks | has("UserPromptSubmit")' "$HOOKS")" = "false" ] \
  && ok "相位锚已拆(SessionStart 开场回报一次即可)" || no "UserPromptSubmit 残留"

HELP="$(bash "$PLUGIN_DIR/scripts/mmw.sh" help)"
for command in "worker dispatch" "worker plan-dispatch" "review start" "progress render" "release init" "note set" "approve --report" "pin --produced"; do
  printf '%s' "$HELP" | grep -q "$command" && ok "CLI 能力保留: $command" || no "CLI 能力缺失: $command"
done

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

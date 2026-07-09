#!/usr/bin/env bash
# 命令层 + skill 入口的双宿主可移植性:
#   Droid 不支持 Markdown 命令里的 !`shell` 动态注入,也不给主线程 ${CLAUDE_PLUGIN_ROOT}。
#   所以命令不许用 !注入、不许硬依赖 ${CLAUDE_PLUGIN_ROOT};要跑 mmw 的命令必须自带宿主感知定位块。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CMD_DIR="$PLUGIN_DIR/commands"
SKILL="$PLUGIN_DIR/skills/orchestrate/SKILL.md"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_commands_portable.sh ==="

# 定位块特征:宿主感知 + find 命中 mmw.sh
LOCATOR_RE='find "\$P" -type f -path .\*multi-model-workflow\*/scripts/mmw.sh'

for f in "$CMD_DIR"/*.md; do
  name="$(basename "$f")"
  # 1. 无 Markdown !注入(行首 !`)
  if grep -qE '^!`' "$f"; then no "$name 仍含 !注入"; else ok "$name 无 !注入"; fi
  # 2. 无 ${CLAUDE_PLUGIN_ROOT} 硬依赖
  if grep -q 'CLAUDE_PLUGIN_ROOT' "$f"; then no "$name 仍硬依赖 CLAUDE_PLUGIN_ROOT"; else ok "$name 无 CLAUDE_PLUGIN_ROOT"; fi
  # 3. 引用 mmw 的命令必须自带定位块
  if grep -qE '\bmmw\b' "$f"; then
    if grep -qE "$LOCATOR_RE" "$f"; then ok "$name 含宿主感知 mmw 定位块"; else no "$name 引用 mmw 却缺定位块"; fi
  fi
done

# 4. SKILL 入口 Step 0 必须自带定位块(不靠环境变量)
grep -qE "$LOCATOR_RE" "$SKILL" && ok "SKILL Step 0 含定位块" || no "SKILL Step 0 缺定位块"
grep -q 'CLAUDE_PLUGIN_ROOT' "$SKILL" && no "SKILL 仍含 CLAUDE_PLUGIN_ROOT" || ok "SKILL 无 CLAUDE_PLUGIN_ROOT"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

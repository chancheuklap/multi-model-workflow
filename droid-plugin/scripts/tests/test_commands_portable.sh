#!/usr/bin/env bash
# 命令层 + skill 入口的 Droid 原生可移植性。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CMD_DIR="$PLUGIN_DIR/commands"
SKILL="$PLUGIN_DIR/skills/orchestrate/SKILL.md"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_commands_portable.sh ==="

# 定位块特征:只扫 Factory 插件目录并命中专属插件。
LOCATOR_RE='multi-model-workflow-droid'

for f in "$CMD_DIR"/*.md; do
  name="$(basename "$f")"
  # 1. 无 Markdown !注入(行首 !`)
  if grep -qE '^!`' "$f"; then no "$name 仍含 !注入"; else ok "$name 无 !注入"; fi
  # 2. 引用 mmw 的命令必须自带定位块
  if grep -qE '\bmmw\b' "$f"; then
    if grep -qE "$LOCATOR_RE" "$f"; then ok "$name 含 Droid mmw 定位块"; else no "$name 引用 mmw 却缺定位块"; fi
  fi
done

# 3. SKILL 入口 Step 0 必须自带定位块。
grep -qE "$LOCATOR_RE" "$SKILL" && ok "SKILL Step 0 含定位块" || no "SKILL Step 0 缺定位块"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

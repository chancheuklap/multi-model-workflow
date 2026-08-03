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

# 定位块特征:读实际激活安装位 installed_plugins.json 的 installPath(不扫缓存挑版本号)。
LOCATOR_RE='installed_plugins\.json'

for f in "$CMD_DIR"/*.md; do
  name="$(basename "$f")"
  # 1. 无 Markdown !注入(行首 !`)
  if grep -qE '^!`' "$f"; then no "$name 仍含 !注入"; else ok "$name 无 !注入"; fi
  # 2. 引用 mmw 的命令必须自带激活位定位块,且不做版本号扫描(sort -V 挑最高 ≠ 正在运行的)
  if grep -qE '\bmmw\b' "$f"; then
    if grep -qE "$LOCATOR_RE" "$f" && grep -q 'installPath' "$f" && grep -q 'multi-model-workflow-droid' "$f"; then ok "$name 含 Droid 激活位定位块"; else no "$name 引用 mmw 却缺激活位定位块"; fi
    if grep -q 'sort -V' "$f"; then no "$name 定位块仍扫缓存挑版本号"; else ok "$name 定位块不做版本号扫描"; fi
  fi
done

# 3. SKILL 入口 Step 0 必须自带定位块。
grep -qE "$LOCATOR_RE" "$SKILL" && grep -q 'installPath' "$SKILL" && ok "SKILL Step 0 含激活位定位块" || no "SKILL Step 0 缺定位块"
grep -q 'sort -V' "$SKILL" && no "SKILL 定位块仍扫缓存挑版本号" || ok "SKILL 定位块不做版本号扫描"
# 4. Droid 恢复已有 worktree 后，每个独立工具调用都必须继续钉住该 worktree。
grep -q '每次 `Execute` 都先 `cd <worktree_path>`' "$SKILL" \
  && grep -q '文件工具使用该 worktree 下的绝对路径' "$SKILL" \
  && ok "SKILL 续跑跨独立工具调用保持 worktree 上下文" \
  || no "SKILL 续跑未钉住后续工具调用的 worktree 上下文"

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# pi prompt templates + orchestrate skill 的运行时定位合同。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROMPT_DIR="$PLUGIN_DIR/prompts"
SKILL="$PLUGIN_DIR/skills/orchestrate/SKILL.md"
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }

echo '=== test_commands_portable.sh ==='
count=0
for f in "$PROMPT_DIR"/*.md; do
  count=$((count+1)); name="$(basename "$f")"
  head -1 "$f" | grep -qx -- '---' && grep -q '^description:' "$f" \
    && ok "$name 有 pi prompt frontmatter" || no "$name frontmatter"
  if grep -qE '\bmmw\b' "$f"; then
    grep -q '\.pi/agent/settings.json' "$f" && grep -q 'pi-plugin' "$f" \
      && ok "$name 含 pi 本地包定位块" || no "$name 缺 pi 定位块"
    grep -q 'sort -V' "$f" && no "$name 不应扫描版本缓存" || ok "$name 不扫版本缓存"
  fi
done
[ "$count" = 11 ] && ok '11 个 prompt templates 齐全' || no "prompt 数量=$count"
[ ! -d "$PLUGIN_DIR/commands" ] && ok '旧 commands/ 已删除' || no 'commands/ 未删除'

grep -q '\.pi/agent/settings.json' "$SKILL" && grep -q 'pi-plugin' "$SKILL" \
  && ok 'orchestrate Step 0 含 pi 包定位块' || no 'orchestrate 缺定位块'
grep -q '每次 `bash` 都先 `cd <worktree_path>`' "$SKILL" \
  && grep -q '文件工具使用该 worktree 下的绝对路径' "$SKILL" \
  && ok '续跑跨独立工具调用保持 worktree 上下文' || no '续跑未钉 worktree'

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

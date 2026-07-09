#!/usr/bin/env bash
# test_skill_parity.sh —— worktree-{build,review} 单源软链完整性
# codex-skills/worktree-{build,review} 是指向 plugin/skills/ 同名目录的软链(单源:
# 改 plugin/skills 一处,两宿主都同步;codex-skills 仅供 ~/.agents/skills 软链安装用)。
# 本测试断言软链没断 + 两路径读到同一份(SKILL.md + references/* 全逐字一致)。
# 漂移场景:有人把 codex-skills 软链删了改回真实目录且改了内容 → diff 报差异 → FAIL。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPO_DIR="$(cd "$PLUGIN_DIR/.." && pwd)"
CODEX_SKILLS="$REPO_DIR/codex-skills"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_skill_parity.sh ==="

if [ ! -d "$CODEX_SKILLS" ]; then
  echo "  SKIP: $CODEX_SKILLS 不存在(结构已变);测试退出 0"
  exit 0
fi

for s in worktree-build worktree-review; do
  P="$PLUGIN_DIR/skills/$s"
  C="$CODEX_SKILLS/$s"
  [ -d "$P" ] || { no "plugin 副本缺 $s"; continue; }
  [ -e "$C" ] || { no "codex-skills 软链缺失 $s"; continue; }
  # 软链完整性:codex-skills/<s> 应是符号链接(单源),不是真实目录
  [ -L "$C" ] && ok "$s 是软链(单源指向 plugin/skills)" || no "$s 不是软链(单源结构破坏;应是 symlink → plugin/skills/$s)"
  ok "两路径都在: $s"

  # SKILL.md + references/* 全逐字一致(软链同源,必然一致;不一致=软链断了或被换成真实目录)
  for f in "$P"/SKILL.md "$P"/references/*.md; do
    [ -f "$f" ] || continue
    rel="${f#$P/}"
    if diff -q "$f" "$C/$rel" >/dev/null 2>&1; then
      ok "$s/$rel 单源一致"
    else
      no "$s/$rel 两路径不一致(软链断或被换成真实目录且漂移)"
    fi
  done
done

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

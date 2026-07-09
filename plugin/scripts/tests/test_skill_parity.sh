#!/usr/bin/env bash
# test_skill_parity.sh —— worktree-{build,review} 两副本方法论防漂移
# plugin/skills/(Droid 用)与 codex-skills/(Claude 侧 Codex CLI 用)是同一套方法论的两副本。
# references/* 是方法论本体,必须逐字一致;SKILL.md 框架称呼允许不同(Droid 版宿主中立)。
# 防漂移:改一份忘改另一份 → 此测试报 FAIL。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPO_DIR="$(cd "$PLUGIN_DIR/.." && pwd)"
CODEX_SKILLS="$REPO_DIR/codex-skills"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_skill_parity.sh ==="

# codex-skills 不在仓库(结构变了)→ skip,不硬失败
if [ ! -d "$CODEX_SKILLS" ]; then
  echo "  SKIP: $CODEX_SKILLS 不存在(结构已变,单源化?);测试退出 0"
  exit 0
fi

for s in worktree-build worktree-review; do
  P="$PLUGIN_DIR/skills/$s"
  C="$CODEX_SKILLS/$s"
  [ -d "$P" ] || { no "plugin 副本缺 $s"; continue; }
  [ -d "$C" ] || { no "codex-skills 副本缺 $s"; continue; }
  ok "两副本都存在: $s"

  # references/* 逐字一致(方法论本体,两宿主同源)
  for f in "$P"/references/*.md; do
    [ -f "$f" ] || continue
    name="$(basename "$f")"
    if diff -q "$f" "$C/references/$name" >/dev/null 2>&1; then
      ok "$s/references/$name 逐字一致"
    else
      no "$s/references/$name 两副本漂移(改了一处忘另一处;方法论本体必须同源)"
    fi
  done

  # SKILL.md 必须都存在(框架称呼允许不同,不逐字比对)
  [ -f "$P/SKILL.md" ] && [ -f "$C/SKILL.md" ] && ok "$s/SKILL.md 两副本都在(称呼允许差异)" \
    || no "$s/SKILL.md 缺一份"
done

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

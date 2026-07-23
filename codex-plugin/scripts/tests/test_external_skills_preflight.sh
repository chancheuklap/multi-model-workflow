#!/usr/bin/env bash
# 外部方法论技能只做运行前提示：plugin 不复制、不锁版本，也不把缺装伪装成可用。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MMW="$SCRIPT_DIR/../mmw.sh"
REQUIRED="tdd codebase-design diagnosing-bugs domain-modeling prototype grilling to-tickets triage improve-codebase-architecture"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_external_skills_preflight.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
EMPTY_HOME="$TMP/home"
mkdir -p "$REPO" "$EMPTY_HOME"
git -C "$REPO" init -q
git -C "$REPO" config user.email t@t
git -C "$REPO" config user.name t

OUT="$(cd "$REPO" && HOME="$EMPTY_HOME" bash "$MMW" where 2>&1)"
if printf '%s\n' "$OUT" | grep -q "UNMANAGED"; then
  ok "缺装提示不阻断正常选路"
else
  no "缺装时 where 未保持可用"
fi

missing_ok=yes
for skill in $REQUIRED; do
  if ! printf '%s\n' "$OUT" | grep -q "$skill"; then
    missing_ok=no
  fi
done
if [ "$missing_ok" = yes ]; then
  ok "缺装提示逐项列出真实依赖"
else
  no "缺装提示漏掉依赖"
fi
if printf '%s\n' "$OUT" | grep -q "npx skills@latest add mattpocock/skills"; then
  ok "缺装提示给出用户自己的安装入口"
else
  no "缺装提示没有安装入口"
fi

for skill in $REQUIRED; do
  mkdir -p "$EMPTY_HOME/.agents/skills/$skill"
  printf '%s\n' "---" "name: $skill" "---" > "$EMPTY_HOME/.agents/skills/$skill/SKILL.md"
done
OUT2="$(cd "$REPO" && HOME="$EMPTY_HOME" bash "$MMW" where 2>&1)"
if printf '%s\n' "$OUT2" | grep -q "外部技能.*缺装"; then
  no "技能齐备时仍然告警"
else
  ok "技能齐备时零告警"
fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

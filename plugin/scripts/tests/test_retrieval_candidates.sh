#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }

# shellcheck source=../lib/retrieval-candidates.sh
. "$SCRIPT_DIR/../lib/retrieval-candidates.sh"

cat >"$TMP/valid.json" <<'JSON'
[
  {
    "summary": "candidate",
    "tool": "serena",
    "fallback_reason": "",
    "locators": ["src/app.py:10"],
    "status": "used",
    "query": "find app"
  }
]
JSON
mmw_retrieval_candidates_snapshot "$TMP/valid.json" "$TMP/normalized.json"
jq -e 'length == 1 and .[0].tool == "serena" and (.[0] | keys) == ["fallback_reason","locators","query","status","summary","tool"]' "$TMP/normalized.json" >/dev/null \
  && ok "六字段候选被规范化" || no "有效候选规范化失败"
mmw_retrieval_candidates_snapshot "" "$TMP/empty.json"
[ "$(jq -c . "$TMP/empty.json")" = "[]" ] && ok "省略候选归一为空数组" || no "空候选归一失败"

jq '.[0].extra = true' "$TMP/valid.json" >"$TMP/extra.json"
if mmw_retrieval_candidates_snapshot "$TMP/extra.json" "$TMP/extra-out.json" >/dev/null 2>&1; then
  no "额外字段未被拒绝"
else
  ok "额外字段 fail-closed"
fi
jq '.[0].locators = [7]' "$TMP/valid.json" >"$TMP/bad-locator.json"
if mmw_retrieval_candidates_snapshot "$TMP/bad-locator.json" "$TMP/bad-out.json" >/dev/null 2>&1; then
  no "非字符串 locator 未被拒绝"
else
  ok "locator 类型 fail-closed"
fi
if mmw_retrieval_candidates_snapshot "relative.json" "$TMP/relative-out.json" >/dev/null 2>&1; then
  no "相对路径未被拒绝"
else
  ok "输入只接受绝对路径"
fi

prompt="$(mmw_retrieval_candidates_prompt "$TMP/normalized.json")"
case "$prompt" in
  *"仅候选，不代表本 worker 调过工具"*"源码 Read/grep/rg 亲验"*"fallback_reason"*) ok "prompt 区分候选、实调工具与源码证据" ;;
  *) no "prompt 证据纪律缺失" ;;
esac

for file in \
  skills/orchestrate/references/retrieval-doctrine.md \
  skills/worktree-build/SKILL.md \
  skills/worktree-plan/SKILL.md \
  skills/worktree-review/references/method.md; do
  grep -q '结构候选' "$PLUGIN/$file" && ok "角色纪律已接入: $file" || no "角色纪律缺失: $file"
done
REVIEW_REPO="$TMP/review-repo"
git -C "$TMP" init -q review-repo
git -C "$REVIEW_REPO" config user.email test@example.com
git -C "$REVIEW_REPO" config user.name Test
printf 'seed\n' >"$REVIEW_REPO/seed.txt"
git -C "$REVIEW_REPO" add seed.txt
git -C "$REVIEW_REPO" commit -qm seed
(cd "$REVIEW_REPO" && bash "$PLUGIN/scripts/review.sh" start --stage final --source seed.txt --retrieval-candidates "$TMP/valid.json" >/dev/null)
REVIEW_STATE="$REVIEW_REPO/.claude/multi-model-workflow"
jq -e 'length == 1 and .[0].query == "find app"' "$REVIEW_STATE/retrieval-candidates-final.json" >/dev/null \
  && grep -q 'find app' "$REVIEW_STATE/review-brief.md" && grep -q '源码 Read/grep/rg 亲验' "$REVIEW_STATE/review-brief.md" \
  && ok "review start 真入口快照并传递候选" || no "review start 真入口候选接线"
if (cd "$REVIEW_REPO" && bash "$PLUGIN/scripts/review.sh" start --stage final --source seed.txt --retrieval-candidates relative.json >/dev/null 2>&1); then
  no "review start 接受相对候选路径"
else
  ok "review start 真入口 fail-closed"
fi

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

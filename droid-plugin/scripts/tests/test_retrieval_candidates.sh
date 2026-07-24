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
[{"summary":"candidate","tool":"serena","fallback_reason":"dynamic import unsupported","locators":["src/app.py:10"],"status":"unsupported","query":"dynamic import refs"}]
JSON
mmw_retrieval_candidates_snapshot "$TMP/valid.json" "$TMP/normalized.json"
jq -e 'length == 1 and .[0].status == "unsupported" and (.[0] | keys) == ["fallback_reason","locators","query","status","summary","tool"]' "$TMP/normalized.json" >/dev/null \
  && ok "六字段候选被规范化" || no "有效候选规范化失败"
mmw_retrieval_candidates_snapshot "" "$TMP/empty.json"
[ "$(jq -c . "$TMP/empty.json")" = "[]" ] && ok "省略候选归一为空数组" || no "空候选归一失败"

jq '.[0].extra = true' "$TMP/valid.json" >"$TMP/extra.json"
if mmw_retrieval_candidates_snapshot "$TMP/extra.json" "$TMP/extra-out.json" >/dev/null 2>&1; then no "额外字段未被拒绝"; else ok "额外字段 fail-closed"; fi
jq '.[0].locators = [7]' "$TMP/valid.json" >"$TMP/bad-locator.json"
if mmw_retrieval_candidates_snapshot "$TMP/bad-locator.json" "$TMP/bad-out.json" >/dev/null 2>&1; then no "非字符串 locator 未被拒绝"; else ok "locator 类型 fail-closed"; fi
if mmw_retrieval_candidates_snapshot "relative.json" "$TMP/relative-out.json" >/dev/null 2>&1; then no "相对路径未被拒绝"; else ok "输入只接受绝对路径"; fi

prompt="$(mmw_retrieval_candidates_prompt "$TMP/normalized.json")"
if [[ "$prompt" == *"上游 Serena 候选"* ]] \
  && [[ "$prompt" == *"自己实际 Execute 的 Graphify"* ]] \
  && [[ "$prompt" == *"fallback_reason"* ]]; then
  ok "Droid prompt 区分上游 Serena 与本机 Graphify"
else
  no "Droid prompt 宿主边界缺失"
fi

for script in worker.sh review.sh; do
  grep -q -- '--retrieval-candidates' "$PLUGIN/scripts/$script" \
    && grep -q 'retrieval-candidates.*json' "$PLUGIN/scripts/$script" \
    && ok "$script 传输并快照候选" || no "$script 候选接线缺失"
done
for file in \
  skills/orchestrate/references/retrieval-doctrine.md \
  skills/worktree-build/SKILL.md \
  skills/worktree-plan/SKILL.md \
  skills/worktree-review/references/method.md; do
  grep -q '结构候选' "$PLUGIN/$file" && ok "角色纪律已接入: $file" || no "角色纪律缺失: $file"
done

droid_count="$(find "$PLUGIN/droids" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
empty_mcp_count="$(grep -l '^mcpServers: \[\]$' "$PLUGIN"/droids/*.md | wc -l | tr -d ' ')"
[ "$droid_count" = "$empty_mcp_count" ] \
  && ok "全部 Droid 角色保持 mcpServers 为空" || no "Droid 角色获得了 MCP server"
grep -q 'retrieval_candidates' "$PLUGIN/scripts/investigate.sh" \
  && grep -q '严格六字段' "$PLUGIN/scripts/investigate.sh" \
  && grep -q 'Execute Graphify' "$PLUGIN/scripts/investigate.sh" \
  && ok "Droid investigate 接入严格候选和 Graphify fallback" || no "Droid investigate 候选接线缺失"

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

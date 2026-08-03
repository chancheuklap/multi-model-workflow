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
if [[ "$prompt" == *"上游候选"* ]] \
  && [[ "$prompt" == *"worker 自己实际调用的工具"* ]] \
  && [[ "$prompt" == *"Serena/Graphify MCP 或 Execute graphify CLI"* ]] \
  && [[ "$prompt" == *"fallback_reason"* ]]; then
  ok "Droid prompt 区分上游候选与 worker 实际工具"
else
  no "Droid prompt 宿主边界缺失"
fi

for file in \
  skills/orchestrate/references/retrieval-doctrine.md \
  skills/worktree-build/SKILL.md \
  skills/worktree-plan/SKILL.md \
  skills/worktree-review/references/method.md; do
  grep -q '结构候选' "$PLUGIN/$file" && ok "角色纪律已接入: $file" || no "角色纪律缺失: $file"
done

# MCP 授权政策:插件 mcp.json 注册 serena(只读四符号工具)+graphify;除 investigate-synthesizer 外
# 全部角色 droid 以 mcpServers 获授权;synthesizer 只综合不重查,保持空授权。
jq -e '.mcpServers.serena and .mcpServers.graphify' "$PLUGIN/mcp.json" >/dev/null \
  && ok "插件 mcp.json 注册 serena+graphify" || no "插件 mcp.json 缺 server"
[ "$(jq -c '.mcpServers.serena.enabledTools | sort' "$PLUGIN/mcp.json")" = '["find_implementations","find_referencing_symbols","find_symbol","get_symbols_overview"]' ] \
  && ok "serena 只放行四个只读符号工具" || no "serena 工具面过宽"
jq -e '.mcpServers.serena.command == "serena" and .mcpServers.graphify.command == "graphify-mcp"' "$PLUGIN/mcp.json" >/dev/null \
  && ok "MCP server 走 PATH 裸命令(无机器路径)" || no "MCP server 硬编码路径"
droid_count="$(find "$PLUGIN/droids" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
mcp_roles="$(grep -l '^mcpServers: \["serena", "graphify"\]$' "$PLUGIN"/droids/*.md | wc -l | tr -d ' ')"
[ "$mcp_roles" = "$((droid_count - 1))" ] \
  && ! grep -q 'serena' "$PLUGIN/droids/investigate-synthesizer.md" \
  && ok "除 synthesizer 外全部角色获得 serena/graphify 授权" || no "角色 MCP 授权面错误"
REVIEW_REPO="$TMP/review-repo"
git -C "$TMP" init -q review-repo
git -C "$REVIEW_REPO" config user.email test@example.com
git -C "$REVIEW_REPO" config user.name Test
printf 'seed\n' >"$REVIEW_REPO/seed.txt"
git -C "$REVIEW_REPO" add seed.txt
git -C "$REVIEW_REPO" commit -qm seed
(cd "$REVIEW_REPO" && bash "$PLUGIN/scripts/review.sh" start --stage final --source seed.txt --retrieval-candidates "$TMP/valid.json" >/dev/null)
REVIEW_STATE="$REVIEW_REPO/.factory/multi-model-workflow"
jq -e 'length == 1 and .[0].query == "dynamic import refs"' "$REVIEW_STATE/retrieval-candidates-final.json" >/dev/null \
  && grep -q 'dynamic import refs' "$REVIEW_STATE/review-brief.md" && grep -q '上游结构候选' "$REVIEW_STATE/review-brief.md" \
  && ok "review start 真入口快照并传递候选" || no "review start 真入口候选接线"
if (cd "$REVIEW_REPO" && bash "$PLUGIN/scripts/review.sh" start --stage final --source seed.txt --retrieval-candidates relative.json >/dev/null 2>&1); then
  no "review start 接受相对候选路径"
else
  ok "review start 真入口 fail-closed"
fi

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

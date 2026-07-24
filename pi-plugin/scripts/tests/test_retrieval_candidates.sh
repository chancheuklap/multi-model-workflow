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
[{"summary":"candidate","tool":"graphify","fallback_reason":"source verification required","locators":["src/app.py:10"],"status":"used","query":"affected app"}]
JSON
mmw_retrieval_candidates_snapshot "$TMP/valid.json" "$TMP/normalized.json"
jq -e 'length == 1 and .[0].tool == "graphify" and (.[0] | keys) == ["fallback_reason","locators","query","status","summary","tool"]' "$TMP/normalized.json" >/dev/null \
  && ok "六字段候选被规范化" || no "有效候选规范化失败"
mmw_retrieval_candidates_snapshot "" "$TMP/empty.json"
[ "$(jq -c . "$TMP/empty.json")" = "[]" ] && ok "省略候选归一为空数组" || no "空候选归一失败"

jq '.[0].extra = true' "$TMP/valid.json" >"$TMP/extra.json"
if mmw_retrieval_candidates_snapshot "$TMP/extra.json" "$TMP/extra-out.json" >/dev/null 2>&1; then no "额外字段未被拒绝"; else ok "额外字段 fail-closed"; fi
jq '.[0].locators = [7]' "$TMP/valid.json" >"$TMP/bad-locator.json"
if mmw_retrieval_candidates_snapshot "$TMP/bad-locator.json" "$TMP/bad-out.json" >/dev/null 2>&1; then no "非字符串 locator 未被拒绝"; else ok "locator 类型 fail-closed"; fi
if mmw_retrieval_candidates_snapshot "relative.json" "$TMP/relative-out.json" >/dev/null 2>&1; then no "相对路径未被拒绝"; else ok "输入只接受绝对路径"; fi

prompt="$(mmw_retrieval_candidates_prompt "$TMP/normalized.json")"
case "$prompt" in
  *"仅候选，不代表本 worker 调过工具"*"源码 Read/grep/rg 亲验"*"fallback_reason"*) ok "prompt 区分候选、实调工具与源码证据" ;;
  *) no "prompt 证据纪律缺失" ;;
esac

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

serena_tools='mcp:serena/find_symbol mcp:serena/find_referencing_symbols mcp:serena/get_symbols_overview mcp:serena/find_implementations'
roles='code-explorer investigate-topic plan-writer pack-executor pack-executor-capable reviewer-design-a reviewer-design-b reviewer-plan-a reviewer-plan-b reviewer-final-a reviewer-final-b'
for role in $roles; do
  file="$PLUGIN/agents-roster/$role.md"
  missing=0
  for tool in $serena_tools; do grep -q "$tool" "$file" || missing=1; done
  [ "$missing" -eq 0 ] || no "Serena 工具缺失: $role"
done
if grep -q 'mcp:serena/' "$PLUGIN/agents-roster/investigate-synthesizer.md"; then
  no "synthesizer 不应获得 Serena"
else
  ok "仅 11 个源码角色获得 Serena，synthesizer 排除"
fi
[ "$(grep -l 'mcp:serena/find_symbol' "$PLUGIN"/agents-roster/*.md | wc -l | tr -d ' ')" = 11 ] \
  && ok "Serena 角色集合精确为 11" || no "Serena 角色数量漂移"
node --input-type=module -e '
  import fs from "node:fs";
  const text = fs.readFileSync(process.argv[1], "utf8");
  for (const needle of ["retrieval_candidates", "fallback_reason", "动态 await import()"])
    if (!text.includes(needle)) process.exit(1);
' "$PLUGIN/workflows/investigate-internal.workflow.js" \
  && ok "internal workflow 接入严格候选与盲区说明" || no "internal workflow 候选接线缺失"

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# Native subagent 的返回只经过无状态合同校验；不创建 investigate run 或账本。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTRACT="$SCRIPT_DIR/../investigate-contract.sh"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_investigate_contract.sh ==="

INTERNAL='{"topic":"module-boundary","findings":[
  {"claim":"kept","locator":"src/app.ts:12-18","confidence":"high"},
  {"claim":"low","locator":"src/app.ts:20","confidence":"low"},
  {"claim":"missing","locator":"","confidence":"medium"},
  {"claim":"url in internal","locator":"https://example.com","confidence":"high"},
  {"claim":"url port looks like line","locator":"https://example.com:443","confidence":"high"}
],"summary":"current state","gaps":["one gap"]}'
FILTERED="$(printf '%s\n' "$INTERNAL" | bash "$CONTRACT" topic --mode internal --expected-topic module-boundary)"
if [ "$(jq '.findings|length' <<<"$FILTERED")" = 1 ] \
  && [ "$(jq '.dropped|length' <<<"$FILTERED")" = 4 ] \
  && [ "$(jq -r .mode <<<"$FILTERED")" = internal ]; then
  ok "internal 只保留 file:line 的非低置信证据"
else
  no "internal locator/置信度过滤错误"
fi

EXTERNAL='{"topic":"library","findings":[
  {"claim":"kept","locator":"https://docs.example.com/api","confidence":"medium"},
  {"claim":"file in external","locator":"src/app.ts:12","confidence":"high"},
  {"claim":"missing host","locator":"https://","confidence":"high"},
  {"claim":"whitespace","locator":"https://example.com/bad path","confidence":"high"}
],"summary":"external state","gaps":[]}'
EXTERNAL_FILTERED="$(printf '%s\n' "$EXTERNAL" | bash "$CONTRACT" topic --mode external --expected-topic library)"
if [ "$(jq '.findings|length' <<<"$EXTERNAL_FILTERED")" = 1 ] \
  && [ "$(jq '.dropped|length' <<<"$EXTERNAL_FILTERED")" = 3 ]; then
  ok "external 只保留已给 URL 的证据"
else
  no "external locator 过滤错误"
fi

if printf '%s\n' "$INTERNAL" | bash "$CONTRACT" topic --mode internal --expected-topic another >/dev/null 2>&1; then
  no "topic 名不匹配应失败"
else
  ok "topic 名不匹配 fail loud"
fi
if printf '%s\n' "${INTERNAL%?},\"extra\":true}" | bash "$CONTRACT" topic --mode internal --expected-topic module-boundary >/dev/null 2>&1; then
  no "topic 多余字段应失败"
else
  ok "topic 严格拒绝 schema 外字段"
fi
if printf 'not-json\n' | bash "$CONTRACT" topic --mode internal --expected-topic module-boundary >/dev/null 2>&1; then
  no "非法 JSON 应失败"
else
  ok "非法 JSON fail loud"
fi

REPORT='{"markdown":"# Current state\n\nEvidence: `src/app.ts:12`.","open_questions":["remaining gap"],"spinoff_candidates":[{"tag":"optimize","finding":"later cleanup"}]}'
if printf '%s\n' "$REPORT" | bash "$CONTRACT" report | jq -e '.markdown|length>0' >/dev/null; then
  ok "synth report 合同通过"
else
  no "合法 synth report 被拒"
fi
BAD_REPORT='{"markdown":"x","open_questions":[],"spinoff_candidates":[{"tag":"proposal","finding":"choose A"}]}'
if printf '%s\n' "$BAD_REPORT" | bash "$CONTRACT" report >/dev/null 2>&1; then
  no "非法 spinoff tag 应失败"
else
  ok "synth report 非法 tag fail loud"
fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

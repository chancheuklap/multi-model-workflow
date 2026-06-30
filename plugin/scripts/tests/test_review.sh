#!/usr/bin/env bash
# review.sh 空跑:审闸一条命令——阶段映射 kind/angle 对、init loop、bad stage 拦。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEW="$SCRIPT_DIR/../review.sh"
LOOPF=".claude/multi-model-workflow/loop-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_review.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo x>x; git add -A; git commit -qm seed

# design / plan / final → kind=review
for s in design plan final; do
  OUT="$(bash "$REVIEW" start --stage "$s" --source "src-$s" 2>/dev/null)"
  echo "$OUT" | grep -q "REVIEW_STARTED stage=$s kind=review" && ok "$s → kind=review" || no "$s kind"
  [ "$(jq -r .kind "$LOOPF")" = "review" ] && ok "$s init loop kind=review" || no "$s loop kind"
  echo "$OUT" | grep -q "review/$s.md" && ok "$s → angle review/$s.md" || no "$s angle"
done

# plan-impl → contract-gate,且不派 Codex
OUT="$(bash "$REVIEW" start --stage plan-impl --source x 2>/dev/null)"
echo "$OUT" | grep -q "kind=contract-gate" && ok "plan-impl → contract-gate" || no "plan-impl kind"
[ "$(jq -r .kind "$LOOPF")" = "contract-gate" ] && ok "plan-impl init contract-gate" || no "plan-impl loop"
echo "$OUT" | grep -q "不派 Codex" && ok "③合同门不派 Codex" || no "③不派 Codex"

# review 阶段 brief 含派两个 Codex + 续接 resume
OUT="$(bash "$REVIEW" start --stage final --source x 2>/dev/null)"
echo "$OUT" | grep -q "codex exec resume" && ok "brief 含 codex 续接" || no "brief codex resume"
echo "$OUT" | grep -q "基线1" && ok "final 给两基线视角" || no "final 视角"

# fail-closed
if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then no "非法 stage 被拒"; else ok "非法 stage 被拒"; fi
if bash "$REVIEW" start --stage design >/dev/null 2>&1; then no "缺 source 被拒"; else ok "缺 source 被拒(fail-closed)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

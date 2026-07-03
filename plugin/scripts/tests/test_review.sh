#!/usr/bin/env bash
# review.sh 空跑:审闸一条命令——阶段映射 kind/视角 对、init loop、纯路由指向 Codex skill(不给 plugin 路径)、bad stage 拦。
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
  [ "$(jq -r .max_rounds "$LOOPF")" = "2" ] && ok "$s 审 loop 配轮上限 max_rounds=2(机器熔断)" || no "$s max_rounds"
  echo "$OUT" | grep -q "loop round next" && ok "$s brief 指示轮账 round next" || no "$s brief round"
  echo "$OUT" | grep -q "worktree-review skill,按 stage=$s" && ok "$s → 纯路由指向 worktree-review skill" || no "$s skill 指针"
  if echo "$OUT" | grep -qE "references/review/|quartet"; then no "$s 仍给 Codex plugin 路径/quartet(不该)"; else ok "$s 无 plugin 路径喂 Codex"; fi
done

# plan-impl → contract-gate,且不派 Codex
OUT="$(bash "$REVIEW" start --stage plan-impl --source x 2>/dev/null)"
echo "$OUT" | grep -q "kind=contract-gate" && ok "plan-impl → contract-gate" || no "plan-impl kind"
[ "$(jq -r .kind "$LOOPF")" = "contract-gate" ] && ok "plan-impl init contract-gate" || no "plan-impl loop"
echo "$OUT" | grep -q "不派 Codex" && ok "③合同门不派 Codex" || no "③不派 Codex"
echo "$OUT" | grep -q "references/review/plan-impl.md" && ok "③ brief 纯路由指向 plan-impl.md(方法论单源)" || no "③ brief 未指 plan-impl.md"

# review 阶段 brief 含派 Codex + 续接 resume
OUT="$(bash "$REVIEW" start --stage final --source x 2>/dev/null)"
echo "$OUT" | grep -q "codex exec resume" && ok "brief 含 codex 续接" || no "brief codex resume"
echo "$OUT" | grep -q "基线1" && ok "final 给两基线视角" || no "final 视角"
# ④final 双模型:4 审者 = 两视角 × (Codex + Claude),prompt 同一段;①② 仍 Codex-only
echo "$OUT" | grep -q "4 个独立审者" && ok "final 双模型:4 审者" || no "final 4 审者"
echo "$OUT" | grep -q "claude -p" && ok "final 派 Claude 无头 CLI" || no "final claude -p"
echo "$OUT" | grep -q "同一段" && ok "final 两模型 prompt 同一段" || no "final prompt 一致"
echo "$OUT" | grep -q -- "--resume" && ok "Claude 审者续接 --resume" || no "claude resume"
OUTD="$(bash "$REVIEW" start --stage design --source x 2>/dev/null)"
echo "$OUTD" | grep -q "claude -p" && no "design 审不该派 Claude(Claude 写的不自审)" || ok "①②仍 Codex-only(写审异家)"

# fail-closed
if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then no "非法 stage 被拒"; else ok "非法 stage 被拒"; fi
if bash "$REVIEW" start --stage design >/dev/null 2>&1; then no "缺 source 被拒"; else ok "缺 source 被拒(fail-closed)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# review.sh 空跑:审闸一条命令——阶段映射 kind/视角 对、init loop、brief 落盘(不过主线程 context)、
# 纯路由指向已装 worktree-review skill(不给审者 plugin 路径)、④final 按 scenario 分档、bad stage 拦。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEW="$SCRIPT_DIR/../review.sh"
LOOPF=".claude/multi-model-workflow/loop-state.json"
BRIEF=".claude/multi-model-workflow/review-brief.md"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_review.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo x>x; git add -A; git commit -qm seed

# design / plan / final → kind=review;brief 落盘,stdout 只指路径
for s in design plan final; do
  OUT="$(bash "$REVIEW" start --stage "$s" --source "src-$s" 2>/dev/null)"
  echo "$OUT" | grep -q "REVIEW_STARTED stage=$s kind=review" && ok "$s → kind=review" || no "$s kind"
  [ "$(jq -r .kind "$LOOPF")" = "review" ] && ok "$s init loop kind=review" || no "$s loop kind"
  [ "$(jq -r .max_rounds "$LOOPF")" = "2" ] && ok "$s 审 loop 配轮上限 max_rounds=2(机器熔断)" || no "$s max_rounds"
  echo "$OUT" | grep -q "review-brief.md" && ok "$s stdout 只指 brief 路径(brief 不过主线程 context)" || no "$s brief 指路"
  B="$(cat "$BRIEF")"
  echo "$B" | grep -q "worktree-review skill,按 stage=$s" && ok "$s brief 纯路由指向 worktree-review skill" || no "$s skill 指针"
  if echo "$B" | grep -qE "references/review/|quartet"; then no "$s brief 仍给审者 plugin 路径(不该)"; else ok "$s brief 无 plugin 路径喂审者"; fi
  echo "$B" | grep -q "loop round next" && ok "$s brief 指示轮账 round next" || no "$s brief round"
done

# plan-impl → contract-gate,且不派 Codex(stdout 内联,不写 brief)
OUT="$(bash "$REVIEW" start --stage plan-impl --source x 2>/dev/null)"
echo "$OUT" | grep -q "kind=contract-gate" && ok "plan-impl → contract-gate" || no "plan-impl kind"
[ "$(jq -r .kind "$LOOPF")" = "contract-gate" ] && ok "plan-impl init contract-gate" || no "plan-impl loop"
echo "$OUT" | grep -q "不派 Codex" && ok "③合同门不派 Codex" || no "③不派 Codex"
echo "$OUT" | grep -q "references/review/plan-impl.md" && ok "③ brief 纯路由指向 plan-impl.md(方法论单源)" || no "③ brief 未指 plan-impl.md"

# ④final 无 manifest(默认 develop 档):双模型 2×2,prompt 同一段
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "codex exec resume" && ok "final brief 含 codex 续接" || no "brief codex resume"
echo "$B" | grep -q "基线1" && ok "final 给两基线视角" || no "final 视角"
echo "$B" | grep -q "4 个独立审者" && ok "final 双模型:4 审者" || no "final 4 审者"
echo "$B" | grep -q "claude -p" && ok "final 派 Claude 无头 CLI" || no "final claude -p"
echo "$B" | grep -q "同一段" && ok "final 两模型 prompt 同一段" || no "final prompt 一致"
echo "$B" | grep -q -- "--resume" && ok "Claude 审者续接 --resume" || no "claude resume"

# ④final 分档:small-change/bug 任务 → 1×Codex 一肩挑两视角,不派双模型
mkdir -p .claude/multi-model-workflow
echo '{"scenario":"small-change"}' > .claude/multi-model-workflow/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "1 个独立 Codex 审者一肩挑" && ok "small-change ④ 降档:1×Codex 一肩挑两视角" || no "small-change 降档"
echo "$B" | grep -q "claude -p" && no "small-change ④ 不该派 Claude(省 token)" || ok "small-change ④ 无双模型开销"
echo '{"scenario":"bug"}' > .claude/multi-model-workflow/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "1 个独立 Codex 审者一肩挑" "$BRIEF" && ok "bug ④ 同样降档" || no "bug 降档"
echo '{"scenario":"develop"}' > .claude/multi-model-workflow/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "4 个独立审者" "$BRIEF" && ok "develop ④ 保持双模型 2×2" || no "develop 2×2"

# ①②审不派 Claude(设计/计划是 Claude 写的,写者≠验者)
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
grep -q "claude -p" "$BRIEF" && no "design 审不该派 Claude" || ok "①②仍 Codex-only(写审异家)"

# fail-closed
if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then no "非法 stage 被拒"; else ok "非法 stage 被拒"; fi
if bash "$REVIEW" start --stage design >/dev/null 2>&1; then no "缺 source 被拒"; else ok "缺 source 被拒(fail-closed)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

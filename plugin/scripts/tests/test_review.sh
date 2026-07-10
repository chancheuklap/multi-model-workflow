#!/usr/bin/env bash
# review.sh 空跑:审闸一条命令——阶段映射 kind/视角 对、init loop、brief 落盘(不过主线程 context)、
# 纯路由指向已装 worktree-review skill(不给审者 plugin 路径)、④final 按 scenario 分档、bad stage 拦。
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEW="$SCRIPT_DIR/../review.sh"
LOOPF="${STATE_SUBDIR}/loop-state.json"
BRIEF="${STATE_SUBDIR}/review-brief.md"

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
echo "$B" | grep -q "resume <session-id>" && ok "final brief 含 codex 续接" || no "brief codex resume"
echo "$B" | grep -q -- "read-only.*resume <session-id>" && ok "codex 续接重钉围栏(resume 不继承)" || no "resume 未重钉围栏"
echo "$B" | grep -q "run_in_background" && ok "brief 定死后台跑(防 10min 超时)" || no "brief 无后台跑指令"
echo "$B" | grep -q "基线1" && ok "final 给两基线视角" || no "final 视角"
echo "$B" | grep -q "4 个独立审者" && ok "final 双模型:4 审者" || no "final 4 审者"
echo "$B" | grep -q "code-reviewer" && ok "final Claude 审者=会话内 sub-agent" || no "final Claude sub-agent"
echo "$B" | grep -q "claude -p" && no "final 不该用 claude -p 无头(另起进程另计费)" || ok "final 无 claude -p(成本回归守卫)"
echo "$B" | grep -q "同一段\|同一份" && ok "final 两模型读同一段方法论" || no "final prompt 一致"
echo "$B" | grep -q "再派一个 code-reviewer" && ok "Claude 审者续接=再派 sub-agent" || no "claude sub-agent 续接"

# ④final 分档:small-change/bug 任务 → 1×Codex 一肩挑两视角,不派双模型
mkdir -p ${STATE_SUBDIR}
echo '{"scenario":"small-change"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "1 个独立 Codex 审者一肩挑" && ok "small-change ④ 降档:1×Codex 一肩挑两视角" || no "small-change 降档"
{ echo "$B" | grep -q "claude -p" || echo "$B" | grep -q "code-reviewer"; } && no "small-change ④ 不该派 Claude(省 token)" || ok "small-change ④ 无双模型开销"
echo '{"scenario":"bug"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "1 个独立 Codex 审者一肩挑" "$BRIEF" && ok "bug ④ 同样降档" || no "bug 降档"
echo '{"scenario":"develop"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "4 个独立审者" "$BRIEF" && ok "develop ④ 判不出数据(无 base/slug)→ fail-closed 保 4 审者" || no "develop fail-closed 4"

# ④final develop 风险分档:全 plan 无 capable 且 diff 小 → 2 审者;有 capable → 4 审者
BASE="$(git rev-parse HEAD)"
printf '{"scenario":"develop","base_commit":"%s","slug":"t1"}' "$BASE" > ${STATE_SUBDIR}/task.json
mkdir -p docs/plans/t1
printf '**Complexity:** standard\n' > docs/plans/t1/001-a.md
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "2 个独立审者" "$BRIEF" && ok "develop ④ 无 capable+diff 小 → 降 2 审者" || no "develop 降 2 审者"
grep -q "code-reviewer" "$BRIEF" && ok "2 审者档仍跨模型(Claude sub-agent 在)" || no "2 审者跨模型"
grep -q "claude -p" "$BRIEF" && no "2 审者档不该用 claude -p 无头" || ok "2 审者档无 claude -p(成本守卫)"
printf '**Complexity:** capable\n' > docs/plans/t1/002-b.md
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "4 个独立审者" "$BRIEF" && ok "develop ④ 有 capable plan → 保 4 审者" || no "capable 保 4"

# 多 --source(阶段可钉多个产出,where 逐个吐)
OUT="$(bash "$REVIEW" start --stage design --source s1.md --source s2.md 2>/dev/null)"
echo "$OUT" | grep -q "REVIEW_STARTED" && grep -q "s1.md s2.md" "$BRIEF" && ok "多 --source 可重复收(brief 拼全)" || no "多 source"

# ③合同门:anchors 节机械核实为空 → 自动登记并 cover no-cross-plan-contracts
mkdir -p docs/design
printf '# d\n## Cross-Plan Contract Anchors\n<!-- 占位 -->\n<!-- 由 plan 阶段回填 -->\n' > docs/design/d.md
OUT="$(bash "$REVIEW" start --stage plan-impl --source docs/design/d.md 2>/dev/null)"
[ "$(jq -r '.checklist[]|select(.item=="no-cross-plan-contracts")|.status' "$LOOPF")" = "covered" ] \
  && ok "③ anchors 空 → 自动登记+cover 显式空项" || no "③ 自动空项"
echo "$OUT" | grep -q "自动登记" && ok "③ 回执说明已自动代劳" || no "③ 回执"
# anchors 有实体内容 → 不自动,照旧人工核
printf '# d\n## Cross-Plan Contract Anchors\n| owner | provider |\n| 001 | 002 |\n' > docs/design/d.md
bash "$REVIEW" start --stage plan-impl --source docs/design/d.md >/dev/null 2>&1
[ "$(jq -r '.checklist|length' "$LOOPF")" = "0" ] && ok "③ anchors 有内容 → 不自动过,人工核" || no "③ 有内容不自动"

# ①设计审仍 Codex(设计是 Claude 写的,写者≠验者)
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
{ grep -q "claude -p" "$BRIEF" || grep -q "code-reviewer" "$BRIEF"; } && no "design 审不该派 Claude" || ok "①设计审仍 Codex-only(写审异家)"

# ②计划审翻 Claude(计划改由 Codex 写 → 审者=Claude code-reviewer,写者≠验者)
bash "$REVIEW" start --stage plan --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "code-reviewer" && ok "②计划审派 Claude code-reviewer(跨模型)" || no "②plan Claude 审者"
echo "$B" | grep -q "轴A 覆盖与质量" && ok "②计划审两路视角(轴A/轴B)" || no "②plan 视角"
echo "$B" | grep -q "codex exec" && no "②计划审不该再派 Codex(Codex 写的)" || ok "②计划审无 Codex 派发(写审异家)"
echo "$B" | grep -q "claude -p" && no "②计划审不用 claude -p 无头" || ok "②计划审无 claude -p(成本守卫)"

# 留痕落点:任务审走 docs/reviews/;merge-impl(主仓库)落状态平面,不写 docs/
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
grep -q "docs/reviews/<slug>-design.md" "$BRIEF" && ok "任务审留痕落 docs/reviews/" || no "design 留痕落点"
bash "$REVIEW" start --stage merge-impl --source x >/dev/null 2>&1
grep -q "${STATE_SUBDIR}/<slug>-merge-impl-review.md" "$BRIEF" && ok "merge-impl 留痕落状态平面(主仓库零残留)" || no "merge-impl 留痕落点"
grep -q "docs/reviews/" "$BRIEF" && no "merge-impl 不该指 docs/" || ok "merge-impl 不写 docs/"
# 主仓库状态平面已遮蔽:起审后 git status 不冒 ?? .claude/
grep -qxF 'multi-model-workflow/' .claude/.gitignore && ok "review start 遮蔽主仓库状态平面" || no "review 遮蔽"

# fail-closed
if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then no "非法 stage 被拒"; else ok "非法 stage 被拒"; fi
if bash "$REVIEW" start --stage design >/dev/null 2>&1; then no "缺 source 被拒"; else ok "缺 source 被拒(fail-closed)"; fi

# ===== Droid overlay: design-a/b · plan-a/b · final tier · merge-impl =====
export MMW_HOST=droid
STATE_SUBDIR=.factory/multi-model-workflow
BRIEF="${STATE_SUBDIR}/review-brief.md"
LOOPF="${STATE_SUBDIR}/loop-state.json"
mkdir -p "$STATE_SUBDIR"

echo '{"scenario":"develop"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "host=droid" && ok "droid design brief 标 host=droid" || no "droid design host"
echo "$B" | grep -q "reviewer-design-a" && ok "droid design 派 design-a" || no "droid design-a"
echo "$B" | grep -q "reviewer-design-b" && ok "droid design 派 design-b" || no "droid design-b"
echo "$B" | grep -q "codex exec" && no "droid design 不该 codex exec" || ok "droid design 无 codex exec"

bash "$REVIEW" start --stage plan --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "reviewer-plan-a" && ok "droid plan 派 plan-a" || no "droid plan-a"
echo "$B" | grep -q "reviewer-plan-b" && ok "droid plan 派 plan-b" || no "droid plan-b"

# final fail-closed 4 (no base/slug)
echo '{"scenario":"develop"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "tier=4" && ok "droid final fail-closed brief tier=4" || no "droid final tier=4 标注"
echo "$B" | grep -q "4 路" && ok "droid final tier=4 派 4 路" || no "droid final 4 路"
echo "$B" | grep -q "reviewer-final-a" && ok "droid final 含 final-a" || no "droid final-a"
echo "$B" | grep -q "reviewer-final-b" && ok "droid final 含 final-b" || no "droid final-b"

# final tier=2(独立 slug,避免复用先前 capable plan 目录)
BASE="$(git rev-parse HEAD)"
printf '{"scenario":"develop","base_commit":"%s","slug":"t-droid-2"}' "$BASE" > ${STATE_SUBDIR}/task.json
mkdir -p docs/plans/t-droid-2
printf '**Complexity:** standard\n' > docs/plans/t-droid-2/001-a.md
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "tier=2" && ok "droid final 降档 tier=2" || no "droid tier=2 标注"
echo "$B" | grep -q "2 路" && ok "droid final tier=2 派 2 路" || no "droid tier=2 路数"

# small-change tier=1
echo '{"scenario":"small-change"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "tier=1" && ok "droid small-change final tier=1" || no "droid sc tier=1"
echo "$B" | grep -q "reviewer-final-a" && ok "droid small-change 单 final-a" || no "droid sc final-a"

# merge-impl 双路
bash "$REVIEW" start --stage merge-impl --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "merge-impl" && ok "droid merge-impl brief" || no "droid merge brief"
echo "$B" | grep -q "reviewer-final-a" && echo "$B" | grep -q "reviewer-final-b" \
  && ok "droid merge-impl 派 final-a+b" || no "droid merge 双路"
echo "$B" | grep -q 'reviewer-\*' && no "droid merge 不该空壳 reviewer-*" || ok "droid merge 非空壳"
echo "$B" | grep -q "不 consult advisor" && ok "droid brief 禁 consult advisor" || no "droid brief 缺禁 advisor"

unset MMW_HOST
export MMW_HOST=claude

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# review.sh 空跑(pi 原生):审闸一条命令——brief 落盘(主线程读它直接派审者)、纯路由指向已装 worktree-review skill、
# 审不记账(无 loop 账本,收口硬核=留痕文件含 verdict,由 flow.sh 核)、④final 按场景/风险分档、③合同门机器核、bad stage 拦。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.pi/multi-model-workflow}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REVIEW="$SCRIPT_DIR/../review.sh"
BRIEF="${STATE_SUBDIR}/review-brief.md"
LOOPF="${STATE_SUBDIR}/loop-state.json"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_review.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo x>x; git add -A; git commit -qm seed

# design / plan / final → brief 落盘,stdout 只指路径;审不记账(不建 loop 账本)
for s in design plan final; do
  OUT="$(bash "$REVIEW" start --stage "$s" --source "src-$s" 2>/dev/null)"
  echo "$OUT" | grep -q "REVIEW_STARTED stage=$s host=pi" && ok "$s → REVIEW_STARTED host=pi" || no "$s REVIEW_STARTED"
  [ ! -f "$LOOPF" ] && ok "$s 审不记账(无 loop 账本)" || no "$s 不该建 loop 账本"
  echo "$OUT" | grep -q "review-brief.md" && ok "$s stdout 指 brief 路径(主线程读它直接派审者)" || no "$s brief 指路"
  B="$(cat "$BRIEF")"
  echo "$B" | grep -q "worktree-review" && echo "$B" | grep -q "stage=$s 审" && ok "$s brief 纯路由指向 worktree-review skill" || no "$s skill 指针"
  if echo "$B" | grep -qE "references/review/"; then no "$s brief 仍给审者 plugin 路径(不该)"; else ok "$s brief 无 plugin 路径喂审者"; fi
  echo "$B" | grep -q "verdict" && ok "$s brief 写明留痕含 verdict(收口硬核)" || no "$s brief verdict"
  echo "$B" | grep -q "亲验" && ok "$s brief 要求收回亲验(审者是劳动力不是信源)" || no "$s brief 亲验"
  echo "$B" | grep -q "waived" && ok "$s brief 含 waived 处置" || no "$s brief waived"
  echo "$B" | grep -q "四问" && ok "$s brief 含处置四问" || no "$s brief 四问"
  echo "$B" | grep -q "一次审透" && ok "$s brief 要求一次审透" || no "$s brief 一次审透"
  echo "$B" | grep -q "subagent 调用" && echo "$B" | grep -q "tasks 数组并行" && ok "$s 派发=单次调用 tasks 数组并行" || no "$s tasks 派发"
  echo "$B" | grep -q 'codex ''exec' && no "$s brief 不该派 codex(pi 宿主无 Codex CLI)" || ok "$s 无 codex 派发"
  echo "$B" | grep -q "claude -p" && no "$s brief 不该用 claude -p 无头" || ok "$s 无 claude -p"
done

# accepted prototype 是设计待审产物；review start 自动补 README + selected，不带未选候选。
DESIGN_ROOT="docs/design/review-prototype"
mkdir -p "$STATE_SUBDIR" "$DESIGN_ROOT/prototype"
printf '# design\n' >"$DESIGN_ROOT/review-prototype.md"
printf '# prototype log\n' >"$DESIGN_ROOT/prototype/README.md"
printf 'selected\n' >"$DESIGN_ROOT/prototype/selected.py"
printf 'rejected\n' >"$DESIGN_ROOT/prototype/rejected.py"
cat >"$STATE_SUBDIR/task.json" <<JSON
{"scenario":"develop","slug":"review-prototype","phase":"design","docs":{"design":"$DESIGN_ROOT"},"prototype":{"status":"accepted","kind":"logic","question":"q","iteration":1,"run_command":"run","artifacts":["$DESIGN_ROOT/prototype/selected.py","$DESIGN_ROOT/prototype/rejected.py"],"selected":["$DESIGN_ROOT/prototype/selected.py"],"log":"$DESIGN_ROOT/prototype/README.md","updated_at":"2026-07-23T00:00:00Z"}}
JSON
bash "$REVIEW" start --stage design --source "$DESIGN_ROOT/review-prototype.md" >/dev/null
B="$(cat "$BRIEF")"
echo "$B" | grep -q "$DESIGN_ROOT/prototype/README.md" \
  && echo "$B" | grep -q "$DESIGN_ROOT/prototype/selected.py" \
  && ! echo "$B" | grep -q "$DESIGN_ROOT/prototype/rejected.py" \
  && ok "design review 自动读取 accepted README + selected" || no "design review prototype 材料"

# phase=design 且 prototype 未 accepted → 预审被拒(顺序机器化;过门后复审不受限)
jq '.prototype.status="active"' "$STATE_SUBDIR/task.json" > "$STATE_SUBDIR/task.json.tmp" && mv "$STATE_SUBDIR/task.json.tmp" "$STATE_SUBDIR/task.json"
if bash "$REVIEW" start --stage design --source "$DESIGN_ROOT/review-prototype.md" >/dev/null 2>&1; then
  no "phase=design 未 accepted 预审应被拒"; else ok "phase=design 未 accepted 预审被拒(顺序机器化)"; fi
jq 'del(.phase) | .prototype.status="accepted"' "$STATE_SUBDIR/task.json" > "$STATE_SUBDIR/task.json.tmp" && mv "$STATE_SUBDIR/task.json.tmp" "$STATE_SUBDIR/task.json"

# 复审 brief
mkdir -p ${STATE_SUBDIR} docs/reviews
echo '{"scenario":"develop","slug":"rr1","repair_count":1}' > ${STATE_SUBDIR}/task.json
printf '# prior\n## verdict\npass\n' > docs/reviews/rr1-plan.md
bash "$REVIEW" start --stage plan --source x >/dev/null 2>&1
BR="$(cat "$BRIEF")"
echo "$BR" | grep -q "本轮是 re-review" && ok "re-review brief 注入" || no "re-review brief"
echo "$BR" | grep -q "prior_trace" && ok "re-review 含 prior_trace" || no "prior_trace"

# 续接语义:审者 Agent 不复用被审 context——中断重派对应视角
grep -q "重派对应视角" "$BRIEF" && grep -q "不需 resume" "$BRIEF" \
  && ok "中断续接=重派视角(审者无状态)" || no "续接语义"
grep -q "resume <session-id>" "$BRIEF" && no "brief 不该出现 codex resume 续接" || ok "无 codex resume 语义"
grep -q "run_in_background" "$BRIEF" && no "brief 不该出现后台跑指令(tasks 前台同步)" || ok "无 run_in_background(tasks 同步返回)"
grep -q "subagent_type" "$BRIEF" && no "brief 不该出现旧 Agent 工具参数名" || ok "无 subagent_type 旧参数"

# ①设计审:两视角 reviewer pis(设计是主线程写的,写者≠审者=隔离 context 的 reviewer)
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
grep -q "reviewer-design-a" "$BRIEF" && grep -q "reviewer-design-b" "$BRIEF" && ok "design 派 reviewer-design-a/b 两视角" || no "design 审者编制"
grep -q "轴A 设计内容" "$BRIEF" && grep -q "轴B 项目对齐" "$BRIEF" && ok "design 两轴视角" || no "design 视角"

# ②计划审:计划由 plan-writer 写,审者另派(写者≠审者)
bash "$REVIEW" start --stage plan --source x >/dev/null 2>&1
grep -q "reviewer-plan-a" "$BRIEF" && grep -q "reviewer-plan-b" "$BRIEF" && ok "②计划审派 reviewer-plan-a/b" || no "②plan 审者编制"
grep -q "写者与审者分离" "$BRIEF" && ok "②计划审写审分离(plan-writer 写,审者另派)" || no "②plan 写审分离"
grep -q "轴A 覆盖与质量" "$BRIEF" && ok "②计划审两路视角(轴A/轴B)" || no "②plan 视角"

# ④final 分档:small-change/bug → 1×GPT 一肩挑两基线,不耗 Claude
mkdir -p ${STATE_SUBDIR}
echo '{"scenario":"small-change"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "一个独立审者一肩挑两条基线" && ok "small-change ④ 降档:1×GPT 覆盖两基线" || no "small-change 降档"
echo "$B" | grep -q "reviewer-final-a" && ! echo "$B" | grep -q "reviewer-final-b" && ok "small-change ④ 只派 GPT 路线" || no "small-change 审者路线"
echo '{"scenario":"bug"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "一个独立审者一肩挑两条基线" "$BRIEF" && ok "bug ④ 同样降档" || no "bug 降档"

# develop 判不出风险数据 → fail-closed 保 4;无 capable 且 diff 小 → 2;capable → 4
echo '{"scenario":"develop"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "四个跨模型审者" && ok "develop 风险未知保 4 审者" || no "develop fail-closed 4"
echo "$B" | grep -q "reviewer-final-a" && echo "$B" | grep -q "reviewer-final-b" && ok "develop 4 档派 A/B" || no "develop 4 档编制"
echo "$B" | grep -q "同一份方法论" && ok "develop 4 档同方法论" || no "develop 4 档 prompt"
echo "$B" | grep -q "跨模型对账" && ok "develop 4 档跨模型对账" || no "develop 4 档对账"
mkdir -p docs/plans/t-invalid
printf '**Complexity:** standard\n' > docs/plans/t-invalid/001-a.md
printf '{"scenario":"develop","base_commit":"not-a-commit","slug":"t-invalid"}' > ${STATE_SUBDIR}/task.json
if bash "$REVIEW" start --stage final --source x >/dev/null 2>&1; then
  grep -q "四个跨模型审者" "$BRIEF" && ok "develop base 无效 → fail-closed 保 4 审者" || no "develop 无效 base 编制"
else
  no "develop 无效 base 不应中断起审"
fi
BASE="$(git rev-parse HEAD)"
printf '{"scenario":"develop","base_commit":"%s","slug":"t1"}' "$BASE" > ${STATE_SUBDIR}/task.json
mkdir -p docs/plans/t1
printf '**Complexity:** standard\n' > docs/plans/t1/001-a.md
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "两个独立跨模型审者" "$BRIEF" && ok "develop 无 capable+diff 小 → 2 审者" || no "develop 降 2 审者"
REVIEW_TIER_DIFF_MAX=-1 bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "四个跨模型审者" "$BRIEF" && ok "develop diff 超阈值 → 4 审者" || no "develop diff 阈值保 4"
printf '**复杂度:** Capable\n' > docs/plans/t1/002-b.md
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "四个跨模型审者" "$BRIEF" && ok "develop capable → 4 审者" || no "develop capable 保 4"

# 多 --source(阶段可钉多个产出,brief 拼全)
OUT="$(bash "$REVIEW" start --stage design --source s1.md --source s2.md 2>/dev/null)"
echo "$OUT" | grep -q "REVIEW_STARTED" && grep -q "s1.md s2.md" "$BRIEF" && ok "多 --source 可重复收(brief 拼全)" || no "多 source"

# ③合同门:anchors 节机械核实为空 → 直接放行回执(不派审者、不写 brief 判断)
mkdir -p docs/design
printf '# d\n## Cross-Plan Contract Anchors\n<!-- 占位 -->\n<!-- 由 plan 阶段回填 -->\n' > docs/design/d.md
OUT="$(bash "$REVIEW" start --stage plan-impl --source docs/design/d.md 2>/dev/null)"
echo "$OUT" | grep -q "CONTRACT_GATE_EMPTY" && ok "③ anchors 空 → CONTRACT_GATE_EMPTY 直接放行" || no "③ 空 anchors 放行 ($OUT)"
echo "$OUT" | grep -q "handoff --conclusion pass" && ok "③ 空 anchors 回执给下一步命令" || no "③ 回执命令"
# anchors 有实体内容 → 指到 plan-impl.md 人工核,结论写留痕
printf '# d\n## Cross-Plan Contract Anchors\n| owner | provider |\n| 001 | 002 |\n' > docs/design/d.md
OUT="$(bash "$REVIEW" start --stage plan-impl --source docs/design/d.md 2>/dev/null)"
echo "$OUT" | grep -q "REVIEW_STARTED stage=plan-impl host=pi" && ok "③ 有合同 → 起门" || no "③ 有合同起门"
echo "$OUT" | grep -q "references/review/plan-impl.md" && ok "③ 指向 plan-impl.md(方法论单源)" || no "③ 未指 plan-impl.md"
echo "$OUT" | grep -q "不派审者" && ok "③合同门不派审者(机器核+主线程判断)" || no "③ 不派审者"
echo "$OUT" | grep -q "verdict" && ok "③ 结论要求写留痕 verdict" || no "③ verdict 留痕"

# 留痕落点:任务审走 docs/reviews/<slug>-<stage>.md;merge-impl(主仓库)落状态平面,不写 docs/
printf '{"scenario":"develop","slug":"t1"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
grep -q "docs/reviews/t1-design.md" "$BRIEF" && ok "任务审留痕落 docs/reviews/<slug>-<stage>.md" || no "design 留痕落点"
bash "$REVIEW" start --stage merge-impl --source x >/dev/null 2>&1
grep -q "${STATE_SUBDIR}/t1-merge-impl-review.md" "$BRIEF" && ok "merge-impl 留痕落状态平面(主仓库零残留)" || no "merge-impl 留痕落点"
grep -q "docs/reviews/" "$BRIEF" && no "merge-impl 不该指 docs/" || ok "merge-impl 不写 docs/"
grep -q "reviewer-final-a" "$BRIEF" && grep -q "reviewer-final-b" "$BRIEF" && ok "merge-impl 派两跨模型 Task" || no "merge-impl 编制"
# 主仓库状态平面已遮蔽:起审后 git status 不冒 ?? .pi/
grep -qxF 'multi-model-workflow/' .pi/.gitignore && ok "review start 遮蔽主仓库状态平面" || no "review 遮蔽"

# fail-closed
if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then no "非法 stage 被拒"; else ok "非法 stage 被拒"; fi
if bash "$REVIEW" start --stage design >/dev/null 2>&1; then no "缺 source 被拒"; else ok "缺 source 被拒(fail-closed)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

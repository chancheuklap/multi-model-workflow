#!/usr/bin/env bash
# review.sh 空跑:审闸一条命令——brief 落盘(主线程读它直接派审者)、纯路由指向已装 worktree-review skill、
# 审不记账(无 loop 账本,收口硬核=留痕文件含 verdict,由 flow.sh 核)、④final 按 scenario/风险分档、③合同门机器核、bad stage 拦。
set -euo pipefail
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
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
  echo "$OUT" | grep -q "REVIEW_STARTED stage=$s" && ok "$s → REVIEW_STARTED" || no "$s REVIEW_STARTED"
  [ ! -f "$LOOPF" ] && ok "$s 审不记账(无 loop 账本)" || no "$s 不该建 loop 账本"
  echo "$OUT" | grep -q "review-brief.md" && ok "$s stdout 指 brief 路径(主线程读它直接派审者)" || no "$s brief 指路"
  B="$(cat "$BRIEF")"
  echo "$B" | grep -q "worktree-review skill,按 stage=$s" && ok "$s brief 纯路由指向 worktree-review skill" || no "$s skill 指针"
  if echo "$B" | grep -qE "references/review/|quartet"; then no "$s brief 仍给审者 plugin 路径(不该)"; else ok "$s brief 无 plugin 路径喂审者"; fi
  echo "$B" | grep -q "verdict" && ok "$s brief 写明留痕含 verdict(收口硬核)" || no "$s brief verdict"
  echo "$B" | grep -q "亲验" && ok "$s brief 要求收回亲验(审者是劳动力不是信源)" || no "$s brief 亲验"
  echo "$B" | grep -q "waived" && ok "$s brief 含 waived 处置" || no "$s brief waived"
  echo "$B" | grep -q "四问" && ok "$s brief 含处置四问" || no "$s brief 四问"
  echo "$B" | grep -q "一次审透" && ok "$s brief 要求一次审透" || no "$s brief 一次审透"
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

# 复审 brief:repair_count>0 或已有留痕 → 注入 re-review 规则
mkdir -p ${STATE_SUBDIR} docs/reviews
echo '{"scenario":"develop","slug":"rr1","repair_count":1}' > ${STATE_SUBDIR}/task.json
printf '# prior\n## verdict\npass\n' > docs/reviews/rr1-plan.md
bash "$REVIEW" start --stage plan --source x >/dev/null 2>&1
BR="$(cat "$BRIEF")"
echo "$BR" | grep -q "本轮是 re-review" && ok "re-review brief 注入" || no "re-review brief"
echo "$BR" | grep -q "prior_trace" && ok "re-review 含 prior_trace" || no "prior_trace"
echo "$BR" | grep -q "不得重提" && ok "re-review 禁重提 waived/rejected" || no "re-review 禁重提"

# ④final 无 manifest(默认 develop 档):双模型 2×2,prompt 同一段
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
BD="$(cat "$BRIEF")"
echo "$BD" | grep -q "resume <session-id>" && ok "design brief 含 codex 续接" || no "brief codex resume"
echo "$BD" | grep -q -- "read-only.*resume <session-id>" && ok "codex 续接重钉围栏(resume 不继承)" || no "resume 未重钉围栏"
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "重钉围栏" && ok "final 续接同样要求整套重钉" || no "final 续接重钉"
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
mkdir -p docs/plans/t-invalid
printf '**Complexity:** standard\n' > docs/plans/t-invalid/001-a.md
printf '{"scenario":"develop","base_commit":"not-a-commit","slug":"t-invalid"}' > ${STATE_SUBDIR}/task.json
if bash "$REVIEW" start --stage final --source x >/dev/null 2>&1; then
  grep -q "4 个独立审者" "$BRIEF" && ok "develop ④ base 无效 → fail-closed 保 4 审者" || no "develop 无效 base 编制"
else
  no "develop 无效 base 不应中断起审"
fi

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
# 中文"复杂度"标签 + 大小写不敏感也认 capable(防 fail-open 错降 tier=2 少审者)
printf '{"scenario":"develop","base_commit":"%s","slug":"t-cn"}' "$BASE" > ${STATE_SUBDIR}/task.json
mkdir -p docs/plans/t-cn
printf '**复杂度:** Capable\n' > docs/plans/t-cn/001-a.md
bash "$REVIEW" start --stage final --source x >/dev/null 2>&1
grep -q "4 个独立审者" "$BRIEF" && ok "develop ④ 中文复杂度/大小写 capable 也认 → 保 4 审者(fail-open 已堵)" || no "中文 capable 漏检 fail-open"

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
echo "$OUT" | grep -q "REVIEW_STARTED stage=plan-impl" && ok "③ 有合同 → 起门" || no "③ 有合同起门"
echo "$OUT" | grep -q "references/review/plan-impl.md" && ok "③ 指向 plan-impl.md(方法论单源)" || no "③ 未指 plan-impl.md"
echo "$OUT" | grep -q "不派审者" && ok "③合同门不派审者(机器核+主线程判断)" || no "③ 不派审者"
echo "$OUT" | grep -q "verdict" && ok "③ 结论要求写留痕 verdict" || no "③ verdict 留痕"

# ①设计审仍 Codex(设计是 Claude 写的,写者≠审者)
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
{ grep -q "claude -p" "$BRIEF" || grep -q "code-reviewer" "$BRIEF"; } && no "design 审不该派 Claude" || ok "①设计审仍 Codex-only(写审异家)"

# ②计划审翻 Claude(计划由 Codex 写 → 审者=Claude code-reviewer,写者≠审者)
bash "$REVIEW" start --stage plan --source x >/dev/null 2>&1
B="$(cat "$BRIEF")"
echo "$B" | grep -q "code-reviewer" && ok "②计划审派 Claude code-reviewer(跨模型)" || no "②plan Claude 审者"
echo "$B" | grep -q "轴A 覆盖与质量" && ok "②计划审两路视角(轴A/轴B)" || no "②plan 视角"
echo "$B" | grep -q "codex exec" && no "②计划审不该再派 Codex(Codex 写的)" || ok "②计划审无 Codex 派发(写审异家)"
echo "$B" | grep -q "claude -p" && no "②计划审不用 claude -p 无头" || ok "②计划审无 claude -p(成本守卫)"

# 留痕落点:任务审走 docs/reviews/<slug>-<stage>.md;merge-impl(主仓库)落状态平面,不写 docs/
printf '{"scenario":"develop","slug":"t1"}' > ${STATE_SUBDIR}/task.json
bash "$REVIEW" start --stage design --source x >/dev/null 2>&1
grep -q "docs/reviews/t1-design.md" "$BRIEF" && ok "任务审留痕落 docs/reviews/<slug>-<stage>.md" || no "design 留痕落点"
bash "$REVIEW" start --stage merge-impl --source x >/dev/null 2>&1
grep -q "${STATE_SUBDIR}/t1-merge-impl-review.md" "$BRIEF" && ok "merge-impl 留痕落状态平面(主仓库零残留)" || no "merge-impl 留痕落点"
grep -q "docs/reviews/" "$BRIEF" && no "merge-impl 不该指 docs/" || ok "merge-impl 不写 docs/"
# 主仓库状态平面已遮蔽:起审后 git status 不冒 ?? .claude/
grep -qxF 'multi-model-workflow/' .claude/.gitignore && ok "review start 遮蔽主仓库状态平面" || no "review 遮蔽"

# fail-closed
if bash "$REVIEW" start --stage bogus --source x >/dev/null 2>&1; then no "非法 stage 被拒"; else ok "非法 stage 被拒"; fi
if bash "$REVIEW" start --stage design >/dev/null 2>&1; then no "缺 source 被拒"; else ok "缺 source 被拒(fail-closed)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

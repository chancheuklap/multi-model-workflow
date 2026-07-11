#!/usr/bin/env bash
# worker.sh 空跑(fake codex):派发组对 prompt 铁律 + codex 参数、建 worktree、
# 记 session、resume 续会话。不连真 Codex。
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
WT_REL="${WT_REL:-.claude/worktrees}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CW="$SCRIPT_DIR/../worker.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_codex_worker.sh (fake codex) ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t
echo seed>seed; git add -A; git commit -qm seed

# fake codex:把收到的 argv 和 stdin(prompt)落盘,模拟 session header + 最后消息
FAKEBIN="$TMP/bin"; mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/codex" <<'FAKE'
#!/usr/bin/env bash
echo "ARGV: $*" > "$FAKE_CAP/argv"
cat > "$FAKE_CAP/stdin"
# -o <file> 找出最后消息落点
prev=""; for a in "$@"; do [ "$prev" = "-o" ] && echo "codex done" > "$a"; prev="$a"; done
echo "session id: sess-123"
FAKE
chmod +x "$FAKEBIN/codex"
export FAKE_CAP="$TMP/cap"; mkdir -p "$FAKE_CAP"
export CODEX_BIN="$FAKEBIN/codex"

PLAN="$TMP/plan.md"; echo "# plan" > "$PLAN"
DESIGN="$TMP/design.md"; echo "# design" > "$DESIGN"
ISSUE="$TMP/issue.md"; echo "# issue" > "$ISSUE"
WT="$TMP/wt-001"

OUT="$(bash "$CW" dispatch --plan "$PLAN" --worktree "$WT" --design "$DESIGN" --issue "$ISSUE" 2>/dev/null)"
[ -d "$WT" ] && ok "worktree 不存在则建好" || no "建 worktree"
[ "$(git -C "$WT" branch --show-current)" = "codex/wt-001" ] && ok "子 worktree 挂 codex/<名> 分支(不留 detached)" || no "worktree 分支 ($(git -C "$WT" branch --show-current))"
parent="${STATE_SUBDIR%%/*}"; [ "$(cat "$WT/$parent/.gitignore" 2>/dev/null)" = "*" ] && ok "状态平面 parent 已 gitignore(防 add -A 污染)" || no "state parent gitignore"
PROMPT="$(cat "$FAKE_CAP/stdin")"
# 瘦派发:prompt 只给指针(指向 worktree-build skill)+ 三文档路径;铁律本体在 Codex 侧 skill,不在 prompt
echo "$PROMPT" | grep -q "worktree-build" && ok "prompt 指向 worktree-build skill(铁律渐进加载)" || no "指向 build skill"
echo "$PROMPT" | grep -q "禁改 docs/" && ok "prompt 含禁改 docs 边界" || no "禁改 docs"
echo "$PROMPT" | grep -q '全在 worktree-build skill' && ok "prompt 委托 skill(提交格式/收工回执本体在 skill,不内联)" || no "委托 skill"
echo "$PROMPT" | grep -q '本消息不重复' && ok "prompt 纯路由(明示不重复 skill 方法)" || no "纯路由声明"
echo "$PROMPT" | grep -q "TDD" && ok "prompt 含 TDD 指向" || no "TDD"
echo "$PROMPT" | grep -q "$DESIGN" && ok "prompt 传了设计文档路径" || no "传设计路径"
echo "$PROMPT" | grep -q "$ISSUE" && ok "prompt 传了 issue 路径" || no "传 issue 路径"
echo "$PROMPT" | grep -q "$PLAN" && ok "prompt 传了计划路径(实施权威)" || no "传计划路径"
ARGV="$(cat "$FAKE_CAP/argv")"
echo "$ARGV" | grep -q -- "-C $WT" && ok "codex -C <worktree>" || no "-C worktree"
echo "$ARGV" | grep -q -- "--sandbox workspace-write" && ok "--sandbox workspace-write" || no "sandbox"
echo "$ARGV" | grep -q 'model_reasoning_effort="xhigh"' && ok "落地默认 xhigh effort(CODEX_EFFORT)" || no "落地 effort($ARGV)"
echo "$ARGV" | grep -q -- "-m gpt-5.6-luna" && ok "落地默认 gpt-5.6-luna(CODEX_MODEL)" || no "落地模型档($ARGV)"
echo "$ARGV" | grep -q -- "--add-dir" && ok "--add-dir 放行 git common dir" || no "add-dir"
# capable 自动切档:plan 标 Complexity: capable → 脚本自动切 sol high(agent 不手传 --model/--effort)
PLAN_CAP="$TMP/plan-cap.md"; printf '# plan\n\n**Complexity:** capable\n' > "$PLAN_CAP"
bash "$CW" dispatch --plan "$PLAN_CAP" --worktree "$TMP/wt-cap" >/dev/null 2>&1
ARGV_CAP="$(cat "$FAKE_CAP/argv")"
echo "$ARGV_CAP" | grep -q -- "-m gpt-5.6-sol" && ok "capable plan 自动切 gpt-5.6-sol(不手传)" || no "capable 模型档($ARGV_CAP)"
echo "$ARGV_CAP" | grep -q 'model_reasoning_effort="high"' && ok "capable plan 自动切 high effort" || no "capable effort($ARGV_CAP)"
# 中文"复杂度"标签 + 大小写不敏感也认 capable(与 review.sh 同语义)
PLAN_CAP2="$TMP/plan-cap2.md"; printf '# plan\n\n复杂度: Capable\n' > "$PLAN_CAP2"
bash "$CW" dispatch --plan "$PLAN_CAP2" --worktree "$TMP/wt-cap2" >/dev/null 2>&1
echo "$(cat "$FAKE_CAP/argv")" | grep -q -- "-m gpt-5.6-sol" && ok "中文复杂度/大小写 capable 也认自动切" || no "中文 capable 漏检"
# 显式 --model/--effort 覆盖自动切档(逃生口仍在)
bash "$CW" dispatch --plan "$PLAN_CAP" --worktree "$TMP/wt-ov" --model gpt-5.6-terra --effort xhigh >/dev/null 2>&1
echo "$(cat "$FAKE_CAP/argv")" | grep -q -- "-m gpt-5.6-terra" && ok "--model 显式覆盖自动切档" || no "显式覆盖失效"
echo "$OUT" | grep -q "SESSION=sess-123" && ok "抓到并打印 session id" || no "session 记账"
[ "$(cat "$WT/${STATE_SUBDIR}/codex-session")" = "sess-123" ] && ok "session 落盘供 resume" || no "session 落盘"
echo "$OUT" | grep -q "codex done" && ok "打印 codex 最后消息(供验收)" || no "最后消息"

# ANSI 色码回归:真 Codex header 是带颜色的 `\033[1msession id:\033[0m <uuid>`;
# 剥色前 `^session id:` 锚点被前导色码顶开抓空,session 不落盘、resume 记账整条丢失。
cat > "$FAKEBIN/codex-ansi" <<'FAKE'
#!/usr/bin/env bash
prev=""; for a in "$@"; do [ "$prev" = "-o" ] && echo "codex done" > "$a"; prev="$a"; done
printf '\033[1msession id:\033[0m sess-ansi-9\n'
FAKE
chmod +x "$FAKEBIN/codex-ansi"
OUT_A="$(CODEX_BIN="$FAKEBIN/codex-ansi" bash "$CW" dispatch --plan "$PLAN" --worktree "$TMP/wt-ansi" 2>/dev/null)"
echo "$OUT_A" | grep -q "SESSION=sess-ansi-9" && ok "带 ANSI 色码的 session id 仍抓到(剥色后锚点匹配)" || no "ANSI session 抓取($OUT_A)"
[ "$(cat "$TMP/wt-ansi/${STATE_SUBDIR}/codex-session" 2>/dev/null)" = "sess-ansi-9" ] && ok "ANSI session 落盘供 resume" || no "ANSI session 落盘"
# design/issue 可空(small-change/bug):空时不应出现裸标签行(放最后,免得覆盖上面 argv 断言)
bash "$CW" dispatch --plan "$PLAN" --worktree "$TMP/wt-nodoc" >/dev/null 2>&1
PROMPT2="$(cat "$FAKE_CAP/stdin")"
echo "$PROMPT2" | grep -q "设计文档(意图" && no "无 design 时不该出现设计行" || ok "design 可空:无则不出设计行"

# resume:用记的 session 续会话,exec 层重钉与 dispatch 一致的围栏
INSTR="$TMP/fix.md"; echo "fix this" > "$INSTR"
OUT2="$(bash "$CW" resume --worktree "$WT" --instructions "$INSTR" 2>/dev/null)"
ARGV2="$(cat "$FAKE_CAP/argv")"
echo "$ARGV2" | grep -q "resume sess-123" && ok "resume 续原 session" || no "resume session"
echo "$ARGV2" | grep -q -- "-C $WT" && ok "resume 重钉 -C <worktree>(不掉回调用 cwd)" || no "resume -C"
echo "$ARGV2" | grep -q -- "--sandbox workspace-write" && ok "resume 重钉 workspace-write(不掉回 config 默认)" || no "resume sandbox"
echo "$ARGV2" | grep -q -- "-m gpt-5.6-luna" && ok "resume 复用派发模型档(不掉回 config 默认档)" || no "resume 模型档"
[ "$(cat "$FAKE_CAP/stdin")" = "fix this" ] && ok "resume 发回修复指令" || no "resume 指令"

# resume 兜捞:session 文件丢(dispatch 被杀)→ 从 run.log 捞回,不丢续会话能力
rm "$WT/${STATE_SUBDIR}/codex-session"
bash "$CW" resume --worktree "$WT" --instructions "$INSTR" >/dev/null 2>&1
grep -q "resume sess-123" "$FAKE_CAP/argv" && ok "session 丢失从 run.log 捞回 resume" || no "run.log 捞回"
[ "$(cat "$WT/${STATE_SUBDIR}/codex-session" 2>/dev/null)" = "sess-123" ] && ok "捞回后补记 session 落盘" || no "捞回补记"

# fail-closed
if bash "$CW" dispatch --plan /nope.md --worktree "$WT" >/dev/null 2>&1; then no "缺/坏 plan 被拒"; else ok "坏 plan 被拒"; fi
if bash "$CW" resume --worktree "$TMP/nowt" --instructions "$INSTR" >/dev/null 2>&1; then no "无 session 被拒"; else ok "无 session 被拒(fail-closed)"; fi

# ===== docs/ 守卫:Codex 碰 docs/ → fail-closed 退非零 + DOCS_VIOLATION(Worker 禁改 docs/)=====
cat > "$FAKEBIN/codex-evil" <<'FAKE'
#!/usr/bin/env bash
wt=""; prev=""; for a in "$@"; do [ "$prev" = "-C" ] && wt="$a"; prev="$a"; done
mkdir -p "$wt/docs/design"; echo evil > "$wt/docs/design/hacked.md"       # Codex 越界改设计文档
git -C "$wt" add -A && git -C "$wt" -c user.email=x@x -c user.name=x commit -qm "Pack 1.1: sneak" >/dev/null
prev=""; for a in "$@"; do [ "$prev" = "-o" ] && echo done > "$a"; prev="$a"; done
echo "session id: sess-evil"
FAKE
chmod +x "$FAKEBIN/codex-evil"
CODEX_BIN="$FAKEBIN/codex-evil"
if OUT_E="$(CODEX_BIN="$FAKEBIN/codex-evil" bash "$CW" dispatch --plan "$PLAN" --worktree "$TMP/wt-evil" 2>&1)"; then no "Codex 改 docs/ 应退非零"; else ok "Codex 改 docs/ → fail-closed 退非零"; fi
echo "$OUT_E" | grep -q "DOCS_VIOLATION" && ok "报 DOCS_VIOLATION(留痕可见)" || no "无 DOCS_VIOLATION"
echo "$OUT_E" | grep -q "docs/design/hacked.md" && ok "列出越界文件" || no "未列越界文件"

# resume 也守 docs/ 边界(resume 续修时越界同样 fail-closed)
cat > "$FAKEBIN/codex-evil2" <<'FAKE'
#!/usr/bin/env bash
wt=""; prev=""; for a in "$@"; do [ "$prev" = "-C" ] && wt="$a"; prev="$a"; done
echo more >> "$wt/docs/design/hacked.md"
prev=""; for a in "$@"; do [ "$prev" = "-o" ] && echo done > "$a"; prev="$a"; done
echo "session id: sess-evil"
FAKE
chmod +x "$FAKEBIN/codex-evil2"
if OUT_R="$(CODEX_BIN="$FAKEBIN/codex-evil2" bash "$CW" resume --worktree "$TMP/wt-evil" --instructions "$INSTR" 2>&1)"; then no "resume 改 docs/ 应退非零"; else ok "resume 改 docs/ → fail-closed 退非零"; fi
echo "$OUT_R" | grep -q "DOCS_VIOLATION" && ok "resume 越界报 DOCS_VIOLATION" || no "resume 无 DOCS_VIOLATION"

# 越界已全部提交进历史、resume 期间工人不再动 → 仍核到(基线钉派发时持久化,不随 resume HEAD 漂移)
cat > "$FAKEBIN/codex-clean" <<'FAKE'
#!/usr/bin/env bash
prev=""; for a in "$@"; do [ "$prev" = "-o" ] && echo done > "$a"; prev="$a"; done
echo "session id: sess-evil"
FAKE
chmod +x "$FAKEBIN/codex-clean"
git -C "$TMP/wt-evil" add -A >/dev/null 2>&1
git -C "$TMP/wt-evil" -c user.email=x@x -c user.name=x commit -qm "Pack 1.2: bury evidence" >/dev/null 2>&1
if OUT_R2="$(CODEX_BIN="$FAKEBIN/codex-clean" bash "$CW" resume --worktree "$TMP/wt-evil" --instructions "$INSTR" 2>&1)"; then no "已提交越界 resume 应仍退非零"; else ok "已提交越界 → resume 仍 fail-closed(基线钉派发)"; fi
echo "$OUT_R2" | grep -q "docs/design/hacked.md" && ok "resume 列出历史越界文件" || no "resume 未列历史越界"

# ===== Droid backend: 派发包 + worker/ 分支 + check-docs fail-closed =====
export MMW_HOST=droid
STATE_SUBDIR=.factory/multi-model-workflow
WT_D="$TMP/wt-droid"
OUT_D="$(bash "$CW" dispatch --plan "$PLAN" --worktree "$WT_D" --design "$DESIGN" --issue "$ISSUE" 2>/dev/null)"
echo "$OUT_D" | grep -q "WORKER_BACKEND=droid-task" && ok "droid dispatch 后端 droid-task" || no "droid backend"
[ "$(git -C "$WT_D" branch --show-current)" = "worker/wt-droid" ] && ok "droid 子 worktree 挂 worker/<名>" || no "droid worker 分支"
[ -f "$WT_D/$STATE_SUBDIR/worker-dispatch/prompt.md" ] && ok "droid 派发包 prompt.md" || no "droid prompt 包"
[ -f "$WT_D/$STATE_SUBDIR/worker-dispatch/meta.json" ] && ok "droid 派发包 meta.json" || no "droid meta"
[ -f "$WT_D/$STATE_SUBDIR/worker-dispatch/start_sha" ] && ok "droid 记 start_sha" || no "droid start_sha"
echo "$OUT_D" | grep -q "check-docs" && ok "droid 回执要求 check-docs" || no "droid 回执 check-docs"
# 干净树 check-docs 应过
if bash "$CW" check-docs --worktree "$WT_D" >/dev/null 2>&1; then ok "droid check-docs 干净树通过"; else no "droid check-docs 干净应过"; fi
# 污染 docs 后 check-docs 应 fail
mkdir -p "$WT_D/docs/x"; echo bad > "$WT_D/docs/x/h.md"
git -C "$WT_D" add -A && git -C "$WT_D" -c user.email=x@x -c user.name=x commit -qm "sneak docs" >/dev/null
if OUT_CD="$(bash "$CW" check-docs --worktree "$WT_D" 2>&1)"; then no "droid check-docs 应拦 docs 污染"; else ok "droid check-docs 拦 docs 污染"; fi
echo "$OUT_CD" | grep -q "DOCS_VIOLATION" && ok "droid check-docs 报 DOCS_VIOLATION" || no "droid 无 DOCS_VIOLATION 字样"
# resume 写 resume 包
INSTR_D="$TMP/fix-d.md"; echo "fix droid" > "$INSTR_D"
OUT_DR="$(bash "$CW" resume --worktree "$WT_D" --instructions "$INSTR_D" 2>/dev/null)"
echo "$OUT_DR" | grep -q "WORKER_MODE=resume" && ok "droid resume 写 resume 包" || no "droid resume"
grep -q "fix droid" "$WT_D/$STATE_SUBDIR/worker-dispatch/prompt.md" && ok "droid resume prompt=指令" || no "droid resume prompt"
unset MMW_HOST
export MMW_HOST=claude
STATE_SUBDIR=.claude/multi-model-workflow

# ===== 写计划派发(plan-dispatch;任务 worktree 内、不开子 worktree、只碰 docs/plans+issues、不 commit)=====
CODEX_BIN="$FAKEBIN/codex"   # 复位干净 fake
WT_TASK="$TMP/wt-task"
git worktree add -q -b task/x "$WT_TASK" HEAD
PLAN_OUT="$WT_TASK/docs/plans/x/001-foo.md"
OUT_P="$(bash "$CW" plan-dispatch --plan "$PLAN_OUT" --worktree "$WT_TASK" --design "$DESIGN" --issue "$ISSUE" 2>/dev/null)"
PROMPT_P="$(cat "$FAKE_CAP/stdin")"
echo "$PROMPT_P" | grep -q "worktree-plan" && ok "plan prompt 指向 worktree-plan skill" || no "plan 指 worktree-plan"
echo "$PROMPT_P" | grep -q "不 commit" && ok "plan prompt 声明不 commit" || no "plan 不 commit 声明"
echo "$PROMPT_P" | grep -q "task-pack" && no "plan prompt 不该再注入方法论路径(在 skill references)" || ok "plan prompt 不注入 task-pack 路径(委托 skill)"
echo "$PROMPT_P" | grep -q "plan-self-check" && no "plan prompt 不该再注入自检路径(在 skill references)" || ok "plan prompt 不注入 self-check 路径(委托 skill)"
echo "$PROMPT_P" | grep -q "$PLAN_OUT" && ok "plan prompt 传落点" || no "plan 落点"
echo "$PROMPT_P" | grep -q "本消息不重复" && ok "plan prompt 委托 skill(纯路由)" || no "plan 纯路由"
ARGV_P="$(cat "$FAKE_CAP/argv")"
echo "$ARGV_P" | grep -q -- "-C $WT_TASK" && ok "plan codex -C 任务 worktree(不开子 worktree)" || no "plan -C 任务 wt"
echo "$ARGV_P" | grep -q -- "--sandbox workspace-write" && ok "plan --sandbox workspace-write" || no "plan sandbox"
echo "$ARGV_P" | grep -q 'model_reasoning_effort="high"' && ok "plan 用 high(CODEX_PLAN_EFFORT)" || no "plan effort($ARGV_P)"
echo "$ARGV_P" | grep -q -- "-m gpt-5.6-sol" && ok "plan 用 gpt-5.6-sol(CODEX_PLAN_MODEL)" || no "plan 模型档"
echo "$OUT_P" | grep -q "PLAN_WORKER_NS=001-foo" && ok "plan 回执报命名空间 ns" || no "plan ns 回执"
[ "$(cat "$WT_TASK/${STATE_SUBDIR}/plan-workers/001-foo/codex-session")" = "sess-123" ] && ok "plan session 落 plan-workers/<ns>(并行隔离)" || no "plan session 命名空间"
git -C "$WT_TASK" worktree list | grep -q "001-foo" && no "plan 不该开子 worktree" || ok "plan 不开子 worktree(在任务 wt 内写)"
[ "$(cat "$WT_TASK/${STATE_SUBDIR%%/*}/.gitignore" 2>/dev/null)" = "*" ] && ok "plan 自设状态平面 gitignore(防 plan-workers 被边界误报)" || no "plan state gitignore"

# plan-check 边界:干净(fake 没写文件)→ pass;越界写源码 → PLAN_VIOLATION;docs/plans+issues → 放行
if bash "$CW" plan-check --plan "$PLAN_OUT" --worktree "$WT_TASK" >/dev/null 2>&1; then ok "plan-check 干净树过"; else no "plan-check 干净应过"; fi
echo evil > "$WT_TASK/hack.py"
if OUT_PV="$(bash "$CW" plan-check --plan "$PLAN_OUT" --worktree "$WT_TASK" 2>&1)"; then no "plan-check 碰源码应拦"; else ok "plan-check 拦源码越界"; fi
echo "$OUT_PV" | grep -q "PLAN_VIOLATION" && ok "报 PLAN_VIOLATION" || no "无 PLAN_VIOLATION"
echo "$OUT_PV" | grep -q "hack.py" && ok "列出越界文件 hack.py" || no "未列越界文件"
rm -f "$WT_TASK/hack.py"
mkdir -p "$WT_TASK/docs/plans/x" "$WT_TASK/docs/issues/x"; echo p > "$PLAN_OUT"; echo i > "$WT_TASK/docs/issues/x/001.md"
if bash "$CW" plan-check --plan "$PLAN_OUT" --worktree "$WT_TASK" >/dev/null 2>&1; then ok "plan-check 放行 docs/plans+docs/issues"; else no "plan-check 应放行 docs/plans+issues"; fi

# plan-resume 续原 session(重钉围栏 + 复用 plan 档)
INSTR_P="$TMP/fix-plan.md"; echo "fix plan" > "$INSTR_P"
OUT_PR="$(bash "$CW" plan-resume --plan "$PLAN_OUT" --worktree "$WT_TASK" --instructions "$INSTR_P" 2>/dev/null)"
ARGV_PR="$(cat "$FAKE_CAP/argv")"
echo "$ARGV_PR" | grep -q "resume sess-123" && ok "plan-resume 续原 session" || no "plan-resume session"
echo "$ARGV_PR" | grep -q -- "-C $WT_TASK" && ok "plan-resume 重钉 -C 任务 wt" || no "plan-resume -C"
[ "$(cat "$FAKE_CAP/stdin")" = "fix plan" ] && ok "plan-resume 发回修复指令" || no "plan-resume 指令"
# plan-resume 无 session 记账 → fail-closed
if bash "$CW" plan-resume --plan "$WT_TASK/docs/plans/x/999.md" --worktree "$WT_TASK" --instructions "$INSTR_P" >/dev/null 2>&1; then no "plan-resume 无 session 应拒"; else ok "plan-resume 无 session 被拒(fail-closed)"; fi

# Droid backend 写计划:派 plan-writer droid + plan-check 回执(用干净任务 worktree,避开 .claude 平面复用)
export MMW_HOST=droid
STATE_SUBDIR_D=.factory/multi-model-workflow
WT_TASK_D="$TMP/wt-task-d"
git worktree add -q -b task/xd "$WT_TASK_D" HEAD
PLAN_OUT_D="$WT_TASK_D/docs/plans/x/001-bar.md"
OUT_DP="$(bash "$CW" plan-dispatch --plan "$PLAN_OUT_D" --worktree "$WT_TASK_D" --design "$DESIGN" --issue "$ISSUE" 2>/dev/null)"
echo "$OUT_DP" | grep -q "DROID=plan-writer" && ok "droid 写计划派 plan-writer droid" || no "droid plan droid"
echo "$OUT_DP" | grep -q "plan-check" && ok "droid 写计划回执要求 plan-check" || no "droid plan-check 回执"
[ -f "$WT_TASK_D/$STATE_SUBDIR_D/plan-workers/001-bar/dispatch/prompt.md" ] && ok "droid 写计划派发包 prompt.md" || no "droid plan pkg prompt"
grep -q "worktree-plan" "$WT_TASK_D/$STATE_SUBDIR_D/plan-workers/001-bar/dispatch/prompt.md" && ok "droid plan prompt 指 plugin 内 worktree-plan" || no "droid plan prompt skill 指针"
unset MMW_HOST
export MMW_HOST=claude
STATE_SUBDIR=.claude/multi-model-workflow

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

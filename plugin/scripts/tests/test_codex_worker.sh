#!/usr/bin/env bash
# codex-worker.sh 空跑(fake codex):派发组对 prompt 铁律 + codex 参数、建 worktree、
# 记 session、resume 续会话。不连真 Codex。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CW="$SCRIPT_DIR/../codex-worker.sh"

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
[ "$(cat "$WT/.claude/.gitignore" 2>/dev/null)" = "*" ] && ok "状态平面 .claude/ 已 gitignore(防 add -A 污染)" || no ".claude gitignore"
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
echo "$ARGV" | grep -q -- "--add-dir" && ok "--add-dir 放行 git common dir" || no "add-dir"
echo "$OUT" | grep -q "SESSION=sess-123" && ok "抓到并打印 session id" || no "session 记账"
[ "$(cat "$WT/.claude/multi-model-workflow/codex-session")" = "sess-123" ] && ok "session 落盘供 resume" || no "session 落盘"
echo "$OUT" | grep -q "codex done" && ok "打印 codex 最后消息(供验收)" || no "最后消息"
# design/issue 可空(small-change/bug):空时不应出现裸标签行(放最后,免得覆盖上面 argv 断言)
bash "$CW" dispatch --plan "$PLAN" --worktree "$TMP/wt-nodoc" >/dev/null 2>&1
PROMPT2="$(cat "$FAKE_CAP/stdin")"
echo "$PROMPT2" | grep -q "设计文档(意图" && no "无 design 时不该出现设计行" || ok "design 可空:无则不出设计行"

# resume:用记的 session 续会话
INSTR="$TMP/fix.md"; echo "fix this" > "$INSTR"
OUT2="$(bash "$CW" resume --worktree "$WT" --instructions "$INSTR" 2>/dev/null)"
ARGV2="$(cat "$FAKE_CAP/argv")"
echo "$ARGV2" | grep -q "exec resume sess-123" && ok "resume 走 codex exec resume <session>" || no "resume session"
[ "$(cat "$FAKE_CAP/stdin")" = "fix this" ] && ok "resume 发回修复指令" || no "resume 指令"

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

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

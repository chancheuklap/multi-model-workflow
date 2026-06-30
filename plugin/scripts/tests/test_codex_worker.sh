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
WT="$TMP/wt-001"

OUT="$(bash "$CW" dispatch --plan "$PLAN" --worktree "$WT" 2>/dev/null)"
[ -d "$WT" ] && ok "worktree 不存在则建好" || no "建 worktree"
PROMPT="$(cat "$FAKE_CAP/stdin")"
echo "$PROMPT" | grep -q "严防过度设计" && ok "prompt 含严防过度设计铁律" || no "反过度设计"
echo "$PROMPT" | grep -q "禁改 docs/" && ok "prompt 含禁改 docs" || no "禁改 docs"
echo "$PROMPT" | grep -q 'Pack N.M' && ok "prompt 含 Pack N.M 提交格式" || no "Pack N.M"
echo "$PROMPT" | grep -q "TDD" && ok "prompt 含 TDD 纪律" || no "TDD"
echo "$PROMPT" | grep -q "公开行为" && ok "prompt 含 测公开行为/不测 private 纪律" || no "测公开行为"
echo "$PROMPT" | grep -q "项目自己的测试治理文档为准" && ok "prompt 含 测试绑定仓库标准文档" || no "测试绑仓库标准"
echo "$PROMPT" | grep -q "正式契约类型" && ok "prompt 含 跨边界正式契约/不裸 dict 纪律" || no "正式契约"
echo "$PROMPT" | grep -q "登记 + 走校验器" && ok "prompt 含 登记+校验器/迁移对称 纪律" || no "登记校验"
ARGV="$(cat "$FAKE_CAP/argv")"
echo "$ARGV" | grep -q -- "-C $WT" && ok "codex -C <worktree>" || no "-C worktree"
echo "$ARGV" | grep -q -- "--sandbox workspace-write" && ok "--sandbox workspace-write" || no "sandbox"
echo "$ARGV" | grep -q -- "--add-dir" && ok "--add-dir 放行 git common dir" || no "add-dir"
echo "$OUT" | grep -q "SESSION=sess-123" && ok "抓到并打印 session id" || no "session 记账"
[ "$(cat "$WT/.claude/multi-model-workflow/codex-session")" = "sess-123" ] && ok "session 落盘供 resume" || no "session 落盘"
echo "$OUT" | grep -q "codex done" && ok "打印 codex 最后消息(供验收)" || no "最后消息"

# resume:用记的 session 续会话
INSTR="$TMP/fix.md"; echo "fix this" > "$INSTR"
OUT2="$(bash "$CW" resume --worktree "$WT" --instructions "$INSTR" 2>/dev/null)"
ARGV2="$(cat "$FAKE_CAP/argv")"
echo "$ARGV2" | grep -q "exec resume sess-123" && ok "resume 走 codex exec resume <session>" || no "resume session"
[ "$(cat "$FAKE_CAP/stdin")" = "fix this" ] && ok "resume 发回修复指令" || no "resume 指令"

# fail-closed
if bash "$CW" dispatch --plan /nope.md --worktree "$WT" >/dev/null 2>&1; then no "缺/坏 plan 被拒"; else ok "坏 plan 被拒"; fi
if bash "$CW" resume --worktree "$TMP/nowt" --instructions "$INSTR" >/dev/null 2>&1; then no "无 session 被拒"; else ok "无 session 被拒(fail-closed)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

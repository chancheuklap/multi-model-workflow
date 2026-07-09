#!/usr/bin/env bash
# progress.sh 投影板:无任务不伪造、聚合真相源、可从真相重建、fail-closed。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROG="$SCRIPT_DIR/../progress.sh"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_progress.sh ==="
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cd "$TMP"; git init -q; git config user.email t@t; git config user.name t; echo s>s; git add -A; git commit -qm s
SD=.claude/multi-model-workflow; mkdir -p "$SD"
BOARD="$SD/progress-board.md"

# 无 task.json:不伪造状态
OUT="$(bash "$PROG" render)"
echo "$OUT" | grep -q "NO-ACTIVE-RUN" && ok "无任务 → NO-ACTIVE-RUN(不伪造)" || no "无任务处理 ($OUT)"
[ ! -f "$BOARD" ] && ok "无任务不落板" || no "无任务不该落板"

# 造真相源
cat > "$SD/task.json" <<'J'
{"slug":"demo","scenario":"develop","phase":"build","status":"active","attendance":"unattended","repair_count":0,
"open_items":[{"tag":"bug","finding":"空指针","from_phase":"build","disposition":"fix_now"}]}
J
cat > "$SD/loop-state.json" <<'J'
{"schema_version":"1","kind":"execution","round":1,"max_rounds":0,"guard_blocks":0,
"steps":[{"id":"1.1","desc":"a","status":"done","plan":"001"}],
"checklist":[],"findings":[],"decisions":[],"pause":null}
J

bash "$PROG" render >/dev/null
[ -f "$BOARD" ] && ok "render 落板" || no "render 落板"
grep -q "值守模式：\*\*unattended\*\*" "$BOARD" && ok "板反映 mode=unattended" || no "板 mode"
grep -q "demo" "$BOARD" && ok "板含 slug" || no "板 slug"
grep -q "001" "$BOARD" && ok "板含 plan 步" || no "板 plan"
grep -q "fix_now" "$BOARD" && ok "板含计划外项 disposition" || no "板计划外项"

# --stdout 打全文到 stdout
bash "$PROG" render --stdout | grep -q "# Progress Board" && ok "--stdout 打板全文(供注入)" || no "--stdout"

# 从真相重建:删板仍能重渲染
rm -f "$BOARD"
bash "$PROG" render >/dev/null
[ -f "$BOARD" ] && ok "板丢失可从真相源重建" || no "重建"

# task.json 损坏 → 报错不静默
echo 'not json' > "$SD/task.json"
if bash "$PROG" render >/dev/null 2>&1; then no "损坏 task.json 应报错"; else ok "损坏 task.json → 报错退非零(不静默)"; fi

echo ""; echo "Results: $pass passed, $fail failed"; [ "$fail" = 0 ]

#!/usr/bin/env bash
# 完成拦截：有未清关卡顶回、全清放行、文件损坏/缺失放行、连续无进展放行、三家输出形状、stdin 不关闭超时。
set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
H="$(dirname "$HERE")"
rc=0
fail() { echo "失败：$1" >&2; rc=1; }
ROOT="$(mktemp -d)"
STATE="$ROOT/.mmw-ticket-state.json"
stop() { printf '{"cwd":"%s","session_id":"s1"}' "$ROOT" | node "$H/mmw-stop.mjs" "$@"; }
unmet='{"ticket":54,"branch":"ticket/54-x","gates":[{"text":"tests green","kind":"check","check":"bash run.sh","expect":"全过","manual":null,"checked":true,"evidence":"全过"},{"text":"README updated","kind":"manual","check":null,"expect":null,"manual":"user","checked":false,"evidence":null}]}'

# 文件缺失：放行，无输出。
out="$(stop)"; [ -z "$out" ] || fail "缺失应放行且无输出：$out"

# 未清：顶回，Claude 形状。
printf '%s' "$unmet" > "$STATE"
out="$(stop)"
python3 - "$out" <<'PY' || fail "未清应输出 decision:block 并点名关卡"
import json,sys; d=json.loads(sys.argv[1]); assert d["decision"]=="block" and "G2 README updated" in d["reason"] and "#54" in d["reason"], d
PY

# 各家形状。
out="$(stop --host cursor)"
python3 - "$out" <<'PY' || fail "Cursor 应是 {followup_message}"
import json,sys; d=json.loads(sys.argv[1]); assert list(d)==["followup_message"]
PY
out="$(GROK_HOOK_EVENT=stop stop --host claude)"
python3 - "$out" <<'PY' || fail "Grok 应是 decision:block"
import json,sys; d=json.loads(sys.argv[1]); assert d["decision"]=="block"
PY
out="$(stop --host codex)"
python3 - "$out" <<'PY' || fail "Codex 应是 decision:block"
import json,sys; d=json.loads(sys.argv[1]); assert d["decision"]=="block"
PY

# 全清：放行，会话状态清掉。
python3 - "$STATE" <<'PY'
import json,sys; p=sys.argv[1]; d=json.load(open(p)); [g.update(checked=True, evidence="ok") for g in d["gates"]]; json.dump(d, open(p,"w"))
PY
out="$(stop)"; [ -z "$out" ] || fail "全清应放行：$out"
[ ! -e "$ROOT/.mmw-hook-state.json" ] || fail "全清后钩子状态文件应被清掉"

# 损坏：放行。
printf '{"gates": [' > "$STATE"
out="$(stop)"; [ -z "$out" ] || fail "损坏应放行：$out"
printf '{"ticket":1}' > "$STATE"
out="$(stop)"; [ -z "$out" ] || fail "没有 gates 数组应放行：$out"

# 连续无进展：MAX_BLOCKS=6，第 7 次放行。
printf '%s' "$unmet" > "$STATE"
rm -f "$ROOT/.mmw-hook-state.json"
for i in 1 2 3 4 5 6; do
  out="$(stop)"; [[ "$out" == *'"decision":"block"'* ]] || fail "第 $i 次应仍顶回：$out"
done
out="$(stop)"; [[ "$out" == *"releasing after 6 blocks"* ]] || fail "第 7 次应放行并说明：$out"
# 有进展（勾掉一条）就重新计数。
python3 - "$STATE" <<'PY'
import json,sys; p=sys.argv[1]; d=json.load(open(p)); d["gates"].append({"text":"x","kind":"manual","check":None,"expect":None,"manual":"u","checked":False,"evidence":None}); json.dump(d, open(p,"w"))
PY
out="$(stop)"; [[ "$out" == *'"decision":"block"'* ]] || fail "关卡集合变了应重新顶回：$out"

# stdin 坏 JSON：放行。
out="$(echo 'garbage' | node "$H/mmw-stop.mjs")"; [ -z "$out" ] || fail "stdin 坏 JSON 应放行：$out"

# stdin 永不关闭：超时后退出并放行。
fifo="$(mktemp -d)/p"; mkfifo "$fifo"; exec 3<>"$fifo"
node "$H/mmw-stop.mjs" <"$fifo" >/dev/null &
pid=$!
for _ in $(seq 1 40); do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
if kill -0 "$pid" 2>/dev/null; then kill "$pid"; fail "stdin 不关闭时应在超时后退出"; fi
exec 3>&-

exit "$rc"

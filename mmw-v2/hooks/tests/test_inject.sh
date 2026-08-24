#!/usr/bin/env bash
# 开场注入、subagent 注入、pi 扩展：每家输出形状对不对，纪律标记行在不在。
set -uo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
H="$(dirname "$HERE")"
rc=0
fail() { echo "失败：$1" >&2; rc=1; }
MARK='MMW DISCIPLINE ACTIVE — role: worker'
REDLINE='input validation at trust boundaries'

out="$(node "$H/mmw-activate.js" </dev/null)"
[[ "$out" == "$MARK"* ]] || fail "Claude 开场：裸 stdout 应以标记行开头"
[[ "$out" == *"$REDLINE"* ]] || fail "Claude 开场：缺安全红线"

out="$(node "$H/mmw-activate.js" --host codex </dev/null)"
python3 - "$out" <<'PY' || fail "Codex 开场：JSON 形状不对"
import json,sys; d=json.loads(sys.argv[1]); h=d["hookSpecificOutput"]
assert h["hookEventName"]=="SessionStart" and h["additionalContext"].startswith("MMW DISCIPLINE ACTIVE — role: worker") and d["systemMessage"]=="MMW:WORKER"
PY

out="$(node "$H/mmw-activate.js" --host cursor </dev/null)"
python3 - "$out" <<'PY' || fail "Cursor 开场：应是 {additional_context}"
import json,sys; d=json.loads(sys.argv[1]); assert list(d)==["additional_context"] and d["additional_context"].startswith("MMW DISCIPLINE ACTIVE")
PY

out="$(GROK_HOOK_EVENT=session_start node "$H/mmw-activate.js" --host claude </dev/null)"
python3 - "$out" <<'PY' || fail "Grok 跑 Claude 配置：环境变量应优先，输出 hookSpecificOutput JSON"
import json,sys; d=json.loads(sys.argv[1]); assert d["hookSpecificOutput"]["hookEventName"]=="SessionStart"
PY

out="$(echo '{"agent_type":"general-purpose"}' | node "$H/mmw-subagent.js")"
python3 - "$out" <<'PY' || fail "Claude subagent：必须是 hookSpecificOutput 形式且为工人块"
import json,sys; d=json.loads(sys.argv[1]); h=d["hookSpecificOutput"]
assert h["hookEventName"]=="SubagentStart" and "role: worker" in h["additionalContext"]
PY

out="$(echo '{"agent_type":"mmw-verifier"}' | node "$H/mmw-subagent.js")"
[[ "$out" == *"role: verifier"* && "$out" == *"Do not invent project-local CRAP"* ]] || fail "subagent：agent_type 含 verifier 应注入复验者块"

out="$(echo '{"subagent_type":"explore"}' | node "$H/mmw-subagent.js" --host cursor)"
python3 - "$out" <<'PY' || fail "Cursor subagent：应是 {additional_context}"
import json,sys; d=json.loads(sys.argv[1]); assert list(d)==["additional_context"]
PY

out="$(echo '{"agent_type":"general"}' | MMW_SUBAGENT_MATCHER='^explore$' node "$H/mmw-subagent.js")"
[ -z "$out" ] || fail "subagent 过滤：agent_type 不命中 MMW_SUBAGENT_MATCHER 应不注入"

out="$(echo 'not json' | MMW_SUBAGENT_MATCHER='^explore$' node "$H/mmw-subagent.js")"
[[ "$out" == *"role: worker"* ]] || fail "subagent 过滤：stdin 解析失败应 fail-open 注入"

out="$(echo '{"agent_type":"general"}' | MMW_SUBAGENT_MATCHER='(' node "$H/mmw-subagent.js")"
[[ "$out" == *"role: worker"* ]] || fail "subagent 过滤：坏正则应当没设、照常注入"

# stdin 永不关闭：1 秒超时后必须自己退出。
fifo="$(mktemp -d)/p"; mkfifo "$fifo"; exec 3<>"$fifo"
start=$(date +%s)
node "$H/mmw-subagent.js" <"$fifo" >/dev/null &
pid=$!
for _ in $(seq 1 40); do kill -0 "$pid" 2>/dev/null || break; sleep 0.1; done
if kill -0 "$pid" 2>/dev/null; then kill "$pid"; fail "subagent：stdin 不关闭时应在超时后退出"; fi
exec 3>&-
[ $(( $(date +%s) - start )) -le 3 ] || fail "subagent：超时退出用时过长"

# pi 扩展：before_agent_start 返回追加了纪律的系统提示。
node --input-type=module -e "
import ext from '$H/pi-extension/index.js';
const handlers = {};
ext({ on: (name, fn) => { handlers[name] = fn; } });
if (!handlers.before_agent_start) { console.error('没注册 before_agent_start'); process.exit(1); }
const r = await handlers.before_agent_start({ systemPrompt: 'BASE' });
if (!r.systemPrompt.startsWith('BASE\n\nMMW DISCIPLINE ACTIVE — role: worker')) { console.error('系统提示形状不对: ' + r.systemPrompt.slice(0, 80)); process.exit(1); }
const r2 = await handlers.before_agent_start(undefined);
if (!r2.systemPrompt.startsWith('MMW DISCIPLINE ACTIVE')) { console.error('空 event 应只返回纪律'); process.exit(1); }
" || fail "pi 扩展"

exit "$rc"

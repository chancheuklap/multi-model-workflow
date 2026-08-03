#!/usr/bin/env bash
# pi hooks 离线合同：红线脚本 argv/env、提交记账、分诊输出、扩展事件接线。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN="$(cd "$SCRIPT_DIR/../.." && pwd)"
GUARD="$PLUGIN/hooks/guard-redline.sh"
RECORD="$PLUGIN/hooks/record-step.sh"
TRIAGE="$PLUGIN/hooks/session-triage.sh"
EXT="$PLUGIN/extensions/mmw-hooks.ts"
LOOP="$PLUGIN/scripts/loop.sh"
SD=.pi/multi-model-workflow
pass=0; fail=0
ok(){ echo "  PASS: $1"; pass=$((pass+1)); }
no(){ echo "  FAIL: $1"; fail=$((fail+1)); }

echo '=== test_hooks.sh ==='
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
git -C "$TMP" init -q
git -C "$TMP" config user.email test@example.com
git -C "$TMP" config user.name Test
printf seed >"$TMP/seed.txt"; git -C "$TMP" add .; git -C "$TMP" commit -qm seed

bash "$GUARD" 'echo push' >/dev/null 2>&1 && ok '参数位 push 不误拦' || no '安全命令误拦'
if bash "$GUARD" 'git push origin main' >/dev/null 2>"$TMP/reason"; then no 'git push 应拦';
elif [ "$?" = 2 ] && grep -q 'git push' "$TMP/reason"; then ok 'git push → exit 2 + 原因'; else no 'git push 返回合同'; fi
bash "$GUARD" 'git merge feature' >/dev/null 2>&1 && ok '本地 git merge 放行' || no '本地 merge 误拦'
if MMW_TOOL_COMMAND='terraform destroy -auto-approve' bash "$GUARD" >/dev/null 2>"$TMP/reason2"; then no 'terraform destroy 应拦';
elif [ "$?" = 2 ] && grep -q '部署' "$TMP/reason2"; then ok 'env 通道红线命中'; else no 'env 红线合同'; fi

SQL_HEREDOC="$(cat <<'CMD'
uv tool install --force 'graphifyy[sql]==0.9.25' && python3 - <<'PY'
import tree_sitter_sql
print(tree_sitter_sql.__file__)
PY
CMD
)"
bash "$GUARD" "$SQL_HEREDOC" >/dev/null 2>&1 \
  && ok 'SQL 安装 heredoc 不误报守卫异常' || no 'SQL heredoc 触发守卫异常'

mkdir -p "$TMP/slow-hooks"
cat >"$TMP/slow-hooks/slow.sh" <<'SH'
#!/usr/bin/env bash
sleep 1
SH
cat >"$TMP/hook-wrapper.mjs" <<'JS'
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
const { runHook } = await import(pathToFileURL(process.env.MMW_EXT).href);
const hooks = process.env.MMW_HOOKS;
const slow = process.env.MMW_SLOW_HOOKS;
const safeCommand = `uv tool install --force 'graphifyy[sql]==0.9.25' && python3 - <<'PY'\nimport tree_sitter_sql\nPY`;
const safe = await runHook('guard-redline.sh', safeCommand, 10_000, hooks);
assert.equal(safe.code, 0);
const blocked = await runHook('guard-redline.sh', 'git push origin main', 10_000, hooks);
assert.equal(blocked.code, 2);
assert.match(blocked.stderr, /git push/);
const missing = await runHook('missing.sh', 'true', 1_000, hooks);
assert.equal(missing.code, 127);
assert.match(missing.stderr, /missing\.sh/);
const timedOut = await runHook('slow.sh', 'true', 10, slow);
assert.equal(timedOut.code, 124);
assert.match(timedOut.stderr, /timeout=10ms/);
JS
if MMW_EXT="$EXT" MMW_HOOKS="$PLUGIN/hooks" MMW_SLOW_HOOKS="$TMP/slow-hooks" \
  node "$TMP/hook-wrapper.mjs" >/dev/null 2>"$TMP/node.err"; then
  ok 'Node hook 包装层区分放行、红线、缺文件与超时'
else
  no "Node hook 包装层诊断:$(cat "$TMP/node.err")"
fi

OUT="$(cd "$TMP" && bash "$TRIAGE")"
[ -z "$OUT" ] && ok '未在管仓库不注入 MMW 分诊' || no "未在管仓库应静默:$OUT"

mkdir -p "$TMP/$SD"
printf '{"attendance":"attended"}\n' >"$TMP/$SD/task.json"
(cd "$TMP" && bash "$LOOP" init >/dev/null && bash "$LOOP" step add --id 1.1 --desc test >/dev/null)
printf change >>"$TMP/seed.txt"; git -C "$TMP" add seed.txt; git -C "$TMP" commit -qm 'Pack 1.1: test'
(cd "$TMP" && bash "$RECORD" 'git commit -m "Pack 1.1: test"')
[ "$(jq -r '.steps[0].status' "$TMP/$SD/loop-state.json")" = done ] \
  && ok 'git commit 后 record-step 按 HEAD Pack 号记 done' || no 'record-step 未记账'

OUT="$(cd "$TMP" && bash "$TRIAGE")"
echo "$OUT" | grep -q 'multi-model-workflow-pi' && echo "$OUT" | grep -q '续跑:' \
  && ok '在管任务分诊输出可注入文本' || no '分诊输出'

for token in 'session_start' 'session_compact' 'before_agent_start' 'tool_call' 'tool_result' 'ctx.ui.confirm' 'hasUI'; do
  grep -q "$token" "$EXT" || { no "扩展缺事件/API:$token"; continue; }
  ok "扩展接线:$token"
done
if grep -q 'session_start.*message' "$EXT"; then no 'session_start 不应直接注入 message'; else ok 'message 注入留给 before_agent_start'; fi

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

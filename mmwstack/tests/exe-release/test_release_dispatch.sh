#!/usr/bin/env bash
# release-flow.sh dispatch:P2 derive 的功能分支提交(只收 derive 自己产生的改动)、P0 的
# 直接 PAUSE、收敛护栏(fingerprint/fix_rounds/墙钟三种熔断)。
set -euo pipefail
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
RF="$SCRIPT_DIR/../../skills/exe-release/scripts/release-flow.sh"
FIX="$SCRIPT_DIR/fixtures/release-flow"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

run_release() {
  local repo="$1"
  shift
  (cd "$repo" && bash "$RF" "$@")
}

state_file() {
  printf '%s/.release/release-state.json\n' "$1"
}

new_case() {
  local name="$1" derive_argv="$2" diagnose_argv="$3"
  local repo="$TMP/$name"
  mkdir -p "$repo/scripts/release"
  git -C "$repo" init -q
  git -C "$repo" config user.email t@example.test
  git -C "$repo" config user.name release-test
  # 本机的提交前门禁可能是全局 core.hooksPath，会把这里的 seed 提交拦下来。仓库级设置压过
  # 全局，指向仓库自己的 .githooks（此夹具仓库里不存在该目录，等价于无钩子）。
  git -C "$repo" config core.hooksPath .githooks
  printf 'seed\n' > "$repo/scripts/release/existing.txt"
  # .release/ is the engine's own state directory, which a consuming repository gitignores;
  # events.jsonl stands in for this fixture's event_sink (a real one posts elsewhere).
  printf '.release/\nevents.jsonl\n' > "$repo/.gitignore"
  git -C "$repo" add -A
  git -C "$repo" commit -qm seed
  jq --argjson derive "$derive_argv" --argjson diagnose "$diagnose_argv" \
    '.stages=[{name:"doctor",run:["true"]}] | .derive=$derive | .diagnose=$diagnose' \
    "$FIX/manifest.fake.json" > "$repo/manifest.json"
  # 钥匙本身是已跟踪、已提交的文件,现实里它就活在仓库里。
  git -C "$repo" add manifest.json
  git -C "$repo" commit -qm "add manifest"
  run_release "$repo" init --manifest manifest.json >/dev/null
  printf '%s\n' "$repo"
}

fail_stage_p1() {
  run_release "$1" stage fail --stage verify_key --findings "$FIX/finding.p1.json" >/dev/null
}

fail_stage_p2() {
  run_release "$1" stage fail --stage verify_key --findings "$FIX/finding.p2.json" >/dev/null
}

assert_all_pending_from_verify_key() {
  local sf
  sf="$(state_file "$1")"
  jq -e '.source_commit != "" and .current_stage == "doctor"
    and all(.stages[]; .status == "pending")' "$sf" >/dev/null
}

# 每条 event 都要过 ReleaseLoopEvent 合同。
assert_events_are_valid_json() {
  local file="$1" bad=0 event
  while IFS= read -r event; do
    [ -n "$event" ] || continue
    printf '%s' "$event" | uv run --quiet --with 'pydantic>=2' python3 -c '
import sys
sys.path.insert(0, "'"$SCRIPT_DIR/../../skills/exe-release/scripts"'")
from release_contracts import ReleaseLoopEvent
ReleaseLoopEvent.model_validate_json(sys.stdin.read())
' || bad=1
  done < "$file"
  [ "$bad" -eq 0 ]
}

# 守:熔断不只是印一行字——driving.md 要求「熔断与花光的预算不得自己继续」,所以这一轮必须真的
# 停在 needs-redirection 上(where 报 PAUSED),并且事件流里留一条 paused。
assert_circuit_break_paused() {
  local repo="$1" label="$2" event_filter="$3"
  [ "$(run_release "$repo" where)" = "PAUSED:needs-redirection" ] \
    && ok "$label 后这一轮停在 needs-redirection" || no "$label 后 where ($(run_release "$repo" where))"
  jq -s -e "$event_filter" "$repo/events.jsonl" >/dev/null 2>&1 \
    && ok "$label 在事件流里留一条 paused" || no "$label 没留 paused 事件"
}

echo "=== test_release_dispatch.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

diagnose_empty='["sh","-c","echo {\\\"findings\\\":[]}"]'

derive_editable='["sh","-c","mkdir -p scripts/release; printf derived > scripts/release/derived.txt"]'
repo="$(new_case p2-derive "$derive_editable" "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
case "$out" in
  *"DERIVED-COMMITTED:verify_key commit="*) ok "P2 derive 提交到功能分支" ;;
  *) no "P2 未提交 ($out)" ;;
esac
case "$(git -C "$repo" log -1 --format=%s)" in
  *drift:REQUIRED_RUNTIME_PATHS*) ok "P2 commit message 使用 fingerprint" ;;
  *) no "P2 commit message ($(git -C "$repo" log -1 --format=%s))" ;;
esac
assert_all_pending_from_verify_key "$repo" && ok "P2 提交后从 verify_key 全量重验" || no "P2 未失效全部 stages"
jq -e 'any(.attempt_ledger[]; .action_kind == "derive" and .outcome == "applied" and (.artifact_refs | any(startswith("git-commit:"))))' "$sf" >/dev/null && ok "P2 ledger 记录 commit" || no "P2 ledger"
git -C "$repo" diff --quiet HEAD && ok "P2 后 tracked worktree 干净" || no "P2 后 tracked worktree 脏"
[ "$(jq -r '.budget.fix_rounds' "$sf")" = "1" ] && ok "P2 derive 提交成功算一个修复轮次" || no "P2 修复轮次 ($(jq -r '.budget.fix_rounds' "$sf"))"
# stage fail 分级时已经落过一条 classified;derive 提交成功后还要再落一条,指向产生这次提交的那次尝试。
derive_attempt="$(jq -r '[.attempt_ledger[]|select(.action_kind=="derive")][0].attempt_id' "$sf")"
jq -s -e --arg a "$derive_attempt" 'any(.[]; .event == "classified" and .tier == "P2" and .attempt_ref == $a)' "$repo/events.jsonl" >/dev/null 2>&1 \
  && assert_events_are_valid_json "$repo/events.jsonl" && ok "P2 提交后落一条指向 derive 那次尝试的合法 classified 事件" || no "P2 提交的 classified 事件缺失或不合法"

# derive 之前就在工作树里的未跟踪文件是用户自己的,不进 derive 的提交。
repo="$(new_case p2-derive-keeps-untracked "$derive_editable" "$diagnose_empty")"
printf 'scratch\n' > "$repo/notes.txt"
fail_stage_p2 "$repo"
run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json" >/dev/null
files="$(git -C "$repo" show --name-only --format= HEAD)"
case "$files" in
  *notes.txt*) no "P2 把事先存在的未跟踪文件提交了 ($files)" ;;
  *derived.txt*) ok "P2 只提交 derive 产生的文件" ;;
  *) no "P2 提交内容不对 ($files)" ;;
esac
[ -f "$repo/notes.txt" ] && [ -z "$(git -C "$repo" ls-files notes.txt)" ] && ok "事先存在的未跟踪文件原样留在工作树" || no "事先存在的未跟踪文件被动过"

repo="$(new_case p2-no-derive-executor '[]' "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && ok "钥匙没声明 derive 时交给驱动 agent" || no "无 derive 未 escalate ($out)"

repo="$(new_case p2-no-change '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
head_before="$(git -C "$repo" rev-parse HEAD)"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [ "$(git -C "$repo" rev-parse HEAD)" = "$head_before" ] && ok "derive 零改动不伪装为修复" || no "零改动错误 ($out)"

repo="$(new_case p2-preflight-dirty "$derive_editable" "$diagnose_empty")"
printf 'unrelated\n' >> "$repo/scripts/release/existing.txt"
sf="$(state_file "$repo")"
head_before="$(git -C "$repo" rev-parse HEAD)"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [ "$(git -C "$repo" rev-parse HEAD)" = "$head_before" ] && ok "derive 前已有 tracked diff 不混入自动提交" || no "tracked preflight 错误 ($out)"

repo="$(new_case direct-p0 '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p0.json")"
case "$out" in
  P0:verify_key*) ok "P0 direct dispatch 保持人工 PAUSE" ;;
  *) no "P0 dispatch 回归 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$sf")" = "needs-redirection" ] && ok "P0 direct dispatch 写 needs-redirection" || no "P0 pause 回归"
[ "$(jq -r '.stages[]|select(.name=="verify_key").status' "$sf")" = "failed" ] \
  && jq -e 'any(.attempt_ledger[]; .action_kind == "dispatch" and .outcome == "fail" and .root_cause_fingerprint == "p0_path:deploy/env")' "$sf" >/dev/null \
  && ok "P0 direct dispatch 把该 stage 标 failed 并记一条带指纹的派发账" || no "P0 direct dispatch 没记 failed 与账"
if [ -s "$repo/events.jsonl" ]; then
  assert_events_are_valid_json "$repo/events.jsonl" && ok "P0 event sink 仍产出合法 Event 合同" || no "P0 event sink/Event 合同回归"
else
  no "P0 event sink 没收到 event"
fi

repo="$(new_case fingerprint-cap '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
# 默认阈值 3 = 两次修复机会;计满 3 次同 fingerprint 观测后熔断。
fail_stage_p1 "$repo"
fail_stage_p1 "$repo"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  CIRCUIT-BREAK:fingerprint=missing_module:scipy*) ok "同 fingerprint 达阈值继续熔断" ;;
  *) no "fingerprint 熔断回归 ($out)" ;;
esac
assert_circuit_break_paused "$repo" "同 fingerprint 熔断" 'any(.[]; .event == "paused" and .fingerprint == "missing_module:scipy")'

repo="$(new_case attempt-cap '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
tmp_state="$(mktemp)"
jq '.budget.fix_rounds=1 | .budget.max_fix_rounds=1' "$sf" > "$tmp_state" && mv "$tmp_state" "$sf"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  BUDGET-EXCEEDED:fix_rounds=1*) ok "fix_rounds 预算继续熔断" ;;
  *) no "fix_rounds 预算回归 ($out)" ;;
esac
assert_circuit_break_paused "$repo" "fix_rounds 熔断" 'any(.[]; .event == "paused" and .stage == "verify_key")'

repo="$(new_case wall-clock-cap '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
tmp_state="$(mktemp)"
jq '.budget.started_at="2000-01-01T00:00:00Z"' "$sf" > "$tmp_state" && mv "$tmp_state" "$sf"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  BUDGET-EXCEEDED:wallclock=*) ok "墙钟预算继续熔断" ;;
  *) no "墙钟预算回归 ($out)" ;;
esac
assert_circuit_break_paused "$repo" "墙钟熔断" 'any(.[]; .event == "paused" and .stage == "verify_key")'

# started_at 两条 date 都解析不了,是状态文件里的一个事实错误,不是预算耗尽:引擎停下并
# 说出这个字段。拿 0 顶上会让 elapsed 变成当前 Unix 时间,比任何墙钟上限都大。
repo="$(new_case wall-clock-unreadable '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
tmp_state="$(mktemp)"
jq '.budget.started_at="not-a-date"' "$sf" > "$tmp_state" && mv "$tmp_state" "$sf"
err_file="$(mktemp)"
rc=0
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json" 2>"$err_file")" || rc=$?
[ "$rc" -eq 1 ] && ok "started_at 读不出→退 1" || no "started_at 读不出退出码=$rc"
case "$out" in
  *BUDGET-EXCEEDED*) no "started_at 读不出仍印 BUDGET-EXCEEDED ($out)" ;;
  *) ok "started_at 读不出不印 BUDGET-EXCEEDED" ;;
esac
err_text="$(cat "$err_file")"
case "$err_text" in
  *"budget.started_at"*) ok "stderr 点名 budget.started_at" ;;
  *) no "stderr 未点名 budget.started_at ($err_text)" ;;
esac

# 守:阈值 3 = 给两次修复机会。同一个指纹只观测到两次时还不熔断,继续把第二次修复交出去;
# 阈值被改成 2,正常的第二次迭代就会被误熔断。
repo="$(new_case fingerprint-below-cap '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  P1:verify_key*) ok "同 fingerprint 只见过两次时还给第二次修复机会" ;;
  *) no "同 fingerprint 两次就熔断了 ($out)" ;;
esac

# 守:findings 里没有一条失败时没有什么可派发的。若把它当成「全是瞬态」,会白白把 stage 重置重跑。
repo="$(new_case nothing-to-dispatch '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
printf '{"findings":[]}' > "$repo/no-findings.json"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$repo/no-findings.json")"
case "$out" in
  NOTHING-TO-DISPATCH:verify_key*) ok "没有失败的 finding 时不派发" ;;
  *) no "没有失败 finding 却派发了 ($out)" ;;
esac
[ "$(jq -r '.pause' "$sf")" = "null" ] && [ "$(jq -r '.attempt_ledger|length' "$sf")" = "0" ] \
  && ok "没有失败 finding 时状态原样不动" || no "没有失败 finding 却改了状态"

# 守:派发时拿到的 findings 读不出合法的 Finding,就交给驱动 agent,而不是当作没事。
repo="$(new_case dispatch-unclassifiable '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.bad.json" 2>/dev/null)"
case "$out" in
  UNCLASSIFIABLE:verify_key*) ok "派发时读不出合法 finding 就升级" ;;
  *) no "派发时读不出 finding 的处理 ($out)" ;;
esac
[ "$(run_release "$repo" where)" = "PAUSED:needs-context" ] \
  && ok "读不出 finding 时这一轮停在 needs-context" || no "读不出 finding 后 where ($(run_release "$repo" where))"

# 守:P1 没有自动修复,交给正在驱动出包的 agent:写一份简报、停在 needs-context、pause 的问题指向简报;
# agent 照简报改代码并提交之后 resume,看见 HEAD 变了就把全部 stage 重验一遍(driving.md 的 P1 全程)。
repo="$(new_case p1-handoff '["true"]' "$diagnose_empty")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
brief_path="${out##*(}"
brief_path="${brief_path%)}"
case "$out" in
  P1:verify_key*) ok "P1 交给驱动 agent" ;;
  *) no "P1 交接 ($out)" ;;
esac
[ -s "$brief_path" ] && [ "$brief_path" != "$FIX/finding.p1.json" ] \
  && grep -q "missing_module:scipy" "$brief_path" && grep -qi "commit" "$brief_path" \
  && ok "P1 简报落了地,带着这条 finding 和「提交后 resume」的要求" || no "P1 简报缺失、退回成原始 findings,或没要求提交 ($brief_path)"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [[ "$(jq -r '.pause.question' "$sf")" == *"$brief_path"* ]] \
  && ok "P1 停在 needs-context,问题指向简报" || no "P1 pause ($(jq -c '.pause' "$sf"))"
[ "$(run_release "$repo" where)" = "PAUSED:needs-context" ] && ok "P1 交接后 where PAUSED:needs-context" || no "P1 后 where ($(run_release "$repo" where))"
jq -e 'any(.attempt_ledger[]; .action_kind == "fix_dispatch" and .outcome == "handed_to_agent" and .root_cause_fingerprint == "missing_module:scipy")' "$sf" >/dev/null \
  && ok "P1 交接记进 attempt_ledger" || no "P1 交接没进 attempt_ledger"
jq -s -e 'any(.[]; .event == "paused" and .tier == "P1" and .fingerprint == "missing_module:scipy")' "$repo/events.jsonl" >/dev/null 2>&1 \
  && assert_events_are_valid_json "$repo/events.jsonl" && ok "P1 交接在事件流里留一条合法的 paused" || no "P1 的 paused 事件缺失或不合法"
printf 'fixed\n' > "$repo/fix.txt"
git -C "$repo" add fix.txt
git -C "$repo" commit -qm "fix scipy"
run_release "$repo" resume >/dev/null
[ "$(run_release "$repo" where)" = "STAGE:doctor RUN:true" ] \
  && assert_all_pending_from_verify_key "$repo" \
  && [ "$(jq -r '.source_commit' "$sf")" = "$(git -C "$repo" rev-parse HEAD)" ] \
  && ok "agent 提交修复并 resume 之后从头重验,绑定新 HEAD" || no "P1 修复后 resume ($(run_release "$repo" where))"

# 守:derive 失败(退出码非零)不能当作修好了。引擎停下并留着现场给驱动 agent。
# 写了一半的文件和非零退出码一起出现:不能把半截产物当成修好了提交上去。
derive_half_done='["sh","-c","mkdir -p scripts/release; printf partial > scripts/release/derived.txt; exit 1"]'
repo="$(new_case p2-derive-fails "$derive_half_done" "$diagnose_empty")"
sf="$(state_file "$repo")"
head_before="$(git -C "$repo" rev-parse HEAD)"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [ "$(git -C "$repo" rev-parse HEAD)" = "$head_before" ] \
  && ok "derive 退非零时停下,半截产物不提交" || no "derive 失败的处理 ($out)"

# 守:derive 在产品仓库根下跑,不管驱动 agent 在哪个子目录里敲的命令;
# 钥匙里的 ${RELEASE_PLUGIN_DIR} 被展开成引擎所在目录。
plugin_dir="$(CDPATH= cd -- "$(dirname -- "$RF")" && pwd -P)"
derive_probe='["sh","-c","mkdir -p scripts/release; printf %s \"$0\" > scripts/release/derived.txt","${RELEASE_PLUGIN_DIR}"]'
repo="$(new_case p2-derive-from-subdir "$derive_probe" "$diagnose_empty")"
fail_stage_p2 "$repo"
(cd "$repo/scripts" && bash "$RF" dispatch --stage verify_key --findings "$FIX/finding.p2.json" >/dev/null)
[ -f "$repo/scripts/release/derived.txt" ] && [ ! -e "$repo/scripts/scripts" ] \
  && ok "derive 在仓库根下执行,即使命令是从子目录敲的" || no "derive 的工作目录不是仓库根"
[ "$(cat "$repo/scripts/release/derived.txt" 2>/dev/null)" = "$plugin_dir" ] \
  && ok "derive 命令里的 RELEASE_PLUGIN_DIR 被展开成引擎所在目录" || no "derive 的 RELEASE_PLUGIN_DIR ($(cat "$repo/scripts/release/derived.txt" 2>/dev/null))"

# 守:RELEASE_STAGE_DIR / RELEASE_LOOP_DIR 只在 stage 与 diagnose 里有意义。derive 里写了就停下说清楚,
# 不能展开成空串——那会变成一条指向文件系统根目录的路径,跑起来才看得见。
for token in RELEASE_STAGE_DIR RELEASE_LOOP_DIR; do
  derive_with_token="$(jq -nc --arg t "\${$token}" '["sh","-c","mkdir -p scripts/release; printf x > scripts/release/derived.txt",$t]')"
  repo="$(new_case "p2-derive-$token" "$derive_with_token" "$diagnose_empty")"
  head_before="$(git -C "$repo" rev-parse HEAD)"
  fail_stage_p2 "$repo"
  err="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json" 2>&1 >/dev/null)" && rc=0 || rc=$?
  if [ "$rc" -ne 0 ] && [[ "$err" == *"$token"* ]] && [ ! -e "$repo/scripts/release/derived.txt" ] \
    && [ "$(git -C "$repo" rev-parse HEAD)" = "$head_before" ]; then
    ok "derive 里用了没有意义的 $token 就停下并点名它"
  else
    no "derive 里的 $token 没被拦住 (rc=$rc err=$err)"
  fi
done

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]

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
  # 本机的提交前门禁是全局 core.hooksPath,会把这里的 seed 提交拦下来。仓库级设置压过
  # 全局,指向一个不存在的目录就等于这个仓库没有钩子——跟 husky 仓库的做法一样。
  git -C "$repo" config core.hooksPath "$repo/.git/no-hooks"
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

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]

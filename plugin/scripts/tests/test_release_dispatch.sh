#!/usr/bin/env bash
# release-flow.sh fix-dispatch:功能分支提交、保护路径闸与 gate 回退。
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"
STATE_SUBDIR="${STATE_SUBDIR:-.claude/multi-model-workflow}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
RF="$SCRIPT_DIR/../release-flow.sh"
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
  printf '%s/%s/release-state.json\n' "$1" "$STATE_SUBDIR"
}

new_case() {
  local name="$1" fix_argv="$2" derive_argv="$3" gate_argv="$4" diagnose_argv="$5"
  local editable_paths="${6:-[\"scripts/release/**\"]}"
  local repo="$TMP/$name"
  mkdir -p "$repo/scripts/release" "$repo/migrations"
  git -C "$repo" init -q
  git -C "$repo" config user.email t@example.test
  git -C "$repo" config user.name release-test
  printf 'seed\n' > "$repo/scripts/release/existing.txt"
  printf 'migration seed\n' > "$repo/migrations/0001.py"
  # 让 `migrations/*.ignored` 被 gitignore,用于验证「gitignored 的受保护文件也必须被 path-gate 拦」
  printf 'migrations/*.ignored\n' > "$repo/.gitignore"
  git -C "$repo" add -A
  git -C "$repo" commit -qm seed
  cp "$FIX/release_protection.fake.json" "$repo/release_protection.json"
  jq --argjson fix "$fix_argv" --argjson derive "$derive_argv" \
    --argjson gate "$gate_argv" --argjson diagnose "$diagnose_argv" \
    --argjson editable "$editable_paths" \
    '.stages=[
        {name:"verify_key",run:["true"]},
        {name:"assemble",run:["true"]},
        {name:"build",run:["true"]}
      ]
     | .fix_executor=$fix
     | .derive=$derive
     | .post_fix_gate=$gate
     | .diagnose=$diagnose
     | .editable_paths=$editable
     | .protection_source="release_protection.json"' \
    "$FIX/manifest.fake.json" > "$repo/manifest.json"
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
  jq -e '.source_commit != "" and .current_stage == "verify_key"
    and all(.stages[]; .status == "pending")' "$sf" >/dev/null
}

assert_no_candidate_status_change() {
  local repo="$1" before="$2"
  [ "$(git -C "$repo" status --porcelain)" = "$before" ]
}

echo "=== test_release_dispatch.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fix_editable='["sh","-c","test -z \"${RELEASE_FIX_STAGING+x}\" || exit 91; mkdir -p scripts/release; printf fixed > scripts/release/patched.txt; printf worker-1 > \"$RELEASE_FIX_WORKER_REF_FILE\""]'
repo="$(new_case p1-editable "$fix_editable" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
base_head="$(git -C "$repo" rev-parse HEAD)"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  *"FIX-COMMITTED:verify_key commit="*) ok "P1 editable 修复提交到功能分支" ;;
  *) no "P1 未提交 ($out)" ;;
esac
repair_sha="$(git -C "$repo" rev-parse HEAD)"
[ "$repair_sha" != "$base_head" ] && [ "$(git -C "$repo" log -1 --format=%s)" = "fix(release): missing_module:scipy" ] && ok "P1 commit message 使用 fingerprint" || no "P1 commit message"
[ "$(jq -r '.source_commit' "$sf")" = "$repair_sha" ] && assert_all_pending_from_verify_key "$repo" && ok "P1 提交后从 verify_key 全量重验" || no "P1 未失效全部 stages"
jq -e --arg sha "$repair_sha" 'any(.attempt_ledger[]; .action_kind == "fix" and .outcome == "applied"
  and .worker_ref == "worker-1" and (.changed_paths | index("scripts/release/patched.txt"))
  and (.artifact_refs | index("git-commit:" + $sha)))' "$sf" >/dev/null && ok "P1 ledger 记录 commit、worker 与改动" || no "P1 ledger"
git -C "$repo" diff --quiet HEAD && ok "P1 后 tracked worktree 干净" || no "P1 后 tracked worktree 脏"

derive_editable='["sh","-c","mkdir -p scripts/release; printf derived > scripts/release/derived.txt"]'
repo="$(new_case p2-editable '["true"]' "$derive_editable" '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
case "$out" in
  *"DERIVED-COMMITTED:verify_key commit="*) ok "P2 derive 提交到功能分支" ;;
  *) no "P2 未提交 ($out)" ;;
esac
[ "$(git -C "$repo" log -1 --format=%s)" = "chore(release): regenerate drift:REQUIRED_RUNTIME_PATHS" ] && ok "P2 commit message 使用 fingerprint" || no "P2 commit message"
assert_all_pending_from_verify_key "$repo" && ok "P2 提交后从 verify_key 全量重验" || no "P2 未失效全部 stages"
jq -e 'any(.attempt_ledger[]; .action_kind == "derive" and .outcome == "applied" and (.artifact_refs | any(startswith("git-commit:"))))' "$sf" >/dev/null && ok "P2 ledger 记录 commit" || no "P2 ledger"

editable_and_p0='["scripts/release/**","migrations/**"]'
fix_tracked_p0='["sh","-c","printf hacked >> migrations/0001.py"]'
repo="$(new_case tracked-p0 "$fix_tracked_p0" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]' "$editable_and_p0")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
before_status="$(git -C "$repo" status --porcelain)"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  *"PATH-GATE-REJECT:verify_key"*"migrations/0001.py"*) ok "tracked 保护路径优先于 editable 拒绝" ;;
  *) no "tracked P0 未拒绝 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$sf")" = "needs-redirection" ] && [ "$(git -C "$repo" rev-list --count HEAD)" = "1" ] && ok "tracked P0 不创建 repair commit" || no "tracked P0 commit/pause"
artifact="$(jq -r '[.attempt_ledger[] | select(.action_kind == "path_gate") | .artifact_refs[]? | select(startswith("file:"))] | last // ""' "$sf")"
[ -n "$artifact" ] && [ -s "${artifact#file:}" ] && grep -q 'migrations/0001.py' "${artifact#file:}" && ok "tracked P0 留 patch artifact" || no "tracked P0 patch"
[ "$(cat "$repo/migrations/0001.py")" = "migration seed" ] && assert_no_candidate_status_change "$repo" "$before_status" && ok "tracked P0 复原且不污染 worktree" || no "tracked P0 未复原"

fix_untracked_p0='["sh","-c","printf new-p0 > migrations/0002.py"]'
repo="$(new_case untracked-p0 "$fix_untracked_p0" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]' "$editable_and_p0")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
before_status="$(git -C "$repo" status --porcelain)"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  *"PATH-GATE-REJECT:verify_key"*"migrations/0002.py"*) ok "untracked 保护路径拒绝" ;;
  *) no "untracked P0 未拒绝 ($out)" ;;
esac
artifact="$(jq -r '[.attempt_ledger[] | select(.action_kind == "path_gate") | .artifact_refs[]? | select(startswith("file:"))] | last // ""' "$sf")"
[ -n "$artifact" ] && grep -q 'migrations/0002.py' "${artifact#file:}" && grep -q 'new-p0' "${artifact#file:}" && ok "untracked P0 patch 含路径与内容" || no "untracked P0 patch 不完整"
[ ! -e "$repo/migrations/0002.py" ] && assert_no_candidate_status_change "$repo" "$before_status" && ok "untracked P0 清理且只保留基线文件" || no "untracked P0 未清理"

derive_p0='["sh","-c","printf derived-p0 > migrations/0003.py"]'
repo="$(new_case p2-untracked-p0 '["true"]' "$derive_p0" '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]' "$editable_and_p0")"
sf="$(state_file "$repo")"
fail_stage_p2 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p2.json")"
case "$out" in
  *"PATH-GATE-REJECT:verify_key"*"migrations/0003.py"*) ok "P2 derive 同样经过未跟踪保护路径闸" ;;
  *) no "P2 untracked P0 未拒绝 ($out)" ;;
esac
[ "$(git -C "$repo" rev-list --count HEAD)" = "1" ] && [ ! -e "$repo/migrations/0003.py" ] && ok "P2 越界不提交且清理新文件" || no "P2 越界残留或提交"

fix_outside='["sh","-c","mkdir -p random; printf out > random/other.txt"]'
repo="$(new_case editable-outside "$fix_outside" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
before_status="$(git -C "$repo" status --porcelain)"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  *"PATH-GATE-REJECT:verify_key"*"random/other.txt"*) ok "editable 外路径拒绝" ;;
  *) no "editable 外未拒绝 ($out)" ;;
esac
[ ! -e "$repo/random/other.txt" ] && assert_no_candidate_status_change "$repo" "$before_status" && ok "editable 外路径清理" || no "editable 外路径未清理"

fix_baseline='["sh","-c","printf changed > baseline-untracked.txt"]'
repo="$(new_case baseline-untracked "$fix_baseline" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
printf 'original\n' > "$repo/baseline-untracked.txt"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [ "$(cat "$repo/baseline-untracked.txt")" = "changed" ] && ok "改写基线 untracked 时停下且保留现场" || no "基线 untracked 处理错误 ($out)"

repo="$(new_case no-change '["true"]' '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [ "$(git -C "$repo" rev-list --count HEAD)" = "1" ] && ok "零改动不伪装为修复" || no "零改动错误 ($out)"

repo="$(new_case preflight-dirty "$fix_editable" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
printf 'unrelated\n' >> "$repo/scripts/release/existing.txt"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
[ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] && [ "$(git -C "$repo" rev-list --count HEAD)" = "1" ] && ok "已有 tracked diff 不混入自动提交" || no "tracked preflight 错误 ($out)"

fix_gate_red='["sh","-c","mkdir -p scripts/release; printf bad > scripts/release/patched.txt"]'
gate_fail_diagnose="$(jq -nc --arg p "$FIX/finding.gatefail.json" '["cat",$p]')"
repo="$(new_case gate-red "$fix_gate_red" '["true"]' '["false"]' "$gate_fail_diagnose")"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
base_head="$(git -C "$repo" rev-parse HEAD)"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  *"FIX-REVERTED:"*) ok "post-fix gate 红撤回 repair commit" ;;
  *) no "gate 红未撤回 ($out)" ;;
esac
[ "$(git -C "$repo" rev-list --count HEAD)" = "3" ] && [ ! -e "$repo/scripts/release/patched.txt" ] && [ "$(jq -r '.source_commit' "$sf")" = "$(git -C "$repo" rev-parse HEAD)" ] && ok "gate 红生成 revert 且修复内容已撤回" || no "gate 红回退状态错误"
[ "$(run_release "$repo" exit-check)" != "DONE" ] && jq -e 'any(.attempt_ledger[]; .action_kind == "post_fix_gate" and .outcome == "fail")' "$sf" >/dev/null && jq -e 'any(.attempt_ledger[]; .root_cause_fingerprint == "arch:shared_reverse_import")' "$sf" >/dev/null && ok "gate 红重新诊断且不宣告 DONE" || no "gate 红诊断/DONE 错误"

repo="$(new_case direct-p0 '["true"]' '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p0.json")"
case "$out" in
  P0:verify_key*) ok "P0 direct dispatch 保持人工 PAUSE" ;;
  *) no "P0 dispatch 回归 ($out)" ;;
esac
[ "$(jq -r '.pause.reason' "$sf")" = "needs-redirection" ] && ok "P0 direct dispatch 写 needs-redirection" || no "P0 pause 回归"
[ -s "$repo/events.jsonl" ] && while IFS= read -r event; do
  printf '%s\n' "$event" | UV_CACHE_DIR="${UV_CACHE_DIR:-/private/tmp/mmw-uv-cache}" uv run --quiet "$SCRIPT_DIR/../release_contracts.py" validate-event -
done < "$repo/events.jsonl" && ok "P0 event sink 仍产出合法 Event 合同" || no "P0 event sink/Event 合同回归"

repo="$(new_case fingerprint-cap '["true"]' '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
fail_stage_p1 "$repo"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  CIRCUIT-BREAK:fingerprint=missing_module:scipy*) ok "同 fingerprint 达阈值继续熔断" ;;
  *) no "fingerprint 熔断回归 ($out)" ;;
esac

repo="$(new_case attempt-cap '["true"]' '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
tmp_state="$(mktemp)"
jq '.budget.max_attempts=1' "$sf" > "$tmp_state" && mv "$tmp_state" "$sf"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  BUDGET-EXCEEDED:attempts=1*) ok "attempt 预算继续熔断" ;;
  *) no "attempt 预算回归 ($out)" ;;
esac

repo="$(new_case wall-clock-cap '["true"]' '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
tmp_state="$(mktemp)"
jq '.budget.started_at="2000-01-01T00:00:00Z"' "$sf" > "$tmp_state" && mv "$tmp_state" "$sf"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  BUDGET-EXCEEDED:wallclock=*) ok "墙钟预算继续熔断" ;;
  *) no "墙钟预算回归 ($out)" ;;
esac

# P0 安全回归:gitignored 的受保护文件(如自愈修复新建 .env/secret)不能绕过 path-gate。
# 一般候选集用 --exclude-standard 排除 gitignored,曾致 gitignored 的受保护路径不被 gate 看到。
fix_gitignored='["sh","-c","printf leak > migrations/oops.ignored"]'
repo="$(new_case gitignored-protected "$fix_gitignored" '["true"]' '["true"]' '["sh","-c","echo {\\\"findings\\\":[]}"]')"
sf="$(state_file "$repo")"
fail_stage_p1 "$repo"
before_status="$(git -C "$repo" status --porcelain)"
out="$(run_release "$repo" dispatch --stage verify_key --findings "$FIX/finding.p1.json")"
case "$out" in
  *"PATH-GATE-REJECT:verify_key"*"migrations/oops.ignored"*) ok "gitignored 受保护文件被拦(不漏 secret)" ;;
  *) no "gitignored 受保护文件绕过 path-gate ($out)" ;;
esac
artifact="$(jq -r '[.attempt_ledger[] | select(.action_kind == "path_gate") | .artifact_refs[]? | select(startswith("file:"))] | last // ""' "$sf")"
[ -n "$artifact" ] && grep -q 'migrations/oops.ignored' "${artifact#file:}" && grep -q 'leak' "${artifact#file:}" && ok "gitignored 受保护 patch 含路径与内容" || no "gitignored 受保护 patch 不完整"
[ ! -e "$repo/migrations/oops.ignored" ] && assert_no_candidate_status_change "$repo" "$before_status" && ok "gitignored 受保护清理且不污染 worktree" || no "gitignored 受保护未清理"

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]

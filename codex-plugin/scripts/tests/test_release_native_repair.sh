#!/usr/bin/env bash
# Codex release P1：引擎准备边界，GPT 子代理改工作树，引擎验收并提交。
set -euo pipefail

STATE_SUBDIR="${STATE_SUBDIR:-.codex/multi-model-workflow}"
SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
RF="$SCRIPT_DIR/../release-flow.sh"
FIX="$SCRIPT_DIR/fixtures/release-flow"

pass=0
fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

echo "=== test_release_native_repair.sh ==="
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
repo="$TMP/repo"
mkdir -p "$repo/scripts/release" "$repo/migrations"
git -C "$repo" init -q
git -C "$repo" config user.email t@example.test
git -C "$repo" config user.name release-test
printf 'seed\n' > "$repo/scripts/release/existing.txt"
printf 'migration\n' > "$repo/migrations/0001.py"
cp "$FIX/release_protection.fake.json" "$repo/release_protection.json"
git -C "$repo" add -A
git -C "$repo" commit -qm seed

external_fix="$repo/external-fix.sh"
cat > "$external_fix" <<'SH'
#!/usr/bin/env bash
printf 'external-called\n' > "${EXTERNAL_MARKER:?}"
SH
chmod +x "$external_fix"
jq --arg external "$external_fix" '
  .stages=[{name:"verify_key",run:["true"]}]
  | .fix_executor=[$external]
  | .derive=["true"]
  | .post_fix_gate=["true"]
  | .diagnose=["sh","-c","echo {\\\"findings\\\":[]}"]
  | .editable_paths=["scripts/release/**"]
  | .protection_source="release_protection.json"
' "$FIX/manifest.fake.json" > "$repo/manifest.json"

(
  cd "$repo"
  bash "$RF" init --manifest manifest.json >/dev/null
  bash "$RF" stage fail --stage verify_key --findings "$FIX/finding.p1.json" >/dev/null
)

out="$(cd "$repo" && EXTERNAL_MARKER="$TMP/external-called.txt" bash "$RF" dispatch --stage verify_key)"
case "$out" in
  *"NATIVE-REPAIR-READY:verify_key"*"spawn_agent(fork_turns=\"none\")"*)
    ok "P1 dispatch 要求当前 Codex task 派原生 GPT 子代理"
    ;;
  *) no "P1 dispatch 没有给出原生派发动作 ($out)" ;;
esac

[ ! -e "$TMP/external-called.txt" ] \
  && ok "Codex P1 没有执行 manifest.fix_executor" \
  || no "Codex P1 仍调用了外部修复模型"

sf="$repo/$STATE_SUBDIR/release-state.json"
prompt="$(jq -r '.native_repair.prompt_path // ""' "$sf")"
if jq -e '.native_repair.stage == "verify_key"
  and .native_repair.fingerprint == "missing_module:scipy"
  and (.native_repair.protection_matchers | index("migrations/**"))
  and (.native_repair.editable_matchers | index("scripts/release/**"))' "$sf" >/dev/null \
  && [ -s "$prompt" ] \
  && grep -Fq "$repo" "$prompt" \
  && grep -Fq '不要 commit' "$prompt"; then
  ok "引擎持久化恢复所需边界并生成完整修复 brief"
else
  no "native repair state 或 prompt 不完整"
fi

where="$(cd "$repo" && bash "$RF" where)"
case "$where" in
  NATIVE-REPAIR-PENDING:verify_key*) ok "where 可在压缩或重开后恢复待派修复" ;;
  *) no "where 没有报告待派原生修复 ($where)" ;;
esac

if (cd "$repo" && bash "$RF" dispatch --stage verify_key >/dev/null 2>&1); then
  no "native repair pending 时仍允许重复 dispatch"
else
  ok "native repair pending 时拒绝重复 dispatch"
fi
if (cd "$repo" && bash "$RF" resume >/dev/null 2>&1); then
  no "native repair pending 时仍允许 resume"
else
  ok "native repair pending 时拒绝 resume 绕过验收"
fi
if (cd "$repo" && bash "$RF" stage run --stage verify_key >/dev/null 2>&1) \
  || (cd "$repo" && bash "$RF" round next >/dev/null 2>&1); then
  no "native repair pending 时仍允许 stage/round 推进"
else
  ok "native repair pending 时冻结 stage/round"
fi
[ "$(cd "$repo" && bash "$RF" exit-check)" = "NOT-DONE:native-repair=verify_key" ] \
  && ok "native repair pending 时 exit-check 不宣告完成" \
  || no "exit-check 绕过待验收修复"

printf 'fixed\n' > "$repo/scripts/release/patched.txt"
where="$(cd "$repo" && bash "$RF" where)"
case "$where" in
  NATIVE-REPAIR-VERIFY:verify_key*) ok "where 发现候选改动后指向 repair verify" ;;
  *) no "where 没有报告待验收改动 ($where)" ;;
esac
verify="$(cd "$repo" && bash "$RF" repair verify --stage verify_key --worker-ref codex-test-worker)"
case "$verify" in
  *"FIX-COMMITTED:verify_key commit="*"POST-FIX-GATE-PASS:verify_key"*)
    ok "子代理改动经过路径闸、提交和 post-fix gate"
    ;;
  *) no "原生修复验收未闭环 ($verify)" ;;
esac

repair_sha="$(git -C "$repo" rev-parse HEAD)"
if [ "$(git -C "$repo" log -1 --format=%s)" = "fix(release): missing_module:scipy" ] \
  && jq -e --arg sha "$repair_sha" '
    .native_repair == null
    and .source_commit == $sha
    and .round == 2
    and .budget.fix_rounds == 1
    and any(.attempt_ledger[];
      .action_kind == "fix"
      and .outcome == "applied"
      and .worker_ref == "codex-test-worker"
      and (.changed_paths | index("scripts/release/patched.txt")))
  ' "$sf" >/dev/null; then
  ok "提交、预算、worker 回执和断点状态一致"
else
  no "原生修复 ledger 或状态不一致"
fi

(
  cd "$repo"
  bash "$RF" close >/dev/null
  bash "$RF" init --manifest manifest.json >/dev/null
  bash "$RF" stage fail --stage verify_key --findings "$FIX/finding.p1.json" >/dev/null
  bash "$RF" dispatch --stage verify_key >/dev/null
)
printf 'other\n' > "$repo/other.txt"
git -C "$repo" add other.txt
git -C "$repo" commit -qm other-head
changed_head="$(git -C "$repo" rev-parse HEAD)"
verify="$(cd "$repo" && bash "$RF" repair verify --stage verify_key)"
if [ "$changed_head" = "$(git -C "$repo" rev-parse HEAD)" ] \
  && [ "$(jq -r '.pause.reason' "$sf")" = "needs-context" ] \
  && [ "$(jq -r '.native_repair == null' "$sf")" = "true" ]; then
  ok "子代理擅自提交或并发 HEAD 变化时保留现场并暂停"
else
  no "HEAD 变化被混入或被静默复原 ($verify)"
fi

echo "=== $pass PASS / $fail FAIL ==="
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# package-phase 的公开命令面：真实 Git diff + scope + S1 adapter 合同。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE="$SCRIPT_DIR/../package-phase.sh"
MMW="$SCRIPT_DIR/../mmw.sh"
FIXTURES="$SCRIPT_DIR/fixtures/package-phase"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass + 1)); }
no() { echo "  FAIL: $1"; fail=$((fail + 1)); }

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
# 测试的 uv cache 必须可写，不能依赖开发机用户目录的权限或既有缓存。
export UV_CACHE_DIR="${UV_CACHE_DIR:-$TMP/uv-cache}"
CASE=""; OUT=""; ERR=""; RESULT=""; ERROR=""; RC=0

new_case() {
  local name="$1" seeded_path="${2:-}"
  CASE="$TMP/$name"
  mkdir -p "$CASE"
  git -C "$CASE" init -q
  git -C "$CASE" config user.email t@t
  git -C "$CASE" config user.name t
  printf 'seed\n' > "$CASE/seed.txt"
  if [ -n "$seeded_path" ]; then
    mkdir -p "$CASE/$(dirname "$seeded_path")"
    printf 'old\n' > "$CASE/$seeded_path"
  fi
  git -C "$CASE" add -A
  git -C "$CASE" commit -qm seed
  local base
  base="$(git -C "$CASE" rev-parse HEAD)"
  mkdir -p "$CASE/.claude/multi-model-workflow"
  jq -n --arg base "$base" \
    '{schema_version:"1",phase:"package",base_commit:$base}' \
    > "$CASE/.claude/multi-model-workflow/task.json"
  cp -R "$FIXTURES" "$CASE/fixtures"
  OUT="$CASE/out"; ERR="$CASE/err"
}

commit_path() {
  local path="$1"
  mkdir -p "$CASE/$(dirname "$path")"
  printf 'x\n' > "$CASE/$path"
  git -C "$CASE" add -- "$path"
  git -C "$CASE" commit -qm "change $path"
}

delete_path() {
  local path="$1"
  rm "$CASE/$path"
  git -C "$CASE" add -- "$path"
  git -C "$CASE" commit -qm "delete $path"
}

resolve() {
  (cd "$CASE" && bash "$PACKAGE" resolve --scope fixtures/agentflow.release-package-scope.json)
}

run_resolve() {
  local scope="$1"
  shift
  RC=0
  (cd "$CASE" && bash "$PACKAGE" resolve --scope "$scope" "$@") >"$OUT" 2>"$ERR" || RC=$?
  RESULT="$(cat "$OUT")"
  ERROR="$(cat "$ERR")"
}

run_package() {
  RC=0
  (cd "$CASE" && bash "$PACKAGE" "$@") >"$OUT" 2>"$ERR" || RC=$?
  RESULT="$(cat "$OUT")"
  FIRST="$(head -n1 "$OUT")"
  ERROR="$(cat "$ERR")"
}

package_state() {
  printf '%s/.claude/multi-model-workflow/package-state.json' "$CASE"
}

release_done() {
  local product="$1" manifest
  manifest="$(jq -r --arg p "$product" '.targets[] | select(.product == $p) | .manifest' "$(package_state)")"
  (cd "$CASE" && bash "$MMW" release init --manifest "$CASE/$manifest" >/dev/null)
  (cd "$CASE" && bash "$MMW" release stage done --stage build >/dev/null)
}

targets() {
  jq -c '[.targets[].product]' <<<"$RESULT"
}

assert_targets() {
  local label="$1" expected="$2" path="$3"
  new_case "$label"
  commit_path "$path"
  run_resolve fixtures/agentflow.release-package-scope.json
  if [ "$RC" -eq 0 ] && [ "$(targets)" = "$expected" ]; then
    ok "$label → $expected"
  else
    no "$label → $expected (rc=$RC targets=$(targets 2>/dev/null || true) err=$ERROR)"
  fi
}

assert_empty() {
  local label="$1" path="$2"
  new_case "$label"
  commit_path "$path"
  run_resolve fixtures/agentflow.release-package-scope.json
  if [ "$RC" -eq 2 ] && [ "$(targets)" = '[]' ]; then
    ok "$label → 空目标 / exit 2"
  else
    no "$label → 空目标 / exit 2 (rc=$RC targets=$(targets 2>/dev/null || true) err=$ERROR)"
  fi
}

assert_error() {
  local label="$1" expected="$2"
  shift 2
  new_case "$label"
  "$@"
  run_resolve fixtures/agentflow.release-package-scope.json
  if [ "$RC" -eq 1 ] && grep -Fqx "$expected" "$ERR"; then
    ok "$label → fail-loud"
  else
    no "$label → fail-loud (rc=$RC err=$ERROR)"
  fi
}

replace_scope() {
  local filter="$1"
  jq "$filter" "$CASE/fixtures/agentflow.release-package-scope.json" > "$CASE/scope"
  mv "$CASE/scope" "$CASE/fixtures/agentflow.release-package-scope.json"
}

make_malformed_scope() { replace_scope '.unexpected=true'; }
make_duplicate_product() { replace_scope '.products[1].product=.products[0].product'; }
make_duplicate_manifest() { replace_scope '.products[1].manifest=.products[0].manifest'; }
make_absolute_manifest() { replace_scope '.products[0].manifest="/absolute.json"'; }
make_parent_path() { replace_scope '.products[0].paths=["../outside/**"]'; }
make_absent_adapter() { replace_scope '.products[0].manifest="fixtures/adapters/missing.release-adapter.json"'; }
make_invalid_adapter() {
  printf '{}\n' > "$CASE/fixtures/adapters/invalid.release-adapter.json"
  replace_scope '.products[0].manifest="fixtures/adapters/invalid.release-adapter.json"'
}
make_adapter_product_mismatch() {
  jq '.product="not-duck"' "$CASE/fixtures/adapters/duck.release-adapter.json" \
    > "$CASE/fixtures/adapters/mismatch.release-adapter.json"
  replace_scope '.products[0].manifest="fixtures/adapters/mismatch.release-adapter.json"'
}

echo "=== test_package_phase.sh ==="

# 产品目录、资产与共享出包面。每个 case 都是从同一 seed 生成的真实提交。
assert_targets duck-source '["duck"]' src/local_agent/app.py
assert_targets parrot-source '["parrot"]' src/parrot_dubbing/app.py
assert_targets hedgehog-source '["hedgehog"]' src/hedgehog/app.py
assert_targets parrot-assets '["parrot"]' src/parrot_dubbing/assets/fonts/NotoSans-Bold.ttf
assert_targets hedgehog-assets '["hedgehog"]' src/hedgehog/assets/bgm/bgm_manifest.json

new_case duck-deletion src/local_agent/obsolete_runtime.py
delete_path src/local_agent/obsolete_runtime.py
run_resolve fixtures/agentflow.release-package-scope.json
if [ "$RC" -eq 0 ] && [ "$(targets)" = '["duck"]' ]; then
  ok "删除产品代码仍出 duck 包"
else
  no "删除产品代码仍出 duck 包 (rc=$RC targets=$(targets 2>/dev/null || true) err=$ERROR)"
fi

for path in src/shared/ports.py scripts/release/build_doctor.py scripts/agentflow-build pyproject.toml uv.lock assets/brand/parrot/parrot-dubbing-app-icon.svg; do
  assert_targets "shared-$(echo "$path" | tr '/.' '--')" '["duck","parrot","hedgehog"]' "$path"
done

for path in docs/plans/example.md tests/local_agent/test_example.py src/gateway/api.py src/collection/api.py migrations/gateway/versions/x.py deploy/systemd/x.service .github/workflows/x.yml; do
  assert_empty "ignored-$(echo "$path" | tr '/.' '--')" "$path"
done

# 回归:真实批次改动上百个路径。bash 3.2 在外层解析循环(process substitution 重定向)内部
# 再套 process substitution 填 product paths,会累积文件描述符,跑够多轮后内层读空——product
# 匹配拿到空 glob 列表,靠后的产品源(src/<产品>/…)被误判「未分类」而 fail-loud。单路径用例
# 永远不触发;这里把上百个在前的 ignored 路径顶在前面,把一个产品源路径排到最后。
new_case many-paths-late-product
mkdir -p "$CASE/docs/plans"
for n in $(seq -w 1 200); do printf 'x\n' > "$CASE/docs/plans/filler-$n.md"; done
mkdir -p "$CASE/src/hedgehog"
printf 'x\n' > "$CASE/src/hedgehog/zzz_late_source.py"
git -C "$CASE" add -- docs/plans src/hedgehog
git -C "$CASE" commit -qm "batch of many paths with a late product source"
run_resolve fixtures/agentflow.release-package-scope.json
if [ "$RC" -eq 0 ] && [ "$(targets)" = '["hedgehog"]' ]; then
  ok "上百路径下靠后的产品源仍归类(bash 3.2 process-sub fd 累积回归)"
else
  no "上百路径下靠后的产品源仍归类 (rc=$RC targets=$(targets 2>/dev/null || true) err=$ERROR)"
fi

new_case unknown-path
commit_path scripts/new_surface.py
run_resolve fixtures/agentflow.release-package-scope.json
if [ "$RC" -eq 1 ] && grep -Fqx 'ERROR: 未分类改动路径: scripts/new_surface.py' "$ERR"; then
  ok "未知路径拒绝推进"
else
  no "未知路径拒绝推进 (rc=$RC err=$ERROR)"
fi

new_case missing-scope
run_resolve fixtures/missing.release-package-scope.json
if [ "$RC" -eq 1 ] && grep -Fqx 'ERROR: scope 文件不存在: fixtures/missing.release-package-scope.json' "$ERR"; then
  ok "缺 scope 拒绝"
else
  no "缺 scope 拒绝 (rc=$RC err=$ERROR)"
fi

assert_error malformed-scope 'ERROR: scope 形状不合规: fixtures/agentflow.release-package-scope.json' make_malformed_scope
assert_error duplicate-product 'ERROR: scope 形状不合规: fixtures/agentflow.release-package-scope.json' make_duplicate_product
assert_error duplicate-manifest 'ERROR: scope 形状不合规: fixtures/agentflow.release-package-scope.json' make_duplicate_manifest
assert_error absolute-manifest 'ERROR: scope 形状不合规: fixtures/agentflow.release-package-scope.json' make_absolute_manifest
assert_error parent-path 'ERROR: scope 形状不合规: fixtures/agentflow.release-package-scope.json' make_parent_path
assert_error absent-adapter 'ERROR: scope 指向的 adapter 不存在: fixtures/adapters/missing.release-adapter.json' make_absent_adapter
assert_error invalid-adapter 'ERROR: scope 指向的 adapter 不合规: fixtures/adapters/invalid.release-adapter.json' make_invalid_adapter
assert_error adapter-product-mismatch 'ERROR: scope product 与 adapter product 不一致: fixtures/adapters/mismatch.release-adapter.json' make_adapter_product_mismatch

new_case generic-products
commit_path shared/runtime.txt
run_resolve fixtures/generic.release-package-scope.json
if [ "$RC" -eq 0 ] && [ "$(targets)" = '["alpha","beta"]' ]; then
  ok "非 AgentFlow 产品按 scope 声明顺序解析"
else
  no "非 AgentFlow 产品按 scope 声明顺序解析 (rc=$RC targets=$(targets 2>/dev/null || true) err=$ERROR)"
fi

if find "$TMP" -name package-state.json -print -quit | grep -q .; then
  no "resolve 不应写 package-state"
else
  ok "resolve 只读，不写 package-state"
fi

# package 生命周期：目标快照、两次人工门与每把钥匙独立的 S1 DONE 证明。
new_case package-empty
run_package init --scope fixtures/generic.release-package-scope.json
if [ "$RC" -eq 0 ] && [ "$(jq -c '.targets' "$(package_state)")" = '[]' ]; then
  ok "init 固化空目标 package state"
else
  no "init 固化空目标 package state (rc=$RC err=$ERROR)"
fi
run_package where
if [ "$RC" -eq 0 ] && [ "$FIRST" = 'NO-PACKAGE' ]; then ok "空目标 where=NO-PACKAGE"; else no "空目标 where (rc=$RC out=$RESULT err=$ERROR)"; fi
run_package exit-check
if [ "$RC" -eq 0 ] && [ "$RESULT" = 'DONE' ]; then ok "空目标 exit-check=DONE"; else no "空目标 exit-check (rc=$RC out=$RESULT err=$ERROR)"; fi
run_package init --scope fixtures/generic.release-package-scope.json
if [ "$RC" -eq 0 ]; then ok "同一空目标 init 幂等"; else no "同一空目标 init 幂等 (rc=$RC err=$ERROR)"; fi

new_case package-gates
commit_path src/local_agent/app.py
commit_path src/parrot_dubbing/app.py
run_package init --scope fixtures/agentflow.release-package-scope.json
if [ "$RC" -eq 0 ] && [ "$(jq -c '[.targets[].product]' "$(package_state)")" = '["duck","parrot"]' ]; then
  ok "init 一次固化有序 release 目标"
else
  no "init 一次固化有序 release 目标 (rc=$RC err=$ERROR)"
fi
run_package where
if [ "$RC" -eq 0 ] && [ "$FIRST" = 'PAUSED-HUMAN:development-mode-test' ]; then ok "未确认开发模式时停位"; else no "开发模式停位 (rc=$RC out=$RESULT err=$ERROR)"; fi
run_package confirm --gate installed-test --by owner
if [ "$RC" -ne 0 ]; then ok "未完成 release 时拒绝安装后确认"; else no "未完成 release 时应拒绝安装后确认"; fi
run_package record-release --product duck
if [ "$RC" -ne 0 ]; then ok "无 matching S1 DONE 时拒绝记录 release"; else no "无 S1 DONE 时应拒绝记录"; fi
release_done duck
run_package record-release --product duck
if [ "$RC" -ne 0 ]; then ok "开发模式未确认时即使 S1 DONE 也拒绝记录"; else no "开发模式未确认时应拒绝记录"; fi
(cd "$CASE" && bash "$MMW" release close >/dev/null)
run_package confirm --gate development-mode-test --by afk-policy
if [ "$RC" -ne 0 ]; then ok "AFK 不能代填开发模式确认"; else no "AFK 不应代填开发模式确认"; fi
run_package confirm --gate development-mode-test --by owner
if [ "$RC" -eq 0 ]; then ok "具名开发模式确认落盘"; else no "开发模式确认 (rc=$RC err=$ERROR)"; fi
run_package where
if [ "$RC" -eq 0 ] && [ "$FIRST" = 'RELEASE product=duck manifest=fixtures/adapters/duck.release-adapter.json' ]; then ok "确认后只要求第一个 release"; else no "确认后 release 指引 (rc=$RC out=$RESULT err=$ERROR)"; fi
if grep -q 'next=.*release init' "$OUT" && grep -q 'drive-loop.md' "$OUT" && grep -q 'record-release --product duck' "$OUT"; then ok "RELEASE 状态自带 next 指路(init/drive-loop/record-release)"; else no "RELEASE next 指路 (out=$RESULT)"; fi
VERB_OUT="$( (cd "$CASE" && bash "$MMW" package where) 2>/dev/null )"
VERB_FIRST="${VERB_OUT%%
*}"
if [ "$VERB_FIRST" = 'RELEASE product=duck manifest=fixtures/adapters/duck.release-adapter.json' ]; then ok "mmw package 动词直达 package-phase"; else no "mmw package 动词 (out=$VERB_FIRST)"; fi
release_done parrot
run_package record-release --product duck
if [ "$RC" -ne 0 ]; then ok "S1 product 不匹配时拒绝记录"; else no "S1 product 不匹配应拒绝"; fi
(cd "$CASE" && bash "$MMW" release close >/dev/null)
release_done duck
run_package record-release --product duck
if [ "$RC" -eq 0 ] && [ "$(jq -r '.targets[] | select(.product == "duck") | .release_commit' "$(package_state)")" = "$(git -C "$CASE" rev-parse HEAD)" ]; then
  ok "matching S1 DONE 记录当前功能分支提交"
else
  no "matching S1 DONE 记录 (rc=$RC err=$ERROR)"
fi
(cd "$CASE" && bash "$MMW" release close >/dev/null)
run_package where
if [ "$RC" -eq 0 ] && [ "$FIRST" = 'RELEASE product=parrot manifest=fixtures/adapters/parrot.release-adapter.json' ]; then ok "一个产品完成不越过另一个"; else no "第二个产品仍 pending (rc=$RC out=$RESULT err=$ERROR)"; fi
release_done parrot
run_package record-release --product parrot
(cd "$CASE" && bash "$MMW" release close >/dev/null)
run_package where
if [ "$RC" -eq 0 ] && [ "$FIRST" = 'PAUSED-HUMAN:installed-test' ]; then ok "所有 release 后停在安装后测试"; else no "安装后测试停位 (rc=$RC out=$RESULT err=$ERROR)"; fi
run_package confirm --gate installed-test --by owner
run_package exit-check
if [ "$RC" -eq 0 ] && [ "$RESULT" = 'DONE' ]; then ok "两次具名确认和所有 release 后 DONE"; else no "最终 DONE (rc=$RC out=$RESULT err=$ERROR)"; fi
commit_path src/hedgehog/app.py
run_package init --scope fixtures/agentflow.release-package-scope.json
if [ "$RC" -ne 0 ]; then ok "运行中 snapshot 不接受变化后的目标列表"; else no "运行中 snapshot 应拒绝变化"; fi
run_package close
if [ "$RC" -eq 0 ] && [ ! -e "$(package_state)" ]; then ok "close 只移除本 worktree package state"; else no "close package state (rc=$RC err=$ERROR)"; fi
run_package init --scope fixtures/agentflow.release-package-scope.json
if [ "$RC" -eq 0 ] && [ "$(jq -r .initial_head_commit "$(package_state)")" = "$(git -C "$CASE" rev-parse HEAD)" ]; then
  ok "close 后 init 以新 HEAD 建立新快照"
else
  no "close 后 init 新快照 (rc=$RC err=$ERROR)"
fi

# 多产品交付一致性:后记录的产品若经自愈提交推进了 HEAD,早前产品的包已不是最终代码,必须
# 重置回待出包由驱动循环重出;混着不同 commit 的包绝不能 DONE。
new_case package-multi-product-provenance
commit_path src/local_agent/app.py
commit_path src/parrot_dubbing/app.py
run_package init --scope fixtures/agentflow.release-package-scope.json
run_package confirm --gate development-mode-test --by owner
release_done duck
run_package record-release --product duck
if [ "$RC" -eq 0 ]; then ok "duck 在提交 A 记录 release"; else no "duck 记录 release (rc=$RC err=$ERROR)"; fi
(cd "$CASE" && bash "$MMW" release close >/dev/null)
commit_path src/parrot_dubbing/self_heal_fix.py
release_done parrot
run_package record-release --product parrot
if [ "$RC" -eq 0 ] && printf '%s\n' "$RESULT" | grep -q 'RESET-STALE:duck'; then
  ok "parrot 在新 HEAD 记录时把旧提交的 duck 重置回待出包"
else
  no "旧提交的 duck 未被重置 (rc=$RC out=$RESULT err=$ERROR)"
fi
[ "$(jq -r '.targets[] | select(.product == "duck") | .release_commit' "$(package_state)")" = "null" ] && ok "被重置的 duck release_commit 清空" || no "duck 仍绑旧 commit"
(cd "$CASE" && bash "$MMW" release close >/dev/null)
run_package where
if [ "$RC" -eq 0 ] && [ "$FIRST" = 'RELEASE product=duck manifest=fixtures/adapters/duck.release-adapter.json' ]; then ok "重置后 where 要求重出 duck"; else no "重置后未要求重出 duck (rc=$RC out=$RESULT err=$ERROR)"; fi
run_package exit-check
if [ "$RC" -ne 0 ] && [ "$RESULT" = 'NOT-DONE:release:duck' ]; then ok "重置后 exit-check 不 DONE"; else no "重置后 exit-check (rc=$RC out=$RESULT err=$ERROR)"; fi
# 防御第二道:状态文件被外部写坏成混 commit(第一道重置被绕过)时,exit-check 仍绝不 DONE。
jq '.targets |= map(if .product == "duck" then .release_commit = "deadbeef" else . end) | .installed_test = {by:"owner"}' "$(package_state)" > "$(package_state).tmp" && mv "$(package_state).tmp" "$(package_state)"
run_package exit-check
if [ "$RC" -ne 0 ] && [ "$RESULT" = 'NOT-DONE:release-commit-mismatch' ]; then ok "混 commit 状态被 exit-check 第二道防御拦截"; else no "混 commit 未被拦 (rc=$RC out=$RESULT err=$ERROR)"; fi

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# package-phase 的公开命令面：真实 Git diff + scope + S1 adapter 合同。
set -euo pipefail
export MMW_HOST="${MMW_HOST:-claude}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE="$SCRIPT_DIR/../package-phase.sh"
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

echo ""
echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

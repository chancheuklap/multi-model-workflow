#!/usr/bin/env bash
# package-phase.sh —— develop 的产品影响解析与 package 运行态入口。
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

repo_top() {
  git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"
}

task_manifest() {
  local top sd file
  top="$(repo_top)"
  sd="$MMW_STATE_SUBDIR"
  file="$top/$sd/task.json"
  [ -f "$file" ] || die "无 task.json；未给 --base/--head 时必须在受管任务内"
  printf '%s\n' "$file"
}

package_state_path() {
  local top sd
  top="$(repo_top)"
  sd="$MMW_STATE_SUBDIR"
  printf '%s\n' "$top/$sd/package-state.json"
}

need_package_state() {
  local file
  file="$(package_state_path)"
  [ -f "$file" ] || die "无 package-state(先 package init)"
  jq -e . "$file" >/dev/null 2>&1 || die "package-state 损坏，拒绝继续"
  printf '%s\n' "$file"
}

write_package_state() {
  local file="$1" dir tmp
  dir="$(dirname "$file")"
  mkdir -p "$dir"
  tmp="$(mktemp "$dir/.package-state.XXXXXX")"
  cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    die "拒绝写入空/非法 JSON 到 $file;原 package-state 保留"
  fi
  mv "$tmp" "$file"
}

matches_any() {
  local path="$1" glob
  shift
  for glob in "$@"; do
    [[ "$path" == $glob ]] && return 0
  done
  return 1
}

validate_scope() {
  local top="$1" scope_rel="$2" scope_abs canon index product manifest manifest_abs adapter
  scope_rel="${scope_rel#./}"
  scope_abs="$top/$scope_rel"
  [ -f "$scope_abs" ] || die "scope 文件不存在: $scope_rel"
  canon="$(jq -ce '
    def nonempty: type == "string" and length > 0;
    def relative: nonempty and (startswith("/") | not) and (contains("..") | not);
    def paths: type == "array" and all(.[]; relative);
    def valid:
      (type == "object") and
      ((keys | sort) == ["all_products_paths", "ignored_paths", "products", "schema_version"]) and
      (.schema_version == "1") and (.all_products_paths | paths) and (.ignored_paths | paths) and
      (.products | type == "array" and length > 0) and
      (all(.products[]; type == "object" and
        ((keys | sort) == ["manifest", "paths", "product"]) and
        (.product | nonempty) and (.manifest | relative) and (.paths | paths))) and
      ((.products | map(.product) | unique | length) == (.products | length)) and
      ((.products | map(.manifest) | unique | length) == (.products | length));
    select(valid)
  ' "$scope_abs")" || die "scope 形状不合规: $scope_rel"
  index=0
  while [ "$index" -lt "$(jq -r '.products | length' <<<"$canon")" ]; do
    product="$(jq -r --argjson i "$index" '.products[$i].product' <<<"$canon")"
    manifest="$(jq -r --argjson i "$index" '.products[$i].manifest' <<<"$canon")"
    manifest_abs="$top/$manifest"
    [ -f "$manifest_abs" ] || die "scope 指向的 adapter 不存在: $manifest"
    adapter="$(uv run --quiet "$SCRIPT_DIR/release_contracts.py" validate-manifest "$manifest_abs")" \
      || die "scope 指向的 adapter 不合规: $manifest"
    [ "$(jq -r .product <<<"$adapter")" = "$product" ] \
      || die "scope product 与 adapter product 不一致: $manifest"
    index=$((index + 1))
  done
  printf '%s\n' "$canon"
}

cmd_resolve() {
  local scope="" base="" head="" top manifest scope_json changed_json classified="[]" path indices targets result
  local product_count index
  local -a all_globs product_globs ignored_globs
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --scope) scope="$2"; shift 2 ;;
      --base) base="$2"; shift 2 ;;
      --head) head="$2"; shift 2 ;;
      *) die "resolve 参数非法: $1" ;;
    esac
  done
  [ -n "$scope" ] || die "resolve 必须给 --scope"
  top="$(repo_top)"
  if [ -z "$base" ] || [ -z "$head" ]; then
    manifest="$(task_manifest)"
    [ -n "$base" ] || base="$(jq -r .base_commit "$manifest")"
    [ -n "$head" ] || head="$(git rev-parse HEAD)"
  fi
  git rev-parse --verify "$base^{commit}" >/dev/null 2>&1 || die "base revision 不存在: $base"
  git rev-parse --verify "$head^{commit}" >/dev/null 2>&1 || die "head revision 不存在: $head"
  scope_json="$(validate_scope "$top" "$scope")"
  # core.quotepath=false:中文/特殊字符文件名默认被 git 引号转义成 "\345..." 形式,
  # 转义串永远匹配不上任何 scope glob,会把无关素材文件误判成「未分类改动」卡死解析。
  changed_json="$(git -c core.quotepath=false diff --name-only --diff-filter=ACMRTD "$base..$head" | LC_ALL=C sort -u | jq -Rsc 'split("\n") | map(select(length > 0))')"
  all_globs=()
  while IFS= read -r glob; do all_globs+=("$glob"); done < <(jq -r '.all_products_paths[]' <<<"$scope_json")
  # ignored 桶在循环外一次性读好:bash 3.2 在「外层 while 重定向 + || 复合组」内不执行
  # process substitution,曾致 ignored 恒为空、全部改动被误判「未分类」。
  ignored_globs=()
  while IFS= read -r glob; do ignored_globs+=("$glob"); done < <(jq -r '.ignored_paths[]' <<<"$scope_json")
  product_count="$(jq -r '.products | length' <<<"$scope_json")"
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if matches_any "$path" "${all_globs[@]-}"; then
      indices="$(jq -c '[range(0; .products | length)]' <<<"$scope_json")"
    else
      indices="[]"
      for ((index = 0; index < product_count; index++)); do
        product_globs=()
        while IFS= read -r glob; do product_globs+=("$glob"); done \
          < <(jq -r --argjson i "$index" '.products[$i].paths[]' <<<"$scope_json")
        if matches_any "$path" "${product_globs[@]-}"; then
          indices="$(jq -c --argjson i "$index" '. + [$i]' <<<"$indices")"
        fi
      done
      [ "$indices" != "[]" ] || {
        matches_any "$path" "${ignored_globs[@]-}" || die "未分类改动路径: $path"
      }
    fi
    classified="$(jq -c --arg p "$path" --argjson i "$indices" '. + [{path:$p, indices:$i}]' <<<"$classified")"
  done < <(jq -r '.[]' <<<"$changed_json")
  targets="$(jq -cn --argjson s "$scope_json" --argjson c "$classified" '
    [range(0; ($s.products | length)) as $i
      | [$c[] | select(.indices | index($i)) | .path] as $paths
      | select($paths | length > 0)
      | {product:$s.products[$i].product, manifest:$s.products[$i].manifest, matched_paths:$paths}]')"
  result="$(jq -cn --arg base "$(git rev-parse "$base")" --arg head "$(git rev-parse "$head")" \
    --arg scope "${scope#./}" --argjson changed "$changed_json" --argjson targets "$targets" \
    '{schema_version:"1", base_commit:$base, head_commit:$head, scope_path:$scope, changed_paths:$changed, targets:$targets}')"
  printf '%s\n' "$result"
  [ "$(jq -r '.targets | length' <<<"$result")" -gt 0 ] || return 2
}

cmd_init() {
  local scope="" manifest current resolved rc state expected existing
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --scope) scope="$2"; shift 2 ;;
      *) die "init 参数非法: $1" ;;
    esac
  done
  [ -n "$scope" ] || die "init 必须给 --scope"
  manifest="$(task_manifest)"
  current="$(jq -r '.phase // ""' "$manifest")"
  [ "$current" = "package" ] || die "package init 必须在 package 阶段(当前: $current)"
  if resolved="$(cmd_resolve --scope "$scope")"; then
    rc=0
  else
    rc=$?
  fi
  [ "$rc" -eq 0 ] || [ "$rc" -eq 2 ] || return "$rc"
  state="$(package_state_path)"
  expected="$(jq -cn --argjson resolved "$resolved" --arg created "$(now)" '
    {schema_version:"1", base_commit:$resolved.base_commit,
     initial_head_commit:$resolved.head_commit, scope_path:$resolved.scope_path,
     created_at:$created,
     targets:[$resolved.targets[] | . + {release_commit:null}],
     development_mode_test:null, installed_test:null}')"
  if [ -f "$state" ]; then
    jq -e . "$state" >/dev/null 2>&1 || die "package-state 损坏，拒绝覆盖"
    existing="$(jq -c '{base_commit,initial_head_commit,scope_path,targets}' "$state")"
    expected="$(jq -c '{base_commit,initial_head_commit,scope_path,targets}' <<<"$expected")"
    [ "$existing" = "$expected" ] || die "已有 package-state 与当前 package 目标不一致；拒绝替换运行中的 package"
    echo "INIT-UNCHANGED"
    return 0
  fi
  printf '%s\n' "$expected" | write_package_state "$state"
  echo "INIT targets=$(jq -r '.targets | length' "$state")"
}

cmd_where() {
  local state pending
  state="$(need_package_state)"
  if [ "$(jq -r '.targets | length' "$state")" -eq 0 ]; then
    echo "NO-PACKAGE"
    return 0
  fi
  if [ "$(jq -r '.development_mode_test == null' "$state")" = "true" ]; then
    echo "PAUSED-HUMAN:development-mode-test"
    return 0
  fi
  pending="$(jq -c '[.targets[] | select(.release_commit == null)][0] // null' "$state")"
  if [ "$pending" != "null" ]; then
    jq -r '"RELEASE product="+.product+" manifest="+.manifest' <<<"$pending"
    return 0
  fi
  if [ "$(jq -r '.installed_test == null' "$state")" = "true" ]; then
    echo "PAUSED-HUMAN:installed-test"
    return 0
  fi
  echo "DONE"
}

cmd_confirm() {
  local gate="" by="" state missing
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --gate) gate="$2"; shift 2 ;;
      --by) by="$2"; shift 2 ;;
      *) die "confirm 参数非法: $1" ;;
    esac
  done
  case "$gate" in development-mode-test|installed-test) ;; *) die "confirm 的 --gate 只能是 development-mode-test|installed-test" ;; esac
  [ -n "$by" ] || die "confirm 必须给非空 --by"
  state="$(need_package_state)"
  if [ "$gate" = "installed-test" ]; then
    missing="$(jq -r '[.targets[] | select(.release_commit == null) | .product] | join(",")' "$state")"
    [ -z "$missing" ] || die "尚有未完成 release: $missing"
  fi
  if [ "$gate" = "development-mode-test" ]; then
    [ "$(jq -r '.development_mode_test == null' "$state")" = "true" ] || die "development-mode-test 已确认，不能重复写入"
    jq --arg by "$by" --arg at "$(now)" '.development_mode_test={confirmed_by:$by,confirmed_at:$at}' "$state" | write_package_state "$state"
  else
    [ "$(jq -r '.installed_test == null' "$state")" = "true" ] || die "installed-test 已确认，不能重复写入"
    jq --arg by "$by" --arg at "$(now)" '.installed_test={confirmed_by:$by,confirmed_at:$at}' "$state" | write_package_state "$state"
  fi
  echo "CONFIRMED:$gate"
}

cmd_record_release() {
  local product="" state top sd release_state result actual commit
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --product) product="$2"; shift 2 ;;
      *) die "record-release 参数非法: $1" ;;
    esac
  done
  [ -n "$product" ] || die "record-release 必须给 --product"
  state="$(need_package_state)"
  jq -e --arg p "$product" '.targets[] | select(.product == $p)' "$state" >/dev/null || die "package target 不存在: $product"
  [ "$(jq -r --arg p "$product" '.targets[] | select(.product == $p) | .release_commit == null' "$state")" = "true" ] \
    || die "package target 已记录 release: $product"
  [ "$(jq -r '.development_mode_test != null' "$state")" = "true" ] \
    || die "开发模式功能测试尚未确认，不能记录 release"
  if result="$(bash "$SCRIPT_DIR/mmw.sh" release exit-check)"; then :; else die "无法读取 S1 release exit-check"; fi
  [ "$result" = "DONE" ] || die "S1 release 尚未 DONE: $result"
  top="$(repo_top)"
  sd="$MMW_STATE_SUBDIR"
  release_state="$top/$sd/release-state.json"
  [ -f "$release_state" ] || die "无 S1 release-state，不能记录 release"
  actual="$(jq -r '.product // ""' "$release_state")"
  [ "$actual" = "$product" ] || die "S1 release product 不匹配: 期望 $product，实际 $actual"
  commit="$(git -C "$top" rev-parse HEAD)"
  # 安装包必须来自当前 HEAD:release-state.source_commit 是引擎实际构建的 commit,若 HEAD 已
  # 前进(出包后又有新提交),记录会把旧代码的包冒充成新 HEAD 的 release。
  local built_commit
  built_commit="$(jq -r '.source_commit // ""' "$release_state")"
  [ "$built_commit" = "$commit" ] || die "S1 release 构建的是 $built_commit,当前 HEAD 是 $commit;先重跑 release 再记录"
  # 多产品不变量:全部已记录产品的安装包必须出自同一 commit。后记录的产品若经过自愈修复把
  # HEAD 推前(修复可能改到共用打包代码),早前产品的包就已经不是最终代码——把它们重置回待出
  # 包由驱动循环重出,否则 exit-check 会把旧提交的包当成最终交付。
  local stale
  stale="$(jq -r --arg commit "$commit" '[.targets[] | select(.release_commit != null and .release_commit != $commit) | .product] | join(",")' "$state")"
  jq --arg p "$product" --arg commit "$commit" '
    .targets |= map(
      if .product == $p then .release_commit=$commit
      elif .release_commit != null and .release_commit != $commit then .release_commit=null
      else . end)' "$state" | write_package_state "$state"
  [ -z "$stale" ] || echo "RESET-STALE:$stale"
  echo "RECORDED:$product"
}

cmd_exit_check() {
  local state pending
  state="$(need_package_state)"
  if [ "$(jq -r '.targets | length' "$state")" -eq 0 ]; then
    echo "DONE"
    return 0
  fi
  if [ "$(jq -r '.development_mode_test == null' "$state")" = "true" ]; then
    echo "NOT-DONE:development-mode-test"
    return 1
  fi
  pending="$(jq -r '[.targets[] | select(.release_commit == null) | .product][0] // ""' "$state")"
  if [ -n "$pending" ]; then
    echo "NOT-DONE:release:$pending"
    return 1
  fi
  # 防御第二道(record-release 的重置是第一道):所有产品的 release_commit 必须是同一个,
  # 混着不同 commit 的包绝不能判 DONE。
  if [ "$(jq -r '[.targets[].release_commit] | unique | length' "$state")" -gt 1 ]; then
    echo "NOT-DONE:release-commit-mismatch"
    return 1
  fi
  if [ "$(jq -r '.installed_test == null' "$state")" = "true" ]; then
    echo "NOT-DONE:installed-test"
    return 1
  fi
  echo "DONE"
}

cmd_close() {
  rm -f "$(package_state_path)"
  echo "CLOSED"
}

case "${1:-}" in
  resolve) shift; cmd_resolve "$@" ;;
  init) shift; cmd_init "$@" ;;
  where) shift; cmd_where "$@" ;;
  confirm) shift; cmd_confirm "$@" ;;
  record-release) shift; cmd_record_release "$@" ;;
  exit-check) shift; cmd_exit_check "$@" ;;
  close) shift; cmd_close "$@" ;;
  *) die "用法: package-phase.sh resolve|init|where|confirm|record-release|exit-check|close" ;;
esac

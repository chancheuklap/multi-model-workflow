#!/usr/bin/env bash
# package-phase.sh —— develop 的产品影响解析与 package 运行态入口。
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# shellcheck source=lib/host.sh
. "$SCRIPT_DIR/lib/host.sh"

die() { echo "ERROR: $*" >&2; exit 1; }

repo_top() {
  git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"
}

task_manifest() {
  local top sd file
  top="$(repo_top)"
  sd="$(mmw_resolve_state_subdir "$top")"
  file="$top/$sd/task.json"
  [ -f "$file" ] || die "无 task.json；未给 --base/--head 时必须在受管任务内"
  printf '%s\n' "$file"
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
  local -a all_globs product_globs
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
  changed_json="$(git diff --name-only --diff-filter=ACMRTD "$base..$head" | LC_ALL=C sort -u | jq -Rsc 'split("\n") | map(select(length > 0))')"
  all_globs=()
  while IFS= read -r glob; do all_globs+=("$glob"); done < <(jq -r '.all_products_paths[]' <<<"$scope_json")
  product_count="$(jq -r '.products | length' <<<"$scope_json")"
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    if matches_any "$path" "${all_globs[@]}"; then
      indices="$(jq -c '[range(0; .products | length)]' <<<"$scope_json")"
    else
      indices="[]"
      for ((index = 0; index < product_count; index++)); do
        product_globs=()
        while IFS= read -r glob; do product_globs+=("$glob"); done \
          < <(jq -r --argjson i "$index" '.products[$i].paths[]' <<<"$scope_json")
        if matches_any "$path" "${product_globs[@]}"; then
          indices="$(jq -c --argjson i "$index" '. + [$i]' <<<"$indices")"
        fi
      done
      [ "$indices" != "[]" ] || {
        product_globs=()
        while IFS= read -r glob; do product_globs+=("$glob"); done < <(jq -r '.ignored_paths[]' <<<"$scope_json")
        matches_any "$path" "${product_globs[@]}" || die "未分类改动路径: $path"
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

case "${1:-}" in
  resolve) shift; cmd_resolve "$@" ;;
  *) die "用法: package-phase.sh resolve --scope <repo-relative-scope> [--base <commit>] [--head <commit>]" ;;
esac

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"

MANIFEST_NAME="task.json"
NONE_CHECKPOINT='{"phase":null,"status":"none","report":[],"source_fingerprint":null,"approval_id":null,"prepared_at":null,"approved_at":null}'

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

manifest_path() {
  local top state manifest
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  state="$(mmw_resolve_state_subdir "$top")"
  manifest="$top/$state/$MANIFEST_NAME"
  [ -f "$manifest" ] || die "当前不是在管任务"
  echo "$manifest"
}

write_manifest() {
  local manifest="$1" tmp
  tmp="$(mktemp "$(dirname "$manifest")/.task.json.checkpoint.XXXXXX")" || return 1
  cat >"$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    return 1
  fi
  mv "$tmp" "$manifest"
}

cmd_prepare() {
  local -a reports=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --report) reports+=("$2"); shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ "${#reports[@]}" -gt 0 ] || die "prepare 需要 --report <path>"

  local manifest phase gate loop_file loop_state
  manifest="$(manifest_path)"
  phase="$(jq -r .phase "$manifest")"
  gate="$(jq -r '.gate // empty' "$manifest")"
  [ "$phase" = "design" ] && [ -z "$gate" ] \
    || die "轻量 checkpoint 只用于 design 产物进入设计审之前"

  loop_file="$(dirname "$manifest")/loop-state.json"
  if [ -f "$loop_file" ]; then
    loop_state="$(bash "$SCRIPT_DIR/loop.sh" exit-check 2>/dev/null || true)"
    [ "$loop_state" = "DONE" ] || die "design 内层 loop 未收束: $loop_state"
  fi

  local top rel fingerprint reports_json approval_id timestamp
  top="$(git rev-parse --show-toplevel)"
  for rel in "${reports[@]}"; do
    case "$rel" in
      /*|*'
'*) die "报告路径必须是无换行的 worktree 相对路径: $rel" ;;
    esac
    case "/$rel/" in */../*) die "报告路径不能包含 .. 段: $rel" ;; esac
    [ -e "$top/$rel" ] || die "报告路径不存在: $rel"
    if [ -f "$top/$rel" ]; then
      [ -s "$top/$rel" ] || die "报告文件为空: $rel"
    elif [ -d "$top/$rel" ]; then
      [ -n "$(find "$top/$rel" -type f ! -path '*/.git/*' -size +0 -print -quit)" ] \
        || die "报告目录没有非空文件: $rel"
    else
      die "报告路径必须是文件或目录: $rel"
    fi
  done

  reports_json="$(printf '%s\n' "${reports[@]}" | jq -R . | jq -s 'unique')"
  local -a normalized_reports=() fingerprint_args=()
  while IFS= read -r rel; do normalized_reports+=("$rel"); done \
    < <(jq -r '.[]' <<<"$reports_json")
  for rel in "${normalized_reports[@]}"; do fingerprint_args+=("--report" "$rel"); done
  fingerprint="$(bash "$SCRIPT_DIR/flow.sh" fingerprint "${fingerprint_args[@]}")" \
    || die "无法计算 design 报告指纹"
  approval_id="$(printf '%s\n%s\n%s:%s:%s\n' "$phase" "$fingerprint" "$(date +%s)" "$$" "$RANDOM" \
    | git hash-object --stdin | cut -c1-12)"
  timestamp="$(now)"

  jq --argjson report "$reports_json" --arg fp "$fingerprint" --arg id "$approval_id" --arg at "$timestamp" '
    .checkpoint={
      phase:"design",
      status:"waiting-user",
      report:$report,
      source_fingerprint:$fp,
      approval_id:$id,
      prepared_at:$at,
      approved_at:null
    }
    | .status="waiting-user"
  ' "$manifest" | write_manifest "$manifest" || die "checkpoint 写入失败"

  echo "CHECKPOINT_WAITING"
  echo "approval_token=MMW-APPROVE:${approval_id}"
  echo "reports=$reports_json"
  echo "NEXT=使用 AskUser 让用户选择“确认设计 MMW-APPROVE:${approval_id}”或提出修改"
}

cmd_status() {
  local manifest
  manifest="$(manifest_path)"
  jq -r --argjson none "$NONE_CHECKPOINT" '
    (.checkpoint // $none) as $c
    | "checkpoint_phase=\($c.phase // "none")",
      "checkpoint_status=\($c.status)",
      "checkpoint_report=\($c.report | @json)",
      "checkpoint_approval_id=\($c.approval_id // "none")"
  ' "$manifest"
}

cmd_clear() {
  [ "${1:-}" = "--internal-flow" ] && [ "$#" -eq 1 ] \
    || die "clear 仅供 flow 内部调用"
  local manifest
  manifest="$(manifest_path)"
  jq --argjson none "$NONE_CHECKPOINT" '.checkpoint=$none' "$manifest" \
    | write_manifest "$manifest" || die "checkpoint 清理失败"
}

case "${1:-}" in
  prepare) shift; cmd_prepare "$@" ;;
  status) shift; cmd_status "$@" ;;
  clear) shift; cmd_clear "$@" ;;
  *) die "用法: checkpoint.sh prepare|status|clear ..." ;;
esac

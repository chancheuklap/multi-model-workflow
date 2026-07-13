#!/usr/bin/env bash
# UserPromptSubmit 相位锚(Droid 原生):注入当前流程位置；用户提交精确的设计确认
# token 时，在 Droid 处理该消息前原子批准对应 design checkpoint。
set -euo pipefail
input="$(cat)"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../scripts/lib/runtime.sh
. "$SCRIPT_DIR/../scripts/lib/runtime.sh"

cwd="$(printf '%s' "$input" | jq -r '.cwd // empty' 2>/dev/null || true)"
prompt="$(printf '%s' "$input" | jq -r '.prompt // empty' 2>/dev/null || true)"
[ -n "$cwd" ] || cwd="$PWD"
top="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" || exit 0
STATE_SUBDIR="$(mmw_resolve_state_subdir "$top")"
man="$top/$STATE_SUBDIR/task.json"
[ -f "$man" ] || exit 0

die() { echo "ERROR: $*" >&2; exit 1; }
jq -e . "$man" >/dev/null 2>&1 || die "task.json 损坏"

checkpoint_status="$(jq -r '.checkpoint.status // "none"' "$man")"
approval_id="$(jq -r '.checkpoint.approval_id // empty' "$man")"
if [ "$checkpoint_status" = "waiting-user" ] && [ -n "$approval_id" ]; then
  expected="确认设计 MMW-APPROVE:$approval_id"
  if [ "$prompt" = "$expected" ] || [ "$prompt" = "MMW-APPROVE:$approval_id" ]; then
    local_fp="$(jq -r '.checkpoint.source_fingerprint // empty' "$man")"
    reports=()
    while IFS= read -r report; do [ -n "$report" ] && reports+=("$report"); done \
      < <(jq -r '.checkpoint.report[]' "$man")
    args=()
    for report in "${reports[@]}"; do args+=("--report" "$report"); done
    current_fp="$(cd "$top" && bash "$SCRIPT_DIR/../scripts/flow.sh" fingerprint "${args[@]}")" \
      || die "无法复核待确认设计报告"
    [ "$current_fp" = "$local_fp" ] || die "设计报告在用户确认前已改变，请重新 prepare"

    tmp="$(mktemp "$(dirname "$man")/.task.json.approve.XXXXXX")" \
      || die "无法创建 checkpoint 临时文件"
    jq --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
      .checkpoint.status="approved"
      | .checkpoint.approved_at=$at
      | .status="active"
    ' "$man" >"$tmp" || { rm -f "$tmp"; die "设计批准写入失败"; }
    [ -s "$tmp" ] && jq -e . "$tmp" >/dev/null 2>&1 \
      || { rm -f "$tmp"; die "设计批准生成了非法状态"; }
    mv "$tmp" "$man" || { rm -f "$tmp"; die "设计批准原子替换失败"; }
    checkpoint_status="approved"
  fi
fi

slug="$(jq -r .slug "$man")"
phase="$(jq -r .phase "$man")"
status="$(jq -r .status "$man")"
mode="$(jq -r '.attendance // "afk"' "$man")"
if [ "$checkpoint_status" = "waiting-user" ]; then
  printf '[mmw ⚓ %s phase=%s status=%s mode=%s checkpoint=waiting-user] 必须用 AskUser 提供选项“确认设计 MMW-APPROVE:%s”或让用户提出修改；未收到精确选项前不能 handoff pass。\n' \
    "$slug" "$phase" "$status" "$mode" "$approval_id"
else
  printf '[mmw ⚓ %s phase=%s status=%s mode=%s checkpoint=%s] 按本 phase 的 load/do 干；换步、交接或不确定位置先跑 mmw where。\n' \
    "$slug" "$phase" "$status" "$mode" "$checkpoint_status"
fi
exit 0

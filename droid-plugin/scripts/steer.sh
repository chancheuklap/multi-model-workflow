#!/usr/bin/env bash
# steer.sh —— 控制面:运行级值守档切换 + 计划外分流登记(机械层,判断在 Coordinator)
#
# 值守档权威在外层 task.json.attendance(跨阶段留存);本脚本改它,并把当前活动 loop 的
# loop-state.attendance 同步过去(供软停即时判断)。进度板随改随渲染。
#
#   attend --mode attended|afk         自由切换(无门禁;afk 档无 slash 命令,直接 mmw attend)
#   unattended enter [--policy <json>] 强无人:过门禁才写(设计+计划已过门、无未答 HITL);任一不满足拒绝进入、不静默降级
#   unattended status                  报当前 mode + policy
#   side-finding record --tag <t> --disposition issue|fix [--finding <s>]  计划外分流落 open_items(见 Slice B)
#
# fail-closed:门禁不过直接 die(非零),绝不降级成 afk 蒙混。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
MANIFEST_NAME="task.json"
LOOP_NAME="loop-state.json"

die() { echo "ERROR: $*" >&2; exit 1; }

top_dir() { git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"; }
state_here() { mmw_resolve_state_subdir "$(top_dir)"; }
man_path() { echo "$(top_dir)/$(state_here)/$MANIFEST_NAME"; }
loop_path() { echo "$(top_dir)/$(state_here)/$LOOP_NAME"; }

need_man() {
  local m; m="$(man_path)"
  [ -f "$m" ] || die "当前不是在管任务 worktree(无 task.json),无 run 可指挥"
  jq -e . "$m" >/dev/null 2>&1 || die "task.json 损坏:$m"
  echo "$m"
}

# 原子写 + fail-closed(同 loop.sh):验非空且合法 JSON 才落盘,否则保留原档报错
write_json() {
  local f="$1" tmp; tmp="$(mktemp)"; cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; die "拒绝写入空/非法 JSON 到 $f;原文件保留"
  fi
  mv "$tmp" "$f"
}

# 把 mode 写进 task.json(权威),并同步当前活动 loop 的缓存
set_mode() {
  local mode="$1" policy="${2:-null}"
  local m; m="$(need_man)"
  jq --arg mode "$mode" --argjson pol "$policy" '.attendance=$mode | .unattended_policy=$pol' "$m" | write_json "$m"
  local lf; lf="$(loop_path)"
  if [ -f "$lf" ] && jq -e . "$lf" >/dev/null 2>&1; then
    jq --arg mode "$mode" '.attendance=$mode' "$lf" | write_json "$lf"
  fi
  # 板随值守档变更刷新(进入/退出 unattended 后必须)
  bash "$(dirname "$0")/progress.sh" render >/dev/null 2>&1 || true
}

# 阶段是否已过:phases 里无该阶段 → 视为不适用(真空满足);有则要求 phase_index 已越过它
phase_passed() {
  local m="$1" name="$2"
  local idx pidx
  idx="$(jq -r --arg n "$name" '.phases | index($n) // -1' "$m")"
  [ "$idx" = "-1" ] && return 0   # 本预设无此阶段,不适用
  pidx="$(jq -r '.phase_index' "$m")"
  [ "$pidx" -gt "$idx" ]
}

# 有无未答的"必须人答"HITL:status=waiting-user 或 内层 loop pause 非空
has_unanswered_hitl() {
  local m="$1"
  [ "$(jq -r '.status' "$m")" = "waiting-user" ] && return 0
  local lf; lf="$(loop_path)"
  if [ -f "$lf" ] && jq -e . "$lf" >/dev/null 2>&1; then
    [ "$(jq -r '.pause' "$lf")" != "null" ] && return 0
  fi
  return 1
}

# 第一刀默认策略(与 attendance reference 的 policy 表一致)
DEFAULT_POLICY='{"side_finding_default":"auto","hitl_unanswered":"reject_enter","budget_at_100":"hard_stop","design_gap":"hard_stop","external_env":"hard_stop","blocked_no_auto_path":"hard_stop","review_fail":"rework_then_hard_stop"}'

cmd_attend() {
  local mode=""
  while [ $# -gt 0 ]; do case "$1" in --mode) mode="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  case "$mode" in attended|afk) ;; *) die "attend --mode 只能 attended|afk(unattended 走 unattended enter 过门禁)";; esac
  set_mode "$mode" null
  echo "ATTENDANCE=$mode(运行级,已写 task.json)"
}

cmd_unattended() {
  local verb="${1:-}"; shift || true
  case "$verb" in
    enter)
      local policy="$DEFAULT_POLICY"
      while [ $# -gt 0 ]; do case "$1" in --policy) policy="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      jq -e . <<<"$policy" >/dev/null 2>&1 || die "--policy 不是合法 JSON"
      local m; m="$(need_man)"
      # 门禁:全部满足才进,任一不满足拒绝(不静默降级)
      local reasons=""
      phase_passed "$m" "design" || reasons="${reasons}- 设计未过门(design 阶段未越过)"$'\n'
      phase_passed "$m" "plan"   || reasons="${reasons}- 计划未过审(plan 阶段未越过)"$'\n'
      has_unanswered_hitl "$m"   && reasons="${reasons}- 有未答的必须人答 HITL(status=waiting-user 或 loop pause 非空)"$'\n'
      if [ -n "$reasons" ]; then
        die "拒绝进入 unattended,缺:"$'\n'"$reasons""(修完再敲,绝不降级成 afk 蒙混)"
      fi
      set_mode "unattended" "$policy"
      echo "UNATTENDED-ENTERED"
      echo "policy=$(jq -c . <<<"$policy")"
      echo "no-question 合同已激活:续跑先读盘 mode 自我约束,遇硬停写板等人。"
      ;;
    status)
      local m; m="$(need_man)"
      echo "mode=$(jq -r '.attendance // "afk"' "$m")"
      echo "policy=$(jq -c '.unattended_policy' "$m")"
      ;;
    exit)
      # 显式退出 unattended → 回 attended(用户回来接管)
      set_mode "attended" null
      echo "ATTENDANCE=attended(已退出 unattended)"
      ;;
    *) die "用法 unattended enter|status|exit" ;;
  esac
}

# 计划外分流登记:落 open_items(带 disposition),板刷新。标签枚举不变(复用 worker 标签)。
cmd_sidefinding() {
  local verb="${1:-}"; shift || true
  [ "$verb" = "record" ] || die "用法 side-finding record --tag <t> --disposition issue|fix [--finding <s>]"
  local tag="" disp="" finding=""
  while [ $# -gt 0 ]; do case "$1" in
    --tag) tag="$2"; shift 2;;
    --disposition) disp="$2"; shift 2;;
    --finding) finding="$2"; shift 2;;
    *) die "未知参数 $1";; esac; done
  case "$tag" in bug|optimize|out-of-scope|needs-evaluation) ;; *) die "--tag 只能 bug|optimize|out-of-scope|needs-evaluation";; esac
  # issue→defer_issue,fix→fix_now(命令面二选一,盘上落规范枚举)
  local disposition
  case "$disp" in
    issue) disposition="defer_issue" ;;
    fix)   disposition="fix_now" ;;
    *) die "--disposition 只能 issue|fix" ;;
  esac
  [ -n "$finding" ] || finding="(未填摘要)"
  local m; m="$(need_man)"
  local from; from="$(jq -r '.phase' "$m")"
  jq --arg t "$tag" --arg f "$finding" --arg p "$from" --arg d "$disposition" \
    '.open_items += [{tag:$t, finding:$f, from_phase:$p, disposition:$d}]' "$m" | write_json "$m"
  bash "$(dirname "$0")/progress.sh" render >/dev/null 2>&1 || true
  echo "SIDE-FINDING recorded tag=$tag disposition=$disposition"
}

case "${1:-}" in
  attend)       shift; cmd_attend "$@" ;;
  unattended)   shift; cmd_unattended "$@" ;;
  side-finding) shift; cmd_sidefinding "$@" ;;
  *) die "用法: steer.sh attend|unattended|side-finding ..." ;;
esac

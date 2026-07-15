#!/usr/bin/env bash
# note.sh —— 讨论态书签 + 唯一人闸(approve)
#
#   note set --text "<一句话>"   记现场注记(开场回报三源之一;另两源=最近 commit 标题 + 设计文档 Open Decisions)
#   note show                    读注记
#   approve --report <文件|目录>...
#       确认设计(用户显式过门后由主线程执行;用户口头同意不算,必须走 /approve-design 命令进来):
#       盖承重文档指纹(白名单第 4 条:防「确认的是 A、执行的是 B」)→ 记录确认 → attendance→afk →
#       在 design 阶段则推进到下一阶段;已过门后重跑 = 设计修订后的重新确认(只重盖指纹,不动阶段)。
#       指纹只盖 --report 指到的承重文档(主设计 + 被引用合同文档);evidence/prototype 追加不作废确认。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
MANIFEST_NAME="task.json"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

manifest_path() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  local m="$top/$MMW_STATE_SUBDIR/$MANIFEST_NAME"
  [ -f "$m" ] || die "当前不是在管任务(无 task.json)"
  echo "$m"
}

write_manifest() {
  local m="$1" tmp; tmp="$(mktemp)"; cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; echo "ERROR: 拒绝写入空/非法 JSON 到 $m;原 manifest 保留" >&2; return 1
  fi
  local stamped; stamped="$(mktemp)"
  if jq --arg at "$(now)" '.updated_at=$at' "$tmp" > "$stamped" && [ -s "$stamped" ]; then
    mv "$stamped" "$m"; rm -f "$tmp"
  else
    rm -f "$stamped"; mv "$tmp" "$m"
  fi
}

# 承重文档指纹:文件 git hash;目录 = 目录内全文件(排 .git)排序后逐一 hash 再汇总。
# 与 flow.sh where 的 approval_stale 检查同算法(单源在此,flow 调本脚本 fingerprint)。
cmd_fingerprint() {
  local -a reports=()
  while [ $# -gt 0 ]; do case "$1" in --report) reports+=("$2"); shift 2;; *) die "未知参数 $1";; esac; done
  [ "${#reports[@]}" -gt 0 ] || die "--report 必填"
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  local rel
  { for rel in "${reports[@]}"; do
      local abs="$top/$rel"; [ -e "$abs" ] || abs="$rel"
      if [ -f "$abs" ]; then git hash-object "$abs" 2>/dev/null
      elif [ -d "$abs" ]; then ( cd "$abs" && find . -type f ! -path '*/.git/*' | sort | while IFS= read -r f; do git hash-object "$f" 2>/dev/null; done )
      else echo "MISSING:$rel"
      fi
    done; } | git hash-object --stdin
}

cmd_note() {
  local verb="${1:-}"; shift || true
  local m; m="$(manifest_path)"
  case "$verb" in
    set)
      local text=""
      while [ $# -gt 0 ]; do case "$1" in --text) text="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$text" ] || die "--text 必填(一句话现场注记)"
      jq --arg t "$text" --arg at "$(now)" '.note={text:$t, at:$at}' "$m" | write_manifest "$m"
      echo "NOTE-SET" ;;
    show)
      jq -r 'if .note then "note=\(.note.text)  (记于 \(.note.at))" else "note=(空)" end' "$m" ;;
    *) die "用法: note set --text <s> | note show" ;;
  esac
}

cmd_approve() {
  local -a reports=()
  while [ $# -gt 0 ]; do case "$1" in --report) reports+=("$2"); shift 2;; *) die "未知参数 $1";; esac; done
  local m; m="$(manifest_path)"
  local top; top="$(git rev-parse --show-toplevel)"
  local phase pidx; phase="$(jq -r .phase "$m")"; pidx="$(jq -r .phase_index "$m")"

  # 缺 --report 时回落 design 阶段已钉产出(主设计文档)
  if [ "${#reports[@]}" -eq 0 ]; then
    while IFS= read -r r; do [ -n "$r" ] && reports+=("$r"); done \
      < <(jq -r '(.phase_outputs.design // [])[]' "$m")
  fi
  [ "${#reports[@]}" -gt 0 ] || die "没有可确认的承重文档:--report 指定,或先把设计文档钉进接力单(mmw pin --phase design --produced <路径>)"

  local rel
  for rel in "${reports[@]}"; do
    case "$rel" in /*) die "报告用 worktree 相对路径: $rel" ;; esac
    [ -e "$top/$rel" ] || die "承重文档不存在: $rel"
    if [ -f "$top/$rel" ]; then [ -s "$top/$rel" ] || die "承重文档为空: $rel"; fi
  done

  local args=() r
  for r in "${reports[@]}"; do args+=(--report "$r"); done
  local fp; fp="$(cmd_fingerprint "${args[@]}")" || die "指纹计算失败"
  local reports_json; reports_json="$(printf '%s\n' "${reports[@]}" | jq -R . | jq -s 'unique')"

  local had_approval; had_approval="$(jq -r 'if .approval then "yes" else "no" end' "$m")"
  local advanced=no next_phase=""
  if [ "$phase" = "design" ]; then
    # 过门:记录确认 + 承重产出钉进 design 接力单 + attendance→afk + 推进
    local phases_len last
    phases_len="$(jq -r '.phases | length' "$m")"; last=$(( phases_len - 1 ))
    if [ "$pidx" -lt "$last" ]; then
      next_phase="$(jq -r --argjson i "$(( pidx + 1 ))" '.phases[$i]' "$m")"
      jq --argjson reports "$reports_json" --arg fp "$fp" --arg at "$(now)" --arg np "$next_phase" --argjson npi "$(( pidx + 1 ))" \
        '.approval={reports:$reports, fingerprint:$fp, at:$at}
         | .phase_outputs.design=(((.phase_outputs.design // []) + $reports) | unique)
         | .artifacts += $reports | .artifacts |= unique
         | .attendance="afk" | .unattended_policy=null
         | .phase=$np | .phase_index=$npi | .repair_count=0 | .gate=null | .status="active" | .step_index=0' \
        "$m" | write_manifest "$m"
      advanced=yes
    else
      die "design 已是末阶段?phases 配置异常,人工核 task.json"
    fi
  else
    # 已过门后的重新确认(设计修订后重盖指纹),不动阶段与值守
    [ "$had_approval" = "yes" ] || die "不在 design 阶段且从未确认过,无门可过(当前 phase=$phase)"
    jq --argjson reports "$reports_json" --arg fp "$fp" --arg at "$(now)" \
      '.approval={reports:$reports, fingerprint:$fp, at:$at}' \
      "$m" | write_manifest "$m"
  fi

  bash "$SCRIPT_DIR/progress.sh" render >/dev/null 2>&1 || true
  echo "APPROVED fingerprint=$fp"
  echo "reports=$(jq -rc . <<<"$reports_json")"
  if [ "$advanced" = yes ]; then
    echo "attendance=afk(过门放权:计划起自主跑,缺输入/方向疑/出站才找用户)"
    echo "NEXT_PHASE=$next_phase(跑 mmw where 进下一阶段)"
  else
    echo "RE-APPROVED(设计修订已重新确认,指纹已更新;阶段与值守不变)"
  fi
}

case "${1:-}" in
  note)        shift; cmd_note "$@" ;;
  approve)     shift; cmd_approve "$@" ;;
  fingerprint) shift; cmd_fingerprint "$@" ;;
  *) die "用法: note.sh note set|show ... | note.sh approve --report <f>... | note.sh fingerprint --report <f>..." ;;
esac

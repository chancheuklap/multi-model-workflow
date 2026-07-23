#!/usr/bin/env bash
# note.sh —— 讨论态书签 + 唯一人闸(approve)
#
#   note set --text "<一句话>"   记现场注记(开场回报三源之一;另两源=最近 commit 标题 + 设计文档 Open Decisions)
#   note show                    读注记
#   approve --report <文件|目录>...
#       确认设计(用户显式过门后由主线程执行;用户口头同意不算,必须走 /approve-design 命令进来):
#       盖承重文档指纹(白名单第 4 条:防「确认的是 A、执行的是 B」)→ 记录确认 → attendance→afk →
#       在 design 阶段则推进到下一阶段;已过门后重跑 = 设计修订后的重新确认(只重盖指纹,不动阶段)。
#       指纹盖主设计、被引用合同，以及 accepted prototype 的 README + selected；未选候选和普通 evidence 不进确认面。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"
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
  local design_rel r primary_reports=0
  design_rel="$(mmw_prototype_design_rel "$m")" || die "manifest.docs.design 缺失"
  # 缺 --report 时先回落已钉的设计材料；旧 prototype/mockup 自动项不跟进新一轮审批。
  if [ "${#reports[@]}" -eq 0 ]; then
    while IFS= read -r r; do
      [ -n "$r" ] || continue
      case "$r" in "$design_rel/prototype/"*|"$design_rel/mockup/"*) continue ;; esac
      reports+=("$r")
    done < <(jq -r '(.phase_outputs.design // [])[]' "$m")
  fi
  for r in ${reports[@]+"${reports[@]}"}; do
    case "$r" in "$design_rel/prototype/"*|"$design_rel/mockup/"*) ;; *) primary_reports=$(( primary_reports + 1 )) ;; esac
  done

  # prototype 是 design 内层机器门：未收敛、已废止或磁盘有未登记产物都不能越过唯一人闸。
  local prototype_status prototype_untracked rel
  prototype_status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$m")"
  case "$prototype_status" in
    active)
      die "prototype 仍在第 $(jq -r '.prototype.iteration' "$m") 轮，拒绝确认设计；先按 mmw where 完成本轮 checkpoint"
      ;;
    superseded)
      die "prototype 验证问题已随方向失效，拒绝确认设计；先运行 mmw handoff --conclusion needs-redirection --to-phase propose"
      ;;
    accepted)
      rel="$(jq -r '.prototype.log // empty' "$m")"
      [ -n "$rel" ] || die "accepted prototype 缺 log"
      mmw_prototype_validate_log "$top" "$m" "$rel" || die "accepted prototype log 无效"
      reports+=("$rel")
      [ "$(jq -r '.prototype.selected | length' "$m")" -gt 0 ] || die "accepted prototype 缺 selected"
      while IFS= read -r rel; do
        [ -n "$rel" ] || continue
        mmw_prototype_validate_artifact "$top" "$m" "$rel" || die "accepted prototype selected 无效:$rel"
        reports+=("$rel")
      done < <(jq -r '.prototype.selected[]' "$m")
      ;;
    "")
      prototype_untracked="$(mmw_prototype_untracked_paths "$top" "$m")"
      [ -z "$prototype_untracked" ] || die "磁盘有未登记 prototype/mockup，拒绝确认设计；先按 mmw where 运行 prototype start --adopt"
      ;;
    *) die "prototype 状态损坏(status=$prototype_status)，拒绝确认设计" ;;
  esac

  [ "$primary_reports" -gt 0 ] || die "没有主设计材料可确认；先 --report 主设计文档，或 mmw pin --phase design --produced <主设计文档>"
  [ "${#reports[@]}" -gt 0 ] || die "没有可确认的承重文档:--report 指定,或先把设计文档钉进接力单(mmw pin --phase design --produced <路径>)"

  local rel
  for rel in "${reports[@]}"; do
    case "$rel" in /*) die "报告用 worktree 相对路径: $rel" ;; esac
    [ -e "$top/$rel" ] || die "承重文档不存在: $rel"
    if [ -f "$top/$rel" ]; then [ -s "$top/$rel" ] || die "承重文档为空: $rel"; fi
  done

  # 指纹输入顺序必须与落盘 reports 顺序完全一致；先 unique/sort，再按该数组计算。
  local reports_json; reports_json="$(printf '%s\n' "${reports[@]}" | jq -R . | jq -s 'unique')"
  local args=() r
  while IFS= read -r r; do [ -n "$r" ] && args+=(--report "$r"); done < <(jq -r '.[]' <<<"$reports_json")
  local fp; fp="$(cmd_fingerprint "${args[@]}")" || die "指纹计算失败"

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
         | .phase_outputs.design=$reports
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
      '.approval={reports:$reports, fingerprint:$fp, at:$at}
       | .phase_outputs.design=$reports
       | .artifacts += $reports | .artifacts |= unique' \
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

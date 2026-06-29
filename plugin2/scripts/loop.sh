#!/usr/bin/env bash
# loop.sh —— 内层 loop 引擎(确定层:看守 steps/checklist、软停×在场、退出三件套核对)
#
# 操作 <worktree>/.claude/multi-model-workflow/loop-state.json(独立于外层 task.json)。
# 进一个 loop 阶段时 init,退出时由阶段收尾清。看守 hook 与 exit-check 都读它。
#
#   init        建 loop-state(--kind execution|review|contract-gate)
#   attendance  设 attended|afk(只动软停一档)
#   step        add / done                落地步(pack)
#   checklist   add / cover               审核覆盖清单(主线程从文档抽)
#   finding     add                       审核发现(置信度/严重度)
#   softstop    有默认的判断:在场→写 pause;afk→自决+留 decisions,继续
#   surface     缺输入/方向疑:永远写 pause(needs-context|needs-redirection)
#   resume      清 pause(答复后续)
#   exit-check  退出判据核:DONE / NOT-DONE:<剩> / PAUSED:<因>(给看守 hook 用)
set -euo pipefail

STATE_SUBDIR=".claude/multi-model-workflow"
LOOP_NAME="loop-state.json"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
loop_file() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  echo "$top/$STATE_SUBDIR/$LOOP_NAME"
}
need_loop() { local f; f="$(loop_file)"; [ -f "$f" ] || die "无 loop-state(先 loop.sh init)"; echo "$f"; }
# 原子写 + fail-closed:上游 jq 失败会送来空/非法内容,验过非空且合法 JSON 才 mv,
# 否则保留原文件并报错退非零(绝不把状态截成 0 字节,违"不搞静默兜底")。
write() {
  local f="$1" tmp; tmp="$(mktemp)"; cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; echo "ERROR: 拒绝写入空/非法 JSON 到 $f(上游 jq 可能失败);原文件保留" >&2; return 1
  fi
  mv "$tmp" "$f"
}
edit() { local f="$1"; shift; jq "$@" "$f" | write "$f"; }

cmd_init() {
  local kind=""
  while [ $# -gt 0 ]; do case "$1" in --kind) kind="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  case "$kind" in execution|review|contract-gate) ;; *) die "--kind 只能 execution|review|contract-gate";; esac
  local f top; top="$(git rev-parse --show-toplevel)"; f="$top/$STATE_SUBDIR/$LOOP_NAME"
  mkdir -p "$top/$STATE_SUBDIR"
  jq -n --arg k "$kind" '{schema_version:"1", kind:$k, attendance:"afk",
    steps:[], checklist:[], findings:[], decisions:[], pause:null}' > "$f"
  echo "INIT kind=$kind"
}

cmd_attendance() {
  local mode=""
  while [ $# -gt 0 ]; do case "$1" in --mode) mode="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  case "$mode" in attended|afk) ;; *) die "--mode 只能 attended|afk";; esac
  edit "$(need_loop)" --arg m "$mode" '.attendance=$m'
  echo "ATTENDANCE=$mode"
}

cmd_step() {
  local verb="${1:-}"; shift || true
  local f; f="$(need_loop)"
  case "$verb" in
    add)
      local id="" desc=""
      while [ $# -gt 0 ]; do case "$1" in --id) id="$2"; shift 2;; --desc) desc="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$id" ] || die "--id 必填"
      edit "$f" --arg id "$id" --arg d "$desc" '.steps += [{id:$id, desc:$d, status:"pending", commit:null}]'
      echo "STEP-ADD $id" ;;
    done)
      local id="" commit=""
      while [ $# -gt 0 ]; do case "$1" in --id) id="$2"; shift 2;; --commit) commit="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$id" ] || die "--id 必填"
      jq -e --arg id "$id" 'any(.steps[]; .id==$id)' "$f" >/dev/null || die "无此 step: $id"
      edit "$f" --arg id "$id" --arg c "$commit" \
        '.steps |= map(if .id==$id then .status="done" | .commit=($c|select(.!="")) else . end)'
      echo "STEP-DONE $id" ;;
    *) die "用法 step add|done" ;;
  esac
}

cmd_checklist() {
  local verb="${1:-}"; shift || true
  local f; f="$(need_loop)"
  case "$verb" in
    add)
      local item="" source=""
      while [ $# -gt 0 ]; do case "$1" in --item) item="$2"; shift 2;; --source) source="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$item" ] || die "--item 必填"
      edit "$f" --arg i "$item" --arg s "$source" '.checklist += [{item:$i, source:$s, status:"open", evidence:null}]'
      echo "CHECK-ADD $item" ;;
    cover)
      local item="" ev=""
      while [ $# -gt 0 ]; do case "$1" in --item) item="$2"; shift 2;; --evidence) ev="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$item" ] || die "--item 必填"
      jq -e --arg i "$item" 'any(.checklist[]; .item==$i)' "$f" >/dev/null || die "无此 item: $item"
      edit "$f" --arg i "$item" --arg e "$ev" \
        '.checklist |= map(if .item==$i then .status="covered" | .evidence=($e|select(.!="")) else . end)'
      echo "CHECK-COVER $item" ;;
    *) die "用法 checklist add|cover" ;;
  esac
}

cmd_finding() {
  local verb="${1:-}"; shift || true
  [ "$verb" = "add" ] || die "用法 finding add"
  local sev="" conf="" loc=""
  while [ $# -gt 0 ]; do case "$1" in --severity) sev="$2"; shift 2;; --confidence) conf="$2"; shift 2;; --locator) loc="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  case "$sev" in Critical|Important|Minor) ;; *) die "--severity 只能 Critical|Important|Minor";; esac
  edit "$(need_loop)" --arg s "$sev" --argjson c "${conf:-5}" --arg l "$loc" \
    '.findings += [{severity:$s, confidence:$c, locator:$l, status:"open"}]'
  echo "FINDING-ADD $sev"
}

# 软停:有合理默认的判断。在场→写 pause 问人;afk→自决+留痕,继续(不偷跳)
cmd_softstop() {
  local q="" at="" default=""
  while [ $# -gt 0 ]; do case "$1" in --question) q="$2"; shift 2;; --at-step) at="$2"; shift 2;; --default) default="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  [ -n "$q" ] || die "--question 必填"
  local f; f="$(need_loop)"
  local mode; mode="$(jq -r .attendance "$f")"
  if [ "$mode" = "attended" ]; then
    edit "$f" --arg at "$at" --arg q "$q" '.pause={at_step:$at, kind:"soft", reason:"soft", question:$q}'
    echo "PAUSED-SOFT"
  else
    [ -n "$default" ] || default="(default)"
    edit "$f" --arg at "$at" --arg c "$default" --arg q "$q" --arg t "$(now)" \
      '.decisions += [{at_step:$at, chose:$c, why:("afk 自决: "+$q), at:$t}]'
    echo "AUTO-DECIDED chose=$default"
  fi
}

# 冒泡:缺输入/方向疑。永远停,不分在场
cmd_surface() {
  local kind="" q="" at=""
  while [ $# -gt 0 ]; do case "$1" in --kind) kind="$2"; shift 2;; --question) q="$2"; shift 2;; --at-step) at="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  case "$kind" in needs-context|needs-redirection) ;; *) die "--kind 只能 needs-context|needs-redirection";; esac
  [ -n "$q" ] || die "--question 必填"
  edit "$(need_loop)" --arg at "$at" --arg k "$kind" --arg q "$q" \
    '.pause={at_step:$at, kind:"surface", reason:$k, question:$q}'
  echo "SURFACED $kind"
}

cmd_resume() { edit "$(need_loop)" '.pause=null'; echo "RESUMED"; }

# 退出三件套核对:DONE / NOT-DONE:<剩> / PAUSED:<因>。给看守 hook 用(它据此 exit2 顶回去 or 放停)
cmd_exit_check() {
  local f; f="$(need_loop)"
  # fail-closed:状态文件损坏/空/非法 JSON 不能当 done/PAUSED 放行,报 CORRUPT 让看守拦
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:loop-state 空/非法 JSON"; return 0; }
  local kind; kind="$(jq -r .kind "$f")"
  # 暂停优先:停着就是停着,不算 done
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"; return 0
  fi
  case "$kind" in
    execution)
      local rem; rem="$(jq -r '[.steps[]|select(.status!="done")|.id]|join(",")' "$f")"
      [ -z "$rem" ] && echo "DONE" || echo "NOT-DONE:steps=$rem" ;;
    review)
      local rem crit
      rem="$(jq -r '[.checklist[]|select(.status!="covered")|.item]|join(",")' "$f")"
      crit="$(jq -r '[.findings[]|select(.severity=="Critical" and (.status//"open")=="open")]|length' "$f")"
      if [ -z "$rem" ] && [ "$crit" -eq 0 ]; then echo "DONE"
      else echo "NOT-DONE:checklist=${rem:-none};open_critical=$crit"; fi ;;
    contract-gate)
      local sr cr
      sr="$(jq -r '[.steps[]|select(.status!="done")|.id]|join(",")' "$f")"
      cr="$(jq -r '[.checklist[]|select(.status!="covered")|.item]|join(",")' "$f")"
      if [ -z "$sr" ] && [ -z "$cr" ]; then echo "DONE"
      else echo "NOT-DONE:packs=${sr:-none};contracts=${cr:-none}"; fi ;;
  esac
}

case "${1:-}" in
  init)        shift; cmd_init "$@" ;;
  attendance)  shift; cmd_attendance "$@" ;;
  step)        shift; cmd_step "$@" ;;
  checklist)   shift; cmd_checklist "$@" ;;
  finding)     shift; cmd_finding "$@" ;;
  softstop)    shift; cmd_softstop "$@" ;;
  surface)     shift; cmd_surface "$@" ;;
  resume)      shift; cmd_resume "$@" ;;
  exit-check)  shift; cmd_exit_check "$@" ;;
  *) die "用法: loop.sh init|attendance|step|checklist|finding|softstop|surface|resume|exit-check ..." ;;
esac

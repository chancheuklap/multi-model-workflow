#!/usr/bin/env bash
# loop.sh —— 内层 loop 引擎(确定层:看守 steps/checklist、软停×在场、退出三件套核对)
#
# 操作 <worktree>/状态平面(mmw_state_subdir)/loop-state.json(独立于外层 task.json)。
# 进一个 loop 阶段时 init,退出时由阶段收尾清。exit-check 与 flow.sh handoff 确定性闸都读它。
#
#   init        建 loop-state(--kind execution|review|contract-gate [--max-rounds N])
#   attendance  设当前 loop 的档 attended|afk|unattended(权威在 task.json,这里只改当前 loop 缓存)
#   step        add / done                落地步(pack)
#   round       next                      审 loop 轮账;到 max_rounds 自动 surface 熔断(机器计数)
#   checklist   add / cover               审核覆盖清单(主线程从文档抽)
#   finding     add                       审核发现(置信度/严重度)
#   softstop    有默认的判断:在场→写 pause;afk→自决+留 decisions,继续
#   surface     缺输入/方向疑:永远写 pause(needs-context|needs-redirection)
#   resume      清 pause(答复后续)
#   exit-check  退出判据核:DONE / NOT-DONE:<剩> / PAUSED:<因>(给 flow.sh handoff 确定性闸 + where 断点恢复用)
#   close       loop 收束:删 loop-state(schema「退出时清」的落地)。由 flow.sh handoff 结论落定时调,防残留污染下阶段 where。幂等,无 loop 也不报错。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
LOOP_NAME="loop-state.json"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
loop_file() {
  local top sd
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  sd="$(mmw_resolve_state_subdir "$top")"
  echo "$top/$sd/$LOOP_NAME"
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
  local kind="" max_rounds=0
  while [ $# -gt 0 ]; do case "$1" in
    --kind) kind="$2"; shift 2;;
    --max-rounds) max_rounds="$2"; shift 2;;   # 审 loop 轮上限(0=不限;review.sh 起审时传,熔断机器计数)
    *) die "未知参数 $1";; esac; done
  case "$kind" in execution|review|contract-gate) ;; *) die "--kind 只能 execution|review|contract-gate";; esac
  case "$max_rounds" in ''|*[!0-9]*) die "--max-rounds 必须是非负整数";; esac
  local f top sd
  top="$(git rev-parse --show-toplevel)"
  sd="$(mmw_resolve_state_subdir "$top")"
  f="$top/$sd/$LOOP_NAME"
  # fail-closed:已有未收束 loop 不许覆盖(防手滑 re-init 抹掉 execution 进度/子 worktree 映射)。
  # 换 loop 前必须显式 close(handoff 会自动 close;review start 换审 loop 前也先 close)。
  if [ -f "$f" ]; then
    die "已有未收束 loop(kind=$(jq -r '.kind // "?"' "$f" 2>/dev/null));先 mmw loop close 再 init,或复用当前 loop"
  fi
  mkdir -p "$top/$sd"
  # 值守档权威在外层 task.json(跨阶段留存);loop init 读它入 loop-state 供软停判断,缺省 afk。
  local mode="afk" man="$top/$sd/task.json"
  if [ -f "$man" ]; then
    local m; m="$(jq -r '.attendance // "afk"' "$man" 2>/dev/null || echo afk)"
    case "$m" in attended|afk|unattended) mode="$m";; esac
  fi
  jq -n --arg k "$kind" --argjson mr "$max_rounds" --arg mode "$mode" '{schema_version:"1", kind:$k, attendance:$mode,
    round:1, max_rounds:$mr,
    steps:[], checklist:[], findings:[], decisions:[], pause:null}' > "$f"
  echo "INIT kind=$kind max_rounds=$max_rounds attendance=$mode"
}

# 轮账:审 loop 每跑完一整轮(全视角覆盖+修复重验)未收敛,round next 记一轮。
# 到上限自动 surface 熔断(机器计数,不靠主线程自觉)——防无限打转/reward hacking。
cmd_round() {
  local verb="${1:-}"; shift || true
  [ "$verb" = "next" ] || die "用法 round next"
  local f; f="$(need_loop)"
  local max cur new
  max="$(jq -r '.max_rounds // 0' "$f")"
  cur="$(jq -r '.round // 1' "$f")"
  new=$(( cur + 1 ))
  if [ "$max" -gt 0 ] && [ "$new" -gt "$max" ]; then
    edit "$f" --arg q "审满 $max 轮未收敛,引擎熔断交人(防无限打转/reward hacking)" \
      '.pause={at_step:"", kind:"surface", reason:"needs-redirection", question:$q}'
    echo "ROUND-CAP:max=$max(已自动 surface,主线程收口 handoff)"
    return 0
  fi
  edit "$f" --argjson r "$new" '.round=$r'
  echo "ROUND=$new/$max"
}

cmd_attendance() {
  local mode=""
  while [ $# -gt 0 ]; do case "$1" in --mode) mode="$2"; shift 2;; *) die "未知参数 $1";; esac; done
  case "$mode" in attended|afk|unattended) ;; *) die "--mode 只能 attended|afk|unattended";; esac
  edit "$(need_loop)" --arg m "$mode" '.attendance=$m'
  echo "ATTENDANCE=$mode"
}

cmd_step() {
  local verb="${1:-}"; shift || true
  local f; f="$(need_loop)"
  case "$verb" in
    add)
      local id="" desc="" plan="" worktree=""
      while [ $# -gt 0 ]; do case "$1" in --id) id="$2"; shift 2;; --desc) desc="$2"; shift 2;; --plan) plan="$2"; shift 2;; --worktree) worktree="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$id" ] || die "--id 必填"
      # plan/worktree 可空(模式A 小改步无 plan);模式B 一 plan 一步,派前记好映射供断点恢复
      edit "$f" --arg id "$id" --arg d "$desc" --arg p "$plan" --arg w "$worktree" \
        '.steps += [{id:$id, desc:$d, status:"pending", commit:null,
                     plan:(if $p=="" then null else $p end),
                     worktree:(if $w=="" then null else $w end)}]'
      echo "STEP-ADD $id" ;;
    done)
      local id="" commit=""
      while [ $# -gt 0 ]; do case "$1" in --id) id="$2"; shift 2;; --commit) commit="$2"; shift 2;; *) die "未知参数 $1";; esac; done
      [ -n "$id" ] || die "--id 必填"
      jq -e --arg id "$id" 'any(.steps[]; .id==$id)' "$f" >/dev/null || die "无此 step: $id"
      # 注意别用 `=($c|select(...))`:右侧 empty 会把整个元素从数组蒸发(步账静默清空)
      edit "$f" --arg id "$id" --arg c "$commit" \
        '.steps |= map(if .id==$id then (.status="done" | .commit=(if $c=="" then .commit else $c end)) else . end)'
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
      # 同 step done:右侧 select 出 empty 会蒸发整个元素,禁用该写法
      edit "$f" --arg i "$item" --arg e "$ev" \
        '.checklist |= map(if .item==$i then (.status="covered" | .evidence=(if $e=="" then .evidence else $e end)) else . end)'
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

# 收束:删 loop-state(schema「进 loop 时 init,退出时清」的落地)。幂等——无 loop / 不在 git 都安静退 0,
# 绝不让清理失败反过来阻断上游 handoff 的回执。
cmd_close() {
  local top sd
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "NO-GIT"; return 0; }
  sd="$(mmw_resolve_state_subdir "$top")"
  rm -f "$top/$sd/$LOOP_NAME"
  echo "CLOSED"
}

# 退出三件套核对:DONE / NOT-DONE:<剩> / PAUSED:<因>。给 flow.sh handoff 确定性闸(审闸内 pass 前核 DONE)+ where 断点恢复用
cmd_exit_check() {
  local f; f="$(need_loop)"
  # fail-closed:状态文件损坏/空/非法 JSON 不能当 done/PAUSED 放行,报 CORRUPT 让上游闸拦
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:loop-state 空/非法 JSON"; return 0; }
  local kind; kind="$(jq -r .kind "$f")"
  # 暂停优先:停着就是停着,不算 done
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"; return 0
  fi
  # 空账本不算 DONE(fail-closed):没登记 steps/checklist = 忘了建账,不是"没剩余"。
  # 防"漏登记 → 空清单静默过门"(execution 忘 step add / review 忘抽清单 / ③门忘登记合同——
  # 无跨 plan 合同也要登记一条 no-cross-plan-contracts 并 cover 坐实,见 plan-impl.md)。
  case "$kind" in
    execution)
      [ "$(jq -r '.steps|length' "$f")" -gt 0 ] || { echo "NOT-DONE:steps=EMPTY(步账未登记,先 loop step add)"; return 0; }
      local rem; rem="$(jq -r '[.steps[]|select(.status!="done")|.id]|join(",")' "$f")"
      [ -z "$rem" ] && echo "DONE" || echo "NOT-DONE:steps=$rem" ;;
    review)
      [ "$(jq -r '.checklist|length' "$f")" -gt 0 ] || { echo "NOT-DONE:checklist=EMPTY(覆盖清单未登记,先 loop checklist add)"; return 0; }
      local rem crit
      rem="$(jq -r '[.checklist[]|select(.status!="covered")|.item]|join(",")' "$f")"
      crit="$(jq -r '[.findings[]|select(.severity=="Critical" and (.status//"open")=="open")]|length' "$f")"
      if [ -z "$rem" ] && [ "$crit" -eq 0 ]; then echo "DONE"
      else echo "NOT-DONE:checklist=${rem:-none};open_critical=$crit"; fi ;;
    contract-gate)
      [ "$(jq -r '.checklist|length' "$f")" -gt 0 ] || { echo "NOT-DONE:contracts=EMPTY(合同清单未登记;无跨 plan 合同也要登记 no-cross-plan-contracts 并 cover 坐实)"; return 0; }
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
  round)       shift; cmd_round "$@" ;;
  checklist)   shift; cmd_checklist "$@" ;;
  finding)     shift; cmd_finding "$@" ;;
  softstop)    shift; cmd_softstop "$@" ;;
  surface)     shift; cmd_surface "$@" ;;
  resume)      shift; cmd_resume "$@" ;;
  close)       shift; cmd_close "$@" ;;
  exit-check)  shift; cmd_exit_check "$@" ;;
  *) die "用法: loop.sh init|attendance|step|round|checklist|finding|softstop|surface|resume|close|exit-check ..." ;;
esac

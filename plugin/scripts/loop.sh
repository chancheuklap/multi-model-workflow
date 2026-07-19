#!/usr/bin/env bash
# loop.sh —— 落地执行账本(书记员:只记录,不否决)
#
# 操作 <worktree>/.claude/multi-model-workflow/loop-state.json(独立于外层 task.json)。
# 只服务 build 落地:记「哪份 plan 派给了哪个子 worktree、做到哪」,断点恢复靠它认路。
# 审查不再记账——审的收口看产物(审查报告落盘含 verdict),不看本账本。
#
#   init        建执行账本(build 派发前;已有未收束账本拒覆盖,防抹掉派发映射)
#   step        add / done                 一份 plan 一步;done 由 record-step hook 在 commit 后自动打,也可手打
#   attendance  设当前账本的值守缓存 attended|afk|unattended(权威在 task.json)
#   softstop    有合理默认的小事:在场→写 pause 问人;否则自决+留痕继续
#   surface     缺输入/方向疑:永远写 pause(needs-context|needs-redirection)
#   resume      清 pause(答复后续)
#   status      报账本现状:steps 完成度 + pause(where 断点恢复用;只报告,不当闸)
#   close       收束:删账本。幂等,无账本也不报错。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
LOOP_NAME="loop-state.json"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
loop_file() {
  local top
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  echo "$top/$MMW_STATE_SUBDIR/$LOOP_NAME"
}
need_loop() { local f; f="$(loop_file)"; [ -f "$f" ] || die "无执行账本(先 loop init)"; echo "$f"; }
# 原子写 + fail-closed:上游 jq 失败会送来空/非法内容,验过非空且合法 JSON 才 mv,
# 否则保留原文件并报错退非零(绝不把状态截成 0 字节)。
write() {
  local f="$1" tmp; tmp="$(mktemp)"; cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; echo "ERROR: 拒绝写入空/非法 JSON 到 $f(上游 jq 可能失败);原文件保留" >&2; return 1
  fi
  mv "$tmp" "$f"
}
edit() { local f="$1"; shift; jq "$@" "$f" | write "$f"; }

cmd_init() {
  [ $# -eq 0 ] || die "loop init 不带参数(只有执行账本;审查不记账,收口看审查报告)"
  local f top
  top="$(git rev-parse --show-toplevel)"
  f="$top/$MMW_STATE_SUBDIR/$LOOP_NAME"
  # 已有未收束账本不许覆盖(防手滑 re-init 抹掉派发映射)。换账本先显式 loop close。
  if [ -f "$f" ]; then
    die "已有未收束执行账本;先 mmw loop close 再 init,或复用当前账本"
  fi
  mkdir -p "$top/$MMW_STATE_SUBDIR"
  # 值守档权威在外层 task.json;init 读入缓存供软停判断,缺省 attended(不冒充放权)
  local mode="attended" man="$top/$MMW_STATE_SUBDIR/task.json"
  if [ -f "$man" ]; then
    local m; m="$(jq -r '.attendance // "attended"' "$man" 2>/dev/null || echo attended)"
    case "$m" in attended|afk|unattended) mode="$m";; esac
  fi
  jq -n --arg mode "$mode" --arg ts "$(now)" '{schema_version:"2", kind:"execution", attendance:$mode,
    started_at:$ts, steps:[], decisions:[], pause:null}' > "$f"
  echo "INIT attendance=$mode"
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
      # plan/worktree 可空(小改步无 plan);一 plan 一步,派前记好映射供断点恢复
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

# 软停:有合理默认的判断。在场→写 pause 问人;否则→自决+留痕,继续(不偷跳)
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
      '.decisions += [{at_step:$at, chose:$c, why:("自决: "+$q), at:$t}]'
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

# 现状报告(只报,不否决):NO-LOOP / CORRUPT / PAUSED:<因> / steps=<done>/<total> remaining=<ids|none>
cmd_status() {
  local f; f="$(loop_file)"
  [ -f "$f" ] || { echo "NO-LOOP"; return 0; }
  jq -e . "$f" >/dev/null 2>&1 || { echo "CORRUPT:loop-state 空/非法 JSON"; return 0; }
  if [ "$(jq -r '.pause // "null"' "$f")" != "null" ]; then
    echo "PAUSED:$(jq -r '.pause.reason' "$f")"; return 0
  fi
  local total ndone rem
  total="$(jq -r '.steps|length' "$f")"
  ndone="$(jq -r '[.steps[]|select(.status=="done")]|length' "$f")"
  rem="$(jq -r '[.steps[]|select(.status!="done")|.id]|join(",")' "$f")"
  echo "steps=$ndone/$total remaining=${rem:-none}"
  # unattended 墙钟软预算(只报不硬杀):超了亮 BUDGET-EXCEEDED,由 where / progress 板浮出
  if [ "$(jq -r '.attendance // "attended"' "$f")" = "unattended" ]; then
    local started budget then_s now_s elapsed
    started="$(jq -r '.started_at // ""' "$f")"
    budget="$(jq -r '.loop_guards.unattended_wall_clock_seconds // 10800' "$SCRIPT_DIR/../state-schema/routes.json" 2>/dev/null || echo 10800)"
    case "$budget" in ''|*[!0-9]*) budget=10800 ;; esac
    if [ -n "$started" ] && [ "$budget" -gt 0 ]; then
      then_s="$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$started" +%s 2>/dev/null || date -u -d "$started" +%s 2>/dev/null || echo "")"
      now_s="$(date -u +%s)"
      if [ -n "$then_s" ]; then
        elapsed=$(( now_s - then_s ))
        [ "$elapsed" -gt "$budget" ] && echo "BUDGET-EXCEEDED elapsed=${elapsed}s budget=${budget}s(unattended 墙钟软预算;只浮出,不硬杀)"
      fi
    fi
  fi
}

# 收束:删账本。幂等——无账本/不在 git 都安静退 0,清理失败不阻断上游回执。
cmd_close() {
  local top
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "NO-GIT"; return 0; }
  rm -f "$top/$MMW_STATE_SUBDIR/$LOOP_NAME"
  echo "CLOSED"
}

case "${1:-}" in
  init)        shift; cmd_init "$@" ;;
  attendance)  shift; cmd_attendance "$@" ;;
  step)        shift; cmd_step "$@" ;;
  softstop)    shift; cmd_softstop "$@" ;;
  surface)     shift; cmd_surface "$@" ;;
  resume)      shift; cmd_resume "$@" ;;
  status)      shift; cmd_status "$@" ;;
  close)       shift; cmd_close "$@" ;;
  *) die "用法: loop.sh init|attendance|step|softstop|surface|resume|status|close ..." ;;
esac

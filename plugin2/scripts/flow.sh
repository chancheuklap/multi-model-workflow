#!/usr/bin/env bash
# flow.sh —— 推进引擎(确定的部分:登记 + 交接 + 算下一步,零手搓)
#
#   handoff   阶段/帮手干完调它:记交接单(产出+结论)→ 按结论算动作 → 写进度档 → 回"下一步"
#   spinoff   阶段中途挖到 bug/旁路优化:登记成关联子任务,主流程不动,不盲目 out-of-scope
#   where     不推进,只算"你在哪、下一步什么"(给断点恢复用)
#
# 结论词是统一一套(routes.json conclusions),全 plugin 通用,根除旧 plugin 6-vs-4 分裂。
# 选哪个结论是 LLM 判断(灵活);选完的登记和推进是本脚本做(确定)。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROUTES="$SCRIPT_DIR/../state-schema/routes.json"
STATE_SUBDIR=".claude/multi-model-workflow"
MANIFEST_NAME="task.json"

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

manifest_path() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  local m="$top/$STATE_SUBDIR/$MANIFEST_NAME"
  [ -f "$m" ] || die "当前不是在管任务(无 task.json),先回入口走路由/准备"
  echo "$m"
}

# 原子写:tmp + mv
write_manifest() { local m="$1" tmp; tmp="$(mktemp)"; cat > "$tmp"; mv "$tmp" "$m"; }

# ---------- handoff ----------
cmd_handoff() {
  local conclusion="" ; local -a produced=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --conclusion) conclusion="$2"; shift 2 ;;
      --produced)   produced+=("$2"); shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$conclusion" ] || die "--conclusion 必填(交接单缺结论,拒收)"   # fail-closed
  [ -f "$ROUTES" ] || die "找不到 routes.json: $ROUTES"

  # 结论词必须在统一词表内,否则当场拦(fail-closed)
  jq -e --arg c "$conclusion" '.conclusions | index($c) != null' "$ROUTES" >/dev/null \
    || die "结论词非法: $conclusion(只能 $(jq -rc .conclusions "$ROUTES"))"

  local m; m="$(manifest_path)"
  local cur_phase pidx rc tc gate gated
  cur_phase="$(jq -r .phase "$m")"
  pidx="$(jq -r .phase_index "$m")"
  rc="$(jq -r .repair_count "$m")"
  tc="$(jq -r .turnaround_count "$m")"
  gate="$(jq -r '.gate // empty' "$m")"   # "" = 不在审闸;非空 = 正在该阶段审 loop 里
  # 本阶段是不是 review-gated(routes.review_gates)
  gated=no
  jq -e --arg p "$cur_phase" '(.review_gates // []) | index($p) != null' "$ROUTES" >/dev/null 2>&1 && gated=yes

  # 阶段序列读进度记录的 phases(本任务开着的阶段),不按 scenario 查 routes
  local phases_len last max_repair max_turn first_phase
  phases_len="$(jq -r '.phases | length' "$m")"
  [ "$phases_len" -gt 0 ] || die "进度记录无 phases"
  last=$(( phases_len - 1 ))
  max_repair="$(jq -r '.caps.max_repair' "$ROUTES")"
  max_turn="$(jq -r '.caps.max_turnaround' "$ROUTES")"
  first_phase="$(jq -r '.phases[0]' "$m")"

  # 按结论算动作(引擎核心)。new_gate 默认清空;只有"进审闸"那一支把它设成当前阶段。
  local new_phase="$cur_phase" new_pidx="$pidx" new_rc="$rc" new_tc="$tc" new_status="active" new_gate=""
  local next_action next_phase="" human
  case "$conclusion" in
    pass)
      if [ -z "$gate" ] && [ "$gated" = yes ]; then
        # 阶段产物刚过、还没审:进审闸,phase 不动、不 advance,等审的 verdict 再来一次 handoff
        new_gate="$cur_phase"
        next_action="review"; next_phase="$cur_phase"
        human="[$cur_phase] 产物通过 → 进审闸(review/$cur_phase.md),审过 handoff pass 才进下一阶段"
      elif [ "$pidx" -ge "$last" ]; then
        # 不在闸(或非 gated)且是末阶段 → 待收尾
        new_status="ready-to-close"; next_action="done"; next_phase=""
        human="末阶段 [$cur_phase] 通过 → 待收尾(回主仓库 prepare.sh cleanup)"
      else
        # 不在闸的普通过 或 审 verdict pass(gate 清空)→ advance
        new_pidx=$(( pidx + 1 )); new_rc=0
        new_phase="$(jq -r --argjson i "$new_pidx" '.phases[$i]' "$m")"
        next_action="advance"; next_phase="$new_phase"
        if [ -n "$gate" ]; then human="[$cur_phase] 审通过 → 进入 [$new_phase]"
        else human="[$cur_phase] 通过 → 进入 [$new_phase]"; fi
      fi
      ;;
    needs-repair)
      new_rc=$(( rc + 1 ))
      if [ "$new_rc" -gt "$max_repair" ]; then
        new_status="blocked"; next_action="report-user"
        human="[$cur_phase] 返工已达上限 $max_repair → blocked,上报用户"
      else
        next_action="repair"; next_phase="$cur_phase"
        human="[$cur_phase] 原地返工(第 $new_rc/$max_repair 轮)"
      fi
      ;;
    needs-redirection)
      new_tc=$(( tc + 1 ))
      if [ "$new_tc" -gt "$max_turn" ]; then
        new_status="blocked"; next_action="report-user"
        human="掉头已达上限 $max_turn → blocked,上报用户"
      else
        new_pidx=0; new_rc=0; new_phase="$first_phase"
        next_action="turn-around"; next_phase="$first_phase"
        human="方向错 → 掉头回 [$first_phase](第 $new_tc/$max_turn 次)"
      fi
      ;;
    needs-context)
      new_status="waiting-user"; next_action="ask-user"; next_phase="$cur_phase"
      human="[$cur_phase] 缺输入 → 停下问用户,补齐后 resume"
      ;;
    blocked)
      new_status="blocked"; next_action="report-user"
      human="[$cur_phase] 卡住 → 上报用户(带完整经过)"
      ;;
  esac

  # 产出数组
  local produced_json="[]"
  if [ "${#produced[@]}" -gt 0 ]; then
    produced_json="$(printf '%s\n' "${produced[@]}" | jq -R . | jq -s .)"
  fi

  jq \
    --arg phase "$new_phase" --argjson pidx "$new_pidx" --argjson rc "$new_rc" \
    --argjson tc "$new_tc" --arg status "$new_status" --arg gate "$new_gate" \
    --arg hphase "$cur_phase" --arg hconc "$conclusion" --arg at "$(now)" \
    --argjson produced "$produced_json" \
    '.phase=$phase | .phase_index=$pidx | .repair_count=$rc | .turnaround_count=$tc | .status=$status
     | .gate=(if $gate=="" then null else $gate end)
     | .artifacts += $produced
     | .history += [{phase:$hphase, conclusion:$hconc, at:$at}]' \
    "$m" | write_manifest "$m"

  cat <<EOF
NEXT_ACTION=$next_action
NEXT_PHASE=$next_phase
STATUS=$new_status
EOF
  [ "$next_action" = review ] && echo "REVIEW_STAGE=$cur_phase"
  echo "$human"
}

# ---------- spinoff ----------
cmd_spinoff() {
  local tag="" finding=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --tag) tag="$2"; shift 2 ;;
      --finding) finding="$2"; shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$tag" ] || die "--tag 必填"
  [ -n "$finding" ] || die "--finding 必填"
  jq -e --arg t "$tag" '.spinoff_tags | index($t) != null' "$ROUTES" >/dev/null \
    || die "tag 非法: $tag(只能 $(jq -rc .spinoff_tags "$ROUTES"))"
  local m; m="$(manifest_path)"
  local cur_phase; cur_phase="$(jq -r .phase "$m")"
  jq --arg tag "$tag" --arg f "$finding" --arg p "$cur_phase" \
    '.subtasks += [{tag:$tag, finding:$f, from_phase:$p, status:"spun-off"}]' \
    "$m" | write_manifest "$m"
  echo "SPUN-OFF tag=$tag from=$cur_phase(已登记为关联子任务,主流程继续)"
}

# ---------- where(只读,算下一步,不推进) ----------
cmd_where() {
  local m; m="$(manifest_path)"
  local scenario phase pidx status rc tc
  scenario="$(jq -r .scenario "$m")"; phase="$(jq -r .phase "$m")"
  pidx="$(jq -r .phase_index "$m")"; status="$(jq -r .status "$m")"
  rc="$(jq -r .repair_count "$m")"; tc="$(jq -r .turnaround_count "$m")"
  local phases gate; phases="$(jq -rc '.phases' "$m")"; gate="$(jq -r '.gate // "null"' "$m")"
  cat <<EOF
scenario=$scenario
phase=$phase
phase_index=$pidx
gate=$gate
status=$status
repair_count=$rc
turnaround_count=$tc
phases=$phases
subtasks=$(jq -r '.subtasks | length' "$m")
open_items=$(jq -r '.open_items | length' "$m")
EOF
}

case "${1:-}" in
  handoff) shift; cmd_handoff "$@" ;;
  spinoff) shift; cmd_spinoff "$@" ;;
  where)   shift; cmd_where "$@" ;;
  *) die "用法: flow.sh handoff|spinoff|where ..." ;;
esac

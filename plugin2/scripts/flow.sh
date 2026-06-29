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

# 原子写 + fail-closed:验过非空且合法 JSON 才 mv,上游 jq 失败时保留原 manifest 报错退非零
# (绝不把 task.json 截成 0 字节,违"不搞静默兜底")。
write_manifest() {
  local m="$1" tmp; tmp="$(mktemp)"; cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; echo "ERROR: 拒绝写入空/非法 JSON 到 $m;原 manifest 保留" >&2; return 1
  fi
  mv "$tmp" "$m"
}

# ---------- handoff ----------
cmd_handoff() {
  local conclusion="" to_phase="" ; local -a produced=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --conclusion) conclusion="$2"; shift 2 ;;
      --produced)   produced+=("$2"); shift 2 ;;
      --to-phase)   to_phase="$2"; shift 2 ;;   # needs-redirection 回到指定上游阶段(默认首阶段)
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
        # 默认回首阶段;--to-phase 指定回上游任一开着的阶段(必须在 phases 内且不晚于当前)
        local tgt_idx=0 tgt_phase="$first_phase"
        if [ -n "$to_phase" ]; then
          tgt_idx="$(jq -r --arg p "$to_phase" '.phases | index($p) // -1' "$m")"
          [ "$tgt_idx" != "-1" ] || die "--to-phase 不在本任务 phases 内: $to_phase"
          [ "$tgt_idx" -le "$pidx" ] || die "--to-phase 必须是上游(≤当前阶段),不能往前跳: $to_phase"
          tgt_phase="$to_phase"
        fi
        new_pidx="$tgt_idx"; new_rc=0; new_phase="$tgt_phase"; new_gate=""
        next_action="turn-around"; next_phase="$tgt_phase"
        human="方向错 → 掉头回 [$tgt_phase](第 $new_tc/$max_turn 次)"
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
     | (if ($produced|length)>0 then .phase_outputs[$hphase] = ((.phase_outputs[$hphase] // []) + $produced) else . end)
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

# 找 manifest,没有不报错(冷启动用)
find_manifest() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  local m="$top/$STATE_SUBDIR/$MANIFEST_NAME"
  [ -f "$m" ] || return 1
  echo "$m"
}

# ---------- where(只读,算"你在哪 + 下一步具体干嘛",不推进) ----------
# 自带指路:冷启动枚举起始选项;在途按 phase_bindings 报 load/do/then,不靠背 SKILL。
cmd_where() {
  local m
  if ! m="$(find_manifest)"; then
    # 冷启动:不是在管任务 → 枚举起始选项(单源 routes.start_options),指向 task new
    echo "UNMANAGED"
    echo "当前不是在管任务。看需求选一个起始选项,再 mmw task new:"
    jq -r '.start_options[] | "  [\(.scenario)] \(.when) → \(.phases_note)"' "$ROUTES"
    echo "命令: mmw task new --scenario <small-change|develop|bug> --slug <YYYY-MM-DD-theme> --title \"<标题>\""
    echo "merge: 不开 worktree,直接走 references/scenario/merge.md;概念/事实问题不进 orchestrate,直接答。"
    return 0
  fi
  local scenario phase pidx status rc tc
  scenario="$(jq -r .scenario "$m")"; phase="$(jq -r .phase "$m")"
  pidx="$(jq -r .phase_index "$m")"; status="$(jq -r .status "$m")"
  rc="$(jq -r .repair_count "$m")"; tc="$(jq -r .turnaround_count "$m")"
  local phases gate prev_out reads_json; phases="$(jq -rc '.phases' "$m")"; gate="$(jq -r '.gate // "null"' "$m")"
  # 接力单:本阶段声明读哪些上游(routes phase_bindings.reads),where 照声明拼,下阶段一单读全、不自己找。
  # 没声明 → 默认读上一个开着阶段;design 这种跨两阶(查清现状 + 选定方向)的用 reads 把上游列全。
  reads_json="$(jq -rc --arg k "$phase" '.phase_bindings[$k].reads // empty' "$ROUTES")"
  if { [ "$gate" = "null" ] || [ -z "$gate" ]; } && [ -n "$reads_json" ]; then
    # 按声明序取各上游阶段产出(只取本任务 phases 里真实开着的,preset 关掉的跳过),拼成一张单
    prev_out="$(jq -rc --argjson reads "$reads_json" '. as $m
      | [ $reads[] | select($m.phases | index(.)) | ($m.phase_outputs[.] // []) ] | add // []' "$m")"
  else
    prev_out="$(jq -rc --argjson i "$pidx" 'if $i>0 then (.phase_outputs[.phases[$i-1]] // []) else [] end' "$m")"
  fi
  # 指路:gate 非空(在审闸里)用 review_gate 绑定,否则用当前阶段绑定
  local bkey="$phase"
  { [ "$gate" != "null" ] && [ -n "$gate" ]; } && bkey="review_gate"
  local b_load b_do b_prod slug
  b_load="$(jq -r --arg k "$bkey" '.phase_bindings[$k].load // "?"' "$ROUTES")"
  b_do="$(jq -r --arg k "$bkey" '.phase_bindings[$k].do // "?"' "$ROUTES")"
  b_prod="$(jq -r --arg k "$bkey" '.phase_bindings[$k].produced // ""' "$ROUTES")"
  # produced 模板里的 <slug> 用 manifest 真 slug 解析,让 then 直接可粘贴跑,不让 agent 手搓
  slug="$(jq -r '.slug' "$m")"
  b_prod="${b_prod//<slug>/$slug}"
  local then_cmd="mmw handoff --conclusion <pass|needs-repair|needs-redirection|needs-context|blocked>"
  [ -n "$b_prod" ] && then_cmd="$then_cmd --produced $b_prod"
  cat <<EOF
scenario=$scenario
phase=$phase
phase_index=$pidx
gate=$gate
status=$status
load=$b_load
do=$b_do
then=$then_cmd
prev_outputs=$prev_out
repair_count=$rc
turnaround_count=$tc
phases=$phases
phase_outputs=$(jq -rc '.phase_outputs' "$m")
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

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

# source-stability:算某阶段产物(phase_outputs[phase] 列的文件/目录)在工作树上的内容指纹。
# 过闸时记一次,where 再算一次比对——不同 = 过闸后被改,该回该阶段重审。空产物返回 "none"。
fingerprint_outputs() {  # $1=manifest $2=phase
  local m="$1" ph="$2" top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo ""; return; }
  local paths; paths="$(jq -r --arg p "$ph" '(.phase_outputs[$p] // [])[]' "$m" 2>/dev/null)"
  [ -n "$paths" ] || { echo "none"; return; }
  { while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      local abs="$top/$rel"
      if [ -f "$abs" ]; then git hash-object "$abs" 2>/dev/null
      elif [ -d "$abs" ]; then ( cd "$abs" && find . -type f ! -path '*/.git/*' | sort | while IFS= read -r f; do git hash-object "$f" 2>/dev/null; done )
      fi
    done <<< "$paths"; } | git hash-object --stdin 2>/dev/null || echo "err"
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
  local cur_step; cur_step="$(jq -r '.step_index // 0' "$m")"
  # 本阶段是不是 review-gated(routes.review_gates)
  gated=no
  jq -e --arg p "$cur_phase" '(.review_gates // {}) | has($p)' "$ROUTES" >/dev/null 2>&1 && gated=yes

  # 阶段序列读进度记录的 phases(本任务开着的阶段),不按 scenario 查 routes
  local phases_len last max_repair max_turn first_phase
  phases_len="$(jq -r '.phases | length' "$m")"
  [ "$phases_len" -gt 0 ] || die "进度记录无 phases"
  last=$(( phases_len - 1 ))
  max_repair="$(jq -r '.caps.max_repair' "$ROUTES")"
  max_turn="$(jq -r '.caps.max_turnaround' "$ROUTES")"
  first_phase="$(jq -r '.phases[0]' "$m")"

  # 交接单产出校验(fail-closed:交接靠固定单子,缺了当场拒收):
  # ① 空手 pass 拒收——routes 声明本阶段(或本审闸)有产出的,pass 必须 --produced 钉上;
  # ② 幽灵路径拒收——钉的产出必须真实存在(文件/目录),或是合法提交范围(build 的 base..HEAD)。
  if [ "$conclusion" = "pass" ] && [ "${#produced[@]}" -eq 0 ]; then
    local expected
    if [ -n "$gate" ]; then
      expected="$(jq -r --arg p "$gate" '.review_gates[$p].produced // ""' "$ROUTES")"
    else
      expected="$(jq -r --arg k "$cur_phase" '.phase_bindings[$k].produced // "" | if type=="array" then join(" ") else . end' "$ROUTES")"
    fi
    [ -z "$expected" ] || die "[$cur_phase] pass 必须钉产出(本阶段声明产 $expected);空手 pass 拒收"
  fi
  local top_wt pp
  top_wt="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
  for pp in ${produced[@]+"${produced[@]}"}; do
    if { [ -n "$top_wt" ] && [ -e "$top_wt/$pp" ]; } || [ -e "$pp" ]; then continue; fi
    case "$pp" in
      *..*) git rev-list -n 1 "$pp" >/dev/null 2>&1 && continue ;;
    esac
    die "--produced 不存在(拒收,防幽灵产出进接力单): $pp"
  done

  # 按结论算动作(引擎核心)。new_gate 默认清空;只有"进审闸"那一支把它设成当前阶段。
  # new_step 默认 0(换阶段/原地返工/掉头都从头走该阶段步序);needs-context/blocked 停在原地→保留游标,resume 续上当前步
  local new_phase="$cur_phase" new_pidx="$pidx" new_rc="$rc" new_tc="$tc" new_status="active" new_gate="" new_step=0
  local next_action next_phase="" human
  case "$conclusion" in
    pass)
      if [ -z "$gate" ] && [ "$gated" = yes ]; then
        # 阶段产物刚过、还没审:进审闸,phase 不动、不 advance,等审的 verdict 再来一次 handoff
        new_gate="$cur_phase"
        next_action="review"; next_phase="$cur_phase"
        human="[$cur_phase] 产物通过 → 进审闸(跑 mmw where 拿 review_start 直接起审),审过 handoff pass 才进下一阶段"
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
      new_status="waiting-user"; next_action="ask-user"; next_phase="$cur_phase"; new_step="$cur_step"
      human="[$cur_phase] 缺输入 → 停下问用户,补齐后 resume"
      ;;
    blocked)
      new_status="blocked"; next_action="report-user"; new_step="$cur_step"
      human="[$cur_phase] 卡住 → 上报用户(带完整经过)"
      ;;
  esac

  # 产出数组
  local produced_json="[]"
  if [ "${#produced[@]}" -gt 0 ]; then
    produced_json="$(printf '%s\n' "${produced[@]}" | jq -R . | jq -s .)"
  fi

  # source-stability:这一手是"清掉 gate 过闸"(审 verdict pass)→ 记下被审产物此刻指纹,
  # 下游 where 再算一次比对,过闸后被改就警告回审。被审产物来自上一手(进闸时)已钉的 phase_outputs。
  local fp_phase="" fp_val=""
  if [ "$conclusion" = "pass" ] && [ -n "$gate" ] && [ "$next_action" = "advance" ]; then
    fp_phase="$cur_phase"; fp_val="$(fingerprint_outputs "$m" "$cur_phase")"
  fi

  jq \
    --arg phase "$new_phase" --argjson pidx "$new_pidx" --argjson rc "$new_rc" \
    --argjson tc "$new_tc" --arg status "$new_status" --arg gate "$new_gate" \
    --arg hphase "$cur_phase" --arg hconc "$conclusion" --arg at "$(now)" \
    --argjson produced "$produced_json" --argjson nstep "$new_step" \
    --arg fpphase "$fp_phase" --arg fpval "$fp_val" \
    '.phase=$phase | .phase_index=$pidx | .repair_count=$rc | .turnaround_count=$tc | .status=$status
     | .gate=(if $gate=="" then null else $gate end)
     | .step_index=$nstep
     | .artifacts += $produced
     | (if ($produced|length)>0 then .phase_outputs[$hphase] = ((.phase_outputs[$hphase] // []) + $produced) else . end)
     | (if $fpphase!="" then .gate_fingerprints[$fpphase]=$fpval else . end)
     | .history += [{phase:$hphase, conclusion:$hconc, at:$at}]' \
    "$m" | write_manifest "$m"

  # loop 生命周期:结论落定 = 当前内层 loop(若有)收束——清 loop-state(schema「退出时清」的落地),
  # 防上一个 loop 的残留污染下阶段 where。往前(pass)/返工(needs-repair)/掉头(needs-redirection)都清;
  # needs-context/blocked 是原地等 resume,保留 loop 现场不清。新 loop 由下阶段 init 重建。
  case "$conclusion" in
    pass|needs-repair|needs-redirection) bash "$SCRIPT_DIR/loop.sh" close >/dev/null ;;
  esac

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
  local b_load b_do slug
  b_load="$(jq -r --arg k "$bkey" '.phase_bindings[$k].load // "?"' "$ROUTES")"
  # 按 scenario 选阶段 load(build 的就地TDD vs 派Codex 是确定分叉 → 脚本直接给对的那份,
  # 不让 agent 读散文自己挑;非 build 阶段无 load_by_scenario,回落到默认 load)。
  local b_load_scen
  b_load_scen="$(jq -r --arg k "$bkey" --arg s "$scenario" '.phase_bindings[$k].load_by_scenario[$s] // empty' "$ROUTES")"
  [ -n "$b_load_scen" ] && b_load="$b_load_scen"
  b_do="$(jq -r --arg k "$bkey" '.phase_bindings[$k].do // "?"' "$ROUTES")"
  slug="$(jq -r '.slug' "$m")"

  # 阶段内步骤游标:phase(不在审闸)有 steps 时,where 只报当前那一步的 load/do——
  # 到那步才加载那一份干净文档,导航走脚本(mmw step next),不在 reference 里文字跳转、不 upfront 全load。
  local step_total=0 step_idx=0 step_id="" step_line=""
  if [ "$bkey" = "$phase" ]; then
    step_total="$(jq -r --arg k "$phase" '(.phase_bindings[$k].steps // []) | length' "$ROUTES")"
  fi
  if [ "$step_total" -gt 0 ]; then
    step_idx="$(jq -r '.step_index // 0' "$m")"
    [ "$step_idx" -lt 0 ] && step_idx=0
    [ "$step_idx" -ge "$step_total" ] && step_idx=$(( step_total - 1 ))
    step_id="$(jq -r --arg k "$phase" --argjson i "$step_idx" '.phase_bindings[$k].steps[$i].id' "$ROUTES")"
    b_load="$(jq -r --arg k "$phase" --argjson i "$step_idx" '.phase_bindings[$k].steps[$i].load' "$ROUTES")"
    b_do="$(jq -r --arg k "$phase" --argjson i "$step_idx" '.phase_bindings[$k].steps[$i].do' "$ROUTES")"
    step_line="step=$step_id ($(( step_idx + 1 ))/$step_total)
step_note=断点回来时:本步产物若已完成,核一眼直接 mmw step next,别重做"
  fi

  # then:有步骤且未到末步 → 推进到下一步走脚本;否则(末步或无步骤)→ 阶段 handoff 钉产物。
  # produced 可为字符串(单产物)或数组,逐个吐,解析 <slug> 用真 slug,then 直接可粘贴跑、钉全、不让 agent 手搓/漏钉。
  local then_cmd
  if [ "$step_total" -gt 0 ] && [ "$step_idx" -lt $(( step_total - 1 )) ]; then
    then_cmd="mmw step next   # 本步干完推进下一步(下一步 load 那时现读)"
  else
    then_cmd="mmw handoff --conclusion <pass|needs-repair|needs-redirection|needs-context|blocked>"
    # 产物源:在审闸里取 review_gates[gate].produced(审闸该钉啥由 map 定,如 build 闸钉终审报告);
    # 否则取当前阶段绑定的 produced。审是闸不产文件的(design/plan)→ produced 空,不带 --produced。
    local produced_src
    if { [ "$gate" != "null" ] && [ -n "$gate" ]; }; then
      produced_src="$(jq -r --arg p "$gate" '.review_gates[$p].produced // ""' "$ROUTES")"
    else
      produced_src="$(jq -r --arg k "$bkey" '.phase_bindings[$k].produced // "" | if type=="array" then .[] else . end' "$ROUTES")"
    fi
    local p
    while IFS= read -r p; do
      [ -n "$p" ] || continue
      p="${p//<slug>/$slug}"
      then_cmd="$then_cmd --produced $p"
    done <<< "$produced_src"
  fi
  # 审闸里:stage 由 review_gates[gate].stage 定(design→design / plan→plan / build→final),
  # where 直接吐确切的 review_start 命令 + review_source,agent 照跑不靠散文猜哪个 stage。
  local review_line="" review_start_line=""
  if [ "$gate" != "null" ] && [ -n "$gate" ]; then
    local g_stage g_source
    g_stage="$(jq -r --arg p "$gate" '.review_gates[$p].stage // "?"' "$ROUTES")"
    # 吐裸路径喂 review start --source(不吐 JSON 数组,省 agent 拆 ["x"]→x);多产物空格连
    g_source="$(jq -r --arg p "$phase" '(.phase_outputs[$p] // []) | join(" ")' "$m")"
    review_line="review_source=$g_source"
    review_start_line="review_start=mmw review start --stage $g_stage --source $g_source"
  fi
  cat <<EOF
scenario=$scenario
phase=$phase
phase_index=$pidx
${step_line:+$step_line
}gate=$gate
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
  if [ -n "$review_line" ]; then echo "$review_line"; fi
  if [ -n "$review_start_line" ]; then echo "$review_start_line"; fi

  # 内层 loop 可见性:有 loop-state = 正在某内层 loop(execution 落地 / review 审 / contract-gate 合同门)。
  # 断点恢复靠 where —— 报 loop 种类、进度(借 loop.sh exit-check,单源不重算)、该读哪份(routes.loop_bindings)。
  # loop-state 由 handoff 结论落定时清(loop close),文件在 = loop 真活着,不是上阶段残留。
  local top loopf
  top="${m%/$STATE_SUBDIR/$MANIFEST_NAME}"
  loopf="$top/$STATE_SUBDIR/loop-state.json"
  if [ -f "$loopf" ]; then
    local lkind lstate lload
    lkind="$(jq -r '.kind // "?"' "$loopf" 2>/dev/null || echo "?")"
    lstate="$(cd "$top" && bash "$SCRIPT_DIR/loop.sh" exit-check 2>/dev/null || echo "?")"
    # 内层文档:loop_bindings 只列'与阶段 load 不同'的(contract-gate→plan-impl.md);
    # execution/review 回落到阶段 load(build-a/b 随 scenario、审 review.md),不重复配。
    lload="$(jq -r --arg k "$lkind" '.loop_bindings[$k].load // empty' "$ROUTES")"
    [ -n "$lload" ] || lload="$b_load"
    echo "inner_loop=$lkind"
    echo "inner_loop_state=$lstate"
    echo "inner_loop_load=$lload"
  fi

  # source-stability:已过闸的 gated 阶段,产物指纹和当下不一致 = 过闸后被改 → 提示回审
  local stale=""
  while IFS= read -r gphase; do
    [ -n "$gphase" ] || continue
    local stored cur_fp
    stored="$(jq -r --arg p "$gphase" '.gate_fingerprints[$p] // ""' "$m")"
    [ -n "$stored" ] || continue
    cur_fp="$(fingerprint_outputs "$m" "$gphase")"
    [ "$cur_fp" = "$stored" ] || stale="$stale $gphase"
  done < <(jq -r '(.gate_fingerprints // {}) | keys[]' "$m" 2>/dev/null)
  if [ -n "$stale" ]; then
    echo "stale_gate=${stale# }  # 这些阶段产物过闸后被改了,回 mmw handoff --conclusion needs-redirection --to-phase <阶段> 重审"
  fi
}

# ---------- step(阶段内步骤游标:推进到下一步,报那一步的 load/do) ----------
# 阶段有 steps 时,agent 干完当前步调 step next:游标 +1、报下一步要读哪份/干什么(到那步才加载)。
cmd_step() {
  local verb="${1:-}"; shift || true
  [ "$verb" = "next" ] || die "用法: mmw step next"
  local m; m="$(manifest_path)"
  [ -f "$ROUTES" ] || die "找不到 routes.json: $ROUTES"
  local phase gate total idx
  phase="$(jq -r .phase "$m")"
  gate="$(jq -r '.gate // empty' "$m")"
  [ -z "$gate" ] || die "审闸里不走阶段步骤;审完 mmw handoff 报 verdict"
  total="$(jq -r --arg k "$phase" '(.phase_bindings[$k].steps // []) | length' "$ROUTES")"
  [ "$total" -gt 0 ] || die "[$phase] 阶段无步骤,直接 mmw handoff"
  idx="$(jq -r '.step_index // 0' "$m")"
  local nidx=$(( idx + 1 ))
  if [ "$nidx" -ge "$total" ]; then
    echo "STEPS_DONE [$phase] 步骤走完 → mmw handoff(产物钉法见 mmw where 的 then)"
    return 0
  fi
  jq --argjson i "$nidx" '.step_index=$i' "$m" | write_manifest "$m"
  local sid sload sdo
  sid="$(jq -r --arg k "$phase" --argjson i "$nidx" '.phase_bindings[$k].steps[$i].id' "$ROUTES")"
  sload="$(jq -r --arg k "$phase" --argjson i "$nidx" '.phase_bindings[$k].steps[$i].load' "$ROUTES")"
  sdo="$(jq -r --arg k "$phase" --argjson i "$nidx" '.phase_bindings[$k].steps[$i].do' "$ROUTES")"
  cat <<EOF
step=$sid ($(( nidx + 1 ))/$total)
load=$sload
do=$sdo
EOF
  if [ "$nidx" -lt $(( total - 1 )) ]; then echo "then=mmw step next"
  else echo "then=mmw handoff --conclusion <...>(产物钉法见 mmw where 的 then)"; fi
}

case "${1:-}" in
  handoff)         shift; cmd_handoff "$@" ;;
  spinoff)         shift; cmd_spinoff "$@" ;;
  where)           shift; cmd_where "$@" ;;
  step)            shift; cmd_step "$@" ;;
  *) die "用法: flow.sh handoff|spinoff|where|step ..." ;;
esac

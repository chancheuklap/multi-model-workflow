#!/usr/bin/env bash
# flow.sh —— 推进引擎(书记员+工长:登记、指路、算下一步;不否决判断)
#
#   handoff   阶段/帮手干完调它:记交接单(产出+结论)→ 按结论算动作 → 写进度档 → 回"下一步"
#   pin       补钉产出到当前阶段接力单(只登记,不推进;handoff 漏钉/产物后到用它补)
#   spinoff   阶段中途挖到 bug/旁路优化:登记成关联子任务,主流程不动,不盲目 out-of-scope
#   where     不推进,只算"你在哪、下一步什么"(给断点恢复用)
#
# 结论词是统一一套(routes.json conclusions)。选哪个结论是 LLM 判断;登记和推进是本脚本做。
# 机器否决权只认白名单事实(见 guard-redline/approve);判断层问题一律警告留痕,不拒收。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
ROUTES="$SCRIPT_DIR/../state-schema/routes.json"
MANIFEST_NAME="task.json"
# 回执里的命令一律吐完整可执行形式(agent 直接粘贴跑,不用自己把 mmw 别名展开成路径)
MMW="bash \"$SCRIPT_DIR/mmw.sh\""

die() { echo "ERROR: $*" >&2; exit 1; }
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }

manifest_path() {
  local top sd; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  sd="$(mmw_resolve_state_subdir "$top")"
  local m="$top/$sd/$MANIFEST_NAME"
  [ -f "$m" ] || die "当前不是在管任务(无 task.json),先回入口走路由/准备"
  echo "$m"
}

# 原子写 + fail-closed:验过非空且合法 JSON 才 mv,上游 jq 失败时保留原 manifest 报错退非零
# (绝不把 task.json 截成 0 字节)。每次落盘刷 updated_at(状态新鲜度戳)。
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

# 白名单第 4 条:设计确认后被改 → 不许拿着走样的设计继续执行。
# 返回 0=一致或无确认;返回 1 时输出不一致详情。指纹算法单源在 note.sh fingerprint。
approval_check() {  # $1=manifest
  local m="$1"
  jq -e '.approval' "$m" >/dev/null 2>&1 || return 0
  local fp_stored fp_now
  fp_stored="$(jq -r '.approval.fingerprint' "$m")"
  local -a args=()
  local r
  while IFS= read -r r; do [ -n "$r" ] && args+=(--report "$r"); done \
    < <(jq -r '.approval.reports[]' "$m")
  [ "${#args[@]}" -gt 0 ] || return 0
  fp_now="$(bash "$SCRIPT_DIR/note.sh" fingerprint "${args[@]}" 2>/dev/null || echo "err")"
  [ "$fp_now" = "$fp_stored" ] && return 0
  echo "设计承重文档在用户确认后被改($(jq -rc '.approval.reports' "$m"));请用户重新过目并 /approve-design 重盖指纹,或把改动回退"
  return 1
}

# ---------- handoff ----------
cmd_handoff() {
  local conclusion="" to_phase="" ; local -a produced=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --conclusion) conclusion="$2"; shift 2 ;;
      --produced)   produced+=("$2"); shift 2 ;;
      --to-phase)   to_phase="$2"; shift 2 ;;   # needs-redirection 回到指定上游阶段(默认上一阶段)
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$conclusion" ] || die "--conclusion 必填(引擎要靠它算下一步)"
  [ -f "$ROUTES" ] || die "找不到 routes.json: $ROUTES"

  # 结论词是引擎的输入枚举(CLI 参数校验,不是判断审查):词不在表里引擎算不了下一步
  jq -e --arg c "$conclusion" '.conclusions | index($c) != null' "$ROUTES" >/dev/null \
    || die "结论词不认识: $conclusion(可用 $(jq -rc .conclusions "$ROUTES"))"

  local m; m="$(manifest_path)"
  local cur_phase pidx rc tc gate gated slug
  cur_phase="$(jq -r .phase "$m")"
  pidx="$(jq -r .phase_index "$m")"
  rc="$(jq -r .repair_count "$m")"
  tc="$(jq -r .turnaround_count "$m")"
  gate="$(jq -r '.gate // empty' "$m")"   # "" = 不在审闸;非空 = 正在该阶段审 loop 里
  slug="$(jq -r .slug "$m")"
  # 本阶段是不是 review-gated(routes.review_gates)
  gated=no
  jq -e --arg p "$cur_phase" '(.review_gates // {}) | has($p)' "$ROUTES" >/dev/null 2>&1 && gated=yes

  # 阶段序列读进度记录的 phases(本任务开着的阶段),不按 scenario 查 routes
  local phases_len last first_phase
  phases_len="$(jq -r '.phases | length' "$m")"
  [ "$phases_len" -gt 0 ] || die "进度记录无 phases"
  last=$(( phases_len - 1 ))
  first_phase="$(jq -r '.phases[0]' "$m")"

  # 产出登记检查:只警告留痕,不拒收(判断是 agent 的;引擎把缺口摆到明面)
  local -a warns=()
  if [ "$conclusion" = "pass" ] && [ "${#produced[@]}" -eq 0 ]; then
    local expected
    if [ -n "$gate" ]; then
      expected="$(jq -r --arg p "$gate" '.review_gates[$p].produced // ""' "$ROUTES")"
    else
      expected="$(jq -r --arg k "$cur_phase" '.phase_bindings[$k].produced // "" | if type=="array" then join(" ") else . end' "$ROUTES")"
    fi
    [ -z "$expected" ] || warns+=("[$cur_phase] 本阶段声明产 $expected 但没钉;下阶段接力单会缺——补:$MMW pin --produced <路径>")
  fi
  # 幽灵路径不进接力单(接力单里的路径必须真实),但只提醒补钉,不拒收结论
  local top_wt pp; local -a pinned=()
  top_wt="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
  for pp in ${produced[@]+"${produced[@]}"}; do
    if { [ -n "$top_wt" ] && [ -e "$top_wt/$pp" ]; } || [ -e "$pp" ]; then pinned+=("$pp"); continue; fi
    case "$pp" in
      *..*) git rev-list -n 1 "$pp" >/dev/null 2>&1 && { pinned+=("$pp"); continue; } ;;
    esac
    warns+=("--produced 路径不存在,未进接力单: $pp(产物就绪后 $MMW pin --produced <路径> 补钉)")
  done

  # 审闸收口的唯一产物级硬核(白名单「写者≠审者」的证据面):
  # 审 verdict=pass 必须有落盘的审查留痕(docs/reviews/<slug>-<stage>.md 存在且含 verdict)。
  # 报告在=审真跑过;质量与 Critical 处置是判断,不机器核。merge-impl 在主仓库另有留痕路径,不经此闸。
  if [ "$conclusion" = "pass" ] && [ -n "$gate" ]; then
    local g_stage trace
    g_stage="$(jq -r --arg p "$gate" '.review_gates[$p].stage // ""' "$ROUTES")"
    trace="$top_wt/docs/reviews/$slug-$g_stage.md"
    if [ ! -f "$trace" ]; then
      die "[$gate 审闸] 找不到审查留痕 $trace;先按 review-brief 派审者、findings 落盘并写 verdict 段再收口(报告在=审真跑过,这是写者≠审者的证据面)"
    fi
    grep -qi 'verdict' "$trace" \
      || die "[$gate 审闸] 审查留痕 $trace 无 verdict 段;亲验 findings 后把每条处置与总 verdict 写进去再收口"
  fi

  # 白名单第 4 条:过门后的推进(pass)前核设计确认指纹;不符 → 硬停交用户
  if [ "$conclusion" = "pass" ]; then
    local ap_msg
    if ! ap_msg="$(approval_check "$m")"; then
      die "$ap_msg"
    fi
  fi

  # package 出包闸(release 子系统,机器核 release state;不属账本类,保留):
  # 无 Windows 包目标时 exit-check 即 DONE,正常放行。
  if [ "$conclusion" = "pass" ] && [ -z "$gate" ] && [ "$cur_phase" = "package" ]; then
    local package_result
    package_result="$(bash "$SCRIPT_DIR/package-phase.sh" exit-check)" \
      || die "[package] 不能交接到 closing: $package_result"
    [ "$package_result" = "DONE" ] \
      || die "[package] 不能交接到 closing: $package_result"
  fi

  # 按结论算动作(引擎核心)。new_gate 默认清空;只有"进审闸"那一支把它设成当前阶段。
  # new_step 默认 0;needs-context/blocked 停在原地→保留游标,resume 续上当前步
  local cur_step; cur_step="$(jq -r '.step_index // 0' "$m")"
  local new_phase="$cur_phase" new_pidx="$pidx" new_rc="$rc" new_tc="$tc" new_status="active" new_gate="" new_step=0
  local next_action next_phase="" human prune_from=-1
  case "$conclusion" in
    pass)
      if [ -z "$gate" ] && [ "$gated" = yes ]; then
        # 阶段产物刚过、还没审:进审闸,phase 不动、不 advance,等审的 verdict 再来一次 handoff
        new_gate="$cur_phase"
        next_action="review"; next_phase="$cur_phase"
        human="[$cur_phase] 产物通过 → 进审闸(跑 mmw where 拿 review_start 直接起审),审过 handoff pass 才进下一阶段"
      elif [ "$pidx" -ge "$last" ]; then
        new_status="ready-to-close"; next_action="done"; next_phase=""
        human="末阶段 [$cur_phase] 通过 → 待收尾(回主仓库 prepare.sh cleanup)"
      else
        new_pidx=$(( pidx + 1 )); new_rc=0
        new_phase="$(jq -r --argjson i "$new_pidx" '.phases[$i]' "$m")"
        next_action="advance"; next_phase="$new_phase"
        if [ -n "$gate" ]; then human="[$cur_phase] 审通过 → 进入 [$new_phase]"
        else human="[$cur_phase] 通过 → 进入 [$new_phase]"; fi
      fi
      ;;
    needs-repair)
      new_rc=$(( rc + 1 ))
      next_action="repair"; next_phase="$cur_phase"
      human="[$cur_phase] 原地返工(第 $new_rc 轮)"
      if [ "$new_rc" -ge 3 ]; then
        warns+=("[$cur_phase] 已返工 $new_rc 轮:每轮向用户汇报卡点/根因/下一步再继续,持续打转要主动交人")
      fi
      ;;
    needs-redirection)
      new_tc=$(( tc + 1 ))
      # 默认回上一阶段(不是首阶段);--to-phase 指定回上游任一开着的阶段
      local tgt_idx tgt_phase
      if [ -n "$to_phase" ]; then
        tgt_idx="$(jq -r --arg p "$to_phase" '.phases | index($p) // -1' "$m")"
        [ "$tgt_idx" != "-1" ] || die "--to-phase 不在本任务 phases 内: $to_phase(本任务无该阶段;bug/小改要补设计走 $MMW task escalate --to develop)"
        [ "$tgt_idx" -le "$pidx" ] || die "--to-phase 必须是上游(≤当前阶段),不能往前跳: $to_phase"
        tgt_phase="$to_phase"
      else
        tgt_idx=$(( pidx > 0 ? pidx - 1 : 0 ))
        tgt_phase="$(jq -r --argjson i "$tgt_idx" '.phases[$i]' "$m")"
      fi
      new_pidx="$tgt_idx"; new_rc=0; new_phase="$tgt_phase"; new_gate=""
      next_action="turn-around"; next_phase="$tgt_phase"
      prune_from=$(( tgt_idx + 1 ))   # 回拨后下游阶段的接力单产出已过期,剪掉(文件仍在盘上)
      human="方向错 → 掉头回 [$tgt_phase](第 $new_tc 次)"
      if [ "$new_tc" -ge 2 ]; then
        warns+=("已掉头 $new_tc 次:先向用户讲清楚这次为什么又要回头,再继续")
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

  # 产出数组(只收真实存在的)
  local produced_json="[]"
  if [ "${#pinned[@]}" -gt 0 ]; then
    produced_json="$(printf '%s\n' "${pinned[@]}" | jq -R . | jq -s .)"
  fi

  jq \
    --arg phase "$new_phase" --argjson pidx "$new_pidx" --argjson rc "$new_rc" \
    --argjson tc "$new_tc" --arg status "$new_status" --arg gate "$new_gate" \
    --arg hphase "$cur_phase" --arg hconc "$conclusion" --arg at "$(now)" \
    --argjson produced "$produced_json" --argjson nstep "$new_step" \
    --argjson prune_from "$prune_from" \
    '.phase=$phase | .phase_index=$pidx | .repair_count=$rc | .turnaround_count=$tc | .status=$status
     | .gate=(if $gate=="" then null else $gate end)
     | .step_index=$nstep
     | .artifacts += $produced
     | (if ($produced|length)>0 then .phase_outputs[$hphase] = (((.phase_outputs[$hphase] // []) + $produced) | unique) else . end)
     | (if $prune_from >= 0 then
          (.phases[$prune_from:] // []) as $downstream
          | .phase_outputs = (.phase_outputs | with_entries(select(.key as $k | ($downstream | index($k)) | not)))
        else . end)
     | .history += [{phase:$hphase, conclusion:$hconc, at:$at}]' \
    "$m" | write_manifest "$m"

  if [ "$cur_phase" = "package" ] && [ "$conclusion" = "needs-redirection" ] && [ "$to_phase" = "build" ]; then
    bash "$SCRIPT_DIR/package-phase.sh" close >/dev/null
  fi

  # 执行账本生命周期:结论落定 = 本阶段执行账本(若有)收束。
  # needs-context/blocked 是原地等 resume,保留现场不清。
  case "$conclusion" in
    pass|needs-repair|needs-redirection) bash "$SCRIPT_DIR/loop.sh" close >/dev/null ;;
  esac

  cat <<EOF
NEXT_ACTION=$next_action
NEXT_PHASE=$next_phase
STATUS=$new_status
EOF
  [ "$next_action" = review ] && echo "REVIEW_STAGE=$cur_phase"
  local w
  for w in ${warns[@]+"${warns[@]}"}; do echo "WARN=$w"; done
  echo "$human"
}

# ---------- pin(补钉产出:只登记,不推进) ----------
cmd_pin() {
  local -a produced=()
  local to_phase=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --produced) produced+=("$2"); shift 2 ;;
      --phase)    to_phase="$2"; shift 2 ;;   # 默认钉当前阶段;可指定已开阶段(如刚 advance 完补上一阶段)
      *) die "未知参数: $1" ;;
    esac
  done
  [ "${#produced[@]}" -gt 0 ] || die "--produced 必填(可重复)"
  local m; m="$(manifest_path)"
  local phase; phase="${to_phase:-$(jq -r .phase "$m")}"
  jq -e --arg p "$phase" '.phases | index($p) != null' "$m" >/dev/null || die "--phase 不在本任务 phases 内: $phase"
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null || echo "")"
  local pp; local -a ok=()
  for pp in "${produced[@]}"; do
    if { [ -n "$top" ] && [ -e "$top/$pp" ]; } || [ -e "$pp" ]; then ok+=("$pp"); continue; fi
    case "$pp" in *..*) git rev-list -n 1 "$pp" >/dev/null 2>&1 && { ok+=("$pp"); continue; } ;; esac
    die "路径不存在,拒绝钉幽灵产出: $pp"
  done
  local produced_json; produced_json="$(printf '%s\n' "${ok[@]}" | jq -R . | jq -s .)"
  jq --arg p "$phase" --argjson produced "$produced_json" \
    '.artifacts += $produced
     | .phase_outputs[$p] = (((.phase_outputs[$p] // []) + $produced) | unique)' \
    "$m" | write_manifest "$m"
  echo "PINNED phase=$phase produced=$(printf '%s ' "${ok[@]}")"
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

# 找 manifest,没有不报错(冷启动用);跨宿主解析真实状态平面
find_manifest() {
  local top sd; top="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  sd="$(mmw_resolve_state_subdir "$top")"
  local m="$top/$sd/$MANIFEST_NAME"
  [ -f "$m" ] || return 1
  echo "$m"
}

# 状态新鲜度(白名单第 3 条:旧状态先对表再采信):版本不符或超 7 天没动 → 提示先 /reassess
freshness_lines() {  # $1=manifest
  local m="$1"
  local cur_ver man_ver upd
  cur_ver="$(jq -r '.version // ""' "$SCRIPT_DIR/../.factory-plugin/plugin.json" 2>/dev/null || echo "")"
  man_ver="$(jq -r '.plugin_version // ""' "$m")"
  upd="$(jq -r '.updated_at // .created_at // ""' "$m")"
  if [ -n "$man_ver" ] && [ -n "$cur_ver" ] && [ "$man_ver" != "$cur_ver" ]; then
    echo "stale_version=$man_ver(当前 plugin $cur_ver;状态由旧版写入,先 /reassess 从磁盘对表再续,别把旧指令当最新)"
  fi
  if [ -n "$upd" ]; then
    local then_s now_s age_d
    then_s="$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$upd" +%s 2>/dev/null || date -u -d "$upd" +%s 2>/dev/null || echo "")"
    now_s="$(date -u +%s)"
    if [ -n "$then_s" ]; then
      age_d=$(( (now_s - then_s) / 86400 ))
      if [ "$age_d" -ge 7 ]; then echo "stale_age=${age_d}d(超 7 天没动;先 /reassess 重建真相再续)"; fi
    fi
  fi
  return 0
}

# ---------- where(只读,算"你在哪 + 下一步具体干嘛",不推进) ----------
cmd_where() {
  local m
  if ! m="$(find_manifest)"; then
    # Droid 会把已有 linked worktree 的启动 cwd 归一化到主仓库;先从主仓库扫描在飞任务。
    local top_ls mm
    local flying=()
    if top_ls="$(git rev-parse --show-toplevel 2>/dev/null)"; then
      while IFS= read -r mm; do
        [ -f "$mm" ] || continue
        flying+=("$mm")
      done < <(mmw_foreach_flying_manifest "$top_ls")
    fi

    if [ "${#flying[@]}" -gt 0 ]; then
      echo "RESUMABLE"
      echo "当前主仓库有在飞任务。按用户意图选择续跑或新建:"
      echo "在飞任务(全量视图: $MMW task team):"
      for mm in ${flying[@]+"${flying[@]}"}; do
        jq -r --arg mmw "$MMW" '
          "  - \(.slug)  [\(.scenario)] phase=\(.phase) status=\(.status)  path=\(.worktree_path)",
          "    resume=cd \(.worktree_path | @sh) && \($mmw) where"
        ' "$mm" 2>/dev/null || true
      done
      echo "用户明确要新建任务时,再选下面的起始选项:"
    else
      echo "UNMANAGED"
      echo "当前没有在管任务。看需求选一个起始选项:"
    fi
    jq -r '.start_options[] | "  [\(.scenario)] \(.when) → \(.phases_note)"' "$ROUTES"
    echo "命令: $MMW task new --scenario <small-change|develop|bug> --slug <YYYY-MM-DD-theme> --title '<标题>' --request '<用户原始需求与验收条件>' [--direction-given]"
    echo "问答、解释、只读查看，以及主线程可直接完成并验证的琐碎单步动作不进 orchestrate，直接处理。merge 不开 worktree，直接走 references/scenario/merge.md。"
    return 0
  fi
  local scenario phase pidx status rc tc
  scenario="$(jq -r .scenario "$m")"; phase="$(jq -r .phase "$m")"
  pidx="$(jq -r .phase_index "$m")"; status="$(jq -r .status "$m")"
  rc="$(jq -r .repair_count "$m")"; tc="$(jq -r .turnaround_count "$m")"
  local phases gate prev_out reads_json; phases="$(jq -rc '.phases' "$m")"; gate="$(jq -r '.gate // "null"' "$m")"
  # 接力单:本阶段声明读哪些上游(routes phase_bindings.reads),where 照声明拼,下阶段一单读全、不自己找。
  reads_json="$(jq -rc --arg k "$phase" '.phase_bindings[$k].reads // empty' "$ROUTES")"
  if { [ "$gate" = "null" ] || [ -z "$gate" ]; } && [ -n "$reads_json" ]; then
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
  local b_load_scen
  b_load_scen="$(jq -r --arg k "$bkey" --arg s "$scenario" '.phase_bindings[$k].load_by_scenario[$s] // empty' "$ROUTES")"
  [ -n "$b_load_scen" ] && b_load="$b_load_scen"
  b_do="$(jq -r --arg k "$bkey" '.phase_bindings[$k].do // "?"' "$ROUTES")"
  # propose 分叉:用户开口已带明确方向(task new --direction-given 钉进 manifest)→ 降级
  if [ "$bkey" = "propose" ] && [ "$(jq -r '.direction_given // false' "$m")" = "true" ]; then
    b_do="方向已由用户明示(direction_given):读现状报告,落方向文档(选定方向+为什么+一个最强对照一句),向用户确认一句;不重摆 2-3 方案"
  fi
  slug="$(jq -r '.slug' "$m")"

  # then:阶段 handoff 钉产物。produced 可为字符串或数组,逐个吐,解析 <slug> 用真 slug。
  local then_cmd
  then_cmd="$MMW handoff --conclusion <pass|needs-repair|needs-redirection|needs-context|blocked>"
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
  # 审闸里:stage 由 review_gates[gate].stage 定,where 直接吐确切的 review_start 命令 + review_source
  local review_line="" review_start_line="" review_trace_line=""
  if [ "$gate" != "null" ] && [ -n "$gate" ]; then
    local g_stage g_source src_args="" srcp
    g_stage="$(jq -r --arg p "$gate" '.review_gates[$p].stage // "?"' "$ROUTES")"
    g_source="$(jq -r --arg p "$phase" '(.phase_outputs[$p] // []) | join(" ")' "$m")"
    while IFS= read -r srcp; do
      [ -n "$srcp" ] || continue
      src_args="$src_args --source $srcp"
    done < <(jq -r --arg p "$phase" '(.phase_outputs[$p] // [])[]' "$m")
    review_line="review_source=$g_source"
    review_start_line="review_start=$MMW review start --stage ${g_stage}$src_args"
    review_trace_line="review_trace=docs/reviews/$slug-$g_stage.md  # 收口 pass 前 findings+verdict 落这里(硬核:文件在且含 verdict)"
  fi
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
  if [ -n "$review_line" ]; then echo "$review_line"; fi
  if [ -n "$review_start_line" ]; then echo "$review_start_line"; fi
  if [ -n "$review_trace_line" ]; then echo "$review_trace_line"; fi

  # 执行账本可见性(只报,不当闸):有 loop-state = build 落地账本在,报完成度与 pause
  local top sd_here loopf
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || top=""
  sd_here="$(mmw_resolve_state_subdir "$top")"
  loopf="$top/$sd_here/loop-state.json"
  if [ -f "$loopf" ]; then
    local lstate
    lstate="$(cd "$top" && bash "$SCRIPT_DIR/loop.sh" status 2>/dev/null || echo "?")"
    echo "inner_loop=execution"
    echo "inner_loop_state=$lstate"
  fi

  # 白名单第 4 条:确认过的设计被改 → 提前亮出来(handoff pass 会硬停)
  local ap_msg
  if ! ap_msg="$(approval_check "$m")"; then
    echo "approval_stale=$ap_msg"
  fi

  # 状态新鲜度(白名单第 3 条)
  freshness_lines "$m"
}

case "${1:-}" in
  handoff)         shift; cmd_handoff "$@" ;;
  pin)             shift; cmd_pin "$@" ;;
  spinoff)         shift; cmd_spinoff "$@" ;;
  where)           shift; cmd_where "$@" ;;
  *) die "用法: flow.sh handoff|pin|spinoff|where ..." ;;
esac

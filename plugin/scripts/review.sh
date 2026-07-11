#!/usr/bin/env bash
# review.sh —— 审闸一条命令(把"起一道审"的机械 6 步收成 1 步)
#
#   start --stage <design|plan|plan-impl|final|merge-impl> --source <源意图路径/描述>
#       按阶段映射 kind + 视角,init loop-state,把审派发指南写进状态目录文件 review-brief.md
#       (主线程读它**直接派审者**——拍平,不再派协调帮手中间层)。
#       审者读已装的 worktree-review skill(方法本体单源在那,不给审者 plugin 内路径)。
#       ④final 按 scenario 分档:develop = 双模型 2×2;small-change/bug = 1×Codex 一肩挑两视角(diff 小)。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/host.sh
. "$SCRIPT_DIR/lib/host.sh"
LOOP="$SCRIPT_DIR/loop.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""   # 打印给主线程的命令,完整可执行形式
# 当前目录真实状态平面(跨宿主续跑)
state_here() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  mmw_resolve_state_subdir "$top"
}
# 审 = 高判断,审者跑高档;可 env 覆盖。
# Codex 审者(外部 agent)走 codex exec 无头,模型/档在这里钉;
# Claude 审者走会话内 sub-agent(agents/code-reviewer.md),模型/档在该 agent frontmatter 钉——
# 不用 claude -p 无头(那是另起进程另外计费,本会话已在 Claude Code CLI 里)。
CODEX_REVIEW_MODEL="${CODEX_REVIEW_MODEL:-gpt-5.6-sol}"
CODEX_REVIEW_EFFORT="${CODEX_REVIEW_EFFORT:-xhigh}"

die() { echo "ERROR: $*" >&2; exit 1; }

# Droid 宿主:把 brief 里的 codex/claude CLI 派发改写成 Task + reviewer-* droids
# $5=tier(final 用: 1|2|4; 其它 stage 可传 0)
overlay_droid_brief_if_needed() {
  local brief="$1" stage="$2" scen="$3" source="$4" tier="${5:-0}"
  [ "$(mmw_host)" = "droid" ] || return 0
  # Droid 审者读 plugin 内随插件发布的 worktree-review skill(绝对路径,不赌子代理自动加载 skill)
  local skill; skill="$(mmw_plugin_root)/skills/worktree-review"
  local dispatch=""
  case "$stage" in
    design)
      dispatch="用 Task 并行派 2 个 Custom Droids(干净 context · 写者≠验者,模型钉在 droid 文件):
  - subagent_type=reviewer-design-a · 轴A 设计内容
  - subagent_type=reviewer-design-b · 轴B 项目对齐
每个 prompt:读 plugin 内 worktree-review skill(${skill}/SKILL.md),按 stage=design;你负责 <轴A|轴B>;Source: ${source};按 Return Contract 回 findings。"
      ;;
    plan)
      dispatch="用 Task 并行派 2 个 Custom Droids:
  - subagent_type=reviewer-plan-a · 轴A 覆盖与质量
  - subagent_type=reviewer-plan-b · 轴B 合规与交叉验证
prompt:读 plugin 内 worktree-review skill(${skill}/SKILL.md),按 stage=plan;你负责 <轴A|轴B>;Source: ${source}。"
      ;;
    final)
      if [ "$scen" = "small-change" ] || [ "$scen" = "bug" ] || [ "$tier" = "1" ]; then
        dispatch="小任务 final(tier=1):派 1 个 Task droid reviewer-final-a 一肩挑两视角。
prompt:读 plugin 内 worktree-review skill(${skill}/SKILL.md),按 stage=final;覆盖基线1+基线2;Source: ${source}。"
      elif [ "$tier" = "2" ]; then
        dispatch="④final 分档 tier=2:Task 并行 2 路(跨模型):
  - subagent_type=reviewer-final-a · 基线1
  - subagent_type=reviewer-final-b · 基线2
prompt:读 plugin 内 worktree-review skill(${skill}/SKILL.md),按 stage=final;你负责 <基线1|基线2>;Source: ${source}。"
      else
        dispatch="④final tier=4(fail-closed 默认/有 capable 或 diff 大):Task 并行 4 路 = 两视角×两模型:
  - reviewer-final-a · 基线1
  - reviewer-final-b · 基线1
  - reviewer-final-a · 基线2
  - reviewer-final-b · 基线2
prompt 同一段(只改「你负责 <基线1|基线2>」):读 plugin 内 worktree-review skill(${skill}/SKILL.md),按 stage=final;Source: ${source};按 Return Contract 回 findings。
同视角跨模型对账:只一家报的重点亲验,两家同报置信升。"
      fi
      ;;
    merge-impl)
      dispatch="merge-impl 跨 PR 集成审:Task 并行 2 个 Custom Droids(跨模型,不信各 PR ④终审):
  - subagent_type=reviewer-final-a · 七角度路1
  - subagent_type=reviewer-final-b · 七角度路2
prompt:读 plugin 内 worktree-review skill(${skill}/SKILL.md),按 stage=merge-impl 走七角度(组合行为/合同/迁移/状态/import/回归/修复质量);你负责一路;Source: ${source};按 Return Contract 回 findings。"
      ;;
    *)
      dispatch="ERROR: droid overlay 未覆盖 stage=${stage};应 design|plan|final|merge-impl。"
      ;;
  esac
  {
    echo "# 审派发指南(stage=${stage} · host=droid · tier=${tier} · 机器生成,主线程读完直接派审者)"
    echo
    echo "主线程直接派审者跑 kind=review 审 loop,自己记账/亲验/收敛,不派协调帮手、不自己写产物结论。"
    echo "Source: ${source}"
    echo "宿主: droid · 壳工具: Execute · 问人: AskUser"
    echo
    echo "## 派审者"
    printf '%s\n' "$dispatch"
    echo
    awk 'BEGIN{p=0} /^## 留痕|^把全部审者|^## 收回|亲验后|## 收敛/{p=1} p{print}' "$brief" 2>/dev/null || true
  } > "${brief}.tmp" && mv "${brief}.tmp" "$brief"
}

# 主仓库状态平面遮蔽见 lib/host.sh mmw_ensure_state_ignore

cmd_start() {
  local stage=""; local -a sources=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage)  stage="$2";  shift 2 ;;
      --source) sources+=("$2"); shift 2 ;;   # 可重复(阶段可能钉多个产出,where 的 review_start 逐个吐)
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$stage" ]  || die "--stage 必填(design|plan|plan-impl|final|merge-impl)"
  [ "${#sources[@]}" -gt 0 ] || die "--source 必填(源意图路径/描述,派给审者用;可重复)"
  local source; source="${sources[*]}"

  # stage → loop kind + 视角(审查方法/角度本体在审者已装的 worktree-review skill,这里只留视角标签做派发路由)
  local kind views
  case "$stage" in
    design)     kind="review";        views="轴A 设计内容 / 轴B 项目对齐" ;;
    plan)       kind="review";        views="轴A 覆盖与质量 / 轴B 合规与交叉验证" ;;
    plan-impl)  kind="contract-gate"; views="(③合同门:机器核合同兑现,不派 Codex 判断)" ;;
    final)      kind="review";        views="基线1 回归+意图+跨plan / 基线2 独立代码审计" ;;
    merge-impl) kind="review";        views="跨 PR 集成审 7 角度(组合行为/合同/迁移/状态/import/回归/修复质量)" ;;
    *) die "--stage 只能 design|plan|plan-impl|final|merge-impl" ;;
  esac

  local top scen brief
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  STATE_SUBDIR="$(state_here)"; scen="$(jq -r '.scenario // ""' "$top/$STATE_SUBDIR/task.json" 2>/dev/null || echo "")"
  brief="$top/$STATE_SUBDIR/review-brief.md"
  mmw_ensure_state_ignore "$top"
  mkdir -p "$top/$STATE_SUBDIR"

  # 留痕落点:任务审(worktree 内)走 docs/reviews/(docs/.gitignore 已忽略);
  # merge-impl 在主仓库跑,不落 docs/ ——一切主仓库产物进状态平面,零残留。
  local trace="docs/reviews/<slug>-$stage.md"
  [ "$stage" = "merge-impl" ] && trace="$STATE_SUBDIR/<slug>-merge-impl-review.md"

  # fail-closed:未收束的 execution loop 不许被起审静默清掉(步账里存着 plan↔worktree 派发映射,
  # 清了断点恢复账本就没了)。先做完(exit-check DONE)或人工 mmw loop close 再起审。
  local lf="$top/$STATE_SUBDIR/loop-state.json"
  if [ -f "$lf" ] && [ "$(jq -r '.kind // ""' "$lf" 2>/dev/null)" = "execution" ]; then
    local lst; lst="$(bash "$LOOP" exit-check 2>/dev/null || echo "?")"
    [ "$lst" = "DONE" ] || die "execution loop 未收束($lst),拒绝起审(防落地步账被静默清);先做完或显式 mmw loop close"
  fi

  # 换审/门 loop 前先收束上一个内层 loop。close 幂等,无 loop 也安静过。
  # 审 loop 配轮上限(round next 机器计数,到顶自动 surface 熔断);③合同门机械核不设轮。
  bash "$LOOP" close >&2
  if [ "$kind" = "review" ]; then
    bash "$LOOP" init --kind "$kind" --max-rounds 2 >&2
  else
    bash "$LOOP" init --kind "$kind" >&2
  fi

  cat <<EOF
REVIEW_STARTED stage=$stage kind=$kind host=$(mmw_host)

下一步(主线程):
1. 抽覆盖清单进 loop(判断,从源文档逐条抽):
   $MMW loop checklist add --item "<要审到的维度>" --source "<doc:line>"
   $MMW loop attendance --mode <attended|afk>
EOF

  if [ "$kind" = "contract-gate" ]; then
    # 机械代劳:--source 指到的设计文档 anchors 节能坐实为空(只有占位注释/或单行"无跨计划共享合同")
    # → 脚本自动登记并 cover 显式空项(fail-closed 语义不变:检测本身就是 plan-impl.md 要求的证据);
    # 检测不出(文件/节找不到、节有实体内容)→ 不动,照旧走 plan-impl.md 人工核。
    local sfile="" anchors_ln="" body=""
    sfile="$(printf '%s\n' "${sources[@]}" | grep -oE '[^[:space:]]+\.md' | head -1 || true)"
    [ -n "$sfile" ] && [ ! -f "$sfile" ] && [ -f "$top/$sfile" ] && sfile="$top/$sfile"
    if [ -n "$sfile" ] && [ -f "$sfile" ]; then
      anchors_ln="$(grep -n '^## Cross-Plan Contract Anchors' "$sfile" 2>/dev/null | head -1 | cut -d: -f1 || true)"
      if [ -n "$anchors_ln" ]; then
        body="$(sed -n "$((anchors_ln+1)),\$p" "$sfile" | sed '/^## /q' | sed '/^## /d' \
                 | grep -vE '^[[:space:]]*(<!--.*-->)?[[:space:]]*$' || true)"
        if [ -z "$body" ] || { [ "$(printf '%s\n' "$body" | grep -c .)" -eq 1 ] && printf '%s' "$body" | grep -q '无跨计划共享合同'; }; then
          bash "$LOOP" checklist add --item "no-cross-plan-contracts" --source "$sfile:$anchors_ln" >&2
          bash "$LOOP" checklist cover --item "no-cross-plan-contracts" --evidence "$sfile:$anchors_ln(脚本机械核实 anchors 节为空)" >&2
          cat <<EOF
2. ③合同门:anchors 节已由脚本机械核实为空,no-cross-plan-contracts 已自动登记并 cover。
   直接回 build 收尾:mmw handoff --conclusion pass(引擎随即强制 ④终审闸)。
EOF
          return 0
        fi
      fi
    fi
    cat <<EOF
2. ③合同门不派 Codex、不列 pack(全 Pack 提交已由 build 执行 loop exit-check 保证):
   **读 references/review/plan-impl.md,照它走**——核什么(跨 plan 合同兑现)、怎么走 checklist、
   三个出口(全兑现 pass / 没兑现回 build / 合同根上错回 design)全在那份,方法论只此一源。
EOF
    return 0
  fi

  # ---- ④final develop 分档(效果×token 平衡):全 plan 无 capable 且 diff ≤ 阈值 → 2 审者
  # (每视角一模型:基线1 Codex / 基线2 Claude,仍跨模型互补);判不出数据(缺 manifest/base/plans)
  # → fail-closed 保 4 审者。阈值 env REVIEW_TIER_DIFF_MAX 覆盖,默认 800 改动行。
  local tier=4
  if [ "$stage" = "final" ] && [ "$scen" = "develop" ]; then
    local man="$top/$STATE_SUBDIR/task.json"
    local base tslug pdir cap diffn
    base="$(jq -r '.base_commit // ""' "$man" 2>/dev/null || echo "")"
    tslug="$(jq -r '.slug // ""' "$man" 2>/dev/null || echo "")"
    pdir="$top/docs/plans/$tslug"
    if [ -n "$base" ] && [ -n "$tslug" ] && [ -d "$pdir" ]; then
      # capable 检测 fail-closed:大小写不敏感 + 认中文"复杂度"标签(计划按仓库惯例常写中文),
      # 只要同一行有 complexity/复杂度 标签且带 capable 就算高风险,漏检=错降 tier=2(少审者)。
      # 宁可多匹配(留 tier=4 多审)也不漏(降档 fail-open);无 capable 才可能降 tier=2。
      cap="$(grep -rlEi '(complexity|复杂度).*capable' "$pdir" 2>/dev/null || true)"
      # 空 diff 时 grep 无匹配退 1,{ ...|| true; } 挡住 pipefail(bash3.2+set -e 惯性坑)
      diffn="$(git -C "$top" diff --shortstat "$base"..HEAD 2>/dev/null \
               | { grep -oE '[0-9]+ (insertion|deletion)' || true; } | awk '{s+=$1} END{print s+0}')"
      if [ -z "$cap" ] && [ "${diffn:-0}" -le "${REVIEW_TIER_DIFF_MAX:-800}" ]; then tier=2; fi
    fi
  fi

  # ---- 审 loop:brief 落文件,主线程派帮手只传路径(brief 不过主线程 context)----
  local dispatch
  if [ "$stage" = "final" ] && { [ "$scen" = "small-change" ] || [ "$scen" = "bug" ]; }; then
    # 小任务分档:diff 小,1 个 Codex 一肩挑两视角,不派双模型
    dispatch="$(cat <<DISPATCH
派 **1 个独立 Codex 审者一肩挑两路视角**($views)——本任务是 $scen,diff 小,不派双模型:
  codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>   (run_in_background)
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=final 审;两路视角($views)都由你覆盖,先跑完基线2(不看 plan 全新眼光审 diff)再跑基线1(对 design/issue 逐条);Source: ${source};按 skill 的 Return Contract 回结构化 findings。
  续接用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉)。
DISPATCH
)"
  elif [ "$stage" = "final" ] && [ "$tier" -eq 2 ]; then
    dispatch="$(cat <<DISPATCH
④final 分档(全 plan 无 capable 且 diff 小):派 **2 个独立审者 = 两路视角($views)各配一个模型**,
并行起、各自干净 context、互不通气。仍跨模型互补:
  基线1(回归+意图+跨plan)→ Codex:codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>   (run_in_background)
  基线2(独立代码审计,全新眼光)→ Claude:用 **Agent 工具派会话内 sub-agent** code-reviewer(模型/档在该 agent 定,只读),传 stage=final、视角=基线2、Source=${source}。走会话内 sub-agent,不另起无头进程(那会另计费)。
  prompt/传参(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=final 审;你负责 <基线1|基线2> 这一路视角;Source: ${source};按 skill 的 Return Contract 回结构化 findings。
  续接:Codex 用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉);Claude 侧再派一个 code-reviewer sub-agent 续审同视角(不复用被审 context)。
DISPATCH
)"
  elif [ "$stage" = "final" ]; then
    dispatch="$(cat <<DISPATCH
④final 双模型:派 **4 个独立审者 = 两路视角($views)× 两个模型(Codex / Claude)**,
并行起、各自干净 context、互不通气。
四个审者读**同一份方法论**(只有"你负责 <视角>"一处不同):
  读你已装的 worktree-review skill,按 stage=final 审(skill 落点 ~/.agents/skills/worktree-review/,两模型同读此单源);你负责 <基线1|基线2> 这一路视角;Source: ${source};按 skill 的 Return Contract 回结构化 findings。
派发(每视角两模型各一个):
  Codex(× 两视角):codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>   (run_in_background)
  Claude(× 两视角):用 **Agent 工具各派一个会话内 sub-agent** code-reviewer(模型/档在该 agent 定,只读),传 stage=final、视角=<基线1|基线2>、Source=${source}。**走会话内 sub-agent,不另起无头进程**——本会话已在 Claude Code CLI 里,另起无头是独立进程会另外计费;sub-agent 同会话覆盖、天生只读、干净 context。
  续接:Codex 用 codex exec --sandbox read-only ... resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉);Claude 侧再派一个 code-reviewer sub-agent 续审同视角。
同视角跨模型对账:Claude 与 Codex 同视角 findings 互相对照——只一家报出的重点亲验,两家同报的置信升。
DISPATCH
)"
  elif [ "$stage" = "plan" ]; then
    # ②计划审跨模型:计划由 Codex 写(plan 阶段),审者翻成 Claude——写者≠审者
    dispatch="$(cat <<DISPATCH
②计划审跨模型(Codex 写的计划 → Claude 审):派 **2 个 Claude code-reviewer sub-agent**(Agent 工具,会话内、只读、干净 context),两路视角各配一个:
  - 轴A 覆盖与质量
  - 轴B 合规与交叉验证
每个传参(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=plan 审;你负责 <轴A|轴B> 这一路视角;Source: ${source};按 skill 的 Return Contract 回结构化 findings。
**走会话内 sub-agent,不另起无头进程**——本会话已在 Claude Code CLI 里,另起无头是独立进程会另外计费;sub-agent 同会话覆盖、天生只读、干净 context。
续接同视角追问:再派一个 code-reviewer sub-agent 续审,不复用被审 context。
DISPATCH
)"
  else
    dispatch="$(cat <<DISPATCH
派两个独立 Codex 审者($views),单条消息并行起、各自干净 context,每个跑:
  codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>   (run_in_background)
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=$stage 审;你负责其中一路视角(两审者分走 $views);Source: ${source};按 skill 的 Return Contract 回结构化 findings。
  续接用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉)。
DISPATCH
)"
  fi

  cat > "$brief" <<EOF
# 审派发指南(stage=$stage · host=$(mmw_host) · 机器生成,主线程读完直接派审者)

主线程直接派审者跑 kind=review 审 loop,自己记账/亲验/收敛,不派协调帮手、不自己写产物结论。
Source: ${source}

## 派审者
$dispatch

以上无头 CLI 一律用宿主后台能力起(Claude: Bash \`run_in_background: true\` + TaskOutput; Droid: Task 派 droid)。审一轮常超前台超时上限;Codex 的 session id 在其输出头部 \`session id:\` 行。

## 留痕(必做)
把全部审者的结构化 findings **原样落盘** $trace(不重写不摘要,保真);
亲验后把每条 verdict/处置(accepted/rejected/duplicate/needs-evidence)就近标该条下,文末写一句总 verdict。
收口只回读这份文档的 verdict 段,findings 全文压在 trace 文件里、不长驻主线程 context。

## 收回亲验
每条 finding 自己 Read/grep/跑坐实(审者是劳动力不是信源),引不出 file:line 降置信。
承重 finding 亲验后才 accept(判断在此收口做,审 verify 期间不 consult advisor)。
  坐实一个维度: $MMW loop checklist cover --item <i> --evidence <file:line>
  真 finding:   $MMW loop finding add --severity <C/I/M> --confidence <1-10> --locator <file:line>

## 收敛与熔断
全部审者跑完追一轮无新高置信 finding = 收敛;每跑完一整轮(全视角覆盖+修复重验)未收敛 →
  $MMW loop round next   (轮账机器计数;到上限引擎自动 surface 熔断,不靠自觉)
方向疑/缺输入 → $MMW loop surface --kind <needs-context|needs-redirection> --question "<...>",别当产物缺陷修。
清单全绿+无开口 Critical(\`$MMW loop exit-check\`==DONE)前,收口 handoff pass 会被引擎拒(确定性闸,不靠看守)。
EOF

  # small-change/bug final 在 Claude 侧 tier 语义=1;overlay 用 scen 已处理,这里传 1 便于 brief 标注
  local droid_tier="$tier"
  if [ "$stage" = "final" ] && { [ "$scen" = "small-change" ] || [ "$scen" = "bug" ]; }; then
    droid_tier=1
  fi
  overlay_droid_brief_if_needed "$brief" "$stage" "$scen" "$source" "$droid_tier"

  cat <<EOF
2. 主线程读 $brief,按「派审者」段**直接派审者**(拍平,不再派协调帮手):审者各自干净 context 并行起,
   读 worktree-review skill 出结构化 findings;findings 落 $trace,只回读 verdict 段。
3. 审者跑完 → 主线程按 brief 的留痕/亲验/收敛落 findings 与 checklist cover;
   清单全绿 + 无开口 Critical(\`$MMW loop exit-check\`==DONE)后回 review/review.md 收口 handoff verdict
   (未收束时 handoff pass 会被引擎拒)。
EOF
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...>" ;;
esac

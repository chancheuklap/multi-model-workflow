#!/usr/bin/env bash
# review.sh —— 起一道审(定编制 + 出派发指南,一条命令)
#
#   start --stage <design|plan|plan-impl|final|merge-impl> --source <源意图路径/描述>
#       按阶段定视角与审者编制,把审派发指南写进状态目录 review-brief.md(主线程读它直接派审者)。
#       审者读已装的 worktree-review skill(方法本体单源在那,不给审者 plugin 内路径)。
#       ④final 按 scenario 分档:develop = 双模型 2×2 或 2;small-change/bug = 1×Codex 一肩挑两视角。
#
# 审不记账:收口看产物——findings 原样落盘 docs/reviews/<slug>-<stage>.md,亲验后标处置、写 verdict 段;
# 审闸 pass 时引擎只核「该文件在且含 verdict」(flow.sh),质量与 Critical 处置是主线程判断。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""   # 打印给主线程的命令,完整可执行形式
state_here() {
  printf '%s' "$MMW_STATE_SUBDIR"
}
# 审 = 高判断,审者跑高档;可 env 覆盖。
# Codex 审者(外部 agent)走 codex exec 无头;Claude 审者走会话内 sub-agent(agents/code-reviewer.md)。
CODEX_REVIEW_MODEL="${CODEX_REVIEW_MODEL:-gpt-5.6-sol}"
CODEX_REVIEW_EFFORT="${CODEX_REVIEW_EFFORT:-xhigh}"
# 设计审跑 high 档(对齐 pi reviewer-design-a);终审 / 合并审仍 xhigh。
CODEX_DESIGN_REVIEW_EFFORT="${CODEX_DESIGN_REVIEW_EFFORT:-high}"

die() { echo "ERROR: $*" >&2; exit 1; }

cmd_start() {
  local stage=""; local -a sources=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage)  stage="$2";  shift 2 ;;
      --source) sources+=("$2"); shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$stage" ]  || die "--stage 必填(design|plan|plan-impl|final|merge-impl)"
  [ "${#sources[@]}" -gt 0 ] || die "--source 必填(源意图路径/描述,派给审者用;可重复)"
  local source; source="${sources[*]}"

  # stage → 视角(审查方法/角度本体在审者已装的 worktree-review skill,这里只留视角标签做派发路由)
  local views
  case "$stage" in
    design)     views="轴A 设计内容 / 轴B 项目对齐" ;;
    plan)       views="轴A 覆盖与质量 / 轴B 合规与交叉验证" ;;
    plan-impl)  views="(③合同门:机器核合同兑现,不派审者判断)" ;;
    final)      views="基线1 回归+意图+跨plan / 基线2 独立代码审计" ;;
    merge-impl) views="跨 PR 集成审 7 角度(组合行为/合同/迁移/状态/import/回归/修复质量)" ;;
    *) die "--stage 只能 design|plan|plan-impl|final|merge-impl" ;;
  esac

  local top scen brief slug
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  STATE_SUBDIR="$(state_here)"
  scen="$(jq -r '.scenario // ""' "$top/$STATE_SUBDIR/task.json" 2>/dev/null || echo "")"
  slug="$(jq -r '.slug // "<slug>"' "$top/$STATE_SUBDIR/task.json" 2>/dev/null || echo "<slug>")"
  brief="$top/$STATE_SUBDIR/review-brief.md"
  mmw_ensure_state_ignore "$top"
  mkdir -p "$top/$STATE_SUBDIR"

  # 留痕落点:任务审(worktree 内)走 docs/reviews/(docs/.gitignore 已忽略);
  # merge-impl 在主仓库跑,不落 docs/ ——一切主仓库产物进状态平面,零残留。
  local trace="docs/reviews/$slug-$stage.md"
  [ "$stage" = "merge-impl" ] && trace="$STATE_SUBDIR/$slug-merge-impl-review.md"

  if [ "$stage" = "plan-impl" ]; then
    # ③合同门:机器能坐实的机器坐实——设计文档 anchors 节为空(占位注释/单行"无跨计划共享合同")
    # → 直接放行回执;有实体合同 → 指到 plan-impl.md 人工核,结论写进 trace。
    local sfile="" anchors_ln="" body=""
    sfile="$(printf '%s\n' "${sources[@]}" | grep -oE '[^[:space:]]+\.md' | head -1 || true)"
    [ -n "$sfile" ] && [ ! -f "$sfile" ] && [ -f "$top/$sfile" ] && sfile="$top/$sfile"
    if [ -n "$sfile" ] && [ -f "$sfile" ]; then
      anchors_ln="$(grep -n '^## Cross-Plan Contract Anchors' "$sfile" 2>/dev/null | head -1 | cut -d: -f1 || true)"
      if [ -n "$anchors_ln" ]; then
        body="$(sed -n "$((anchors_ln+1)),\$p" "$sfile" | sed '/^## /q' | sed '/^## /d' \
                 | grep -vE '^[[:space:]]*(<!--.*-->)?[[:space:]]*$' || true)"
        if [ -z "$body" ] || { [ "$(printf '%s\n' "$body" | grep -c .)" -eq 1 ] && printf '%s' "$body" | grep -q '无跨计划共享合同'; }; then
          cat <<EOF
CONTRACT_GATE_EMPTY(脚本机械核实 anchors 节为空:$sfile:$anchors_ln)
③合同门无跨计划合同,直接回 build 收尾:$MMW handoff --conclusion pass(引擎随即强制 ④终审闸)。
EOF
          return 0
        fi
      fi
    fi
    cat <<EOF
REVIEW_STARTED stage=plan-impl host=claude
③合同门不派审者、不列 pack:**读 references/review/plan-impl.md,照它走**——核什么(跨 plan 合同兑现)、
三个出口(全兑现 pass / 没兑现回 build / 合同根上错回 design)全在那份。
核对过程与逐条兑现证据写进 $trace(含一句总 verdict);兑现全 → $MMW handoff --conclusion pass。
EOF
    return 0
  fi

  # ---- ④final develop 分档(效果×token 平衡):全 plan 无 capable 且 diff ≤ 阈值 → 2 审者;
  # 判不出数据(缺 manifest/base/plans)→ 保 4 审者。阈值 env REVIEW_TIER_DIFF_MAX 覆盖,默认 800 改动行。
  local tier=4
  if [ "$stage" = "final" ] && [ "$scen" = "develop" ]; then
    local man="$top/$STATE_SUBDIR/task.json"
    local base tslug pdir cap diffn
    base="$(jq -r '.base_commit // ""' "$man" 2>/dev/null || echo "")"
    tslug="$(jq -r '.slug // ""' "$man" 2>/dev/null || echo "")"
    pdir="$top/docs/plans/$tslug"
    if [ -n "$base" ] && [ -n "$tslug" ] && [ -d "$pdir" ]; then
      # capable 检测:大小写不敏感 + 认中文"复杂度";宁可多匹配(留 4 审)也不漏
      cap="$(grep -rlEi '(complexity|复杂度).*capable' "$pdir" 2>/dev/null || true)"
      diffn="$(git -C "$top" diff --shortstat "$base"..HEAD 2>/dev/null \
               | { grep -oE '[0-9]+ (insertion|deletion)' || true; } | awk '{s+=$1} END{print s+0}')"
      if [ -z "$cap" ] && [ "${diffn:-0}" -le "${REVIEW_TIER_DIFF_MAX:-800}" ]; then tier=2; fi
    fi
  fi

  # ---- 派发指南落文件(brief 不过主线程 context)----
  # 设计审 Codex 跑 high(对齐 pi);终审 / 合并审跑 xhigh。
  local ceffort="$CODEX_REVIEW_EFFORT"
  [ "$stage" = "design" ] && ceffort="$CODEX_DESIGN_REVIEW_EFFORT"
  local dispatch
  if [ "$stage" = "final" ] && { [ "$scen" = "small-change" ] || [ "$scen" = "bug" ]; }; then
    dispatch="$(cat <<DISPATCH
派 **1 个独立 Codex 审者一肩挑两路视角**($views)——本任务是 $scen,diff 小,不派双模型:
  codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$ceffort" - < <prompt>   (run_in_background)
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=final 审;两路视角($views)都由你覆盖,先跑完基线2(不看 plan 全新眼光审 diff)再跑基线1(对 design/issue 逐条);Source: ${source};按 skill 的 Return Contract 回结构化 findings。
  续接用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$ceffort" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,必须整套重钉)。
DISPATCH
)"
  elif [ "$stage" = "final" ] && [ "$tier" -eq 2 ]; then
    dispatch="$(cat <<DISPATCH
④final 分档(全 plan 无 capable 且 diff 小):派 **2 个独立审者 = 两路视角($views)各配一个模型**,
并行起、各自干净 context、互不通气。仍跨模型互补:
  基线1(回归+意图+跨plan)→ Codex:codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$ceffort" - < <prompt>   (run_in_background)
  基线2(独立代码审计,全新眼光)→ Claude:用 **Agent 工具派会话内 sub-agent** code-reviewer(模型/档在该 agent 定,只读),传 stage=final、视角=基线2、Source=${source}。走会话内 sub-agent,不另起无头进程(那会另计费)。
  prompt/传参(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=final 审;你负责 <基线1|基线2> 这一路视角;Source: ${source};按 skill 的 Return Contract 回结构化 findings。
  续接:Codex 用 codex exec --sandbox read-only ... resume <session-id> "<追问>"(必须整套重钉围栏/模型档);Claude 侧再派一个 code-reviewer sub-agent 续审同视角(不复用被审 context)。
DISPATCH
)"
  elif [ "$stage" = "final" ]; then
    dispatch="$(cat <<DISPATCH
④final 双模型:派 **4 个独立审者 = 两路视角($views)× 两个模型(Codex / Claude)**,
并行起、各自干净 context、互不通气。四个审者读**同一份方法论**(只有"你负责 <视角>"一处不同):
  读你已装的 worktree-review skill,按 stage=final 审(两模型同读此单源);你负责 <基线1|基线2> 这一路视角;Source: ${source};按 skill 的 Return Contract 回结构化 findings。
派发(每视角两模型各一个):
  Codex(× 两视角):codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$ceffort" - < <prompt>   (run_in_background)
  Claude(× 两视角):用 **Agent 工具各派一个会话内 sub-agent** code-reviewer(模型/档在该 agent 定,只读),传 stage=final、视角=<基线1|基线2>、Source=${source}。走会话内 sub-agent,不另起无头进程。
  续接:Codex resume 必须整套重钉围栏/模型档;Claude 侧再派一个 code-reviewer sub-agent 续审同视角。
同视角跨模型对账:Claude 与 Codex 同视角 findings 互相对照——只一家报出的重点亲验,两家同报的置信升。
DISPATCH
)"
  elif [ "$stage" = "plan" ]; then
    dispatch="$(cat <<DISPATCH
②计划审跨模型(Codex 写的计划 → Claude 审):派 **2 个 Claude code-reviewer sub-agent**(Agent 工具,会话内、只读、干净 context),两路视角各配一个:
  - 轴A 覆盖与质量
  - 轴B 合规与交叉验证
每个传参(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=plan 审;你负责 <轴A|轴B> 这一路视角;Source: ${source};按 skill 的 Return Contract 回结构化 findings。
**走会话内 sub-agent,不另起无头进程**;续接同视角追问:再派一个 code-reviewer sub-agent 续审,不复用被审 context。
DISPATCH
)"
  else
    dispatch="$(cat <<DISPATCH
派两个独立 Codex 审者($views),单条消息并行起、各自干净 context,每个跑:
  codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$ceffort" - < <prompt>   (run_in_background)
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=$stage 审;你负责其中一路视角(两审者分走 $views);Source: ${source};按 skill 的 Return Contract 回结构化 findings。
  续接用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$ceffort" resume <session-id> "<追问>"(resume 必须整套重钉)。
DISPATCH
)"
  fi

  cat > "$brief" <<EOF
# 审派发指南(stage=$stage · host=claude · 机器生成,主线程读完直接派审者)

主线程直接派审者,自己亲验收敛,不自己写产物结论。审不记账,收口看产物(下方留痕)。
Source: ${source}

## 派审者
$dispatch

以上无头 CLI 一律用 Bash \`run_in_background: true\` + TaskOutput 起。审一轮常超前台超时上限;Codex 的 session id 在其输出头部 \`session id:\` 行。
派审者时在每个 task/prompt 写明:遵守 worktree-review method——一次审透本视角全部承重问题;报全≠报噪;Minor 标 blocking=no;按 Return Contract 回。

## 留痕(收口的硬核就在这份文件)
把全部审者的结构化 findings **原样落盘** $trace(不重写不摘要,保真);
亲验后把每条 verdict/处置(accepted/rejected/duplicate/needs-evidence/waived)就近标该条下,文末写一句总 verdict。
审闸收口 handoff pass 时引擎核该文件存在且含 verdict——没有留痕 = 审没跑过,不放行。
收口只回读这份文档的 verdict 段,findings 全文压在 trace 文件里、不长驻主线程 context。

## 收回亲验(裁判权在主线程)
审者是劳动力不是信源,也不是放行权人。对每条 finding:
1. 自己 Read/grep/跑坐实;引不出 file:line → rejected 或 needs-evidence。
2. 过四问:是否过度设计/过度考虑?不修的真实后果(谁受伤)?边际收益?现在是否值得修(第2轮起还要问相对上轮的承重增量)?
3. 标处置:accepted|rejected|duplicate|needs-evidence|waived(理由必填)。
硬纪律:只有 accepted 驱动 needs-repair;Critical 必须处置(修或有理 reject/waive);Minor/non-blocking 默认 waived;不要因为 Nit 未清就 needs-repair。
放行标准:整体在变好 + 无开口 Critical + 无未修 accepted 承重项,不追求完美。

## 收敛
无新高置信 accepted = 收敛。指纹重合或审闸 repair_count 触顶由引擎 GUARD,到顶交人并亮未收敛/已 waive 清单,别硬磨。
方向疑/缺输入 → handoff needs-redirection / needs-context 交上去,别当产物缺陷修。
EOF

  # 复审收敛:已有留痕或 repair_count>0 → brief 追加 prior_trace 规则
  local rc_now=0
  rc_now="$(jq -r '.repair_count // 0' "$top/$STATE_SUBDIR/task.json" 2>/dev/null || echo 0)"
  case "$rc_now" in ''|*[!0-9]*) rc_now=0 ;; esac
  if [ -f "$top/$trace" ] || [ "$rc_now" -gt 0 ]; then
    cat >> "$brief" <<EOF

## 本轮是 re-review
上一轮留痕: $trace
派审者时在每个 task/prompt 写明:stage=$stage; re-review=yes; prior_trace=$trace; 只验证 accepted 已修 + 修复 diff 回归;已 rejected/waived/duplicate 无新证据不得重提;不对未改区域起新 Nit。
EOF
  fi

  cat <<EOF
REVIEW_STARTED stage=$stage host=claude
1. 主线程读 $brief,按「派审者」段直接派(各自干净 context 并行起,读 worktree-review skill 出结构化 findings)。
2. findings 原样落 $trace,亲验标处置、写总 verdict(收口硬核:该文件在且含 verdict)。
3. 收口回 review/review.md 按 Gap 选结论词 handoff。
EOF
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...>" ;;
esac

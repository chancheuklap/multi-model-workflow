#!/usr/bin/env bash
# review.sh —— 审闸一条命令(把"起一道审"的机械 6 步收成 1 步)
#
#   start --stage <design|plan|plan-impl|final|merge-impl> --source <源意图路径/描述>
#       按阶段映射 kind + 视角,init loop-state,把协调帮手 brief 写进状态目录文件
#       (主线程派帮手只传文件路径,brief 不过主线程 context)。
#       审者读已装的 worktree-review skill(方法本体单源在那,不给审者 plugin 内路径)。
#       ④final 按 scenario 分档:develop = 双模型 2×2;small-change/bug = 1×Codex 一肩挑两视角(diff 小)。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/loop.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""   # 打印给协调帮手的命令,完整可执行形式
# 审 = 高判断,审者跑高档;可 env 覆盖。
CODEX_REVIEW_MODEL="${CODEX_REVIEW_MODEL:-gpt-5.5}"
CODEX_REVIEW_EFFORT="${CODEX_REVIEW_EFFORT:-high}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"
CLAUDE_REVIEW_MODEL="${CLAUDE_REVIEW_MODEL:-opus}"
CLAUDE_REVIEW_EFFORT="${CLAUDE_REVIEW_EFFORT:-xhigh}"

die() { echo "ERROR: $*" >&2; exit 1; }

# 主仓库状态平面遮蔽(merge-impl 在主仓库起审时写 .claude/multi-model-workflow/):
# 与 prepare.sh 同款,幂等;worktree 内已有全遮蔽(*)直接跳过。
ensure_state_ignore() {  # $1=git toplevel
  local g="$1/.claude/.gitignore" line
  mkdir -p "$1/.claude"
  if [ -f "$g" ] && grep -qxF '*' "$g"; then return 0; fi
  for line in 'worktrees/' 'multi-model-workflow/' '.gitignore'; do
    { [ -f "$g" ] && grep -qxF "$line" "$g"; } || printf '%s\n' "$line" >> "$g"
  done
}

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
  scen="$(jq -r '.scenario // ""' "$top/.claude/multi-model-workflow/task.json" 2>/dev/null || echo "")"
  brief="$top/.claude/multi-model-workflow/review-brief.md"
  ensure_state_ignore "$top"
  mkdir -p "$top/.claude/multi-model-workflow"

  # 留痕落点:任务审(worktree 内)走 docs/reviews/(docs/.gitignore 已忽略);
  # merge-impl 在主仓库跑,不落 docs/ ——一切主仓库产物进状态平面,零残留。
  local trace="docs/reviews/<slug>-$stage.md"
  [ "$stage" = "merge-impl" ] && trace=".claude/multi-model-workflow/<slug>-merge-impl-review.md"

  # fail-closed:未收束的 execution loop 不许被起审静默清掉(步账里存着 plan↔worktree 派发映射,
  # 清了断点恢复账本就没了)。先做完(exit-check DONE)或人工 mmw loop close 再起审。
  local lf="$top/.claude/multi-model-workflow/loop-state.json"
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
REVIEW_STARTED stage=$stage kind=$kind

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
    local man="$top/.claude/multi-model-workflow/task.json"
    local base tslug pdir cap diffn
    base="$(jq -r '.base_commit // ""' "$man" 2>/dev/null || echo "")"
    tslug="$(jq -r '.slug // ""' "$man" 2>/dev/null || echo "")"
    pdir="$top/docs/plans/$tslug"
    if [ -n "$base" ] && [ -n "$tslug" ] && [ -d "$pdir" ]; then
      cap="$(grep -rlE 'Complexity:.*capable' "$pdir" 2>/dev/null || true)"
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
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=final 审;两路视角($views)都由你覆盖,先跑完基线2(不看 plan 全新眼光审 diff)再跑基线1(对 design/issue 逐条);Source: $source;按 skill 的 Return Contract 回结构化 findings。
  续接用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉)。
DISPATCH
)"
  elif [ "$stage" = "final" ] && [ "$tier" -eq 2 ]; then
    dispatch="$(cat <<DISPATCH
④final 分档(全 plan 无 capable 且 diff 小):派 **2 个独立审者 = 两路视角($views)各配一个模型**,
单条消息并行起(run_in_background)、各自干净 context、互不通气。仍跨模型互补:
  基线1(回归+意图+跨plan)→ Codex:codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>
  基线2(独立代码审计,全新眼光)→ Claude:$CLAUDE_BIN -p "<prompt>" --model $CLAUDE_REVIEW_MODEL --effort $CLAUDE_REVIEW_EFFORT --session-id <uuidgen 自生成并记下,供续接>
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=final 审;你负责 <基线1|基线2> 这一路视角;Source: $source;按 skill 的 Return Contract 回结构化 findings。
  续接:codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉);Claude 用 $CLAUDE_BIN -p --resume <你起审时给的 uuid> "<追问>" --model $CLAUDE_REVIEW_MODEL --effort ${CLAUDE_REVIEW_EFFORT}。
DISPATCH
)"
  elif [ "$stage" = "final" ]; then
    dispatch="$(cat <<DISPATCH
④final 双模型:派 **4 个独立审者 = 两路视角($views)× 两个模型(Codex / Claude)**,
单条消息并行起(run_in_background)、各自干净 context、互不通气。
四个审者 prompt 用**同一段文本**(只有"你负责 <视角>"一处不同):
  读你已装的 worktree-review skill,按 stage=final 审(skill 落点 ~/.agents/skills/worktree-review/,两模型同读此单源);你负责 <基线1|基线2> 这一路视角;Source: $source;按 skill 的 Return Contract 回结构化 findings。
派发命令(每视角两模型各一个):
  Codex:  codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>
  Claude: $CLAUDE_BIN -p "<同一段 prompt>" --model $CLAUDE_REVIEW_MODEL --effort $CLAUDE_REVIEW_EFFORT --session-id <uuidgen 自生成并记下,供续接>
  续接:codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉);Claude 用 $CLAUDE_BIN -p --resume <你起审时给的 uuid> "<追问>" --model $CLAUDE_REVIEW_MODEL --effort $CLAUDE_REVIEW_EFFORT
同视角跨模型对账:Claude 与 Codex 同视角 findings 互相对照——只一家报出的重点亲验,两家同报的置信升。
DISPATCH
)"
  else
    dispatch="$(cat <<DISPATCH
派两个独立 Codex 审者($views),单条消息并行起、各自干净 context,每个跑:
  codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>   (run_in_background)
  prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=$stage 审;你负责其中一路视角(两审者分走 $views);Source: $source;按 skill 的 Return Contract 回结构化 findings。
  续接用 codex exec --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" resume <session-id> "<追问>"(resume 不继承原围栏/模型档,掉回 config 默认,必须整套重钉)。
DISPATCH
)"
  fi

  cat > "$brief" <<EOF
# 审核协调帮手 brief(stage=$stage · 机器生成,读完照做)

你是审核协调帮手,跑 kind=review 审 loop,不自己写结论也不改产物。
Source: $source

## 派审者
$dispatch

以上无头 CLI 一律用 Bash 工具 \`run_in_background: true\` 起(审一轮常超前台 10 分钟超时上限),完成后 TaskOutput 收全文;Codex 的 session id 在其输出头部 \`session id:\` 行。

## 留痕(必做)
把全部审者的结构化 findings **原样落盘** $trace(不重写不摘要,保真+省主线程 context);
亲验后把每条 verdict/处置(accepted/rejected/duplicate/needs-evidence)就近标该条下,文末写一句总 verdict。

## 收回亲验
每条 finding 自己 Read/grep/跑坐实(审者是劳动力不是信源),引不出 file:line 降置信。
你只做机械亲验与记账,不 consult advisor(判断在主线程收口做)。
  坐实一个维度: $MMW loop checklist cover --item <i> --evidence <file:line>
  真 finding:   $MMW loop finding add --severity <C/I/M> --confidence <1-10> --locator <file:line>

## 收敛与熔断
全部审者跑完追一轮无新高置信 finding = 收敛;每跑完一整轮(全视角覆盖+修复重验)未收敛 →
  $MMW loop round next   (轮账机器计数;到上限引擎自动 surface 熔断,不靠自觉)
方向疑/缺输入 → $MMW loop surface --kind <needs-context|needs-redirection> --question "<...>",别当产物缺陷修。
清单全绿+无开口 Critical 前 guard-loop 不让你停。
EOF

  cat <<EOF
2. 派审核协调帮手(Claude sub-agent,SubagentStop 受 guard-loop 看守),prompt 只给一句:
   「读 $brief 照做」——派发命令/留痕/亲验/收敛熔断全在 brief 里,不过主线程 context。
3. 协调帮手停下后,主线程读 loop-state(pause/findings),回 review/review.md 的收口步 handoff verdict。
EOF
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...>" ;;
esac

#!/usr/bin/env bash
# review.sh —— 审闸一条命令(把"起一道审"的机械 6 步收成 1 步)
#
#   start --stage <design|plan|plan-impl|final|merge-impl> --source <源意图路径/描述>
#       按阶段映射 kind + 两路视角,init loop-state,打印好协调帮手 brief。
#       审者 = Codex,读它已装的 worktree-review skill(审查方法本体单源在那,plugin 不重复、
#       不给 Codex 任何 plugin 内路径——Codex 读不到 Claude 的 plugin/)。派发只给 stage + 视角 + Source。
#       主线程拿到后:抽覆盖清单进 loop(判断,留你) → 用打印的 brief 派协调帮手。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOOP="$SCRIPT_DIR/loop.sh"
MMW="bash $SCRIPT_DIR/mmw.sh"   # 打印给协调帮手的命令走统一 CLI
# 审 = 高判断,审者 Codex 跑高档(不吃 codex 默认档);可 env 覆盖
CODEX_REVIEW_MODEL="${CODEX_REVIEW_MODEL:-gpt-5.5}"
CODEX_REVIEW_EFFORT="${CODEX_REVIEW_EFFORT:-high}"

die() { echo "ERROR: $*" >&2; exit 1; }

cmd_start() {
  local stage="" source=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage)  stage="$2";  shift 2 ;;
      --source) source="$2"; shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$stage" ]  || die "--stage 必填(design|plan|plan-impl|final|merge-impl)"
  [ -n "$source" ] || die "--source 必填(源意图路径/描述,派给 Codex 用)"

  # stage → loop kind + 两路视角(审查方法/角度本体在 Codex 侧 worktree-review skill,这里只留视角标签做派发路由)
  local kind views
  case "$stage" in
    design)     kind="review";        views="轴A 设计内容 / 轴B 项目对齐" ;;
    plan)       kind="review";        views="轴A 覆盖与质量 / 轴B 合规与交叉验证" ;;
    plan-impl)  kind="contract-gate"; views="(③合同门:机器核合同兑现,不派 Codex 判断)" ;;
    final)      kind="review";        views="基线1 回归+意图+跨plan / 基线2 独立代码审计" ;;
    merge-impl) kind="review";        views="跨 PR 集成审 7 角度(组合行为/合同/迁移/状态/import/回归/修复质量)" ;;
    *) die "--stage 只能 design|plan|plan-impl|final|merge-impl" ;;
  esac

  # 换审/门 loop 前先收束上一个内层 loop(如 ③ 前的 execution:执行已 DONE、git 提交为准,
  # ledger 显式归零而非被 init 静默覆盖)。close 幂等,无 loop 也安静过。
  bash "$LOOP" close >&2
  bash "$LOOP" init --kind "$kind" >&2

  cat <<EOF
REVIEW_STARTED stage=$stage kind=$kind

下一步(主线程):
1. 抽覆盖清单进 loop(判断,从源文档逐条抽):
   $MMW loop checklist add --item "<要审到的维度>" --source "<doc:line>"
   $MMW loop attendance --mode <attended|afk>
EOF

  if [ "$kind" = "contract-gate" ]; then
    cat <<EOF
2. ③合同门不派 Codex、不列 pack(全 Pack 提交已由 build 执行 loop exit-check 保证):
   **读 references/review/plan-impl.md,照它走**——核什么(跨 plan 合同兑现)、怎么走 checklist、
   三个出口(全兑现 pass / 没兑现回 build / 合同根上错回 design)全在那份,方法论只此一源。
EOF
  else
    cat <<EOF
2. 派审核协调帮手(Claude sub-agent,SubagentStop 受 guard-loop 看守),给这份 brief:

   > 你是审核协调帮手,跑 kind=review 审 loop,不自己写结论也不改产物。
   > Source: $source
   > 派两个独立 Codex 审者($views),单条消息并行起、各自干净 context,每个跑:
   >   codex exec -C . --sandbox read-only -m $CODEX_REVIEW_MODEL -c model_reasoning_effort="$CODEX_REVIEW_EFFORT" - < <prompt>   (run_in_background)
   >   prompt(纯路由,不内联审查方法):读你已装的 worktree-review skill,按 stage=$stage 审;你负责其中一路视角(两审者分走 $views);Source: $source;按 skill 的 Return Contract 回结构化 findings。
   >   续接用 codex exec resume <id>。
   > 留痕(必做):把两个 Codex 审者的结构化 findings **原样落盘** docs/reviews/<slug>-$stage.md(不重写不摘要,保真+省主线程 context);亲验后把每条 verdict/处置(accepted/rejected/duplicate/needs-evidence)就近标该条下,文末写一句总 verdict。
   > 收回亲验:每条 finding 自己 Read/grep/跑坐实(Codex 是劳动力不是信源),引不出 file:line 降置信。
   >   坐实一个维度: $MMW loop checklist cover --item <i> --evidence <file:line>
   >   真 finding:   $MMW loop finding add --severity <C/I/M> --confidence <1-10> --locator <file:line>
   > 收敛:两视角跑完追一轮无新高置信 finding = 收敛;round 到上限(①②=2,④=1-2)未收敛 →
   >   $MMW loop surface --kind needs-redirection --question "<审不收敛/卡在哪>"
   > 方向疑/缺输入 → surface,别当产物缺陷修。清单全绿+无开口 Critical 前 guard-loop 不让你停。
EOF
  fi
  cat <<EOF
3. 协调帮手停下后,主线程读 loop-state(pause/findings),回 review/review.md 的收口步 handoff verdict。
EOF
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...>" ;;
esac

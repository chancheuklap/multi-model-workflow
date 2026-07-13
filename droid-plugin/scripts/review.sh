#!/usr/bin/env bash
# Droid 原生审闸派发指南生成器。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
LOOP="$SCRIPT_DIR/loop.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""

die() { echo "ERROR: $*" >&2; exit 1; }

state_here() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  mmw_resolve_state_subdir "$top"
}

final_tier() {
  local top="$1" state="$2" scenario="$3"
  if [ "$scenario" = "small-change" ] || [ "$scenario" = "bug" ]; then
    printf '1'; return
  fi
  local man="$top/$state/task.json" base slug pdir capable diffn
  base="$(jq -r '.base_commit // ""' "$man" 2>/dev/null || true)"
  slug="$(jq -r '.slug // ""' "$man" 2>/dev/null || true)"
  pdir="$top/docs/plans/$slug"
  [ -n "$base" ] && [ -n "$slug" ] && [ -d "$pdir" ] || { printf '4'; return; }
  capable="$(grep -rlEi '(complexity|复杂度).*capable' "$pdir" 2>/dev/null || true)"
  diffn="$(git -C "$top" diff --shortstat "$base"..HEAD 2>/dev/null |
    { grep -oE '[0-9]+ (insertion|deletion)' || true; } |
    awk '{s+=$1} END{print s+0}')"
  if [ -z "$capable" ] && [ "${diffn:-0}" -le "${REVIEW_TIER_DIFF_MAX:-800}" ]; then
    printf '2'
  else
    printf '4'
  fi
}

dispatch_for() {
  local stage="$1" tier="$2" source="$3" skill="$4"
  case "$stage" in
    design)
      cat <<EOF
单条消息并行派两个 Task,各自干净 context:
- reviewer-design-a,负责轴A设计内容
- reviewer-design-b,负责轴B项目对齐
prompt:读 $skill/SKILL.md,按 stage=design;Source:$source;只负责指定轴;按 Return Contract 回 findings。
EOF
      ;;
    plan)
      cat <<EOF
单条消息并行派两个 Task,写者与验者分离:
- reviewer-plan-a,负责轴A覆盖与质量
- reviewer-plan-b,负责轴B合规与交叉验证
prompt:读 $skill/SKILL.md,按 stage=plan;Source:$source;只负责指定轴;按 Return Contract 回 findings。
EOF
      ;;
    final)
      if [ "$tier" = "1" ]; then
        cat <<EOF
派一个 Task:reviewer-final-a,依次覆盖基线2独立代码审计和基线1回归、意图、跨计划合同。
prompt:读 $skill/SKILL.md,按 stage=final;Source:$source;覆盖两条基线;按 Return Contract 回 findings。
EOF
      elif [ "$tier" = "2" ]; then
        cat <<EOF
单条消息并行派两个跨模型 Task:
- reviewer-final-a,基线1回归、意图、跨计划合同
- reviewer-final-b,基线2独立代码审计
prompt:读 $skill/SKILL.md,按 stage=final;Source:$source;只负责指定基线;按 Return Contract 回 findings。
EOF
      else
        cat <<EOF
单条消息并行派四个跨模型 Task,两条基线各跑两个模型:
- reviewer-final-a,基线1
- reviewer-final-b,基线1
- reviewer-final-a,基线2
- reviewer-final-b,基线2
prompt:读 $skill/SKILL.md,按 stage=final;Source:$source;只负责指定基线;按 Return Contract 回 findings。
同基线跨模型对账,单家重点必须亲验,两家同报提高置信。
EOF
      fi
      ;;
    merge-impl)
      cat <<EOF
单条消息并行派两个跨模型 Task:
- reviewer-final-a,跨 worktree 集成审路线1
- reviewer-final-b,跨 worktree 集成审路线2
prompt:读 $skill/SKILL.md,按 stage=merge-impl 走组合行为、合同、迁移、状态、import、回归、修复质量七角度;Source:$source;按 Return Contract 回 findings。
EOF
      ;;
    *) die "未覆盖 stage:$stage" ;;
  esac
}

cmd_start() {
  local stage="" source="" tier=0
  while [ $# -gt 0 ]; do case "$1" in
    --stage) stage="$2"; shift 2 ;;
    --source) source="${source}${source:+ }$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -n "$stage" ] || die "--stage 必填"
  [ -n "$source" ] || die "--source 必填"

  local kind views
  case "$stage" in
    design) kind=review; views="轴A设计内容 / 轴B项目对齐" ;;
    plan) kind=review; views="轴A覆盖与质量 / 轴B合规与交叉验证" ;;
    plan-impl) kind=contract-gate; views="跨计划合同兑现" ;;
    final) kind=review; views="基线1回归+意图+跨计划 / 基线2独立代码审计" ;;
    merge-impl) kind=review; views="跨 worktree 集成审七角度" ;;
    *) die "--stage 只能 design|plan|plan-impl|final|merge-impl" ;;
  esac

  local top state scenario brief trace loop_file
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  state="$(state_here)"
  scenario="$(jq -r '.scenario // ""' "$top/$state/task.json" 2>/dev/null || true)"
  brief="$top/$state/review-brief.md"
  trace="docs/reviews/<slug>-$stage.md"
  [ "$stage" = "merge-impl" ] && trace="$state/<slug>-merge-impl-review.md"
  mmw_ensure_state_ignore "$top"
  mkdir -p "$top/$state"

  loop_file="$top/$state/loop-state.json"
  if [ -f "$loop_file" ] && [ "$(jq -r '.kind // ""' "$loop_file")" = execution ]; then
    [ "$(bash "$LOOP" exit-check 2>/dev/null || true)" = DONE ] ||
      die "execution loop 未收束,拒绝起审"
  fi

  bash "$LOOP" close >&2
  if [ "$kind" = review ]; then
    bash "$LOOP" init --kind review --max-rounds 2 >&2
  else
    bash "$LOOP" init --kind contract-gate >&2
  fi

  echo "REVIEW_STARTED stage=$stage kind=$kind"
  echo "1. 从源文档抽覆盖清单:mmw loop checklist add --item <维度> --source <doc:line>"
  echo "2. 设置值守:mmw loop attendance --mode <attended|afk>"

  if [ "$kind" = contract-gate ]; then
    local file line body
    file="$(printf '%s\n' "$source" | grep -oE '[^[:space:]]+\.md' | head -1 || true)"
    [ -f "$file" ] || [ ! -f "$top/$file" ] || file="$top/$file"
    if [ -f "$file" ]; then
      line="$(grep -n '^## Cross-Plan Contract Anchors' "$file" | head -1 | cut -d: -f1 || true)"
      if [ -n "$line" ]; then
        body="$(sed -n "$((line+1)),\$p" "$file" | sed '/^## /q' | sed '/^## /d' |
          grep -vE '^[[:space:]]*(<!--.*-->)?[[:space:]]*$' || true)"
        if [ -z "$body" ] || { [ "$(printf '%s\n' "$body" | grep -c .)" -eq 1 ] && printf '%s' "$body" | grep -q '无跨计划共享合同'; }; then
          bash "$LOOP" checklist add --item no-cross-plan-contracts --source "$file:$line" >&2
          bash "$LOOP" checklist cover --item no-cross-plan-contracts --evidence "$file:$line(机器核实为空)" >&2
          echo "3. 合同 anchors 为空,已自动 cover;直接 handoff pass。"
          return
        fi
      fi
    fi
    echo "3. 读 references/review/plan-impl.md,核跨计划合同兑现后按出口收口。"
    return
  fi

  [ "$stage" = final ] && tier="$(final_tier "$top" "$state" "$scenario")"
  local skill dispatch
  skill="$(mmw_plugin_root)/skills/worktree-review"
  dispatch="$(dispatch_for "$stage" "$tier" "$source" "$skill")"
  cat > "$brief" <<EOF
# 审派发指南(stage=$stage · tier=$tier · Droid 原生)

Source:$source
视角:$views

## 派审者
$dispatch

在单条消息中并行发出独立 Task 调用，每个审者按当前工具合同直接返回结果。调用中断时重派对应视角，不假设后台 task ID、TaskOutput 或 resume。

## 留痕
把全部审者 findings 原样落盘 $trace,亲验后逐条标 accepted/rejected/duplicate/needs-evidence,文末写总 verdict。

## 亲验
每条 finding 由主线程 Read/Grep/运行命令坐实。覆盖维度:
  $MMW loop checklist cover --item <i> --evidence <file:line>
真实 finding:
  $MMW loop finding add --severity <C|I|M> --confidence <1-10> --locator <file:line>

## 收敛
全视角一轮无新高置信 finding 才收敛。未收敛执行:
  $MMW loop round next
方向或输入问题执行:
  $MMW loop surface --kind <needs-context|needs-redirection> --question "<...>"
只有 $MMW loop exit-check 返回 DONE 才允许 handoff pass。
EOF
  echo "3. 读 $brief 并按派发段直接派 reviewer droids。"
  echo "4. findings 留痕、亲验、收敛后再 handoff。"
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  *) die "用法:review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...>" ;;
esac

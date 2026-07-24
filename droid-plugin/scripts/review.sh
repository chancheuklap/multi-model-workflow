#!/usr/bin/env bash
# review.sh —— 起一道审(定编制 + 出派发指南,一条命令;Droid 原生)
#
#   start --stage <design|plan|plan-impl|final|merge-impl> --source <源意图路径/描述>
#       按阶段定视角与审者编制,把审派发指南写进状态目录 review-brief.md(主线程读它直接派审者)。
#       审者=Droid 会话内 reviewer droids(单条消息并行 Task),读已装的 worktree-review skill。
#
# 审不记账:收口看产物——findings 原样落盘 docs/reviews/<slug>-<stage>.md,亲验后标处置、写 verdict 段;
# 审闸 pass 时引擎只核「该文件在且含 verdict」(flow.sh),质量与 Critical 处置是主线程判断。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"
# shellcheck source=lib/retrieval-candidates.sh
. "$SCRIPT_DIR/lib/retrieval-candidates.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""

die() { echo "ERROR: $*" >&2; exit 1; }

state_here() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  mmw_resolve_state_subdir "$top"
}

dispatch_for() {
  local stage="$1" source="$2" skill="$3"
  case "$stage" in
    design)
      cat <<EOF
单条消息并行派两个 Task,各自干净 context:
- reviewer-design-a,负责轴A 设计内容
- reviewer-design-b,负责轴B 项目对齐
prompt(纯路由,不内联审查方法):读 $skill/SKILL.md,按 stage=design 审;Source:$source;只负责指定轴;按 Return Contract 回结构化 findings。
EOF
      ;;
    plan)
      cat <<EOF
单条消息并行派两个 Task,写者与审者分离(计划由 plan-writer 写,审者另派):
- reviewer-plan-a,负责轴A 覆盖与质量
- reviewer-plan-b,负责轴B 合规与交叉验证
prompt(纯路由,不内联审查方法):读 $skill/SKILL.md,按 stage=plan 审;Source:$source;只负责指定轴;按 Return Contract 回结构化 findings。
EOF
      ;;
    final)
      cat <<EOF
单条消息并行派四个跨模型 Task,两条基线各跑两个模型:
- reviewer-final-a,基线1(回归+意图+跨plan)
- reviewer-final-b,基线1
- reviewer-final-a,基线2(独立代码审计,全新眼光)
- reviewer-final-b,基线2
prompt(纯路由,四审者读同一份方法论):读 $skill/SKILL.md,按 stage=final 审;Source:$source;只负责指定基线;按 Return Contract 回结构化 findings。
同基线跨模型对账:只一家报出的重点亲验,两家同报的置信升。
EOF
      ;;
    merge-impl)
      cat <<EOF
单条消息并行派两个跨模型 Task:
- reviewer-final-a,跨 worktree 集成审路线1
- reviewer-final-b,跨 worktree 集成审路线2
prompt:读 $skill/SKILL.md,按 stage=merge-impl 走组合行为、合同、迁移、状态、import、回归、修复质量七角度;Source:$source;按 Return Contract 回结构化 findings。
EOF
      ;;
    *) die "未覆盖 stage:$stage" ;;
  esac
}

cmd_start() {
  local stage="" retrieval=""; local -a sources=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage)  stage="$2";  shift 2 ;;
      --source) sources+=("$2"); shift 2 ;;
      --retrieval-candidates) retrieval="$2"; shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$stage" ]  || die "--stage 必填(design|plan|plan-impl|final|merge-impl)"
  [ "${#sources[@]}" -gt 0 ] || die "--source 必填(源意图路径/描述,派给审者用;可重复)"

  local views
  case "$stage" in
    design)     views="轴A 设计内容 / 轴B 项目对齐" ;;
    plan)       views="轴A 覆盖与质量 / 轴B 合规与交叉验证" ;;
    plan-impl)  views="(③合同门:机器核合同兑现,不派审者判断)" ;;
    final)      views="基线1 回归+意图+跨plan / 基线2 独立代码审计" ;;
    merge-impl) views="跨 PR 集成审 7 角度(组合行为/合同/迁移/状态/import/回归/修复质量)" ;;
    *) die "--stage 只能 design|plan|plan-impl|final|merge-impl" ;;
  esac

  local top state brief slug
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  state="$(state_here)"
  local man prototype_status rel existing already
  man="$top/$state/task.json"
  prototype_status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$man" 2>/dev/null || true)"
  # 设计预审顺序机器化:phase=design 的预审必须在 prototype accepted 之后
  # (design-self-check 声明的顺序,不再只靠文档纪律;过门后的设计复审不在此限)。
  if [ "$stage" = design ] && [ "$(jq -r '.phase // empty' "$man" 2>/dev/null || true)" = design ] \
     && [ "$prototype_status" != accepted ]; then
    die "设计预审前 prototype 必须 accepted(当前:${prototype_status:-未启动});先按 mmw where 完成 prototype 迭代"
  fi
  if [ "$stage" = design ] && [ "$prototype_status" = accepted ]; then
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      mmw_prototype_validate_downstream_material "$top" "$man" "$rel" \
        || die "设计预审 prototype 材料无效:$rel"
      already=false
      for existing in "${sources[@]}"; do [ "$existing" = "$rel" ] && already=true; done
      $already || sources+=("$rel")
    done < <(mmw_prototype_selected_relpaths "$man")
  fi
  local source; source="${sources[*]}"
  slug="$(jq -r '.slug // "<slug>"' "$top/$state/task.json" 2>/dev/null || echo "<slug>")"
  brief="$top/$state/review-brief.md"
  mmw_ensure_state_ignore "$top"
  mkdir -p "$top/$state"
  local retrieval_snapshot="$top/$state/retrieval-candidates-$stage.json"
  mmw_retrieval_candidates_snapshot "$retrieval" "$retrieval_snapshot" || die "结构候选校验失败"

  # 留痕落点:任务审(worktree 内)走 docs/reviews/(docs/.gitignore 已忽略);
  # merge-impl 在主仓库跑,不落 docs/ ——一切主仓库产物进状态平面,零残留。
  local trace="docs/reviews/$slug-$stage.md"
  [ "$stage" = "merge-impl" ] && trace="$state/$slug-merge-impl-review.md"

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
REVIEW_STARTED stage=plan-impl host=droid
③合同门不派审者、不列 pack:**读 references/review/plan-impl.md,照它走**——核什么(跨 plan 合同兑现)、
三个出口(全兑现 pass / 没兑现回 build / 合同根上错回 design)全在那份。
核对过程与逐条兑现证据写进 $trace(含一句总 verdict);兑现全 → $MMW handoff --conclusion pass。
EOF
    return 0
  fi

  # ---- 派发指南落文件(brief 不过主线程 context)----
  local skill dispatch
  skill="$(mmw_plugin_root)/skills/worktree-review"
  dispatch="$(dispatch_for "$stage" "$source" "$skill")"

  cat > "$brief" <<EOF
# 审派发指南(stage=$stage · host=droid · 机器生成,主线程读完直接派审者)

主线程直接派审者,自己亲验收敛,不自己写产物结论。审不记账,收口看产物(下方留痕)。
Source: ${source}

$(mmw_retrieval_candidates_prompt "$retrieval_snapshot")

## 派审者
$dispatch

在单条消息中并行发出独立 Task 调用,每个审者按当前工具合同直接返回结果。
调用中断时重派对应视角,不假设后台 task ID 或 resume。
派审者时在每个 task 写明:遵守 worktree-review method——一次审透本视角全部承重问题;报全≠报噪;Minor 标 blocking=no;按 Return Contract 回。

## 留痕(收口的硬核就在这份文件)
把全部审者的结构化 findings **原样落盘** $trace(不重写不摘要,保真);
亲验后把每条 verdict/处置(accepted/rejected/duplicate/needs-evidence/waived)就近标该条下,文末写一句总 verdict。
审闸收口 handoff pass 时引擎核该文件存在且含 verdict——没有留痕 = 审没跑过,不放行。
收口只回读这份文档的 verdict 段,findings 全文压在 trace 文件里、不长驻主线程 context。

## 收回亲验(裁判权在主线程)
审者是劳动力不是信源,也不是放行权人。对每条 finding:
1. 自己 Read/Grep/跑坐实;引不出 file:line → rejected 或 needs-evidence。
2. 过四问:是否过度设计/过度考虑?不修的真实后果(谁受伤)?边际收益?现在是否值得修(第2轮起还要问相对上轮的承重增量)?
3. 标处置:accepted|rejected|duplicate|needs-evidence|waived(理由必填)。
硬纪律:只有 accepted 驱动 needs-repair;Critical 必须处置(修或有理 reject/waive);Minor/non-blocking 默认 waived;不要因为 Nit 未清就 needs-repair。
放行标准:整体在变好 + 无开口 Critical + 无未修 accepted 承重项,不追求完美。

## 收敛
无新高置信 accepted = 收敛。审闸 repair_count 触顶由引擎 GUARD,到顶交人并亮未收敛/已 waive 清单,别硬磨。
方向疑/缺输入 → handoff needs-redirection / needs-context 交上去,别当产物缺陷修。
EOF

  # 复审收敛:已有留痕或 repair_count>0 → brief 追加 prior_trace 规则
  local rc_now=0
  rc_now="$(jq -r '.repair_count // 0' "$top/$state/task.json" 2>/dev/null || echo 0)"
  case "$rc_now" in ''|*[!0-9]*) rc_now=0 ;; esac
  if [ -f "$top/$trace" ] || [ "$rc_now" -gt 0 ]; then
    cat >> "$brief" <<EOF

## 本轮是 re-review
上一轮留痕: $trace
派审者时在每个 task 写明:stage=$stage; re-review=yes; prior_trace=$trace; 只验证 accepted 已修 + 修复 diff 回归;已 rejected/waived/duplicate 无新证据不得重提;不对未改区域起新 Nit。
EOF
  fi

  cat <<EOF
REVIEW_STARTED stage=$stage host=droid
1. 主线程读 $brief,按「派审者」段直接派(单条消息并行 Task,读 worktree-review skill 出结构化 findings)。
2. findings 原样落 $trace,亲验标处置、写总 verdict(收口硬核:该文件在且含 verdict)。
3. 收口回 review/review.md 按 Gap 选结论词 handoff。
EOF
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...>" ;;
esac

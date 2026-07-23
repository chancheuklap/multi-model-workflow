#!/usr/bin/env bash
# review.sh —— 起一道审(定编制 + 出派发指南,一条命令;pi 原生)
#
#   start --stage <design|plan|plan-impl|final|merge-impl> --source <源意图路径/描述>
#       按阶段定视角与审者编制,把审派发指南写进状态目录 review-brief.md(主线程读它直接派审者)。
#       审者=pi 会话内经 pi-subagents 的 subagent 工具 tasks 数组并行派发(agent 直接用花名册角色名,
#       model/工具白名单由已注册的 agents-roster frontmatter 提供),读已装的 worktree-review skill。
#   clean-check --worktree <路径> --baseline <工作树指纹>
#       审收口边界闸(写者≠审者的硬实现,弥补 pi 无只读沙盒):审后 HEAD、tracked diff、
#       untracked 文件集合与内容必须和审前完全一致；审前已有设计稿可保留。
#
# 审不记账:收口看产物——findings 原样落盘 docs/reviews/<slug>-<stage>.md,亲验后标处置、写 verdict 段;
# 审闸 pass 时引擎核「该文件在且含 verdict」+ clean-check 边界闸(flow.sh),质量与 Critical 处置是主线程判断。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""

die() { echo "ERROR: $*" >&2; exit 1; }

state_here() {
  local top; top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  mmw_resolve_state_subdir "$top"
}

# 审收口边界闸:审期间 worktree 必须原封不动。指纹覆盖 HEAD、tracked diff、
# untracked 路径和内容，允许审前已有未提交文件，但审者不能改变它们。
review_worktree_fingerprint() {
  local wt="$1" rel
  {
    git -C "$wt" rev-parse HEAD
    git -C "$wt" diff --binary HEAD --
    while IFS= read -r -d '' rel; do
      printf 'untracked:%s\0' "$rel"
      git -C "$wt" hash-object --no-filters -- "$rel"
    done < <(git -C "$wt" ls-files --others --exclude-standard -z)
  } | shasum -a 256 | awk '{print $1}'
}

review_worktree_clean_check() {  # $1=worktree $2=baseline_fingerprint
  local wt="$1" baseline="$2" current dirty
  [ -d "$wt" ] || { echo "REVIEW_BOUNDARY_VIOLATION: worktree 不存在:$wt" >&2; return 3; }
  [ -n "$baseline" ] || { echo "REVIEW_BOUNDARY_VIOLATION: 缺审前工作树指纹" >&2; return 3; }
  current="$(review_worktree_fingerprint "$wt")" || return 3
  [ "$current" = "$baseline" ] && return 0
  dirty="$(git -C "$wt" status --porcelain --untracked-files=all 2>/dev/null || true)"
  {
    echo "REVIEW_BOUNDARY_VIOLATION: 审期间 worktree 被改动:$wt"
    echo "  工作树指纹变化: baseline=$baseline current=$current"
    [ -z "$dirty" ] || { echo "  当前 git status --porcelain:"; printf '%s\n' "$dirty" | sed 's/^/    /'; }
  } >&2
  return 3
}

cmd_clean_check() {
  local wt="" baseline=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --worktree) wt="$2"; shift 2 ;;
      --baseline) baseline="$2"; shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$wt" ] || die "--worktree 必填"
  [ -n "$baseline" ] || die "--baseline 必填(审前工作树指纹)"
  review_worktree_clean_check "$wt" "$baseline"
}

dispatch_for() {
  local stage="$1" source="$2" skill="$3"
  case "$stage" in
    design)
      cat <<EOF
单次 subagent 调用、tasks 数组并行两个审者(pi-subagents,按名字派,model 由 agent 定义自带),各自干净 context:
- tasks[0]: agent=reviewer-design-a,负责轴A 设计内容
- tasks[1]: agent=reviewer-design-b,负责轴B 项目对齐
每个 task(纯路由,不内联审查方法):读 $skill/SKILL.md,按 stage=design 审;Source:$source;只负责指定轴;按 Return Contract 回结构化 findings。
EOF
      ;;
    plan)
      cat <<EOF
单次 subagent 调用、tasks 数组并行两个审者(pi-subagents,按名字派,model 由 agent 定义自带),写者与审者分离(计划由 plan-writer 写,审者另派):
- tasks[0]: agent=reviewer-plan-a,负责轴A 覆盖与质量
- tasks[1]: agent=reviewer-plan-b,负责轴B 合规与交叉验证
每个 task(纯路由,不内联审查方法):读 $skill/SKILL.md,按 stage=plan 审;Source:$source;只负责指定轴;按 Return Contract 回结构化 findings。
EOF
      ;;
    final)
      cat <<EOF
单次 subagent 调用、tasks 数组并行四个跨模型审者(pi-subagents,按名字派,model 由 agent 定义自带),两条基线各跑两个模型:
- tasks[0]: agent=reviewer-final-a, label=基线1(回归+意图+跨plan)
- tasks[1]: agent=reviewer-final-b, label=基线1
- tasks[2]: agent=reviewer-final-a, label=基线2(独立代码审计,全新眼光)
- tasks[3]: agent=reviewer-final-b, label=基线2
每个 task(纯路由,四审者读同一份方法论):读 $skill/SKILL.md,按 stage=final 审;Source:$source;只负责指定基线;按 Return Contract 回结构化 findings。
同基线跨模型对账:只一家报出的重点亲验,两家同报的置信升。
EOF
      ;;
    merge-impl)
      cat <<EOF
单次 subagent 调用、tasks 数组并行两个跨模型审者(pi-subagents,按名字派,model 由 agent 定义自带):
- tasks[0]: agent=reviewer-final-a, label=跨 worktree 集成审路线1
- tasks[1]: agent=reviewer-final-b, label=跨 worktree 集成审路线2
每个 task:读 $skill/SKILL.md,按 stage=merge-impl 走组合行为、合同、迁移、状态、import、回归、修复质量七角度;Source:$source;按 Return Contract 回结构化 findings。
EOF
      ;;
    *) die "未覆盖 stage:$stage" ;;
  esac
}

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

  # 审前工作树指纹落盘:收口时核审者没有改变任何 tracked/untracked 内容。
  local baseline_sha baseline_fingerprint baseline_tmp
  baseline_sha="$(git -C "$top" rev-parse HEAD)" || die "无法取审前基线 sha"
  baseline_fingerprint="$(review_worktree_fingerprint "$top")" || die "无法取审前工作树指纹"
  baseline_tmp="$(mktemp "$top/$state/.review-baseline.XXXXXX")" || die "无法写审前基线"
  jq -n --arg sha "$baseline_sha" --arg fingerprint "$baseline_fingerprint" --arg stage "$stage" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{sha:$sha,fingerprint:$fingerprint,stage:$stage,at:$at}' >"$baseline_tmp" \
    && mv "$baseline_tmp" "$top/$state/review-baseline.json" \
    || { rm -f "$baseline_tmp"; die "无法写审前基线"; }

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
REVIEW_STARTED stage=plan-impl host=pi
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
# 审派发指南(stage=$stage · host=pi · 机器生成,主线程读完直接派审者)

主线程直接派审者,自己亲验收敛,不自己写产物结论。审不记账,收口看产物(下方留痕)。
Source: ${source}

## 派审者
$dispatch

一次 subagent 调用 tasks 数组并行发出,前台等全部审者返回。
调用中断时重派对应视角;审者无状态读,不需 resume。
派审者时在每个 task 写明:遵守 worktree-review method——一次审透本视角全部承重问题;报全≠报噪;Minor 标 blocking=no;按 Return Contract 回。

## 留痕(收口的硬核就在这份文件)
把全部审者的结构化 findings **原样落盘** $trace(不重写不摘要,保真);
亲验后把每条 verdict/处置(accepted/rejected/duplicate/needs-evidence/waived)就近标该条下,文末写一句总 verdict。
审闸收口 handoff pass 时引擎核该文件存在且含 verdict,并跑 clean-check 核 worktree
与审前基线一致(审者只读是纪律,这里是机器闸)——没有留痕 = 审没跑过,不放行。
收口只回读这份文档的 verdict 段,findings 全文压在 trace 文件里、不长驻主线程 context。

## 收回亲验(裁判权在主线程)
审者是劳动力不是信源,也不是放行权人。对每条 finding:
1. 自己 read/grep/跑坐实;引不出 file:line → rejected 或 needs-evidence。
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
REVIEW_STARTED stage=$stage host=pi
1. 主线程读 $brief,按「派审者」段直接派(单次 subagent 调用 tasks 数组并行,读 worktree-review skill 出结构化 findings)。
2. findings 原样落 $trace,亲验标处置、写总 verdict(收口硬核:该文件在且含 verdict)。
3. 收口回 review/review.md 按 Gap 选结论词 handoff。
EOF
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  clean-check) shift; cmd_clean_check "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...> | review.sh clean-check --worktree <路径> --baseline <工作树指纹>" ;;
esac

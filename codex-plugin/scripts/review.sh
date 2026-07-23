#!/usr/bin/env bash
# Codex 原生审查编排：生成 provider-neutral slots 和完整审查 prompt。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"
MMW="bash \"$SCRIPT_DIR/mmw.sh\""

die() { echo "ERROR: $*" >&2; exit 1; }

state_here() {
  local top
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  mmw_resolve_state_subdir "$top"
}

review_worktree_fingerprint() {
  local worktree="$1" rel
  {
    git -C "$worktree" rev-parse HEAD
    git -C "$worktree" diff --binary HEAD --
    while IFS= read -r -d '' rel; do
      printf 'untracked:%s\0' "$rel"
      git -C "$worktree" hash-object --no-filters -- "$rel"
    done < <(git -C "$worktree" ls-files --others --exclude-standard -z)
  } | shasum -a 256 | awk '{print $1}'
}

cmd_clean_check() {
  local worktree="" baseline="" current dirty
  while [ $# -gt 0 ]; do
    case "$1" in
      --worktree) worktree="$2"; shift 2 ;;
      --baseline) baseline="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  [ -d "$worktree" ] || die "REVIEW_BOUNDARY_VIOLATION: worktree 不存在:$worktree"
  [ -n "$baseline" ] || die "REVIEW_BOUNDARY_VIOLATION: 缺审前工作树指纹"
  current="$(review_worktree_fingerprint "$worktree")"
  [ "$current" = "$baseline" ] && return 0
  dirty="$(git -C "$worktree" status --porcelain --untracked-files=all 2>/dev/null || true)"
  {
    echo "REVIEW_BOUNDARY_VIOLATION: 审期间 worktree 被改动:$worktree"
    echo "  baseline=$baseline current=$current"
    [ -z "$dirty" ] || printf '%s\n' "$dirty" | sed 's/^/  /'
  } >&2
  return 3
}

stage_reference() {
  case "$1" in
    design) printf 'design.md' ;;
    plan) printf 'plan.md' ;;
    final) printf 'final.md' ;;
    merge-impl) printf 'merge.md' ;;
    *) return 1 ;;
  esac
}

safe_task_name() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_]/_/g'
}

render_prompt() {
  local stage="$1" view="$2" source="$3" output="$4"
  local plugin_root skill_root stage_ref worktree
  plugin_root="$(mmw_plugin_root)"
  skill_root="$plugin_root/skills/worktree-review"
  stage_ref="$(stage_reference "$stage")" || die "无法渲染 stage:$stage"
  worktree="$(git rev-parse --show-toplevel)"
  {
    cat "$plugin_root/agents-roster/reviewer.md"
    printf '\n<dispatch>\nworktree: %s\nstage: %s\nview: %s\nsource: %s\n所有命令都明确在 worktree 绝对路径下运行。\n</dispatch>\n\n' \
      "$worktree" "$stage" "$view" "$source"
    printf '%s\n' \
      "<worktree-review-skill>" \
      "以下内容是本次审查唯一方法权威。"
    cat "$skill_root/SKILL.md"
    printf '\n<shared-method>\n'
    cat "$skill_root/references/method.md"
    printf '\n<stage-method>\n'
    cat "$skill_root/references/$stage_ref"
    printf '\n</stage-method>\n</shared-method>\n</worktree-review-skill>\n'
  } >"$output"
}

add_slot() {
  local slots="$1" prompts="$2" results="$3" stage="$4" provider="$5" id="$6" view="$7" source="$8"
  local prompt result task temp
  prompt="$prompts/$id.md"
  result="$results/$id.md"
  task="$(safe_task_name "review_${stage}_${id}")"
  render_prompt "$stage" "$view" "$source" "$prompt"
  temp="$slots.tmp.$$"
  jq \
    --arg id "$id" \
    --arg provider "$provider" \
    --arg stage "$stage" \
    --arg view "$view" \
    --arg task "$task" \
    --arg prompt "$prompt" \
    --arg result "$result" \
    '. + [{id:$id,provider:$provider,stage:$stage,view:$view,task_name:$task,
           prompt_file:$prompt,result_file:$result}]' \
    "$slots" >"$temp" \
    && mv "$temp" "$slots" \
    || { rm -f "$temp"; die "无法写 review slot:$id"; }
}

append_design_prototype_sources() {
  local top="$1" manifest="$2"
  shift 2
  local -a current=("$@")
  local status rel existing duplicate
  status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$manifest" 2>/dev/null || true)"
  [ "$status" = accepted ] || { printf '%s\n' "${current[@]}"; return 0; }
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_prototype_validate_downstream_material "$top" "$manifest" "$rel" \
      || { echo "ERROR: 设计预审 prototype 材料无效:$rel" >&2; return 1; }
    duplicate=false
    for existing in "${current[@]}"; do
      [ "$existing" = "$rel" ] && duplicate=true
    done
    $duplicate || current+=("$rel")
  done < <(mmw_prototype_selected_relpaths "$manifest")
  printf '%s\n' "${current[@]}"
}

write_baseline() {
  local top="$1" state="$2" temp
  temp="$(mktemp "$top/$state/.review-baseline.XXXXXX")"
  jq -n \
    --arg sha "$(git -C "$top" rev-parse HEAD)" \
    --arg fingerprint "$(review_worktree_fingerprint "$top")" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{sha:$sha,fingerprint:$fingerprint,at:$at}' >"$temp" \
    && mv "$temp" "$top/$state/review-baseline.json" \
    || { rm -f "$temp"; die "无法写审前基线"; }
}

contract_gate() {
  local top="$1" state="$2" trace="$3"
  shift 3
  local -a sources=("$@")
  local source_file="" line="" body=""
  source_file="$(printf '%s\n' "${sources[@]}" | grep -oE '[^[:space:]]+\.md' | head -1 || true)"
  [ -n "$source_file" ] && [ ! -f "$source_file" ] && [ -f "$top/$source_file" ] \
    && source_file="$top/$source_file"
  if [ -n "$source_file" ] && [ -f "$source_file" ]; then
    line="$(grep -n '^## Cross-Plan Contract Anchors' "$source_file" | head -1 | cut -d: -f1 || true)"
    if [ -n "$line" ]; then
      body="$(sed -n "$((line + 1)),\$p" "$source_file" | sed '/^## /q' | sed '/^## /d' \
        | grep -vE '^[[:space:]]*(<!--.*-->)?[[:space:]]*$' || true)"
      if [ -z "$body" ] \
        || { [ "$(printf '%s\n' "$body" | grep -c .)" -eq 1 ] && printf '%s' "$body" | grep -q '无跨计划共享合同'; }; then
        printf '%s\n' \
          "CONTRACT_GATE_EMPTY(脚本机械核实 anchors 节为空:$source_file:$line)" \
          "③合同门无跨计划合同，直接回 build 收尾:$MMW handoff --conclusion pass。"
        return 0
      fi
    fi
  fi
  printf '%s\n' \
    "REVIEW_STARTED stage=plan-impl host=codex" \
    "③合同门不派审者。读 references/review/plan-impl.md，核对过程与 verdict 写进 ${trace}；全兑现后运行 $MMW handoff --conclusion pass。"
}

write_brief() {
  local brief="$1" slots="$2" top="$3" trace="$4" stage="$5" source="$6" adapter="$7"
  {
    printf '# 审派发指南(stage=%s · host=codex)\n\n' "$stage"
    printf '%s\n' \
      "Source: $source" \
      "" \
      "## 派审者" \
      "" \
      "所有 slot 相互独立。先启动全部 native spawn_agent 和第二模型 exec_command，再等待；禁止串行审。"
    while IFS= read -r row; do
      local provider id view task prompt result
      provider="$(jq -r .provider <<<"$row")"
      id="$(jq -r .id <<<"$row")"
      view="$(jq -r .view <<<"$row")"
      task="$(jq -r .task_name <<<"$row")"
      prompt="$(jq -r .prompt_file <<<"$row")"
      result="$(jq -r .result_file <<<"$row")"
      if [ "$provider" = native ]; then
        printf -- '- %s (%s): `spawn_agent(task_name="%s", fork_turns="none", message=<读取 %s 全文>)`。\n' \
          "$id" "$view" "$task" "$prompt"
      else
        printf -- '- %s (%s): `exec_command(cmd="bash %s --worktree %s < %s > %s")`；非零、空输出或超时即该 slot 失败，不得替换 provider。\n' \
          "$id" "$view" "$adapter" "$top" "$prompt" "$result"
      fi
    done < <(jq -c '.[]' "$slots")
    cat <<EOF

每个 prompt 都已经完整包含同一份 worktree-review 方法、当前 stage 角度、Source 和 Return Contract。
审者中断时只重派该 slot；当轮 native 返问可 followup_task，跨会话按 prompt 重新派干净审者。

## 留痕与亲验

把全部结构化 findings 原样落盘 ${trace}。主线程逐条核 locator 和原文，再就近标
accepted、rejected、duplicate、needs-evidence 或 waived；文末写总 verdict。
只有 accepted 驱动 needs-repair。Critical 必须明确处置，Minor/non-blocking 默认
waived。收口时 flow 会核 trace 含 verdict，并用 review clean-check 确认被审
worktree 与审前指纹一致。

## 收敛

无新高置信 accepted 即收敛。方向错误或缺输入分别 handoff needs-redirection /
needs-context；返工轮次和重复 finding 指纹继续由流程引擎限制。
EOF
  } >"$brief"
}

cmd_start() {
  local stage=""
  local -a sources=()
  while [ $# -gt 0 ]; do
    case "$1" in
      --stage) stage="$2"; shift 2 ;;
      --source) sources+=("$2"); shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  [ -n "$stage" ] || die "--stage 必填"
  [ "${#sources[@]}" -gt 0 ] || die "--source 必填"
  case "$stage" in
    design|plan|plan-impl|final|merge-impl) ;;
    *) die "--stage 只能 design|plan|plan-impl|final|merge-impl" ;;
  esac

  local top state manifest slug scenario trace source brief slots prompts results adapter
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || die "不在 git 仓库内"
  state="$(state_here)"
  manifest="$top/$state/task.json"
  slug="$(jq -r '.slug // "<slug>"' "$manifest" 2>/dev/null || printf '<slug>')"
  scenario="$(jq -r '.scenario // ""' "$manifest" 2>/dev/null || true)"
  trace="docs/reviews/$slug-$stage.md"
  [ "$stage" = merge-impl ] && trace="$state/$slug-merge-impl-review.md"
  if [ "$stage" = plan-impl ]; then
    contract_gate "$top" "$state" "$trace" "${sources[@]}"
    return
  fi

  [ -n "${MMW_SECOND_REVIEW_CMD:-}" ] \
    || die "本阶段需要第二审查模型；先配置 MMW_SECOND_REVIEW_CMD"
  adapter="$SCRIPT_DIR/second-review.sh"
  [ -f "$adapter" ] || die "第二模型 Adapter 缺失:$adapter"
  if [ "$stage" = design ] && [ -f "$manifest" ]; then
    local -a expanded_sources=()
    local expanded_source expanded_file
    expanded_file="$(mktemp "${TMPDIR:-/tmp}/mmw-review-sources.XXXXXX")"
    if ! append_design_prototype_sources "$top" "$manifest" "${sources[@]}" >"$expanded_file"; then
      rm -f "$expanded_file"
      die "设计预审 prototype 材料校验失败"
    fi
    while IFS= read -r expanded_source; do
      [ -n "$expanded_source" ] && expanded_sources+=("$expanded_source")
    done <"$expanded_file"
    rm -f "$expanded_file"
    sources=("${expanded_sources[@]}")
  fi
  source="${sources[*]}"

  mmw_ensure_state_ignore "$top"
  mkdir -p "$top/$state"
  write_baseline "$top" "$state"
  brief="$top/$state/review-brief.md"
  slots="$top/$state/review-slots.json"
  prompts="$top/$state/review-prompts"
  results="$top/$state/review-results"
  mkdir -p "$prompts" "$results"
  printf '[]\n' >"$slots"

  case "$stage" in
    design)
      add_slot "$slots" "$prompts" "$results" "$stage" second design_a "轴A 设计内容" "$source"
      add_slot "$slots" "$prompts" "$results" "$stage" second design_b "轴B 项目对齐" "$source"
      ;;
    plan)
      add_slot "$slots" "$prompts" "$results" "$stage" second plan_a "轴A 覆盖与质量" "$source"
      add_slot "$slots" "$prompts" "$results" "$stage" second plan_b "轴B 合规与交叉验证" "$source"
      ;;
    final)
      if [ "$scenario" = small-change ] || [ "$scenario" = bug ]; then
        add_slot "$slots" "$prompts" "$results" "$stage" second final_both \
          "基线1 回归+意图+跨plan；基线2 独立代码审计" "$source"
      else
        local tier=4 base task_slug plan_dir capable diff_lines
        base="$(jq -r '.base_commit // empty' "$manifest" 2>/dev/null || true)"
        task_slug="$(jq -r '.slug // empty' "$manifest" 2>/dev/null || true)"
        plan_dir="$top/docs/plans/$task_slug"
        if [ -n "$base" ] && [ -d "$plan_dir" ]; then
          capable="$(grep -rlEi '(complexity|复杂度).*capable' "$plan_dir" 2>/dev/null || true)"
          diff_lines="$(git -C "$top" diff --shortstat "$base"..HEAD 2>/dev/null \
            | { grep -oE '[0-9]+ (insertion|deletion)' || true; } \
            | awk '{sum += $1} END {print sum + 0}')"
          [ -n "$capable" ] || [ "${diff_lines:-0}" -gt "${REVIEW_TIER_DIFF_MAX:-800}" ] || tier=2
        fi
        add_slot "$slots" "$prompts" "$results" "$stage" second final_base1_second "基线1 回归+意图+跨plan" "$source"
        if [ "$tier" -eq 2 ]; then
          add_slot "$slots" "$prompts" "$results" "$stage" native final_base2_native "基线2 独立代码审计" "$source"
        else
          add_slot "$slots" "$prompts" "$results" "$stage" native final_base1_native "基线1 回归+意图+跨plan" "$source"
          add_slot "$slots" "$prompts" "$results" "$stage" second final_base2_second "基线2 独立代码审计" "$source"
          add_slot "$slots" "$prompts" "$results" "$stage" native final_base2_native "基线2 独立代码审计" "$source"
        fi
      fi
      ;;
    merge-impl)
      add_slot "$slots" "$prompts" "$results" "$stage" native merge_native "跨 PR 集成审七角度 路线1" "$source"
      add_slot "$slots" "$prompts" "$results" "$stage" second merge_second "跨 PR 集成审七角度 路线2" "$source"
      ;;
  esac

  write_brief "$brief" "$slots" "$top" "$trace" "$stage" "$source" "$adapter"
  local repair_count=0
  repair_count="$(jq -r '.repair_count // 0' "$manifest" 2>/dev/null || printf 0)"
  case "$repair_count" in ''|*[!0-9]*) repair_count=0 ;; esac
  if [ -f "$top/$trace" ] || [ "$repair_count" -gt 0 ]; then
    cat >>"$brief" <<EOF

## 本轮是 re-review

prior_trace: $trace
每个 slot 只验证 accepted 已修和修复 diff 回归；已 rejected、waived、duplicate
没有新证据不得重提，不对未改区域起新 Nit。
EOF
  fi

  printf '%s\n' \
    "REVIEW_STARTED stage=$stage host=codex" \
    "SLOTS_FILE=$slots" \
    "BRIEF_FILE=$brief" \
    "TRACE_FILE=$trace" \
    "NEXT=按 brief 先并行启动全部 slot；回执齐后亲验、落 trace、写 verdict，再回 review/review.md 选 handoff 结论。"
}

case "${1:-}" in
  start) shift; cmd_start "$@" ;;
  clean-check) shift; cmd_clean_check "$@" ;;
  *) die "用法: review.sh start --stage <design|plan|plan-impl|final|merge-impl> --source <...> | review.sh clean-check --worktree <路径> --baseline <指纹>" ;;
esac

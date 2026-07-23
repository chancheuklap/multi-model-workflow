#!/usr/bin/env bash
# Droid exec 写码工人和写计划工人派发器。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"
# shellcheck source=lib/droid-exec.sh
. "$SCRIPT_DIR/lib/droid-exec.sh"

EXECUTOR_DROID="${DROID_EXECUTOR_DROID:-pack-executor}"
EXECUTOR_MODEL="${DROID_EXECUTOR_MODEL:-custom:GPT-5.6-Terra-[Codex]-0}"
EXECUTOR_EFFORT="${DROID_EXECUTOR_EFFORT:-high}"
CAPABLE_EXECUTOR_DROID="${DROID_CAPABLE_EXECUTOR_DROID:-pack-executor-capable}"
CAPABLE_EXECUTOR_MODEL="${DROID_CAPABLE_EXECUTOR_MODEL:-custom:GPT-5.6-Sol-[Codex]-0}"
CAPABLE_EXECUTOR_EFFORT="${DROID_CAPABLE_EXECUTOR_EFFORT:-medium}"
PLAN_DROID="${DROID_PLAN_DROID:-plan-writer}"
PLAN_MODEL="${DROID_PLAN_MODEL:-custom:GPT-5.6-Sol-[Codex]-0}"
PLAN_EFFORT="${DROID_PLAN_EFFORT:-high}"
WORKER_ALLOWED_TOOLS="read-cli,create-cli,edit-cli,apply-patch-cli,execute-cli,grep_tool_cli,glob-search-cli,ls-cli,skill"

die() { echo "ERROR: $*" >&2; exit 2; }
state_for() { mmw_resolve_state_subdir "$1"; }
plan_ns() { basename "$1" .md; }

# 派发前自检(机器可核验的事实,缺装备当场报错,不让工人开工后才发现):
# 点名的 plugin skill 真实存在(工人 prompt 指它当总纲)。
preflight_plugin_skill() {  # $1=skill 名
  local sk="$(mmw_plugin_root)/skills/$1/SKILL.md"
  [ -f "$sk" ] || die "preflight:工人 skill 缺失($sk 不存在);plugin 安装不完整,先修再派"
}
# 定位仓库测试薄层(机械活归脚本,工人不漫山遍野找):TESTING.md 在 worktree 根或 tests/ 下。
# 回显相对路径;找不到回显空(prompt 会声明 no-repo-test-sheet)。
locate_test_sheet() {  # $1=worktree
  local c
  for c in TESTING.md tests/TESTING.md docs/TESTING.md; do
    [ -f "$1/$c" ] && { echo "$c"; return 0; }
  done
  echo ""
}
test_sheet_lines() {  # $1=薄层相对路径(可空)
  if [ -n "$1" ]; then
    echo "- 仓库测试薄层(本仓库测试事实:目录分层/外部接缝/权威源/门控): $1"
  else
    echo "- 仓库无测试薄层:测试写法按 worktree-build/worktree-plan skill 里的测试写作权威;落点随仓库既有目录惯例;收工回执标 no-repo-test-sheet。"
  fi
}

prepare_exec_policy() {
  local pkg="$1" model="$2" inventory="$pkg/tool-inventory.json"
  mmw_droid_load_tool_inventory "$inventory" "$model" \
    || die "无法读取 worker Droid tool inventory:$model"
  mmw_droid_disable_all_except "$WORKER_ALLOWED_TOOLS" "$inventory"
}

render_droid_prompt() {
  local source="$1" target="$2"
  mmw_droid_render_prompt "$source" "$target" || die "droid prompt 为空:$source"
}

native_worktree_path() {
  local repo="$1" root="$2" branch="$3"
  printf '%s/%s-wt-%s' "$root" "$(basename "$repo")" "${branch//\//-}"
}

# 讨论态材料从设计路径与 manifest 机械推导；prototype 只传 accepted 的日志与 selected。
design_dir_of() {
  local parent base
  parent="$(dirname "$1")"; base="$(basename "$1" .md)"
  if [ "$(basename "$parent")" = "$base" ]; then printf '%s' "$parent";
  elif [ -d "$parent/$base" ]; then printf '%s' "$parent/$base";
  else printf '%s' "$parent"; fi
}
emit_companion_rel() {
  local task_root="$1" rel="$2"
  [ -e "$task_root/$rel" ] || return 0
  mmw_prototype_relpath_syntax_ok "$rel" || { echo "ERROR: 伴随材料路径非法:$rel" >&2; return 1; }
  mmw_prototype_path_has_symlink "$task_root" "$rel" \
    && { echo "ERROR: 伴随材料路径含软链:$rel" >&2; return 1; }
  printf '%s\n' "$task_root/$rel"
}

validate_task_approval() {
  local task_root="$1" man="$2" stored current rel untracked status selected
  status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$man")"
  case "$status" in
    active|superseded|BROKEN) echo "ERROR: prototype 状态未收敛:$status" >&2; return 1 ;;
    "")
      untracked="$(mmw_prototype_untracked_paths "$task_root" "$man")" || return 1
      [ -z "$untracked" ] || { echo "ERROR: 存在未登记 prototype/mockup；退回 design 后按 mmw where 执行 start --adopt" >&2; return 1; } ;;
    accepted)
      selected="$(mmw_prototype_selected_relpaths "$man")" || return 1
      while IFS= read -r rel; do
        [ -n "$rel" ] || continue
        mmw_prototype_validate_artifact "$task_root" "$man" "$rel" || return 1
      done <<<"$selected" ;;
    *) echo "ERROR: prototype 状态损坏:$status" >&2; return 1 ;;
  esac
  stored="$(jq -r '.approval.fingerprint // empty' "$man")"
  [ -n "$stored" ] || return 0
  local -a args=()
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_prototype_relpath_syntax_ok "$rel" || { echo "ERROR: approval report 路径非法:$rel" >&2; return 1; }
    [ -e "$task_root/$rel" ] || { echo "ERROR: approval report 不存在:$rel" >&2; return 1; }
    mmw_prototype_path_has_symlink "$task_root" "$rel" \
      && { echo "ERROR: approval report 路径含软链:$rel" >&2; return 1; }
    args+=(--report "$rel")
  done < <(jq -r '.approval.reports[]?' "$man")
  [ "${#args[@]}" -gt 0 ] || { echo "ERROR: approval 缺 reports" >&2; return 1; }
  current="$(cd "$task_root" && bash "$SCRIPT_DIR/note.sh" fingerprint "${args[@]}")" || return 1
  [ "$current" = "$stored" ] || { echo "ERROR: 设计确认已过期；先重新 /approve-design" >&2; return 1; }
}

validate_task_root() {
  local task_root="$1" man
  man="$(mmw_prototype_manifest_from_top "$task_root")" || return 0
  [ -f "$man" ] || return 0
  validate_task_approval "$task_root" "$man"
}

design_companions() {
  local m top man rel design_rel task_root selected investigating_rel prefix
  top="$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$top" ] || return 0
  man="$(mmw_prototype_manifest_from_top "$top")" || return 0
  [ -f "$man" ] || return 0
  design_rel="$(mmw_prototype_design_rel "$man")"
  task_root="$top"
  prefix="$(git -C "$1" rev-parse --show-prefix 2>/dev/null || true)"; prefix="${prefix%/}"
  if [ -n "$prefix" ]; then
    case "$1" in */"$prefix") task_root="${1%/"$prefix"}" ;; esac
  fi
  validate_task_approval "$task_root" "$man" || return 1
  emit_companion_rel "$task_root" "$design_rel/evidence" || return 1
  emit_companion_rel "$task_root" "$design_rel/direction.md" || return 1
  emit_companion_rel "$task_root" "${design_rel}-direction.md" || return 1
  investigating_rel="$(jq -r '.docs.investigating // empty' "$man")"
  if [ -n "$investigating_rel" ]; then
    emit_companion_rel "$task_root" "$investigating_rel" || return 1
    emit_companion_rel "$task_root" "${investigating_rel}.md" || return 1
  fi
  emit_companion_rel "$task_root" "$design_rel/investigating.md" || return 1
  selected="$(mmw_prototype_selected_relpaths "$man")" || return 1
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_prototype_validate_artifact "$task_root" "$man" "$rel" \
      || { echo "ERROR: accepted prototype 伴随材料无效:$rel" >&2; return 1; }
    printf '%s\n' "$task_root/$rel"
  done <<<"$selected"
}
companion_prompt_lines() {
  [ -n "$1" ] || return 0
  local c companions
  companions="$(design_companions "$1")" || return 1
  while IFS= read -r c; do
    [ -n "$c" ] || continue
    echo "  - $c"
  done <<<"$companions"
}

build_prompt() {
  local plan="$1" wt="$2" design="$3" issue="$4" mode="$5" sheet="$6"
  local skill; skill="$(mmw_plugin_root)/skills/worktree-build"
  if [ "$mode" = merge ]; then
    cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 按 mini-plan 修复已判定方向的合并冲突。
先读 Droid plugin 内 worktree-build skill 并严格执行:$skill/SKILL.md

工作树(你唯一可写的源码区):$wt
合并冲突 mini-plan(唯一意图与验收来源):$plan

只改 mini-plan 明确拥有的路径。逐 Task Pack TDD、每 Pack 本地提交、禁改 docs/、禁 push/gh pr merge/部署、卡住协议和 Return Contract 全按 worktree-build skill。不要重新选择哪边意图胜出,不要向用户提问,不要启动其它 agent;mini-plan 缺关键意图时在最终回执中结构化报告。
PROMPT
    return
  fi
  local ddir="" companions=""
  if [ -n "$design" ]; then
    ddir="$(design_dir_of "$design")"
    companions="$(companion_prompt_lines "$ddir")" || return 1
  fi
  cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 落地一份计划。
先读 Droid plugin 内 worktree-build skill 并严格执行:$skill/SKILL.md

工作树(你唯一可写的源码区):$wt
开工前依次读:
${design:+- 设计文档:$design
}${issue:+- 负责的 issue:$issue
}- 实施计划:$plan
${companions:+- 讨论态材料(prototype 仅含 accepted README + selected；selected 是 UI/状态逻辑实现起点):
$companions
}$(test_sheet_lines "$sheet")

只改 plan 的 File / Responsibility Map 和当前 Pack 拥有的路径。逐 Task Pack TDD、每 Pack 本地提交、禁改 docs/、禁 push/gh pr merge/部署、卡住协议和 Return Contract 全按 worktree-build skill。不要向用户提问,不要启动其它 agent;缺输入时在最终回执中结构化报告。
PROMPT
}

build_plan_prompt() {
  local plan="$1" wt="$2" design="$3" issue="$4" companions="$5" sheet="$6"
  local skill; skill="$(mmw_plugin_root)/skills/worktree-plan"
  cat <<PROMPT
你是计划撰写者,被主线程派进任务 worktree 把一个大 issue 写成一份实施计划。
先读 Droid plugin 内 worktree-plan skill 并严格执行:$skill/SKILL.md

任务工作树:$wt
唯一 plan 落点:$plan
开工前依次读:
${design:+- 源设计文档:$design
}${issue:+- 负责的大 issue:$issue
}${companions:+- 讨论态材料(prototype 仅含 accepted README + selected；只采用 selected):
$companions
}$(test_sheet_lines "$sheet")

只准写该 plan 与对应 issue 的 Small issues。禁止改源码、docs/design、其他 issue 或其他 plan,禁止 commit/push/发布。不要向用户提问,不要启动其它 agent;缺输入时在最终回执中结构化报告。
PROMPT
}

check_docs_boundary() {
  local wt="$1" start_sha="$2" touched
  touched="$( {
    git -C "$wt" diff --name-only "$start_sha" HEAD 2>/dev/null || true
    git -C "$wt" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'
  } | grep '^docs/' | sort -u || true )"
  [ -z "$touched" ] && return 0
  echo "DOCS_VIOLATION: Worker 改了 docs/:" >&2
  printf '%s\n' "$touched" | sed 's/^/  /' >&2
  return 3
}

mask_small_issues() {
  awk '
    /^## Small issues[[:space:]]*$/ { print; inside=1; next }
    inside && /^##[[:space:]]/ { inside=0 }
    !inside { print }
  '
}

path_fingerprint() {
  local wt="$1" rel="$2"
  if [ -L "$wt/$rel" ]; then
    printf 'link:%s' "$(readlink "$wt/$rel")" | shasum -a 256 | awk '{print $1}'
  elif [ -f "$wt/$rel" ]; then
    git -C "$wt" hash-object --no-filters -- "$rel"
  elif [ -e "$wt/$rel" ]; then
    printf 'other'
  else
    printf 'missing'
  fi
}

capture_plan_baseline() {
  local wt="$1" out="$2" tmp rel
  tmp="$out.tmp.$$"
  {
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      printf '%s\t%s\n' "$rel" "$(path_fingerprint "$wt" "$rel")"
    done < <(git -C "$wt" status --porcelain --untracked-files=all | sed 's/^...//' | sort -u)
  } | jq -Rn '
    [inputs | capture("^(?<path>[^\\t]+)\\t(?<hash>.*)$")] |
    reduce .[] as $x ({}; .[$x.path] = $x.hash)
  ' >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$out" \
    || { rm -f "$tmp"; return 1; }
}

path_matches_plan_baseline() {
  local wt="$1" baseline="$2" rel="$3" expected
  expected="$(jq -r --arg p "$rel" '.[$p] // empty' "$baseline")"
  [ -n "$expected" ] && [ "$(path_fingerprint "$wt" "$rel")" = "$expected" ]
}

check_plan_boundary() {
  local wt="$1" start_sha="$2" plan="$3" issue="$4" baseline="$5" issue_baseline="$6"
  local touched offending="" plan_rel issue_rel rel
  local base_mask current_mask
  case "$plan" in "$wt"/*) plan_rel="${plan#"$wt"/}" ;; *) die "plan 不在任务 worktree 内:$plan" ;; esac
  case "$issue" in "$wt"/*) issue_rel="${issue#"$wt"/}" ;; *) die "issue 不在任务 worktree 内:$issue" ;; esac
  [ -f "$baseline" ] || die "计划工人边界基线不存在:$baseline"
  [ -f "$issue_baseline" ] || die "issue 边界基线不存在:$issue_baseline"
  touched="$( {
    git -C "$wt" diff --name-only "$start_sha" HEAD 2>/dev/null || true
    git -C "$wt" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'
  } | sort -u | grep -v '^[[:space:]]*$' || true )"
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    [ "$rel" = "$plan_rel" ] && continue
    [ "$rel" = "$issue_rel" ] && continue
    path_matches_plan_baseline "$wt" "$baseline" "$rel" && continue
    offending="${offending}${offending:+
}$rel"
  done <<<"$touched"
  if [ -n "$offending" ]; then
    echo "PLAN_VIOLATION: 计划工人越界:" >&2
    printf '%s\n' "$offending" | sed 's/^/  /' >&2
    return 3
  fi
  if printf '%s\n' "$touched" | grep -Fxq "$issue_rel"; then
    base_mask="$(mktemp "${TMPDIR:-/tmp}/mmw-issue-base.XXXXXX")" || return 3
    current_mask="$(mktemp "${TMPDIR:-/tmp}/mmw-issue-current.XXXXXX")" || {
      rm -f "$base_mask"
      return 3
    }
    mask_small_issues <"$issue_baseline" >"$base_mask" \
      && mask_small_issues <"$wt/$issue_rel" >"$current_mask" \
      || { rm -f "$base_mask" "$current_mask"; return 3; }
    if ! cmp -s "$base_mask" "$current_mask"; then
      rm -f "$base_mask" "$current_mask"
      echo "PLAN_VIOLATION: issue 只准修改 ## Small issues:$issue_rel" >&2
      return 3
    fi
    rm -f "$base_mask" "$current_mask"
  fi
  return 0
}

write_meta() {
  local file="$1" mode="$2" droid="$3" model="$4" effort="$5" wt="$6" prompt="$7" start_sha="$8"
  local plan="$9" system_prompt="${10}" issue="${11:-}" disabled_tools="${12:-}"
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")" || return 1
  jq -n \
    --arg backend droid-exec --arg mode "$mode" --arg droid "$droid" \
    --arg model "$model" --arg effort "$effort" --arg wt "$wt" \
    --arg plan "$plan" --arg prompt "$prompt" --arg start "$start_sha" \
    --arg system "$system_prompt" --arg issue "$issue" --arg disabled "$disabled_tools" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{backend:$backend,mode:$mode,droid:$droid,model:$model,reasoning_effort:$effort,
      worktree:$wt,plan:$plan,issue:$issue,prompt_file:$prompt,system_prompt_file:$system,
      disabled_tools:$disabled,autonomy:"medium",start_sha:$start,
      status:"prepared",pid:null,session_id:null,result_file:null,log_file:null,
      created_at:$at,updated_at:$at}' >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

update_meta() {
  local meta="$1"; shift
  mmw_droid_atomic_update "$meta" "$@"
}

launch_exec() {
  local meta="$1" prompt="$2" wt="$3" model="$4" effort="$5" system_prompt="$6" session_id="${7:-}" status_cmd="$8"
  local disabled_tools="${9:-}"
  local native_branch="${10:-}" native_root="${11:-}" native_repo="${12:-}" native_path="${13:-}"
  mmw_droid_launch "$meta" "$prompt" "$wt" "$model" "$effort" "$system_prompt" "$session_id" medium "$disabled_tools" \
    "$native_branch" "$native_root" "$native_repo" "$native_path" \
    || die "worker 启动或派发账本写入失败"
  echo "WORKER_STARTED"
  echo "pid=$MMW_DROID_PID"
  echo "result_file=$MMW_DROID_RESULT_FILE"
  echo "log_file=$MMW_DROID_LOG_FILE"
  echo "NEXT=$status_cmd"
}

refresh_meta() {
  local meta="$1"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  mmw_droid_refresh "$meta"
}

guard_no_active() {
  local meta="$1" state
  [ -f "$meta" ] || return 0
  state="$(refresh_meta "$meta" 2>/dev/null || true)"
  case "$state" in
    RUNNING) die "已有 worker 正在运行:$meta" ;;
    COMPLETED) die "已有成功 worker；需要补改请用 resume:$meta" ;;
  esac
}

plan_sandbox_create() {
  local task_wt="$1" ns="$2" common main sandbox branch
  common="$(git -C "$task_wt" rev-parse --git-common-dir)" || return 1
  case "$common" in /*) ;; *) common="$task_wt/$common" ;; esac
  main="$(cd "$(dirname "$common")" && pwd -P)" || return 1
  sandbox="$main/$(mmw_worktrees_rel)/$(basename "$task_wt")-plan-$ns"
  branch="$(mmw_worker_branch_prefix)/$(basename "$task_wt")-plan-$ns"
  [ ! -e "$sandbox" ] || die "plan writer 隔离 worktree 已存在:$sandbox；请先 resume 或清理失败派发"
  git -C "$main" show-ref --verify --quiet "refs/heads/$branch" \
    && die "plan writer 隔离分支已存在:$branch；请先 resume 或清理失败派发"
  git -C "$main" worktree add -b "$branch" "$sandbox" "$(git -C "$task_wt" rev-parse HEAD)" >&2 \
    || die "建立 plan writer 隔离 worktree 失败:$sandbox"
  mmw_ensure_wt_state_ignore "$sandbox"
  printf '%s\t%s\n' "$sandbox" "$branch"
}

plan_sandbox_overlay() {
  local task_wt="$1" sandbox="$2" source="$3" rel
  [ -e "$source" ] || return 0
  case "$source" in "$task_wt"/*) rel="${source#"$task_wt"/}" ;; *) die "plan writer 输入不在任务 worktree:$source" ;; esac
  tar -C "$task_wt" -cf - "$rel" | tar -C "$sandbox" -xf - \
    || die "复制 plan writer 输入到隔离 worktree 失败:$source"
}

publish_plan_result() {
  local sandbox="$1" sandbox_plan="$2" sandbox_issue="$3" task_plan="$4" task_issue="$5"
  local tmp
  [ -f "$sandbox_plan" ] && [ ! -L "$sandbox_plan" ] || die "plan writer 未产出普通 plan 文件:$sandbox_plan"
  [ -f "$sandbox_issue" ] && [ ! -L "$sandbox_issue" ] || die "plan writer issue 结果无效:$sandbox_issue"
  mkdir -p "$(dirname "$task_plan")" "$(dirname "$task_issue")"
  tmp="$task_plan.tmp.$$"
  cp "$sandbox_plan" "$tmp" && mv "$tmp" "$task_plan" \
    || { rm -f "$tmp"; die "发布 plan writer 结果失败:$task_plan"; }
  tmp="$task_issue.tmp.$$"
  cp "$sandbox_issue" "$tmp" && mv "$tmp" "$task_issue" \
    || { rm -f "$tmp"; die "发布 plan writer issue 结果失败:$task_issue"; }
}

cleanup_plan_sandbox() {
  local task_wt="$1" sandbox="$2" branch="$3"
  git -C "$task_wt" worktree remove --force "$sandbox" >/dev/null 2>&1 \
    && git -C "$task_wt" branch -D "$branch" >/dev/null 2>&1
}

guard_unique_plan_targets() {
  local task_wt="$1" st="$2" own_ns="$3" issue="$4" meta other_ns other_issue
  for meta in "$task_wt/$st"/plan-workers/*/dispatch/meta.json; do
    [ -f "$meta" ] || continue
    other_ns="$(basename "$(dirname "$(dirname "$meta")")")"
    [ "$other_ns" = "$own_ns" ] && continue
    other_issue="$(jq -r '.task_issue // empty' "$meta")"
    [ "$other_issue" != "$issue" ] || die "同一 issue 已分配给 plan writer $other_ns:$issue"
  done
}

cmd_dispatch() {
  local plan="" wt="" base="HEAD" design="" issue="" model="" effort="" mode="pack"
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;; --issue) issue="$2"; shift 2 ;;
    --mode) mode="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;; --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -f "$plan" ] || die "plan 文件不存在:$plan"
  case "$mode" in
    pack)
      [ -f "$design" ] || die "--design 文件不存在:$design"
      [ -f "$issue" ] || die "--issue 文件不存在:$issue"
      ;;
    merge)
      design="$plan"
      issue="$plan"
      ;;
    *) die "--mode 只能 pack|merge" ;;
  esac
  [ -n "$wt" ] || die "--worktree 必填"
  local repo; repo="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel 2>/dev/null)" ||
    die "plan 不在 git 仓库内:$plan"
  local droid="$EXECUTOR_DROID" default_model="$EXECUTOR_MODEL" default_effort="$EXECUTOR_EFFORT"
  if grep -qiE '(complexity|复杂度).*capable' "$plan" 2>/dev/null; then
    droid="$CAPABLE_EXECUTOR_DROID"
    default_model="$CAPABLE_EXECUTOR_MODEL"
    default_effort="$CAPABLE_EXECUTOR_EFFORT"
  fi
  [ -n "$model" ] || model="$default_model"
  [ -n "$effort" ] || effort="$default_effort"
  local run_wt="$wt" native_branch="" native_root="" native_repo="" target_top="" target_path=""
  if [ -d "$wt" ]; then
    target_path="$(cd "$wt" && pwd -P)"
    target_top="$(git -C "$wt" rev-parse --show-toplevel 2>/dev/null || true)"
  fi
  if [ -z "$target_top" ] || [ "$target_path" != "$target_top" ]; then
    native_branch="$(mmw_worker_branch_prefix)/$(basename "$wt")"
    git -C "$repo" show-ref --verify --quiet "refs/heads/$native_branch" \
      || git -C "$repo" branch "$native_branch" "$base" \
      || die "建立 worker 分支失败:$native_branch"
    mkdir -p "$wt"
    mmw_ensure_wt_state_ignore "$wt"
    native_root="$wt"
    native_repo="$repo"
    run_wt="$(native_worktree_path "$repo" "$native_root" "$native_branch")"
  else
    run_wt="$target_top"
    mmw_ensure_wt_state_ignore "$run_wt"
  fi
  local st pkg start prompt meta system_prompt system_source disabled_tools
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  mkdir -p "$pkg"
  if [ -n "$native_branch" ]; then
    start="$(git -C "$repo" rev-parse "$native_branch")"
  else
    start="$(git -C "$run_wt" rev-parse HEAD)"
  fi
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  guard_no_active "$meta"
  system_source="$(mmw_plugin_root)/droids/$droid.md"
  [ -f "$system_source" ] || die "找不到 executor droid:$system_source"
  system_prompt="$pkg/system-prompt.md"
  render_droid_prompt "$system_source" "$system_prompt"
  disabled_tools="$(prepare_exec_policy "$pkg" "$model")"
  preflight_plugin_skill worktree-build
  local test_sheet; test_sheet="$(locate_test_sheet "${target_top:-$repo}")"
  build_prompt "$plan" "$run_wt" "$design" "$issue" "$mode" "$test_sheet" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" "$mode" "$droid" "$model" "$effort" "$run_wt" "$prompt" "$start" \
    "$plan" "$system_prompt" "$issue" "$disabled_tools"
  update_meta "$meta" --arg control "$wt" --arg branch "$native_branch" \
    --arg root "$native_root" --arg repo "$native_repo" \
    '.control_worktree=$control | .native_branch=$branch | .native_root=$root | .native_repo=$repo' \
    || die "无法记录 worker worktree 元数据"
  echo "WORKER_BACKEND=droid-exec"
  echo "DROID=$droid"
  echo "MODEL=$model"
  echo "REASONING_EFFORT=$effort"
  echo "PROMPT_FILE=$prompt"
  echo "META_FILE=$meta"
  launch_exec "$meta" "$prompt" "$run_wt" "$model" "$effort" "$system_prompt" "" \
    "mmw worker status --worktree \"$wt\"" "$disabled_tools" \
    "$native_branch" "$native_root" "$native_repo" "$run_wt"
}

cmd_resume() {
  local wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -d "$wt" ] || die "worktree 不存在:$wt"
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  validate_task_root "$wt" || die "任务设计确认或 prototype 状态无效"
  local st pkg meta state session model effort system_prompt disabled_tools
  local run_wt native_branch native_root native_repo
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  meta="$pkg/meta.json"
  state="$(refresh_meta "$meta" 2>/dev/null || true)"
  [ "$state" != RUNNING ] || die "原 worker 仍在运行"
  session="$(jq -r '.session_id // empty' "$meta")"
  model="$(jq -r .model "$meta")"
  effort="$(jq -r .reasoning_effort "$meta")"
  system_prompt="$(jq -r .system_prompt_file "$meta")"
  disabled_tools="$(jq -r '.disabled_tools // empty' "$meta")"
  run_wt="$(jq -r .worktree "$meta")"
  native_branch="$(jq -r '.native_branch // empty' "$meta")"
  native_root="$(jq -r '.native_root // empty' "$meta")"
  native_repo="$(jq -r '.native_repo // empty' "$meta")"
  [ -n "$session" ] || die "无成功 session_id,不能续接；先看 $(jq -r '.log_file // empty' "$meta")"
  cp "$instr" "$pkg/resume-prompt.md"
  launch_exec "$meta" "$pkg/resume-prompt.md" "$run_wt" "$model" "$effort" "$system_prompt" "$session" \
    "mmw worker status --worktree \"$wt\"" "$disabled_tools" \
    "$native_branch" "$native_root" "$native_repo" "$run_wt"
}

cmd_plan_dispatch() {
  local plan="" wt="" design="" issue="" model="$PLAN_MODEL" effort="$PLAN_EFFORT"
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;; --issue) issue="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  case "$plan" in /*) ;; *) die "--plan 必须绝对路径" ;; esac
  [ -d "$wt" ] || die "任务 worktree 不存在:$wt"
  [ -f "$design" ] || die "--design 文件不存在:$design"
  [ -f "$issue" ] || die "--issue 文件不存在:$issue"
  [ ! -L "$design" ] || die "--design 不得是符号链接:$design"
  [ ! -L "$issue" ] || die "--issue 不得是符号链接:$issue"
  [ ! -L "$plan" ] || die "--plan 不得是符号链接:$plan"
  case "$plan" in "$wt"/*) ;; *) die "--plan 必须位于任务 worktree:$plan" ;; esac
  case "$design" in "$wt"/*) ;; *) die "--design 必须位于任务 worktree:$design" ;; esac
  case "$issue" in "$wt"/*) ;; *) die "--issue 必须位于任务 worktree:$issue" ;; esac
  local ddir companions="" c
  ddir="$(design_dir_of "$design")"
  companions="$(design_companions "$ddir")" || die "讨论态材料校验失败"
  [ -z "$companions" ] || companions="$companions
"
  mmw_ensure_wt_state_ignore "$wt"
  local st ns pkg start prompt meta system_prompt system_source disabled_tools baseline issue_baseline
  local sandbox branch sandbox_plan sandbox_design sandbox_issue sandbox_info sandbox_companions=""
  local task_plan_baseline task_issue_baseline
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  mkdir -p "$pkg"
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  guard_no_active "$meta"
  guard_unique_plan_targets "$wt" "$st" "$ns" "$issue"
  task_plan_baseline="$(path_fingerprint "$wt" "${plan#"$wt"/}")"
  task_issue_baseline="$(path_fingerprint "$wt" "${issue#"$wt"/}")"
  sandbox_info="$(plan_sandbox_create "$wt" "$ns")"
  sandbox="${sandbox_info%%$'\t'*}"
  branch="${sandbox_info#*$'\t'}"
  sandbox_plan="$sandbox/${plan#"$wt"/}"
  sandbox_design="$sandbox/${design#"$wt"/}"
  sandbox_issue="$sandbox/${issue#"$wt"/}"
  plan_sandbox_overlay "$wt" "$sandbox" "$design"
  plan_sandbox_overlay "$wt" "$sandbox" "$issue"
  plan_sandbox_overlay "$wt" "$sandbox" "$plan"
  while IFS= read -r c; do
    [ -n "$c" ] || continue
    plan_sandbox_overlay "$wt" "$sandbox" "$c"
    sandbox_companions="${sandbox_companions}  - $sandbox/${c#"$wt"/}
"
  done < <(printf '%s' "$companions")
  start="$(git -C "$sandbox" rev-parse HEAD)"
  baseline="$pkg/worktree-baseline.json"
  issue_baseline="$pkg/issue-baseline.md"
  capture_plan_baseline "$sandbox" "$baseline" || die "无法记录 plan writer worktree 边界基线"
  cp "$sandbox_issue" "$issue_baseline" || die "无法记录 issue 边界基线"
  system_source="$(mmw_plugin_root)/droids/$PLAN_DROID.md"
  [ -f "$system_source" ] || die "找不到 plan writer droid:$system_source"
  system_prompt="$pkg/system-prompt.md"
  render_droid_prompt "$system_source" "$system_prompt"
  disabled_tools="$(prepare_exec_policy "$pkg" "$model")"
  preflight_plugin_skill worktree-plan
  local plan_test_sheet; plan_test_sheet="$(locate_test_sheet "$sandbox")"
  build_plan_prompt "$sandbox_plan" "$sandbox" "$sandbox_design" "$sandbox_issue" "$sandbox_companions" "$plan_test_sheet" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" dispatch "$PLAN_DROID" "$model" "$effort" "$sandbox" "$prompt" "$start" \
    "$sandbox_plan" "$system_prompt" "$sandbox_issue" "$disabled_tools"
  update_meta "$meta" \
    --arg task_wt "$wt" --arg task_plan "$plan" --arg task_design "$design" \
    --arg task_issue "$issue" --arg branch "$branch" \
    --arg task_plan_baseline "$task_plan_baseline" --arg task_issue_baseline "$task_issue_baseline" \
    '.task_worktree=$task_wt | .task_plan=$task_plan | .task_design=$task_design |
      .task_issue=$task_issue | .sandbox_branch=$branch |
      .task_plan_baseline=$task_plan_baseline | .task_issue_baseline=$task_issue_baseline' \
    || die "无法记录 plan writer 隔离边界"
  echo "WORKER_BACKEND=droid-exec"
  echo "PLAN_WORKER_NS=$ns"
  echo "DROID=$PLAN_DROID"
  echo "MODEL=$model"
  echo "REASONING_EFFORT=$effort"
  echo "PROMPT_FILE=$prompt"
  launch_exec "$meta" "$prompt" "$sandbox" "$model" "$effort" "$system_prompt" "" \
    "mmw worker status --plan \"$plan\" --worktree \"$wt\"" "$disabled_tools"
}

cmd_plan_resume() {
  local plan="" wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  validate_task_root "$wt" || die "任务设计确认或 prototype 状态无效"
  local st ns pkg meta state session model effort system_prompt disabled_tools sandbox
  local task_design task_issue sandbox_info sandbox_plan sandbox_design sandbox_issue start
  local task_plan_baseline task_issue_baseline
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  meta="$pkg/meta.json"
  state="$(refresh_meta "$meta" 2>/dev/null || true)"
  [ "$state" != RUNNING ] || die "原 plan writer 仍在运行"
  session="$(jq -r '.session_id // empty' "$meta")"
  model="$(jq -r .model "$meta")"
  effort="$(jq -r .reasoning_effort "$meta")"
  sandbox="$(jq -r .worktree "$meta")"
  task_design="$(jq -r '.task_design' "$meta")"
  task_issue="$(jq -r '.task_issue' "$meta")"
  system_prompt="$(jq -r .system_prompt_file "$meta")"
  disabled_tools="$(jq -r '.disabled_tools // empty' "$meta")"
  if [ ! -d "$sandbox" ]; then
    task_plan_baseline="$(path_fingerprint "$wt" "${plan#"$wt"/}")"
    task_issue_baseline="$(path_fingerprint "$wt" "${task_issue#"$wt"/}")"
    sandbox_info="$(plan_sandbox_create "$wt" "$ns")"
    sandbox="${sandbox_info%%$'\t'*}"
    sandbox_plan="$sandbox/${plan#"$wt"/}"
    sandbox_design="$sandbox/${task_design#"$wt"/}"
    sandbox_issue="$sandbox/${task_issue#"$wt"/}"
    plan_sandbox_overlay "$wt" "$sandbox" "$task_design"
    plan_sandbox_overlay "$wt" "$sandbox" "$task_issue"
    plan_sandbox_overlay "$wt" "$sandbox" "$plan"
    local c
    local resume_companions
    resume_companions="$(design_companions "$(design_dir_of "$task_design")")" || die "讨论态材料校验失败"
    while IFS= read -r c; do
      [ -n "$c" ] && plan_sandbox_overlay "$wt" "$sandbox" "$c"
    done <<<"$resume_companions"
    start="$(git -C "$sandbox" rev-parse HEAD)"
    capture_plan_baseline "$sandbox" "$pkg/worktree-baseline.json" \
      || die "无法刷新 plan writer worktree 边界基线"
    cp "$sandbox_issue" "$pkg/issue-baseline.md" || die "无法刷新 issue 边界基线"
    update_meta "$meta" \
      --arg sandbox "$sandbox" --arg sandbox_plan "$sandbox_plan" --arg sandbox_issue "$sandbox_issue" \
      --arg branch "${sandbox_info#*$'\t'}" --arg start "$start" \
      --arg task_plan_baseline "$task_plan_baseline" --arg task_issue_baseline "$task_issue_baseline" \
      '.worktree=$sandbox | .plan=$sandbox_plan | .issue=$sandbox_issue |
        .sandbox_branch=$branch | .start_sha=$start | .published=false |
        .task_plan_baseline=$task_plan_baseline | .task_issue_baseline=$task_issue_baseline |
        del(.published_at,.published_plan_hash,.published_issue_hash,.cleanup_warning)' \
      || die "无法刷新 plan writer resume 隔离边界"
  fi
  task_plan_baseline="$(path_fingerprint "$wt" "${plan#"$wt"/}")"
  task_issue_baseline="$(path_fingerprint "$wt" "${task_issue#"$wt"/}")"
  update_meta "$meta" --arg task_plan_baseline "$task_plan_baseline" --arg task_issue_baseline "$task_issue_baseline" \
    '.published=false | .task_plan_baseline=$task_plan_baseline |
      .task_issue_baseline=$task_issue_baseline |
      del(.published_at,.published_plan_hash,.published_issue_hash)' \
    || die "无法重置 plan writer 发布状态"
  cp "$instr" "$pkg/resume-prompt.md"
  launch_exec "$meta" "$pkg/resume-prompt.md" "$sandbox" "$model" "$effort" "$system_prompt" "$session" \
    "mmw worker status --plan \"$plan\" --worktree \"$wt\"" "$disabled_tools"
}

cmd_status() {
  local wt="" plan=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --plan) plan="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -n "$wt" ] || die "--worktree 必填"
  local st meta state result log session start pkg sandbox sandbox_plan sandbox_issue task_issue branch
  local plan_hash issue_hash expected_plan_hash expected_issue_hash
  st="$(state_for "$wt")"
  if [ -n "$plan" ]; then
    pkg="$wt/$st/plan-workers/$(plan_ns "$plan")/dispatch"
    meta="$pkg/meta.json"
  else
    meta="$wt/$st/worker-dispatch/meta.json"
  fi
  state="$(refresh_meta "$meta")" || true
  result="$(jq -r '.result_file // empty' "$meta")"
  log="$(jq -r '.log_file // empty' "$meta")"
  session="$(jq -r '.session_id // empty' "$meta")"
  echo "WORKER_STATUS=$state"
  echo "META_FILE=$meta"
  echo "SESSION_ID=${session:-none}"
  echo "RESULT_FILE=${result:-none}"
  echo "LOG_FILE=${log:-none}"
  [ "$state" = COMPLETED ] || return 1
  if [ -n "$plan" ]; then
    if [ "$(jq -r '.published // false' "$meta")" != true ]; then
      start="$(jq -r '.start_sha' "$meta")"
      sandbox="$(jq -r '.worktree' "$meta")"
      sandbox_plan="$(jq -r '.plan' "$meta")"
      sandbox_issue="$(jq -r '.issue' "$meta")"
      task_issue="$(jq -r '.task_issue' "$meta")"
      branch="$(jq -r '.sandbox_branch' "$meta")"
      check_plan_boundary "$sandbox" "$start" "$sandbox_plan" "$sandbox_issue" \
        "$pkg/worktree-baseline.json" "$pkg/issue-baseline.md" || return 3
      expected_plan_hash="$(jq -r '.task_plan_baseline' "$meta")"
      expected_issue_hash="$(jq -r '.task_issue_baseline' "$meta")"
      if [ "$(path_fingerprint "$wt" "${plan#"$wt"/}")" != "$expected_plan_hash" ] \
        || [ "$(path_fingerprint "$wt" "${task_issue#"$wt"/}")" != "$expected_issue_hash" ]; then
        echo "PLAN_PUBLISH_CONFLICT: 任务 worktree 的目标 plan/issue 在 writer 运行期间被改动" >&2
        return 3
      fi
      publish_plan_result "$sandbox" "$sandbox_plan" "$sandbox_issue" "$plan" "$task_issue"
      plan_hash="$(path_fingerprint "$wt" "${plan#"$wt"/}")"
      issue_hash="$(path_fingerprint "$wt" "${task_issue#"$wt"/}")"
      update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg plan_hash "$plan_hash" --arg issue_hash "$issue_hash" \
        '.published=true | .published_at=$at | .published_plan_hash=$plan_hash | .published_issue_hash=$issue_hash' \
        || die "无法记录 plan writer 发布状态"
      if ! cleanup_plan_sandbox "$wt" "$sandbox" "$branch"; then
        update_meta "$meta" --arg warning "隔离 worktree 清理失败:$sandbox" \
          '.cleanup_warning=$warning' || true
        echo "WARNING: 隔离 worktree 清理失败:$sandbox" >&2
      fi
    fi
  else
    start="$(jq -r '.start_sha' "$meta")"
    check_docs_boundary "$(jq -r .worktree "$meta")" "$start" || return 3
  fi
  echo "--- Droid 最后消息 ---"
  jq -r '.result // "(无结果)"' "$result"
}

cmd_check_docs() {
  local wt="" start=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --start-sha) start="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  local st meta run_wt; st="$(state_for "$wt")"
  meta="$wt/$st/worker-dispatch/meta.json"
  [ -n "$start" ] || start="$(cat "$wt/$st/worker-dispatch/start_sha" 2>/dev/null || true)"
  [ -n "$start" ] || die "无 start_sha"
  run_wt="$(jq -r .worktree "$meta")"
  check_docs_boundary "$run_wt" "$start"
}

cmd_plan_check() {
  local plan="" wt="" start="" issue=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --start-sha) start="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -d "$wt" ] || die "任务 worktree 不存在:$wt"
  case "$plan" in "$wt"/*) ;; *) die "--plan 必须位于任务 worktree:$plan" ;; esac
  local st ns sandbox sandbox_plan sandbox_issue task_issue; st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"
  local meta="$wt/$st/plan-workers/$ns/dispatch/meta.json"
  if [ "$(jq -r '.published // false' "$meta" 2>/dev/null)" = true ]; then
    sandbox_plan="$(jq -r '.plan' "$meta")"
    sandbox_issue="$(jq -r '.issue' "$meta")"
    task_issue="$(jq -r '.task_issue' "$meta")"
    [ "$(path_fingerprint "$wt" "${plan#"$wt"/}")" = "$(jq -r '.published_plan_hash' "$meta")" ] \
      || die "已发布 plan 在任务 worktree 被改动:$plan"
    [ "$(path_fingerprint "$wt" "${task_issue#"$wt"/}")" = "$(jq -r '.published_issue_hash' "$meta")" ] \
      || die "已发布 issue 在任务 worktree 被改动:$task_issue"
    return 0
  fi
  [ -n "$start" ] || start="$(cat "$wt/$st/plan-workers/$ns/dispatch/start_sha" 2>/dev/null || true)"
  sandbox="$(jq -r '.worktree // empty' "$meta" 2>/dev/null || true)"
  sandbox_plan="$(jq -r '.plan // empty' "$meta" 2>/dev/null || true)"
  sandbox_issue="$(jq -r '.issue // empty' "$meta" 2>/dev/null || true)"
  issue="$sandbox_issue"
  [ -n "$start" ] || die "无 start_sha"
  [ -n "$issue" ] || die "无 issue 路径"
  check_plan_boundary "$sandbox" "$start" "$sandbox_plan" "$sandbox_issue" \
    "$wt/$st/plan-workers/$ns/dispatch/worktree-baseline.json" \
    "$wt/$st/plan-workers/$ns/dispatch/issue-baseline.md"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume) shift; cmd_resume "$@" ;;
  check-docs) shift; cmd_check_docs "$@" ;;
  plan-dispatch) shift; cmd_plan_dispatch "$@" ;;
  plan-resume) shift; cmd_plan_resume "$@" ;;
  plan-check) shift; cmd_plan_check "$@" ;;
  status) shift; cmd_status "$@" ;;
  *) die "用法:worker.sh dispatch|resume|check-docs|plan-dispatch|plan-resume|plan-check|status ..." ;;
esac

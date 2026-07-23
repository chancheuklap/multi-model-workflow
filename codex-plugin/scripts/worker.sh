#!/usr/bin/env bash
# Codex 原生计划/写码工人准备器。
# 本脚本只做机械工作：建隔离 worktree、组 prompt、记录边界、验收和发布。
# 推理与写作由当前 Codex 任务里的原生 subagent 完成。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"

die() { echo "ERROR: $*" >&2; exit 2; }
state_for() { mmw_resolve_state_subdir "$1"; }
plan_ns() { basename "$1" .md; }
native_task_name() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_]/_/g'
}

preflight_plugin_skill() {
  local skill
  skill="$(mmw_plugin_root)/skills/$1/SKILL.md"
  [ -f "$skill" ] || die "preflight:工人 skill 缺失:$skill"
}

locate_test_sheet() {
  local root="$1" candidate
  for candidate in TESTING.md tests/TESTING.md docs/TESTING.md; do
    [ -f "$root/$candidate" ] && { printf '%s\n' "$candidate"; return 0; }
  done
  printf '\n'
}

test_sheet_line() {
  if [ -n "$1" ]; then
    printf '%s\n' "- 仓库测试说明:$1"
  else
    printf '%s\n' "- 仓库没有 TESTING.md；按项目规则和 worktree skill 里的测试纪律执行，并在回执标明 no-repo-test-sheet。"
  fi
}

design_dir_of() {
  local parent base
  parent="$(dirname "$1")"
  base="$(basename "$1" .md)"
  if [ "$(basename "$parent")" = "$base" ]; then
    printf '%s' "$parent"
  elif [ -d "$parent/$base" ]; then
    printf '%s' "$parent/$base"
  else
    printf '%s' "$parent"
  fi
}

emit_companion_rel() {
  local task_root="$1" rel="$2"
  [ -e "$task_root/$rel" ] || return 0
  mmw_prototype_relpath_syntax_ok "$rel" \
    || { echo "ERROR: 伴随材料路径非法:$rel" >&2; return 1; }
  mmw_prototype_path_has_symlink "$task_root" "$rel" \
    && { echo "ERROR: 伴随材料路径含软链:$rel" >&2; return 1; }
  printf '%s\n' "$task_root/$rel"
}

validate_task_approval() {
  local task_root="$1" manifest="$2" status selected stored current rel untracked
  status="$(jq -r 'if .prototype == null then "" else (.prototype.status // "BROKEN") end' "$manifest")"
  case "$status" in
    accepted)
      [ "$(jq -r '.prototype.selected | length' "$manifest")" -gt 0 ] \
        || { echo "ERROR: accepted prototype 缺 selected" >&2; return 1; }
      selected="$(mmw_prototype_selected_relpaths "$manifest")" || return 1
      while IFS= read -r rel; do
        [ -n "$rel" ] || continue
        mmw_prototype_validate_downstream_material "$task_root" "$manifest" "$rel" || return 1
      done <<<"$selected"
      ;;
    active|superseded|BROKEN)
      echo "ERROR: prototype 状态未收敛:$status" >&2
      return 1
      ;;
    "")
      untracked="$(mmw_prototype_untracked_paths "$task_root" "$manifest")" || return 1
      if [ -n "$untracked" ]; then
        echo "ERROR: 存在未登记 prototype/mockup；退回 design 接管" >&2
      else
        echo "ERROR: design 尚未完成 mandatory prototype" >&2
      fi
      return 1
      ;;
    *)
      echo "ERROR: prototype 状态损坏:$status" >&2
      return 1
      ;;
  esac

  stored="$(jq -r '.approval.fingerprint // empty' "$manifest")"
  [ -n "$stored" ] || { echo "ERROR: accepted prototype 尚未确认设计" >&2; return 1; }
  local -a reports=()
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_prototype_relpath_syntax_ok "$rel" \
      || { echo "ERROR: approval report 路径非法:$rel" >&2; return 1; }
    [ -e "$task_root/$rel" ] \
      || { echo "ERROR: approval report 不存在:$rel" >&2; return 1; }
    mmw_prototype_path_has_symlink "$task_root" "$rel" \
      && { echo "ERROR: approval report 路径含软链:$rel" >&2; return 1; }
    reports+=(--report "$rel")
  done < <(jq -r '.approval.reports[]?' "$manifest")
  [ "${#reports[@]}" -gt 0 ] || { echo "ERROR: approval 缺 reports" >&2; return 1; }

  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    jq -e --arg rel "$rel" '.approval.reports | index($rel) != null' "$manifest" >/dev/null \
      || { echo "ERROR: 当前 selected 未纳入设计确认:$rel" >&2; return 1; }
  done <<<"$selected"

  current="$(cd "$task_root" && bash "$SCRIPT_DIR/note.sh" fingerprint "${reports[@]}")" || return 1
  [ "$current" = "$stored" ] \
    || { echo "ERROR: 设计确认已过期；先重新确认设计" >&2; return 1; }
}

validate_task_root() {
  local task_root="$1" manifest
  manifest="$(mmw_prototype_manifest_from_top "$task_root")" \
    || { echo "ERROR: 无法定位任务 manifest:$task_root" >&2; return 1; }
  [ -f "$manifest" ] \
    || { echo "ERROR: 任务缺 .codex/multi-model-workflow/task.json" >&2; return 1; }
  validate_task_approval "$task_root" "$manifest" || return 1
  [ -n "$(jq -r '.approval.fingerprint // empty' "$manifest")" ] \
    || { echo "ERROR: 任务缺设计确认指纹" >&2; return 1; }
}

task_approval_fingerprint() {
  local manifest
  manifest="$(mmw_prototype_manifest_from_top "$1")" || { printf '\n'; return 0; }
  [ -f "$manifest" ] || { printf '\n'; return 0; }
  jq -r '.approval.fingerprint // empty' "$manifest"
}

assert_same_task_approval() {
  local task_root="$1" meta="$2" expected current
  validate_task_root "$task_root" || return 1
  expected="$(jq -r '.approval_fingerprint // empty' "$meta")"
  current="$(task_approval_fingerprint "$task_root")"
  [ -n "$expected" ] && [ -n "$current" ] && [ "$current" = "$expected" ] \
    || { echo "ERROR: 派发后的设计确认已变化；停止恢复或发布，请重新派发" >&2; return 1; }
}

design_companions() {
  local design_dir="$1" top manifest design_rel task_root selected rel item
  top="$(git -C "$design_dir" rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$top" ] || return 0
  manifest="$(mmw_prototype_manifest_from_top "$top")" || return 0
  [ -f "$manifest" ] || return 0
  design_rel="$(mmw_prototype_design_rel "$manifest")"
  task_root="$top"
  if [ "$design_rel" = "." ]; then
    task_root="$design_dir"
  else
    case "$design_dir" in */"$design_rel") task_root="${design_dir%/"$design_rel"}" ;; esac
  fi
  validate_task_approval "$task_root" "$manifest" || return 1
  for item in evidence direction.md investigating.md; do
    emit_companion_rel "$task_root" "$design_rel/$item" || return 1
  done
  selected="$(mmw_prototype_selected_relpaths "$manifest")" || return 1
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_prototype_validate_downstream_material "$task_root" "$manifest" "$rel" || return 1
    printf '%s\n' "$task_root/$rel"
  done <<<"$selected"
}

companion_prompt_lines() {
  local companion companions
  [ -n "$1" ] || return 0
  companions="$(design_companions "$1")" || return 1
  while IFS= read -r companion; do
    [ -n "$companion" ] && printf '  - %s\n' "$companion"
  done <<<"$companions"
}

build_prompt() {
  local plan="$1" worktree="$2" design="$3" issue="$4" mode="$5" sheet="$6"
  local skill companions="" design_dir=""
  skill="$(mmw_plugin_root)/skills/worktree-build/SKILL.md"
  if [ "$mode" = merge ]; then
    printf '%s\n' \
      "你是落地执行者。先完整阅读并严格执行:$skill" \
      "唯一可写源码区:$worktree" \
      "合并冲突 mini-plan:$plan" \
      "所有命令和文件操作都明确使用上述绝对 worktree。只改 mini-plan 拥有的路径；逐 Pack TDD 并提交；禁改 docs/、禁 push、禁部署、禁派其他 agent。"
    return
  fi
  if [ -n "$design" ]; then
    design_dir="$(design_dir_of "$design")"
    companions="$(companion_prompt_lines "$design_dir")" || return 1
  fi
  {
    printf '%s\n' \
      "你是落地执行者。先完整阅读并严格执行:$skill" \
      "唯一可写源码区:$worktree" \
      "开工前依次阅读:"
    [ -n "$design" ] && printf -- '- 设计文档:%s\n' "$design"
    [ -n "$issue" ] && printf -- '- 负责的 issue:%s\n' "$issue"
    printf -- '- 实施计划:%s\n' "$plan"
    if [ -n "$companions" ]; then
      printf '%s\n%s\n' "- 已确认的讨论态材料；prototype 仅含迭代 README 与 selected，selected 是实现起点:" "$companions"
    fi
    test_sheet_line "$sheet"
    printf '%s\n' "所有命令和文件操作都明确使用上述绝对 worktree。只改计划授权路径；逐 Pack TDD 并提交；禁改 docs/、禁 push、禁部署、禁派其他 agent。"
  }
}

build_plan_prompt() {
  local plan="$1" worktree="$2" design="$3" issue="$4" companions="$5" sheet="$6"
  local skill
  skill="$(mmw_plugin_root)/skills/worktree-plan/SKILL.md"
  {
    printf '%s\n' \
      "你是计划撰写者。先完整阅读并严格执行:$skill" \
      "唯一工作目录:$worktree" \
      "唯一 plan 落点:$plan" \
      "开工前依次阅读:" \
      "- 源设计文档:$design" \
      "- 负责的大 issue:$issue"
    if [ -n "$companions" ]; then
      printf '%s\n%s\n' "- 已确认的讨论态材料；prototype 仅含迭代 README 与 selected，只采用 selected:" "$companions"
    fi
    test_sheet_line "$sheet"
    printf '%s\n' "所有命令和文件操作都明确使用上述绝对 worktree。只准写该 plan 与对应 issue 的 Small issues；禁改源码、设计和其他文档；禁 commit、push、发布、派其他 agent。"
  }
}

path_fingerprint() {
  local worktree="$1" rel="$2"
  if [ -L "$worktree/$rel" ]; then
    printf 'link:%s' "$(readlink "$worktree/$rel")" | shasum -a 256 | awk '{print $1}'
  elif [ -f "$worktree/$rel" ]; then
    git -C "$worktree" hash-object --no-filters -- "$rel"
  elif [ -e "$worktree/$rel" ]; then
    printf 'other'
  else
    printf 'missing'
  fi
}

check_docs_boundary() {
  local worktree="$1" start_sha="$2" touched
  touched="$({
    git -C "$worktree" diff --name-only "$start_sha" HEAD 2>/dev/null || true
    git -C "$worktree" status --porcelain --untracked-files=all | sed 's/^...//'
  } | grep '^docs/' | sort -u || true)"
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

capture_dirty_baseline() {
  local worktree="$1" output="$2" temp rel
  temp="$output.tmp.$$"
  {
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      printf '%s\t%s\n' "$rel" "$(path_fingerprint "$worktree" "$rel")"
    done < <(git -C "$worktree" status --porcelain --untracked-files=all | sed 's/^...//' | sort -u)
  } | jq -Rn '
    [inputs | capture("^(?<path>[^\\t]+)\\t(?<hash>.*)$")] |
    reduce .[] as $x ({}; .[$x.path] = $x.hash)
  ' >"$temp" \
    && jq -e . "$temp" >/dev/null \
    && mv "$temp" "$output" \
    || { rm -f "$temp"; return 1; }
}

path_matches_baseline() {
  local worktree="$1" baseline="$2" rel="$3" expected
  expected="$(jq -r --arg path "$rel" '.[$path] // empty' "$baseline")"
  [ -n "$expected" ] && [ "$(path_fingerprint "$worktree" "$rel")" = "$expected" ]
}

check_plan_boundary() {
  local worktree="$1" start_sha="$2" plan="$3" issue="$4" baseline="$5" issue_baseline="$6"
  local plan_rel issue_rel touched rel offending="" before after
  case "$plan" in "$worktree"/*) plan_rel="${plan#"$worktree"/}" ;; *) die "plan 不在隔离 worktree:$plan" ;; esac
  case "$issue" in "$worktree"/*) issue_rel="${issue#"$worktree"/}" ;; *) die "issue 不在隔离 worktree:$issue" ;; esac
  [ -f "$baseline" ] || die "计划工人边界基线不存在:$baseline"
  [ -f "$issue_baseline" ] || die "issue 边界基线不存在:$issue_baseline"
  touched="$({
    git -C "$worktree" diff --name-only "$start_sha" HEAD 2>/dev/null || true
    git -C "$worktree" status --porcelain --untracked-files=all | sed 's/^...//'
  } | sort -u | grep -v '^[[:space:]]*$' || true)"
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    [ "$rel" = "$plan_rel" ] && continue
    [ "$rel" = "$issue_rel" ] && continue
    path_matches_baseline "$worktree" "$baseline" "$rel" && continue
    offending="${offending}${offending:+
}$rel"
  done <<<"$touched"
  if [ -n "$offending" ]; then
    echo "PLAN_VIOLATION: 计划工人越界:" >&2
    printf '%s\n' "$offending" | sed 's/^/  /' >&2
    return 3
  fi
  if printf '%s\n' "$touched" | grep -Fxq "$issue_rel"; then
    before="$(mktemp "${TMPDIR:-/tmp}/mmw-issue-before.XXXXXX")"
    after="$(mktemp "${TMPDIR:-/tmp}/mmw-issue-after.XXXXXX")"
    mask_small_issues <"$issue_baseline" >"$before"
    mask_small_issues <"$worktree/$issue_rel" >"$after"
    if ! cmp -s "$before" "$after"; then
      rm -f "$before" "$after"
      echo "PLAN_VIOLATION: issue 只准修改 ## Small issues:$issue_rel" >&2
      return 3
    fi
    rm -f "$before" "$after"
  fi
}

write_meta() {
  local file="$1" mode="$2" role="$3" worktree="$4" prompt="$5" start_sha="$6" plan="$7" issue="${8:-}"
  local temp
  temp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")"
  jq -n \
    --arg backend "$(mmw_worker_backend)" \
    --arg mode "$mode" \
    --arg role "$role" \
    --arg worktree "$worktree" \
    --arg prompt "$prompt" \
    --arg start "$start_sha" \
    --arg plan "$plan" \
    --arg issue "$issue" \
    --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{backend:$backend,mode:$mode,role:$role,worktree:$worktree,prompt_file:$prompt,
      start_sha:$start,plan:$plan,issue:$issue,status:"dispatched",
      created_at:$at,updated_at:$at}' >"$temp" \
    && jq -e . "$temp" >/dev/null \
    && mv "$temp" "$file" \
    || { rm -f "$temp"; return 1; }
}

update_meta() {
  local meta="$1"
  shift
  mmw_atomic_update "$meta" "$@"
}

guard_no_pending() {
  local meta="$1" status
  [ -f "$meta" ] || return 0
  status="$(jq -r '.status // empty' "$meta")"
  case "$status" in
    dispatched) die "已有派发未验收:${meta}；先 verify 或 resume" ;;
    verified) die "已有验收通过的派发；补改请用 resume:$meta" ;;
  esac
}

print_dispatch() {
  local task_name="$1" prompt="$2" meta="$3" verify_cmd="$4" note="$5"
  printf '%s\n' \
    "WORKER_BACKEND=$(mmw_worker_backend)" \
    "ROLE=$task_name" \
    "PROMPT_FILE=$prompt" \
    "META_FILE=$meta" \
    "DISPATCH=调用 spawn_agent(task_name=\"$task_name\", fork_turns=\"none\", message=PROMPT_FILE 全文)。不要指定外部 CLI；主工人使用当前 Codex 的 GPT 模型。$note" \
    "NEXT=工人完成后先运行 ${verify_cmd}，再亲验回执中的路径、提交与测试。"
}

repo_main_path() {
  local worktree="$1" common
  common="$(git -C "$worktree" rev-parse --git-common-dir)"
  case "$common" in /*) ;; *) common="$worktree/$common" ;; esac
  cd "$(dirname "$common")" && pwd -P
}

inner_worktree_path() {
  local task_worktree="$1" suffix="$2" main
  main="$(repo_main_path "$task_worktree")"
  printf '%s/%s/%s-%s' "$main" "$(mmw_worktrees_rel)" "$(basename "$task_worktree")" "$suffix"
}

create_build_worktree() {
  local task_worktree="$1" name="$2" base="$3" main path branch
  main="$(repo_main_path "$task_worktree")"
  path="$(inner_worktree_path "$task_worktree" "$name")"
  branch="$(mmw_worker_branch_prefix)/$name"
  [ ! -e "$path" ] || die "写码工人 worktree 已存在:${path}；请 resume"
  git -C "$main" show-ref --verify --quiet "refs/heads/$branch" \
    && die "写码工人分支已存在:${branch}；请 resume"
  mkdir -p "$(dirname "$path")"
  git -C "$main" worktree add -b "$branch" "$path" "$base" >&2 \
    || die "建立写码工人 worktree 失败:$path"
  : >"$path/.mmw-keep-worktree"
  mmw_ensure_wt_state_ignore "$path"
  printf '%s\t%s\n' "$path" "$branch"
}

create_plan_sandbox() {
  local task_worktree="$1" namespace="$2" main path branch
  main="$(repo_main_path "$task_worktree")"
  path="$(inner_worktree_path "$task_worktree" "plan-$namespace")"
  branch="$(mmw_worker_branch_prefix)/$(basename "$task_worktree")-plan-$namespace"
  [ ! -e "$path" ] || die "计划工人隔离 worktree 已存在:${path}；请 plan-resume"
  git -C "$main" show-ref --verify --quiet "refs/heads/$branch" \
    && die "计划工人隔离分支已存在:${branch}；请 plan-resume"
  mkdir -p "$(dirname "$path")"
  git -C "$main" worktree add -b "$branch" "$path" "$(git -C "$task_worktree" rev-parse HEAD)" >&2 \
    || die "建立计划工人隔离 worktree 失败:$path"
  mmw_ensure_wt_state_ignore "$path"
  printf '%s\t%s\n' "$path" "$branch"
}

overlay_input() {
  local task_worktree="$1" sandbox="$2" source="$3" rel
  [ -e "$source" ] || return 0
  case "$source" in "$task_worktree"/*) rel="${source#"$task_worktree"/}" ;; *) die "计划工人输入不在任务 worktree:$source" ;; esac
  mkdir -p "$(dirname "$sandbox/$rel")"
  if [ -d "$source" ]; then
    cp -R "$source" "$sandbox/$rel"
  else
    cp "$source" "$sandbox/$rel"
  fi
}

publish_plan_result() {
  local sandbox_plan="$1" sandbox_issue="$2" task_plan="$3" task_issue="$4" temp
  [ -f "$sandbox_plan" ] && [ ! -L "$sandbox_plan" ] \
    || die "计划工人未产出普通 plan 文件:$sandbox_plan"
  [ -f "$sandbox_issue" ] && [ ! -L "$sandbox_issue" ] \
    || die "计划工人 issue 结果无效:$sandbox_issue"
  mkdir -p "$(dirname "$task_plan")" "$(dirname "$task_issue")"
  temp="$task_plan.tmp.$$"
  cp "$sandbox_plan" "$temp" && mv "$temp" "$task_plan" \
    || { rm -f "$temp"; die "发布 plan 失败:$task_plan"; }
  temp="$task_issue.tmp.$$"
  cp "$sandbox_issue" "$temp" && mv "$temp" "$task_issue" \
    || { rm -f "$temp"; die "发布 issue 失败:$task_issue"; }
}

cleanup_plan_sandbox() {
  local task_worktree="$1" sandbox="$2" branch="$3"
  git -C "$task_worktree" worktree remove --force "$sandbox" >/dev/null 2>&1 \
    && git -C "$task_worktree" branch -D "$branch" >/dev/null 2>&1
}

guard_unique_plan_issue() {
  local task_worktree="$1" state="$2" own_namespace="$3" issue="$4" meta namespace
  for meta in "$task_worktree/$state"/plan-workers/*/dispatch/meta.json; do
    [ -f "$meta" ] || continue
    namespace="$(basename "$(dirname "$(dirname "$meta")")")"
    [ "$namespace" = "$own_namespace" ] && continue
    [ "$(jq -r '.task_issue // empty' "$meta")" != "$issue" ] \
      || die "同一 issue 已分配给计划工人 $namespace:$issue"
  done
}

cmd_dispatch() {
  local plan="" control="" design="" issue="" mode="pack" base="HEAD"
  while [ $# -gt 0 ]; do
    case "$1" in
      --plan) plan="$2"; shift 2 ;;
      --worktree) control="$2"; shift 2 ;;
      --design) design="$2"; shift 2 ;;
      --issue) issue="$2"; shift 2 ;;
      --mode) mode="$2"; shift 2 ;;
      --base) base="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  [ -f "$plan" ] || die "plan 文件不存在:$plan"
  [ -n "$control" ] || die "--worktree 必填"
  case "$mode" in
    pack)
      [ -f "$design" ] || die "--design 文件不存在:$design"
      [ -f "$issue" ] || die "--issue 文件不存在:$issue"
      ;;
    merge)
      design=""
      issue=""
      ;;
    *) die "--mode 只能 pack|merge" ;;
  esac

  local repo task_origin run_worktree branch="" start state package prompt meta info sheet base_sha
  repo="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel 2>/dev/null)" \
    || die "plan 不在 git 仓库:$plan"
  task_origin="$repo"
  if [ "$mode" = pack ]; then
    task_origin="$(git -C "$(dirname "$design")" rev-parse --show-toplevel 2>/dev/null)" \
      || die "无法定位设计所属任务 worktree:$design"
    validate_task_root "$task_origin" || die "设计确认或 prototype 状态无效"
  fi
  base_sha="$(git -C "$task_origin" rev-parse "$base" 2>/dev/null)" \
    || die "无法在任务 worktree 解析 --base:$base"
  state="$(state_for "$control")"
  package="$control/$state/worker-dispatch"
  prompt="$package/prompt.md"
  meta="$package/meta.json"
  guard_no_pending "$meta"
  preflight_plugin_skill worktree-build
  if [ "$mode" = pack ]; then
    companion_prompt_lines "$(design_dir_of "$design")" >/dev/null \
      || die "讨论态材料校验失败"
  fi
  sheet="$(locate_test_sheet "$task_origin")"

  if [ -d "$control" ] \
    && [ "$(cd "$control" && pwd -P)" = "$(git -C "$control" rev-parse --show-toplevel 2>/dev/null || true)" ]; then
    run_worktree="$(cd "$control" && pwd -P)"
  else
    mkdir -p "$control"
    mmw_ensure_wt_state_ignore "$control"
    info="$(create_build_worktree "$task_origin" "$(basename "$control")" "$base_sha")"
    run_worktree="${info%%$'\t'*}"
    branch="${info#*$'\t'}"
  fi

  mkdir -p "$package"
  build_prompt "$plan" "$run_worktree" "$design" "$issue" "$mode" "$sheet" >"$prompt"
  start="$(git -C "$run_worktree" rev-parse HEAD)"
  printf '%s\n' "$start" >"$package/start_sha"
  write_meta "$meta" "$mode" build-worker "$run_worktree" "$prompt" "$start" "$plan" "$issue"
  update_meta "$meta" \
    --arg control "$control" \
    --arg branch "$branch" \
    --arg origin "$task_origin" \
    --arg approval "$(task_approval_fingerprint "$task_origin")" \
    '.control_worktree=$control | .branch=$branch | .task_origin=$origin |
      .approval_fingerprint=$approval' \
    || die "无法记录写码工人边界"
  print_dispatch build_worker "$prompt" "$meta" \
    "mmw worker verify --worktree \"$control\"" \
    "工人在独立内层 worktree 工作，主任务可继续调度其他互不依赖的工人。"
}

cmd_resume() {
  local control="" instructions=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --worktree) control="$2"; shift 2 ;;
      --instructions) instructions="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  [ -f "$instructions" ] || die "--instructions 文件不存在:$instructions"
  local state package meta origin run_worktree
  state="$(state_for "$control")"
  package="$control/$state/worker-dispatch"
  meta="$package/meta.json"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  origin="$(jq -r '.task_origin // empty' "$meta")"
  [ -n "$origin" ] || die "派发账本缺 task_origin"
  if [ "$(jq -r .mode "$meta")" != merge ]; then
    assert_same_task_approval "$origin" "$meta" || die "设计确认或 prototype 状态无效"
  fi
  run_worktree="$(jq -r .worktree "$meta")"
  [ -d "$run_worktree" ] || die "写码工人 worktree 不存在:$run_worktree"
  cp "$instructions" "$package/resume-prompt.md"
  update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="dispatched" | .updated_at=$at' || die "无法重置派发状态"
  printf '%s\n' \
    "WORKER_BACKEND=$(mmw_worker_backend)" \
    "PROMPT_FILE=$package/resume-prompt.md" \
    "META_FILE=$meta" \
    "DISPATCH=如果原工人仍在当前任务中，调用 followup_task(target=<当前工人>, message=PROMPT_FILE 全文)；否则调用 spawn_agent(task_name=\"build_worker_repair\", fork_turns=\"none\", message=\"返修既有 worktree ${run_worktree}；先读 git log 和 PROMPT_FILE 后继续\")。不保存 agent id，跨任务靠盘上 worktree 与账本续接。" \
    "NEXT=工人完成后运行 mmw worker verify --worktree \"$control\"。"
}

cmd_plan_dispatch() {
  local plan="" task_worktree="" design="" issue=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --plan) plan="$2"; shift 2 ;;
      --worktree) task_worktree="$2"; shift 2 ;;
      --design) design="$2"; shift 2 ;;
      --issue) issue="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  case "$plan" in /*) ;; *) die "--plan 必须是绝对路径" ;; esac
  [ -d "$task_worktree" ] || die "任务 worktree 不存在:$task_worktree"
  [ -f "$design" ] || die "--design 文件不存在:$design"
  [ -f "$issue" ] || die "--issue 文件不存在:$issue"
  [ ! -L "$design" ] && [ ! -L "$issue" ] && [ ! -L "$plan" ] \
    || die "plan/design/issue 不得是符号链接"
  case "$plan" in "$task_worktree"/*) ;; *) die "--plan 必须位于任务 worktree:$plan" ;; esac
  case "$design" in "$task_worktree"/*) ;; *) die "--design 必须位于任务 worktree:$design" ;; esac
  case "$issue" in "$task_worktree"/*) ;; *) die "--issue 必须位于任务 worktree:$issue" ;; esac
  validate_task_root "$task_worktree" || die "设计确认或 prototype 状态无效"

  local design_dir companions namespace state package prompt meta info sandbox branch
  local sandbox_plan sandbox_design sandbox_issue sandbox_companions="" companion
  local start baseline issue_baseline sheet task_plan_hash task_issue_hash native_name
  design_dir="$(design_dir_of "$design")"
  companions="$(design_companions "$design_dir")" || die "讨论态材料校验失败"
  state="$(state_for "$task_worktree")"
  namespace="$(plan_ns "$plan")"
  native_name="$(native_task_name "plan_writer_$namespace")"
  package="$task_worktree/$state/plan-workers/$namespace/dispatch"
  prompt="$package/prompt.md"
  meta="$package/meta.json"
  guard_no_pending "$meta"
  guard_unique_plan_issue "$task_worktree" "$state" "$namespace" "$issue"
  preflight_plugin_skill worktree-plan
  task_plan_hash="$(path_fingerprint "$task_worktree" "${plan#"$task_worktree"/}")"
  task_issue_hash="$(path_fingerprint "$task_worktree" "${issue#"$task_worktree"/}")"

  mmw_ensure_wt_state_ignore "$task_worktree"
  mkdir -p "$package"
  info="$(create_plan_sandbox "$task_worktree" "$namespace")"
  sandbox="${info%%$'\t'*}"
  branch="${info#*$'\t'}"
  sandbox_plan="$sandbox/${plan#"$task_worktree"/}"
  sandbox_design="$sandbox/${design#"$task_worktree"/}"
  sandbox_issue="$sandbox/${issue#"$task_worktree"/}"
  overlay_input "$task_worktree" "$sandbox" "$design"
  overlay_input "$task_worktree" "$sandbox" "$issue"
  overlay_input "$task_worktree" "$sandbox" "$plan"
  while IFS= read -r companion; do
    [ -n "$companion" ] || continue
    overlay_input "$task_worktree" "$sandbox" "$companion"
    sandbox_companions="${sandbox_companions}  - $sandbox/${companion#"$task_worktree"/}
"
  done <<<"$companions"
  start="$(git -C "$sandbox" rev-parse HEAD)"
  baseline="$package/worktree-baseline.json"
  issue_baseline="$package/issue-baseline.md"
  capture_dirty_baseline "$sandbox" "$baseline" || die "无法记录计划工人边界基线"
  cp "$sandbox_issue" "$issue_baseline"
  sheet="$(locate_test_sheet "$sandbox")"
  build_plan_prompt "$sandbox_plan" "$sandbox" "$sandbox_design" "$sandbox_issue" "$sandbox_companions" "$sheet" >"$prompt"
  printf '%s\n' "$start" >"$package/start_sha"
  write_meta "$meta" plan plan-writer "$sandbox" "$prompt" "$start" "$sandbox_plan" "$sandbox_issue"
  update_meta "$meta" \
    --arg task_worktree "$task_worktree" \
    --arg task_plan "$plan" \
    --arg task_design "$design" \
    --arg task_issue "$issue" \
    --arg branch "$branch" \
    --arg plan_hash "$task_plan_hash" \
    --arg issue_hash "$task_issue_hash" \
    --arg approval "$(task_approval_fingerprint "$task_worktree")" \
    '.task_worktree=$task_worktree | .task_origin=$task_worktree |
      .task_plan=$task_plan | .task_design=$task_design | .task_issue=$task_issue |
      .sandbox_branch=$branch | .task_plan_baseline=$plan_hash |
      .task_issue_baseline=$issue_hash | .approval_fingerprint=$approval' \
    || die "无法记录计划工人隔离边界"
  printf 'PLAN_WORKER_NS=%s\n' "$namespace"
  print_dispatch "$native_name" "$prompt" "$meta" \
    "mmw worker verify --plan \"$plan\" --worktree \"$task_worktree\"" \
    "互不依赖的 plan 先全部调用 spawn_agent，再等待；每个 writer 使用各自隔离 worktree。"
}

cmd_plan_resume() {
  local plan="" task_worktree="" instructions=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --plan) plan="$2"; shift 2 ;;
      --worktree) task_worktree="$2"; shift 2 ;;
      --instructions) instructions="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  [ -f "$instructions" ] || die "--instructions 文件不存在:$instructions"
  local state namespace package meta sandbox task_design task_issue recreated=false native_name
  local info branch sandbox_plan sandbox_design sandbox_issue companions companion sandbox_companions=""
  local start sheet
  state="$(state_for "$task_worktree")"
  namespace="$(plan_ns "$plan")"
  native_name="$(native_task_name "plan_writer_${namespace}_repair")"
  package="$task_worktree/$state/plan-workers/$namespace/dispatch"
  meta="$package/meta.json"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  assert_same_task_approval "$task_worktree" "$meta" || die "设计确认或 prototype 状态无效"
  sandbox="$(jq -r .worktree "$meta")"
  task_design="$(jq -r .task_design "$meta")"
  task_issue="$(jq -r .task_issue "$meta")"
  if [ ! -d "$sandbox" ]; then
    info="$(create_plan_sandbox "$task_worktree" "$namespace")"
    sandbox="${info%%$'\t'*}"
    branch="${info#*$'\t'}"
    sandbox_plan="$sandbox/${plan#"$task_worktree"/}"
    sandbox_design="$sandbox/${task_design#"$task_worktree"/}"
    sandbox_issue="$sandbox/${task_issue#"$task_worktree"/}"
    overlay_input "$task_worktree" "$sandbox" "$task_design"
    overlay_input "$task_worktree" "$sandbox" "$task_issue"
    overlay_input "$task_worktree" "$sandbox" "$plan"
    companions="$(design_companions "$(design_dir_of "$task_design")")" \
      || die "讨论态材料校验失败"
    while IFS= read -r companion; do
      [ -n "$companion" ] || continue
      overlay_input "$task_worktree" "$sandbox" "$companion"
      sandbox_companions="${sandbox_companions}  - $sandbox/${companion#"$task_worktree"/}
"
    done <<<"$companions"
    start="$(git -C "$sandbox" rev-parse HEAD)"
    capture_dirty_baseline "$sandbox" "$package/worktree-baseline.json" \
      || die "无法刷新计划工人边界基线"
    cp "$sandbox_issue" "$package/issue-baseline.md"
    sheet="$(locate_test_sheet "$sandbox")"
    build_plan_prompt "$sandbox_plan" "$sandbox" "$sandbox_design" "$sandbox_issue" \
      "$sandbox_companions" "$sheet" >"$package/prompt.md"
    printf '%s\n' "$start" >"$package/start_sha"
    update_meta "$meta" \
      --arg sandbox "$sandbox" \
      --arg sandbox_plan "$sandbox_plan" \
      --arg sandbox_issue "$sandbox_issue" \
      --arg branch "$branch" \
      --arg start "$start" \
      --arg prompt "$package/prompt.md" \
      '.worktree=$sandbox | .plan=$sandbox_plan | .issue=$sandbox_issue |
        .sandbox_branch=$branch | .start_sha=$start |
        .prompt_file=$prompt' \
      || die "无法刷新计划工人隔离边界"
    recreated=true
  fi
  if [ "$recreated" = false ]; then
    [ "$(path_fingerprint "$task_worktree" "${plan#"$task_worktree"/}")" = "$(jq -r .task_plan_baseline "$meta")" ] \
      && [ "$(path_fingerprint "$task_worktree" "${task_issue#"$task_worktree"/}")" = "$(jq -r .task_issue_baseline "$meta")" ] \
      || die "计划工人运行期间目标 plan/issue 已变化；拒绝用旧沙箱覆盖，请重新分配"
  fi
  cp "$instructions" "$package/resume-prompt.md"
  update_meta "$meta" \
    --arg plan_hash "$(path_fingerprint "$task_worktree" "${plan#"$task_worktree"/}")" \
    --arg issue_hash "$(path_fingerprint "$task_worktree" "${task_issue#"$task_worktree"/}")" \
    '.status="dispatched" | .task_plan_baseline=$plan_hash |
      .task_issue_baseline=$issue_hash | .published=false |
      del(.published_at,.published_plan_hash,.published_issue_hash,.cleanup_warning)' \
    || die "无法重置计划工人状态"
  printf '%s\n' \
    "WORKER_BACKEND=$(mmw_worker_backend)" \
    "BASE_PROMPT_FILE=$package/prompt.md" \
    "PROMPT_FILE=$package/resume-prompt.md" \
    "META_FILE=$meta"
  if [ "$recreated" = true ]; then
    printf '%s\n' "DISPATCH=隔离 worktree 已重建，调用 spawn_agent(task_name=\"$native_name\", fork_turns=\"none\", message=\"先完整阅读 BASE_PROMPT_FILE 和 PROMPT_FILE，再在 ${sandbox} 返修\")。"
  else
    printf '%s\n' "DISPATCH=原计划工人仍在当前任务时调用 followup_task；否则调用 spawn_agent(task_name=\"$native_name\", fork_turns=\"none\", message=\"先完整阅读 BASE_PROMPT_FILE 和 PROMPT_FILE，再在 ${sandbox} 返修\")。不保存 agent id。"
  fi
  printf '%s\n' "NEXT=完成后运行 mmw worker verify --plan \"$plan\" --worktree \"$task_worktree\"。"
}

cmd_verify() {
  local task_worktree="" plan=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --worktree) task_worktree="$2"; shift 2 ;;
      --plan) plan="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  [ -n "$task_worktree" ] || die "--worktree 必填"
  local state package meta origin start sandbox sandbox_plan sandbox_issue task_issue branch
  local expected_plan expected_issue plan_hash issue_hash
  state="$(state_for "$task_worktree")"
  if [ -n "$plan" ]; then
    package="$task_worktree/$state/plan-workers/$(plan_ns "$plan")/dispatch"
  else
    package="$task_worktree/$state/worker-dispatch"
  fi
  meta="$package/meta.json"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  origin="$(jq -r '.task_origin // .task_worktree // empty' "$meta")"
  [ -n "$origin" ] || die "派发账本缺 task_origin"
  if [ "$(jq -r .mode "$meta")" != merge ]; then
    assert_same_task_approval "$origin" "$meta" || die "设计确认或 prototype 状态无效"
  fi
  printf 'META_FILE=%s\n' "$meta"

  if [ -z "$plan" ]; then
    start="$(jq -r .start_sha "$meta")"
    check_docs_boundary "$(jq -r .worktree "$meta")" "$start" || return 3
    update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="verified" | .updated_at=$at' || die "无法记录验收状态"
    echo "WORKER_VERIFY=pass(docs 边界干净)"
    return
  fi

  if [ "$(jq -r '.published // false' "$meta")" != true ]; then
    start="$(jq -r .start_sha "$meta")"
    sandbox="$(jq -r .worktree "$meta")"
    sandbox_plan="$(jq -r .plan "$meta")"
    sandbox_issue="$(jq -r .issue "$meta")"
    task_issue="$(jq -r .task_issue "$meta")"
    branch="$(jq -r .sandbox_branch "$meta")"
    check_plan_boundary "$sandbox" "$start" "$sandbox_plan" "$sandbox_issue" \
      "$package/worktree-baseline.json" "$package/issue-baseline.md" || return 3
    expected_plan="$(jq -r .task_plan_baseline "$meta")"
    expected_issue="$(jq -r .task_issue_baseline "$meta")"
    [ "$(path_fingerprint "$task_worktree" "${plan#"$task_worktree"/}")" = "$expected_plan" ] \
      && [ "$(path_fingerprint "$task_worktree" "${task_issue#"$task_worktree"/}")" = "$expected_issue" ] \
      || { echo "PLAN_PUBLISH_CONFLICT: 目标 plan/issue 在工人运行期间被改动" >&2; return 3; }
    publish_plan_result "$sandbox_plan" "$sandbox_issue" "$plan" "$task_issue"
    plan_hash="$(path_fingerprint "$task_worktree" "${plan#"$task_worktree"/}")"
    issue_hash="$(path_fingerprint "$task_worktree" "${task_issue#"$task_worktree"/}")"
    update_meta "$meta" \
      --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      --arg plan_hash "$plan_hash" \
      --arg issue_hash "$issue_hash" \
      '.status="verified" | .published=true | .published_at=$at |
        .published_plan_hash=$plan_hash | .published_issue_hash=$issue_hash' \
      || die "无法记录计划发布状态"
    if ! cleanup_plan_sandbox "$task_worktree" "$sandbox" "$branch"; then
      update_meta "$meta" --arg warning "隔离 worktree 清理失败:$sandbox" \
        '.cleanup_warning=$warning' || true
      echo "WARNING: 隔离 worktree 清理失败:$sandbox" >&2
    fi
  fi
  echo "WORKER_VERIFY=pass(plan 已发布:$plan)"
}

cmd_check_docs() {
  local control="" start=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --worktree) control="$2"; shift 2 ;;
      --start-sha) start="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  local state package meta
  state="$(state_for "$control")"
  package="$control/$state/worker-dispatch"
  meta="$package/meta.json"
  [ -n "$start" ] || start="$(cat "$package/start_sha" 2>/dev/null || true)"
  [ -n "$start" ] || die "无 start_sha"
  check_docs_boundary "$(jq -r .worktree "$meta")" "$start"
}

cmd_plan_check() {
  local plan="" task_worktree="" start=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --plan) plan="$2"; shift 2 ;;
      --worktree) task_worktree="$2"; shift 2 ;;
      --start-sha) start="$2"; shift 2 ;;
      *) die "未知参数:$1" ;;
    esac
  done
  case "$plan" in "$task_worktree"/*) ;; *) die "--plan 必须位于任务 worktree:$plan" ;; esac
  local state namespace package meta task_issue
  state="$(state_for "$task_worktree")"
  namespace="$(plan_ns "$plan")"
  package="$task_worktree/$state/plan-workers/$namespace/dispatch"
  meta="$package/meta.json"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  if [ "$(jq -r '.published // false' "$meta")" = true ]; then
    task_issue="$(jq -r .task_issue "$meta")"
    [ "$(path_fingerprint "$task_worktree" "${plan#"$task_worktree"/}")" = "$(jq -r .published_plan_hash "$meta")" ] \
      || die "已发布 plan 被改动:$plan"
    [ "$(path_fingerprint "$task_worktree" "${task_issue#"$task_worktree"/}")" = "$(jq -r .published_issue_hash "$meta")" ] \
      || die "已发布 issue 被改动:$task_issue"
    return 0
  fi
  [ -n "$start" ] || start="$(cat "$package/start_sha" 2>/dev/null || true)"
  check_plan_boundary \
    "$(jq -r .worktree "$meta")" \
    "$start" \
    "$(jq -r .plan "$meta")" \
    "$(jq -r .issue "$meta")" \
    "$package/worktree-baseline.json" \
    "$package/issue-baseline.md"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume) shift; cmd_resume "$@" ;;
  check-docs) shift; cmd_check_docs "$@" ;;
  plan-dispatch) shift; cmd_plan_dispatch "$@" ;;
  plan-resume) shift; cmd_plan_resume "$@" ;;
  plan-check) shift; cmd_plan_check "$@" ;;
  verify) shift; cmd_verify "$@" ;;
  *) die "用法:worker.sh dispatch|resume|check-docs|plan-dispatch|plan-resume|plan-check|verify ..." ;;
esac

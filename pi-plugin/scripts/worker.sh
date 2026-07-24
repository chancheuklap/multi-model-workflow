#!/usr/bin/env bash
# 写码工人和写计划工人派发准备器(pi-subagents 原生)。
# 脚本只做机械把关:准备 worktree/隔离沙箱、组工人 prompt、记边界基线和派发账本;
# 工人本体由协调者在 pi 会话内用 Agent 工具按名字派发(subagent_type=角色名,
# model/工具白名单/系统提示词由已注册的 agents-roster frontmatter 提供)。
# 工人完成(会话内收到回执)后跑 verify 过机器边界门;plan 工人过门才原子发布。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"
# shellcheck source=lib/retrieval-candidates.sh
. "$SCRIPT_DIR/lib/retrieval-candidates.sh"

EXECUTOR_AGENT="${PI_EXECUTOR_AGENT:-pack-executor}"
CAPABLE_EXECUTOR_AGENT="${PI_CAPABLE_EXECUTOR_AGENT:-pack-executor-capable}"
PLAN_AGENT="${PI_PLAN_AGENT:-plan-writer}"

die() { echo "ERROR: $*" >&2; exit 2; }
state_for() { mmw_resolve_state_subdir "$1"; }
plan_ns() { basename "$1" .md; }

# 派发前自检(机器可核验的事实,缺装备当场报错,不让工人开工后才发现):
# 点名的 plugin skill 真实存在(工人 prompt 指它当总纲)。
preflight_plugin_skill() {  # $1=skill 名
  local sk="$(mmw_plugin_root)/skills/$1/SKILL.md"
  [ -f "$sk" ] || die "preflight:工人 skill 缺失($sk 不存在);plugin 安装不完整,先修再派"
}
# 点名的工人角色已注册为 pi agent(全局 agents 目录有同名定义,软链或实体均可)。
preflight_registered_agent() {  # $1=agent 名
  local roster="$(mmw_plugin_root)/agents-roster/$1.md"
  [ -f "$roster" ] || die "preflight:找不到工人角色:$roster"
  local reg="${PI_CODING_AGENT_DIR:-$HOME/.pi/agent}/agents/$1.md"
  [ -e "$reg" ] || die "preflight:工人角色未注册为 pi agent($reg 不存在);先软链 agents-roster/$1.md 进全局 agents 目录"
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

native_worktree_path() {
  local repo="$1" root="$2" branch="$3"
  printf '%s/%s-wt-%s' "$root" "$(basename "$repo")" "${branch//\//-}"
}

# 讨论态材料推导(固定归脚本):从设计文档路径机械推导设计文件夹与伴随材料,LLM 不传路径。
# 布局:docs/design/<slug>/<slug>.md 单文件夹形态;兼容在飞旧任务 docs/design/<slug>.md 根文件形态。
design_dir_of() {  # $1=设计文档路径 → 设计文件夹
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
      if [ -n "$untracked" ]; then
        echo "ERROR: 存在未登记 prototype/mockup；退回 design 后按 mmw where 执行 start --adopt" >&2
      else
        echo "ERROR: design 尚未完成 mandatory prototype；退回 design 后按 mmw where 启动" >&2
      fi
      return 1 ;;
    accepted)
      [ "$(jq -r '.prototype.selected | length' "$man")" -gt 0 ] || { echo "ERROR: accepted prototype 缺 selected" >&2; return 1; }
      selected="$(mmw_prototype_selected_relpaths "$man")" || return 1
      while IFS= read -r rel; do
        [ -n "$rel" ] || continue
        mmw_prototype_validate_downstream_material "$task_root" "$man" "$rel" || return 1
      done <<<"$selected" ;;
    *) echo "ERROR: prototype 状态损坏:$status" >&2; return 1 ;;
  esac
  stored="$(jq -r '.approval.fingerprint // empty' "$man")"
  if [ "$status" = accepted ] && [ -z "$stored" ]; then echo "ERROR: accepted prototype 尚未经过 /approve-design" >&2; return 1; fi
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
  if [ "$status" = accepted ]; then
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      jq -e --arg rel "$rel" '.approval.reports | index($rel) != null' "$man" >/dev/null \
        || { echo "ERROR: 当前 prototype selected 未纳入设计确认:$rel" >&2; return 1; }
    done <<<"$selected"
  fi
  current="$(cd "$task_root" && bash "$SCRIPT_DIR/note.sh" fingerprint "${args[@]}")" || return 1
  [ "$current" = "$stored" ] || { echo "ERROR: 设计确认已过期；先重新 /approve-design" >&2; return 1; }
}

validate_task_root() {
  local task_root="$1" man
  man="$(mmw_prototype_manifest_from_top "$task_root")" || return 0
  [ -f "$man" ] || return 0
  validate_task_approval "$task_root" "$man"
}

design_companions() {  # $1=设计文件夹 → 结论材料 + accepted prototype 精确选中项
  local m top man rel design_rel task_root selected
  top="$(git -C "$1" rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$top" ] || return 0
  man="$(mmw_prototype_manifest_from_top "$top")" || return 0
  [ -f "$man" ] || return 0
  design_rel="$(mmw_prototype_design_rel "$man")"
  task_root="$top"
  if [ "$design_rel" = "." ]; then
    task_root="$1"
  else
    case "$1" in */"$design_rel") task_root="${1%/"$design_rel"}" ;; esac
  fi
  validate_task_approval "$task_root" "$man" || return 1
  for m in evidence direction.md investigating.md; do
    emit_companion_rel "$task_root" "$design_rel/$m" || return 1
  done
  selected="$(mmw_prototype_selected_relpaths "$man")" || return 1
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    mmw_prototype_validate_downstream_material "$task_root" "$man" "$rel" \
      || { echo "ERROR: accepted prototype 伴随材料无效:$rel" >&2; return 1; }
    printf '%s\n' "$task_root/$rel"
  done <<<"$selected"
}
companion_prompt_lines() {  # $1=设计文件夹(可空) → prompt 材料清单行
  [ -n "$1" ] || return 0
  local c companions
  companions="$(design_companions "$1")" || return 1
  while IFS= read -r c; do
    [ -n "$c" ] || continue
    echo "  - $c"
  done <<<"$companions"
}

build_prompt() {
  local plan="$1" wt="$2" design="$3" issue="$4" mode="$5" sheet="$6" retrieval="$7"
  local skill; skill="$(mmw_plugin_root)/skills/worktree-build"
  if [ "$mode" = merge ]; then
    cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 按 mini-plan 修复已判定方向的合并冲突。
先读 pi plugin 内 worktree-build skill 并严格执行:$skill/SKILL.md

工作树(你唯一可写的源码区,所有文件操作用它下面的绝对路径):$wt
合并冲突 mini-plan(唯一意图与验收来源):$plan

$(mmw_retrieval_candidates_prompt "$retrieval")

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
先读 pi plugin 内 worktree-build skill 并严格执行:$skill/SKILL.md

工作树(你唯一可写的源码区,所有文件操作用它下面的绝对路径):$wt
开工前依次读:
${design:+- 设计文档:$design
}${issue:+- 负责的 issue:$issue
}- 实施计划:$plan
${companions:+- 讨论态材料(prototype 仅含 accepted README + selected；selected 是 UI/状态逻辑实现起点):
$companions
}$(test_sheet_lines "$sheet")

$(mmw_retrieval_candidates_prompt "$retrieval")

只改 plan 的 File / Responsibility Map 和当前 Pack 拥有的路径。逐 Task Pack TDD、每 Pack 本地提交、禁改 docs/、禁 push/gh pr merge/部署、卡住协议和 Return Contract 全按 worktree-build skill。不要向用户提问,不要启动其它 agent;缺输入时在最终回执中结构化报告。
PROMPT
}

build_plan_prompt() {
  local plan="$1" wt="$2" design="$3" issue="$4" companions="$5" sheet="$6" retrieval="$7"
  local skill; skill="$(mmw_plugin_root)/skills/worktree-plan"
  cat <<PROMPT
你是计划撰写者,被主线程派进任务 worktree 把一个大 issue 写成一份实施计划。
先读 pi plugin 内 worktree-plan skill 并严格执行:$skill/SKILL.md

任务工作树(所有文件操作用它下面的绝对路径):$wt
唯一 plan 落点:$plan
开工前依次读:
${design:+- 源设计文档:$design
}${issue:+- 负责的大 issue:$issue
}${companions:+- 讨论态材料(prototype 仅含 accepted README + selected；只采用 selected):
$companions
}$(test_sheet_lines "$sheet")

$(mmw_retrieval_candidates_prompt "$retrieval")

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
  local file="$1" mode="$2" agent="$3" wt="$4" prompt="$5" start_sha="$6" plan="$7" issue="${8:-}"
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.meta.XXXXXX")" || return 1
  jq -n \
    --arg backend "$(mmw_worker_backend)" --arg mode "$mode" --arg agent "$agent" \
    --arg wt "$wt" --arg plan "$plan" --arg prompt "$prompt" --arg start "$start_sha" \
    --arg issue "$issue" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '{backend:$backend,mode:$mode,agent:$agent,worktree:$wt,plan:$plan,issue:$issue,
      prompt_file:$prompt,start_sha:$start,status:"dispatched",
      created_at:$at,updated_at:$at}' >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

update_meta() {
  local meta="$1"; shift
  mmw_atomic_update "$meta" "$@"
}

# 派发指令(协调者照它在会话内派 subagent run;工人回执在会话内直接回来,不落 result 文件)。
print_dispatch() {
  local agent="$1" prompt="$2" meta="$3" verify_cmd="$4" resume_note="$5" note_cmd="$6"
  echo "WORKER_BACKEND=$(mmw_worker_backend)"
  echo "AGENT=$agent"
  echo "PROMPT_FILE=$prompt"
  echo "META_FILE=$meta"
  echo "DISPATCH=单条消息用 subagent 工具派发:{agent:\"$agent\", task:PROMPT_FILE 全文原样传入, async:true};拿到 run id 立刻落账:$note_cmd(返修 resume 的唯一凭据)。$resume_note"
  echo "NEXT=工人回执完成后先跑 $verify_cmd 过机器边界门,再亲验回执声明"
}

# 同一账本重复派发守卫:上一轮未验收(可能在飞)不准覆盖。
guard_no_pending() {
  local meta="$1" status
  [ -f "$meta" ] || return 0
  status="$(jq -r '.status // empty' "$meta")"
  case "$status" in
    dispatched) die "已有派发未验收(工人可能在飞):$meta;工人已结束则先 verify,返修用 resume" ;;
    verified) die "已有验收通过的派发;补改请用 resume:$meta" ;;
  esac
}

plan_sandbox_create() {
  local task_wt="$1" ns="$2" common main sandbox branch
  common="$(git -C "$task_wt" rev-parse --git-common-dir)" || return 1
  case "$common" in /*) ;; *) common="$task_wt/$common" ;; esac
  main="$(cd "$(dirname "$common")" && pwd -P)" || return 1
  sandbox="$main/$(mmw_worktrees_rel)/$(basename "$task_wt")-plan-$ns"
  branch="$(mmw_worker_branch_prefix)/$(basename "$task_wt")-plan-$ns"
  [ ! -e "$sandbox" ] || die "plan writer 隔离 worktree 已存在:$sandbox;请先 resume 或清理失败派发"
  git -C "$main" show-ref --verify --quiet "refs/heads/$branch" \
    && die "plan writer 隔离分支已存在:$branch;请先 resume 或清理失败派发"
  git -C "$main" worktree add -b "$branch" "$sandbox" "$(git -C "$task_wt" rev-parse HEAD)" >&2 \
    || die "建立 plan writer 隔离 worktree 失败:$sandbox"
  mmw_ensure_wt_state_ignore "$sandbox"
  mmw_prepare_retrieval_graph "$task_wt" "$sandbox"
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
  local plan="" wt="" base="HEAD" design="" issue="" mode="pack" agent="" retrieval=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;; --issue) issue="$2"; shift 2 ;;
    --mode) mode="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;; --agent) agent="$2"; shift 2 ;;
    --retrieval-candidates) retrieval="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
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
  if [ -z "$agent" ]; then
    agent="$EXECUTOR_AGENT"
    if grep -qiE '(complexity|复杂度).*capable' "$plan" 2>/dev/null; then
      agent="$CAPABLE_EXECUTOR_AGENT"
    fi
  fi
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
    if [ ! -d "$run_wt" ]; then
      git -C "$repo" worktree add "$run_wt" "$native_branch" >&2 \
        || die "建立 worker worktree 失败:$run_wt"
    fi
    : >"$run_wt/.mmw-keep-worktree"
    mmw_ensure_wt_state_ignore "$run_wt"
  else
    run_wt="$target_top"
    mmw_ensure_wt_state_ignore "$run_wt"
  fi
  mmw_prepare_retrieval_graph "$repo" "$run_wt"
  local st pkg start prompt meta task_origin="-"
  if [ "$mode" = pack ] && [ -n "$design" ]; then
    task_origin="$(git -C "$(dirname "$design")" rev-parse --show-toplevel 2>/dev/null)" || die "无法定位设计所属任务 worktree:$design"
  fi
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  mkdir -p "$pkg"
  if [ -n "$native_branch" ]; then
    start="$(git -C "$repo" rev-parse "$native_branch")"
  else
    start="$(git -C "$run_wt" rev-parse HEAD)"
  fi
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  guard_no_pending "$meta"
  preflight_registered_agent "$agent"
  preflight_plugin_skill worktree-build
  local test_sheet; test_sheet="$(locate_test_sheet "${target_top:-$repo}")"
  local retrieval_snapshot="$pkg/retrieval-candidates.json"
  mmw_retrieval_candidates_snapshot "$retrieval" "$retrieval_snapshot" || die "结构候选校验失败"
  build_prompt "$plan" "$run_wt" "$design" "$issue" "$mode" "$test_sheet" "$retrieval_snapshot" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" "$mode" "$agent" "$run_wt" "$prompt" "$start" "$plan" "$issue"
  update_meta "$meta" --arg control "$wt" --arg branch "$native_branch" \
    --arg root "$native_root" --arg repo "$native_repo" --arg task_origin "$task_origin" \
    '.control_worktree=$control | .native_branch=$branch | .native_root=$root | .native_repo=$repo | .task_origin=$task_origin' \
    || die "无法记录 worker worktree 元数据"
  print_dispatch "$agent" "$prompt" "$meta" "mmw worker verify --worktree \"$wt\"" \
    "工人在独立 worktree 干活,主会话继续别的事不受影响。" \
    "mmw worker note-run-id --worktree \"$wt\" --id <run id>"
}

cmd_resume() {
  local wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -d "$wt" ] || die "worktree 不存在:$wt"
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  local st pkg meta agent run_wt task_origin
  st="$(state_for "$wt")"; pkg="$wt/$st/worker-dispatch"
  meta="$pkg/meta.json"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  task_origin="$(jq -r '.task_origin // empty' "$meta")"
  [ -n "$task_origin" ] || die "旧派发缺 task_origin，不能安全 resume；请重新 dispatch"
  validate_task_root "$task_origin" || die "任务设计确认或 prototype 状态无效"
  agent="$(jq -r .agent "$meta")"
  run_wt="$(jq -r .worktree "$meta")"
  [ -d "$run_wt" ] || die "worker worktree 不存在,不能续接:$run_wt"
  cp "$instr" "$pkg/resume-prompt.md"
  update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.status="dispatched" | .updated_at=$at' || die "无法重置派发状态"
  local run_id; run_id="$(jq -r '.run_id // empty' "$meta")"
  echo "WORKER_BACKEND=$(mmw_worker_backend)"
  echo "AGENT=$agent"
  echo "PROMPT_FILE=$pkg/resume-prompt.md"
  echo "META_FILE=$meta"
  if [ -n "$run_id" ]; then
    echo "DISPATCH=优先续原工人:subagent({action:\"resume\", id:\"$run_id\", message:PROMPT_FILE 全文})——resume 从落盘会话文件复活原上下文,长效、无会话内外之分。仅当 resume 报会话不可用才重派:{agent:\"$agent\", task:PROMPT_FILE 全文(开头注明「返修:worktree $run_wt 已有此前提交,先读 git log 对齐进度」), async:true},新 run id 重新落账:mmw worker note-run-id --worktree \"$wt\" --id <新 run id>。"
  else
    echo "DISPATCH=账本无 run id(旧派发),直接重派:{agent:\"$agent\", task:PROMPT_FILE 全文(开头注明「返修:worktree $run_wt 已有此前提交,先读 git log 对齐进度」), async:true},run id 落账:mmw worker note-run-id --worktree \"$wt\" --id <run id>。"
  fi
  echo "NEXT=工人回执完成后先跑 mmw worker verify --worktree \"$wt\""
}

cmd_plan_dispatch() {
  local plan="" wt="" design="" issue="" retrieval=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;; --issue) issue="$2"; shift 2 ;;
    --retrieval-candidates) retrieval="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
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
  # 讨论态材料由脚本机械推导；prototype 只传 accepted README + selected，不传旗标
  local ddir companions="" c
  ddir="$(design_dir_of "$design")"
  companions="$(design_companions "$ddir")" || die "讨论态材料校验失败"
  [ -z "$companions" ] || companions="$companions
"
  mmw_ensure_wt_state_ignore "$wt"
  local st ns pkg start prompt meta baseline issue_baseline
  local sandbox branch sandbox_plan sandbox_design sandbox_issue sandbox_info
  local task_plan_baseline task_issue_baseline
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  mkdir -p "$pkg"
  prompt="$pkg/prompt.md"; meta="$pkg/meta.json"
  guard_no_pending "$meta"
  guard_unique_plan_targets "$wt" "$st" "$ns" "$issue"
  preflight_registered_agent "$PLAN_AGENT"
  preflight_plugin_skill worktree-plan
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
  mkdir -p "$(dirname "$sandbox_plan")"
  local sandbox_companions=""
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
  local plan_test_sheet; plan_test_sheet="$(locate_test_sheet "$sandbox")"
  local retrieval_snapshot="$pkg/retrieval-candidates.json"
  mmw_retrieval_candidates_snapshot "$retrieval" "$retrieval_snapshot" || die "结构候选校验失败"
  build_plan_prompt "$sandbox_plan" "$sandbox" "$sandbox_design" "$sandbox_issue" "$sandbox_companions" "$plan_test_sheet" "$retrieval_snapshot" > "$prompt"
  printf '%s\n' "$start" > "$pkg/start_sha"
  write_meta "$meta" dispatch "$PLAN_AGENT" "$sandbox" "$prompt" "$start" "$sandbox_plan" "$sandbox_issue"
  update_meta "$meta" \
    --arg task_wt "$wt" --arg task_plan "$plan" --arg task_design "$design" \
    --arg task_issue "$issue" --arg branch "$branch" \
    --arg task_plan_baseline "$task_plan_baseline" --arg task_issue_baseline "$task_issue_baseline" \
    '.task_worktree=$task_wt | .task_origin=$task_wt | .task_plan=$task_plan | .task_design=$task_design |
      .task_issue=$task_issue | .sandbox_branch=$branch |
      .task_plan_baseline=$task_plan_baseline | .task_issue_baseline=$task_issue_baseline' \
    || die "无法记录 plan writer 隔离边界"
  echo "PLAN_WORKER_NS=$ns"
  print_dispatch "$PLAN_AGENT" "$prompt" "$meta" \
    "mmw worker verify --plan \"$plan\" --worktree \"$wt\"" \
    "互不依赖的 plan 并行各派一个 subagent run;verify 过门才原子发布 plan 与 issue。" \
    "mmw worker note-run-id --plan \"$plan\" --worktree \"$wt\" --id <run id>"
}

cmd_plan_resume() {
  local plan="" wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;; --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -f "$instr" ] || die "--instructions 文件不存在:$instr"
  validate_task_root "$wt" || die "任务设计确认或 prototype 状态无效"
  local st ns pkg meta sandbox
  local task_design task_issue sandbox_info sandbox_plan sandbox_design sandbox_issue start
  local task_plan_baseline task_issue_baseline
  st="$(state_for "$wt")"; ns="$(plan_ns "$plan")"; pkg="$wt/$st/plan-workers/$ns/dispatch"
  meta="$pkg/meta.json"
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  sandbox="$(jq -r .worktree "$meta")"
  task_design="$(jq -r '.task_design' "$meta")"
  task_issue="$(jq -r '.task_issue' "$meta")"
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
    mkdir -p "$(dirname "$sandbox_plan")"
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
    '.status="dispatched" | .published=false | .task_plan_baseline=$task_plan_baseline |
      .task_issue_baseline=$task_issue_baseline |
      del(.published_at,.published_plan_hash,.published_issue_hash)' \
    || die "无法重置 plan writer 发布状态"
  cp "$instr" "$pkg/resume-prompt.md"
  local run_id; run_id="$(jq -r '.run_id // empty' "$meta")"
  echo "WORKER_BACKEND=$(mmw_worker_backend)"
  echo "AGENT=$PLAN_AGENT"
  echo "PROMPT_FILE=$pkg/resume-prompt.md"
  echo "META_FILE=$meta"
  if [ -n "$run_id" ]; then
    echo "DISPATCH=优先续原计划工人:subagent({action:\"resume\", id:\"$run_id\", message:PROMPT_FILE 全文})——resume 从落盘会话文件复活原上下文,长效、无会话内外之分。仅当 resume 报会话不可用才重派:{agent:\"$PLAN_AGENT\", task:PROMPT_FILE 全文(开头注明「返修:隔离 worktree $sandbox,plan 草稿已在盘上,先读它对齐进度」), async:true},新 run id 重新落账:mmw worker note-run-id --plan \"$plan\" --worktree \"$wt\" --id <新 run id>。"
  else
    echo "DISPATCH=账本无 run id(旧派发),直接重派:{agent:\"$PLAN_AGENT\", task:PROMPT_FILE 全文(开头注明「返修:隔离 worktree $sandbox,plan 草稿已在盘上,先读它对齐进度」), async:true},run id 落账:mmw worker note-run-id --plan \"$plan\" --worktree \"$wt\" --id <run id>。"
  fi
  echo "NEXT=工人回执完成后先跑 mmw worker verify --plan \"$plan\" --worktree \"$wt\""
}

# 把 subagent run id 落进派发账本(resume 的唯一凭据;run id 长效、可跨会话)。
cmd_note_run_id() {
  local wt="" plan="" id=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --plan) plan="$2"; shift 2 ;;
    --id) id="$2"; shift 2 ;; *) die "未知参数:$1" ;;
  esac; done
  [ -d "$wt" ] || die "任务 worktree 不存在:$wt"
  [ -n "$id" ] || die "--id 必填"
  local st meta; st="$(state_for "$wt")"
  if [ -n "$plan" ]; then
    meta="$wt/$st/plan-workers/$(plan_ns "$plan")/dispatch/meta.json"
  else
    meta="$wt/$st/worker-dispatch/meta.json"
  fi
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  update_meta "$meta" --arg id "$id" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.run_id=$id | .updated_at=$at' || die "run id 落账失败"
  echo "OK run id 已落账:$meta"
}

# 机器边界门(工人回执已在会话内;这里只核机器可验事实,plan 工人过门才发布)。
cmd_verify() {
  local wt="" plan=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;; --plan) plan="$2"; shift 2 ;;
    *) die "未知参数:$1" ;;
  esac; done
  [ -n "$wt" ] || die "--worktree 必填"
  local st meta start pkg sandbox sandbox_plan sandbox_issue task_plan task_issue branch
  local plan_hash issue_hash expected_plan_hash expected_issue_hash
  st="$(state_for "$wt")"
  if [ -n "$plan" ]; then
    pkg="$wt/$st/plan-workers/$(plan_ns "$plan")/dispatch"
    meta="$pkg/meta.json"
  else
    meta="$wt/$st/worker-dispatch/meta.json"
  fi
  [ -f "$meta" ] || die "派发账本不存在:$meta"
  local task_origin; task_origin="$(jq -r '.task_origin // .task_worktree // empty' "$meta")"
  [ -n "$task_origin" ] || die "派发账本缺 task_origin，不能安全 verify"
  validate_task_root "$task_origin" || die "任务设计确认或 prototype 状态无效"
  echo "META_FILE=$meta"
  if [ -n "$plan" ]; then
    task_plan="$(jq -r '.task_plan // empty' "$meta")"
    [ -n "$task_plan" ] || die "派发账本缺 task_plan，不能安全 verify"
    [ "$plan" = "$task_plan" ] || die "--plan 与派发账本目标不一致:$plan"
    case "$task_plan" in "$wt"/*) ;; *) die "派发账本 task_plan 不在任务 worktree 内:$task_plan" ;; esac
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
      if [ "$(path_fingerprint "$wt" "${task_plan#"$wt"/}")" != "$expected_plan_hash" ] \
        || [ "$(path_fingerprint "$wt" "${task_issue#"$wt"/}")" != "$expected_issue_hash" ]; then
        echo "PLAN_PUBLISH_CONFLICT: 任务 worktree 的目标 plan/issue 在 writer 运行期间被改动" >&2
        return 3
      fi
      publish_plan_result "$sandbox" "$sandbox_plan" "$sandbox_issue" "$task_plan" "$task_issue"
      plan_hash="$(path_fingerprint "$wt" "${task_plan#"$wt"/}")"
      issue_hash="$(path_fingerprint "$wt" "${task_issue#"$wt"/}")"
      [ "$plan_hash" != missing ] || die "发布后 plan 缺失，拒绝标记 verified:$task_plan"
      update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg plan_hash "$plan_hash" --arg issue_hash "$issue_hash" \
        '.status="verified" | .published=true | .published_at=$at | .published_plan_hash=$plan_hash | .published_issue_hash=$issue_hash' \
        || die "无法记录 plan writer 发布状态"
      if ! cleanup_plan_sandbox "$wt" "$sandbox" "$branch"; then
        update_meta "$meta" --arg warning "隔离 worktree 清理失败:$sandbox" \
          '.cleanup_warning=$warning' || true
        echo "WARNING: 隔离 worktree 清理失败:$sandbox" >&2
      fi
    fi
    echo "WORKER_VERIFY=pass(plan 已发布:$task_plan)"
  else
    start="$(jq -r '.start_sha' "$meta")"
    check_docs_boundary "$(jq -r .worktree "$meta")" "$start" || return 3
    update_meta "$meta" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      '.status="verified" | .updated_at=$at' || die "无法记录验收状态"
    echo "WORKER_VERIFY=pass(docs 边界干净)"
  fi
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
  note-run-id) shift; cmd_note_run_id "$@" ;;
  check-docs) shift; cmd_check_docs "$@" ;;
  plan-dispatch) shift; cmd_plan_dispatch "$@" ;;
  plan-resume) shift; cmd_plan_resume "$@" ;;
  plan-check) shift; cmd_plan_check "$@" ;;
  verify) shift; cmd_verify "$@" ;;
  *) die "用法:worker.sh dispatch|resume|note-run-id|check-docs|plan-dispatch|plan-resume|plan-check|verify ..." ;;
esac

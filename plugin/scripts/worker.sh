#!/usr/bin/env bash
# worker.sh —— Claude Code 主线程派发 Codex 写码与写计划工人。
#
# 写码(build 落地,开子 worktree、改源码、每 Pack 提交):
#   dispatch  --plan <abs.md> --worktree <abs> [--design ...] [--issue ...] [--base ...] [--model ...] [--effort ...]
#   resume    --worktree <abs> --instructions <abs.md>
#   check-docs --worktree <abs>                 # 机器核 docs/ 红线(禁碰 docs/)
#
# 写计划(plan 撰写,在任务 worktree 内、只写 docs/plans + docs/issues、不 commit):
#   plan-dispatch --plan <落点 abs.md> --worktree <任务 wt abs> [--design ...] [--issue ...] [--model ...] [--effort ...]
#   plan-resume   --plan <落点 abs.md> --worktree <abs> --instructions <abs.md>
#   plan-check    --plan <落点 abs.md> --worktree <abs>   # 反向边界:diff 必须 ⊆ {docs/plans, docs/issues}
#
# 兼容:mmw codex * 仍路由到本脚本。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
# shellcheck source=lib/prototype-state.sh
. "$SCRIPT_DIR/lib/prototype-state.sh"

CODEX_BIN="${CODEX_BIN:-codex}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.6-terra}"
CODEX_EFFORT="${CODEX_EFFORT:-high}"
# capable 落地档(计费/权限/migration 等高风险 plan,gpt-5.6-sol medium):脚本按 plan 的 Complexity 字段自动切,不靠 agent 手传。
CODEX_CAPABLE_MODEL="${CODEX_CAPABLE_MODEL:-gpt-5.6-sol}"
CODEX_CAPABLE_EFFORT="${CODEX_CAPABLE_EFFORT:-medium}"
# 写计划档(plan-dispatch):Codex = gpt-5.6-sol high。
CODEX_PLAN_MODEL="${CODEX_PLAN_MODEL:-gpt-5.6-sol}"
CODEX_PLAN_EFFORT="${CODEX_PLAN_EFFORT:-high}"

state_for() { printf '%s' "$MMW_STATE_SUBDIR"; }

die() { echo "ERROR: $*" >&2; exit 2; }

# 派发前自检(机器可核验的事实,缺装备当场报错,不让工人开工后才发现):
# ① 点名的 skill 已装(Codex 技能根 ~/.codex/skills = $CODEX_HOME/skills);② 传给工人的文档真实存在。
preflight_skill() {  # $1=skill 名
  local sk="${MMW_AGENT_SKILLS_DIR:-$HOME/.codex/skills}/$1/SKILL.md"
  [ -f "$sk" ] || die "preflight:工人 skill 未装($sk 不存在);先把 $1 装进 Codex 技能根再派"
}
preflight_doc() {  # $1=标签 $2=路径(可空=跳过)
  [ -z "$2" ] && return 0
  [ -e "$2" ] || die "preflight:$1 不存在: $2"
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
    echo "- 仓库无测试薄层:测试写法按你已装 skill 里的测试写作权威;落点随仓库既有目录惯例;收工回执标 no-repo-test-sheet。"
  fi
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
  [ -n "$task_root" ] && [ "$task_root" != "-" ] || return 0
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

build_prompt() {  # $1=plan $2=worktree $3=design $4=issue $5=测试薄层相对路径(可空)
  local companions=""
  if [ -n "$3" ]; then
    companions="$(companion_prompt_lines "$(design_dir_of "$3")")" || return 1
  fi
  cat <<PROMPT
你是落地执行者,被主线程派进一个 worktree 落地一份计划。
**读你已装的 \`worktree-build\` skill,照它走整个落地流程**(它是总纲,细纪律在它的 references,到那步再读)。

工作树(你唯一可写的源码区): $2
开工前读这几份(worktree 内路径,顺序读):
${3:+- 设计文档(意图/合同边界/发布风险): $3
}${4:+- 你的 issue(What to build / Acceptance / Blocked by): $4
}- 你的计划(实施唯一权威): $1
${companions:+- 讨论态材料(prototype 仅含 accepted README + selected；selected 是 UI/状态逻辑实现起点):
$companions
}$(test_sheet_lines "$5")

落地铁律、逐 Pack TDD、每 Pack 提交格式、禁改 docs/、卡住协议、收工回执格式 —— **全在 worktree-build skill,照它做,本消息不重复**。
PROMPT
}

plan_ns() { basename "$1" .md; }  # 落点路径 → 派发命名空间(并行写计划在同一 worktree,靠它隔离 session/log)

build_plan_prompt() {  # $1=落点 $2=worktree $3=design $4=issue $5=讨论态材料清单(可空) $6=测试薄层相对路径(可空)
  cat <<PROMPT
你是计划撰写者,被主线程派进任务 worktree 把一个大 issue 写成一份实施计划。
**读你已装的 \`worktree-plan\` skill,照它走整个写计划流程**(总纲,细纪律在它的 references,到那步再读)。

任务工作树: $2
你的落点(只写这一份 plan 文件): $1
开工前读这几份(绝对路径,顺序读):
${3:+- 源设计文档(architecture / 合同边界 / Cross-Plan Contract Anchors): $3
}${4:+- 你负责的大 issue(What to build;## Small issues 若为 PENDING 你来拆): $4
}${5:+- 讨论态材料(prototype 仅含 accepted README + selected；只采用 selected):
$5
}$(test_sheet_lines "$6")

拆小 issue、逐 Task Pack、无 Placeholder、测试规划严谨度、Return Contract —— **全在 worktree-plan skill,照它做,本消息不重复**。
边界:只写你落点那份 plan + 你 issue 的 \`## Small issues\`;不碰源码 / \`docs/design/\` / 别的 plan;不 commit(改动留 unstaged,主线程统一提交)。
PROMPT
}

check_docs_boundary() {  # $1=worktree $2=start_sha
  local docs_touched
  docs_touched="$( { [ -n "$2" ] && git -C "$1" diff --name-only "$2" HEAD 2>/dev/null
                     git -C "$1" status --porcelain 2>/dev/null | sed 's/^...//'; } \
                   | grep '^docs/' | sort -u || true )"
  [ -z "$docs_touched" ] && return 0
  echo "DOCS_VIOLATION: Worker 改了 docs/(只有 Coordinator 能改),打回重来:" >&2
  printf '%s\n' "$docs_touched" | sed 's/^/  /' >&2
  return 3
}

check_plan_boundary() {  # $1=worktree $2=start_sha —— 反向:写计划只准碰 docs/plans + docs/issues,越界打回
  # --untracked-files=all:否则 git 把整棵未跟踪目录折叠成一条(如 docs/),核不到文件级会误判。
  local touched offending
  touched="$( { [ -n "$2" ] && git -C "$1" diff --name-only "$2" HEAD 2>/dev/null
                git -C "$1" status --porcelain --untracked-files=all 2>/dev/null | sed 's/^...//'; } \
              | sort -u | grep -v '^[[:space:]]*$' || true )"
  offending="$( printf '%s\n' "$touched" | grep -vE '^docs/(plans|issues)/' | grep -v '^[[:space:]]*$' || true )"
  [ -z "$offending" ] && return 0
  echo "PLAN_VIOLATION: 写计划工人碰了 docs/plans, docs/issues 以外的文件(只准写这两处),打回重来:" >&2
  printf '%s\n' "$offending" | sed 's/^/  /' >&2
  return 3
}

# ---------- Codex CLI backend (Claude host) ----------
# Codex 输出头部 `session id:` 行可能带 ANSI 颜色码(ESC[..m);先剥色再按行首锚点抓,
# 否则 `^session id:` 锚点被前导色码顶开、抓空,codex-session 不落盘 → resume 记账整条丢失。
_extract_codex_session() {
  local esc; esc="$(printf '\033')"
  sed -E "s/${esc}\[[0-9;]*[A-Za-z]//g" "$1" 2>/dev/null \
    | grep -m1 -E '^session id:' \
    | sed -E 's/^session id:[[:space:]]*//' || true
}
record_session() {
  local sid sd; sid="$(_extract_codex_session "$2")"
  [ -n "$sid" ] || { echo ""; return; }
  sd="$(state_for "$1")"
  mkdir -p "$1/$sd"
  printf '%s\n' "$sid" > "$1/$sd/codex-session"
  echo "$sid"
}

run_codex() {
  local wt="$1" prompt="$2"; shift 2
  local st; st="$(state_for "$wt")"
  local sd="$wt/$st/codex-logs"; mkdir -p "$sd"
  local log="$sd/run.log" last="$sd/last.md"
  set +e
  "$CODEX_BIN" "$@" -o "$last" - < "$prompt" > "$log" 2>&1
  local ec=$?
  set -e
  local sid; sid="$(record_session "$wt" "$log")"
  echo "CODEX_EXIT=$ec"
  echo "SESSION=${sid:-unknown}"
  echo "--- codex 最后消息(验收读这个,事实需主线程亲验)---"
  cat "$last" 2>/dev/null || echo "(无最后消息;读 $log 排障)"
  return "$ec"
}

# 写计划专用:session/log 落 plan-workers/<ns>/,并行同 worktree 多 writer 互不覆盖。
run_codex_plan() {  # $1=wt $2=ns $3=prompt; shift 3; rest=codex args
  local wt="$1" ns="$2" prompt="$3"; shift 3
  local st; st="$(state_for "$wt")"
  local sd="$wt/$st/plan-workers/$ns"; mkdir -p "$sd"
  local log="$sd/run.log" last="$sd/last.md"
  set +e
  "$CODEX_BIN" "$@" -o "$last" - < "$prompt" > "$log" 2>&1
  local ec=$?
  set -e
  local sid; sid="$(_extract_codex_session "$log")"
  [ -n "$sid" ] && printf '%s\n' "$sid" > "$sd/codex-session"
  echo "CODEX_EXIT=$ec"
  echo "SESSION=${sid:-unknown}"
  echo "PLAN_WORKER_NS=$ns"
  echo "--- codex 最后消息(验收读这个,事实需主线程亲验)---"
  cat "$last" 2>/dev/null || echo "(无最后消息;读 $log 排障)"
  return "$ec"
}

ensure_worktree() {
  local wt="$1" base="$2"
  if [ ! -d "$wt" ]; then
    git worktree add -b "codex/$(basename "$wt")" "$wt" "$base" >&2 \
      || die "建 worktree 失败: $wt(分支 codex/$(basename "$wt") 已存在?先清理)"
  fi
  mmw_ensure_worktree_state_ignore "$wt"
}

# 机器核 docs/ 边界(dispatch/resume 末自动跑)
cmd_check_docs() {
  local wt="" start_sha=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;;
    --start-sha) start_sha="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$wt" ] || die "--worktree 必填"
  [ -d "$wt" ] || die "worktree 不存在: $wt"
  local st; st="$(state_for "$wt")"
  if [ -z "$start_sha" ] && [ -f "$wt/$st/start_sha" ]; then
    start_sha="$(cat "$wt/$st/start_sha")"
  fi
  [ -n "$start_sha" ] || die "无 start_sha(派发记录或 --start-sha);无法核 docs 边界"
  check_docs_boundary "$wt" "$start_sha"
}

cmd_dispatch() {
  local plan="" wt="" base="HEAD" model="" effort="" design="" issue=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;;
    --issue) issue="$2"; shift 2 ;;
    --base) base="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填"
  [ -n "$wt" ]   || die "--worktree 必填"
  [ -f "$plan" ] || die "plan 文件不存在: $plan"
  local plan_top managed_man
  plan_top="$(git -C "$(dirname "$plan")" rev-parse --show-toplevel 2>/dev/null || true)"
  managed_man="$(mmw_prototype_manifest_from_top "$plan_top")"
  if [ -f "$managed_man" ] && [ "$(jq -r '.scenario // empty' "$managed_man")" = develop ]; then
    [ -n "$design" ] || die "develop worker 必须传 --design，不能绕过已确认 prototype 材料"
  fi
  preflight_skill worktree-build
  preflight_doc "设计文档(--design)" "$design"
  preflight_doc "issue(--issue)" "$issue"

  local task_origin="-"
  if [ -n "$design" ]; then
    task_origin="$(git -C "$(dirname "$design")" rev-parse --show-toplevel 2>/dev/null)" || die "无法定位设计所属任务 worktree:$design"
  fi
  ensure_worktree "$wt" "$base"
  local st; st="$(state_for "$wt")"
  mkdir -p "$wt/$st"
  printf '%s\n' "$task_origin" >"$wt/$st/task-origin"
  local test_sheet; test_sheet="$(locate_test_sheet "$wt")"

  local dmodel="$CODEX_MODEL" deffort="$CODEX_EFFORT"
  if grep -qiE '(complexity|复杂度).*capable' "$plan" 2>/dev/null; then
    dmodel="$CODEX_CAPABLE_MODEL"; deffort="$CODEX_CAPABLE_EFFORT"
  fi
  [ -n "$model" ] || model="$dmodel"
  [ -n "$effort" ] || effort="$deffort"
  local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
  local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
  printf '%s\n' "$start_sha" > "$wt/$st/start_sha"
  printf '%s %s\n' "$model" "$effort" > "$wt/$st/codex-model"
  local pf; pf="$(mktemp)"; build_prompt "$plan" "$wt" "$design" "$issue" "$test_sheet" > "$pf"
  local rc=0
  run_codex "$wt" "$pf" \
    exec -C "$wt" --sandbox workspace-write \
    ${gcd:+--add-dir "$gcd"} \
    -m "$model" -c "model_reasoning_effort=\"$effort\"" || rc=$?
  rm -f "$pf"
  if ! check_docs_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
  return "$rc"
}

cmd_resume() {
  local wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$wt" ]    || die "--worktree 必填"
  [ -f "$instr" ] || die "--instructions 文件不存在: $instr"
  local st; st="$(state_for "$wt")"
  [ -f "$wt/$st/task-origin" ] || die "旧派发缺 task-origin，不能安全 resume；请重新 dispatch"
  validate_task_root "$(cat "$wt/$st/task-origin")" || die "任务设计确认或 prototype 状态无效"

  local sf="$wt/$st/codex-session"
  [ -f "$sf" ] || record_session "$wt" "$wt/$st/codex-logs/run.log" >/dev/null
  [ -f "$sf" ] || die "无 session 记账($sf,run.log 也捞不到);首派走 dispatch"
  local sid; sid="$(cat "$sf")"
  local model="$CODEX_MODEL" effort="$CODEX_EFFORT"
  [ -f "$wt/$st/codex-model" ] && read -r model effort < "$wt/$st/codex-model"
  local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
  local start_sha; start_sha="$(cat "$wt/$st/start_sha" 2>/dev/null || git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
  local rc=0
  run_codex "$wt" "$instr" \
    exec -C "$wt" --sandbox workspace-write \
    ${gcd:+--add-dir "$gcd"} \
    -m "$model" -c "model_reasoning_effort=\"$effort\"" \
    resume "$sid" || rc=$?
  if ! check_docs_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
  return "$rc"
}

# ---------- 写计划派发(在任务 worktree 内,不开子 worktree、不 commit)----------
cmd_plan_dispatch() {
  local plan="" wt="" design="" issue="" model="" effort=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --design) design="$2"; shift 2 ;;
    --issue) issue="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填(落点路径)"
  [ -n "$wt" ]   || die "--worktree 必填"
  case "$plan" in /*) ;; *) die "--plan 必须绝对路径" ;; esac
  [ -d "$wt" ]   || die "任务 worktree 不存在: $wt"
  preflight_skill worktree-plan
  preflight_doc "设计文档(--design)" "$design"
  preflight_doc "issue(--issue)" "$issue"
  # 讨论态材料由脚本机械推导；prototype 只传 accepted README + selected，不传旗标
  local companions; companions="$(companion_prompt_lines "$(design_dir_of "$design")")" || die "讨论态材料校验失败"
  # 写计划方法论(task-pack / 自检)在 worktree-plan skill 自己的 references/,工人读 skill 自取,dispatch 不再传路径。
  local st; st="$(state_for "$wt")"; mkdir -p "$wt/$st"
  mmw_ensure_worktree_state_ignore "$wt"
  local ns; ns="$(plan_ns "$plan")"
  local test_sheet; test_sheet="$(locate_test_sheet "$wt")"

  [ -n "$model" ] || model="$CODEX_PLAN_MODEL"
  [ -n "$effort" ] || effort="$CODEX_PLAN_EFFORT"
  local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
  local start_sha; start_sha="$(git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
  mkdir -p "$wt/$st/plan-workers/$ns"
  printf '%s %s\n' "$model" "$effort" > "$wt/$st/plan-workers/$ns/codex-model"
  printf '%s\n' "$start_sha" > "$wt/$st/plan-workers/$ns/start_sha"
  local pf; pf="$(mktemp)"; build_plan_prompt "$plan" "$wt" "$design" "$issue" "$companions" "$test_sheet" > "$pf"
  local rc=0
  run_codex_plan "$wt" "$ns" "$pf" \
    exec -C "$wt" --sandbox workspace-write \
    ${gcd:+--add-dir "$gcd"} \
    -m "$model" -c "model_reasoning_effort=\"$effort\"" || rc=$?
  rm -f "$pf"
  if ! check_plan_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
  return "$rc"
}

cmd_plan_resume() {
  local plan="" wt="" instr=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --instructions) instr="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ]  || die "--plan 必填(定位是哪份计划的会话)"
  [ -n "$wt" ]    || die "--worktree 必填"
  [ -f "$instr" ] || die "--instructions 文件不存在: $instr"
  validate_task_root "$wt" || die "任务设计确认或 prototype 状态无效"
  local st; st="$(state_for "$wt")"
  local ns; ns="$(plan_ns "$plan")"
  local sd="$wt/$st/plan-workers/$ns"

  [ -f "$sd/codex-session" ] || die "无 session 记账($sd/codex-session);首派走 plan-dispatch"
  local sid; sid="$(cat "$sd/codex-session")"
  local model="$CODEX_PLAN_MODEL" effort="$CODEX_PLAN_EFFORT"
  [ -f "$sd/codex-model" ] && read -r model effort < "$sd/codex-model"
  local gcd; gcd="$(cd "$wt" && git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || gcd=""
  local start_sha; start_sha="$(cat "$sd/start_sha" 2>/dev/null || git -C "$wt" rev-parse HEAD 2>/dev/null || echo "")"
  local rc=0
  run_codex_plan "$wt" "$ns" "$instr" \
    exec -C "$wt" --sandbox workspace-write \
    ${gcd:+--add-dir "$gcd"} \
    -m "$model" -c "model_reasoning_effort=\"$effort\"" \
    resume "$sid" || rc=$?
  if ! check_plan_boundary "$wt" "$start_sha" && [ "$rc" -eq 0 ]; then rc=3; fi
  return "$rc"
}

cmd_plan_check() {
  local plan="" wt="" start_sha=""
  while [ $# -gt 0 ]; do case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --worktree) wt="$2"; shift 2 ;;
    --start-sha) start_sha="$2"; shift 2 ;;
    *) die "未知参数: $1" ;;
  esac; done
  [ -n "$plan" ] || die "--plan 必填"
  [ -n "$wt" ]   || die "--worktree 必填"
  [ -d "$wt" ]   || die "worktree 不存在: $wt"
  local st; st="$(state_for "$wt")"
  local ns; ns="$(plan_ns "$plan")"
  [ -z "$start_sha" ] && [ -f "$wt/$st/plan-workers/$ns/start_sha" ] && start_sha="$(cat "$wt/$st/plan-workers/$ns/start_sha")"
  [ -n "$start_sha" ] || die "无 start_sha(派发记录或 --start-sha);无法核写计划边界"
  check_plan_boundary "$wt" "$start_sha"
}

case "${1:-}" in
  dispatch) shift; cmd_dispatch "$@" ;;
  resume)   shift; cmd_resume "$@" ;;
  check-docs) shift; cmd_check_docs "$@" ;;
  plan-dispatch) shift; cmd_plan_dispatch "$@" ;;
  plan-resume)   shift; cmd_plan_resume "$@" ;;
  plan-check)    shift; cmd_plan_check "$@" ;;
  *) die "用法: worker.sh dispatch|resume|check-docs|plan-dispatch|plan-resume|plan-check ..." ;;
esac

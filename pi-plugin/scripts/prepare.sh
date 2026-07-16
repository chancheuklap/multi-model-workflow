#!/usr/bin/env bash
# prepare.sh —— 入口准备层(路由确定后的全部机械活,一条命令做完)
#
#   new     从主仓库建命名 worktree(本地 HEAD 分叉)+ scaffold docs + 写 manifest
#   resume  从 worktree 内读 manifest,返回"你是谁、在哪、什么状态"(单一真相源)
#   cleanup 合并后删干净:worktree + 分支 + 临时状态(随 worktree 一起没)
#
# 路由(四选一)由 LLM 当场判,不在本脚本。本脚本只做机器该快做的准备。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/runtime.sh
. "$SCRIPT_DIR/lib/runtime.sh"
ROUTES="$SCRIPT_DIR/../state-schema/routes.json"
# 所有任务统一写入 pi 状态平面。
STATE_SUBDIR="$(mmw_state_subdir)"
MANIFEST_NAME="task.json"

die() { echo "ERROR: $*" >&2; exit 1; }

# 主仓库 top-level(worktree 里 .git 是文件,主仓库里是目录)
git_toplevel() { git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"; }
in_worktree() { [ -f "$1/.git" ]; }

# 主仓库状态平面遮蔽见 lib/runtime.sh mmw_ensure_state_ignore

# ---------- new ----------
cmd_new() {
  local scenario="" slug="" title="" request="" direction_given=false
  while [ $# -gt 0 ]; do
    case "$1" in
      --scenario) scenario="$2"; shift 2 ;;
      --slug)     slug="$2";     shift 2 ;;
      --title)    title="$2";    shift 2 ;;
      --request)  request="$2";  shift 2 ;;
      --direction-given) direction_given=true; shift ;;   # 用户开口已带明确方向:propose 降级(where 照此指路)
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$scenario" ] || die "--scenario 必填(small-change|develop|bug)"
  [ -n "$slug" ]     || die "--slug 必填"
  [ -n "$title" ]    || die "--title 必填"
  [ -n "$request" ]  || die "--request 必填(用户原始需求与验收条件,不能只传标题)"
  case "$scenario" in small-change|develop|bug) ;; *) die "--scenario 只能 small-change|develop|bug(merge 不开 worktree)" ;; esac
  printf '%s' "$slug" | grep -Eq '^[a-z0-9][a-z0-9._-]{0,63}$' || die "slug 非法(小写字母数字 . _ -,≤64):$slug"

  local top; top="$(git_toplevel)"
  in_worktree "$top" && die "已在 worktree 内($top),建新 worktree 请回主仓库"

  local wt="$top/$(mmw_worktrees_rel)/$slug"
  [ -e "$wt" ] && die "worktree 已存在:$wt"
  git -C "$top" show-ref --verify --quiet "refs/heads/$slug" && die "分支已存在:$slug(换个 slug 或先清理)"
  mmw_ensure_state_ignore "$top"   # 建 worktree 前遮蔽主仓库状态平面,git status 零残留

  local base; base="$(git -C "$top" rev-parse HEAD)"
  # 从本地最新 HEAD 分叉
  git -C "$top" worktree add -b "$slug" "$wt" HEAD >&2

  # 文档落点:investigating / design / issues / plans 按 slug,context 项目级共享(domain-modeling 维护)
  mkdir -p "$wt/docs/investigating" "$wt/docs/design" "$wt/docs/issues" "$wt/docs/plans" "$wt/docs/context" "$wt/docs/reviews" "$wt/$STATE_SUBDIR"
  # 状态平面对 git 不可见。
  mmw_ensure_wt_state_ignore "$wt"
  # 过程产物不永久存档(随 worktree 删):现状报告 / 审查留痕 / 终审报告。
  # 提交进分支的只有:设计(含 mockup/prototype)/ issue / 计划 / 领域文档(docs/context 项目级资产)。
  # (merge-brief 不在这:merge 场景在主仓库,产物落状态平面,不进 docs/)
  # 本 .gitignore 自忽略:plugin 脚手架不进 git,随 worktree 死,下个任务 new 时重建。
  cat > "$wt/docs/.gitignore" <<'IGN'
investigating/
reviews/
*-final-review.md
.gitignore
IGN

  # 阶段序列从预设解析:主干被 preset 过滤后的开着阶段(单源,prepare 不硬编码)
  [ -f "$ROUTES" ] || die "找不到 routes.json: $ROUTES"
  local phases_json; phases_json="$(jq -c --arg s "$scenario" '.presets[$s] // empty' "$ROUTES")"
  [ -n "$phases_json" ] || die "routes.json 未定义预设 $scenario 的 phases"
  local phase; phase="$(printf '%s' "$phases_json" | jq -r '.[0]')"
  # 值守档:讨论态天生 attended(develop 有 propose/design 讨论期);bug/small-change 无讨论期,
  # 但动手前有一次轻确认(scenario reference 定),之后自主 → 起步 afk。过门(approve)自动切 afk。
  local attendance="afk"
  [ "$scenario" = "develop" ] && attendance="attended"
  local plugin_version
  plugin_version="$(jq -r '.version // ""' "$SCRIPT_DIR/../package.json" 2>/dev/null || echo "")"

  local created; created="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  jq -n \
    --arg sv "2" --arg slug "$slug" --arg title "$title" --arg request "$request" --arg scenario "$scenario" \
    --argjson phases "$phases_json" \
    --arg status "active" --arg phase "$phase" --arg created "$created" \
    --arg base "$base" --arg branch "$slug" --arg wt "$wt" \
    --argjson dg "$direction_given" \
    --arg inv "docs/investigating/$slug" --arg ddoc "docs/design/$slug" --arg idir "docs/issues/$slug" --arg pdir "docs/plans/$slug" --arg ctx "docs/context" \
    --arg attendance "$attendance" --arg pv "$plugin_version" \
    '{schema_version:$sv, slug:$slug, title:$title, request:$request, scenario:$scenario, phases:$phases, direction_given:$dg,
      status:$status, waiting_for:null, phase:$phase, phase_index:0, step_index:0, gate:null,
      created_at:$created, updated_at:$created, plugin_version:$pv, base_commit:$base,
      branch:$branch, worktree_path:$wt, docs:{investigating:$inv, design:$ddoc, issues:$idir, plans:$pdir, context:$ctx},
      repair_count:0, turnaround_count:0, attendance:$attendance, unattended_policy:null,
      note:null, approval:null,
      artifacts:[], phase_outputs:{}, open_items:[], subtasks:[], history:[]}' \
    > "$wt/$STATE_SUBDIR/$MANIFEST_NAME"

  # 给 SKILL/LLM 的回执:下一步进 worktree,再进对应 phase
  cat <<EOF
PREPARED
worktree_path=$wt
branch=$slug
scenario=$scenario
phase=$phase
design_doc=docs/design/$slug
NEXT=$(mmw_enter_worktree_hint "$wt"); 然后进入 $scenario 的 $phase 阶段
EOF
}

# ---------- resume ----------
cmd_resume() {
  local top; top="$(git_toplevel)"
  local sd; sd="$(mmw_resolve_state_subdir "$top")"
  local manifest="$top/$sd/$MANIFEST_NAME"
  if [ ! -f "$manifest" ]; then
    echo "UNMANAGED"   # 没 manifest:当全新任务处理(回 SKILL 走路由)
    exit 0
  fi
  jq -e . "$manifest" >/dev/null 2>&1 || die "manifest 损坏:$manifest"
  # resume = 用户答完回来继续:waiting-user 翻回 active(否则状态一直挂 waiting 到下次 handoff)。
  # 只翻这一种,别的状态原样;fail-closed 写(空/非法 JSON 拒写、保留原档)。
  if [ "$(jq -r .status "$manifest")" = "waiting-user" ]; then
    local tmp; tmp="$(mktemp)"
    if jq '.status="active" | .waiting_for=null' "$manifest" > "$tmp" && [ -s "$tmp" ] && jq -e . "$tmp" >/dev/null 2>&1; then
      mv "$tmp" "$manifest"
    else
      rm -f "$tmp"; die "resume 翻 active 写入失败,manifest 保留不动"
    fi
  fi
  echo "MANAGED"
  cat "$manifest"
}

# ---------- scope(需求变化:刷新 manifest.request 为当前确认范围与验收基线) ----------
cmd_scope() {
  local request=""
  while [ $# -gt 0 ]; do
    case "$1" in --request) request="$2"; shift 2 ;; *) die "未知参数: $1" ;; esac
  done
  [ -n "$request" ] || die "--request 必填(更新后的完整范围与验收条件,不是增量说明)"
  local top sd manifest tmp
  top="$(git_toplevel)"
  sd="$(mmw_resolve_state_subdir "$top")"
  manifest="$top/$sd/$MANIFEST_NAME"
  [ -f "$manifest" ] || die "当前不是在管任务(无 manifest)"
  tmp="$(mktemp)"
  if jq --arg request "$request" '.request=$request' "$manifest" > "$tmp" \
    && [ -s "$tmp" ] && jq -e . "$tmp" >/dev/null 2>&1; then
    mv "$tmp" "$manifest"
  else
    rm -f "$tmp"; die "scope 写入失败,manifest 保留不动"
  fi
  echo "SCOPE_UPDATED"
}

# ---------- cleanup(合并后删干净) ----------
cmd_cleanup() {
  local slug=""
  while [ $# -gt 0 ]; do
    case "$1" in --slug) slug="$2"; shift 2 ;; *) die "未知参数: $1" ;; esac
  done
  [ -n "$slug" ] || die "--slug 必填"
  local top; top="$(git_toplevel)"
  in_worktree "$top" && die "在 worktree 内不能清理自己,回主仓库执行 cleanup"
  # 只在 pi worktree 根查找。
  local wt; wt="$(mmw_find_worktree "$top" "$slug" || true)"
  [ -n "$wt" ] || wt="$top/$(mmw_worktrees_rel)/$slug"

  # 安全门:动任何东西之前先确认分支已并入当前 HEAD,未并入直接拒,绝不先删后死
  if git -C "$top" show-ref --verify --quiet "refs/heads/$slug"; then
    git -C "$top" merge-base --is-ancestor "$slug" HEAD 2>/dev/null \
      || die "分支 $slug 未并入当前 HEAD,拒绝清理(先 merge,确认要丢弃再手动 git worktree remove)"
  fi
  # 过门:worktree 内含 .pi 临时状态(gitignore),--force 一并删。
  # worktree 真删失败 → 直接拒,绝不接着删分支(防留下悬空 worktree 却把分支删了,失败不可见)。
  if [ -e "$wt" ]; then
    git -C "$top" worktree remove --force "$wt" >/dev/null 2>&1 \
      || die "worktree remove 失败:$wt(没删成,分支保留不动,请人查后手动处理)"
  fi
  git -C "$top" worktree prune >/dev/null 2>&1 || true   # 清理已消失 worktree 的残留记录(安全)
  # 分支已验证并入 HEAD,-D 安全;删失败让它 surface(set -e 中止)
  git -C "$top" show-ref --verify --quiet "refs/heads/$slug" && git -C "$top" branch -D "$slug" >/dev/null
  echo "CLEANED slug=$slug"
}

# ---------- escalate(bug/small-change 中途发现系统性设计问题 → 原地升级到 develop 完整设计路) ----------
# PDF:bug「了解仓库现状 → 系统性设计问题 → create worktree(develop)」。worktree 已在,
# 升级 = 把剩余流水线从当前预设换成 develop 预设,游标回首阶段(investigate,带设计意图重查),
# 投查成果(phase_outputs/artifacts/subtasks)全留、history 记一笔。不开新 worktree、不丢已查。
cmd_escalate() {
  local to=""
  while [ $# -gt 0 ]; do
    case "$1" in --to) to="$2"; shift 2 ;; *) die "未知参数: $1" ;; esac
  done
  [ -n "$to" ] || die "--to 必填(目标预设,目前只支持 develop)"
  case "$to" in develop) ;; *) die "--to 目前只支持 develop(系统性设计问题升级到完整设计路)" ;; esac

  local top; top="$(git_toplevel)"
  in_worktree "$top" || die "escalate 在任务 worktree 内执行(当前不在 worktree)"
  local sd; sd="$(mmw_resolve_state_subdir "$top")"
  local man="$top/$sd/$MANIFEST_NAME"
  [ -f "$man" ] || die "当前不是在管任务(无 manifest)"
  jq -e . "$man" >/dev/null 2>&1 || die "manifest 损坏:$man"
  [ -f "$ROUTES" ] || die "找不到 routes.json: $ROUTES"

  local cur_scenario cur_phase
  cur_scenario="$(jq -r .scenario "$man")"
  cur_phase="$(jq -r .phase "$man")"
  [ "$cur_scenario" != "$to" ] || die "已是 $to,无需升级"

  local phases_json first
  phases_json="$(jq -c --arg s "$to" '.presets[$s] // empty' "$ROUTES")"
  [ -n "$phases_json" ] || die "routes.json 未定义预设 $to"
  first="$(printf '%s' "$phases_json" | jq -r '.[0]')"

  local at; at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local tmp; tmp="$(mktemp)"
  jq --arg sc "$to" --argjson ph "$phases_json" --arg first "$first" --arg cur "$cur_phase" --arg at "$at" \
    '.scenario=$sc | .phases=$ph | .phase=$first | .phase_index=0 | .step_index=0 | .gate=null | .status="active"
     | .repair_count=0 | .turnaround_count=0
     | .history += [{phase:$cur, conclusion:("escalate→"+$sc), at:$at}]' \
    "$man" > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; die "升级写入失败(空/非法 JSON),manifest 保留不动"
  fi
  mv "$tmp" "$man"
  cat <<EOF
ESCALATED from=$cur_scenario to=$to
phase=$first(回 investigate,带设计意图重查;投查成果与 history 全保留)
NEXT=mmw where(按 develop 续:investigate→propose→design→…)
EOF
}

# ---------- team(merge 用:列全队在管 worktree 的身份与状态) ----------
cmd_team() {
  local top; top="$(git_toplevel)"
  in_worktree "$top" && die "在 worktree 内;merge 回主仓库执行"
  echo "TEAM"
  local found=0 man
  # 扫 pi 状态平面的全部在飞 manifest。
  while IFS= read -r man; do
    [ -n "$man" ] || continue
    found=1
    # 每队员一行 JSON:身份 + 状态 + 设计文档(merge 据此查业务/设计冲突,非纯 git)
    jq -c '{slug, title, scenario, phase, status, branch, base_commit,
            design: .docs.design, worktree: .worktree_path,
            open_items: (.open_items|length), subtasks: (.subtasks|length)}' "$man"
  done < <(mmw_foreach_flying_manifest "$top")
  [ "$found" = 1 ] || echo "(无在管 worktree)"
}

case "${1:-}" in
  new)      shift; cmd_new "$@" ;;
  resume)   shift; cmd_resume "$@" ;;
  scope)    shift; cmd_scope "$@" ;;
  cleanup)  shift; cmd_cleanup "$@" ;;
  escalate) shift; cmd_escalate "$@" ;;
  team)     shift; cmd_team "$@" ;;
  *) die "用法: prepare.sh new|resume|cleanup|escalate|team ..." ;;
esac

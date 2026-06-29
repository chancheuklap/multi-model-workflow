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
ROUTES="$SCRIPT_DIR/../state-schema/routes.json"
STATE_SUBDIR=".claude/multi-model-workflow"
MANIFEST_NAME="task.json"

die() { echo "ERROR: $*" >&2; exit 1; }

# 主仓库 top-level(worktree 里 .git 是文件,主仓库里是目录)
git_toplevel() { git rev-parse --show-toplevel 2>/dev/null || die "不在 git 仓库内"; }
in_worktree() { [ -f "$1/.git" ]; }

# ---------- new ----------
cmd_new() {
  local scenario="" slug="" title=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --scenario) scenario="$2"; shift 2 ;;
      --slug)     slug="$2";     shift 2 ;;
      --title)    title="$2";    shift 2 ;;
      *) die "未知参数: $1" ;;
    esac
  done
  [ -n "$scenario" ] || die "--scenario 必填(small-change|develop|bug)"
  [ -n "$slug" ]     || die "--slug 必填"
  [ -n "$title" ]    || die "--title 必填"
  case "$scenario" in small-change|develop|bug) ;; *) die "--scenario 只能 small-change|develop|bug(merge 不开 worktree)" ;; esac
  printf '%s' "$slug" | grep -Eq '^[a-z0-9][a-z0-9._-]{0,63}$' || die "slug 非法(小写字母数字 . _ -,≤64):$slug"

  local top; top="$(git_toplevel)"
  in_worktree "$top" && die "已在 worktree 内($top),建新 worktree 请回主仓库"

  local wt="$top/.claude/worktrees/$slug"
  [ -e "$wt" ] && die "worktree 已存在:$wt"
  git -C "$top" show-ref --verify --quiet "refs/heads/$slug" && die "分支已存在:$slug(换个 slug 或先清理)"

  local base; base="$(git -C "$top" rev-parse HEAD)"
  # 从本地最新 HEAD 分叉
  git -C "$top" worktree add -b "$slug" "$wt" HEAD >&2

  # 文档落点:investigating / design / issues / plans 按 slug,context 项目级共享(domain-modeling 维护)
  mkdir -p "$wt/docs/investigating" "$wt/docs/design" "$wt/docs/issues" "$wt/docs/plans" "$wt/docs/context" "$wt/$STATE_SUBDIR"

  # 阶段序列从预设解析:主干被 preset 过滤后的开着阶段(单源,prepare 不硬编码)
  [ -f "$ROUTES" ] || die "找不到 routes.json: $ROUTES"
  local phases_json; phases_json="$(jq -c --arg s "$scenario" '.presets[$s] // empty' "$ROUTES")"
  [ -n "$phases_json" ] || die "routes.json 未定义预设 $scenario 的 phases"
  local phase; phase="$(printf '%s' "$phases_json" | jq -r '.[0]')"

  local created; created="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  jq -n \
    --arg sv "1" --arg slug "$slug" --arg title "$title" --arg scenario "$scenario" \
    --argjson phases "$phases_json" \
    --arg status "active" --arg phase "$phase" --arg created "$created" \
    --arg base "$base" --arg branch "$slug" --arg wt "$wt" \
    --arg inv "docs/investigating/$slug" --arg ddoc "docs/design/$slug" --arg idir "docs/issues/$slug" --arg pdir "docs/plans/$slug" --arg ctx "docs/context" \
    '{schema_version:$sv, slug:$slug, title:$title, scenario:$scenario, phases:$phases,
      status:$status, phase:$phase, phase_index:0, gate:null, created_at:$created, base_commit:$base,
      branch:$branch, worktree_path:$wt, docs:{investigating:$inv, design:$ddoc, issues:$idir, plans:$pdir, context:$ctx},
      repair_count:0, turnaround_count:0,
      artifacts:[], phase_outputs:{}, open_items:[], subtasks:[], history:[]}' \
    > "$wt/$STATE_SUBDIR/$MANIFEST_NAME"

  # 给 SKILL/LLM 的回执:下一步去 EnterWorktree(path),再进对应 phase
  cat <<EOF
PREPARED
worktree_path=$wt
branch=$slug
scenario=$scenario
phase=$phase
design_doc=docs/design/$slug
NEXT=EnterWorktree({ path: "$wt" }) 然后进入 $scenario 的 $phase 阶段
EOF
}

# ---------- resume ----------
cmd_resume() {
  local top; top="$(git_toplevel)"
  local manifest="$top/$STATE_SUBDIR/$MANIFEST_NAME"
  if [ ! -f "$manifest" ]; then
    echo "UNMANAGED"   # 没 manifest:当全新任务处理(回 SKILL 走路由)
    exit 0
  fi
  jq -e . "$manifest" >/dev/null 2>&1 || die "manifest 损坏:$manifest"
  echo "MANAGED"
  cat "$manifest"
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
  local wt="$top/.claude/worktrees/$slug"

  # 安全门:动任何东西之前先确认分支已并入当前 HEAD,未并入直接拒,绝不先删后死
  if git -C "$top" show-ref --verify --quiet "refs/heads/$slug"; then
    git -C "$top" merge-base --is-ancestor "$slug" HEAD 2>/dev/null \
      || die "分支 $slug 未并入当前 HEAD,拒绝清理(先 merge,确认要丢弃再手动 git worktree remove)"
  fi
  # 过门:worktree 内含 .claude 临时状态(gitignore),--force 一并删。
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

# ---------- team(merge 用:列全队在管 worktree 的身份与状态) ----------
cmd_team() {
  local top; top="$(git_toplevel)"
  in_worktree "$top" && die "在 worktree 内;merge 回主仓库执行"
  local wtroot="$top/.claude/worktrees"
  [ -d "$wtroot" ] || { echo "TEAM 空(无在管 worktree)"; return 0; }
  echo "TEAM"
  local found=0
  for d in "$wtroot"/*/; do
    local man="$d$STATE_SUBDIR/$MANIFEST_NAME"
    [ -f "$man" ] || continue
    found=1
    # 每队员一行 JSON:身份 + 状态 + 设计文档(merge 据此查业务/设计冲突,非纯 git)
    jq -c '{slug, title, scenario, phase, status, branch, base_commit,
            design: .docs.design, worktree: .worktree_path,
            open_items: (.open_items|length), subtasks: (.subtasks|length)}' "$man"
  done
  [ "$found" = 1 ] || echo "(无合法 manifest)"
}

case "${1:-}" in
  new)     shift; cmd_new "$@" ;;
  resume)  shift; cmd_resume "$@" ;;
  cleanup) shift; cmd_cleanup "$@" ;;
  team)    shift; cmd_team "$@" ;;
  *) die "用法: prepare.sh new|resume|cleanup|team ..." ;;
esac

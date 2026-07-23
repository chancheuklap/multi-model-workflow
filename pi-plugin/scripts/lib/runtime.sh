#!/usr/bin/env bash
# pi 原生运行时路径与工具约定。
# prepare/flow/loop/review/worker/hooks 统一 source 本文件。

mmw_state_parent() { printf '.pi'; }
mmw_state_subdir() { printf '.pi/multi-model-workflow'; }
mmw_worktrees_rel() { printf '.pi/worktrees'; }
mmw_worker_branch_prefix() { printf 'worker'; }
mmw_ask_user_tool() { printf 'ask_user'; }
mmw_shell_tool() { printf 'bash'; }
mmw_worker_backend() { printf 'pi-subagents'; }

# 原子更新 JSON 账本(jq 表达式作参数)。
mmw_atomic_update() {
  local file="$1"; shift
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.pi-meta.XXXXXX")" || return 1
  jq "$@" "$file" >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

mmw_resolve_state_subdir() {
  printf '%s' "$(mmw_state_subdir)"
}

mmw_find_worktree() {
  local top="$1" slug="$2" path
  [ -n "$top" ] && [ -n "$slug" ] || return 1
  path="$top/$(mmw_worktrees_rel)/$slug"
  [ -d "$path" ] || return 1
  printf '%s' "$path"
}

mmw_foreach_flying_manifest() {
  local top="$1" root d man
  [ -n "$top" ] || return 0
  root="$top/$(mmw_worktrees_rel)"
  [ -d "$root" ] || return 0
  for d in "$root"/*/; do
    [ -d "$d" ] || continue
    man="${d}$(mmw_state_subdir)/task.json"
    [ -f "$man" ] && printf '%s\n' "$man"
  done
}

mmw_ensure_state_ignore() {
  local top="$1" parent g line
  parent="$(mmw_state_parent)"
  g="$top/$parent/.gitignore"
  mkdir -p "$top/$parent"
  if [ -f "$g" ] && grep -qxF '*' "$g" 2>/dev/null; then return 0; fi
  for line in 'worktrees/' 'multi-model-workflow/' '.gitignore'; do
    { [ -f "$g" ] && grep -qxF "$line" "$g"; } || printf '%s\n' "$line" >> "$g"
  done
}

mmw_ensure_wt_state_ignore() {
  local wt="$1" parent
  parent="$(mmw_state_parent)"
  mkdir -p "$wt/$parent"
  [ -f "$wt/$parent/.gitignore" ] || printf '*\n' > "$wt/$parent/.gitignore"
}

mmw_enter_worktree_hint() {
  printf '在 worktree 路径继续本任务: cd %s 后跑 mmw where，或在该目录新开 pi 会话' "$1"
}

mmw_plugin_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

# manifest 原子写 + fail-closed(flow/note 共用单源;prototype.sh 因三镜像实体副本约束自含同款):
# 临时文件建在 manifest 同目录(同文件系统,mv 才是原子 rename);验过非空且合法 JSON 才落盘,
# 上游 jq 失败时保留原 manifest 并退非零(绝不把 task.json 截成 0 字节)。每次落盘刷 updated_at。
mmw_write_manifest() {
  local m="$1" tmp stamped
  tmp="$(mktemp "$(dirname "$m")/.mmw-manifest.XXXXXX")" || return 1
  cat > "$tmp"
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"; echo "ERROR: 拒绝写入空/非法 JSON 到 $m;原 manifest 保留" >&2; return 1
  fi
  stamped="$(mktemp "$(dirname "$m")/.mmw-manifest.XXXXXX")" || { rm -f "$tmp"; return 1; }
  if jq --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '.updated_at=$at' "$tmp" > "$stamped" \
     && [ -s "$stamped" ] && jq -e . "$stamped" >/dev/null 2>&1; then
    mv "$stamped" "$m"; rm -f "$tmp"
  else
    rm -f "$stamped"; mv "$tmp" "$m"
  fi
}

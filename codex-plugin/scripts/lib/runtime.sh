#!/usr/bin/env bash
# Codex 原生运行时路径与工具约定。
# prepare/flow/loop/review/worker/hooks 统一 source 本文件。

mmw_state_parent() { printf '.codex'; }
mmw_state_subdir() { printf '.codex/multi-model-workflow'; }
mmw_worktrees_rel() { printf '.codex/worktrees'; }
mmw_worker_branch_prefix() { printf 'worker'; }
mmw_ask_user_tool() { printf 'request_user_input'; }
mmw_shell_tool() { printf 'exec_command'; }
mmw_worker_backend() { printf 'codex-native-subagents'; }

# 原子更新 JSON 账本(jq 表达式作参数)。
mmw_atomic_update() {
  local file="$1"; shift
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.codex-meta.XXXXXX")" || return 1
  jq "$@" "$file" >"$tmp" \
    && jq -e . "$tmp" >/dev/null 2>&1 \
    && mv "$tmp" "$file" \
    || { rm -f "$tmp"; return 1; }
}

mmw_resolve_state_subdir() {
  printf '%s' "$(mmw_state_subdir)"
}

mmw_find_worktree() {
  local top="$1" slug="$2" path man
  [ -n "$top" ] && [ -n "$slug" ] || return 1
  while IFS= read -r path; do
    [ -d "$path" ] || continue
    man="$path/$(mmw_state_subdir)/task.json"
    [ -f "$man" ] || continue
    if [ "$(jq -r '.slug // empty' "$man" 2>/dev/null)" = "$slug" ]; then
      printf '%s' "$path"
      return 0
    fi
  done < <(git -C "$top" worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p')
  return 1
}

mmw_foreach_flying_manifest() {
  local top="$1" path man
  [ -n "$top" ] || return 0
  while IFS= read -r path; do
    [ -d "$path" ] || continue
    man="$path/$(mmw_state_subdir)/task.json"
    [ -f "$man" ] && printf '%s\n' "$man"
  done < <(git -C "$top" worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p')
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
  printf '在 Codex App 当前任务 worktree 继续：确认 cwd=%s 后运行 mmw where' "$1"
}

mmw_plugin_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

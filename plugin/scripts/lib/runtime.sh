#!/usr/bin/env bash
# runtime.sh —— Claude Code 状态平面与 worktree 公共操作。

MMW_STATE_SUBDIR=".claude/multi-model-workflow"
MMW_WORKTREES_REL=".claude/worktrees"

mmw_ensure_state_ignore() {
  local top="$1"
  local g="$top/.claude/.gitignore" line
  mkdir -p "$top/.claude"
  if [ -f "$g" ] && grep -qxF '*' "$g" 2>/dev/null; then return 0; fi
  for line in 'worktrees/' 'multi-model-workflow/' '.gitignore'; do
    { [ -f "$g" ] && grep -qxF "$line" "$g"; } || printf '%s\n' "$line" >> "$g"
  done
}

mmw_ensure_worktree_state_ignore() {
  local wt="$1"
  mkdir -p "$wt/.claude"
  [ -f "$wt/.claude/.gitignore" ] || printf '*\n' > "$wt/.claude/.gitignore"
}

# 项目 hook 可覆盖通用初始化;普通仓库统一由用户级 Graphify 生命周期模块预热。
# 两条路径失败都明确告警但不阻断任务创建;首次复杂检索会再次 ensure。
mmw_prepare_worktree() {
  local source_wt="$1" target_wt="$2"
  local hook="" init_log="" graph_manager="" candidate

  for candidate in "$target_wt/.claude/worktree-init.sh" "$target_wt/.pi/worktree-init.sh"; do
    [ -f "$candidate" ] && { hook="$candidate"; break; }
  done

  init_log="$(mktemp "${TMPDIR:-/tmp}/mmw-worktree-init.XXXXXX")" || {
    echo "[mmw] WARNING: 无法创建 worktree 初始化日志:$target_wt" >&2
    return 0
  }

  if [ -n "$hook" ]; then
    if (
      cd "$target_wt"
      /bin/bash "$hook" "$source_wt" "$target_wt"
    ) >"$init_log" 2>&1; then
      [ ! -s "$init_log" ] || cat "$init_log" >&2
    else
      cat "$init_log" >&2
      echo "[mmw] WARNING: 项目 worktree 初始化失败;继续任务:$target_wt" >&2
    fi
    rm -f "$init_log"
    return 0
  fi

  graph_manager="$(command -v graphify-ensure 2>/dev/null || true)"
  if [ -z "$graph_manager" ]; then
    rm -f "$init_log"
    echo "[mmw] WARNING: 找不到 graphify-ensure;工作树已创建,首次复杂检索前必须补建图:$target_wt" >&2
    return 0
  fi
  if "$graph_manager" --repo "$target_wt" --source "$source_wt" >"$init_log" 2>&1; then
    [ ! -s "$init_log" ] || cat "$init_log" >&2
  else
    cat "$init_log" >&2
    echo "[mmw] WARNING: 通用图谱初始化失败;工作树已创建,首次复杂检索将重试:$target_wt" >&2
  fi
  rm -f "$init_log"
  return 0
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

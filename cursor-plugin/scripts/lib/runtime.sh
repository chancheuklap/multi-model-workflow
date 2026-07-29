#!/usr/bin/env bash
# Cursor 原生运行时路径与工具约定。
# prepare/flow/loop/review/worker/hooks 统一 source 本文件。

mmw_state_parent() { printf '.cursor'; }
mmw_state_subdir() { printf '.cursor/multi-model-workflow'; }
mmw_worktrees_rel() { printf '.cursor/worktrees'; }
mmw_worker_branch_prefix() { printf 'worker'; }
mmw_ask_user_tool() { printf 'AskQuestion'; }
# 问用户合同短句（写入 prompt / 文档时用）：名字真实，但按模型挂载。
mmw_ask_user_howto() {
  printf '%s' 'AskQuestion（宿主注入的结构化多选；会话工具列表无此项时禁止假装调用，改用聊天正文固定选项；不是 cursor_dialog）'
}
mmw_shell_tool() { printf 'Shell'; }
mmw_worker_backend() { printf 'cursor-task'; }

# 原子更新 JSON 账本(jq 表达式作参数)。
mmw_atomic_update() {
  local file="$1"; shift
  local tmp
  tmp="$(mktemp "$(dirname "$file")/.cursor-meta.XXXXXX")" || return 1
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
  # 优先仓内约定根
  path="$top/$(mmw_worktrees_rel)/$slug"
  if [ -d "$path" ]; then
    printf '%s' "$path"
    return 0
  fi
  # Cursor UI 悬空 wt：扫 git worktree list，按 task.json.slug 匹配
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    man="$path/$(mmw_state_subdir)/task.json"
    [ -f "$man" ] || continue
    if [ "$(jq -r '.slug // empty' "$man" 2>/dev/null)" = "$slug" ]; then
      printf '%s' "$path"
      return 0
    fi
  done < <(git -C "$top" worktree list --porcelain 2>/dev/null | /usr/bin/awk '/^worktree /{print substr($0,10)}')
  return 1
}

# 发现在飞任务：git worktree list 各 path 下找 task.json（含 UI 悬空 wt + 仓内工人 wt）
mmw_foreach_flying_manifest() {
  local top="$1" path man seen=""
  [ -n "$top" ] || return 0
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    man="$path/$(mmw_state_subdir)/task.json"
    [ -f "$man" ] || continue
    case " $seen " in
      *" $man "*) continue ;;
    esac
    seen="$seen $man"
    printf '%s\n' "$man"
  done < <(git -C "$top" worktree list --porcelain 2>/dev/null | /usr/bin/awk '/^worktree /{print substr($0,10)}')
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
  printf '在 worktree 路径继续本任务: 用 Cursor Open Folder 打开 %s 后跑 mmw where（勿依赖 move_agent_to_root）' "$1"
}

# 工人 wt 初始化：项目 hook 优先；否则用本插件内 ensure 脚本按内容复用/重建图谱。
mmw_prepare_worktree() {
  local source_wt="$1" target_wt="$2"
  local hook="$target_wt/.cursor/worktree-init.sh" init_log="" ensure_py="" plugin_root=""

  init_log="$(mktemp "${TMPDIR:-/tmp}/mmw-worktree-init.XXXXXX")" || {
    echo "[mmw] WARNING: 无法创建 worktree 初始化日志:$target_wt" >&2
    return 0
  }
  if [ -f "$hook" ]; then
    if (
      cd "$target_wt"
      /bin/bash "$hook" "$source_wt" "$target_wt"
    ) >"$init_log" 2>&1; then
      [ ! -s "$init_log" ] || cat "$init_log" >&2
    else
      cat "$init_log" >&2
      echo "[mmw] WARNING: 项目 worktree 初始化失败；继续任务:$target_wt" >&2
    fi
    rm -f "$init_log"
    return 0
  fi

  plugin_root="$(mmw_plugin_root)"
  ensure_py="$plugin_root/skills/graphify/scripts/graphify_ensure.py"
  if [ ! -f "$ensure_py" ]; then
    rm -f "$init_log"
    echo "[mmw] WARNING: 找不到插件内 graphify ensure；工作树已创建，首次复杂检索前必须补建图:$target_wt" >&2
    return 0
  fi
  if python3 "$ensure_py" --repo "$target_wt" --source "$source_wt" >"$init_log" 2>&1; then
    [ ! -s "$init_log" ] || cat "$init_log" >&2
  else
    cat "$init_log" >&2
    echo "[mmw] WARNING: 通用图谱初始化失败；工作树已创建，首次复杂检索将重试:$target_wt" >&2
  fi
  rm -f "$init_log"
  return 0
}

mmw_user_agents_dir() {
  printf '%s' "${CURSOR_USER_AGENTS:-$HOME/.cursor/agents}"
}

mmw_user_skills_dir() {
  printf '%s' "${CURSOR_USER_SKILLS:-$HOME/.cursor/skills}"
}

# 引擎根：MMW_ENGINE_ROOT → 默认 ~/.cursor/multi-model-workflow-engine → 脚本上溯（仓内开发）。
# CURSOR_PLUGIN_ROOT 仅当指向含 scripts/mmw.sh 的树时兼容（测试 fixture）。
mmw_plugin_root() {
  local cand
  if [ -n "${MMW_ENGINE_ROOT:-}" ] && [ -f "$MMW_ENGINE_ROOT/scripts/mmw.sh" ]; then
    printf '%s' "$MMW_ENGINE_ROOT"
    return 0
  fi
  cand="${HOME}/.cursor/multi-model-workflow-engine"
  if [ -f "$cand/scripts/mmw.sh" ]; then
    printf '%s' "$cand"
    return 0
  fi
  if [ -n "${CURSOR_PLUGIN_ROOT:-}" ] && [ -f "$CURSOR_PLUGIN_ROOT/scripts/mmw.sh" ]; then
    printf '%s' "$CURSOR_PLUGIN_ROOT"
    return 0
  fi
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

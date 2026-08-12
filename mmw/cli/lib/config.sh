#!/usr/bin/env bash
# 读仓库根的 .mmw.json，以及判定当前宿主。
#
# 这一层不做任何流程判断，只回答两类问题：这个仓库的参数是什么、我们跑在哪个
# 宿主里。判断留给技能，动作留给 adapter。

set -euo pipefail

# 仓库根。CLI 的每条命令都是（仓库，参数）的纯函数，仓库就是这里。
mmw_repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || {
    echo "mmw: 当前目录不在 git 仓库里" >&2
    return 1
  }
}

# Git 共享根。在 linked worktree 里跑时，mmw_repo_root 给当前 checkout；这里通过
# git-common-dir 找到创建这些 worktree 的 Local checkout。共享运行记录落在这里。
mmw_main_root() {
  local common
  common="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || {
    echo "mmw: 当前目录不在 git 仓库里" >&2
    return 1
  }
  dirname "$common"
}

mmw_config_path() {
  echo "$(mmw_repo_root)/.mmw.json"
}

# 配置缺失时立刻报错并给出补救命令，不用默认值兜过去。
mmw_require_config() {
  local path
  path="$(mmw_config_path)"
  if [ ! -f "$path" ]; then
    echo "mmw: 找不到 ${path}，先跑 mmw init" >&2
    return 1
  fi
  echo "$path"
}

# mmw_config <jq 表达式>
mmw_config() {
  local path
  path="$(mmw_require_config)" || return 1
  jq -er "$1" "$path" 2>/dev/null || {
    echo "mmw: .mmw.json 里没有 $1" >&2
    return 1
  }
}

# 当前宿主：claude-code | pi | grok | codex。宿主变量都没有时报错，不猜。
mmw_host() {
  if [ -n "${MMW_HOST:-}" ]; then
    echo "$MMW_HOST"
  elif [ -n "${CLAUDECODE:-}" ]; then
    echo "claude-code"
  elif [ -n "${PI_CODING_AGENT:-}" ]; then
    echo "pi"
  elif [ -n "${GROK_AGENT:-}" ]; then
    echo "grok"
  elif [ -n "${CODEX_THREAD_ID:-}" ]; then
    echo "codex"
  else
    echo "mmw: 认不出当前宿主（Claude Code、Pi、Grok 与 Codex 标识都没有）" >&2
    echo "mmw: 要在别处跑，用 MMW_HOST=claude-code、pi、grok 或 codex 显式指定" >&2
    return 1
  fi
}

# mmw_model_field <角色> <字段>，字段是 family / id / effort。
#
# 模型档属于已安装的 MMW runtime，不属于目标仓库。源码安装流程从
# cli/mmw.default.json 为各宿主物化运行时；目标仓库的 .mmw.json 不保存 models。
mmw_model_field() {
  local role="$1" field="$2" host override
  host="$(mmw_host)" || return 1
  if override="$(jq -er ".models[\"$role\"].hosts[\"$host\"].$field" \
      "$MMW_ROOT/cli/mmw.default.json" 2>/dev/null)"; then
    echo "$override"
    return 0
  fi
  jq -er ".models[\"$role\"].$field" "$MMW_ROOT/cli/mmw.default.json" 2>/dev/null || {
    echo "mmw: 已安装 runtime 的模型档缺少 $role.$field" >&2
    return 1
  }
}

mmw_path_field() {
  mmw_config ".paths[\"$1\"]"
}

# 任务 worktree 相对主仓的目录名；无 .mmw.json 时用默认 .worktrees。
mmw_worktrees_rel() {
  mmw_path_field worktrees 2>/dev/null || echo ".worktrees"
}

# doctor 只验证 installed runtime。需要修复安装时，回到记录下来的源码仓库重装。
mmw_install_repair_command() {
  local marker source_repo
  marker="$MMW_ROOT/../.mmw-source-root"
  if [ -f "$marker" ]; then
    source_repo="$(sed -n '1p' "$marker")"
    if [ -x "$source_repo/mmw/install.sh" ]; then
      printf 'bash %q\n' "$source_repo/mmw/install.sh"
      return 0
    fi
  fi
  echo "bash <MMW源码仓库>/mmw/install.sh"
}

# 可写角色的 cwd：必须是干净的 git 任务 worktree。Codex App 的 managed worktree
# 可以位于全局 Worktree root 下，不受目标仓库 paths.worktrees 约束。
# 成功时把绝对路径打到 stdout；失败非零，绝不把 git 报错当成干净。
mmw_require_writable_cwd() {
  local cwd="${1:-}"
  if [ -z "$cwd" ]; then
    echo "mmw: 可写任务 --cwd 必填，指向任务 worktree" >&2
    return 1
  fi
  if [ ! -d "$cwd" ]; then
    echo "mmw: 工作目录不存在：$cwd" >&2
    return 1
  fi
  cwd="$(cd "$cwd" && pwd -P)" || return 1

  if ! git -C "$cwd" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "mmw: $cwd 不是 git 工作树，可写任务不派" >&2
    return 1
  fi

  mmw_git_clean "$cwd" "可写任务不派" || return 1

  local common main wt_root host git_dir branch
  common="$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || {
    echo "mmw: 无法解析 $cwd 的主仓库" >&2
    return 1
  }
  host="$(mmw_host)" || return 1
  if [ "$host" = "codex" ]; then
    git_dir="$(git -C "$cwd" rev-parse --path-format=absolute --git-dir 2>/dev/null)" || {
      echo "mmw: 无法解析 $cwd 的 worktree 元数据" >&2
      return 1
    }
    if [ "$git_dir" = "$common" ]; then
      echo "mmw: Codex 可写任务必须使用 App 创建的 linked worktree，不是 Local checkout" >&2
      return 1
    fi
    branch="$(git -C "$cwd" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
    case "$branch" in
      codex/*) ;;
      *) echo "mmw: Codex 可写任务必须先绑定 codex/<slug> 分支：$cwd" >&2; return 1 ;;
    esac
    printf '%s\n' "$cwd"
    return 0
  fi
  if [ "$host" = "grok" ]; then
    git_dir="$(git -C "$cwd" rev-parse --path-format=absolute --git-dir 2>/dev/null)" || {
      echo "mmw: 无法解析 $cwd 的 worktree 元数据" >&2
      return 1
    }
    if [ "$git_dir" = "$common" ]; then
      echo "mmw: Grok 可写任务必须使用宿主创建的 linked worktree，不是 Local checkout" >&2
      return 1
    fi
    case "$cwd" in
      "$HOME/.grok/worktrees/"*) ;;
      *)
        echo "mmw: Grok 可写任务的 --cwd 必须在 ${HOME}/.grok/worktrees/ 下，不是 $cwd" >&2
        return 1
        ;;
    esac
    printf '%s\n' "$cwd"
    return 0
  fi

  main="$(cd "$(dirname "$common")" && pwd -P)"
  wt_root="$main/$(mmw_worktrees_rel)"
  case "$cwd" in
    "$wt_root"/*) ;;
    *)
      echo "mmw: 可写任务的 --cwd 必须是任务 worktree（${wt_root}/<slug>），不是 $cwd" >&2
      return 1
      ;;
  esac

  printf '%s\n' "$cwd"
}

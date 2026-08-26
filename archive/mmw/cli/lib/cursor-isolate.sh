#!/usr/bin/env bash
# Cursor CLI 的用户级隔离：挡住 $HOME/.claude 与 $HOME/.codex，让 worker 只看见
# Cursor 自己的用户目录、仓库合同和跨宿主共享技能。
#
# 仓库里的 `.claude/` 与 `CLAUDE.md` 不在这个名单里——它们是项目合同，官方 CLI
# 本来就要读。`$HOME/.agents/skills` 同样要读，那是跨宿主共享技能，不是 MMW 碰撞。
#
# 隔离手段是 macOS sandbox-exec。假 HOME 不够：os.homedir() 会跟着 HOME 走，
# os.userInfo().homedir 仍指向真实家目录。seatbelt 的 subpath 按内核看到的
# 规范路径匹配：/tmp 和 /var/folders 是指向 /private/... 的符号链接，只写
# $HOME/.claude 会让隔离失效。profile 同时写入原路径和 pwd -P 展开后的路径。
# 不要写 file-ioctl*，那条在当前系统上是未绑定变量。

set -euo pipefail

mmw_cursor_agent_real() {
  local candidate resolved
  if [ -n "${MMW_CURSOR_AGENT_REAL:-}" ]; then
    if [ -x "$MMW_CURSOR_AGENT_REAL" ]; then
      printf '%s\n' "$MMW_CURSOR_AGENT_REAL"
      return 0
    fi
    echo "mmw: MMW_CURSOR_AGENT_REAL 不是可执行文件：$MMW_CURSOR_AGENT_REAL" >&2
    return 1
  fi

  candidate="$(command -v cursor-agent 2>/dev/null || true)"
  if [ -n "$candidate" ]; then
    resolved="$(mmw_cursor_resolve_executable "$candidate")" || return 1
    if ! mmw_cursor_is_isolate_wrapper "$resolved"; then
      printf '%s\n' "$resolved"
      return 0
    fi
  fi

  echo "mmw: 找不到真正的 cursor-agent。装 Cursor CLI 之后再跑，或设 MMW_CURSOR_AGENT_REAL" >&2
  return 1
}

mmw_cursor_resolve_executable() {
  local path="$1"
  if [ -L "$path" ]; then
    # macOS 的 readlink 没有 -f。包装命令要的是 symlink 指向的那份二进制。
    local dest
    dest="$(readlink "$path")" || return 1
    case "$dest" in
      /*) printf '%s\n' "$dest" ;;
      *) printf '%s\n' "$(cd "$(dirname "$path")" && pwd)/$dest" ;;
    esac
    return 0
  fi
  printf '%s\n' "$path"
}

mmw_cursor_is_isolate_wrapper() {
  local path="$1"
  grep -q 'Managed by MMW cursor isolate' "$path" 2>/dev/null
}

mmw_cursor_sbpl_quote() {
  printf '"%s"' "$(printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g')"
}

# 目录在就 pwd -P；目录还不在就展开已有的父目录，再接最后一段。
mmw_cursor_canonical_path() {
  local path="$1" parent base
  if [ -d "$path" ]; then
    (cd "$path" && pwd -P)
    return 0
  fi
  parent="$(dirname -- "$path")"
  base="$(basename -- "$path")"
  if [ -d "$parent" ]; then
    parent="$(cd "$parent" && pwd -P)"
    if [ "$parent" = / ]; then
      printf '/%s\n' "$base"
    else
      printf '%s/%s\n' "$parent" "$base"
    fi
    return 0
  fi
  printf '%s\n' "$path"
}

mmw_cursor_seatbelt_add_subpath() {
  local path="$1" quoted
  quoted="$(mmw_cursor_sbpl_quote "$path")"
  case "$MMW_CURSOR_SEATBELT_FILTERS" in
    *" (subpath ${quoted})"*) ;;
    *) MMW_CURSOR_SEATBELT_FILTERS="${MMW_CURSOR_SEATBELT_FILTERS}  (subpath ${quoted})"$'\n' ;;
  esac
}

mmw_cursor_seatbelt_profile() {
  local raw real
  MMW_CURSOR_SEATBELT_FILTERS=""
  for raw in "${HOME}/.claude" "${HOME}/.codex"; do
    mmw_cursor_seatbelt_add_subpath "$raw"
    real="$(mmw_cursor_canonical_path "$raw")"
    mmw_cursor_seatbelt_add_subpath "$real"
  done
  printf '%s\n' '(version 1)' '(allow default)' '(deny file-read* file-write*'
  printf '%s' "$MMW_CURSOR_SEATBELT_FILTERS"
  printf '%s\n' ')'
  unset MMW_CURSOR_SEATBELT_FILTERS
}

mmw_cursor_exec() {
  local real profile
  if [ "$(uname -s)" != "Darwin" ]; then
    echo "mmw: Cursor 隔离包装需要 macOS sandbox-exec" >&2
    return 1
  fi
  real="$(mmw_cursor_agent_real)" || return 1
  profile="$(mmw_cursor_seatbelt_profile)"
  exec sandbox-exec -p "$profile" "$real" "$@"
}

#!/usr/bin/env bash
# 把三个检索工具装进五个宿主各自的用户级配置。
#
# 每个宿主的位置与形状：
#   Claude Code  ~/.claude.json 的 mcpServers（JSON）
#   Codex App    ~/.codex/config.toml 的 [mcp_servers]（TOML）
#   pi           ~/.pi/agent/mcp.json（JSON）
#   Cursor       ~/.cursor/mcp.json（JSON）
#   Grok         ~/.grok/config.toml 的 [mcp_servers]（TOML）
#
# 两种形状，两套合并代码。同一形状的宿主共用一套，不按宿主名分支。
#
# 技能由 mmw-v2/install.sh 装；本脚本只接管这三个检索工具，由那个入口调用。
#
# 服务器定义的唯一事实来源是 mmw-v2/.mcp.json，本脚本只做翻译，不另存一份清单。
# 只读白名单在 Serena 服务器那一侧（config/serena-readonly.yml），在这里再列一遍就是第二处
# 要维护的清单，旧实现四个 harness 各抄一份白名单就是这么散掉的。
#
# 我们不主动写 pi 的 directTools，但也绝不覆盖它已有的那份。directTools 跟白名单是两回事：
# 它把几个高频查询提升成宿主直接工具。整对象替换会把它冲掉，而且冲掉之后工具还在、只是
# 退回成普通 MCP 工具，没有任何人看得见。所以合并一律用递归形式。
#
# 只加不删：用户自己配的别的服务器原样保留，同名的才覆盖成我们这份。
#
# 写进用户配置的绝对路径指向本脚本所在的这个 checkout。所以要从主检出装，不要从任务
# worktree 装——worktree 合并后会删掉，写进去的路径就断了。
#
#   install-mcp.sh          装
#   install-mcp.sh --check       只看 JSON 那三面装没装。装齐回 0，缺东西回 1
#   install-mcp.sh --check-toml  只看 config.toml 那两面（Grok 与 Codex）

set -euo pipefail

MMW_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$MMW_ROOT/.mcp.json"
PI_AGENT_DIR="${PI_CODING_AGENT_DIR:-${PI_HOME:-$HOME/.pi}/agent}"
PI_MCP="${MMW_PI_MCP_FILE:-$PI_AGENT_DIR/mcp.json}"
CURSOR_MCP="${MMW_CURSOR_MCP_FILE:-$HOME/.cursor/mcp.json}"
GROK_CONFIG="${MMW_GROK_CONFIG_FILE:-$HOME/.grok/config.toml}"
CODEX_CONFIG="${MMW_CODEX_CONFIG_FILE:-${CODEX_HOME:-$HOME/.codex}/config.toml}"
CLAUDE_JSON="${MMW_CLAUDE_JSON_FILE:-$HOME/.claude.json}"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  --check-toml) mode=check-toml ;;
  "") ;;
  *) echo "用法: install-mcp.sh [--check|--check-toml]" >&2; exit 2 ;;
esac

[ -f "$SOURCE" ] || { echo "ERROR: 没找到 .mcp.json: $SOURCE" >&2; exit 2; }

# 把 .mcp.json 翻译成某一面要的服务器 map。展开规则（MMW_ROOT、密钥、默认值）全在
# resolve.py 里，本脚本不自己解析占位符——两处解析就是两处维护。
translate() {
  python3 "$MMW_ROOT/mcp/resolve.py" --format "$1"
}

# 服务器 map 在这个文件里放在哪一层。调用方给定形状，auto 表示按文件现状判。
#
# pi 与 Cursor 用 auto：两种形状都有真实来源——pi 的适配器写 {"mcpServers": {...}}，
# 而 Cursor 会把同一个文件规范化成顶层直接放服务器。认错层会写出两套并存的定义。
#
# Claude Code 固定 wrapped，不能猜：~/.claude.json 本来就有 projects、oauthAccount
# 这些顶层键，第一次装（还没有 mcpServers 这个键）会被猜成顶层，于是三台服务器
# 倒在那些键旁边，Claude Code 一台都读不到。
shape_of() {
  local file="$1" declared="${2:-auto}"
  if [ "$declared" != auto ]; then
    echo "$declared"
    return
  fi
  if [ -f "$file" ] && jq -e 'has("mcpServers") | not' "$file" >/dev/null 2>&1; then
    echo top
  else
    echo wrapped
  fi
}

# 读某个面里已经装了什么，输出服务器 map。
current_servers() {
  local file="$1" declared="${2:-auto}"
  if [ "$(shape_of "$file" "$declared")" = top ]; then
    jq '.' "$file"
  else
    jq '.mcpServers // {}' "$file"
  fi
}

# pi 那一面的 env 保留 ${VAR} 不写密钥明文（它的目标文件入库）。展开由宿主在启动服务器
# 时做，取的是宿主进程的环境。值只写在密钥文件里宿主看不到，那时它展成空串，
# 服务器把空 key 当成配错，而配置文件看上去是对的。这一步把那种失败当场说出来。
warn_unreachable_placeholders() {
  local label="$1" file="$2" names name
  names="$(current_servers "$file" "${3:-auto}" \
    | jq -r '.[] | (.env // {}) | .[]' \
    | { grep -o '\${[A-Za-z_][A-Za-z0-9_]*}' || true; } \
    | tr -d '${}' | sort -u)"
  for name in $names; do
    [ -z "${!name:-}" ] || continue
    echo "注意  ${label} 的 ${name} 不在进程环境里，宿主启动服务器时会把它展成空串；在 shell 启动文件里导出它" >&2
  done
}

check_face() {
  local label="$1" file="$2" declared="${3:-auto}"
  local wanted names rc=0
  # 展开失败必须当场停：翻译不出来时 wanted 是空的，后面的 jq 会把它当空 map，
  # 于是「什么都没装」看起来跟「装好了」一模一样。
  wanted="$(translate "$label")" || { echo "ERROR: 展开 .mcp.json 失败" >&2; return 2; }
  [ -n "$wanted" ] || { echo "ERROR: 展开 .mcp.json 得到空结果" >&2; return 2; }
  names="$(printf '%s' "$wanted" | jq -r 'keys[]')"

  if [ ! -d "$(dirname "$file")" ] && [ ! -e "$file" ]; then
    echo "跳过  这台机器没有 ${label}（$(dirname "$file") 不在）"
    return 0
  fi
  if [ ! -f "$file" ]; then
    echo "未装  $label 的 $file 不存在" >&2
    return 1
  fi

  local have
  have="$(current_servers "$file" "$declared")"
  warn_unreachable_placeholders "$label" "$file" "$declared"
  for n in $names; do
    # 只断我们定义的那些字段，不断整个对象相等：目标那一侧可能有宿主自己的字段
    # （pi 的 directTools 就是），断相等会把「它多了个我们不管的字段」误判成未装，
    # 于是每次都重写一遍。合并后没有变化，就说明我们要的都已经在了。
    if [ "$(jq -n --arg n "$n" --argjson h "$have" --argjson w "$wanted" \
        '(($h[$n] // {}) * $w[$n]) == ($h[$n] // {})')" = true ]; then
      echo "已装  $label $n"
    else
      echo "未装  $label ${n}（或与 MMW 当前定义不一致）" >&2
      rc=1
    fi
  done
  return "$rc"
}

install_face() {
  local label="$1" file="$2" declared="${3:-auto}"
  local wanted names dir
  wanted="$(translate "$label")" || { echo "ERROR: 展开 .mcp.json 失败" >&2; return 2; }
  [ -n "$wanted" ] || { echo "ERROR: 展开 .mcp.json 得到空结果" >&2; return 2; }
  names="$(printf '%s' "$wanted" | jq -r 'keys[]')"
  dir="$(dirname "$file")"

  # 这台机器压根没有这个面就不要凭空造出一个配置目录来。跳过是正确结果，不是失败。
  if [ ! -d "$dir" ] && [ ! -e "$file" ]; then
    echo "跳过  这台机器没有 ${label}（${dir} 不在）"
    return 0
  fi

  mkdir -p "$dir"
  [ -f "$file" ] || printf '{"mcpServers":{}}\n' > "$file"
  jq -e . "$file" >/dev/null 2>&1 || {
    echo "ERROR: $label 的 $file 不是合法 JSON，先处理它再装" >&2
    return 2
  }

  local shape tmp
  shape="$(shape_of "$file" "$declared")"
  # 原子写：先写同目录临时文件、验合法、再替换。中途失败保留原文件。
  tmp="$(mktemp "$dir/.mcpXXXXXX")"
  # 递归合并而不是整对象替换：宿主自己在服务器对象里加的字段要留着。pi 的
  # directTools 把四个查询提升成直接工具，那是宿主侧的能力，被我们覆盖掉的话
  # 它会安静地退回成普通 MCP 工具，没有任何人看得见。
  if [ "$shape" = top ]; then
    jq --argjson w "$wanted" '. * $w' "$file" > "$tmp"
  else
    jq --argjson w "$wanted" '.mcpServers = ((.mcpServers // {}) * $w)' "$file" > "$tmp"
  fi
  if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
    rm -f "$tmp"
    echo "ERROR: 拒绝写入空或非法 JSON，$file 保留原样" >&2
    return 1
  fi
  mv "$tmp" "$file"

  warn_unreachable_placeholders "$label" "$file" "$declared"
  for n in $names; do echo "装好  $label $n → $file"; done
}

# TOML 那一面：Grok 与 Codex 的 config.toml 是同一种形状，同一段代码两个宿主。
check_toml_face() {
  local label="$1" config="$2"
  if [ ! -d "$(dirname "$config")" ] && [ ! -e "$config" ]; then
    echo "跳过  这台机器没有 ${label}（$(dirname "$config") 不在）"
    return 0
  fi
  if python3 - "$config" "$MMW_ROOT" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[2] + "/mcp")
import resolve as r
servers = r.Resolver().servers(want_type=False, keep_env_placeholders=False)
sys.exit(0 if r.toml_config_has_servers(Path(sys.argv[1]), servers) else 1)
PY
  then
    echo "已装  $label 三台检索服务器 → $config"
    return 0
  fi
  echo "未装  $label 的 $config 缺三台检索服务器（或与当前定义不一致）" >&2
  return 1
}

install_toml_face() {
  local label="$1" config="$2"
  if [ ! -d "$(dirname "$config")" ] && [ ! -e "$config" ]; then
    echo "跳过  这台机器没有 ${label}（$(dirname "$config") 不在）"
    return 0
  fi
  python3 "$MMW_ROOT/mcp/resolve.py" --merge-toml "$config" || return 2
  echo "装好  $label serena/graphify/context7 → $config"
}

rc=0
if [ "$mode" = check ]; then
  check_face pi "$PI_MCP" || rc=1
  check_face cursor "$CURSOR_MCP" || rc=1
  check_face claude "$CLAUDE_JSON" wrapped || rc=1
elif [ "$mode" = check-toml ]; then
  check_toml_face grok "$GROK_CONFIG" || rc=1
  check_toml_face codex "$CODEX_CONFIG" || rc=1
else
  install_face pi "$PI_MCP" || rc=$?
  install_face cursor "$CURSOR_MCP" || rc=$?
  install_face claude "$CLAUDE_JSON" wrapped || rc=$?
  install_toml_face grok "$GROK_CONFIG" || rc=$?
  install_toml_face codex "$CODEX_CONFIG" || rc=$?
fi
exit "$rc"

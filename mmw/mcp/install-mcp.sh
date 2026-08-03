#!/usr/bin/env bash
# 把三个检索工具装进那些「宿主规格里没有声明 MCP 位置」的执行面。
#
# 四个执行面各自怎么拿到这三个工具：
#   Claude Code  插件根的 .mcp.json 自动生效，什么都不用做
#   Codex        mmw dispatch 派发时用 -c 注入，退出即无痕，什么都不用做。
#                不往 ~/.codex/config.toml 写：那份配置是用户自己的，而且它是 TOML，
#                里面还有别的程序（比如 ChatGPT.app）在维护的段落，我们去改会破坏
#                它的格式、注释和顺序
#   pi           package.json 的 pi 字段只收 extensions / skills / prompts，扩展接口
#                也没有注册 MCP 的能力，所以只能写用户级的 ~/.pi/agent/mcp.json
#   Cursor       它的插件规格同样没有 MCP 的位置，只能写用户级的 ~/.cursor/mcp.json。
#                mmw 只接管它这三个检索工具，不往 Cursor 装技能和花名册——那两样是
#                编排流程的一部分，Cursor 不是 mmw 的宿主
#
# 服务器定义的唯一事实来源是插件根的 .mcp.json，本脚本只做翻译，不另存一份清单。
# 只读白名单在 Serena 服务器那一侧（config/serena-readonly.yml），在这里再列一遍就是第二处
# 要维护的清单，旧实现四个 harness 各抄一份白名单就是这么散掉的。
#
# 我们不主动写 pi 的 directTools，但也绝不覆盖它已有的那份。directTools 跟白名单是两回事：
# 它把几个高频查询提升成宿主直接工具。整对象替换会把它冲掉，而且冲掉之后工具还在、只是
# 退回成普通 MCP 工具，没有任何人看得见。所以合并一律用递归形式。
#
# 只加不删：用户自己配的别的服务器原样保留，同名的才覆盖成我们这份。
#
# 已知边界（跟 install-agent-skills.sh 同一条）：写进去的是绝对路径，指向脚本跑起来时
# 所在的那棵树。在任务 worktree 里跑，worktree 删掉后那一面就断了。正式安装从主仓库跑。
#
#   install-mcp.sh          装
#   install-mcp.sh --check  只看装没装。装齐回 0，缺东西回 1

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$PLUGIN_ROOT/.mcp.json"
PI_MCP="${MMW_PI_MCP_FILE:-${PI_HOME:-$HOME/.pi}/agent/mcp.json}"
CURSOR_MCP="${MMW_CURSOR_MCP_FILE:-$HOME/.cursor/mcp.json}"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-mcp.sh [--check]" >&2; exit 2 ;;
esac

[ -f "$SOURCE" ] || { echo "ERROR: 插件里没有 .mcp.json: $SOURCE" >&2; exit 2; }

# 把 .mcp.json 翻译成某一面要的服务器 map。展开规则（插件根、密钥、默认值）全在
# resolve.py 里，本脚本不自己解析占位符——两处解析就是两处维护。
translate() {
  python3 "$PLUGIN_ROOT/mcp/resolve.py" --format "$1"
}

# 服务器 map 在这个文件里放在哪一层。两种形状都有真实来源：pi 的适配器写
# {"mcpServers": {...}}，而 Cursor 会把同一个文件规范化成顶层直接放服务器。
# 认错层会写出两套并存的定义，所以按文件现状判，不按我们的偏好写。
# 文件不存在时用 mcpServers——两个面都认它。
shape_of() {
  local file="$1"
  if [ -f "$file" ] && jq -e 'has("mcpServers") | not' "$file" >/dev/null 2>&1; then
    echo top
  else
    echo wrapped
  fi
}

# 读某个面里已经装了什么，输出服务器 map。
current_servers() {
  local file="$1"
  if [ "$(shape_of "$file")" = top ]; then
    jq '.' "$file"
  else
    jq '.mcpServers // {}' "$file"
  fi
}

check_face() {
  local label="$1" file="$2"
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
  have="$(current_servers "$file")"
  for n in $names; do
    # 只断我们定义的那些字段，不断整个对象相等：目标那一侧可能有宿主自己的字段
    # （pi 的 directTools 就是），断相等会把「它多了个我们不管的字段」误判成未装，
    # 于是每次都重写一遍。合并后没有变化，就说明我们要的都已经在了。
    if [ "$(jq -n --arg n "$n" --argjson h "$have" --argjson w "$wanted" \
        '(($h[$n] // {}) * $w[$n]) == ($h[$n] // {})')" = true ]; then
      echo "已装  $label $n"
    else
      echo "未装  $label ${n}（或与插件当前定义不一致）" >&2
      rc=1
    fi
  done
  return "$rc"
}

install_face() {
  local label="$1" file="$2"
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
  shape="$(shape_of "$file")"
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

  for n in $names; do echo "装好  $label $n → $file"; done
}

rc=0
if [ "$mode" = check ]; then
  check_face pi "$PI_MCP" || rc=1
  check_face cursor "$CURSOR_MCP" || rc=1
else
  install_face pi "$PI_MCP" || rc=$?
  install_face cursor "$CURSOR_MCP" || rc=$?
fi
exit "$rc"

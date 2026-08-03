#!/usr/bin/env bash
# 把三个检索工具装进 pi 的 MCP 配置。
#
# 三个执行面里只有 pi 需要这一步：
#   Claude Code  插件根的 .mcp.json 自动生效，什么都不用做
#   Codex        mmw dispatch 派发时用 -c 注入，退出即无痕，什么都不用做
#   pi           它的插件规格里没有声明 MCP 的位置（package.json 的 pi 字段只收
#                extensions / skills / prompts，扩展接口也没有注册 MCP 的能力），
#                所以只能写用户级的 ~/.pi/agent/mcp.json
#
# 服务器定义的唯一事实来源是插件根的 .mcp.json，本脚本只做翻译，不另存一份清单。
# 不写 pi 的 directTools：只读白名单已经在 Serena 服务器那一侧（config/serena-readonly.yml），
# 在这里再列一遍就是第二处要维护的清单，旧实现四个 harness 各抄一份白名单就是这么散掉的。
#
# 只加不删：用户自己配的别的服务器原样保留，同名的才覆盖成我们这份。
#
# 已知边界（跟 install-agent-skills.sh 同一条）：写进 pi 配置的是绝对路径，指向
# 脚本跑起来时所在的那棵树。在任务 worktree 里跑，worktree 删掉后 pi 那侧就断了。
# 正式安装从主仓库跑。
#
#   install-mcp.sh          装
#   install-mcp.sh --check  只看装没装。装齐回 0，缺东西回 1

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$PLUGIN_ROOT/.mcp.json"
PI_MCP="${MMW_PI_MCP_FILE:-${PI_HOME:-$HOME/.pi}/agent/mcp.json}"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *) echo "用法: install-mcp.sh [--check]" >&2; exit 2 ;;
esac

[ -f "$SOURCE" ] || { echo "ERROR: 插件里没有 .mcp.json: $SOURCE" >&2; exit 2; }

# 这台机器压根没有 pi 就不要凭空造出一个配置目录来。Claude Code 与 Codex 两侧本来
# 就不经过这里，跳过是正确结果，不是失败。
if [ ! -d "$(dirname "$PI_MCP")" ] && [ ! -e "$PI_MCP" ]; then
  echo "跳过  这台机器没有 pi（$(dirname "$PI_MCP") 不在），Claude Code 与 Codex 两侧不需要这一步"
  exit 0
fi

# 把 .mcp.json 翻译成 pi 认的形状：展开 ${CLAUDE_PLUGIN_ROOT}，补 type: stdio。
wanted="$(jq --arg root "$PLUGIN_ROOT" '
  def expand: gsub("\\$\\{CLAUDE_PLUGIN_ROOT\\}"; $root);
  .mcpServers | map_values(
    {type: "stdio", command: (.command | expand)}
    + (if (.args // []) | length > 0 then {args: [.args[] | expand]} else {} end)
    + (if (.env // {}) | length > 0 then {env: (.env | map_values(expand))} else {} end)
  )
' "$SOURCE")"

names="$(printf '%s' "$wanted" | jq -r 'keys[]')"

if [ "$mode" = check ]; then
  [ -f "$PI_MCP" ] || { echo "未装  pi 的 $PI_MCP 不存在" >&2; exit 1; }
  rc=0
  for n in $names; do
    if [ "$(jq --arg n "$n" --argjson w "$wanted" '.mcpServers[$n] == $w[$n]' "$PI_MCP" 2>/dev/null)" = "true" ]; then
      echo "已装  $n"
    else
      echo "未装  $n（或与插件当前定义不一致）" >&2
      rc=1
    fi
  done
  exit "$rc"
fi

mkdir -p "$(dirname "$PI_MCP")"
[ -f "$PI_MCP" ] || printf '{"mcpServers":{}}\n' > "$PI_MCP"
jq -e . "$PI_MCP" >/dev/null 2>&1 || {
  echo "ERROR: pi 的 $PI_MCP 不是合法 JSON，先处理它再装" >&2
  exit 2
}

# 原子写：先写同目录临时文件、验合法、再替换。中途失败保留原文件。
tmp="$(mktemp "$(dirname "$PI_MCP")/.mcpXXXXXX")"
jq --argjson w "$wanted" '.mcpServers = ((.mcpServers // {}) + $w)' "$PI_MCP" > "$tmp"
if [ ! -s "$tmp" ] || ! jq -e . "$tmp" >/dev/null 2>&1; then
  rm -f "$tmp"
  echo "ERROR: 拒绝写入空或非法 JSON，$PI_MCP 保留原样" >&2
  exit 1
fi
mv "$tmp" "$PI_MCP"

for n in $names; do echo "装好  $n → $PI_MCP"; done

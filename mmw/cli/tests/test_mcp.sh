#!/usr/bin/env bash
# 三个检索工具的接入。每条守的东西写在它自己那行前面。
#
# 不测的：不断言 .mcp.json 的文本内容，也不断言 doctor 的输出长什么样——那是锁实现
# 不是守行为。这里只断外部可观察的事实：服务器协议输出、codex 认不认、装出来的配置。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW_ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
check() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       想要：$want" >&2
    echo "       得到：$got" >&2
    fail=$((fail + 1))
  fi
}

# 守：派出去写代码的 agent 不能拿检索工具当后门。上游默认还暴露任意命令执行、覆写
# 文件、在符号前后插代码、重命名与删除符号，以及一套往仓库落文件的记忆系统；这份
# 白名单一旦失效，五个 GPT 角色立刻全都拿得到。
echo "Serena 只读白名单"
if command -v serena >/dev/null 2>&1; then
  got="$(python3 "$MMW_ROOT/mcp/probe.py" --json 2>/dev/null \
    | jq -r '.serena.detail // "探测失败"' \
    | sed 's/^[0-9]* 个工具：//')"
  check "服务器只注册四个只读工具" \
    "find_implementations, find_referencing_symbols, find_symbol, get_symbols_overview" \
    "$got"
else
  echo "  跳过 这台机器没装 serena（uv tool install serena-agent）"
fi

# 守：图过期时给出的是历史事实，而它不会告诉你它过期了。官方入口假定图已存在、不
# 检查新鲜度，还多带三个查 GitHub PR 的工具跟我们的 issue 约定打架。
echo
echo "Graphify 包装器"
if command -v graphify >/dev/null 2>&1; then
  got="$(python3 "$MMW_ROOT/mcp/probe.py" --json 2>/dev/null | jq -r '.graphify.detail // "探测失败"')"
  check "收成一个工具，不是官方那十个" "1 个工具：graphify" "$got"
else
  echo "  跳过 这台机器没装 graphify（uv tool install graphifyy）"
fi

# 守：五个 GPT 角色（写码、写计划、调查、GPT 审查）真的拿得到工具。它们走 codex
# 外部进程，而 codex 的 MCP 配置没有任何工具过滤字段——这条断的是注入本身成不成立。
echo
echo "Codex 侧注入"
if command -v codex >/dev/null 2>&1; then
  overrides=()
  while IFS= read -r line; do
    [ -n "$line" ] && overrides+=(-c "$line")
  done < <(MMW_ROOT="$MMW_ROOT" bash -c '. "$MMW_ROOT/cli/adapters/claude-code.sh"; mmw_adapter_mcp_overrides')
  listed="$(codex mcp list ${overrides[@]+"${overrides[@]}"} 2>/dev/null \
    | awk '/^(serena|graphify|context7)[[:space:]]/ {print $1}' | sort | paste -sd, -)"
  check "三个服务器都被 codex 认下" "context7,graphify,serena" "$listed"
else
  echo "  跳过 这台机器没装 codex"
fi

# 守：改一处三边都变。旧实现四个 harness 各写一套，结果 Graphify 的接法在两份里
# 是矛盾的、白名单抄了三份还各不相同——这条盯住的就是那个病根。
echo
echo ".mcp.json 是唯一事实来源"
FAKE_ROOT="$WORK/fake-plugin"
mkdir -p "$FAKE_ROOT/cli/adapters" "$FAKE_ROOT/mcp"
cp "$MMW_ROOT/cli/adapters/claude-code.sh" "$FAKE_ROOT/cli/adapters/"
cp "$MMW_ROOT/mcp/install-mcp.sh" "$FAKE_ROOT/mcp/"
cat > "$FAKE_ROOT/.mcp.json" <<'JSON'
{"mcpServers":{"新加的":{"command":"some-tool","args":["--root","${CLAUDE_PLUGIN_ROOT}/x"]}}}
JSON
got="$(MMW_ROOT="$FAKE_ROOT" bash -c '. "$MMW_ROOT/cli/adapters/claude-code.sh"; mmw_adapter_mcp_overrides' \
  | grep -c '新加的' || true)"
check "往 .mcp.json 加一个，codex 覆盖项跟着有" "2" "$got"
MMW_PI_MCP_FILE="$WORK/pi-mcp.json" bash "$FAKE_ROOT/mcp/install-mcp.sh" >/dev/null
check "同一个也进了 pi 的配置" "some-tool" \
  "$(jq -r '.mcpServers["新加的"].command' "$WORK/pi-mcp.json")"
check "插件根路径被展开成绝对路径" "$FAKE_ROOT/x" \
  "$(jq -r '.mcpServers["新加的"].args[1]' "$WORK/pi-mcp.json")"

# 守：用户自己配的 MCP 不能被我们的安装抹掉。
echo
echo "装 pi 的配置只加不删"
cat > "$WORK/pi-existing.json" <<'JSON'
{"mcpServers":{"用户自己的":{"type":"stdio","command":"his-tool"}}}
JSON
MMW_PI_MCP_FILE="$WORK/pi-existing.json" bash "$FAKE_ROOT/mcp/install-mcp.sh" >/dev/null
check "别人的服务器还在" "his-tool" \
  "$(jq -r '.mcpServers["用户自己的"].command' "$WORK/pi-existing.json")"

# 守：doctor 不能在服务器坏掉时报绿。旧实现出过这个事故——配置在、工具名在列表里、
# 直到模型真去调用才报错，而那时它已经在一次审查中途了。
echo
echo "探测发现起不来的服务器"
BROKEN="$WORK/broken-plugin"
mkdir -p "$BROKEN/mcp"
cp "$MMW_ROOT/mcp/probe.py" "$BROKEN/mcp/"
cat > "$BROKEN/.mcp.json" <<'JSON'
{"mcpServers":{"起不来的":{"command":"这个命令根本不存在"}}}
JSON
if out="$(python3 "$BROKEN/mcp/probe.py" 2>&1)"; then
  check "命令不存在时探测应退非零" "退非零" "退 0：$out"
else
  check "命令不存在时探测退非零并指名道姓" "起不来的" \
    "$(printf '%s' "$out" | grep -o '起不来的' | head -1)"
fi

echo
echo "过 $pass / 失败 $fail"
[ "$fail" -eq 0 ]

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
cp "$MMW_ROOT/mcp/install-mcp.sh" "$MMW_ROOT/mcp/resolve.py" "$FAKE_ROOT/mcp/"
cat > "$FAKE_ROOT/.mcp.json" <<'JSON'
{"mcpServers":{"新加的":{"command":"some-tool","args":["--root","${CLAUDE_PLUGIN_ROOT}/x"],
 "env":{"要密钥的":"${MMW_TEST_SECRET:-}","不要密钥的":"固定值"}}}}
JSON
# 密钥文件指到临时目录：读用户真实的那份，这几条断言就随他机器上配没配而变。
export MMW_SECRETS_FILE="$WORK/secrets.env"
printf 'MMW_TEST_SECRET=真值\n' > "$MMW_SECRETS_FILE"
# 两个面都指到临时文件。少指一个，测试会写到跑测试那个人真实的配置上。
fake_install() { MMW_PI_MCP_FILE="$1" MMW_CURSOR_MCP_FILE="$2" bash "$FAKE_ROOT/mcp/install-mcp.sh"; }

got="$(MMW_ROOT="$FAKE_ROOT" bash -c '. "$MMW_ROOT/cli/adapters/claude-code.sh"; mmw_adapter_mcp_overrides' \
  | grep -c '新加的' || true)"
check "往 .mcp.json 加一个，codex 覆盖项跟着有" "3" "$got"
fake_install "$WORK/pi-mcp.json" "$WORK/cursor-mcp.json" >/dev/null
check "同一个也进了 pi 的配置" "some-tool" \
  "$(jq -r '.mcpServers["新加的"].command' "$WORK/pi-mcp.json")"
check "同一个也进了 Cursor 的配置" "some-tool" \
  "$(jq -r '.mcpServers["新加的"].command' "$WORK/cursor-mcp.json")"
# 期望值走一遍 pwd -P：展开出去的必须是解析过 symlink 的真路径（macOS 的
# /var 就是 /private/var 的 symlink），下游进程按它去找文件。
check "插件根路径被展开成解析过的绝对路径" "$(cd "$FAKE_ROOT" && pwd -P)/x" \
  "$(jq -r '.mcpServers["新加的"].args[1]' "$WORK/pi-mcp.json")"
# 守：pi 认 type: stdio，Cursor 不认。同一份定义要按面翻译，不是一份到处抄。
check "pi 那一面带 type" "stdio" "$(jq -r '.mcpServers["新加的"].type' "$WORK/pi-mcp.json")"
check "Cursor 那一面不带 type" "null" "$(jq -r '.mcpServers["新加的"].type' "$WORK/cursor-mcp.json")"

# 守：密钥不进仓库。.mcp.json 里只写 ${…} 声明，值住在机器上那份密钥文件里；
# 没配的时候要的是「这个键不存在」，不是一个空字符串——下游拿到空串会当成配错了。
# pi 那一面多一道：它的目标文件 ~/.pi/agent/mcp.json 入库，写进去的密钥下一次
# git add 就跟着进仓库，所以只写 pi 自己认的 ${VAR}。Cursor 的配置不在任何仓库里。
echo
echo "密钥从密钥文件展开"
check "pi 那一面只写占位符，不写真值" '${MMW_TEST_SECRET}' \
  "$(jq -r '.mcpServers["新加的"].env["要密钥的"]' "$WORK/pi-mcp.json")"
check "Cursor 那一面展开成真值" "真值" \
  "$(jq -r '.mcpServers["新加的"].env["要密钥的"]' "$WORK/cursor-mcp.json")"
check "不带占位符的原样保留" "固定值" \
  "$(jq -r '.mcpServers["新加的"].env["不要密钥的"]' "$WORK/pi-mcp.json")"
# 守：占位符留在 pi 的配置里、值却只写在密钥文件时，Pi 启动服务器取不到，会把它
# 展成空串。配置文件看上去完全正常，所以这件事只能在安装时说出来。
check "值只在密钥文件时安装会报出来" "1" \
  "$(fake_install "$WORK/pi-warn.json" "$WORK/cursor-warn.json" 2>&1 >/dev/null | grep -c 'MMW_TEST_SECRET' || true)"
check "值已经在进程环境里就不报" "0" \
  "$(MMW_TEST_SECRET=真值 fake_install "$WORK/pi-env.json" "$WORK/cursor-env.json" 2>&1 >/dev/null | grep -c 'MMW_TEST_SECRET' || true)"
: > "$MMW_SECRETS_FILE"
fake_install "$WORK/pi-nokey.json" "$WORK/cursor-nokey.json" >/dev/null
check "没配就把那个键丢掉，不写空串" "null" \
  "$(jq -r '.mcpServers["新加的"].env["要密钥的"]' "$WORK/pi-nokey.json")"
check "同一个 env 里没占位符的键不受牵连" "固定值" \
  "$(jq -r '.mcpServers["新加的"].env["不要密钥的"]' "$WORK/pi-nokey.json")"
printf 'MMW_TEST_SECRET=真值\n' > "$MMW_SECRETS_FILE"

# 守：用户自己配的 MCP 不能被我们的安装抹掉。
echo
echo "只加不删"
cat > "$WORK/pi-existing.json" <<'JSON'
{"mcpServers":{"用户自己的":{"type":"stdio","command":"his-tool"}}}
JSON
# Cursor 会把这个文件规范化成顶层直接放服务器。认错层就会写出两套并存的定义。
cat > "$WORK/cursor-existing.json" <<'JSON'
{"用户自己的":{"command":"his-tool"}}
JSON
fake_install "$WORK/pi-existing.json" "$WORK/cursor-existing.json" >/dev/null
check "pi 那边别人的服务器还在" "his-tool" \
  "$(jq -r '.mcpServers["用户自己的"].command' "$WORK/pi-existing.json")"
check "Cursor 那边别人的服务器还在" "his-tool" \
  "$(jq -r '.["用户自己的"].command' "$WORK/cursor-existing.json")"
check "顶层形状的文件不会被塞进第二层" "some-tool" \
  "$(jq -r '.["新加的"].command' "$WORK/cursor-existing.json")"
check "也没有多长出一个 mcpServers" "null" \
  "$(jq -r '.mcpServers // "null"' "$WORK/cursor-existing.json")"

# 守：脚本在任何 locale 下都要跑得动。派出去的 headless 进程、CI、cron 继承的
# locale 都不受控，而 bash 在非 UTF-8 locale 下按单字节切词——`$label（` 这种写法
# 会把中文全角括号的首字节当成变量名读下去，报「line 114: label」这类看不懂的错。
# 两支都要跑到：真装那一支和目标目录不在时跳过那一支，报错的原本只在后者。
echo
echo "非 UTF-8 locale 下也能跑"
LC_ALL=C LANG=C fake_install "$WORK/c-pi.json" "$WORK/c-cursor.json" > "$WORK/c-install" 2>&1 || true
check "LC_ALL=C 装出来的内容跟平时一样" "some-tool" \
  "$(jq -r '.mcpServers["新加的"].command' "$WORK/c-pi.json" 2>/dev/null)"
LC_ALL=C LANG=C fake_install "$WORK/没有这个目录/mcp.json" "$WORK/也没有这个/mcp.json" \
  > "$WORK/c-skip" 2>&1 || true
check "LC_ALL=C 走跳过那一支不报 bash 错" "0" "$(grep -c 'line [0-9]*:' "$WORK/c-skip")"

# 守：doctor 不能在服务器坏掉时报绿。旧实现出过这个事故——配置在、工具名在列表里、
# 直到模型真去调用才报错，而那时它已经在一次审查中途了。
echo
echo "探测发现起不来的服务器"
BROKEN="$WORK/broken-plugin"
mkdir -p "$BROKEN/mcp"
cp "$MMW_ROOT/mcp/probe.py" "$MMW_ROOT/mcp/resolve.py" "$BROKEN/mcp/"
cat > "$BROKEN/.mcp.json" <<'JSON'
{"mcpServers":{"起不来的":{"command":"这个命令根本不存在"}}}
JSON
if out="$(python3 "$BROKEN/mcp/probe.py" 2>&1)"; then
  check "命令不存在时探测应退非零" "退非零" "退 0：$out"
else
  check "命令不存在时探测退非零并指名道姓" "起不来的" \
    "$(printf '%s' "$out" | grep -o '起不来的' | head -1)"
fi
# 守：护栏没检查跟护栏检查通过是两回事。这棵临时插件树里没有 config/，正好用来
# 断言合同读不出来时它会说出来，而不是安静地跳过检查。
check "合同读不出来时说出来" 1 \
  "$(printf '%s' "$out" | grep -c '没做护栏检查')"

# 守：裁剪合同必须真的会红。上游哪天默认多暴露一个工具，五个派出去的角色立刻都
# 拿得到——这一条要在体检里当场可见，而不是等某个角色真调用到它。
echo
echo "工具集合跟裁剪合同对不上"
DRIFT="$WORK/drift-plugin"
mkdir -p "$DRIFT/mcp" "$DRIFT/config"
cp "$MMW_ROOT/mcp/probe.py" "$MMW_ROOT/mcp/resolve.py" "$DRIFT/mcp/"
# 最小的假服务器：握手之后回两个工具，够用来验合同比对，不用真起上游那两个。
cat > "$DRIFT/fake-server.py" <<'PY'
import json, sys
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    msg = json.loads(line)
    if msg.get("id") == 1:
        print(json.dumps({"jsonrpc": "2.0", "id": 1, "result": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "serverInfo": {"name": "fake", "version": "0"}}}), flush=True)
    elif msg.get("id") == 2:
        print(json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": [
            {"name": "该有的"}, {"name": "不该有的"}]}}), flush=True)
        break
PY
cat > "$DRIFT/.mcp.json" <<JSON
{"mcpServers":{"假的":{"command":"python3","args":["$DRIFT/fake-server.py"]}}}
JSON
cat > "$DRIFT/config/retrieval-contract.json" <<'JSON'
{"servers":{"假的":{"exact_tools":["该有的"]}}}
JSON
if out="$(python3 "$DRIFT/mcp/probe.py" 2>&1)"; then
  check "多出一个工具时应退非零" "退非零" "退 0：$out"
else
  check "多出一个工具时指名道姓" "多了 不该有的" \
    "$(printf '%s' "$out" | grep -o '多了 不该有的' | head -1)"
fi

# Codex 不读 MCP 握手交回的服务器说明，所以派 GPT 时纪律要拼进提示词。这几条守的是
# 那段拼得出来、内容对得上两处唯一事实来源、以及来源坏掉时当场失败而不是静默少一段。
discipline="$(python3 "$MMW_ROOT/mcp/discipline.py")" \
  && check "纪律拼得出来" "退 0" "退 0" \
  || check "纪律拼得出来" "退 0" "退非零"
check "纪律里有 Serena 那一段" "有" \
  "$(printf '%s' "$discipline" | grep -q 'find_referencing_symbols' && echo 有 || echo 没有)"
check "纪律里有 Graphify 那一段" "有" \
  "$(printf '%s' "$discipline" | grep -q 'reverse impact' && echo 有 || echo 没有)"
check "纪律讲了两类静态分析看不见的关系" "有" \
  "$(printf '%s' "$discipline" | grep -q 'registered by a decorator' && echo 有 || echo 没有)"
check "纪律讲了候选必须回源码验证" "有" \
  "$(printf '%s' "$discipline" | grep -qi 'verify every candidate' && echo 有 || echo 没有)"

# 来源坏掉：prompt 块被改名，取不出来必须非零退出。静默少一段的话，工人手里有工具、
# 没有说明书，而派发看起来是成功的。
BROKEN_D="$WORK/broken-discipline"
mkdir -p "$BROKEN_D/mcp" "$BROKEN_D/config"
cp "$MMW_ROOT/mcp/discipline.py" "$BROKEN_D/mcp/"
cp "$MMW_ROOT/mcp/graphify_mcp.py" "$BROKEN_D/mcp/"
sed 's/^prompt: |$/promptx: |/' "$MMW_ROOT/config/serena-readonly.yml" \
  > "$BROKEN_D/config/serena-readonly.yml"
if python3 "$BROKEN_D/mcp/discipline.py" >/dev/null 2>&1; then
  check "prompt 块缺失时退非零" "退非零" "退 0"
else
  check "prompt 块缺失时退非零" "退非零" "退非零"
fi

echo
echo "过 $pass / 失败 $fail"
[ "$fail" -eq 0 ]

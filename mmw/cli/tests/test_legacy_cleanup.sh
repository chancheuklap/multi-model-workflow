#!/usr/bin/env bash
# install.sh 摘除上一版插件时对 ~/.codex/config.toml 做的那段清理。
#
# 只验这一段，不验两条 plugin 命令：那两条要真的 claude/codex CLI，而且它们的
# 幂等性归宿主。这里验的是我们自己写的正则会不会削到别人的东西——它直接改用户
# 的 config.toml，削错一个区块就是把别人的配置弄丢。

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL="$HERE/../../install.sh"
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

# 只把这一个函数取出来跑。整个 install.sh 会动这台真机器。
sed -n '/^remove_legacy_codex_hook_state() {/,/^}/p' "$INSTALL" > "$WORK/fn.sh"
[ -s "$WORK/fn.sh" ] || { echo "取不到 remove_legacy_codex_hook_state" >&2; exit 1; }
# shellcheck source=/dev/null
. "$WORK/fn.sh"

export CODEX_HOME="$WORK/codex"
mkdir -p "$CODEX_HOME"
config="$CODEX_HOME/config.toml"

echo "config.toml 里有 mmw 的旧信任记录"
cat > "$config" <<'TOML'
model = "gpt-5.6"

[hooks.state."mmw@mmw-codex:hooks.json:post_tool_use:0:0"]
trusted_hash = "sha256:dead"
enabled = true

[hooks.state."别人的插件:hooks.json:post_tool_use:0:0"]
trusted_hash = "sha256:cafe"

[mcp_servers.serena]
command = "serena"
TOML
out="$(remove_legacy_codex_hook_state 2>&1)"
check "报出清掉几条" 1 "$(printf '%s' "$out" | grep -c '清掉 1 条' || true)"
check "mmw 那条没了" 0 "$(grep -c 'mmw@mmw-codex' "$config" || true)"
check "别人那条还在" 1 "$(grep -c '别人的插件' "$config" || true)"
check "别人的哈希没被削" 1 "$(grep -c 'sha256:cafe' "$config" || true)"
check "mmw 区块里的第二行也删干净" 0 "$(grep -c 'sha256:dead' "$config" || true)"
check "紧跟其后的区块没被吞" 1 "$(grep -cx '\[mcp_servers.serena\]' "$config" || true)"
check "顶层键没被动" 1 "$(grep -cx 'model = "gpt-5.6"' "$config" || true)"
check "仍是合法 TOML" ok \
  "$(python3 -c "
import tomllib, pathlib, sys
try:
    tomllib.loads(pathlib.Path('$config').read_text())
    print('ok')
except Exception as exc:
    print(exc)
")"

echo
echo "再跑一次"
out="$(remove_legacy_codex_hook_state 2>&1)"
check "第二次不再打印" "" "$out"
check "第二次退出码为零" 零 "$([ $? -eq 0 ] && echo 零 || echo 非零)"

echo
echo "从没装过插件的机器"
printf 'model = "gpt-5.6"\n' > "$config"
before="$(cat "$config")"
out="$(remove_legacy_codex_hook_state 2>&1)"
check "一句话都不说" "" "$out"
check "文件一个字节都没动" "$before" "$(cat "$config")"

echo
echo "根本没有 config.toml"
rm -f "$config"
out="$(remove_legacy_codex_hook_state 2>&1)"
check "不报错也不造文件" "" "$out"
check "没凭空造出 config.toml" 没有 "$([ -e "$config" ] && echo 有 || echo 没有)"

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]

#!/usr/bin/env bash
# 依赖检查的测试。
#
# 三种 kind 各有各的找法，这里验它们不会互相顶替：
#   command       PATH 上的命令，找不到就点名它来自哪个 npm 包
#   sibling-file  没有命令入口，从 PATH 上另一个命令的位置反推。命令在而文件不在，
#                 要报得出来——两个包装在不同目录时就是这样
#   skill         skills CLI 装的落点，缺了要给出该跑的命令
#
# PATH 与 HOME 都指到临时目录，好验「没装时报得出来」，也不碰真的家目录。

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPT="$HERE/../scripts/check-deps.sh"
DEPS_JSON="$HERE/../scripts/deps.json"
rc=0

fail() {
  echo "  失败：$1" >&2
  rc=1
}

command -v jq >/dev/null 2>&1 || { echo "没装 jq，这份测试跑不了" >&2; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# 假 PATH 上只放脚本自己要用的外部命令，不放任何被检的依赖。bash 本身用绝对路径
# 调，否则连解释器都在这条 PATH 上找不到。
BASH_BIN="$(command -v bash)"
mkdir -p "$TMP/bin"
for c in jq dirname; do ln -s "$(command -v "$c")" "$TMP/bin/$c"; done

echo "--- 这台机器上四个能力齐了，逐条报出在哪"
out="$(bash "$SCRIPT" 2>&1)"; code=$?
[ "$code" -eq 0 ] || fail "本机依赖齐，退出码应当是 0：$out"
for cap in $(jq -r '.capabilities[].capability' "$DEPS_JSON"); do
  grep -q "$cap -> " <<<"$out" || fail "没报出 $cap 解析到哪"
done

echo "--- PATH 上什么都没有时，命令类能力逐个点名，并说出它来自哪个包"
out="$(PATH="$TMP/bin" HOME="$TMP" "$BASH_BIN" "$SCRIPT" 2>&1)"; code=$?
[ "$code" -ne 0 ] || fail "缺依赖时退出码应当非零"
grep -q "缺 browser" <<<"$out" || fail "没点名缺的浏览器能力"
grep -q "@playwright/cli" <<<"$out" || fail "没说出浏览器能力来自哪个包"
grep -q "缺 design-lint" <<<"$out" || fail "没点名缺的 lint 能力"

echo "--- 缺的那条要写明 missing 级别，好让正文按它分流"
grep -q "缺 browser（stop）" <<<"$out" || fail "browser 的级别应当是 stop"
grep -q "缺 design-lint（degrade）" <<<"$out" || fail "design-lint 的级别应当是 degrade"

echo "--- 外部技能缺失时报得出来，并给出该跑的命令"
grep -q "缺 design-system-author" <<<"$out" || fail "没点名缺的技能"
grep -q "npx skills add" <<<"$out" || fail "没给出该跑的命令"

echo "--- 锚点命令在、同级文件不在时，报的是文件不在，不是命令不在"
: >"$TMP/bin/playwright-cli"
chmod +x "$TMP/bin/playwright-cli"
out="$(PATH="$TMP/bin" HOME="$TMP" "$BASH_BIN" "$SCRIPT" 2>&1)"
grep -q "缺 accessibility" <<<"$out" || fail "没点名缺的无障碍引擎"
grep -q "旁边没有" <<<"$out" || fail "锚点在而文件不在，应当报文件不在"

echo "--- 外部技能在时不报它"
mkdir -p "$TMP/.agents/skills/create-design-md"
touch "$TMP/.agents/skills/create-design-md/SKILL.md"
out="$(PATH="$TMP/bin" HOME="$TMP" "$BASH_BIN" "$SCRIPT" 2>&1)"
grep -q "缺 design-system-author" <<<"$out" && fail "技能已在，不该报缺"

echo "--- 脚本自己不装任何东西"
grep -qE 'npm install|pnpm add|npx skills add[^"]*\$|curl |ln -s' "$SCRIPT" \
  && fail "脚本里有安装动作，它只该找和报"

echo "--- 不写死版本，也不写死找法"
grep -qE '[0-9]+\.[0-9]+\.[0-9]+' "$SCRIPT" && fail "脚本里写死了版本号"
grep -qE 'playwright|axe-core|@google/design\.md|create-design-md' "$SCRIPT" \
  && fail "脚本里写死了某个具体依赖，应当只从 deps.json 读"

echo "--- 不碰任何宿主的技能目录"
grep -qE '\.claude/skills|\.codex/skills|\.cursor/skills|\.grok/skills|\.pi/.*skills' "$SCRIPT" \
  && fail "脚本碰了宿主技能目录，那是 install.sh 的职权"

echo "--- 用法错误退出码是 2"
bash "$SCRIPT" --nonsense >/dev/null 2>&1
[ "$?" -eq 2 ] || fail "用法错误应当退出码 2"

[ "$rc" -eq 0 ] && echo "依赖检查：全过"
exit "$rc"

#!/usr/bin/env bash
# 依赖检查的测试。
#
# 三种 kind 各判各的，这里验它们不会互相顶替：
#   command / source  npm 装的，判版本
#   external-skill    skills CLI 装的，判落点在不在。跟着 npm 那几个按包名回读，
#                     会被永远判成已装，直到委派时才当场失败
#   shared-npx        不装也不判版本，报出来即可——它跟设计系统作者技能共用同一条
#                     npx 调用，两边解析同一份
#
# HOME 与 UI_QA_DEPS_ROOT 都指到临时目录，好验「没装时报得出来」，也不碰真的家目录。

set -uo pipefail

HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPT="$HERE/../scripts/install-deps.sh"
rc=0

fail() {
  echo "  失败：$1" >&2
  rc=1
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export UI_QA_DEPS_ROOT="$TMP/deps"

echo "--- 外部技能缺失时报得出来，并给出该跑的命令"
out="$(HOME="$TMP" bash "$SCRIPT" --check 2>&1)"
code=$?
[ "$code" -ne 0 ] || fail "缺依赖时退出码应当非零"
grep -q "create-design-md" <<<"$out" || fail "没点名缺的技能"
grep -q "npx skills add" <<<"$out" || fail "没给出该跑的命令"

echo "--- npm 那几个没装时逐个点名，并带上声明里的版本"
grep -q "@playwright/test（要 1.61.0）" <<<"$out" || fail "没点名浏览器自动化框架与版本"
grep -q "axe-core（要 4.13.0）" <<<"$out" || fail "没点名可访问性引擎与版本"

echo "--- 共享调用那条不判版本，但要报出来"
grep -q "@google/design.md 走共享调用" <<<"$out" || fail "没报出共享调用那一条"
grep -q "@google/design.md（要" <<<"$out" && fail "共享调用那条不该被当成 npm 包判版本"

echo "--- 外部技能在时不报它"
mkdir -p "$TMP/.agents/skills/create-design-md"
touch "$TMP/.agents/skills/create-design-md/SKILL.md"
out="$(HOME="$TMP" bash "$SCRIPT" --check 2>&1)"
grep -q "缺技能" <<<"$out" && fail "技能已在，不该报缺"

echo "--- 版本从声明里读，不写死在脚本里"
grep -qE '1\.61\.0|4\.13\.0' "$SCRIPT" && fail "脚本里写死了版本号，应当只从 deps.json 读"

echo "--- 用法错误退出码是 2"
HOME="$TMP" bash "$SCRIPT" --nonsense >/dev/null 2>&1
[ "$?" -eq 2 ] || fail "用法错误应当退出码 2"

echo "--- 不碰任何宿主的技能目录"
grep -qE '\.claude/skills|\.codex/skills|\.cursor/skills|\.grok/skills|\.pi/.*skills|ln -s' "$SCRIPT" \
  && fail "脚本碰了宿主技能目录或建了软链，那是 install.sh 的职权"

[ "$rc" -eq 0 ] && echo "依赖检查：全过"
exit "$rc"

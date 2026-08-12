#!/usr/bin/env bash
# 装界面 QA 的三个运行时依赖，版本按 deps.json 钉死。
#
# 装在哪：$MMW_RUNTIME_HOME/ui-qa，跟 runtime 平级，不在 runtime 里面。
# 三条理由：
#   1. Codex 与 Claude Code 运行的是 plugins/cache 里的副本，node_modules 跟着
#      复制过去会把插件撑大几百 MB，而它们并不需要这份副本。
#   2. install.sh 的 require_version_bump 逐字 diff runtime 与已装副本。装在
#      runtime 里，node_modules 一有差异就会误报「内容变了要升版本号」。
#   3. 依赖版本由 deps.json 管，跟产品版本号是两件事，不该绑在一起升。
#
# 技能不直接摸这个目录，走 mmw-ui-qa 转发器。所以这里只负责装，不负责被找到。
#
#   install-ui-qa-deps.sh          装
#   install-ui-qa-deps.sh --check  只看装没装、版本对不对。齐了回 0，缺东西回 1

set -euo pipefail

UI_QA_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS_JSON="$UI_QA_SRC/deps.json"
RUNTIME_HOME="${MMW_RUNTIME_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/mmw}"
DEPS_ROOT="${MMW_UI_QA_HOME:-$RUNTIME_HOME/ui-qa}"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *)
    echo "用法：install-ui-qa-deps.sh [--check]" >&2
    exit 2
    ;;
esac

die() {
  echo "mmw ui-qa install: $1" >&2
  exit "${2:-1}"
}

[ -f "$DEPS_JSON" ] || die "找不到依赖声明：$DEPS_JSON"
command -v jq >/dev/null 2>&1 || die "要 jq 才能读依赖声明"

installed_version() {
  local pkg="$1" manifest="$DEPS_ROOT/node_modules/$1/package.json"
  [ -f "$manifest" ] || return 1
  jq -r '.version // empty' "$manifest"
}

if [ "$mode" = check ]; then
  missing=0
  while IFS=$'\t' read -r pkg want; do
    [ -n "$pkg" ] || continue
    have="$(installed_version "$pkg" || true)"
    if [ -z "$have" ]; then
      echo "界面 QA  : 缺 ${pkg}（要 ${want}）" >&2
      missing=1
    elif [ "$have" != "$want" ]; then
      echo "界面 QA  : ${pkg} 版本是 ${have}，声明要 ${want}" >&2
      missing=1
    fi
  done < <(jq -r '.packages[] | [.package, .version] | @tsv' "$DEPS_JSON")
  [ "$missing" -eq 0 ] || exit 1
  echo "界面 QA  : 三个运行时依赖齐了"
  exit 0
fi

command -v npm >/dev/null 2>&1 || {
  echo "界面 QA  : 没有 npm，跳过三个运行时依赖。/mmw-ui-qa 会在起步第二步停下来说缺什么" >&2
  exit 0
}

mkdir -p "$DEPS_ROOT"
# 独立的 package.json：不写 npm -g，也不动用户的任何全局安装。
# private 为真，防止有人误 publish 这个目录。
if [ ! -f "$DEPS_ROOT/package.json" ]; then
  cat > "$DEPS_ROOT/package.json" <<'EOF'
{
  "name": "mmw-ui-qa-deps",
  "private": true,
  "description": "Managed by MMW. 版本由 mmw/ui-qa/deps.json 决定，不要手改这里。"
}
EOF
fi

specs=()
while IFS=$'\t' read -r pkg want; do
  [ -n "$pkg" ] || continue
  have="$(installed_version "$pkg" || true)"
  [ "$have" = "$want" ] && continue
  specs+=("$pkg@$want")
done < <(jq -r '.packages[] | [.package, .version] | @tsv' "$DEPS_JSON")

if [ "${#specs[@]}" -eq 0 ]; then
  echo "界面 QA  : 三个运行时依赖已是声明版本"
else
  # --save-exact：装完写进 package.json 的是精确版本，不是 ^ 范围。范围会让下一次
  # npm install 悄悄升上去，那就等于版本没钉死。
  ( cd "$DEPS_ROOT" && npm install --no-audit --no-fund --save-exact "${specs[@]}" >/dev/null ) \
    || die "装界面 QA 依赖失败：${specs[*]}"
  echo "界面 QA  : 已装 ${specs[*]}"
fi

# Playwright 的浏览器二进制单独下载，装了包不等于跑得起来。
# 只装 chromium：Electron 的渲染层就是 Chromium，另外两个引擎这里用不到。
if [ -x "$DEPS_ROOT/node_modules/.bin/playwright" ]; then
  ( cd "$DEPS_ROOT" && ./node_modules/.bin/playwright install chromium >/dev/null 2>&1 ) \
    || echo "界面 QA  : Chromium 没装上，自己跑一次 mmw-ui-qa browser install chromium 看报什么" >&2
fi

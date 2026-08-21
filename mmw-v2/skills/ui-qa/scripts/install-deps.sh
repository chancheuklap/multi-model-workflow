#!/usr/bin/env bash
# 装界面 QA 的运行时依赖，版本按 deps.json 钉死。
#
# 装在哪：这个技能自己的 deps/ 目录。技能软链进五个宿主，脚本用相对路径找它，
# 所以全机器只有一份 node_modules，五个宿主共用。
#
# 这里只装 npm 那几个，也只查四个装没装。**不碰任何宿主的技能目录**——软链是
# install.sh 的职权，两处都做就有两套安装逻辑。第四个依赖是一份技能，由 skills CLI
# 装在 ~/.agents/skills，这里只判它在不在，不装也不钉版本。
#
#   install-deps.sh          装
#   install-deps.sh --check  只看装没装、版本对不对。齐了回 0，缺东西回 1

set -euo pipefail

HERE="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS_JSON="$HERE/deps.json"
DEPS_ROOT="$HERE/deps"

mode=install
case "${1:-}" in
  --check) mode=check ;;
  "") ;;
  *)
    echo "用法：install-deps.sh [--check]" >&2
    exit 2
    ;;
esac

die() {
  echo "ui-qa deps: $1" >&2
  exit "${2:-1}"
}

[ -f "$DEPS_JSON" ] || die "找不到依赖声明：$DEPS_JSON"
command -v jq >/dev/null 2>&1 || die "要 jq 才能读依赖声明"

installed_version() {
  local manifest="$DEPS_ROOT/node_modules/$1/package.json"
  [ -f "$manifest" ] || return 1
  jq -r '.version // empty' "$manifest"
}

dep_count="$(jq -r '.packages | length' "$DEPS_JSON")"

if [ "$mode" = check ]; then
  missing=0

  # npm 那几个：装没装，版本对不对。
  while IFS=$'\t' read -r pkg want; do
    [ -n "$pkg" ] || continue
    have="$(installed_version "$pkg" || true)"
    if [ -z "$have" ]; then
      echo "ui-qa deps: 缺 ${pkg}（要 ${want}）" >&2
      missing=1
    elif [ "$have" != "$want" ]; then
      echo "ui-qa deps: ${pkg} 版本是 ${have}，声明要 ${want}" >&2
      missing=1
    fi
  done < <(jq -r '.packages[] | select(.kind != "external-skill") | [.package, .version] | @tsv' "$DEPS_JSON")

  # 外部技能：单独判它自己的落点。跟着上面按包名回读会把它永远判成已装，
  # 直到委派时才当场失败。
  while IFS=$'\t' read -r name detect installed_by; do
    [ -n "$name" ] || continue
    if [ ! -f "$HOME/$detect" ]; then
      echo "ui-qa deps: 缺技能 ${name}。装它：${installed_by}" >&2
      missing=1
    fi
  done < <(jq -r '.packages[] | select(.kind == "external-skill") | [.skill, .detect, .installedBy] | @tsv' "$DEPS_JSON")

  [ "$missing" -eq 0 ] || exit 1
  echo "ui-qa deps: ${dep_count} 个运行时依赖齐了"
  exit 0
fi

command -v npm >/dev/null 2>&1 || die "没有 npm，装不了浏览器自动化框架与那两个 npm 依赖"

mkdir -p "$DEPS_ROOT"

# 独立的 package.json：不写 npm -g，也不动用户的任何全局安装。
# private 为真，防止有人误 publish 这个目录。
if [ ! -f "$DEPS_ROOT/package.json" ]; then
  cat > "$DEPS_ROOT/package.json" <<'EOF'
{
  "name": "ui-qa-deps",
  "private": true,
  "description": "Managed by MMW. 版本由 ../deps.json 决定，不要手改这里。"
}
EOF
fi

specs=()
while IFS=$'\t' read -r pkg want; do
  [ -n "$pkg" ] || continue
  have="$(installed_version "$pkg" || true)"
  [ "$have" = "$want" ] && continue
  specs+=("$pkg@$want")
done < <(jq -r '.packages[] | select(.kind != "external-skill") | [.package, .version] | @tsv' "$DEPS_JSON")

if [ "${#specs[@]}" -eq 0 ]; then
  echo "ui-qa deps: npm 那几个已是声明版本"
else
  # --save-exact：装完写进 package.json 的是精确版本，不是 ^ 范围。范围会让下一次
  # npm install 悄悄升上去，那就等于版本没钉死。
  ( cd "$DEPS_ROOT" && npm install --no-audit --no-fund --save-exact "${specs[@]}" >/dev/null ) \
    || die "装依赖失败：${specs[*]}"
  echo "ui-qa deps: 已装 ${specs[*]}"
fi

# 浏览器二进制单独下载，装了包不等于跑得起来。
# 只装 chromium：Electron 的渲染层就是 Chromium，另外两个引擎这里用不到。
if [ -x "$DEPS_ROOT/node_modules/.bin/playwright" ]; then
  ( cd "$DEPS_ROOT" && ./node_modules/.bin/playwright install chromium >/dev/null 2>&1 ) \
    || echo "ui-qa deps: Chromium 没装上，自己跑一次 deps/node_modules/.bin/playwright install chromium 看报什么" >&2
fi

# 外部技能不在这里装：它归 skills CLI 管，MMW 替它装就有了第二个事实来源。
# 缺了就报出该跑的命令。
while IFS=$'\t' read -r name detect installed_by; do
  [ -n "$name" ] || continue
  if [ -f "$HOME/$detect" ]; then
    echo "ui-qa deps: 技能 ${name} 已在 ~/${detect%/SKILL.md}"
  else
    echo "ui-qa deps: 还缺技能 ${name}。装它：${installed_by}" >&2
  fi
done < <(jq -r '.packages[] | select(.kind == "external-skill") | [.skill, .detect, .installedBy] | @tsv' "$DEPS_JSON")

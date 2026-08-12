#!/usr/bin/env bash
# 装界面 QA 的四个运行时依赖，版本按 deps.json 钉死。
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

# 技能没有 package.json，版本写在 SKILL.md 的 YAML frontmatter 里。
# 只认顶部第一个 version: 行，正文里再出现同样的字样不算。
installed_skill_version() {
  local skill="$DEPS_ROOT/$1/SKILL.md"
  [ -f "$skill" ] || return 1
  awk '/^---[[:space:]]*$/{n++; if (n==2) exit; next}
       n==1 && /^version:[[:space:]]*/{sub(/^version:[[:space:]]*/,""); print; exit}' "$skill"
}

dep_count="$(jq -r '.packages | length' "$DEPS_JSON")"

if [ "$mode" = check ]; then
  missing=0
  while IFS=$'\t' read -r kind pkg want install_name; do
    [ -n "$pkg" ] || continue
    if [ "$kind" = skill ]; then
      have="$(installed_skill_version "$install_name" || true)"
    else
      have="$(installed_version "$pkg" || true)"
    fi
    if [ -z "$have" ]; then
      echo "界面 QA  : 缺 ${pkg}（要 ${want}）" >&2
      missing=1
    elif [ "$have" != "$want" ]; then
      echo "界面 QA  : ${pkg} 版本是 ${have}，声明要 ${want}" >&2
      missing=1
    fi
  done < <(jq -r '.packages[] | [.kind, .package, .version, (.installName // "")] | @tsv' "$DEPS_JSON")
  [ "$missing" -eq 0 ] || exit 1
  echo "界面 QA  : ${dep_count} 个运行时依赖齐了"
  exit 0
fi

mkdir -p "$DEPS_ROOT"

# npm 只管 kind 为 command 和 source 的那几个。没有 npm 时跳过它们，
# 不 exit——kind 为 skill 的那份只要 git，跟 npm 无关，下面还要装。
have_npm=1
command -v npm >/dev/null 2>&1 || {
  have_npm=0
  echo "界面 QA  : 没有 npm，跳过 npm 那几个依赖。/mmw-ui-qa 会在第 2 步停下来说缺什么" >&2
}

install_npm_deps() {
  local specs=() pkg want have

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

  while IFS=$'\t' read -r pkg want; do
    [ -n "$pkg" ] || continue
    have="$(installed_version "$pkg" || true)"
    if [ "$have" = "$want" ]; then continue; fi
    specs+=("$pkg@$want")
  done < <(jq -r '.packages[] | select(.kind != "skill") | [.package, .version] | @tsv' "$DEPS_JSON")

  if [ "${#specs[@]}" -eq 0 ]; then
    echo "界面 QA  : npm 那几个依赖已是声明版本"
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
}

if [ "$have_npm" -eq 1 ]; then
  install_npm_deps
fi

# ---- kind 为 skill 的依赖：从 GitHub 稀疏检出一份技能目录 ----
#
# 不整仓克隆：impeccable 整仓 950MB，要的那一份 3.4MB。--filter=blob:none 加
# --sparse 只取声明的那个子目录，按 tag 钉版本。
#
# 不装它的 plugin：plugin 会把它自己的 marketplace、hooks 和四个 subagent 一起
# 带进宿主，而界面 QA 只用到这一份技能。
install_skill_dep() {
  local pkg="$1" want="$2" repo="$3" tag="$4" repo_path="$5" name="$6"
  local dst="$DEPS_ROOT/$name" have stage

  have="$(installed_skill_version "$name" || true)"
  if [ "$have" = "$want" ]; then
    echo "界面 QA  : ${pkg} 已是 ${want}"
    return 0
  fi

  command -v git >/dev/null 2>&1 || {
    echo "界面 QA  : 没有 git，装不了 ${pkg}。/mmw-ui-qa 会在第 2 步停下来" >&2
    return 0
  }

  stage="$(mktemp -d "$DEPS_ROOT/.skill.XXXXXX")"
  if ! git clone --quiet --depth 1 --branch "$tag" --filter=blob:none --sparse \
       "$repo" "$stage/src" 2>/dev/null; then
    find "$stage" -depth -delete
    echo "界面 QA  : 取不到 ${pkg} 的 ${tag}，装不上。/mmw-ui-qa 会在第 2 步停下来" >&2
    return 0
  fi
  ( cd "$stage/src" && git sparse-checkout set "$repo_path" >/dev/null 2>&1 )

  if [ ! -f "$stage/src/$repo_path/SKILL.md" ]; then
    find "$stage" -depth -delete
    die "${pkg} 的 ${tag} 里没有 ${repo_path}/SKILL.md，上游布局变了，先改 deps.json"
  fi

  # 先搬到 stage 里的最终名字再原子换位：中途失败时旧的那份还完整可用。
  mv "$stage/src/$repo_path" "$stage/$name"
  if [ -e "$dst" ]; then
    mv "$dst" "$stage/.old"
  fi
  mv "$stage/$name" "$dst"
  find "$stage" -depth -delete
  echo "界面 QA  : 已装 ${pkg} $(installed_skill_version "$name")"
}

while IFS=$'\t' read -r pkg want repo tag repo_path name; do
  [ -n "$pkg" ] || continue
  install_skill_dep "$pkg" "$want" "$repo" "$tag" "$repo_path" "$name"
done < <(jq -r '.packages[] | select(.kind == "skill")
  | [.package, .version, .repo, .tag, .repoPath, .installName] | @tsv' "$DEPS_JSON")

# 技能要被宿主看见才有用。软链进本机已有的各宿主技能目录；目录不存在就说明
# 那个宿主没装，跳过。指向非 MMW 内容时不覆盖，报出来让人自己处理。
link_skill_into_hosts() {
  local name="$1"
  local src="$DEPS_ROOT/$name" dir dst current
  [ -d "$src" ] || return 0
  for dir in "${CODEX_HOME:-$HOME/.codex}/skills" "$HOME/.claude/skills" \
             "$HOME/.pi/skills" "$HOME/.cursor/skills"; do
    [ -d "$dir" ] || continue
    dst="$dir/$name"
    if [ -L "$dst" ]; then
      current="$(readlink "$dst")"
      if [ "$current" = "$src" ]; then
        continue
      fi
      case "$current" in
        "$DEPS_ROOT"/*) ln -sfn "$src" "$dst"; echo "界面 QA  : 更新软链 $dst" ;;
        *) echo "界面 QA  : $dst 指向非 MMW 内容（$current），没动它" >&2 ;;
      esac
    elif [ -e "$dst" ]; then
      echo "界面 QA  : $dst 已被非 MMW 内容占用，没动它" >&2
    else
      ln -s "$src" "$dst"
      echo "界面 QA  : 软链 $dst"
    fi
  done
}

while IFS= read -r name; do
  [ -n "$name" ] || continue
  link_skill_into_hosts "$name"
done < <(jq -r '.packages[] | select(.kind == "skill") | .installName' "$DEPS_JSON")

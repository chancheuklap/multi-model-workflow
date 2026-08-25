#!/usr/bin/env bash
# 把 SOURCES 列出的上游技能目录整份拉进本目录。每次同步整目录删掉重写，
# 所以永远不会有冲突，也永远没有手改 vendor 的机会。
# 用法：sync.sh          同步全部，写回 VENDOR.lock
#       sync.sh --check  只校验，不动文件
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK="$HERE/VENDOR.lock"

# <本地目录>|<owner/repo>|<分支>|<仓库内路径>|<许可证文件>|<故意没取的兄弟技能引用>
#
# 末段声明这份 vendor 指向本目录之外的哪些技能，空格分隔。我们只取需要的技能，
# 被指向的兄弟技能没跟过来，那条链接就断着——这是选择，不是损坏。校验要求实际
# 断链与这里声明的完全相等：上游新加或去掉一条跨技能引用，校验立刻红。
SOURCES='
diagram-design|cathrynlavery/diagram-design|main|skills/diagram-design|LICENSE|
html-diagram|plannotator/effective-html|main|skills/html-diagram|LICENSE|../design-artifact/SKILL.md
'

die() { echo "错：$*" >&2; exit 1; }

check_all() {
  local red=0 name repo branch path license external
  while IFS='|' read -r name repo branch path license external; do
    [ -n "$name" ] || continue
    check_one "$name" "$external" || red=1
  done < <(echo "$SOURCES" | grep -v '^[[:space:]]*$')
  return "$red"
}

# 先把分支解析成 commit，再按那个 commit 取归档，下来的内容和写进 lock 的 sha
# 必定是同一份。走 api / codeload 而不是 git 远程，只需要 HTTPS。
sync_one() {
  local name="$1" repo="$2" branch="$3" path="$4" license="$5"
  local tmp; tmp="$(mktemp -d)"

  local commit=""
  local try
  for try in 1 2 3 4 5; do
    commit="$(gh api "repos/${repo}/commits/${branch}" --jq .sha)" && break
    commit=""
    sleep "$try"
  done
  [ -n "$commit" ] || die "${name}：取不到 ${repo}@${branch} 的 commit"

  curl -fsSL --retry 3 --retry-delay 2 \
    "https://codeload.github.com/${repo}/tar.gz/${commit}" \
    | tar -xz -C "$tmp" || die "${name}：下载或解包失败"

  local root; root="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d)"
  [ -d "$root/$path" ] || die "${name}：上游没有 $path"
  [ -f "$root/$path/SKILL.md" ] || die "${name}：$path 里没有 SKILL.md"

  rm -rf "${HERE:?}/$name"
  cp -R "$root/$path" "$HERE/$name"
  [ -f "$root/$license" ] && cp "$root/$license" "$HERE/LICENSE-$name"

  rm -rf "$tmp"
  echo "${name}|${repo}|${path}|${commit}|$(date -u +%Y-%m-%d)"
}

# 每条 markdown 链接相对它所在文件的目录解析，打印解析不到的那些（去重排序）。
broken_links() {
  local dir="$1"
  find "$dir" -name '*.md' -type f | while read -r f; do
    grep -ohE '\]\([a-zA-Z0-9_./-]+\.md\)' "$f" 2>/dev/null \
      | sed -E 's/^\]\(//; s/\)$//' \
      | while read -r rel; do
          [ -e "$(dirname "$f")/$rel" ] || echo "$rel"
        done
  done | sort -u
}

check_one() {
  local name="$1" declared="$2" red=0
  local dir="$HERE/$name"

  [ -d "$dir" ] || { echo "缺  ${name}/"; return 1; }
  [ -f "$dir/SKILL.md" ] || { echo "缺  ${name}/SKILL.md"; return 1; }
  [ -f "$HERE/LICENSE-$name" ] || { echo "缺  LICENSE-${name}"; red=1; }

  head -1 "$dir/SKILL.md" | grep -q '^---$' || { echo "坏  ${name}/SKILL.md 没有 frontmatter"; red=1; }
  awk '/^---$/{n++; next} n==1 && /^name:/{f=1} n>=2{exit} END{exit !f}' "$dir/SKILL.md" \
    || { echo "坏  ${name}/SKILL.md frontmatter 没有 name:"; red=1; }

  local actual want
  actual="$(broken_links "$dir" | tr '\n' ' ' | sed -E 's/[[:space:]]+$//')"
  want="$(echo "$declared" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ' | sed -E 's/[[:space:]]+$//')"
  if [ "$actual" != "$want" ]; then
    echo "断链 ${name}/：声明「${want:-无}」，实际「${actual:-无}」"
    red=1
  fi

  grep -q "^${name}|" "$LOCK" 2>/dev/null || { echo "缺  VENDOR.lock 里没有 ${name}"; red=1; }

  [ "$red" -eq 0 ] && echo "好  ${name}/"
  return "$red"
}

if [ "${1:-}" = "--check" ]; then
  check_all
  exit $?
fi

command -v gh >/dev/null || die "没有 gh"
command -v curl >/dev/null || die "没有 curl"

{
  echo "# 本目录的每一份 vendor 从哪来、锁在哪个 commit。由 sync.sh 写，不要手改。"
  echo "# <目录>|<owner/repo>|<仓库内路径>|<commit>|<同步日期 UTC>"
  echo "$SOURCES" | grep -v '^[[:space:]]*$' | while IFS='|' read -r name repo branch path license external; do
    sync_one "$name" "$repo" "$branch" "$path" "$license"
  done
} > "$LOCK.new"
mv "$LOCK.new" "$LOCK"

echo
check_all
exit $?

#!/usr/bin/env bash
# spec 归档：GitHub Wiki。
#
# Wiki 没有 API——`gh` 没有 wiki 命令，REST 也没有 wiki 端点。读写一律 clone
# 之后走普通 git。
#
# 导航文件由本文件从各页面重新生成，不增量维护。所以每份 spec 页面第一行要有
# 一个机器可读块，`mmw-closing` 写页面时一并写上：
#
#   <!-- mmw:spec
#   slug: feat-phone-login
#   summary: 手机号登录取代邮箱验证码
#   date: 2026-08-03
#   source: https://github.com/o/r/pull/42
#   -->
#
# 用 HTML 注释不用 YAML frontmatter：GitHub Wiki 不解析 frontmatter，会把它当
# 正文显示出来。

set -euo pipefail

# Wiki 的工作副本落在**当前这棵树**下，不是主仓库——跟 mmw_task_dir 用
# mmw_main_root 不一样，这是有意的。收尾的会话各自克隆一份，两个任务同时收尾
# 时各写各的页面、各推各的；共用主仓库那一份的话，A 写完还没推、B 一跑 pull
# 就撞上 A 的未提交改动。Wiki 仓库很小，多克隆几次不心疼。
mmw_wiki_dir() {
  echo "$(mmw_repo_root)/$(mmw_path_field worktrees)/.wiki"
}

# clone 或 pull，输出本地路径。Wiki 还没初始化就报错——只有用户能在网页上建
# 第一页，没有 API 能替他建。
mmw_wiki_ensure() {
  local repo url dir
  repo="$(mmw_gh_repo)"
  url="https://github.com/$repo.wiki.git"
  dir="$(mmw_wiki_dir)"

  if ! git ls-remote "$url" >/dev/null 2>&1; then
    echo "mmw: $repo 的 Wiki 还没初始化" >&2
    echo "     去 https://github.com/$repo/wiki 手建一页任意内容，没有 API 能替代" >&2
    return 1
  fi

  if [ -d "$dir/.git" ]; then
    git -C "$dir" pull --quiet
  else
    mkdir -p "$(dirname "$dir")"
    git clone --quiet "$url" "$dir"
  fi
  echo "$dir"
}

# 从一份页面里取机器可读块的某个字段。取不到输出空。
mmw_wiki_field() {
  local file="$1" key="$2"
  awk -v key="$key" '
    /^<!-- mmw:spec[[:space:]]*$/ { inblock = 1; next }
    inblock && /^-->/ { exit }
    inblock {
      if (match($0, "^" key ":[[:space:]]*")) {
        print substr($0, RLENGTH + 1)
        exit
      }
    }
  ' "$file"
}

# 重新生成 Home.md 与 _Sidebar.md。两份都是导出物，每次从全部 spec 页面重建，
# 不增量改——页面被删或改名时导航跟着对。
mmw_wiki_nav() {
  local dir home sidebar
  dir="$(mmw_wiki_dir)"
  [ -d "$dir" ] || { echo "mmw: $dir 不在，先跑 mmw wiki ensure" >&2; return 1; }
  home="$dir/Home.md"
  sidebar="$dir/_Sidebar.md"

  local rows="" page slug summary date source count=0 missing=""
  for page in "$dir"/Spec-*.md; do
    [ -e "$page" ] || continue
    slug="$(mmw_wiki_field "$page" slug)"
    summary="$(mmw_wiki_field "$page" summary)"
    date="$(mmw_wiki_field "$page" date)"
    source="$(mmw_wiki_field "$page" source)"
    # 旧页面使用 pr 字段。读取兼容只用于导航，不要求重写历史页面。
    [ -n "$source" ] || source="$(mmw_wiki_field "$page" pr)"
    if [ -z "$slug" ] || [ -z "$summary" ] || [ -z "$date" ] || [ -z "$source" ]; then
      missing="$missing $(basename "$page")"
      continue
    fi
    rows="$rows$date\t$slug\t$summary\t$source\n"
    count=$((count + 1))
  done

  if [ -n "$missing" ]; then
    echo "mmw: 这几页缺 slug、summary、date 或 source/pr 元数据，没进导航：$missing" >&2
  fi

  {
    printf '# Specs\n\n'
    printf '| Spec | 解决什么 | 落地日期 | Source |\n'
    printf '| --- | --- | --- | --- |\n'
    if [ "$count" -gt 0 ]; then
      printf '%b' "$rows" | sort -r | while IFS=$'\t' read -r d s sm src; do
        [ -n "$s" ] || continue
        printf '| [[Spec-%s\|%s]] | %s | %s | %s |\n' "$s" "$s" "$sm" "$d" "${src:--}"
      done
    fi
  } > "$home"

  {
    printf '**[[Home]]**\n\n'
    if [ "$count" -gt 0 ]; then
      printf '%b' "$rows" | sort -r | while IFS=$'\t' read -r d s sm src; do
        [ -n "$s" ] || continue
        printf -- '- [[Spec-%s|%s]]\n' "$s" "$s"
      done
    fi
  } > "$sidebar"

  echo "导航已重生成，收录 $count 份 spec"
  [ -z "$missing" ]
}

# 页面及四项元数据、两个导航条目、远端一致性三组验证全过才允许删本地文档。
mmw_wiki_verify() {
  local slug="$1" dir page page_slug summary date source rc=0
  dir="$(mmw_wiki_dir)"
  page="$dir/Spec-$slug.md"

  if [ -s "$page" ]; then
    echo "页面     : $page"
  else
    echo "页面     : 不存在或是空的 — $page" >&2
    rc=1
  fi

  page_slug="$(mmw_wiki_field "$page" slug 2>/dev/null || true)"
  summary="$(mmw_wiki_field "$page" summary 2>/dev/null || true)"
  date="$(mmw_wiki_field "$page" date 2>/dev/null || true)"
  source="$(mmw_wiki_field "$page" source 2>/dev/null || true)"
  # 旧页面使用 pr 字段。验证兼容旧页面，不要求重写历史元数据。
  [ -n "$source" ] || source="$(mmw_wiki_field "$page" pr 2>/dev/null || true)"
  if [ "$page_slug" = "$slug" ] && [ -n "$summary" ] && [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && [ -n "$source" ]; then
    echo "元数据   : slug、summary、date、source 完整"
  else
    echo "元数据   : 不完整 — 必须有匹配的 slug、非空 summary、YYYY-MM-DD date 和 source/pr" >&2
    rc=1
  fi

  local f
  for f in Home.md _Sidebar.md; do
    if [ -f "$dir/$f" ] && grep -q "Spec-$slug" "$dir/$f"; then
      echo "$f  : 有这一页的条目"
    else
      echo "$f  : 没有 Spec-$slug 的条目" >&2
      rc=1
    fi
  done

  local head upstream
  head="$(git -C "$dir" rev-parse HEAD 2>/dev/null || echo "")"
  upstream="$(git -C "$dir" rev-parse '@{u}' 2>/dev/null || echo "")"
  if [ -n "$head" ] && [ "$head" = "$upstream" ]; then
    echo "推送     : 已推上去（${head}）"
  else
    echo "推送     : 本地 ${head:-无} 与远端 ${upstream:-无} 不一致" >&2
    rc=1
  fi

  return $rc
}

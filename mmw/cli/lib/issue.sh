#!/usr/bin/env bash
# issue tracker：GitHub Issues。
#
# 只收三类动作：要连着发好几个请求的、要先取 database id 的、要按规矩过滤排
# 序的。一条 gh 命令就做完的（读、评论、打标签、关闭）不收——技能直接用 gh，
# 少一层包装。
#
# 顺序的判据：ticket 按依赖顺序发布、阻塞方先发（`/mmw-to-tickets` 第 5 步），
# 所以 issue 编号升序就是依赖顺序。不靠 sub-issues 端点的返回顺序，那个没有
# 文档化的保证；也不靠父正文的清单，父正文里没有清单。
#
# 父子关系用 sub-issues 端点、阻塞关系用 issue dependencies 端点，两者都没有
# 降级路径，这是有意的：端点没开时 `mmw issue create --parent` 直接失败，不退
# 回「父正文写任务清单、子正文顶部写 Blocked by」那套文本约定。理由是
# `mmw issue frontier` 要靠这两个端点算出谁可认领，文本约定算不出来——留一条
# 降级路径只会让 frontier 在那些仓库里静默返回错的结果。端点在 GitHub 上按仓
# 库启用，报错了就去仓库设置里开，不要在这里绕。

set -euo pipefail

mmw_gh_repo() {
  if [ -z "${MMW_GH_REPO:-}" ]; then
    MMW_GH_REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
    export MMW_GH_REPO
  fi
  echo "$MMW_GH_REPO"
}

# issue 的 database id。连依赖边要它，不是 #编号，也不是 node_id。
mmw_issue_dbid() {
  gh api "repos/$(mmw_gh_repo)/issues/$1" --jq .id
}

# 父 issue 的全部子 issue，一行一个 JSON 对象，按编号升序。
# sub_issues 端点返回的对象不一定带依赖摘要，缺了就逐个补齐。
#
# 多页时 gh 把各页的数组合并成一个数组（gh 2.96 实测：82 条跨 5 页，顶层仍是
# 单个 array），所以下面直接对整体取 length 和 .[0] 是成立的。
mmw_issue_children_raw() {
  local parent="$1" repo list
  repo="$(mmw_gh_repo)"
  list="$(gh api --paginate "repos/$repo/issues/$parent/sub_issues")"

  if [ "$(jq 'length' <<<"$list")" -eq 0 ]; then
    return 0
  fi

  if [ "$(jq -r '.[0] | has("issue_dependencies_summary")' <<<"$list")" = "true" ]; then
    jq -c 'sort_by(.number) | .[]' <<<"$list"
    return 0
  fi

  local n
  for n in $(jq -r 'sort_by(.number) | .[].number' <<<"$list"); do
    gh api "repos/$repo/issues/$n"
  done | jq -c .
}

# 过滤成一行一张：编号、状态、认领人、未关闭阻塞数、标签、标题。
mmw_issue_children() {
  mmw_issue_children_raw "$1" | jq -r '
    [ .number,
      .state,
      (if (.assignees | length) > 0 then (.assignees | map(.login) | join(",")) else "-" end),
      (.issue_dependencies_summary.blocked_by // 0),
      ([.labels[].name] | join(",") // "-"),
      .title
    ] | @tsv'
}

# frontier：open、没被挡、没人认领的子 issue，按编号升序。
# 全部要的自己读全部行，只要下一张的取第一行。
mmw_issue_frontier() {
  local parent="$1" label="${2:-}"
  mmw_issue_children_raw "$parent" | jq -r --arg label "$label" '
    select(.state == "open")
    | select((.issue_dependencies_summary.blocked_by // 0) == 0)
    | select((.assignees | length) == 0)
    | select($label == "" or ([.labels[].name] | index($label)))
    | [.number, .title] | @tsv'
}

# 认领：先确认还没人占，再指派给自己。
# 两步之间有窗口，指派后再读一次确认落在自己头上——并行会话靠这个互斥。
mmw_issue_claim() {
  local n="$1" repo me holder
  repo="$(mmw_gh_repo)"
  holder="$(gh api "repos/$repo/issues/$n" --jq '[.assignees[].login] | join(",")')"
  if [ -n "$holder" ]; then
    echo "mmw: #$n 已被 $holder 认领" >&2
    return 1
  fi
  gh issue edit "$n" --add-assignee @me >/dev/null
  me="$(gh api user --jq .login)"
  holder="$(gh api "repos/$repo/issues/$n" --jq '[.assignees[].login] | join(",")')"
  if [ "$holder" != "$me" ]; then
    echo "mmw: #$n 认领失败，现在归 ${holder:-无人}" >&2
    return 1
  fi
  echo "#$n 已认领"
}

# 连一条阻塞边：<被挡的> 被 <挡它的> 挡着。
mmw_issue_link() {
  local child="$1" blocker="$2" repo blocker_id
  repo="$(mmw_gh_repo)"
  blocker_id="$(mmw_issue_dbid "$blocker")"
  gh api --method POST \
    "repos/$repo/issues/$child/dependencies/blocked_by" \
    -F "issue_id=$blocker_id" >/dev/null
  echo "#$child 被 #$blocker 挡着"
}

# 建 issue，可选挂到父 issue 下、连阻塞边、打标签。
# 三件事一次做完：单独做要主 agent 记住取 database id 和调用顺序。
mmw_issue_create() {
  local title="" body_file="" parent="" labels="" blocked_by=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --title) title="${2:-}"; shift 2 ;;
      --body-file) body_file="${2:-}"; shift 2 ;;
      --parent) parent="${2:-}"; shift 2 ;;
      --label) labels="${2:-}"; shift 2 ;;
      --blocked-by) blocked_by="${2:-}"; shift 2 ;;
      *) echo "mmw: issue create 认不出参数 $1" >&2; return 2 ;;
    esac
  done
  [ -n "$title" ] || { echo "mmw: issue create 要 --title" >&2; return 2; }
  [ -n "$body_file" ] || { echo "mmw: issue create 要 --body-file" >&2; return 2; }
  [ -f "$body_file" ] || { echo "mmw: 正文文件不存在：$body_file" >&2; return 1; }

  local repo url n
  repo="$(mmw_gh_repo)"

  local args=(--title "$title" --body-file "$body_file")
  [ -z "$labels" ] || args+=(--label "$labels")
  url="$(gh issue create "${args[@]}")"
  n="${url##*/}"

  if [ -n "$parent" ]; then
    gh api --method POST "repos/$repo/issues/$parent/sub_issues" \
      -F "sub_issue_id=$(mmw_issue_dbid "$n")" >/dev/null
  fi

  local b
  for b in ${blocked_by//,/ }; do
    if [ -n "$b" ]; then
      mmw_issue_link "$n" "$b" > /dev/null
    fi
  done

  echo "$n"
}

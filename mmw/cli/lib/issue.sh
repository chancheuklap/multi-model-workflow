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

mmw_issue_set_parent_edge() {
  local child="$1" parent="$2" repo child_id
  repo="$(mmw_gh_repo)"
  child_id="$(mmw_issue_dbid "$child")"
  gh api --method POST "repos/$repo/issues/$parent/sub_issues" \
    -F "sub_issue_id=$child_id" > /dev/null
}

# 父 issue 的全部子 issue，一行一个 JSON 对象，按编号升序。
# sub_issues 端点返回的对象不一定带依赖摘要，缺了就逐个补齐。
#
# 多页时 gh 把各页的数组合并成一个数组（gh 2.96 实测：82 条跨 5 页，顶层仍是
# 单个 array），所以下面直接对整体取 length 和 .[0] 是成立的。
mmw_issue_children_raw() {
  local parent="$1" repo list
  repo="$(mmw_gh_repo)" || return 1
  # 显式判 gh 的失败，不靠 set -e。调用方把这个函数放进 `if` 或 `||` 的左侧时
  # set -e 被禁用，那时空的 list 会一路走到下面的整数比较，函数反而返回 0，
  # 调用方拿到一份空清单当成「这个 parent 没有子 issue」。
  if ! list="$(gh api --paginate "repos/$repo/issues/$parent/sub_issues")"; then
    echo "mmw issue: 读不到 issue $parent 的子 issue" >&2
    return 1
  fi

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

# 过滤成一行一张：编号、状态、认领人、还被几张挡着、标签、标题。
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
  local parent="$1" label="${2:-}" label_prefix="${3:-}"
  mmw_issue_children_raw "$parent" | jq -r --arg label "$label" --arg label_prefix "$label_prefix" '
    select(.state == "open")
    | select((.issue_dependencies_summary.blocked_by // 0) == 0)
    | select((.assignees | length) == 0)
    | [(.labels // [])[].name] as $labels
    | select($label == "" or ($labels | index($label)))
    | select($label_prefix == "" or any($labels[]; startswith($label_prefix)))
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

  local url n
  local args=(--title "$title" --body-file "$body_file")
  [ -z "$labels" ] || args+=(--label "$labels")
  url="$(gh issue create "${args[@]}")"
  n="${url##*/}"

  if [ -n "$parent" ]; then
    mmw_issue_set_parent_edge "$n" "$parent"
  fi

  local b
  for b in ${blocked_by//,/ }; do
    if [ -n "$b" ]; then
      mmw_issue_link "$n" "$b" > /dev/null
    fi
  done

  echo "$n"
}

# 把正文里的二级标题取成标题文字，一行一个。
mmw_issue_h2_titles() {
  awk '/^## / { print substr($0, 4) }' <<<"$1"
}

# 返回 first 的全部行中不在 second 里的行。重复行按出现次数分别计算。
mmw_issue_missing_lines() {
  awk '
    NR == FNR {
      count[$0]++
      if (!($0 in seen)) {
        seen[$0] = 1
        order[++order_length] = $0
      }
      next
    }
    count[$0] > 0 { count[$0]-- }
    END {
      for (i = 1; i <= order_length; i++) {
        for (j = 0; j < count[order[i]]; j++) {
          print order[i]
        }
      }
    }
  ' <(printf '%s\n' "$1") <(printf '%s\n' "$2")
}

# 在指定二级标题的最后一个非空行之后插入传入的行。
# 找不到标题时返回 3；调用方负责列出可用标题。
mmw_issue_insert_lines() {
  local body="$1" section="$2"
  shift 2
  local -a lines=("$@") body_lines=()
  local i header=-1 last=-1 in_section=0 current

  while IFS= read -r current || [ -n "$current" ]; do
    body_lines+=("$current")
  done <<<"$body"
  for i in "${!body_lines[@]}"; do
    current="${body_lines[$i]}"
    if [ "$current" = "## $section" ]; then
      header="$i"
      last="$i"
      in_section=1
      continue
    fi
    if [ "$in_section" -eq 1 ] && [[ "$current" == "## "* ]]; then
      break
    fi
    if [ "$in_section" -eq 1 ] && [[ "$current" =~ [^[:space:]] ]]; then
      last="$i"
    fi
  done

  [ "$header" -ge 0 ] || return 3

  for i in "${!body_lines[@]}"; do
    printf '%s\n' "${body_lines[$i]}"
    if [ "$i" -eq "$last" ]; then
      [ "${#lines[@]}" -eq 0 ] || printf '%s\n' "${lines[@]}"
    fi
  done
}

mmw_issue_read_body() {
  gh api "repos/$(mmw_gh_repo)/issues/$1" --jq .body
}

mmw_issue_write_body() {
  local n="$1" body="$2" file rc
  file="$(mktemp "${TMPDIR:-/tmp}/mmw-issue-body.XXXXXX")"
  printf '%s' "$body" > "$file"
  if gh issue edit "$n" --body-file "$file" > /dev/null; then
    rm "$file"
    return 0
  fi
  rc=$?
  rm "$file"
  return "$rc"
}

# 追加一行：读、插入、写、等待、重读。重读同时确认旧行与新行都还在。
mmw_issue_append() {
  local n="$1"
  shift
  local section="" line="" got_section=0 got_line=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --section)
        [ $# -ge 2 ] || { echo "mmw: issue append 要 --section" >&2; return 2; }
        section="$2"
        got_section=1
        shift 2
        ;;
      --line)
        [ $# -ge 2 ] || { echo "mmw: issue append 要 --line" >&2; return 2; }
        line="$2"
        got_line=1
        shift 2
        ;;
      *) echo "mmw: issue append 认不出参数 $1" >&2; return 2 ;;
    esac
  done
  [ "$got_section" -eq 1 ] && [ -n "$section" ] || {
    echo "mmw: issue append 要 --section" >&2
    return 2
  }
  [ "$got_line" -eq 1 ] && [ -n "$line" ] || {
    echo "mmw: issue append 要 --line" >&2
    return 2
  }
  case "$line" in
    *$'\n'*) echo "mmw: issue append 的 --line 只接收单行内容" >&2; return 2 ;;
  esac

  local -a required_lines=("$line") additions=()
  local attempt v1 v2 v3 missing_v1 candidate known new_line_present rc
  for attempt in 0 1 2 3; do
    if v1="$(mmw_issue_read_body "$n")"; then
      :
    else
      return $?
    fi
    additions=()
    for candidate in "${required_lines[@]}"; do
      if ! grep -Fqx -- "$candidate" <<<"$v1"; then
        additions+=("$candidate")
      fi
    done

    if v2="$(mmw_issue_insert_lines "$v1" "$section" ${additions[@]+"${additions[@]}"})"; then
      rc=0
    else
      rc=$?
    fi
    if [ "$rc" -eq 3 ]; then
      echo "mmw: #$n 找不到二级标题「${section}」；现有二级标题：" >&2
      mmw_issue_h2_titles "$v1" | sed 's/^/  /' >&2
      return 1
    fi
    [ "$rc" -eq 0 ] || return "$rc"

    mmw_issue_write_body "$n" "$v2" || return $?
    sleep 2 || return $?
    if v3="$(mmw_issue_read_body "$n")"; then
      :
    else
      return $?
    fi
    if missing_v1="$(mmw_issue_missing_lines "$v1" "$v3")"; then
      :
    else
      return $?
    fi
    if grep -Fqx -- "$line" <<<"$v3"; then
      new_line_present=1
    else
      new_line_present=0
    fi
    if [ -z "$missing_v1" ] && [ "$new_line_present" -eq 1 ]; then
      echo "#$n 已向「${section}」追加一行"
      return 0
    fi

    if [ -n "$missing_v1" ]; then
      while IFS= read -r known || [ -n "$known" ]; do
        [ -n "$known" ] || continue
        local duplicate=0
        for candidate in "${required_lines[@]}"; do
          [ "$candidate" = "$known" ] && duplicate=1
        done
        [ "$duplicate" -eq 1 ] || required_lines+=("$known")
      done <<<"$missing_v1"
    fi

    if [ "$attempt" -eq 3 ]; then
      echo "mmw: #$n 重做 3 次后仍不一致；缺失行：" >&2
      [ -z "$missing_v1" ] || printf '%s\n' "$missing_v1" >&2
      [ "$new_line_present" -eq 1 ] || printf '%s\n' "$line" >&2
      return 1
    fi
  done
}

# 给已存在的 issue 设置父 issue。端点不可用时直接把错误交给调用方。
mmw_issue_set_parent() {
  local child="$1"
  shift
  local parent=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --parent)
        [ $# -ge 2 ] || { echo "mmw: issue set-parent 要 --parent" >&2; return 2; }
        parent="$2"
        shift 2
        ;;
      *) echo "mmw: issue set-parent 认不出参数 $1" >&2; return 2 ;;
    esac
  done
  [ -n "$parent" ] || { echo "mmw: issue set-parent 要 --parent" >&2; return 2; }
  mmw_issue_set_parent_edge "$child" "$parent" || return $?
  echo "#$child 已挂到 #$parent 下"
}

#!/usr/bin/env bash
# 产物落点数据只在 artifacts.json。这里读取数据、验证调用方输入并返回路径。

set -euo pipefail

MMW_ARTIFACT_DATA="$MMW_ROOT/cli/artifacts.json"

usage_artifact() {
  cat >&2 <<'EOF'
mmw artifact path <类别> [--name <工作名>] [--issue <编号>] [--sub <类别内细分>] [--absolute]
mmw artifact index <类别>
mmw artifact check
mmw artifact list [--name <工作名>] [--map <map 编号>]

类别与术语：
EOF
  jq -r 'to_entries | sort_by(.key)[] | [.key, .value.term] | @tsv' "$MMW_ARTIFACT_DATA" >&2
  return 2
}

mmw_artifact_error() {
  echo "mmw artifact: $*" >&2
  return 1
}

mmw_artifact_validate_segment() {
  local value="$1" label="$2"
  mmw_path_safe_segment "$value" "$label" "mmw artifact:"
}

mmw_artifact_validate_sub() {
  local sub="$1" segment
  local -a segments
  if [[ "$sub" == *$'\n'* ]]; then
    mmw_artifact_error "--sub 不能包含换行"
    return 1
  fi
  if [ -z "$sub" ] || [[ "$sub" == /* ]] || [[ "$sub" == */ ]] || [[ "$sub" == *//* ]]; then
    mmw_artifact_error "--sub 不能有空路径段"
    return 1
  fi
  local IFS='/'
  read -r -a segments <<< "$sub"
  for segment in "${segments[@]}"; do
    mmw_artifact_validate_segment "$segment" "--sub 的路径段" || return 1
  done
}

mmw_artifact_allowed_subs() {
  local record="$1"
  # 用 jq 自己 join。`paste -d ', '` 把两个字符当成分隔符列表循环使用，
  # 结果是逗号和空格交替出现，读的人会把 `evidence questionnaire` 当成一个取值。
  jq -r '.sub_fixed | join(", ")' <<< "$record"
}

mmw_artifact_path() {
  local category="${1:-}" record status term root root_kind
  local name="" issue="" sub="" absolute=false
  local name_given=false issue_given=false sub_given=false
  local has_name allows_scope sub_naming fixed_count fixed_first pattern
  local scope="" relative="" result="" part
  local task_state task_kind task_branch task_head task_name task_extra

  [ -n "$category" ] || usage_artifact
  shift

  while [ $# -gt 0 ]; do
    case "$1" in
      --name)
        [ $# -ge 2 ] || { mmw_artifact_error "--name 要有工作名"; return 1; }
        [ "$name_given" = false ] || { mmw_artifact_error "--name 只能给一次"; return 1; }
        name="$2"
        name_given=true
        shift 2
        ;;
      --issue)
        [ $# -ge 2 ] || { mmw_artifact_error "--issue 要有编号"; return 1; }
        [ "$issue_given" = false ] || { mmw_artifact_error "--issue 只能给一次"; return 1; }
        issue="$2"
        issue_given=true
        shift 2
        ;;
      --sub)
        [ $# -ge 2 ] || { mmw_artifact_error "--sub 要有类别内细分"; return 1; }
        [ "$sub_given" = false ] || { mmw_artifact_error "--sub 只能给一次"; return 1; }
        sub="$2"
        sub_given=true
        shift 2
        ;;
      --absolute)
        absolute=true
        shift
        ;;
      *)
        mmw_artifact_error "认不出参数 $1"
        return 1
        ;;
    esac
  done

  [ -f "$MMW_ARTIFACT_DATA" ] || {
    mmw_artifact_error "找不到产物落点数据 $MMW_ARTIFACT_DATA"
    return 1
  }
  if ! record="$(jq -ce --arg category "$category" '.[$category]' "$MMW_ARTIFACT_DATA" 2>/dev/null)"; then
    mmw_artifact_error "认不出的类别 ${category}；全部合法类别名：$(jq -r 'keys | join(", ")' "$MMW_ARTIFACT_DATA")"
    return 1
  fi

  status="$(jq -r '.status' <<< "$record")"
  term="$(jq -r '.term' <<< "$record")"
  case "$status" in
    no-file)
      if [ "$category" = "task" ]; then
        mmw_artifact_error "$term 不写文件；正文经标准输入传给 mmw dispatch"
      else
        mmw_artifact_error "$term 不写文件；正文走 subagent 的标准输出"
      fi
      return 1
      ;;
    not-shaped)
      mmw_artifact_error "$term 不套路径形状；由 $(jq -r '.answered_by' <<< "$record") 回答"
      return 1
      ;;
    external)
      if [ "$category" = "handoff" ]; then
        mmw_artifact_error "$term 落在操作系统临时目录，不在仓库里"
      else
        mmw_artifact_error "$term 的位置由用户指定，不在仓库里"
      fi
      return 1
      ;;
    tracker)
      mmw_artifact_error "$term 落在 issue tracker 上，不占仓库路径；用 gh issue view <编号> 访问"
      return 1
      ;;
    active) ;;
    *)
      mmw_artifact_error "$category 的状态无效：$status"
      return 1
      ;;
  esac

  has_name="$(jq -r '.has_name' <<< "$record")"
  allows_scope="$(jq -r '.allows_scope' <<< "$record")"
  if [ "$has_name" = "true" ]; then
    if [ "$name_given" = false ]; then
      task_state="$(mmw_task_state)" || return 1
      IFS=' ' read -r task_kind task_branch task_head task_name task_extra <<< "$task_state"
      if [ "$task_kind" != "bound" ] || [ -z "$task_branch" ] || [ -z "$task_head" ] || \
        [ -z "$task_name" ] || [ -n "$task_extra" ]; then
        mmw_artifact_error "$category 要 --name <工作名>，或在带工作名的任务 worktree 里运行"
        return 1
      fi
      name="$task_name"
    fi
    mmw_artifact_validate_segment "$name" "--name" || return 1
  elif [ "$name_given" = true ]; then
    mmw_artifact_error "$category 没有名字段，不能给 --name"
    return 1
  fi

  if [ "$issue_given" = true ]; then
    [[ "$issue" =~ ^[0-9]+$ ]] || {
      mmw_artifact_error "--issue 只接收纯编号"
      return 1
    }
    [ "$allows_scope" = "true" ] || {
      mmw_artifact_error "$category 没有范围段，不能给 --issue"
      return 1
    }
    scope="issue-$issue"
  fi

  fixed_count="$(jq -r '.sub_fixed | length' <<< "$record")"
  if [ "$sub_given" = false ] && [ "$fixed_count" -eq 1 ]; then
    sub="$(jq -r '.sub_fixed[0]' <<< "$record")"
  elif [ "$sub_given" = false ]; then
    mmw_artifact_error "$category 要 --sub <类别内细分>"
    return 1
  fi

  if jq -e --arg sub "$sub" '.sub_fixed | index($sub) != null' <<< "$record" >/dev/null; then
    :
  else
    mmw_artifact_validate_sub "$sub" || return 1
    fixed_first="${sub%%/*}"
    if [ "$fixed_count" -gt 1 ] && jq -e --arg first "$fixed_first" '.sub_fixed | index($first) != null' <<< "$record" >/dev/null; then
      :
    else
      pattern="$(jq -r '.sub_pattern // empty' <<< "$record")"
      if [ -n "$pattern" ]; then
        pattern="${pattern//\\d/[0-9]}"
        if [[ ! "$sub" =~ $pattern ]]; then
          mmw_artifact_error "$category 的 --sub 不匹配允许的模式"
          return 1
        fi
      elif [ "$fixed_count" -gt 0 ]; then
        mmw_artifact_error "$category 的 --sub 不在允许的取值：$(mmw_artifact_allowed_subs "$record")"
        return 1
      fi
    fi
  fi

  root="$(jq -r '.root' <<< "$record")"
  root_kind="$(jq -r '.root_kind' <<< "$record")"
  if [ "$root_kind" = "workdir" ]; then
    root="$(mmw_path_field "$root")" || return 1
  fi

  for part in "$root" "$name" "$scope" "$sub"; do
    [ -n "$part" ] || continue
    if [ -z "$relative" ]; then
      relative="$part"
    else
      relative="$relative/$part"
    fi
  done

  if [ "$absolute" = "true" ]; then
    if [[ "$root" = /* ]]; then
      result="$root"
      for part in "$name" "$scope" "$sub"; do
        [ -n "$part" ] && result="$result/$part"
      done
    else
      result="$(mmw_repo_root)/$relative"
    fi
  else
    result="$relative"
  fi
  printf '%s\n' "$result"

  sub_naming="$(jq -r '.sub_naming' <<< "$record")"
  if [ "$sub_naming" = "ad-hoc" ]; then
    echo "mmw artifact: 这一类的名字当场取，写第一个文件之前先列一次父目录" >&2
  fi
}

mmw_artifact_list() {
  local name="" map="" task_state task_kind task_branch task_head task_name task_extra
  local name_given=false map_given=false record root repo_root category category_dir index
  local relative issue sub ticket number title children

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --name)
        [ $# -ge 2 ] || { mmw_artifact_error "--name 要有工作名"; return 1; }
        [ "$name_given" = false ] || { mmw_artifact_error "--name 只能给一次"; return 1; }
        name="$2"
        name_given=true
        shift 2
        ;;
      --map)
        [ $# -ge 2 ] || { mmw_artifact_error "--map 要有编号"; return 1; }
        [ "$map_given" = false ] || { mmw_artifact_error "--map 只能给一次"; return 1; }
        map="$2"
        map_given=true
        shift 2
        ;;
      *)
        mmw_artifact_error "认不出参数 $1"
        return 1
        ;;
    esac
  done

  [ -f "$MMW_ARTIFACT_DATA" ] || {
    mmw_artifact_error "找不到产物落点数据 $MMW_ARTIFACT_DATA"
    return 1
  }

  if [ "$name_given" = false ]; then
    task_state="$(mmw_task_state)" || return 1
    IFS=' ' read -r task_kind task_branch task_head task_name task_extra <<< "$task_state"
    if [ "$task_kind" != "bound" ] || [ -z "$task_branch" ] || [ -z "$task_head" ] || \
      [ -z "$task_name" ] || [ -n "$task_extra" ]; then
      mmw_artifact_error "list 要 --name <工作名>，或在带工作名的任务 worktree 里运行"
      return 1
    fi
    name="$task_name"
  fi
  mmw_artifact_validate_segment "$name" "--name" || return 1

  if [ "$map_given" = true ] && [[ ! "$map" =~ ^[0-9]+$ ]]; then
    mmw_artifact_error "--map 只接收纯编号"
    return 1
  fi

  repo_root="$(mmw_repo_root)" || return 1

  # 先取 tracker 那一半。读不到就一条候选都不输出：调用方拿这份清单补必读材料
  # 声明，一份缺了结论评论的清单会让它以为 map 上没有已关闭的 decision ticket，
  # 于是一条上游结论都不补——那正是必读材料声明本身要修的失效。
  if [ "$map_given" = true ]; then
    children="$(mmw_issue_children_raw "$map")" || {
      mmw_artifact_error "读不到 map $map 的子 issue，清单会缺结论评论那一半"
      return 1
    }
  fi

  {
    for category in prototype research; do
      if ! record="$(jq -ce --arg category "$category" '.[$category]' "$MMW_ARTIFACT_DATA" 2>/dev/null)"; then
        mmw_artifact_error "找不到类别 $category 的产物落点数据"
        return 1
      fi
      root="$(jq -r '.root' <<< "$record")"
      category_dir="$repo_root/$root/$name"
      [ -d "$category_dir" ] || continue

      while IFS= read -r index; do
        relative="${index#"$category_dir"/}"
        relative="${relative%/README.md}"
        [ -n "$relative" ] || continue
        issue=""
        sub="$relative"
        if [[ "$relative" =~ ^issue-([0-9]+)/(.*)$ ]]; then
          issue="${BASH_REMATCH[1]}"
          sub="${BASH_REMATCH[2]}"
        fi
        [ -n "$sub" ] || continue
        mmw_artifact_validate_sub "$sub" > /dev/null 2>&1 || continue
        if [ -n "$issue" ]; then
          printf '%s\n' "- category=$category name=$name issue=$issue sub=$sub"
        else
          printf '%s\n' "- category=$category name=$name sub=$sub"
        fi
      done < <(find "$category_dir" -type f -name README.md -print | LC_ALL=C sort)
    done

    if [ "$map_given" = true ]; then
      while IFS= read -r ticket; do
        [ -n "$ticket" ] || continue
        if jq -e '(.state == "closed") and any(.labels[]?; .name | startswith("wayfinder:"))' \
          <<< "$ticket" > /dev/null; then
          number="$(jq -r '.number' <<< "$ticket")"
          title="$(jq -r '.title' <<< "$ticket")"
          printf '%s\n' "- issue=$number 结论评论 $title"
        fi
      done <<< "$children"
    fi
  } | LC_ALL=C sort
}

mmw_artifact_index() {
  if [ "$#" -ne 1 ]; then
    echo "mmw artifact: 用法是 mmw artifact index <类别>；类别只能是 adr 或 spec" >&2
    return 2
  fi

  python3 "$MMW_ROOT/cli/lib/artifact_index.py" "$1" "$(mmw_repo_root)" "$MMW_ARTIFACT_DATA"
}

mmw_artifact_check() {
  if [ "$#" -ne 0 ]; then
    usage_artifact
  fi

  python3 "$MMW_ROOT/cli/lib/artifact_check.py" \
    "$(mmw_repo_root)" "$MMW_ROOT/cli/mmw" "$MMW_ARTIFACT_DATA"
}

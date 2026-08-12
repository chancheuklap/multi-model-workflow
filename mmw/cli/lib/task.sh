#!/usr/bin/env bash
# 任务隔离：查状态、建 worktree、绑定分支、给出路径、清理。
#
# 切会话工作目录只有宿主工具做得到，脚本做不了。所以 new 只输出路径，切目录
# 那一步由技能用宿主自己的工具做。
#
# 落点一律在主仓库的 .worktrees/ 下，不管命令在哪棵树上执行——分支可以嵌
# 套，目录不嵌套。
#
# 清理一律用非强制形式：有未合并的改动时 git 自己会失败，那正是要的行为。

set -euo pipefail

mmw_task_read_work_name_at() {
  local dir="$1" name
  name="$(git -C "$dir" config --worktree --get mmw.task.work-name 2>/dev/null || true)"
  [ -n "$name" ] || return 1
  mmw_path_safe_segment "$name" "工作名" "mmw:" >/dev/null 2>&1 || return 1
  printf '%s\n' "$name"
}

mmw_task_current_bound_branch() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1

  local git_dir common_dir branch
  git_dir="$(git rev-parse --path-format=absolute --git-dir)"
  common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
  branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  [ "$git_dir" != "$common_dir" ] && [ -n "$branch" ] || return 1
  printf '%s\n' "$branch"
}

mmw_task_current_work_name() {
  mmw_task_current_bound_branch >/dev/null || return 1
  mmw_task_read_work_name_at .
}

mmw_task_parent_work_name() {
  local from="$1" parent
  parent="$(mmw_git_worktree_of "$from")" || return 1
  mmw_task_read_work_name_at "$parent"
}

mmw_task_store_binding() {
  local dir="$1" branch="$2" note="$3" name="$4"
  git -C "$dir" config extensions.worktreeConfig true || return 1
  git -C "$dir" config --worktree mmw.task.branch "$branch" || return 1
  git -C "$dir" config --worktree mmw.task.note "$note" || return 1
  git -C "$dir" config --worktree mmw.task.work-name "$name" || return 1
}

mmw_task_note_for_branch() {
  local branch="$1" commit subject note
  note="$(git config --worktree --get mmw.task.note 2>/dev/null || true)"
  if [ -n "$note" ]; then
    printf '%s\n' "$note"
    return 0
  fi

  while IFS= read -r commit; do
    subject="$(git show -s --format=%s "$commit")"
    [ "$subject" = "$branch" ] || continue
    [ -z "$(git diff-tree --no-commit-id --name-only -r "$commit")" ] || continue
    note="$(git show -s --format=%b "$commit")"
    if [ -n "$note" ]; then
      printf '%s\n' "$note"
      return 0
    fi
  done < <(git rev-list --reverse "$branch")

  printf '%s\n' "补写工作名"
}

mmw_task_quote() {
  local value="$1"
  value="${value//\'/\'\\\'\'}"
  printf "'%s'" "$value"
}

mmw_task_command_word() {
  local value="$1"
  if [[ "$value" =~ ^[A-Za-z0-9._/-]+$ ]]; then
    printf '%s' "$value"
  else
    mmw_task_quote "$value"
  fi
}

mmw_task_missing_work_name() {
  local branch="$1" note
  note="$(mmw_task_note_for_branch "$branch")"
  echo "mmw: 当前任务 worktree 缺少合法工作名。运行：mmw task bind $(mmw_task_command_word "$branch") $(mmw_task_quote "$note") --name <工作名>" >&2
}

mmw_task_state() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "outside"
    return 0
  fi

  local git_dir common_dir branch head
  git_dir="$(git rev-parse --path-format=absolute --git-dir)"
  common_dir="$(git rev-parse --path-format=absolute --git-common-dir)"
  branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  head="$(git rev-parse HEAD)"

  if [ "$git_dir" = "$common_dir" ]; then
    echo "local ${branch:-detached} ${head}"
  elif [ -z "$branch" ]; then
    echo "detached ${head}"
  else
    local name
    if ! name="$(mmw_task_read_work_name_at .)"; then
      mmw_task_missing_work_name "$branch"
      return 1
    fi
    echo "bound ${branch} ${head} ${name}"
  fi
}

# 只回答工作名，一行，不带别的字段。
#
# 有了 `state` 还要这一条，是因为工作名原来靠位置取：技能正文写「运行 `mmw task
# state`，取第四字段」。那句话是一份跨十二份技能源的合同——`state` 的输出形状一变，
# 十二处散着改，漏掉一处不会有任何机械校验发现。
#
# 这条命令让工作名有一个自己的出口。`state` 继续回答「当前处在哪一种位置」，技能
# 用它决定要不要建树；工作名从这里取。
#
# 不在已绑定的任务 worktree 里时非零退出，并说清当前是哪一种位置。调用方按 `state`
# 的第一个词选建树动作，不用解析这条命令的错误文本。
#
# 取值走 `mmw_task_current_work_name`，不去切 `state` 的输出——那样这条命令自己就
# 成了下一个位置型消费方，`state` 加一个字段又要跟着改。
mmw_task_name() {
  local name state
  if name="$(mmw_task_current_work_name)"; then
    printf '%s\n' "$name"
    return 0
  fi
  # 取不到有两种。分支绑好了、工作名没写的那一种由 `state` 自己报——它的错误文本里
  # 带着补写用的 `mmw task bind` 命令，这里不重写第二份。
  state="$(mmw_task_state)" || return 1
  echo "mmw: 当前位置是 $(printf '%s' "$state" | awk '{print $1}')，不是已绑定的任务 worktree，取不到工作名" >&2
  return 1
}

# 把宿主已经创建的 detached linked worktree 绑到任务分支。
# 用法：mmw_task_bind <完整分支名> <用户原话或任务目标> [--name <工作名>] [--from <预期基点>]
mmw_task_bind() {
  local branch="${1:-}" note="${2:-}" from="" name="" name_given=false
  shift 2 2>/dev/null || true
  while [ $# -gt 0 ]; do
    case "$1" in
      --name)
        name="${2:-}"
        [ -n "$name" ] || { echo "mmw: task bind 的 --name 要工作名" >&2; return 1; }
        [ "$name_given" = false ] || { echo "mmw: task bind 的 --name 只能给一次" >&2; return 1; }
        name_given=true
        shift 2
        ;;
      --from)
        from="${2:-}"
        [ -n "$from" ] || { echo "mmw: task bind 的 --from 要基点" >&2; return 1; }
        shift 2
        ;;
      *)
        echo "mmw: task bind 不认识 $1" >&2
        return 1
        ;;
    esac
  done
  [ -n "$branch" ] || { echo "mmw: task bind 要完整分支名" >&2; return 1; }
  [ -n "$note" ] || { echo "mmw: task bind 要用户原话或任务目标" >&2; return 1; }
  git check-ref-format --branch "$branch" >/dev/null 2>&1 || {
    echo "mmw: ${branch} 不是合法分支名" >&2
    return 1
  }
  if [ "$name_given" = true ]; then
    mmw_path_safe_segment "$name" "工作名" "mmw:" || return 1
  fi

  local current_branch parent_name current_name from_sha
  current_branch="$(mmw_task_current_bound_branch || true)"
  if [ -n "$current_branch" ]; then
    [ "$branch" = "$current_branch" ] || {
      echo "mmw: task bind 的分支必须是当前任务分支 ${current_branch}" >&2
      return 1
    }
    [ "$name_given" = true ] || {
      echo "mmw: 已绑定任务 worktree 的 task bind 要 --name <工作名>" >&2
      return 1
    }
    if [ -n "$from" ]; then
      from_sha="$(mmw_git_commit "$from")" || return 1
      if [ "$(git rev-parse HEAD)" != "$from_sha" ]; then
        echo "mmw: 任务 worktree 不在预期基点 ${from}" >&2
        return 1
      fi
    fi
    current_name="$(mmw_task_current_work_name || true)"
    if [ -n "$current_name" ] && [ "$name" != "$current_name" ]; then
      echo "mmw: 已绑定任务 worktree 的工作名是 ${current_name}，不能改成 ${name}" >&2
      return 1
    fi
    mmw_task_store_binding . "$branch" "$note" "$name" || {
      echo "mmw: 没有写入任务 worktree 的绑定信息" >&2
      return 1
    }
    printf '%s\t%s\n' "$branch" "$(git rev-parse HEAD)"
    return 0
  fi

  [ "$(mmw_task_state | awk '{print $1}')" = "detached" ] || {
    echo "mmw: task bind 只能在 detached linked worktree 执行" >&2
    return 1
  }
  [ "$(mmw_host)" = "codex" ] || {
    echo "mmw: task bind 只用于 Codex App 已创建的 detached worktree" >&2
    return 1
  }
  parent_name=""
  if [ -n "$from" ]; then
    parent_name="$(mmw_task_parent_work_name "$from" || true)"
  fi
  if [ -n "$parent_name" ]; then
    if [ "$name_given" = true ] && [ "$name" != "$parent_name" ]; then
      echo "mmw: 显式工作名必须与父任务 worktree 的工作名相同：${parent_name}" >&2
      return 1
    fi
    name="$parent_name"
  elif [ "$name_given" = false ]; then
    echo "mmw: task bind 找不到可继承的工作名，要 --name <工作名>" >&2
    return 1
  fi
  mmw_git_clean . "不绑定分支" || return 1
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    echo "mmw: ${branch} 已存在" >&2
    return 1
  fi
  if [ -n "$from" ]; then
    from_sha="$(mmw_git_commit "$from")" || return 1
    if [ "$(git rev-parse HEAD)" != "$from_sha" ]; then
      echo "mmw: detached worktree 不在预期基点 ${from}" >&2
      return 1
    fi
  fi

  git switch -c "$branch"
  git commit --allow-empty -q -m "$branch" -m "$note"
  mmw_task_store_binding . "$branch" "$note" "$name" || {
    echo "mmw: 没有写入任务 worktree 的绑定信息" >&2
    return 1
  }
  printf '%s\t%s\n' "$branch" "$(git rev-parse HEAD)"
}

mmw_result_verify() {
  local branch="${1:-}" reported_head="${2:-}" base="${3:-}"
  [ -n "$branch" ] && [ -n "$reported_head" ] && [ -n "$base" ] || {
    echo "mmw: result verify 要 <结果分支> <HEAD SHA> <基点 SHA>" >&2
    return 1
  }
  local actual_head reported_sha base_sha
  actual_head="$(mmw_git_commit "refs/heads/$branch")" || return 1
  reported_sha="$(mmw_git_commit "$reported_head")" || return 1
  base_sha="$(mmw_git_commit "$base")" || return 1

  [ "$actual_head" = "$reported_sha" ] || {
    echo "mmw: ${branch} 当前 HEAD ${actual_head} 与报告不一致" >&2
    return 1
  }
  mmw_git_descends_from "$actual_head" "$base_sha" "$branch" || return 1

  local worktree_path
  worktree_path="$(mmw_git_worktree_of "$branch")" || {
    echo "mmw: 找不到 ${branch} 对应的 worktree；先恢复拥有该分支的后台任务" >&2
    return 1
  }
  printf 'verified\t%s\t%s\t%s\t%s\n' \
    "$branch" "$actual_head" "$(git rev-list --count "${base_sha}..${actual_head}")" "$worktree_path"
}

mmw_result_integrate() {
  local branch="${1:-}" reported_head="${2:-}" base="${3:-}"
  mmw_result_verify "$branch" "$reported_head" "$base" >/dev/null || return 1
  local target
  target="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  [ -n "$target" ] || {
    echo "mmw: result integrate 要求当前 checkout 已绑定目标分支" >&2
    return 1
  }
  [ "$target" != "$branch" ] || {
    echo "mmw: 结果分支不能与当前目标分支相同：${branch}" >&2
    return 1
  }
  mmw_git_contains "$base" || {
    echo "mmw: 基点 ${base} 不在当前目标分支 ${target} 的历史中" >&2
    return 1
  }
  mmw_git_clean . "不集成结果" || return 1
  git merge --no-ff --no-edit "$branch"
  printf 'integrated\t%s\t%s\n' "$branch" "$(git rev-parse HEAD)"
}

mmw_task_dir() {
  local slug="$1"
  echo "$(mmw_main_root)/$(mmw_path_field worktrees)/$slug"
}

# 建 worktree、建分支、打一个记住用户原话的空提交。
#
# 用法：mmw_task_new <slug> [原话] [--name <工作名>] [--from <基点>]
#
# 不给 --from 就从当前 HEAD 分叉：在主仓库跑从主线分叉，在某棵 worktree 里跑
# 从那条分支分叉。要从别的分支分叉必须显式给 --from——`/mmw-wayfinder` 走链时
# 会话还在主仓库，而那条链要从 map 分支分叉，光靠当前 HEAD 取不到；`git
# checkout` 也切不过去，map 分支正被 map 的 worktree 占着。
#
# 同名分支已经存在时挂回它，不新建也不打空提交，--from 一并忽略——map 的
# worktree 被清理过之后要建回来，走的就是这条。
mmw_task_new() {
  local slug="" note="" from="" name="" name_given=false parent_name=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --name)
        name="${2:-}"
        if [ -z "$name" ]; then
          echo "mmw: task new 的 --name 要工作名" >&2
          return 1
        fi
        if [ "$name_given" = true ]; then
          echo "mmw: task new 的 --name 只能给一次" >&2
          return 1
        fi
        name_given=true
        shift 2
        ;;
      --from)
        from="${2:-}"
        if [ -z "$from" ]; then
          echo "mmw: --from 要跟一个分支名或提交" >&2
          return 1
        fi
        shift 2
        ;;
      -*)
        echo "mmw: task new 不认识 $1" >&2
        return 1
        ;;
      *)
        if [ -z "$slug" ]; then slug="$1"; else note="$1"; fi
        shift
        ;;
    esac
  done

  if [ -z "$slug" ]; then
    echo "mmw: task new 要一个 slug" >&2
    return 1
  fi
  if [ "$name_given" = true ]; then
    mmw_path_safe_segment "$name" "工作名" "mmw:" || return 1
  fi

  local root dir base
  root="$(mmw_main_root)"
  dir="$(mmw_task_dir "$slug")"

  if [ -e "$dir" ]; then
    echo "mmw: ${dir} 已经存在" >&2
    return 1
  fi

  if git show-ref --quiet --verify "refs/heads/$slug"; then
    [ "$name_given" = true ] || {
      echo "mmw: 挂回已有任务分支要 --name <工作名>" >&2
      return 1
    }
    git -C "$root" worktree add "$dir" "$slug" >&2
    mmw_task_store_binding "$dir" "$slug" "$note" "$name" || {
      echo "mmw: 没有写入任务 worktree 的绑定信息" >&2
      return 1
    }
    echo "$dir"
    return 0
  fi

  if [ -n "$from" ]; then
    parent_name="$(mmw_task_parent_work_name "$from" || true)"
  else
    parent_name="$(mmw_task_current_work_name || true)"
  fi
  if [ -n "$parent_name" ]; then
    if [ "$name_given" = true ] && [ "$name" != "$parent_name" ]; then
      echo "mmw: 显式工作名必须与父任务 worktree 的工作名相同：${parent_name}" >&2
      return 1
    fi
    name="$parent_name"
  elif [ "$name_given" = false ]; then
    echo "mmw: task new 找不到可继承的工作名，要 --name <工作名>" >&2
    return 1
  fi

  if [ -n "$from" ]; then
    mmw_git_commit "$from" >/dev/null || return 1
    base="$from"
  else
    # 当前 HEAD 要在这里取出来再传给 git -C "$root"。不传的话 worktree add 用
    # 的是主仓库的 HEAD，在任务 worktree 里再开一棵就会错分叉到主线。
    base="$(git rev-parse HEAD)"
  fi

  git -C "$root" worktree add -b "$slug" "$dir" "$base" >&2
  if [ -n "$note" ]; then
    git -C "$dir" commit --allow-empty -q -m "$slug" -m "$note"
  fi
  mmw_task_store_binding "$dir" "$slug" "$note" "$name" || {
    echo "mmw: 没有写入任务 worktree 的绑定信息" >&2
    return 1
  }
  echo "$dir"
}

mmw_task_cleanup() {
  local slug="$1"
  local root dir onto here
  root="$(mmw_main_root)"
  dir="$(mmw_task_dir "$slug")"

  if ! git -C "$root" show-ref --quiet --verify "refs/heads/$slug"; then
    echo "mmw: 没有 ${slug} 这条分支" >&2
    return 1
  fi

  # 站在自己那棵树里删自己，会把脚下的目录一起删掉，而这条分支上的提交多半还
  # 没合进任何地方。git 不挡这个动作，下面那条合并判据也挡不住——一条分支永远
  # 是它自己的祖先，判据恒真。所以在这里显式拒绝。
  here="$(git rev-parse --show-toplevel)"
  if [ "$here" = "$dir" ]; then
    echo "mmw: 现在就在 ${slug} 这棵 worktree 里，先切到别处再清理" >&2
    return 1
  fi

  # 合没合并要在动 worktree 之前判。反过来会留下半完成状态：worktree 已经删
  # 掉、分支还在，而命令报的是失败——人看到失败，以为什么都没发生。
  #
  # 判据看的是调用者当前所在的分支，不是主仓库 checkout 的那条。理由与 task new
  # 取 base 的那一处相同：在任务 worktree 里跑时，主仓库停在哪条分支纯属偶然。
  # 结果分支合进的是当前任务分支，拿主仓库 HEAD 判会把该删的判成不该删。
  #
  # 删除也留在当前位置执行。git branch -d 自带的已合并判据同样看执行位置的
  # HEAD，放回主仓库跑会被它再挡一次，即便上面这条判据已经通过。
  onto="$(git rev-parse --abbrev-ref HEAD)"
  if ! mmw_git_contains "$slug"; then
    echo "mmw: ${slug} 还没合并进 ${onto}，不清理" >&2
    return 1
  fi

  # 这一条是非强制形式：worktree 里有未提交改动时 git 会拒绝，命令带着非零退
  # 出码停在这里，由人决定要不要真的丢掉。
  git worktree remove "$dir"
  git branch -d "$slug"
}

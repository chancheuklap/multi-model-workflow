#!/usr/bin/env bash
# 护栏语义。跑法：bash mmw/cli/tests/guardrails.sh
#
# 这个 CLI 的准入判据第 2 条说，护栏是「在破坏性动作前做 agent 容易偷懒跳过的
# 完整性校验」。护栏全是拒绝路径，日常用法永远不经过它们：删掉一条，所有正常
# 操作照样跑通，直到某天它该拦没拦——那天丢的是用户还没合并的工作。
#
# 所以每条用例断言两件事：命令拒绝了，而且**破坏没有发生**。只看退出码不够，
# 一条命令完全可以先删掉 worktree 再报错。
#
# 用例跑真命令、真 git 仓库，只在仓库这个系统边界上准备状态，不给任何内部函数
# 打桩。断言的预期值是仓库的实际状态，不是把实现再算一遍。
#
# 计数必须留在这一层的 shell 里。用例曾经包在 ( cd 仓库 && … ) 子 shell 里跑，
# PASS 和 FAIL 加在子 shell 的副本上，父 shell 收到的永远是 0——失败一条也报
# 不出来，整份测试恒绿。换目录的事交给 expect_* 内部的命令替换去做。

set -uo pipefail

MMW_TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$MMW_TESTS_DIR/../mmw"
[ -x "$MMW" ] || { echo "找不到 mmw：$MMW" >&2; exit 1; }

PASS=0
FAIL=0
WORKBENCH="$(mktemp -d "${TMPDIR:-/tmp}/mmw-guardrails.XXXXXX")"
trap 'rm -rf "$WORKBENCH"' EXIT

# 一个一次性仓库：一条 main、一个初始提交、.worktrees 已忽略。
# 回显仓库路径。任务 worktree 落在 .worktrees/ 下，不忽略的话主检出永远不干净，
# 「工作区干净」那几条用例就永远是假的。
fresh_repo() {
  local repo
  repo="$(mktemp -d "$WORKBENCH/repo.XXXXXX")"
  git init -q -b main "$repo"
  git -C "$repo" config user.name "MMW Guardrails"
  git -C "$repo" config user.email "guardrails@example.invalid"
  printf '.worktrees/\n' > "$repo/.gitignore"
  printf '{"paths":{"worktrees":".worktrees","scratch":".scratch","reviews":".reviews","release":".release"}}\n' \
    > "$repo/.mmw.json"
  printf 'seed\n' > "$repo/seed.txt"
  git -C "$repo" add .gitignore .mmw.json seed.txt
  git -C "$repo" commit -q -m "seed"
  printf '%s\n' "$repo"
}

report() {
  local outcome="$1" name="$2" detail="${3:-}"
  if [ "$outcome" = pass ]; then
    PASS=$((PASS + 1))
    printf '  ok   %s\n' "$name"
  else
    FAIL=$((FAIL + 1))
    printf '  FAIL %s\n' "$name"
    [ -n "$detail" ] && printf '%s\n' "$detail" | sed 's/^/         /'
  fi
  return 0
}

# 期望命令成功。用法：expect_ok <用例名> <在哪个目录跑> <命令...>
expect_ok() {
  local name="$1" dir="$2"; shift 2
  local out
  if out="$(cd "$dir" && "$@" 2>&1)"; then
    report pass "$name"
  else
    report fail "$name" "期望成功，实际非零：$out"
  fi
}

# 期望命令拒绝。用法：expect_deny <用例名> <在哪个目录跑> <命令...>
expect_deny() {
  local name="$1" dir="$2"; shift 2
  local out
  if out="$(cd "$dir" && "$@" 2>&1)"; then
    report fail "$name" "期望拒绝，实际成功：$out"
  else
    report pass "$name"
  fi
}

# 破坏有没有发生。用法：expect_state <用例名> <期望的状态> <断言命令...>
# 断言命令成立记 pass。用来说明拒绝之后分支还在、合并没做成。
expect_state() {
  local name="$1" expectation="$2"; shift 2
  if "$@" >/dev/null 2>&1; then
    report pass "${name} —— ${expectation}"
  else
    report fail "${name}" "期望：${expectation}，实际不成立"
  fi
}

# setup 步骤里跑 mmw 也必须显式说明在哪个仓库跑。裸着调用会落在这个脚本自己的
# 当前目录上，把任务 worktree 建进 MMW 源码仓库——这件事真的发生过一次。
# 用法：mmw_in <仓库> <MMW_HOST 值> <参数...>
mmw_in() {
  local dir="$1" host="$2"; shift 2
  ( cd "$dir" && MMW_HOST="$host" "$MMW" "$@" )
}

branch_exists() { git -C "$1" show-ref --verify --quiet "refs/heads/$2"; }
branch_absent() { ! git -C "$1" show-ref --verify --quiet "refs/heads/$2"; }
merge_count_is() { [ "$(git -C "$1" rev-list --count --merges HEAD)" = "$2" ]; }

# 造一条从 base 长出新提交的任务分支，回显它的 HEAD。
grow_branch() {
  local repo="$1" branch="$2" wt="$1/.worktrees/$2"
  git -C "$repo" branch -q "$branch"
  git -C "$repo" worktree add -q "$wt" "$branch"
  printf '%s\n' "$branch" > "$wt/$branch.txt"
  git -C "$wt" add "$branch.txt"
  git -C "$wt" commit -q -m "$branch"
  git -C "$wt" rev-parse HEAD
}

# ---------------------------------------------------------------- result verify

suite_result_verify() {
  echo "mmw result verify"
  local repo base new unrelated
  repo="$(fresh_repo)"
  base="$(git -C "$repo" rev-parse HEAD)"
  new="$(grow_branch "$repo" feat)"

  expect_ok "报告与实际一致时通过" "$repo" \
    env MMW_HOST=codex "$MMW" result verify feat "$new" "$base"
  expect_deny "报告的 HEAD 与分支实际 HEAD 不符" "$repo" \
    env MMW_HOST=codex "$MMW" result verify feat "$base" "$base"
  expect_deny "结果分支不存在" "$repo" \
    env MMW_HOST=codex "$MMW" result verify nosuch "$new" "$base"
  expect_deny "报告的 HEAD 不是这个仓库里的提交" "$repo" \
    env MMW_HOST=codex "$MMW" result verify feat 0000000 "$base"
  expect_deny "基点不是这个仓库里的提交" "$repo" \
    env MMW_HOST=codex "$MMW" result verify feat "$new" 0000000

  git -C "$repo" branch -q stalled "$base"
  git -C "$repo" worktree add -q "$repo/.worktrees/stalled" stalled
  expect_deny "分支停在基点上，没有产生新提交" "$repo" \
    env MMW_HOST=codex "$MMW" result verify stalled "$base" "$base"

  # 另起一条与 feat 无关的线，拿它当基点：feat 不是从这里长出来的。
  unrelated="$(grow_branch "$repo" elsewhere)"
  expect_deny "结果分支不是从给定基点分叉的" "$repo" \
    env MMW_HOST=codex "$MMW" result verify feat "$new" "$unrelated"

  # 分支存在、SHA 都对，但那棵 worktree 已经被撤掉：报告无处可读。
  git -C "$repo" worktree remove "$repo/.worktrees/feat"
  expect_deny "分支的 worktree 已经不在时拒绝" "$repo" \
    env MMW_HOST=codex "$MMW" result verify feat "$new" "$base"
}

# ------------------------------------------------------------- result integrate

suite_result_integrate() {
  echo "mmw result integrate"
  local repo base new orphan
  repo="$(fresh_repo)"
  base="$(git -C "$repo" rev-parse HEAD)"
  new="$(grow_branch "$repo" feat)"

  printf 'dirty\n' > "$repo/dirty.txt"
  expect_deny "工作区不干净时不集成" "$repo" \
    env MMW_HOST=codex "$MMW" result integrate feat "$new" "$base"
  expect_state "工作区不干净时不集成" "没有产生合并提交" \
    merge_count_is "$repo" 0
  rm -f "$repo/dirty.txt"

  expect_deny "结果分支与当前分支相同时不集成" "$repo" \
    env MMW_HOST=codex "$MMW" result integrate main "$(git -C "$repo" rev-parse HEAD)" "$base"

  # 拿 feat 自己的 HEAD 当基点：它不在 main 的历史里。
  orphan="$new"
  expect_deny "报告的基点不在当前分支历史里时不集成" "$repo" \
    env MMW_HOST=codex "$MMW" result integrate feat "$new" "$orphan"
  expect_state "报告的基点不在当前分支历史里时不集成" "仍然没有合并提交" \
    merge_count_is "$repo" 0

  expect_ok "干净且基点在历史里时集成" "$repo" \
    env MMW_HOST=codex "$MMW" result integrate feat "$new" "$base"
  expect_state "干净且基点在历史里时集成" "留下一个 --no-ff 合并提交" \
    merge_count_is "$repo" 1
}

# ---------------------------------------------------------------- task cleanup

suite_task_cleanup() {
  echo "mmw task cleanup"
  local repo task_wt
  repo="$(fresh_repo)"

  grow_branch "$repo" unmerged >/dev/null
  expect_deny "分支还没合并进当前分支时不清理" "$repo" \
    env MMW_HOST=pi "$MMW" task cleanup unmerged
  expect_state "分支还没合并进当前分支时不清理" "分支还在" \
    branch_exists "$repo" unmerged
  expect_state "分支还没合并进当前分支时不清理" "worktree 还在" \
    test -d "$repo/.worktrees/unmerged"

  expect_deny "分支不存在时报错" "$repo" \
    env MMW_HOST=pi "$MMW" task cleanup nosuch

  grow_branch "$repo" merged >/dev/null
  git -C "$repo" merge -q --no-ff --no-edit merged
  expect_ok "已经合并进当前分支时允许清理" "$repo" \
    env MMW_HOST=pi "$MMW" task cleanup merged
  expect_state "已经合并进当前分支时允许清理" "分支和 worktree 都已删掉" \
    branch_absent "$repo" merged

  # 上面几条都站在主仓库里跑。那里「当前分支」和「主仓库 checkout 的分支」是同
  # 一条，判据取哪一个都过，分不出对错。下面几条站在任务 worktree 里跑：主仓库
  # 停在 main，结果分支只合进任务分支，判据必须看任务分支才判得对。
  task_wt="$repo/.worktrees/task"
  grow_branch "$repo" task >/dev/null

  mmw_in "$task_wt" pi task new landed --name cleanup-work >/dev/null
  git -C "$repo/.worktrees/landed" commit -q --allow-empty -m "landed work"
  git -C "$task_wt" merge -q --no-ff --no-edit landed
  expect_ok "在任务 worktree 里，已经合并进任务分支时允许清理" "$task_wt" \
    env MMW_HOST=pi "$MMW" task cleanup landed
  expect_state "在任务 worktree 里，已经合并进任务分支时允许清理" "分支和 worktree 都已删掉" \
    branch_absent "$repo" landed

  mmw_in "$task_wt" pi task new adrift --name cleanup-work >/dev/null
  git -C "$repo/.worktrees/adrift" commit -q --allow-empty -m "adrift work"
  expect_deny "在任务 worktree 里，还没合并进任务分支时不清理" "$task_wt" \
    env MMW_HOST=pi "$MMW" task cleanup adrift
  expect_state "在任务 worktree 里，还没合并进任务分支时不清理" "分支还在" \
    branch_exists "$repo" adrift

  # 一条分支永远是它自己的祖先，合并判据在这里恒真；git 也不挡，它会把调用者脚
  # 下的目录真的删掉。挡这一下的只能是显式检查。
  expect_deny "站在自己那棵 worktree 里不清理自己" "$repo/.worktrees/adrift" \
    env MMW_HOST=pi "$MMW" task cleanup adrift
  expect_state "站在自己那棵 worktree 里不清理自己" "worktree 还在" \
    test -d "$repo/.worktrees/adrift"
}

# -------------------------------------------------------------------- task new

suite_task_state() {
  echo "mmw task state"
  local repo detached expected_state
  repo="$(fresh_repo)"

  expect_state "仓库外输出 outside" "状态行只有 outside" \
    test "$(cd "$WORKBENCH" && MMW_HOST=pi "$MMW" task state)" = outside
  expected_state="local main $(git -C "$repo" rev-parse HEAD)"
  expect_state "主检出输出 local" "状态行带分支和 HEAD" \
    test "$(cd "$repo" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"
  detached="$repo/.worktrees/state-detached"
  git -C "$repo" worktree add -q --detach "$detached" HEAD
  expected_state="detached $(git -C "$detached" rev-parse HEAD)"
  expect_state "detached linked worktree 输出 detached" "状态行带 HEAD" \
    test "$(cd "$detached" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"
}

suite_task_new() {
  echo "mmw task new"
  local repo before expected_state
  repo="$(fresh_repo)"

  expect_deny "普通检出缺工作名时不建任务分支" "$repo" \
    env MMW_HOST=pi "$MMW" task new nameless "没有工作名"
  expect_state "普通检出缺工作名时不建任务分支" "分支没有建出来" \
    branch_absent "$repo" nameless

  expect_ok "建一条新任务分支" "$repo" \
    env MMW_HOST=pi "$MMW" task new first "第一条" --name delivery-name
  expected_state="bound first $(git -C "$repo/.worktrees/first" rev-parse HEAD) delivery-name"
  expect_state "新任务状态输出工作名" "bound 的第四字段是工作名" \
    test "$(cd "$repo/.worktrees/first" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"
  expect_deny "目录已经存在时不覆盖" "$repo" \
    env MMW_HOST=pi "$MMW" task new first "重复的" --name delivery-name
  expect_deny "--from 给了不存在的基点时报错" "$repo" \
    env MMW_HOST=pi "$MMW" task new second "第二条" --name second-name --from nosuchref
  expect_state "--from 给了不存在的基点时报错" "分支没有建出来" \
    branch_absent "$repo" second

  # 同名分支已存在、worktree 被清掉过：挂回去，不再打一个新的空提交。
  before="$(git -C "$repo" rev-list --count first)"
  git -C "$repo" worktree remove "$repo/.worktrees/first"
  expect_deny "已有任务分支挂回时缺工作名不添加 worktree" "$repo" \
    env MMW_HOST=pi "$MMW" task new first "再来一次"
  expect_state "已有任务分支挂回时缺工作名不添加 worktree" "worktree 没有建出来" \
    test ! -e "$repo/.worktrees/first"
  expect_ok "同名分支已存在时挂回那条分支" "$repo" \
    env MMW_HOST=pi "$MMW" task new first "再来一次" --name rebuilt-name
  expect_state "同名分支已存在时挂回那条分支" "没有多打一个空提交" \
    test "$(git -C "$repo" rev-list --count first)" -eq "$before"
  expected_state="bound first $(git -C "$repo/.worktrees/first" rev-parse HEAD) rebuilt-name"
  expect_state "挂回任务分支后重新保存工作名" "bound 的第四字段是重新给的工作名" \
    test "$(cd "$repo/.worktrees/first" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"

  expect_ok "工作名允许点、下划线和连字符" "$repo" \
    env MMW_HOST=pi "$MMW" task new safe-name "安全路径段" --name safe.name_with-tail
  expect_deny "工作名拒绝大写字母" "$repo" \
    env MMW_HOST=pi "$MMW" task new upper-name "大写" --name Upper
  expect_state "工作名拒绝大写字母" "分支没有建出来" \
    branch_absent "$repo" upper-name
  expect_deny "工作名拒绝非法首字符" "$repo" \
    env MMW_HOST=pi "$MMW" task new dash-name "连字符开头" --name -dash
  expect_state "工作名拒绝非法首字符" "分支没有建出来" \
    branch_absent "$repo" dash-name
  expect_deny "工作名拒绝斜杠" "$repo" \
    env MMW_HOST=pi "$MMW" task new slash-name "斜杠" --name bad/name
  expect_state "工作名拒绝斜杠" "分支没有建出来" \
    branch_absent "$repo" slash-name

  expect_ok "当前任务 worktree 的子任务继承工作名" "$repo/.worktrees/safe-name" \
    env MMW_HOST=pi "$MMW" task new child-name "子任务"
  expected_state="bound child-name $(git -C "$repo/.worktrees/child-name" rev-parse HEAD) safe.name_with-tail"
  expect_state "当前任务 worktree 的子任务继承工作名" "bound 的第四字段沿用父工作名" \
    test "$(cd "$repo/.worktrees/child-name" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"

  expect_ok "--from 父任务分支时继承工作名" "$repo" \
    env MMW_HOST=pi "$MMW" task new from-parent "指定父任务" --from safe-name
  expected_state="bound from-parent $(git -C "$repo/.worktrees/from-parent" rev-parse HEAD) safe.name_with-tail"
  expect_state "--from 父任务分支时继承工作名" "bound 的第四字段沿用父工作名" \
    test "$(cd "$repo/.worktrees/from-parent" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"
  expect_deny "显式工作名不能改变父任务工作名" "$repo" \
    env MMW_HOST=pi "$MMW" task new changed-parent "错误名字" --name changed-name --from safe-name
  expect_state "显式工作名不能改变父任务工作名" "分支没有建出来" \
    branch_absent "$repo" changed-parent
}

# ------------------------------------------------------------------- task bind

suite_task_bind() {
  echo "mmw task bind"
  local repo base det legacy legacy_head legacy_count legacy_index legacy_worktree state_out state_err expected_state
  repo="$(fresh_repo)"
  base="$(git -C "$repo" rev-parse HEAD)"

  expect_deny "在已绑定分支的检出上不允许 bind" "$repo" \
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标"

  # 让 main 往前走一步，detached worktree 留在 base：--from main 才是真的不符。
  printf 'moved\n' > "$repo/moved.txt"
  git -C "$repo" add moved.txt
  git -C "$repo" commit -q -m "main 前进一步"

  det="$repo/.worktrees/detached"
  git -C "$repo" worktree add -q --detach "$det" "$base"

  expect_deny "缺任务目标时不 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind codex/x
  expect_deny "分支名不合法时不 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind "有空格的 名字" "任务目标"
  expect_deny "--from 与当前 HEAD 不符时不 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标" --from main
  expect_state "--from 与当前 HEAD 不符时不 bind" "分支没有建出来" \
    branch_absent "$repo" codex/x

  printf 'dirty\n' > "$det/dirty.txt"
  expect_deny "工作区不干净时不 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标"
  expect_state "工作区不干净时不 bind" "分支没有建出来" \
    branch_absent "$repo" codex/x
  rm -f "$det/dirty.txt"

  expect_ok "干净的 detached worktree 允许 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标" --name codex-work
  expect_deny "分支已经存在时不 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标"

  legacy="$repo/.worktrees/legacy"
  git -C "$repo" branch -q legacy "$base"
  git -C "$repo" worktree add -q "$legacy" legacy
  git -C "$legacy" commit --allow-empty -q -m legacy -m "旧任务目标"
  state_out="$WORKBENCH/legacy-state.out"
  state_err="$WORKBENCH/legacy-state.err"
  if (cd "$legacy" && MMW_HOST=pi "$MMW" task state) >"$state_out" 2>"$state_err"; then
    report fail "旧绑定缺工作名时 task state 拒绝" "期望非零，实际成功"
  else
    report pass "旧绑定缺工作名时 task state 拒绝"
  fi
  expect_state "旧绑定缺工作名时 task state 拒绝" "标准输出为空" test ! -s "$state_out"
  expect_state "旧绑定缺工作名时 task state 拒绝" "诊断点名实际任务分支" \
    grep -F "mmw task bind legacy '旧任务目标' --name <工作名>" "$state_err"

  expect_deny "补写时分支必须等于当前任务分支" "$legacy" \
    env MMW_HOST=pi "$MMW" task bind other "旧任务目标" --name legacy-work
  expect_deny "补写时必须显式给工作名" "$legacy" \
    env MMW_HOST=pi "$MMW" task bind legacy "旧任务目标"
  expect_deny "补写时拒绝非法工作名" "$legacy" \
    env MMW_HOST=pi "$MMW" task bind legacy "旧任务目标" --name Legacy

  legacy_head="$(git -C "$legacy" rev-parse HEAD)"
  legacy_count="$(git -C "$legacy" rev-list --count HEAD)"
  legacy_index="$(git -C "$legacy" diff --cached --binary)"
  legacy_worktree="$(git -C "$legacy" status --porcelain)"
  expect_ok "Pi 能在旧绑定上补写工作名" "$legacy" \
    env MMW_HOST=pi "$MMW" task bind legacy "旧任务目标" --name legacy-work
  expected_state="bound legacy ${legacy_head} legacy-work"
  expect_state "Pi 能在旧绑定上补写工作名" "状态读出补写的工作名" \
    test "$(cd "$legacy" && MMW_HOST=pi "$MMW" task state)" = "$expected_state"
  expect_state "Pi 能在旧绑定上补写工作名" "任务分支不变" \
    test "$(git -C "$legacy" branch --show-current)" = legacy
  expect_state "Pi 能在旧绑定上补写工作名" "HEAD 不变" \
    test "$(git -C "$legacy" rev-parse HEAD)" = "$legacy_head"
  expect_state "Pi 能在旧绑定上补写工作名" "提交数不变" \
    test "$(git -C "$legacy" rev-list --count HEAD)" = "$legacy_count"
  expect_state "Pi 能在旧绑定上补写工作名" "索引不变" \
    test "$(git -C "$legacy" diff --cached --binary)" = "$legacy_index"
  expect_state "Pi 能在旧绑定上补写工作名" "工作区不变" \
    test "$(git -C "$legacy" status --porcelain)" = "$legacy_worktree"

  legacy="$repo/.worktrees/legacy-codex"
  git -C "$repo" branch -q legacy-codex "$base"
  git -C "$repo" worktree add -q "$legacy" legacy-codex
  expect_ok "Codex App 能在旧绑定上补写工作名" "$legacy" \
    env MMW_HOST=codex "$MMW" task bind legacy-codex "Codex 旧任务目标" --name codex-legacy-work
  expected_state="bound legacy-codex $(git -C "$legacy" rev-parse HEAD) codex-legacy-work"
  expect_state "Codex App 能在旧绑定上补写工作名" "状态读出补写的工作名" \
    test "$(cd "$legacy" && MMW_HOST=codex "$MMW" task state)" = "$expected_state"
}

# -------------------------------------------------------------------- dispatch

suite_dispatch() {
  echo "mmw dispatch（可写角色）"
  local repo task
  repo="$(fresh_repo)"
  task="$WORKBENCH/task.md"
  printf '任务表\n' > "$task"

  expect_deny "可写角色没给 --cwd" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task "$task"
  expect_deny "--cwd 不是 git 工作树" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task "$task" --cwd "$WORKBENCH"
  expect_deny "--cwd 是主检出而不是任务 worktree" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task "$task" --cwd "$repo"

  # setup 失败就让它响。吞掉的话，下一条用例会拿一个不存在的目录去测，
  # dispatch 照样拒绝，用例照样绿——测到的却是「目录不存在」，不是「不干净」。
  mmw_in "$repo" pi task new dispatchable "派活用" --name dispatchable-work >/dev/null
  expect_ok "干净的任务 worktree 可以派活" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task "$task" \
      --cwd "$repo/.worktrees/dispatchable"
  printf 'dirty\n' > "$repo/.worktrees/dispatchable/dirty.txt"
  expect_deny "任务 worktree 工作区不干净" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task "$task" \
      --cwd "$repo/.worktrees/dispatchable"
}

# -------------------------------------------------------------- gitfacts 谓词

suite_gitfacts() {
  echo "gitfacts 谓词"
  # shellcheck source=../lib/gitfacts.sh
  . "$MMW_TESTS_DIR/../lib/gitfacts.sh"
  local notrepo repo
  notrepo="$(mktemp -d "$WORKBENCH/notrepo.XXXXXX")"
  expect_deny "git 读不到状态时不得判成干净" "$notrepo" \
    mmw_git_clean "$notrepo" "测试用"

  repo="$(fresh_repo)"
  expect_ok "干净的仓库判成干净" "$repo" \
    mmw_git_clean "$repo" "测试用"
  printf 'x\n' > "$repo/x.txt"
  expect_deny "有未跟踪文件时判成不干净" "$repo" \
    mmw_git_clean "$repo" "测试用"
}

suite_result_verify
suite_result_integrate
suite_task_cleanup
suite_task_state
suite_task_new
suite_task_bind
suite_dispatch
suite_gitfacts

printf '\n通过 %d，失败 %d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]

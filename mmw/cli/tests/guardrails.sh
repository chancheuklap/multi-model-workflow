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
  # 与 mmw init 写的 gitignore 保持一致（见 lib/init.sh 的 mmw_init_gitignore）。
  # 少写 .scratch/ 会让这些一次性仓库跟真实目标仓库行为不同：派发往 scratch 写进度
  # 日志和句柄文件，那时工作区会被判成不干净，下一次派发被护栏拒掉。
  printf '%s\n' '.worktrees/' '.scratch/' '.reviews/' '.release/' > "$repo/.gitignore"
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

# 在期限内跑完一条命令。用法：run_with_deadline <秒> <命令...>
#
# 不用 `timeout`：它在 macOS 上不是自带的，测试入口不该要求装 coreutils。
# 超期返回 124，与 `timeout` 的约定一致。
run_with_deadline() {
  local secs="$1"; shift
  "$@" &
  local pid=$! waited=0
  while kill -0 "$pid" 2>/dev/null && [ "$waited" -lt "$secs" ]; do
    sleep 1
    waited=$((waited + 1))
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
    return 124
  fi
  wait "$pid"
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

suite_task_name() {
  echo "mmw task name"
  local repo tree detached out
  repo="$(fresh_repo)"
  mmw_in "$repo" pi task new named-work "取工作名" --name work-name-here >/dev/null
  tree="$repo/.worktrees/named-work"

  expect_state "已绑定的任务 worktree 输出工作名" "输出只有工作名这一行" \
    test "$(cd "$tree" && MMW_HOST=pi "$MMW" task name)" = work-name-here

  expect_deny "主检出取不到工作名" "$repo" \
    env MMW_HOST=pi "$MMW" task name
  expect_deny "仓库外取不到工作名" "$WORKBENCH" \
    env MMW_HOST=pi "$MMW" task name

  detached="$repo/.worktrees/name-detached"
  git -C "$repo" worktree add -q --detach "$detached" HEAD
  expect_deny "detached 树取不到工作名" "$detached" \
    env MMW_HOST=pi "$MMW" task name

  # 绑好了分支、工作名没写的那一种要给出补写命令。这条错误由 state 拥有，
  # name 不重写第二份；断言它确实传了出来。
  git -C "$tree" config --worktree --unset mmw.task.work-name
  out="$WORKBENCH/task-name-missing.err"
  (cd "$tree" && MMW_HOST=pi "$MMW" task name) 2> "$out" || true
  expect_state "缺工作名时给出补写命令" "错误里带 mmw task bind" \
    grep -qF "mmw task bind" "$out"

  expect_deny "缺工作名时非零退出" "$tree" \
    env MMW_HOST=pi "$MMW" task name
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
  local repo base det legacy legacy_head legacy_count legacy_index legacy_worktree state_out state_err expected_state work_name_err
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
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标" --name aaa
  work_name_err="$WORKBENCH/detached-work-name.err"
  if (cd "$det" && MMW_HOST=codex "$MMW" task bind codex/x "任务目标" --name bbb) \
      >"$work_name_err" 2>&1; then
    report fail "已绑定任务 worktree 不改写已经确定的工作名" "期望拒绝，实际成功"
  else
    report pass "已绑定任务 worktree 不改写已经确定的工作名"
  fi
  expect_state "已绑定任务 worktree 不改写已经确定的工作名" "错误说明原工作名" \
    grep -F "aaa" "$work_name_err"
  expect_state "已绑定任务 worktree 不改写已经确定的工作名" "错误说明传入工作名" \
    grep -F "bbb" "$work_name_err"
  expect_state "已绑定任务 worktree 不改写已经确定的工作名" "工作名保持不变" \
    test "$(cd "$det" && MMW_HOST=codex "$MMW" task state)" = "bound codex/x $(git -C "$det" rev-parse HEAD) aaa"
  expect_ok "已绑定任务 worktree 用原工作名可以重复 bind" "$det" \
    env MMW_HOST=codex "$MMW" task bind codex/x "任务目标" --name aaa
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

  expect_deny "已绑定任务 worktree 的 --from 与 HEAD 不符时拒绝" "$legacy" \
    env MMW_HOST=pi "$MMW" task bind legacy "旧任务目标" --name legacy-work --from main
  expect_ok "已绑定任务 worktree 的 --from 与 HEAD 相符时允许重复 bind" "$legacy" \
    env MMW_HOST=pi "$MMW" task bind legacy "旧任务目标" --name legacy-work --from "$legacy_head"

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

# 假 codex 与假 date，两个派发用例共用一份。
#
# 只写一份的理由跟 adapter 里 MCP 配置只写一份是同一条：假 codex 模拟的是真 codex 的
# 参数合同（`--json` 把事件流打到标准输出、`-o` 把最终消息写进文件）。两份假 codex
# 就是两处维护，其中一处漂了不会有人发现。
#
# 输出到标准输出的是这个目录路径，调用方接住它当 PATH 前缀。
#
# 行为由环境变量控制：
#   FAKE_CODEX_STDIN      必填。把收到的标准输入原样存到这个文件
#   FAKE_CODEX_REPORT     写进 `-o` 指向的文件的报告正文
#   FAKE_CODEX_PROGRESS   写到标准错误的进度行
#   FAKE_CODEX_THREAD_ID  `thread.started` 事件里的 thread_id
#   FAKE_CODEX_NO_THREAD  设成 1 就不发 `thread.started`，模拟取不到句柄
#   FAKE_CODEX_EXIT       退出码
#   CODEX_STUB_ARGV       设了就把 argv 一行一个记进这个文件，供断言检查传参顺序
make_fake_codex() {
  local fake_bin="$WORKBENCH/fake-bin"
  mkdir -p "$fake_bin"
  cat > "$fake_bin/codex" <<'FAKE_CODEX'
#!/usr/bin/env bash
set -eu
if [ -n "${CODEX_STUB_ARGV:-}" ]; then
  printf '%s\n' "$@" > "$CODEX_STUB_ARGV"
fi
cat > "$FAKE_CODEX_STDIN"
report=""
prev=""
for arg in "$@"; do
  case "$prev" in
    -o|--output-last-message) report="$arg" ;;
  esac
  prev="$arg"
done
if [ -n "$report" ]; then
  printf '%s\n' "${FAKE_CODEX_REPORT:-fake report}" > "$report"
fi
printf '%s\n' "${FAKE_CODEX_PROGRESS:-fake progress}" >&2
if [ "${FAKE_CODEX_NO_THREAD:-}" != "1" ]; then
  printf '{"type":"thread.started","thread_id":"%s"}\n' \
    "${FAKE_CODEX_THREAD_ID:-fake-thread-1}"
fi
printf '{"type":"turn.completed"}\n'
exit "${FAKE_CODEX_EXIT:-0}"
FAKE_CODEX
  chmod +x "$fake_bin/codex"
  cat > "$fake_bin/date" <<'FAKE_DATE_SCRIPT'
#!/usr/bin/env bash
printf '%s\n' "${FAKE_DATE:-20260812-101057}"
FAKE_DATE_SCRIPT
  chmod +x "$fake_bin/date"
  printf '%s\n' "$fake_bin"
}

suite_dispatch_output() {
  echo "mmw dispatch（正文、报告与进度日志）"
  local repo task_body task_text fake_bin request_out command execution_out execution_err
  local captured task_size task_suffix log_dir log first_log first_log_name second_log fixed_first_out fixed_second_out fixed_status handle_stem
  repo="$(fresh_repo)"
  task_body="$WORKBENCH/dispatch-output-task.txt"
  printf '%s' '## 目标

保留 "双引号"、反斜线 \\ 和 `反引号`。

## 验收

结尾换行也必须保留。
' > "$task_body"
  task_text="$(cat "$task_body"; printf x)"
  task_text="${task_text%x}"

  fake_bin="$(make_fake_codex)"

  mmw_in "$repo" pi task new dispatch-output "派活输出" --name dispatch-output-work >/dev/null

  request_out="$WORKBENCH/dispatch-background-request.out"
  if (cd "$repo" && env -u MMW_INTERNAL_BACKGROUND_DISPATCH MMW_HOST=claude-code \
      "$MMW" dispatch worker --task-text "$task_text" \
      --cwd "$repo/.worktrees/dispatch-output" --issue 39 > "$request_out" 2>&1) \
      && command="$(sed -n 's/^params: //p' "$request_out" | jq -r '.command')" \
      && [ -n "$command" ]; then
    report pass "GPT 后台命令接收多行 task 正文和范围段"
  else
    command=""
    report fail "GPT 后台命令接收多行 task 正文和范围段" \
      "$(cat "$request_out" 2>/dev/null || true)"
  fi

  captured="$WORKBENCH/codex-success.stdin"
  execution_out="$WORKBENCH/codex-success.out"
  execution_err="$WORKBENCH/codex-success.err"
  if [ -n "$command" ] && env PATH="$fake_bin:$PATH" FAKE_CODEX_STDIN="$captured" \
      FAKE_CODEX_REPORT="成功报告" FAKE_CODEX_EXIT=0 \
      bash -c "$command" > "$execution_out" 2> "$execution_err"; then
    report pass "GPT 后台命令执行成功"
  else
    report fail "GPT 后台命令执行成功" "$(cat "$execution_err" 2>/dev/null || true)"
  fi

  task_size="$(wc -c < "$task_body" | tr -d ' ')"
  task_suffix="$WORKBENCH/codex-success-task.txt"
  tail -c "$task_size" "$captured" > "$task_suffix" 2>/dev/null || true
  expect_state "GPT 后台命令" "多行 task 正文和结尾换行一字不差" \
    cmp -s "$task_body" "$task_suffix"
  expect_state "角色报告" "内容只走标准输出" \
    sh -c 'grep -qxF "成功报告" "$1" && ! grep -q "^report:" "$1"' sh "$execution_out"
  expect_state "角色报告" "不创建 .dispatch 目录" \
    test ! -e "$repo/.worktrees/dispatch-output/.dispatch"
  log_dir="$repo/.worktrees/dispatch-output/.scratch/dispatch-output-work/issue-39/dispatch"
  # 下面这条把断言包进 sh -c，"$1" 由内层 sh 展开，不是外层漏引。
  # shellcheck disable=SC2016
  expect_state "成功的派发进度日志" "日志已删除" \
    sh -c 'test -z "$(find "$1" -maxdepth 1 -name "*.log" -print -quit 2>/dev/null)"' \
      sh "$log_dir"
  # 句柄文件跟日志不同命：日志是过程噪音，成功就删；句柄是修复轮恢复原生产者的入口，
  # 必须活到那一轮。文件名由角色加 task 正文摘要确定性算出，同一份 task 永远同一个名字。
  handle_stem="worker-$(printf '%s' "$task_text" | shasum -a 256 | cut -c1-12)"
  expect_state "成功的派发" "句柄文件留下，内容是 thread_id 原文" \
    grep -qx "fake-thread-1" "$log_dir/$handle_stem.session"
  expect_state "成功的派发" "句柄也在标准输出给一次" \
    grep -qxF "session: fake-thread-1" "$execution_out"

  # 取不到 thread_id 时不静默：说清修复轮恢复不了，并且目录确实空了就收掉。
  execution_out="$WORKBENCH/codex-no-thread.out"
  execution_err="$WORKBENCH/codex-no-thread.err"
  rm -f "$log_dir/$handle_stem.session"
  if [ -n "$command" ] && env PATH="$fake_bin:$PATH" \
      FAKE_CODEX_STDIN="$WORKBENCH/codex-no-thread.stdin" \
      FAKE_CODEX_REPORT="无句柄报告" FAKE_CODEX_NO_THREAD=1 FAKE_CODEX_EXIT=0 \
      bash -c "$command" > "$execution_out" 2> "$execution_err"; then
    report pass "取不到 thread_id 时派发仍然成功"
  else
    report fail "取不到 thread_id 时派发仍然成功" "$(cat "$execution_err" 2>/dev/null || true)"
  fi
  expect_state "取不到 thread_id" "标准错误说明恢复不了这个生产者" \
    grep -qF "这次派发没取到 thread_id" "$execution_err"
  expect_state "取不到 thread_id" "没有句柄文件，空目录被收掉" \
    test ! -e "$log_dir"

  captured="$WORKBENCH/codex-failure.stdin"
  execution_out="$WORKBENCH/codex-failure.out"
  execution_err="$WORKBENCH/codex-failure.err"
  if [ -n "$command" ] && env PATH="$fake_bin:$PATH" FAKE_CODEX_STDIN="$captured" \
      FAKE_CODEX_REPORT="失败报告" FAKE_CODEX_EXIT=7 \
      bash -c "$command" > "$execution_out" 2> "$execution_err"; then
    report fail "GPT 失败时返回 codex 退出码" "期望退出码 7，实际成功"
  elif [ "$?" -eq 7 ]; then
    report pass "GPT 失败时返回 codex 退出码"
  else
    report fail "GPT 失败时返回 codex 退出码" \
      "$(cat "$execution_err" 2>/dev/null || true)"
  fi
  log="$(find "$log_dir" -maxdepth 1 -type f -name 'worker-*.log' -print -quit 2>/dev/null)"
  expect_state "失败的派发进度日志" "路径带工作名与范围段" \
    test -n "$log"
  expect_state "失败的派发进度日志" "文件名是角色、时间戳和随机段" \
    sh -c 'test "$(basename "$1")" != "" && echo "$(basename "$1")" | grep -Eq "^worker-[0-9]{8}-[0-9]{6}-[A-Za-z0-9]{6}\\.log$"' sh "$log"
  expect_state "失败的派发进度日志" "保留 codex 标准错误" \
    grep -qxF "fake progress" "$log"
  expect_state "失败的角色报告" "仍走标准输出" \
    grep -qxF "失败报告" "$execution_out"
  expect_state "失败的角色报告" "仍不创建 .dispatch 目录" \
    test ! -e "$repo/.worktrees/dispatch-output/.dispatch"

  mv "$log" "$WORKBENCH/previous-dispatch.log" || exit 1

  if [ -n "$command" ]; then
    fixed_first_out="$WORKBENCH/codex-fixed-first.out"
    fixed_second_out="$WORKBENCH/codex-fixed-second.out"
    if env PATH="$fake_bin:$PATH" FAKE_CODEX_STDIN="$WORKBENCH/codex-fixed-first.stdin" \
        FAKE_CODEX_PROGRESS="fixed-time first" FAKE_CODEX_EXIT=7 bash -c "$command" \
        > "$fixed_first_out" 2>&1; then
      report fail "固定时间戳的第一个同角色派发保留日志" "期望退出码 7，实际成功"
    else
      fixed_status=$?
      if [ "$fixed_status" -eq 7 ]; then
        report pass "固定时间戳的第一个同角色派发保留日志"
      else
        report fail "固定时间戳的第一个同角色派发保留日志" "期望退出码 7，实际是 $fixed_status"
      fi
    fi
    first_log="$(sed -n 's/^log: //p' "$fixed_first_out")"
    first_log_name="$(basename "$first_log")"
    if [ -n "$first_log" ] && [ -f "$first_log" ]; then
      mv "$first_log" "$WORKBENCH/fixed-time-first.log" || exit 1
      first_log="$WORKBENCH/fixed-time-first.log"
    fi
    if env PATH="$fake_bin:$PATH" FAKE_CODEX_STDIN="$WORKBENCH/codex-fixed-second.stdin" \
        FAKE_CODEX_PROGRESS="fixed-time second" FAKE_CODEX_EXIT=7 bash -c "$command" \
        > "$fixed_second_out" 2>&1; then
      report fail "固定时间戳的第二个同角色派发保留日志" "期望退出码 7，实际成功"
    else
      fixed_status=$?
      if [ "$fixed_status" -eq 7 ]; then
        report pass "固定时间戳的第二个同角色派发保留日志"
      else
        report fail "固定时间戳的第二个同角色派发保留日志" \
          "期望退出码 7，实际是 ${fixed_status}：$(cat "$fixed_second_out")"
      fi
    fi
    second_log="$(sed -n 's/^log: //p' "$fixed_second_out")"
  else
    report fail "固定时间戳的同角色派发保留两份日志" "后台命令为空"
    first_log=""
    first_log_name=""
    second_log=""
  fi
  expect_state "固定时间戳的同角色派发" "留下两份不同文件名的日志" \
    sh -c 'test -f "$1" && test -f "$2" && test "$3" != "$(basename "$2")"' \
      sh "$first_log" "$second_log" "$first_log_name"
  expect_state "固定时间戳的同角色派发" "第一份日志内容完整" \
    grep -qxF "fixed-time first" "$first_log"
  expect_state "固定时间戳的同角色派发" "第二份日志内容完整" \
    grep -qxF "fixed-time second" "$second_log"

  captured="$WORKBENCH/codex-no-log.stdin"
  execution_out="$WORKBENCH/codex-no-log.out"
  execution_err="$WORKBENCH/codex-no-log.err"
  if (cd "$repo" && env MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 \
      PATH="$fake_bin:$PATH" FAKE_CODEX_STDIN="$captured" \
      FAKE_CODEX_REPORT="无日志报告" FAKE_CODEX_EXIT=0 \
      "$MMW" dispatch reviewer-gpt --task-text "$task_text" \
      > "$execution_out" 2> "$execution_err"); then
    report pass "主检出算不出日志落点时仍然派发"
  else
    report fail "主检出算不出日志落点时仍然派发" \
      "$(cat "$execution_err" 2>/dev/null || true)"
  fi
  expect_state "主检出算不出日志落点" "标准错误说明不写日志但继续派发" \
    grep -qF "派发进度日志算不出落点时不写日志，派发照常进行" "$execution_err"
  expect_state "主检出算不出日志落点" "报告仍走标准输出" \
    grep -qxF "无日志报告" "$execution_out"
  expect_state "主检出算不出日志落点" "不创建 .scratch 回退目录" \
    test ! -e "$repo/.scratch"
}

suite_dispatch() {
  echo "mmw dispatch（可写角色）"
  local repo task_body task_text out actual
  repo="$(fresh_repo)"
  task_body="$WORKBENCH/task-body.txt"
  printf '%s' '## 目标

保留 "双引号"、反斜线 \\ 和 `反引号`。

## 验收

结尾换行也必须保留。
' > "$task_body"
  task_text="$(cat "$task_body"; printf x)"
  task_text="${task_text%x}"

  expect_deny "可写角色没给 --cwd" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task-text "$task_text"
  expect_deny "--cwd 不是 git 工作树" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task-text "$task_text" --cwd "$WORKBENCH"
  expect_deny "--cwd 是主检出而不是任务 worktree" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task-text "$task_text" --cwd "$repo"

  # setup 失败就让它响。吞掉的话，下一条用例会拿一个不存在的目录去测，
  # dispatch 照样拒绝，用例照样绿——测到的却是「目录不存在」，不是「不干净」。
  mmw_in "$repo" pi task new dispatchable "派活用" --name dispatchable-work >/dev/null
  expect_ok "干净的任务 worktree 可以派活" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task-text "$task_text" \
      --cwd "$repo/.worktrees/dispatchable"

  out="$WORKBENCH/dispatch-stdin.out"
  actual="$WORKBENCH/dispatch-stdin-task.txt"
  if (cd "$repo" && env MMW_HOST=pi "$MMW" dispatch reviewer-gpt \
      < "$task_body" > "$out" 2>&1) \
      && sed -n 's/^params: //p' "$out" | jq -j '.task' > "$actual" \
      && cmp -s "$task_body" "$actual" \
      && ! grep -q '^task-file:' "$out"; then
    report pass "标准输入把多行 task 正文一字不差地交给 Pi adapter"
  else
    report fail "标准输入把多行 task 正文一字不差地交给 Pi adapter" \
      "$(cat "$out" 2>/dev/null || true)"
  fi

  out="$WORKBENCH/dispatch-task-text.out"
  actual="$WORKBENCH/dispatch-task-text-task.txt"
  if (cd "$repo" && env MMW_HOST=claude-code "$MMW" dispatch reviewer-claude \
      --task-text "$task_text" > "$out" 2>&1) \
      && sed -n 's/^params: //p' "$out" | jq -j '.prompt' > "$actual" \
      && cmp -s "$task_body" "$actual" \
      && ! grep -q '^task-file:' "$out"; then
    report pass "--task-text 把多行 task 正文一字不差地交给 Claude adapter"
  else
    report fail "--task-text 把多行 task 正文一字不差地交给 Claude adapter" \
      "$(cat "$out" 2>/dev/null || true)"
  fi

  # --task-text 优先于标准输入，两种都给时用 --task-text。
  out="$WORKBENCH/dispatch-precedence.out"
  actual="$WORKBENCH/dispatch-precedence-task.txt"
  if (cd "$repo" && printf '管道正文' \
      | env MMW_HOST=pi "$MMW" dispatch reviewer-gpt --task-text "参数正文" > "$out" 2>&1) \
      && sed -n 's/^params: //p' "$out" | jq -j '.task' > "$actual" \
      && [ "$(cat "$actual")" = "参数正文" ]; then
    report pass "两种都给时用 --task-text"
  else
    report fail "两种都给时用 --task-text" "$(cat "$out" 2>/dev/null || true)"
  fi

  # 标准输入是一根开着的空管道时不许去读它。
  # agent 的 Bash 工具给的就是这种标准输入：没有数据，也没人关写端。原来这里会
  # `cat` 一次来拦「两种都给了」，于是命令永久挂住——没有输出，也没有退出码。
  out="$WORKBENCH/dispatch-openpipe.out"
  if run_with_deadline 20 \
      bash -c 'cd "$1" && env MMW_HOST=pi "$2" dispatch reviewer-gpt \
        --task-text "正文" > "$3" 2>&1 < <(sleep 60; :)' \
      bash "$repo" "$MMW" "$out"; then
    report pass "标准输入是开着的空管道时不挂住"
  else
    report fail "标准输入是开着的空管道时不挂住" \
      "20 秒内没有返回，或者返回了非零：$(cat "$out" 2>/dev/null || true)"
  fi
  expect_deny "旧 --task 文件接口已经删除" "$repo" \
    env MMW_HOST=pi "$MMW" dispatch reviewer-gpt --task "$task_body"

  printf 'dirty\n' > "$repo/.worktrees/dispatchable/dirty.txt"
  expect_deny "任务 worktree 工作区不干净" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch worker --task-text "$task_text" \
      --cwd "$repo/.worktrees/dispatchable"
}

# ------------------------------------------------------- dispatch --resume

# 输出断言。用法：expect_out_has <用例名> <要找的字符串> <输出>
expect_out_has() {
  local name="$1" needle="$2" out="$3"
  if printf '%s' "$out" | grep -qF -- "$needle"; then
    report pass "$name"
  else
    report fail "$name" "输出里找不到：${needle}
实际输出：${out}"
  fi
}

suite_dispatch_resume() {
  echo "mmw dispatch --resume（恢复原生产者）"
  local repo task_text fake_bin out handle log_dir handle_stem
  repo="$(fresh_repo)"
  task_text='## 目标

修复第 3 条 finding。'

  expect_deny "--resume 空句柄当场拒绝" "$repo" \
    env MMW_HOST=claude-code "$MMW" dispatch reviewer-gpt --task-text "$task_text" --resume ""
  expect_deny "pi 宿主没有 resume 通道" "$repo" \
    env MMW_HOST=pi "$MMW" dispatch reviewer-gpt --task-text "$task_text" --resume abc

  out="$(env MMW_HOST=claude-code "$MMW" dispatch 2>&1)" || true
  expect_out_has "usage 登记了 --resume" "--resume" "$out"

  # gpt 族第一段装配：--resume 必须进后台命令，否则第二段拿不到句柄。
  out="$(cd "$repo" && env MMW_HOST=claude-code "$MMW" dispatch reviewer-gpt \
    --task-text "$task_text" --resume abc123 2>&1)"
  expect_out_has "gpt 族第一段带上 --resume" "--resume abc123" "$out"

  # claude 族：派发要有确定性句柄，恢复走 SendMessage。
  # 句柄是角色名加 task 正文的 shasum 前 12 位——没有 task 文件可以借文件名，
  # 正文摘要同样确定性：同一份 task 永远算出同一个名字，上下文压缩后也能重建。
  handle="reviewer-claude-$(printf '%s' "$task_text" | shasum -a 256 | cut -c1-12)"
  out="$(cd "$repo" && env MMW_HOST=claude-code "$MMW" dispatch reviewer-claude \
    --task-text "$task_text" 2>&1)"
  expect_out_has "claude 族派发输出 handle 行" "handle: $handle" "$out"
  expect_out_has "claude 族 params 携带确定性 name" "\"name\":\"$handle\"" "$out"
  out="$(cd "$repo" && env MMW_HOST=claude-code "$MMW" dispatch reviewer-claude \
    --task-text "$task_text" --resume "$handle" 2>&1)"
  expect_out_has "claude 族恢复走 SendMessage" "tool: SendMessage" "$out"
  expect_out_has "claude 族恢复收件名是句柄" "\"to\":\"$handle\"" "$out"
  expect_out_has "claude 族恢复把修复 task 原样带进去" '修复第 3 条 finding。' "$out"

  # gpt 族第二段：拿假 codex 跑真命令，断言句柄采集与 resume 装配。
  # 假 codex 把 argv 一行一个记下来，供断言检查真实传参顺序。
  fake_bin="$(make_fake_codex)"
  mmw_in "$repo" pi task new resume-work "恢复用" --name resume-work >/dev/null
  log_dir="$repo/.worktrees/resume-work/.scratch/resume-work/dispatch"
  handle_stem="worker-$(printf '%s' "$task_text" | shasum -a 256 | cut -c1-12)"

  out="$(cd "$repo" && env PATH="$fake_bin:$PATH" \
    CODEX_STUB_ARGV="$WORKBENCH/argv-exec" \
    FAKE_CODEX_STDIN="$WORKBENCH/resume-exec.stdin" \
    FAKE_CODEX_THREAD_ID=stub-thread-1 \
    MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 \
    "$MMW" dispatch worker --task-text "$task_text" \
    --cwd "$repo/.worktrees/resume-work" 2>&1)"
  expect_out_has "gpt 族第二段输出 session 行" "session: stub-thread-1" "$out"
  expect_state "gpt 族第二段写出句柄文件" "句柄文件内容是 thread_id 原文" \
    grep -qx "stub-thread-1" "$log_dir/$handle_stem.session"

  env PATH="$fake_bin:$PATH" \
    CODEX_STUB_ARGV="$WORKBENCH/argv-resume" \
    FAKE_CODEX_STDIN="$WORKBENCH/resume-resume.stdin" \
    FAKE_CODEX_THREAD_ID=stub-thread-1 \
    MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 \
    "$MMW" dispatch worker --task-text "$task_text" \
    --cwd "$repo/.worktrees/resume-work" --resume stub-thread-1 >/dev/null 2>&1 || true
  # 下面四条把断言包进 bash -c，"$1" 由内层 bash 展开，不是外层漏引。
  # shellcheck disable=SC2016
  expect_state "恢复走 codex exec resume" "argv 前两项是 exec resume" \
    bash -c 'head -2 "$1" | tr "\n" " " | grep -q "^exec resume "' _ "$WORKBENCH/argv-resume"
  # `codex exec resume` 没有 --color、-C、--sandbox 三个参数；传了当场报错。
  # shellcheck disable=SC2016
  expect_state "恢复不传 resume 认不了的参数" "argv 里没有 --color、-C 和 --sandbox" \
    bash -c '! grep -qxE -- "--color|-C|--sandbox" "$1"' _ "$WORKBENCH/argv-resume"
  # shellcheck disable=SC2016
  expect_state "恢复用 -c 传同一档 sandbox" "argv 里有 workspace-write 配置覆盖" \
    bash -c 'grep -qx -- "sandbox_mode=\"workspace-write\"" "$1"' _ "$WORKBENCH/argv-resume"
  # shellcheck disable=SC2016
  expect_state "选项排在句柄之前" "句柄是倒数第二个参数、stdin 记号收尾" \
    bash -c '[ "$(tail -2 "$1" | head -1)" = "stub-thread-1" ] && [ "$(tail -1 "$1")" = "-" ]' \
    _ "$WORKBENCH/argv-resume"
  # 恢复不再拼检索纪律前言：上下文还在，那份纪律它已经读过。
  expect_state "恢复只把修复 task 送进标准输入" "标准输入就是 task 正文本身" \
    grep -qxF "修复第 3 条 finding。" "$WORKBENCH/resume-resume.stdin"
}

# --------------------------------------------- dispatch 的沙箱可写范围

suite_dispatch_writable_roots() {
  echo "mmw dispatch（可写角色的沙箱范围）"
  local repo fake_bin gitdir commondir argv phys
  repo="$(fresh_repo)"
  fake_bin="$(make_fake_codex)"
  mmw_in "$repo" pi task new writable-work "可写范围" --name writable-work >/dev/null

  # linked worktree 的 .git 是文件，真正要写的是主仓库 .git/worktrees/<名字>。
  # 拼 <cwd>/.git 的老写法在这里指向那个文件本身，git commit 的 index.lock 落不进去。
  gitdir="$(cd "$repo/.worktrees/writable-work" && git rev-parse --absolute-git-dir)"
  commondir="$(cd "$repo/.worktrees/writable-work" \
    && git rev-parse --path-format=absolute --git-common-dir)"
  expect_state "linked worktree 的 .git" "是文件而不是目录" \
    sh -c 'test -f "$1/.git" && test ! -d "$1/.git"' sh "$repo/.worktrees/writable-work"

  argv="$WORKBENCH/argv-writable"
  (cd "$repo" && env PATH="$fake_bin:$PATH" \
    CODEX_STUB_ARGV="$argv" \
    FAKE_CODEX_STDIN="$WORKBENCH/writable.stdin" \
    MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 \
    "$MMW" dispatch worker --task-text "干活" \
    --cwd "$repo/.worktrees/writable-work" >/dev/null 2>&1) || true

  expect_state "可写角色的 writable_roots" "含这棵 worktree 的 Git 目录" \
    grep -qxF "sandbox_workspace_write.writable_roots=[\"$gitdir\",\"$commondir\"]" "$argv"
  # 比对物理路径。`fresh_repo` 用 `mktemp -d`，在 macOS 上给的是 `/var/folders/…`，
  # 而 `/var` 是 `/private/var` 的符号链接；落进 argv 的是解析过的物理路径。拿 `$repo`
  # 原样去拼，字符串永远对不上，这条断言就恒为通过——旧写法也照样绿。
  phys="$(cd "$repo/.worktrees/writable-work" && pwd -P)"
  expect_state "可写角色的 writable_roots" "不再是拼出来的 <cwd>/.git" \
    sh -c '! grep -qF "$2/.git\"]" "$1"' sh "$argv" "$phys"

  # 只读角色不给可写范围。
  argv="$WORKBENCH/argv-readonly"
  (cd "$repo" && env PATH="$fake_bin:$PATH" \
    CODEX_STUB_ARGV="$argv" \
    FAKE_CODEX_STDIN="$WORKBENCH/readonly.stdin" \
    MMW_HOST=claude-code MMW_INTERNAL_BACKGROUND_DISPATCH=1 \
    "$MMW" dispatch reviewer-gpt --task-text "只读" >/dev/null 2>&1) || true
  expect_state "只读角色" "argv 里没有 writable_roots" \
    sh -c '! grep -q "writable_roots" "$1"' sh "$argv"
  expect_state "只读角色" "sandbox 是 read-only" \
    sh -c 'grep -qx -- "read-only" "$1"' sh "$argv"
}

# -------------------------------------------------------------- Cursor 宿主

suite_cursor_host() {
  echo "Cursor 宿主"
  local repo det home slug_dir out
  repo="$(fresh_repo)"

  expect_deny "Cursor 拒绝 task new" "$repo" \
    env MMW_HOST=cursor "$MMW" task new cursor-new "不该建" --name cursor-work
  expect_state "Cursor 拒绝 task new" "分支没有建出来" \
    branch_absent "$repo" cursor-new

  expect_deny "CURSOR_AGENT 也拒绝 task new" "$repo" \
    env -u MMW_HOST -u CLAUDECODE -u PI_CODING_AGENT -u CODEX_THREAD_ID \
      CURSOR_AGENT=1 "$MMW" task new cursor-env "不该建" --name cursor-work
  expect_state "CURSOR_AGENT 也拒绝 task new" "分支没有建出来" \
    branch_absent "$repo" cursor-env

  expect_deny "Cursor 拒绝 task cleanup" "$repo" \
    env MMW_HOST=cursor "$MMW" task cleanup nosuch

  det="$repo/.worktrees/cursor-det"
  git -C "$repo" worktree add -q --detach "$det" HEAD
  expect_ok "Cursor 能 bind detached worktree" "$det" \
    env MMW_HOST=cursor "$MMW" task bind cursor-bound "任务目标" --name cursor-work

  mmw_in "$repo" pi task new pi-tree "对照" --name pi-work >/dev/null
  out="$WORKBENCH/cursor-writable.err"
  if (cd "$repo" && MMW_HOST=cursor "$MMW" dispatch worker --task-text "x" \
       --cwd "$repo/.worktrees/pi-tree") >"$out" 2>&1; then
    report fail "Cursor 可写角色不在 ~/.cursor/worktrees 时拒绝" "期望拒绝，实际成功"
  else
    report pass "Cursor 可写角色不在 ~/.cursor/worktrees 时拒绝"
  fi
  expect_state "Cursor 可写角色不在 ~/.cursor/worktrees 时拒绝" "诊断点名 ~/.cursor/worktrees" \
    grep -F ".cursor/worktrees" "$out"

  home="$WORKBENCH/cursor-home"
  mkdir -p "$home/.cursor/worktrees"
  slug_dir="$home/.cursor/worktrees/$(basename "$repo")/ok"
  git -C "$repo" worktree add -q -b cursor-ok "$slug_dir" HEAD
  out="$WORKBENCH/cursor-dispatch.err"
  if (cd "$slug_dir" && HOME="$home" MMW_HOST=cursor "$MMW" dispatch worker \
       --task-text "x" --cwd "$slug_dir") >"$out" 2>&1; then
    report fail "Cursor worker 不走 dispatch" "期望拒绝，实际成功"
  else
    report pass "Cursor worker 不走 dispatch"
  fi
  expect_state "Cursor worker 不走 dispatch" "诊断点名 mmw-cursor-agent" \
    grep -F "mmw-cursor-agent" "$out"

  out="$(cd "$repo" && MMW_HOST=cursor "$MMW" dispatch investigator --task-text "查" 2>&1)"
  expect_out_has "Cursor 只读角色走原生 Task" "tool: Task" "$out"
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
suite_task_name
suite_task_new
suite_task_bind
suite_dispatch_output
suite_dispatch
suite_dispatch_resume
suite_dispatch_writable_roots
suite_cursor_host
suite_gitfacts

suite_grok_host() {
  echo "grok 宿主"
  local repo fake_home tree
  repo="$(fresh_repo)"
  fake_home="$WORKBENCH/grok-home"
  mkdir -p "$fake_home/.grok/worktrees/demo"

  expect_deny "Grok 拒绝 task new" "$repo" \
    env MMW_HOST=grok "$MMW" task new grok-new "目标" --name grok-new
  expect_deny "Grok 拒绝 task cleanup" "$repo" \
    env MMW_HOST=grok "$MMW" task cleanup grok-new

  tree="$fake_home/.grok/worktrees/demo/tree"
  git -C "$repo" worktree add -q --detach "$tree" HEAD
  expect_ok "Grok 在 ~/.grok/worktrees 下 bind" "$tree" \
    env HOME="$fake_home" MMW_HOST=grok "$MMW" task bind grok-result "目标" --name grok-work

  expect_deny "Grok 拒绝仓库内 .worktrees 当可写目录" "$repo" \
    env HOME="$fake_home" MMW_HOST=grok "$MMW" dispatch worker --task-text "干活" \
      --cwd "$repo"

  if (cd "$repo" && env -u MMW_HOST -u CLAUDECODE -u PI_CODING_AGENT -u CODEX_THREAD_ID \
      GROK_AGENT=1 "$MMW" task state >/dev/null); then
    report pass "GROK_AGENT 认出 grok 宿主"
  else
    report fail "GROK_AGENT 认出 grok 宿主" "task state 失败"
  fi
}

suite_grok_host

printf '\n通过 %d，失败 %d\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]

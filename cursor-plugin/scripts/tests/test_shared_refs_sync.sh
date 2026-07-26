#!/usr/bin/env bash
# 共享方法论 reference 一致性守卫:task-pack.md 有两份实体 copy
# (一份给写计划工人的 worktree-plan skill,一份给主线程 build-a / selfcheck 步的 orchestrate)。
# 用实体 copy 不用软链(打包/安装链路软链会断);代价是漂移风险,本测试就是那道闸——改了一份忘另一份即红。
# 改动方法论:两份都改,或改一份后 cp 覆盖另一份,再跑本测试确认一致。
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS="$SCRIPT_DIR/../../skills"

pass=0; fail=0
ok() { echo "  PASS: $1"; pass=$((pass+1)); }
no() { echo "  FAIL: $1"; fail=$((fail+1)); }

echo "=== test_shared_refs_sync.sh ==="

# 每对:worktree-plan 侧 <-> orchestrate 侧,必须 byte-identical
check_pair() {  # $1=文件名 $2=worktree-plan 侧路径 $3=orchestrate 侧路径
  local name="$1" a="$2" b="$3"
  if [ ! -f "$a" ]; then no "$name: worktree-plan 侧缺失($a)"; return; fi
  if [ ! -f "$b" ]; then no "$name: orchestrate 侧缺失($b)"; return; fi
  if [ -L "$a" ] || [ -L "$b" ]; then no "$name: 出现软链(应为实体 copy,软链打包会断)"; return; fi
  if diff -q "$a" "$b" >/dev/null 2>&1; then
    ok "$name: 两份实体 copy 一致"
  else
    no "$name: 两份漂移了——改一份忘另一份;两份都改或 cp 覆盖后重跑"
  fi
}

check_pair "task-pack.md" \
  "$SKILLS/worktree-plan/references/task-pack.md" \
  "$SKILLS/orchestrate/references/plan/task-pack.md"

# plan-self-check.md 两份已按读者分化(工人版=自检+就绪门;orchestrate 版=抽验+handoff 收尾),
# 不再 byte-identical;判据条目若改,两份都要人工同步(自检 6 条 + 就绪门 2 段是共同核心)。

echo "Results: $pass passed, $fail failed"
[ "$fail" -eq 0 ]

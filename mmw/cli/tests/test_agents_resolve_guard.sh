#!/usr/bin/env bash
# 原生宿主派发前：resolve / guard / list，不经 mmw dispatch。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$HERE/../mmw"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
check() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败 $name" >&2
    echo "       想要：$want" >&2
    echo "       得到：$got" >&2
    fail=$((fail + 1))
  fi
}

printf 'list / resolve\n'
list_out="$("$MMW" agents list)"
check "list 含 planner" "yes" "$(printf '%s\n' "$list_out" | grep -q '^planner' && echo yes || echo no)"
check "list 含 investigator" "yes" "$(printf '%s\n' "$list_out" | grep -q '^investigator' && echo yes || echo no)"

res="$("$MMW" agents resolve planner)"
check "resolve agent" "mmw-planner" "$(sed -n 's/^agent: //p' <<<"$res")"
check "resolve writable" "yes" "$(sed -n 's/^writable: //p' <<<"$res")"
check "resolve skill" "mmw-planner" "$(sed -n 's/^skill: //p' <<<"$res")"

inv="$("$MMW" agents resolve investigator)"
check "investigator 只读" "no" "$(sed -n 's/^writable: //p' <<<"$inv")"
check "investigator 无 skill" "" "$(sed -n 's/^skill: //p' <<<"$inv")"

if "$MMW" agents resolve nosuch >/dev/null 2>&1; then
  check "未知角色失败" "fail" "pass"
else
  check "未知角色失败" "fail" "fail"
fi

printf '\nguard\n'
# 主仓 + 任务 worktree
git -C "$WORK" init -q main
cd "$WORK/main"
git -C "$WORK/main" commit --allow-empty -q -m init
mkdir -p "$WORK/main/.worktrees"
git -C "$WORK/main" worktree add -q "$WORK/main/.worktrees/t1" -b t1

check "只读角色无需 cwd" "ok" "$("$MMW" agents guard investigator | sed -n 's/^ok: //p' | awk '{print "ok"}')"

if "$MMW" agents guard planner >/dev/null 2>&1; then
  check "可写缺 cwd 失败" "fail" "pass"
else
  check "可写缺 cwd 失败" "fail" "fail"
fi

if "$MMW" agents guard planner --cwd /tmp >/dev/null 2>&1; then
  check "可写 /tmp 失败" "fail" "pass"
else
  check "可写 /tmp 失败" "fail" "fail"
fi

if "$MMW" agents guard planner --cwd "$WORK/main" >/dev/null 2>&1; then
  check "可写主仓根失败" "fail" "pass"
else
  check "可写主仓根失败" "fail" "fail"
fi

"$MMW" agents guard planner --cwd "$WORK/main/.worktrees/t1" >/dev/null
check "可写干净 worktree 通过" "0" "$?"

printf 'dirty\n' > "$WORK/main/.worktrees/t1/x.txt"
if "$MMW" agents guard planner --cwd "$WORK/main/.worktrees/t1" >/dev/null 2>&1; then
  check "可写脏 worktree 失败" "fail" "pass"
else
  check "可写脏 worktree 失败" "fail" "fail"
fi

printf '\n过 %s，失败 %s\n' "$pass" "$fail"
[ "$fail" -eq 0 ]

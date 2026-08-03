#!/usr/bin/env bash
# 标签清单的唯一事实来源是 .mmw.json 的 tracker.labels，`mmw init` 按它建标签。
# 技能正文里可以直接写标签串——那是给模型读的执行指令，绕一层查询反而更糟——但
# 两边必须对得上，靠这个脚本把关，不靠人工 grep。
#
# 两个方向都查：
#   技能里用了清单外的  → 那个标签 mmw init 不会建，跑起来才发现打不上
#   清单里有谁都不用的  → 死标签，每个仓库白建一个
#
# 第一个方向只查 `wayfinder:` 开头的。那个命名空间是这套流程独占的，一眼认得
# 出；`needs-triage` 这类通用词形没法跟别的东西机械区分——`needs-evidence`、
# `needs-redirection` 是 findings 的处置词，长得一模一样但根本不是 issue 标签。
#
# mmw-setup 排除在外。那个目录是上一版做法的背景线索，不是技能，它那份
# triage-labels.md 提到全部 12 个标签。不排除的话，往清单加一个新标签、忘了写
# 进任何技能正文，也会因为那份过期文档提过而假过。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$HERE/../mmw.default.json"
SKILLS="$HERE/../../skills"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0

jq -r '.tracker.labels | keys[]' "$CONFIG" | sort > "$WORK/known"

# 只认反引号包起来的。裸写的 bug 是普通名词，圈进来必然误报。
grep -rhoE '`(wayfinder:[a-z-]+|needs-triage|needs-info|ready-for-agent|ready-for-human|wontfix|bug|enhancement)`' \
  "$SKILLS" --include=*.md --exclude-dir=mmw-setup | tr -d '`' | sort -u > "$WORK/used"

grep -rhoE '`wayfinder:[a-z-]+`' "$SKILLS" --include=*.md --exclude-dir=mmw-setup \
  | tr -d '`' | sort -u > "$WORK/wf"
grep -E '^wayfinder:' "$WORK/known" | sort > "$WORK/wf-known"

extra="$(comm -23 "$WORK/wf" "$WORK/wf-known")"
if [ -z "$extra" ]; then
  echo "  过  技能正文里的 wayfinder: 标签都在清单里"
  pass=$((pass + 1))
else
  echo "  失败 技能正文用了清单外的标签：" >&2
  printf '       %s\n' $extra >&2
  fail=$((fail + 1))
fi

dead="$(comm -13 "$WORK/used" "$WORK/known")"
if [ -z "$dead" ]; then
  echo "  过  清单里没有谁都不用的死标签"
  pass=$((pass + 1))
else
  echo "  失败 清单里这几个技能正文从没提过：" >&2
  printf '       %s\n' $dead >&2
  fail=$((fail + 1))
fi

# 插件模板与本仓库自己那份不能分叉——本仓库就是拿它跑的第一个用户。
if diff -q <(jq -S .tracker "$CONFIG") \
          <(jq -S .tracker "$HERE/../../../.mmw.json") > /dev/null; then
  echo "  过  插件模板与仓库根 .mmw.json 的 tracker 一致"
  pass=$((pass + 1))
else
  echo "  失败 插件模板与仓库根 .mmw.json 的 tracker 不一致" >&2
  fail=$((fail + 1))
fi

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]

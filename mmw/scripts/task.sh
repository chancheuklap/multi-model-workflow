#!/usr/bin/env bash
# 适配层。开一个任务：忽略清单、工作树、两份状态文件，一次落齐。
#
# 两份状态文件谁都要读写——主线程每个阶段、被派出去的工人都会碰。它们的格式住
# templates/，脚本只搬运并把任务名与分叉点填进去。这样每棵工作树里的格式都一样，
# 不靠谁凭记忆手抄一遍。
#
#   task.sh new <任务名> [起点技能]
#
# 起什么名字、从哪个阶段开工都是判断，留给主线程；这里只校验拼写。用户敲的是中文阶段名，
# 认出它对应哪份技能也是主线程的活——九份技能它都装着，每份 description 的头一个词
# 就是那个中文名。脚本这一头只收技能名。
#
# 输出头四行机器可读：TASK= / WORKTREE= / BASE= / PHASE=。

set -euo pipefail

PLUGIN_ROOT="${MMW_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TEMPLATES="$PLUGIN_ROOT/templates"

die() { echo "ERROR: $*" >&2; exit 2; }

sub="${1:-}"; [ "$sub" = new ] || die "用法: task.sh new <任务名> [起点技能]"
task="${2:-}"; [ -n "$task" ] || die "缺任务名"
printf '%s' "$task" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$' \
  || die "任务名只能用小写字母、数字和短横线，短横线不能开头结尾也不能连写：${task}"

# phase 存的就是那个阶段技能的名字，主线程读到它直接去读那份技能，中间不再有一层键。
phase="${3:-mmw-wayfind}"
case " mmw-wayfind mmw-investigate mmw-propose mmw-design mmw-to-issue mmw-plan mmw-build mmw-package mmw-done " in
  *" $phase "*) ;;
  *) die "没有这个阶段: ${phase}" ;;
esac

for t in task.json sidelines.md; do
  [ -f "$TEMPLATES/$t" ] || die "模板缺失: ${TEMPLATES}/${t}"
done

git rev-parse --git-dir >/dev/null 2>&1 || die "不在 git 仓库里"
# 任务工作树里再开任务会把新树套进旧树。用 git-dir 与 common-dir 是否同一个判在不在主仓。
gd="$(cd "$(git rev-parse --git-dir)" && pwd)"
gcd="$(cd "$(git rev-parse --git-common-dir)" && pwd)"
[ "$gd" = "$gcd" ] || die "当前在一棵工作树里，回主仓库再开任务"

root="$(git rev-parse --show-toplevel)"
wt=".mmw/worktrees/$task"
# 用 if 不用 &&：set -e 下条件为假会让整条语句非零，脚本当场退出。
if [ -e "$root/$wt" ]; then die "已经有这棵工作树: ${wt}"; fi
if git -C "$root" show-ref --verify --quiet "refs/heads/$task"; then die "分支已存在: ${task}"; fi

# 忽略规则必须先于分叉提交进去，否则工作树里的 .mmw/ 会以未跟踪身份混进工人的改动，
# 验收读 diff 时分不清哪些是它改的。用 pathspec 限定，不带上工作区里别的改动。
if ! git -C "$root" check-ignore -q .mmw/ 2>/dev/null; then
  printf '.mmw/\n' >> "$root/.gitignore"
  git -C "$root" add -- .gitignore
  git -C "$root" commit -q -m "chore: 忽略 .mmw/" -- .gitignore
fi

base="$(git -C "$root" rev-parse HEAD)"
git -C "$root" worktree add -q "$wt" -b "$task" HEAD

dest="$root/$wt/.mmw"
mkdir -p "$dest"
sed -e "s/__TASK__/${task}/" -e "s/__BASE__/${base}/" -e "s/__PHASE__/${phase}/" \
  "$TEMPLATES/task.json" > "$dest/task.json"
cp "$TEMPLATES/sidelines.md" "$dest/sidelines.md"
python3 -m json.tool "$dest/task.json" >/dev/null || die "填出来的 task.json 不是合法 JSON: ${dest}/task.json"

echo "TASK=$task"
echo "WORKTREE=$root/$wt"
echo "BASE=$base"
echo "PHASE=$phase"

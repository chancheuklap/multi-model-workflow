#!/usr/bin/env bash
# 第三层接线的验收证据：在一个临时仓库里空转一整轮。
# 用法：bash docs/design/mmw-rebuild/dryrun.sh [工作目录]
# 覆盖：开任务 → 切格 → 设计未过门的拒绝点 → 过门 → 越界检查两个方向 →
#       工作树脏拒派 → 审查留痕 → 落地回设计清过门 → --no-ff 合并 → 清树。
set -euo pipefail
MMW="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../mmw" && pwd)"
DIR="${1:-$(mktemp -d)}"; rm -rf "$DIR"; mkdir -p "$DIR"; cd "$DIR"
ok(){ printf '%-12s ✓ %s\n' "$1" "$2"; }

git init -q && git config user.email t@t && git config user.name t
echo hello > README.md && git add -A && git commit -qm init

# ① 开任务：先忽略再建树，否则状态文件会以未跟踪身份混进工人的改动
echo ".mmw/" > .gitignore && git add .gitignore && git commit -qm "ignore .mmw"
BASE=$(git rev-parse HEAD)
git worktree add -q .mmw/worktrees/demo -b demo
WT="$PWD/.mmw/worktrees/demo"; mkdir -p "$WT/.mmw"
printf '{ "task": "demo", "phase": "wayfind", "base": "%s", "note": "", "design_approved": null }\n' "$BASE" > "$WT/.mmw/task.json"
: > "$WT/.mmw/sidelines.md"
ok "开任务" "落在主干第一格 wayfind，base=${BASE:0:8}"

setphase(){ python3 -c "import json,sys;f='$WT/.mmw/task.json';d=json.load(open(f));d['phase']=sys.argv[1];json.dump(d,open(f,'w'),indent=2)" "$1"; }
get(){ python3 -c "import json;print(json.load(open('$WT/.mmw/task.json'))['$1'])"; }

# ② 切格到设计，验唯一拒绝点
setphase investigate; setphase propose; setphase design
[ "$(get design_approved)" = "None" ] && ok "切格" "停在 design，未过门不许往下"

# ③ 过门
mkdir -p "$WT/docs/design/demo" && echo "# demo" > "$WT/docs/design/demo/demo.md"
git -C "$WT" add -A && git -C "$WT" commit -qm design
python3 -c "
import json,datetime;f='$WT/.mmw/task.json';d=json.load(open(f))
d['design_approved']={'at':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'docs':['docs/design/demo/demo.md']}
json.dump(d,open(f,'w'),indent=2)"
ok "过门" "记下时间与认可的文档清单"

# ④⑤ 越界检查两个方向
setphase build; START=$(git -C "$WT" rev-parse HEAD)
echo "print(1)" > "$WT/app.py"
bash "$MMW/scripts/dispatch.sh" check --role executor --cwd "$WT" --since "$START" >/dev/null 2>&1 \
  && ok "越界检查" "改源码合规"
echo "x" >> "$WT/docs/design/demo/demo.md"
if bash "$MMW/scripts/dispatch.sh" check --role executor --cwd "$WT" --since "$START" >/dev/null 2>&1; then
  echo "越界检查 ✗ 碰 docs 竟然放过了"; exit 1
else
  ok "越界检查" "碰 docs 判越界"
fi

# ⑥ 工作树脏拒派
echo x > "$DIR/p.md"
if bash "$MMW/scripts/dispatch.sh" run --role executor --cwd "$WT" --prompt "$DIR/p.md" >/dev/null 2>&1; then
  echo "拒派 ✗ 脏工作树竟然派出去了"; exit 1
else
  ok "拒派" "工作树脏，要求先提交"
fi

# ⑦ 审查留痕
git -C "$WT" add -A && git -C "$WT" commit -qm wip
mkdir -p "$WT/.mmw/reviews"
printf '基准: %s\n\n(审者原样发现落这里)\n' "$(git -C "$WT" rev-parse HEAD)" > "$WT/.mmw/reviews/build-1.md"
ok "审查留痕" "头部写基准提交，供下次判增量"

# ⑧ 落地完回设计再调（主路上的大环）：目标格是 design，过门标记清回空
setphase design
python3 -c "import json;f='$WT/.mmw/task.json';d=json.load(open(f));d['design_approved']=None;json.dump(d,open(f,'w'),indent=2)"
[ "$(get design_approved)" = "None" ] && ok "回设计" "过门标记清回空，改完要重新过门"
setphase build; setphase package

# ⑨⑩ 合并与清树
git merge --no-ff -q demo -m "merge demo"
ok "合并" "--no-ff，主分支 $(git rev-list --count HEAD) 个提交"
git worktree remove --force .mmw/worktrees/demo
[ ! -e .mmw/worktrees/demo ] && ok "清树" "状态与旁路清单随工作树一起消失"

echo
echo "空转通过。真派一次（起无头进程）不在本脚本内——那要花钱，单独跑："
echo "  bash $MMW/scripts/dispatch.sh run --role reviewer-gpt --cwd <仓库> --prompt <文件>"

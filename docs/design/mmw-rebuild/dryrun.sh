#!/usr/bin/env bash
# 第三层接线的验收证据：在一个临时仓库里空转一整轮。
# 用法：bash docs/design/mmw-rebuild/dryrun.sh [工作目录]
# 覆盖：开任务 → 切格 → 设计未过门的拒绝点 → 过门 → 越界检查两个方向 → 工作树脏拒派 →
#       派发提示词组装 → 审查留痕 → 落地回设计清过门 → 产品层宿主名扫描 → --no-ff 合并 → 清树。
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

# ⑦ 送到被派者手里的那份提示词：角色说明、按参数生成的边界、技能名单都要在
for r in executor executor-capable plan-writer reviewer-gpt reviewer-claude scout; do
  out="$(bash "$MMW/scripts/dispatch.sh" preview --role "$r" --prompt "$DIR/p.md")"
  case "$r" in scout|reviewer-*) b="写不了盘" ;; plan-writer) b="别的文档不动" ;; *) b="文档目录禁碰" ;; esac
  for must in "你的角色是 $r" "$b" "开工要拿到" "收工" "先读你已装的这几份 skill" "## 这次的活"; do
    case "$out" in *"$must"*) ;; *) echo "提示词 ✗ ${r} 缺「${must}」"; exit 1 ;; esac
  done
done
ok "提示词" "六份角色的说明与技能名单都由脚本抄进开头，调用方只写这次的活"

# ⑧ 审查留痕
git -C "$WT" add -A && git -C "$WT" commit -qm wip
mkdir -p "$WT/.mmw/reviews"
printf '基准: %s\n\n(审者原样发现落这里)\n' "$(git -C "$WT" rev-parse HEAD)" > "$WT/.mmw/reviews/build-1.md"
ok "审查留痕" "头部写基准提交，供下次判增量"

# ⑨ 落地完回设计再调（主路上的大环）：目标格是 design，过门标记清回空
setphase design
python3 -c "import json;f='$WT/.mmw/task.json';d=json.load(open(f));d['design_approved']=None;json.dump(d,open(f,'w'),indent=2)"
[ "$(get design_approved)" = "None" ] && ok "回设计" "过门标记清回空，改完要重新过门"
setphase build; setphase package

# ⑩ 产品层不许出现宿主名（线下区讲机制成因可以，适配层那份除外）
leak=""
for f in "$MMW"/skills/*/SKILL.md "$MMW"/roles/*.md; do
  case "$f" in */mmw-dispatch/*) continue ;; esac
  hit="$(sed '/^## 线下/,$d' "$f" \
    | grep -nEi 'codex|cursor|droid|factory|claude[ -]code|\.codex|\.claude|subagent_type|allowed-tools' || true)"
  [ -n "$hit" ] && leak="${leak}${f}: ${hit}"$'\n'
done
if [ -n "$leak" ]; then
  printf '宿主名 ✗ 产品层渗进宿主耦合:\n%s' "$leak"; exit 1
else
  ok "宿主名" "产品层线上区干净，换宿主只改适配层"
fi

# ⑪⑫ 合并与清树
git merge --no-ff -q demo -m "merge demo"
ok "合并" "--no-ff，主分支 $(git rev-list --count HEAD) 个提交"
git worktree remove --force .mmw/worktrees/demo
[ ! -e .mmw/worktrees/demo ] && ok "清树" "状态与旁路清单随工作树一起消失"

echo
echo "空转通过。真派一次（起无头进程）不在本脚本内——那要花钱，单独跑："
echo "  bash $MMW/scripts/dispatch.sh run --role reviewer-gpt --cwd <仓库> --prompt <文件>"

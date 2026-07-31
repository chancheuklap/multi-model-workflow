#!/usr/bin/env bash
# 第三层接线的验收证据：在一个临时仓库里空转一整轮。
# 用法：bash docs/design/mmw-rebuild/dryrun.sh [工作目录]
# 覆盖：开任务（走 task.sh）→ 可选起点 → 状态文件注入 → 切格 → 设计未过门的拒绝点 → 过门 → 工作树脏拒派 → 派发提示词组装 →
#       审查留痕 → 落地回设计清过门 → 产品层宿主名扫描 → --no-ff 合并 → 清树。
set -euo pipefail
MMW="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../mmw" && pwd)"
DIR="${1:-$(mktemp -d)}"; rm -rf "$DIR"; mkdir -p "$DIR"; cd "$DIR"
ok(){ printf '%-12s ✓ %s\n' "$1" "$2"; }

git init -q && git config user.email t@t && git config user.name t
echo hello > README.md && git add -A && git commit -qm init

# ① 开任务：走生产脚本，不在这里复制一份建树逻辑
eval "$(bash "$MMW/scripts/task.sh" new demo)"; WT="$WORKTREE"
[ "$(git check-ignore -q .mmw/ && echo y)" = y ] || { echo "FAIL 忽略清单没落地"; exit 1; }
[ "$(python3 -c "import json;print(json.load(open('$WT/.mmw/task.json'))['phase'])")" = mmw-wayfind ] \
  || { echo "FAIL 默认起点不是 mmw-wayfind"; exit 1; }
ok "开任务" "不给起点就落在主干第一格探路，base=${BASE:0:8}"

# ①'' 给了起点就开在那一格；不是九格之一的当场拒绝
eval "$(bash "$MMW/scripts/task.sh" new demo-bug mmw-investigate | sed 's/^/S_/')"
SP="$(python3 -c "import json;print(json.load(open('$S_WORKTREE/.mmw/task.json'))['phase'])")"
[ "$SP" = mmw-investigate ] || { echo "FAIL 起点参数没写进状态"; exit 1; }
# phase 存的就是技能名：主线程照它直接找到那份技能，中间不再有一层键
[ -f "$MMW/skills/$SP/SKILL.md" ] || { echo "FAIL phase 的值不是一份现成技能的名字"; exit 1; }
for bad in investigate closing mmw-invesigate; do
  if bash "$MMW/scripts/task.sh" new "demo-typo-$bad" "$bad" >/dev/null 2>&1; then
    echo "FAIL 不是九格之一的 ${bad} 竟然收下了"; exit 1
  fi
done
ok "起点" "起点参数即技能名，主线程照它就能找到技能；另起的键与拼错当场拒绝"

# ①''' 中文格名认哪份技能，全靠 description 的头一个词——没有第二份对应表兜底，这条必须成立
python3 - "$MMW" <<'PY_CELLS' || exit 1
import pathlib,re,sys
want=["探路","查清现状","给方案","做设计","切片","写计划","落地","出包","收尾"]
skills=["mmw-wayfind","mmw-investigate","mmw-propose","mmw-design","mmw-to-issue",
        "mmw-plan","mmw-build","mmw-package","mmw-done"]
got={}
for cell,name in zip(want,skills):
    text=(pathlib.Path(sys.argv[1])/"skills"/name/"SKILL.md").read_text()
    desc=re.search(r'^description:\s*(.+)$',text,re.M).group(1)
    head=re.split(r'[。：:]',desc)[0].strip()
    if head!=cell:
        print(f"FAIL {name} 的 description 头一个词是「{head}」，不是格名「{cell}」");sys.exit(1)
    got.setdefault(head,[]).append(name)
dup={k:v for k,v in got.items() if len(v)>1}
if dup: print(f"FAIL 两份技能抢同一个格名: {dup}");sys.exit(1)
PY_CELLS
ok "格名" "九份技能 description 的头一个词就是那个中文名，互不重复"

# ①' 两份状态文件由脚本从 templates/ 注入，主线程不手抄
[ "$(python3 -c "import json;print(json.load(open('$WT/.mmw/task.json'))['task'])")" = demo ] \
  || { echo "FAIL task.json 没填对"; exit 1; }
diff <(sed 's/^/ /' "$MMW/templates/sidelines.md") <(sed 's/^/ /' "$WT/.mmw/sidelines.md") >/dev/null \
  || { echo "FAIL sidelines.md 与模板不一致"; exit 1; }
grep -q '^| 现象 | 位置 |' "$WT/.mmw/sidelines.md" || { echo "FAIL 旁路清单没有表头"; exit 1; }
ok "注入" "task.json 填好任务名与分叉点，旁路清单带着表头进树"

setphase(){ python3 -c "import json,sys;f='$WT/.mmw/task.json';d=json.load(open(f));d['phase']=sys.argv[1];json.dump(d,open(f,'w'),indent=2)" "$1"; }
get(){ python3 -c "import json;print(json.load(open('$WT/.mmw/task.json'))['$1'])"; }

# ② 切格到设计，验唯一拒绝点
setphase mmw-investigate; setphase mmw-propose; setphase mmw-design
[ "$(get design_approved)" = "None" ] && ok "切格" "停在做设计那一格，未过门不许往下"

# ③ 过门
mkdir -p "$WT/docs/design/demo" && echo "# demo" > "$WT/docs/design/demo/demo.md"
git -C "$WT" add -A && git -C "$WT" commit -qm design
python3 -c "
import json,datetime;f='$WT/.mmw/task.json';d=json.load(open(f))
d['design_approved']={'at':datetime.datetime.now().astimezone().isoformat(timespec='seconds'),'docs':['docs/design/demo/demo.md']}
json.dump(d,open(f,'w'),indent=2)"
ok "过门" "记下时间与认可的文档清单"

setphase mmw-build

# ④ 工作树脏拒派
echo x > "$DIR/p.md"
echo "print(1)" > "$WT/app.py"
if bash "$MMW/scripts/dispatch.sh" run --role executor --cwd "$WT" --prompt "$DIR/p.md" >/dev/null 2>&1; then
  echo "拒派 ✗ 脏工作树竟然派出去了"; exit 1
else
  ok "拒派" "工作树脏，要求先提交"
fi

# ⑤ 送到被派者手里的那份提示词：角色说明、按参数生成的边界、技能名单都要在
for r in executor executor-capable plan-writer reviewer-gpt reviewer-claude scout; do
  out="$(bash "$MMW/scripts/dispatch.sh" preview --role "$r" --prompt "$DIR/p.md")"
  for must in "你的角色是 $r" "开工要拿到" "收工" "先读你已装的这几份 skill" "## 这次的活"; do
    case "$out" in *"$must"*) ;; *) echo "提示词 ✗ ${r} 缺「${must}」"; exit 1 ;; esac
  done
done
ok "提示词" "六份角色的说明与技能名单都由脚本抄进开头，调用方只写这次的活"

# ⑥ 审查留痕
git -C "$WT" add -A && git -C "$WT" commit -qm wip
mkdir -p "$WT/.mmw/reviews"
printf '基准: %s\n\n(审者原样发现落这里)\n' "$(git -C "$WT" rev-parse HEAD)" > "$WT/.mmw/reviews/mmw-build-1.md"
ok "审查留痕" "头部写基准提交，供下次判增量"

# ⑦ 落地完回设计再调（主路上的大环）：目标格是 mmw-design，过门标记清回空
setphase mmw-design
python3 -c "import json;f='$WT/.mmw/task.json';d=json.load(open(f));d['design_approved']=None;json.dump(d,open(f,'w'),indent=2)"
[ "$(get design_approved)" = "None" ] && ok "回设计" "过门标记清回空，改完要重新过门"
setphase mmw-build; setphase mmw-package

# ⑧ 产品层不许出现宿主名（线下区讲机制成因可以，适配层那份除外）
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

# ⑨⑩ 合并与清树
git merge --no-ff -q demo -m "merge demo"
ok "合并" "--no-ff，主分支 $(git rev-list --count HEAD) 个提交"
git worktree remove --force .mmw/worktrees/demo
[ ! -e .mmw/worktrees/demo ] && ok "清树" "状态与旁路清单随工作树一起消失"

echo
echo "空转通过。真派一次（起无头进程）不在本脚本内——那要花钱，单独跑："
echo "  bash $MMW/scripts/dispatch.sh run --role reviewer-gpt --cwd <仓库> --prompt <文件>"

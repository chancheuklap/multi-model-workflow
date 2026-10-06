"""Figures of lesson 0020: the verdict on each checklist item drawn from the owner's past lessons;
the moments where v3, set up and used as designed, went wrong, and what each does now."""
import html

from kit import Fig, tbox as _box, txt as _txt

# One verdict per checklist item, in the order the checklist gives them.
VERDICTS = {
    "K": ("还在", "--ok", ""),
    "D": ("按决定改了", "--k-mode", ""),
    "F": ("这次补回", "--k-principle", ""),
    "V": ("v2 时就缺", "--k-other", "stroke-dasharray:4 3;"),
}

GROUPS = [
    ("A", "提示层与 mode", "D K D D D D D D D D K K"),
    ("B", "路由", "K D K K K K F K D K K K"),
    ("C", "spec 与切票", "K F K K D K K K K K K K F K"),
    ("D", "worker", "K K K K K K K K K K F K F F K"),
    ("E", "reviewer", "K K D F K K K K K"),
    ("F", "夜", "K K D K K K D D K K F K K D"),
    ("G", "界面链", "K K K K V K"),
    ("H", "记忆与复盘", "K K K V F"),
    ("I", "技能集文字", "K F F K K K K K K"),
]


def _cell(f, x, y, w, h, code, label):
    _, var, extra = VERDICTS[code]
    f.e(f'<rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4" style="--c:var({var});{extra}"/>', False)
    f.e(f'<text x="{x + w / 2}" y="{y + h / 2 + 4.5:.1f}" text-anchor="middle" class="s" '
        f'style="fill:var(--ink)">{html.escape(label)}</text>')


def verdicts():
    f = Fig("m201", 1000)
    X0, CW, CH, GAP, RH = 200, 44, 28, 6, 38
    counts = {k: 0 for k in VERDICTS}
    y = 10
    for letter, name, codes in GROUPS:
        _txt(f, 10, y + 19, f"{letter}　{name}", "h", room=X0 - 16)
        for i, code in enumerate(codes.split()):
            counts[code] += 1
            _cell(f, X0 + i * (CW + GAP), y, CW, CH, code, f"{letter}{i + 1}")
        y += RH
    y += 10
    f.e(f'<line class="rule" x1="10" y1="{y}" x2="990" y2="{y}"/>', False)
    y += 14
    x = 10
    for code, (label, _, _) in VERDICTS.items():
        _cell(f, x, y, 30, 22, code, str(counts[code]))
        _txt(f, x + 38, y + 15.5, label, "s", room=200)
        x += 38 + int(len(label) * 11.5 + 30)
    total = sum(counts.values())
    return f.svg(y + 32, ARIA_VERDICTS.format(total=total, **counts))


ARIA_VERDICTS = (
    "第 20 课图 1，清单上 {total} 条 v2 的原则和教训，每条在 v3 里的结论。"
    "还在 {K} 条，按决定改了 {D} 条，这次补回 {F} 条，v2 时就缺 {V} 条。"
    "A 组提示层与 mode 多数是按决定改了：v2 用户层提示里的规则 2 到 15 按第 4 课的决定搬进了 mmw-mode。"
    "这次补回的是迁移后变弱的 8 条、两处说法相反的 2 条和 H5，分布在路由、spec、worker、reviewer、夜、记忆和技能集文字各组。"
    "仍缺的两条是 G5 和 H4。")


MOMENTS = [
    ("早上 finish 退 2：还有票开着", "script",
     "原来：playbook 说一张都别自己关，dispatch.sh 却印 close them",
     ["现在：stderr 说这些票由 owner 定，一张都别自己关，",
      "和 Run a night 的 Finish once the owner accepts 说同一件事"]),
    ("干净合并后仓库检查变红，票被退回", "playbook",
     "原来：worker 只读到「修产品直到 exit 0」",
     ["现在：Work a ticket 第 3 步这一支也先读 integrate 列出的进来的票",
      "和它们的关票评论，保留已落地的，再修到 exit 0"]),
    ("仓库头一夜，Memory 索引是 none", "reference",
     "原来：写 Memory 的规则只挂在「打开索引里的记录」后面",
     ["现在：第 2 步不论索引是不是 none 都读 references/memory.md，",
      "从那一步到最后照它的 ## Save 存经验"]),
    ("map 分成几份 spec，第一份发布之后", "playbook",
     "原来：没有一步把它的链接填回 map 的 ## Specs",
     ["现在：Write a spec 第 4 步发布后把链接填进它那一行，",
      "Done when 也查这一行有没有链接"]),
    ("改一个有 J 记录的上游拷贝，漏记一条", "script",
     "原来：check_imports.py 照样印 IMPORTS OK",
     ["现在：文件在它那一行最后一次改动之后又改过，就报 UNRECORDED-EDIT；",
      "第一次跑查出 12 处旧漏记，都已补上"]),
]


def moments():
    f = Fig("m203", 1000)
    y = 10
    for left, kind, title, lines in MOMENTS:
        h = 30 + len(lines) * 17
        _box(f, "other", 10, y + (h - 30) / 2, 300, left, [])
        f.ar([(312, y + h / 2), (346, y + h / 2)])
        _box(f, kind, 348, y, 642, title, lines)
        y += h + 12
    aria = "第 20 课图 2，配置好、按设计使用时会出错的五个时刻，原来怎样，现在怎样。" + "".join(
        f"{left}：{t}；{'；'.join(lines)}。" for left, _, t, lines in MOMENTS)
    return f.svg(y - 2, aria)


FIGS = {"l20-verdicts": verdicts, "l20-moments": moments}

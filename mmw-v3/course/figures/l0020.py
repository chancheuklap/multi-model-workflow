"""Figures of lesson 0020: the verdict on each checklist item drawn from the owner's past lessons;
which sessions read the owner's rules under v2 and v3; the moments where v3 goes wrong in real use."""
import html

from kit import Fig, tbox as _box, txt as _txt

# One verdict per checklist item, in the order the checklist gives them.
VERDICTS = {
    "K": ("还在", "--ok", ""),
    "D": ("按决定改了", "--k-mode", ""),
    "W": ("变弱", "--warn", ""),
    "C": ("两处说法相反", "--bad", ""),
    "L": ("没有 .mmw/ 的仓库里丢了", "--bad", "fill:color-mix(in srgb,var(--bad) 45%,var(--surface));"),
    "V": ("v2 时就缺", "--k-other", "stroke-dasharray:4 3;"),
}

GROUPS = [
    ("A", "提示层与 mode", "L K L L L L L L L W C W"),
    ("B", "路由", "W D K K K K W K D K K K"),
    ("C", "spec 与切票", "K W K K D K K K K K K K W K"),
    ("D", "worker", "K K K K K K K K K K W K W W K"),
    ("E", "reviewer", "K K D W K K K K K"),
    ("F", "夜", "K K D K W K D D K K C K K W"),
    ("G", "界面链", "K K K K V K"),
    ("H", "记忆与复盘", "K K K V V"),
    ("I", "技能集文字", "K W C K K K K K K"),
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
    return f.svg(y + 32, ARIA_VERDICTS.format(total=total, **{k: v for k, v in counts.items()}))


ARIA_VERDICTS = (
    "第 20 课图 1，清单上 {total} 条 v2 的原则和教训，每条在 v3 里的结论。"
    "还在 {K} 条，按决定改了 {D} 条，变弱 {W} 条，两处说法相反 {C} 条，"
    "只在没有 .mmw/ 的仓库里丢了 {L} 条，v2 时就缺 {V} 条。"
    "丢了的 8 条都在 A 组，提示层与 mode：A1 和 A3 到 A9。变弱的分布在路由、spec、worker、reviewer、夜和技能集文字各组。")


READERS = [
    ("有 .mmw/ 的仓库 · Claude Code、Codex", "你开的会话：mode-hook.py 让它先读 mode", "yes"),
    ("dispatch.sh 开的 worker、reviewer", "start prompt 第一句让它读 mode", "yes"),
    ("有 .mmw/ 的仓库 · Grok、Cursor", "没有钩子；你没输入 /mmw-mode 时", "no"),
    ("没有 .mmw/ 的仓库 · 任何宿主", "钩子什么都不输出", "no"),
    ("宿主的子代理", "按设计不读 mode，派它的 brief 写全它要的", "design"),
]


def readers():
    f = Fig("m202", 1000)
    COLS = [(420, "v2：shared.md", "规则 1–15，每个会话都带"),
            (610, "v3：shared.md", "读者是谁 + 规则 1"),
            (800, "v3：mmw-mode", "规则 2–15 搬到这里")]
    W = 180
    for x, head, sub in COLS:
        _txt(f, x + W / 2, 22, head, "h", anchor="middle", room=W)
        _txt(f, x + W / 2, 40, sub, "s", anchor="middle", room=W)
    y = 56
    for name, how, mode in READERS:
        h = 46
        f.e(f'<g class="k-other"><rect class="box" x="10" y="{y}" width="396" height="{h}" rx="4"/></g>', False)
        _txt(f, 22, y + 20, name, "h", room=376)
        _txt(f, 22, y + 37, how, "s", room=376)
        marks = [("yes", "全部"), ("yes", "两段"),
                 {"yes": ("yes", "读到"), "no": ("no", "读不到"), "design": ("design", "不需要")}[mode]]
        for (x, _, _), (state, word) in zip(COLS, marks):
            var = {"yes": "--ok", "no": "--bad", "design": "--k-other"}[state]
            sym = {"yes": "✓", "no": "✗", "design": "–"}[state]
            f.e(f'<rect class="box" x="{x}" y="{y}" width="{W}" height="{h}" rx="4" style="--c:var({var})"/>', False)
            _txt(f, x + W / 2, y + 28, f"{sym}　{word}", "h", anchor="middle", room=W - 10)
        y += h + 8
    _txt(f, 10, y + 14, "第 3、4 行在 v2 里整套规则都在；在 v3 里只剩中间那一列的两段。", "s", room=980)
    return f.svg(y + 26, ARIA_READERS)


ARIA_READERS = (
    "第 20 课图 2，五种会话在 v2 和 v3 里各读得到哪些规则。"
    "v2 的 shared.md 有规则 1 到 15，五种会话都带。v3 的 shared.md 只有读者是谁和规则 1，五种会话都带；"
    "规则 2 到 15 搬进了 mmw-mode。有 .mmw/ 的仓库里 Claude Code、Codex 你开的会话读得到 mode；"
    "dispatch.sh 开的 worker 和 reviewer 读得到；有 .mmw/ 的仓库里 Grok、Cursor 你没输入 /mmw-mode 时读不到；"
    "没有 .mmw/ 的仓库里任何宿主都读不到；宿主的子代理按设计不读 mode，由派它的 brief 写全。")


NIGHT = [
    ("槽位全被占（默认 8 个）", "playbook",
     "worker 报 fault 停下；orchestrator 只知道修环境或停整夜",
     ["改：Run a night 第 5 步 fault 那一行加一句：写着槽位全占时，",
      "等下一次 advance 落地一张票、空出槽位，再 resume 这个 worker"]),
    ("早上 finish 退 2：还有票开着", "script",
     "playbook 说一张都别自己关，dispatch.sh 却印 close them",
     ["改：stderr 改成「交给 owner 定」，和 Run a night 第 10 步一致"]),
    ("新机器上没有 models.json", "script",
     "拒绝文字叫 orchestrator 去跑 install.sh",
     ["在别的仓库里没有禁令挡着，照做就改掉各宿主的配置和钩子",
      "改：改成「告诉 owner；install.sh 只由 owner 跑」"]),
    ("你说「这一夜先停」", "playbook",
     "会走到 Pause safely，它不提 suspend，worker 照跑",
     ["改：Run a night 第 1 步的表加一行：owner 要停这一夜，去第 11 步"]),
    ("干净合并后仓库检查变红，票被退回", "playbook",
     "worker 只读到「修产品直到 exit 0」",
     ["可能改掉刚落地那张票的行为；v2 写着这是合并造成的，先读合进来的票",
      "改：Work a ticket 第 3 步给这一支接上冲突那一支已有的同一句"]),
    ("新仓库头一夜，Memory 索引是 none", "reference",
     "写 Memory 的规则只挂在「打开索引里的记录」后面",
     ["没有记录可开，worker 就不读 memory.md，整夜一条经验都不写",
      "改：第 1 步就点名 references/memory.md，它的规则对每一步都成立"]),
]

DAY = [
    ("不在 map 上：「做个原型给我试」", "skill",
     "prototype 只在被点名时跑，没有路由行通到它",
     ["结果是一次性代码，没有 README 结论给 spec 当基线",
      "改：给一条路由行加这类触发词，或恢复 v2 那句 description"]),
    ("「找找 deepening opportunities」", "skill",
     "codebase-design 和 Improve the architecture 抢同一句",
     ["前者只在对话里答一遍就停，不出报告，不交给 Write a spec",
      "改：从 codebase-design 的 description 删掉这组触发词"]),
    ("map 分成几份 spec，第一份发布之后", "playbook",
     "没有一步把它的链接填回 map 的 ## Specs",
     ["下一次照「写第一份没有链接的」，会把第一份再写一遍",
      "改：Write a spec 第 4 步发布后回填，并写进 Done when"]),
    ("在产品仓库里说「评审一下技能集」", "playbook",
     "修复会顺着软链改到已安装的 checkout（推断）",
     ["改动立即对所有宿主生效，绕过根 AGENTS.md 的四步发布",
      "改：两份 playbook 开头写明只在 MMW 仓库的 main worktree 里做"]),
    ("改一个有 J 记录的上游拷贝，漏记一条", "script",
     "check_imports.py 照样印 IMPORTS OK",
     ["它只比没有 J 记录的行；下次拉上游，这处改动被盖掉，没人知道",
      "改：文件比 imports.tsv 里它那一行改得晚，就报一条"]),
    ("五处用步骤编号引用别的 playbook", "reference",
     "今天都指对；被引用的那份插进一步就指错",
     ["skill-set-rules.md 规定按标题引用，check_wiring.py 不查这一类",
      "改：换成步骤的加粗标题"]),
]


def _moments(mid, rows, aria):
    f = Fig(mid, 1000)
    y = 10
    for left, kind, title, lines in rows:
        h = 30 + len(lines) * 17
        _box(f, "other", 10, y + (h - 30) / 2, 300, left, [])
        f.ar([(312, y + h / 2), (346, y + h / 2)])
        _box(f, kind, 348, y, 642, title, lines)
        y += h + 12
    return f.svg(y - 2, aria)


def _aria(n, title, rows):
    return f"第 20 课图 {n}，{title}。" + "".join(
        f"{left}：{t}；{'；'.join(lines)}。" for left, _, t, lines in rows)


def night():
    return _moments("m203", NIGHT, _aria(3, "夜里和做票时会出错的六个时刻", NIGHT))


def day():
    return _moments("m204", DAY, _aria(4, "白天的路由、spec 和技能集里会出错的六个时刻", DAY))


FIGS = {"l20-verdicts": verdicts, "l20-readers": readers, "l20-night": night, "l20-day": day}

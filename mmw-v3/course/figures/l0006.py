"""Figures of lesson 0006: the six kinds of routing in MMW v2's skills, MMW's work cut into playbooks,
where each v2 skill's text goes, how an agent a skill sends out gets its part, how Investigation is wired,
which kind of agent a role is, the role table, and one batch of briefs. A dashed box or chip is not in v3 yet."""
import html
from kit import Fig, tw


SIZES = {"s": 11.5, "m": 12.0, "h": 14.0}


def _fits(text, cls, room):
    """Refuse a line wider than the room it is drawn in; monospace fallbacks run wider."""
    need = tw(text, SIZES[cls], cls == "m") * (1.12 if cls == "m" else 1.0)
    if need > room:
        raise ValueError(f"{text!r} needs {need:.0f}px and has {room}px")


def _box(f, kind, x, y, w, title, lines, mono_title=True, dashed=False):
    """A box with a title and lines below it, each line checked against the room; returns its height."""
    h = 30 + len(lines) * 17
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"{dash}/></g>', False)
    _t(f, x + 12, y + 20, title, "m" if mono_title else "h", room=w - 20)
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 39 + i * 17, line, room=w - 20)
    return h



def _t(f, x, y, t, cls="s", anchor="start", room=None):
    if room is not None:
        _fits(t, cls, room)
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f.e(f'<text x="{x}" y="{y:.1f}" class="{cls}"{a}>{html.escape(t)}</text>')


def _chip(f, kind, x, y, label, mono=True, dashed=False):
    """kit's chip, with room for a monospace font wider than JetBrains Mono; returns its right edge."""
    w = tw(label, 11.5, mono) * (1.1 if mono else 1.0) + (18 if mono else 24)
    tc = "m" if mono else "s"
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w:.1f}" height="24" rx="4"{dash}/>'
        f'<text x="{x+9}" y="{y+16.5}" class="{tc}">{html.escape(label)}</text></g>')
    return x + w


def _chips(f, x, y, items, gap=6):
    """A row of chips, (kind, label[, mono[, dashed]]); returns the x after the last one."""
    for it in items:
        kind, label = it[0], it[1]
        mono = it[2] if len(it) > 2 else True
        dashed = it[3] if len(it) > 3 else False
        x = _chip(f, kind, x, y, label, mono, dashed) + gap
    return x


def _numdot(f, x, y, n):
    f.e(f'<circle cx="{x}" cy="{y}" r="11" fill="var(--ink2)"/>'
        f'<text x="{x}" y="{y+4.5}" text-anchor="middle" style="fill:var(--surface);font-size:12px;font-weight:700">{n}</text>')


def _pb(f, x, y, w, title, sub=None, dashed=False, h=None):
    """A playbook box: its name, and under it one short line; returns (x, y, w, h)."""
    h = h or (46 if sub else 30)
    f.e(f'<g class="k-playbook"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"'
        + (' style="stroke-dasharray:6 3"' if dashed else '') + '/></g>', False)
    if sub:
        _t(f, x + 10, y + 19, title, "h")
        _t(f, x + 10, y + 37, sub)
    else:
        _t(f, x + 10, y + 20, title, "h")
    return x, y, w, h


def _mid(b):
    x, y, w, h = b
    return y + h / 2


# ---- figure 1: six kinds of routing ----

ROUTES = [
    ("①", "按读它的角色选路",
     [("skill", "code-review"), ("skill", "advisor"), ("skill", "dispatch")],
     ["## Find your moment：reviewer 读一份，轴读另一份",
      "advisor：Two moments（请教的人 / advisor 本人）"],
     ["读它的是", "哪个角色？"],
     [("playbook", "Work a ticket", False), ("playbook", "Review a ticket", False), ("reference", "<轴>-reviewer.md")],
     ["角色是一个会话：一份 playbook。角色是派出的 agent：",
      "派它的那一步把 reference 当提示词交给它"]),
    ("②", "按调用方走到哪一步选路",
     [("skill", "ui-acceptance"), ("skill", "verify-ticket"), ("skill", "design-pages")],
     ["Writing a page ticket's code, before the first line",
      "Cutting something out of the ticket"],
     ["调用方此刻", "在做什么？"],
     [("playbook", "Work a ticket 第 2 步", False), ("reference", "writing-interface-code.md", True, True)],
     ["那一步直接点名文件，表删掉。几份 playbook 都读的，",
      "留在管那件东西的技能里，由各份点名"]),
    ("③", "按脚本刚打印的那行选路",
     [("skill", "ui-acceptance"), ("reference", "pull.md")],
     ["Reading the DIFF line the story oracle printed",
      "pull-report.md 的 改动分类 决定下一份"],
     ["这行输出", "该去哪读？"],
     [("script", "story-parity.py", True, True), ("script", "refusal.py")],
     ["输出行自己写明去读哪个文件、哪一节。lease.py 的",
      "拒绝已经这样做：每条拒绝都写下一步"]),
    ("④", "做完以后交给谁",
     [("skill", "to-spec"), ("skill", "write-screen-contract")],
     ["## Next：The to-tickets skill.",
      "## Next：第一次写交 to-spec，重写交 revising-a-spec.md"],
     ["做完之后", "谁接着？"],
     [("playbook", "Write a spec 最后一步：Run Cut tickets", False)],
     ["调用方 playbook 的最后一步用名字调用下一份。",
      "技能交回自己的产出就停"]),
    ("⑤", "跨会话的事做到哪了",
     [("skill", "wayfinder")],
     ["## Invocation：Two modes",
      "Chart the map / Work through the map"],
     ["这件事现在", "做到哪了？"],
     [("playbook", "Chart a map", False, True), ("playbook", "Resolve a map ticket", False, True)],
     ["触发不同就是两份 playbook。mode 的路由行按 tracker",
      "上的状态把会话送到其中一份"]),
    ("⑥", "按手上的输入分支",
     [("skill", "manage-agents-md"), ("skill", "prototype")],
     ["## Find your situation：create / rewrite",
      "## Pick a branch：LOGIC / UI / EXP"],
     ["手上的输入", "是哪一种？"],
     [("skill", "manage-agents-md", True, True), ("skill", "prototype", True, True)],
     ["留在技能里：同一件事，交回同一种东西，",
      "调用方不变，只是做法随输入不同"]),
]


def routes():
    f = Fig("m61", 1000)
    _t(f, 40, 20, "v2 技能里的样子", "h")
    _t(f, 505, 20, "它在问", "h", "middle")
    _t(f, 600, 20, "v3 里去哪", "h")
    BH, Y0 = 108, 34
    f.zone(4, Y0, 992, 5 * BH + 6, "")
    f.zone(4, Y0 + 5 * BH + 18, 992, BH + 4, "")
    _t(f, 990, Y0 + 18, "搬出技能：调用方的事，写在调用方那边", "s", "end")
    _t(f, 990, Y0 + 5 * BH + 36, "留在技能里", "s", "end")
    _t(f, 990, Y0 + 6 * BH + 40, "虚线：还没搬进 v3 的", "s", "end")
    for i, (num, name, lchips, ltext, q, rchips, rtext) in enumerate(ROUTES):
        y = Y0 + 12 + i * BH + (12 if i == 5 else 0)
        _numdot(f, 24, y + 14, num)
        _t(f, 42, y + 19, name, "h")
        _chips(f, 42, y + 28, lchips)
        for j, line in enumerate(ltext):
            _t(f, 42, y + 70 + j * 15, line)
        f.dia(505, y + 50, 72, 34, q)
        f.ar([(420, y + 50), (431, y + 50)])
        f.ar([(579, y + 50), (596, y + 50)])
        _chips(f, 600, y + 10, rchips)
        for j, line in enumerate(rtext):
            _t(f, 600, y + 56 + j * 15, line)
    return f.svg(Y0 + 6 * BH + 48, "v2 技能里六种路由，各在问什么，在 v3 里去哪。① 按读它的角色选路，例如 code-review、advisor、dispatch 的表：会话的角色成为一份 playbook，派出的 agent 由派它的那一步把 reference 当提示词交给它。② 按调用方走到哪一步选路，例如 ui-acceptance、verify-ticket、design-pages 的表：那一步直接点名文件，几份 playbook 都读的留在管那件东西的技能里。③ 按脚本刚打印的那行选路，例如 story oracle 的 DIFF 行、pull 报告的改动分类：输出行自己写明去哪读。④ 做完以后交给谁，例如 to-spec 的 ## Next：调用方 playbook 的最后一步用名字调用下一份。⑤ 跨会话的事做到哪了，例如 wayfinder 的两种模式：触发不同就是两份 playbook。⑥ 按手上的输入分支，例如 manage-agents-md 的 create 和 rewrite、prototype 的三个分支：留在技能里。虚线是还没搬进 v3 的：writing-interface-code.md、story-parity.py、Write a spec、Chart a map、Resolve a map ticket、manage-agents-md、prototype。")


# ---- figure 2: MMW's work cut into playbooks ----

def _pb_lines(f, x, y, w, title, lines, dashed=False):
    """A playbook box with its name and several short lines under it; returns (x, y, w, h)."""
    h = 30 + 17 * len(lines)
    f.e(f'<g class="k-playbook"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"'
        + (' style="stroke-dasharray:6 3"' if dashed else '') + '/></g>', False)
    _t(f, x + 10, y + 19, title, "h")
    for i, line in enumerate(lines):
        _t(f, x + 10, y + 37 + i * 17, line)
    return x, y, w, h


def net():
    f = Fig("m62", 1000)
    H = 838
    f.zone(8, 8, 330, H, "白天 · 你在场")
    f.e(f'<rect class="zone open" x="362" y="8" width="330" height="{H}" rx="6"/>', False)
    _t(f, 374, 27, "夜里 · 你不在", "h")
    f.zone(712, 8, 280, H, "早上 · 你在场")

    DX, DW = 36, 288
    chart = _pb(f, DX, 40, DW, "Chart a map", "一个会话画完地图", dashed=True)
    resolve = _pb(f, DX, 110, DW, "Resolve a map ticket", "一个会话只解决地图上的一张票", dashed=True)
    design = _pb(f, DX, 180, DW, "Design pages", "在 Claude Design 里画页、处理评论", dashed=True)
    pull = _pb(f, DX, 250, DW, "Pull a design", "把签了字的设计包拉进仓库", dashed=True)
    wsc = _pb(f, DX, 334, DW, "Write the screen contract", "写 screen-contract.yaml", dashed=True)
    spec = _pb(f, DX, 404, DW, "Write a spec", "spec 的模板在这一份里")
    cut_ = _pb(f, DX, 474, DW, "Cut tickets", "切票、问你定；票的格式照 verify-ticket")
    rev = _pb_lines(f, DX, 558, DW, "Revise a spec",
                    ["改已发布 spec 里的一个决定。调用它的：",
                     "Run a night 的 contract 子票一节、", "Cut tickets、Write a spec、Triage"])
    build = _pb(f, DX, 656, DW, "Build a design system", "你要建设计系统时；不在主线上", dashed=True)
    bug = _pb(f, DX, 722, DW, "Bug fix", "你报来的缺陷：诊断，写一张票，Run one ticket")
    _pb(f, DX, 788, DW, "Make a small change", "一个会话做完：测试、验证、第二个读者、推")

    def down(a, b, label=None, cls="", x=160):
        f.ar([(x, a[1] + a[3]), (x, b[1] - 2)], cls=cls)
        if label:
            _t(f, x + 8, (a[1] + a[3] + b[1]) / 2 + 4, label)

    down(chart, resolve, "之后每个会话")
    down(resolve, design, "地图上的设计票")
    down(design, pull, "你签字", "human")
    down(pull, wsc)
    _t(f, 168, pull[1] + pull[3] + 14, "没有 screen contract，")
    _t(f, 168, pull[1] + pull[3] + 29, "或增删了控件")
    down(wsc, spec, "第一次写")
    down(spec, cut_, "最后一步 Run Cut tickets")
    down(cut_, rev, "你答的问题改了决定")
    f.ar([(DX, _mid(resolve)), (18, _mid(resolve)), (18, _mid(spec)), (DX - 2, _mid(spec))], cls="human")
    for i, ch in enumerate("地图清了你开新会话"):
        _t(f, 23, _mid(resolve) + 60 + i * 15, ch, "lbl")

    NX, NW = 376, 302
    run = _pb_lines(f, NX, 40, NW, "Run a night",
                    ["orchestrator 一个会话，从 open 到 finish",
                     "1–5 开夜、advance、每次叫醒",
                     "6–8 收尾：finding 定去处、reverify、summary",
                     "9 retro　10 你验收后 finish",
                     "11 流水线自己坏了：suspend",
                     "两节：contract 子票怎样定，",
                     "一条 finding 怎样分流"])
    work = _pb_lines(f, NX, 254, NW, "Work a ticket",
                     ["worker 一个会话：认领、写代码、跑判据、",
                      "开 reviewer，按报告修或驳回，关票"])
    rv = _pb(f, NX, 390, NW, "Review a ticket", "reviewer：沿几条轴审 diff，交一份报告")
    one = _pb_lines(f, NX, 500, NW, "Run one ticket",
                    ["夜外的一张票，一个会话守到落地；",
                     "叫醒和 contract 子票两节借 Run a night"])

    # day to night: you start the night; a bug fix runs one ticket
    f.ar([(DX + DW, _mid(cut_)), (344, _mid(cut_)), (344, 70), (NX - 2, 70)], cls="human")
    for i, ch in enumerate("你说开始今晚"):
        _t(f, 349, 160 + i * 15, ch, "lbl")
    f.ar([(DX + DW, _mid(bug)), (354, _mid(bug)), (354, _mid(one)), (NX - 2, _mid(one))])

    # inside the night
    f.ar([(600, run[1] + run[3]), (600, work[1] - 2)])
    _t(f, 592, run[1] + run[3] + 38, "advance 开 worker", "s", "end")
    f.ar([(NX, _mid(work)), (368, _mid(work)), (368, run[1] + run[3] - 20), (NX - 2, run[1] + run[3] - 20)])
    _t(f, 384, run[1] + run[3] + 18, "关票后叫醒：ticket.passed")
    f.ar([(420, work[1] + work[3]), (420, rv[1] - 2)])
    _t(f, 428, work[1] + work[3] + 20, "start reviewer")
    f.ar([(640, rv[1]), (640, work[1] + work[3] + 2)])
    _t(f, 632, work[1] + work[3] + 40, "叫醒同一个 worker：", "s", "end")
    _t(f, 632, work[1] + work[3] + 56, "reviewer.reported", "s", "end")
    f.att([(NX + NW, _mid(one)), (686, _mid(one)), (686, run[1] + 120), (NX + NW + 2, run[1] + 120)])

    MX, MW = 724, 256
    f.ar([(NX + NW, 64), (MX - 2, 64)])
    _t(f, MX, 60, "你读 NIGHT SUMMARY", "h")
    _t(f, MX, 78, "和 NIGHT RETRO")
    f.ar([(MX - 4, 118), (NX + NW + 2, 118)], cls="human")
    _t(f, MX, 114, "你说验收：同一个会话")
    _t(f, MX, 132, "跑 Run a night 第 10 步的 finish")
    _t(f, MX, 168, "交回、留在 needs-triage 的票：")
    _pb(f, MX, 178, MW, "Triage", "你挑，逐张用 triage 技能判")
    _t(f, MX, 244, "agent 做的进 spec：Write a spec，")
    _t(f, MX, 262, "或 Revise a spec 再 Cut tickets")
    for i, name in enumerate(["Authoring or modifying a skill", "Review the skill set", "Pause safely"]):
        _pb(f, MX, 300 + i * 40, MW, name)
    _t(f, MX, 432, "已在 v3，不在这一课的范围")
    _pb(f, MX, 456, MW, "Investigation", "只读，交回带出处的答案；用 how、why")
    _t(f, MX, 530, "接入一个仓库，第一次和每次体检：")
    _chip(f, "skill", MX, 540, "setup-mmw", dashed=True)
    _t(f, MX, 584, "配齐仓库、产品、机器三层；")
    _t(f, MX, 602, "配不了的告诉你在哪里点什么")
    _t(f, MX, 642, "虚线框：还没写或还没搬")
    _t(f, MX, 660, "虚线箭头：同类兄弟之间按节借")
    _t(f, MX, 710, "一个会话从开始做到交付的，是一份")
    _t(f, MX, 728, "playbook。叫醒和你开口都回到同一个")
    _t(f, MX, 746, "会话，所以这两处都不切开。")
    return f.svg(H + 16, "MMW 拆成的 playbook，虚线框是还没写的。白天你在场：Chart a map 画地图，之后每个会话 Resolve a map ticket 解决一张；地图上的设计票走 Design pages，你签字后 Pull a design，没有 screen contract 或增删控件时 Write the screen contract，第一次写就接着 Write a spec；地图清了你开新会话 Write a spec；Write a spec 最后一步 Run Cut tickets；你答的问题改了决定时 Run Revise a spec。以上 Write a spec、Cut tickets、Revise a spec 已写；Revise a spec 由 Run a night 的 contract 子票一节、Cut tickets、Write a spec 和 Triage 调用。Build a design system 不在主线上。你报来的缺陷走 Bug fix：诊断，写一张票，Run one ticket。一个会话做得完的小改动走 Make a small change：测试、验证、第二个读者、推到 base 分支。你说开始今晚，进夜里。夜里你不在：Run a night 是 orchestrator 一个会话，从 open 到 finish，十一步：开夜、advance、每次叫醒，收尾时给 finding 定去处、reverify、summary，retro，你验收后 finish，流水线坏了时 suspend；另有 contract 子票和 finding 分流两节；advance 开 worker 做 Work a ticket，worker 一个会话从认领到关票，中间 start reviewer 做 Review a ticket，reviewer.reported 叫醒同一个 worker；关票后 ticket.passed 叫醒 Run a night。Run one ticket 是夜外的一张票，叫醒和 contract 子票两节借 Run a night。早上你在场：你读 NIGHT SUMMARY 和 NIGHT RETRO，说验收，同一个 orchestrator 会话跑 Run a night 第 10 步的 finish；交回、留在 needs-triage 的票，你在任何会话里走 Triage：挑出要判的，逐张用 triage 技能判；agent 做的进 spec，走 Write a spec，或 Revise a spec 再 Cut tickets。右栏另有：Investigation，只读，用 how 和 why 交回带出处的答案；接入仓库用 setup-mmw 技能，配齐仓库、产品、机器三层，还没做。")


# ---- figure 3: where each v2 skill's text goes ----

# A playbook written in v3 is a plain string; one not written yet is ("todo", name).
FATES_A = [
    ([("reference", "dispatch/references/night.md")], ["Run a night"],
     "dispatch 留下：脚本、换模型、## On waking"),
    ([("reference", "dispatch/references/one-ticket.md")], ["Run one ticket"], "同上"),
    ([("skill", "implement")], ["Work a ticket"], "删掉；界面代码那份 reference 等界面验收"),
    ([("reference", "code-review/references/session.md")], ["Review a ticket"], "code-review 留下三条轴"),
    ([("skill", "to-tickets")], ["Cut tickets"], "票的格式进 verify-ticket；歧义扫描提示进 mmw-mode"),
    ([("skill", "to-spec")], ["Write a spec", "Revise a spec"], "spec 模板在 Write a spec 里"),
    ([("skill", "triage")], ["Triage"], "triage 留下：角色、逐张判断、模板"),
    ([("skill", "wayfinder")], [("todo", "Chart a map"), ("todo", "Resolve a map ticket")], "还没搬"),
    ([("skill", "design-pages")], [("todo", "Design pages"), ("todo", "Pull a design"), ("todo", "Build a design system")],
     "还没搬"),
    ([("skill", "write-screen-contract")], [("todo", "Write the screen contract")], "还没搬"),
    ([("skill", "setup-matt-pocock-skills")], [("skill", "setup-mmw")], "还没做：由它配齐整个仓库"),
]

# (name, what it does, in v3 yet)
VERBS = [
    ("grilling", "问到每个决定都定下", True), ("domain-modeling", "定词、写 ADR", True),
    ("research", "查一手来源，写研究文件", True), ("prototype", "写代码回答一个设计问题", False),
    ("tdd", "先红后绿", True), ("diagnosing-bugs", "复现、定因", True),
    ("code-review", "沿三条轴审 diff", True), ("ui-acceptance", "判定界面和设计一致；判官没搬", True),
    ("advisor", "请教一次", True), ("retro", "复盘一夜", True),
    ("triage", "逐张判 issue，含夜里交回的票", True),
]


def fates():
    f = Fig("m63", 1000)
    _t(f, 16, 22, "v2 的来源", "h")
    _t(f, 330, 22, "做法成为的 playbook", "h")
    _t(f, 656, 22, "技能留下什么", "h")
    # lay out first, so the zone can be drawn behind the rows; a row's playbooks wrap before x 646
    placed, y = [], 58
    for src, pbs, keep in FATES_A:
        x, ry, row = 330, y, []
        for pb in pbs:
            w = tw(pb if isinstance(pb, str) else pb[1], 11.5, False) + 24
            if x + w > 646:
                x, ry = 330, ry + 30
            row.append((x, ry, pb))
            x += w + 5
        placed.append((src, y, row, keep))
        y = ry + 34
    ha = y - 30
    f.zone(4, 30, 992, ha, "A　一种任务的做法：搬进 playbook；技能只留下它管的那件东西。虚线：还没写")
    for src, y, row, keep in placed:
        _chips(f, 16, y, src)
        f.ar([(302, y + 12), (326, y + 12)])
        for x, ry, pb in row:
            if isinstance(pb, tuple) and pb[0] == "todo":
                _chip(f, "playbook", x, ry, pb[1], mono=False, dashed=True)
            elif isinstance(pb, tuple):
                _chip(f, pb[0], x, ry, pb[1], dashed=True)
            else:
                _chip(f, "playbook", x, ry, pb, mono=False)
        _t(f, 656, y + 16.5, keep)
    by = 30 + ha + 12
    hb = 36 + 6 * 34 + 6
    f.zone(4, by, 992, hb, "B　一个动词：不知道谁在用它，由 playbook 的步骤点名。虚线：还没搬")
    for i, (name, what, there) in enumerate(VERBS):
        col, r = i // 6, i % 6
        x0, y = 16 + col * 496, by + 32 + r * 34
        _chip(f, "skill", x0, y, name, dashed=not there)
        _t(f, x0 + 236, y + 16.5, what)
    cy = by + hb + 12
    hc = 82
    f.zone(4, cy, 992, hc, "C　其余的技能：路由很少，多是自己内部的先后。虚线的还没搬，搬时写到用它的 playbook 里逐条判")
    D = [("to-questionnaire", True), ("grill-with-docs", False), ("codebase-design", False),
         ("improve-codebase-architecture", False), ("manage-agents-md", False), ("code-checkers", False),
         ("exe-release", False), ("writing-for-agents", True), ("teach", True), ("handoff", True),
         ("wait-what", True), ("wizard", False), ("diagram-design", True)]
    x, y = 16, cy + 30
    for name, there in D:
        w = tw(name, 11.5, True) * 1.1 + 18
        if x + w > 988:
            x, y = 16, y + 28
        x = _chip(f, "skill", x, y, name, dashed=not there) + 6
    dy = cy + hc + 12
    E = [
        ([("reference", "dispatch/references/inside-a-ticket.md")], "自己捡起一张票的会话；worker 只由派发开"),
        ([("script", "dispatch.sh adopt")], "命令、函数和两个测试场景都删了"),
        ([("skill", "verify-ticket 的 ## Find your moment、## Reached from here", False)], "路由；换成一句话，点名它的三份 reference"),
        ([("skill", "grill-me")], "只有一句「去读 grilling 照做」；你定了删掉"),
        ([("skill", "resolving-merge-conflicts")], "上游已删；解冲突的规矩在 Work a ticket 第 3 步"),
    ]
    hd = 36 + len(E) * 34 + 6
    f.zone(4, dy, 992, hd, "D　删掉的")
    for i, (src, why) in enumerate(E):
        y = dy + 32 + i * 34
        x = _chips(f, 16, y, src)
        _t(f, max(x + 8, 420), y + 16.5, why)
    return f.svg(dy + hd + 8, "v2 每个技能的文字去哪，虚线是还没写或还没搬的。A 一种任务的做法搬进 playbook，技能只留下它管的那件东西的格式、规则和脚本：night.md 成为 Run a night，one-ticket.md 成为 Run one ticket，dispatch 留下脚本、换模型和 On waking；implement 成为 Work a ticket，技能删掉，写界面代码那份 reference 等界面验收那一课；code-review 的 session.md 成为 Review a ticket，code-review 留下三条轴；to-tickets 成为 Cut tickets，票的格式进 verify-ticket，歧义扫描的提示进 mmw-mode；to-spec 成为 Write a spec 和 Revise a spec；triage 里交给下一步的那几句成为 Triage，技能留下角色、逐张判断和模板；wayfinder、design-pages、write-screen-contract 还没搬；setup-mmw 还没做。B 一个动词，由 playbook 的步骤点名：已搬 grilling、domain-modeling、research、tdd、diagnosing-bugs、code-review、ui-acceptance（判官没搬）、advisor、retro、triage；还没搬 prototype。C 其余技能：已搬 to-questionnaire、writing-for-agents、teach、handoff、wait-what、diagram-design；还没搬 grill-with-docs、codebase-design、improve-codebase-architecture、manage-agents-md、code-checkers、exe-release、wizard。D 删掉的：v2 的 inside-a-ticket.md，dispatch.sh 的 adopt，verify-ticket 的两节路由，grill-me，以及上游已删的 resolving-merge-conflicts。")


def _box_lines(f, kind, x, y, w, title, lines, mono_title=True):
    h = 30 + len(lines) * 17
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>', False)
    _t(f, x + 12, y + 20, title, "m" if mono_title else "h")
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 39 + i * 17, line)
    return h


# ---- figure 5: agents a skill sends out ----

def sent():
    f = Fig("m65", 1000)
    f.e('<line class="div" x1="498" y1="10" x2="498" y2="420"/>')
    _t(f, 10, 22, "派出的 agent 先读技能，再在技能里按角色选路", "h")
    _t(f, 512, 22, "派它的一方只交给它自己那一份", "h")
    lanes = [
        ("code-review 的一个轴（v2）",
         ["Use the code-review skill to review", "ticket #n from base commit <b>, axis Standards."],
         [("skill", "code-review"), ("other", "按轴名查表", True), ("reference", "standards-reviewer.md")],
         "Review a ticket、Make a small change：跑几条轴",
         [("skill", "code-review"), ("reference", "references/standards-reviewer.md")],
         ["code-review 给每条轴开一个通用子代理，提示词就是", "那条轴的 reference，填上请求（ticket #n，或 the", "request in <path>）和 base commit"]),
        ("advisor（v2）",
         ["Use the advisor skill.", "+ brief"],
         [("skill", "advisor"), ("other", "Two moments", True), ("reference", "advising.md")],
         "任何 agent：dispatch.sh brief advisor <文件>",
         [("script", "dispatch.sh brief advisor"), ("reference", "references/advising.md")],
         ["dispatch.sh 照 roles.json 把 advising.md 放在 brief", "前面，末尾加交回说明；文件不在就拒绝开。", "advisor/SKILL.md 只写请教的那一边"]),
        ("researcher（一度加进 v3 的做法，已删）",
         ["Use the research skill.", "+ brief"],
         [("skill", "research"), ("other", "If … started", True), ("reference", "researching.md")],
         "how、why：dispatch.sh brief researcher <文件>",
         [("skill", "research")],
         ["开工第一句是 Use the research skill.（roles.json", "的 lead），接着是填好的 explorer 或 investigator", "模板；何时派、查哪里，写在 how 和 why 里"]),
    ]
    for i, (who, prompt, v2chain, step, v3chips, v3text) in enumerate(lanes):
        y = 40 + i * 128
        _t(f, 10, y + 14, who, "h")
        f.e(f'<g class="k-agent"><rect class="box" x="10" y="{y + 22}" width="300" height="{18 + 16 * len(prompt)}" rx="4"/></g>')
        for j, line in enumerate(prompt):
            _t(f, 20, y + 40 + j * 16, line, "m")
        cx, cy = 10, y + 76
        for k, (kind, label, *rest) in enumerate(v2chain):
            nx = _chip(f, kind, cx, cy, label, mono=not rest)
            if k < len(v2chain) - 1:
                f.ar([(nx + 2, cy + 12), (nx + 16, cy + 12)])
            cx = nx + 20
        _chip(f, "playbook", 512, y + 4, step, mono=False)
        _chips(f, 512, y + 36, v3chips)
        for j, line in enumerate(v3text):
            _t(f, 512, y + 78 + j * 15, line)
    return f.svg(432, "派出的 agent 怎样拿到自己那一份。左边是避开的做法：code-review 的轴拿到一句 Use the code-review skill … axis Standards，读 code-review/SKILL.md，在表里按轴名找到 standards-reviewer.md；advisor 拿到 Use the advisor skill 加 brief，在 Two moments 表里找到 advising.md；researcher 拿到 Use the research skill 加 brief，再按 If that is how you were started 找到 researching.md，这张表是一度加进 v3 的，已删。右边是现在：Review a ticket 和 Make a small change 用 code-review 跑几条轴，code-review 给每条轴开一个通用子代理，提示词就是那条轴的 reference，填上请求和 base commit；dispatch.sh brief advisor 照 roles.json 把 advising.md 放在 brief 前面、末尾加交回说明；how 和 why 用 dispatch.sh brief researcher，开工第一句是 Use the research skill.，接着是填好的模板。")


# ---- Investigation's wiring, which kind an agent is, a how question's two wakes ----

def wiring():
    f = Fig("m71", 1000)
    _t(f, 10, 20, "从你的一个问题到交回的答案", "h")

    # mmw-mode
    f.zone(4, 34, 290, 196, "mmw-mode/SKILL.md")
    _box_lines(f, "mode", 16, 64, 266, "## Non-negotiables", ["不小的改动、架构决定、「我们确定吗」", "→ how，不论在哪份 playbook 里"])
    _box_lines(f, "mode", 16, 148, 266, "## Playbooks", ["Investigation 的路由行：只读的问题，", "怎么工作、为什么这样、确定吗、选哪个"])

    # the playbook
    hp = _box_lines(f, "playbook", 330, 64, 300, "playbooks/investigation.md",
                    ["1  走 how；问的是动机，也走 why",
                     "2  写成 how 的五节，或带取舍表的建议",
                     "3  回复过 unslop",
                     "不提交，不开票",
                     "Reply：照 Writing the reply 写给你，",
                     "讲它做什么、为什么、对产品意味着什么"])
    f.ar([(282, 180), (326, 180)])

    # the skills it routes through
    h1 = _box_lines(f, "skill", 680, 40, 310, "how", ["简单的问题：1 个 explainer 边查边讲", "复杂的问题：2 到 4 个 researcher 分头查，", "再 1 个 explainer 汇总"])
    h2 = _box_lines(f, "skill", 680, 40 + h1 + 12, 310, "why", ["先钉住代码和提交", "每类有来源的证据 1 个 researcher，", "再 1 个 synthesizer 分清查到和推断"])
    uy = 40 + h1 + 12 + h2 + 12
    _chip(f, "skill", 680, uy, "unslop")
    f.ar([(630, 92), (676, 70)])
    f.ar([(630, 112), (676, 40 + h1 + 12 + 40)])
    f.ar([(630, 132), (676, uy + 12)])
    f.ar([(282, 96), (306, 96), (306, 28), (835, 28), (835, 37)])
    _t(f, 500, uy + 46, "每个都是 dispatch.sh brief 开的独立会话，模型照 models.json 里它的角色")
    _t(f, 500, uy + 63, "brief 结尾写明只读，只许跑交回的那一条命令；why 的不进只读模式，以免没有 MCP")

    # hand back
    by = uy + 80
    f.zone(4, by, 992, 72, "要改代码时：不改，交回你，转 Bug fix 或 Make a small change；要你做产品决定的，转 Write a spec")
    x = 16
    for name, dashed in (("Bug fix", False), ("Make a small change", False), ("Write a spec", False)):
        x = _chip(f, "playbook", x, by + 34, name, mono=False, dashed=dashed) + 10
    f.ar([(480, 64 + hp), (480, by)])

    # other users
    cy = by + 72 + 12
    rows = [
        ("Bug fix 第 2 步", "how 看出问题的那一块，why 查是哪次改动引入的", False),
        ("Make a small change", "不点名：改动不小时，Non-negotiables 那一行管", False),
        ("Write a spec", "不点名：碰到架构决定时，Non-negotiables 那一行管", False),
        ("Chart a map", "决定碰到现有代码时 how，要知道当初为什么时 why", True),
        ("Work a ticket（夜里的 worker）", "不接：票的 ## Read first 已经列好要读的", False),
    ]
    f.zone(4, cy, 992, 36 + len(rows) * 30 + 4, "其他用 how 和 why 的地方（虚线：还没写）")
    for i, (who, what, dashed) in enumerate(rows):
        y = cy + 32 + i * 30
        _chip(f, "playbook", 16, y, who, mono=False, dashed=dashed)
        _t(f, 300, y + 16.5, what)
    H = cy + 36 + len(rows) * 30 + 12
    return f.svg(H, "从你的一个问题到交回的答案。mmw-mode 的 ## Playbooks 有一行路由，把只读的问题（怎么工作、为什么这样、确定吗、选哪个）送进 playbooks/investigation.md；## Non-negotiables 有一行触发，不小的改动、架构决定和「我们确定吗」在任何 playbook 里都用 how。Investigation 三步：走 how，问动机时也走 why；写成 how 的五节或带取舍表的建议；回复过 unslop。不提交、不开票，回复照 Writing the reply 写给你。how 简单问题开 1 个 explainer，复杂问题开 2 到 4 个 researcher 再开 1 个 explainer 汇总；why 先钉住代码和提交，每类有来源的证据开 1 个 researcher，再开 1 个 synthesizer。每个都是 dispatch.sh brief 开的独立会话，模型照 models.json 里它的角色；brief 结尾写明只读。要改代码时交回你，转 Bug fix 或 Make a small change，要你做产品决定的转 Write a spec。其他用 how 和 why 的地方：Bug fix 第 2 步；Make a small change 不点名，改动不小时由 Non-negotiables 那一行管；Write a spec 不点名，碰到架构决定时由 Non-negotiables 那一行管；还没写的 Chart a map；夜里的 worker 不接。")


def roles():
    f = Fig("m72", 1000)
    _t(f, 10, 20, "要开一个 agent 干活之前，依次问三个问题", "h")
    qs = [
        ("1", "会话自己在这个回合里能不能做，自己读就够？", "能：不开 agent，会话自己做"),
        ("2", "要不要自己的模型，或者在这个回合之外独立跑？", "要：独立会话（session），dispatch.sh 开"),
        ("3", "其余：要几份同时做，或要一个没被会话思路影响过的上下文", "子代理（subagent），宿主的通用子代理，跟会话同一个模型"),
    ]
    for i, (n, q, a) in enumerate(qs):
        y = 38 + i * 50
        f.e(f'<circle cx="22" cy="{y + 15}" r="11" fill="var(--ink2)"/>'
            f'<text x="22" y="{y + 19.5}" text-anchor="middle" style="fill:var(--surface);font-size:12px;font-weight:700">{n}</text>')
        _t(f, 42, y + 20, q, "h")
        _t(f, 470, y + 20, a)
    y0 = 200
    f.zone(4, y0, 492, 222, "独立会话：dispatch.sh 开，交回走中继")
    rows = [("worker", "junior、senior 两种：写代码，关票"), ("reviewer", "审一张票"), ("advisor", "对一个决定给第二意见"),
            ("researcher", "读来源，交回带出处的发现"), ("explainer", "把发现写成「怎么工作」的说明"),
            ("synthesizer", "把发现分成查到、推断、不知道")]
    for i, (name, what) in enumerate(rows):
        y = y0 + 32 + i * 29
        _chip(f, "agent", 16, y, name)
        _t(f, 150, y + 16.5, what)
    f.zone(504, y0, 492, 222, "子代理：技能或 playbook 在会话里派，当场交回")
    _chip(f, "agent", 516, y0 + 32, "code-review 的轴")
    _t(f, 690, y0 + 48.5, "三条轴同时审一段 diff")
    _chip(f, "agent", 516, y0 + 64, "grilling 的 fact-finder")
    _t(f, 720, y0 + 80.5, "查一个问题要用的事实")
    _chip(f, "agent", 516, y0 + 96, "ambiguity scanner")
    _t(f, 690, y0 + 112.5, "Cut tickets 派：找草稿漏掉的决定")
    _t(f, 516, y0 + 146, "要换模型的角色都不在这一边：Codex 默认把子代理的")
    _t(f, 516, y0 + 163, "模型参数藏起来，Claude Code 只能选系列；独立会话")
    _t(f, 516, y0 + 180, "用命令行参数指定模型，五个宿主都管用。")
    _t(f, 516, y0 + 204, "每个角色在 dispatch/roles.json 有一行。")
    return f.svg(y0 + 230, "要开一个 agent 干活之前依次问三个问题。一，会话自己在这个回合里能不能做、自己读就够，能就不开。二，要不要自己的模型或在回合之外独立跑，要就做成独立会话，由 dispatch.sh 开。三，其余情况，要几份同时做或要一个干净的上下文，做成子代理，跟会话同一个模型。独立会话有 worker（junior、senior）、reviewer、advisor、researcher、explainer、synthesizer。子代理有 code-review 的轴、grilling 的 fact-finder 和 Cut tickets 派的 ambiguity scanner。要换模型的角色都不做成子代理，因为 Codex 默认藏起子代理的模型参数，Claude Code 只能选系列，独立会话用命令行参数指定模型，五个宿主都管用。每个角色在 dispatch/roles.json 有一行。")


def howflow():
    f = Fig("m73", 1000)
    _t(f, 10, 20, "一个复杂的 how 问题：会话被叫醒两次，每次一条", "h")
    steps = [
        ("Investigation 会话", ["dispatch.sh brief", "researcher × 3，同一批", "然后结束回合"], "playbook"),
        ("3 个 researcher 会话", ["各用自己的宿主和模型", "读代码的一个侧面", "做完跑 report"], "agent"),
        ("本机状态目录", ["briefs/<批>/<brief>/", "result.md 和 reported", "加锁写"], "config"),
        ("中继，每 30 秒", ["一批全交了或有人 lost", "才排一行唤醒：", "brief <批> done"], "script"),
        ("runner 的 send", ["把这一行送进会话；", "会话正在回合里，", "留到下一轮再送"], "script"),
    ]
    xs = [10, 210, 410, 600, 800]
    for (title, lines, kind), x in zip(steps, xs):
        _box_lines(f, kind, x, 40, 186 if x != 410 else 176, title, lines, mono_title=False)
    for a, b in zip(xs, xs[1:]):
        w = 186 if a != 410 else 176
        f.ar([(a + w, 79), (b - 4, 79)])
    _box_lines(f, "playbook", 10, 150, 380, "会话醒来（第 1 次）", ["读 3 份结果，ack；", "dispatch.sh brief explainer，附 3 份结果的路径；结束回合"], mono_title=False)
    _box_lines(f, "agent", 420, 150, 260, "explainer 会话", ["核对发现，写成五节的说明", "report，中继再叫醒一次"], mono_title=False)
    _box_lines(f, "playbook", 710, 150, 280, "会话醒来（第 2 次）", ["对照代码核实，照 Writing the reply 写给你；", "brief close：删掉这一批的目录"], mono_title=False)
    f.ar([(893, 121), (893, 134), (200, 134), (200, 146)])
    f.ar([(390, 183), (416, 183)])
    f.ar([(680, 183), (706, 183)])
    f.zone(4, 250, 992, 100, "子会话出事时")
    _t(f, 16, 288,"死了，没交：看门进程 watchdog.py 问 runner，答 stopped 就记 lost；一批里有 lost 也算交齐，会话醒来看到是谁")
    _t(f, 16, 310, "活着，结束回合却没交：回合守卫 turn-guard.py 拦一次，告诉它跑 report（claude、codex、grok 能拦，cursor、pi 补发一条）")
    _t(f, 16, 332, "上级不在 runner 里（读不出会话号）：dispatch.sh brief 拒绝开，因为结果落下了也没人被叫醒")
    return f.svg(358, "一个复杂的 how 问题怎样跑。Investigation 会话用 dispatch.sh brief 开 3 个 researcher，同一批，然后结束回合。每个 researcher 在自己的宿主和模型上读代码的一个侧面，做完跑 dispatch.sh report，结果写进本机状态目录 briefs/批/brief/result.md，加锁写。中继每 30 秒读一次，一批全交了或有人判为 lost，才排一行 brief 批 done，经 runner 的 send 送进会话，会话正在回合里就留到下一轮。会话第一次醒来，读 3 份结果，ack，开 explainer，附上 3 份结果的路径，结束回合。explainer 写成五节的说明并 report，中继再叫醒一次。会话第二次醒来，对照代码核实，照 Writing the reply 写给你，brief close 删掉这一批的目录。子会话死了没交，看门进程记 lost；活着却没交就结束回合，回合守卫拦一次；上级不在 runner 里，dispatch.sh brief 拒绝开。")


# ---- the role table, and one batch of briefs from start to close ----

def table():
    f = Fig("m81", 1000)
    _t(f, 10, 20, "一张角色表，两种角色，一条检查管住两头", "h")

    # the table itself
    th = _box(f, "config", 330, 40, 340, "dispatch/roles.json", [
        "session，command start：",
        "  junior-worker、senior-worker、reviewer",
        "session，command brief：",
        "  advisor、researcher、explainer、synthesizer",
        "subagent：",
        "  code-review axis、grilling fact-finder",
        "每行写：做什么、交回什么、谁用它",
    ])

    # adding a session role
    f.zone(4, 34, 314, 300, "加一个独立会话角色：三处")
    y = 66
    for title, lines in (
        ("roles.json 一行", ["kind session，command brief，", "lead 或 brief 模板，sent_by"]),
        ("hosts.json 的 defaults 一行", ["新机器上它用的宿主、模型、effort"]),
        ("它开工读的文字", ["lead 文件，或调用方填的模板"]),
    ):
        y += _box(f, "config" if "json" in title else "reference", 16, y, 290, title, lines,
                  mono_title=False) + 10
    _t(f, 16, y + 14, "自动跟上的：", "h")
    _t(f, 16, y + 34, "models.py 从表里读角色名，install 给缺的", room=296)
    _t(f, 16, y + 51, "角色补上默认行；dispatch.sh brief 读 lead", room=296)
    f.ar([(306, 82), (326, 82)])

    # adding a subagent
    f.zone(682, 34, 314, 300, "加一个子代理角色：两处")
    y = 66
    y += _box(f, "config", 694, y, 290, "roles.json 一行", ["kind subagent，sent_by，", "有模板文件时 prompt 点名它"], mono_title=False) + 10
    y += _box(f, "reference", 694, y, 290, "它的提示词", ["写在派它的技能里；长的放进", "那个技能的 references/"], mono_title=False) + 10
    _t(f, 694, y + 14, "子代理跟会话同一个模型。", room=290)
    _t(f, 694, y + 31, "要换模型的，做成独立会话。", room=290)
    f.ar([(690, 82), (674, 82)])

    # the check
    cy = 350
    checks = [
        "1  每个独立会话角色在 hosts.json 有默认行；defaults 里没有表外的角色",
        "2  表里点名的 lead、brief 模板、prompt 文件都在；lead 技能在",
        "3  sent_by 的技能在，且真的用它：写了 dispatch.sh brief <角色>，或点名了 prompt 文件",
        "4  任何 SKILL.md 和 playbook 写的 dispatch.sh brief <角色>，表里都是 brief 角色",
        "5  派子代理的 SKILL.md（send、spawn、dispatch 后接 subagent 或 sub-agent）是某个子代理行的 sent_by",
    ]
    f.zone(4, cy, 992, 34 + len(checks) * 22 + 8, "check-interfaces.py 第 6 条，每次跑都查")
    for i, line in enumerate(checks):
        _t(f, 16, cy + 46 + i * 22, line, room=970)
    f.ar([(500, 40 + th), (500, cy)])
    H = cy + 34 + len(checks) * 22 + 16
    return f.svg(H, "一张角色表 dispatch/roles.json，两种角色。独立会话角色里，junior-worker、senior-worker、reviewer 由 dispatch.sh start 开，advisor、researcher、explainer、synthesizer 由 dispatch.sh brief 开；子代理角色有 code-review axis 和 grilling fact-finder。加一个独立会话角色要改三处：roles.json 一行，hosts.json 的 defaults 一行，它开工读的文字。models.py 从表里读角色名，install 给缺的角色补默认行，dispatch.sh brief 从表里读开工的文字。加一个子代理角色要改两处：roles.json 一行，以及它的提示词，写在派它的技能里，长的放进那个技能的 references。check-interfaces.py 第 6 条每次都查五件事：会话角色都有默认行；表里点名的文件都在；sent_by 的技能真的用它；技能写的 dispatch.sh brief 角色都在表里；派子代理的技能都在表里。")


LANES = [("上级会话", "playbook"), ("dispatch.sh", "script"), ("briefs/<批>/", "config"),
         ("中继 relay.py", "script"), ("子会话", "agent")]
LANE_W = 196
LANE_X = [4 + i * (LANE_W + 3) for i in range(5)]
LANE_H = 690


def _step(f, lane, y, title, lines, kind=None, mono=True):
    x = LANE_X[lane] + 6
    return _box(f, kind or LANES[lane][1], x, y, LANE_W - 12, title, lines, mono_title=mono)


def life():
    f = Fig("m82", 1000)
    _t(f, 10, 20, "一批 brief 从开到关：两个 researcher", "h")
    top = 34
    for (name, kind), x in zip(LANES, LANE_X):
        f.e(f'<rect class="zone" x="{x}" y="{top}" width="{LANE_W}" height="{LANE_H}" rx="6"/>', False)
        f.e(f'<g class="k-{kind}"><text x="{x + 12}" y="{top + 20}" class="h">{html.escape(name)}</text></g>', False)

    y = top + 34
    _step(f, 0, y, "brief researcher", ["a.md b.md"])
    _step(f, 1, y, "认出上级", ["own_session：读不出", "会话号就拒绝，", "什么也不开"], mono=False)
    _step(f, 2, y, "batch.json", ["角色、份数、", "上级的 runner 和会话号"])
    _step(f, 3, y, "看守 briefs:<批>", ["上级就是这个看守", "的 orchestrator"])
    f.ar([(LANE_X[1] - 3, y + 30), (LANE_X[1] + 4, y + 30)])
    f.ar([(LANE_X[2] - 3, y + 30), (LANE_X[2] + 4, y + 30)])
    f.ar([(LANE_X[3] - 3, y + 30), (LANE_X[3] + 4, y + 30)])

    y += 104
    _step(f, 1, y, "每份 brief 开一个", ["开工的话三段：", "lead（表里写的）", "brief 文件全文", "交回说明"], mono=False)
    _step(f, 2, y, "1/started.json", ["子会话的 runner、", "会话号、模型"])
    _step(f, 4, y, "researcher × 2", ["各在自己的宿主上", "读、查、写答案"], mono=False)
    f.ar([(LANE_X[2] - 3, y + 30), (LANE_X[2] + 4, y + 30)])
    f.ar([(LANE_X[1] + LANE_W - 6, y + 90), (LANE_X[4] + 4, y + 90)])
    _t(f, LANE_X[0] + 10, y + 30, "然后结束回合", "h", room=180)
    _t(f, LANE_X[0] + 10, y + 50, "不轮询，不挂着等", room=180)
    _t(f, LANE_X[1] + 10, y + 120, "开第二份失败：已开的", room=180)
    _t(f, LANE_X[1] + 10, y + 137, "停掉，整批删掉，", room=180)
    _t(f, LANE_X[1] + 10, y + 154, "看守关掉", room=180)

    y += 120 + 58
    _step(f, 4, y, "report <批>/1 x.md", ["只认 started.json", "记的那个会话"])
    _step(f, 2, y, "1/result.md", ["复制过来的答案，", "然后写 reported.json"])
    f.ar([(LANE_X[4] - 3, y + 30), (LANE_X[2] + LANE_W - 2, y + 30)])

    y += 104
    _step(f, 3, y, "每 30 秒看一次", ["两份都 reported", "或 lost：排一行", "brief <批> done，", "写 woken.json"], mono=False)
    _step(f, 0, y, "醒来", ["runner 的 send", "把这一行送进来"], mono=False)
    f.ar([(LANE_X[3] - 3, y + 30), (LANE_X[0] + LANE_W - 2, y + 30)])

    y += 120
    _step(f, 0, y, "brief show <批>", ["每份的状态和", "答案文件路径"])
    _step(f, 1, y, "ack brief <批>", ["中继不再送"])
    f.ar([(LANE_X[1] - 3, y + 30), (LANE_X[1] + 4, y + 30)])
    y += 82
    _step(f, 0, y, "brief close <批>", ["用完再关"])
    _step(f, 1, y, "停掉子会话", ["关掉看守"], mono=False)
    _step(f, 2, y, "整个目录删掉", ["什么也不留"], mono=False)
    f.ar([(LANE_X[1] - 3, y + 30), (LANE_X[1] + 4, y + 30)])
    f.ar([(LANE_X[2] - 3, y + 30), (LANE_X[2] + 4, y + 30)])
    return f.svg(top + LANE_H + 8, "一批 brief 从开到关，以两个 researcher 为例。上级会话跑 dispatch.sh brief researcher a.md b.md。dispatch.sh 先认出上级的会话号，读不出就拒绝，什么也不开；然后在本机状态目录建 briefs/批/batch.json，记下角色、份数和上级；中继开一个看守 briefs:批，上级是它的 orchestrator。dispatch.sh 每份 brief 开一个会话，开工的话三段：表里写的 lead、brief 文件全文、交回说明，并写 1/started.json；上级随后结束回合，不轮询。开第二份失败时，已开的会话停掉，整批删掉，看守关掉。子会话做完跑 dispatch.sh report 批/1 x.md，只认 started.json 记的那个会话，答案复制成 result.md，再写 reported.json。中继每 30 秒看一次，两份都 reported 或 lost 时排一行 brief 批 done，写 woken.json，经 runner 的 send 叫醒上级。上级跑 brief show 看每份的状态和答案文件，ack brief 批，用完后 brief close 批：停掉子会话，关掉看守，删掉整个目录。")


FIGS = {"l6-routes": routes, "l6-net": net, "l6-fates": fates, "l6-sent": sent, "l6-wiring": wiring,
        "l6-roles": roles, "l6-howflow": howflow, "l6-table": table, "l6-life": life}

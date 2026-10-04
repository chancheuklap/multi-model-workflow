"""Figures of lesson 0006: the six kinds of routing in MMW v2's skills, MMW's work cut into playbooks,
where each v2 skill's text goes, and two worked examples (ui-acceptance's table, and the agents a skill
sends out)."""
import html
from kit import Fig, tw


def _t(f, x, y, t, cls="s", anchor="start"):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f.e(f'<text x="{x}" y="{y:.1f}" class="{cls}"{a}>{html.escape(t)}</text>')


def _chip(f, kind, x, y, label, mono=True):
    """kit's chip, with room for a monospace font wider than JetBrains Mono; returns its right edge."""
    w = tw(label, 11.5, mono) * (1.1 if mono else 1.0) + (18 if mono else 24)
    tc = "m" if mono else "s"
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w:.1f}" height="24" rx="4"/>'
        f'<text x="{x+9}" y="{y+16.5}" class="{tc}">{html.escape(label)}</text></g>')
    return x + w


def _chips(f, x, y, items, gap=6):
    """A row of chips, (kind, label[, mono]); returns the x after the last one."""
    for it in items:
        kind, label = it[0], it[1]
        mono = it[2] if len(it) > 2 else True
        x = _chip(f, kind, x, y, label, mono) + gap
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
     [("playbook", "Work a ticket 第 2 步", False), ("reference", "writing-interface-code.md")],
     ["那一步直接点名文件，表删掉。几份 playbook 都读的，",
      "留在管那件东西的技能里，由各份点名"]),
    ("③", "按脚本刚打印的那行选路",
     [("skill", "ui-acceptance"), ("reference", "pull.md")],
     ["Reading the DIFF line the story oracle printed",
      "pull-report.md 的 改动分类 决定下一份"],
     ["这行输出", "该去哪读？"],
     [("script", "story-parity.py"), ("script", "refusal.py")],
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
     [("playbook", "Chart a map", False), ("playbook", "Resolve a map ticket", False)],
     ["触发不同就是两份 playbook。mode 的路由行按 tracker",
      "上的状态把会话送到其中一份"]),
    ("⑥", "按手上的输入分支",
     [("skill", "manage-agents-md"), ("skill", "prototype")],
     ["## Find your situation：create / rewrite",
      "## Pick a branch：LOGIC / UI / EXP"],
     ["手上的输入", "是哪一种？"],
     [("skill", "manage-agents-md"), ("skill", "prototype")],
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
    return f.svg(Y0 + 6 * BH + 28, "v2 技能里六种路由，各在问什么，在 v3 里去哪。① 按读它的角色选路，例如 code-review、advisor、dispatch 的表：会话的角色成为一份 playbook，派出的 agent 由派它的那一步把 reference 当提示词交给它。② 按调用方走到哪一步选路，例如 ui-acceptance、verify-ticket、design-pages 的表：那一步直接点名文件，几份 playbook 都读的留在管那件东西的技能里。③ 按脚本刚打印的那行选路，例如 story oracle 的 DIFF 行、pull 报告的改动分类：输出行自己写明去哪读。④ 做完以后交给谁，例如 to-spec 的 ## Next：调用方 playbook 的最后一步用名字调用下一份。⑤ 跨会话的事做到哪了，例如 wayfinder 的两种模式：触发不同就是两份 playbook。⑥ 按手上的输入分支，例如 manage-agents-md 的 create 和 rewrite、prototype 的三个分支：留在技能里。")


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
    chart = _pb(f, DX, 40, DW, "Chart a map", "一个会话画完地图，派 researcher")
    resolve = _pb(f, DX, 110, DW, "Resolve a map ticket", "一个会话只解决地图上的一张票")
    design = _pb(f, DX, 180, DW, "Design pages", "在 Claude Design 里画页、处理评论")
    pull = _pb(f, DX, 250, DW, "Pull a design", "把签了字的设计包拉进仓库")
    wsc = _pb(f, DX, 334, DW, "Write the screen contract", "写 screen-contract.yaml")
    spec = _pb(f, DX, 404, DW, "Write a spec", "spec 的模板在这一份里")
    cut_ = _pb(f, DX, 474, DW, "Cut tickets", "切票、问你定；票的格式照 verify-ticket")
    rev = _pb_lines(f, DX, 558, DW, "Revise a spec",
                    ["改已发布 spec 里的一个决定。被三份调用：",
                     "Cut tickets、Write the screen contract、", "Run a night 的 contract 子票一节"])
    build = _pb(f, DX, 656, DW, "Build a design system", "你要建设计系统时；不在主线上")
    bug = _pb(f, DX, 722, DW, "Bug fix", "你报来的缺陷：诊断，写一张票，Run one ticket")
    _pb(f, DX, 788, DW, "Make a small change", "一个会话做得完：测试、验证、第二个读者、推")

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
                     "#### 开夜：check、open、查票、第一次 advance",
                     "#### 每次叫醒：按事件处理，再 advance",
                     "#### contract 子票：按权威顺序定",
                     "#### 收尾：每条 finding 定去处，能修的自己修",
                     "#### reverify、summary、retro；你验收后 finish",
                     "#### 流水线自己坏了：suspend"])
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
    _t(f, MX, 132, "跑 Run a night 最后一节的 finish")
    _t(f, MX, 176, "交回、留在 needs-triage 的票：")
    _chip(f, "skill", MX, 186, "triage")
    _t(f, MX, 230, "你在任何会话里用它，不在哪份")
    _t(f, MX, 248, "playbook 里")
    for i, name in enumerate(["Authoring or modifying a skill", "Review the skill set", "Pause safely"]):
        _pb(f, MX, 300 + i * 40, MW, name)
    _t(f, MX, 432, "已在 v3，随时可用，不在这一课的范围")
    _pb(f, MX, 456, MW, "Investigation", "只读，交回带出处的答案；用 how、why")
    _t(f, MX, 530, "接入一个仓库，第一次和每次体检：")
    _chip(f, "skill", MX, 540, "setup-mmw")
    _t(f, MX, 584, "配齐仓库、产品、机器三层；")
    _t(f, MX, 602, "配不了的告诉你在哪里点什么")
    _t(f, MX, 660, "虚线箭头：同类兄弟之间按节借")
    _t(f, MX, 710, "一个会话从开始做到交付的，是一份")
    _t(f, MX, 728, "playbook。叫醒和你开口都回到同一个")
    _t(f, MX, 746, "会话，所以这两处都不切开。")
    return f.svg(H + 16, "MMW 拆成的 playbook。白天你在场：Chart a map 画地图，之后每个会话 Resolve a map ticket 解决一张；地图上的设计票走 Design pages，你签字后 Pull a design，没有 screen contract 或增删控件时 Write the screen contract，第一次写就接着 Write a spec；地图清了你开新会话 Write a spec；Write a spec 最后一步 Run Cut tickets；你答的问题改了决定时 Run Revise a spec，Revise a spec 也被 Write the screen contract 和 Run a night 的 contract 子票一节调用。Build a design system 不在主线上。你报来的缺陷走 Bug fix：诊断，写一张票，Run one ticket。一个会话做得完的小改动走 Make a small change：测试、验证、第二个读者、推到 base 分支。你说开始今晚，进夜里。夜里你不在：Run a night 是 orchestrator 一个会话，从 open 到 finish，分开夜、每次叫醒、contract 子票、收尾、reverify summary retro 和你验收后的 finish、suspend 几节；advance 开 worker 做 Work a ticket，worker 一个会话从认领到关票，中间 start reviewer 做 Review a ticket，reviewer.reported 叫醒同一个 worker；关票后 ticket.passed 叫醒 Run a night。Run one ticket 是夜外的一张票，叫醒和 contract 子票两节借 Run a night。早上你在场：你读 NIGHT SUMMARY 和 NIGHT RETRO，说验收，同一个 orchestrator 会话跑 Run a night 最后一节的 finish；交回、留在 needs-triage 的票，你在任何会话里用 triage 技能处理。右栏另有：Investigation，只读，用 how 和 why 交回带出处的答案；接入仓库用 setup-mmw 技能，配齐仓库、产品、机器三层。")


# ---- figure 3: where each v2 skill's text goes ----

FATES_A = [
    ([("reference", "dispatch/references/night.md")], ["Run a night"],
     "dispatch 留下：脚本、换模型、## On waking"),
    ([("reference", "dispatch/references/one-ticket.md")], ["Run one ticket"], "同上"),
    ([("skill", "implement")], ["Work a ticket"], "删掉；界面代码那份 reference 进 ui-acceptance"),
    ([("reference", "code-review/references/session.md")], ["Review a ticket"], "code-review 留下：几条轴"),
    ([("skill", "to-tickets")], ["Cut tickets"], "票的格式进 verify-ticket；技能删掉"),
    ([("skill", "to-spec")], ["Write a spec", "Revise a spec"], "技能删掉；spec 模板在 Write a spec 里"),
    ([("skill", "wayfinder")], ["Chart a map", "Resolve a map ticket"], "wayfinder 留下：地图格式、票的种类"),
    ([("skill", "design-pages")], ["Design pages", "Pull a design", "Build a design system"],
     "design-pages 留下：页的约定、pull 的脚本"),
    ([("skill", "write-screen-contract")], ["Write the screen contract"], "技能留下：格式和脚本"),
    ([("skill", "setup-matt-pocock-skills")], [("skill", "setup-mmw")], "种子文件搬进 setup-mmw，它配齐整个仓库"),
]

VERBS = [
    ("grilling", "问到每个决定都定下"), ("domain-modeling", "定词、写 ADR"), ("research", "查一手来源，写研究文件"),
    ("prototype", "写代码回答一个设计问题"), ("tdd", "先红后绿"), ("diagnosing-bugs", "复现、定因"),
    ("resolving-merge-conflicts", "解合并冲突"), ("code-review", "沿几条轴审 diff"),
    ("ui-acceptance", "判定界面和设计一致"), ("advisor", "请教一次"), ("retro", "复盘一夜"),
    ("triage", "给 issue 分类，含夜里交回的票"),
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
    f.zone(4, 30, 992, ha, "A　一种任务的做法：搬进 playbook；技能只留下它管的那件东西的格式、规则和脚本")
    for src, y, row, keep in placed:
        _chips(f, 16, y, src)
        f.ar([(302, y + 12), (326, y + 12)])
        for x, ry, pb in row:
            if isinstance(pb, tuple):
                _chip(f, pb[0], x, ry, pb[1])
            else:
                _chip(f, "playbook", x, ry, pb, mono=False)
        _t(f, 656, y + 16.5, keep)
    by = 30 + ha + 12
    hb = 36 + 6 * 34 + 6
    f.zone(4, by, 992, hb, "B　一个动词：不知道谁在用它，由 playbook 的步骤点名")
    for i, (name, what) in enumerate(VERBS):
        col, r = i // 6, i % 6
        x0, y = 16 + col * 496, by + 32 + r * 34
        _chip(f, "skill", x0, y, name)
        _t(f, x0 + 236, y + 16.5, what)
    cy = by + hb + 12
    hc = 82
    f.zone(4, cy, 992, hc, "C　其余的技能：路由很少，多是自己内部的先后；写到用它的那份 playbook 时逐条判")
    D = ["to-questionnaire", "grill-with-docs", "codebase-design", "improve-codebase-architecture",
         "manage-agents-md", "code-checkers", "exe-release", "writing-for-agents",
         "teach", "handoff", "wait-what", "wizard", "diagram-design"]
    x, y = 16, cy + 30
    for name in D:
        w = tw(name, 11.5, True) * 1.1 + 18
        if x + w > 988:
            x, y = 16, y + 28
        x = _chip(f, "skill", x, y, name) + 6
    dy = cy + hc + 12
    E = [
        ([("reference", "dispatch/references/inside-a-ticket.md")], "自己捡起一张票的会话；第 5 课定了 worker 只由派发开"),
        ([("script", "dispatch.sh adopt")], "v3 里还在，没有任何技能文字用它"),
        ([("skill", "verify-ticket 的 ## Find your moment、## Reached from here", False)], "路由；票的格式搬进来以后它只讲票"),
        ([("skill", "grill-me")], "只有一句「去读 grilling 照做」；你定了删掉"),
    ]
    hd = 36 + len(E) * 34 + 6
    f.zone(4, dy, 992, hd, "D　删掉的")
    for i, (src, why) in enumerate(E):
        y = dy + 32 + i * 34
        x = _chips(f, 16, y, src)
        _t(f, max(x + 8, 420), y + 16.5, why)
    return f.svg(dy + hd + 8, "v2 每个技能的文字去哪。A 一种任务的做法搬进 playbook，技能只留下它管的那件东西的格式、规则和脚本：night.md 成为 Run a night，one-ticket.md 成为 Run one ticket，dispatch 留下脚本、换模型和 On waking；implement 成为 Work a ticket，技能删掉，writing-interface-code.md 进 ui-acceptance；code-review 的 session.md 成为 Review a ticket，code-review 留下几条轴；to-tickets 成为 Cut tickets，票的格式进 verify-ticket；to-spec 成为 Write a spec 和 Revise a spec，spec 模板在 Write a spec 里；wayfinder 成为 Chart a map 和 Resolve a map ticket，留下地图格式和票的种类；design-pages 成为 Design pages、Pull a design、Build a design system，留下页的约定和 pull 的脚本；write-screen-contract 成为 Write the screen contract，留下格式和脚本；setup-matt-pocock-skills 的种子文件搬进新的 setup-mmw 技能，由它配齐整个仓库。B 一个动词，由 playbook 的步骤点名：grilling、domain-modeling、research、prototype、tdd、diagnosing-bugs、resolving-merge-conflicts、code-review、ui-acceptance、advisor、retro、triage。C 其余技能路由很少，写到用它的 playbook 时逐条判。D 删掉的：v2 的 inside-a-ticket.md，v3 dispatch.sh 里没人用的 adopt，verify-ticket 的两节路由，只有一句去读 grilling 照做的 grill-me。")


# ---- figure 4: ui-acceptance's table, row by row ----

UI_ROWS = [
    ("Writing a page ticket's code, before the first line", "②", [("playbook", "Work a ticket 第 2 步", False), ("reference", "writing-interface-code.md")]),
    ("Building the product's story service and its story adapter", "②", [("playbook", "Work a ticket 第 2 步", False), ("reference", "story-parity.md")]),
    ("Writing a story, boundary, journey or harness guard criterion", "②", [("playbook", "Cut tickets", False), ("reference", "cutting-interface-tickets.md")]),
    ("Reading the DIFF line the story oracle printed", "③", [("script", "story-parity.py"), ("other", "那一行写明去读哪一节", False)]),
    ("Writing the boundary test; reading MISS", "②③", [("playbook", "Work a ticket 第 2 步", False), ("script", "boundary-check.py")]),
    ("Writing a journey script; reading JOURNEY FAILED", "②③", [("playbook", "Work a ticket 第 2 步", False), ("script", "journey.py")]),
    ("Writing a repository's product answers", "③", [("script", "journey.py"), ("script", "harness-guard.py"), ("other", "缺配置时已经指到", False)]),
    ("Reading HARNESS LEAK / HARNESS DESIGN PAGE", "③", [("script", "harness-guard.py"), ("other", "那一行写明去读哪一节", False)]),
    ("Giving a run its own ports, or reading a refusal", "③", [("script", "lease.py"), ("other", "已经这样做", False)]),
]


def _box_lines(f, kind, x, y, w, title, lines):
    h = 30 + len(lines) * 17
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>')
    _t(f, x + 12, y + 20, title, "h")
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 39 + i * 17, line)
    return h


def ui_rows():
    f = Fig("m64", 1000)
    _t(f, 10, 20, "v2 ui-acceptance/SKILL.md 的 ## Find your moment，九行", "h")
    _t(f, 604, 20, "v3 里由谁点名", "h")
    for i, (row, kind, dest) in enumerate(UI_ROWS):
        y = 34 + i * 40
        f.e(f'<g class="k-skill"><rect class="box soft" x="10" y="{y}" width="500" height="30" rx="4"/></g>')
        _t(f, 22, y + 19.5, row, "m")
        _t(f, 548, y + 19.5, kind, "lbl", "middle")
        f.ar([(512, y + 15), (600, y + 15)])
        _chips(f, 604, y + 3, dest)
    y = 34 + 9 * 40 + 10
    h = _box_lines(f, "skill", 10, y, 980, "ui-acceptance/SKILL.md 剩下的：一件事，判定一个界面和它的设计、screen contract 是否一致",
                   ["product under test 是什么；四个判官各证明什么；绿只能说明产品对，红了改产品，设计或 screen contract 错了开子票，从不改检查",
                    "## Five rules while the product is running（第 5 课已搬）"])
    return f.svg(y + h + 8, "ui-acceptance 的 Find your moment 九行在 v3 里由谁点名。写页面票代码、搭 story 服务、写边界测试和 journey 脚本，由 Work a ticket 第 2 步点名对应的 reference；写判据由 Cut tickets 点名 cutting-interface-tickets.md；读 DIFF、MISS、JOURNEY、HARNESS 各行，由打印它的脚本写明去读哪一节；缺 .mmw/target.json 时 journey.py 和 harness-guard.py 的报错已经指到 target_config.py --check；端口和目录由 lease.py 的拒绝指到。技能剩下的是一件事：判定界面和设计、screen contract 是否一致，以及五条规则。")


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
         "Review a ticket：Run the axes",
         [("skill", "code-review"), ("reference", "references/standards-reviewer.md")],
         ["code-review 一件事：沿几个轴审一段 diff。它给每个轴", "开一个通用子代理，提示词就是那个轴的 reference，", "填上票号和 base commit"]),
        ("advisor（v2）",
         ["Use the advisor skill.", "+ brief"],
         [("skill", "advisor"), ("other", "Two moments", True), ("reference", "advising.md")],
         "任何 agent：dispatch.sh advise <brief>",
         [("script", "dispatch.sh advise"), ("reference", "references/advising.md")],
         ["dispatch.sh 把 advising.md 放在 brief 前面作为开工的", "那段话，缺了就拒绝开；advisor/SKILL.md 只写请教的", "那一边"]),
        ("researcher（第 5 课搬进 v3 时加的）",
         ["Use the research skill.", "+ brief"],
         [("skill", "research"), ("other", "If … started", True), ("reference", "researching.md")],
         "Chart a map：派 researcher 那一步",
         [("skill", "research")],
         ["research/SKILL.md 本身就是怎么查；何时派、brief 写", "什么，写在派它的那一步。v2 的 research 没有这张表"]),
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
    return f.svg(432, "派出的 agent 怎样拿到自己那一份。左边：code-review 的轴拿到一句 Use the code-review skill … axis Standards，读 code-review/SKILL.md，在表里按轴名找到 standards-reviewer.md；advisor 拿到 Use the advisor skill 加 brief，在 Two moments 表里找到 advising.md；researcher 拿到 Use the research skill 加 brief，按 If that is how you were started 找到 researching.md，这一条是第 5 课搬进 v3 时加的，v2 的 research 没有。右边：Review a ticket 的 Run the axes 用 code-review，code-review 给每个轴开一个通用子代理，提示词就是那个轴的 reference；dispatch.sh advise 把 advising.md 放在 brief 前面作为开工的那段话；research/SKILL.md 本身就是怎么查，何时派写在 Chart a map 派 researcher 那一步。")


FIGS = {"l6-routes": routes, "l6-net": net, "l6-fates": fates, "l6-ui-rows": ui_rows, "l6-sent": sent}

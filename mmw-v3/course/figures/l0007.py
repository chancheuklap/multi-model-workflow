"""Figure of lesson 0007: how the Investigation playbook, the how and why skills and the other playbooks are wired."""
import html
from kit import Fig, tw


def _t(f, x, y, t, cls="s", anchor="start"):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f.e(f'<text x="{x}" y="{y:.1f}" class="{cls}"{a}>{html.escape(t)}</text>')


def _chip(f, kind, x, y, label, mono=True, dashed=False):
    """A chip with room for a monospace font wider than JetBrains Mono; returns its right edge."""
    w = tw(label, 11.5, mono) * (1.1 if mono else 1.0) + (18 if mono else 24)
    tc = "m" if mono else "s"
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w:.1f}" height="24" rx="4"{dash}/>'
        f'<text x="{x+9}" y="{y+16.5}" class="{tc}">{html.escape(label)}</text></g>')
    return x + w


def _box_lines(f, kind, x, y, w, title, lines, mono_title=True):
    h = 30 + len(lines) * 17
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>', False)
    _t(f, x + 12, y + 20, title, "m" if mono_title else "h")
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 39 + i * 17, line)
    return h


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
    h1 = _box_lines(f, "skill", 680, 40, 310, "how", ["简单的问题：1 个 explainer 边查边讲", "复杂的问题：2 到 4 个 explorer 分头查，", "再 1 个 explainer 汇总"])
    h2 = _box_lines(f, "skill", 680, 40 + h1 + 12, 310, "why", ["先钉住代码、提交和 PR", "每类证据来源 1 个 investigator，", "再 1 个 synthesizer 分清查到和推断"])
    uy = 40 + h1 + 12 + h2 + 12
    _chip(f, "skill", 680, uy, "unslop")
    f.ar([(630, 92), (676, 70)])
    f.ar([(630, 112), (676, 40 + h1 + 12 + 40)])
    f.ar([(630, 132), (676, uy + 12)])
    f.ar([(282, 96), (306, 96), (306, 28), (835, 28), (835, 37)])
    _t(f, 560, uy + 46, "每个子代理都是宿主的通用子代理，不点模型（mode 的 ## Subagents）")
    _t(f, 560, uy + 63, "how 的子代理在提示词结尾写明只读；why 的不进只读模式，以免没有 MCP")

    # hand back
    by = uy + 80
    f.zone(4, by, 992, 72, "要改代码时：不改，交回你，再转一份 playbook（虚线的三份还没写，第 8、9、11 课写）")
    x = 16
    for name in ("Bug fix", "Make a small change", "Write a spec"):
        x = _chip(f, "playbook", x, by + 34, name, mono=False, dashed=True) + 10
    f.ar([(480, 64 + hp), (480, by)])

    # other users
    cy = by + 72 + 12
    rows = [
        ("Bug fix 诊断那一步", "how 看出问题的那一块，why 查是哪次改动引入的"),
        ("Make a small change 第 1 步", "how 看要改的那一块"),
        ("Write a spec、Chart a map", "决定碰到现有代码时 how，要知道当初为什么时 why"),
        ("Work a ticket（夜里的 worker）", "不接：票的 ## Read first 已经列好要读的"),
    ]
    f.zone(4, cy, 992, 36 + len(rows) * 30 + 4, "其他用 how 和 why 的步骤：写到那一份时照第 6 课第 5 节的接线表加")
    for i, (who, what) in enumerate(rows):
        y = cy + 32 + i * 30
        _chip(f, "playbook", 16, y, who, mono=False, dashed=i < 3)
        _t(f, 300, y + 16.5, what)
    H = cy + 36 + len(rows) * 30 + 12
    return f.svg(H, "从你的一个问题到交回的答案。mmw-mode 的 ## Playbooks 有一行路由，把只读的问题（怎么工作、为什么这样、确定吗、选哪个）送进 playbooks/investigation.md；## Non-negotiables 有一行触发，不小的改动、架构决定和「我们确定吗」在任何 playbook 里都用 how。Investigation 三步：走 how，问动机时也走 why；写成 how 的五节或带取舍表的建议；回复过 unslop。不提交、不开票，回复照 Writing the reply 写给你。how 简单问题开 1 个 explainer，复杂问题开 2 到 4 个 explorer 再开 1 个 explainer 汇总；why 先钉住代码、提交和 PR，每类证据来源开 1 个 investigator，再开 1 个 synthesizer。每个子代理都是宿主的通用子代理，不点模型。要改代码时交回你，转 Bug fix、Make a small change 或 Write a spec，这三份还没写。其他用 how 和 why 的步骤：Bug fix 诊断、Make a small change 第 1 步、Write a spec 和 Chart a map；夜里的 worker 不接。")


def roles():
    f = Fig("m72", 1000)
    _t(f, 10, 20, "要开一个 agent 干活之前，依次问三个问题", "h")
    qs = [
        ("1", "会话自己在这个回合里能不能做？", "能：不开 agent，会话自己做"),
        ("2", "要不要自己的模型，或者在这个回合之外独立跑？", "要：独立会话（session），dispatch.sh 开，models.json 有它一行"),
        ("3", "其余：要几份同时做，或要一个没被会话思路影响过的上下文", "子代理（subagent），宿主的通用子代理，跟会话同一个模型"),
    ]
    for i, (n, q, a) in enumerate(qs):
        y = 38 + i * 50
        f.e(f'<circle cx="22" cy="{y + 15}" r="11" fill="var(--ink2)"/>'
            f'<text x="22" y="{y + 19.5}" text-anchor="middle" style="fill:var(--surface);font-size:12px;font-weight:700">{n}</text>')
        _t(f, 42, y + 20, q, "h")
        _t(f, 470, y + 20, a)
    y0 = 200
    f.zone(4, y0, 492, 214, "独立会话：dispatch.sh 开，交回走中继")
    rows = [("worker", "写代码，关票"), ("reviewer", "审一张票"), ("advisor", "对一个决定给第二意见"),
            ("researcher", "读来源，交回带出处的发现"), ("explainer", "把发现写成「怎么工作」的说明"),
            ("synthesizer", "把发现分成查到、推断、不知道")]
    for i, (name, what) in enumerate(rows):
        y = y0 + 32 + i * 29
        _chip(f, "agent", 16, y, name, dashed=name in ("explainer", "synthesizer"))
        _t(f, 150, y + 16.5, what)
    f.zone(504, y0, 492, 214, "子代理：技能在会话里派，当场交回")
    _chip(f, "agent", 516, y0 + 32, "code-review 的轴")
    _t(f, 690, y0 + 48.5, "四条轴同时审一段 diff")
    _t(f, 516, y0 + 92, "要换模型的角色都不在这一边：Codex 默认把子代理的")
    _t(f, 516, y0 + 109, "模型参数藏起来，Claude Code 只能选系列；独立会话")
    _t(f, 516, y0 + 126, "用命令行参数指定模型，五个宿主都管用。")
    _t(f, 516, y0 + 160, "虚线的两个是第 8 课新加的，researcher 改成也替")
    _t(f, 516, y0 + 177, "how、why 去查。每个角色在 dispatch/roles.json 有一行。")
    return f.svg(y0 + 222, "要开一个 agent 干活之前依次问三个问题。一，会话自己在这个回合里能不能做，能就不开。二，要不要自己的模型或在回合之外独立跑，要就做成独立会话，由 dispatch.sh 开，models.json 有它一行。三，其余情况，要几份同时做或要一个干净的上下文，做成子代理，跟会话同一个模型。独立会话有 worker、reviewer、advisor、researcher，以及第 8 课新加的 explainer 和 synthesizer。子代理有 code-review 的轴。要换模型的角色都不做成子代理，因为 Codex 默认藏起子代理的模型参数，Claude Code 只能选系列，独立会话用命令行参数指定模型，五个宿主都管用。")


def brief():
    f = Fig("m73", 1000)
    _t(f, 10, 20, "一个复杂的 how 问题：会话被叫醒两次，每次一条", "h")
    steps = [
        ("Investigation 会话", ["dispatch.sh brief", "researcher × 3，同一批", "然后结束回合"], "playbook"),
        ("3 个 researcher 会话", ["各用自己的宿主和模型", "读代码的一个侧面", "做完跑 report"], "agent"),
        ("本机状态目录", ["briefs/<批>/<brief>/", "result.md 和 reported", "加锁写"], "config"),
        ("中继，每 30 秒", ["一批全交了或有人 lost", "才排一行唤醒：", "brief <批> done"], "script"),
        ("runner 的 send", ["把这一行送进会话", "Paseo、Orca、Herdr", "都有"], "script"),
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
    return f.svg(358, "一个复杂的 how 问题怎样跑。Investigation 会话用 dispatch.sh brief 开 3 个 researcher，同一批，然后结束回合。每个 researcher 在自己的宿主和模型上读代码的一个侧面，做完跑 dispatch.sh report，结果写进本机状态目录 briefs/批/brief/result.md，加锁写。中继每 30 秒读一次，一批全交了或有人判为 lost，才排一行 brief 批 done，经 runner 的 send 送进会话。会话第一次醒来，读 3 份结果，ack，开 explainer，附上 3 份结果的路径，结束回合。explainer 写成五节的说明并 report，中继再叫醒一次。会话第二次醒来，对照代码核实，照 Writing the reply 写给你，brief close 删掉这一批的目录。子会话死了没交，看门进程记 lost；活着却没交就结束回合，回合守卫拦一次；上级不在 runner 里，dispatch.sh brief 拒绝开。")


FIGS = {"l7-wiring": wiring, "l7-roles": roles, "l7-brief": brief}

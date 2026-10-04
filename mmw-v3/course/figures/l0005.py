"""Figures of lesson 0005: how each role in MMW v2 gets its guidance today, the v3 design for how every session and subagent gets its guidance, and the ticket read as a brief."""
import html
from kit import Fig, tw


def _t(f, x, y, t, cls=""):
    c = f' class="{cls}"' if cls else ""
    f.e(f'<text x="{x}" y="{y:.1f}"{c}>{html.escape(t)}</text>')


def _lines_box(f, kind, x, y, w, title, lines, mono_title=False, mono_lines=False):
    """A box with a title line and body lines; returns its height."""
    h = 30 + len(lines) * 16
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>')
    _t(f, x + 10, y + 20, title, "m" if mono_title else "h")
    for i, line in enumerate(lines):
        _t(f, x + 10, y + 38 + i * 16, line, "m" if mono_lines else "s")
    return h


# ---- figure 1: MMW v2 today ----

COLS = {"orch": 116, "worker": 336, "reviewer": 556, "axis": 776}
CW = 200


def v2_roles():
    f = Fig("m13", 1000)
    # row 1: the roles and who starts whom
    f.box("other", 10, 40, 86, 44, "你", [], head=True)
    for key, name in [("orch", "orchestrator"), ("worker", "worker"), ("reviewer", "reviewer"), ("axis", "code-review 的轴")]:
        f.box("other", COLS[key], 40, CW if key != "axis" else 214, 44, name, [], head=True)
    f.ar([(96, 62), (114, 62)], cls="human")
    f.lbl(14, 30, "开会话，说开始")
    f.ar([(316, 62), (334, 62)])
    f.lbl(326, 30, "advance 里的 dispatch.sh start", "middle")
    f.ar([(536, 62), (554, 62)])
    f.lbl(546, 30, "dispatch.sh start <n> reviewer", "middle")
    f.ar([(756, 62), (774, 62)])
    f.lbl(766, 16, "宿主自带的通用子代理，", "middle")
    f.lbl(766, 30, "一次开三或四个", "middle")

    # row 2: what it reads when it starts
    y = 104
    _t(f, 10, y + 20, "开工时", "s")
    _t(f, 10, y + 36, "读到的", "s")
    _lines_box(f, "other", COLS["orch"], y, CW, "你的消息", ["例：开始今晚，spec #120"])
    _lines_box(f, "script", COLS["worker"], y, CW, "start prompt", [
        "Use the implement skill", "to work ticket #n.",
        "+ AUTONOMOUS 一句", "+ PRODUCT_RULES 一句", "+ Memory 索引"], mono_title=True)
    _lines_box(f, "script", COLS["reviewer"], y, CW, "start prompt", [
        "Use the code-review skill", "to review ticket #n from", "base commit <base>.",
        "+ AUTONOMOUS 一句", "+ reviewer Rules"], mono_title=True)
    _lines_box(f, "skill", COLS["axis"], y, 214, "一句话，别的都没有", [
        "Use the code-review skill", "to review ticket #n from", "base commit <base>,", "axis Standards."])

    # row 3: where its guidance comes from
    y = 244
    _t(f, 10, y + 16, "指引从", "s")
    _t(f, 10, y + 32, "哪里来", "s")
    chips = {
        "orch": [("config", "shared.md"), ("skill", "dispatch 技能"), ("reference", "references/night.md")],
        "worker": [("config", "shared.md"), ("skill", "implement"), ("skill", "verify-ticket"), ("script", "AUTONOMOUS")],
        "reviewer": [("config", "shared.md"), ("skill", "code-review"), ("reference", "references/session.md"), ("script", "AUTONOMOUS")],
        "axis": [("skill", "code-review"), ("reference", "references/<轴>-reviewer.md")],
    }
    for key, items in chips.items():
        for i, (k, label) in enumerate(items):
            f.chip(k, COLS[key], y + i * 30, label, mono=label.isascii() and label.isupper())
    for key, note in [("orch", "经 dispatch 的 Find your moment 第 3 行"), ("worker", "经 dispatch 的 Find your moment 第 1 行"),
                      ("reviewer", "经 code-review 的 Find your moment"), ("axis", "经同一张表，轴名选文件")]:
        _t(f, COLS[key], y + 132, note, "s")

    # row 4: what it hands back
    y = 396
    _t(f, 10, y + 16, "交回", "s")
    for key, text in [("orch", "NIGHT SUMMARY、NIGHT RETRO"), ("worker", "收尾评论 → ticket.passed"),
                      ("reviewer", "审查报告 → reviewer.reported"), ("axis", "轴报告，交给 reviewer")]:
        f.chip("other", COLS[key], y, text, mono=False)

    # row 5: the relay and the wakes
    y = 470
    _t(f, 10, y + 16, "什么", "s")
    _t(f, 10, y + 32, "叫醒它", "s")
    f.box("script", COLS["orch"], y + 70, 640, 48, "relay.py：读票上的事件，按 WAKES 叫醒等它的会话，叫醒行是「#n 事件」",
          ["watchdog.py 问 runner 会话还在不在，不在就写 worker.lost；turn-guard.py 看着 watchdog"], mono=False)
    f.ar([(COLS["orch"] + 100, y + 68), (COLS["orch"] + 100, y)])
    _t(f, COLS["orch"] + 108, y + 18, "ticket.passed / returned / refused、", "s")
    _t(f, COLS["orch"] + 108, y + 34, "child.opened、worker.lost", "s")
    f.ar([(COLS["worker"] + 150, y + 68), (COLS["worker"] + 150, y)])
    _t(f, COLS["worker"] + 158, y + 18, "reviewer.reported、", "s")
    _t(f, COLS["worker"] + 158, y + 34, "worker.queued", "s")
    _t(f, COLS["reviewer"] + 50, y + 18, "不被叫醒：等轴报告时", "s")
    _t(f, COLS["reviewer"] + 50, y + 34, "不结束回合", "s")
    f.ar([(COLS["worker"] + 40, y - 50), (COLS["worker"] + 40, y + 68)])
    f.ar([(COLS["reviewer"] + 20, y - 50), (COLS["reviewer"] + 20, y + 68)])

    # the advisor, beside the relay
    ay = 470
    h = _lines_box(f, "skill", COLS["axis"], ay, 214, "advisor", [
        "谁开：任何会话，在难撤回的决定前，", "dispatch.sh advise <brief>",
        "读到：Use the advisor skill. + brief", "指引：references/advising.md",
        "交回：它会话里的答案"])
    f.note(10, 620, "models.json 有行的角色：junior-worker 和 senior-worker（按票上的标签选一个）、reviewer、advisor。orchestrator 跑在你开的会话上，轴跑在 reviewer 的模型上，都没有行。")
    return f.svg(632, "MMW v2 现在的角色系统：你开的会话做 orchestrator，读你的消息，指引来自 dispatch 技能的 references/night.md；它用 dispatch.sh start 开 worker，start prompt 是 Use the implement skill to work ticket #n 加 AUTONOMOUS、PRODUCT_RULES 两句规则和 Memory 索引；worker 用 dispatch.sh start 开 reviewer，start prompt 是 Use the code-review skill 加 base commit、AUTONOMOUS 和 reviewer Rules；reviewer 用宿主的通用子代理开三或四个轴，每个只拿一句话，读 code-review 里自己那份 reference。worker 交回收尾评论和 ticket.passed，reviewer 交回 reviewer.reported；relay.py 读票上的事件，叫醒 orchestrator 或 worker，叫醒行是 #n 事件。advisor 由任何会话用 dispatch.sh advise 开，只拿 brief。")


# ---- figure 2: the v3 design ----

def guidance():
    f = Fig("m14", 1000)
    SX = 370   # the spine of the left part

    f.pill(SX, 10, "一个会话或子代理开始")
    f.ar([(SX, 44), (SX, 60)])
    f.box("config", SX - 190, 62, 380, 46, "宿主载入用户级提示词 shared.md", ["读者是谁；哪些决定只归你"], mono=False)
    f.ar([(SX, 108), (SX, 123)])
    f.dia(SX, 165, 150, 40, ["它跑一份角色 playbook，", "还是由某个技能派出？"])

    # right column, top: an agent a skill sends out, which reads what that skill gives it
    RX, RW = 760, 230
    f.ar([(SX + 150, 165), (RX - 2, 165)], "由某个技能派出", SX + 162, 157)
    _lines_box(f, "agent", RX, 128, RW, "开它的那段话由技能定", [
        "advisor：Use the advisor skill.", "　＋ brief", "researcher：Use the research skill.", "　＋ brief",
        "轴：Use the code-review skill … axis", "其他：技能写好的提示词"])
    f.ar([(RX + RW / 2, 254), (RX + RW / 2, 272)])
    _lines_box(f, "reference", RX, 274, RW, "技能里给它的那一份", [
        "advisor → 回答的那部分", "researcher → 调查的那部分", "轴 → references/<轴>-reviewer.md",
        "其他 → 技能 references/ 里的提示词"])
    f.ar([(RX + RW / 2, 368), (RX + RW / 2, 384)], head=False)
    _t(f, RX, 400, "不载入 mode：它只做技能交给的这一件", "s")
    _t(f, RX, 416, "事。advisor、researcher 还因此看不到", "s")
    _t(f, RX, 432, "派发方想过什么，意见和调查才独立", "s")
    f.ar([(RX + RW / 2, 440), (RX + RW / 2, 456)])
    f.pill(RX + RW / 2, 458, "交回派发方，派发方负责")

    # who started a session that runs a role playbook
    f.ar([(SX, 205), (SX, 230)], "跑角色 playbook", SX + 8, 222)
    f.dia(SX, 262, 76, 30, ["谁开的它？"])
    f.ar([(SX, 292), (SX, 310)], head=False)
    A, B, C = 10, 255, 500
    f.ar([(A + 115, 310), (B + 115, 310)], head=False)
    for x, label in [(A, "你"), (B, "派发方用 dispatch.sh start")]:
        f.ar([(x + 115, 310), (x + 115, 340)])
        f.lbl(x + 123, 330, label)
    _lines_box(f, "script", A, 342, 230, "SessionStart 钩子", [
        "仓库有 .mmw/：载入 mmw-mode", "没有钩子的宿主：", "你输入 /mmw-mode"])
    _lines_box(f, "agent", B, 342, 230, "start prompt", [
        "第 1 句：Use the mmw-mode skill.", "第 2 句：点名 playbook 和票号", "其余是数据：Memory 索引、Rules"])
    for x in (A, B):
        f.ar([(x + 115, 420), (x + 115, 454)])

    # the mode, in context from here on
    f.frame("mode", 10, 456, 720, 96, "mmw-mode 载入，之后一直在上下文", [], mono=False)
    cx = 22
    for label in ["## Principles 索引", "## Non-negotiables 触发行", "## Autonomy，含 Unattended 一段"]:
        cx = f.chip("mode", cx, 484, label, mono=False) + 8
    cx = 22
    for label in ["## Subagents", "## Writing the reply", "## Comments", "## Playbooks"]:
        cx = f.chip("mode", cx, 516, label, mono=False) + 8

    # the route
    f.ar([(SX, 552), (SX, 574)])
    f.dia(SX, 610, 104, 34, ["start prompt", "点名了 playbook？"])
    f.ar([(SX - 104, 610), (125, 610), (125, 648)], "没有：你开的会话", 132, 602)
    f.ar([(SX + 104, 610), (615, 610), (615, 648)], "点名了", 480, 602)
    _lines_box(f, "mode", A, 650, 230, "## Playbooks 按任务选一份", [
        "开始今晚 → Run a night", "修一个 bug → Bug fix", "写技能 → Authoring a skill", "审技能 → Review the skill set",
        "要暂停 → Pause safely"])
    _lines_box(f, "mode", C, 650, 230, "照点名的走，不再选路", [
        "worker → Work a ticket", "reviewer → Review a ticket"])
    f.ar([(125, 760), (125, 790)])
    f.ar([(615, 712), (615, 790)])
    f.box("playbook", 110, 792, 520, 66, "playbook：它的 **You own** 和 **Reply:** 就是这个角色",
          ["Run a night、Bug fix = orchestrator（一夜一批票、单张票）", "Work a ticket = worker · Review a ticket = reviewer"], mono=False)

    # where in the playbook
    f.ar([(SX, 858), (SX, 872)])
    f.dia(SX, 904, 90, 32, ["这件事", "挂在票上吗？"])
    f.ar([(SX - 90, 904), (125, 904), (125, 940)], "挂在票上", 136, 896)
    f.ar([(SX + 90, 904), (615, 904), (615, 940)], "没有", 480, 896)
    _lines_box(f, "script", A, 942, 230, "读票上的事件，定走到哪一步", [
        "worker、reviewer：verify-ticket.py", "　--preflight 认领，给出 RESUME 行", "orchestrator：dispatch.sh status",
        "票正文就是任务说明（图 4）"])
    _lines_box(f, "other", C, 942, 230, "从第 1 步开始", [
        "依据你的消息"])
    f.ar([(125, 1036), (125, 1068)])
    f.ar([(615, 988), (615, 1068)])

    # doing a step
    f.zone(10, 1070, 720, 104, "做这一步时，按需读")
    cx = 24
    for k, label in [("principle", "条件出现 → 读原则全文"), ("skill", "情况出现 → 触发行点名的技能")]:
        cx = f.chip(k, cx, 1102, label, mono=False) + 10
    cx = 24
    for k, label in [("reference", "这一步写明的 reference"), ("script", "越界的动作：钩子拦下，tool-guard.py")]:
        cx = f.chip(k, cx, 1136, label, mono=False) + 10

    # end, or wait to be woken
    f.ar([(SX, 1174), (SX, 1192)])
    f.dia(SX, 1228, 120, 34, ["这一步开了别的 agent，", "或在等一个结果？"])
    f.ar([(SX, 1262), (SX, 1284)], "没有", SX + 8, 1278)
    f.pill(SX, 1286, "按 playbook 的 Reply: 交回")
    for i, t in enumerate(["白天会话：回复你　orchestrator：NIGHT SUMMARY，", "或 Bug fix 的落地结果", "worker：收尾评论，事件 ticket.passed",
                           "reviewer：审查报告，事件 reviewer.reported", "落在票上的事件，relay 据此叫醒等它的会话"]):
        _t(f, SX - 180, 1340 + i * 16, t, "s")

    # right column, bottom: the wake
    pl, _ = f.pill(RX + RW / 2, 1211, "结束回合")
    f.ar([(SX + 120, 1228), (pl - 2, 1228)], "是", SX + 128, 1220)
    _t(f, RX, 1262, "结束回合的那一步写明：等哪个事件，", "s")
    _t(f, RX, 1278, "被叫醒时先做 dispatch 的 ## On waking", "s")
    f.ar([(RX + RW / 2, 1211), (RX + RW / 2, 1172)])
    _lines_box(f, "script", RX, 1092, RW, "relay.py", [
        "票上出现它等的事件", "按 WAKES 找到等它的会话", "watchdog.py：会话没了写 lost"], mono_title=True)
    f.ar([(RX + RW / 2, 1092), (RX + RW / 2, 1072)])
    _lines_box(f, "agent", RX, 1024, RW, "叫醒行", ["#n 事件，别的都没有"])
    f.ar([(RX + RW / 2, 1024), (RX + RW / 2, 1004)])
    _lines_box(f, "skill", RX, 910, RW, "dispatch 技能的 ## On waking", [
        "重跑被打断的命令；到票上读这个事件", "dispatch.sh ack；再照自己的 playbook，", "回到等这个事件的那一步"])
    f.ar([(RX, 952), (745, 952), (745, 1122), (732, 1122)])
    return f.svg(1428, "v3 的设计：每个会话一开，宿主载入 shared.md。第一个判断：它跑一份角色 playbook，还是由某个技能派出。由技能派出的 advisor、researcher、code-review 的轴和其他技能的子代理，开它的那段话由技能定，读技能里给它的那一份，不载入 mode，交回派发方，由派发方负责。跑角色 playbook 的，按谁开的分两路载入 mmw-mode：你开的会话由 SessionStart 钩子载入，没有钩子的宿主由你输入 /mmw-mode；派发方用 dispatch.sh start 开的会话由 start prompt 第一句载入，第二句点名 playbook 和票号，其余是数据。mode 载入后一直在上下文。第二个判断：start prompt 有没有点名 playbook；没有就由 ## Playbooks 按任务选，例如开始今晚选 Run a night、修一个 bug 选 Bug fix，点名了就照走。playbook 的 You own 和 Reply 就是这个角色：Run a night 和 Bug fix 是 orchestrator，一个管一夜一批票，一个管单张票，Work a ticket 是 worker，Review a ticket 是 reviewer。第三个判断：这件事挂在票上吗；挂在票上就读票上的事件定走到哪一步。做一步时按需读原则、技能、reference，越界的动作由钩子拦下。最后一个判断：这一步开了别的 agent 或在等结果吗；没有就按 Reply 交回；是就结束回合，结束回合的那一步写明等哪个事件、被叫醒时先做 dispatch 技能的 ## On waking。relay.py 在票上出现它等的事件时叫醒它，叫醒行只有 #n 事件；On waking 四步做完，回到等这个事件的那一步。")


# ---- figure 3: the two documents every role needs ----

PAIRS = [
    ("固定时机：工作流的某一步派它，派发说明写在那一步", [
        ("orchestrator", "你",
         [("mode", "## Playbooks 的路由行")], [("other", "你开的会话")],
         [("playbook", "Run a night 或 Bug fix"), ("mode", "mmw-mode")], ["一夜：NIGHT SUMMARY", "单张票：落地结果"]),
        ("worker", "orchestrator",
         [("playbook", "Run a night：advance 那一步"), ("playbook", "Bug fix：开 worker 那一步")], [("script", "dispatch.sh start")],
         [("playbook", "Work a ticket"), ("mode", "mmw-mode")], ["ticket.passed / returned", "叫醒 orchestrator"]),
        ("reviewer", "worker",
         [("playbook", "Work a ticket：起 reviewer 那一步")], [("script", "dispatch.sh start")],
         [("playbook", "Review a ticket"), ("mode", "mmw-mode")], ["reviewer.reported", "叫醒 worker"]),
        ("code-review 的轴", "reviewer",
         [("playbook", "Review a ticket：跑轴那一步")], [("other", "宿主的通用子代理")],
         [("skill", "code-review"), ("reference", "references/<轴>-reviewer.md")], ["轴报告，回到", "reviewer 的同一回合"]),
        ("researcher", "wayfinder",
         [("skill", "wayfinder：发起调查那一步")], [("script", "dispatch.sh，独立会话")],
         [("skill", "research：调查的那部分")], ["研究文件；结论贴到", "research 票上并关票"]),
        ("其他技能的子代理", "某个技能",
         [("skill", "派它的那个技能的那一步")], [("other", "宿主的通用子代理")],
         [("reference", "技能 references/ 里的提示词")], ["按技能写明的", "格式交回派发方"]),
    ]),
    ("自由人：任何 agent 遇到情况就派它，何时派写在它自己技能的 description 里", [
        ("advisor", "任何 agent",
         [("skill", "advisor 的 description：何时请教"), ("skill", "advisor：怎么写 brief")], [("script", "dispatch.sh，独立会话")],
         [("skill", "advisor：回答的那部分")], ["答案，决定", "仍归派发方"]),
    ]),
]


def pairs():
    f = Fig("m16", 1000)
    D, O, G, R = 140, 450, 616, 852   # columns: dispatcher's document, how it is started, the agent's document, what comes back
    f.note(10, 16, "角色 · 派发方")
    f.note(D, 16, "派发方那份：何时派、给什么、回来怎么办")
    f.note(O, 16, "怎么开")
    f.note(G, 16, "agent 那份：去哪拿规则")
    f.note(R, 16, "交回什么")
    y = 28
    for group, rows in PAIRS:
        f.zone(10, y + 6, 980, 30 + len(rows) * 68, group)
        y += 34
        for role, by, ddoc, how, gdoc, back in rows:
            h = 68
            mid = y + h / 2
            _t(f, 22, mid - 2, role, "h")
            _t(f, 22, mid + 15, "派发方：" + by, "s")
            for i, (k, label) in enumerate(ddoc):
                f.chip(k, D, mid - 12 + (i - (len(ddoc) - 1) / 2) * 28, label, mono=False)
            f.ar([(O - 26, mid), (O - 6, mid)])
            for k, label in how:
                f.chip(k, O, mid - 12, label, mono=False)
            f.ar([(G - 26, mid), (G - 6, mid)])
            for i, (k, label) in enumerate(gdoc):
                f.chip(k, G, mid - 12 + (i - (len(gdoc) - 1) / 2) * 28, label, mono=False)
            f.ar([(R - 26, mid), (R - 6, mid)])
            for i, t in enumerate(back):
                _t(f, R, mid - 4 + i * 16, t, "s")
            y += h
        y += 14
    y += 18
    hb = _lines_box(f, "script", 10, y, 980, "检查脚本，放在 dispatch/scripts/：两份对不上就报错，指出哪一处", [
        "1　dispatch.sh 拼的 start prompt 里点名的 playbook，mode 的 ## Playbooks 里有它的路由行",
        "2　agent 的 playbook 写明交回时发的事件，relay.py 的 WAKES 会把它送到派发方",
        "3　送到派发方的每个事件，派发方的 playbook 写了收到后怎么做"])
    return f.svg(y + hb + 8, "每个角色的两份东西，分固定时机和自由人两组。orchestrator 由你派，你那份是 mode 的路由行，它读 Run a night（一夜一批票）或 Bug fix（单张票）和 mode。worker 由 orchestrator 派，派发方那份是 Run a night 的 advance 那一步或 Bug fix 开 worker 那一步，经 dispatch.sh start 开，它读 Work a ticket 和 mode，交回 ticket.passed 或 returned 叫醒 orchestrator。reviewer 由 worker 派，派发方那份是 Work a ticket 起 reviewer 那一步，经 dispatch.sh start 开，它读 Review a ticket 和 mode，交回 reviewer.reported 叫醒 worker。code-review 的轴由 reviewer 派，派发方那份是 Review a ticket 跑轴那一步，经宿主的通用子代理开，它读 code-review 里自己那一份。researcher 现在由 wayfinder 派，派发方那份是 wayfinder 发起调查那一步，经 dispatch.sh 开独立会话，它读 research 里调查的那部分，交回研究文件，把结论贴到 research 票上并关票。其他技能派出的子代理，派发方那份是派它的那一步，经宿主的通用子代理开，它读技能 references/ 里的提示词。以上是固定时机：工作流的某一步派它。下面是自由人：任何 agent 遇到情况就派。advisor 的派发方那份是它技能的 description（何时请教）和怎么写 brief 的那部分，经 dispatch.sh 开独立会话，它读回答的那部分，交回答案，决定仍归派发方。底下一个检查脚本核对三处：start prompt 点名的 playbook 有路由行；agent 交回的事件在 relay.py 的 WAKES 里；送到派发方的事件，派发方的 playbook 写了怎么做。")


# ---- figure 4: the ticket, read as pstack's brief ----

BRIEF = [
    ("GOAL", "一句话的结果，陌生人照着能做", [("skill", "## What to build")], "to-tickets 写，白天当面问清"),
    ("SCOPE", "能写哪些路径，独占的工作区", [("skill", "## Owns"), ("script", "工作区 issue-<n>")], "Owns 以外的改动写进 ## Outside Owns，由审查判断"),
    ("CONTEXT", "指向文件；上游的报告全文贴进来", [("skill", "## Read first"), ("skill", "## Parent"), ("agent", "Memory 索引")], "已落地的兄弟票由 dispatch.sh integrated 列出，给 Spec 轴读"),
    ("ACCEPTANCE · VERIFY", "可检查的判据，确切的命令", [("skill", "CHECK: 与 EXPECT:"), ("skill", "verify-ticket.py")], "verify-ticket.py --lint 在第一次 advance 前查整批票"),
    ("TIMEBOX", "跑多久，到时交回部分结果", [("other", "没有对应")], "轮数由 worker 自己判断；watchdog 的 idle 提醒最接近"),
    ("FORBIDDEN", "不准做的事", [("script", "tool-guard.py")], "不写成文字，由钩子拦下：手动关票、弹出提问"),
    ("REPORT", "交回什么，什么格式", [("skill", "收尾评论"), ("skill", "verify-ticket.py --draft")], "模板由脚本生成，--closeout 不合格式就拒绝"),
    ("STANDING", "每次开工、每次续上都原样贴入的常设指令", [("mode", "mmw-mode")], "start prompt 第 1 句载入"),
]


def brief_map():
    f = Fig("m15", 1000)
    f.note(10, 16, "pstack Orchestrate 的 brief 字段")
    f.note(330, 16, "夜里的票里，对应的部分")
    f.note(640, 16, "说明")
    y = 28
    for field, meaning, chips, note in BRIEF:
        h = 46
        f.e(f'<g class="k-playbook"><rect class="box" x="10" y="{y + 4}" width="290" height="{h - 8}" rx="4"/></g>')
        _t(f, 20, y + 21, field, "m")
        _t(f, 20, y + 37, meaning, "s")
        f.ar([(300, y + h / 2), (324, y + h / 2)])
        cx = 330
        for k, label in chips:
            cx = f.chip(k, cx, y + h / 2 - 12, label, mono=False) + 6
        words, line, lines = note, "", []
        for ch in words:
            if tw(line + ch, 11.5) > 340:
                lines.append(line)
                line = ""
            line += ch
        lines.append(line)
        for i, ln in enumerate(lines):
            _t(f, 640, y + h / 2 + 4 - (len(lines) - 1) * 8 + i * 16, ln, "s")
        y += h
        f.e(f'<line x1="10" y1="{y}" x2="990" y2="{y}" class="rule"/>', False)
    return f.svg(y + 6, "pstack Orchestrate 的 brief 字段和夜里的票逐项对应：GOAL 是 ## What to build；SCOPE 是 ## Owns 和工作区 issue-<n>；CONTEXT 是 ## Read first、## Parent 和 start prompt 里的 Memory 索引；ACCEPTANCE 和 VERIFY 是 CHECK: 与 EXPECT:，由 verify-ticket.py 跑；TIMEBOX 没有对应；FORBIDDEN 由 tool-guard.py 拦下；REPORT 是收尾评论，模板由 verify-ticket.py --draft 生成；STANDING 对应 mmw-mode，由 start prompt 第一句载入。")


FIGS = {"l5-v2-roles": v2_roles, "l5-guidance": guidance, "l5-pairs": pairs, "l5-brief": brief_map}

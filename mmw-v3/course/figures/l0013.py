"""Figures of lesson 0013: the four oracles; what a repository answers in .mmw/ and who reads it;
the tickets a screen contract produces; one page ticket through the worker and the review; where
v2's acceptance-side files went."""
from kit import Fig, txt as _t, tbox as _box, tw, flow


def _plain(f, kind, x, y, w, h, lines):
    """A box of plain lines, no title line."""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>', False)
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 20 + i * 17, line, room=w - 20)


def oracles():
    f = Fig("m131", 1000)
    _t(f, 10, 20, "夜里没人看屏幕：四个判官各看一处，每次先证明自己会红", "h")
    cols = [(16, 200, "判官"), (228, 290, "看的是什么，起什么"), (530, 250, "反面对照：必须红的那一遍"), (792, 196, "打印什么")]
    rows = [
        ("script", "story oracle", ["story-parity.py"],
         ["产品的 story 页对设计包的页面，", "按 data-ui 编号逐个元素比；", "起 story 服务，不占 lease"],
         ["先改掉设计侧全部字号、拿掉产品侧", "全部编号，证明看得见；看不见", "就报 NEGATIVE CONTROL FAILED"],
         ["绿：STORY OK 过/总", "红：一行 DIFF 一个编号", "一个属性，两边的值"]),
        ("script", "边界判官", ["boundary-check.py"],
         ["产品自己的四列边界测试：", "点了以后 calls、shows、next、", "on_failure 是否照 screen contract"],
         ["同一条命令再跑一遍，", "MMW_NEGATIVE=1 让点击", "什么都不做，必须变红"],
         ["绿：BOUNDARY OK n/n", "红：MISS；第二遍还绿：", "GREEN WITHOUT INTERACTION"]),
        ("script", "journey", ["journey.py"],
         ["用 start 起整个真产品，不 mock，", "走一条端到端的路，", "最后到另一页读回结果"],
         ["--break 让一个接口故意失败", "再走一遍，必须失败；", "没有 --break 就关掉产品再走"],
         ["绿：JOURNEY OK 名字", "红：JOURNEY FAILED、", "JOURNEY GREEN WITH BREAK 等"]),
        ("script", "harness guard", ["harness-guard.py"],
         ["扫整个仓库：只为自动化开的后门", "（MMW_ 变量、harness_markers）", "只许在 .mmw/、tests/ 等处"],
         ["不跑产品。它防的是：", "后门写进产品代码，", "随发布装到客户的机器上"],
         ["绿：HARNESS OK", "红：HARNESS LEAK 文件:行、", "HARNESS DESIGN PAGE"]),
    ]
    for x, w, head in cols:
        _t(f, x, 52, head, "h")
    y = 64
    for kind, name, sub, what, neg, out in rows:
        h = _box(f, kind, 16, y, 200, name, sub + [""], mono_title=False)
        _plain(f, "other", 228, y, 290, h, what)
        _plain(f, "other", 530, y, 250, h, neg)
        _plain(f, "other", 792, y, 196, h, out)
        f.ar([(216, y + 20), (226, y + 20)])
        y += max(h, 64) + 14
    f.zone(4, y, 992, 74, "四个判官共用的")
    _t(f, 16, y + 42, "lease.py：每个 worktree 一段自己的端口和目录，几个夜里的运行同在一台机器上互不碰。", room=970)
    _t(f, 16, y + 62, "五条规矩：不结束别人的进程；不在 lease 外起产品；不替自动化做人的步骤；够不着产品就报 blocked；流水线自己坏了也报 blocked。", room=970)
    return f.svg(y + 82, ARIA_ORACLES)


ARIA_ORACLES = ("四个判官，夜里没有人看屏幕时，各看界面的一处，每次先证明自己会红。"
                "story oracle（story-parity.py）把产品的 story 页和设计包的页面按 data-ui 编号逐个元素比，起 story 服务，不占 lease；每次先改掉设计侧全部字号、拿掉产品侧全部编号，证明看得见这两种差别，看不见就报 NEGATIVE CONTROL FAILED；绿是 STORY OK 过/总，红是一行 DIFF 一个编号一个属性和两边的值。"
                "边界判官（boundary-check.py）跑产品自己的四列边界测试，看点了以后 calls、shows、next、on_failure 是否照 screen contract；同一条命令再跑一遍，MMW_NEGATIVE=1 让点击什么都不做，必须变红；绿是 BOUNDARY OK n/n，红是 MISS，第二遍还绿是 GREEN WITHOUT INTERACTION。"
                "journey（journey.py）用 start 起整个真产品，不 mock，走一条端到端的路，最后到另一页读回结果；--break 让一个接口故意失败再走一遍，必须失败，没有 --break 就关掉产品再走；绿是 JOURNEY OK，红是 JOURNEY FAILED、JOURNEY GREEN WITH BREAK 或 JOURNEY GREEN WITHOUT PRODUCT。"
                "harness guard（harness-guard.py）扫整个仓库，只为自动化开的后门（MMW_ 变量、harness_markers）只许在 .mmw/、tests/ 等处；它不跑产品，防的是后门写进产品代码、随发布装到客户机器上；绿是 HARNESS OK，红是 HARNESS LEAK 或 HARNESS DESIGN PAGE。"
                "四个判官共用 lease.py：每个 worktree 一段自己的端口和目录。五条规矩：不结束别人的进程；不在 lease 外起产品；不替自动化做人的步骤；够不着产品就报 blocked；流水线自己坏了也报 blocked。")


def answers():
    f = Fig("m132", 1000)
    _t(f, 10, 20, "仓库在 .mmw/ 里回答判官问不出的事：怎样起、怎样停、页面在哪", "h")
    rows = [
        ("start、stop、discover", ["起整个产品（从 lease 取端口和目录）、", "只停自己起的、打印地址"], [("script", "journey.py")]),
        ("stories", ["起 story 服务，打印 origin；", "不占 lease，向机器要一个空端口"], [("script", "story-parity.py")]),
        (".mmw/stories/", ["story 页和 story adapter：", "把产品自己的组件放进一个场景"], [("script", "story-parity.py")]),
        ("journeys，.mmw/journeys/", ["一条路一个目录，", "默认三条：钱、登录、一串提交"], [("script", "journey.py")]),
        (".mmw/harness/", ["起整个栈的代码、故意失败的开关", "（start 读 MMW_BREAK）、假的外部服务"], [("script", "journey.py --break")]),
        ("harness_markers、leaves_machine", ["只为自动化开的后门；", "会离开这台机器的动作，记到哪个文件"], [("script", "harness-guard.py")]),
        ("instance（可选）", ["端口挪不动的产品：", "一台机器同时能跑几次，为什么"], [("script", "lease.py")]),
        ("checks（可选）", ["仓库自己的检查命令，", "关票前、落地前都跑"], [("script", "verify-ticket.py --closeout")]),
    ]
    _t(f, 16, 52, ".mmw/target.json 的字段和 .mmw/ 的目录", "h")
    _t(f, 690, 52, "谁读它", "h")
    y = 64
    for title, lines, readers in rows:
        h = _box(f, "other", 16, y, 600, title, lines, mono_title=True)
        ry = y + (h - 24) / 2
        f.ar([(616, y + h / 2), (688, ry + 12)])
        x = 690
        for kind, label in readers:
            x = f.chip(kind, x, ry, label) + 6
        y += h + 10
    f.zone(4, y + 4, 992, 78, "谁建，谁查")
    _t(f, 16, y + 46, "建：一批票里的 contract 票；产品从零开始就整个建，已有的产品只补 spec 说缺的。", room=970)
    _t(f, 16, y + 66, "查：target_config.py --check 列出每个还没回答的字段。一批票有 screen contract 时，Run a night 第 2 步跑它；setup-mmw 不查。", room=970)
    return f.svg(y + 90, ARIA_ANSWERS)


ARIA_ANSWERS = ("仓库在 .mmw/ 里回答判官问不出的事。.mmw/target.json 的 start、stop、discover 起整个产品（从 lease 取端口和目录）、只停自己起的、打印地址，journey.py 读。"
                "stories 起 story 服务、打印 origin，不占 lease，向机器要一个空端口，story-parity.py 读。.mmw/stories/ 放 story 页和 story adapter，把产品自己的组件放进一个场景，story-parity.py 读。"
                "journeys 和 .mmw/journeys/ 一条路一个目录，默认三条：钱、登录、一串提交，journey.py 读。.mmw/harness/ 放起整个栈的代码、故意失败的开关（start 读 MMW_BREAK）、假的外部服务，journey.py --break 用。"
                "harness_markers 和 leaves_machine 写只为自动化开的后门、会离开这台机器的动作记到哪个文件，harness-guard.py 读。instance 可选，端口挪不动的产品写一台机器同时能跑几次和为什么，lease.py 读。"
                "checks 可选，仓库自己的检查命令，关票前、落地前都跑，verify-ticket.py --closeout 读。"
                "谁建：一批票里的 contract 票，产品从零开始就整个建，已有的产品只补 spec 说缺的。谁查：target_config.py --check 列出每个还没回答的字段；一批票有 screen contract 时 Run a night 第 2 步跑它；setup-mmw 不查。")


def tickets():
    f = Fig("m133", 1000)
    _t(f, 10, 20, "一份 screen contract 切出的票：箭头是「挡住」，起点关了终点才开工", "h")
    W = 300
    nodes = {
        "ds": (16, 60, "design-system 票", ["把设计系统的变量、字体、零件样式", "抄进产品代码；判据一条命令"]),
        "ct": (16, 190, "contract 票", ["建 .mmw/、story 服务、交互 helper、", "故意失败的开关；判据：smoke journey"]),
        "cp": (350, 120, "component page 票（每页一张）", ["一条 story 判据；每个有调用或", "流转的行一条边界判据"]),
        "ap": (350, 270, "app page 票（每个 App 页一张）", ["一条 story 判据；每条跨区域的行", "一条边界判据"]),
        "cf": (684, 120, "critical-flow 票（每条关键流程一张）", ["journey 判据带 --break；最后一张", "还带静态检查和 harness guard"]),
        "re": (684, 290, "reaction 票（你来做）", ["在跑起来的产品上用一遍，", "判 story 截图看不到的手感"]),
    }
    hs = {}
    for k, (x, y, title, lines) in nodes.items():
        kind = "other"
        hs[k] = _box(f, kind, x, y, W, title, lines, mono_title=False)
    def mid_r(k):
        x, y, *_ = nodes[k]
        return (x + W, y + hs[k] / 2)
    def mid_l(k):
        x, y, *_ = nodes[k]
        return (x, y + hs[k] / 2)
    def bot(k):
        x, y, *_ = nodes[k]
        return (x + 60, y + hs[k])
    f.ar([bot("ds"), (76, 188)])
    f.ar([mid_r("ct"), (330, mid_r("ct")[1]), (330, mid_l("cp")[1]), (348, mid_l("cp")[1])])
    f.ar([(330, mid_r("ct")[1]), (330, mid_l("ap")[1]), (348, mid_l("ap")[1])])
    cpx, cpy = 500, 120 + hs["cp"]
    f.ar([(cpx, cpy), (cpx, 268)])
    f.ar([(650, 140), (682, 140)])
    f.ar([(650, mid_r("ap")[1] - 10), (668, mid_r("ap")[1] - 10), (668, 172), (682, 172)])
    f.ar([(650, mid_r("ap")[1] + 10), (682, mid_l("re")[1])])
    _t(f, 16, 380, "没有 contract 票的一批，design-system 票直接挡每张 page 票。", room=970)
    _t(f, 16, 400, "critical-flow 票还被造它要调用的那些接口的票挡住：journey 什么都不 mock，接口不在，第一次写入就失败。", room=970)
    return f.svg(412, ARIA_TICKETS)


ARIA_TICKETS = ("一份 screen contract 切出的票，箭头是挡住，起点关了终点才开工。design-system 票把设计系统的变量、字体、零件样式抄进产品代码，判据一条命令；它挡 contract 票。"
                "contract 票建 .mmw/、story 服务、交互 helper、故意失败的开关，判据是 smoke journey；它挡这批里除 design-system 票外的每一张，图里只画到 page 票。"
                "component page 票每页一张，一条 story 判据，每个有调用或流转的行一条边界判据；它挡 app page 票。app page 票每个 App 页一张，一条 story 判据，每条跨区域的行一条边界判据。"
                "critical-flow 票每条关键流程一张，journey 判据带 --break，最后一张还带静态检查和 harness guard；它被 page 票挡住。reaction 票由你来做，在跑起来的产品上用一遍，判 story 截图看不到的手感；它被每张 page 票挡住。"
                "没有 contract 票的一批，design-system 票直接挡每张 page 票。critical-flow 票还被造它要调用的接口的票挡住，因为 journey 什么都不 mock。")


def page():
    steps = [
        ("Work a ticket 第 2 步：读进来", ["Read first 列着 screen contract，", "就读 writing-interface-code.md"],
         [("reference", "ui-acceptance 的 writing-interface-code.md")], None, 0),
        ("先取设计那一侧的值", ["story-parity.py --render-only，", "不用产品：截图和每个编号的值"],
         [("script", "story-parity.py --render-only")], None, 0),
        ("照这些值写组件", ["组件、story adapter；每个自己的行", "一个四列边界测试，先红后绿"],
         [("reference", "story-parity.md"), ("reference", "boundary-check.md")], None, 0),
        ("跑 story 判据，按 DIFF 改", ["一行 DIFF 就是要改的一个编号一个属性；", "改产品组件，不改 story 页"],
         [("script", "story-parity.py")], ("设计那一侧错了", ["开 contract 子票；这条判据", "记 ABANDON stuck"]), 0),
        ("Review a ticket 第 2 步：四条轴", ["有 story 判据就加 UI 轴：", "Standards、Spec、Tests、UI"],
         [("reference", "spec-reviewer.md"), ("reference", "tests-reviewer.md"), ("reference", "ui-reviewer.md")],
         ("UI 轴报的", ["没编号的装饰、整体观感、", "设计页本身画错"]), 18),
    ]
    f, rows, bottom = flow("m134", "一张页面票：worker 照设计的值写，判官判，审查看判官看不到的", steps,
                           "worker 和 reviewer 的会话", "交出去的")
    return f.svg(bottom + 8, ARIA_PAGE)


ARIA_PAGE = ("一张页面票走过的路。Work a ticket 第 2 步读进来：Read first 列着 screen contract，就读 ui-acceptance 的 writing-interface-code.md。"
             "先取设计那一侧的值：story-parity.py --render-only 不用产品，写出截图和每个编号的值。照这些值写组件：组件、story adapter，每个自己的行一个四列边界测试，先红后绿，读 story-parity.md 和 boundary-check.md。"
             "跑 story 判据，按 DIFF 改：一行 DIFF 就是要改的一个编号一个属性，改产品组件，不改 story 页；设计那一侧错了就开 contract 子票，这条判据记 ABANDON stuck。"
             "Review a ticket 第 2 步：有 story 判据就加 UI 轴，四条轴 Standards、Spec、Tests、UI，各读 spec-reviewer.md、tests-reviewer.md、ui-reviewer.md；UI 轴报没编号的装饰、整体观感、设计页本身画错。")


def moves():
    f = Fig("m135", 1000)
    _t(f, 16, 22, "v2 的文件", "h")
    _t(f, 420, 22, "在 v3 里", "h")
    _t(f, 760, 22, "为什么在那里", "h")
    rows = [
        ([("skill", "ui-acceptance 的 SKILL.md（796）")], [("skill", "ui-acceptance 的 SKILL.md")], ["## Find your moment 换成", "## What each file covers"]),
        ([("skill", "它的 description 的四种时机")], [("mode", "mmw-mode 的一条触发")], ["除 mmw-mode 外，技能只在", "被点名时运行"]),
        ([("skill", "verify-ticket 的 ## Reached from here")], [("mode", "同一条触发")], ["同上；三处说的是同一件事"]),
        ([("reference", "五份 reference、九个脚本")], [("reference", "ui-acceptance/ 原处")], ["原样；journey.md 一处", "user 改 owner"]),
        ([("reference", "implement 的 writing-interface-code.md（880）")], [("reference", "ui-acceptance/references/")], ["implement 已拆成 Work a ticket；", "它讲的是判官的规矩"]),
        ([("reference", "code-review 的 ui-reviewer.md（476）")], [("reference", "code-review/references/ 原处")], ["加上另三条轴都有的", "开头一句"]),
        ([("reference", "to-tickets 的 cutting-interface-tickets.md")], [("reference", "mmw-mode/references/")], ["Cut tickets 第 3 步读；", "to-tickets 已拆成 playbook"]),
        ([("other", "tests/ui-acceptance/（55 个文件）")], [("other", "mmw-v3/tests/ui-acceptance/")], ["只改路径；run.sh 去掉", "两项 v3 没有的预检"]),
    ]
    y = 44
    for src, dst, note in rows:
        x = 16
        for kind, label in src:
            x = f.chip(kind, x, y, label, mono=False) + 6
        f.ar([(x, y + 12), (416, y + 12)])
        x = 420
        for kind, label in dst:
            x = f.chip(kind, x, y, label, mono=False) + 6
        for i, line in enumerate(note):
            _t(f, 760, y + 16.5 + i * 15, line, room=230)
        y += 30 + 15 * (len(note) - 1) + 8
    return f.svg(y + 4, ARIA_MOVES)


ARIA_MOVES = ("v2 验收这一侧的文件在 v3 里去了哪。ui-acceptance 的 SKILL.md（796 词）留在 ui-acceptance，## Find your moment 换成 ## What each file covers。"
              "它的 description 里的四种时机成为 mmw-mode 的一条触发，因为除 mmw-mode 外技能只在被点名时运行；verify-ticket 的 ## Reached from here 并进同一条触发。"
              "五份 reference 和九个脚本原样留在 ui-acceptance，journey.md 一处 user 改 owner。implement 的 writing-interface-code.md（880 词）进 ui-acceptance/references/，因为 implement 已拆成 Work a ticket，它讲的是判官的规矩。"
              "code-review 的 ui-reviewer.md（476 词）留在原处，加上另三条轴都有的开头一句。to-tickets 的 cutting-interface-tickets.md 进 mmw-mode/references/，Cut tickets 第 3 步读它。"
              "tests/ui-acceptance/ 的 55 个文件进 mmw-v3/tests/ui-acceptance/，只改路径，run.sh 去掉两项 v3 没有的预检。")


FIGS = {"l13-oracles": oracles, "l13-answers": answers, "l13-tickets": tickets, "l13-page": page, "l13-moves": moves}

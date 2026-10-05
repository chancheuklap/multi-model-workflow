"""Figures of lesson 0009: from an issue to a night's batch; Write a spec; Cut tickets; Triage; the five
questions; where v2's to-spec, to-tickets and triage went."""
import html

from kit import Fig, flow, tw, txt as _t, tbox as _box


def _chip(f, kind, x, y, label, mono=False, dashed=False):
    w = tw(label, 11.5, mono) * (1.1 if mono else 1.0) + (18 if mono else 24)
    tc = "m" if mono else "s"
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w:.1f}" height="24" rx="4"{dash}/>'
        f'<text x="{x+9}" y="{y+16.5}" class="{tc}">{html.escape(label)}</text></g>')
    return x + w


def chain():
    f = Fig("m91", 1000)
    _t(f, 10, 20, "从你说定的事、或队列里的一张 issue，到一夜跑的一批票", "h")
    H = 456
    f.zone(4, 34, 236, H - 34, "从哪来")
    f.zone(248, 34, 500, H - 34, "白天 · 你在场")
    f.e(f'<rect class="zone open" x="756" y="34" width="240" height="{H - 34}" rx="6"/>', False)
    _t(f, 768, 53, "夜里 · 你不在", "h")

    talk_h = _box(f, "other", 16, 70, 212, "你在对话里说定的事", ["一个想法，问过、定过"], dashed=True)
    q_h = _box(f, "other", 16, 182, 212, "待判队列里的 issue", ["外来的报告和请求"], dashed=True)
    r_h = _box(f, "other", 16, 262, 212, "retro 的提案", ["你批准了的"], dashed=True)
    b_h = _box(f, "other", 16, 342, 212, "夜里交回的票", ["needs-triage 里的票和子票"], dashed=True)

    spec_h = _box(f, "playbook", 500, 70, 232, "Write a spec", ["写 spec、问你没定的产品决定、", "发布；最后一步跑 Cut tickets"])
    cut_h = _box(f, "playbook", 500, 200, 232, "Cut tickets", ["切票、扫歧义、问你定、", "发布在 spec 下面"])
    rev_h = _box(f, "playbook", 500, 330, 232, "Revise a spec", ["扩一份已发布的 spec，", "原地改，理由留在 spec 上"])
    tri_h = _box(f, "playbook", 262, 200, 206, "Triage", ["你挑，逐张用 triage 技能判；", "agent 做的进 spec"])
    run_h = _box(f, "playbook", 772, 200, 210, "Run a night", ["开夜、派 worker、收尾、", "你验收后 finish"])

    f.ar([(228, 88), (498, 88)])
    for y, h in ((182, q_h), (262, r_h), (342, b_h)):
        f.ar([(228, y + h / 2), (244, y + h / 2), (244, 200 + tri_h / 2), (260, 200 + tri_h / 2)])
    f.ar([(400, 200), (400, 118), (498, 118)], "新的一份", 408, 160)
    f.ar([(380, 200 + tri_h), (380, 362), (498, 362)], "扩已有的", 388, 352)
    f.ar([(640, 330), (640, 200 + cut_h + 2)], "新的那部分", 648, 312)
    f.ar([(616, 70 + spec_h), (616, 198)], "最后一步", 624, 172)
    f.ar([(732, 200 + cut_h / 2), (770, 200 + cut_h / 2)], cls="human")
    _t(f, 772, 190, "你说开始", "lbl")
    f.ar([(300, 200 + tri_h), (300, 428), (877, 428), (877, 200 + run_h + 2)])
    _t(f, 312, 446, "交回的票换回 ready-for-agent，下一次 advance 派 worker", "lbl")
    return f.svg(H + 8, ARIA_CHAIN)


ARIA_CHAIN = ("从你说定的事或队列里的一张 issue，到一夜跑的一批票。左边是来源：你在对话里说定的事，直接进 Write a spec；"
              "待判队列里的外来 issue、你批准了的 retro 提案、夜里交回到 needs-triage 的票和子票，都进 Triage。"
              "白天你在场：Triage 让你挑，逐张用 triage 技能判；agent 做的进 spec，要新的一份就走 Write a spec，扩一份已发布的就走 Revise a spec，"
              "再对新的那部分跑 Cut tickets；夜里交回的票判成 ready-for-agent 时不进 spec，标签换回去，下一次 advance 就派 worker。"
              "Write a spec 写 spec、问你没定的产品决定、发布，最后一步跑 Cut tickets。Cut tickets 切票、扫歧义、问你定，发布在 spec 下面。"
              "你说开始，夜里 Run a night 跑这一批：开夜、派 worker、收尾、你验收后 finish。")


def write_spec():
    steps = [
        ("1 读每一份来源", ["读你给的 issue、链接、文件，追到结论；", "一份 spec 还是几份：几份时分法问你，", "写进第一份的 ## Further Notes"],
         [("playbook", "改已发布的 spec：Revise a spec")], ("停下", ["docs/agents/ 两份文件缺了：", "仓库还没接入流水线"]), 0),
        ("2 读代码、词汇表和 ADR", ["用项目自己的词，守这一块的 ADR"],
         [("principle", "principle-start-from-what-exists"), ("other", "CONTEXT.md、这一块的 ADR")], None, 0),
        ("3 选 seam", ["测试在哪里看结果，又怎样把系统放进", "每个要测的状态；工程决定，会话自己做"],
         [("other", "CODING_STANDARDS.md 的 ## Tests")], None, 0),
        ("4 写 spec 并发布", ["照模板写；顾客看到的、钱、范围上没", "人定过的事先问你；不打 triage 标签"],
         [("script", "verify-ticket.py --publish --spec-body")], ("问你", ["来源没定的产品决定，", "带选项和你的建议"]), 0),
        ("5 切它的票", ["跑 Cut tickets"],
         [("playbook", "Cut tickets")], ("交回", ["spec 号、你可能要推翻", "的决定、切票的回复"]), 0),
    ]
    f, rows, bottom = flow("m92", "Write a spec：把已经定下的事写成 spec 发布，再切成一批票", steps,
                           "Write a spec 的步骤", "停下或问你")
    return f.svg(bottom + 8, ARIA_SPEC)


ARIA_SPEC = ("Write a spec 的五步，左列步骤，中列用到的组件，右列停下或问你的地方。开始前：仓库的 docs/agents/issue-tracker.md 或 triage-labels.md 缺了，就告诉你仓库还没接入流水线，停下。"
             "1 读每一份来源：读你给的 issue、链接、文件，追到结论；要改的是一份已发布的 spec 时改走 Revise a spec；判断是一份 spec 还是几份，几份时把分法问你，写进第一份的 ## Further Notes。"
             "2 读代码、词汇表 CONTEXT.md 和这一块的 ADR，用项目自己的词，照 principle-start-from-what-exists。"
             "3 选 seam：测试在哪里看结果，又怎样把系统放进每个要测的状态，依据 CODING_STANDARDS.md 的 ## Tests；这是工程决定，不问你。"
             "4 照模板写 spec；顾客看到的、钱、范围上来源没定的事，带选项和建议先问你；然后用 verify-ticket.py --publish --spec-body 发布，不打 triage 标签。"
             "5 跑 Cut tickets。交回：spec 号、你可能要推翻的决定、切票的回复。")


def cut_tickets():
    steps = [
        ("1 读 spec", ["读全正文和评论；没有发布的 spec，", "先走 Write a spec"], [("playbook", "Write a spec")], None, 0),
        ("2 读代码", ["每张票写哪个模块；有没有能先做的", "预备重构"], [], None, 0),
        ("3 切成竖切片", ["每片穿过每一层，能单独验证；大范围", "的机械改动走 expand–contract"],
         [("principle", "Migrate Callers Then Delete Legacy APIs")], None, 0),
        ("4 写每条判据", ["五个问题逐条问；规则要进 spec 的，", "走 Revise a spec；要你选的带到第 6 步"],
         [("reference", "verify-ticket 的 ticket-format.md"), ("playbook", "Revise a spec")], None, 0),
        ("5 定先后", ["新建的东西要改哪些现有文件才用得上，", "这些文件归同一张票；能同时跑的两张票", "不写同一个文件"],
         [("principle", "Separate Before Serializing Shared State")], None, 0),
        ("6 扫歧义，再问你", ["子代理读 spec 和草稿，找漏掉的决定；", "列出每张票的先后、交付、worker 等级、", "要你选的；改到你批准"],
         [("agent", "子代理：ambiguity scanner"), ("reference", "mmw-mode 的 ambiguity-scan.md")],
         ("问你", ["粒度、先后、等级，", "每个选择选哪个"]), 0),
        ("7 检查并发布", ["每张写成草稿，--lint --drafts 修到没有", "ERROR；再 --publish --drafts，它最后", "lint 发布后的整批"],
         [("script", "verify-ticket.py --lint --drafts"), ("script", "verify-ticket.py --publish --drafts"),
          ("reference", "verify-ticket 的 linting.md")], None, 0),
        ("8 读回整批", ["读发布最后那次 lint：没有 ERROR；每张", "ready-for-human 的票五样东西齐全"],
         [("script", "改了票再跑 verify-ticket.py --lint"), ("reference", "verify-ticket 的 person-ticket.md")],
         ("交回", ["这一批票；你说开始，", "Run a night 跑它"]), 0),
    ]
    f, rows, bottom = flow("m93", "Cut tickets：把一份发布了的 spec 切成你批准的一批票", steps,
                           "Cut tickets 的步骤", "问你或交回")
    return f.svg(bottom + 8, ARIA_CUT)


ARIA_CUT = ("Cut tickets 的八步，左列步骤，中列用到的组件，右列问你或交回的地方。"
            "1 读 spec 的全文和评论；没有发布的 spec 时先走 Write a spec。2 读代码：每张票写哪个模块，有没有能先做的预备重构。"
            "3 切成竖切片：每片穿过每一层，能单独验证；大范围的机械改动走 expand–contract，照 principle-migrate-callers-then-delete-legacy-apis。"
            "4 写每条判据：照 verify-ticket 的 ticket-format.md 逐条问五个问题；要进 spec 的规则走 Revise a spec；要你选的带到第 6 步。"
            "5 定先后：新建的东西要改哪些现有文件才用得上，这些文件归同一张票的 Owns；能同时跑的两张票不写同一个文件，照 principle-separate-before-serializing-shared-state。"
            "6 扫歧义，再问你：派一个子代理 ambiguity scanner，照 mmw-mode 的 references/ambiguity-scan.md 读 spec 和草稿，找漏掉的决定；"
            "然后列出每张票的先后、交付、worker 等级和要你选的，问你粒度、先后、等级和每个选择，改到你批准。"
            "7 检查并发布：每张写成草稿，照 linting.md，verify-ticket.py --lint --drafts 修到没有 ERROR，再 --publish --drafts，它最后对发布后的整批跑一次 lint。"
            "8 读回整批：读发布最后那次 lint，没有 ERROR，改了哪张票就再跑一次 --lint；每张 ready-for-human 的票照 person-ticket.md 五样东西齐全。交回这一批票；你说开始，Run a night 跑它。")


def triage():
    steps = [
        ("1 列出队列", ["没判过的、needs-triage、reporter 回了", "的 needs-info；你挑，或你点名"],
         [("skill", "triage 的 ## Show what needs attention")], ("问你", ["判哪几张"]), 0),
        ("2 逐张判", ["读全、查重、查以前拒过的、复现，", "要追问就追问；你定四个结果之一"],
         [("skill", "triage 的 ## Triage a specific issue"), ("reference", "triage 的 pipeline-issues.md"),
          ("skill", "grilling、domain-modeling")], ("问你", ["每张的结果"]), 0),
        ("3 agent 做的进 spec", ["新的一份：Write a spec，它最后切票；", "扩已发布的：Revise a spec 再", "Cut tickets；关 issue，链到 spec"],
         [("playbook", "Write a spec"), ("playbook", "Revise a spec"), ("playbook", "Cut tickets")],
         ("交回", ["每张一行结果和理由；", "写了哪些 spec；队列剩什么"]), 0),
    ]
    f, rows, bottom = flow("m94", "Triage：你挑，逐张判，agent 做的进 spec 和它的票", steps,
                           "Triage 的步骤", "问你或交回")
    return f.svg(bottom + 8, ARIA_TRIAGE)


ARIA_TRIAGE = ("Triage 的三步，左列步骤，中列用到的组件，右列问你或交回的地方。"
               "1 列出队列：照 triage 技能的 ## Show what needs attention，列出没判过的、needs-triage 的、reporter 回过话的 needs-info；问你判哪几张，或照你点名的。"
               "2 逐张判：照 triage 技能的 ## Triage a specific issue，读全、查重、查以前拒过的、复现，要追问就读 grilling 和 domain-modeling 追问；流水线开的 issue 照 references/pipeline-issues.md 读；每张的结果问你，四个结果之一。"
               "3 agent 做的进 spec：外来的 ready-for-agent issue 和你批准的 retro 提案，要新的一份走 Write a spec，它最后切票；扩一份已发布的走 Revise a spec 再 Cut tickets；然后关掉 issue，评论里链到那份 spec。"
               "交回：每张一行结果和理由，写了哪些 spec，队列里剩什么。")


def five():
    f = Fig("m95", 1000)
    _t(f, 10, 20, "想对一张票说的每一句话，依次问五个问题，第一个答「是」的决定它去哪", "h")
    rows = [
        ("1 是比较吗", ["相等、匹配、计数、过阈值，", "机器够得着"],
         [("other", "一条判据：CHECK: 和 EXPECT:", "跑命令就有对错")]),
        ("2 是判断吗", ["接口深不深、一段话够不够，", "机器够得着"],
         [("other", "spec 的 Implementation Decisions 一句", "代码审查的 Spec 轴读它"),
          ("playbook", "切票时经 Revise a spec 写进去", "")]),
        ("3 是一个人的反应吗", ["新人知不知道下一步、措辞", "顺不顺，只有人能量"],
         [("other", "一张 ready-for-human 票，kind reaction", "五样东西，见 person-ticket.md")]),
        ("4 机器能判，只是够不着", ["要先把系统放进某个状态，", "或要真设备、真账号"],
         [("other", "够得着的办法这一批要造：仍是判据", "spec 写明办法，有一张票 Owns 它"),
          ("other", "造不了：一张 ready-for-human 票，kind reach", "")]),
        ("5 是选择不是检查", ["没有对错，只有偏好，", "答案决定下一步做什么"],
         [("playbook", "Cut tickets 第 6 步问你", "答案写进那张票的 What to build")]),
    ]
    y = 44
    for i, (q, lines, dests) in enumerate(rows):
        h = _box(f, "other", 16, y, 340, q, lines)
        dy = y
        for kind, title, note in dests:
            dh = 40 if note else 26
            f.e(f'<g class="k-{kind}"><rect class="box" x="410" y="{dy}" width="574" height="{dh}" rx="4"/></g>', False)
            _t(f, 422, dy + 17, title, room=556)
            if note:
                _t(f, 422, dy + 33, note, room=556)
            dy += dh + 6
        f.ar([(356, y + 18), (408, y + 18)], "是", 376, y + 12)
        nxt = y + max(h, dy - y - 6) + 16
        if i < len(rows) - 1:
            f.ar([(60, y + h), (60, nxt - 2)], "否", 68, y + h + 13)
        y = nxt
    _box(f, "other", 16, y, 968, "没有命令，因为 spec 从没定过怎样验证它", ["不要自己编一条：先经 Revise a spec 定在 spec 的 Testing Decisions 里"], dashed=True)
    return f.svg(y + 47 + 10, ARIA_FIVE)


ARIA_FIVE = ("五个问题。想对一张票说的每一句话依次问，第一个答「是」的决定它去哪。"
             "1 是比较吗，相等、匹配、计数、过阈值，机器够得着：写成一条判据，CHECK: 和 EXPECT:，跑命令就有对错。"
             "2 是判断吗，接口深不深、一段话够不够，机器够得着：写成 spec 的 Implementation Decisions 里的一句，代码审查的 Spec 轴读它；切票时经 Revise a spec 写进去。"
             "3 是一个人的反应吗，新人知不知道下一步、措辞顺不顺，只有人能量：一张 ready-for-human 票，kind reaction，五样东西见 person-ticket.md。"
             "4 机器能判，只是够不着，要先把系统放进某个状态，或要真设备、真账号：够得着的办法这一批要造的，仍是判据，spec 写明办法，有一张票 Owns 它；造不了的，一张 ready-for-human 票，kind reach。"
             "5 是选择不是检查，没有对错只有偏好：Cut tickets 第 6 步问你，答案写进那张票的 What to build。"
             "没有命令，因为 spec 从没定过怎样验证它：不要自己编，先经 Revise a spec 定在 spec 的 Testing Decisions 里。")


# (v2 source chips, v3 destination chips, note); a dashed chip is not in v3 yet.
MOVES = [
    ([("skill", "to-spec 第 1 到 4 步、spec 模板")], [("playbook", "Write a spec")], "界面部分：第 12、13 课补回"),
    ([("reference", "to-spec 的 several-specs.md")], [("playbook", "Write a spec 第 1 步")], "地图那段见第 10 课"),
    ([("reference", "to-spec 的 revising-a-spec.md")], [("playbook", "Revise a spec")], "第 8 课"),
    ([("skill", "to-tickets 第 1 到 3、5、8 步")], [("playbook", "Cut tickets")], ""),
    ([("skill", "to-tickets 第 4 步")], [("reference", "ticket-format.md"), ("playbook", "Cut tickets 第 4 步")], "五个问题、一批票互相影响"),
    ([("skill", "to-tickets 第 6 步")], [("playbook", "Cut tickets 第 6 步"), ("reference", "ambiguity-scan.md")], "扫歧义的提示进 mmw-mode"),
    ([("skill", "to-tickets 第 7 步")], [("reference", "linting.md 草稿一段"), ("playbook", "Cut tickets 第 7 步")], ""),
    ([("reference", "to-tickets 的 person-ticket.md")], [("reference", "verify-ticket 的 person-ticket.md")], ""),
    ([("reference", "cutting-interface-tickets.md")], [("reference", "mmw-mode/references/ 同名")], "Cut tickets 第 3 步读；第 13 课"),
    ([("skill", "triage 里交给下一步的几句")], [("playbook", "Triage 第 3 步")], ""),
    ([("skill", "triage 其余")], [("skill", "triage")], "删掉 PR 的部分"),
    ([("skill", "domain-modeling（mattpocock）")], [("skill", "domain-modeling")], "GLOSSARY 改名 CONTEXT"),
]


def moves():
    f = Fig("m96", 1000)
    _t(f, 16, 22, "v2 的来源", "h")
    _t(f, 372, 22, "在 v3 里", "h")
    _t(f, 760, 22, "说明", "h")
    y = 44
    for src, dst, note in MOVES:
        x = 16
        for kind, label in src:
            x = _chip(f, kind, x, y, label) + 6
        f.ar([(340, y + 12), (368, y + 12)])
        x = 372
        for d in dst:
            kind, label = d[0], d[1]
            x = _chip(f, kind, x, y, label, dashed=len(d) > 2) + 6
        if note:
            _t(f, 760, y + 16.5, note, room=230)
        y += 32
    return f.svg(y + 6, ARIA_MOVES)


ARIA_MOVES = ("v2 的文字在 v3 里去了哪。to-spec 第 1 到 4 步和 spec 模板成为 Write a spec，screen contract 的设计部分第 12 课补回，验收部分第 13 课补回；"
              "to-spec 的 several-specs.md 进 Write a spec 第 1 步，地图那段见第 10 课；to-spec 的 revising-a-spec.md 成为 Revise a spec，见第 8 课。"
              "to-tickets 第 1 到 3、5、8 步成为 Cut tickets；第 4 步进 verify-ticket 的 ticket-format.md（五个问题、一批票互相影响）和 Cut tickets 第 4 步；"
              "第 6 步进 Cut tickets 第 6 步，扫歧义的提示进 mmw-mode 的 references/ambiguity-scan.md；第 7 步进 linting.md 的草稿一段和 Cut tickets 第 7 步；"
              "person-ticket.md 搬到 verify-ticket 下；cutting-interface-tickets.md 第 13 课搬进 mmw-mode/references/，Cut tickets 第 3 步读它。"
              "triage 里交给下一步的几句成为 Triage 第 3 步，其余留在 triage 技能，删掉 PR 的部分。mattpocock 的 domain-modeling 搬成 domain-modeling 技能，GLOSSARY 改名 CONTEXT。")


FIGS = {"l9-chain": chain, "l9-spec": write_spec, "l9-cut": cut_tickets, "l9-triage": triage,
        "l9-five": five, "l9-moves": moves}

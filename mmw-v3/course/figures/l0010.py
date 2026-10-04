"""Figures of lesson 0010: Work a ticket and Review a ticket as landed; which step uses each rule about tests;
the runs from closing a ticket to finish, now and as proposed."""
from kit import Fig, flow, txt as _t, tbox as _box


def work():
    steps = [
        ("1 认领，找到这一步", ["--preflight 认领并在没改的代码上跑一遍", "判据；有 RESUME: 行就去它点名的步"],
         [("script", "verify-ticket.py <n> --preflight")], ("NOT_READY", ["原因已在票上，停下"]), 0),
        ("2 读进来，写代码", ["票、Read first、spec 点名的几节、", "CONTEXT.md、Memory；先红后绿，", "一次一个 seam"],
         [("skill", "tdd（SKILL.md、tests.md、mocking.md）"),
          ("principle", "principle-a-check-must-be-able-to-fail"),
          ("principle", "principle-run-the-smallest-test-set"),
          ("principle", "principle-baseline-is-the-contract"),
          ("principle", "principle-never-block-on-the-human"),
          ("principle", "laziness、migrate-callers、start-from-…"),
          ("reference", "mmw-mode 的 references/memory.md")], None, 0),
        ("3 并入 base，跑每条判据", ["冲突时保住已落地的，提交合并后", "再 integrate；逐条跑判据，红了改产品"],
         [("script", "dispatch.sh integrate <n>"), ("script", "verify-ticket.py <n>（gate-check）"),
          ("principle", "principle-fix-the-product-not-the-check"),
          ("reference", "verify-ticket 的 ABANDON lines")],
         ("没有空闲的产品位", ["结束回合，等 worker.queued"]), 0),
        ("4 贴 decisions 评论", ["自己做的决定、Owns 以外改的文件"],
         [("script", "verify-ticket.py <n> --decisions")], None, 0),
        ("5 开 reviewer", ["一轮一个"], [("script", "dispatch.sh start <n> reviewer")],
         ("结束回合", ["等 reviewer.reported"]), 0),
        ("6 读审查报告", ["票内的修一轮或写 refuted；票外", "仍成立的开 finding 子票"],
         [("script", "dispatch.sh wait <n> reviewer"), ("script", "verify-ticket.py --sub-issue finding")],
         None, 0),
        ("7 最后跑一遍全部判据", ["在最终提交上，不再给修的机会"],
         [("script", "verify-ticket.py --reverify --actor worker")], None, 0),
        ("8 自查", ["What to build 每一点在产品里成立，", "不只在测试里成立"],
         [("principle", "principle-prove-it-works")], None, 0),
        ("9 告诉兄弟票", ["改了别的票拥有的文件就告诉它"],
         [("script", "verify-ticket.py <n> --touched")], None, 0),
        ("10 写结案草稿", ["Green before work 一节解释写代码前", "就绿的判据"],
         [("script", "verify-ticket.py <n> --draft")], None, 0),
        ("11 关票", ["贴结案评论，写 ticket.passed 或", "ticket.returned"],
         [("script", "verify-ticket.py <n> --closeout")], ("交给 orchestrator", ["它把票合进 base"]), 0),
    ]
    f, rows, bottom = flow("m101", "Work a ticket：worker 一个会话，从认领到关票", steps,
                           "Work a ticket 的步骤", "停下：结束回合，或交出去")
    return f.svg(bottom + 8, ARIA_WORK)


ARIA_WORK = ("Work a ticket 落地后的十一步，左列步骤，中列用到的组件，右列停下的地方。"
             "1 认领：verify-ticket.py --preflight 认领，并在没改的代码上跑一遍判据，有 RESUME 行就去它点名的步；NOT_READY 时原因已在票上，停下。"
             "2 读进来写代码：读票、Read first、spec 点名的几节、CONTEXT.md、Memory，先红后绿，一次一个 seam；用 tdd 的 SKILL.md、tests.md、mocking.md，principle-a-check-must-be-able-to-fail、principle-run-the-smallest-test-set、principle-baseline-is-the-contract、principle-never-block-on-the-human、laziness-protocol、migrate-callers、start-from-what-exists，以及 mmw-mode 的 references/memory.md。"
             "3 并入 base 跑每条判据：dispatch.sh integrate，冲突时保住已落地的，提交合并后再 integrate；verify-ticket.py 逐条跑判据，红了照 principle-fix-the-product-not-the-check 改产品，修不好写 ABANDON；没有空闲的产品位就结束回合等 worker.queued。"
             "4 用 --decisions 贴决定评论。5 dispatch.sh start 开 reviewer，结束回合等 reviewer.reported。"
             "6 读审查报告：票内的修一轮或写 refuted，票外仍成立的开 finding 子票。"
             "7 用 --reverify --actor worker 在最终提交上最后跑一遍全部判据。8 自查，用 principle-prove-it-works。"
             "9 --touched 告诉兄弟票。10 --draft 写结案草稿，解释写代码前就绿的判据。11 --closeout 关票，交给 orchestrator 合进 base。")


def review():
    steps = [
        ("1 钉住 diff", ["base 提交到 HEAD，三个点比合并基点；", "解析不了或 diff 为空就报失败"],
         [("other", "git rev-parse、git diff、git log")], ("失败", ["把失败当报告贴出，停下"]), 0),
        ("2 跑几条轴", ["一条轴一个子代理，同时跑，互相", "看不到；有界面判据才加 UI 轴"],
         [("skill", "code-review"), ("reference", "standards-reviewer.md"),
          ("reference", "spec-reviewer.md"), ("reference", "tests-reviewer.md")], None, 0),
        ("3 逐条核实", ["到引用的那一行看坏结果会不会发生：", "成立、refuted、或说不清"], [], None, 0),
        ("4 分票内票外", ["碰到判据、spec 那一节、Read first、", "Out of Scope、Testing Decisions、Owns", "就是票内"],
         [], None, 0),
        ("5 贴报告", ["固定格式；叫醒 worker"],
         [("script", "verify-ticket.py <n> --review")], ("交回 worker", ["reviewer.reported"]), 0),
    ]
    f, rows, bottom = flow("m102", "Review a ticket：reviewer 一个会话，只写一份报告", steps,
                           "Review a ticket 的步骤", "停下")
    return f.svg(bottom + 8, ARIA_REVIEW)


ARIA_REVIEW = ("Review a ticket 落地后的五步。1 钉住 diff：git rev-parse、git diff 三个点、git log，解析不了或 diff 为空就把失败当报告贴出并停下。"
               "2 跑几条轴：用 code-review 技能，一条轴一个子代理，Standards、Spec、Tests 三条同时跑、互相看不到，有界面判据才加 UI 轴。"
               "3 逐条核实：到引用的那一行看坏结果会不会发生，结论是成立、refuted 或说不清。"
               "4 分票内票外：碰到判据、spec 那一节、Read first、Out of Scope、Testing Decisions、Owns 的是票内。"
               "5 用 verify-ticket.py --review 贴固定格式的报告，叫醒 worker。")


# One row per moment a rule about tests is needed: the rules that hold then, and the steps that use them.
RULES = [
    ("写判据", "切票时", [("reference", "ticket-format.md：判据怎样写"), ("other", "仓库的 TESTING.md")],
     ["Bug fix 第 3 步", "Cut tickets（还没写）"], None),
    ("证明判据能红", "认领时", [("script", "--preflight 的基线运行")],
     ["Work a ticket 第 1 步", "第 10 步解释写前就绿的"], None),
    ("写测试", "写代码时", [("skill", "tdd：SKILL.md、tests.md、mocking.md"),
                        ("principle", "principle-a-check-must-be-able-to-fail"),
                        ("other", "仓库的 TESTING.md")],
     ["Work a ticket 第 2 步", "Make a small change 第 2 步"], "写测试的一方没被叫去读 TESTING.md"),
    ("边写边跑", "写代码时", [("principle", "principle-run-the-smallest-test-set")],
     ["Work a ticket 第 2 步", "Make a small change 第 3 步"], None),
    ("判定过没过", "写完之后", [("script", "verify-ticket.py 和 gate-check"),
                           ("principle", "principle-fix-the-product-not-the-check")],
     ["Work a ticket 第 3、7 步"], None),
    ("审测试", "审查时", [("reference", "code-review 的 tests-reviewer.md"), ("other", "仓库的 TESTING.md")],
     ["Review a ticket 第 2 步", "Make a small change 第 5 步"], None),
    ("守住 base", "落地时", [("other", ".mmw/target.json 的 checks"), ("script", "dispatch.sh 合并时跑")],
     ["advance、land", "Make a small change 第 6 步"], "Make a small change 推送前不跑 checks"),
    ("守住这一批", "一夜收尾", [("script", "dispatch.sh reverify")], ["Run a night 第 8 步（第 11 课）"], None),
    ("在产品上证明", "交出之前", [("principle", "principle-prove-it-works")],
     ["Work a ticket 第 8 步", "Make a small change 第 3 步", "Bug fix 第 5 步"], None),
]


def rules():
    f = Fig("m103", 1000)
    _t(f, 10, 20, "写测试的规则：每一刻用哪几样，哪一步来用", "h")
    y = 66
    placed = []
    for name, when, comps, users, gap in RULES:
        n = max(len(comps), len(users) + (1 if gap else 0))
        h = max(30 + 2 * 17, n * 30 + 4)
        placed.append((y, h, name, when, comps, users, gap))
        y += h + 12
    bottom = y + 2
    f.zone(4, 34, 170, bottom - 34, "什么时候")
    f.zone(180, 34, 400, bottom - 34, "规则和组件")
    f.zone(586, 34, 410, bottom - 34, "哪一步用")
    for y, h, name, when, comps, users, gap in placed:
        _t(f, 16, y + 20, name, "h", room=150)
        _t(f, 16, y + 38, when, "s", room=150)
        cy = y
        for kind, text in comps:
            dash = ' style="stroke-dasharray:6 3"' if kind == "other" else ""
            f.e(f'<g class="k-{kind}"><rect class="box" x="192" y="{cy}" width="376" height="24" rx="4"{dash}/></g>', False)
            _t(f, 202, cy + 16, text, room=360)
            cy += 30
        uy = y
        for u in users:
            f.e(f'<g class="k-playbook"><rect class="box" x="598" y="{uy}" width="386" height="24" rx="4"/></g>', False)
            _t(f, 608, uy + 16, u, room=370)
            uy += 30
        if gap:
            f.e(f'<g class="k-other"><rect class="box" x="598" y="{uy}" width="386" height="24" rx="4" style="stroke-dasharray:4 3"/></g>', False)
            _t(f, 608, uy + 16, "缺：" + gap, room=370)
        f.ar([(568, y + 12), (596, y + 12)])
    return f.svg(bottom + 8, ARIA_RULES)


ARIA_RULES = ("写测试的规则按需要它的那一刻排成九行，每行左边是时刻，中间是那一刻用的规则和组件，右边是用它的 playbook 步骤，虚线框是仓库自己的文件或缺口。"
              "写判据，切票时：ticket-format.md 写判据的规则和仓库的 TESTING.md；Bug fix 第 3 步，Cut tickets 还没写。"
              "证明判据能红，认领时：--preflight 的基线运行；Work a ticket 第 1 步，第 10 步解释写前就绿的。"
              "写测试，写代码时：tdd 的 SKILL.md、tests.md、mocking.md，principle-a-check-must-be-able-to-fail，仓库的 TESTING.md；Work a ticket 第 2 步和 Make a small change 第 2 步；缺口是写测试的一方没被叫去读 TESTING.md。"
              "边写边跑：principle-run-the-smallest-test-set；Work a ticket 第 2 步，Make a small change 第 3 步。"
              "判定过没过，写完之后：verify-ticket.py 和 gate-check，principle-fix-the-product-not-the-check；Work a ticket 第 3、7 步。"
              "审测试，审查时：code-review 的 tests-reviewer.md 和仓库的 TESTING.md；Review a ticket 第 2 步，Make a small change 第 5 步。"
              "守住 base，落地时：.mmw/target.json 的 checks，dispatch.sh 合并时跑；advance 和 land，Make a small change 第 6 步；缺口是 Make a small change 推送前不跑 checks。"
              "守住这一批，一夜收尾：dispatch.sh reverify；Run a night 第 8 步。"
              "在产品上证明，交出之前：principle-prove-it-works；Work a ticket 第 8 步，Make a small change 第 3 步，Bug fix 第 5 步。")


RUNS = [
    ("关票", "仓库检查，在票的分支上", ["这棵树多半不会原样落地：", "夜里别的票还在落地"],
     "不跑", ["worker 第 2 步已跑改动相关的测试", "和类型检查"], False),
    ("合并进 base", "仓库检查再跑；base 动过就跑", ["一夜里几乎每张票都动过"],
     "只在这里跑，每张票一次", ["这是唯一真正落进 base 的树"], True),
    ("一夜收尾", "每张落地票的判据在最终 base 上", ["重跑一遍"],
     "保留，一遍", ["仓库检查覆盖不到的判据只有它查；", "仓库没声明 checks 时它是唯一的一道"], True),
    ("finish", "仓库检查再跑，不管项目分支动没动", ["没动时，这棵树和最后一次落地时", "检查过的一模一样"],
     "项目分支没动过就不跑", ["动过才跑，那是一棵新树"], False),
]


def runs():
    f = Fig("m104", 1000)
    _t(f, 10, 20, "从关票到 finish：现在跑什么，建议跑什么", "h")
    y = 66
    rowh = 30 + 2 * 17
    bottom = 66 + len(RUNS) * (rowh + 14) + 2
    f.zone(4, 34, 130, bottom - 34, "什么时候")
    f.zone(140, 34, 420, bottom - 34, "现在")
    f.zone(566, 34, 430, bottom - 34, "建议")
    for when, now, why, keep, note, kept in RUNS:
        _t(f, 16, y + 20, when, "h", room=112)
        _box(f, "script", 152, y, 396, now, why + [""] * (2 - len(why)))
        _box(f, "script" if kept else "other", 578, y, 406, keep, note + [""] * (2 - len(note)), dashed=not kept)
        f.ar([(548, y + 20), (576, y + 20)])
        y += rowh + 14
    return f.svg(bottom + 8, ARIA_RUNS)


ARIA_RUNS = ("从关票到 finish 的四次运行，左边现在，右边建议，虚线框是建议去掉或改成有条件的。"
             "关票：现在在票的分支上跑仓库检查，这棵树多半不会原样落地，因为夜里别的票还在落地；建议不跑，worker 第 2 步已跑改动相关的测试和类型检查。"
             "合并进 base：现在 base 动过就再跑一次仓库检查，一夜里几乎每张票都动过；建议只在这里跑，每张票一次，这是唯一真正落进 base 的树。"
             "一夜收尾：每张落地票的判据在最终 base 上重跑一遍；建议保留一遍，仓库检查覆盖不到的判据只有它查，仓库没声明 checks 时它是唯一的一道。"
             "finish：现在不管项目分支动没动都再跑仓库检查，没动时这棵树和最后一次落地时检查过的一模一样；建议项目分支没动过就不跑，动过才跑。")


FIGS = {"l10-work": work, "l10-review": review, "l10-rules": rules, "l10-runs": runs}

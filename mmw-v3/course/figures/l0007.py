"""Figures of lesson 0007: one ticket from claim to land; Work a ticket, Review a ticket, Make a small change
and Bug fix, each step with what it names and where it stops; which step uses each rule about tests; when the
repository checks run from closing a ticket to finish."""
import html
from kit import Fig, flow, rule_table, txt as _t, tbox as _box


LANES = [("Run a night", "playbook", 150), ("Work a ticket（worker）", "playbook", 250),
         ("票上的事件", "config", 170), ("Review a ticket（reviewer）", "playbook", 230),
         ("三条轴（子代理）", "agent", 172)]
GAP = 4
LANE_X = []
_x = 4
for _name, _kind, _w in LANES:
    LANE_X.append(_x)
    _x += _w + GAP


def _lane_box(f, lane, y, title, lines, kind=None, mono=False):
    x = LANE_X[lane] + 6
    w = LANES[lane][2] - 12
    return _box(f, kind or LANES[lane][1], x, y, w, title, lines, mono_title=mono)


def _event(f, y, name, note=None):
    """An event written on the ticket, drawn in the ticket lane; returns the y of its middle."""
    x = LANE_X[2] + 6
    w = LANES[2][2] - 12
    h = 24 if note is None else 41
    f.e(f'<g class="k-config"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/></g>', False)
    _t(f, x + 10, y + 16, name, "m", room=w - 16)
    if note:
        _t(f, x + 10, y + 33, note, room=w - 16)
    return y + 12


def _right(lane):
    return LANE_X[lane] + LANES[lane][2] - 6


def _left(lane):
    return LANE_X[lane] + 6


def ticket():
    f = Fig("m70", 1000)
    _t(f, 10, 20, "一张票从认领到合进 base：worker 十一步，reviewer 五步，每一步在票上留下事件", "h")
    top = 34
    H_LANE = 1320
    for (name, kind, w), x in zip(LANES, LANE_X):
        f.e(f'<rect class="zone" x="{x}" y="{top}" width="{w}" height="{H_LANE}" rx="6"/>', False)
        f.e(f'<g class="k-{kind}"><text x="{x + 10}" y="{top + 20}" class="h">{html.escape(name)}</text></g>', False)

    def link(a_lane, b_lane, y):
        if a_lane < b_lane:
            f.ar([(_right(a_lane), y), (_left(b_lane) - 2, y)])
        else:
            f.ar([(_left(a_lane), y), (_right(b_lane) + 2, y)])

    y = top + 34
    _lane_box(f, 0, y, "advance", ["开 worker"], mono=True)
    m = _event(f, y + 8, "worker.started")
    link(0, 2, m)

    y += 70
    _lane_box(f, 1, y, "1 认领，找到这一步", ["--preflight；RESUME: 行", "按标题指回第 3 到 8 步"])
    m = _event(f, y + 8, "ticket.claimed")
    link(1, 2, m)

    y += 80
    _lane_box(f, 1, y, "2 读进来，写代码", ["票、Read first、spec 几节、", "Memory、CODING_STANDARDS.md；", "tdd 先红后绿，守写代码的规矩"])

    y += 98
    _lane_box(f, 1, y, "3 合进 base，跑判据", ["dispatch.sh integrate；", "verify-ticket.py <n>"])
    m = _event(f, y + 8, "ticket.checked", "run self")
    link(1, 2, m)

    y += 80
    _lane_box(f, 1, y, "4 贴 decisions 评论", ["--decisions：自己定的事、", "Owns 以外改的文件"])
    m = _event(f, y + 8, "worker.decided")
    link(1, 2, m)

    y += 80
    _lane_box(f, 1, y, "5 开 reviewer", ["dispatch.sh start <n> reviewer，", "然后结束回合，睡着等"])
    m = _event(f, y + 8, "reviewer.started")
    link(1, 2, m)
    link(2, 3, m)
    _lane_box(f, 3, y, "1 钉住 diff", ["base 提交到 HEAD；", "解析不了或为空就报失败"])

    y += 80
    _lane_box(f, 3, y, "2 跑几条轴", ["一条轴一个子代理，同时开；", "等每条都交回"])
    _lane_box(f, 4, y, "Standards", ["Spec", "Tests"], mono=True)
    link(3, 4, y + 30)
    _t(f, LANE_X[4] + 12, y + 92, "互相看不到对方", room=LANES[4][2] - 20)
    _t(f, LANE_X[4] + 12, y + 109, "的意见", room=LANES[4][2] - 20)

    y += 128
    _lane_box(f, 3, y, "3 逐条核实", ["到引用的那一行看坏结果会不", "会发生：成立、refuted、", "看不出"])
    y += 98
    _lane_box(f, 3, y, "4 分票内、票外", ["碰到六样东西之一的是票内"])
    y += 64
    _lane_box(f, 3, y, "5 贴报告", ["verify-ticket.py --review"])
    m = _event(f, y + 8, "reviewer.reported", "叫醒 worker")
    link(3, 2, m)
    link(2, 1, m + 8)

    y += 64
    _lane_box(f, 1, y, "6 读报告", ["票内的修一轮，或写 refuted:；", "票外仍成立的开 finding 子票"])

    y += 80
    _lane_box(f, 1, y, "7 最后跑一遍判据", ["--reverify --actor worker；", "这一轮不再修"])
    m = _event(f, y + 8, "ticket.checked", "run reverify")
    link(1, 2, m)

    y += 80
    _lane_box(f, 1, y, "8 自查  9 告诉别的票", ["对照票读一遍分支；--touched", "在被改了文件的票上留事件"])
    y += 76
    _lane_box(f, 1, y, "10 写结案草稿", ["--draft；每个 <fill> 填满"])
    y += 60
    _lane_box(f, 1, y, "11 关票", ["--closeout：贴结案评论"])
    m = _event(f, y + 8, "ticket.passed", "或 ticket.returned")
    link(1, 2, m)
    low = y + 80
    mid = LANE_X[2] + LANES[2][2] // 2
    f.ar([(mid, y + 49), (mid, low), (_right(0) + 2, low)])
    _lane_box(f, 0, low - 30, "advance", ["合进 base，", "跑仓库检查"], mono=True)
    _event(f, low + 24, "ticket.landed")
    return f.svg(top + H_LANE + 8, "一张票从认领到合进 base 分支，五条泳道。Run a night 的 advance 开 worker，票上写 worker.started。worker 照 Work a ticket 做十一步：1 用 --preflight 认领，写 ticket.claimed，有 RESUME 行就回到它点名的第 3 到 8 步之一；2 读票、Read first、spec 的几节、Memory 和仓库的 CODING_STANDARDS.md，用 tdd 先红后绿写代码；3 dispatch.sh integrate 合进 base，跑 verify-ticket.py，写 ticket.checked；4 贴 decisions 评论，写 worker.decided；5 开 reviewer，写 reviewer.started，然后结束回合。reviewer 照 Review a ticket 做五步：钉住 diff；一条轴一个子代理，Standards、Spec、Tests 同时跑，互相看不到；逐条核实；分票内票外；用 --review 贴报告，写 reviewer.reported，叫醒 worker。worker 接着：6 读报告，票内的修一轮或写 refuted，票外仍成立的开 finding 子票；7 最后跑一遍判据，写 ticket.checked；8 自查；9 --touched；10 写结案草稿；11 --closeout 关票，写 ticket.passed 或 ticket.returned。advance 把通过的票合进 base，在合并结果上跑仓库检查，写 ticket.landed。")


def work():
    steps = [
        ("1 认领，找到这一步", ["--preflight 认领并在没改的代码上跑一遍", "判据；有 RESUME: 行就去它点名的步"],
         [("script", "verify-ticket.py <n> --preflight"),
          ("principle", "principle-progress-is-what-the-record-…")], ("NOT_READY", ["原因已在票上，停下"]), 0),
        ("2 读进来，写代码", ["票、Read first、spec 点名的几节、", "CONTEXT.md、Memory、CODING_STANDARDS.md", "全文；先红后绿；要保住的行为先写 pin"],
         [("other", "仓库的 CODING_STANDARDS.md（含 ## Tests）"),
          ("skill", "tdd（SKILL.md、tests.md、mocking.md）"),
          ("principle", "principle-a-check-must-be-able-to-fail"),
          ("principle", "principle-run-the-smallest-test-set"),
          ("principle", "principle-baseline-is-the-contract"),
          ("principle", "principle-never-block-on-the-human"),
          ("principle", "principle-separate-before-serializing-…"),
          ("principle", "laziness、migrate-callers、start-from-…"),
          ("reference", "mmw-mode 的 references/memory.md")], None, 0),
        ("3 并入 base，跑每条判据", ["冲突时保住已落地的，跑冲突文件的", "测试，提交合并后再 integrate；", "逐条跑判据，红了改产品"],
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
        ("10 写结案草稿", ["写前就绿的判据：别的票做的、pin，", "或看不见本票（同时开 contract）"],
         [("script", "verify-ticket.py <n> --draft")], None, 0),
        ("11 关票", ["贴结案评论，写 ticket.passed 或", "ticket.returned；不跑仓库检查"],
         [("script", "verify-ticket.py <n> --closeout")], ("交给 orchestrator", ["合进 base 时跑仓库检查"]), 0),
    ]
    f, rows, bottom = flow("m72", "Work a ticket：worker 一个会话，从认领到关票", steps,
                           "Work a ticket 的步骤", "停下：结束回合，或交出去")
    return f.svg(bottom + 8, ARIA_WORK)


ARIA_WORK = ("Work a ticket 的十一步，左列步骤，中列用到的组件，右列停下的地方。"
             "1 认领：verify-ticket.py --preflight 认领，并在没改的代码上跑一遍判据，有 RESUME 行就去它点名的步，点名 principle-progress-is-what-the-record-says；NOT_READY 时原因已在票上，停下。"
             "2 读进来写代码：读票、Read first、spec 点名的几节、CONTEXT.md、Memory，以及仓库 CODING_STANDARDS.md 全文，连同它的 ## Tests 一节；先红后绿，要保住的行为先写 pin；用 tdd 的三份文件，principle-a-check-must-be-able-to-fail、principle-run-the-smallest-test-set、principle-baseline-is-the-contract、principle-never-block-on-the-human、principle-separate-before-serializing-shared-state（不改能并行的票拥有的文件）、laziness-protocol、migrate-callers、start-from-what-exists，以及 references/memory.md。"
             "3 并入 base 跑每条判据：dispatch.sh integrate，冲突时保住已落地的票的行为，跑冲突文件的测试，提交合并后再 integrate；verify-ticket.py 逐条跑，红了照 principle-fix-the-product-not-the-check 改产品；修不好写 ABANDON；没有空闲的产品位就结束回合等 worker.queued。"
             "4 贴 decisions 评论。5 开 reviewer，结束回合等 reviewer.reported。6 读审查报告。7 用 --reverify --actor worker 最后跑一遍。8 自查，用 principle-prove-it-works。9 --touched 告诉兄弟票。"
             "10 --draft 写结案草稿，写前就绿的判据有三种解释：别的票做的、pin、或这个 CHECK 看不见本票的行为，后一种同时开 contract 子票。"
             "11 --closeout 关票，不跑仓库检查，交给 orchestrator，合进 base 时跑仓库检查。")


def small():
    steps = [
        ("1 写下要改什么，判断够不够小", ["你的原话原样写进一个文件；够小 =", "一个会话做得完，不用你做产品决定"],
         [("other", "你的原话就是 spec")], ("不够小", ["告诉你它要一份 spec，", "这份 playbook 到此结束"]), 0),
        ("2 先写会失败的测试", ["读全 CODING_STANDARDS.md；seam 写进那个", "文件请你确认；要保住的行为先写 pin；",
                              "没有行为可测的，写下证明它的检查"],
         [("other", "仓库的 CODING_STANDARDS.md（含 ## Tests）"), ("skill", "tdd"),
          ("principle", "principle-a-check-must-be-able-to-fail"), ("principle", "principle-start-from-what-exists"),
          ("principle", "principle-migrate-callers-…"), ("principle", "principle-laziness-protocol"),
          ("principle", "principle-baseline-is-the-contract")], None, 0),
        ("3 在产品上证明，跑相关的测试", ["红了改产品，不改检查"],
         [("principle", "principle-prove-it-works"), ("principle", "principle-run-the-smallest-test-set"),
          ("principle", "principle-fix-the-product-not-the-check")], None, 0),
        ("4 提交", ["一个原因一个提交；只碰原因要求的", "和证明它的测试；提交信息引用测试", "输出的那一行"],
         [("other", "收尾自己修的也守这三条")], ("超出这三条", ["它其实是一张票，告诉你"]), 0),
        ("5 请没写它的读者看", ["code-review 三条轴，base 是开始前的", "提交，请求是第 1 步那个文件；每条",
                               "意见到代码上核实，成立的修"],
         [("skill", "code-review"), ("playbook", "Review a ticket 第 3 步")],
         ("开不了子代理", ["这一步记作没做，交回里", "写明，并给你新会话里", "要跑的那句话"]), 0),
        ("6 推到 base 分支", ["推之前跑仓库检查；被拒就取回、合并，", "重跑受影响的测试和仓库检查，再推"],
         [("other", ".mmw/target.json 的 checks")], None, 0),
    ]
    f, rows, bottom = flow("m73", "Make a small change：一个会话，六步，三个出口", steps,
                           "步骤（这个会话自己做）", "出口：停下，交回你")
    return f.svg(bottom + 8, ARIA_SMALL)


ARIA_SMALL = ("Make a small change 的六步，左列步骤，中列用到的组件，右列出口。"
              "1 把你的原话原样写进一个文件，那就是 spec，判断够不够小；不够小就告诉你它要一份 spec，到此结束。"
              "2 先写会失败的测试：先读全仓库的 CODING_STANDARDS.md，连同 ## Tests 一节；seam 写进那个文件请你确认；要保住的行为先写 pin；没有行为可测的写下证明它的检查；用 tdd、principle-a-check-must-be-able-to-fail、principle-start-from-what-exists、principle-migrate-callers-then-delete-legacy-apis、principle-laziness-protocol，你的原话点名已定的东西时用 principle-baseline-is-the-contract。"
              "3 在产品上证明并跑相关的测试，红了改产品不改检查。4 提交，守三条提交规矩，Run a night 收尾自己修的也守这三条，超出就是一张票。"
              "5 用 code-review 三条轴请没写它的读者看，开不了子代理就记作没做。"
              "6 推到 base 分支：推之前跑 .mmw/target.json 列的仓库检查；被拒就取回、合并，重跑受影响的测试和仓库检查，再推。")


def review():
    steps = [
        ("1 钉住 diff", ["base 提交到 HEAD，三个点比合并基点；", "解析不了或 diff 为空就报失败"],
         [("other", "git rev-parse、git diff、git log")], ("失败", ["把失败当报告贴出，停下"]), 0),
        ("2 跑三条轴", ["一条轴一个子代理，同时跑，互相", "看不到；等每条都交回"],
         [("skill", "code-review"), ("reference", "standards-reviewer.md"),
          ("reference", "spec-reviewer.md"), ("reference", "tests-reviewer.md")], None, 0),
        ("3 逐条核实", ["到引用的那一行看坏结果会不会发生：", "成立、refuted、或说不清"], [], None, 0),
        ("4 分票内票外", ["碰到判据、spec 那一节、Read first、", "Out of Scope、Testing Decisions、Owns", "就是票内"],
         [], None, 0),
        ("5 贴报告", ["固定格式；叫醒 worker"],
         [("script", "verify-ticket.py <n> --review")], ("交回 worker", ["reviewer.reported"]), 0),
    ]
    f, rows, bottom = flow("m71", "Review a ticket：reviewer 一个会话，只写一份报告", steps,
                           "Review a ticket 的步骤", "停下")
    return f.svg(bottom + 8, ARIA_REVIEW)


ARIA_REVIEW = ("Review a ticket 的五步。1 钉住 diff：git rev-parse、git diff 三个点、git log，解析不了或 diff 为空就把失败当报告贴出并停下。"
               "2 跑三条轴：用 code-review 技能，一条轴一个子代理，Standards、Spec、Tests 三条同时跑、互相看不到，拿住回合等每条都交回。"
               "3 逐条核实：到引用的那一行看坏结果会不会发生，结论是成立、refuted 或说不清。"
               "4 分票内票外：碰到判据、spec 那一节、Read first、Out of Scope、Testing Decisions、Owns 的是票内。"
               "5 用 verify-ticket.py --review 贴固定格式的报告，叫醒 worker。")


def bugfix():
    steps = [
        ("1 自己复现", ["在你看到它的那个界面上；做出一条", "跑过、能红在你说的症状上的命令，", "再把场景缩到最小"],
         [("skill", "diagnosing-bugs 第 1、2 阶段"), ("skill", "ui-acceptance 的五条规矩")],
         ("做不出这条命令", ["说试了什么、要你给什么，", "到此结束"]), 0),
        ("2 找到原因", ["3 到 5 个可证伪的假设，排好序给你", "看，不等你；一次只改一个变量；", "用运行时证据确认，删掉调试日志"],
         [("skill", "diagnosing-bugs 第 3、4 阶段"), ("skill", "how、why")],
         ("代码照要求在做", ["不是 bug：告诉你，转", "Make a small change 或 spec"]), 0),
        ("3 写一张票", ["症状、原因和证据、证据支持的最小", "改动；AC1 是 seam 上的回归测试，", "第 1 步的命令能无人值守就是 AC2"],
         [("reference", "verify-ticket 的 ticket-format.md"), ("script", "verify-ticket.py <n> --lint")], None, 0),
        ("4 落地", ["对这张票跑 Run one ticket"], [("playbook", "Run one ticket")], None, 0),
        ("5 在同一个界面上再证明", ["base 上用第 1 步的命令跑没缩小的", "原场景：红过的地方现在绿"],
         [("principle", "principle-prove-it-works")], None, 0),
    ]
    f, rows, bottom = flow("m76", "Bug fix：这个会话诊断、写票、落地、再证明，修复本身交给 worker", steps,
                           "步骤（这个会话自己做）", "出口：停下，交回你")
    return f.svg(bottom + 8, ARIA_BUGFIX)


ARIA_BUGFIX = ("Bug fix，五步，左列是这个会话做的步骤，中列是用到的技能、原则和 playbook，右列是出口。"
               "第 1 步自己复现：在你看到它的那个界面上做出一条跑过、能红在你说的症状上的命令，再把场景缩到最小，用 diagnosing-bugs 第 1、2 阶段，界面在跑时守 ui-acceptance 的五条规矩；做不出这条命令就说试了什么、要你给什么，到此结束。"
               "第 2 步找原因：3 到 5 个可证伪的假设排好序给你看但不等你，一次只改一个变量，用运行时证据确认，删掉调试日志，用 diagnosing-bugs 第 3、4 阶段和 how、why；代码其实照要求在做时不是 bug，告诉你，转 Make a small change 或 spec。"
               "第 3 步写一张票：症状、原因和证据、证据支持的最小改动，AC1 是 seam 上的回归测试，第 1 步的命令能无人值守就是 AC2，照 verify-ticket 的 ticket-format.md，用 verify-ticket.py --lint 查。"
               "第 4 步对这张票跑 Run one ticket。第 5 步在同一个界面上再证明：base 上用第 1 步的命令跑没缩小的原场景，红过的地方现在绿。")


RULES = [
    ("写判据", "切票时", [("reference", "ticket-format.md：判据怎样写，含 pin"),
                       ("other", "CODING_STANDARDS.md 的 ## Tests")],
     ["Bug fix 第 3 步", "Run a night 收尾写的票", "Cut tickets（还没写）"], None),
    ("证明判据能红", "认领时", [("script", "--preflight 的基线运行"),
                          ("principle", "principle-a-check-…：pin 手动弄红")],
     ["Work a ticket 第 1 步", "第 10 步解释写前就绿的，pin 是一种"], None),
    ("写测试", "写代码时", [("skill", "tdd：SKILL.md、tests.md、mocking.md"),
                        ("principle", "principle-a-check-must-be-able-to-fail"),
                        ("other", "CODING_STANDARDS.md 的 ## Tests")],
     ["Work a ticket 第 2 步", "Make a small change 第 2 步"], None),
    ("边写边跑", "写代码时", [("principle", "principle-run-the-smallest-test-set")],
     ["Work a ticket 第 2 步", "Make a small change 第 3 步"], None),
    ("判定过没过", "写完之后", [("script", "verify-ticket.py 和 gate-check"),
                           ("principle", "principle-fix-the-product-not-the-check")],
     ["Work a ticket 第 3、7 步"], None),
    ("审测试", "审查时", [("reference", "code-review 的 tests-reviewer.md"),
                       ("principle", "principle-a-check-…：cannot-fail、pin"),
                       ("other", "CODING_STANDARDS.md 的 ## Tests")],
     ["Review a ticket 第 2 步", "Make a small change 第 5 步"], None),
    ("守住 base", "每棵树落进 base 前", [("other", ".mmw/target.json 的 checks"),
                                    ("script", "dispatch.sh 合并时跑，每张票一次")],
     ["advance、land", "Make a small change 第 6 步", "Run a night 收尾自己修的"], None),
    ("守住这一批", "一夜收尾", [("script", "dispatch.sh reverify")], ["Run a night 第 8 步"], None),
    ("守住项目分支", "finish", [("script", "dispatch.sh finish：没检查过的树才跑")],
     ["Run a night 第 10 步"], None),
    ("在产品上证明", "交出之前", [("principle", "principle-prove-it-works")],
     ["Work a ticket 第 8 步", "Make a small change 第 3 步", "Bug fix 第 5 步"], None),
]


def rules():
    return rule_table("m74", "写测试的规则：每一刻用哪几样，哪一步来用", RULES, ARIA_RULES)


ARIA_RULES = ("写测试的规则按需要它的那一刻排成十行，左边是时刻，中间是那一刻用的规则和组件，右边是用它的 playbook 步骤，虚线框是消费仓库自己的文件。"
              "写判据，切票时：ticket-format.md 写判据的规则，含 pin，和 CODING_STANDARDS.md 的 ## Tests；Bug fix 第 3 步、Run a night 收尾写的票、还没写的 Cut tickets。"
              "证明判据能红，认领时：--preflight 的基线运行，以及 principle-a-check-must-be-able-to-fail 说的 pin 要手动弄红一次；Work a ticket 第 1 步，第 10 步解释写前就绿的判据，pin 是其中一种。"
              "写测试，写代码时：tdd 的三份文件、principle-a-check-must-be-able-to-fail、CODING_STANDARDS.md 的 ## Tests；Work a ticket 第 2 步、Make a small change 第 2 步。"
              "边写边跑：principle-run-the-smallest-test-set；Work a ticket 第 2 步、Make a small change 第 3 步。"
              "判定过没过：verify-ticket.py 和 gate-check、principle-fix-the-product-not-the-check；Work a ticket 第 3、7 步。"
              "审测试：tests-reviewer.md，它先问 principle-a-check-must-be-able-to-fail 的那个问题，能不能失败、pin 是否看着它要保住的行为，再用 CODING_STANDARDS.md 的 ## Tests；Review a ticket 第 2 步、Make a small change 第 5 步。"
              "守住 base，每棵树落进 base 前：.mmw/target.json 的 checks，dispatch.sh 合并时每张票跑一次；advance 和 land、Make a small change 第 6 步、Run a night 收尾自己修的。"
              "守住这一批，一夜收尾：dispatch.sh reverify；Run a night 第 8 步。"
              "守住项目分支，finish：dispatch.sh finish 只在树没检查过时跑；Run a night 第 10 步。"
              "在产品上证明，交出之前：principle-prove-it-works；Work a ticket 第 8 步、Make a small change 第 3 步、Bug fix 第 5 步。")


RUNS = [
    ("关票", "不跑仓库检查", ["这棵树多半不会原样落地：", "夜里别的票还在落地"], False),
    ("合并进 base", "每张票跑一次，跑在合并结果上", ["红了退回这张票，base 不动；", "这是真正落进 base 的树"], True),
    ("你自己推到 base", "推之前跑一次，被拒合并后再跑", ["Make a small change 第 6 步、收尾", "自己修的、reverify 红票的修复"], True),
    ("一夜收尾", "reverify 每张落地票的判据", ["不是仓库检查；仓库没声明 checks", "时它是唯一的一道"], True),
    ("finish", "只在合出来的树没检查过时跑", ["项目分支在 base 里、base 顶端是某张", "票落地的合并提交：不跑；否则跑"], True),
]


def runs():
    f = Fig("m75", 1000)
    _t(f, 10, 20, "从关票到 finish：仓库检查什么时候跑", "h")
    y = 66
    rowh = 30 + 2 * 17
    bottom = 66 + len(RUNS) * (rowh + 14) + 2
    f.zone(4, 34, 170, bottom - 34, "什么时候")
    f.zone(180, 34, 816, bottom - 34, "现在")
    for when, what, why, kept in RUNS:
        _t(f, 16, y + 20, when, "h", room=150)
        _box(f, "script" if kept else "other", 192, y, 792, what, why, dashed=not kept)
        y += rowh + 14
    return f.svg(bottom + 8, ARIA_RUNS)


ARIA_RUNS = ("从关票到 finish，仓库检查在五个时刻的做法；虚线框是不跑的。"
             "关票：不跑，这棵树多半不会原样落地，夜里别的票还在落地。"
             "合并进 base：每张票跑一次，跑在合并结果上，红了退回这张票、base 不动，这是真正落进 base 的树。"
             "你自己推到 base：推之前跑一次，被拒合并后再跑；包括 Make a small change 第 6 步、收尾自己修的、reverify 红票的修复。"
             "一夜收尾：reverify 重跑每张落地票的判据，不是仓库检查，仓库没声明 checks 时它是唯一的一道。"
             "finish：只在合出来的树没检查过时跑；项目分支在 base 里、base 的顶端是某张票落地时的合并提交，就不跑，否则跑。")


FIGS = {"l7-ticket": ticket, "l7-work": work, "l7-review": review, "l7-small": small, "l7-bugfix": bugfix,
        "l7-rules": rules, "l7-runs": runs}

"""Figures of lesson 0012: Revise a spec, Work a ticket and Make a small change as landed; which step uses
each rule about tests after the landing; the repository checks from closing a ticket to finish."""
from kit import Fig, flow, rule_table, txt as _t, tbox as _box


def revise():
    steps = [
        ("1 读 spec 和从它切出的票", ["读全 issue 正文和评论，列出子票；", "说出要改的那一节和从它切出的每张票"],
         [("other", "gh api …/issues/<spec>/sub_issues")], None, 0),
        ("2 改写那一节", ["改成像一开始就这样写的，", "写回 issue 正文"],
         [("principle", "principle-files-describe-the-present"), ("other", "gh issue edit --body-file")], None, 0),
        ("3 说改了什么、为什么", ["spec 上贴一条评论：改了什么、为什么、", "从哪张 issue、子票或决定来"], [], None, 0),
        ("4 让票对齐", ["没落地的票照新文字改，再 lint；前提", "没了的判据拿掉，编号不复用；落地的", "票跟一张更正票"],
         [("script", "verify-ticket.py <n> --lint"), ("reference", "verify-ticket 的 linting.md"),
          ("reference", "verify-ticket 的 ticket-format.md")],
         ("交回", ["改了哪一节、为什么，", "每张票怎样处理"]), 0),
    ]
    f, rows, bottom = flow("m121", "Revise a spec：原地改一份已发布的 spec，理由留在 spec 上", steps,
                           "Revise a spec 的步骤", "停下")
    return f.svg(bottom + 8, ARIA_REVISE)


ARIA_REVISE = ("Revise a spec 的四步，左列步骤，中列用到的组件，右列停下的地方。"
               "1 读 spec 和从它切出的票：读全 issue 正文和评论，用 gh api 列出子票，说出要改的那一节和从它切出的每张票。"
               "2 改写那一节：改成像一开始就这样写的，照 principle-files-describe-the-present，用 gh issue edit --body-file 写回。"
               "3 在 spec 上贴一条评论，说改了什么、为什么、从哪张 issue、子票或决定来。"
               "4 让票对齐：没落地的票照新文字改，再用 verify-ticket.py --lint 查，照 linting.md 读；前提没了的判据拿掉，编号不复用；落地的票跟一张照 ticket-format.md 写的更正票。然后交回：改了哪一节、为什么，每张票怎样处理。")


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
          ("principle", "laziness、migrate-callers、start-from-…"),
          ("reference", "mmw-mode 的 references/memory.md")], None, 0),
        ("3 并入 base，跑每条判据", ["冲突时保住已落地的，提交合并后", "再 integrate；逐条跑判据，红了改产品"],
         [("script", "dispatch.sh integrate <n>"), ("script", "verify-ticket.py <n>（gate-check）"),
          ("principle", "principle-fix-the-product-not-the-check"),
          ("principle", "principle-separate-before-serializing-…"),
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
    f, rows, bottom = flow("m122", "Work a ticket：worker 一个会话，从认领到关票", steps,
                           "Work a ticket 的步骤", "停下：结束回合，或交出去")
    return f.svg(bottom + 8, ARIA_WORK)


ARIA_WORK = ("Work a ticket 这次落地后的十一步，左列步骤，中列用到的组件，右列停下的地方。"
             "1 认领：verify-ticket.py --preflight 认领，并在没改的代码上跑一遍判据，有 RESUME 行就去它点名的步，点名 principle-progress-is-what-the-record-says；NOT_READY 时原因已在票上，停下。"
             "2 读进来写代码：读票、Read first、spec 点名的几节、CONTEXT.md、Memory，以及仓库 CODING_STANDARDS.md 全文，连同它的 ## Tests 一节；先红后绿，要保住的行为先写 pin；用 tdd 的三份文件，principle-a-check-must-be-able-to-fail、principle-run-the-smallest-test-set、principle-baseline-is-the-contract、principle-never-block-on-the-human、laziness-protocol、migrate-callers、start-from-what-exists，以及 references/memory.md。"
             "3 并入 base 跑每条判据：dispatch.sh integrate，verify-ticket.py 逐条跑，红了照 principle-fix-the-product-not-the-check 改产品；不改能并行的票拥有的文件，点名 principle-separate-before-serializing-shared-state；修不好写 ABANDON；没有空闲的产品位就结束回合等 worker.queued。"
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
          ("principle", "principle-a-check-must-be-able-to-fail"), ("principle", "principle-migrate-callers-…"),
          ("principle", "principle-laziness-protocol")], None, 0),
        ("3 在产品上证明，跑相关的测试", ["红了改产品，不改检查"],
         [("principle", "principle-prove-it-works"), ("principle", "principle-run-the-smallest-test-set"),
          ("principle", "principle-fix-the-product-not-the-check")], None, 0),
        ("4 提交", ["一个原因一个提交；只碰原因要求的", "和证明它的测试；提交信息引用测试", "输出的那一行"],
         [("other", "v2 night.md 收尾自己修的三条")], ("超出这三条", ["它其实是一张票，告诉你"]), 0),
        ("5 请没写它的读者看", ["code-review 三条轴，base 是开始前的", "提交，请求是第 1 步那个文件；每条",
                               "意见到代码上核实，成立的修"],
         [("skill", "code-review"), ("playbook", "Review a ticket 第 3 步")],
         ("开不了子代理", ["这一步记作没做，交回里", "写明，并给你新会话里", "要跑的那句话"]), 0),
        ("6 推到 base 分支", ["推之前跑仓库检查；被拒就取回、合并，", "重跑受影响的测试和仓库检查，再推"],
         [("other", ".mmw/target.json 的 checks")], None, 0),
    ]
    f, rows, bottom = flow("m123", "Make a small change：一个会话，六步，三个出口", steps,
                           "步骤（这个会话自己做）", "出口：停下，交回你")
    return f.svg(bottom + 8, ARIA_SMALL)


ARIA_SMALL = ("Make a small change 这次落地后的六步，左列步骤，中列用到的组件，右列出口。"
              "1 把你的原话原样写进一个文件，那就是 spec，判断够不够小；不够小就告诉你它要一份 spec，到此结束。"
              "2 先写会失败的测试：先读全仓库的 CODING_STANDARDS.md，连同 ## Tests 一节；seam 写进那个文件请你确认；要保住的行为先写 pin；没有行为可测的写下证明它的检查；用 tdd、principle-a-check-must-be-able-to-fail、principle-migrate-callers-then-delete-legacy-apis、principle-laziness-protocol。"
              "3 在产品上证明并跑相关的测试，红了改产品不改检查。4 提交，守三条提交规矩，超出就是一张票。"
              "5 用 code-review 三条轴请没写它的读者看，开不了子代理就记作没做。"
              "6 推到 base 分支：推之前跑 .mmw/target.json 列的仓库检查；被拒就取回、合并，重跑受影响的测试和仓库检查，再推。")


# The same moments as lesson 10, figure 5, after the landing: no gap is left.
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
    return rule_table("m124", "写测试的规则，落地之后：每一刻用哪几样，哪一步来用", RULES, ARIA_RULES)


ARIA_RULES = ("落地之后，写测试的规则按需要它的那一刻排成十行，左边是时刻，中间是那一刻用的规则和组件，右边是用它的 playbook 步骤，虚线框是消费仓库自己的文件；没有缺口了。"
              "写判据，切票时：ticket-format.md 写判据的规则，含 pin，和 CODING_STANDARDS.md 的 ## Tests；Bug fix 第 3 步、Run a night 收尾写的票、还没写的 Cut tickets。"
              "证明判据能红，认领时：--preflight 的基线运行，以及 principle-a-check-must-be-able-to-fail 说的 pin 要手动弄红一次；Work a ticket 第 1 步，第 10 步解释写前就绿的判据，pin 是其中一种。"
              "写测试，写代码时：tdd 的三份文件、principle-a-check-must-be-able-to-fail、CODING_STANDARDS.md 的 ## Tests；Work a ticket 第 2 步、Make a small change 第 2 步。"
              "边写边跑：principle-run-the-smallest-test-set；Work a ticket 第 2 步、Make a small change 第 3 步。"
              "判定过没过：verify-ticket.py 和 gate-check、principle-fix-the-product-not-the-check；Work a ticket 第 3、7 步。"
              "审测试：tests-reviewer.md 和 CODING_STANDARDS.md 的 ## Tests；Review a ticket 第 2 步、Make a small change 第 5 步。"
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
    f = Fig("m125", 1000)
    _t(f, 10, 20, "从关票到 finish：落地之后，仓库检查什么时候跑", "h")
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


ARIA_RUNS = ("落地之后，从关票到 finish，仓库检查在五个时刻的做法；虚线框是不跑的。"
             "关票：不跑，这棵树多半不会原样落地，夜里别的票还在落地。"
             "合并进 base：每张票跑一次，跑在合并结果上，红了退回这张票、base 不动，这是真正落进 base 的树。"
             "你自己推到 base：推之前跑一次，被拒合并后再跑；包括 Make a small change 第 6 步、收尾自己修的、reverify 红票的修复。"
             "一夜收尾：reverify 重跑每张落地票的判据，不是仓库检查，仓库没声明 checks 时它是唯一的一道。"
             "finish：只在合出来的树没检查过时跑；项目分支在 base 里、base 的顶端是某张票落地时的合并提交，就不跑，否则跑。")


FIGS = {"l12-revise": revise, "l12-work": work, "l12-small": small, "l12-rules": rules, "l12-runs": runs}

"""Figures of lesson 0011: Run a night's eleven steps; how one finding is routed; the authority order for a contract child."""
from kit import Fig, txt as _t, tbox as _box


def _flow(fig_id, heading, steps, aria, exit_head):
    """One session's steps down the left, what each names in the middle, where it stops on the right."""
    f = Fig(fig_id, 1000)
    _t(f, 10, 20, heading, "h")
    y = 66
    rows = []
    for title, lines, uses, exit_, gap_before in steps:
        y += gap_before
        h = 30 + len(lines) * 17
        rows.append((y, h, title, lines, uses, exit_))
        y += max(h, len(uses) * 30) + 18
    bottom = y + 4
    f.zone(4, 34, 384, bottom - 34, "Run a night 的步骤")
    f.zone(394, 34, 336, bottom - 34, "用到的")
    f.zone(736, 34, 260, bottom - 34, exit_head)
    for y, h, title, lines, uses, exit_ in rows:
        _box(f, "playbook", 16, y, 360, title, lines)
        uy = y
        for kind, u in uses:
            f.e(f'<g class="k-{kind}"><rect class="box" x="406" y="{uy}" width="312" height="24" rx="4"/></g>', False)
            _t(f, 416, uy + 16, u, room=296)
            uy += 30
        if uses:
            f.ar([(376, y + 14), (404, y + 14)])
        if exit_:
            et, el = exit_
            _box(f, "other", 748, y, 236, et, el + [""] * (len(lines) - len(el)), dashed=True)
            # Below a single chip the arrow runs along the step's foot; past a stack of chips
            # it runs through the 6px gap under the first one.
            ey = y + h - 10 if len(uses) < 2 else y + 27
            f.ar([(376, ey), (746, ey)])
    return f, rows, bottom


def night():
    steps = [
        ("1 找到你在哪一步", ["读 status 和 spec 自己的事件，", "走第一行成立的那一步"],
         [("script", "dispatch.sh status"), ("principle", "principle-progress-is-what-the-record-says")], None, 0),
        ("2 检查、开夜、检查整批票", ["check 修到 0；open 让这个会话成为", "orchestrator；第一次 advance 之前", "lint 整批票"],
         [("script", "dispatch.sh check、open"), ("script", "verify-ticket.py <spec> --lint"),
          ("reference", "verify-ticket 的 linting.md")], None, 0),
        ("3 advance", ["合进通过的票，给前沿上的票开 worker"],
         [("script", "dispatch.sh advance")], ("结束回合", ["等叫醒"]), 0),
        ("4 让每个 worker 守在自己的票上", ["你改它依据的东西，用 resume 告诉它，", "不碰它的工作区和分支"],
         [("script", "dispatch.sh resume")], None, 0),
        ("5 每次被叫醒", ["On waking，status，按表处理每一行，", "然后 advance 一次"],
         [("skill", "dispatch 的 On waking"), ("other", "Settling a contract child"),
          ("script", "dispatch.sh retract")], ("结束回合", ["前沿空、没有活着的 agent", "时转第 6 步"]), 0),
        ("6 处理每条还开着的 finding", ["先查 Step 0，再按四步分流，先匹配", "的算；自己修的守三条提交规矩"],
         [("script", "dispatch.sh findings、route"), ("other", "Routing a finding"),
          ("reference", "verify-ticket 的 ticket-format.md")], ("写了票", ["advance 后结束回合，", "前沿再空时回到这一步"]), 26),
        ("7 关掉这份 spec 的 Memory 记录", ["每条判 retain、deprecate、", "supersede 或 propose"],
         [("script", "dispatch.sh memory-list")], None, 0),
        ("8 收夜", ["reverify 每张落地的票；summary 贴", "NIGHT SUMMARY，关掉这一夜的 watch"],
         [("script", "dispatch.sh reverify、summary")], ("还有票是红的", ["告诉你哪张、为什么，", "停下"]), 0),
        ("9 跑 retro", ["只认证据；贴 NIGHT RETRO，", "记下 spec.retroed"],
         [("skill", "retro")], ("交回你", ["两份报告在 spec 上，", "等你验收"]), 0),
        ("10 你验收之后 finish", ["合进项目分支；合进默认分支是你的", "发布决定"],
         [("script", "dispatch.sh finish")], None, 0),
        ("11 暂停这一夜（从第 1、5 步来）", ["毛病在流水线上时；工作区、分支、", "已推的提交都留着"],
         [("script", "dispatch.sh suspend")], ("交回你", ["stderr 留下的每一行"]), 26),
    ]
    f, rows, bottom = _flow("m111", "Run a night：一个会话，从开夜守到 finish，中间每次叫醒都回到它", steps, ARIA_NIGHT,
                            "停下：结束回合，或交回你")
    # Phase labels in the gaps before step 6 and step 11.
    y6 = rows[5][0]
    y11 = rows[10][0]
    _t(f, 16, y6 - 10, "收尾：前沿空了，没有活着的 agent", "s", room=360)
    _t(f, 16, y11 - 10, "不在顺序里：流水线本身坏了", "s", room=360)
    # The loop from step 5 back to step 3.
    y3, h3 = rows[2][0], rows[2][1]
    y5, h5 = rows[4][0], rows[4][1]
    f.ar([(16, y5 + h5 / 2), (8, y5 + h5 / 2), (8, y3 + h3 / 2), (14, y3 + h3 / 2)])
    return f.svg(bottom + 8, ARIA_NIGHT)


ARIA_NIGHT = ("Run a night 的十一步，左列是步骤，中列是每一步用到的脚本、技能、原则和参考，右列是会话停下的地方。"
              "1 找到你在哪一步：读 dispatch.sh status 和 spec 自己的事件，走第一行成立的那一步，用 principle-progress-is-what-the-record-says。"
              "2 检查、开夜、检查整批票：check 修到 0，open 让这个会话成为 orchestrator，第一次 advance 之前用 verify-ticket.py lint 整批票，照 linting.md。"
              "3 advance：合进通过的票，给前沿上的票开 worker，然后结束回合等叫醒。"
              "4 让每个 worker 守在自己的票上：你改它依据的东西，用 resume 告诉它，不碰它的工作区和分支。"
              "5 每次被叫醒：做 dispatch 的 On waking，读 status，按表处理每一行，contract 子票照 Settling a contract child，丢了会话的 worker 用 retract，然后 advance 一次；前沿空、没有活着的 agent 时转第 6 步，否则结束回合；第 5 步回到第 3 步是一个循环。"
              "收尾从第 6 步开始。6 处理每条还开着的 finding：dispatch.sh findings 列出，先查 Step 0，再按四步分流，自己修的守三条提交规矩，写成票的照 ticket-format.md，都用 route 关掉；写了票就 advance 后结束回合，前沿再空时回到这一步。"
              "7 关掉这份 spec 的 Memory 记录：dispatch.sh memory-list，每条判 retain、deprecate、supersede 或 propose。"
              "8 收夜：reverify 每张落地的票，summary 贴 NIGHT SUMMARY 并关掉这一夜的 watch；还有票是红的就告诉你哪张、为什么，停下。"
              "9 跑 retro 技能：只认证据，贴 NIGHT RETRO，记下 spec.retroed；交回你，等你验收。"
              "10 你验收之后跑 dispatch.sh finish，合进项目分支；合进默认分支是你的发布决定。"
              "11 不在顺序里：流水线本身坏了时，从第 1 或第 5 步来，dispatch.sh suspend 暂停这一夜，工作区、分支、已推的提交都留着，stderr 留下的每一行交回你。")


def route():
    f = Fig("m112", 1000)
    _t(f, 10, 20, "一条 finding 怎样分流：自上而下，第一个答「是」的就是它的去处", "h")
    qx, qw = 16, 430
    ox, ow = 560, 424
    rows = [
        ("Step 0　它说的情况，在当前 HEAD 上成立过吗？", ["先于分类；只看 finding 正文写的条件"],
         "从没成立过：route stale invalid", ["成立过、已被别处修好：", "route stale fixed-elsewhere"], "否则", "other"),
        ("1　落在另一张还开着的票的 ## Owns 里？", ["不看大小，看并发：你一修，那张票", "合进来时就冲突"],
         "写成票，Blocked by 那张", ["principle-separate-before-serializing-", "shared-state"], "是", "principle"),
        ("2　是判据本身的缺口吗？", ["CHECK: 绿着，它说的东西却坏着", "或根本没走到"],
         "写成票，senior-worker", ["要一个能变红的反向对照", "principle-a-check-must-be-able-to-fail"], "是", "principle"),
        ("3　修它要动两个以上、设计上互相牵连的文件？", ["改一个的方式决定另一个怎么改；", "同一个名字在几处文字里出现不算"],
         "写成票，senior-worker", ["跨文件的形状要有人看"], "是", "other"),
        ("4　都不是", ["默认是自己修，不是开票"],
         "自己修，然后 route fixed", ["一个原因一个提交；只碰原因要求的", "和证明它的测试；提交信息引用测试", "输出的那一行；超出三条就是一张票"], "是", "other"),
    ]
    y = 56
    prev_bottom = None
    ticket_rows = []
    for i, (q, ql, ot, ol, yes, okind) in enumerate(rows):
        hq = _box(f, "playbook", qx, y, qw, q, ql)
        ho = _box(f, okind, ox, y, ow, ot, ol)
        f.ar([(qx + qw, y + 20), (ox - 2, y + 20)])
        label = "没成立，或已修好" if i == 0 else ("" if i == len(rows) - 1 else "是")
        if label:
            _t(f, (qx + qw + ox) / 2, y + 14, label, "s", anchor="middle")
        if prev_bottom is not None:
            f.ar([(qx + 60, prev_bottom), (qx + 60, y - 2)])
            _t(f, qx + 70, prev_bottom + 15, "仍成立" if i == 1 else "否", "s")
        if ot.startswith("写成票"):
            ticket_rows.append(y + 20)
        prev_bottom = y + hq
        y += max(hq, ho) + 26
    # Every ticket the rows above write is written and linted the same way.
    hb = _box(f, "reference", ox, y, ow, "写成的票", ["照 verify-ticket 的 ticket-format.md 写，", "每条判据由一条命令判定；下次 advance", "之前 lint；route became-ticket"])
    rail = ox + ow + 9
    for ty in ticket_rows:
        f.ar([(ox + ow, ty), (rail, ty)], head=False)
    f.ar([(rail, ticket_rows[0]), (rail, y + 20), (ox + ow + 2, y + 20)])
    y += hb + 12
    return f.svg(y, ARIA_ROUTE)


ARIA_ROUTE = ("一条 finding 的分流，自上而下，第一个答是的就是它的去处。"
              "Step 0 先于分类：它正文说的情况在当前 HEAD 上从没成立过，route stale invalid；成立过但已被这一批后面的票或收尾的修复解决了，route stale fixed-elsewhere。"
              "1 落在另一张还开着的票的 ## Owns 里：写成票，Blocked by 那张，因为你一修，那张票合进来时就冲突，用 principle-separate-before-serializing-shared-state。"
              "2 是判据本身的缺口，CHECK 绿着而它说的东西坏着或根本没走到：写成票，senior-worker，要一个能变红的反向对照，用 principle-a-check-must-be-able-to-fail。"
              "3 修它要动两个以上、设计上互相牵连的文件：写成票，senior-worker；同一个名字在几处文字里出现不算牵连。"
              "4 都不是：自己修，守三条提交规矩，一个原因一个提交，只碰原因要求的和证明它的测试，提交信息引用测试输出的那一行，超出三条就是一张票；然后 route fixed。"
              "写成的票照 verify-ticket 的 ticket-format.md 写，每条判据由一条命令判定，下次 advance 之前 lint，route became-ticket。")


def authority():
    f = Fig("m113", 1000)
    _t(f, 10, 20, "contract 子票：照这个顺序找一条写下来的权威", "h")
    ladder = [("决定票和 ADR", "config"), ("spec", "config"), ("设计包，或 screen contract（各管自己那一块）", "config"),
              ("领域文档（CONTEXT.md）", "config"), ("票的正文", "config")]
    x, w = 16, 400
    y = 56
    tops = []
    for i, (name, kind) in enumerate(ladder):
        h = _box(f, kind, x, y, w, f"{i + 1}　{name}", [])
        tops.append((y, h))
        if i:
            f.ar([(x + w / 2, y - 14), (x + w / 2, y - 2)])
        y += h + 16
    _t(f, x + w + 8, tops[0][0] + 20, "高", "s")
    _t(f, x + w + 8, tops[-1][0] + 20, "低", "s")
    ladder_bottom = y - 16
    ox, ow = 470, 514
    y1 = 56
    h1 = _box(f, "playbook", ox, y1, ow, "能引用一条：自己改", [
        "spec 的一节，跑 Revise a spec；票的正文和判据，", "直接在 tracker 上改；仓库里的 baseline，一个推到", "origin/<base branch> 的提交",
        "同一句错话派生出的每张还没落地的票都改；子票上", "评论写明依据、改了什么、提交、查过哪些票；", "route fixed；resume worker，带上改动和提交"])
    y2 = y1 + h1 + 20
    h2 = _box(f, "other", ox, y2, ow, "没有一条能定，或会推翻你定过的事", [
        "还没开工的、同一个决定派生的票移到 needs-triage；", "子票上写选项、建议和移走的票号，留给你；正在做的", "票停在这个问题上，不改它要交付的东西",
        "点名 Claude Design 页面的子票也走这里：设计包只能", "从 Claude Design 重新拉，这一夜做不到"], dashed=True)
    mid = ladder_bottom / 2 + 28
    f.ar([(x + w + 26, mid), (ox - 2, y1 + h1 / 2)])
    f.ar([(x + w + 26, mid), (ox - 2, y2 + h2 / 2)])
    bottom = max(ladder_bottom, y2 + h2) + 10
    return f.svg(bottom, ARIA_AUTH)


ARIA_AUTH = ("contract 子票的权威顺序，从高到低：1 决定票和 ADR；2 spec；3 设计包或 screen contract，各管自己那一块；4 领域文档 CONTEXT.md；5 票的正文。"
             "能引用其中一条写下来的权威时自己改：spec 的一节跑 Revise a spec，票的正文和判据直接在 tracker 上改，仓库里的 baseline 用一个推到 origin/<base branch> 的提交；同一句错话派生出的每张还没落地的票都改；子票上评论写明依据、改了什么、提交、查过哪些票；route fixed；resume worker，带上改动和提交。"
             "没有一条能定，或改动会推翻你定过的事、扩大 spec 时，把还没开工的、同一个决定派生的票移到 needs-triage，子票上写选项、建议和移走的票号，留给你；正在做的票停在这个问题上，不改它要交付的东西。点名 Claude Design 页面的子票也走这条：设计包只能从 Claude Design 重新拉，这一夜做不到。")


FIGS = {"l11-night": night, "l11-route": route, "l11-authority": authority}

"""Figures of lesson 0009: one ticket from claim to close; Make a small change and Bug fix, each with its exits."""
import html
from kit import Fig, txt as _t, tbox as _box


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
    f = Fig("m91", 1000)
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
    _lane_box(f, 1, y, "1 认领，找到这一步", ["--preflight；RESUME: 行", "按标题指回某一步"])
    m = _event(f, y + 8, "ticket.claimed")
    link(1, 2, m)

    y += 80
    _lane_box(f, 1, y, "2 读进来，写代码", ["票、Read first、spec 几节、", "Memory 索引；tdd 先红后绿；", "写代码的规矩（第 4 节）"])

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
    _lane_box(f, 0, low - 30, "advance", ["合进 base 分支"], mono=True)
    _event(f, low + 24, "ticket.landed")
    return f.svg(top + H_LANE + 8, "一张票从认领到合进 base 分支，五条泳道。Run a night 的 advance 开 worker，票上写 worker.started。worker 照 Work a ticket 做十一步：1 用 --preflight 认领，写 ticket.claimed；2 读票、Read first、spec 的几节和 Memory 索引，用 tdd 先红后绿写代码；3 dispatch.sh integrate 合进 base，跑 verify-ticket.py，写 ticket.checked；4 贴 decisions 评论，写 worker.decided；5 开 reviewer，写 reviewer.started，然后结束回合。reviewer 照 Review a ticket 做五步：钉住 diff；一条轴一个子代理，Standards、Spec、Tests 同时跑，互相看不到；逐条核实；分票内票外；用 --review 贴报告，写 reviewer.reported，叫醒 worker。worker 接着：6 读报告，票内的修一轮或写 refuted，票外仍成立的开 finding 子票；7 最后跑一遍判据，写 ticket.checked；8 自查；9 --touched；10 写结案草稿；11 --closeout 关票，写 ticket.passed 或 ticket.returned。advance 把通过的票合进 base，写 ticket.landed。")


def _use_kind(u):
    first = u.split()[0].rstrip("、")
    if ".py" in first:
        return "script"
    if first in ("tdd", "code-review", "diagnosing-bugs", "how", "why", "verify-ticket", "ui-acceptance"):
        return "skill"
    if u.startswith("principle"):
        return "principle"
    if u.startswith(("Review a ticket", "Run one ticket")):
        return "playbook"
    return "reference"


def _flow(fig_id, heading, steps, aria):
    """One session's steps down the left, what each names in the middle, its exits on the right."""
    f = Fig(fig_id, 1000)
    _t(f, 10, 20, heading, "h")
    y = 66
    rows = []
    for title, lines, uses, exit_ in steps:
        h = 30 + len(lines) * 17
        rows.append((y, h, title, lines, uses, exit_))
        y += max(h, len(uses) * 30) + 18
    bottom = y + 4
    f.zone(4, 34, 384, bottom - 34, "步骤（这个会话自己做）")
    f.zone(394, 34, 336, bottom - 34, "用到的")
    f.zone(736, 34, 260, bottom - 34, "出口：停下，交回你")
    for y, h, title, lines, uses, exit_ in rows:
        _box(f, "playbook", 16, y, 360, title, lines)
        uy = y
        for u in uses:
            f.e(f'<g class="k-{_use_kind(u)}"><rect class="box" x="406" y="{uy}" width="312" height="24" rx="4"/></g>', False)
            _t(f, 416, uy + 16, u, room=296)
            uy += 30
        if uses:
            f.ar([(376, y + 14), (404, y + 14)])
        if exit_:
            et, el = exit_
            _box(f, "other", 748, y, 236, et, el + [""] * (len(lines) - len(el)), dashed=True)
            f.ar([(376, y + h - 10), (746, y + h - 10)])
    return f.svg(bottom + 8, aria)


def small():
    return _flow("m92", "Make a small change：一个会话，六步，三个出口", [
        ("1 写下要改什么，判断够不够小", ["你的原话原样写进一个文件；够小 =", "一个会话做得完，不用你做产品决定"],
         ["你的原话就是 spec"], ("不够小", ["告诉你它要一份 spec，", "这份 playbook 到此结束"])),
        ("2 先写会失败的测试", ["没有票，seam 写进那个文件请你确认；", "没有行为可测的，写下改完后用来", "证明的那条检查"],
         ["tdd", "principle-a-check-must-be-able-to-fail", "principle-migrate-callers-…",
          "principle-laziness-protocol"], None),
        ("3 在产品上证明，跑仓库的检查", ["红了改产品，不改检查"],
         ["principle-prove-it-works", "principle-run-the-smallest-test-set",
          "principle-fix-the-product-not-the-check"], None),
        ("4 提交", ["一个原因一个提交；只碰原因要求的", "和证明它的测试；提交信息引用测试", "输出的那一行"],
         ["v2 night.md 收尾自己修的三条"], ("超出这三条", ["它其实是一张票，告诉你"])),
        ("5 请没写它的读者看", ["code-review 三条轴，base 是开始前的", "提交，请求是第 1 步那个文件；每条", "意见到代码上核实，成立的修"],
         ["code-review", "Review a ticket 第 3 步"], ("开不了子代理", ["这一步记作没做，交回里", "写明，并给你新会话里", "要跑的那句话"])),
        ("6 推到 base 分支", ["被拒就取回、合并、重跑受影响的", "测试，再推"], [], None),
    ], "Make a small change，一个会话做完的六步，左列是步骤，中列是每一步用到的技能和原则，右列是停下交回的出口。第 1 步把你的原话原样写进一个文件，判断够不够小：一个会话做得完、不用你做产品决定；不够小就告诉你它要一份 spec，到此结束。第 2 步用 tdd 先写会失败的测试，seam 写进那个文件请你确认，没有行为可测的写下改完后用来证明的检查；用到 principle-a-check-must-be-able-to-fail、principle-migrate-callers-then-delete-legacy-apis 和 principle-laziness-protocol。第 3 步在产品上证明并跑仓库的检查，红了改产品不改检查；用到 principle-prove-it-works、principle-run-the-smallest-test-set、principle-fix-the-product-not-the-check。第 4 步提交，照 v2 night.md 收尾自己修的三条：一个原因一个提交，只碰原因要求的和证明它的测试，提交信息引用测试输出的那一行；超出这三条它其实是一张票。第 5 步用 code-review 的三条轴请没写它的读者看，每条意见按 Review a ticket 第 3 步到代码上核实；宿主开不了子代理时这一步记作没做，交回里写明。第 6 步推到 base 分支，被拒就取回、合并、重跑受影响的测试再推。")


def bugfix():
    return _flow("m93", "Bug fix：这个会话诊断、写票、落地、再证明，修复本身交给 worker", [
        ("1 自己复现", ["在你看到它的那个界面上；做出一条", "跑过、能红在你说的症状上的命令，", "再把场景缩到最小"],
         ["diagnosing-bugs 第 1、2 阶段", "ui-acceptance 的五条规矩"],
         ("做不出这条命令", ["说试了什么、要你给什么，", "到此结束"])),
        ("2 找到原因", ["3 到 5 个可证伪的假设，排好序给你", "看，不等你；一次只改一个变量；", "用运行时证据确认，删掉调试日志"],
         ["diagnosing-bugs 第 3、4 阶段", "how、why"],
         ("代码照要求在做", ["不是 bug：告诉你，转", "Make a small change 或 spec"])),
        ("3 写一张票", ["症状、原因和证据、证据支持的最小", "改动；AC1 是 seam 上的回归测试，", "第 1 步的命令能无人值守就是 AC2"],
         ["verify-ticket 的票格式", "verify-ticket.py --lint"], None),
        ("4 落地", ["对这张票跑 Run one ticket"], ["Run one ticket"], None),
        ("5 在同一个界面上再证明", ["base 上用第 1 步的命令跑没缩小的", "原场景：红过的地方现在绿"],
         ["principle-prove-it-works"], None),
    ], "Bug fix，五步，左列是这个会话做的步骤，中列是用到的技能、原则和 playbook，右列是出口。第 1 步自己复现：在你看到它的那个界面上做出一条跑过、能红在你说的症状上的命令，再把场景缩到最小，用 diagnosing-bugs 第 1、2 阶段，界面在跑时守 ui-acceptance 的五条规矩；做不出这条命令就说试了什么、要你给什么，到此结束。第 2 步找原因：3 到 5 个可证伪的假设排好序给你看但不等你，一次只改一个变量，用运行时证据确认，删掉调试日志，用 diagnosing-bugs 第 3、4 阶段和 how、why；代码其实照要求在做时不是 bug，告诉你，转 Make a small change 或 spec。第 3 步写一张票：症状、原因和证据、证据支持的最小改动，AC1 是 seam 上的回归测试，第 1 步的命令能无人值守就是 AC2，照 verify-ticket 的票格式，用 verify-ticket.py --lint 查。第 4 步对这张票跑 Run one ticket。第 5 步在同一个界面上再证明：base 上用第 1 步的命令跑没缩小的原场景，红过的地方现在绿。")


FIGS = {"l9-ticket": ticket, "l9-small": small, "l9-bugfix": bugfix}

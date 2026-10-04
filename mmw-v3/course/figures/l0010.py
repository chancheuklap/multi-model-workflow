"""Figure of lesson 0010: where the workflow tests a change on its way to the base branch, and what of each is in v3."""
from kit import Fig, txt as _t, tbox as _box

ROWS = [
    ("切票", "reference", "每条判据写成 CHECK 和 EXPECT", ["由一条命令判定，不由写代码的人说了算"],
     "● 格式已落地", ["verify-ticket 的 ticket-format.md；哪些", "规则能成判据（五个问题）留给切票那一课"]),
    ("认领", "script", "先在没改过的代码上跑一遍判据", ["写代码前就绿的判据，结案时要解释"],
     "● 已搬", ["verify-ticket.py --preflight；", "Work a ticket 第 10 步的 Green before work"]),
    ("写代码", "playbook", "先红后绿", ["CHECK 点名的用例先跑红，", "红要红在行为不存在上"],
     "● 已落地", ["Work a ticket 第 2 步，tdd，", "principle-a-check-must-be-able-to-fail"]),
    ("并入最新 base", "script", "逐条跑判据", ["退出 0 且输出匹配 EXPECT 才算过"],
     "◐ 脚本已搬，界面判官没有", ["verify-ticket.py 和 gate-check 在；4 个界面", "判官没搬，点名它们的票会被拒绝"]),
    ("审查", "skill", "Tests 轴：这些测试值不值得信", ["六种坏测试，对照仓库的 TESTING.md"],
     "◐ 部分", ["界面两段留给界面验收；", "TESTING.md 没有技能负责写"]),
    ("审查修完", "script", "最后一次跑全部判据", ["这一次不再给修的机会"],
     "● 已落地", ["Work a ticket 第 7 步"]),
    ("关票", "script", "跑仓库自己的检查 checks", ["lint、类型检查、整套测试，", "由仓库在 .mmw/target.json 里声明"],
     "○ 只有脚本，没有说明", ["checks 是什么、谁来写，v3 里没有一句；", "写检查命令的 code-checkers 没搬"]),
    ("合并进 base", "script", "checks 再跑一次", ["关票时同一提交跑过且通过就跳过；", "红了不合并，记 ticket.bounced"],
     "● 已搬", ["dispatch.sh advance 和 land"]),
    ("一夜收尾", "script", "在 base 上重跑每张落地票的判据", ["后来的票弄坏了它，就重开它"],
     "◇ 第 11 课设计", ["dispatch.sh reverify"]),
    ("finish", "script", "合进项目分支前再跑 checks", ["红了什么都不推"],
     "● 已搬", ["dispatch.sh finish"]),
]


def chain():
    f = Fig("m101", 1000)
    _t(f, 10, 20, "一张票的改动，在去 base 分支的路上被测了几次", "h")
    y = 66
    placed = []
    for when, kind, title, lines, st, sl in ROWS:
        h = 30 + max(len(lines), len(sl)) * 17
        placed.append((y, h, when, kind, title, lines, st, sl))
        y += h + 14
    bottom = y + 2
    f.zone(4, 34, 130, bottom - 34, "什么时候")
    f.zone(140, 34, 420, bottom - 34, "测什么")
    f.zone(566, 34, 430, bottom - 34, "v3 里现在")
    for i, (y, h, when, kind, title, lines, st, sl) in enumerate(placed):
        _t(f, 16, y + 20, when, "h", room=112)
        _box(f, kind, 152, y, 396, title, lines + [""] * (len(sl) - len(lines)))
        dashed = not st.startswith("●")
        _box(f, "other", 578, y, 406, st, sl + [""] * (len(lines) - len(sl)), dashed=dashed)
        f.ar([(548, y + 20), (576, y + 20)], head=False)
        if i:
            py, ph = placed[i - 1][0], placed[i - 1][1]
            f.ar([(350, py + ph), (350, y - 2)])
    return f.svg(bottom + 8, ARIA)


ARIA = ("一张票的改动在去 base 分支的路上被测的十处，左列是时刻，中列是测什么，右列是 v3 里现在的状态。"
        "切票时每条判据写成 CHECK 和 EXPECT，由一条命令判定，格式已落地在 verify-ticket 的 ticket-format.md，哪些规则能成判据留给切票那一课。"
        "认领时先在没改过的代码上跑一遍判据，写代码前就绿的判据结案时要解释，已搬，verify-ticket.py --preflight 和 Work a ticket 第 10 步。"
        "写代码时先红后绿，CHECK 点名的用例先跑红，已落地在 Work a ticket 第 2 步、tdd 和 principle-a-check-must-be-able-to-fail。"
        "worker 把最新的 base 并进票的分支之后逐条跑判据，退出 0 且输出匹配 EXPECT 才算过，verify-ticket.py 和 gate-check 已搬，4 个界面判官没搬，点名它们的票会被拒绝。"
        "审查时 Tests 轴看测试值不值得信，部分落地，界面两段留给界面验收，TESTING.md 没有技能负责写。"
        "审查修完后最后一次跑全部判据，已落地在 Work a ticket 第 7 步。"
        "关票时跑仓库自己的检查 checks，只有脚本，checks 是什么、谁来写 v3 里没有一句说明，写检查命令的 code-checkers 没搬。"
        "合并进 base 时 checks 再跑一次，关票时同一提交跑过且通过就跳过，红了不合并，已搬在 dispatch.sh advance 和 land。"
        "一夜收尾时在 base 上重跑每张落地票的判据，第 11 课设计。finish 合进项目分支前再跑 checks，已搬。")

FIGS = {"l10-tests": chain}

"""Figures of lesson 0015: the loop from a review finding back to the rules the review applies; where a
retro lesson goes, and the bar a CODING_STANDARDS.md row must clear."""
from kit import Fig, txt as _t, tbox as _box


def loop():
    f = Fig("m151", 1000)
    SX = 315          # spine of the left column
    RX, RW = 650, 340  # the files, right column

    f.pill(SX, 10, "一份 spec 要写了")
    f.ar([(SX, 44), (SX, 84)])

    # before the night
    _t(f, 10, 72, "写之前", "h")
    _box(f, "playbook", 10, 86, 610, "Write a spec 第 3 步：选 seam，写 ## Testing Decisions",
         ["读仓库的 TESTING.md：有哪几层、哪些外部边界打桩、测试怎样把系统", "放进一个状态；用到的那一行写进 spec"])
    f.ar([(SX, 150), (SX, 166)])
    _box(f, "playbook", 10, 168, 610, "Cut tickets：每张票的 Seam 和 Read first", ["抄进 spec 用到的 TESTING.md 那几行"])
    _box(f, "other", RX, 86, RW, "仓库根 TESTING.md（事实）",
         ["setup-mmw 第 9 步照代码写：测试在哪、", "怎样跑、哪几层、哪些边界打桩、", "怎样把系统放进一个状态"], dashed=True)
    f.ar([(RX - 2, 118), (622, 118)])

    # the night: one ticket
    f.ar([(SX, 215), (SX, 262)])
    _t(f, 10, 250, "夜里：一张票", "h")
    _box(f, "playbook", 10, 264, 610, "Work a ticket：worker 写代码和测试",
         ["读票、Read first、spec 里点名的几节、Memory 索引；", "不读 CODING_STANDARDS.md，也不直接读 TESTING.md"])
    f.ar([(SX, 328), (SX, 344)])
    _box(f, "playbook", 10, 346, 610, "Review a ticket：code-review 派出各轴",
         ["Standards 轴：通用的 ## Code，加仓库自己那一份，加词汇表",
          "Tests 轴：通用的 ## Tests，加仓库自己那一份，加 TESTING.md",
          "两轴的报告第一行是 Standards applied:，缺了就重派一次",
          "每条意见用它违反的那条规则的名字做类别"])
    _box(f, "skill", RX, 296, RW, "code-review/CODING_STANDARDS.md（通用）",
         ["7 条 ## Code，9 条 ## Tests", "整份放进两轴的提示词", "写代码的人不读；只经批准的提案改"])
    f.ar([(RX - 2, 362), (622, 362)])
    _box(f, "other", RX, 392, RW, "仓库根 CODING_STANDARDS.md（可以没有）",
         ["只放这个仓库才成立的判断，轴自己读", "同样只经批准的 retro 提案建或改"], dashed=True)
    f.ar([(RX - 2, 428), (622, 428)])

    f.ar([(SX, 444), (SX, 468)])
    f.dia(SX, 504, 120, 34, ["这条意见", "在票内吗？"])
    f.ar([(SX - 120, 504), (130, 504), (130, 560)], "在票内", 138, 496)
    f.ar([(SX + 120, 504), (500, 504), (500, 560)], "票外", 452, 496)
    _box(f, "playbook", 10, 562, 250, "worker 修一轮，或答 refuted:", ["refuted: 写明坏结果为什么", "不会在那一处发生"])
    _box(f, "playbook", 380, 562, 240, "worker 开 finding 子票", ["不挡这张票关"])
    f.ar([(10, 594), (4, 594), (4, 980), (9, 980)])
    _t(f, 14, 648, "refuted: 留在收尾评论里，retro 第 7 步读它", "s", room=360)
    f.ar([(500, 609), (500, 700)])

    # closing the night
    _t(f, 10, 690, "收夜：Run a night 第 6 到 9 步", "h")
    _box(f, "playbook", 10, 702, 610, "第 6 步 route 每条 finding",
         ["fixed · stale invalid · stale fixed-elsewhere · became-ticket"])
    f.ar([(SX, 749), (SX, 763)])
    _box(f, "playbook", 10, 765, 610, "第 7 步 这份 spec 的每条 Worker Memory 判一次",
         ["retain · deprecate · supersede · propose（交给 retro）"])
    f.ar([(SX, 812), (SX, 826)])
    _box(f, "script", 10, 828, 610, "第 8 步 reverify、summary：记下 spec.closed", [])
    f.ar([(SX, 858), (SX, 900)])

    # the retro
    _t(f, 10, 890, "第 9 步 retro，同一个会话", "h")
    _box(f, "skill", 10, 902, 610, "gather：这一夜的事件、提交、文件，逐条标「在、缺、读不了」", [])
    f.ar([(SX, 932), (SX, 946)])
    _box(f, "skill", 10, 948, 610, "七类各查一遍，另记 review_learning",
         ["无效的意见：route 成 stale invalid，或 worker 答 refuted: 而没被推翻",
          "按类别数：两条引用同一条规则的无效意见，指向改写或删掉那一行"])
    f.ar([(SX, 1012), (SX, 1028)])
    f.dia(SX, 1062, 140, 34, ["下次怎样不再发生？", "去处见图 2"])
    f.ar([(SX, 1096), (SX, 1112)])
    f.dia(SX, 1154, 190, 42, ["同一原因两次独立发生？或 propose", "的记录加上一个卡住的事件？"])
    f.ar([(SX + 190, 1154), (RX - 2, 1154)], "都没有", SX + 200, 1146)
    _box(f, "other", RX, 1124, RW, "只记 Handled here",
         ["一次是偶然；写成一行，以后每个", "读它的 agent 都要付这份代价"])
    f.ar([(SX, 1196), (SX, 1212)], "有", SX + 8, 1208)
    f.dia(SX, 1246, 120, 34, ["同因的提案", "还开着吗？"])
    f.ar([(SX - 120, 1246), (145, 1246), (145, 1272)], "开着", 152, 1238)
    f.ar([(SX + 120, 1246), (480, 1246), (480, 1272)], "没有", 440, 1238)
    _box(f, "skill", 10, 1274, 280, "在那份提案上加一条评论", ["existing：不再开第二份"])
    _box(f, "skill", 340, 1274, 280, "开一份 needs-triage 提案", ["标题 Retro #<spec>: …"])
    f.ar([(145, 1321), (145, 1350)])
    f.ar([(480, 1321), (480, 1350)])
    _box(f, "script", 10, 1352, 610, "finalize：写 Retro Memory，贴 NIGHT RETRO（spec.retroed）", [])

    # the owner
    f.ar([(SX, 1382), (SX, 1424)])
    _t(f, 10, 1412, "你", "h")
    _box(f, "other", 10, 1426, 610, "triage：每份提案你批准或不批准", [])
    f.ar([(SX, 1456), (SX, 1470)])
    _box(f, "playbook", 10, 1472, 610, "批准的写成 spec 和票，在一夜里落地",
         ["去处是 coding-standard 的：在 CODING_STANDARDS.md 加、改或删一行"])
    f.ar([(622, 1496), (995, 1496), (995, 340), (992, 340)])
    _t(f, RX + 10, 1488, "下一次审查起，各轴就用这一行", "s", room=RW - 20)
    return f.svg(1532, ARIA_LOOP)


ARIA_LOOP = ("第 15 课图 1，一条把审查意见送回审查规则的回路。写之前：Write a spec 第 3 步读仓库根的 TESTING.md，选 seam、写 Testing Decisions，"
             "用到的那一行写进 spec；Cut tickets 把这几行抄进每张票的 Seam 和 Read first。TESTING.md 是事实，由 setup-mmw 第 9 步照代码写。"
             "夜里：Work a ticket 的 worker 只读票、Read first、spec 里点名的几节和 Memory 索引，不读 CODING_STANDARDS.md，也不直接读 TESTING.md。"
             "Review a ticket 由 code-review 派出各轴：Standards 轴拿通用的 Code 规则、仓库自己那一份和词汇表；Tests 轴拿通用的 Tests 规则、仓库自己那一份和 TESTING.md。"
             "通用的 code-review/CODING_STANDARDS.md 有 7 条 Code、9 条 Tests，整份放进两轴的提示词；仓库根的 CODING_STANDARDS.md 可以没有，只放这个仓库才成立的判断，轴自己读。"
             "两轴报告第一行是 Standards applied:，缺了就重派一次；每条意见用它违反的规则名做类别。票内的意见 worker 修一轮或答 refuted:，票外的开 finding 子票。"
             "收夜：Run a night 第 6 步 route 每条 finding（fixed、stale invalid、stale fixed-elsewhere、became-ticket），第 7 步每条 Worker Memory 判 retain、deprecate、supersede 或 propose，"
             "第 8 步 reverify、summary 记下 spec.closed。第 9 步 retro：gather 逐条标在、缺、读不了；七类各查一遍，另记 review_learning，"
             "无效的意见是 route 成 stale invalid 的，或 worker 答 refuted: 而没被推翻的，两条引用同一条规则的无效意见指向改写或删掉那一行。"
             "然后定下次怎样不再发生（去处见图 2）；同一原因两次独立发生，或 propose 的记录加一个卡住的事件，才写提案，否则只记 Handled here。"
             "同因的提案还开着，就在它上面加一条评论（existing），否则开一份 needs-triage 提案。finalize 写 Retro Memory，贴 NIGHT RETRO。"
             "你在 triage 批准或不批准；批准的写成 spec 和票，在一夜里落地；去处是 coding-standard 的，就在 CODING_STANDARDS.md 加、改或删一行，下一次审查起各轴就用它。")


def destination():
    f = Fig("m152", 1000)
    SX = 480
    RX, RW = 740, 250
    LW = 260

    f.pill(SX, 10, "retro 找到一条有证据的问题")
    f.ar([(SX, 44), (SX, 58)])
    f.dia(SX, 100, 175, 40, ["违规的形状固定吗？", "禁用的调用、import 写法、文件位置"])
    f.ar([(SX + 175, 100), (RX - 2, 100)], "固定", SX + 183, 92)
    _box(f, "script", RX, 64, RW, "check 或 script",
         ["先看仓库已有的检查命令：有却没", "接上，或悄悄坏了，那就是要报的问题"])
    f.ar([(SX, 140), (SX, 166)], "要判断", SX + 8, 158)
    f.dia(SX, 200, 130, 32, ["在 diff 里", "看得出吗？"])
    f.ar([(SX - 130, 200), (140, 200), (140, 244)], "看不出", 200, 192)
    _box(f, "other", 10, 246, LW, "看谁读这条教训",
         ["repository-agents：AGENTS.md 的指路行", "repository-skill：这个仓库的多步流程",
          "mmw-skill：MMW 的 playbook、原则、", "　mode 的一节或技能；用户级提示词",
          "toolbox-memory：拷进 toolbox Memory", "none：什么都防不了下一次"])
    f.ar([(SX, 232), (SX, 258)], "看得出", SX + 8, 250)
    f.dia(SX, 312, 190, 52, ["会改变以后一次审查报什么，", "规则、气味、检查都没盖住，", "代码变了也还成立？"])
    f.ar([(SX + 190, 312), (RX - 2, 312)], "有一条不是", SX + 196, 304)
    _box(f, "other", RX, 282, RW, "只记 Handled here",
         ["多一行，每次审查都要多读一行"])
    f.ar([(SX, 364), (SX, 392)], "都是", SX + 8, 386)
    f.dia(SX, 426, 140, 32, ["所有仓库", "都成立吗？"])
    f.ar([(SX + 140, 426), (RX - 2, 426)], "都成立", SX + 148, 418)
    _box(f, "skill", RX, 404, RW, "通用的 CODING_STANDARDS.md",
         ["在 code-review 技能里", "提案开在 MMW 仓库"])
    f.ar([(SX - 140, 426), (LW + 12, 426)], "只在这里", LW + 16, 418)
    _box(f, "other", 10, 404, LW, "仓库根 CODING_STANDARDS.md",
         ["没有就由这份提案建"], dashed=True)
    f.ar([(10 + LW / 2, 451), (10 + LW / 2, 500), (SX - 2, 500)], head=False)
    f.ar([(RX + RW / 2, 468), (RX + RW / 2, 500), (SX + 2, 500)], head=False)
    f.ar([(SX, 500), (SX, 522)])
    _box(f, "playbook", SX - 250, 524, 500, "提案写出那一行，原样",
         ["规则名、算违规的情形、细节在哪；放进哪一份"])
    f.ar([(SX, 571), (SX, 590)])
    f.pill(SX, 592, "两次独立发生，你批准，一夜落地")
    _t(f, 10, 660, "改写或删掉一行，要同样的证据，方向相反：引用它的无效意见。", "s", room=980)
    return f.svg(676, ARIA_DEST)


ARIA_DEST = ("第 15 课图 2，retro 找到一条有证据的问题后，它的教训去哪，一行怎样进 CODING_STANDARDS.md。"
             "先问违规的形状固定吗，比如禁用的调用、import 写法、文件位置：固定的去 check 或 script，先看仓库已有的检查命令，有却没接上或悄悄坏了，那就是要报的问题。"
             "要判断的，再问在 diff 里看得出吗：看不出的按谁读这条教训分去 repository-agents（AGENTS.md 的指路行）、repository-skill（这个仓库的多步流程）、"
             "mmw-skill（MMW 的 playbook、原则、mode 的一节或技能，或用户级提示词）、toolbox-memory（拷进 toolbox Memory）或 none。"
             "看得出的，再问三件事：会改变以后一次审查报什么吗，已有的规则、Standards 轴的气味和检查都没盖住吗，代码变了也还成立吗；有一条不是，就只记 Handled here，因为多一行，每次审查都要多读一行。"
             "三件都是，再问所有仓库都成立吗：都成立的进通用的 CODING_STANDARDS.md，在 code-review 技能里，提案开在 MMW 仓库；只在这里成立的进仓库根的 CODING_STANDARDS.md，没有就由这份提案建。"
             "提案原样写出那一行：规则名、算违规的情形、细节在哪、放进哪一份。同一原因两次独立发生、你批准，才在一夜里落地。改写或删掉一行要同样的证据，方向相反：引用它的无效意见。")


FIGS = {"l15-loop": loop, "l15-dest": destination}

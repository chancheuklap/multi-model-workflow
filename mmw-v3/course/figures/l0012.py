"""Figures of lesson 0012: the design side from a winning prototype to a spec; where v2's design-side
text went; the two tickets an interface adds to a map."""
from kit import Fig, txt as _t, tbox as _box


def path():
    f = Fig("m121", 1000)
    _t(f, 10, 20, "设计这一侧：赢的原型进 Claude Design，签字后拉进仓库，再和后端的决定对齐", "h")
    H = 570
    f.zone(4, 34, 372, H - 34, "这个会话跑的（要有 Claude Design 工具）")
    f.zone(384, 34, 612, H - 34, "留下的东西，和谁定它")
    steps = [
        ("skill", "prototype 的 UI 分支", ["几种截然不同的界面，你挑一种；", "赢的那种列出每个区域的状态"], False),
        ("playbook", "Build a design system", ["可选：产品的变量、零件、字体、图标，", "由 Claude Design 里的 agent 建"], True),
        ("playbook", "Design in Claude Design", ["建项目、写约定和 task.md，", "处理你发来的评论，直到你签字"], False),
        ("playbook", "Pull a design", ["把签了字的项目原样拉进仓库，", "读报告，按改了什么交给下一步"], False),
        ("playbook", "Write the screen contract", ["每个控件绑到它背后的后端决定；", "定不了的列成清单，由你定"], False),
        ("playbook", "Write a spec", ["读两份基线：设计包管长相和原文，", "screen contract 管调用和流转"], False),
    ]
    outs = [
        ("other", "prototypes/<effort>/<issue>/UI/", ["leaf README 的 ## State list：一个区域一个标题，", "每个状态一行；你挑赢家"]),
        ("other", "Claude Design 里的设计系统项目", ["每个零件一张卡；readme.md 末尾的 Unifications 表，", "代码里不一致的值统一成哪一个，你定"]),
        ("other", "Claude Design 里的页面项目", ["CLAUDE.md、state-list.md、ui-ids.md、task.md；", "页面怎么长由你和那边的 agent 定，你签字"]),
        ("other", "prototypes/<effort>/claude-design/", ["设计包和 pull-report.md，提交进 git；", "git 是设计唯一的版本历史"]),
        ("other", "docs/specs/<effort>/screen-contract.yaml", ["每个用户看得见的行为一行：调用什么、显示哪个字段、", "成功去哪、失败去哪、出处；空缺清单的答案是你的"]),
        ("other", "spec 的 API contract、cross-component composition", ["从 screen contract 的行推出来，每条注明行号"]),
    ]
    y = 58
    at = {}
    for (kind, title, lines, dashed), (okind, otitle, olines) in zip(steps, outs):
        at[title] = y
        h = _box(f, kind, 16, y, 348, title, lines, dashed=dashed)
        oh = _box(f, okind, 396, y, 588, otitle, olines, mono_title=otitle.startswith(("prototypes", "docs")))
        f.ar([(364, y + 20), (394, y + 20)])
        if title != "Write a spec":
            f.ar([(190, y + h), (190, y + h + 22)])
        y += max(h, oh) + 22
    py, dy = at["Pull a design"] + 40, at["Design in Claude Design"] + 40
    f.ar([(16, py), (9, py), (9, dy), (14, dy)])
    _t(f, 200, at["Pull a design"] - 6, "有设计问题：回去改，再拉", "lbl")
    return f.svg(y + 4, ARIA_PATH)


ARIA_PATH = ("设计这一侧的路，左边是这个会话跑的，要有 Claude Design 工具；右边是留下的东西和谁定它。"
             "prototype 技能的 UI 分支做几种截然不同的界面让你挑，赢的那种在 prototypes/<effort>/<issue>/UI/ 的 leaf README 里写 ## State list，一个区域一个标题、每个状态一行。"
             "可选的 Build a design system 让 Claude Design 里的 agent 建产品的变量、零件、字体和图标，留下 Claude Design 里的设计系统项目，每个零件一张卡，readme.md 末尾的 Unifications 表写代码里不一致的值统一成哪一个，由你定。"
             "Design in Claude Design 建项目、写约定和 task.md、处理你发来的评论，直到你签字；留下 Claude Design 里的页面项目，含 CLAUDE.md、state-list.md、ui-ids.md、task.md，页面怎么长由你和那边的 agent 定。"
             "Pull a design 把签了字的项目原样拉进仓库，读报告，按改了什么交给下一步；留下 prototypes/<effort>/claude-design/ 的设计包和 pull-report.md，提交进 git，git 是设计唯一的版本历史。"
             "报告里有设计问题，就回 Design in Claude Design 改，再拉一次。"
             "Write the screen contract 把每个控件绑到它背后的后端决定，定不了的列成清单由你定；留下 docs/specs/<effort>/screen-contract.yaml，每个用户看得见的行为一行：调用什么、显示哪个字段、成功去哪、失败去哪、出处。"
             "Write a spec 读两份基线，设计包管长相和原文，screen contract 管调用和流转；spec 的 API contract 和 cross-component composition 两节从 screen contract 的行推出来，每条注明行号。")


def split():
    f = Fig("m122", 1000)
    _t(f, 10, 20, "v2 的设计这一侧去哪：做法进 playbook，两个技能只留它们管的东西", "h")
    rows = [
        ("design-pages 的 SKILL.md（401）", ["谁能做、状态清单"],
         [("skill", "design-pages 的 SKILL.md")]),
        ("edit-pages.md（624）、draw.md（161）", ["建项目、和那边的 agent 说话、签字；", "处理评论、自己画"],
         [("playbook", "Design in Claude Design"), ("skill", "design-pages：两段两份 playbook 都读的")]),
        ("pull.md（942）", ["拉、报告、拆脚手架、交给谁、", "回答 contract 子票"],
         [("playbook", "Pull a design"), ("skill", "design-pages：设计包和报告的表")]),
        ("design-system.md（904）", ["什么时候建、谁建、怎么查；", "已有产品搬进 Claude Design"],
         [("playbook", "Build a design system"), ("skill", "design-pages：设计系统是什么")]),
        ("两份 CLAUDE.md 模板、pull_design.py 等两个脚本", ["写进 Claude Design 项目的约定；拉取"],
         [("reference", "design-pages/references/、scripts/，原样")]),
        ("write-screen-contract 的 SKILL.md（1,839）", ["它是什么、规则；输入、七步、", "重跑、交给谁"],
         [("skill", "write-screen-contract：是什么、规则、脚本"), ("playbook", "Write the screen contract：八步")]),
        ("screen-contract-format.md（1,891）和三个脚本", ["文件的格式；骨架、lint、OpenAPI"],
         [("reference", "原处，读它的人换成 v3 的名字")]),
        ("wayfinder 的 interface-and-remake.md（572）", ["有界面、重做产品时多开的票"],
         [("reference", "mmw-mode/references/interface-and-remake.md")]),
        ("prototype 的 UI.md（1,372）和 UI 句子", ["第 10 课拿掉的那一支"],
         [("skill", "prototype：原样回来，去掉 ## Next")]),
        ("ui-acceptance 的 design_render.py", ["离线渲染设计页，拉取和骨架都用"],
         [("script", "ui-acceptance/scripts/，原处")]),
    ]
    y = 40
    for title, lines, outs in rows:
        h = _box(f, "other", 16, y, 440, title, lines)
        oy = y
        for kind, label in outs:
            f.chip(kind, 500, oy, label, mono=False)
            f.ar([(456, y + 14), (498, oy + 12)])
            oy += 30
        y += max(h, oy - y) + 12
    return f.svg(y + 4, ARIA_SPLIT)


ARIA_SPLIT = ("v2 设计这一侧的文字在 v3 去哪。design-pages 的 SKILL.md（401 词）里谁能做、状态清单两段留在 v3 的 design-pages SKILL.md。"
              "edit-pages.md（624 词）和 draw.md（161 词）讲建项目、和 Claude Design 里的 agent 说话、签字、处理评论、自己画，成为 playbook Design in Claude Design；其中两份 playbook 都读的两段留在 design-pages 技能。"
              "pull.md（942 词）讲拉取、报告、拆脚手架、交给谁、回答 contract 子票，成为 Pull a design；设计包和报告各节的表留在技能。"
              "design-system.md（904 词）讲什么时候建、谁建、怎么查、已有产品搬进 Claude Design，成为 Build a design system；设计系统是什么留在技能。"
              "两份 CLAUDE.md 模板和 pull_design.py、check_editable_selectors.py 原样搬进 design-pages 的 references/ 和 scripts/。"
              "write-screen-contract 的 SKILL.md（1,839 词）里它是什么和规则留在技能，加上脚本表；输入、七步、重跑、交给谁成为 playbook Write the screen contract 的八步。"
              "screen-contract-format.md（1,891 词）和三个脚本留在原处，读它的人换成 v3 的名字。"
              "wayfinder 的 interface-and-remake.md（572 词）移到 mmw-mode/references/。prototype 的 UI.md（1,372 词）和 UI 句子原样回来，去掉 ## Next。"
              "ui-acceptance 的 design_render.py 离线渲染设计页，拉取和骨架都用它，搬进 v3 ui-acceptance/scripts/。")


def tickets():
    f = Fig("m123", 1000)
    _t(f, 10, 20, "有界面的地图多两张票：设计票等决定，对齐票最后关", "h")
    H = 330
    f.zone(4, 34, 992, H - 34, "地图的子 issue")
    a = _box(f, "other", 16, 70, 280, "决定票", ["grilling、research、task：", "后端做什么"])
    b = _box(f, "other", 16, 190, 280, "原型票（prototype）", ["其中 UI 原型的赢家", "写进 State list"])
    d = _box(f, "playbook", 360, 190, 290, "设计票 · prototype", ["开头一行：Design in Claude Design，", "只有带 Claude Design 工具的会话做；", "签字、拉取后关"])
    al = _box(f, "playbook", 700, 70, 284, "对齐票 · grilling", ["开头一行：Write the screen", "contract；它写 screen contract，", "最后一张关"])
    f.ar([(296, 190 + b / 2), (358, 190 + d / 2)])
    f.ar([(296, 70 + a / 2 + 10), (330, 70 + a / 2 + 10), (330, 214), (358, 214)])
    _t(f, 338, 166, "会改页面状态的", "lbl")
    f.ar([(296, 70 + a / 2 - 6), (698, 70 + a / 2 - 6)])
    f.ar([(650, 190 + d / 2), (690, 190 + d / 2), (690, 140), (698, 140)])
    _t(f, 360, 300, "地图 ## Notes 的规矩：后来加的决定票也挡对齐票；会改页面状态的也挡设计票。", "s", room=620)
    _t(f, 360, 318, "Resolve a map ticket 第 3 步：票开头一行点名 playbook，就跑那份 playbook，不看类型。", "s", room=620)
    return f.svg(H + 8, ARIA_TICKETS)


ARIA_TICKETS = ("有界面的地图多两张票。决定票（grilling、research、task）定后端做什么，原型票（prototype）里，UI 原型在几种界面里挑一种，赢家写进 State list。"
                "设计票是 prototype 类型，开头一行点名 Design in Claude Design，只有带 Claude Design 工具的会话做，签字和拉取之后关；它被每张原型票和每张会改页面状态的决定票挡住。"
                "对齐票是 grilling 类型，开头一行点名 Write the screen contract，写出 screen contract，是最后关的一张；它被每张决定票和设计票挡住。"
                "地图 ## Notes 写一条规矩：后来加的决定票也挡对齐票，会改页面状态的也挡设计票。"
                "Resolve a map ticket 第 3 步：票开头一行点名 playbook，就跑那份 playbook，不看类型。")


FIGS = {"l12-path": path, "l12-split": split, "l12-tickets": tickets}

"""Figures of lesson 0010: what a map is on the tracker; Chart a map; Resolve a map ticket; how a research
ticket is answered."""
from kit import Fig, flow, txt as _t, tbox as _box


def anatomy():
    f = Fig("m101", 1000)
    _t(f, 10, 20, "一张地图在 tracker 上是什么：一个 issue 当索引，它的子 issue 是决定票", "h")
    H = 462
    f.zone(4, 34, 360, H - 34, "地图 issue：wayfinder:map、mmw:map")
    f.zone(372, 34, 624, H - 34, "它的子 issue")

    secs = [
        ("## Destination", ["走到头是什么样：一份 spec、一个决定或一处改动"]),
        ("## Notes", ["每个会话要读的技能、偏好、effort 目录名"]),
        ("## Decisions so far", ["每张关了的票一行：名字带链接，一句要点"]),
        ("## Not yet specified", ["雾：知道要来、还问不准的问题"]),
        ("## Out of scope", ["划出去的：关掉，一行理由，不再回来"]),
        ("## Specs", ["分成几份 spec 时，Write a spec 写在这里"]),
    ]
    y = 56
    pos = {}
    for title, lines in secs:
        h = _box(f, "other", 16, y, 336, title, lines, mono_title=True)
        pos[title] = (y, h)
        y += h + 10

    rows = [
        ("决定票 · 已关", ["答案在它的 resolution comment 里，", "地图上只留一行指针"], False),
        ("决定票 · 前沿", ["开着、没被挡住、没人认领；下一个", "会话取第一张（四种：research、", "prototype、grilling、task）"], False),
        ("决定票 · 已认领", ["有 assignee，别的会话跳过它"], False),
        ("决定票 · 被挡住", ["还有开着的 blocker；blocker 都关了", "才进前沿"], True),
        ("spec · mmw:spec", ["地图清了以后 Write a spec 用 --map", "发布；不算决定票"], False),
    ]
    ry = 56
    rpos = []
    for title, lines, dashed in rows:
        kind = "playbook" if title.startswith("spec") else "other"
        h = _box(f, kind if kind == "other" else "other", 420, ry, 560, title, lines, dashed=dashed)
        rpos.append((ry, h))
        ry += h + 12

    dy, dh = pos["## Decisions so far"]
    f.ar([(352, dy + dh / 2), (418, rpos[0][0] + rpos[0][1] / 2)], "指针", 372, dy + dh / 2 - 6)
    ny, nh = pos["## Not yet specified"]
    f.ar([(352, ny + nh / 2), (360, ny + nh / 2), (360, rpos[1][0] + 24), (418, rpos[1][0] + 24)])
    _t(f, 368, ny + nh / 2 - 22, "问得准了", "lbl")
    _t(f, 368, ny + nh / 2 - 8, "就成新票", "lbl")
    sy, sh = pos["## Specs"]
    f.ar([(352, sy + sh / 2), (418, rpos[4][0] + rpos[4][1] / 2)], "链接", 372, sy + sh / 2 - 6)
    _t(f, 420, ry + 10, "地图清了：没有一张决定票还开着，Not yet specified 是空的。spec 是子 issue，但不算。", "s", room=560)
    return f.svg(H + 8, ARIA_ANATOMY)


ARIA_ANATOMY = ("一张地图在 tracker 上是什么。左边是地图 issue，带 wayfinder:map 和 mmw:map 两个标签，正文六节："
                "## Destination 写走到头是什么样，一份 spec、一个决定或一处改动；## Notes 写每个会话要读的技能、偏好和 effort 目录名；"
                "## Decisions so far 每张关了的票一行，名字带链接和一句要点；## Not yet specified 是雾，知道要来、还问不准的问题；"
                "## Out of scope 是划出去的，关掉、一行理由、不再回来；## Specs 是分成几份 spec 时 Write a spec 写的。"
                "右边是它的子 issue：已关的决定票，答案在 resolution comment 里，地图上只留一行指针；前沿上的决定票，开着、没被挡住、没人认领，下一个会话取第一张，"
                "决定票有 research、prototype、grilling、task 四种；已认领的有 assignee，别的会话跳过；被挡住的还有开着的 blocker；"
                "最后是 mmw:spec 的 spec，地图清了以后由 Write a spec 用 --map 发布，不算决定票。"
                "Decisions so far 指向已关的票，Not yet specified 里的问题问得准了就成新票，## Specs 链到 spec。"
                "地图清了，是指没有一张决定票还开着，Not yet specified 是空的；spec 是子 issue，但不算。")


def chart():
    steps = [
        ("1 定终点", ["读 grilling 和 domain-modeling，和你", "一起定：走到头是什么样"],
         [("skill", "grilling、domain-modeling")], ("问你", ["终点那一两行"]), 0),
        ("2 铺开前沿", ["横着问遍整片，找出还没定的决定和", "现在能走的第一步；没有雾就不要地图"],
         [("skill", "grilling")], ("没有雾", ["告诉你，路清了走", "Write a spec，问你怎么走"]), 0),
        ("3 建地图", ["照地图正文的格式写；发成一个 issue，", "带两个标签；缺标签就是仓库没接入，停下"],
         [("skill", "wayfinder 的 ### The map body"), ("other", "gh issue create")], None, 0),
        ("4 建现在问得准的票", ["每张一个子 issue、一个类型标签；", "第二遍再连先后；问不准的留在雾里"],
         [("skill", "wayfinder 的 ### Tickets"), ("other", "issue-tracker.md 的 Wayfinding operations")], None, 0),
        ("5 回答研究票", ["每张一份 brief，一次开齐 researcher；", "叫醒后逐张存笔记、推、评论、关票、", "把指针加进地图"],
         [("script", "dispatch.sh brief researcher"), ("reference", "mmw-mode 的 map-research-brief.md"),
          ("skill", "dispatch 的 ## On waking")], ("交回", ["地图、前沿上的票、", "雾、研究的答案"]), 0),
    ]
    f, rows, bottom = flow("m102", "Chart a map：一个会话把一大块还看不清路的工作画成地图，研究票当场答掉", steps,
                           "Chart a map 的步骤", "问你或交回")
    return f.svg(bottom + 8, ARIA_CHART)


ARIA_CHART = ("Chart a map 的五步，左列步骤，中列用到的组件，右列问你或交回的地方。"
              "1 定终点：读 grilling 和 domain-modeling 两份技能，和你一起定走到头是什么样，终点那一两行问你。"
              "2 铺开前沿：再用 grilling，横着问遍整片，找出还没定的决定和现在能走的第一步；没有雾就不要地图，告诉你路清了走 Write a spec，问你怎么走。"
              "3 建地图：照 wayfinder 技能 ### The map body 的格式写正文；用 gh issue create 发成一个 issue，带 wayfinder:map 和 mmw:map；仓库缺这些标签就是没接入，说明并停下，标签由 setup-mmw 一次建好。"
              "4 建现在问得准的票：照 wayfinder 的 ### Tickets，每张一个子 issue、一个 wayfinder 类型标签；第二遍再按 issue-tracker.md 的 Wayfinding operations 连先后；问不准的留在雾里。"
              "5 回答研究票：每张研究票照 mmw-mode 的 map-research-brief.md 写一份 brief，用 dispatch.sh brief researcher 一次开齐；被叫醒后照 dispatch 的 ## On waking，逐张存笔记、提交推到 base、评论答案、关票、把指针加进地图。"
              "交回：地图、前沿上的票、雾、研究的答案。")


def resolve():
    steps = [
        ("1 读地图", ["只读地图正文，不读每张票；读 Notes", "点名的技能"], [("skill", "Notes 点名的技能")], None, 0),
        ("2 选票，先认领", ["你点名的那张，否则前沿的第一张；", "认领是第一件写的事"],
         [("other", "Wayfinding operations 的前沿查询"), ("other", "gh issue edit --add-assignee @me")], None, 0),
        ("3 按类型解决", ["追问问你；原型照 prototype 做给你看；", "任务自己做或给你清单；研究开一个", "researcher；人的那一半只由你答"],
         [("skill", "grilling、domain-modeling"), ("skill", "prototype"), ("script", "dispatch.sh brief researcher")],
         ("问你", ["追问、原型要你的反应，", "任务里只有你能做的"]), 0),
        ("4 记下结果", ["答案贴成评论，关票，地图上加一行", "指针；先重读地图再改"], [("other", "gh issue comment、close")], None, 0),
        ("5 推前沿", ["问得准了的建新票再连先后；清掉毕业的雾；", "超出终点的划出范围；被推翻的票改或关"],
         [("skill", "wayfinder 的 ## Out of scope")], None, 0),
        ("6 地图清了吗", ["没有决定票开着、雾是空的：下一步是", "新会话 Write a spec；地图不关"],
         [("skill", "wayfinder 的 ## A clear map")], ("交回", ["这张的答案、开关了哪些票、", "前沿；清了就说下一步"]), 0),
    ]
    f, rows, bottom = flow("m103", "Resolve a map ticket：一个会话只解决一张决定票，结果记在地图上", steps,
                           "Resolve a map ticket 的步骤", "问你或交回")
    return f.svg(bottom + 8, ARIA_RESOLVE)


ARIA_RESOLVE = ("Resolve a map ticket 的六步，左列步骤，中列用到的组件，右列问你或交回的地方。"
                "1 读地图：只读地图正文，不读每张票，读 Notes 点名的技能。"
                "2 选票，先认领：你点名的那张，否则照 Wayfinding operations 的前沿查询取第一张；用 gh issue edit --add-assignee @me 认领，这是第一件写的事。"
                "3 按类型解决：追问票读 grilling 和 domain-modeling 问你；原型票照 prototype 技能做给你看；任务票自己做或给你清单；研究票用 dispatch.sh brief researcher 开一个研究员会话；人的那一半只由你答。"
                "4 记下结果：答案贴成评论，关票，地图的 Decisions so far 加一行指针；改地图前先重读。"
                "5 推前沿：问得准了的建新票再连先后，清掉毕业的雾，超出终点的照 wayfinder 的 ## Out of scope 划出去，被推翻的票改或关。"
                "6 地图清了吗：照 wayfinder 的 ## A clear map，没有决定票开着、雾是空的，下一步是新会话 Write a spec，地图不关。"
                "交回：这张的答案、开关了哪些票、前沿，清了就说下一步。")


def research():
    f = Fig("m104", 1000)
    _t(f, 10, 20, "一张研究票怎样答掉：研究员只交一个文件，写 tracker 和仓库的只有画图会话", "h")
    lanes = [(4, "画图的会话（Chart a map 第 5 步）"), (338, "dispatch 和中继"), (672, "researcher 会话，一张票一个")]
    H = 470
    for x, title in lanes:
        f.zone(x, 34, 324, H - 34, title)
    b1 = _box(f, "playbook", 16, 66, 300, "写 brief，开齐，结束回合", ["每张研究票一份：问题、终点、笔记路径；", "dispatch.sh brief researcher a.md b.md"])
    b2 = _box(f, "script", 350, 66, 300, "每份 brief 开一个会话", ["在同一个检出目录；开头一句", "Use the research skill."])
    b3 = _box(f, "agent", 684, 150, 300, "只查这一个问题", ["一手来源；答案写成一个 Markdown 文件，", "开头 ## Answer 不超过三句"])
    b4 = _box(f, "agent", 684, 250, 300, "dispatch.sh report", ["文件被拷出；不改仓库，", "不写 tracker"])
    b5 = _box(f, "script", 350, 250, 300, "全部交了，叫醒一次", ["brief <batch> done"])
    b6 = _box(f, "playbook", 16, 330, 300, "逐张收尾，再 brief close", ["存到笔记路径，提交、推到 base；", "评论 ## Answer 和路径，关票；", "指针加进地图，每次先重读"])
    f.ar([(316, 66 + b1 / 2), (348, 66 + b2 / 2)])
    f.ar([(650, 66 + b2 / 2), (834, 66 + b2 / 2), (834, 148)])
    f.ar([(834, 150 + b3), (834, 248)])
    f.ar([(684, 250 + b4 / 2), (652, 250 + b5 / 2)])
    f.ar([(500, 250 + b5), (500, 360), (318, 360)])
    return f.svg(H + 8, ARIA_RESEARCH)


ARIA_RESEARCH = ("一张研究票怎样答掉，三条泳道。画图的会话，即 Chart a map 第 5 步：给每张研究票写一份 brief，写明问题、终点和笔记路径，"
                 "用 dispatch.sh brief researcher 一次开齐，然后结束回合。dispatch 为每份 brief 开一个 researcher 会话，在同一个检出目录，开头一句 Use the research skill。"
                 "researcher 只查这一个问题，查一手来源，答案写成一个 Markdown 文件，开头 ## Answer 不超过三句；用 dispatch.sh report 交回，文件被拷出；它不改仓库，不写 tracker。"
                 "全部交了，中继叫醒画图的会话一次：brief <batch> done。画图的会话逐张收尾：存到笔记路径，提交、推到 base 分支；把 ## Answer 和路径贴成评论，关票；"
                 "把指针加进地图的 Decisions so far，每次先重读地图；最后 brief close。")


FIGS = {"l10-anatomy": anatomy, "l10-chart": chart, "l10-resolve": resolve, "l10-research": research}

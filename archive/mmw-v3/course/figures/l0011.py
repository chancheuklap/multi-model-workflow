"""Figures of lesson 0011: what setup-mmw covers; its eleven steps; one creator for each thing."""
from kit import Fig, flow, txt as _t, tbox as _box, tw


def _row(f, y, item, action, kind):
    _t(f, 28, y + 16.5, item, room=360)
    f.chip(kind, 400, y, action, mono=False)


def layers():
    f = Fig("m111", 1000)
    _t(f, 10, 20, "setup-mmw 管什么：仓库这一层建好写好，机器这一层只查，其余不归它", "h")
    groups = [
        ("仓库这一层：setup-mmw 建或写，check.py 查", [
            ("GitHub 的 Issues、sub-issues、issue 依赖", "只查；缺了你在 GitHub 的设置里开", "other"),
            ("保护分支和生效的 ruleset", "只查；有就告诉你，夜里的推送可能被拒", "other"),
            ("docs/agents/ 的三份说明", "从种子写；已有的只补缺的、只改错的", "reference"),
            ("AGENTS.md 指向它们的三行，CLAUDE.md 的 @AGENTS.md", "写", "reference"),
            ("流水线的全部标签（16 个）", "labels.py 建，只有这里建", "script"),
            ("这个仓库的 Memory Space", "space.py 建，只有这里建", "script"),
            (".gitignore 的 .worktrees/、.scratch/、story-shots/", "写", "reference"),
            (".mmw/target.json 的 checks", "记下仓库已有、在基线上能过的检查命令", "reference"),
            ("CODING_STANDARDS.md 和它的 ## Tests", "照代码现在的写法写", "reference"),
        ]),
        ("机器这一层：只查，由安装入口装", [
            ("gh 已登录；git、python3、uv、node、nmem", "只查", "other"),
            ("至少一个 runner：paseo、herdr、orca", "只查", "other"),
            ("~/.mmw/models.json，mmw-toolbox Space", "只查", "other"),
        ]),
        ("不归 setup-mmw", [
            ("产品层：target.json 的产品命令、harness、stories、journeys", "contract 票建；开夜时查", "other"),
            ("项目分支：一夜一个，dispatch.sh open 自己推断", "Run a night", "playbook"),
            ("每个功能自己的：原型、spec、票", "各自的 playbook", "playbook"),
        ]),
    ]
    y = 34
    for title, rows in groups:
        h = 34 + len(rows) * 32 + 6
        f.zone(4, y, 992, h, title)
        for i, (item, action, kind) in enumerate(rows):
            _row(f, y + 34 + i * 32, item, action, kind)
        y += h + 10
    return f.svg(y, ARIA_LAYERS)


ARIA_LAYERS = ("setup-mmw 管什么。仓库这一层由 setup-mmw 建或写，check.py 查：GitHub 的 Issues、sub-issues 和 issue 依赖只查，缺了你在 GitHub 设置里开；"
               "保护分支和生效的 ruleset 只查，有就告诉你，夜里的推送可能被拒；docs/agents/ 的三份说明从种子写，已有的只补缺的、只改错的；"
               "AGENTS.md 指向它们的三行和 CLAUDE.md 的 @AGENTS.md 由它写；流水线的全部 16 个标签由 labels.py 建，只有这里建；"
               "这个仓库的 Memory Space 由 space.py 建，只有这里建；.gitignore 加 .worktrees/、.scratch/ 和 story-shots/；.mmw/target.json 的 checks 记下仓库已有、在基线上能过的检查命令；"
               "CODING_STANDARDS.md 和它的 ## Tests 照代码现在的写法写。机器这一层只查，由安装入口装：gh 登录，git、python3、uv、node、nmem，"
               "至少一个 runner（paseo、herdr、orca），~/.mmw/models.json 和 mmw-toolbox Space。不归 setup-mmw 的：产品层，即 target.json 的产品命令、harness、stories、journeys，由一批票里的 contract 票建，开夜时 Run a night 第 2 步用 target_config.py --check 查；"
               "项目分支一夜一个，由 dispatch.sh open 推断，归 Run a night；每个功能自己的原型、spec、票，归各自的 playbook。")


def steps():
    st = [
        ("1 先查一遍", ["跑 check.py：每项一行，ok、missing、", "note 或 unchecked，最后一行总结"],
         [("script", "scripts/check.py")], None, 0),
        ("2 不是 GitHub 就停", ["Issues、sub-issues、依赖缺一样，", "告诉你去哪里开，什么都不配"],
         [("other", "tracker、sub-issues and dependencies")], ("停下", ["告诉你在 GitHub 哪里开"]), 0),
        ("3 写 docs/agents/", ["三份从种子写；已有的是仓库自己的", "记录，只补缺的、只改错的"],
         [("reference", "issue-tracker.md、triage-labels.md"), ("reference", "domain.md")], None, 0),
        ("4 AGENTS.md、CLAUDE.md", ["External References 每份一行；", "CLAUDE.md 加一行 @AGENTS.md"],
         [("other", "## External References")], None, 0),
        ("5 建标签", ["缺的全建，已有的不动"], [("script", "scripts/labels.py")], None, 0),
        ("6 建 Memory Space", ["没有就建，形状不对就修，再读回来"], [("script", "scripts/space.py")], None, 0),
        ("7 .gitignore", ["加 .worktrees/ 和 .scratch/"], [("other", "git check-ignore")], None, 0),
        ("8 记下检查命令", ["找仓库已有的 lint、类型、测试命令，", "在基线上跑一遍，过的写进 checks"],
         [("other", ".mmw/target.json 的 checks")], ("告诉你", ["哪条在基线上就失败，", "或仓库根本没有检查"]), 0),
        ("9 CODING_STANDARDS.md", ["缺了就照代码现在的写法写，", "每条带一个例子文件"],
         [("other", "worker 先读，审查两条轴拿它判")], None, 0),
        ("10 提交并推送", ["一次提交，推到 origin：夜里的", "工作区从 origin 切"], [("other", "git commit、git push")], None, 0),
        ("11 再查一遍", ["再跑 check.py"], [("script", "scripts/check.py")],
         ("交回", ["两张表的差别、写了建了什么、", "还缺什么和谁来补、提交"]), 0),
    ]
    f, rows, bottom = flow("m112", "setup-mmw 的十一步：先查，配能配的，再查；不是 GitHub 就什么都不配", st,
                           "setup-mmw 的步骤", "停下、告诉你或交回")
    return f.svg(bottom + 8, ARIA_STEPS)


ARIA_STEPS = ("setup-mmw 的十一步，左列步骤，中列用到的，右列停下、告诉你或交回。1 先查一遍：跑 scripts/check.py，每项一行，ok、missing、note 或 unchecked，最后一行总结。"
              "2 不是 GitHub 就停：tracker 或 sub-issues and dependencies 两行缺一样，告诉你在 GitHub 哪里开，什么都不配。"
              "3 写 docs/agents/：issue-tracker.md、triage-labels.md、domain.md 从种子写；已有的是仓库自己的记录，只补缺的、只改错的。"
              "4 AGENTS.md 的 ## External References 每份一行，CLAUDE.md 加一行 @AGENTS.md。5 建标签：scripts/labels.py 缺的全建，已有的不动。"
              "6 建 Memory Space：scripts/space.py 没有就建，形状不对就修，再读回来。7 .gitignore 加 .worktrees/ 和 .scratch/，用 git check-ignore 确认。"
              "8 记下检查命令：找仓库已有的 lint、类型、测试命令，在基线上跑一遍，过的写进 .mmw/target.json 的 checks；哪条在基线上就失败，或仓库根本没有检查，告诉你。"
              "9 CODING_STANDARDS.md 缺了就照代码现在的写法写，每条带一个例子文件；worker 先读它，审查的两条轴拿它判。"
              "10 提交并推送：一次提交推到 origin，因为夜里的工作区从 origin 切。11 再查一遍，交回两张表的差别、写了建了什么、还缺什么和谁来补、提交。")


def creators():
    f = Fig("m113", 1000)
    _t(f, 10, 20, "一样东西只有一处建：setup-mmw 的脚本建，用到它的地方只查，缺了就拒绝并点名 setup-mmw", "h")
    f.zone(4, 34, 300, 262, "建的地方：setup-mmw")
    f.zone(312, 34, 684, 262, "只查的地方")
    lab = _box(f, "script", 16, 66, 276, "scripts/labels.py", ["照 verify-ticket.py 的表建", "缺的标签；已有的不动"], mono_title=True)
    spc = _box(f, "script", 16, 216, 276, "scripts/space.py", ["没有就建，形状不对就修；", "--check 只读"], mono_title=True)
    checks_l = [
        ("verify-ticket.py 的 missing_labels", "发 spec、发一批票、开子票之前；一批票先查齐"),
        ("dispatch.sh 的 require_label", "route … became-ticket 之前"),
        ("wayfinder 技能", "tracker 拒绝 wayfinder:* 或 mmw:map 时停下"),
    ]
    checks_s = [
        ("dispatch.sh 的 ensure_repository_memory", "open 和 start 之前跑 space.py --check"),
    ]
    y = 66
    for title, line in checks_l:
        _box(f, "script" if ".py" in title or ".sh" in title else "skill", 324, y, 660, title, [line])
        f.ar([(292, 66 + lab / 2), (322, y + 23)])
        y += 52
    y = 230
    for title, line in checks_s:
        _box(f, "script", 324, y, 660, title, [line])
        f.ar([(292, 216 + spc / 2), (322, y + 23)])
        y += 52
    return f.svg(304, ARIA_CREATORS)


ARIA_CREATORS = ("一样东西只有一处建。建的地方是 setup-mmw：scripts/labels.py 照 verify-ticket.py 的表建缺的标签，已有的不动；"
                 "scripts/space.py 没有 Space 就建，形状不对就修，带 --check 时只读。只查的地方，缺了就拒绝并点名 setup-mmw："
                 "verify-ticket.py 的 missing_labels 在发 spec、发一批票、开子票之前查，一批票先查齐；dispatch.sh 的 require_label 在 route … became-ticket 之前查；"
                 "wayfinder 技能在 tracker 拒绝 wayfinder:* 或 mmw:map 时停下；dispatch.sh 的 ensure_repository_memory 在 open 和 start 之前跑 space.py --check。")


FIGS = {"l11-layers": layers, "l11-steps": steps, "l11-creators": creators}

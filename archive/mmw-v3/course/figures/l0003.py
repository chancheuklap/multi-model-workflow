"""Figures of lesson 0003: one feature's way through MMW v2, v2's parts grouped by the problem each solves, and where v2 and pstack keep the order of a task."""
from kit import Fig, tw


def lifecycle():
    f = Fig("m4", 1000)
    # daytime
    f.zone(10, 10, 980, 206, "白天 · 你在场：把想法变成夜里能无人执行的票")
    _, r = f.pill(0, 42, "你有一个想法", left=26)
    f.ar([(r, 59), (186, 59)])
    f.box("skill", 186, 38, 236, 42, "grilling：访谈，把决定问清", [])
    f.ar([(304, 80), (304, 100)])
    f.box("skill", 186, 100, 236, 42, "to-spec：写 spec，发到 GitHub", [])
    f.ar([(304, 142), (304, 162)])
    f.box("skill", 186, 162, 236, 42, "to-tickets：切成票", ["每条判据带 CHECK 命令和 EXPECT"])
    f.ar([(422, 183), (462, 183)])
    f.box("script", 462, 162, 240, 42, "verify-ticket.py --lint", ["发布前检查整批票"])
    f.box("skill", 450, 38, 262, 42, "wayfinder：一次会话装不下时", ["代替访谈：一张决策票一张票地解决"])
    f.ar([(560, 80), (560, 112), (424, 112)])
    f.box("skill", 740, 38, 236, 42, "design-pages：有界面时", ["把 Claude Design 定稿的设计拉进仓库"])
    f.ar([(858, 80), (858, 100)])
    f.box("skill", 740, 100, 236, 42, "write-screen-contract", ["写 screen-contract.yaml"])
    f.ar([(858, 142), (858, 152), (724, 152), (724, 130), (424, 130)])
    # night
    f.zone(10, 228, 980, 422, "夜里 · 你不在：一批票由 agent 做完、合并")
    f.note(26, 267, "orchestrator：开夜的那个会话，照 dispatch 的 references/night.md 做")
    f.note(560, 267, "每张票：一个 worker、一个 reviewer，同一个工作树")
    f.box("script", 26, 276, 330, 42, "dispatch.sh check / open", ["开夜：检查本机、推送分支、登记给 relay"])
    f.ar([(190, 318), (190, 338)])
    f.box("script", 26, 338, 330, 42, "dispatch.sh advance", ["开出所有能做的票，每张起一个 worker"])
    f.ar([(356, 359), (558, 359)], "start", 440, 351)
    f.box("skill", 560, 338, 414, 42, "implement：认领、读票、写代码", ["测试照 tdd 技能写，写在票的 ## Seam 上"])
    f.ar([(767, 380), (767, 398)])
    f.box("script", 560, 398, 414, 42, "合进最新 base，verify-ticket.py 跑全部判据", ["CHECK 退出码为 0 且输出对上 EXPECT 才算过"])
    f.ar([(767, 440), (767, 458)])
    f.box("skill", 560, 458, 414, 42, "code-review：另起一个 reviewer 会话审", ["四个轴：Standards、Spec、Tests、UI"])
    f.ar([(767, 500), (767, 518)])
    f.box("script", 560, 518, 414, 42, "修 finding，对最终提交再跑一次全部判据", ["--closeout 通过，票上写下事件 ticket.passed"])
    f.box("skill", 400, 476, 136, 42, "advisor", ["卡住时的第二意见"])
    f.att([(468, 476), (468, 370), (558, 370)])
    f.box("script", 380, 586, 330, 46, "relay：读票上的事件，叫醒等它的会话", ["watchdog、turn-guard 看会话是否还活着"])
    f.ar([(767, 560), (767, 608), (712, 608)], "ticket.passed", 722, 600)
    f.ar([(380, 609), (368, 609), (368, 421), (358, 421)])
    f.lbl(362, 602, "叫醒 orchestrator", "end")
    f.box("script", 26, 400, 330, 42, "被叫醒后再 advance", ["合并、跑仓库检查、推送；开出下一批"])
    f.ar([(190, 442), (190, 460)])
    f.box("script", 26, 460, 330, 42, "closing pass，然后 reverify", ["给每条 finding 定去向；在合并后的 base 上重跑判据"])
    f.ar([(190, 502), (190, 520)])
    f.box("script", 26, 520, 330, 42, "summary，然后 retro", ["写 NIGHT SUMMARY；复盘写 NIGHT RETRO"])
    # morning
    f.zone(10, 662, 980, 74, "早上 · 你在场")
    _, r = f.pill(0, 684, "读 NIGHT SUMMARY 与 NIGHT RETRO", left=26)
    l2, r2 = f.pill(0, 684, "你验收", left=r + 32)
    f.ar([(r, 701), (l2 - 2, 701)])
    f.ar([(r2, 701), (r2 + 30, 701)])
    f.box("script", r2 + 30, 680, 360, 42, "dispatch.sh finish", ["把 base branch 合回 project branch，清理"])
    return f.svg(746, "一个需求在 MMW v2 里的路径：白天在你面前访谈、写 spec、切票；夜里 orchestrator 开出票，每张票由 worker 实现、跑判据、另一个会话审、再跑判据后写下 ticket.passed，relay 读到事件叫醒 orchestrator 合并并开下一批，最后给 finding 定去向、重跑判据、写总结和复盘；早上你读总结、验收，finish 合回。")


GROUPS = [
    ("1 白天：把想法变成夜里能无人执行的票", "skill", [
        ("skill", "grilling ✎"), ("skill", "grill-me ✎"), ("skill", "grill-with-docs ✎"), ("skill", "wayfinder ✎"),
        ("skill", "to-spec ✎"), ("skill", "to-tickets ✎"), ("skill", "triage ✎"), ("skill", "prototype ✎"),
        ("skill", "to-questionnaire ✎"), ("skill", "research"), ("script", "verify-ticket.py --lint")]),
    ("2 界面：定稿的设计原样落进产品", "skill", [
        ("skill", "design-pages"), ("skill", "write-screen-contract"), ("skill", "ui-acceptance")]),
    ("3 一张票：你不读代码，也能信它关得对", "skill", [
        ("skill", "implement ✎"), ("skill", "tdd ✎"), ("skill", "diagnosing-bugs"), ("skill", "code-review ✎"),
        ("skill", "verify-ticket"), ("skill", "advisor"), ("script", "gate-check ✎"),
        ("other", "Nowledge Mem")]),
    ("4 编排：没人看着，不停也不乱", "script", [
        ("skill", "dispatch"), ("script", "dispatch.sh"), ("script", "relay.py"), ("script", "watchdog.py"),
        ("script", "turn-guard.py"), ("script", "tool-guard.py"), ("script", "status.py"),
        ("script", "runners/orca.sh"), ("script", "runners/paseo.sh"), ("script", "runners/herdr.sh"), ("config", "~/.mmw/models.json")]),
    ("5 合并：并行的票合在一起不坏", "script", [
        ("script", "dispatch.sh land"), ("script", "dispatch.sh reverify"), ("script", "dispatch.sh route"),
        ("skill", "resolving-merge-conflicts ✎")]),
    ("6 早上：几分钟看懂这一夜，再收尾", "other", [
        ("script", "dispatch.sh summary"), ("skill", "retro"), ("other", "mmw-v2/board/"),
        ("script", "dispatch.sh finish")]),
    ("7 工具箱本身：一套技能在五个宿主上都能用", "config", [
        ("config", "install.sh"), ("config", "skills.txt"), ("config", "prompt/shared.md"), ("config", "prompt/render.py"),
        ("other", "merge-notes/"), ("other", "docs/adr/"), ("other", "docs/contexts/")]),
    ("8 不属于流水线的单件事", "skill", [
        ("skill", "setup-matt-pocock-skills ✎"), ("skill", "manage-agents-md"), ("skill", "code-checkers"),
        ("skill", "exe-release"), ("skill", "writing-for-agents ✎"), ("skill", "codebase-design ✎"),
        ("skill", "domain-modeling ✎"), ("skill", "improve-codebase-architecture ✎"), ("skill", "handoff ✎"),
        ("skill", "teach ✎"), ("skill", "wait-what ✎"), ("skill", "wizard ✎"), ("skill", "diagram-design ✎")]),
]


def _rows(chips, w):
    """Lay chips left to right inside a zone of width w; return positions and the number of rows."""
    out, cx, row = [], 14, 0
    for k, label in chips:
        cw = tw(label, 11.5, True) + 18
        if cx + cw > w - 10:
            cx, row = 14, row + 1
        out.append((k, label, cx, row))
        cx += cw + 8
    return out, row + 1


def inventory():
    f = Fig("m5", 1000)
    W = 485
    y = 10
    for i in range(0, len(GROUPS), 2):
        pair = GROUPS[i:i + 2]
        laid = [_rows(chips, W) for _, _, chips in pair]
        h = 40 + max(n for _, n in laid) * 32
        for j, ((title, _, _), (chips, _)) in enumerate(zip(pair, laid)):
            x = 10 + j * (W + 10)
            f.zone(x, y, W, h, title)
            for k, label, cx, row in chips:
                f.chip(k, x + cx, y + 32 + row * 32, label)
        y += h + 10
    f.note(10, y + 12, "✎ = 来自上游（mattpocock/skills、diagram-design、unlazy），本仓库改过，改动和理由写在 mmw-v2/merge-notes/ 的同名文件里")
    return f.svg(y + 22, "MMW v2 的全部组成，按各自解决的问题分成八组：白天写票、界面、一张票、编排、合并、早上、工具箱本身、不属于流水线的单件事。")


def routing():
    f = Fig("m6", 1000)
    # pstack
    f.zone(10, 10, 485, 380, "pstack：任务的顺序写在 playbook 里")
    f.box("mode", 26, 42, 453, 52, "poteto-mode/SKILL.md", ["一直在上下文里；## Playbooks 一行路由一份"], mono=True)
    f.ar([(252, 94), (252, 116)])
    f.box("playbook", 26, 116, 453, 52, "playbooks/feature.md", ["编号步骤，抄进 todolist 逐步做"], mono=True)
    f.ar([(252, 168), (252, 190)])
    f.box("skill", 26, 190, 453, 52, "步骤点名的技能，例 how、architect", ["技能只管一件事，不知道是哪份 playbook 在用它"])
    f.ar([(252, 242), (252, 264)])
    f.box("reference", 26, 264, 453, 52, "技能的 references/", ["某一步、某个子代理才用的材料"])
    f.note(26, 344, "49 个技能设了 disable-model-invocation: true，")
    f.note(26, 362, "由你用 /名字 调用，或由 playbook 的步骤点名")
    # v2
    f.zone(505, 10, 485, 380, "MMW v2：没有 mode 和 playbook")
    f.box("config", 521, 42, 453, 52, "prompt/shared.md → ~/.claude/CLAUDE.md", ["一直在上下文里；讲谁做决定、怎么汇报，不路由"], mono=True)
    f.box("skill", 521, 116, 453, 52, "dispatch/SKILL.md 的 description", ["宿主据它决定要不要打开这个技能"])
    f.ar([(747, 168), (747, 190)])
    f.box("skill", 521, 190, 453, 52, "## Find your moment：按你此刻是谁选一行", ["Moment 1 worker … Moment 3 orchestrator …"])
    f.ar([(640, 242), (640, 264)])
    f.ar([(860, 242), (860, 264)])
    f.box("skill", 521, 264, 220, 52, "implement 的", ["## Closing steps，8 步"])
    f.box("reference", 754, 264, 220, 52, "references/night.md", ["## 1 到 ## 6 编号各节"], mono=True)
    f.note(521, 344, "顺序写在技能正文或它的 reference 里；")
    f.note(521, 362, "implement 的每步以「Done when」结尾：做到什么才算完")
    return f.svg(400, "pstack 和 MMW v2 把一个任务的顺序放在不同地方：pstack 由一直在上下文里的 mode 路由到 playbook，playbook 的步骤点名技能；v2 没有 mode 和 playbook，宿主按技能的 description 打开技能，技能里的 Find your moment 表按角色指向技能正文的编号步骤或一份 reference。")


FIGS = {"l3-lifecycle": lifecycle, "l3-inventory": inventory, "l3-routing": routing}

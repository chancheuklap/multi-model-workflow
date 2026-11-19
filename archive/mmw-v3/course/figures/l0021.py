"""Figures of lesson 0021: what MMW v3 took from pstack. pstack's components with the ones taken
marked; how a v3 session uses the shape taken from poteto-mode; the how and why skills run as
sessions; Bug fix in pstack and in v3; Pause safely; technical-writing's four layers."""
from kit import Fig, tbox as _box, txt as _txt

# pstack's components in the order poteto-mode and the skills directory list them.
# A name with a kind was copied into v3; a name without one was not.
PLAYBOOKS = [
    ("Investigation", "playbook"), ("Bug fix", "playbook"), ("Perf issue", None), ("Hillclimb", None),
    ("Runtime forensics", "playbook"), ("Trace forensics", "playbook"), ("Feature", None), ("Refactoring", None),
    ("Prototype", None), ("Visual parity", None), ("Authoring a skill", None), ("Eval", None),
    ("Babysit", None), ("Shipping", None), ("Autonomous run", None), ("Orchestrate", None),
    ("Autopilot-full", None), ("Autopilot-stack", None), ("Session pickup", None),
    ("Pause safely", "playbook"), ("Multi-phase plan", None), ("Worktree cleanup", None),
    ("Opening a PR", None),
]
PRINCIPLES = [
    ("Laziness Protocol", "principle"), ("Foundational Thinking", None), ("Redesign from First Principles", None),
    ("Attack the Premise", None), ("Subtract Before You Add", None), ("Minimize Reader Load", None),
    ("Outcome-Oriented Execution", None), ("Experience First", None), ("Exhaust the Design Space", None),
    ("Build the Lever", None), ("Model the Domain", None), ("Boundary Discipline", None),
    ("Type System Discipline", None), ("Make Operations Idempotent", None),
    ("Migrate Callers Then Delete Legacy APIs", "principle"),
    ("Separate Before Serializing Shared State", "principle"), ("Prove It Works", "principle"),
    ("Fix Root Causes", None), ("Sequence Work into Verifiable Units", None),
    ("Test Behavior, Not Implementation", "principle"), ("Explain the Number", "principle"),
    ("Guard the Context Window", None), ("Never Block on the Human", "principle"),
    ("Encode Lessons in Structure", None),
]
SKILLS = [
    ("architect", None), ("arena", None), ("automate-me", None), ("benchmark-checklist", "skill"),
    ("blast-radius", None), ("bro", None), ("correct", None), ("create-verification-skill", None),
    ("figure-it-out", None), ("how", "skill"), ("interrogate", None), ("maintain-verification-skill", None),
    ("make-bot-ui", None), ("no-comments", None), ("recall", None), ("reflect", None),
    ("setup-pstack", None), ("show-me-your-work", None), ("swarm", None),
    ("tdd（v3 用 mattpocock 的）", None), ("teach（v3 用 mattpocock 的）", None),
    ("technical-writing", "skill"), ("typescript-best-practices", None), ("unslop", "skill"), ("why", "skill"),
]
OTHERS = [
    ("poteto-agent（子代理定义）", None), ("comment-sicko（子代理定义）", None),
    ("pstack-models.mdc（rule）", None), ("automations/benny", None),
]
RENAMED = {"Test Behavior, Not Implementation": "v3 名：A Check Must Be Able to Fail"}


def _column(f, x, w, y0, title, items):
    taken = sum(1 for _, k in items if k)
    rows = len(items) + sum(1 for n, _ in items if n in RENAMED)
    h = 44 + rows * 22
    f.zone(x, y0, w, h, f"{title}（{len(items)}，拿了 {taken}）")
    y = y0 + 32
    for name, kind in items:
        if kind:
            f.e(f'<g class="k-{kind}"><rect class="box" x="{x + 8}" y="{y}" width="{w - 16}" height="19" rx="3"/></g>', False)
            _txt(f, x + 15, y + 14, name, "s", room=w - 30)
            f.front[-1] = f.front[-1].replace('class="s"', 'class="s" style="fill:var(--ink)"')
        else:
            _txt(f, x + 15, y + 14, name, "s", room=w - 30)
        y += 22
        if name in RENAMED:
            _txt(f, x + 22, y + 12, "↳ " + RENAMED[name], "s", room=w - 36)
            y += 22
    return y0 + h


def pstack_map():
    f = Fig("m211", 1000)
    _box(f, "mode", 10, 10, 980, "poteto-mode/SKILL.md（mode 技能，每个会话先读它）",
         ["七节：## Non-negotiables、## Principles、## Autonomy、## Subagents、## Writing the reply、## Comments 六节改写进 mmw-mode；",
          "## Playbooks 拿了它的写法和其中五条路由，路由表换成 MMW 自己的 27 条"])
    y0 = 92
    bottoms = [
        _column(f, 10, 206, y0, "playbook", PLAYBOOKS),
        _column(f, 222, 290, y0, "principle", PRINCIPLES),
        _column(f, 518, 262, y0, "其他技能", SKILLS),
        _column(f, 786, 204, y0, "其他组件", OTHERS),
    ]
    return f.svg(max(bottoms) + 8, ARIA_MAP)


ARIA_MAP = (
    "第 21 课图 1，pstack 的全部组件，v3 拿了的上了颜色。mode 技能 poteto-mode 的七节里六节改写进 mmw-mode，"
    "## Playbooks 拿了写法和五条路由。23 份 playbook 拿了 Investigation、Bug fix、Runtime forensics、Trace forensics、Pause safely。"
    "24 条原则拿了 Laziness Protocol、Migrate Callers Then Delete Legacy APIs、Separate Before Serializing Shared State、"
    "Prove It Works、Explain the Number、Never Block on the Human，以及改名为 A Check Must Be Able to Fail 的 Test Behavior, Not Implementation。"
    "25 个其他技能拿了 benchmark-checklist、how、why、unslop、technical-writing；tdd 和 teach 在 v3 里用的是 mattpocock 的版本。"
    "子代理定义 poteto-agent、comment-sicko、模型配置 pstack-models.mdc 和 benny 自动化都没拿。")


def session():
    f = Fig("m212", 1000)
    _box(f, "script", 10, 10, 320, "你在接入过的仓库开会话",
         ["Claude Code、Codex：mode-hook.py", "往上下文加一句：先读 mode 全文"])
    _box(f, "script", 340, 10, 320, "dispatch.sh 开 worker、reviewer",
         ["起始提示词第一句：先读 mode 全文", "第二句：点名要跑的 playbook"])
    _box(f, "other", 670, 10, 320, "任何宿主上：你输入 /mmw-mode",
         ["mode 只有人能开，", "模型自己调不了它"])
    f.ar([(170, 74), (170, 90), (390, 90), (390, 108)])
    f.ar([(500, 74), (500, 108)])
    f.ar([(830, 74), (830, 90), (610, 90), (610, 108)], cls="human")
    f.box("mode", 330, 110, 340, 46, "会话读 mmw-mode/SKILL.md 全文", head=True)

    # Left column: what stays in force all session.
    _box(f, "mode", 10, 190, 290, "一直生效的四节",
         ["## Autonomy：哪些直接做，哪些停", "## Subagents：子代理怎么派", "## Writing the reply：回复怎么写",
          "## Comments：代码注释写什么"])
    _box(f, "mode", 10, 310, 290, "## Non-negotiables：时刻 → 技能",
         ["非小的改动、架构决定 → how", "任何文字 → unslop", "文档、提交信息 → technical-writing",
          "要跑产品或读判官输出 → ui-acceptance", "仓库没接入流水线 → setup-mmw"])
    f.ar([(330, 126), (155, 126), (155, 188)])
    f.ar([(330, 146), (316, 146), (316, 367), (302, 367)])

    # Right column: the principle index and the leaf it points to.
    _box(f, "mode", 700, 190, 290, "## Principles：16 行索引",
         ["每行：什么情况下用，规则一句话", "这 16 行一直在上下文里", "情况出现时才读那条的全文"])
    _box(f, "principle", 700, 310, 290, "principle-*/SKILL.md（16 个）",
         ["规则、Why、做法、何时停；", "回复里点名用了哪条"])
    f.ar([(670, 133), (845, 133), (845, 188)])
    f.ar([(845, 271), (845, 308)], "情况出现", 852, 294)

    # Middle: routing to one playbook.
    f.dia(500, 215, 110, 34, ["起始提示词", "点名了 playbook？"])
    f.ar([(500, 156), (500, 179)])
    f.ar([(390, 215), (360, 215), (360, 278)], "是", 344, 248)
    f.ar([(610, 215), (640, 215), (640, 278)], "否", 648, 248)
    _box(f, "playbook", 330, 280, 160, "照它跑", ["从任务记录指向的", "那一步做起"])
    _box(f, "playbook", 510, 280, 160, "自己挑", ["按 ## Playbooks 的", "路由行挑一份"])
    f.ar([(410, 344), (410, 372)])
    f.ar([(590, 344), (590, 372)])
    _box(f, "playbook", 330, 374, 340, "打开那份 playbook", ["步骤逐字抄进 todolist，不做的写 skip"])
    f.ar([(500, 421), (500, 443)])
    _box(f, "playbook", 330, 445, 340, "逐步做", ["每一步点名它用的技能、原则、", "references 文件和 scripts 程序"])
    f.att([(330, 477), (155, 477), (155, 425)])
    f.att([(670, 477), (845, 477), (845, 374)])
    f.ar([(500, 509), (500, 533)])
    f.pill(500, 535, "回复：照 ## Writing the reply 和 playbook 的 Reply 行")
    return f.svg(580, ARIA_SESSION)


ARIA_SESSION = (
    "第 21 课图 2，一个 v3 会话怎样用从 poteto-mode 拿来的结构。三条路进来：接入过的仓库里 mode-hook.py 加一句，"
    "dispatch.sh 的起始提示词第一句，或你输入 /mmw-mode。会话读 mmw-mode 全文。Autonomy、Subagents、Writing the reply、"
    "Comments 四节一直生效；Non-negotiables 在某种时刻点名一个技能；Principles 的 16 行索引一直在上下文里，情况出现时才读原则全文。"
    "起始提示词点名了 playbook 就从任务记录指向的那一步跑，否则按路由行挑一份；打开 playbook，步骤逐字抄进 todolist，"
    "逐步做，每步点名它用的技能、原则、references 和 scripts，最后照 Writing the reply 和 playbook 的 Reply 行回复。")


def investigation():
    f = Fig("m213", 1000)
    f.zone(200, 10, 790, 222, "how：这段代码怎样工作")
    f.zone(200, 250, 790, 200, "why：它为什么是这个样子")
    _box(f, "playbook", 10, 186, 180, "Investigation", ["第 1 步：本仓库的问题", "交给 how、why；仓库外", "的问题开一个 researcher"])
    f.ar([(190, 205), (202, 205), (202, 120), (213, 120)])
    f.ar([(190, 240), (202, 240), (202, 330), (213, 330)])
    f.dia(275, 120, 60, 40, ["问题", "复杂吗？"])
    f.ar([(275, 80), (275, 73), (358, 73)], "复杂", 300, 66)
    f.ar([(275, 160), (275, 173), (358, 173)], "简单", 300, 166)
    _box(f, "agent", 360, 50, 160, "researcher × 2–4", ["每个查一个角度"])
    f.ar([(520, 73), (568, 73)], "叫醒", 544, 66, "middle")
    _box(f, "agent", 570, 50, 170, "explainer", ["读答案文件，写说明"])
    _box(f, "other", 360, 150, 380, "你的会话", ["简单问题：自己边读边写，不开会话"])
    f.ar([(740, 73), (765, 73), (765, 110), (788, 110)], "叫醒", 753, 66, "middle")
    f.ar([(740, 173), (765, 173), (765, 140), (788, 140)])
    _box(f, "other", 790, 80, 190, "你的会话", ["对照代码核一遍，", "照 Writing the reply", "写给你"])
    _txt(f, 360, 220, "交回五节：Overview、Key Concepts、How It Works、Where Things Live、Gotchas", "s", room=620)
    _box(f, "other", 215, 298, 170, "代码锚点", ["git blame、git log，", "gh 读 PR 的讨论"])
    f.ar([(385, 330), (413, 330)])
    _box(f, "agent", 415, 298, 230, "investigator × 每种来源一个", ["源码历史、工单、文档、聊天、", "监控、报错、数据仓库"])
    f.ar([(645, 330), (678, 330)], "叫醒", 661, 322, "middle")
    _box(f, "agent", 680, 298, 150, "synthesizer", ["已知、推断、不知道", "分开写"])
    f.ar([(830, 330), (858, 330)], "叫醒", 844, 322, "middle")
    _box(f, "other", 860, 298, 125, "你的会话", ["核对后写给你，", "把握程度不改"])
    _txt(f, 215, 400, "交回：问题、相关代码、查到的、合理推断、几种可能的解释、不知道的、", "s", room=760)
    _txt(f, 215, 418, "查过哪些来源（没查的也写，附理由）、把握程度小结", "s", room=760)
    return f.svg(460, ARIA_INV)


ARIA_INV = (
    "第 21 课图 6，Investigation 怎样用 how 和 why，每个 agent 都是 dispatch.sh brief 开的独立会话。"
    "how：简单问题由你的会话自己边读边写；复杂问题先开 2 到 4 个 researcher 各查一个角度，全部答完后 relay 叫醒，"
    "再开一个 explainer 读它们的答案写说明；最后你的会话对照代码核一遍，照 Writing the reply 写给你。交回五节。"
    "why：先建代码锚点（git blame、git log、gh 读 PR 讨论），每种证据来源开一个 investigator，叫醒后开一个 synthesizer，"
    "把已知、推断、不知道分开写，你的会话核对后写给你，不改它标的把握程度。")


PSTACK_BUG = [
    ("1. 自己复现", ["在出错的那个界面上用 control 技能亲手复现；够不着才请你"]),
    ("2. 二分找原因", ["列出假设逐个排除；how 看子系统，why 查引入它的改动"]),
    ("3. 计划修法", ["跨函数边界先跑 architect；写代码交给一个子代理"]),
    ("4. 在同一界面验证", ["原来的复现现在通过；「不确定」或换了界面都不算"]),
    ("5. 失败的复现先进 git 历史", ["测试便宜时照 tdd：先提交会失败的测试，修复在上面"]),
    ("6. Opening a PR", ["开 PR，交给 bugbot 和人审，再合并"]),
]
V3_BUG = [
    ("1. 自己复现", "同", ["照 diagnosing-bugs 第 1、2 阶段；跑产品时守 ui-acceptance 五条",
                         "不报错、只在运行中出现：Runtime forensics；你交来文件：Trace forensics",
                         "复现不了：告诉你试了什么、还要什么，到此为止"]),
    ("2. 找原因", "同", ["照 diagnosing-bugs 第 3、4 阶段；how、why 帮忙列假设",
                        "排好序的假设给你看，不等回复；代码照要求做了就不是 bug"]),
    ("3. 写一张票", "改", ["症状、原因和证据、证据撑得住的最小改动；",
                          "第一条判据是一个回归测试，放在 bug 发生的位置"]),
    ("4. 交给 Run one ticket 落地", "改", ["worker 先写会失败的测试再修，reviewer 审，",
                                         "land 把它合进 base 分支；没有 PR"]),
    ("5. 在原场景上证明", "同", ["base 上重跑第 1 步的命令：原来红，现在绿"]),
]


def bugfix():
    f = Fig("m214", 1000)
    _txt(f, 10, 22, "pstack：在你的会话里修完，开 PR", "h", room=480)
    _txt(f, 510, 22, "v3：诊断、写票，交给夜里那套机器落地", "h", room=480)
    y = 38
    for title, lines in PSTACK_BUG:
        h = _box(f, "other", 10, y, 480, title, lines)
        y += h + 10
    left_bottom = y
    y = 38
    for title, tag, lines in V3_BUG:
        h = _box(f, "playbook", 510, y, 480, title, lines)
        word = "和 pstack 一样" if tag == "同" else "MMW 改的"
        _txt(f, 978, y + 20, word, "s", anchor="end")
        y += h + 10
    return f.svg(max(left_bottom, y), ARIA_BUG)


ARIA_BUG = (
    "第 21 课图 4，左边 pstack 的 Bug fix 六步：自己复现，二分找原因，计划修法并交子代理写代码，在同一界面验证，"
    "失败的复现先进 git 历史，开 PR。右边 v3 的五步：自己复现，找原因，写一张票，交给 Run one ticket 落地，"
    "在原场景上证明。复现、找原因、在原场景证明三步和 pstack 一样；写票和交给 Run one ticket 是 MMW 改的，因为 MMW 没有 PR，"
    "代码由 worker 先写失败的测试再修，reviewer 审，land 合进 base 分支。")


PAUSE = [
    ("1. 在安全处停", ["做完当前这一步或退回；", "不开新的，叫停子代理"]),
    ("2. 不做收不回的事", ["分支原本没推过，", "这时也不推"]),
    ("3. 让工作落盘", ["没提交的改动提交成", "一个 wip: 提交"]),
    ("4. 写续做说明", ["用 handoff 技能：意图、进度、", "下一步、关键文件、坑"]),
]


def pause():
    f = Fig("m215", 1000)
    x = 10
    for i, (title, lines) in enumerate(PAUSE):
        _box(f, "playbook", x, 10, 230, title, lines)
        if i < len(PAUSE) - 1:
            f.ar([(x + 230, 42), (x + 248, 42)])
        x += 250
    f.ar([(500, 74), (500, 98)])
    f.pill(500, 100, "回复：停在哪、哪些已在磁盘上、续做时第一步做什么")
    return f.svg(144, "第 21 课图 3，Pause safely 的四步：在安全处停，不做收不回的事，让工作落盘成一个 wip: 提交，"
                      "用 handoff 技能写续做说明；最后回复停在哪、哪些已在磁盘上、续做时第一步做什么。")


def writing_layers():
    f = Fig("m216", 1000)
    _txt(f, 10, 20, "第一层 Diátaxis：先定这份文档是哪一种", "h", room=480)
    X, Y, CW, CH = 110, 60, 180, 78
    _txt(f, X + CW / 2, Y - 10, "教人做事（action）", "s", anchor="middle")
    _txt(f, X + CW * 1.5 + 8, Y - 10, "帮人理解（understanding）", "s", anchor="middle")
    _txt(f, X - 10, Y + CH / 2 + 4, "学习时", "s", anchor="end")
    _txt(f, X - 10, Y + CH * 1.5 + 12, "干活时", "s", anchor="end")
    cells = [
        (0, 0, "tutorial 教程", ["带新手做出一个东西"]),
        (1, 0, "explanation 解释", ["讲为什么，可以有观点"]),
        (0, 1, "how-to 操作指南", ["解决一件具体的事"]),
        (1, 1, "reference 参考", ["只陈述事实，供查阅"]),
    ]
    for cx, cy, title, lines in cells:
        _box(f, "skill", X + cx * (CW + 8), Y + cy * (CH + 8), CW, title, lines)
    layers = [
        ("第二层 Google 开发者文档风格", ["对读者说「你」，用现在时，说清谁做什么；", "条件写在指令前面，常见情况写在前面"]),
        ("第三层 STE 规则（简化技术英语）", ["一句一条指令，指令超过约 20 词就拆；", "一个词只表达一个意思，一个动作只用一个词"]),
        ("第四层 Global English", ["每一句只能读出一种意思：", "only、not 紧贴它修饰的词，it 和 this 指向明确"]),
    ]
    y = 34
    for title, lines in layers:
        h = _box(f, "skill", 520, y, 470, title, lines)
        y += h + 10
    return f.svg(max(y, Y + 2 * CH + 20), ARIA_LAYERS)


ARIA_LAYERS = (
    "第 21 课图 7，technical-writing 技能的四层。第一层 Diátaxis 用两个问题定文档种类：教人做事还是帮人理解，"
    "在学习时还是干活时读；四格是 tutorial 教程、explanation 解释、how-to 操作指南、reference 参考。"
    "第二层 Google 开发者文档风格管句子怎样对读者说话；第三层 STE 规则管每句承载多少；第四层 Global English 让每句只有一种读法。")


RUNTIME = [
    ("1 抓证据", ["自己起一个实例，", "用工具清单里的工具"]),
    ("2 缩小", ["找到热路径、引用链", "或卡住的线程"]),
    ("3 证明", ["在自己起的实例上", "注入探针验证"]),
    ("4 对应源码", ["文件、函数、行号", ""]),
    ("5 停掉", ["停掉自己起的实例，", "停不了就告诉你"]),
]
TRACE = [
    ("1 认格式、载入", ["按工具清单选工具，", "问清哪个版本"]),
    ("2 变成可查询", ["Perfetto、SQLite", "或 memlab"]),
    ("3 缩小", ["耗时最多的调用、", "泄漏对象的引用链"]),
    ("4 对应源码", ["没有符号就照实说", ""]),
    ("5 对照", ["有前后两份就比较，", "没有就只算假设"]),
]


def forensics():
    f = Fig("m217", 1000)
    f.zone(170, 10, 820, 150, "Runtime forensics：对着正在运行的进程")
    f.zone(170, 176, 820, 150, "Trace forensics：对着已经抓好的文件")
    for y0, steps in ((44, RUNTIME), (210, TRACE)):
        for i, (title, lines) in enumerate(steps):
            x = 180 + i * 162
            _box(f, "playbook", x, y0, 150, title, lines)
            if i < len(steps) - 1:
                f.ar([(x + 150, y0 + 32), (x + 160, y0 + 32)])
    _txt(f, 182, 136, "别的机器上启动前先问你；只在自己起的实例上动手，别人的实例先问你；证据文件不进仓库", "s", room=800)
    _txt(f, 182, 302, "文件来自你，或来自够不着的机器（比如客户电脑）；只读，不重跑", "s", room=800)
    _box(f, "playbook", 10, 44, 150, "Bug fix 第 1 步", ["症状不报错，", "只在运行中出现"])
    _box(f, "other", 10, 210, 150, "你交来一个文件", ["比如客户电脑上", "抓的堆快照"])
    f.ar([(160, 76), (178, 76)])
    f.ar([(160, 242), (178, 242)])
    f.ar([(978, 76), (986, 76), (986, 356)])
    f.ar([(903, 274), (903, 356)])
    _box(f, "playbook", 180, 358, 810, "回到 Bug fix，从「写票」接着做",
         ["修好后第 5 步：用同样的方法再抓一次，和第一次的对比；只诊断、不修时，到交回诊断为止"])
    return f.svg(412, ARIA_FORENSICS)


ARIA_FORENSICS = (
    "第 21 课图 5，两份 forensics playbook。Runtime forensics 由 Bug fix 第 1 步在症状不报错、只在运行中出现时转来："
    "自己起一个实例并用工具清单里的工具抓证据，缩小到热路径、引用链或卡住的线程，在自己起的实例上注入探针证明，"
    "对应到文件、函数、行号，最后停掉自己起的实例，停不了就告诉你；在别的机器上启动之前先问你，别人的实例先问你，证据文件不进仓库。"
    "Trace forensics 从你交来的文件开始：认格式、问清版本并载入，变成 Perfetto、SQLite 或 memlab 能查询的形式，缩小，对应源码，有前后两份就对比。"
    "两份都回到 Bug fix，从写票接着做；修好后用同样的方法再抓一次对比。")


FIGS = {
    "l21-pstack-map": pstack_map,
    "l21-session": session,
    "l21-investigation": investigation,
    "l21-bugfix": bugfix,
    "l21-pause": pause,
    "l21-writing-layers": writing_layers,
    "l21-forensics": forensics,
}

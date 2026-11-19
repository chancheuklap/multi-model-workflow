"""Figures of lesson 0004: the moments when agents communicate, what pstack and MMW v2 each say about them, which of two like skills is kept, and the merged design drawn inside the skeleton of mmw-mode/SKILL.md."""
import html
import re
from kit import Fig, tw


def moments():
    f = Fig("m7", 1000)
    f.box("other", 30, 180, 180, 80, "你", ["产品负责人，不读代码"], head=True)
    f.box("other", 410, 180, 200, 80, "和你对话的 agent", ["白天会话、orchestrator"], head=True)
    f.box("other", 790, 180, 180, 80, "它派出的 agent", ["子代理、worker、reviewer"], head=True)
    for i, t in enumerate(["① 回复你", "② 要不要先问你", "③ 不同意你", "④ 你不在时的交代",
                           "⑪ 访谈你，把决定问清", "⑫ 给你讲明白一件事"]):
        f.lbl(232, 70 + i * 18, t)
    f.ar([(408, 200), (212, 200)])
    f.ar([(212, 240), (408, 240)], "⑩ 你没听懂，请它重说", 232, 260)
    f.ar([(612, 200), (788, 200)], "⑤ 任务说明（brief）", 626, 190)
    f.ar([(788, 240), (612, 240)], "⑥ 交回的报告", 626, 260)
    f.box("script", 560, 20, 200, 44, "票上的子票", ["早上你读到"])
    f.ar([(880, 178), (880, 42), (762, 42)])
    f.lbl(888, 114, "⑦ 夜里没人可问时")
    f.lbl(888, 132, "的问题")
    f.ar([(558, 42), (120, 42), (120, 178)])
    f.box("other", 300, 350, 230, 64, "以后接手的 agent", ["冷启动，看不到这次对话"], head=True)
    f.box("other", 600, 350, 260, 64, "文件的读者", ["文档、注释、技能正文、提示词"], head=True)
    f.ar([(470, 262), (470, 348)], "⑧ 暂停与接手", 478, 312)
    f.ar([(560, 262), (560, 302), (730, 302), (730, 348)], "⑨ 写进文件的文字", 600, 294)
    return f.svg(424, "agent 沟通发生的十二个时刻：对你的回复、要不要先问、不同意、你不在时的交代、访谈你、给你讲解、你请它重说；给派出的 agent 写任务说明、收它的报告；夜里没人可问时把问题写进票上的子票；暂停与接手；写进文件的文字。")


ROWS = [
    ("① 回复你",
     [("mode", "Writing the reply"), ("skill", "unslop")],
     [("config", "shared.md 开头五条事实"), ("config", "规则 4、5、6、8、9")]),
    ("② 要不要先问你",
     [("mode", "Non-negotiables：问之前先分类"), ("mode", "Autonomy"), ("principle", "never-block-on-the-human")],
     [("config", "shared.md 规则 1、2、11"), ("skill", "advisor")]),
    ("③ 不同意你",
     [("mode", "Autonomy：No is an acceptable answer"), ("playbook", "Investigation 的 Reply")],
     [("config", "shared.md 规则 3")]),
    ("④ 你不在时的交代",
     [("skill", "show-me-your-work"), ("playbook", "Autonomous run 第 4 步"), ("playbook", "Orchestrate：Escalation")],
     [("config", "shared.md 规则 2"), ("script", "dispatch.sh summary"), ("skill", "retro")]),
    ("⑤ 任务说明",
     [("mode", "Subagents"), ("playbook", "Orchestrate：The brief")],
     [("config", "shared.md 规则 10"), ("skill", "to-tickets 的票"), ("script", "dispatch.sh 拼的开工提示词")]),
    ("⑥ 交回的报告",
     [("mode", "Subagents：You own every subagent's work"), ("playbook", "Orchestrate：REPORT")],
     [("skill", "code-review 的报告"), ("skill", "implement 的收尾评论")]),
    ("⑦ 夜里没人可问",
     [("playbook", "Orchestrate：gates.md")],
     [("skill", "implement：Put no question on the screen"), ("script", "tool-guard.py"), ("skill", "verify-ticket 的子票")]),
    ("⑧ 暂停与接手",
     [("playbook", "Pause safely"), ("playbook", "Session pickup")],
     [("skill", "handoff")]),
    ("⑨ 写进文件的文字",
     [("skill", "technical-writing"), ("skill", "unslop"), ("mode", "Comments"), ("playbook", "Authoring a skill"), ("other", "create-skill（Cursor 内置）")],
     [("config", "shared.md 规则 7、8、10、13"), ("skill", "writing-for-agents")]),
    ("⑩ 请它重说",
     [("skill", "bro")],
     [("skill", "wait-what")]),
    ("⑪ 访谈你",
     [("playbook", "Prototype"), ("mode", "Non-negotiables：问之前先分类")],
     [("skill", "grilling"), ("skill", "grill-me"), ("skill", "grill-with-docs"), ("skill", "to-questionnaire")]),
    ("⑫ 给你讲明白",
     [("skill", "teach（讲清一段代码）"), ("skill", "how"), ("skill", "why")],
     [("skill", "teach（多次课的课程）"), ("skill", "wait-what visual")]),
]


def _lay(chips, x0, w):
    out, cx, row = [], x0, 0
    for k, label in chips:
        cw = tw(label, 11.5, False) + 24
        if cx + cw > x0 + w and cx > x0:
            cx, row = x0, row + 1
        out.append((k, label, cx, row))
        cx += cw + 8
    return out, row + 1


def coverage():
    f = Fig("m8", 1000)
    f.note(10, 16, "时刻")
    f.note(200, 16, "pstack 写在哪")
    f.note(620, 16, "MMW v2 写在哪")
    y = 28
    for label, ps, v2 in ROWS:
        a, na = _lay(ps, 200, 400)
        b, nb = _lay(v2, 620, 370)
        h = max(na, nb) * 30 + 10
        f.e(f'<line x1="10" y1="{y + h}" x2="990" y2="{y + h}" class="rule"/>', False)
        f.e(f'<text x="10" y="{y + 22}" class="h">{label}</text>')
        for k, t, cx, row in a + b:
            f.chip(k, cx, y + 6 + row * 30, t, mono=False)
        y += h
    return f.svg(y + 6, "十二个沟通时刻里，pstack 与 MMW v2 各自把规则写在哪。每一行两边都有内容：pstack 分散在 mode 各节、技能、原则和几份 playbook；MMW v2 有 shared.md 的编号规则，也有 wait-what、writing-for-agents、handoff、grilling、teach、advisor 等技能和 tool-guard.py 等脚本。")


CHOICES = [
    ("⑩", [("skill", "bro")], [("skill", "wait-what")], "v2",
     "留 wait-what：同样换简单说法，还要先补背景、用 CONTEXT.md 的词，加 visual 能画一页图"),
    ("⑨⑤", [("playbook", "Authoring a skill"), ("other", "create-skill（Cursor 内置）")],
     [("skill", "writing-for-agents"), ("reference", "SKILL-SET-RULES.md"), ("reference", "REVIEWING-A-SKILL-SET.md")], "both",
     "writing-for-agents 占 create-skill 的位置；两份规则书里写和审的步骤各成一份 playbook，共用的规则成为 mode 的 reference"),
    ("⑨", [("skill", "technical-writing")], [], "pstack",
     "留 technical-writing：v2 没有同类，用于写给人读的文档"),
    ("①⑨", [("skill", "unslop")], [("config", "shared.md 规则 7")], "pstack",
     "留 unslop：规则 7 是它 30 多条里的一条"),
    ("⑧", [("playbook", "Pause safely")], [("skill", "handoff")], "both",
     "两个都留：Pause safely 第 4 步写交接说明时照 handoff 写"),
    ("⑪", [], [("skill", "grilling"), ("skill", "to-questionnaire")], "v2",
     "留 v2 的：pstack 没有访谈技能"),
    ("⑫", [("skill", "teach（讲清一段代码）")], [("skill", "teach（课程）")], "both",
     "两个都留，做的事不同；teach 这个名字归 v2 的课程技能，pstack 那个改名"),
    ("⑤", [("playbook", "Orchestrate：The brief")], [("skill", "to-tickets 的票")], "open",
     "下一课定：夜里的任务说明是票；白天派子代理怎么写说明，和 MMW 自己的子代理规则一起比较"),
    ("⑥", [("playbook", "Orchestrate：REPORT")], [("skill", "implement 的收尾评论")], "open",
     "下一课定：夜里用收尾评论，由 verify-ticket.py 检查；白天子代理怎么交回，和 MMW 自己的子代理规则一起比较"),
    ("⑦", [("playbook", "Orchestrate：gates.md")], [("skill", "implement：不弹提问"), ("script", "tool-guard.py")], "v2",
     "用 v2 的，脚本已经强制；补上 pstack「到你 / 不到你」两张清单"),
    ("②", [("skill", "interrogate")], [("skill", "advisor")], "open",
     "本课不比较：两者是做决定时找第二意见，属于协作，下一课比较"),
]


def _wrap(text, width, size=11.5):
    """Split a note into lines no wider than width: between CJK characters or Latin words, never before a closing mark."""
    lines, cur = [], ""
    for tok in re.findall(r"[A-Za-z0-9_.#/*:-]+|.", text):
        if tw(cur + tok, size) > width and cur.strip() and tok not in "，。；：、）」":
            lines.append(cur.rstrip())
            cur = tok.lstrip()
        else:
            cur += tok
    return lines + [cur] if cur else lines


def choices():
    f = Fig("m10", 1000)
    f.note(10, 16, "时刻")
    f.note(60, 16, "pstack")
    f.note(300, 16, "MMW v2")
    f.note(540, 16, "留哪个，为什么")
    tint = {"v2": "skill", "pstack": "mode", "both": "playbook", "open": "other"}
    word = {"v2": "留 v2 的", "pstack": "留 pstack 的", "both": "两边都留", "open": "待比较"}
    y = 28
    for n, ps, v2, who, why in CHOICES:
        a, na = _lay(ps, 60, 230)
        b, nb = _lay(v2, 300, 230)
        lines = _wrap(why, 440)
        h = max(max(na, nb) * 30 + 10, 44 + len(lines) * 16)
        f.e(f'<line x1="10" y1="{y + h}" x2="990" y2="{y + h}" class="rule"/>', False)
        f.e(f'<text x="10" y="{y + 22}" class="h">{n}</text>')
        for k, t, cx, row in a + b:
            f.chip(k, cx, y + 6 + row * 30, t, mono=False)
        if not ps:
            f.note(60, y + 22, "（没有同类）")
        if not v2:
            f.note(300, y + 22, "（没有同类）")
        f.chip(tint[who], 540, y + 6, word[who], mono=False)
        for i, line in enumerate(lines):
            f.note(540, y + 48 + i * 16, line)
        y += h
    return f.svg(y + 6, "同类组件逐对比较后的去留：bro 与 wait-what 留 wait-what；写给 agent 的文字照 pstack 的分法放 v2 的内容，writing-for-agents 占 create-skill 的位置，规则书拆成两份 playbook 和一份 mode 的 reference；technical-writing 与 unslop 留 pstack 的；Pause safely 与 handoff 都留；访谈留 grilling 一组；两个 teach 都留；任务说明和报告下一课和 MMW 自己的子代理规则一起比较；夜里没人可问用 v2 的机制；interrogate 与 advisor 待比较。")


# ---- where every rule goes: each unit of shared.md, and each communication rule only pstack has ----

SHARED = [
    ("开头五条事实：读者不读代码、只看产品和文字、工作记忆小……", [("config", "全局层"), ("mode", "## Writing the reply")],
     "压成两三句写进全局层；理由删掉，只写做什么（pstack 的写法）；「只看产品和文字」「工作记忆小」进 Writing the reply 开头"),
    ("一句话：像工程师向老板汇报，老板不是外行、不读代码", [("config", "全局层")], "原样留，作全局层第一句"),
    ("脚本起的会话（worker、reviewer）按票办事", [("mode", "## Autonomy")], "移出全局层，成为 Unattended 一段：只对脚本起的会话成立，三份角色 playbook 共用（第 5 课决定 5）"),
    ("规则 1：工程归你，产品归我", [("config", "全局层"), ("mode", "## Autonomy")],
     "只归你的决定清单放全局层；「先做完不依赖它的部分再问」「范围外的先问」进 Always pause"),
    ("规则 2：讨论里的问题只回答；批准的计划做到底", [("mode", "## Autonomy")],
     "后半并进 Session overrides；「问题就是问题，答完等你说做」「夜里的报告要第二天冷读也懂」pstack 没有，原样留"),
    ("规则 3：该反对就反对，不编造反对", [("mode", "## Autonomy")],
     "并进 No is an acceptable answer；正确性、安全、钱要说清后果并请你确认，加进 Always pause；「你反驳是让我重查证据」留"),
    ("规则 4：证据要能核对", [("mode", "## Writing the reply"), ("principle", "prove-it-works")],
     "标签换成 measured / inferred / guess；「原因是查到的不是猜的」「Half done is not done」「没碰、没查的也要说」留"),
    ("规则 5：讲理由和后果，篇幅按改动大小", [("mode", "## Writing the reply")],
     "并进 Frame impact 和 Terse is not an excuse；「警告、数字、前提最后才删」留"),
    ("规则 6：标准词汇，新术语第一次解释一句", [("mode", "## Writing the reply")], "pstack 没有，写成一行"),
    ("规则 7：不要修辞腔", [("skill", "unslop")], "unslop 规则 32 是同一条，全局层删掉"),
    ("规则 8：引用要锚定，名字照抄原文", [("principle", "anchor-every-reference")], "pstack 没有，成为原则，回复和文档都用"),
    ("规则 9：什么时候用列表和表格", [("mode", "## Writing the reply")], "pstack 没有，写成一行"),
    ("规则 10：先想清楚谁在哪里读", [("principle", "write-for-where-it-is-read"), ("skill", "writing-for-agents")],
     "成为原则；写给 agent 的那部分由 writing-for-agents 展开"),
    ("规则 11：失败了自己重做，只交给你只有你能做的", [("principle", "never-block-on-the-human")],
     "并进这条原则的 Finish what failed；它的索引行在要不要问你的那一刻就会读到"),
    ("规则 12：读够了再下结论，改之前先读", [("principle", "read-before-you-conclude")], "pstack 没有，成为原则"),
    ("规则 13：文件只写现状，不写历史", [("principle", "files-describe-the-present")],
     "成为原则，代码注释也归它管；Comments 一节只写 pstack 那条「只留代码说不出的 why」"),
    ("规则 14：先找现成的，再决定自己写", [("principle", "start-from-what-exists")],
     "pstack 没有，成为原则；索引行的条件就是「提出设计或写不小的代码之前」"),
    ("规则 15：不默认跑全量测试", [("principle", "run-the-smallest-test-set")], "pstack 没有，成为原则"),
    ("结尾：这份文件起作用时是什么样", [("mode", "## Writing the reply")],
     "改成回复的完成判据：你读完不用问「所以呢」，要么决定，要么放下"),
    ("hosts/codex.md：别打断正在干活的子代理", [("mode", "## Subagents")], "并进「派发方对产出负责」一段：等派出的子代理都交回再结束回合（第 5 课）；脚本开的会话不轮询，结束回合等叫醒"),
]

PSTACK_MERGED = [
    ("mode", "Non-negotiables 开头：回复里点名改变了决定的原则，只点读过全文的", [("mode", "## Non-negotiables")], "照搬"),
    ("mode", "Writing the reply：起草时就写干净，一句一个意思", [("mode", "## Writing the reply")], "照搬"),
    ("mode", "Writing the reply：不用长破折号，冒号不当句中连接", [("mode", "## Writing the reply")], "照搬，中文也一样（你已定）"),
    ("mode", "Writing the reply：不编造链接、引用和对话记录", [("mode", "## Writing the reply")], "照搬"),
    ("mode", "每份 playbook 的回复照这一节写，Reply 只写独有内容，附 PR 链接", [("mode", "## Writing the reply")], "照搬"),
    ("mode", "Autonomy：Just do it，更新票、团队消息、跑评测都直接做", [("mode", "## Autonomy")],
     "照搬，并进规则 1：工程决定也直接做，说明理由和放弃的方案"),
    ("mode", "Autonomy：Always pause，force-push、部署、删数据、客户消息", [("mode", "## Autonomy")],
     "和 shared.md 规则 1 的清单合成一份"),
    ("mode", "不给你一个暗号照打，你用自己的话回答", [("mode", "## Autonomy")], "照搬，放在 Always pause「再问你」之后"),
    ("mode", "全权委托时：只归你的决定也先取默认值做下去，事后报告", [("other", "待你定")],
     "和规则 2「只在归你的决定处停下」冲突"),
    ("mode", "Non-negotiables：问之前先分类，跑得出来的事实不拿来问", [("mode", "## Autonomy")],
     "只取跑得出来的事实那一句，并进 Just do it；哪些决定归你由 Always pause 定"),
    ("mode", "Comments：只留代码说不出的 why", [("mode", "## Comments")], "照搬；注释不写历史归 files-describe-the-present"),
    ("playbook", "Investigation：前提错了就反驳", [("mode", "## Autonomy")], "并进规则 3，写进 No is an acceptable answer"),
    ("playbook", "Orchestrate：到你 / 不到你两张清单", [("playbook", "夜里的 playbook")],
     "并进 v2 夜里的机制：到你的那些先写成子票，工作绕开它继续"),
    ("playbook", "Pause safely：写一份离开上下文也能接上的交接说明", [("playbook", "Pause safely"), ("skill", "handoff")],
     "并进 v2 的 handoff：第 4 步照 handoff 写"),
    ("playbook", "Autonomous run：死路要报出来，不放宽完成条件", [("playbook", "夜里的 playbook")], "照搬；夜里的完成条件是票上的 CHECK: 行"),
]


def _src_box(f, kind, x, y, w, lines):
    h = 12 + len(lines) * 16
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>')
    for i, line in enumerate(lines):
        _text(f, x + 10, y + 19 + i * 16, line)
    return h


def _mapping(rows, head):
    f = Fig(head[0], 1000)
    f.note(10, 16, head[1])
    f.note(372, 16, "去哪")
    f.note(626, 16, "怎么采用")
    y = 28
    for kind, src, dests, how in rows:
        src_lines = _wrap(src, 300, 13)
        how_lines = _wrap(how, 360)
        laid, nd = _lay(dests, 372, 240)
        h = max(12 + len(src_lines) * 16, nd * 30 - 4, len(how_lines) * 16 + 6) + 12
        sh = _src_box(f, kind, 10, y + 4, 320, src_lines)
        f.ar([(330, y + 4 + sh / 2), (366, y + 4 + sh / 2)])
        for k, t, cx, row in laid:
            f.chip(k, cx, y + 4 + row * 30, t, mono=False)
        for i, line in enumerate(how_lines):
            f.note(626, y + 20 + i * 16, line)
        y += h
        f.e(f'<line x1="10" y1="{y - 4}" x2="990" y2="{y - 4}" class="rule"/>', False)
    return f, y


def shared_map():
    f, y = _mapping([("config", s, d, h) for s, d, h in SHARED], ("m11", "shared.md 的每一段"))
    return f.svg(y + 4, "shared.md 的每一段和 hosts/codex.md 去哪、怎么采用：读者和只归主人的决定留在全局层；规则 1、2、3 进 Autonomy；规则 11 并进 never-block-on-the-human；规则 4、5、6、9 和结尾进 Writing the reply；规则 7 交给 unslop；规则 8、10、12、13、14、15 各成一条新原则；脚本起的会话那段成为 Autonomy 的 Unattended 一段；codex.md 那句并进 Subagents。")


def pstack_map():
    f, y = _mapping(PSTACK_MERGED, ("m12", "pstack 的沟通规则，搬进来的"))
    return f.svg(y + 4, "pstack 的沟通规则里搬进 v3 的各条去哪：回复点名原则进 Non-negotiables；起草就写干净、一句一个意思、标点、不编造链接、每份 playbook 的 Reply 分工进 Writing the reply；Just do it、Always pause、不给暗号进 Autonomy，并进 shared.md 规则 1、3；问之前先分类只取跑得出来的事实那一句；Comments、Investigation 的反驳、Orchestrate 的两张清单、Pause safely、Autonomous run 的不放宽完成条件各有去处；全权委托时取默认值那句和规则 2 冲突，待主人定。")


# ---- the merged design, drawn inside the skeleton of mmw-mode/SKILL.md ----

X0 = 206          # left edge of the flow area inside a section band
COMP_X = 676      # where the component column starts in a branching band


def _text(f, x, y, t, cls=""):
    c = f' class="{cls}"' if cls else ""
    f.e(f'<text x="{x}" y="{y:.1f}"{c}>{html.escape(t)}</text>')


def _band_head(f, y, name, when, h):
    f.e(f'<line x1="24" y1="{y + h}" x2="976" y2="{y + h}" class="rule"/>', False)
    _text(f, 34, y + 24, name, "m")
    for i, line in enumerate(when):
        _text(f, 34, y + 44 + i * 16, line, "s")


def _branch(f, y, dia_lines, rows, rh=36):
    """A diamond whose exits fan out to one row each: condition text, arrow, component chip and note."""
    n = len(rows)
    h = n * rh
    mid = y + h / 2
    f.dia(X0 + 82, mid, 82, 30, dia_lines)
    trunk = X0 + 184
    f.ar([(X0 + 164, mid), (trunk, mid)], head=False)
    f.ar([(trunk, y + rh / 2), (trunk, y + h - rh / 2)], head=False)
    for i, (cond, kind, label, note) in enumerate(rows):
        yy = y + i * rh + rh / 2
        f.ar([(trunk, yy), (trunk + 12, yy)])
        _text(f, trunk + 16, yy + 4.5, cond)
        f.ar([(COMP_X - 22, yy), (COMP_X - 3, yy)])
        f.chip(kind, COMP_X, yy - 12, label, note, mono=False)
    return h


def design():
    f = Fig("m9", 1000)
    # before the mode: the session and the global layer
    _, r = f.pill(0, 14, "一个会话开始", left=14)
    f.ar([(r, 31), (r + 24, 31)])
    f.box("config", r + 24, 8, 300, 46, "~/.claude/CLAUDE.md，宿主自动载入", ["读者是谁；哪些决定只归你"], mono=False)
    bx = r + 324
    f.ar([(bx, 31), (bx + 24, 31)])
    dcx = bx + 24 + 150
    f.dia(dcx, 31, 150, 28, ["钩子、你输入 /mmw-mode，", "或 start prompt 第一句？"])
    f.ar([(dcx + 150, 31), (dcx + 178, 31)], "否", dcx + 154, 24)
    _text(f, dcx + 182, 35, "只照全局层工作", "s")
    f.ar([(dcx, 59), (dcx, 92)], "是：载入全文", dcx + 8, 80)

    top = 94
    y = top + 30
    # frontmatter
    _band_head(f, y, "frontmatter", ["决定什么时候载入"], 48)
    _text(f, X0, y + 22, "disable-model-invocation: true", "m")
    _text(f, X0, y + 40, "模型不会自己载入它：有 .mmw/ 的仓库里钩子载入，没有钩子的宿主你输入 /mmw-mode，脚本开的会话由 start prompt 第一句载入", "s")
    y += 48

    # Non-negotiables
    rows = [
        ("要写任何文字", "skill", "unslop", "①⑨"),
        ("写给人读的文档", "skill", "technical-writing", "⑨"),
        ("写给 agent 读的文字", "skill", "writing-for-agents", "⑤⑨　提示词、任务说明"),
    ]
    h = _branch(f, y + 10, ["出现了", "哪种情况？"], rows) + 20
    _band_head(f, y, "## Non-negotiables", ["任务中任何时刻，", "情况一出现就用"], h)
    y += h

    # Principles
    names = ["never-block-on-the-human ②", "prove-it-works ①④",
             "anchor-every-reference ①⑨", "write-for-where-it-is-read ⑤⑨", "read-before-you-conclude ①",
             "files-describe-the-present ⑨", "start-from-what-exists", "run-the-smallest-test-set ①"]
    laid, nrows = _lay([("principle", n) for n in names], X0 + 384, 976 - X0 - 384)
    h = max(136, 34 + nrows * 30 + 14)
    _band_head(f, y, "## Principles", ["载入时读索引；", "条件出现时读全文"], h)
    f.box("mode", X0, y + 34, 150, 52, "索引行一直在", ["条件 + 一句规则"], mono=False)
    f.ar([(X0 + 150, y + 60), (X0 + 172, y + 60)])
    f.dia(X0 + 262, y + 60, 90, 30, ["某条原则的", "条件出现了？"])
    f.ar([(X0 + 262, y + 90), (X0 + 262, y + 112)])
    _text(f, X0 + 270, y + 106, "否：只留着索引行", "s")
    f.ar([(X0 + 352, y + 60), (X0 + 380, y + 60)], "是", X0 + 356, y + 52)
    _text(f, X0 + 384, y + 24, "读这条原则的 SKILL.md 全文：", "s")
    for k, t, cx, row in laid:
        f.chip(k, cx, y + 34 + row * 30, t, mono=False)
    y += h

    # Autonomy
    rows = [
        ("跑一下就能看到的事实", "mode", "自己跑出来，不拿来问你", None),
        ("工程上的决定，可撤回", "mode", "直接做，事后说明理由和放弃的方案", None),
        ("只有你能定的（见下行）", "mode", "先做完不依赖它的部分，再带选项和建议问你", None),
        ("你说「去睡了」，或计划已批准", "mode", "一直做到底，不中途问「要继续吗」", None),
        ("你问它的意见", "mode", "给真实判断，有问题就说并给替代方案", None),
        ("脚本起的会话，没人可问", "mode", "Unattended：取最可能的选项，记下来，接着做", None),
    ]
    h = _branch(f, y + 10, ["这件事", "归谁定？"], rows) + 40
    _band_head(f, y, "## Autonomy", ["要做一件事，", "或想问你的时候"], h)
    _text(f, X0, y + h - 12, "只有你能定的：客户看到什么、钱怎么走、范围和先后、什么公开出去、难以撤回的事", "s")
    y += h

    # Subagents
    h = 78
    _band_head(f, y, "## Subagents", ["开子代理之前"], h)
    f.box("mode", X0, y + 16, 600, 46, "技能派出子代理的通用规则（第 5 课）⑤⑥", ["宿主自带的通用子代理、不指定模型；brief 写明交回什么、多长；派发方对产出负责"], mono=False)
    y += h

    # Writing the reply
    h = 74
    _band_head(f, y, "## Writing the reply", ["写每一条回复时"], h)
    f.box("mode", X0, y + 14, 440, 46, "读者是谁、一句一个意思、篇幅按改动大小、证据三标签 ①④", ["不用长破折号和句中冒号；不编造链接；读完不用问「所以呢」"], mono=False)
    f.ar([(X0 + 440, y + 37), (X0 + 464, y + 37)])
    f.box("playbook", X0 + 464, y + 14, 300, 46, "加上这份 playbook 的 **Reply:**", ["只写这种任务独有的内容"], mono=False)
    y += h

    # Comments
    h = 64
    _band_head(f, y, "## Comments", ["写代码注释时"], h)
    f.box("mode", X0, y + 12, 520, 40, "只留代码说不出的 why；测试脚本不写分阶段的注释 ⑨", [], mono=False)
    y += h

    # Playbooks
    rows = [
        ("要暂停，或上下文快满", "playbook", "Pause safely", "⑧　第 4 步照 handoff 写交接说明"),
        ("写或改技能、playbook、原则、mode", "playbook", "Authoring or modifying a skill", "⑨"),
        ("审一套技能", "playbook", "Review the skill set", "⑨"),
        ("跑一夜的票，或修一个 bug", "playbook", "Run a night / Bug fix", "⑤⑦"),
        ("start prompt 点名的", "playbook", "Work / Review a ticket", "⑥"),
        ("没有一份合适", "skill", "figure-it-out", "为这一次设计流程"),
    ]
    h = _branch(f, y + 10, ["匹配哪一行", "路由？"], rows) + 56
    _band_head(f, y, "## Playbooks", ["任务开始时选路"], h)
    yy = y + 10 + len(rows) * 36 + 18
    _text(f, X0 + 200, yy + 4.5, "这两份都要读的规则")
    f.ar([(COMP_X - 22, yy), (COMP_X - 3, yy)])
    rx = f.chip("reference", COMP_X, yy - 12, "references/skill-set-rules.md", mono=False)
    for i, label in [(1, "Authoring or modifying a skill"), (2, "Review the skill set")]:
        ya = y + 10 + i * 36 + 18
        xr = COMP_X + tw(label, 11.5, False) + 24 + 30
        f.e(f'<path class="att" d="M{xr:.1f},{ya} H954 V{yy} H{rx + 4:.1f}"/>', False)
    y += h

    f.frame("mode", 10, top, 980, y - top + 6, "mmw-mode/SKILL.md", [])
    f.back.insert(0, f.back.pop())  # the frame's fill goes under the band lines drawn before it

    # outside the mode
    y += 24
    rows = [
        ("你说没听懂", "other", "你输入 /wait-what", "skill", "wait-what", "⑩　加 visual：diagram-design 画一页图"),
        ("要把一个计划问清楚", "other", "你输入 /grill-me", "skill", "grilling", "⑪　卡在别人知道的事：to-questionnaire"),
        ("要学一个主题", "other", "你输入 /teach", "skill", "teach", "⑫"),
        ("夜里 worker 想弹出提问", "script", "tool-guard.py 拦下", "skill", "verify-ticket 的子票", "⑦　decision 或 contract"),
        ("worker 关票", "script", "verify-ticket.py --closeout", "playbook", "Work a ticket 的收尾评论", "⑥　格式不对就拒绝"),
    ]
    zh = 40 + len(rows) * 36
    f.zone(10, y, 980, zh, "不经过 mode：你直接调用的技能，和脚本强制的规则")
    for i, (cond, rk, route, kk, comp, note) in enumerate(rows):
        yy = y + 44 + i * 36
        _text(f, 26, yy + 4.5, cond)
        f.ar([(240, yy), (262, yy)])
        f.chip(rk, 266, yy - 12, route, mono=False)
        f.ar([(COMP_X - 22, yy), (COMP_X - 3, yy)])
        f.chip(kk, COMP_X, yy - 12, comp, note, mono=False)
    y += zh
    return f.svg(y + 8, "合并后的设计，画在 mmw-mode/SKILL.md 的骨架里：会话开始时宿主载入全局层，钩子、你输入 /mmw-mode 或 start prompt 第一句才载入 mode；Non-negotiables 在写文字时按情况调用 unslop、technical-writing、writing-for-agents，其余的触发就是原则的索引行；Principles 载入时读索引，条件出现读原则全文；Autonomy 按归谁定分六种做法，跑得出来的事实自己跑，脚本起的会话按 Unattended 一段做；Subagents 写技能派出子代理的通用规则；Writing the reply 与 Comments 在写的时候用；Playbooks 在任务开始时按路由选 Pause safely、Authoring or modifying a skill、Review the skill set、四份角色 playbook 或 figure-it-out，两份写技能和审技能的 playbook 共用 references/skill-set-rules.md。mode 之外：你直接调用 wait-what（visual 交给 diagram-design 画）、grilling、teach；tool-guard.py 和 verify-ticket.py 在夜里强制两条规则。")


FIGS = {"l4-moments": moments, "l4-coverage": coverage, "l4-choices": choices,
        "l4-shared-map": shared_map, "l4-pstack-map": pstack_map, "l4-design": design}

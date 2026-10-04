"""Figure of lesson 0007: how the Investigation playbook, the how and why skills and the other playbooks are wired."""
import html
from kit import Fig, tw


def _t(f, x, y, t, cls="s", anchor="start"):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    f.e(f'<text x="{x}" y="{y:.1f}" class="{cls}"{a}>{html.escape(t)}</text>')


def _chip(f, kind, x, y, label, mono=True, dashed=False):
    """A chip with room for a monospace font wider than JetBrains Mono; returns its right edge."""
    w = tw(label, 11.5, mono) * (1.1 if mono else 1.0) + (18 if mono else 24)
    tc = "m" if mono else "s"
    dash = ' style="stroke-dasharray:6 3"' if dashed else ""
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w:.1f}" height="24" rx="4"{dash}/>'
        f'<text x="{x+9}" y="{y+16.5}" class="{tc}">{html.escape(label)}</text></g>')
    return x + w


def _box_lines(f, kind, x, y, w, title, lines, mono_title=True):
    h = 30 + len(lines) * 17
    f.e(f'<g class="k-{kind}"><rect class="box" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/></g>', False)
    _t(f, x + 12, y + 20, title, "m" if mono_title else "h")
    for i, line in enumerate(lines):
        _t(f, x + 12, y + 39 + i * 17, line)
    return h


def wiring():
    f = Fig("m71", 1000)
    _t(f, 10, 20, "从你的一个问题到交回的答案", "h")

    # mmw-mode
    f.zone(4, 34, 290, 196, "mmw-mode/SKILL.md")
    _box_lines(f, "mode", 16, 64, 266, "## Non-negotiables", ["不小的改动、架构决定、「我们确定吗」", "→ how，不论在哪份 playbook 里"])
    _box_lines(f, "mode", 16, 148, 266, "## Playbooks", ["Investigation 的路由行：只读的问题，", "怎么工作、为什么这样、确定吗、选哪个"])

    # the playbook
    hp = _box_lines(f, "playbook", 330, 64, 300, "playbooks/investigation.md",
                    ["1  走 how；问的是动机，也走 why",
                     "2  写成 how 的五节，或带取舍表的建议",
                     "3  回复过 unslop",
                     "不提交，不开票",
                     "Reply：照 Writing the reply 写给你，",
                     "讲它做什么、为什么、对产品意味着什么"])
    f.ar([(282, 180), (326, 180)])

    # the skills it routes through
    h1 = _box_lines(f, "skill", 680, 40, 310, "how", ["简单的问题：1 个 explainer 边查边讲", "复杂的问题：2 到 4 个 explorer 分头查，", "再 1 个 explainer 汇总"])
    h2 = _box_lines(f, "skill", 680, 40 + h1 + 12, 310, "why", ["先钉住代码、提交和 PR", "每类证据来源 1 个 investigator，", "再 1 个 synthesizer 分清查到和推断"])
    uy = 40 + h1 + 12 + h2 + 12
    _chip(f, "skill", 680, uy, "unslop")
    f.ar([(630, 92), (676, 70)])
    f.ar([(630, 112), (676, 40 + h1 + 12 + 40)])
    f.ar([(630, 132), (676, uy + 12)])
    f.ar([(282, 96), (306, 96), (306, 28), (835, 28), (835, 37)])
    _t(f, 560, uy + 46, "每个子代理都是宿主的通用子代理，不点模型（mode 的 ## Subagents）")
    _t(f, 560, uy + 63, "how 的子代理在提示词结尾写明只读；why 的不进只读模式，以免没有 MCP")

    # hand back
    by = uy + 80
    f.zone(4, by, 992, 72, "要改代码时：不改，交回你，再转一份 playbook（虚线的三份还没写，第 8、9、11 课写）")
    x = 16
    for name in ("Bug fix", "Make a small change", "Write a spec"):
        x = _chip(f, "playbook", x, by + 34, name, mono=False, dashed=True) + 10
    f.ar([(480, 64 + hp), (480, by)])

    # other users
    cy = by + 72 + 12
    rows = [
        ("Bug fix 诊断那一步", "how 看出问题的那一块，why 查是哪次改动引入的"),
        ("Make a small change 第 1 步", "how 看要改的那一块"),
        ("Write a spec、Chart a map", "决定碰到现有代码时 how，要知道当初为什么时 why"),
        ("Work a ticket（夜里的 worker）", "不接：票的 ## Read first 已经列好要读的"),
    ]
    f.zone(4, cy, 992, 36 + len(rows) * 30 + 4, "其他用 how 和 why 的步骤：写到那一份时照第 6 课第 5 节的接线表加")
    for i, (who, what) in enumerate(rows):
        y = cy + 32 + i * 30
        _chip(f, "playbook", 16, y, who, mono=False, dashed=i < 3)
        _t(f, 300, y + 16.5, what)
    H = cy + 36 + len(rows) * 30 + 12
    return f.svg(H, "从你的一个问题到交回的答案。mmw-mode 的 ## Playbooks 有一行路由，把只读的问题（怎么工作、为什么这样、确定吗、选哪个）送进 playbooks/investigation.md；## Non-negotiables 有一行触发，不小的改动、架构决定和「我们确定吗」在任何 playbook 里都用 how。Investigation 三步：走 how，问动机时也走 why；写成 how 的五节或带取舍表的建议；回复过 unslop。不提交、不开票，回复照 Writing the reply 写给你。how 简单问题开 1 个 explainer，复杂问题开 2 到 4 个 explorer 再开 1 个 explainer 汇总；why 先钉住代码、提交和 PR，每类证据来源开 1 个 investigator，再开 1 个 synthesizer。每个子代理都是宿主的通用子代理，不点模型。要改代码时交回你，转 Bug fix、Make a small change 或 Write a spec，这三份还没写。其他用 how 和 why 的步骤：Bug fix 诊断、Make a small change 第 1 步、Write a spec 和 Chart a map；夜里的 worker 不接。")


FIGS = {"l7-wiring": wiring}

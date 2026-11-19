"""Figures of lesson 0017: what can change the MMW this machine runs; the three routes by which a session
gets the mode."""
from kit import Fig, tbox as _box


def guarantee():
    f = Fig("m171", 1000)
    CX = 500

    f.pill(CX, 10, "你在已安装的 checkout 里，显式跑一次 install.sh")
    f.ar([(CX, 44), (CX, 58)])
    _box(f, "config", 10, 60, 980, "九样东西全部指向这一个 checkout",
         ["技能软链；hook 命令（走 ~/.agents/skills 下的技能软链）；提示词软链和生成的 AGENTS.md；",
          "两个 launchd 任务的 plist（写的是这个 checkout 的路径）；Paseo、Orca、Nowledge Mem、Cursor 的设置"])
    f.ar([(CX, 124), (CX, 140)])
    _box(f, "config", 10, 142, 980, "~/.mmw/installed-root 记下这个 checkout",
         ["今天记的是 .worktrees/mmw-installed/mmw-v2；在那里跑 mmw-v3/install.sh 之后，记的是 …/mmw-v3"])

    f.zone(10, 208, 980, 268, "其他做法都换不掉正在跑的那一份")
    rows = [
        (238, "script", "从别的 checkout 跑 install.sh --check", [],
         "转交 installed-root 那一份的 install.sh --check", ["只核对，不写任何东西"]),
        (295, "script", "dispatch.sh check（每晚开夜前）", [],
         "只跑 install.sh --check，缺的印成警告", ["从不自己跑 install.sh（第 19 课改的）"]),
        (352, "other", "主工作区、票的 worktree 改了技能", ["或 install.sh，合进哪个分支都一样"],
         "没有一样已装的东西指向它们", ["所以不生效，直到你显式安装"]),
        (409, "other", "直接跑一份不是已安装的 dispatch.sh", [],
         "只有这一条靠规矩，不靠机制", ["根 AGENTS.md 的 Self-hosting boundary 禁止"]),
    ]
    for y, kind, left, left_lines, right, right_lines in rows:
        h = _box(f, kind, 24, y, 440, left, left_lines)
        f.ar([(466, y + h / 2), (508, y + h / 2)])
        _box(f, "other", 510, y, 466, right, right_lines, dashed=(y == 409))
    return f.svg(488, ARIA_GUARANTEE)


ARIA_GUARANTEE = (
    "第 17 课图 1，什么能改变这台机器正在跑的 MMW。只有一条：你在已安装的 checkout 里显式跑一次 install.sh。"
    "它装的九样东西全部指向这一个 checkout：技能软链；hook 命令走 ~/.agents/skills 下的技能软链；提示词软链和生成的 AGENTS.md；"
    "两个 launchd 任务的 plist 写的是这个 checkout 的路径；以及 Paseo、Orca、Nowledge Mem、Cursor 的设置。"
    "然后 ~/.mmw/installed-root 记下这个 checkout，今天记的是 .worktrees/mmw-installed/mmw-v2，在那里跑 mmw-v3/install.sh 之后记的是 mmw-v3。"
    "其他做法都换不掉正在跑的那一份：从别的 checkout 跑 install.sh --check，会转交 installed-root 那一份的 --check，只核对不写；"
    "dispatch.sh check 每晚开夜前跑，只跑 install.sh --check，缺的印成警告，从不自己跑 install.sh，这是第 19 课改的；"
    "主工作区或票的 worktree 改了技能或 install.sh，合进哪个分支都一样，没有一样已装的东西指向它们，所以不生效；"
    "直接跑一份不是已安装的 dispatch.sh，这一条靠规矩不靠机制，根 AGENTS.md 的 Self-hosting boundary 禁止。")


def mode():
    f = Fig("m172", 1000)
    rows = [
        (10, "other", "你在有 .mmw/ 的仓库里开会话", ["Claude Code 或 Codex"],
         "script", "mode-hook.py，挂在 SessionStart 上", ["往上下文加一句：先完整读 mmw-mode 的", "SKILL.md，后面跟它在本机的路径"]),
        (90, "script", "dispatch.sh start", ["开 worker 或 reviewer"],
         "other", "start prompt 的第一句", ["先完整读 mmw-mode 的 SKILL.md，", "后面跟它在本机的路径，再点名 playbook"]),
        (170, "other", "你输入 /mmw-mode", ["Grok、Cursor，或没有 .mmw/ 的仓库"],
         "other", "宿主载入这个技能", ["人输入的名字，不受", "disable-model-invocation 限制"]),
    ]
    for y, lk, lt, ll, rk, rt, rl in rows:
        _box(f, lk, 10, y, 300, lt, ll)
        f.ar([(312, y + 23), (348, y + 23)])
        h = _box(f, rk, 350, y, 340, rt, rl)
        f.ar([(692, y + h / 2), (708, y + h / 2), (708, 132), (724, 132)])
    f.pill(0, 115, "mode 留在上下文里，直到会话结束", left=726)

    _box(f, "other", 10, 256, 980, "为什么三条路都说「读这个文件」，不说 Use the mmw-mode skill.",
         ["mmw-mode 的 frontmatter 有 disable-model-invocation: true：只有人能开它。",
          "Claude Code 的文档说，这样的技能模型调用不了，它的 description 也不在上下文里；模型硬调，会被拦下。",
          "所以第 5 课定的那一句在 Claude Code 上开不了 mode。pstack 的 poteto-agent 也是这样写：读 poteto-mode 的 SKILL.md。"],
         dashed=True)
    return f.svg(348, ARIA_MODE)


ARIA_MODE = (
    "第 17 课图 2，一个会话怎样拿到 mmw-mode，三条路。第一条：你在有 .mmw/ 的仓库里开 Claude Code 或 Codex 的会话，"
    "挂在 SessionStart 上的 mode-hook.py 往上下文加一句，先完整读 mmw-mode 的 SKILL.md，后面跟它在本机的路径。"
    "第二条：dispatch.sh start 开 worker 或 reviewer，start prompt 的第一句是先完整读 mmw-mode 的 SKILL.md，后面跟路径，再点名 playbook。"
    "第三条：你输入 /mmw-mode，用于 Grok、Cursor，或没有 .mmw/ 的仓库；人输入的名字不受 disable-model-invocation 限制，宿主载入这个技能。"
    "三条都到同一处：mode 留在上下文里，直到会话结束。"
    "下面一格解释为什么三条路都说读这个文件而不说 Use the mmw-mode skill.：mmw-mode 的 frontmatter 有 disable-model-invocation: true，只有人能开它；"
    "Claude Code 的文档说这样的技能模型调用不了，description 也不在上下文里，模型硬调会被拦下；所以第 5 课定的那一句在 Claude Code 上开不了 mode。"
    "pstack 的 poteto-agent 也是这样写：读 poteto-mode 的 SKILL.md。")


FIGS = {"l17-guarantee": guarantee, "l17-mode": mode}

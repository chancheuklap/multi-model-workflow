"""Figures of lesson 0019: where each of the owner's six decisions landed; how much code each part
of the night machine and the install entry lost."""
from kit import Fig, tbox as _box, txt as _txt


def decisions():
    f = Fig("m191", 1000)
    rows = [
        ("1　Paseo 和 Herdr：支持", "script", "两个 runner 的适配器原样留着，一行没删",
         ["选 runner 时用不到的层删了：票上指定 runner，", "以及没有适配器的 tmux、lody 等运行时列表"]),
        ("2　runner 的 auto：能用就要", "script", "auto 读当前会话所在的 runner：Herdr，再 Orca",
         ["先看 MMW_RUNNER，再看 models.json 的 runner；都不是就 orca。", "10 个测试，其中一个在 auto 不再读环境时失败"]),
        ("3　Pi：不要", "config", "hosts.json、models.py、两个守卫和看板里都没有 Pi",
         ["install.sh 摘掉 v2 给 Pi 装的两个扩展和生成的 AGENTS.md；", "宿主剩四个：Claude Code、Codex、Grok、Cursor（ADR 0032）"]),
        ("4　v2 留下的票：改票，不兼容", "script", "读事件不留回退链，也没有为旧格式写的分支",
         ["只读扫了两个仓库开着的 56 张票：带事件的 3 张 v3 都读得懂，", "一张都不用改（ADR 0034）"]),
        ("5　自动修补：删掉", "script", "dispatch.sh check 只跑 install.sh --check",
         ["缺什么就印成警告，从不自己跑 install.sh；", "本机装哪一份、什么时候装，只由你决定"]),
        ("6　根文档和 ADR：改成 v3", "other", "AGENTS.md、CONTEXT-MAP.md、CODING_STANDARDS.md、TESTING.md",
         ["六个 context 和 how-it-works.md；新写 ADR 0032、0033、0034；", "每个词条的出处都指向 v3 里真写着它的文件"]),
    ]
    y = 10
    for left, kind, title, lines in rows:
        h = 30 + len(lines) * 17
        _box(f, "other", 10, y + (h - 30) / 2, 300, left, [])
        f.ar([(312, y + h / 2), (346, y + h / 2)], cls="human")
        _box(f, kind, 348, y, 642, title, lines)
        y += h + 12
    return f.svg(y - 2, ARIA_DECISIONS)


ARIA_DECISIONS = (
    "第 19 课图 1，你定的六件各落在哪。"
    "1，Paseo 和 Herdr 支持：两个 runner 的适配器原样留着，选 runner 时用不到的层删了，就是票上指定 runner 和没有适配器的运行时列表。"
    "2，runner 的 auto 能用就要：先看 MMW_RUNNER，再看 models.json 的 runner，auto 或都没写时读当前会话所在的 runner，Herdr 再 Orca，都不是就 orca；10 个测试，其中一个在 auto 不再读环境时失败。"
    "3，不要 Pi：hosts.json、models.py、两个守卫和看板里都没有 Pi，install.sh 摘掉 v2 给 Pi 装的两个扩展和生成的 AGENTS.md，宿主剩四个。"
    "4，v2 留下的票改票不兼容：读事件不留回退链，也没有为旧格式写的分支；只读扫了两个仓库开着的 56 张票，带事件的 3 张 v3 都读得懂，一张都不用改。"
    "5，删掉自动修补：dispatch.sh check 只跑 install.sh --check，缺什么印成警告，从不自己跑 install.sh。"
    "6，根文档和 ADR 改成 v3：AGENTS.md、CONTEXT-MAP.md、CODING_STANDARDS.md、TESTING.md，六个 context 和 how-it-works.md，新写 ADR 0032、0033、0034。")


SIZES = [
    ("dispatch.sh", "script", 4699, 4338),
    ("relay.py", "script", 1934, 1721),
    ("install.sh", "script", 1879, 1240),
    ("gate-check（两个文件）", "script", 1766, 753),
    ("models.py", "script", 1297, 1175),
    ("watchdog.py", "script", 1017, 884),
    ("lease.py", "script", 746, 637),
    ("mmw-mode/SKILL.md", "mode", 291, 139),
]


def sizes():
    f = Fig("m192", 1000)
    X0, SPAN, TOP = 230, 600, 34
    scale = SPAN / 5000
    for tick in range(0, 5001, 1000):
        x = X0 + tick * scale
        f.e(f'<line class="rule" x1="{x:.1f}" y1="{TOP - 6}" x2="{x:.1f}" y2="{TOP + len(SIZES) * 40}"/>', False)
        f.note(x, TOP - 12, f"{tick:,}", anchor="middle")
    for i, (name, kind, before, after) in enumerate(SIZES):
        y = TOP + i * 40 + 6
        _txt(f, X0 - 12, y + 18, name, "m", anchor="end", room=X0 - 20)
        f.e(f'<rect class="zone" x="{X0}" y="{y}" width="{before * scale:.1f}" height="12" rx="2"/>', False)
        f.e(f'<g class="k-{kind}"><rect class="box" x="{X0}" y="{y + 14}" width="{after * scale:.1f}" height="12" rx="2"/></g>', False)
        f.note(X0 + before * scale + 8, y + 22, f"{before:,} → {after:,}")
    bottom = TOP + len(SIZES) * 40 + 22
    f.note(10, bottom, "全部脚本（技能、install.sh、看板）41,411 → 38,306 行；测试 43,050 → 41,396 行。")
    return f.svg(bottom + 12, ARIA_SIZES)


ARIA_SIZES = (
    "第 19 课图 2，这一批改动前后各部分的行数，同一把尺子，刻度 0 到 5000。"
    + "；".join(f"{n} {b} 行变 {a} 行" for n, _, b, a in SIZES)
    + "。全部脚本从 41,411 行到 38,306 行，测试从 43,050 行到 41,396 行。")


FIGS = {"l19-decisions": decisions, "l19-sizes": sizes}

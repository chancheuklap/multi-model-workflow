"""Figures of lesson 0002: what creates each kind of component in pstack, and what moving text by type broke in MMW."""
import html
from kit import Fig


def creation_paths():
    f = Fig("m3", 1000)
    f.note(10, 16, "发生了什么")
    f.note(330, 16, "pstack 里由谁处理")
    f.note(640, 16, "产出什么")
    rows = [
        (["你要写或改一个 SKILL.md"], ("playbook", "Authoring or modifying a skill", ["交给 Cursor 内置的 create-skill"]),
         [("skill", "一份 SKILL.md", "技能、原则、mode 都是 SKILL.md")]),
        (["一次长任务做完，学到了东西", "你输入 /reflect"], ("skill", "reflect", ["三个审阅者 + 一个汇总者"]),
         [("skill", "默认：改一个已有的技能", None), ("other", "能用检查强制的：进 Backlog", None)]),
        (["同一类错误被纠正了两次", "你输入 /correct"], ("skill", "correct", ["从最高的一层修起"]),
         [("script", "架构 > 类型 > lint / CI > 测试", None), ("other", "最后才写文字规则，只写要判断的", None)]),
        (["同一句指令你写了第二遍"], ("principle", "Encode Lessons in Structure", []),
         [("script", "lint、metadata flag、运行时检查、脚本", None), ("other", "要判断的：那句写醒目，配失败例子", None)]),
        (["要做的工作不是一眼能做完的"], ("principle", "Build the Lever", []),
         [("script", "脚本、codemod、生成器、可重跑的检查", None), ("skill", "分给子代理时：一份它们都读的技能", None)]),
        (["想让 agent 按你的方式工作", "你输入 /automate-me"], ("skill", "automate-me", ["从你的聊天记录里找重复的偏好"]),
         [("mode", "<你的名字>-mode 技能", "只写你有明确、非默认规则的节")]),
        (["没有一份 playbook 适合这个任务"], ("skill", "figure-it-out", ["先设计流程，再动手"]),
         [("playbook", "这一次用的 playbook", "写进 todolist 和决策日志，不存成文件")]),
        (["选每个角色用哪个模型", "你输入 /setup-pstack"], ("skill", "setup-pstack", []),
         [("config", "~/.cursor/rules/pstack-models.mdc", "技能各自带默认值；mode 里只留一句指向")]),
    ]
    y = 30
    RH = 80
    for trig, (ck, ct, csub), outs in rows:
        cy = y + RH / 2 - 6
        # trigger
        f.e(f'<rect class="pill" x="10" y="{cy-20}" width="290" height="40" rx="20"/>')
        for i, t in enumerate(trig):
            f.e(f'<text x="155" y="{cy + 4.5 - (len(trig)-1)*8 + i*16:.1f}" text-anchor="middle" class="{"" if i == 0 else "s"}">{html.escape(t)}</text>')
        f.ar([(300, cy), (330, cy)])
        f.box(ck, 330, cy - 24, 270, 48, ct, csub, mono=False)
        if len(outs) == 1:
            k, t, sub = outs[0]
            f.box(k, 640, cy - 24, 350, 48, t, [sub] if sub else [], mono=t.startswith("~"))
            f.ar([(600, cy), (638, cy)])
        else:
            for j, (k, t, sub) in enumerate(outs):
                oy = cy - 34 + j * 36
                f.box(k, 640, oy, 350, 32, t, [])
                f.ar([(600, cy), (620, cy), (620, oy + 16), (638, oy + 16)])
        y += RH
    return f.svg(y + 6, "pstack 里八种情况分别由谁处理、产出什么：写技能走 Authoring 那份 playbook；学到东西用 reflect，默认改已有技能；反复犯的错用 correct，从架构修起，文字规则最后；写第二遍的指令改成检查或脚本；不平凡的工作先做工具；个人风格用 automate-me 生成 mode；没有合适的 playbook 用 figure-it-out 现场设计；选模型用 setup-pstack 写出 rule。")


def move_defects():
    W, H = 1000, 250
    rows = [
        ("同一个情况，两处给出不同做法", 12, "#880：#874、#875、#877 和另外 9 处"),
        ("同一句规则或事实写了两遍", 13, "#884：B2 那一夜已修 13 张子票，还剩 13 处"),
        ("引用一个已经搬走或改名的东西", 5, "#885"),
        ("能力技能知道是谁在调用它", 1, "#889"),
    ]
    x0, scale = 330, 22
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="第一次迁移按类型搬家之后登记的缺陷：两处做法不同 12 处，同一句写两遍还剩 13 处，引用已搬走的东西 5 处，能力技能知道调用方 1 处。">']
    out.append(f'<text x="{x0}" y="20" class="s">每一格 = 1 处登记的缺陷（截至 2026-10-04，按 GitHub issue 计）</text>')
    for i, (label, n, src) in enumerate(rows):
        y = 40 + i * 50
        out.append(f'<text x="{x0-12}" y="{y+18}" text-anchor="end">{html.escape(label)}</text>')
        for k in range(n):
            out.append(f'<g class="k-other"><rect class="box" x="{x0 + k*scale}" y="{y+4}" width="{scale-4}" height="20" rx="2"/></g>')
        out.append(f'<text x="{x0 + n*scale + 8}" y="{y+18}" class="h">{n}</text>')
        out.append(f'<text x="{x0}" y="{y+40}" class="s">{html.escape(src)}</text>')
    out.append('</svg>')
    return ''.join(out)


FIGS = {"l2-creation": creation_paths, "l2-defects": move_defects}

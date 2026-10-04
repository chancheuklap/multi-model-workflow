"""Figures of lesson 0001: what pstack contains, and when each part is read during one task."""
from kit import Fig


def inventory():
    f = Fig("m1", 1000)
    # the plugin
    f.zone(10, 10, 640, 572, "pstack 插件 · cursor/plugins 仓库的 pstack/ 目录")
    f.box("other", 26, 40, 608, 46, ".cursor-plugin/plugin.json", ["插件清单：登记 skills/ 和 agents/ 两个目录；version 0.15.9"], mono=True)
    f.zone(26, 100, 608, 316, "skills/ · 50 个技能目录，每个一份 SKILL.md")
    f.frame("mode", 40, 130, 284, 272, "poteto-mode/", ["mode 技能，1 个", "SKILL.md 2,971 词：规则与路由"])
    f.chip("playbook", 54, 194, "playbooks/", "23 份，一种任务一份")
    f.chip("reference", 54, 228, "references/", "1 份：bugbot-triage.md")
    f.chip("script", 54, 262, "scripts/", "4 组：")
    f.note(54, 304, "watch-pr、orch、check-plan.mjs、")
    f.note(54, 320, "worktree-audit.sh")
    f.note(54, 356, "playbook 不是技能：没有 frontmatter，")
    f.note(54, 374, "不能用 /名字 调用，只由 mode 打开")
    f.box("principle", 338, 130, 282, 76, "principle-*/  × 24", ["每条原则一个技能，只有一份 SKILL.md", "126–773 词"], mono=True)
    f.frame("skill", 338, 220, 282, 182, "其余 25 个技能", ["how、why、architect、arena、swarm、", "interrogate、figure-it-out、tdd、", "unslop、setup-pstack……"], mono=False)
    f.chip("reference", 352, 300, "references/", "给子代理的提示词模板等")
    f.chip("script", 352, 334, "scripts/", "例：show-me-your-work 的 log.sh")
    f.note(352, 382, "都可选：8 个技能带 references/，1 个带 scripts/")
    f.zone(26, 430, 608, 74, "agents/ · 2 个子代理定义")
    x = f.chip("agent", 40, 462, "poteto-agent.md", None)
    f.chip("agent", x + 14, 462, "comment-sicko.md", "Comment Sicko")
    f.box("other", 26, 518, 196, 52, "docs/guide/", ["给人读的指南，10 章"], mono=True)
    f.box("other", 232, 518, 160, 52, "README.md", ["给人读的总览"], mono=True)
    f.box("other", 402, 518, 232, 52, "automations/benny/", ["休眠的自动化包，不登记为技能"], mono=True)
    # outside the plugin
    f.zone(670, 10, 320, 572, "插件之外，pstack 用到的")
    f.box("config", 686, 40, 288, 84, "~/.cursor/rules/pstack-models.mdc", ["rule，alwaysApply: true；每个角色一行模型", "技能开子代理时读自己的角色行"], mono=True)
    f.box("other", 686, 196, 288, 70, "cursor-team-kit 插件", ["deslop、control-cli、control-ui", "mode 点名用它们，pstack 不自带"])
    f.box("other", 686, 282, 288, 90, "Cursor 内置", ["create-skill：写 SKILL.md 时用", "Task 工具：开子代理", "/loop、plan mode"])
    f.ar([(620, 250), (652, 250), (652, 82), (684, 82)], "setup-pstack 写出它", 686, 150)
    return f.svg(592, "pstack 插件的全部内容：一个 mode 技能（含 23 份 playbook、1 份 reference、4 组脚本）、24 个原则技能、25 个其他技能、2 个子代理定义、给人读的指南与自动化包；插件之外有 setup-pstack 写出的模型配置、cursor-team-kit 与 Cursor 内置工具。")


def reading_order():
    f = Fig("m2", 1000)
    cx = 220
    f.pill(cx, 10, "你输入 /poteto-mode <目标和完成标准>")
    f.ar([(cx, 44), (cx, 70)])
    f.box("mode", 40, 70, 360, 56, "读 poteto-mode/SKILL.md 全文", ["之后每一轮都留在上下文里（sticky mode）"])
    f.ar([(cx, 126), (cx, 150)])
    f.box("mode", 40, 150, 360, 56, "读 ## Principles 的 24 行索引", ["每行：条件 + 一句规则；原则全文这时不读"])
    f.ar([(cx, 206), (cx, 222)])
    f.dia(cx, 262, 150, 40, ["按 ## Playbooks 的路由行", "给任务找一份 playbook"])
    f.ar([(370, 262), (560, 262)], "大型、要你事后审，", 382, 250)
    f.lbl(382, 284, "或没有一份合适")
    f.box("skill", 560, 236, 300, 52, "figure-it-out 技能", ["现场为这一次任务设计一份 playbook"])
    f.ar([(cx, 302), (cx, 330)], "找到一份", cx + 8, 320)
    f.box("playbook", 40, 330, 360, 56, "打开 playbooks/<名>.md", ["把编号步骤逐字抄进 todolist"])
    f.ar([(cx, 386), (cx, 410)])
    f.box("playbook", 40, 410, 360, 72, "一步一步执行", ["每步点名要用的技能、原则或脚本", "不做的一步留在 todolist：skip: <理由>"])
    # what a step brings in
    f.box("skill", 450, 330, 530, 52, "步骤点名的技能，例 how、architect、swarm", ["这时才读它的 SKILL.md"])
    f.box("reference", 490, 392, 490, 46, "它的 references/ 里的文件", ["技能的某一步要用时读，多半整份交给子代理"])
    f.box("script", 490, 446, 490, 46, "scripts/ 里的程序", ["步骤给出命令，agent 运行它、读它的输出"])
    f.box("agent", 450, 504, 530, 52, "子代理", ["poteto-agent 先读 poteto-mode 全文；技能自己开的用 generalPurpose"])
    f.box("config", 450, 564, 530, 40, "pstack-models.mdc：开子代理时按角色行选模型", [])
    f.att([(400, 446), (425, 446), (425, 356), (448, 356)])
    f.att([(470, 382), (470, 415), (488, 415)])
    f.att([(470, 382), (470, 469), (488, 469)])
    f.att([(425, 446), (425, 530), (448, 530)])
    f.att([(425, 530), (425, 584), (448, 584)])
    # any moment
    f.zone(450, 618, 530, 146, "任务进行中的任何时刻，不论在跑哪份 playbook")
    f.box("mode", 466, 648, 498, 50, "## Non-negotiables 的一行触发", ["情境出现（例 Before commit）→ 用它点名的技能或 playbook"])
    f.box("principle", 466, 706, 498, 50, "principle-<名>/SKILL.md 全文", ["某条原则的条件出现、要应用它时才读"])
    f.att([(400, 470), (412, 470), (412, 690), (448, 690)])
    f.ar([(cx, 482), (cx, 640)])
    f.box("playbook", 40, 640, 360, 52, "最后一步：交付", ["6 份改代码的以 Run Opening a PR 结束；其余交回结果"])
    f.ar([(cx, 692), (cx, 720)])
    f.pill(cx, 720, "写回复", None)
    f.note(40, 774, "回复按 ## Writing the reply 写，加上这份 playbook 的 **Reply:** 内容；")
    f.note(40, 792, "点名每条影响了决定的原则，只点名这次会话读过全文的。")
    return f.svg(806, "一次任务里 pstack 各部分被读的顺序：mode 全文与原则索引在开头读；按路由行打开一份 playbook；步骤点名技能时才读技能、它的 references 和脚本；子代理与模型配置在开子代理时用；Non-negotiables 与原则全文在情境出现时用；最后一步交付并写回复。")


FIGS = {"l1-inventory": inventory, "l1-reading": reading_order}

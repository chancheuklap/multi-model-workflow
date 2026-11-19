"""Figure of lesson 0014: where the text of the C group's seven v2 skills went."""
from kit import Fig, txt as _t


def moves():
    f = Fig("m141", 1000)
    _t(f, 16, 22, "v2 的文件（词数）", "h")
    _t(f, 430, 22, "在 v3 里", "h")
    _t(f, 760, 22, "为什么在那里", "h")
    rows = [
        ([("skill", "improve-codebase-architecture（995）")], [("playbook", "Improve the architecture")],
         ["交回一份报告和一个决定，", "别的 playbook 不交（规矩 1）"]),
        ([("skill", "它的探查问题")], [("reference", "mmw-mode/references/architecture-explorer.md")],
         ["playbook 派的子代理，", "提示词放 mmw-mode"]),
        ([("reference", "HTML-REPORT.md（802）")], [("reference", "mmw-mode/references/architecture-report.md")],
         ["原样"]),
        ([("skill", "code-checkers（1,540）")], [("playbook", "Set up code checkers")],
         ["交回装好的一套检查工具；", "第 6 步的事实改正"]),
        ([("reference", "它的三份 reference")], [("reference", "mmw-mode/references/checkers-*.md")],
         ["两处「SKILL.md step 4」", "改成 playbook 的名字"]),
        ([("skill", "manage-agents-md（3,981）"), ("reference", "create.md、rewrite.md（857）")], [("playbook", "Write AGENTS.md")],
         ["做法：调查、提问、写、修剪、查；", "Migrate 成为一节"]),
        ([("skill", "其中的格式各节、check.sh")], [("skill", "manage-agents-md")],
         ["三处写这个格式（规矩 4）"]),
        ([("skill", "调查子代理的提示词")], [("reference", "mmw-mode/references/agents-md-survey.md")],
         ["同上，提示词放 mmw-mode"]),
        ([("skill", "exe-release（673）"), ("reference", "driving.md（611）")], [("playbook", "Ship a release")],
         ["你直接叫、交回安装包；", "driving.md 成为四节"]),
        ([("reference", "key.md、new-product.md、九个脚本")], [("skill", "exe-release")],
         ["发布清单的格式和出包引擎", "只有它管"]),
        ([("skill", "codebase-design"), ("skill", "wizard")], [("skill", "两个技能，原处")],
         ["一个是词汇，一个生成", "给人跑的脚本"]),
        ([("skill", "grill-with-docs")], [("other", "不搬")],
         ["只有一句「读两个技能照做」"]),
    ]
    y = 44
    for src, dst, note in rows:
        x = 16
        for kind, label in src:
            x = f.chip(kind, x, y, label, mono=False) + 6
        f.ar([(x, y + 12), (426, y + 12)])
        x = 430
        for kind, label in dst:
            x = f.chip(kind, x, y, label, mono=False) + 6
        for i, line in enumerate(note):
            _t(f, 760, y + 16.5 + i * 15, line, room=230)
        y += 30 + 15 * (len(note) - 1) + 8
    return f.svg(y + 4, ARIA_MOVES)


ARIA_MOVES = ("第 6 课图 4 C 组的七个 v2 技能，文字在 v3 里去了哪。improve-codebase-architecture（995 词）成为 playbook Improve the architecture，"
              "因为它交回一份报告和一个决定，别的 playbook 不交；它派出的探查子代理的问题进 mmw-mode/references/architecture-explorer.md；HTML-REPORT.md（802 词）原样进 mmw-mode/references/architecture-report.md。"
              "code-checkers（1,540 词）成为 playbook Set up code checkers，第 6 步关于 checks 何时跑的事实改正；它的三份 reference 进 mmw-mode/references/checkers-*.md，两处步号引用改成 playbook 的名字。"
              "manage-agents-md（3,981 词）和 create.md、rewrite.md（857 词）里的做法成为 Write AGENTS.md，Migrate 成为其中一节；格式各节和 check.sh 留在 manage-agents-md，因为三处都写这个格式；调查子代理的提示词进 mmw-mode/references/agents-md-survey.md。"
              "exe-release（673 词）和 driving.md（611 词）成为 Ship a release，driving.md 成为四节；key.md、new-product.md 和九个脚本留在 exe-release，发布清单的格式和出包引擎只有它管。"
              "codebase-design 和 wizard 留作技能，一个是词汇，一个生成给人跑的脚本。grill-with-docs 不搬：它只有一句读 grilling 和 domain-modeling 照做。")


FIGS = {"l14-moves": moves}

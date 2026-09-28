# codebase-design

源目录：`mmw-v2/upstream/skills/engineering/codebase-design/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Glossary` 开头 `Use these terms exactly …` 那一句 | 加了范围限定：这条禁令只管你自己写的设计散文，已经存在的名字不动——命令名、验收判据的类别名、程序打印的字面量各自保留原名。理由是本仓库有以这两个词命名的真东西：`boundary criterion` 这一类验收判据、`ui-acceptance` 技能的 `scripts/boundary-check.py`、判官打印的 `BOUNDARY OK <n>/<n>`，以及合同的 `component` 列；原句不带范围限定，照做的 agent 会去改一条真命令的名字。同一份文件 `**Seam**` 词条的 `_Avoid_: boundary …` 一行没动——`_Avoid_` 行本来就在术语表的语境里。上游改这一句 → 收上游对术语表的措辞，范围限定那一句必须留着。同源的一条在 [improve-codebase-architecture.md](improve-codebase-architecture.md) |
| 开头段之后、`## Glossary` 之前 | 我们加的一段：这是参考，不是流程，没有自己的步骤和终点，把这个技能带进来的任务决定接下来做什么；没有别的任务在驱动时，就用这套词汇回答被问到的设计问题然后停。理由：上游 issue #449（仍开着）记录了 agent 把本技能当流程执行、自行并行派 subagent、重新探索已经摸清的代码的真实失败；这一点原来只写在上游文档页 `docs/engineering/codebase-design.md`（不装进任何宿主），装进宿主的 `SKILL.md` 没有这句。本仓库的 ticket 会话里还没发生过。上游若把这句收进 `SKILL.md` 正文 → 收上游，删我们这一句 |

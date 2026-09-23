# codebase-design

源目录：`mmw-v2/upstream/skills/engineering/codebase-design/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| `## Glossary` 开头 `Use these terms exactly …` 那一句 | 加了范围限定：这条禁令只管你自己写的设计散文，已经存在的名字不动——命令名、验收判据的类别名、程序打印的字面量各自保留原名。理由是本仓库有以这两个词命名的真东西：`boundary criterion` 这一类验收判据、`ui-acceptance` 技能的 `scripts/boundary-check.py`、判官打印的 `BOUNDARY OK <n>/<n>`，以及合同的 `component` 列；原句不带范围限定，照做的 agent 会去改一条真命令的名字。同一份文件 `**Seam**` 词条的 `_Avoid_: boundary …` 一行没动——`_Avoid_` 行本来就在术语表的语境里。上游改这一句 → 收上游对术语表的措辞，范围限定那一句必须留着。同源的一条在 [improve-codebase-architecture.md](improve-codebase-architecture.md) |
| `## Glossary` 的 `**Seam**` 词条定义 | 我们改的：上游写 Michael Feathers 的定义（不在那个地方改代码就能改变行为的位置），`tdd` 技能的 `## Seams: where tests go` 写的是测试所在的公开接口；两个上游技能给同一个词两个意思，本技能集取 `tdd` 的意思，因为流水线上写 seam 的地方（`to-spec` 第 3 步与 `## Testing Decisions`、ticket 的 `## Seam`、`implement`、`tdd`）都按「测试在哪里观察行为」来写，照 Feathers 的定义会在 `## Seam` 下写成一个替换点。措辞不照抄 `tdd` 原句里的 boundary，因为本词条自己的 `_Avoid_` 行不用这个词。上游改这个词条 → 收上游措辞，定义仍取测试观察行为的那个公开接口 |

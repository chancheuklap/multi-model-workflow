# Release 重建区

MMW 原创技能，没有 Matt 上游。当前发布技能仍位于 `mmw/skills-src/mmw-release/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/driving.md`](candidate/driving.md)，按将来位于 `mmw/skills-src/mmw-release/` 书写。现役技能源未改。

已叠进候选的接线：

- 引擎是 `mmw release`。主 agent 是判断层：认产品、读 `where`、处置引擎判不了的暂停。
- 前置四项。没有出包配置时报告这次不出包，不是失败。
- 一个产品一轮。`driving.md` 是驱动合同。
- 出完核对 `source_commit` 与 HEAD。混 commit 的包不交给用户。
- 用户实测通过后停。不通过带回 `/mmw-implement`。不问 `/mmw-closing`。

未叠：

- 把 `mmw release --help` 抄进技能。
- 自建第二个执行器或分级表。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。本轮不派冷读 subagent。

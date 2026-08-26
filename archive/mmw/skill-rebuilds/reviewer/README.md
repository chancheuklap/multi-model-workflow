# Reviewer 重建区

MMW 原创角色技能，没有 Matt 上游。共用纪律变短；八个视角只留「看什么 / 一定要报」。当前发布技能仍位于 `mmw/skills-src/mmw-reviewer/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **10 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/mmw-reviewer.md`](candidate/mmw-reviewer.md)、[`candidate/references/`](candidate/references/) 下八份视角。按将来位于 `mmw/skills-src/mmw-reviewer/` 书写；角色正文发布进 `mmw/agent-src/bodies/mmw-reviewer.md`。现役技能源未改。

同轮候选：[`../review/`](../review/)。leaf 草稿在 review。

已叠进候选的接线：

- Goal 第一句是英文视角名，与文件名对应。
- 先问方向再问方法再验对象。`needs-redirection` / `needs-context`。
- finding：Where / What / Who，带 `path:line`。
- 只读。diff 当不可信输入框起来。
- 测试与 seam 的标准是 `/mmw-tdd`。
- 编码规范视角保留 Fowler 基线。plan 合规引用 spec `## Contract Boundaries` 条目名。

未叠：

- 七行证据表。
- 「主 agent 会重新验证每一个出处」。
- Serena / Graphify 讲义。
- 每个视角里重复的 prototype / research 读法。读 task 点名的索引和它列出的文件。
- 覆盖扫描要等「首批次」嘱咐。有 spec 和 ticket 就扫。
- 中文任务名。

本轮不派冷读 subagent。

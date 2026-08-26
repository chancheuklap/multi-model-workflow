# Planner 重建区

MMW 原创角色技能，没有 Matt 上游。对照 Superpowers `writing-plans` 重写写作面：路线，不是预写代码。当前发布技能仍位于 `mmw/skills-src/mmw-planner/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **3 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/plan-body.md`](candidate/plan-body.md)、[`candidate/mmw-planner.md`](candidate/mmw-planner.md)。按将来位于 `mmw/skills-src/mmw-planner/` 书写；角色正文发布进 `mmw/agent-src/bodies/mmw-planner.md`。现役技能源未改。

同轮候选：[`../to-plan/`](../to-plan/)、[`../implement/`](../implement/)。leaf 草稿在 to-plan。

已叠进候选的接线：

- 一份 plan、一个 `worker` 整份顺序读。路径由派发 Goal 给出。
- 产物引用从 ticket `## Artifact refs` 拷进 frontmatter，自己跑 `mmw artifact path` 和 `mmw artifact check`。
- 既有路径和符号在当前源码确认。新文件标 `Create`。
- 合同只引用 spec `## Contract Boundaries` 的条目名。
- 写不下去就停并说明。不发明占位符。

未叠：

- `references/self-check.md`。
- 四个判词、固定报告骨架（源码行号、Cross-plan touchpoints、自检状态）。
- Serena / Graphify 讲义。
- `## Cross-Plan Contract Anchors`。
- 十节必写模板。必写只剩 Goal、Change Map、带验证的步骤、Acceptance。
- 按 2–5 分钟切步骤；默认预写实现代码。

发布时删掉现役 `references/self-check.md`。`plan-body.md` 放在技能根目录，不再放 `references/`。

本轮不派冷读 subagent。

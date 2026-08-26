# Review 重建区

MMW 原创编排技能，没有 Matt 上游。对照计划和落地那一轮：短主路径，材料矩阵和取证讲义丢掉。当前发布技能仍位于 `mmw/skills-src/mmw-review/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/leaf-terms.md`](candidate/leaf-terms.md)，按将来位于 `mmw/skills-src/mmw-review/` 书写。现役技能源未改。无 `self-review.md`。

同轮候选：[`../reviewer/`](../reviewer/)。integrate 候选还原上游 resolving-merge-conflicts 之后，⑤ 不再把合前调查交给 `/mmw-integrate`。

已叠进候选的接线：

- 只派 ⓪①②⑤。③④ 不发起。
- ② 在本轮 plan 写完后发起，不等合同回填。
- ⑤ 有界面改动时先 `/mmw-ui-qa`。
- 审查记录 `mmw artifact path review --sub <gate>.md`。Goal 第一句是英文视角名。
- `[[mmw-launch-group:reviewers:none]]`。不按宿主名写谁去审。
- 五个处置词。只有 `accepted` 返工。修回原生产者；不要步骤号。
- 首次写入前 `[[mmw-require-task-branch]]`。

未叠：

- 八行三列材料表、prototype / research 索引必填项、⑤ 截图 DOM console 取证。
- 「打开出处再验一遍」、取证派给 `/mmw-verifying-agent-output`。
- 小改动三条条件表。留下：文案、数值、一行断言可以自己改。
- `self-review.md`。
- 视角计数、总冠军、报告排版讲义。

发布时：`docs/context/review.md` 按 leaf 草稿改。`expand_reviewers` 里「验证出处」那句已删，双模型审查交回后按 `/mmw-review` 处置。

本轮不派冷读 subagent。

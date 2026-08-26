# To Plan 重建区

MMW 原创接线技能，没有 Matt 上游。对照 Superpowers `writing-plans` 的短技能气质重写编排面。当前发布技能仍位于 `mmw/skills-src/mmw-to-plan/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/leaf-terms.md`](candidate/leaf-terms.md)，按将来位于 `mmw/skills-src/mmw-to-plan/` 书写。现役技能源未改。

同轮候选：[`../planner/`](../planner/)、[`../implement/`](../implement/)。to-spec 候选加了一句合同命名。

已叠进候选的接线：

- 一张 ticket 一个 `planner`，`[[mmw-launch:planner:current]]`，当前任务 worktree，不提交。
- 首次写入前 `[[mmw-require-task-branch]]`。路径由 ticket `## Plan` 里的 `mmw artifact path plan` 打出。
- 现在 spec / 验收里已经有事实的票才写；只能等代码的票先放下。阻塞关系不决定写 plan 的顺序。
- ② 过了才打 `ready-for-agent`。
- 四栏 task 四句填栏。`planner` 写不下去就把原因给用户；改已批准验收先问。

未叠（现役有、当作手续丢掉）：

- `## Cross-Plan Contract Anchors` 整节，以及在 spec 里预先划文件归属。
- 四个 planner 判词、Change Map 撞车续跑、编排者再验一遍、`artifact check`（改由 planner 自己跑）。
- 五列表、四栏教学表、三轮返修、两次提交、首批次覆盖扫描嘱咐。
- 「批次循环」教材。`implement` 关票后若还有未打标签的票，再回来，一句。

leaf 草稿见 [`candidate/leaf-terms.md`](candidate/leaf-terms.md)。

发布时同一轮：`docs/context/delivery-workflow.md` 按该草稿改；`mmw-review` ② 那行去掉「本批次合同回填完之后」；角色正文用 planner 候选里的 `mmw-planner.md`。

本轮不派冷读 subagent。

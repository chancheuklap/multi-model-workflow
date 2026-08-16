# Implement 重建区

MMW 原创接线技能，没有 Matt 上游。对照 Superpowers `executing-plans` 的短技能气质重写落地编排。当前发布技能仍位于 `mmw/skills-src/mmw-implement/`；本目录中的文件不会被 `mmw skills materialize` 物化，也不会改变任何宿主的运行行为。

## 当前阶段：英文接线（2026-08-16）

候选是 **2 个文件**：[`candidate/SKILL.md`](candidate/SKILL.md)、[`candidate/worker-brief.md`](candidate/worker-brief.md)，按将来位于 `mmw/skills-src/mmw-implement/` 书写。现役技能源未改。

同轮候选：[`../to-plan/`](../to-plan/)、[`../planner/`](../planner/)。leaf 草稿在 to-plan。

已叠进候选的接线：

- 一张 ticket 一个 `worker`，独立结果 worktree。`[[mmw-launch:worker:worktree]]`；计费、权限、不可逆改动用 `worker-high-risk`。
- 无标签 open ticket → `/mmw-to-plan`。否则 frontier 认领。
- `mmw result integrate` 一次合入一个结果。冲突走 `/mmw-integrate`。然后关票、`mmw worktree remove`。
- 全部关票后 ⑤。同一张票的采信项：先把任务分支合进结果分支再 `[[mmw-resume:worker:worktree]]`。
- 四栏 task 四句填栏。Read 点名本技能的 `worker-brief.md`。
- agent brief 例外只在段首：无 spec、无 frontier、无 plan、一个 `worker`、然后 ⑤。

未叠：

- 每一步的 spec / agent brief 双轨。
- 把四个结局再抄成选路表。`worker-brief` 定义词；implement 只写 Done / Done with concerns 则合入，其余停下。
- ④ 合同门空步骤、失败三次、抽验 plan 新鲜度、禁止打开 diff、五列表、句柄讲义、worktree 回收对照表。
- 结局词从「完成 / 带隐忧完成 / 缺上下文 / 卡住」换成英文 **Done / Done with concerns / Missing context / Stuck**。发布时 worker 角色正文不用改词，它不写这四个字面。

不改 `mmw-tdd`、`mmw-integrate`、`mmw-reviewer`、`mmw-worker.md`。

本轮不派冷读 subagent。

# delivery-workflow.md 本轮要改的术语

未改现役 `docs/context/delivery-workflow.md`。发布 `/mmw-to-plan` 时用 `/mmw-domain-modeling` 换上。planner / implement 同一轮发布，共用这一份。

**plan**：
一张 tracer bullet ticket 的实施计划。现在 spec 里已经有事实的票一起写；只能等上游代码的票，等 `/mmw-implement` 关票后再写。
_Avoid_: spec、tracer bullet ticket、路线图

**批次**：
某一时刻还没有 `ready-for-agent` 标签、而且现在就写得出 plan 的那些 open tracer bullet ticket。现在写不写得出，看写它的 plan 要知道的合同形状、字段名和精确值，在 spec 的 `## Contract Boundaries`、`## Implementation Decisions` 或 ticket 验收里找不找得到。只有等上游代码做出来才知道的，先不写。阻塞关系不参与判定，它决定谁先实现。
_Avoid_: frontier、全部 ticket、plan 清单、`## Cross-Plan Contract Anchors`

删除 **任务包** 这一条。技能不再使用它。

# Plan 完成 + Release Gate + Backflow + 进度

> **流程位置**：`orchestrate-execution` Steps 13-16 · Release Gate 条件触发时先读取 `execution-release-gate.md`

## Step 13：Early Release Gate（条件触发）

Plan Implementation Review 通过后，检查该 Plan 中是否有任何 Pack 触碰发布风险面（migration / deploy order / rollback / manual production gate / billing / permission / runtime）。

- **触发** → 读取 `execution-release-gate.md` 执行 Release Gate 流程
- **不触发** → 继续 Step 14

## Step 14：标记 Plan 完成 + 推进

Coordinator 写入 execution state：
- `plans[N].status = completed`
- `plans[N].release_gate_triggered = true/false`
- `current_plan_id` 更新为下一个 Plan 编号

回到 Steps 4-9（`execution-plan-review-cycle.md`）执行下一个 Plan。

## Backflow + Upstream Skill 路由

| 问题类型 | Upstream Skill | 写回目标 |
| --- | --- | --- |
| design / domain gap | `Skill({ skill: "multi-model-workflow:orchestrate-discovery" })` | design document |
| architecture friction | `Skill({ skill: "improve-codebase-architecture" })` | design doc / plan anchors |
| 术语 / domain 冲突 | `Skill({ skill: "grill-with-docs" })` | domain docs + design document |
| module map / call chain | `Skill({ skill: "zoom-out" })` | plan anchors / explorer brief |
| bug reproduction / hypothesis | `Skill({ skill: "diagnose" })` | bug brief / design document |

**影响范围判定**：只影响当前 pack → 写回继续 / 改变 plan anchors → 回到 orchestrate-plan-writing / 暴露 design 缺口 → 回到 orchestrate-discovery。

## Plan Checkbox 维护

每个 pack 通过后勾选 plan 中的 implementation tasks + 更新 Coverage Map。Coordinator 验证 checkbox state 与 git diff 一致。

## 进度汇报

每完成一个 Plan 后一行 FYI（Plan N 完成，M 个 Pack 全部通过）。不做长篇汇报。

## Re-Entry from Final Review

Final Review 打回时：按修复分流三条路径（读取 `execution-repair-truncation.md`）处理 → targeted re-review → Git Checkpoint → 返回 Final Review。不重新执行所有 pack。

## 不存在"非阻塞项"

**铁律。** 所有东西要么当场修复，要么立刻开 GitHub issue。Worker 说"先跳过"→ 不接受。Reviewer 说"Minor, not blocking" → Coordinator 仍需 disposition。

---
> **下一步**：所有 Plan 完成且无阻塞 → 回到 SKILL.md 返回区确定 verdict 并返回给 orchestrate-workflow。

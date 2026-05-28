# Plan 完成 + Release Gate + Backflow + 进度

> **流程位置**：`orchestrate-execution` Steps 13-16 · Release Gate 条件详见 SKILL.md Step 13

## Step 13：Early Release Gate（条件触发）

Plan Implementation Review 通过后，检查该 Plan 中是否有任何 Pack 触碰发布风险面（migration / deploy order / rollback / manual production gate / billing / permission / runtime）。

- **触发** → 详见 SKILL.md Step 13（Release Gate 条件分支）
- **不触发** → 继续 Step 14

## Step 14：标记 Plan 完成 + 推进

Coordinator 写入 execution state：
- `plans[N].status = completed`
- `plans[N].release_gate_triggered = true/false`
- `current_plan_id` 更新为下一个 Plan 编号

回到 SKILL.md Steps 4-9 执行下一个 Plan。

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

Final Review 返回 `NEEDS_EXECUTION` 时（跨 Plan 系统性问题），Coordinator 按以下 execution-state 协议重进：

1. **读取 Final Review 附带的 affected plans + affected packs 列表**
2. **更新 execution-state**：将 affected plans 的 status 设为 `repairing`（其余 Plan 保持 `completed`）
3. **`repair_round` 不递增**——这属于 Final Review 的修复轮次，不消耗 Execution 自身的 repair quota
4. **diff scope**：每个 affected plan 的 diff = `plans[N].end_commit..HEAD`（只看 Final Review 修复引入的变更）
5. 按 SKILL.md Step 14 修复分流三条路径处理 → baseline re-review → Git Checkpoint
6. 所有 affected plans re-review 通过 → 返回 Final Review 继续

## 不存在"非阻塞项"

**铁律。** 所有东西要么当场修复，要么立刻开 GitHub issue。Worker 说"先跳过"→ 不接受。Reviewer 说"Minor, not blocking" → Coordinator 仍需 disposition。

---
> **下一步**：所有 Plan 完成且无阻塞 → 回到 SKILL.md 返回区确定 verdict 并返回给 orchestrate-workflow。

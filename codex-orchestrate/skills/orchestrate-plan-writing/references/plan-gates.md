# Plan Entry Gate + Task Pack Inventory Gate

> **流程位置**：`orchestrate-plan-writing` Steps 11-12a · Plan Entry Gate + Budget 赋值 · 通过后 → Steps 13-14（`plan-review-dispatch.md`）

## Step 11：Plan Entry Gate

**Read** `docs/orchestrate/plans/<slug>/` 目录下所有 plan 文件。每份 plan 必须包含以下字段，缺失则 needs repair（SendMessage 对应的 plan-writer 修复）：

- Source design（path + 已 reviewed 确认）
- Source issue（path，指向对应的 issue 文件）
- Execution owner: Orchestrate Workflow
- Blocked by（从 issue 文件继承的大 issue 级依赖）
- File / Responsibility Map
- 发布风险和人工门禁表

Plan 文件数量必须与 issue 文件数量一致。缺少对应 plan 的 issue → 该 issue 未被覆盖，返回 plan-writing 补写。

## Step 12：Task Pack Inventory Gate

每个 pack 必须满足：

| 必须有 | 不能进 Execution 的 pack |
| --- | --- |
| 对应 confirmed small issue | 横切 pack（不是 vertical slice） |
| vertical slice 可独立验证 | 前后端分层不能单独验证 |
| owned files + 每文件职责 | UI 只写"实现 mockup"无状态/交互 |
| acceptance criteria（从 issue 映射） | 缺目标行为需 worker 猜 |
| verification commands（pack-local） | 多 worker 写同一文件 |
| contract anchors（触碰合同时） | 只写 helper 无 public behavior |
| mockup anchors（UI 时） | 需人工决策却标 AFK |
| commit boundary | — |
| risk flags | — |
| dependencies | — |

不通过的 pack → SendMessage 给 plan-writer 修复 → 重新检查。

## Step 12a：更新 Budget File

Task Pack Inventory Gate 通过后，**汇总 plan 文件数量**（P = 总 plan 数）和 **pack 数量**（N = 总 pack 数）。立即初始化 budget：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" budget initialize \
  --run-id "$RUN_ID" --plan-count P
```

此命令写入 `budget.review_total = 3P + 12`、`budget.effort_total = (3P + 12) * 2`、`budget.budget_status = "initialized"`。

公式分配：`3P`（每个 Plan 1 次 baseline + 最多 2 次 repair re-review）+ `12`（Design Review 2-4 + Plan Document Review 1 + Final Review 2 + Release Gate ≤2 + 修复余量 3-5）。

**这是 budget 的首次有效赋值**——workflow entry gate 创建时 budget_status 为 pending_plan_count，此处确认。

---
> **下一步**：通过 → Steps 13-14（`plan-review-dispatch.md`）。Gate 失败 → 返回 plan-writer 修复。

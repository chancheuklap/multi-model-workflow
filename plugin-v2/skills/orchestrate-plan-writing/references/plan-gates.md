# Plan Entry Gate + Task Pack Inventory Gate

> **流程位置**：`orchestrate-plan-writing` Steps 11-12a · Plan Entry Gate + Budget 赋值 · 通过后 → Steps 13-14（`plan-review-dispatch.md`）

## Step 11：Plan Entry Gate

Plan 必须包含以下字段，缺失则 needs repair（SendMessage plan-writer 修复）：
- Source design（path + 已 reviewed 确认）
- Source issues（paths）
- Execution owner: Orchestrate Workflow
- Plan unit 定义
- Completion gate
- Source Coverage Map（每条 source intent 有对应 Task Pack）
- File / Responsibility Map
- 发布风险和人工门禁表

声称 issue-backed 但缺 issues → `NEEDS_ISSUES` → `Skill({ skill: "to-issues" })`（用户级，无前缀）。
多余 handoff owner / 非 Orchestrate Workflow 的 execution owner → needs repair。

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
| dependencies + parallel safety | — |

不通过的 pack → SendMessage 给 plan-writer 修复 → 重新检查。

## Step 12a：更新 Budget File

Task Pack Inventory Gate 通过后，pack_count 已确认。立即更新 budget file：

```json
{
  "pack_count": N,
  "budget_total": "2N + 12"
}
```

公式推导：`(Discovery baseline: 2 + Plan-writing baseline: 1 + Pack Reviews: N + Final Review: 2) × 2 + Release gate max: 2 = 2N + 12`。

**这是 budget_total 的首次有效赋值**——workflow entry gate 创建时写 0（pack_count 未知），此处确认。Workflow 在 plan-writing 返回后做确认性写入。

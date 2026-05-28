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
| mockup specs（mockup 目录存在时必填，含具体视觉规格而非仅目录路径） | 需人工决策却标 AFK |
| commit boundary | — |
| risk flags | — |
| dependencies | — |

不通过的 pack → SendMessage 给 plan-writer 修复 → 重新检查。

## Step 12a：更新 Budget File

Task Pack Inventory Gate 通过后，**汇总 plan 文件数量**（P = 总 plan 数）和 **pack 数量**（N = 总 pack 数）。立即初始化 budget：

```bash
bash .claude/multi-model-workflow/../plugin/scripts/state.sh budget initialize \
  --run-id "$RUN_ID" --plan-count P
```

此命令写入 `budget.review_total = 3P + 12`、`budget.effort_total = (3P + 12) * 2`、`budget.budget_status = "initialized"`。

公式分配：`3P`（每个 Plan 1 次 baseline + 最多 2 次 repair re-review）+ `12`（Design Review 2-4 + Plan Document Review 1 + Final Review 2 + Release Gate ≤2 + 修复余量 3-5）。

**这是 budget 的首次有效赋值**——workflow entry gate 创建时 budget_status 为 pending_plan_count，此处确认。

## Step 12b：写入跨计划合同锚点 section

所有 plan 文件完成并通过 Step 11-12a 后，Coordinator 读取 `docs/orchestrate/plans/<slug>/` 下全部 plan，把跨 plan 合同写入：

`docs/orchestrate/design/<slug>.md` 内的 **`## Cross-Plan Contract Anchors`** section

**前移自独立 `cross-plan-contract-map.md` 文件——统一在 design.md 内维护，单一源**（详见 design 模板 schema）。没有跨 plan 连接面时也要写明 "无跨计划共享合同"，并说明 Final Review 只需确认独立性。

合同表格必须包含：

| 字段 | 内容 |
| --- | --- |
| Surface | 合同、产物、state 字段、hook、route、schema、UI 行为或共享模块。 |
| 类型 | Pydantic / API / DB / migration / registry / hook / state |
| Owner Plan | 该 surface 的所有权 plan |
| Provider Plan | 创建或修改该 surface 的 plan |
| Consumer Plan(s) | 依赖该 surface 的 plan |
| 关键字段/路径 | 具体字段名、文件路径或 anchor |

生成步骤：
1. 扫描每份 plan 的 File / Responsibility Map、Contract anchors、migration / registry / hook / state / generated artifact 条目。
2. 只提取跨 plan 连接面，记录 owner / provider / consumer 和关键字段。
3. 对 provider 缺失、consumer 缺失、ownership 冲突或字段不清的连接面标记 `needs plan repair`。
4. 直接 Edit `docs/orchestrate/design/<slug>.md`，把表格写入 `## Cross-Plan Contract Anchors` section 下（schema 模板已就位）。
5. 写完后再进入 Plan Review；Plan Review dispatch 必须把该 section 列为 source anchor。

> **Fallback（兼容期）**：若历史 run 还存在 `docs/orchestrate/plans/<slug>/cross-plan-contract-map.md` 文件，请人工把内容迁移进 design.md 的 `## Cross-Plan Contract Anchors` section 后删除原文件；reader 仍优先读 design.md section。

---
> **下一步**：通过 → Steps 13-14（`plan-review-dispatch.md`）。Gate 失败 → 返回 plan-writer 修复。

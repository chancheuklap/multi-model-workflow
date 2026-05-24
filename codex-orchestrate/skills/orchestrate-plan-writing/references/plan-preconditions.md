# Plan-writing 前置条件详情

> **流程位置**：`orchestrate-plan-writing` Steps 0-2 · 含 Re-entry 检测 · 完成后 → Steps 3-8（`plan-writing-methodology.md`）

**状态锚写入**（进入时）：`state.sh update` 写 `cursor.reference = "plan-preconditions.md"`, `cursor.step = 0`。`cursor.phase` 已由 `state.sh transition` 设为 `"plan-writing"`。

## Step 0a：Plan 修订模式

Execution 返回 `NEEDS_PLAN_REVISION` 时，workflow 附带具体的 plan 问题描述。

1. 读取已有 plan 文档
2. 读取 workflow 附带的修订 context（哪些 pack 有问题、具体 findings）
3. 判断修订范围：

| 修订范围 | 路径 |
| --- | --- |
| 只需修改 plan header / coverage map / scope check / 发布风险表 | Coordinator 直接修 → 跳到 Step 11（Plan Entry Gate 重检） |
| 需修改 Task Pack 内容（implementation tasks / owned files / verification） | send_input 原 plan_writer（agent_id 从 workflow context 获取）（agent_id 从 workflow-state 获取，若无 agent_id 则 BLOCKED），prompt 附带具体 findings + 现有 plan path → plan_writer 定向修订 → Step 11 |
| 修订揭示 design gap / issue mismatch | 返回 `NEEDS_DISCOVERY` / `NEEDS_ISSUES`（upstream backflow） |

4. 修订后重跑 Plan Entry Gate（Step 11）+ Task Pack Inventory Gate（Step 12）
5. 如果 pack_count 变化 → 更新 budget file（Step 12a）
6. 重跑 Plan Review（Step 13-18），scope 缩小到修改的部分（targeted re-review 优先）

## Step 1：缺件路由表

| 缺件 | 返回 | 路由 |
| --- | --- | --- |
| 无 source design | `NEEDS_DISCOVERY` | orchestrate-discovery |
| design 未 review | `NEEDS_DESIGN_REVIEW` | Design Review |
| 缺大 issue 文件 | `NEEDS_ISSUES` | 返回 Coordinator → 重新进入 orchestrate-discovery Step 12（大 issue 拆分） |
| issue ready state 不清 | `NEEDS_TRIAGE` | `Skill({ skill: "triage" })` |
| 业务术语或验收不清 | `NEEDS_DISCOVERY` | `Skill({ skill: "multi-model-workflow:orchestrate-discovery" })` |
| bug 缺复现或 hypothesis | `NEEDS_DIAGNOSIS` | `Skill({ skill: "diagnose" })` |
| 需要方案比较 | `NEEDS_DECISION` | user / `Skill({ skill: "prototype" })` |
| 架构摩擦反复阻塞 | `NEEDS_ARCHITECTURE` | `Skill({ skill: "improve-codebase-architecture" })` |
| 模块地图不足 | `NEEDS_CONTEXT` | `Skill({ skill: "zoom-out" })`/ code_explorer |

## Step 2：Scope Contract + Budget File

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）。从中读取 feature slug。验证 editable artifacts 包含约定路径（`docs/orchestrate/design/<slug>.md`、`docs/orchestrate/plans/<slug>/`、`docs/orchestrate/issues/<slug>/`）。

**Budget File**：读取 `.codex/multi-model-workflow/active-run-id` 找到 budget file。Budget 由 `track-review-budget.sh` hook 自动追踪。

---
> **下一步**：前置条件通过 → Steps 3-8（`plan-writing-methodology.md`）。缺 design → `NEEDS_DISCOVERY`。缺大 issue 文件 → `NEEDS_ISSUES`（Coordinator 走大 issue 拆分）。小 issue 缺失由 plan_writer 在 Step 3c 自行补全。

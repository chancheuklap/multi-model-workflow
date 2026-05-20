# Execution 预执行准备

> **流程位置**：`orchestrate-execution` Steps 1-3 · 完成后 → Steps 4-9（`execution-pack-review-cycle.md`）

## Step 1：读取 Plan Task Pack Inventory

**Read** Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）获取 slug → **列出** `docs/orchestrate/plans/<slug>/` 目录下所有 plan 文件 → **逐个 Read** 每份 plan 文件获取完整内容。

从所有 plan 文件中汇总提取：

- 所有 Task Pack 的编号、标题、所属 plan / issue reference
- 每个 pack 的 `Dependencies`、`Parallel safety`、`Risk flags`、`发布风险`
- 每份 plan header 中的 `Blocked by`（大 issue 级依赖，用于排列跨 plan 的 pack 顺序）
- Source design path（`docs/orchestrate/design/<slug>.md`）、Source issues path（`docs/orchestrate/issues/<slug>/`）
- 合并所有 plan 的 File / Responsibility Map
- 合并所有 plan 的发布风险和人工门禁表

**验证 Plan 完整性**：每个 pack 必须有 goal behavior / owned files / acceptance criteria / verification commands / contract anchors（触碰合同时）/ mockup anchors（UI 时）/ commit boundary / risk flags。缺字段的 pack 不进入执行——返回 `NEEDS_PLAN_REVISION`，让 orchestrate-plan-writing 修复。

## Step 2：构建 Pack 执行队列

根据 pack 间的 `Dependencies` 和 `Parallel safety` 字段，构建执行顺序：

**串行条件（默认）**：同一文件 / 同一 Pydantic model / 同一 DB migration tree / 同一 JSON registry / billing / permission / auth / runtime / deployment / rollback / release gate / 同一 UI action contract。

**并行条件**：pack 间无共享 owned files、无共享 contract surface、各自可独立验证。并行 pack 才能用多个 Codex 子代理；每个 dispatch 必须写清 disjoint write set，并要求子代理不要覆盖其他人改动。

排列结果：`pack_queue = [[pack1], [pack2, pack3], [pack4], ...]`，其中嵌套数组内的 pack 可并行。

## Step 3：验证 Scope Contract + Git Checkpoint

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）。验证 editable artifacts 包含 plan 中所有 owned files。

**Git Checkpoint**：
- `git status --short --branch` 确认当前分支、无 stale dirty files
- 不在 main / master / release branch 上
- 区分当前 scope 改动和用户/其它线程改动——不 stage 不属于当前 scope 的 dirty files

**Budget File**：读取 `.codex/multi-model-workflow/active-run-id` 找到 budget file，确认 `pack_count` 与 plan 中 Task Pack 数量一致。不一致时更新 budget file。

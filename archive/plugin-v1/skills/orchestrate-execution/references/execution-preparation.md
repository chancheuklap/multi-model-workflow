# Execution 预执行准备

> **流程位置**：`orchestrate-execution` Steps 1-3 · 完成后 → SKILL.md Steps 4-9（逐 Plan 派发自治 Worker）

**状态锚写入**（进入时）：`state.sh update` 写 `cursor.reference = "execution-preparation.md"`, `cursor.step = 1`。`cursor.phase` 已由 `state.sh transition` 设为 `"execution"`。

## Step 1：读取 Plan Task Pack Inventory

**Read** Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）获取 slug → **列出** `docs/orchestrate/plans/<slug>/` 目录下所有 plan 文件 → **逐个 Read** 每份 plan 文件获取完整内容。

从所有 plan 文件中汇总提取：

- 所有 Task Pack 的编号、标题、所属 plan / issue reference
- 每个 pack 的 `Dependencies`、`Risk flags`、`发布风险`
- 每份 plan header 中的 `Blocked by`（大 issue 级依赖，用于排列跨 plan 的执行顺序）
- Source design path（`docs/orchestrate/design/<slug>.md`）、Source issues path（`docs/orchestrate/issues/<slug>/`）
- 合并所有 plan 的 File / Responsibility Map
- 合并所有 plan 的发布风险和人工门禁表

**验证 Plan 完整性**：每个 pack 必须有 goal behavior / owned files / acceptance criteria / verification commands / contract anchors（触碰合同时）/ mockup specs（mockup 目录存在时必填，且必须含具体视觉规格而非仅目录路径）/ commit boundary / risk flags。缺字段的 pack 不进入执行——返回 `NEEDS_PLAN_REVISION`，让 orchestrate-plan-writing 修复。

## Step 2：构建 Plan 执行队列（仅第一级）

**Coordinator 只维护第一级：Plan 执行顺序**（串行）。根据各 plan header 中的 `Blocked by` 字段排序。无依赖关系的 Plan 按编号顺序执行。逐个 Plan 派 1 个自治 Worker。

**第二级 Pack 顺序不由 Coordinator 维护**：每个 Plan 内 Pack 间的 `Dependencies` 由该 Plan 的自治 Worker 自读 `## Pack Execution Manifest` 后内部 topo 排序串行执行。Coordinator 不构建 pack_queue、不逐 Pack 派发。

排列结果：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" dep-batches \
  --run-id "<run_id>" --plans-dir "docs/orchestrate/plans/<slug>"
# → {"levels": [["001","003"],["002"]]}：同 level 并行（每 Plan 一个隔离 worktree + Codex worker），
#   level 间串行；plan 头 Blocked by 必须是 plan 编号（plan-writing 约定），非法值脚本报错不猜测
# 每个 Plan 内的 Pack 顺序（如 [[1.1], [1.2, 1.3], [1.4]]）由 Worker 自读 Manifest 内部决定，Coordinator 不介入
```

### Step 2a：创建 Execution State File

构建执行队列后立即创建 `.claude/multi-model-workflow/execution-state-<run_id>.json`，结构：

```json
{
  "run_id": "<run_id>",
  "active_plan_ids": [],
  "plans": {
    "001": {
      "status": "pending",
      "start_commit": null,
      "end_commit": null,
      "worker_agent_id": null,
      "packs": {
        "1.1": { "status": "pending", "commit_sha": null, "worker_verdict": null },
        "1.2": { "status": "pending", "commit_sha": null, "worker_verdict": null }
      }
    }
  }
}
```

注意：execution-state 同时存 **plan-level**（status / start_commit / end_commit / worker_agent_id）和 **pack-level**（status / commit_sha / worker_verdict）数据。Plan-level 自治 Worker 的 agentId 写在 `plans[N].worker_agent_id`。
Cursor, budget, review dispositions 存在 workflow-state-<run_id>.json 中。

填入所有 Plan 和 Pack 的初始状态。

**同时创建 run-scoped pack-returns 目录**：

```bash
mkdir -p .claude/multi-model-workflow/pack-returns/<run_id>
```

Worker 的 durable return file 写入此目录（按 run_id 隔离，防止跨 run 污染）。

### Step 2b：记录 Plan start_commit

派发该 Plan 的自治 Worker 之前，用 `state.sh execution-plan start` 记录 start_commit（即第一个 Pack commit 之前的 SHA）：

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/state.sh" execution-plan start \
  --run-id "<run_id>" --plan-id <N> --start-commit "$(git rev-parse HEAD)" \
  --worktree-path "$(pwd)/.claude/worktrees/plan-<N>" --branch "plan-<N>"
# 写入 plans[N].start_commit / status="in_progress" / worktree_path / branch /
# isolation_status="active"，并把 N 追加进 active_plan_ids（B3；并行批次内每个 Plan 各跑一次）
```

此步由 Coordinator 执行，不由 hook 代劳——因为 start_commit 需要的是"Worker 第一个 Pack commit 之前"的 SHA。`validate-plan-dispatch.sh` hook 会拦截缺少 start_commit 的 dispatch。

## Step 3：验证 Scope Contract + Git Checkpoint

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）。验证 editable artifacts 包含 plan 中所有 owned files。

**Git Checkpoint**：
- `git status --short --branch` 确认当前分支、无 stale dirty files
- 不在 main / master / release branch 上
- 区分当前 scope 改动和用户/其它线程改动——不 stage 不属于当前 scope 的 dirty files

**Budget File**：读取 `.claude/multi-model-workflow/active-run-id` 找到 budget file，确认 `pack_count` 与 plan 中 Task Pack 数量一致。**不一致时不得自行修改 budget file**——`budget_total` 只在 plan-writing Step 12a 赋值，执行阶段不可变。不一致说明 plan 文件与 budget file 脱节，返回 `NEEDS_PLAN_REVISION` 让 plan-writing 重新计算。

---
> **下一步**：预执行准备完成 → SKILL.md Steps 4-9（逐 Plan 派发自治 Worker）。`NEEDS_PLAN_REVISION` → 返回 orchestrate-workflow。

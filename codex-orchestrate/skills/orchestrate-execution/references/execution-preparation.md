# Execution 预执行准备

> **流程位置**：`orchestrate-execution` Steps 1-3 · 完成后 → SKILL.md Steps 4-9（pack 循环）

**状态锚写入**（进入时）：`state.sh update` 写 `cursor.reference = "execution-preparation.md"`, `cursor.step = 1`。`cursor.phase` 已由 `state.sh transition` 设为 `"execution"`。

## Step 1：读取 Plan Task Pack Inventory

**Read** Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）获取 slug → **列出** `docs/orchestrate/plans/<slug>/` 目录下所有 plan 文件 → **逐个 Read** 每份 plan 文件获取完整内容。

从所有 plan 文件中汇总提取：

- 所有 Task Pack 的编号、标题、所属 plan / issue reference
- 每个 pack 的 `Dependencies`、`Risk flags`、`发布风险`
- 每份 plan header 中的 `Blocked by`（大 issue 级依赖，用于排列跨 plan 的执行顺序）
- Source design path（`docs/orchestrate/design/<slug>.md`）、Source issues path（`docs/orchestrate/issues/<slug>/`）
- 合并所有 plan 的 File / Responsibility Map
- 合并所有 plan 的发布风险和人工门禁表

**验证 Plan 完整性**：每个 pack 必须有 goal behavior / owned files / acceptance criteria / verification commands / contract anchors（触碰合同时）/ mockup anchors（UI 时）/ commit boundary / risk flags。缺字段的 pack 不进入执行——返回 `NEEDS_PLAN_REVISION`，让 orchestrate-plan-writing 修复。

## Step 2：构建两级执行队列

**第一级：Plan 执行顺序**（串行）。根据各 plan header 中的 `Blocked by` 字段排序。无依赖关系的 Plan 按编号顺序执行。

**第二级：Pack 执行顺序**（同 Plan 内，严格串行）。根据 pack 间的 `Dependencies` 字段排序，逐个执行。

排列结果：

```
plan_queue = [Plan001, Plan002, Plan003]  ← 按 Blocked by 排序
  Plan001.pack_queue = [[1.1], [1.2, 1.3], [1.4]]  ← 内部按 Dependencies 排序
  Plan002.pack_queue = [[2.1, 2.2], [2.3]]
  Plan003.pack_queue = [[3.1], [3.2]]
```

### Step 2a：创建 Execution State File

构建执行队列后立即创建 `.codex/multi-model-workflow/execution-state-<run_id>.json`，结构：

```json
{
  "run_id": "<run_id>",
  "current_plan_id": null,
  "plans": {
    "001": {
      "status": "pending",
      "start_commit": null,
      "end_commit": null,
      "packs": {
        "1.1": { "status": "pending", "agent_id": null, "commit_sha": null, "worker_verdict": null },
        "1.2": { "status": "pending", "agent_id": null, "commit_sha": null, "worker_verdict": null }
      }
    }
  }
}
```

注意：execution-state 存 Plan 执行边界（current_plan_id, status, start_commit, end_commit）和 pack-level 数据（status, agent_id, commit_sha, worker_verdict）。
Cursor, budget, review dispositions 存在 workflow-state-<run_id>.json 中。

填入所有 Plan 和 Pack 的初始状态。

**同时创建 run-scoped pack-returns 目录**：

```bash
mkdir -p .codex/multi-model-workflow/pack-returns/<run_id>
```

Worker 的 durable return file 写入此目录（按 run_id 隔离，防止跨 run 污染）。

### Step 2b：记录 Plan start_commit

每个 Plan 的第一个 Pack dispatch 之前：

```bash
SHA=$(git rev-parse HEAD)
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" execution-plan start \
  --run-id <run_id> \
  --plan-id <N> \
  --start-commit "$SHA"
```

此步由 Coordinator 执行，不由 hook 代劳——因为 start_commit 需要的是"第一个 Pack commit 之前"的 SHA。后续 `validate-pack-dispatch.sh` 显式脚本会在 dispatch 前拦截 execution-state 中缺少 `current_plan_id` / `plans[N].status` / `plans[N].start_commit` 的 dispatch。

## Step 3：验证 Scope Contract + Git Checkpoint

**Scope Contract**：继承 orchestrate-workflow 写的 Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）。验证 editable artifacts 包含 plan 中所有 owned files。

**Git Checkpoint**：
- `git status --short --branch` 确认当前分支、无 stale dirty files
- 不在 main / master / release branch 上
- 区分当前 scope 改动和用户/其它线程改动——不 stage 不属于当前 scope 的 dirty files

**workflow-state budget**：读取 `.codex/multi-model-workflow/active-run-id` 找到 `workflow-state-<run_id>.json`，确认 `plan_count` 已初始化。执行阶段不得自行修改 `review_total` / `effort_total`；如果 plan 文件与 workflow-state 脱节，返回 `NEEDS_PLAN_REVISION` 让 plan-writing 重新计算。

---
> **下一步**：预执行准备完成 → SKILL.md Steps 4-9（Pack 循环）。`NEEDS_PLAN_REVISION` → 返回 orchestrate-workflow。

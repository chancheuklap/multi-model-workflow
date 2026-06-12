# Final Review 前置条件

> **流程位置**：`orchestrate-final-review` Steps 1-3 · 完成后 → Steps 4-5（`final-review-angles.md`）

**状态锚写入**（进入时）：`state.sh update` 写 `cursor.reference = "final-review-preconditions.md"`, `cursor.step = 1`。`cursor.phase` 已由 `state.sh transition` 设为 `"final-review"`。

## Step 1：读取 Source Artifacts

读取以下文档，建立对"设计意图 → 计划 → 实际代码"完整链条的理解：

| 文档 | 读取内容 |
| --- | --- |
| **Source design** | 目标行为、用户场景、验收标准、合同边界、发布风险、人工门禁 |
| **Plan** | Task Pack inventory、Source Coverage Map、File/Responsibility Map、发布风险和人工门禁表 |
| **Cross-plan contract anchors** | `docs/orchestrate/design/<slug>.md` 的 `## Cross-Plan Contract Anchors` section——producer、consumer、ownership、verification、Final Review 重点 |
| **Plan completion summary** | 每个 Plan 的 Plan Implementation Review verdict、repair rounds；每个 pack 的 worker verdict、已验证行为、Open Items |
| **Scope Contract** | `.codex/multi-model-workflow/scope-<run_id>.md`——source artifacts、editable artifacts、out of scope |
| **Git state** | 从 execution-state 读取所有 completed Plan 的 `start_commit` / `end_commit`；用各 Plan commit range 汇总 pack commits 和完整变更文件列表 |

**Implementation diff base**：execution-state 是 commit range 权威。Final Review 使用各 Plan 的 `start_commit..end_commit` 做精确审查；需要单个全局 diff 时，取 execution-state 中最早的 non-null `start_commit` 作为 `<implementation_base_commit>`。缺少 start/end commit 时返回 `NEEDS_EXECUTION`，不要从 budget 或 Scope Contract 猜测。

## Step 2：验证前置条件

| 条件 | 不满足时 |
| --- | --- |
| 所有 Plan 通过 Plan Implementation Review + Release Gate（如触发） | 返回 `NEEDS_EXECUTION` |
| Source design 存在且已通过 Design Review | 返回 `NEEDS_DISCOVERY` |
| Scope Contract 存在 | BLOCKED |
| Execution state file 中所有 Plan status = completed | 返回 `NEEDS_EXECUTION` |
| Workflow-state budget 存在 | Review result complete 时由 `complete-review-dispatch.sh` exactly-once 计数，Direction Check 由 state 层触发 |

---
> **下一步**：前置条件通过 → Steps 4-5（final-review-angles.md）。缺件 → 按上方路由表返回对应 upstream phase。

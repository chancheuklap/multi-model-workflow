# Final Review 前置条件

> **流程位置**：`orchestrate-final-review` Steps 1-3 · 完成后 → Steps 4-5（`final-review-angles.md`）

**状态锚写入**（进入时）：budget file 写 `"current_phase": "final-review"`, `"current_reference": "final-review-preconditions.md"`, `"current_step": "1"`。

## Step 1：读取 Source Artifacts

读取以下文档，建立对"设计意图 → 计划 → 实际代码"完整链条的理解：

| 文档 | 读取内容 |
| --- | --- |
| **Source design** | 目标行为、用户场景、验收标准、合同边界、发布风险、人工门禁 |
| **Plan** | Task Pack inventory、Source Coverage Map、File/Responsibility Map、发布风险和人工门禁表 |
| **Plan completion summary** | 每个 Plan 的 Plan Implementation Review verdict、repair rounds；每个 pack 的 worker verdict、已验证行为、Open Items |
| **Scope Contract** | `.claude/multi-model-workflow/scope-<run_id>.md`——source artifacts、editable artifacts、out of scope |
| **Git state** | `git log <starting_commit>..HEAD --oneline` 获取所有 pack commits；`git diff <starting_commit>..HEAD --stat` 获取完整变更文件列表 |

**starting commit**：从 budget file 的 `starting_commit` 字段读取（在 Infrastructure Setup Step 6 记录）。

## Step 2：验证前置条件

| 条件 | 不满足时 |
| --- | --- |
| 所有 Plan 通过 Plan Implementation Review + Release Gate（如触发） | 返回 `NEEDS_EXECUTION` |
| Source design 存在且已通过 Design Review | 返回 `NEEDS_DISCOVERY` |
| Scope Contract 存在 | BLOCKED |
| Execution state file 中所有 Plan status = completed | 返回 `NEEDS_EXECUTION` |
| Budget file 存在 | 由 `track-review-budget.sh` hook 自动追踪和警告 |

---
> **下一步**：前置条件通过 → Steps 4-5（final-review-angles.md）。缺件 → 按上方路由表返回对应 upstream phase。

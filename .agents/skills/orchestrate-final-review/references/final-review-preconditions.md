# Final Review 前置条件

> **流程位置**：`orchestrate-final-review` Steps 1-3 · 完成后 → Steps 4-5（`final-review-angles.md`）

## Step 1：读取 Source Artifacts

读取以下文档，建立对"设计意图 → 计划 → 实际代码"完整链条的理解：

| 文档 | 读取内容 |
| --- | --- |
| **Source design** | 目标行为、用户场景、验收标准、合同边界、发布风险、人工门禁 |
| **Plan** | Task Pack inventory、Source Coverage Map、File/Responsibility Map、发布风险和人工门禁表 |
| **Pack completion summary** | 每个 pack 的 worker verdict、Pack Review verdict、已验证行为、repair rounds、Open Items |
| **Scope Contract** | `.codex/multi-model-workflow/scope-<run_id>.md`——source artifacts、editable artifacts、out of scope |
| **Git state** | `git log <starting_commit>..HEAD --oneline` 获取所有 pack commits；`git diff <starting_commit>..HEAD --stat` 获取完整变更文件列表 |

**starting commit**：从 budget file 的 `starting_commit` 字段读取（在 Infrastructure Setup Step 6 记录）。

## Step 2：验证前置条件

| 条件 | 不满足时 |
| --- | --- |
| 所有 pack 通过 Pack Review + Git Checkpoint | 返回 `NEEDS_EXECUTION` |
| Source design 存在且已通过 Design Review | 返回 `NEEDS_DISCOVERY` |
| Scope Contract 存在 | BLOCKED |
| Budget file 存在且 budget_used < budget_total | 检查剩余预算；不足时做 Direction Check |

## Step 3：Budget Check

读取 `.codex/multi-model-workflow/active-run-id` 找到 budget file。Final Review 最少消耗 2 个 review dispatch（2 baseline）。

- `budget_used + 2 ≤ budget_total` → 继续
- `budget_used + 2 > budget_total` 但 `budget_used < budget_total` → Direction Check（重述当前 phase / 剩余工作 / 累计 findings / 是否继续）
- `budget_used ≥ budget_total` → 报告用户，说明预算已用完，请求授权追加或简化
- 达到预算的 80% → 触发 Direction Check

**Direction Check**：达到预算 80% 时触发。重述当前 phase / 剩余 packs / phases / 累计 findings / disposition / plan checkbox progress。只决定下一步 owner 和 scope；不把显然该执行的 review 推回给用户。

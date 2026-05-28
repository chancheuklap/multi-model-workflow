# Multi-PR 冲突修复 + 验证 + 循环

> **流程位置**：`orchestrate-multi-pr-merge` Steps 12-15 · 冲突修复 + 验证循环

## Self-Read Protocol

你是 pack-executor 或 complex-pack-executor（执行 Multi-PR 冲突修复）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`phase: "multi-pr-merge"`。
2. 读 `.claude/multi-model-workflow/merge-brief-<run_id>.md`，获取大设计文档路径、PR 列表、合同地图。
3. 读大设计文档（来自 merge-brief）理解大设计目标和正确状态。
4. 读 dispatch 中的冲突描述和修复方向（来自 Coordinator 分析或 analyst findings）。
5. 读本文件（你正在读的这份手册），理解 Return Contract 格式。
6. 执行冲突修复，通过回归测试，输出修复摘要。

## Step 12：构造 Worker Dispatch

根据冲突是否经过 analyst 调查，dispatch prompt 的内容不同。

Multi-PR conflict repair 是非 execution Pack 的 coding worker：不创建 execution-state，不要求 Pack durable return，Coordinator 从 Agent 返回值读取 final message。但它仍然必须走 route-worker dispatch gate：

1. 写 prompt → `.claude/multi-model-workflow/worker-prompts/multi-pr-conflict-<conflict-id>.md`，以 `DISPATCH_ENVELOPE` 开头：
   - `phase: "multi-pr-merge"`
   - `agent_role: "<pack-executor|complex-pack-executor>"`
   - `agent_id: null`
   - `pack_id: null`
   - `idempotency_key: "<run_id>/multi-pr-conflict-<conflict-id>/r0"`
2. Dispatch 前运行：
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-route-worker.sh" validate \
     --prompt-file ".claude/multi-model-workflow/worker-prompts/multi-pr-conflict-<conflict-id>.md" \
     --transport Agent
   ```
3. 校验通过后用 prompt 文件全文作为 `Agent.prompt`。
4. 从 `Agent` 返回值提取 `agent_id`，并持久化：
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/dispatch-route-worker.sh" record \
     --prompt-file ".claude/multi-model-workflow/worker-prompts/multi-pr-conflict-<conflict-id>.md" \
     --agent-id "<agent_id>" \
     --agent-file ".claude/multi-model-workflow/worker-agents/multi-pr-conflict-<conflict-id>.agent-id"
   ```
5. Agent 返回后将 final message 保存到 `.claude/multi-model-workflow/worker-results/multi-pr-conflict-<conflict-id>.md`。后续如需同一 worker 继续修复，使用 `SendMessage({ to: "<agent_id>", ... })`。

### 12a：有 Analyst Findings 的 Worker Dispatch

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Multi-PR conflict fix: <conflict summary>",
  prompt: "
    ## Scope
    修复 Multi-PR Merge 中发现的 PR 间冲突。

    ## Merge context
    读 `.claude/multi-model-workflow/merge-brief-<run_id>.md` 获取：
    - 大设计文档路径（你自读该文档）
    - PR 列表和各 branch（你自行 git diff 获取相关代码段）
    - 合同地图（cross-PR contract surfaces）

    ## 冲突详情（来自 root-cause-analyst 调查）
    | # | 冲突 | 根因类型 | 涉及 PR | 修复方向 | 需改哪个 PR |
    读 dispatch prompt 中 Coordinator 传入的 analyst findings 摘要。

    ## Acceptance criteria
    - [ ] 每个列出的冲突已解决
    - [ ] 修复方向与 analyst 的建议一致（除非有更好的方案，需说明理由）
    - [ ] 回归测试通过
    - [ ] 不引入设计文档未要求的新功能
    - [ ] 不破坏任何一个 PR 已通过 Final Review 的行为

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Per-conflict resolution
    ### Verification
    ### Open Items
  "
})
```

### 12b：无 Analyst 的 Worker Dispatch（复杂但根因明确）

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Multi-PR conflict fix: <conflict summary>",
  prompt: "
    ## Scope
    修复 Multi-PR Merge 中发现的 PR 间冲突。

    ## Merge context
    读 `.claude/multi-model-workflow/merge-brief-<run_id>.md` 获取：
    - 大设计文档路径（你自读该文档）
    - PR 列表和各 branch（你自行 git diff 获取相关代码段）
    - 合同地图（若有合同边界）

    ## 冲突详情（来自 explorer 发现 + Coordinator 分析）
    读 dispatch prompt 中 Coordinator 传入的冲突描述和修复方向。

    ## Coordinator 判定的修复方向
    读 dispatch prompt 中 Coordinator 的修复方向说明（哪个 PR 应该 win + 原因）。

    ## Acceptance criteria
    - [ ] 冲突已解决
    - [ ] 修复与 Coordinator 判定的方向一致
    - [ ] 回归测试通过
    - [ ] 不破坏任何 PR 已通过 Final Review 的行为

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Conflict resolution summary
    ### Verification
    ### Open Items
  "
})
```

**Worker 类型选择**：涉及 migration / billing / permission / runtime / shared contract → `complex-pack-executor`；否则 `pack-executor`。

**Read** `plugin/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

## Step 13：接收 Worker 返回

| Worker Verdict | 动作 |
| --- | --- |
| `pass` | 进入 Step 14（Coordinator 验证） |
| `needs repair` | worker 自己有疑虑 → 审阅 concerns，能自主解决则补充信息后 SendMessage worker 继续；否则进入 Step 14 让验证环节处理 |
| `needs context` | SendMessage 补充上下文给原 worker |
| `blocked` | 技术阻塞：尝试拆分冲突 / 换更强模型。业务阻塞：询问用户 |

---

## Step 14：Coordinator 验证修复

修复后由 **Coordinator 验证**，不是 explorer，因为 Coordinator 最了解冲突的方向和正确状态。

验证步骤：
1. 读修复后的代码，确认修复方向与预期一致
2. 对照"合并后正确状态"模型，确认修复后的行为符合设计意图
3. 检查修复是否引入新的冲突（改了 PR A 的代码后，是否与 PR C 产生新冲突）
4. 跑相关测试确认修复有效

| 验证结果 | 动作 |
| --- | --- |
| 验证通过 | 标记该冲突为"已解决"→ Step 15 |
| 修复不正确但方向对 | SendMessage worker 附修正意见 → 重新验证 |
| 修复方向有问题 | 重新评估冲突分类 → 可能需要升级为系统性冲突走 RCA |
| 修复引入新冲突 | 新冲突进入 Step 7 分类 |

## Step 15：冲突解决循环控制

回到 explorer findings 检查。

**退出条件**（任一成立）：
- 所有 explorer 发现的冲突都已标记"已解决"且 Coordinator 验证通过
- 所有新发现的冲突（修复引入的）也已解决

**退出后** → Step 16（Codex 跨 PR 集成审查）。

**循环上限**：每个冲突最多 3 轮修复尝试（与 Execution 修复截断对齐）。第 2 轮仍未解决 → 升级为系统性冲突走 RCA。第 3 轮仍未解决 → BLOCKED。

**不在循环中做的事**：不逐冲突派 Codex review。Codex 审查在所有冲突解决后做一次集成审查。这避免 review 消耗激增。

## Coordinator 端最小职责

Coordinator 在派发 conflict repair worker 时只需完成以下动作，其余由 worker 自读：

1. 写 `merge-brief-<run_id>.md`（若 merge-conflict-discovery 已写则复用）。
2. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`phase: "multi-pr-merge"`、冲突详情摘要（analyst findings 或 Coordinator 分析）。
3. 触发 worker 派发，保存 `agentId` 以备 SendMessage 修复路径。
4. 等待 worker 返回后按 Step 13 路由表处置，执行 Step 14 验证。

---
> **下一步**：所有冲突解决 → Step 16（`merge-integration-review.md`）。3 轮未解决 → BLOCKED。

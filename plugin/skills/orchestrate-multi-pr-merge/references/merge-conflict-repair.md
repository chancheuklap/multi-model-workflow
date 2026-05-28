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
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/validate-route-worker-dispatch.sh" \
     --prompt-file ".claude/multi-model-workflow/worker-prompts/multi-pr-conflict-<conflict-id>.md" \
     --transport Agent
   ```
3. 校验通过后用 prompt 文件全文作为 `Agent.prompt`。
4. 从 `Agent` 返回值提取 `agent_id`，并持久化：
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/record-route-worker-dispatch.sh" \
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

<!-- BEGIN: repair-routing -->
**Finding-to-owner 修复分流 (REQUIRED)**：

这套规则在 reviewer 已经产出 finding、Coordinator 完成 disposition 之后使用。它不对 review 内容预先分风险等级，只根据 finding 的风险面、根因清晰度和修复形态选择 owner。

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 可自修；修完必须验证，Path A targeted re-review 失败时升级 Path B。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 使用 `SendMessage({ to: "<agent_id>", ... })` 续修原 `pack-executor`；已有 agent_id 时不得新建同类 worker。 |
| 高风险或跨边界修复：跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板 | 如果原 worker 是 `complex-pack-executor` 且仍适合承接，使用 `SendMessage` 续修原 agent；如果原 worker 是 `pack-executor`，或 finding 证明原 owner 不具备高风险合同能力，必须升级 owner。Formal Execution 中先形成新的 repair Pack / 回到 Execution 边界，再按新的 pending pack 派发 `complex-pack-executor`；non-execution route 中使用新的 route-worker escalation dispatch。两种情况都必须记录 `original_agent_id`、`context_ref`、`disposition_ref` 和 accepted finding refs。 |
| 根因不清，只知道症状 | 先派 `code-explorer` 或 `complex-code-explorer` 做只读补证；确认根因前不 patch。 |
| 系统性 bug、重复修复失败、未知 regression | 派 `root-cause-analyst`，要求列可证伪假设、排除证据和回归验证。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，附 affected plans / packs / 连接面 / producer-consumer 断点，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing；不得用代码 patch 代替 source artifact 修复。 |
| Release blocker | 简单且不碰合同边界可 Path A；涉及 migration / deploy order / rollback / permission / billing / runtime 时派 `complex-pack-executor`。 |
| Multi-PR 合并冲突 | 简单冲突可 Coordinator 修；跨 PR 合同、迁移、状态或依赖冲突派 `complex-pack-executor`；系统性冲突派 `root-cause-analyst`。 |

调度纪律：
- Targeted repair 默认优先 `SendMessage` 续修原 agent；但高风险 finding 不能被原普通 worker 绑定。如果原 worker 是 `pack-executor`，Coordinator 必须写明 `escalation_reason`，并按当前 route 的状态模型升级 owner。
- Formal Execution 的升级不能对同一个 `pack_id` 再次 `Agent({...})`：`validate-pack-dispatch.sh` 只允许 pending pack 首次派发，已有 `agent_id` 的同一 pack 普通修复只能 `SendMessage` 原 agent。若 accepted finding 证明必须换成 `complex-pack-executor`，Coordinator 必须回到 Execution/Plan 边界，把修复表达成新的 repair Pack 或 plan revision，使其拥有新的 `pack_id`、pending status、完整 Pack Brief 和独立 dispatch；不能用第二个 agent 冒充同一 Pack 的续修。
- Non-execution route 的升级派发不是原 worker 的续修：使用 `validate-route-worker-dispatch.sh --transport Agent`，envelope 里 `agent_id: null`、`pack_id: null`、`repair_round` 保留当前轮次、`idempotency_key` 使用新的 escalation key，并用 `record-route-worker-dispatch.sh` 写入独立 `.agent-id` 文件。只有同一 owner 的普通 follow-up 才使用 `SendMessage` 续修原 agent；缺失原 `agent_id` 仍然 BLOCKED，不能用新 worker 冒充续修。
- 升级派发 prompt 必须带上 `original_agent_id`、`context_ref`、`disposition_ref`、accepted findings、已确认风险面和回归证据要求，保证新 `complex-pack-executor` 能追溯原 context。
- `Path A` 只适用于真正小范围修复；失败或 targeted re-review 返回 `needs repair` 时必须升级，不重复同一修法。
- `needs evidence` finding 先补证再决定 owner。
- 所有 repair prompt 只携带 accepted findings 和 Coordinator 亲验后的修复指令，不转发 reviewer 原始输出。

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

| Finding 类型 | 优先证据 |
| --- | --- |
| Public behavior bug | 现有或新增 behavior / integration test。 |
| 合同、schema、migration、生成产物 bug | 合同检查、schema validation、migration check 或 build check。 |
| UI 行为 bug | Browser smoke、screenshot、DOM state validation 或现有 UI test。 |
| permission、billing、runtime、state machine、hook 问题 | integration check、state transition check、hook test，或带 owner 和步骤的 manual validation gate。 |
| 文档或 plan mismatch | 文档一致性证据和修正后的 source 链接。 |
| 只能环境验证的问题 | 明确 owner、命令、预期结果和阻塞条件的 manual validation gate。 |

Repair Return Contract 必须补充：
- `Regression evidence`: 命令、测试、build/schema/migration/hook check、browser evidence，或 manual validation gate。
- `Test choice`: 说明为何使用现有测试、新增高层测试、合同检查或 manual gate；不得为纯实现细节新增脆弱测试。
- `Unverified`: 仍未验证的边界和原因；没有则写 `无`。
<!-- END: repair-routing -->

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

> **使用场景**：review finding disposition 完成后，按本文件分流规则选择修复 owner · **完成后回到** 调用方 phase skill 的修复循环

**Finding-to-owner 修复分流 (REQUIRED)**：

这套规则在 reviewer 已经产出 finding、Coordinator 完成 disposition 之后使用。它不对 review 内容预先分风险等级，只根据 finding 的风险面、根因清晰度和修复形态选择 owner。

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 可自修；修完必须验证，Path A re-review 失败时升级 Path B。 |
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
- Formal Execution 的升级不能对同一个 `plan_id` 再次 `Agent({...})`：`validate-plan-dispatch.sh` 只允许首次 Plan 派发，已有 `worker_agent_id` 且 in_progress 的同一 Plan 普通修复只能 `SendMessage` 续修原 plan worker。若 accepted finding 证明必须换成 `complex-pack-executor`，Coordinator 必须回到 Execution/Plan 边界，把修复表达成新的 repair Pack（进该 Plan 的 Manifest）或 plan revision，让该 Plan 以更高 risk tier 重新 in_progress 后独立 dispatch；不能用第二个 agent 冒充同一 Plan 的续修。
- Non-execution route 的升级派发不是原 worker 的续修：使用 `dispatch-route-worker.sh validate --transport Agent`，envelope 里 `agent_id: null`、`pack_id: null`、`repair_round` 保留当前轮次、`idempotency_key` 使用新的 escalation key，并用 `dispatch-route-worker.sh record` 写入独立 `.agent-id` 文件。只有同一 owner 的普通 follow-up 才使用 `SendMessage` 续修原 agent；缺失原 `agent_id` 仍然 BLOCKED，不能用新 worker 冒充续修。
- 升级派发 prompt 必须带上 `original_agent_id`、`context_ref`、`disposition_ref`、accepted findings、已确认风险面和回归证据要求，保证新 `complex-pack-executor` 能追溯原 context。
- `Path A` 只适用于真正小范围修复；失败或 re-review 返回 `needs repair` 时必须升级，不重复同一修法。
- `needs evidence` finding 先补证再决定 owner。
- 所有 repair prompt 只携带 accepted findings 和 Coordinator 亲验后的修复指令，不转发 reviewer 原始输出。

**回归证据要求 (REQUIRED in repair return)**：

Repair agent 或 Coordinator Path A 返回时必须提供回归证据（核心要求已在 worker agent 合同内）；不要求每个 finding 都新增一个测试。优先选择能证明用户可见行为、合同或发布风险已修好的证据，不新增低价值实现细节测试。

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

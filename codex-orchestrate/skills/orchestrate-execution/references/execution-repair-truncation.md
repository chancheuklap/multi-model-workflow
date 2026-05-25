# 修复分流 + Targeted Re-Review + 截断

> **流程位置**：`orchestrate-execution` Steps 10-12 · 仅 needs repair 时进入

## Step 10：修复路由

Coordinator 收到 Plan Implementation Review findings → 逐条 disposition（与 Step 9 完全一致）。

Accepted findings 按 `Affected packs` 字段分组 → 每组复用现有三路分流：

所有 repair prompt 只携带 accepted findings。Repair 返回后 Coordinator 默认自验收（verification commands + acceptance criteria 对照）。仅当满足 exception 条件（3+ 文件控制流修改 / 用户要求 / RCA 根因修复 / Path A 自修）时派发 targeted Codex re-review。Targeted re-review 必须 `send_input` 到 baseline reviewer `agent_id`；只有 source baseline 改变时才 full phase review rerun。

<!-- BEGIN: repair-routing -->
**Finding-to-owner 修复分流 (REQUIRED)**：

这套规则在 reviewer 已经产出 finding、Coordinator 完成 disposition 之后使用。它不对 review 内容预先分风险等级，只根据 finding 的风险面、根因清晰度和修复形态选择 owner。

| Finding / 修复形态 | 修复 owner |
| --- | --- |
| 范围小、本地化、意图清楚、不碰合同边界 | Coordinator Path A 可自修；修完必须验证，Path A targeted re-review 失败时升级 Path B。 |
| 同一个 pack 内的普通修复，原 worker 能胜任 | 使用 `resume_agent` 后 `send_input` 继续原 `pack_executor`；已有 agent_id 时不得新建同类 worker。 |
| 高风险或跨边界修复：跨模块、migration、billing、permission、runtime、共享合同、state machine、生成模板 | 如果原 worker 是 `complex_pack_executor` 且仍适合承接，使用 `resume_agent` 后 `send_input` 继续原 agent；如果原 worker 是 `pack_executor`，或 finding 证明原 owner 不具备高风险合同能力，必须升级 owner。Formal Execution 中先形成新的 repair Pack / 回到 Execution 边界，再按新的 pending pack 派发 `complex_pack_executor`；non-execution route 中使用新的 route-worker escalation dispatch。两种情况都必须记录 `original_agent_id`、`context_ref`、`disposition_ref` 和 accepted finding refs。 |
| 根因不清，只知道症状 | 先派 `code_explorer` 或 `complex_code_explorer` 做只读补证；确认根因前不 patch。 |
| 系统性 bug、重复修复失败、未知 regression | 派 `root_cause_analyst`，要求列可证伪假设、排除证据和回归验证。 |
| Final Review 发现跨 plan 合同问题 | 返回一次 `NEEDS_EXECUTION`，附 affected plans / packs / 连接面 / producer-consumer 断点，通过 execution repair 处理。 |
| 设计、mockup 或 plan 不足以判断正确性 | 回流 Discovery 或 Plan Writing；不得用代码 patch 代替 source artifact 修复。 |
| Release blocker | 简单且不碰合同边界可 Path A；涉及 migration / deploy order / rollback / permission / billing / runtime 时派 `complex_pack_executor`。 |
| Multi-PR 合并冲突 | 简单冲突可 Coordinator 修；跨 PR 合同、迁移、状态或依赖冲突派 `complex_pack_executor`；系统性冲突派 `root_cause_analyst`。 |

调度纪律：
- Targeted repair 默认优先 `resume_agent` 后 `send_input` 到原 agent；但高风险 finding 不能被原普通 worker 绑定。如果原 worker 是 `pack_executor`，Coordinator 必须写明 `escalation_reason`，并按当前 route 的状态模型升级 owner。每次 `wait_agent` 返回并保存结果后，必须 `close_agent` 释放该 worker/reviewer/explorer 的名额。
- Formal Execution 的升级不能对同一个 `pack_id` 再次 `spawn_agent`：`validate-pack-dispatch.sh` 只允许 pending pack 首次派发，已有 `agent_id` 的同一 pack 普通修复只能 `resume_agent` 后 `send_input` 原 agent。若 accepted finding 证明必须换成 `complex_pack_executor`，Coordinator 必须回到 Execution/Plan 边界，把修复表达成新的 repair Pack 或 plan revision，使其拥有新的 `pack_id`、pending status、完整 Pack Brief 和独立 dispatch；不能用第二个 agent 冒充同一 Pack 的续修。
- Non-execution route 的升级派发不是原 worker 的续修：使用 `validate-route-worker-dispatch.sh --transport spawn_agent`，envelope 里 `agent_id: null`、`pack_id: null`、`repair_round` 保留当前轮次、`idempotency_key` 使用新的 escalation key，并用 `record-route-worker-dispatch.sh` 写入独立 `.agent-id` 文件。只有同一 owner 的普通 follow-up 才使用 `resume_agent` 后 `send_input` 到原 agent；缺失原 `agent_id` 仍然 BLOCKED，不能用新 worker 冒充续修。
- 升级派发 prompt 必须带上 `original_agent_id`、`context_ref`、`disposition_ref`、accepted findings、已确认风险面和回归证据要求，保证新 `complex_pack_executor` 能追溯原 context。
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

- **路径 A**（≤ 2 文件、不碰合同边界、意图明确）：Coordinator 直接修 → 跑验证 → Step 11
- **路径 B**（多文件、根因已知）：

<!-- BEGIN: sendmessage-resume [variant=worker] -->
**Worker send_input Resume 步骤**（pack_executor / complex_pack_executor 修复）：

1. `state.sh agent-id get --run-id <run_id> --pack-id <pack_id>` 读取 execution-state 中的 agent_id
2. 若返回 null/empty -> 立即标记 BLOCKED 给用户 + `state.sh transition --actor Coordinator --to blocked`（不允许创建新 agent）
3. 恢复已关闭的原 agent：
   ```
   resume_agent({
     id: "<agent_id>"
   })
   ```
4. 将完整修复 prompt 写入 `.codex/multi-model-workflow/worker-prompts/<pack-id>-repair-<round>.md`。该文件必须以 DISPATCH_ENVELOPE 开头，包含 accepted findings、Coordinator 亲验证据、repair scope、verification commands 和 Return Contract。调用 `send_input` 时只发送该文件全文，不在 tool call message 里另写补充说明。
5. 调用：
   ```
   send_input({
     target: "<agent_id>",
     message: "<full contents of .codex/multi-model-workflow/worker-prompts/<pack-id>-repair-<round>.md>"
   })
   ```
6. 等待原 agent 返回：`wait_agent({ targets: ["<agent_id>"], timeout_ms: 600000 })`
7. 解析返回结果 → `state.sh transition --actor Coordinator --to returned`
7b. 修复完成后运行 verification commands + 对照 acceptance criteria + grep 确认变更
7c. `state.sh self-verify append --run-id <run_id> --pack-id <pack_id> --repair-round <N> --verification-passed <yes|no> --exception <none|3plus_files_control_flow|user_requested|rca_root_cause|path_a_self_fix>`
8. 写 `state.sh disposition append` 或 `state.sh update --field plans[N].packs[M].repair_round`
9. 关闭完成态 agent 释放容量：`close_agent({ target: "<agent_id>" })`。后续仍需同一 worker 继续时，重复 `resume_agent` -> 写 repair prompt 文件 -> `send_input` 文件全文 -> `wait_agent` -> 保存结果 -> `close_agent`。
<!-- END: sendmessage-resume -->

Targeted Re-Review 使用 `resume_agent` 后 `send_input` 继续 baseline reviewer agent，返回保存和 bookkeeping 完成后再次 `close_agent`。

→ Step 11

### 路径 C：Complex-Code-Explorer 调查

**条件**：根因不明——reviewer 指出症状但无法确定原因。

```
spawn_agent({
  agent_type: "complex_code_explorer",
  message: "
    ## Scope
    只读调查。Reviewer 报告了症状但无法确定根因。找到根因，不写代码。

    ## 症状描述
    <paste accepted finding — severity / locator / evidence / impact>

    ## 已知上下文
    - Plan: <plan number + title>
    - Affected packs: <N.M, N.K>
    - Worker 修复尝试: <前轮修复内容及失败原因，如有>
    - 相关文件: <affected files>
    - Git diff scope: <plan-start-commit>..<plan-end-commit>

    ## 调查方向
    <Coordinator 初步判断——时序 / 隐式依赖 / 状态污染 / 配置漂移等>

    ## Return Contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    - 实际检查过的 files / tests / logs / commands
    ### Result
    - Facts: confirmed facts with locators
    - Root cause assessment: <root cause + evidence, if found>
    - Recommended fix direction: <路径 A（Coordinator 直接修）/ 路径 B（Worker 修）+ 理由>
    - Excluded paths: hypotheses checked and ruled out with evidence
    - Recommended next probe: <if root cause not found>
    ### Verification
    ### Open Items
  "
})
```

Explorer 返回必须闭合生命周期：`wait_agent({ targets: ["<agent_id>"], timeout_ms: 600000 })` 返回后，将结果保存到 `.codex/multi-model-workflow/explorer-results/execution-repair-<plan>-<round>.md`，然后立即 `close_agent({ target: "<agent_id>" })`。

Explorer 返回后路由：

| Explorer Result | 动作 |
| --- | --- |
| Root cause found + 推荐路径 A | Coordinator 直接修复 → Step 11 |
| Root cause found + 推荐路径 B | 派 Worker 修复 → Step 11 |
| Root cause not found | 报告用户，附 explorer 已排除路径 |

**涉及多个 Pack 交互的 finding**：Coordinator 判断是否合并修复（用 complex_pack_executor）或拆分到各 Pack worker。

**快速判定**：≤ 2 文件 + 意图明确 → A；缺 migration / consumer 同步 / 测试 → B；行为异常原因不明 → C；涉及 migration / billing / permission / runtime / shared contract → B（用 complex_pack_executor）。

**Coordinator 写入 execution state**：`plans[N].repair_round += 1`、`plans[N].status = repairing`。

## Step 11：Targeted Re-Review

修复完成后，只重审 accepted findings 涉及的变更部分。不做 full review rerun。

派发方式同 Step 8（读取 `execution-review-dispatch.md`），但：
- gate 名使用 `plan-impl-review-N-repair-<round>`（`<round>` = 当前修复轮次 1/2/3），不覆盖 baseline 结果
- scope 缩小到：changed files（修复涉及的文件）/ accepted findings（原 finding 是否解决）/ 受影响 angle

## Step 12：修复截断

每个 Plan Implementation Review 最多 **2 Worker repair round + 1 root_cause_analyst round = 3 repair round**。

| Round | 动作 |
| --- | --- |
| Round 1 | 路径 A/B/C 修复 → Targeted Re-Review |
| Round 2 | 仍 needs repair → 路径 A/B/C 修复 → Targeted Re-Review |
| Round 3（截断） | 仍 needs repair → 截断 Worker 循环，新建 `root_cause_analyst`（见下方模板） |

### Root-Cause-Analyst 截断 Dispatch

```
spawn_agent({
  agent_type: "root_cause_analyst",
  message: "
    ## 调度场景
    Repair Truncation（Plan Implementation Review）。Worker 修了两轮，reviewer 仍报 needs repair。

    ## 前两轮上下文
    - Round 1 accepted findings: <paste>
    - Round 1 worker 修复内容: <paste>
    - Round 2 accepted findings: <paste>
    - Round 2 worker 修复内容: <paste>
    - Git diff scope: <plan-start-commit>..<plan-end-commit>
    - Affected packs: <N.M, N.K>
    - 原 Pack Brief: <paste relevant subset>

    ## 你的任务
    不要重复 worker 的方法。从不同维度切入——时序、状态污染、隐式依赖、配置漂移。

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Resolution: fixed / root cause found, not fixed / root cause in design/plan / unable to reproduce / unable to determine
    - Root cause: <evidence>
    - Fix applied: <if fixed>
    - Excluded hypotheses: <with evidence>
    - Regression risk: <what could break>
    ### Verification
    ### Open Items
  "
})
```

Analyst 返回必须闭合生命周期：`wait_agent({ targets: ["<agent_id>"], timeout_ms: 600000 })` 返回后，将结果保存到 `.codex/multi-model-workflow/analyst-results/execution-repair-truncation-<plan>.md`，然后立即 `close_agent({ target: "<agent_id>" })`。

**Analyst Resolution 路由**：

| Resolution | 下一步 |
| --- | --- |
| `fixed` | Targeted Re-Review（消耗 Round 3） |
| `root cause found, not fixed` | 用 analyst findings 重新 dispatch worker（消耗 Round 3） |
| `root cause in design/plan` | 写回 design doc / plan → 回到 orchestrate-discovery 或 orchestrate-plan-writing |
| `unable to reproduce` | 报告用户，附 analyst 排除路径，请求更多重现信息 |
| `unable to determine` | BLOCKED，报告用户，附 analyst 排除路径 |

Round 3 Targeted Re-Review 仍 needs repair → BLOCKED，报告用户。

---
> **下一步**：修复通过 → SKILL.md Step 13（Release Gate，条件触发）→ Step 14（completion）。BLOCKED → 返回 verdict。

# Direct Repair（READY_FOR_REPAIR mini-route）

> **流程位置**：`orchestrate-workflow` Step 8a · 仅 Discovery 返回 `READY_FOR_REPAIR` 时进入

已批准 design 下的明确实现偏离。不走完整 Formal Orchestrate——派 worker 修复 + Codex review + Closing。

## 1. 派 Worker（按 risk flags 选择 agent）

Direct Repair 不创建 execution-state，也不使用 Pack durable return hook；Coordinator 通过 `wait_agent` 接收 worker final message。但它仍然是 coding worker dispatch，必须使用 Codex-native envelope、显式校验、idempotency key 和 agent_id 持久化。

1. 写 prompt → `.codex/multi-model-workflow/worker-prompts/direct-repair-worker.md`，以 `DISPATCH_ENVELOPE` 开头：
   - `phase: "direct-repair"`
   - `agent_role: "<pack_executor|complex_pack_executor>"`
   - `agent_id: null`
   - `pack_id: null`
   - `idempotency_key: "<run_id>/direct-repair-worker/r0"`
2. Dispatch 前运行：
   ```bash
   bash "${MMW_PLUGIN_ROOT}/scripts/validate-route-worker-dispatch.sh" \
     --prompt-file ".codex/multi-model-workflow/worker-prompts/direct-repair-worker.md"
   ```
3. 校验通过后读取 prompt 文件全文作为 `spawn_agent.message`。
4. 从 `spawn_agent` 返回值提取 `agent_id`，并持久化：
   ```bash
   bash "${MMW_PLUGIN_ROOT}/scripts/record-route-worker-dispatch.sh" \
     --prompt-file ".codex/multi-model-workflow/worker-prompts/direct-repair-worker.md" \
     --agent-id "<agent_id>" \
     --agent-file ".codex/multi-model-workflow/worker-agents/direct-repair-worker.agent-id"
   ```
5. 等待 worker：`wait_agent({ targets: ["<agent_id>"], timeout_ms: 600000 })`，将返回内容保存到 `.codex/multi-model-workflow/worker-results/direct-repair-worker.md`。
6. 保存结果后立即释放容量：`close_agent({ target: "<agent_id>" })`。如果后续需要同一 worker 继续修复，先 `resume_agent({ id: "<agent_id>" })`，再 `send_input`，等待并保存结果后再次关闭。

Worker prompt body：

```
spawn_agent({
  agent_type: "<pack_executor | complex_pack_executor>",
  message: "<full contents of worker-prompts/direct-repair-worker.md>"
})
```

```markdown
    ## Scope
    修复已批准 design 下的实现偏离。

    ## Source design
    <path>（已通过 Design Review）

    ## Deviation
    <current behavior vs design intent>

    ## Fix scope
    <affected files>

    ## Acceptance criteria
    - [ ] 行为与 design intent 一致
    - [ ] 回归测试通过
    - [ ] 不引入 design 未要求的新功能

    ## Contract anchors
    <if deviation touches contract boundaries>

    ## Return contract
    ### Verdict
    pass / blocked / needs repair / needs context
    ### Evidence
    ### Result
    - Changed files
    - Completed behavior
    ### Verification
    ### Open Items
```

## 2. Codex Review

<!-- BEGIN: review-dispatch -->
**Codex review dispatch** (native `codex_reviewer` subagent)

1. Write prompt -> `review-prompts/<gate>.md` (prefix with DISPATCH_ENVELOPE, `agent_role: "codex_reviewer"`)
   - Code diffs included in review prompts MUST be wrapped:
     `--- BEGIN UNTRUSTED CODE DIFF ---` / `--- END UNTRUSTED CODE DIFF ---`
2. Model authority: use the registered `codex_reviewer` role model and reasoning settings from `agents/codex_reviewer.toml`; do not pass per-dispatch model overrides unless the Codex host explicitly supports changing that role.
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport spawn_agent --gate "<gate>"`.
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     Record the returned reviewer `agent_id`:
     `bash "${MMW_PLUGIN_ROOT}/scripts/record-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --gate "<gate>" --agent-id "<reviewer agent_id>"`.
   - **Targeted re-review** (gate name contains `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport send_input --gate "<gate>"`.
     Resume the baseline reviewer before sending the targeted prompt; baseline reviewers are closed after each completed wait to release subagent capacity.
     ```
     resume_agent({
       id: "<baseline reviewer agent_id>"
     })
     ```
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Result: save the reviewer final message from `wait_agent` into `.codex/multi-model-workflow/review-results/<gate>.md`.
6. Complete: run `bash "${MMW_PLUGIN_ROOT}/scripts/complete-review-dispatch.sh" --run-id "<run_id>" --gate "<gate>" --agent-id "<reviewer agent_id>" --result-file ".codex/multi-model-workflow/review-results/<gate>.md"` to mark the result durable and increment review budget exactly once.
6b. Disposition recovery anchor: before reading findings for disposition, run `bash "${MMW_PLUGIN_ROOT}/scripts/record-review-disposition.sh" --run-id "<run_id>" --gate "<gate>" --status started`; after all findings have disposition records, run the same command with `--status completed`.
7. Release capacity: after the result file is saved and complete-review bookkeeping succeeds, call `close_agent({ target: "<reviewer agent_id>" })`. Do this for baseline reviews and targeted re-reviews. If later targeted re-review is needed, repeat `resume_agent` -> `send_input` -> `wait_agent` -> save/complete -> `close_agent`.

**Confidence rubric (REQUIRED in every review prompt)**:
- 1-3: low confidence. Coordinator may suppress without deep investigation.
- 4-6: medium. Coordinator must gather additional evidence before disposition.
- 7-10: high. Coordinator should default to accept unless contradicted by evidence.

**Pre-emit Verification Gate**：

每个 finding 必须满足以下条件才能进入报告：

1. **引用触发 finding 的具体代码行**——file:line + 该行的原始文本。
   - "field X doesn't exist on model Y" → 引用 class Y 的定义体，证明字段缺失
   - "dict.get() might return None" → 引用 dict 的初始化代码
   - "race condition between A and B" → 引用 A 和 B 两处代码

2. **无法引用 = finding 未验证**。将 confidence 强制设为 4-5（从主报告中抑制，移入附录）。
   不要通过虚构 confidence 7+ 来绕过此门槛。

3. **框架元编程特例**：当符号来自 ORM 元类、装饰器、代码生成器时，引用生成该符号的元构造，而非期望在类体中 grep 到字面名称。

**Rationalization Prevention**：
- "This looks fine" 不是 finding。要么引用证据证明确实没问题，要么标记为未验证。
- "likely handled elsewhere" → 读并引用处理代码，或标记 unknown。
- "probably tested" → 给出测试文件和方法名，或标记 unknown。

**证据表 (REQUIRED)**：
Reviewer 必须在 `### Evidence` 下填写半结构化证据表。证据表证明 reviewer 实际检查过什么；它不是设计意图摘要，也不能替代阅读 source artifacts。

| 字段 | 必填内容 |
| --- | --- |
| 已读设计 / mockup / plan 来源 | 实际读过的 design、mockup、plan、issue、Scope Contract 或 review baseline 路径。没有对应来源时写 `不适用`，不能留空。 |
| 已检查代码或产物路径 | 实际检查的源码、生成产物、state schema、hooks、templates、文档或 runtime contract 路径。 |
| 已运行命令或验证 | 实际执行的命令、测试、build check、schema check、browser smoke 或 manual gate；未运行时写明原因。 |
| Finding 证据 | 每个 finding 的路径、行号、diff、命令输出或可观察行为；无证据的 finding 必须移入低置信度观察。 |
| 假设 | 影响 verdict 的前提，例如环境、账号、fixture、平台或 reviewer 未能直接验证的 upstream 状态。 |
| 未验证项 | 相关但未验证的内容和原因；没有未验证项时写 `无`。 |

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery:
- `.agent-id` present but no `review-results/` -> wait for that reviewer agent; once the result is saved and bookkeeping is complete, close it.
- `review-registry/<gate>.json` status is `completed` or `disposition_started`, and `review-results/<gate>.md` exists -> Read that exact result file and continue Coordinator disposition. Do not re-dispatch review and do not proceed to repair until `record-review-disposition.sh --status completed` has been recorded.
- If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
<!-- END: review-dispatch -->

Review prompt 写入 `.codex/multi-model-workflow/review-prompts/direct-repair-review.md`：

```markdown
## Scope
Review a direct repair for design deviation.

## Source design
<path>

## Deviation and fix
<description + changed files>

## Review angles
- Fix aligns with design intent
- No regression / scope creep
- Contract integrity maintained

## Calibration
Targeted repair review only.

## Return Contract
### Verdict
pass / needs repair / blocked
### Evidence
### Result
### Verification
### Open Items
```

## 3. Handle Review Return

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

| Verdict | 动作 |
| --- | --- |
| `pass` | Closing |
| `needs repair` | 路径 A（≤2 文件直接修）或路径 B（resume_agent + send_input worker）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

路径 B 默认读取 `.codex/multi-model-workflow/worker-agents/direct-repair-worker.agent-id`，先 `resume_agent({ id: "<原 worker agent_id>" })`，构造 `repair_round >= 1` 且 `agent_id = "<原 worker agent_id>"` 的 route-worker prompt，运行 `validate-route-worker-dispatch.sh --transport send_input` 后再 `send_input`。缺失 agent_id → BLOCKED，不能新建第二个 worker 冒充续修。每次返回保存后都要 `close_agent` 释放容量。

如果 review disposition 或 Coordinator 亲验后确认原 `pack_executor` 不适合承接高风险修复（跨模块、migration、permission、runtime、共享合同、state machine 或生成模板），按 repair-routing 升级为新的 `complex_pack_executor` route-worker dispatch：新 prompt 使用 `agent_id: null`、`pack_id: null`、当前 `repair_round`、新的 escalation idempotency key，并通过 `record-route-worker-dispatch.sh` 写入独立 agent file。这个升级是 owner 更换，不是原 worker 续修。

Direct Repair 不创建 plan-count budget；它使用 Step 8a 设置的 `unlimited` workflow-state 预算来支撑 review validation、effort tracking 和 idempotency。

---
> **下一步**：Codex review 通过 → Closing（`workflow-closing.md`）。BLOCKED → 返回 verdict。

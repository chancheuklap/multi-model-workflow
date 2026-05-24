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
2. Select model by phase:
   - `cursor.phase in {discovery, plan-writing}` -> `model: "gpt-5.5"`, `reasoning_effort: "xhigh"`
   - `cursor.phase in {execution, final-review, bug-investigation, direct-repair, multi-pr-merge, hotfix, quickfix, maintenance}` -> `model: "gpt-5.4"`, `reasoning_effort: "xhigh"`
3. Validate and dispatch (distinguish baseline vs targeted re-review):
   - **Baseline review** (gate name does not contain `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport spawn_agent`.
     ```
     spawn_agent({
       agent_type: "codex_reviewer",
       message: "<full contents of review-prompts/<gate>.md>",
       model: "<phase-selected model>",
       reasoning_effort: "xhigh"
     })
     ```
     Record the returned reviewer `agent_id` into `.codex/multi-model-workflow/review-agents/<gate>.agent-id`.
   - **Targeted re-review** (gate name contains `-repair-`):
     Run `bash "${MMW_PLUGIN_ROOT}/scripts/validate-review-dispatch.sh" --prompt-file ".codex/multi-model-workflow/review-prompts/<gate>.md" --transport send_input`.
     ```
     send_input({
       target: "<baseline reviewer agent_id>",
       message: "<full contents of review-prompts/<gate>.md>"
     })
     ```
     The targeted prompt envelope MUST set `review_intent: "targeted-re-review"`, `exception_code`, and `agent_id` to the baseline reviewer `agent_id`.
4. Wait: `wait_agent({ targets: ["<reviewer agent_id>"], timeout_ms: 600000 })`.
5. Budget: after `wait_agent` returns for either baseline review or targeted re-review, run `bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" budget increment-review --run-id "<run_id>"`.
6. Result: save the reviewer final message from `wait_agent` into `.codex/multi-model-workflow/review-results/<gate>.md`.

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

**Bias indicators (REQUIRED at end of review output)**:
Reviewer must declare which modules/stacks they lack experience with and which findings may be affected.

Compaction recovery: `.agent-id` present but no `review-results/` -> wait for that reviewer agent. If the `.agent-id` is missing for a targeted re-review, mark BLOCKED; do not create a new reviewer for the same baseline.
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

| Verdict | 动作 |
| --- | --- |
| `pass` | Closing |
| `needs repair` | 路径 A（≤2 文件直接修）或路径 B（send_input worker）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

路径 B 必须读取 `.codex/multi-model-workflow/worker-agents/direct-repair-worker.agent-id`，构造 `repair_round >= 1` 且 `agent_id = "<原 worker agent_id>"` 的 route-worker prompt，运行 `validate-route-worker-dispatch.sh --transport send_input` 后再 `send_input`。缺失 agent_id → BLOCKED，不新建第二个 worker 冒充续修。

Direct Repair 不创建 plan-count budget；它使用 Step 8a 设置的 `unlimited` workflow-state 预算来支撑 review validation、effort tracking 和 idempotency。

---
> **下一步**：Codex review 通过 → Closing（`workflow-closing.md`）。BLOCKED → 返回 verdict。

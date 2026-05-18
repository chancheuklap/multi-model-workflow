# Direct Repair（READY_FOR_REPAIR mini-route）

> **流程位置**：`orchestrate-workflow` Step 8a · 仅 Discovery 返回 `READY_FOR_REPAIR` 时进入

已批准 design 下的明确实现偏离。不走完整 Formal Orchestrate——派 worker 修复 + Codex review + Closing。

## 1. 派 Worker（按 risk flags 选择 agent）

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Direct repair: <deviation summary>",
  prompt: "
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
  "
})
```

## 2. Codex Review

```
Agent({
  subagent_type: "codex:codex-rescue",
  description: "Direct repair review: <deviation summary>",
  prompt: "
    --model gpt-5.4
    ## Scope
    Review a direct repair for design deviation.
    ## Source design: <path>
    ## Deviation and fix: <description + changed files>
    ## Review angles
    - Fix aligns with design intent
    - No regression / scope creep
    - Contract integrity maintained
    ## Calibration
    Targeted repair review only.
    ## Return Contract
    ### Verdict: pass / needs repair / blocked
    ### Evidence / Result / Verification / Open Items
  "
})
```

## 3. Handle Review Return

| Verdict | 动作 |
| --- | --- |
| `pass` | Closing |
| `needs repair` | 路径 A（≤2 文件直接修）或路径 B（SendMessage worker）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

Direct Repair 不创建 budget file。

---
> **下一步**：Codex review 通过 → Closing（`workflow-closing.md`）。BLOCKED → 返回 verdict。

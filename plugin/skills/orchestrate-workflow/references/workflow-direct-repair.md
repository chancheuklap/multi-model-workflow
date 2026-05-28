# Direct Repair（READY_FOR_REPAIR mini-route）

> **流程位置**：`orchestrate-workflow` Step 8a · 仅 Discovery 返回 `READY_FOR_REPAIR` 时进入

## Self-Read Protocol

你是 pack-executor 或 complex-pack-executor（执行 Direct Repair）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`repair_context`（包含 `deviation`、`source_design_path`、`fix_scope`、`acceptance`）。
2. 读 `repair_context.source_design_path` 中的设计文档，理解 design intent。
3. 读 `repair_context.fix_scope` 中列出的所有受影响文件。
4. 读本文件（你正在读的这份手册），理解 Return Contract 格式与 Coordinator 处置路由。
5. 修复偏离：使行为与 design intent 一致，通过回归测试，不引入设计未要求的功能。

已批准 design 下的明确实现偏离。不走完整 Formal Orchestrate——派 worker 修复 + Codex review + Closing。

## 1. 派 Worker（按 risk flags 选择 agent）

```
Agent({
  subagent_type: "<pack-executor | complex-pack-executor>",
  description: "Direct repair: <deviation summary>",
  prompt: "
    ## Scope
    修复已批准 design 下的实现偏离。

    ## Repair context
    读 `DISPATCH_ENVELOPE.repair_context`，该字段包含：
    - `source_design_path`: 设计文档路径（已通过 Design Review）——你自读此文档理解 design intent
    - `deviation`: 当前行为与设计意图的偏离描述
    - `fix_scope`: 受影响文件列表——你自读这些文件理解修复范围
    - `acceptance`: 本次修复的验收标准列表

    注：`envelope.repair_context` 由 Coordinator 在派发时填入 `DISPATCH_ENVELOPE` JSON 块。

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

**Read** `plugin/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/direct-repair-review.md`：

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
| `needs repair` | 路径 A（≤2 文件直接修）或路径 B（SendMessage worker）→ baseline re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

Direct Repair 不创建 budget file。

**Read** `plugin/skills/_shared/repair-routing.md` 并按其流程处理 review findings。

## Coordinator 端最小职责

Coordinator 在派发 Direct Repair worker 时只需完成以下动作，其余由 worker 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`phase: "direct-repair"`、`agent_role: "pack-executor"（或 complex-pack-executor）`。
2. 在 `envelope.repair_context` 中写入 `source_design_path`、`deviation`、`fix_scope`（文件列表）、`acceptance`（验收标准）。
3. 触发 `state.sh` 记录 worker 派发状态，保存 `agentId` 以备 SendMessage 修复路径。
4. 等待 worker 返回后，按 Section 2 触发 Codex review 流程。

---
> **下一步**：Codex review 通过 → Closing（`workflow-closing.md`）。BLOCKED → 返回 verdict。

# Route 1 — Formal Orchestrate Phase Dispatch

> **流程位置**：`orchestrate-workflow` Steps 7-14 · Route 1 Formal Orchestrate · phase 全部通过 → Closing（`workflow-closing.md`）

线性管线：Discovery → Plan Writing → Execution → Final Review → Closing。每个 phase skill 通过 `Skill({ skill: "<name>" })` 加载到主线程。

## Step 7：orchestrate-discovery

```
Skill({ skill: "orchestrate-discovery" })
```

## Step 8：Handle Discovery Return

| Discovery Verdict | Coordinator 动作 |
| --- | --- |
| `DISCOVERY_READY` | 检查 issue hierarchy：有 → Step 9；无 → 调用 `to-issues` → Step 9 |
| `DISCOVERY_NOT_NEEDED` | 已有足够清晰的 design → 检查 issue hierarchy → Step 9 |
| `READY_FOR_REPAIR` | 已批准 design 下的实现偏离 → Step 8a（Direct Repair） |
| `NEEDS_USER_DECISION` | 询问用户（一次只问一个），回答后重新进入 discovery |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "discovery"`, `last_gate_timestamp: <now>`。

### Step 8a：Direct Repair（READY_FOR_REPAIR mini-route）

已批准 design 下的明确实现偏离。不走完整 Formal Orchestrate——派 worker 修复 + Codex review + Closing。

**1. 派 Worker**（按 risk flags 选择 agent）：

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

**2. Codex Review**：

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

| Verdict | 动作 |
| --- | --- |
| `pass` | Closing |
| `needs repair` | 路径 A（≤2 文件直接修）或路径 B（SendMessage worker）→ targeted re-review → 最多 2 轮 → Closing |
| `blocked` | 报告用户 |

Direct Repair 不创建 budget file。

---

## Step 9：orchestrate-plan-writing

```
Skill({ skill: "orchestrate-plan-writing" })
```

## Step 10：Handle Plan-writing Return

| Plan-writing Verdict | Coordinator 动作 |
| --- | --- |
| `PLAN_CREATED` | 确认 budget file → Step 11 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_DESIGN_REVIEW` | 回到 discovery Design Review |
| `NEEDS_ISSUES` | 调用 `to-issues` → 重新 Step 9 |
| `NEEDS_TRIAGE` | 调用 `triage` → 重新 Step 9 |
| `NEEDS_DIAGNOSIS` | 调用 `diagnose` → 写回 → 重新 Step 9 |
| `NEEDS_DECISION` | 询问用户 → 回答后 Step 9 |
| `NEEDS_ARCHITECTURE` | 调用 `improve-codebase-architecture` → 写回 → Step 9 |
| `NEEDS_CONTEXT` | 派 `code-explorer` / `zoom-out` → 补充后 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "plan-writing"`, `last_gate_timestamp: <now>`。

---

## Step 11：orchestrate-execution

```
Skill({ skill: "orchestrate-execution" })
```

## Step 12：Handle Execution Return

| Execution Verdict | Coordinator 动作 |
| --- | --- |
| `EXECUTION_PASSED` | Step 13 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9 |
| `NEEDS_ARCHITECTURE` | `improve-codebase-architecture` → 只影响当前 pack → 回 Step 11；改变 plan → 回 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "execution"`, `last_gate_timestamp: <now>`。

---

## Step 13：orchestrate-final-review

```
Skill({ skill: "orchestrate-final-review" })
```

## Step 14：Handle Final Review Return

| Final Review Verdict | Coordinator 动作 |
| --- | --- |
| `FINAL_REVIEW_PASSED` | Closing |
| `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` | Closing（release review 已内部处理） |
| `NEEDS_EXECUTION` | 回到 Step 11（只处理 Final Review 标出的问题） |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9 |
| `BLOCKED` | 报告用户 |

### Budget 与 Backflow

回流不重置 `budget_used`。Direction Check 在 80% 时仍触发。Plan revision 改变 `pack_count` → plan-writing Step 12a 更新 `budget_total`。

**更新 Budget File**：`last_gate_phase: "final-review"`, `last_gate_timestamp: <now>`。

# Route 1 — Formal Orchestrate Phase Dispatch

> **流程位置**：`orchestrate-workflow` Steps 7-14 · Route 1 Formal Orchestrate · phase 全部通过 → Closing（`workflow-closing.md`）

线性管线：Discovery → Plan Writing → Execution → Final Review → Closing。每个 phase skill 通过 `Skill({ skill: "multi-model-workflow:<name>" })` 加载到主线程。

## Step 7：orchestrate-discovery

```
Skill({ skill: "multi-model-workflow:orchestrate-discovery" })
```

## Step 8：Handle Discovery Return

| Discovery Verdict | Coordinator 动作 |
| --- | --- |
| `DISCOVERY_READY` | 检查 issue hierarchy：有 → Step 9；无 → Step 8b（to-issues + 上下文传递）→ Step 9 |
| `DISCOVERY_NOT_NEEDED` | 已有足够清晰的 design → 检查 issue hierarchy → Step 9 |
| `READY_FOR_REPAIR` | 已批准 design 下的实现偏离 → Step 8a（Direct Repair） |
| `NEEDS_USER_DECISION` | 询问用户（一次只问一个），回答后重新进入 discovery |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "discovery"`, `last_gate_timestamp: <now>`。

### Step 8b：to-issues 上下文传递

调用 to-issues 前，Coordinator 必须：

1. **Read** Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）获取 slug
2. **Read** 设计文档（`docs/orchestrate/design/<slug>.md`）确认内容在上下文中
3. 调用 `Skill({ skill: "to-issues", args: "docs/orchestrate/design/<slug>.md" })`

to-issues 运行时需要设计文档的完整内容来拆 issue。如果 Coordinator 上下文中已无设计文档内容（因 compact 或 phase 切换），必须重新 Read。

### Step 8a：Direct Repair（READY_FOR_REPAIR mini-route）

→ `references/workflow-direct-repair.md`（Worker 修复 + Codex review + Closing）

---

## Step 9：orchestrate-plan-writing

```
Skill({ skill: "multi-model-workflow:orchestrate-plan-writing" })
```

## Step 10：Handle Plan-writing Return

| Plan-writing Verdict | Coordinator 动作 |
| --- | --- |
| `PLAN_CREATED` | 确认 budget file → Step 11 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_DESIGN_REVIEW` | 回到 discovery Design Review |
| `NEEDS_ISSUES` | `Skill({ skill: "to-issues" })` → 重新 Step 9 |
| `NEEDS_TRIAGE` | `Skill({ skill: "triage" })` → 重新 Step 9 |
| `NEEDS_DIAGNOSIS` | `Skill({ skill: "diagnose" })` → 写回 → 重新 Step 9 |
| `NEEDS_DECISION` | 询问用户 → 回答后 Step 9 |
| `NEEDS_ARCHITECTURE` | `Skill({ skill: "improve-codebase-architecture" })` → 写回 → Step 9 |
| `NEEDS_CONTEXT` | 派 `code-explorer` / `Skill({ skill: "zoom-out" })` → 补充后 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "plan-writing"`, `last_gate_timestamp: <now>`。

---

## Step 11：orchestrate-execution

```
Skill({ skill: "multi-model-workflow:orchestrate-execution" })
```

## Step 12：Handle Execution Return

| Execution Verdict | Coordinator 动作 |
| --- | --- |
| `EXECUTION_PASSED` | Step 13 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9 |
| `NEEDS_ARCHITECTURE` | `Skill({ skill: "improve-codebase-architecture" })` → 只影响当前 pack → 回 Step 11；改变 plan → 回 Step 9 |
| `BLOCKED` | 报告用户 |

**更新 Budget File**：`last_gate_phase: "execution"`, `last_gate_timestamp: <now>`。

---

## Step 13：orchestrate-final-review

```
Skill({ skill: "multi-model-workflow:orchestrate-final-review" })
```

## Step 14：Handle Final Review Return

| Final Review Verdict | Coordinator 动作 |
| --- | --- |
| `FINAL_REVIEW_PASSED` | Closing |
| `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` | Closing（release review 已内部处理） |
| `NEEDS_EXECUTION` | 回到 Step 11（只处理 Final Review 标出的问题）。**最多 1 次**；第 2 次 → BLOCKED 报告用户 |
| `NEEDS_DISCOVERY` | 回到 Step 7 |
| `NEEDS_PLAN_REVISION` | 回到 Step 9 |
| `BLOCKED` | 报告用户 |

### Budget 与 Backflow

回流不重置 `budget_used`。Direction Check 在 80% 时仍触发。Plan revision 改变 `pack_count` → plan-writing Step 12a 更新 `budget_total`。

**更新 Budget File**：`last_gate_phase: "final-review"`, `last_gate_timestamp: <now>`。

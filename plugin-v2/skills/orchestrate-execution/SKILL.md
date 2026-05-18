---
name: orchestrate-execution
description: "Plan Review 通过后、已有 reviewed plan + confirmed Task Pack inventory 时主动使用。覆盖完整 Pack 执行循环：预执行准备 → 逐 Pack 派 Worker → Pack Review → Coordinator 验证 + Disposition → 修复分流 → Targeted Re-Review → 修复截断 → Release Gate → Git Checkpoint → 循环释放。纯 Coordinator 技能：主线程读取本技能执行调度、review 接收、修复路由和进度追踪；不由 Sub-Agent 消费。"
---

# Orchestrate Execution

Plan Review 通过 → 逐 Pack 派 Worker → Pack Review → 修复 → Release Gate → Git Checkpoint → 循环 → 全部通过 → Final Review。

**连续执行**：不在 pack 之间暂停汇报或问"要不要继续"。BLOCKED 或业务决策才停。

---

## Steps 1-3：预执行准备

→ `references/execution-preparation.md`（读 plan inventory + 构建执行队列 + 验证 Scope Contract / Git / Budget）

## Steps 4-9：Pack 执行 + Review 循环（per pack）

→ `references/execution-pack-review-cycle.md`（选 worker → 构造 Pack Brief → 派发 → 处理返回 → Pack Review → Disposition）

Worker dispatch template → `references/execution-worker-dispatch.md`（Step 5 读取）
Pack Review dispatch template → `references/execution-review-dispatch.md`（Step 8 读取）

通过 → Step 13。Needs repair → 读取 `references/execution-repair-truncation.md`。

## Steps 10-12：修复分流 + 截断（仅 needs repair 时）

→ `references/execution-repair-truncation.md`（路径 A/B/C → Targeted Re-Review → 最多 3 轮 → RCA 截断）

## Steps 13-16：Release Gate + Git + 并行合并 + 过渡

→ `references/execution-completion.md`（Early Release Gate + Git Checkpoint + 并行 Worktree 合并 + Backflow + Plan Checkbox + 进度 + Re-entry from Final Review + 不存在非阻塞项）

## 返回

```text
### Verdict
EXECUTION_PASSED | NEEDS_DISCOVERY | NEEDS_PLAN_REVISION | NEEDS_ARCHITECTURE | BLOCKED

### Pack execution summary
- Total packs / Passed / Parallel merges

### Per-pack results
| Pack | Worker | Risk | Repair rounds | Release gate | Status |

### Review budget
- Budget total / used / Direction checks triggered

### Findings summary
- Total / Accepted+repaired / Rejected / Out of scope (issues created)

### Git state
### Plan checkbox progress
### Open items
### Next route
- orchestrate-final-review / orchestrate-discovery / orchestrate-plan-writing / user decision / blocked
```

---
name: orchestrate-execution
description: "已有 reviewed plan + Task Pack inventory 时使用。逐 Pack 派 Worker → Pack Review → Disposition → 修复 → Release Gate → Git Checkpoint。产出：所有 pack 通过 + review budget 消耗。"
---

# Orchestrate Execution

Plan Review 通过 → 逐 Pack 派 Worker → Pack Review → 修复 → Release Gate → Git Checkpoint → 循环 → 全部通过 → Final Review。

**连续执行**：不在 pack 之间暂停汇报或问"要不要继续"。BLOCKED 或业务决策才停。

---

## Steps 1-3：预执行准备

**Read** `references/execution-preparation.md` 并严格执行（读 plan inventory + 构建执行队列 + 验证 Scope Contract / Git / Budget）。

## Steps 4-9：Pack 执行 + Review 循环（per pack）

**Read** `references/execution-pack-review-cycle.md` 并严格执行（选 worker → Pre-dispatch Context Transfer → 构造 Pack Brief → 派发 → 处理返回 → Pack Review → Disposition）。

Step 5 构造 Pack Brief 时 **Read** `references/execution-worker-dispatch.md` 获取模板。
Step 8 派发 Reviewer 时 **Read** `references/execution-review-dispatch.md` 获取模板。

通过 → Step 13。Needs repair → 读取 `references/execution-repair-truncation.md`。

## Steps 10-12：修复分流 + 截断（仅 needs repair 时）

→ `references/execution-repair-truncation.md`（路径 A/B/C → Targeted Re-Review → 最多 3 轮 → RCA 截断）

## Step 13：Early Release Gate（条件触发）

→ `references/execution-release-gate.md`（仅 pack 触碰发布风险面时读取）

## Steps 14-16：Git Checkpoint + 并行合并 + 过渡

→ `references/execution-completion.md`（Git Checkpoint + 并行 Worktree 合并 + Backflow + Plan Checkbox + 进度 + Re-entry from Final Review + 不存在非阻塞项）

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
- Total / Accepted+repaired / Rejected / Out of scope (issues created) / Needs evaluation (issues created)

### Git state
### Plan checkbox progress
### Open items
### Next route
- orchestrate-final-review / orchestrate-discovery / orchestrate-plan-writing / user decision / blocked
```

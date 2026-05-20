---
name: orchestrate-execution
description: "已有 reviewed plan + Task Pack inventory 时使用。Plan 级两层循环：外层逐 Plan 串行，内层逐 Pack 派 Worker → Git Checkpoint → Plan Implementation Review → Disposition → 修复 → Release Gate。产出：所有 Plan 通过 + review budget 消耗。"
---

# Orchestrate Execution

Plan Review 通过 → 两级循环（Plan → Pack）→ Pack 执行 + Git Checkpoint → Plan Implementation Review → 修复 → Release Gate → 循环 → 全部 Plan 通过 → Final Review。

**连续执行**：不在 pack 之间暂停汇报或问"要不要继续"。BLOCKED 或业务决策才停。

---

## Steps 1-3：预执行准备

**Read** `references/execution-preparation.md` 并严格执行（读 plan inventory + 构建两级执行队列 + 创建 execution-state file + 验证 Scope Contract / Git / Budget）。

## Steps 4-9：Plan 执行 + Review 循环（per plan）

**Read** `references/execution-plan-review-cycle.md` 并严格执行。

每个 Plan 的内部流程：
1. **Steps 4-7c**（per pack）：选 worker → Pre-dispatch Context Transfer → 构造 Pack Brief → 派发 → 处理返回 → Open Items → Git Checkpoint → 合并 Worktree
2. **Step 8**：所有 Pack 完成 → Plan Implementation Review（Codex dispatch）
3. **Step 9**：接收 findings → Disposition

Step 5 构造 Pack Brief 时 **Read** `references/execution-worker-dispatch.md` 获取模板。
Step 8 派发 Plan Implementation Review 时 **Read** `references/execution-review-dispatch.md` 获取模板。

通过 → Step 13。Needs repair → 读取 `references/execution-repair-truncation.md`。

## Steps 10-12：修复分流 + 截断（仅 needs repair 时）

→ `references/execution-repair-truncation.md`（Affected packs 归属 → 路径 A/B/C → Targeted Re-Review → 最多 3 轮 → RCA 截断）

## Step 13：Early Release Gate（条件触发）

→ `references/execution-release-gate.md`（仅 Plan 中有 Pack 触碰发布风险面时读取）

## Steps 14-16：Plan 完成 + 推进 + 过渡

→ `references/execution-completion.md`（标记 Plan 完成 + 推进下一 Plan + Backflow + Plan Checkbox + 进度 + Re-entry from Final Review + 不存在非阻塞项）

## 返回

```text
### Verdict
EXECUTION_PASSED | NEEDS_DISCOVERY | NEEDS_PLAN_REVISION | NEEDS_ARCHITECTURE | BLOCKED

### Plan execution summary
- Total plans / Passed / Total packs / Parallel merges

### Per-plan results
| Plan | Packs | Review verdict | Repair rounds | Release gate | Status |

### Per-pack results
| Pack | Plan | Worker | Risk | Repair rounds | Status |

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

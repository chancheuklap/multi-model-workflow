---
name: orchestrate-final-review
description: "所有 Pack Review 通过后、orchestrate-execution 返回 EXECUTION_PASSED 时由 orchestrate-workflow 调用。覆盖完整最终审查流程：前置条件验证 → 增强型 Codex 审查（regression sweep + design intent coverage + cross-pack audit + 独立代码级审计）→ Coordinator 验证 + Disposition → 修复分流 → Targeted Re-Review → 修复截断 → Coordinator 清扫遗留尾巴 → Release Gate → 业务汇报 → 返回 verdict 给 orchestrate-workflow 执行 Closing。纯 Coordinator 技能：主线程读取本技能执行调度、review 接收、修复路由、清扫和汇报；不由 Sub-Agent 消费。"
---

# Orchestrate Final Review

所有 pack 通过 Pack Review + Git Checkpoint 后进入。验证整体实现是否满足 design intent，清扫所有遗留尾巴，评估发布风险，向用户汇报业务结果，返回 verdict 给 orchestrate-workflow 执行 Closing。

**两大职责**：
1. **意图验证**：检查落地的代码是否偏离了设计文档、计划文档和 Issue 文档。Pack Review 验证每个 pack 自身——Final Review 验证所有 pack 合在一起是否实现了设计的完整意图。
2. **清扫遗留尾巴**：Coding Worker 经常因为 "Out of Scope" 或 "非阻塞项" 把东西搁置。Final Review 要全部揪出来、全部解决掉。项目中不存在 "非阻塞项" 这种概念。

**Final Review 不做 Closing**——不 cleanup budget/scope/active-run-id，不 commit，不 push，不 PR。这些是 orchestrate-workflow Closing（Steps 21-24）的职责。Final Review 以 verdict 返回结束。

---

## Steps 1-3：前置条件

→ `references/final-review-preconditions.md`（读 source artifacts + 验证前置条件 + Budget Check）

## Steps 4-5：增强型审查派发

→ `references/final-review-angles.md`（与 Pack Review 分工 + 2 baseline Codex dispatch templates）

## Steps 6-8：接收 + Disposition

→ `references/final-review-disposition.md`（Coordinator 主动验证 + 6 disposition + Gap 分类 + Backflow 路由）

通过 → Step 13。有 accepted findings → 读取 `references/final-review-repair.md`。

## Steps 9-12：修复分流 + 截断（仅 needs repair 时）

→ `references/final-review-repair.md`（路径 A/B/C + 回 Execution 判定 + Targeted Re-Review + 3 轮截断 + RCA）

## Steps 13-15, 19-20：清扫 + 业务汇报 + Verdict

→ `references/final-review-completion.md`（Coordinator 清扫遗留尾巴 + 业务汇报组装 + Verdict 判定）

## Steps 16-18：Final Release Gate（条件触发）

→ `references/final-review-release-gate.md`（仅 diff 触碰发布风险面时读取）

---

## 返回

```text
### Verdict
FINAL_REVIEW_PASSED | FINAL_REVIEW_PASSED_WITH_RELEASE_RISK |
NEEDS_EXECUTION | NEEDS_DISCOVERY | NEEDS_PLAN_REVISION | BLOCKED

### Review dispatch summary
- Baseline 1: <verdict> / Baseline 2: <verdict>
- Repair rounds: <count>
- Release gate: triggered / not triggered / passed / blocked

### Baseline 1 result
Regression Sweep:
Intent Coverage: X / Y intents covered
Cross-Pack Audit:
Critical findings: <count>

### Baseline 2 result
Code-Level Audit:
Critical findings: <count>

### Findings summary
- Total findings received: <count>
- Accepted + repaired: <count>
- Rejected: <count>
- Out of scope (issues created): <count>

### Lingering tail sweep
- Worker Open Items processed: <count>
- New TODO/FIXME found and processed: <count>
- Out-of-scope dispositions reviewed: <count>
- GitHub issues created: <refs>
- Immediate fixes applied: <count>

### Release gate
- Risk surfaces: <list or N/A>
- Release blockers: <count or none>
- Release review verdict: pass / N/A

### Business report
新增能力:
验证证据:
残余风险:
发布检查:

### Git state
- Branch: <current branch>
- Commits since starting: <count>
- Clean: yes / no

### Review budget
- Budget total: <N>
- Budget used: <N> (including this phase)
- Direction checks triggered: <count>

### Open items
- Blockers: <if any>
- HITL: <if any>
- Issues created: <GitHub issue refs>

### Next route
- orchestrate-workflow Closing / orchestrate-execution re-entry / orchestrate-discovery / orchestrate-plan-writing / user decision / blocked
```

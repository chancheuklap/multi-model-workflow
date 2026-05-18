---
name: orchestrate-multi-pr-merge
description: "多个来自同一大设计/大计划的并行 PR 需要合并审查时由 orchestrate-workflow Route 3 调用。覆盖完整流程：阅读全部文档建立正确状态理解 → 并行 explorer 发现 PR 间冲突 → 冲突分类与修复分流（简单 / 复杂根因明确 / 系统性根因不明）→ 系统性冲突派 root-cause-analyst 调查根因 → coding worker 落地修复 → Coordinator 验证 → Codex 跨 PR 集成审查 → 按依赖顺序合并 → 返回 verdict 给 orchestrate-workflow 执行 Closing。纯 Coordinator 技能：主线程读取本技能执行调度、冲突分析、修复路由和合并操作；不由 Sub-Agent 消费。"
---

# Orchestrate Multi-PR Merge

多个来自同一大设计/大计划的并行 PR 需要合并。PR 与 PR 之间可能存在代码冲突、功能冲突、意图冲突——这些 PR 各自经历了路线 1（Formal Orchestrate），各自通过了自己的 Final Review，但它们之间的交互尚未验证。

**核心原则**：
- 冲突是 **PR 与 PR 之间**的冲突，不是 PR 与 main 的冲突。
- 代码合并冲突好解决，**功能和意图冲突**最难、最需要思考。
- **Coordinator 读文档**建立方向，**Explorer 做代码验证**——节省主线程上下文。
- **系统性冲突先调查再修**——不让 worker 盲目尝试修复根因不明的冲突。
- 修复后由 **Coordinator 验证**，因为 Coordinator 最了解冲突的方向和正确状态。
- 所有 PR **并行分析**，不是逐个顺序处理。

**Multi-PR Merge 不做 Closing**——不 push，不 PR，不 cleanup。这些是 orchestrate-workflow Closing 的职责。以 verdict 返回结束。

**Multi-PR route 不创建 Budget File**——Codex 审查 dispatch 控制在合理范围内（通常 2-4 次：1-2 full review + 1-2 targeted re-review）。

---

## Steps 1-3：入口 + 文档理解

→ `references/merge-preparation.md`（读全部文档 + 建立合并后正确状态模型 + Scope Contract + Git State）

## Steps 4-8：并行 PR 分析 + 冲突分类

→ `references/merge-conflict-discovery.md`（Explorer 派发 + 冲突发现 + 三级分类 + 简单冲突 Coordinator 直接修）

无冲突 → Step 16。有冲突 → 按分类路由：简单走 Step 8；复杂根因明确走 Step 12；系统性走 Step 9。

## Steps 9-11：系统性冲突 — Root-Cause-Analyst 调查（仅系统性冲突时）

→ `references/merge-rca-investigation.md`（Analyst dispatch + PR 冲突专用方法论 + Resolution 路由）

## Steps 12-15：Coding Worker 修复 + 验证 + 循环

→ `references/merge-conflict-repair.md`（Worker dispatch templates + 验证 + 冲突解决循环控制 + 3 轮上限）

## Steps 16-22：Codex 集成审查 + 顺序合并 + 返回

→ `references/merge-completion.md`（跨 PR 集成审查 + Disposition + 顺序合并 + 不存在非阻塞项 + Verdict 判定）

---

## 返回

```text
### Verdict
MERGE_COMPLETE | NEEDS_DISCOVERY | NEEDS_USER_DECISION | BLOCKED

### PRs merged
| PR | Branch | Merge order | Status |
<per-PR status>

### Conflict resolution summary
- Total conflicts found: <count>
- Simple (coordinator fix): <count>
- Complex (worker fix): <count>
- Systemic (analyst → worker): <count>
- Design/intent conflicts: <count>

### Per-conflict details
| # | Type | PRs | Root cause | Resolution | Verified |

### Integration review
- Codex review verdict: pass / needs repair
- Findings: <count> / Accepted: <count> / Rejected: <count>
- Repair rounds: <count>

### Git state
- Branch: <current branch>
- Merge commits: <list>
- Clean: yes / no

### Test results
- Full suite: pass / fail
- Validation commands: pass / fail

### Open items
- Blockers: <if any>
- Issues created: <GitHub issue refs>
- Design updates needed: <if any>

### Next route
- orchestrate-workflow Closing / orchestrate-discovery / user decision / blocked
```

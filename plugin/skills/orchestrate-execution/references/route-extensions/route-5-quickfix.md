> **[DEPRECATED]** 此文件的权威副本已迁移到 `orchestrate-workflow/references/route-extensions/route-5-quickfix.md`。Entry Gate 路由属于 workflow 职责。本文件保留供过渡期参考，后续确认无引用后删除。

# Route 5: Quick Fix

> **入口**：`orchestrate-workflow` Step 1 Entry Gate 匹配 quick fix / 小改动 / 调整

小规模修复路径。消费现有 design，single Pack，single review round。

**触发关键词**: quickfix, 快速修复, 小改动, 一行修复, trivial fix

**行为差异**（相对 formal route）:

## Phase 简化

- **skip Discovery**：消费现有 design（用户提供 design doc 路径或明确描述）。不走讨论。
- **Plan Writing 简化**：单 Pack plan。Coordinator 自己写，不派 plan-writer。
- **skip Plan Review**：Coordinator 自检 plan 即可。
- `budget_status = "unlimited"`, `review_total = "unlimited"`, `effort_total = "unlimited"`

## 执行约束

- **single Pack**：只允许一个 Task Pack。多文件修改也压到一个 Pack。
- **single Worker**：只派一个 pack-executor（不用 complex-pack-executor，除非触碰 billing/auth/migration）。
- **single review round**：Plan Implementation Review 一轮。needs repair → 修复 → pass 或 BLOCKED。不允许 3 轮截断。

## Plan 内容

```text
Pack 1.1: <fix title>
Goal behavior: <one sentence>
Implementation tasks:
  1. <具体修复动作>
Owned files: <1-3 files>
Acceptance criteria:
  - [ ] <behavior criterion>
Verification commands:
  - <command> → Expected: <result>
Risk flags: trivial | normal
```

## Review Focus

Plan Implementation Review 只关注：
- 修复是否正确解决了问题
- 是否引入新问题
- 测试是否覆盖修复行为
- 不审设计完备性（现有 design 已 reviewed）

---
> **下一步**：Review 通过 → orchestrate-workflow Closing。needs repair → 修复 + targeted re-review（最多 2 轮）。

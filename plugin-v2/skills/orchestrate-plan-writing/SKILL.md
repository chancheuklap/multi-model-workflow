---
name: orchestrate-plan-writing
description: "已有 reviewed design + issue hierarchy 时使用。派 plan-writer → Plan Entry Gate → Plan Review → Git Checkpoint。产出：reviewed plan + Task Pack inventory + budget_total。"
---

# Orchestrate Plan Writing

Source design + issue hierarchy → plan-writer 产出 plan → Codex Plan Review → Git Checkpoint → 进入 Execution。

**plan-writer 消费说明**：plan-writer 通过 `skills: ["orchestrate-plan-writing"]` 自动加载本技能，启动后读取 `references/plan-writing-methodology.md`。

---

## Step 0：Re-entry 检测

| 条件 | 下一步 |
| --- | --- |
| 无已有 plan | Step 1 |
| 已有 plan + `NEEDS_PLAN_REVISION` context | 读取 `references/plan-preconditions.md` 修订模式 → Step 11 |
| 已有 plan + 无修订 context | Step 1（忽略旧 plan） |

## Steps 1-2：前置条件

验证 source design 已 reviewed + issue hierarchy 已就绪 + Scope Contract + Budget File 存在。缺件时读取 `references/plan-preconditions.md` 路由。

## Steps 3-8：写作方法论

**Read** `references/plan-writing-methodology.md`（plan-writer 消费；Coordinator 按此理解 plan 结构，为 dispatch brief 构造做准备）。

## Steps 9-10：派发 plan-writer + 处理返回

**Read** `references/plan-writer-dispatch.md` 并严格执行（Pre-dispatch Context Transfer + dispatch template 填充 + 9 种 verdict 路由）。

## Steps 11-12a：Plan Entry Gate + Task Pack Inventory Gate + Budget 赋值

→ `references/plan-gates.md`（gate 检查条件 + budget_total 首次赋值 `2N + 12`）

## Steps 13-14：Plan Review

Budget check（`budget_used + 1 ≤ budget_total`，80% 触发 Direction Check）→ 读取 `references/plan-review-dispatch.md` 派发 `codex:codex-rescue --model gpt-5.4`。

## Steps 15-18：Disposition + 修复 + 截断

→ `references/plan-review-resolution.md`（Coordinator 亲验 → disposition → 修复路由 A/B/C → 最多 2 轮 → 截断路由）

通过 → Step 19。

## Step 19：Git Checkpoint

`git add` + `git commit`。Plan-writer 不 commit；Coordinator 统一提交。Design doc repair 和 plan doc 分别提交。

## Step 20：返回

```text
### Verdict
PLAN_CREATED | NEEDS_DISCOVERY | NEEDS_DESIGN_REVIEW | NEEDS_ISSUES |
NEEDS_TRIAGE | NEEDS_DIAGNOSIS | NEEDS_DECISION | NEEDS_ARCHITECTURE |
NEEDS_CONTEXT | BLOCKED

### Plan path
### Plan Review
- Review dispatched / Findings dispositioned / Repairs applied / Rounds used
### Issue mapping
- Large issues / Task Packs / Dependencies
### Quality gate
- Overdesign / Underdesign / Coverage / Type consistency / Largest risk
### Git state
### Open items
### Next route
- orchestrate-execution / upstream route / user decision / blocked
```

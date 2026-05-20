---
name: orchestrate-plan-writing
description: "已有 reviewed design + issue hierarchy 时使用。派 plan-writer → Plan Entry Gate → Plan Review → Git Checkpoint。产出：reviewed plan + Task Pack inventory + budget_total。"
---

# Orchestrate Plan Writing

Source design + issue hierarchy → **逐个 issue 派发 plan-writer** → 全部 plan 写完后 Plan Review → Git Checkpoint → 进入 Execution。

**每个大 issue 对应一份 plan 文件**。Coordinator 读取 `issues/<slug>/` 目录，逐个 issue 派发 plan-writer，每个 plan-writer 只写一份 plan。Plan 文件编号与 issue 文件编号一一对应。

---

## Step 0：Re-entry 检测

| 条件 | 下一步 |
| --- | --- |
| 无已有 plan | Step 1 |
| 已有部分 plan + `NEEDS_PLAN_REVISION` context | 读取 `references/plan-preconditions.md` 修订模式 → Step 11 |
| 已有全部 plan + 无修订 context | Step 1（忽略旧 plan） |

## Steps 1-2：前置条件

验证 source design 已 reviewed + issue hierarchy 已就绪 + Scope Contract + Budget File 存在。缺件时读取 `references/plan-preconditions.md` 路由。

## Steps 3-8：写作方法论

**Read** `references/plan-writing-methodology.md`（plan-writer 消费；Coordinator 按此理解 plan 结构，为 dispatch brief 构造做准备）。

## Steps 9-10：逐 issue 派发 plan-writer + 处理返回

**Read** `references/plan-writer-dispatch.md` 并严格执行。

Coordinator 列出 `docs/orchestrate/issues/<slug>/` 目录下的所有大 issue 文件（`001-*.md, 002-*.md, ...`），然后**逐个 issue 派发 plan-writer**：

1. 按 issue 编号顺序遍历
2. 每次派发一个 plan-writer，传入设计文档 + 当前这个 issue 文件
3. plan-writer 写出 `docs/orchestrate/plans/<slug>/00N-<issue-slug>.md`（编号与 issue 文件对应）
4. 处理 plan-writer 返回（verdict 路由见 dispatch 文档）
5. 下一个 issue，直到全部完成

全部 plan-writer 返回 `PLAN_CREATED` 后，进入 Step 11。任一 plan-writer 返回 upstream verdict → 按 verdict 路由处理后重新进入。

## Steps 11-12a：Plan Entry Gate + Task Pack Inventory Gate + Budget 赋值

**Read** `references/plan-gates.md`（对 `plans/<slug>/` 下所有 plan 文件做 gate 检查 + budget_total 首次赋值 `2N + 12`，N = 所有 plan 的 pack 总数）。

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

### Plan directory + file count
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

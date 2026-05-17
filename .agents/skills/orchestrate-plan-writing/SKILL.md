---
name: orchestrate-plan-writing
description: "把已 review 的 design document 和已确认的 vertical issue hierarchy 转成 issue-backed implementation plan。不执行代码，不做 review，不派 worker。"
---

# Orchestrate Plan Writing

只负责生成或修复 plan。Plan 生成后交回 `orchestrate-workflow` 进入 Phase 0b。

## 前置条件

必须同时具备：

- source design / SPEC / PRD / bug brief（已通过 Phase 0a 或等价 review）
- `to-issues` 产出的 vertical large issues 和 vertical small issues

| 缺件 | 返回 | 路由 |
| --- | --- | --- |
| 无 source design | `NEEDS_DISCOVERY` | `orchestrate-discovery` |
| design 未 review | `NEEDS_DESIGN_REVIEW` | Phase 0a |
| 缺 large/small issue | `NEEDS_ISSUES` | `to-issues` |
| issue ready state 不清 | `NEEDS_TRIAGE` | `triage` |
| 业务术语或验收不清 | `NEEDS_DISCOVERY` | `orchestrate-discovery` |
| bug 缺复现或 hypothesis | `NEEDS_DIAGNOSIS` | `diagnose` |
| 需要方案比较 | `NEEDS_DECISION` | user / `prototype` |
| 架构摩擦反复阻塞 | `NEEDS_ARCHITECTURE` | `improve-codebase-architecture` |
| 模块地图不足 | `NEEDS_CONTEXT` | `zoom-out` / `code_explorer` |

## 写作流程

1. 读取 source design，提取 goal、architecture、tech stack、行为、合同边界、失败场景。
2. 读取 `references/plan-contract.md`，确认 issue→pack 映射成立，按模板写 plan。
3. 读取 `references/plan-checklist.md`，删过度设计、补设计不足、自审修正。
4. 保存到 `docs/orchestrate/plans/YYYY-MM-DD-<feature>.md`。

## 固定结构

```
source design → vertical large issue → vertical small issue → Task Pack → pack-local tasks
```

- 一级章节 = large issue。每个 Task Pack = 一个 small issue。
- `Execution owner` 必须是 `Orchestrate Workflow`。
- Task Pack 是 Orchestrate 派发单位；细 task 只服务 pack 内执行。

## 返回格式

```text
### Verdict
PLAN_CREATED | NEEDS_DISCOVERY | NEEDS_DESIGN_REVIEW | NEEDS_ISSUES | NEEDS_TRIAGE | NEEDS_DIAGNOSIS | NEEDS_DECISION | NEEDS_ARCHITECTURE | NEEDS_CONTEXT

### Plan path
- <path>

### Issue mapping
- Large issues:
- Task Packs:
- Dependencies:

### Quality gate
- Overdesign checked:
- Underdesign checked:
- Largest remaining risk:

### Open items
- Blockers / HITL:
```

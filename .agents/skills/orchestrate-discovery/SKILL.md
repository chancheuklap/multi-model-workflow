---
name: orchestrate-discovery
description: "把新功能、issue、bug、反馈、PRD 或模糊讨论转成可进入 Phase 0a 的设计文档。不写 plan，不拆 Task Pack，不派 worker，不执行代码。"
---

# Orchestrate Discovery

只负责生成或修订 design document。

## 流程

1. 读取项目上下文：根 `AGENTS.md`、相关 SPEC / ADR / GUIDE / CONTEXT、相关目录 `agents.overrides.md`。
2. 读取 `references/discovery-input.md`，按输入类型（新功能 / bug / issue / 反馈）执行对应章节。
3. 每轮讨论检查术语、对象 owner、状态、边界和现有文档一致性；发现不清或冲突时按 `discovery-input.md` 的 Domain Alignment 章节处理。
4. 可从代码和文档确认的事实先查证；只把无法自行确定的产品、业务、架构取舍交给用户。每次只问一个会改变设计的问题。
5. 信息足够后按 `references/design-document-contract.md` 写 design document。
6. 写完后按 `references/discovery-checklist.md` 自检并修正。
7. 返回 verdict。

## 边界规则

- 没有可 review 的 design document 前，不进入 plan-writing、Phase A 或 worker 派发。
- 只消费 upstream skill 产出的 clarified context / diagnosis facts / module map / prototype verdict / architecture finding / triage state；upstream 如需发布 issue 或改代码，先交回 Orchestrate parent 确认 scope。
- upstream skill 结论必须写回 design document / domain docs，不停留在聊天记录。
- 已批准 design 下的明确实现偏离 → 返回 `READY_FOR_REPAIR`，不新建 design。
- 用户已有 PRD → 当 source material 消费，不重新生成。
- 设计问题太大 → 先拆成多个 design document。
- 已有 design 足够清楚 → 直接返回 `DISCOVERY_NOT_NEEDED`。

## 返回格式

```text
### Verdict
DISCOVERY_READY | DISCOVERY_NOT_NEEDED | READY_FOR_REPAIR | NEEDS_USER_DECISION | BLOCKED

### Design path
- <path or not created>

### Discovery result
- Problem:
- Target behavior:
- Key decisions:
- Acceptance:
- Out of scope:
- Domain alignment resolved:
- Remaining ambiguity:

### Next route
- Phase 0a / Direct Repair / user decision / blocked
```

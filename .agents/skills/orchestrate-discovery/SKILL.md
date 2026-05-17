---
name: orchestrate-discovery
description: "当 AgentFlow 的新功能、issue、backlog、现有 PRD、系统性 bug、wrong state、performance regression、UI / UX 反馈、截图反馈、测试反馈、系统性改造或产品讨论还没有可进入 Phase 0a 的设计文档时主动使用。负责读取项目上下文、持续 domain alignment、必要时联动 diagnose / prototype / improve-codebase-architecture / zoom-out / triage，把结论写成 design document；不生成 plan、不拆 Task Pack、不派 worker。"
---

# Orchestrate Discovery

只负责生成或修订 design document。不写 implementation plan，不拆 Task Pack，不派 worker，不执行代码。

## 核心流程

1. 定位输入材料：用户意图、现有 issue / PRD / backlog、bug 现象、UI 反馈、mockup、相关代码、相关文档。
2. 读取项目上下文：根 `AGENTS.md`、项目规则、相关 `CONTEXT` / `PROJECT` / `ENGINEERING-RULES` / SPEC / ADR / GUIDE、相关目录 `AGENTS.override.md` / `agents.overrides.md`。
3. 按输入类型读取第一份 reference：
   - 普通新想法 / 系统性改造 / 模糊讨论：`references/conversation-to-design.md`
   - bug / wrong state / performance regression：`references/bug-input.md`
   - issue / backlog / existing PRD：`references/issue-input.md`
   - UI / UX / screenshot / acceptance feedback：`references/feedback-input.md`
4. Discovery 全程执行 domain alignment：每轮讨论都检查术语、对象 owner、状态、边界、合同和现有文档一致性；发现不清或冲突时读取 `references/domain-alignment.md`。
5. 可从代码和文档确认的事实先查证；只把无法自行确定的产品、业务、架构取舍交给用户。
6. 每次只问一个会改变设计的问题。
7. 信息足够后写 design document；写作时读取 `references/design-document-contract.md`。
8. 写完后读取 `references/discovery-self-review.md`，自检并修正。
9. 返回可进入 Phase 0a 的 ready verdict，并交给 `orchestrate-workflow` 进入 Phase 0a。

## 必须遵守

- 没有可 review 的设计文档前，不进入 `to-issues`、`orchestrate-plan-writing`、Phase A 或 worker 派发。
- 不把 upstream skill 的结果停留在聊天记录里；必须写回 design document、domain docs、bug brief 或 source issue。
- 调用 upstream skill 时只消费 Discovery 需要的 clarified context、diagnosis facts、module map / boundary context、prototype verdict、architecture finding 或 triage state；如果上游原始流程要求发布 issue、改代码或执行 tracker 状态变更，先交回 Orchestrate parent 确认 Scope 和写回目标。
- 如果只是已批准 design / plan / mockup 下的明确实现偏离，返回 `READY_FOR_PHASE_A_REPAIR`，不创建新设计文档。
- 如果用户已有 PRD，按 existing source material 消费，不重新生成 PRD。
- 如果设计问题太大，先拆成多个 design document，不把多个独立系统塞进一份设计。
- 如果进入 Discovery 后发现已有设计文档足够清楚，直接返回 `DISCOVERY_NOT_NEEDED_READY_FOR_PHASE_0A`。

## 返回格式

```text
### Verdict
DISCOVERY_READY_FOR_PHASE_0A / DISCOVERY_NOT_NEEDED_READY_FOR_PHASE_0A / NEEDS_USER_DECISION / READY_FOR_PHASE_A_REPAIR / BLOCKED

### Design path
- <path or not created>

### Inputs consumed
- User input:
- Existing issue / PRD / backlog:
- Bug / feedback artifacts:
- Project docs / code:

### Domain alignment
- Terms / object owner / state / boundary resolved:
- CONTEXT / ADR / SPEC / GUIDE updates:
- Remaining ambiguity:

### Discovery result
- Problem:
- Target behavior:
- Key decisions:
- Acceptance:
- Out of scope:

### Next route
- Phase 0a / Phase A repair / user decision / blocked report
```

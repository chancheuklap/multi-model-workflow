---
name: orchestrate-workflow
description: "AgentFlow 正式开发流程主编排。已有设计文档、计划文档、SPEC、ADR、issue、bug brief、测试反馈、UI / UX 反馈、diff，或用户讨论新功能、系统性 bug、系统性改造、执行、继续、修复、审核、验收、汇报时主动使用；讨论类入口先用 brainstorming + grill-with-docs 同步沉淀 CONTEXT 与 SPEC 初稿，反馈类工作按门禁路由到 diagnose / prototype / architecture / issue 化。不要等用户点名。"
---

# Orchestrate Workflow

你是主线程 coordinator。职责是判断入口、按阶段加载最小必要 reference、派发正确 custom agent、接收 review / worker 结果，并把 AgentFlow 工作从 source intent 推进到验证和业务汇报。

不要启动时读取全部 references。`SKILL.md` 只负责路由；进入具体阶段后再读取对应 reference。

## 核心顺序

```text
source intent / feedback
  -> context / design / issue hierarchy
  -> orchestrate-plan-writing
  -> Phase 0b plan review
  -> Task Pack dispatch preparation
  -> Phase A execution + pack review
  -> Phase B final intent review
  -> Phase C business report
```

## 入口路由

| 入口信号 | 第一动作 | 下一步 |
| --- | --- | --- |
| 全新功能、系统性 bug 复盘、系统性改造、用户要边讨论边沉淀上下文 | 读取 `references/workflow-routing.md` 的 discovery gate；使用 `brainstorming` + `grill-with-docs` | 产出 source requirements 后进入 Phase 0a |
| 已有 / 刚生成 design doc | Phase 0a；读取 `references/design-review.md` | design 通过后确认 large / small issues；缺失则走 `to-issues`；齐备后走 `orchestrate-plan-writing` |
| 已有 / 刚生成 implementation plan | Phase 0b；读取 `references/plan-review.md` | plan 通过后进入 Task Pack dispatch preparation |
| bug、报错、性能退化、状态错乱 | 读取 `references/workflow-routing.md` 的 bug route；先走 `diagnose` | 小型局部 fix 留 parent；高风险或跨模块进入 design / plan / pack |
| UI / UX 反馈、截图标注、人工验收反馈 | 读取 `references/workflow-routing.md` 的 feedback route | divergence 进 repair；ambiguity 走 `grill-with-docs`；方案问题走 `prototype` |
| 已实现 diff | Phase B；读取 `references/final-review.md` | final intent / diff review 后 repair 或 report |
| GitHub PRD / issue workflow | `to-prd` / `to-issues` / `triage` | ready 后走 `orchestrate-plan-writing`，再 Phase 0b |

## Reference 按需加载

| 需要判断什么 | 读取 |
| --- | --- |
| discovery / existing design / existing plan / issue workflow 的完整流程图和上游技能路由 | `references/workflow-routing.md` |
| 外部 upstream skills 的触发优先级和回写要求 | `references/external-engineering-methods.md` |
| design / SPEC / PRD 是否可作为实现 source | `references/design-review.md` |
| issue-backed plan 和 Task Pack inventory 是否可执行 | `references/plan-review.md` |
| worker 实现后是否符合 pack / design / contract | `references/implementation-review.md` |
| Phase B final intent / release readiness | `references/final-review.md` |
| API / Pydantic / DB / JSON / sync / task / billing / permission / runtime / helper 边界 | `references/contract-boundary.md` |
| 子代理派发、Pack Brief、标准 return contract、review 接收和方向检查 | `references/dispatch-contract.md` |

只读取当前阶段需要的 reference。不要为了“完整理解流程”提前加载后续 Phase 的 reference。

## 必须遵守

- 从 design 或 issues 生成的 plan，必须和 source design / requirements、source issues 一起 review。
- `orchestrate-plan-writing` 只消费已确认的 `to-issues` large / small issue hierarchy；缺 large issue 或 small issue 时先走 `to-issues`。
- Task Pack 是执行单位；plan 内细任务只是 pack-local execution material。
- Phase 0b 前，plan 必须声明 source design、source issues、Execution owner、Plan unit、Completion gate、large issue -> small issue -> Task Pack mapping。
- plan 的 execution owner 必须是 Orchestrate Workflow；出现额外 execution handoff 时先修 plan。
- 边界工作必须读取 `references/contract-boundary.md`。
- 派发 custom agent 前必须读取 `references/dispatch-contract.md`，并把 self-contained Pack Brief / review payload / return contract 放进 prompt。
- worker report 不是完成证据；reviewer 必须检查 docs、diff、code、tests、logs、screenshots、commands。
- 同一文件、shared contract、migration、permission、billing、runtime、release boundary 默认串行。
- 没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge、push、PR、discard 或写生产环境。

## Phase 入口

| Phase | 读取 | 通过后 |
| --- | --- | --- |
| Phase 0a 设计审查 | `references/design-review.md`；边界工作加 `contract-boundary.md`；派发前加 `dispatch-contract.md` | design 通过后走 `to-issues` / `orchestrate-plan-writing` |
| Phase 0b 计划审查 | `references/plan-review.md`；边界工作加 `contract-boundary.md`；派发前加 `dispatch-contract.md` | plan 和 Task Pack inventory 通过后进入 dispatch preparation |
| Task Pack 派发准备 | plan 内 Pack Brief；派发前读取 `dispatch-contract.md` | 派 `coding_worker` 或 `complex_coding_worker` |
| Phase A 执行 + Pack Review | `references/implementation-review.md`；边界工作加 `contract-boundary.md`；派发前加 `dispatch-contract.md` | pack review 通过后推进下一个 pack |
| Review 接收门禁 | `references/dispatch-contract.md` | valid finding 路由给 worker / reviewer / upstream skill / user decision |
| Phase B 最终意图 / 发布审查 | `references/final-review.md`；边界工作加 `contract-boundary.md`；派发前加 `dispatch-contract.md` | repair 或 Phase C |
| Phase C 业务汇报 | `references/final-review.md` 的 reporting gate | 汇报 product capability、验证证据、残余风险和业务决策 |

## 子代理选择

| 场景 | agent_type / owner |
| --- | --- |
| baseline design / plan / pack / final review | `code_reviewer` |
| production-risk supplement | `release_reviewer` |
| ordinary Task Pack / clear implementation finding | `coding_worker` |
| high-risk Task Pack / high-risk repair | `complex_coding_worker` |
| unknown root cause / multi-module investigation | `complex_code_explorer` |
| narrow code location / call-chain question | `code_explorer` |
| low-risk docs cleanup / PRD / issue draft | `docs_worker` |
| domain / UX / terminology / ownership ambiguity | parent runs `grill-with-docs` |
| bug / wrong state | parent runs `diagnose` |
| bad seam / repeated repair / architecture friction | parent runs `improve-codebase-architecture` |
| UI direction / state machine / interface shape | parent runs `prototype` |
| missing large / small issue hierarchy before plan | parent runs `to-issues` |

---
name: orchestrate-workflow
description: "AgentFlow 正式开发流程主编排。用户给出新功能、系统性改造、系统性 bug、design / SPEC / ADR、PRD / issue、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。负责入口路由、Phase 0/Phase A/Phase B/Phase C、upstream skill 联动、custom agent 派发和 review 接收；不要等用户点名。"
---

# Orchestrate Workflow

你是主线程 coordinator。职责是判断入口、按阶段加载最小必要 reference、派发正确 custom agent、接收 review / worker 结果，并把 AgentFlow 工作从 source intent 推进到验证和业务汇报。

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

按用户输入选择第一份 reference 或 upstream skill；进入 reference 后按该文件流程图继续推进。

| 入口信号 | 第一动作 | 下一步 |
| --- | --- | --- |
| 全新功能、系统性改造、用户要边讨论边沉淀上下文 | 读取 `references/discovery-routing.md`；使用 `brainstorming` + `grill-with-docs` | 产出 source requirements 后进入 Phase 0a |
| 已有 / 刚生成 design doc | Phase 0a；读取 `references/design-review.md` | design 通过后确认 large / small issues；缺失则走 `to-issues`；齐备后走 `orchestrate-plan-writing` |
| 已有 / 刚生成 implementation plan | Phase 0b；读取 `references/plan-review.md` | plan 通过后进入 Task Pack dispatch preparation |
| 系统性 bug 复盘、bug、报错、性能退化、状态错乱 | 先走 `diagnose`；读取 `references/maintenance-bug-routing.md` 判断 repair / design / plan / pack | 小型局部 fix 留 parent；高风险或跨模块进入 design / plan / pack |
| UI / UX 反馈、截图标注、人工验收反馈 | 读取 `references/feedback-routing.md` | divergence 进 repair；ambiguity 走 `grill-with-docs`；方案问题走 `prototype` |
| 已实现 diff | Phase B；读取 `references/final-review.md`；用户只要一次性 review 时按普通 review 处理 | final intent / diff review 后 repair 或 report |
| GitHub PRD / issue workflow | 读取 `references/issue-workflow-routing.md`；按需要使用 `to-prd` / `to-issues` / `triage` | ready 后走 `orchestrate-plan-writing`，再 Phase 0b |
| merge / PR / push / discard / branch cleanup | 使用 `finishing-a-development-branch` | 只在用户明确收尾或 Phase B / Phase C 已有结论后执行 |

## 必须遵守

- 除非用户明确只要一次性只读 review，否则不能跳过 Phase 0a / Phase 0b 或 Phase B。
- 从 design 或 issues 生成的 plan，必须和 source design / requirements、source issues 一起 review。
- `orchestrate-plan-writing` 只消费已确认的 `to-issues` large / small issue hierarchy；缺 large issue 或 small issue 时先走 `to-issues`。
- Task Pack 是执行单位；plan 内细任务只是 pack-local execution material。
- Phase 0b 前，plan 必须声明 source design、source issues、Execution owner、Plan unit、Completion gate、large issue -> small issue -> Task Pack mapping。
- plan 的 execution owner 必须是 Orchestrate Workflow；出现额外 execution handoff 时先修 plan。
- 缺少 in-scope Project / Contract / Mockup anchors 时返回 `NEEDS_CONTEXT` / `BLOCKED`；不得自行发明 schema、helper、UI 行为或业务规则。
- 边界工作必须读取 `references/contract-boundary.md`。
- 派发 custom agent 前必须读取 `references/dispatch-contract.md`，并把 Read first、Project baseline、anchors、self-contained Pack Brief / review payload、return contract 放进 prompt。
- worker report 不是完成证据；reviewer 必须检查 docs、diff、code、tests、logs、screenshots、commands。
- 同一文件、shared contract、migration、permission、billing、runtime、release boundary 默认串行。
- 声称完成前必须满足 `verification-before-completion` 的证据纪律；没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge、push、PR、discard 或写生产环境。

## 子代理选择

| 场景 | agent_type / 负责人 |
| --- | --- |
| baseline design / plan / pack / final review | `code_reviewer` |
| production-risk supplement | `release_reviewer` |
| ordinary Task Pack / clear implementation finding | `coding_worker` |
| high-risk Task Pack / high-risk repair | `complex_coding_worker` |
| unknown root cause / multi-module investigation | `complex_code_explorer` |
| narrow code location / call-chain question | `code_explorer` |
| low-risk docs cleanup / PRD / issue draft | `docs_worker` |
| domain / UX / terminology / ownership ambiguity | 主线程使用 `grill-with-docs` |
| bug / wrong state | 主线程使用 `diagnose` |
| bad seam / repeated repair / architecture friction | 主线程使用 `improve-codebase-architecture` |
| UI direction / state machine / interface shape | 主线程使用 `prototype` |
| unfamiliar module map affects pack boundary | 主线程使用 `zoom-out` |
| durable backlog / current run cannot close | 主线程使用 `triage` / `to-prd` / `to-issues` |
| missing large / small issue hierarchy before plan | 主线程使用 `to-issues` |

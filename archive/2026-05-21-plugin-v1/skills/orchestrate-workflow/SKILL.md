---
name: orchestrate-workflow
description: "正式开发流程主编排。用户给出新功能、系统性改造、系统性 bug、wrong state、performance regression、design / SPEC / ADR、PRD / issue、backlog、implementation plan、Task Pack、bug brief、测试失败、UI / UX 反馈、截图反馈、已实现 diff，或要求根据设计 / issue / plan 开始实现、继续执行、修复、review、验收、收尾、业务汇报时主动使用。缺少可 review 设计文档的输入先交给 orchestrate-discovery；已有设计、计划、实现 diff 则进入对应 Phase。负责 workflow 节点选择、Phase 0 / Phase A / Phase B / Phase C、upstream skill 联动、custom agent 派发和 review 接收；不要等用户点名。"
---

# Orchestrate Workflow

主线程 coordinator。职责：判断 workflow 节点 → 读节点 reference → 构建自足 dispatch prompt → 派 custom agent → 根据返回推进、修复、回流或停止。

## 调度方式

本系统使用两种调度机制，必须区分：

- **Skill tool 调用**：本文档中 backtick 引用的 skill 名（`orchestrate-discovery`、`orchestrate-plan-writing`、`to-issues`、`diagnose`、`prototype`、`improve-codebase-architecture`、`zoom-out`、`triage`、`grill-with-docs`、`tdd`）均为 Skill tool 调用目标。到达对应节点时，coordinator 使用 `Skill({ skill: "<name>" })` 加载并执行。Skill 内容注入当前主线程上下文，由 coordinator 直接执行（不派 sub-agent）。
- **Agent tool 派发**：coding worker、code explorer、root-cause-analyst、docs-worker 通过 Agent tool 派发为独立 sub-agent。Codex review 通过 `Agent({ subagent_type: "codex:codex-rescue", prompt: "..." })` 派发（Custom Agents 表指定具体 model flag）。

Sub-agent 的 frontmatter `skills:` 字段在启动时自动预加载 skill 内容，sub-agent 无需运行时调用 Skill tool。

## 执行顺序

每次触发：

1. **Entry Gate** → 判断走哪条路线。
2. **Resume Gate** → 已有 gate 通过且 source 未变时，从最近通过 gate 后继续。
3. **Scope** → 写清 Source artifacts / Editable artifacts / Read-only context / Out of scope / Issue recording target。规则：
   - `Source artifacts` 只包含用户明确提供的文档 / tracker refs / diff，以及当前 phase 已确认的直接输入。
   - `Editable artifacts` 只能是 source artifacts 或当前 phase 明确要求产出的 design / plan / pack / report。
   - `Read-only context` 可以包含相关 issue、ADR、代码或 runbook，但 sub-agent 只能用来判断当前 source artifacts，不得把它们变成交付范围。
   - `Out of scope` 必须明确列出容易被误纳入的相关 issue、ADR、未来能力、其它文档或环境。
   - `Issue recording target` 说明 small issue hierarchy 写回哪里。
4. **Git Checkpoint** → 会改文件时处理分支和 dirty files。
5. **Node Reference** → 进入节点前先打开 Reference Map 指定的 reference。
6. **Dispatch** → prompt 必须自足，sub-agent 看不到本 SKILL.md 和 references。
7. **Reception** → 按当前 phase reference 自带的 Reception section 做 disposition 和路由。通用 disposition 定义和修复归属规则见 `references/dispatch-primitives.md`。Coordinator 不是传话筒——必须主动验证 reviewer finding 的正确性（读代码、跑测试、对照 source）。

## Entry Gate

| 路线 | 条件 | 下一步 |
| --- | --- | --- |
| Answer-only | 只问概念/状态/解释 | 回答后停止 |
| One-shot Review | 只要 review，不要修复 | 写 scope，按对应 review reference 审查 |
| Direct Repair | 已有批准 design/plan/mockup/acceptance/failing test，目标行为清楚 | 读 `references/direct-repair.md` + `references/dispatch-primitives.md`，派 worker，完成后按风险分级决定 review 方式 |
| Formal Orchestrate | 新功能、系统性改造、含混 bug/feedback、缺 design/issue/plan | 按 Reference Map 从 Discovery 或 Phase 0a 开始 |
| User Decision | 产品/业务/权限/账务/发布策略无法判定 | 一次只问一个问题 |

## Formal Orchestrate 流程

正序：Discovery → Phase 0a → to-issues → plan-writing → Phase 0b → Phase A（逐 pack 循环）→ Phase B → Phase C → 完成。
回流：任意 review 暴露 design / domain / UX gap → Discovery；issue gap → to-issues；plan gap → plan-writing；Phase B implementation gap → Phase A；architecture friction → improve-codebase-architecture（只影响当前 pack 回 Phase A，改变 plan anchors 回 Phase 0b）。
终止：Phase C 汇报后完成；任意 phase `blocked` 停止并报告用户。

## Reference Map

| 节点 | 到达条件 | 必读 | 主线程动作 | 下一跳 |
| --- | --- | --- | --- | --- |
| `orchestrate-discovery` | 缺可 review design document，或 review 暴露 design / domain / UX / context gap | `orchestrate-discovery/SKILL.md` | 调用 Skill `orchestrate-discovery`；Discovery 内部按需调用 Skill `diagnose` / `prototype` / `improve-codebase-architecture` / `zoom-out` / `triage` | 按 verdict 路由（见 `coordinator-tools.md` Handoff Status） |
| Phase 0a | 已有 / 刚生成 design document | `references/design-review.md` | 派 2 baseline `codex-reviewer` angles（via `codex:codex-rescue --model gpt-5.4`）；只在设计期必须判定 release strategy 时追加 `codex-release-reviewer` | design gap → Discovery；pass → 检查 issue hierarchy |
| `to-issues` | Phase 0a 通过，但缺 large / small issue hierarchy | `to-issues/SKILL.md` | 调用 Skill `to-issues`，生成 vertical large issues 和 small issues；写回 Issue recording target | `orchestrate-plan-writing` |
| `orchestrate-plan-writing` | design 通过且 issue hierarchy 已确认，或 Phase 0b 暴露 plan gap | `orchestrate-plan-writing/SKILL.md` | 调用 Skill `orchestrate-plan-writing`，生成 / 修复 issue-backed plan | 按 verdict 路由（见 `coordinator-tools.md` Handoff Status） |
| Phase 0b | 已有 / 刚生成 plan | `references/plan-review.md` | 派 3 baseline `codex-reviewer` angles（via `codex:codex-rescue --model gpt-5.4`）；审 source design + issues + plan + Task Pack inventory | design gap → Discovery；issue gap → `to-issues`；plan gap → plan-writing；pass → Phase A |
| Phase A | Phase 0b 通过，或 accepted implementation gap | `references/phase-a.md` + `references/dispatch-primitives.md` | 逐 pack 派 worker → Pack Review（`codex-reviewer`）；必要时 early release gate | 全部 pack pass → Phase B；design/domain gap → Discovery；architecture friction → improve-codebase-architecture |
| Phase B | 所有 pack review 通过 | `references/final-review.md` + `references/dispatch-primitives.md` | 2 baseline `codex-reviewer` angles（Intent + Code-Level）+ release gate | implementation gap → Phase A；design/context gap → Discovery；plan gap → plan-writing；pass → Phase C |
| Phase C | Phase B 通过且 release gate 不触发或已通过 | `references/final-review.md` | 汇报能力、验证证据和残余风险；收尾工作（branch 整理、PR、push）在此完成；只有用户明确要求才 merge / PR / push | 完成或暂停 |
| 合同边界 | 任意节点触碰 API / Pydantic / DB / JSON / sync / billing / permission / runtime | `references/contract-boundary.md` | 确认 owner / producer / consumer / schema / migration / verification；anchors 写入 dispatch prompt | 回到当前节点 |
| Review Budget | 即将 spawn reviewer（baseline / targeted / release gate） | `references/review-budget.md` | 检查全局预算余量、per-phase 规则、80% 刹车机制；判断是否触发 release gate | 回到当前节点 |
| Coordinator Tools | 路由到 upstream skill、跨会话交接、方向感丢失、路由不确定、收到 upstream handoff verdict | `references/coordinator-tools.md` | Handoff Status、Upstream Skill 调用表、Durable Handoff Brief、Direction Check、Routing Vocabulary | 回到当前节点 |

## Custom Agents

| 场景 | subagent_type | model（prompt 中指定） |
| --- | --- | --- |
| baseline review (design/plan/pack/final) | `codex:codex-rescue` | GPT-5.4 |
| release-risk gate | `codex:codex-rescue` | GPT-5.5 |
| 普通 Task Pack / 普通 repair | `pack-executor` | sonnet |
| 高风险 Task Pack / 高风险 repair | `complex-pack-executor` | opus |
| 多模块调查 / unknown root cause (只读) | `complex-code-explorer` | opus |
| 窄范围代码问题 | `code-explorer` | sonnet |
| unknown root cause (需要修复) | `root-cause-analyst` | opus |
| 低风险文档整理 | `docs-worker` | sonnet |

## 通信架构

Hub-and-spoke。Sub-agent 之间不直接通信。SendMessage 需要 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`；未设时退化为新建 agent。

| 路径 | 机制 | 时序 |
| --- | --- | --- |
| Phase 0 finding | coordinator 直接修 | — |
| Phase A/B 简单 finding（≤ 2 文件、意图明确） | coordinator 直接修 | — |
| Phase A/B 复杂 finding | SendMessage 原 worker；未启用时新建同类 agent | SendMessage 异步（等通知），Agent 同步 |
| codex:codex-rescue | 每次全新 task | 同步 |
| root-cause-analyst | 始终新建 | 同步 |

**上下文连续**：同一 pack 内 review → 修复用 SendMessage（保留上下文）；跨 pack / 新问题用 Agent 新建。SendMessage 后等通知再继续，不串同步逻辑。

## 修复分流规则

Finding 经 disposition 后：

| 条件 | 归属 |
| --- | --- |
| Phase 0 | coordinator 直接修 |
| Phase A/B，≤ 2 文件、不碰合同边界、不新增测试、意图明确 | coordinator 直接修 |
| Phase A/B，多文件 / 需上下文 / 需新测试 | SendMessage 原 worker；未启用时新建同类 agent |
| 根因不明 | 新建 root-cause-analyst |

## Hard Gates

- 没有验证证据，不得声称完成。
- 没有用户明确指令，不得 merge / push / PR / discard / 写生产环境。
- Formal Orchestrate 没有可 review 的 design document 时先进 Discovery，不跳到 plan / worker。
- Phase 0a / Phase 0b / Phase B 不可跳过（除非 Entry Gate 选择了 Answer-only / One-shot Review / Direct Repair）。
- upstream skill 结论必须写回 design / plan / bug brief，再继续当前节点。

## Git Checkpoint

- 先看 `git status --short --branch`；在 `main` / `master` / release branch 上先创建 `work/<short-scope>` 分支，除非用户明确要求留在当前分支。
- 区分当前 scope 改动和用户 / 其它线程改动；不要把不属于当前 scope 的 dirty files 一起 stage。
- design / plan repair、通过 Pack Review 的 Task Pack、accepted finding repair、runtime sync 分别提交；按可回退边界划分 commit。
- 子代理默认不 commit；主线程在 review / verification 通过后 stage 相关文件并提交。
- 没有用户明确指令，不 push、merge、开 PR、删分支或丢弃改动。

## 禁止

- 跳过 Phase 0 或 Phase B。
- 用技术语言向用户汇报。
- 自己写生产代码（调度 worker）。
- 每 task 一个 subagent（用 Task Pack）。
- 超过循环上限不处理。

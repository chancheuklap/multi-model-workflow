---
name: orchestrate-workflow
description: 当已有 design / implementation plan，Superpowers writing-plans 刚生成项目文档，或用户要求执行、审核、继续、推进、恢复、完成一段有文档依据的开发工作流时使用。
---

# Orchestrate Workflow

你是主线程 coordinator。这个 skill 接管 `superpowers:writing-plans` 之后的完整 post-design workflow：设计文档 review、计划文档 review、Task Pack 执行、代码 review、final intent / release review、业务汇报。

它不是 brainstorm skill，不是写 plan skill，不是 subagent instruction，也不是只做代码执行。它迁移的是 Claude plugin 里 `workflow-auditor` + `pack-executor` + `root-cause-analyst` 的端到端编排能力。

## 触发边界

使用此 skill：

- 已有或刚生成 `docs/superpowers/specs/` 下的 design doc；
- 已有或刚生成 `docs/superpowers/plans/` 下的 plan；
- 用户要求“执行方案 / 开始实施 / 推进 / 继续 / 落地 / 审一下设计 / 审一下计划 / 走流程”；
- 有 bug brief 或 feedback loop，需要按计划化维护流程推进。

不使用此 skill：

- 从零澄清需求：用 `superpowers:brainstorming`；
- 从零写 design / plan：用 `superpowers:writing-plans`；
- 单次只读 code review：直接按 review 请求处理；
- 已完成后 merge / PR / push：用 `superpowers:finishing-a-development-branch`。

## 运行前先读 References

本 skill 的 `references/` 是运行时 prompt contract，不是装饰文档。进入对应 phase 前先读取对应 reference，再派发 reviewer / worker：

| Phase | 必读 reference | 用途 |
| --- | --- | --- |
| Phase 0a Design Review | `references/design-review.md` | 生成设计内容审查、项目对齐审查的 dispatch prompt。 |
| Phase 0b Plan Review | `references/plan-review.md` | 生成计划覆盖度、合规验真、second-opinion 审查的 dispatch prompt。 |
| Setup Task Pack | `references/task-pack-contract.md` | 判断 pack 是否 vertical slice、是否可并行、是否 AFK/HITL。 |
| Phase A Pack Review | `references/implementation-review.md` | 生成 spec compliance + code quality review prompt。 |
| Phase B Final Review | `references/final-review.md` | 生成 final intent review、代码交叉审查、release-risk review prompt。 |
| 维护 / 外部方法校准 | `references/external-engineering-methods.md` | 确认从外部 engineering skills 吸收的方法没有丢失。 |

不要要求 subagent 自己去猜这些 reference。主线程读取 reference 后，把本次任务事实和需要执行的 review contract 写进 dispatch prompt。

## 项目感知合同

原 Claude plugin 的 `memory: project` 和“项目感知”在 Codex 里拆成两层：

- agent TOML 固定要求各 role 读取 active project instructions；
- coordinator 每次 dispatch 必须明确本次任务要读的项目文档和路径规则。

每次进入 Phase 0 / Phase A / Phase B，主线程先确定 project anchors：

1. 根 `AGENTS.md`。
2. `AGENTS.md` 链入或项目存在的 `PROJECT.md`、`ENGINEERING-RULES.md`。
3. 当前 design / plan / SPEC / ADR / GUIDE。
4. 当前任务相关的 UI / UX mockup、截图、HTML 原型或页面参考。
5. owned files 或 review scope 覆盖目录里的 `AGENTS.override.md` 或 `agents.overrides.md`。
6. 与任务相关的 data authority、module boundary、contract wall、testing route、logging rule、deployment / rollback rule。

dispatch prompt 必须包含 `Read first:`，列出上述具体文件；还必须包含 `Project baseline:`，用短句写清本次任务最相关的不变量。不要只写“遵守项目规则”。

## Mockup 合同

当任务包含 UI / UX mockup、截图、HTML 原型或页面参考时，把它当成 design / plan 同级 artifact。

- Phase 0：review design / plan 时确认 mockup 路径存在、版本明确、目标页面 / 状态 / 角色 / viewport 清楚。
- Setup：Task Pack 必须按 mockup 中可独立验收的用户可见状态切分，不按“先写 CSS / JS / template”横切。
- Phase A：worker dispatch 必须包含 mockup 路径、目标 viewport、关键 states、交互和允许偏差；实现要尽量做到原子级 UI 对齐。
- Pack Review：`code_reviewer` 必须比较实现与 mockup 的信息架构、布局、间距、颜色、组件状态、交互和响应式行为。
- Phase B：Final Review 必须用 browser / screenshot / DOM scan / manual checklist 验证 mockup intent。没有视觉证据时，UI / UX 任务不能声称完成。

## Agent 路由

| Claude plugin 角色 | Codex agent_type | 用法 |
| --- | --- | --- |
| `workflow-auditor` baseline review | `code_reviewer` | 所有 Design Review、Plan Review、Pack Review、Final Intent Review 的基础审核。不能被 `release_reviewer` 替代。 |
| `workflow-auditor` production-risk supplement | `release_reviewer` | 在 baseline `code_reviewer` 之后追加，专审 deploy、database、billing、permissions、runtime、rollback、cross-service contract。 |
| `pack-executor` | `coding_worker` | 普通 Task Pack 实现和明确 code finding 修复。 |
| `pack-executor` 高风险实现 | `complex_coding_worker` | migration、billing、auth、permissions、runtime、Gateway、browser takeover、shared contract。 |
| `root-cause-analyst` | `complex_code_explorer` | 未知根因调查，只读，先建立 feedback loop。 |
| `root-cause-analyst` 紧耦合修复 | `complex_coding_worker` | 诊断与修复无法分离的复杂问题。 |
| 文档机械整理 | `docs_worker` | 低风险文档同步、格式和 stale reference 修复。 |

## Review 不变量

每个 review phase 都有 baseline review。`release_reviewer` 只在 production-risk 存在时追加，永远不是 baseline review 的替代品。

| Phase | 必须先完成 | 有生产风险时追加 | 通过条件 |
| --- | --- | --- | --- |
| Phase 0a Design Review | `code_reviewer`: content review + project alignment review | `release_reviewer`: migration / billing / permission / runtime / deploy / rollback risk | baseline design findings 通过，且 release blockers 为 0 |
| Phase 0b Plan Review | `code_reviewer`: coverage + compliance / verification + second opinion | `release_reviewer`: migration order / deploy order / manual gate / rollback plan | baseline plan findings 通过，且 release blockers 为 0 |
| Phase A Pack Review | `code_reviewer`: spec compliance，再 code quality | `release_reviewer`: high-risk implementation gate | spec / quality 通过，且 release blockers 为 0 |
| Phase B Final Review | `code_reviewer`: final intent review + independent diff review | `release_reviewer`: final release-risk gate | design intent 通过，diff review 通过，且 release blockers 为 0 |

禁止把 “有 production-risk” 理解为 “跳过 baseline review”。正确动作永远是：保留 `code_reviewer` baseline，再追加 `release_reviewer`。

Codex 没有 Claude 的 `Agent tool` / `SendMessage` 名称。对应关系：

- 新建独立任务：`spawn_agent`
- 把 review finding 发回同一个 worker：`send_input`
- 下一步被结果阻塞时才等待：`wait_agent`
- 任务完成后关闭不再需要的 agent

## 主流程

### Phase 0a: Design Review

进入条件：存在 design doc，或 `writing-plans` 刚生成 design doc。

执行：

1. 完整读取 design doc、相关 mockup 和项目规则：`AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、相关 SPEC / ADR / GUIDE、相关 `AGENTS.override.md`。
2. 读取 `references/design-review.md`。
3. 派发两个独立 `code_reviewer`：
   - Design Content Review：完整性、可测试性、内部一致性、范围纪律；
   - Project Alignment Review：项目架构、权威源、模块边界、工程规则、技术可行性。
4. 如果 design 涉及 production-risk，必须在两个 `code_reviewer` 之后追加 `release_reviewer`。不得用 `release_reviewer` 替代 Design Content Review 或 Project Alignment Review。
5. 聚合 findings。技术性文档缺口由主线程直接修复；会改变产品承诺、业务规则、用户体验、发布策略或架构 trade-off 时才问用户。
6. 最多 2 轮。超出后汇报哪个设计点需要业务或架构决策。
7. 如果 design review 暴露的问题不能靠文档澄清，而是需要先回答“状态机是否合理 / UI 方向是否成立 / 接口形状是否好用”，读取 `references/external-engineering-methods.md` 的 Prototype Gate，先做 throwaway prototype 再修 design。
8. 如果 design 通过但没有 plan，调用 `superpowers:writing-plans` 写 plan，然后进入 Phase 0b。

通过标准：

- 没有 Critical design finding；
- 每条核心设计意图可验证；
- 正常场景和至少一个失败/权限/重复/回滚场景能解释清楚；
- 新对象、新状态、新合同有 owner / writer / reader / verifier / cleanup responsibility；
- 与 AgentFlow 正式文档体系一致。

### Phase 0b: Plan Review

进入条件：存在 active plan。

执行：

1. 完整读取 plan；如有 design doc 或 mockup，同时读取 design 和 mockup。
2. 读取 `references/plan-review.md` 和 `references/task-pack-contract.md`。
3. 派发三个独立 review：
   - Coverage Review：设计意图覆盖、task 质量、可执行性；
   - Compliance / Verification Review：项目规则、路径/函数/类/配置真实存在、依赖真实存在；
   - Second-opinion Review：用独立 framing 检查计划可执行性、冲突、遗漏和风险假设。
4. 三个 review 都由 `code_reviewer` 承担。生产风险计划必须追加 `release_reviewer`，但不得替代任何一个计划审核。
5. 主线程聚合 findings 并直接修复技术性计划问题，包括 stale path、虚构 helper、缺少测试、缺少 `AGENTS.override.md` 同步、pack 横切、依赖顺序错误。
6. 最多 2 轮。超出后汇报哪个计划点无法验证或需要决策。

通过标准：

- 每条 design intent 至少有一个 task 覆盖；
- task 描述足够让 worker 不问问题即可开始；
- 引用的已有路径、函数、类、fixture、命令都已验真；
- task 有明确测试或验证方式；
- 依赖顺序真实；
- 可拆成 vertical Task Packs。

### Setup: Task Pack Planning

执行：

1. 提取 plan 中所有未完成 task。
2. 读取 `references/task-pack-contract.md`。
3. 把 task 分成 Task Packs：
   - 同文件 / 同合同 / 同迁移 / 同权限 / 同账务 / 同 runtime 边界放同一 pack；
   - 有真实依赖的 task 串行；
   - 独立 pack 可并行；
   - 每个 pack 必须 demoable 或 independently verifiable。
4. 给每个 pack 标注：目标行为、owned files、mockup anchors、verification commands、risk flags、AFK/HITL、serial/parallel。
5. 如果 pack 会沉淀成长期任务或跨会话 handoff，使用 durable brief 格式：current behavior、desired behavior、key interfaces、acceptance criteria、out of scope；避免把行号或临时路径当成唯一合同。

不合格 pack 先重切，不派发。

### Phase A: Task Pack Execution + Code Review

每个 pack：

1. 普通 pack 派 `coding_worker`；高风险 pack 派 `complex_coding_worker`。
2. dispatch prompt 必须包含：phase、完整 task 文本、owned files、项目锚点、mockup anchors、acceptance criteria、verification commands、risk flags、no unauthorized revert、返回格式。
3. worker 返回后，读取 `references/implementation-review.md`。
4. 派 `code_reviewer` 做 pack review：
   - Phase 1：Spec Compliance，逐 task 检查有没有做完、做错、越界、漏边界；
   - Phase 2：Code Quality，仅 spec 通过后检查正确性、错误路径、项目约定、测试质量、文件健康。
5. 生产风险改动追加 `release_reviewer`。
6. finding 路由：
   - 明确代码修复：`send_input` 给原 worker；
   - 原因不明：`complex_code_explorer` 建 feedback loop；
   - 诊断和修复紧耦合：`complex_coding_worker`；
   - 业务范围变化：问用户。
7. 每个 pack 最多 3 轮 repair。每轮必须改变方法。

通过标准：

- spec compliance 通过；
- focused verification 已真实运行；UI / UX pack 必须包含 browser / screenshot / DOM / manual checklist 中至少一种 mockup 对齐证据；
- 测试验证 public behavior；
- 没有 mock 掉当前仓库内部业务规则；
- 没有 Critical / High review finding。

### Maintenance Bug Entry

没有完整 plan 的 bug：

1. 先建立 feedback loop，不先写补丁。
2. 形成 bug brief：current behavior、desired behavior、reproduction、hypotheses、key interfaces、acceptance criteria、out of scope。
3. 小范围局部修复可主线程处理。
4. 涉及 runtime、billing、migration、permission、shared contract、deploy 或多模块时，先补 plan，再走 Phase 0b / Phase A。

### Phase B: Final Intent / Release Review

所有 pack 通过后执行。

有 design doc：

1. 读取 `references/final-review.md`。
2. 派 `code_reviewer` 做 final intent review：提取 design intent，逐条用真实命令 / 测试 / UI / smoke / VM / deploy check 验证。
3. 派 independent second-opinion `code_reviewer` 做全 diff review，使用不同 framing，不读取第一次 review 的结论。
4. 涉及生产风险时派 `release_reviewer` 做 release-risk review。
5. 聚合 findings：
   - Implementation Gap：派回 worker 写失败测试 / 复现检查，再修复；
   - Design Gap：用业务语言交给用户；
   - Code-level Critical：派合适 worker 修；
   - Release Blocker：必须修或列为人工 gate，不能声称完成。
6. 每个 gap 最多 2 轮；Phase B 总 dispatch 上限 15 次。

无 design doc：

- 派 `code_reviewer` 对 `git diff <starting_commit>..HEAD` 做代码级全量 review；
- 高风险 diff 必须追加 `release_reviewer`。

通过标准：

- 可验证 design intent 全部通过，或未通过项被明确分类；
- 没有 blocker；
- 验证证据来自真实命令、browser / screenshot / DOM evidence 或人工检查清单；
- 残余风险能用业务语言解释。

### Phase C: Business Report

汇报：

- 完成了什么产品能力；
- 修改了哪些范围；
- 做过哪些 review loop 和 repair；
- 跑了哪些验证，结果是什么；
- 仍需人工验证或业务决策的事项；
- 残余风险和 architecture follow-up。

停止。此 skill 不自动 merge、push 或开 PR。

## 循环上限

| 循环 | 上限 | 超限处理 |
| --- | --- | --- |
| Phase 0a design review -> 主线程修复 | 2 轮 | 说明哪个 design 点需要产品 / 架构决策。 |
| Phase 0b plan review -> 主线程修复 | 2 轮 | 说明哪个 plan 点无法验真或需要决策。 |
| Phase A pack review -> worker repair | 每个 pack 3 轮 | 汇报 attempts，决定拆 pack / root-cause route / 用户决策。 |
| Phase B intent gap -> worker repair | 每个 gap 2 轮 | 区分 implementation gap 与 design gap。 |
| Phase B total dispatch | 15 次 | 汇报完成状态、剩余风险和决策点。 |

## Direction Check

当多轮 pack、review 或 compaction 后方向不清，先回答：

- 我在哪里：当前 phase / pack。
- 我要去哪：剩余 packs / phase。
- 目标是什么：重读 design intent。
- 已经学到什么：累计 review findings。
- 有什么变化：当前 plan checkbox 进度。

## 禁止事项

- 不跳过 Phase 0 或 Phase B。
- 不把 design / plan review 降级成代码 review。
- 不把代码 review 当成唯一 review。
- 不让用户为每个技术阶段下命令。
- 不自动 merge、push 或 create PR。
- 不为每个小 task 都 spawn agent。
- 不把 hooks 当作 workflow 真相源。
- 不把 external engineering skills 只写成方法名；必须按 references 和 agent TOML 中的具体行为执行。

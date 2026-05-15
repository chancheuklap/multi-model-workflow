---
name: orchestrate-workflow
description: 当已有 design / implementation plan，Superpowers writing-plans 刚生成项目文档，或用户要求执行、审核、继续、推进、恢复、完成一段有文档依据的开发工作流时使用。
---

# Orchestrate Workflow

这个 skill 负责 design / plan 之后的执行编排：Phase 0 审核、Task Pack 拆分、subagent 派发、review repair loop、root-cause route、最终意图验证和业务化汇报。

适用场景：

- 已有 `docs/superpowers/specs/` 下的 design doc。
- 已有 `docs/superpowers/plans/` 下的 plan。
- 用户要求执行、审核、继续、推进、恢复或完成一段已经文档化的开发工作。
- 已有 feedback loop 和 bug brief 的维护任务。

不用于原始 brainstorming、从零写 design / plan、很小的一次性改动、单纯只读 code review。

## Superpowers 边界

标准链路：

1. `superpowers:brainstorming` 澄清需求和方向。
2. `superpowers:writing-plans` 生成 design / plan 文档。
3. `orchestrate-workflow` 接管 design / plan 之后的审核、执行和验证。
4. `superpowers:finishing-a-development-branch` 只在工作完成后处理明确的 merge / PR / push 决策。

不要用这个 skill 替代 brainstorming 或 writing-plans；也不要在这里自动 merge、push 或开 PR。

## 主线程职责

主线程负责：

- 定位并完整阅读 design / plan。
- 读取当前项目规则，尤其是 `AGENTS.md`，以及其中要求的 `PROJECT.md`、`ENGINEERING-RULES.md`、SPEC、ADR、GUIDE 和相关 `AGENTS.override.md`。
- 直接修复 Phase 0 发现的技术性文档问题。
- 拆分 Task Pack，判断哪些 pack 真的能并行。
- 只在并行有价值或上下文隔离有价值时使用 `spawn_agent`。
- 整合 subagent 结果，更新 plan checkbox。
- 运行最终验证，用业务语言汇报状态。

派发 prompt 只传当前任务事实：文档位置、任务文本、约束、owned files、acceptance criteria、verification commands 和 risk flags。稳定方法已经写在对应 agent TOML 中，不要在每次派发时重复整段方法论。

## Agent 路由

| 工作类型 | agent_type | 责任 |
| --- | --- | --- |
| 小范围查代码、查调用链、查测试位置 | `code_explorer` | 只读，回答一个窄问题。 |
| 多模块调查、历史行为、未知 root cause | `complex_code_explorer` | 只读，先建立 feedback loop，区分事实和推断。 |
| 普通实现 pack、测试修复、局部重构 | `coding_worker` | owned files only，vertical-slice TDD，返回状态报告。 |
| 高风险实现 pack | `complex_coding_worker` | 先读 formal docs，处理 migration / billing / auth / runtime / contract / rollback 风险。 |
| design、plan、pack review | `code_reviewer` | 只读 finding，先审 spec compliance，再审 code quality。 |
| 发布前或生产风险 review | `release_reviewer` | 审数据、账务、权限、迁移、部署、回滚、人工验证风险。 |
| 低风险文档整理 | `docs_worker` | 只改授权文档，保留既有决策；遇判断题返回 `NEEDS_CONTEXT`。 |

`spawn_agent` 只用于独立 sidecar work。`send_input` 只在同一个 pack 的 repair 需要延续上下文时使用。`wait_agent` 只在下一步真的被该结果阻塞时使用。用完的 agent 要关闭。

## 派发 Prompt 必须包含

- phase 和目的。
- 需要读取的 design / plan / Task Pack / diff / files。
- 项目锚点：`AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、相关 SPEC / ADR / GUIDE、相关 `AGENTS.override.md`。
- owned files 或只读边界。
- acceptance criteria 和 verification commands。
- risk flags：billing、permissions、migrations、runtime、browser takeover、cross-service contract、deploy、rollback、manual validation。
- 本次返回格式。

不要包含：

- `code_reviewer`、`coding_worker`、`complex_code_explorer`、`release_reviewer` 的完整方法文本。
- 只有方法名称、没有任务事实的空泛要求。
- 作为 runtime 前置条件的 reference 文件。

## 循环上限

| 循环 | 上限 | 超出后 |
| --- | --- | --- |
| Phase 0a design review -> 主线程修复 | 2 轮 | 说明哪个 design 点需要产品决策。 |
| Phase 0b plan review -> 主线程修复 | 2 轮 | 说明哪个 plan 点无法被验证。 |
| Phase A pack review -> worker repair | 每个 pack 3 轮 | 汇报 attempts，并决定拆 pack、进入 root-cause route 或请求用户决策。 |
| Phase B intent gap -> worker repair | 每个 gap 2 轮 | 区分 implementation gap 和 design gap。 |
| Phase B total dispatch | 15 次 | 汇报完成状态、剩余风险和决策点。 |

重复尝试必须改变方法。不要用同一套假设反复跑。

## Phase 0a: Design Review

如果存在 design doc：

1. 完整读取 design doc。
2. 派 `code_reviewer` 审内容、术语、AgentFlow 文档 alignment。
3. 涉及架构、账务、权限、迁移、部署、runtime、rollback 或 cross-service contract 时，改用或追加 `release_reviewer`。
4. 汇总 findings。
5. 技术性文档问题由主线程直接修。
6. 只有 design 会改变产品承诺、用户可见行为、业务规则、发布策略或 trade-off 时才问用户。
7. 如果 design review 通过但还没有 plan，使用 `superpowers:writing-plans` 生成 plan，然后进入 Phase 0b。

## Phase 0b: Plan Review

1. 完整读取当前 plan。
2. 用 `code_reviewer` 做 coverage、compliance 和 independent second-opinion review；生产风险 plan 用 `release_reviewer`。
3. 主线程直接修复 stale paths、缺失验证、缺失 `AGENTS.override.md` 同步任务、unsupported routing 等技术性 plan 问题。
4. 只有业务或架构决策才停下来问用户。

## Setup: Task Pack Planning

按以下维度把未完成 plan tasks 分成 Task Packs：

- shared files；
- dependency order；
- section boundaries；
- risk level；
- expected test scope；
- AFK / HITL classification。

Task Pack 必须是 vertical slice，完成后能 demo 或 independently verify。避免 horizontal slicing，例如“先写全部 tests / templates / schema，再写 implementation”。

会碰同一批文件、migration、billing state、auth、runtime scheduler、browser takeover 或 shared contracts 的 packs 默认串行；只有 write set 明确不相交时才并行。

## Phase A: Task Pack Execution

每个 pack：

1. 用 `coding_worker` 或 `complex_coding_worker` 派发完整任务文本、owned files、acceptance criteria、项目规则、no-revert 要求和 verification commands。
2. worker 完成后用 `code_reviewer` review。reviewer 负责 spec compliance、public-behavior evidence、no-internal-mock、vertical-slice 和 architecture-finding 检查。
3. finding 有效且上下文延续重要时，用 `send_input` 发回同一个 worker 修复。
4. 如果失败不是局部问题，派 `complex_code_explorer` 做 feedback-loop-first investigation，或派 `complex_coding_worker` 做紧耦合 diagnosis + fix。
5. 修复后重跑 focused verification。

独立 packs 可以并行。不要把下一步立即依赖的关键路径任务丢给 subagent 后空等。

## Maintenance Bug Entry

没有完整 plan 的 bug：

1. 先用 systematic debugging / diagnose 方法建立 feedback loop。
2. 写 bug brief：current behavior、desired behavior、reproduction、hypotheses、key interfaces、acceptance criteria、out of scope。
3. 如果修复很小且局部，主线程直接用 focused tests 处理。
4. 如果影响 runtime、billing、migration、permission、shared contract、deploy 或多个模块，先创建或修复 plan，再进入 Phase 0b / Phase A。

## Phase B: Final Intent Verification

packs 通过后：

1. 用真实命令和输出端到端验证 design intent，不用 implementer self-report 代替。
2. 跑相关 focused tests、release-gate checks、smoke commands、browser checks、VM checks 或人工验证清单。
3. diff 触及 deploy、database、billing、permissions、runtime、browser takeover、rollback、production dependency 或 cross-service contract 时，用 `release_reviewer`。
4. 非生产风险但仍有最终缺口时，可用独立 `code_reviewer` 做 second opinion。
5. implementation gap 派给合适 worker；design gap 用业务语言交给用户决策。
6. architecture after-effects 记录为 follow-up；只有造成 release risk 才阻塞交付。

## Phase C: Business Report

汇报：

- 已完成的产品能力。
- review loops 和修复。
- validation commands 和结果。
- 仍需人工或产品决策的点。
- residual risk 和 architecture follow-up。

汇报后停止。不要从这个 skill 自动 merge、push 或开 PR；明确收分支时使用 `superpowers:finishing-a-development-branch`。

## Direction Check

当多轮 pack、review 或 compaction 后方向不清，先回答：

- 我在哪里：当前 phase / pack。
- 我要去哪：剩余 packs / phase。
- 目标是什么：重读 design intent。
- 已经学到什么：累计 review findings。
- 有什么变化：当前 plan checkbox 进度。

## 禁止事项

- 不跳过 Phase 0 或 Phase B。
- 不让用户为每个技术阶段下命令。
- 不自动 merge、push 或 create PR。
- 不为每个小任务都 spawn 一个 agent。
- 不把 hooks 当作唯一 enforcement boundary。
- 不同时安装多个互相覆盖的 repo-local、user-level、plugin-installed skill 副本。

---
name: orchestrate-workflow
description: 当已有 design / implementation plan，Superpowers writing-plans 刚生成项目文档，或用户要求执行、审核、继续、推进、恢复、完成一段有文档依据的开发工作流时使用。
---

# Orchestrate Workflow

你是主线程 coordinator。接管 `superpowers:writing-plans` 之后的 post-design workflow：design review、plan review、Task Pack execution、pack review、root-cause repair、final intent / release review、business report。

## Use / Skip

使用：

- 已有或刚生成 design doc。
- 已有或刚生成 implementation plan。
- 用户要求执行、审核、推进、继续、落地。
- 有 bug brief、feedback loop 或维护问题需要计划化推进。

不使用：

- 从零澄清需求：用 `superpowers:brainstorming`。
- 从零写 design / plan：用 `superpowers:writing-plans`。
- 单次只读 code review：直接按 review 请求处理。
- merge / PR / push / discard：用 `superpowers:finishing-a-development-branch`。

进入本 skill 后，不再单独调用 post-plan Superpowers execution skills。本 skill 内部承担 plan execution、subagent dispatch、parallel dispatch、code review、review repair、debugging、TDD 和 completion verification。

## Operating Loop

1. 识别入口：design -> Phase 0a；plan -> Phase 0b；bug -> Maintenance；已实现 diff -> Phase B 或单次 review。
2. 建立 anchors：project、mockup、contract。
3. 读取当前 phase 的 reference，把 review / worker contract 写进 dispatch prompt。
4. Phase 0a 审 design；Phase 0b 审 plan；技术性文档缺口由主线程修。
5. 把 plan task 重切成 Task Packs；不合格 pack 先重切。
6. 按 risk 派 worker；只有独立 pack 才并行。
7. Worker 返回后做 gated pack review：Spec Compliance 通过后才做 Code Quality。
8. 生产风险追加 `release_reviewer`，不能替代 baseline `code_reviewer`。
9. finding 回原 worker、root-cause explorer、release reviewer 或用户决策。
10. 全部 pack 通过后做 Phase B final intent / diff / release review，再给业务汇报。

## Hard Rules

- Phase 0 和 Phase B 不能跳过。
- Task Pack 是执行单位；plan task 只是原材料。
- `Read first:`、`Project baseline:`、`Contract anchors:`、`Mockup anchors:` 必须进 dispatch prompt。
- Reviewer 不信 worker self-report，必须看代码、diff、测试或运行证据。
- Bug 先建 feedback loop，再猜根因。
- Tests 验 public behavior，不测 private helper 和内部调用顺序。
- 同文件、同合同、同 migration、同权限、同账务、同 runtime 边界默认不并行。
- 没有真实验证证据，不声称完成。
- 不自动 merge、push 或 create PR。

## Anchors

每个 phase 先确定：

- Project：根 `AGENTS.md`；其链入的 `PROJECT.md`、`ENGINEERING-RULES.md`、SPEC、ADR、GUIDE；相关 `AGENTS.override.md` / `agents.overrides.md`。
- Mockup：UI / UX mockup、截图、HTML 原型、页面参考；目标页面、role、viewport、states、interaction、允许偏差。
- Contract：API、Pydantic、DB、JSON、sync、task payload、billing、permission、runtime、capability、UI action、helper boundary；owner、provider、consumer、verifier、model、schema_version、registry / migration / catalog、repository / read model、tests / release gate。

缺少 in-scope anchor 时，先补上下文或返回 `NEEDS_CONTEXT` / `BLOCKED`，不要自创 dict、route-local schema、临时 helper 或 UI 方向。

## Agent Routing

| 场景 | agent_type |
| --- | --- |
| baseline design / plan / pack / final review | `code_reviewer` |
| production-risk supplement | `release_reviewer` |
| 普通 Task Pack / 明确 code finding 修复 | `coding_worker` |
| 高风险 Task Pack / 高风险 repair | `complex_coding_worker` |
| 未知根因调查 | `complex_code_explorer` |
| 紧耦合 root-cause 修复 | `complex_coding_worker` |
| 低风险文档整理 | `docs_worker` |

工具映射：

- 新建独立任务：`spawn_agent`
- finding 回原 worker：`send_input`
- 下一步被结果阻塞时才 `wait_agent`
- 任务完成后关闭不再需要的 agent

## Phase Gates

### Phase 0a: Design Review

入口：存在 design doc，或 `writing-plans` 刚生成 design doc。

- 先读 `references/design-review.md`；涉及 API / Pydantic / DB / JSON / helper 边界时再读 `references/contract-boundary.md`。
- 派两个独立 `code_reviewer`：Design Content Review、Project Alignment Review。
- 有 production risk 时，在 baseline review 后追加 `release_reviewer`。
- 技术性文档缺口由主线程修；产品承诺、业务规则、UX、发布策略、架构 trade-off 才问用户。
- 状态机、UI 方向或接口形状无法靠文档判断时，按 Prototype Gate 做 throwaway prototype。
- design 合格但没有 plan 时，调用 `superpowers:writing-plans` 写 plan，再进入 Phase 0b。
- 最多 2 轮；超出后汇报哪个 design 点需要产品 / 架构决策。

通过：没有 Critical design finding；核心 intent 可验证；失败/权限/重复/回滚场景能解释；新对象/状态/合同有责任归属；contract anchors 明确。

### Phase 0b: Plan Review

入口：存在 active plan。

- 先读 `references/plan-review.md` 和 `references/task-pack-contract.md`；涉及 API / Pydantic / DB / JSON / helper 边界时再读 `references/contract-boundary.md`。
- 派三个独立 `code_reviewer`：Coverage、Compliance / Verification、Second Opinion。
- 有 production risk 时追加 `release_reviewer`。
- 主线程修 stale path、虚构 helper、缺测试、override 同步缺口、pack 横切、依赖错误。
- 最多 2 轮；超出后汇报哪个 plan 点无法验真或需要决策。

通过：design intent 被覆盖；task 可执行；已有路径/函数/fixture/命令已验真；每个 task 有验证；contract consumer / registry / migration / catalog 清楚；可拆成 vertical Task Packs。

### Setup: Task Pack Planning

- 先读 `references/task-pack-contract.md`。
- 提取未完成 plan tasks。
- 按可验证行为重切 Task Packs。
- 同文件、同合同、同 migration、同权限、同账务、同 runtime 边界放同一 pack 或串行。
- 独立 pack 才并行。
- 每个 pack 标注 goal behavior、owned scope、anchors、acceptance criteria、verification、risk、AFK/HITL、dependencies、out of scope。

不合格 pack 先重切，不派发。

### Phase A: Execution + Pack Review

每个 pack：

1. 普通 pack 派 `coding_worker`；高风险 pack 派 `complex_coding_worker`。
2. dispatch prompt 包含完整 Pack Brief、anchors、verification、risk、no unauthorized revert、返回格式。
3. worker 返回后先读 `references/implementation-review.md`；涉及 API / Pydantic / DB / JSON / helper 边界时再读 `references/contract-boundary.md`。
4. 派 `code_reviewer` 做 Pack Review。
5. Pack Review 先 Spec Compliance；通过后才 Code Quality。
6. production-risk pack 追加 `release_reviewer`。
7. 明确代码 finding 回原 worker；根因不明走 `complex_code_explorer`；紧耦合修复走 `complex_coding_worker`；业务范围变化问用户。
8. 每个 pack 最多 3 轮 repair；每轮必须改变方法。

通过：spec / quality 通过；focused verification 已运行；UI / UX 有 visual evidence；tests 验 public behavior；contract boundary 闭合；没有 Critical / High finding。

### Maintenance Bug Entry

没有完整 plan 的 bug：

- 先读 `references/external-engineering-methods.md`。
- 先建立 feedback loop，不先写补丁。
- 形成 bug brief：current behavior、desired behavior、reproduction、hypotheses、key interfaces、acceptance criteria、out of scope。
- 小范围局部修复可主线程处理。
- 多个独立失败按 problem domain 分组；无共享状态、文件或合同边界时可并行调查。
- 相关失败、共享状态、共享文件、共享合同边界或一个修复可能影响多个失败时，先合并调查。
- 触碰 runtime、billing、migration、permission、API / Pydantic / DB / JSON boundary、shared contract、deploy 或多模块时，先补 plan，再走 Phase 0b / Phase A。

### Phase B: Final Intent / Release Review

所有 pack 通过后执行。

- 先读 `references/final-review.md`；涉及 API / Pydantic / DB / JSON / helper 边界时再读 `references/contract-boundary.md`。
- 有 design doc：派 `code_reviewer` 做 final intent review，再派 independent `code_reviewer` 做 diff review。
- 无 design doc：派 `code_reviewer` 对 `git diff <starting_commit>..HEAD` 做全量 review。
- 有 production risk 时追加 `release_reviewer`。
- finding 分类：Implementation Gap 回 worker；Design Gap 给用户；Code-level Critical 派 worker；Release Blocker 必须修或列 manual gate。
- 每个 gap 最多 2 轮；Phase B 总 dispatch 上限 15 次。

通过：可验证 intent 全部通过或明确分类；contract boundary、producer / consumer、registry、migration、read model、release gate 闭合；没有 blocker；验证证据真实。

### Phase C: Business Report

汇报：

- 完成的产品能力。
- 修改范围。
- review loop 和 repair。
- 验证命令和结果。
- 人工验证或业务决策。
- 残余风险和 architecture follow-up。

## Direction Check

多轮 pack、review 或 compaction 后方向不清时，先回答：

- 当前 phase / pack。
- 剩余 packs / phase。
- design intent。
- 累计 review findings。
- plan checkbox 进度。

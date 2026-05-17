---
name: orchestrate-plan-writing
description: "当 AgentFlow 已有 reviewed source design / design document / SPEC / existing PRD / explicit requirements，并且已有 mattpocock-skills:to-issues 产出的 vertical large issues / small issues，或用户要求把 design、PRD、issues 转成 implementation plan、Task Pack plan、issue-backed plan 时主动使用。负责生成可进入 Orchestrate Phase 0b 的 plan：large issue 映射 plan section，small issue 映射 Task Pack，pack 内写细 task；缺 source design 时返回 NEEDS_DISCOVERY，缺 issue hierarchy 时返回 NEEDS_ISSUES。"
---

# Orchestrate Plan Writing

只负责生成 plan，不执行、不做 Phase 0b review、不临场派发 worker。

固定结构：

```text
source design / design document / requirements
  -> vertical large issue
  -> vertical small issue
  -> Task Pack
  -> pack-local implementation tasks
```

Plan 生成或修复后交回 `orchestrate-workflow`，从 Phase 0b Plan Review 重新进入。除非 source design、issue hierarchy 或 scope 改变，不回 Discovery、不重跑 Phase 0a、不派 worker。

## 范围输入

只消费用户明确提供或 Orchestrate parent 明确确认的 source design / requirements / issues。Design、SPEC、ADR 或 PRD 中引用的其它 issue，不会自动成为 plan source。

缺 small issue hierarchy 时返回 `NEEDS_ISSUES`。如果当前项目使用 GitHub Issues，而用户提供的是 parent large issue 文档，small issue 拆分必须先写回 parent large issue 文档，作为待上传 / 待确认的 issue hierarchy；不要自行创建新的 standalone issue 文档。

## 入口判断

先定位这些输入：

- source design / design document / SPEC / existing PRD / bug brief / explicit requirements；
- Phase 0a 通过结论，或等价 review 结论；
- 用户明确提供或 parent 明确确认的 `to-issues` vertical large issues；
- 每个 large issue 下的 vertical small issues；
- 项目 anchors：根 `AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、相关 ADR / SPEC / GUIDE / runbook、触碰目录的 `AGENTS.override.md` / `agents.overrides.md`；
- 涉及 UI / UX 时的 mockup anchors：路径、页面、viewport、states、interaction、允许偏差、visual verification；
- 涉及 API / Pydantic / DB / JSON / sync / billing / permission / runtime / helper 时的 Contract anchors：owner、provider、consumer、model、schema_version、registry / migration / catalog、repository / read model、verification。
- 涉及 migration / billing / permission / runtime / cross-service contract / deploy order / rollback / manual gate 时的发布风险事实：风险面、source issue、是否需要提前 review、Phase B 需要什么证据、manual gate owner。plan-writing 负责写进 plan 的“发布风险和人工门禁”；source facts 不足时返回 `NEEDS_DISCOVERY`。

缺正式输入时不要保存半成品，按缺件返回。可以给 `to-issues` 提供 suggested vertical slices；这些 slices 在 `to-issues` 确认前不能写成正式 Task Pack。

| 缺件 / 阻塞 | 返回 | 交回 Orchestrate 的 route |
| --- | --- | --- |
| 没有 source design / source requirements | `NEEDS_DISCOVERY` | `orchestrate-discovery` |
| design 没有 review 结论 | `NEEDS_DESIGN_REVIEW` | Phase 0a |
| 缺 large issue、small issue，或 small issue 不能独立验证 | `NEEDS_ISSUES` | upstream `to-issues` |
| issue ready state、AFK / HITL、blocked-by 不清 | `NEEDS_TRIAGE` | upstream `triage` |
| 业务术语、对象 owner、UI target state、permission、billing、lifecycle 或验收口径不清 | `NEEDS_DISCOVERY` | `orchestrate-discovery` |
| bug / wrong state / performance regression 缺复现、feedback loop、症状或 hypotheses | `NEEDS_DIAGNOSIS` | `orchestrate-discovery` / upstream `diagnose` |
| 状态行为、interface shape 或 UI 方向需要方案比较 | `NEEDS_DECISION` | User Decision / upstream `prototype` |
| bad seam、repeated repair、single-adapter interface 或错误测试面暴露 | `NEEDS_ARCHITECTURE` | upstream `improve-codebase-architecture` |
| 模块地图、调用链或风险区域不足，影响 pack 边界 | `NEEDS_CONTEXT` | `code_explorer` / `complex_code_explorer` / upstream `zoom-out` / `orchestrate-discovery` |

## 写作流程

1. 读取 source design / requirements，提取 goal、architecture、tech stack、用户可见行为、系统可验证行为、合同边界、UI 状态、失败场景和 out of scope。
2. 读取 `references/issue-to-pack-contract.md`，确认 large issue 可以成为 plan section、small issue 可以成为 Task Pack；不成立时按入口判断返回。
3. 读取 `references/plan-document-contract.md`，写 plan：Header、Scope Check、Source Coverage Map、File / Responsibility Map、发布风险和人工门禁、large issue sections、Task Packs、pack-local implementation tasks。
4. 读取 `references/plan-quality-gates.md`，删除过度设计，补齐设计不足；如果缺口来自 issue 边界、业务决策或架构 friction，按入口判断返回。
5. 读取 `references/plan-self-review.md`，保存前自审并修正。
6. 保存到 `docs/orchestrate/plans/YYYY-MM-DD-<feature-name>.md`，除非用户或项目规则指定其他路径；保存前创建父目录。

## 必须遵守

- 一级章节对应 vertical large issue；每个 Task Pack 对应一个 vertical small issue。
- Task Pack 是 Orchestrate 派发单位；细 task 只服务 pack 内执行。
- `Execution owner` 必须是 `Orchestrate Workflow`；不要添加额外 execution handoff。
- 没有 `to-issues` 确认的 issue hierarchy，不生成正式 issue-backed plan。
- 不能把未提及 issue、read-only context、reviewer 顺手提到的 ADR / issue 纳入 Source issues。
- 缺 small issue hierarchy 时，返回 `NEEDS_ISSUES`，并说明应写回哪个 parent large issue 文档；不要临场新建 issue 文档。
- 不自行发明业务行为、术语、schema、helper 位置、UI 状态、issue hierarchy、验收门槛或路径事实。
- existing paths、commands、fixtures、endpoints、mockup paths 必须验真；新文件标为 `Create`。
- in-scope Project / Contract / Mockup anchors 必须进入对应 Task Pack；缺 anchors 时 route，不用 `N/A` 掩盖缺口。
- 同一文件、shared contract、migration、permission、billing、runtime、release boundary 默认串行或同 pack。
- 不写 placeholder：`TBD`、`TODO`、`later`、`defer`、`write tests`、`add validation`、`handle edge cases`、`implement logic`、`similar to previous`。
- plan 是 Phase 0b 的可审执行合同，不是直接开工指令。

## 成功返回

```text
### Verdict
PLAN_CREATED

### Plan path
- <path>

### Inputs consumed
- Source design / requirements:
- Source issues:
- Project / Contract / Mockup anchors:
- 发布风险和人工门禁:

### Issue mapping
- Large issues:
- Task Packs:
- Known dependencies:

### Quality gate
- Overdesign checked:
- Underdesign checked:
- Largest remaining risk:

### Open items
- HITL / blockers:
- Checks not run:
```

## 失败返回

```text
### Verdict
NEEDS_DISCOVERY / NEEDS_CONTEXT / NEEDS_DESIGN_REVIEW / NEEDS_ISSUES / NEEDS_TRIAGE / NEEDS_DIAGNOSIS / NEEDS_DECISION / NEEDS_ARCHITECTURE

### Missing
- 缺少的 source / issue / decision / feedback loop / route state

### Route
- Phase 0a / orchestrate-discovery / upstream to-issues / upstream triage / upstream diagnose / upstream zoom-out / upstream prototype / upstream improve-codebase-architecture / code_explorer / complex_code_explorer / user decision

### Suggested prompt
- 可直接交给 Orchestrate / upstream skill / explorer 的简短输入
```

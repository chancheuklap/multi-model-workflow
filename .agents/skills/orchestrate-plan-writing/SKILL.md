---
name: orchestrate-plan-writing
description: "从已 review 的 design / SPEC / PRD 文档，以及 mattpocock-skills:to-issues 产出的垂直大 issue / 小 issue，生成 AgentFlow 可执行的 issue-backed implementation plan。用于把大 issue 映射成 plan section，把小 issue 映射成 Orchestrate Task Pack；缺少 issue hierarchy 时返回 NEEDS_ISSUES 并交回 Orchestrate 使用 to-issues。"
---

# Orchestrate Plan Writing

## 职责

把已 review 的 source design / requirements 和 `to-issues` issue hierarchy 写成正式 implementation plan。

固定层级：

```text
source design / requirements
  -> vertical large issue
  -> vertical small issue
  -> Task Pack
  -> fine-grained implementation tasks
```

本技能只生成 plan。`orchestrate-workflow` 负责 Phase 0b review、Task Pack 派发、执行、repair、Phase B final intent review 和业务汇报。

开始时说明：正在使用 `orchestrate-plan-writing` 生成 issue-backed implementation plan。

## Reference 按需加载

不要在启动时一次性读取全部 reference。先用本文件完成入口判断和输入检查；走到哪个决策面，再读取对应 reference。

| 需要判断什么 | 读取 |
| --- | --- |
| large issue 能否映射为 plan section、small issue 能否映射为 Task Pack、缺 issue 时如何 route | `references/issue-to-pack-contract.md` |
| 已确认 issue hierarchy 后，正式写 plan header、Scope Check、Source Coverage Map、File / Responsibility Map、Task Pack brief、细 task 和验证语言 | `references/plan-document-contract.md` |
| plan 初稿已经形成后，检查质量、过度设计和设计不足 | `references/plan-quality-gates.md` |
| 保存前最终自审，确认 coverage、executability、pack quality 和 red flags | `references/plan-self-review.md` |

如果用户只要求解释这个技能，只读本文件。如果输入检查已经能返回 `NEEDS_CONTEXT`、`NEEDS_DESIGN_REVIEW`、`NEEDS_ISSUES` 或 `NEEDS_TRIAGE`，不要继续读取后续 plan 写作 reference。

## 输入检查

必须先确认：

- 有 source design、SPEC、PRD、bug brief 或明确 requirements。
- source design 已通过 Phase 0a 或有等价 review 结论。
- 有 `to-issues` 产出的 vertical large issues。
- 每个 large issue 下都有 `to-issues` 产出的 vertical small issues。
- 已读取项目 anchors：根 `AGENTS.md`、`PROJECT.md`、`ENGINEERING-RULES.md`、相关 ADR / SPEC / GUIDE / runbook、触碰目录最近的 `AGENTS.override.md` / `agents.overrides.md`。
- UI / UX 工作有 mockup anchors：截图、HTML prototype、页面路径、viewport、states、interaction、允许偏差、visual verification。
- 合同工作有 Contract anchors：owner、provider、consumer、model、schema_version、registry / migration / catalog、repository / read model、verification。

不要自行发明业务行为、术语、schema、helper 位置、UI 状态、issue hierarchy 或验收门槛。

## 上游联动

遇到缺件时返回结构化 route，由主线程调用对应 upstream skill，再回到本技能。

| 信号 | 返回 | 上游 route |
| --- | --- | --- |
| 没有 source PRD / design / requirements | `NEEDS_CONTEXT` | `to-prd` 或 `grill-with-docs` |
| source design 没有 review 结论 | `NEEDS_DESIGN_REVIEW` | `orchestrate-workflow` Phase 0a |
| 缺少 vertical large issue | `NEEDS_ISSUES` | `to-issues` |
| 大 issue 下面缺少 vertical small issue | `NEEDS_ISSUES` | `to-issues` |
| 小 issue 太大，无法成为单个可验证 Task Pack | `NEEDS_ISSUES` | `to-issues` |
| issue ready state、AFK / HITL、blocked-by 不清 | `NEEDS_TRIAGE` | `triage` |
| 业务术语、对象 owner、UI target state、permission、billing、lifecycle 或验收口径不清 | `NEEDS_CONTEXT` | `grill-with-docs` |
| bug / wrong state / performance regression 缺少复现、feedback loop、真实症状或 hypotheses | `NEEDS_DIAGNOSIS` | `diagnose` |
| state machine、interface shape 或 UI 方向需要比较方案 | `NEEDS_DECISION` | `prototype` |
| 暴露 bad seam、repeated repair、single-adapter interface 或错误测试面 | `NEEDS_ARCHITECTURE` | `improve-codebase-architecture` |
| 需要切 pack 但模块地图、调用链或风险区域不足 | `NEEDS_CONTEXT` | `zoom-out` |

可以向 `to-issues` 提供 suggested vertical slices，但这些只是输入提示；没有经过 `to-issues` 输出确认前，不能把它们写成正式 Task Pack。

## 写作流程

1. 读取 source design / requirements，提取 goal、architecture、tech stack、交付意图、用户可见行为、合同边界、UI 状态、失败场景和 out of scope。
2. 完成输入检查；缺件时按“上游联动”返回。
3. 读取 `references/issue-to-pack-contract.md`，确认 issue hierarchy 可以转换成 plan section 和 Task Pack；如果不能，按“上游联动”返回，不继续读取 plan 写作 reference。
4. 读取 `references/plan-document-contract.md`，写 plan 初稿。
5. 读取 `references/plan-quality-gates.md`，删除过度设计，补齐设计不足；如果缺口来自 issue 边界、业务决策或架构 friction，按 route 返回。
6. 读取 `references/plan-self-review.md`，保存前自审并修正 plan。
7. 保存到 `docs/orchestrate/plans/YYYY-MM-DD-<feature-name>.md`，除非用户或项目规则指定其他路径；保存前创建父目录。
8. 返回 plan path、source docs、issue inventory、coverage summary、HITL / blockers、自审结果和未运行检查。

## 失败返回

无法生成 plan 时不要保存半成品。返回：

```text
### Verdict
NEEDS_CONTEXT / NEEDS_DESIGN_REVIEW / NEEDS_ISSUES / NEEDS_TRIAGE / NEEDS_DIAGNOSIS / NEEDS_DECISION / NEEDS_ARCHITECTURE

### Missing
- 缺少的 source / issue / decision / feedback loop / route state

### Upstream route
- to-prd / to-issues / triage / grill-with-docs / diagnose / prototype / improve-codebase-architecture / zoom-out

### Suggested prompt
- 可直接交给 upstream skill 的简短输入
```

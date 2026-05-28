# Design Review Angles + Dispatch Details

> **流程位置**：`orchestrate-discovery` Steps 10-11 · Design Review 派发 + 修复 · 通过后回到 SKILL.md Step 12

## Self-Read Protocol

你是 codex-reviewer（执行 Design Review）。启动时按以下顺序执行：

1. 读 dispatch prompt 头部的 `DISPATCH_ENVELOPE`，提取 `run_id`、`gate`、feature slug。
2. 读 `<project_root>/CLAUDE.md` 和 `<project_root>/CONTEXT.md`（若存在）获取项目基线、不变量、contract wall。
3. 读 `docs/orchestrate/design/<slug>.md` 获取设计文档全文。
4. 读本文件（你正在读的这份手册），理解 Review Angles 与 Return Contract 格式。
5. 按两个 Baseline Review angle 独立验证，遵守 Pre-emit Verification Gate，输出 findings。

## Codex Dispatch 公共部分

两个 review angle 分别提交 Codex review 任务，可并行提交，结果独立返回。

**Read** `plugin/skills/_shared/review-dispatch.md` 并按其格式派发 Codex review。

**整体 Verdict 前置检查**：如果 reviewer 返回整体 `needs context`（不是某条 finding 的 `needs evidence`），说明 reviewer 无法完成审查。Coordinator 补充 reviewer 所需的上下文后重新 dispatch，不进入 per-finding disposition。

每条 finding 使用 Finding Shape：`severity / confidence / locator / evidence / impact / remediation`。

## Baseline 1: Design Content Review

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/design-content-review.md`：

```markdown
## Scope
Design Content Review — 审设计自身是否完整、可测试、可执行。

## Read first
自读：`<project_root>/CLAUDE.md`、`<project_root>/CONTEXT.md`（若存在）、相关 ADR 文件。

## Source design
docs/orchestrate/design/<slug>.md

## Project baseline
自读 `docs/orchestrate/design/<slug>.md` 中 `## Cross-Plan Contract Anchors` 节（若设计触碰合同边界）。

## Review angles

### 业务术语一致性
设计文档中的术语是否与 CONTEXT.md / ADR 一致。

### 用户旅程覆盖
每条用户可感知的行为是否有对应的目标描述。

### 可测试性
每条目标行为是否可通过命令、断言或截图验证。不可测的 intent 是 finding。

### UI mockup 转化（与设计文档同等重要）
Mockup 是可视化设计文档，地位与文字设计文档平等。如有 mockup（docs/orchestrate/mockups/<slug>/），检查：
- 每个 mockup 页面 × viewport × states 是否已在 `## UI / UX 状态` 中拆解为具体视觉规格（布局/颜色/字体/间距/组件结构）
- 拆解出的视觉规格是否可直接转为 issue 和 plan 的 acceptance criteria（不是"见 mockup"指针）
- 交互行为（点击/hover/输入/动画）是否逐项描述
- 状态变体（空/加载/错误/成功/权限不足）是否在 mockup 中体现并描述

### Contract anchors
跨边界数据是否有 Contract anchors（boundary type / owner / provider / consumer / verifier）。缺 anchors 是 finding。

### 失败场景
错误路径、边界条件、回退策略是否覆盖。

### Scope 纪律
是否混入了未来需求或超出 scope 的能力。

## Critical 定义
以下为 Critical（必须修复才能进入 plan）：
- 核心意图不可测
- 目标行为含混导致 plan 必须猜
- UI 有 mockup 但没拆解为具体视觉规格表（只写了目录路径不算转化）
- 合同缺 anchors
- 文档内部矛盾
- 关键场景缺失
- 新对象缺 owner

## Calibration
只标记会导致实际问题的 issue。措辞改进、风格偏好、"某些 section 不够详细"——不是 finding。除非有严重缺口会导致有缺陷的 plan，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots
### Result
Review: 设计文档 - Design Content Review
Phase summary: 通过 / 阻塞
Critical:
Important:
低置信度观察:
Disposition required:
### Verification
- 已运行的 commands 和结果
### Open Items
- parent 必须处理的问题
```

## Baseline 2: Project Alignment Review

Review prompt 写入 `.claude/multi-model-workflow/review-prompts/design-alignment-review.md`：

```markdown
## Scope
Project Alignment Review — 审设计是否符合项目事实和约束。

## Read first
自读：`<project_root>/CLAUDE.md`、`<project_root>/CONTEXT.md`（若存在）、相关 ADR 文件。

## Source design
docs/orchestrate/design/<slug>.md

## Project baseline
- 北极星 / 不变量 / 数据权威 / contract wall
自读 `<project_root>/CONTEXT.md` 和相关 ADR 获取不变量定义。

## Contract anchors
自读 `docs/orchestrate/design/<slug>.md` 中 `## Cross-Plan Contract Anchors` 节（若设计触碰合同边界）。

## Review angles

### 项目术语
设计文档中的术语是否与项目既有定义一致。

### 数据权威和模块边界
新增数据的权威来源是否明确，是否跨越了既有模块边界。

### 不变量
设计是否违反项目声明的不变量。

### 新端口注册
新增的 port / command / chargeable action / capability 是否进入 registry / catalog。

### Migration tree
新增 DB 字段 / schema 变更是否有对应 migration。

### Helper placement
新增 helper 是否放在正确的模块边界内（不为绕过边界而存在）。

### 基础设施依赖
设计依赖的基础设施（队列、缓存、外部服务）是否已存在或有创建计划。

### ADR 条件
是否触发了需要新 ADR 的架构决策。

## Critical 定义
以下为 Critical（必须修复才能进入 plan）：
- 违反北极星或不变量
- 依赖不存在的基础设施
- 跨服务合同缺 producer-consumer
- 绕过 Pydantic / registry / migration
- 未设计生产风险

## Calibration
只标记会导致实际问题的 issue。措辞改进、风格偏好——不是 finding。除非有严重缺口会导致有缺陷的 plan，否则 approve。

## Return Contract
### Verdict
pass / blocked / needs repair / needs context
### Evidence
- 实际检查过的 files / docs / tests / commands / screenshots
### Result
Review: 设计文档 - Project Alignment Review
Phase summary: 通过 / 阻塞
Critical:
Important:
低置信度观察:
Disposition required:
### Verification
- 已运行的 commands 和结果
### Open Items
- parent 必须处理的问题
```

---
## Disposition 流程

**Read** `plugin/skills/_shared/disposition-table.md` 并按其 disposition 选项处理 findings。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 Reviewer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`gate`（`design-content-review` / `design-alignment-review`）、`review_intent: "baseline"`。
2. 在 `Source design:` 中列出 design 文件路径（reviewer 自读全文）。
3. 写 review-prompts 文件，运行 validate/record 脚本，触发 Codex job。
4. 等待 job 完成后运行 result/complete 脚本，进入 Disposition 流程。

> **下一步**：Design Review 通过 → 回到 SKILL.md Step 12（大 issue 拆分）。needs repair → Coordinator 直接修设计文档 → targeted re-review。

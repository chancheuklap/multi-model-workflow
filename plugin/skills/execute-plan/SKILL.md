---
name: execute-plan
description: |
  Use when a plan exists in docs/superpowers/plans/ and the user wants to
  begin or continue implementation. Trigger: "execute the plan", "start
  implementing", "let's go", "continue the work", "开始落地", "执行方案",
  "开始实施", or references to an existing plan.
---

# 执行实施计划

你是编排器。你调度 agent 团队完成工作，通过 review 循环保证质量。Phase 0 的文档修复由你直接处理（你拥有完整的用户上下文）；生产代码由 sub-agent 编写。

## 核心原则

1. **升级规则**：技术问题 agent 自主解决。仅当"用户能做什么"会变时，用非技术语言询问用户。
2. **上下文连续**：同一 pack 内 review → 修复用 SendMessage 继续原 agent。跨 pack 或新问题用 Agent tool 新建。
3. **循环有限**：每个 review 循环有硬性上限。超限不是失败，是需要用户业务决策。

## 通信架构

严格 hub-and-spoke：subagent 之间不能直接通信。所有结果返回主 session，所有调度由主 session 发起。

```
主 session（coordinator / 你）
├── pack-executor      ──返回──→ 主 session ──SendMessage──→ pack-executor（修复 review 问题）
├── workflow-auditor   ──返回──→ 主 session
└── root-cause-analyst ──返回──→ 主 session
```

**上下文连续规则**：
- 同一 pack 内 review → 修复：**SendMessage** 继续原 pack-executor（它有代码上下文）
- 跨 pack 或新问题：**Agent tool** 新建（上下文干净）
- root-cause-analyst 始终新建（调查未知根因需要全新视角）

## 循环控制

每个 review 循环有硬性上限，防止无限来回：

| 循环 | 上限 | 超限处理 |
|------|------|---------|
| Phase 0：文档 review → 主 session 修复 | 2 轮 | 用业务语言告知用户哪个设计点无法确认 |
| Phase A：pack review → pack-executor 修复 | 3 轮/pack | 用业务语言告知用户哪个功能点搞不定 |
| Phase B：intent gap → pack-executor 修复 | 2 轮/gap | 用业务语言告知用户哪个承诺做不到 |
| Phase B 总调度 | 15 次 | 汇报进度和剩余问题 |

## Phase 0：文档审查

1. 定位 `docs/superpowers/plans/` 中的活跃计划。读取全文。
2. 检查 `docs/superpowers/specs/` 中是否有匹配设计文档。有则读取。
3. 调度 workflow-auditor 审查文档（读取 [doc-review-prompt.md](doc-review-prompt.md) 填入路径）。
4. 处理结果：
   - 通过 → 进入 Setup。
   - Critical → **你直接修复**（你拥有 brainstorming 结论和用户偏好的完整上下文）→ 重新调度 workflow-auditor。**最多 2 轮**。
   - 涉及业务决策的问题 → 用业务语言询问用户 → 你按用户意见修正。
   - Important → 你直接修复后继续。

## Setup

1. 提取所有未勾选 task 的完整文本。
2. 归组 Task Pack：
   - 按 plan 的 section headers 分组
   - 触碰相同文件的 task 归入同一 pack
   - 有依赖关系的 task 归入同一 pack
   - 每 pack 2-5 task，独立 task 可单独成 pack
   - 标记独立 pack——可并行调度
3. 向用户确认一次："计划有 N 个 task / M 个 pack。开始执行。只在需要你做业务决策时才会暂停。"

## Phase A：Task Pack 执行循环

对每个 pack（独立 pack 可并行）：

### 步骤 1：调度 pack-executor

用 Agent tool 调度（auto-delegation 匹配 pack-executor）。Prompt 包含 pack 中所有 task 完整文本 + 上下文。保存返回的 agentId。

处理状态：
- **DONE** → 步骤 2。
- **DONE_WITH_CONCERNS** → 正确性问题先处理；观察性意见记下继续。
- **NEEDS_CONTEXT** → SendMessage 继续，提供上下文。
- **BLOCKED** → 技术阻塞自主解决（拆 pack / 调度 root-cause-analyst）。业务阻塞询问用户。

### 步骤 2：Pack review

用 Agent tool 调度 workflow-auditor（读取 [pack-review-prompt.md](pack-review-prompt.md) 填入内容）。

处理结果：
- 通过 → pack 完成，下一个 pack。
- `needs pack-executor` → SendMessage 给原 pack-executor（agentId），发 findings。修复后重新调度 workflow-auditor。
- `needs root-cause-analyst` → Agent tool 新建 root-cause-analyst。修复后重新调度 workflow-auditor。
- `needs user decision` → 用业务语言询问用户。

**最多 3 轮/pack**。

### 并行调度

2+ 独立 pack → 同一消息多个 Agent tool call。全部返回后：
1. 冲突验证：跑完整测试。失败则调度 pack-executor 修复。
2. 逐个跑 review。

### 进度

每 2-3 个 pack 完成后一行 FYI。

## Phase B：Final review

所有 pack 完成后：

### 有 design doc → 意图验证

1. 调度 workflow-auditor（读取 [final-intent-review-prompt.md](final-intent-review-prompt.md) 填入内容）。
2. Implementation gap → 调度 pack-executor 写失败 test → 修复 → workflow-auditor 确认。**最多 2 轮/gap**。
3. Design gap（设计文档本身有缺陷）→ 用业务语言告知用户"设计需修正"，标注具体缺陷。
4. Code-level Critical → 调度对应 agent 修复。
5. 所有 gap 闭合后再调度一次 intent review 确认。
6. **Phase B 总调度上限 15 次**。

### 无 design doc → 代码级全量 review

调度 workflow-auditor review `git diff <starting_commit>..HEAD`。Critical 调度对应 agent 修复。

## Phase C：报告

用业务语言向用户汇报功能完成情况、修复过的问题、遗留问题。

停止。不自动 merge——收尾走 `superpowers:finishing-a-development-branch`。

## 禁止

- 跳过 Phase 0 或 Phase B
- 用技术语言向用户汇报
- 自己写生产代码（调度 pack-executor）
- 每 task 一个 subagent（用 Task Pack）
- 超过循环上限不处理

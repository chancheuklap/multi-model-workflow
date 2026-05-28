# 大 Issue 拆分方法论

> **流程位置**：`orchestrate-discovery` Step 12 · Design Review 通过后 · 完成后返回 SKILL.md（verdict）

Coordinator 在 Design Review 通过后执行本方法论，将设计文档拆分为大 issue（vertical slice 级）。**小 issue 拆分不在此阶段进行**——由 plan-writer 在 plan-writing 阶段完成。

## Step 12a：读取设计文档

确认设计文档内容在上下文中（compact 后可能丢失）。提取：

- Goal / 目标结果
- 用户场景
- 方案设计（业务对象、角色、状态、实现决策）
- 合同边界
- 发布风险

## Step 12b：探索代码库（按需）

如果对代码现状不够了解，用 `rg` / `find` / `Skill({ skill: "improve-codebase-architecture" })` 确认模块边界、已有模式、合同面。

## Step 12c：拆分 vertical slice

将设计文档拆分为 **tracer bullet** 大 issue。每个大 issue 是一个 thin vertical slice——切穿所有集成层（schema → API → UI → tests），端到端可独立验证。

<vertical-slice-rules>
- 每个 slice 交付一条窄而完整的端到端路径
- 完成后可独立演示或验证
- 优先拆出多个 thin slice，而非少数 thick slice
- 每个 slice 标记为 AFK（可无人值守实现）或 HITL（需要人工决策）
- AFK 优先于 HITL
</vertical-slice-rules>

## Step 12d：与用户确认

向用户展示拆分方案，以编号列表呈现。每个 slice 展示：

- **Title**：简短描述性名称
- **Type**：AFK / HITL
- **Blocked by**：依赖哪些其他 slice（如有）
- **覆盖的用户场景**：本 slice 覆盖设计文档中的哪些场景

询问用户：

- 粒度是否合适？（太粗 / 太细）
- 依赖关系是否正确？
- 是否有 slice 需要合并或继续拆分？
- AFK / HITL 标记是否正确？

迭代直到用户确认。

## Step 12e：写入大 issue 文件

写入 `docs/orchestrate/issues/<slug>/`（slug 从 Scope Contract 读取）。

每个大 issue 写一个文件，按依赖顺序编号（blocker 在前）：

```
docs/orchestrate/issues/<slug>/
├── 001-<large-issue-slug>.md
├── 002-<large-issue-slug>.md
└── ...
```

大 issue 文档格式：

```markdown
# <Large Issue Title>

## What to build
<描述这个 vertical slice 的端到端行为>

## Design context refs

指向 design 文档相关章节的锚点（plan-writer 跟随，无需 Coordinator 临场提取"与本 issue 相关的设计要点"）。至少一条。

- `docs/orchestrate/design/<slug>.md#<anchor-1>` — <相关性说明>
- `docs/orchestrate/design/<slug>.md#<anchor-2>` — <相关性说明>

## Small issues
<!-- PENDING: plan-writer 将在 plan-writing 阶段补全小 issue 拆分 -->

## Blocked by
- <其他大 issue 编号或 "None">
```

**`## Small issues` 章节留空**——标记 `<!-- PENDING -->`，由 plan-writer 在 plan-writing 阶段填充。

**`## Design context refs` 必填至少一条**——Discovery 自检：每个大 issue 至少有一条 design 锚点链接。

---
> **下一步**：大 issue 文件写完 → 返回 SKILL.md（verdict: `DISCOVERY_READY`，issue hierarchy status: `large_issues_ready`）。

# Plan-writer 派发协议

> **流程位置**：`orchestrate-plan-writing` Steps 9-10 · 派发后 → Steps 11-12a（`plan-gates.md`）

## Step 9：构造 Dispatch Brief

Dispatch prompt 必须自足——plan_writer 不读 SKILL.md、不读 Coordinator 的上下文。**Coordinator 必须把 plan_writer 需要的所有信息写进 prompt**。

### Step 9a：Pre-dispatch Context Transfer（强制）

构造 dispatch prompt 之前，Coordinator 必须用 Read 读取以下文件，确认内容在上下文中：

1. **Read** Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）→ 获取 slug、run_id
2. **Read** 设计文档（`docs/orchestrate/design/<slug>.md`）→ 提取 Goal、Architecture、行为清单、合同边界、验收标准
3. **Read** issue hierarchy 文档（`docs/orchestrate/issues/<slug>.md`）→ 提取所有大 issue 的列表、small issue、acceptance criteria、blocked-by 关系

如果以上任何一个 Read 失败（文件不存在），停止派发，返回对应的 upstream verdict。

### Step 9b：填充 Dispatch Prompt

将 Step 9a 读到的内容填入以下模板。**所有 `<>` 占位符都必须替换为实际值**——不得让占位符原样出现在 prompt 中。

```
spawn_agent({
  agent_type: "plan_writer",
  description: "Write implementation plan: <feature title>",
  prompt: "
    ## Goal
    从 source design + issue hierarchy 写出 implementation plan。

    ## Feature slug
    <填入从 Scope Contract 读取的 slug>

    ## Source artifacts（plan_writer 启动后需 Read 这些文件获取完整内容）
    - Source design: docs/orchestrate/design/<slug>.md（已通过 Design Review）
    - Issue hierarchy: docs/orchestrate/issues/<slug>.md（合并文档，H2 = 大 issue，H4 = 小 issue）
    - Mockups（如有）: docs/orchestrate/mockups/<slug>/
    - Scope Contract: .codex/multi-model-workflow/scope-<run_id>.md
    - AGENTS.md / CLAUDE.md: <project root>/AGENTS.md / CLAUDE.md

    ## 设计摘要（Coordinator 从设计文档提取，帮 plan_writer 快速定向）
    **Goal:** <从设计文档 Goal 节提取>
    **Architecture:** <从设计文档 Architecture 节提取关键架构决策>
    **核心行为:** <列出设计文档定义的主要行为/功能点>
    **合同边界:** <列出设计文档中的 contract/interface 边界>
    **验收标准:** <列出设计文档的顶层验收标准>

    ## Issue 概览（Coordinator 从 issue hierarchy 提取）
    <列出所有 large issue 的编号、标题和 small issue 数量>
    <列出 issue 之间的 blocked-by 依赖关系>

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/<slug>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    - Design Review 中 reviewer 的重点建议: <从 Design Review 结果提取，无则写「无」>
    - 用户偏好 / 架构决策: <从讨论中提取，无则写「无」>
    - 已知 gotcha / 路径变更: <从讨论中提取，无则写「无」>

    ## Out of scope
    - <从设计文档的 Out of scope 节提取>
    - 不自创 issue——只消费 to-issues 产出的 issue hierarchy

    ## Return contract
    ### Verdict
    PLAN_CREATED / NEEDS_DISCOVERY / NEEDS_ISSUES / NEEDS_TRIAGE /
    NEEDS_DIAGNOSIS / NEEDS_DECISION / NEEDS_ARCHITECTURE / NEEDS_CONTEXT / BLOCKED
    ### Plan path
    ### Issue mapping
    ### Quality gate
    ### Open items
  "
})
```

**记录返回的 agentId**——后续修复可能需要 send_input / SendMessage 继续该 plan_writer（保有 design + issue 上下文）。

## Step 10：处理 Plan-writer 返回

| Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `PLAN_CREATED` | plan 写完，自检通过 | 进入 Step 11（Plan Entry Gate） |
| `NEEDS_DISCOVERY` | 业务意图/术语不清 | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 缺 issue / issue 粒度不足 / scope 过大 | 调用 to-issues |
| `NEEDS_TRIAGE` | issue ready state 不清 | 调用 triage |
| `NEEDS_DIAGNOSIS` | bug 缺复现或 hypothesis | 调用 diagnose |
| `NEEDS_DECISION` | 需要产品/业务决策 | 询问用户（一次只问一个问题） |
| `NEEDS_ARCHITECTURE` | 架构假设与代码现实不符 | 调用 improve-codebase-architecture |
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 code_explorer / 调用 zoom-out，补充后 send_input 给原 plan_writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan_writer 的阻塞原因 |

upstream skill 结论必须写回 design document / issue hierarchy，再 send_input 给原 plan_writer 继续。

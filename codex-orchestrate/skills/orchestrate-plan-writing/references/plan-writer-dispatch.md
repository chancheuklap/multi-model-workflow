# Plan-writer 派发协议

> **流程位置**：`orchestrate-plan-writing` Steps 9-10 · 派发后 → Steps 11-12a（`plan-gates.md`）

## Step 9：构造 Dispatch Brief

Dispatch prompt 必须自足——plan-writer 不读 SKILL.md、不读 Coordinator 的上下文。**Coordinator 必须把 plan-writer 需要的所有信息写进 prompt**。

### Step 9a：Pre-dispatch Context Transfer（强制，每个 issue 执行一次）

派发当前 issue 的 plan-writer 之前，Coordinator 必须用 Read tool 确认以下内容在上下文中：

1. **Read** Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）→ 获取 slug、run_id（首个 issue 时读取，后续复用）
2. **Read** 设计文档（`docs/orchestrate/design/<slug>.md`）→ 提取设计摘要（首个 issue 时读取，后续复用）
3. **Read** 当前这个 issue 文件（`docs/orchestrate/issues/<slug>/00N-<issue-slug>.md`）→ 提取 What to build、Small issues、Blocked by

如果以上任何一个 Read 失败（文件不存在），停止派发，返回对应的 upstream verdict。

### Step 9b：填充 Dispatch Prompt

将 Step 9a 读到的内容填入以下模板。**所有 `<>` 占位符都必须替换为实际值**。每个 issue 用同一模板、不同的 issue 文件路径和内容。

```
Agent({
  subagent_type: "plan-writer",
  description: "Write plan for issue 00N: <issue title>",
  run_in_background: true,
  prompt: "
    <DISPATCH_ENVELOPE>
    <!-- DISPATCH_ENVELOPE
    {
      \"protocol_version\": \"1\",
      \"run_id\": \"<run_id>\",
      \"phase\": \"plan-writing\",
      \"agent_role\": \"plan-writer\",
      \"agent_id\": null,
      \"pack_id\": null,
      \"repair_round\": 0,
      \"idempotency_key\": \"<run_id>/plan-writer/<issue_id>/r0\",
      \"disposition_refs\": null,
      \"review_intent\": null,
      \"exception_code\": null
    }
    -->

    ## Goal
    为一个大 issue 写出 implementation plan。你只负责这一个 issue，不负责其他 issue。

    ## Methodology
    启动后立即 Read 以下文件，按其中 Steps 3-8 执行：
    ${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-plan-writing/references/plan-writing-methodology.md

    ## Feature slug
    <填入从 Scope Contract 读取的 slug>

    ## Source artifacts
    - Source design: docs/orchestrate/design/<slug>.md（已通过 Design Review，全局上下文）
    - **你的 issue:** docs/orchestrate/issues/<slug>/00N-<issue-slug>.md
    - Mockups（如有）: docs/orchestrate/mockups/<slug>/
    - CLAUDE.md: <project root>/CLAUDE.md

    ## 设计摘要（Coordinator 从设计文档提取）
    **Goal:** <从设计文档 Goal 节提取>
    **Architecture:** <从设计文档 Architecture 节提取关键架构决策>
    **与本 issue 相关的行为:** <只列出与当前 issue 相关的设计要点>

    ## Issue 内容（Coordinator 从 issue 文件提取）
    **Issue title:** <大 issue 标题>
    **What to build:** <从 issue 文件的 What to build 节提取>
    **Small issues 状态:** <已有完整小 issue 列表 / PENDING（需 plan-writer 在 Step 3c 拆分）>
    **Blocked by:** <从 issue 文件的 Blocked by 节提取>

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/<slug>/00N-<issue-slug>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    - Design Review 中 reviewer 的重点建议: <无则写「无」>
    - 已知 gotcha / 路径变更: <无则写「无」>

    ## Out of scope
    - 其他 issue 的内容（不属于你的 scope）
    - 不创建新的大 issue——大 issue 由 Coordinator 在 Discovery 阶段产出。你负责在已有大 issue 内拆分小 issue（Step 3c）并映射为 Task Pack

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

**注意**：`${CLAUDE_PLUGIN_ROOT}` 在 Coordinator 主线程中会被 Claude Code 运行时解析为 plugin 安装目录的绝对路径，Sub-agent 收到的 prompt 中已经是解析后的路径。

**After each Agent call returns**（强制执行）：
1. Extract `agentId` from return value
2. `state.sh update --run-id <run_id> --field '.plan_writer_agent_id' --value '"<agentId>"'`
3. 若后续需要修复/补充上下文，必须使用 SendMessage({to: "<agentId>"}) resume 原 plan-writer

**Critical**: `run_in_background: true` ensures Coordinator gets agentId. Without agentId, plan-writer repair path is BLOCKED.

## Step 10：处理 Plan-writer 返回

| Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `PLAN_CREATED` | plan 写完，自检通过 | 进入 Step 11（Plan Entry Gate） |
| `NEEDS_DISCOVERY` | 业务意图/术语不清 | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 缺大 issue 文件 / scope 过大 | 返回 Coordinator → 重新进入 orchestrate-discovery Step 12（大 issue 拆分） |
| `NEEDS_TRIAGE` | issue ready state 不清 | `Skill({ skill: "triage" })` |
| `NEEDS_DIAGNOSIS` | bug 缺复现或 hypothesis | `Skill({ skill: "diagnose" })` |
| `NEEDS_DECISION` | 需要产品/业务决策 | 询问用户（一次只问一个问题） |
| `NEEDS_ARCHITECTURE` | 架构假设与代码现实不符 | `Skill({ skill: "improve-codebase-architecture" })` |
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 code-explorer / `Skill({ skill: "zoom-out" })`，补充后 SendMessage 给原 plan-writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan-writer 的阻塞原因 |

upstream skill 结论必须写回 design document / issue hierarchy，再 SendMessage 给原 plan-writer 继续。

---
> **下一步**：plan-writer 返回后 → Steps 11-12a（`plan-gates.md`）。

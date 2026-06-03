# Plan-writer 派发协议

> **流程位置**：`orchestrate-plan-writing` Steps 9-10 · 派发后 → Steps 11-12a（`plan-gates.md`）

## Step 9：构造 Dispatch Brief

你（plan-writer）按 Self-Read Protocol 自读所有上下文，Coordinator 只需在 envelope 中写明 `plan_id` 和 source artifact 路径。

### Step 9a：Pre-dispatch Readiness Check（强制，每个 issue 执行一次）

派发当前 issue 的 plan-writer 之前，Coordinator 确认以下路径存在（存在则 plan-writer 自读）：

1. Scope Contract 路径：`.claude/multi-model-workflow/scope-<run_id>.md`（从中获取 slug、run_id）
2. 设计文档路径：`docs/orchestrate/design/<slug>.md`
3. 当前 issue 文件路径：`docs/orchestrate/issues/<slug>/00N-<issue-slug>.md`

如果以上任何路径不存在，停止派发，返回对应的 upstream verdict。

### Step 9b：填充 Dispatch Prompt

将路径填入以下模板的 `Source artifacts:` 字段。每个 issue 用同一模板、不同的 issue 文件路径。

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

    ## Source artifacts（设计文档和 Mockup 地位平等）
    - Source design: docs/orchestrate/design/<slug>.md（已通过 Design Review，全局上下文）
    - **你的 issue:** docs/orchestrate/issues/<slug>/00N-<issue-slug>.md
    - **Mockups:** docs/orchestrate/mockups/<slug>/（如目录存在，是与设计文档平级的源头工件，不是可选参考。你必须 Read mockup 文件和设计文档中的 `## UI / UX 状态` 视觉规格表，把视觉规格原子级拆解写入每个 UI pack 的 acceptance criteria。不能只写"见 mockup 目录"。）
    - CLAUDE.md: <project root>/CLAUDE.md

    ## 设计摘要
    你自读 `docs/orchestrate/design/<slug>.md` 获取 Goal、Architecture、与本 issue 相关的行为。

    ## Issue 内容
    你自读 `docs/orchestrate/issues/<slug>/00N-<issue-slug>.md` 获取 Issue title、What to build、Small issues 状态、Blocked by。

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/<slug>/00N-<issue-slug>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    你自读 Scope Contract（`.claude/multi-model-workflow/scope-<run_id>.md`）获取 Design Review 的重点建议和已知 gotcha。若 Scope Contract 无相关字段，跳过此节。

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
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 `code-explorer`（窄事实）/ `Skill({ skill: "improve-codebase-architecture" })`（模块边界），补充后 SendMessage 给原 plan-writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan-writer 的阻塞原因 |

upstream skill 结论必须写回 design document / issue hierarchy，再 SendMessage 给原 plan-writer 继续。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 plan-writer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`、`phase: "plan-writing"`、`agent_role: "plan-writer"`。
2. 在 `Source artifacts:` 中列出 design.md、issue 文件、mockup 目录路径（plan-writer 自读内容）。
3. 触发 `state.sh` 记录 plan-writer 派发状态，保存 `agentId` 以备 SendMessage 修复路径。
4. 等待 plan-writer 返回 Verdict，按 Step 10 路由表处置。

---
> **下一步**：plan-writer 返回后 → Steps 11-12a（`plan-gates.md`）。

# Plan-writer 派发协议

> **流程位置**：`orchestrate-plan-writing` Steps 9-10 · 派发后 → Steps 11-12a（`plan-gates.md`）

## Step 9：构造 Dispatch Brief

Dispatch prompt 必须自足——Coordinator 在 prompt 中写清所有输入 artifact 路径和上下文，包括方法论文件的绝对路径。

```
Agent({
  subagent_type: "plan-writer",
  description: "Write implementation plan: <feature>",
  prompt: "
    ## Goal
    从 source design + issue hierarchy 写出 implementation plan。

    ## Methodology
    启动后立即 Read 以下文件，按其中 Steps 3-8 执行：
    ${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-plan-writing/references/plan-writing-methodology.md

    ## Source artifacts
    - Source design: <path>（已通过 Design Review）
    - Issue hierarchy:
      - Large issues: <path(s) + titles>
      - Small issues: <listed in large issue docs, or separate paths>
    - Scope Contract: <path>
    - CLAUDE.md: <project root>/CLAUDE.md

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/YYYY-MM-DD-<feature>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    - Design Review 中 reviewer 的重点建议: <paste if any>
    - 用户偏好 / 架构决策: <paste if any>
    - 已知 gotcha / 路径变更: <paste if any>

    ## Out of scope
    - <explicitly list what NOT to include>
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

**注意**：`${CLAUDE_PLUGIN_ROOT}` 在 Coordinator 主线程中会被 Claude Code 运行时解析为 plugin 安装目录的绝对路径，Sub-agent 收到的 prompt 中已经是解析后的路径。

**记录返回的 agentId**——后续修复可能需要 SendMessage 继续该 plan-writer（保有 design + issue 上下文）。

## Step 10：处理 Plan-writer 返回

| Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `PLAN_CREATED` | plan 写完，自检通过 | 进入 Step 11（Plan Entry Gate） |
| `NEEDS_DISCOVERY` | 业务意图/术语不清 | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 缺 issue / issue 粒度不足 / scope 过大 | `Skill({ skill: "to-issues" })`（用户级，无前缀） |
| `NEEDS_TRIAGE` | issue ready state 不清 | `Skill({ skill: "triage" })`（用户级，无前缀） |
| `NEEDS_DIAGNOSIS` | bug 缺复现或 hypothesis | `Skill({ skill: "diagnose" })`（用户级，无前缀） |
| `NEEDS_DECISION` | 需要产品/业务决策 | 询问用户（一次只问一个问题） |
| `NEEDS_ARCHITECTURE` | 架构假设与代码现实不符 | `Skill({ skill: "improve-codebase-architecture" })`（用户级，无前缀） |
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 code-explorer / `Skill({ skill: "zoom-out" })`（用户级，无前缀），补充后 SendMessage 给原 plan-writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan-writer 的阻塞原因 |

upstream skill 结论必须写回 design document / issue hierarchy，再 SendMessage 给原 plan-writer 继续。

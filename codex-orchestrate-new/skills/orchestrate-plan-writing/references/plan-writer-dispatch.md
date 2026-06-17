# Plan-writer 派发协议

> **流程位置**：`orchestrate-plan-writing` Steps 9-10 · 派发后 → Steps 11-12a（`plan-gates.md`）

## Step 9：构造并行 Dispatch Brief

你（plan_writer）按 Self-Read Protocol 自读所有上下文，Coordinator 只需在 envelope 中写明 `plan_id` 和 source artifact 路径。

### Step 9a：Pre-dispatch Readiness Check（强制，整批执行）

派发任何 plan_writer 之前，Coordinator 先枚举本轮所有大 issue，并确认每个 issue 的以下路径存在（存在则 plan_writer 自读）：

1. Scope Contract 路径：`.codex/multi-model-workflow/scope-<run_id>.md`（从中获取 slug、run_id）
2. 设计文档路径：`docs/orchestrate/design/<slug>.md`
3. 当前 issue 文件路径：`docs/orchestrate/issues/<slug>/00N-<issue-slug>.md`

如果任一 issue 缺少以上路径，停止整批派发，返回对应的 upstream verdict；不得先派出部分 writer 再补缺件。

整批派发前对 issue hierarchy 做一次轻量语义检查，检查结果直接写回 issue 文件，不新增派发索引或中间文档：

- `Blocked by` 必须是直接依赖，不接受“只依赖中间 issue、实际还消费更早 producer”的传递依赖捷径。
- 条件项 / HITL issue 必须同时列出决策门和直接 producer；缺任一项时先修 issue hierarchy，再派 writer。
- 度量 issue 的 output 必须是 evidence + Coordinator / user disposition，不得提前写成未 review 的自动阈值。

以上检查失败属于 `NEEDS_ISSUES`，不得先派 plan_writer 后让 Plan Review 再发现。

### Step 9b：为每个 issue 填充 Dispatch Prompt

将路径填入以下模板。每个 issue 用同一模板、不同的 `plan_id`、issue 文件路径和 plan 输出路径。

```
spawn_agent({
  agent_type: "plan_writer",
  message: "
    <DISPATCH_ENVELOPE>
    <!-- DISPATCH_ENVELOPE
    {
      \"protocol_version\": \"1\",
      \"run_id\": \"<run_id>\",
      \"phase\": \"plan-writing\",
      \"agent_role\": \"plan_writer\",
      \"agent_id\": null,
      \"pack_id\": null,
      \"repair_round\": 0,
      \"idempotency_key\": \"<run_id>/<plan_id>/r0\",
      \"disposition_refs\": null,
      \"review_intent\": null,
      \"exception_code\": null
    }
    -->

    ## Goal
    为一个大 issue 写出 implementation plan。你只负责这一个 issue，不负责其他 issue。

    ## Methodology
    启动后立即 Read 以下文件，按其中 Steps 3-8 执行：
    ${MMW_PLUGIN_ROOT}/skills/orchestrate-plan-writing/references/plan-writing-methodology.md

    ## Feature slug
    <填入从 Scope Contract 读取的 slug>

    ## Source artifacts（设计文档和 Mockup 地位平等）
    - Source design: docs/orchestrate/design/<slug>.md（已通过 Design Review，全局上下文）
    - **你的 issue:** docs/orchestrate/issues/<slug>/00N-<issue-slug>.md
    - **Mockups:** docs/orchestrate/mockups/<slug>/（如目录存在，是与设计文档平级的源头工件，不是可选参考。你必须 Read mockup 文件和设计文档中的 `## UI / UX 状态` 视觉规格表，把视觉规格原子级拆解写入每个 UI pack 的 acceptance criteria。不能只写"见 mockup 目录"。）
    - AGENTS.md: <project root>/AGENTS.md

    ## 设计摘要
    你自读 `docs/orchestrate/design/<slug>.md` 获取 Goal、Architecture、与本 issue 相关的行为。

    ## Issue 内容
    你自读 `docs/orchestrate/issues/<slug>/00N-<issue-slug>.md` 获取 Issue title、What to build、Small issues 状态、Blocked by。

    ## Large issue index（只读依赖索引）
    Coordinator 已从本轮所有大 issue 提取以下索引。你只用它理解 plan 编号、直接依赖、条件项和 HITL 决策边界；不得读取或修改其他 issue 全文。
    | plan_id | title | type | blocked_by | decision_output | dependency_rationale |
    | ... |

    ## Plan output
    - Plan 保存路径: docs/orchestrate/plans/<slug>/00N-<issue-slug>.md
    - Execution owner: Orchestrate Workflow（必须写入 plan header）

    ## 补充上下文
    你自读 Scope Contract（`.codex/multi-model-workflow/scope-<run_id>.md`）获取 Design Review 的重点建议和已知 gotcha。若 Scope Contract 无相关字段，跳过此节。

    ## Out of scope
    - 其他 issue 的内容（不属于你的 scope）
    - 其他 issue 对应的 plan 文件（不属于你的可写范围）
    - 设计文档、Mockup、Scope Contract 只读；不得把它们改成 plan-writing 的交付物
    - 不创建新的大 issue——大 issue 由 Coordinator 在 Discovery 阶段产出。你负责在已有大 issue 内拆分小 issue（Step 3c）并映射为 Task Pack

    ## Return contract
    ### Verdict
    PLAN_CREATED / NEEDS_DISCOVERY / NEEDS_ISSUES / NEEDS_TRIAGE /
    NEEDS_DIAGNOSIS / NEEDS_DECISION / NEEDS_ARCHITECTURE / NEEDS_CONTEXT / BLOCKED
    ### Plan path
    ### Issue mapping
    ### Dependency mapping
    - Source issue Blocked by -> Plan header Blocked by
    - Any missing direct producer dependency: NONE or NEEDS_ISSUES with evidence
    ### Gate Readiness
    - Plan path
    - Issue path
    - Pack count
    - Schema checklist: risk table / Plan Review History / Pack Execution Manifest / exact Pack checkbox / dependencies column
    ### Quality gate
    ### Open items
  "
})
```

**注意**：`${MMW_PLUGIN_ROOT}` 在 Coordinator 主线程中会被 Codex 运行时解析为 plugin 安装目录的绝对路径，Sub-agent 收到的 prompt 中已经是解析后的路径。

### Step 9c：并行 spawn + session 登记

Coordinator 必须先完成整批 `spawn_agent`，不得在第一个 writer 返回后才派第二个 writer。每个 `spawn_agent` 返回 `agentId` 后，立即登记到 workflow-state：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" plan-writer-session set \
  --run-id "<run_id>" \
  --plan-id "<NNN>" \
  --agent-id "<AGENT_ID>" \
  --status dispatched \
  --issue-path "docs/orchestrate/issues/<slug>/<NNN>-<issue-slug>.md" \
  --plan-path "docs/orchestrate/plans/<slug>/<NNN>-<issue-slug>.md"
```

如果任一 writer 登记失败，当前 phase 进入 `BLOCKED`；Coordinator 先等待、保存并关闭已经派出的 writer，再向用户报告阻塞原因。不得留下未登记的 writer 继续运行。

### Step 9d：统一 wait + save + durable close

整批 writer 都成功登记后，再统一等待：

```
wait_agent({targets:["<AGENT_ID_001>", "<AGENT_ID_002>", "..."], timeout_ms:600000})
```

每个 writer 返回 final message 后，Coordinator 依次执行：

1. 保存返回结果到 `.codex/multi-model-workflow/plan-writer-results/<run_id>/<NNN>.md`
2. `state.sh plan-writer-session set --run-id <run_id> --plan-id <NNN> --status returned --result-file ".codex/multi-model-workflow/plan-writer-results/<run_id>/<NNN>.md"`
3. 亲自抽验返回里声明的 plan path、issue mapping 和文件存在性
4. `close_agent({target:"<AGENT_ID>"})` 释放并发容量；closed writer 仍可用已记录 agent id `resume_agent`
5. 进入 Step 10

若后续需要修复/补充上下文，必须按 plan id 读取原 writer：

```bash
bash "${MMW_PLUGIN_ROOT}/scripts/state.sh" plan-writer-session get \
  --run-id "<run_id>" \
  --plan-id "<NNN>" \
  --field agent_id
```

拿到 `agent_id` 后，先 `resume_agent({ id: "<AGENT_ID>" })`，再 `send_input({ target: "<AGENT_ID>", message: "..." })` 续修原 plan_writer。

**Critical**: 缺少 `plan_writer_sessions[<NNN>].agent_id` 时，plan_writer repair path 是 BLOCKED，不能新建另一个 plan_writer 冒充续修。

## Step 10：处理 Plan-writer 返回

| Verdict | 含义 | Coordinator 动作 |
| --- | --- | --- |
| `PLAN_CREATED` | 对应 plan 写完，自检通过 | 标记该 plan ready；整批 plan 都 ready 后进入 Step 11（Plan Entry Gate） |
| `NEEDS_DISCOVERY` | 业务意图/术语不清 | 回到 orchestrate-discovery |
| `NEEDS_ISSUES` | 缺大 issue 文件 / scope 过大 | 返回 Coordinator → 重新进入 orchestrate-discovery Step 12（大 issue 拆分） |
| `NEEDS_TRIAGE` | issue ready state 不清 | `加载 skill `triage`` |
| `NEEDS_DIAGNOSIS` | bug 缺复现或 hypothesis | `加载 skill `diagnose`` |
| `NEEDS_DECISION` | 需要产品/业务决策 | 询问用户（一次只问一个问题） |
| `NEEDS_ARCHITECTURE` | 架构假设与代码现实不符 | `加载 skill `improve-codebase-architecture`` |
| `NEEDS_CONTEXT` | 缺代码上下文 | 派 `code_explorer`（窄事实）/ `加载 skill `improve-codebase-architecture``（模块边界），补充后 send_input 给原 plan_writer |
| `BLOCKED` | 无法完成 | 报告用户，附 plan_writer 的阻塞原因 |

任一 writer 返回 `NEEDS_*` 或 `BLOCKED` 时，Coordinator 必须先保存已返回的 writer final message、更新 `plan_writer_sessions[<NNN>]`、关闭已完成 writer，再按路由表处理；不得带着未落盘的结果进入 upstream skill 或 Plan Gate。

upstream skill 结论必须写回 design document / issue hierarchy，再 send_input 给原 plan_writer 继续。

## Coordinator 端最小职责

Coordinator 在派发时只需完成以下动作，其余由 plan_writer 自读：

1. 写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`、`phase: "plan-writing"`、`agent_role: "plan_writer"`。
2. 在 `Source artifacts:` 中列出 design.md、issue 文件、mockup 目录路径（plan_writer 自读内容）。
3. 并行派发整批 plan_writer；每个 writer 返回 `agentId` 后用 `state.sh plan-writer-session set` 按 plan id 记录。
4. 统一等待整批 writer 返回，保存 final message，更新 session status/result-file，并立即关闭已完成 writer。
5. 亲自抽验 writer 返回中的路径和存在性，按 Step 10 路由表处置。

---
> **下一步**：plan_writer 返回后 → Steps 11-12a（`plan-gates.md`）。

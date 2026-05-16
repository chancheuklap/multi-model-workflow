# Issue Workflow 路由

用于 PRD、issue、triage 或 backlog 入口。

## 步骤

1. 缺 source PRD / requirements 时，使用 `to-prd` 或 `grill-with-docs` 生成 source requirements。
2. 缺 vertical large issues 时，使用 `to-issues` 从 source requirements 拆出 tracer-bullet large issues。
3. large issue 下缺 vertical small issues 时，继续使用 `to-issues` 拆到 small issue 层级。
4. issue ready state、AFK / HITL、blocked-by 或 label 不清时，使用 `triage`。
5. large / small issue hierarchy 齐备后，使用 `orchestrate-plan-writing` 生成 issue-backed implementation plan。
6. plan 生成后进入 Phase 0b。

## 流程图

```mermaid
flowchart TD
    A["需要持久化 GitHub issue tracker workflow"] --> B["to-prd"]
    B --> C["创建 issue-backed PRD"]
    C --> D["to-issues"]
    D --> E["创建 vertical-slice issues"]
    E --> F["triage"]
    F --> G["ready-for-agent / needs-info / ready-for-human / wontfix"]
    G --> H{"是否 ready for AgentFlow execution?"}
    H -->|否| I["继续 triage 或请求 user decision"]
    I --> H
    H -->|是| J{"同时具备 vertical large issues 和 vertical small issues?"}
    J -->|否| K["to-issues 补齐缺失层级；必要时 triage ready state"]
    K --> J
    J -->|是| L["orchestrate-plan-writing 生成 issue-backed implementation plan"]
    L --> M["Phase 0b plan review"]
```

## Ready 条件

- 每个 large issue 都能成为 plan section。
- 每个 small issue 都能成为一个可验证 Task Pack。
- 每个 issue 有 source、acceptance、blocked-by / dependencies、AFK / HITL 判断。
- 不能把未确认的 suggested slice 直接当成 Task Pack。

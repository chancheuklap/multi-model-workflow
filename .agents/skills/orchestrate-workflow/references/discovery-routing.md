# Discovery 路由

用于全新功能、系统性改造，或用户要求边讨论边沉淀上下文的入口。系统性 bug 复盘先走 `diagnose`；如果诊断后需要重新定义对象、状态、边界或目标方案，再进入本文件。

## 步骤

1. 使用 `brainstorming` 探索产品意图、用户场景、目标行为和验收口径。
2. 使用 `grill-with-docs` 对齐领域语言、对象 owner、状态、边界、合同和现有文档。
3. 能从代码或文档确认的问题，先查证；只把剩余业务决策交给用户。
4. 稳定术语、对象关系、角色和状态写回 `CONTEXT.md` 或项目规则指定的上下文文档。
5. 功能承诺、UI 状态、接口合同、失败场景、rollout 边界和 acceptance 写入 SPEC / design draft。
6. state machine、interface shape 或 UI 方向需要比较时，先走 `prototype`，再把结论写回 design。
7. source requirements 成形后进入 Phase 0a。

## 流程图

### 新想法 / 系统性改造

```mermaid
flowchart TD
    A["用户提出新想法 / 系统性改造"] --> B["superpowers:brainstorming"]
    B --> C["grill-with-docs 澄清领域语言、对象关系和业务场景"]
    C --> D["更新 CONTEXT.md 和 SPEC / design draft"]
    D --> E["只有当状态机、接口形状或 UI 方向无法从文档判断时，使用 prototype"]
    E --> F["生成 design document / SPEC draft"]
    F --> G["Phase 0a design review"]
    G --> H{"Design 通过 review?"}
    H -->|否| I["修复 design doc，或请求产品 / 架构决策"]
    I --> G
    H -->|是| J{"vertical large issues 和 vertical small issues 已存在?"}
    J -->|否| K["to-issues：先按 design 拆大 issue，再按大 issue 拆小 issue"]
    K --> J
    J -->|是| L["orchestrate-plan-writing"]
    L --> M["基于已通过 review 的 design 和 vertical issues 生成 issue-backed implementation plan"]
    M --> N["Phase 0b plan review，同时提供 design doc、issues 和 plan doc"]
    N --> O{"Plan 通过 joint review?"}
    O -->|否| P["修复 plan；如果 plan 暴露 design gap，也同时修复 design；如果 issue gap，回 to-issues"]
    P --> N
    O -->|是| Q["Task Pack dispatch preparation"]
```

### 系统性 bug 复盘

```mermaid
flowchart TD
    A["系统性 bug 复盘"] --> B["diagnose 建立真实 feedback loop"]
    B --> C{"是否需要重新定义业务对象、状态、边界或目标方案?"}
    C -->|是| D["brainstorming + grill-with-docs"]
    D --> E["更新 CONTEXT.md；维护 SPEC / design draft"]
    E --> F["Phase 0a design review"]
    C -->|否| G["维护型 bug 入口"]
```

## 交付物

- updated context / domain notes
- SPEC / design draft
- open decisions
- acceptance criteria
- source requirements

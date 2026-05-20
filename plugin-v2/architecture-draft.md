# Plugin V2 架构文档（基于 2026-05-20 审计）

> **审计基准**：`plugin-v2/` 目录下的实际代码（skills/ agents/ hooks/）。
> **审计日期**：2026-05-20。

## 图例

```
🟦 蓝色 = 内部 Skill（按需加载到主线程）
🟩 绿色 = Sub-Agent（独立子进程，不消耗主线程上下文）
🟧 橙色 = 外部 Review（跨模型独立审查）
🟪 紫色 = 外部 Skill（orchestrate 之外的独立技能）
⬜ 灰色 = Coordinator 自身逻辑（路线判定、修复分流、git 操作等）
🟥 红色 = 断点 / 矛盾
⬜ 虚线 = 路径存在但机制缺失
```

---

## 图 1：全局流程（三条路线）

```mermaid
flowchart TD
    classDef skill fill:#dbeafe,stroke:#2563eb
    classDef agent fill:#dcfce7,stroke:#16a34a
    classDef review fill:#fef3c7,stroke:#d97706
    classDef extSkill fill:#f3e8ff,stroke:#9333ea
    classDef coord fill:#f3f4f6,stroke:#6b7280
    classDef broken fill:#fee2e2,stroke:#dc2626,stroke-dasharray: 5 5
    classDef review fill:#fef3c7,stroke:#d97706

    A["输入"] --> B{"Step 1：路线判定"}:::coord

    %% 路线 1：Formal Orchestrate
    B -->|"新设计 / 优化 / 反馈"| INFRA["Steps 2-6：Resume + Infrastructure\n（Scope Contract + Git Checkpoint + Budget File）"]:::coord
    INFRA --> C["orchestrate-discovery\n（与用户 Q&A 迭代 + 设计文档）"]:::skill

    %% 路线 2：Bug
    B -->|"Bug / error / regression"| INFRA2["Steps 4-5：Scope + Git\n（跳过 Budget File）"]:::coord
    INFRA2 --> BUG["root-cause-analyst\n（调查 + 修复）"]:::agent
    BUG -->|"简单 bug: fixed"| BRV["Review\nCodex review"]:::review
    BRV --> DONE["Closing\n（汇报 + 提交 + 推送 + PR）"]:::coord
    BUG -->|"复杂: worker 修复"| BWORK["pack-executor /\ncomplex-pack-executor"]:::agent
    BWORK --> BRV
    BUG -->|"深层系统性问题"| INFRA

    %% 路线 3：多 PR 合并
    B -->|"多 PR 合并审查"| INFRA3["Steps 4-5：Scope + Git\n（跳过 Budget File）"]:::coord
    INFRA3 --> MPR["orchestrate-multi-pr-merge\n（见图 3）"]:::skill

    %% 文档阶段（线性，不回流）
    C --> DR["Design Review\nCodex review"]:::review
    DR --> E["to-issues\n（大 Issue → 小 Issue）"]:::extSkill

    %% per issue，同一 session 内完成
    E --> F["orchestrate-plan-writing\n（plan-writer Opus 4.7 1M）"]:::skill
    F --> PR["Plan Review\nCodex review"]:::review

    %% 执行阶段
    PR --> H["orchestrate-execution\n（见图 2）"]:::skill
    H -->|"finding → repair"| H
    H -->|"evidence needed"| P["code-explorer /\ncomplex-code-explorer /\nroot-cause-analyst"]:::agent
    P --> H
    H -->|"architecture friction"| Q["improve-codebase-\narchitecture"]:::extSkill
    Q -->|"只影响当前 pack"| H
    Q -->|"改变 plan anchors"| PR
    H -->|"all packs pass"| I["orchestrate-final-review\n（意图验证 + 清扫遗留尾巴）"]:::skill
    I -->|"implementation gap"| H
    I -->|"pass, release-risk"| J["Release Review\nCodex review"]:::review
    I -->|"pass, no risk"| K
    J -->|"release blocker"| N["complex-pack-executor /\n用户决策"]:::agent
    N -->|"resolved"| J
    J -->|"pass"| K
    K["Closing\n（汇报 + 提交 + 推送 + PR）"]:::coord

    %% Review 节点统一通过 dispatch 模板内联的 Codex review 步骤 的 codex-companion.mjs 机制派发
```

### 图 1 节点分析

| 节点 | 机制 | 做什么 | 产出/消费文档 | 状态 |
|------|------|--------|-------------|------|
| 路线判定 | Coordinator 自身逻辑 | 判断输入属于三条路线中的哪一条 | — | ✅ 正常 |
| Steps 2-6 Infrastructure | Coordinator 逻辑（`workflow-infrastructure.md`） | Cross-Conversation Resume + Scope Contract + Git Checkpoint + Budget File 创建 | **确定** feature slug（贯穿 `docs/orchestrate/` 全链） | ✅ 正常 |
| Discovery | Skill：`orchestrate-discovery` | 与用户 Q&A 迭代 + grill-with-docs 同步维护 CONTEXT.md + 产出设计文档 | **产出** `design/<slug>.md` + CONTEXT.md | ✅ 正常 |
| Design Review | Coordinator + **外部 Review** | 两个 baseline review（Design Content + Project Alignment），按 dispatch 模板内联的 Codex review 步骤派发 | **审查** `design/<slug>.md` | ✅ 正常 |
| to-issues | 外部 Skill | 设计文档拆分为大 Issue → 小 Issue | **消费** `design/<slug>.md` → **产出** `issues/<slug>/00N-*.md` | ✅ 正常 |
| Plan Writing | Skill：`orchestrate-plan-writing` | 前置确认 + 派 plan-writer agent + Budget 赋值（`2N+12`） | **消费** `issues/<slug>/00N-*.md` → **产出** `plans/<slug>/00N-*.md`（编号一一对应） | ✅ 正常 |
| Plan Review | Coordinator + **外部 Review** | Plan Entry Gate + Task Pack Inventory Gate → 派外部 review | **审查** `plans/<slug>/` 全部 plan 文件 | ✅ 正常 |
| Execution | Skill：`orchestrate-execution` | 图 2 的 pack 循环 | **消费** `plans/<slug>/` 提取 Task Pack → 构造 Pack Brief（自足，worker 不读 plan） | ✅ 正常（review 节点除外） |
| Final Review | Skill：`orchestrate-final-review` | 意图验证 + 清扫遗留尾巴 + Release Gate | **消费** `design/<slug>.md` 验证意图覆盖 | ✅ 正常（review 节点除外） |
| Release Review | Coordinator + **外部 Review** | 发布风险审查，仅触碰风险面时进入 | — | ✅ 正常 |
| Bug Investigation | Sub-Agent：root-cause-analyst | 调查 bug 根因，判定简单/深层 | — | ✅ 正常 |
| Bug Fix Review | **外部 Review** | 按 dispatch 模板内联的 Codex review 步骤派发 Codex review | — | ✅ 正常 |
| Closing | Coordinator 自身逻辑 | 汇报 + 提交 + 推送 + 开 PR | — | ✅ 正常 |

---

## 图 2：Execution 循环

```mermaid
flowchart TD
    classDef skill fill:#dbeafe,stroke:#2563eb
    classDef agent fill:#dcfce7,stroke:#16a34a
    classDef review fill:#fef3c7,stroke:#d97706
    classDef coord fill:#f3f4f6,stroke:#6b7280
    classDef broken fill:#fee2e2,stroke:#dc2626,stroke-dasharray: 5 5
    classDef review fill:#fef3c7,stroke:#d97706

    A["Plan Review pass"] --> B["读 plan Task Pack inventory"]:::coord
    B --> C["派 worker\n（pack-executor / complex-pack-executor）"]:::agent
    C --> D["worker 返回\n（SubagentStop hook 提醒 review）"]:::agent
    D --> E["Pack Review\nCodex review"]:::review
    E --> F{"通过?"}:::coord
    F -->|"needs repair"| V["Coordinator 验证 finding"]:::coord
    V --> T{"修复分流"}:::coord
    T -->|"简单（≤2 文件）"| S["Coordinator 直接修复"]:::coord
    T -->|"复杂（原 worker 可用）"| R["SendMessage 给原 worker\n⚠️ 需 AGENT_TEAMS env"]:::agent
    T -->|"根因不明"| RCA["新建 root-cause-analyst"]:::agent
    S --> RE["targeted re-review\nCodex review"]:::review
    R --> D2["worker 修复后返回"]:::agent
    D2 --> RE
    RCA --> D3["analyst 修复后返回"]:::agent
    D3 --> RE
    RE --> F

    F -->|"pass"| RG{"Early Release Gate\n触碰风险面?"}:::coord
    RG -->|"是"| RGR["Release Review\nCodex review"]:::review
    RG -->|"否"| J
    RGR --> J
    J{"还有 pack?"}:::coord
    J -->|"是"| C
    J -->|"否"| K["→ Final Review（图 1）"]:::skill

    RULE["Worker 规则：不存在非阻塞项\n要么当场修复，要么开 GitHub Issue"]
    style RULE fill:#fff3cd,stroke:#856404
```

### 图 2 节点分析

| 节点 | 机制 | 做什么 | 文档交互 | 状态 |
|------|------|--------|---------|------|
| 读 Task Pack inventory | Coordinator 逻辑 | 读取所有 plan 文档中的 Task Pack 列表 | **读** `plans/<slug>/` 全部文件 → 提取 pack 编号、依赖、风险、并行标记 | ✅ 正常 |
| 派 worker | Sub-Agent：`pack-executor`（普通）/ `complex-pack-executor`（高风险） | Agent tool 派发 coding worker，保存 agentId | **嵌入** Pack Brief（从 plan 提取，worker 不读 plan 文件） | ✅ 正常 |
| SubagentStop 提醒 | Hook：`SubagentStop` on `pack-executor\|complex-pack-executor` | 提醒 Coordinator 派发 review | — | ✅ 正常 |
| Pack Review | **外部 Review** | 按 dispatch 模板内联的 Codex review 步骤派发 | — | ✅ 正常 |
| Coordinator 验证 finding | Coordinator 逻辑 | 主线程评估 finding 是否成立 | — | ✅ 正常 |
| 修复分流 | Coordinator 逻辑 | 简单/复杂/根因不明三路分流 | — | ✅ 正常 |
| SendMessage 给原 worker | SendMessage（需 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`） | 复杂修复发回原 worker 保持上下文 | — | ⚠️ env 未设置时静默降级 |
| targeted re-review | **外部 Review** | 只审查修复变更 | — | ✅ 正常 |
| Early Release Gate | Coordinator + **外部 Review** | Pack 触碰风险面时触发 release review | — | ✅ 正常 |

---

## 图 3：Multi-PR Merge 流程

```mermaid
flowchart TD
    classDef skill fill:#dbeafe,stroke:#2563eb
    classDef agent fill:#dcfce7,stroke:#16a34a
    classDef review fill:#fef3c7,stroke:#d97706
    classDef coord fill:#f3f4f6,stroke:#6b7280
    classDef broken fill:#fee2e2,stroke:#dc2626,stroke-dasharray: 5 5
    classDef review fill:#fef3c7,stroke:#d97706

    A["多个并行 PR\n（来自同一大设计 / 大计划）"] --> B["Coordinator 阅读全部文档\n大设计 + 大计划 + 大 Issue + 各 PR 小文档"]:::coord
    B --> C["建立「合并后正确状态」的理解"]:::coord
    C --> D["并行派发 code-explorer\n验证 PR 间的代码 / 功能 / 意图关系"]:::agent
    D --> E{"Explorer findings"}:::coord
    E -->|"无冲突"| K["Integration Review\nCodex review"]:::review
    E -->|"有冲突"| F{"修复分流"}:::coord
    F -->|"简单"| G["Coordinator 直接修复"]:::coord
    F -->|"复杂、根因明确"| H["派发 coding worker"]:::agent
    F -->|"系统性 / 根因不明"| RCA["root-cause-analyst\n调查 PR 间冲突根因\n（最多 1 轮 analyst ↔ explorer）"]:::agent
    RCA --> RCAV["Coordinator 审阅\nanalyst findings"]:::coord
    RCAV -->|"根因明确"| H
    RCAV -->|"设计 / 意图冲突"| RCAROUTE["回到 Discovery\n或询问用户"]:::coord
    H --> J["worker 返回"]:::agent
    G --> V["Coordinator 验证修复"]:::coord
    J --> V
    V --> E
    K --> L{"通过?"}:::coord
    L -->|"needs repair"| M["修复 → re-review"]:::coord
    M --> L
    L -->|"pass"| N["按计划顺序合并所有 PR"]:::coord
    N --> O["Closing\n（汇报 + 推送）"]:::coord
```

### 图 3 节点分析

| 节点 | 机制 | 做什么 | 状态 |
|------|------|--------|------|
| Coordinator 阅读全部文档 | Coordinator 逻辑 | 读大设计 + 大计划 + 各 PR 小文档，建立全局理解 | ✅ 正常 |
| 并行派发 code-explorer | Sub-Agent：`code-explorer` / `complex-code-explorer` | 并行探索各 PR 代码，发现冲突 | ✅ 正常 |
| 修复分流 | Coordinator 逻辑 | 简单/复杂/系统性三路分流 | ✅ 正常 |
| root-cause-analyst 调查 | Sub-Agent：root-cause-analyst | 系统性冲突根因调查（capped at 1 轮 analyst ↔ explorer） | ✅ 正常 |
| Integration Review | **外部 Review** | 跨 PR 集成审查 | ✅ 正常 |
| 按计划顺序合并 PR | Coordinator 逻辑 | git 操作 | ✅ 正常 |

---

## 状态文件链

```
orchestrate-workflow Step 4
  └─ .claude/multi-model-workflow/scope-<run_id>.md        ← Scope Contract
orchestrate-workflow Step 6
  ├─ .claude/multi-model-workflow/budget-<run_id>.json      ← Budget File（Route 1 only）
  └─ .claude/multi-model-workflow/active-run-id             ← Active Run ID
orchestrate-plan-writing Step 12a
  └─ budget-<run_id>.json: budget_total = 2N + 12           ← Budget 赋值（不可变）
每次 review 完成
  └─ budget-<run_id>.json: budget_used += 1                 ← Budget 消耗
每个 phase verdict 后
  └─ budget-<run_id>.json: last_gate_phase + timestamp      ← Phase 标记
Review 派发时
  ├─ .claude/multi-model-workflow/review-prompts/<gate>.md  ← Review prompt
  └─ .claude/multi-model-workflow/review-results/<gate>.md  ← Review result
Closing 前（cleanup-before-push.sh）
  └─ 清除 active-run-id + scope + budget + review temp files
```

---

## 文档产物链：`docs/orchestrate/`

运行态状态文件（上节）跟踪 Coordinator 内部状态。**文档产物**跟踪功能本身的设计-拆分-计划-执行链路——它们是 phase 之间传递信息的载体，也是 review 的审查对象。

### 目录结构与命名

所有 orchestrate 产出文档统一存放在 `docs/orchestrate/`，按类型分子文件夹。同一功能用相同的 **feature slug**（`YYYY-MM-DD-<feature>`，kebab-case）贯穿四个子文件夹：

```
docs/orchestrate/
├── design/                                  # 设计文档（Discovery 产出）
│   └── <slug>.md
├── issues/                                  # Issue hierarchy（to-issues 产出）
│   └── <slug>/
│       ├── 001-<large-issue-slug>.md       # 大 issue（内含小 issue）
│       ├── 002-<large-issue-slug>.md
│       └── ...
├── plans/                                   # 实施计划（plan-writer 产出）
│   └── <slug>/
│       ├── 001-<issue-slug>.md             # 编号与 issues/ 下同编号文件一一对应
│       ├── 002-<issue-slug>.md
│       └── ...
└── mockups/                                 # 原型产出（prototype / frontend-design）
    └── <slug>/
        ├── *.html / *.png / *.svg
        └── README.md                        # mockup 索引
```

**关键约束**：
- feature slug 在 Infrastructure Setup 确定后全流程不变
- `issues/` 和 `plans/` 的文件**编号必须一一对应**（001 ↔ 001, 002 ↔ 002）——Plan Entry Gate 强制检查
- Plan 文件数量必须与 issue 文件数量一致——缺对应 plan 的 issue 返回 plan-writing 补写

### 图 4：文档产物流

```mermaid
flowchart LR
    classDef doc fill:#e0f2fe,stroke:#0284c7
    classDef gate fill:#fef3c7,stroke:#d97706
    classDef embed fill:#f0fdf4,stroke:#16a34a,stroke-dasharray: 3 3

    D["设计文档\n<slug>.md\n（背景 / 目标 / 方案 / 合同 / 风险 / 验收）"]:::doc
    DR["Design Review\n（完整性 + 项目对齐）"]:::gate
    I["大 Issue 文件\n001-*.md\n（What to build + 小 issue 列表）"]:::doc
    SI["小 Issue\n（内嵌在大 issue 中）\nType / What / Acceptance / Blocked by"]:::embed
    P["Plan 文件\n001-*.md\n（Header + File Map + 风险表 + Task Pack 列表）"]:::doc
    TP["Task Pack N.M\n（内嵌在 plan 中）\nGoal / Files / Criteria / Commands / Risk"]:::embed
    PG["Plan Entry Gate\n+ Task Pack Inventory Gate"]:::gate
    W["Worker dispatch\n（Pack Brief 自足，不读 plan 文件）"]:::doc

    D --> DR --> I
    I --- SI
    SI -->|"1 small issue = 1 Task Pack"| TP
    I -->|"1 大 issue = 1 plan 文件\n编号一一对应"| P
    P --- TP
    P --> PG --> W
```

### 四种文档产物

| 产物 | 模板来源 | 产出者 | 消费者 | 审查门禁 |
|------|---------|--------|--------|---------|
| **设计文档** | `discovery-design-document.md` | orchestrate-discovery | to-issues、plan-writer（只读） | Design Review（2 baseline） |
| **大 Issue 文件** | to-issues skill（上游） | to-issues | plan-writer（1 issue = 1 plan） | — |
| **Plan 文件** | `plan-writing-methodology.md` | plan-writer agent | orchestrate-execution | Plan Entry Gate + Task Pack Inventory Gate |
| **Mockup** | prototype / frontend-design | Discovery 阶段 | plan-writer（mockup anchors）、worker（视觉验证） | Design Review 覆盖 |

### 设计文档结构

```
# <功能> 设计文档
├── 背景和问题          — 用户视角问题、触发场景
├── 目标结果            — 完成后能稳定做到什么
├── 用户场景            — actor/action/benefit · happy path + 失败 + 空态 + 权限 + 并发 + 回滚
├── 方案设计
│   ├── 业务对象、角色和状态   — 对象 / owner / writer / reader / verifier / 状态 / 生命周期
│   └── 实现决策               — 讨论中做出的决策（不写 file path / code snippet）
├── 合同边界            — API / Pydantic / DB / JSON / sync / billing / permission / runtime
├── 发布风险和人工门禁
├── 测试和验收
├── UI/UX 状态          — mockup 目录 / viewport / states / interaction
├── 失败场景和异常处理
├── 不在本次范围
└── Open Decisions
```

**硬规则**：使用 CONTEXT.md 正式术语 · 无 TODO/TBD · 不混入 Task Pack 或 worker 指令 · 不写只在聊天中能理解的句子。

### Issue 文档结构

Issue 文档由上游 `to-issues` skill 产出（非 plugin-v2 自有），plugin-v2 只消费它。

```
# <大 Issue 标题>
├── What to build       — 端到端行为描述（vertical slice）
├── Small issues        — 编号子节，每个小 issue 包含：
│   ├── Type: AFK / HITL
│   ├── What to build
│   ├── Acceptance criteria（checkbox 列表）
│   └── Blocked by（其他小 issue 编号或 None）
└── Blocked by          — 其他大 issue 编号或 None（跨 plan 依赖）
```

**层级关系**：大 issue = 一个 vertical slice = 一个文件 · 小 issue = 内嵌子节（不是独立文件）· 小 issue 直接映射 Task Pack。

**编号规则**：文件名 `00N-<slug>.md`，N 按依赖顺序排列（blocker 在前）。to-issues 完成后还会发布 GitHub Issue 并将 issue number 写回本地文件。

### Plan 文档结构

```
# <Issue Title> Implementation Plan
├── Header
│   ├── Goal / Source design / Source issue / Execution owner / Blocked by
│   ├── Architecture / Tech stack / Quality gate
│   ├── File / Responsibility Map（Create / Modify / Test / Docs）
│   └── 发布风险和人工门禁表
└── Task Pack 列表（每个小 issue → 一个 Task Pack）
    └── Task Pack N.M: <small issue title>
        ├── Issue / Goal behavior
        ├── Owned files / responsibilities
        ├── Read first（source docs / ADRs / mockups）
        ├── Contract anchors / Mockup anchors
        ├── Acceptance criteria（从 issue 映射）
        ├── Verification commands（pack-local）
        ├── Implementation tasks（TDD: Red → Green → Refactor per step）
        ├── Commit boundary
        ├── Risk flags / 发布风险
        ├── AFK / HITL
        ├── Dependencies / Parallel safety
        └── Out of scope
```

**Task Pack 编号**：`N.M`，N = plan/issue 文件编号，M = pack 在该 plan 内的序号。Pack 2.3 = plan 002 的第 3 个 Task Pack。

**关键设计决策**：
- 每个 plan-writer agent **只负责一个大 issue**——Coordinator 逐 issue 派发
- Worker **不读 plan 文件**——Pack Brief 在 dispatch prompt 中完整自足
- Task Pack 是最小执行单元：包含 worker 所需的一切（任务、验收、命令、文件、合同锚点）
- 无 Placeholder 规则：TBD/TODO/later 出现在 plan 中 = plan failure
- `Dependencies` + `Parallel safety` 字段决定 pack 能否并行 worktree 执行

### 文档间引用关系

```
设计文档 ←───────────── plan header: Source design
    │
    ├─(Design Review)
    │
    ▼
大 Issue 文件 ←──────── plan header: Source issue
    │                    plan header: Blocked by（从 issue 继承）
    │
    ├─(1 大 issue = 1 plan 文件，编号对应)
    │
    │   小 issue ←────── Task Pack: Issue 字段
    │   acceptance ←──── Task Pack: Acceptance criteria
    │   blocked-by ←──── Task Pack: Dependencies
    │
    ▼
Plan 文件
    │
    ├─(Plan Entry Gate + Task Pack Inventory Gate)
    │
    ▼
Worker dispatch（Pack Brief 自足）
```

**单向引用**：设计文档不引用 issue/plan（上游只产出不消费下游）。Issue 不引用 plan。Plan 引用设计文档和 issue。Worker dispatch 嵌入 pack 内容，不引用 plan 文件路径。

---

## 返回值路由表

### orchestrate-discovery → orchestrate-workflow

| 返回值 | Coordinator 动作 |
|--------|-----------------|
| `DISCOVERY_READY` | 检查 issue hierarchy → 有则进 plan-writing；无则先调 `to-issues` |
| `DISCOVERY_NOT_NEEDED` | 同上 |
| `READY_FOR_REPAIR` | 进入 Direct Repair mini-route → Closing |
| `NEEDS_USER_DECISION` | 询问用户 → 重新进入 discovery |
| `BLOCKED` | 报告用户 |

### orchestrate-plan-writing → orchestrate-workflow

| 返回值 | Coordinator 动作 |
|--------|-----------------|
| `PLAN_CREATED` | 确认 budget file → 进入 execution |
| `NEEDS_DISCOVERY` | 回到 discovery |
| `NEEDS_DESIGN_REVIEW` | 回到 design review |
| `NEEDS_ISSUES` / `NEEDS_TRIAGE` | 调用 to-issues / triage |
| `NEEDS_DIAGNOSIS` / `NEEDS_ARCHITECTURE` / `NEEDS_CONTEXT` | 调用对应外部 skill |
| `NEEDS_DECISION` | 询问用户 |
| `BLOCKED` | 报告用户 |

### orchestrate-execution → orchestrate-workflow

| 返回值 | Coordinator 动作 |
|--------|-----------------|
| `EXECUTION_PASSED` | 进入 final-review |
| `NEEDS_DISCOVERY` | 回到 discovery |
| `NEEDS_PLAN_REVISION` | 回到 plan-writing |
| `NEEDS_ARCHITECTURE` | 调用 improve-codebase-architecture → 回到 execution 或 plan-writing |
| `BLOCKED` | 报告用户 |

### orchestrate-final-review → orchestrate-workflow

| 返回值 | Coordinator 动作 |
|--------|-----------------|
| `FINAL_REVIEW_PASSED` | Closing |
| `FINAL_REVIEW_PASSED_WITH_RELEASE_RISK` | Closing（release review 已在内部处理） |
| `NEEDS_EXECUTION` | 回到 execution（**最多 1 次**；第 2 次 → BLOCKED） |
| `NEEDS_DISCOVERY` | 回到 discovery |
| `NEEDS_PLAN_REVISION` | 回到 plan-writing |
| `BLOCKED` | 报告用户 |

### orchestrate-multi-pr-merge → orchestrate-workflow

| 返回值 | Coordinator 动作 |
|--------|-----------------|
| `MERGE_COMPLETE` | Closing |
| `NEEDS_DISCOVERY` | analyst 发现设计/意图冲突 → 回到 discovery |
| `NEEDS_USER_DECISION` | 询问用户 |
| `BLOCKED` | 报告用户 |

---

## 组件汇总

### 内部 Skill（6 个，按需加载到主线程）

| Skill | 对应节点 | 职责 |
|-------|---------|------|
| `orchestrate-workflow` | 路线判定 + Infrastructure + Bug 路线 + Direct Repair + Closing | 入口路由、Scope Contract、Git Checkpoint、Budget File、Bug 路线调度、Direct Repair mini-route、Closing |
| `orchestrate-discovery` | Discovery + Design Review + to-issues 过渡 | Q&A 迭代 + grill-with-docs + 设计文档 + Design Review + to-issues 检查/调用 |
| `orchestrate-plan-writing` | Plan Writing + Plan Review | 前置确认 + plan-writer dispatch + Budget 赋值 + Plan Review + Git Checkpoint |
| `orchestrate-execution` | Execution（图 2） | Pack 循环：派 worker → Pack Review → 修复分流 → Early Release Gate → 循环释放 |
| `orchestrate-final-review` | Final Review + Release Gate | 意图验证 + 清扫遗留尾巴 + Final Release Gate + 业务汇报 |
| `orchestrate-multi-pr-merge` | Multi-PR Merge（图 3） | 冲突发现 → 根因调查 → 修复 → 集成审查 → 合并 |

Skill 命名空间：`multi-model-workflow:orchestrate-*`（全限定名，通过 `Skill({ skill: "..." })` 调用）。

### Sub-Agent（7 个）

| Agent | 模型 | 用在哪 | `skills:` 自动加载 | 体内 Skill tool 调用 |
|-------|------|--------|-------------------|---------------------|
| `plan-writer` | Opus 4.7 (1M) | Plan Writing | — | `improve-codebase-architecture` |
| `pack-executor` | Sonnet | Execution 普通 pack / Bug worker | `tdd` | `diagnose`, `prototype` |
| `complex-pack-executor` | Opus 4.7 | Execution 高风险 pack / Release blocker | `tdd` | `diagnose`, `improve-codebase-architecture`, `prototype` |
| `code-explorer` | Sonnet | Execution 证据收集 / Multi-PR 代码探索 | — | — |
| `complex-code-explorer` | Opus 4.7 | 多模块调查 | — | — |
| `root-cause-analyst` | Opus 4.7 (1M), maxTurns: 40 | Bug Investigation / Execution RCA / Multi-PR 冲突调查 | `diagnose`, `tdd` | — |
| `docs-worker` | Sonnet, maxTurns: 20 | 文档清理（Closing 阶段可选） | `grill-with-docs` | — |

**注意**：
- Plugin-v2 **没有 `code-reviewer` 和 `release-reviewer` agent**。所有 review 通过 `dispatch 模板内联的 Codex review 步骤` 直接调用 codex 插件的 `codex-companion.mjs` 派发。
- `skills:` 自动加载 = frontmatter 声明，agent 启动时自动预加载。体内 Skill tool 调用 = agent body 中通过 `Skill({ skill: "..." })` 按需调用，不预加载。
- `plan-writer` frontmatter 无 `skills:` 字段，`improve-codebase-architecture` 在 body 中按需调用。
- `docs-worker` frontmatter 只声明 `grill-with-docs`，**`triage` 未在 frontmatter 中声明**（与原 draft 不一致）。

### Hooks（5 个）

| 事件 | Matcher | 做什么 | 强制行为 |
|------|---------|--------|---------|
| `SessionStart` | `startup\|clear\|compact` | `session-start.sh`：注入行为覆盖规则 | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 未设置 → exit 2（阻断会话）。注入 compaction recovery 规则（"进入任何 phase 前 re-read scope contract"）的唯一入口 |
| `PreToolUse` | `Bash` | `guard-premature-push.sh`：阻止未完成时 push/PR | ① plan 文件有未勾选 task（`- [ ]`）→ 阻止 `git push` / `gh pr create`　② 无条件阻止 `git merge --squash` / `git rebase` |
| `PreToolUse` | `Bash` | `cleanup-before-push.sh`：push 前清理 `.claude/multi-model-workflow/` | guard 放行后执行。删除整个 `.claude/multi-model-workflow/` 目录（active-run-id + budget + scope + review 临时文件）。拒绝删除符号链接。**唯一清理机制**——skill 流程中无显式清理步骤 |
| `PostToolUse` | `Bash` | `track-review-budget.sh`：budget 自动追踪 | 检测 Bash 输出含 `codex-companion` + `result` 且 exit 0 → 递增 `budget_used` + 追加 `dispatches[]` 时间戳。80% → Direction Check 警告；100% → BUDGET EXHAUSTED（均通过 `additionalContext` 注入 Coordinator 上下文） |
| `SubagentStop` | `pack-executor\|complex-pack-executor` | 提醒 Coordinator 派发 Codex review | 软提醒（stderr），非阻断 |

### 外部 Skill

#### Coordinator 按需调用（主线程 Skill tool）

| Skill | 用在哪 | 产出 |
|-------|--------|------|
| `grill-with-docs` | Discovery：术语对齐，同步维护 CONTEXT.md | 更新 CONTEXT.md |
| `prototype` | Discovery：状态/UI 方向验证 | throwaway 原型 + verdict |
| `to-issues` | Design Review 通过后 | vertical issues |
| `improve-codebase-architecture` | Execution 中 architecture friction / Discovery 中架构分析 | 架构分析 + 建议 |
| `zoom-out` | 任何阶段需要代码地图 | 模块地图 + 调用链 |
| `triage` | Issue 管理 | issue 分类 |
| `diagnose` | Bug 路线或 Execution 中需要重现/假设 | 反馈循环 + 假设 |

#### Agent-Bound（frontmatter `skills:` 自动加载）

| Skill | 自动加载到 |
|-------|-----------|
| `tdd` | pack-executor, complex-pack-executor, root-cause-analyst |
| `diagnose` | root-cause-analyst |
| `grill-with-docs` | docs-worker |

其他 skill（`improve-codebase-architecture`、`prototype`、`triage`、`zoom-out`）**不在任何 agent frontmatter 的 `skills:` 中**——agent body 中通过 `Skill({ skill: "..." })` 按需调用。

#### 外部 Plugin（可选）

| Plugin Skill | 用在哪 |
|-------------|--------|
| `frontend-design` | Discovery：UI 项目的高品质前端原型 |

---

## Review 派发机制

所有 review 通过 codex 插件的 `codex-companion.mjs` 脚本派发（不使用独立 reviewer agent）。每次 dispatch 固定四步：

```
1. 定位脚本    find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" | head -1
2. 提交任务    node "$CODEX_SCRIPT" task --background --prompt-file <path> --model gpt-5.4 --effort xhigh → JOB_ID
3. 等待完成    node "$CODEX_SCRIPT" status <JOB_ID> --wait --timeout-ms 600000（run_in_background）
4. 取回结果    node "$CODEX_SCRIPT" result <JOB_ID> → 写入 review-results/<gate>.md
```

Budget 计数器在 Step 4 触发（`track-review-budget.sh` 检测 `result` 命令成功执行），不在 Step 2。600 秒超时是单次 review 的硬上限。

### Disposition 表（全 phase 通用）

Coordinator **不是传话筒**——必须亲验每条 finding（读代码、跑测试、对照 source artifacts）后才给 disposition：

| Disposition | 行为 |
|------------|------|
| `accepted` | 进入修复流程（Pack Review → worker 修；Plan Review → 4 种子路由见下） |
| `rejected` | 附技术理由，finding 不进入修复 |
| `needs evidence` | 派 `code-explorer` / `complex-code-explorer` 子调查 → `confirmed / refuted / partially confirmed` → 再定 disposition |
| `duplicate or already covered` | 标记 |
| `out of scope` | 开 GitHub Issue（Durable Handoff Brief 格式） |
| `needs evaluation` | Coordinator 评估后归入其他 disposition |
| `user decision` | 暂停，询问用户 |

**Plan Review `accepted` 的四种子路由**：`plan repair`（Coordinator 或 plan-writer 直接修）· `design gap`（回流 Discovery）· `issue-plan mismatch`（调 to-issues）· `architecture friction`（调 improve-codebase-architecture）。

### Review 链路健壮性审计

#### 🟥 `guard-premature-push.sh` 任务完成检查失效

`guard-premature-push.sh:33` 用 `ls -t docs/orchestrate/plans/*.md` 检查未勾选 task。但实际 plan 文件路径是 `docs/orchestrate/plans/<slug>/00N-*.md`（多一层目录）。glob `plans/*.md` 不匹配任何文件 → `PLAN` 为空 → 检查被跳过 → **push 不会因未完成 task 而阻断**。合并策略规则（squash/rebase 阻断）不受影响。

**修复**：改为 `ls -t docs/orchestrate/plans/**/*.md` 或 `find docs/orchestrate/plans -name '*.md' -print -quit`。

#### 🟥 JOB_ID 不持久化——compaction 后丢失

四步协议中 JOB_ID 只存在于 Coordinator 上下文。如果 Step 2（submit）和 Step 4（result）之间发生 `compact`（SessionStart hook 触发 compaction recovery），JOB_ID 丢失但 Codex 任务仍在后台运行。`review-prompts/<gate>.md` 保存了 prompt 但不保存 JOB_ID。没有任何磁盘文件能恢复 in-flight review 状态。

**影响**：必须重新 submit 相同 prompt（budget 多消耗 1），且无法取消前一个孤儿任务。

**修复方向**：Step 2 后将 JOB_ID 写入 `review-prompts/<gate>.job-id`，Step 4 前先检查该文件。

#### 🟧 Re-review 结果文件无轮次后缀——覆盖前一轮记录

| 文件模式 | 有无轮次区分 |
|---------|------------|
| `pack-review-N.M.md` | ✅ Pack 级唯一 |
| `release-gate-N.M.md` | ✅ Pack 级唯一 |
| `plan-review.md` | ❌ 唯一名称，轮次覆盖 |
| `final-review-re-review.md` | ❌ 修复 Round 2 覆盖 Round 1 |
| `multi-pr-targeted-re-review.md` | ❌ 修复 Round 2 覆盖 Round 1 |
| `final-review-baseline-{1,2}.md` | ✅ 但如果 `needs context` 重派，覆盖前一次 |

前一轮审查记录被覆盖后无法取证（repair truncation 中 RCA 需要前两轮上下文，但 review result 文件只有最新一轮）。实际上 Coordinator 上下文中保留了前轮信息——磁盘丢失的是离线取证能力。

**修复方向**：文件名加 `-round-N` 后缀（如 `final-review-re-review-round-1.md`）。

#### 🟧 `CODEX_SCRIPT` 定位静默失败

`find ~/.claude/plugins -path "*/codex/scripts/codex-companion.mjs" | head -1` 在 codex 插件未安装时返回空字符串。后续 `node "$CODEX_SCRIPT" task ...` 静默失败（exit code ≠ 0）。`track-review-budget.sh` 不递增 budget（因 exit_code ≠ 0），但 Coordinator 也收不到 review 结果——可能把空结果当成 `pass` 或死循环等待。

**修复方向**：Step 1 后检查 `CODEX_SCRIPT` 非空，否则报错退出。

#### 🟧 Discovery 预算与全局预算重叠计数

Discovery Design Review 用 `discovery_used`（上限 4）做 per-phase cap。但 `track-review-budget.sh` 不知道 `discovery_used`——它在每次 `result` 成功时无条件递增 `budget_used`。所以 Discovery 的 2-4 次 dispatch **同时**递增了 `budget_used` 和 `discovery_used`。

当 `budget_total = 2N + 12` 在 plan-writing Step 12a 赋值时，`budget_used` 已经 > 0（Discovery 已消耗 2-4）。+12 余量中实际可用的修复空间比文档暗示的少 2-4。

> 注：上方「Budget 预算分配」中 Design Review 的 2 dispatch 预留应理解为"已消耗"，不是"额外配额"。

---

## 修复截断规则

所有修复循环（Pack Review / Final Review / Multi-PR）共享同一截断模式：

```
Round 1-2：三路分流
  Path A — Coordinator 直接修复（≤ 2 文件）
  Path B — Worker 修复（SendMessage 原 worker 或新建 dispatch）
  Path C — code-explorer 只读调查（根因不明时）
  → Targeted Re-Review

Round 3（截断轮）：
  停止 worker 循环 → 派 root-cause-analyst（带前 2 轮完整上下文）
  RCA 五种结论：
    fixed                     → Targeted Re-Review
    root cause found not fixed → worker 按 RCA 结论修复
    root cause in design/plan → 回流 Discovery（创建 bug seed file）
    unable to reproduce       → 降级为 non-blocking + 开 GitHub Issue
    unable to determine       → BLOCKED

Round 3 Re-Review 仍 needs repair → BLOCKED
```

**Final Review → Execution 回流**：`execution_reflux_count`（budget file 字段，初始 0）。允许回流 1 次（increment → 1）；第 2 次 → BLOCKED。防止无限 Final Review ↔ Execution 循环。

---

## Budget 预算分配

### 公式 `2N + 12`

N = 所有 plan 中 Task Pack 总数。`budget_total` 在 plan-writing Step 12a **首次且唯一赋值**，执行阶段不可变。

### +12 的分配

| 预留 | 数量 | 用途 |
|------|------|------|
| Design Review（已消耗） | 2-4 | 2 baseline + 最多 2 repair。在 `budget_total` 赋值前已发生，赋值时 `budget_used` 已 > 0 |
| Plan Review | 1 | 1 baseline |
| Final Review | 2 | 2 baseline（Regression+Intent+Cross-Pack / Code-level） |
| Release Gate | 2 | Early Release Gate + Final Release Gate（共享，合计 ≤ 2） |
| 修复余量 | 3-5 | pack repair re-review + final repair re-review（Discovery 多消耗则此处缩减） |

### Discovery 预算机制

Design Review 在 `budget_total` 赋值之前执行。Coordinator 用独立计数器 `discovery_used`（上限 4）做 per-phase cap，但 `track-review-budget.sh` 同时递增 `budget_used`。两个计数器并行：`discovery_used` 防单 phase 失控，`budget_used` 跟踪全局消耗。当 Step 12a 赋值 `budget_total = 2N+12` 时，`budget_used` 已包含 Discovery 消耗。

### 三级耗尽行为

| 阈值 | 行为 |
|------|------|
| `budget_used ≥ 80%` | Direction Check：Coordinator 汇报当前进度 + 剩余 pack + 累计 findings，确认是否继续 |
| 下一动作将超 `budget_total` | 停止 dispatch，请求用户授权追加预算或简化 |
| `budget_used ≥ budget_total` | 硬停。Hook 输出 BUDGET EXHAUSTED |

Budget **不因 phase 回流而重置**。Plan revision 改变 pack_count 时必须回到 plan-writing Step 12a 重算。

---

## Scope Contract 完整字段

```markdown
# Scope Contract: <run_id>

## Feature slug
YYYY-MM-DD-<feature>

## Source artifacts
<用户提供的文档 / tracker / diff — 只读参考>

## Editable artifacts
- Design: docs/orchestrate/design/<slug>.md
- Plans: docs/orchestrate/plans/<slug>/
- Issues: docs/orchestrate/issues/<slug>/
- Mockups: docs/orchestrate/mockups/<slug>/        （UI 项目）

## Read-only context
<相关 issue / ADR / 代码 / runbook — sub-agent 可读不可改>

## Out of scope
<明确排除的相关内容 — reviewer 提及也不授权修改>
```

**Editable vs Read-only 的区别是 sub-agent 的写权限边界**：worker 修改的文件必须在 Editable artifacts 中，否则 execution preparation 返回 `NEEDS_PLAN_REVISION`。Out of scope 用于阻止 reviewer scope creep。Feature slug 确定后不可变。

---

## 跨会话恢复

恢复会话时不是"从上次停的地方继续"，而是检查 source artifact 是否在上次 gate 之后被修改过：

```bash
git log --oneline --since="<last_gate_timestamp>" -- \
  "docs/orchestrate/design/${SLUG}.md" \
  "docs/orchestrate/plans/${SLUG}/" \
  "docs/orchestrate/issues/${SLUG}/"
```

- Source artifact 在 gate 后有改动 → **重新进入对应 gate review**（不跳过）
- `active-run-id` 对应的 budget file 超过 1 小时未更新 → 视为 stale，允许新 run 覆盖
- SessionStart hook 注入的 compaction recovery 规则：进入任何 phase 前必须 re-read `scope-<run_id>.md`

---

## Bug Seed File 与设计级别升级

`root-cause-analyst` 返回 `root cause in design/plan` 时不直接回 Discovery，而是：

1. 创建 `.claude/multi-model-workflow/bug-seed-<run_id>.md`（结构化摘要：原始 bug · analyst findings · root cause · 受影响模块 · 排除假设 · 建议设计变更）
2. 更新 Scope Contract：bug seed 加入 Source artifacts，design/plan 加入 Editable artifacts
3. 创建 Budget File
4. 以 seed file 作为 Discovery 上下文进入 Route 1（Formal Orchestrate）

---

## 架构约束

- **渐进式加载**：SKILL.md 是骨架；reference 到达步骤时才读取
- **Sub-agent 隔离**：dispatch prompt 自足；sub-agent 不读 SKILL.md / references
- **Agent 定义 = 行为权威**：TDD、自检、scope 边界等通用规则写 agent 定义，dispatch template 只写场景信息
- **Reviewer 独立验证**：所有 Calibration 包含"不信任上游报告"；Coordinator 亲验后才给 disposition
- **合并策略铁律**：只用 `git merge --no-ff`，禁止 squash merge 和 rebase（`guard-premature-push.sh` 进程级强制）
- **Review 预算**：`2N + 12`（N = pack 数），Discovery 有独立 4-dispatch 预算。三级耗尽（80% Direction Check → 溢出停派 → 100% 硬停）
- **修复截断**：所有修复循环 3 轮封顶（2 轮 A/B/C + 1 轮 RCA），超出 → BLOCKED
- **回流守卫**：Final Review → Execution 回流最多 1 次（`execution_reflux_count`）
- **跨会话稳定性**：恢复时检查 source artifact 是否在 gate 后被修改——有改动则重进 gate review
- **`AGENT_TEAMS` 硬依赖**：`session-start.sh` 阻断未设置 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 的会话
- **Worker scope 漂移检测**：worker 修改了 Owned files 之外的文件 → 当前 scope 内的保留，scope 外的回滚

---

## 设计决策

- Bug 路线不走 Final Review——`bug-investigation-route.md` Step 17/18 → Closing
- Bug RCA 发现设计问题 → 不直接回 Discovery，先创建 bug seed file 再以 seed 进入 Route 1
- 文档阶段线性不回流——Discovery → Design Review → to-issues → Plan Writing → Plan Review，各一轮 review + 修复
- Release Review 最多两次——Execution Early Release Gate + Final Release Gate，共享 ≤ 2 dispatch 配额
- Coding Worker 无"非阻塞项"——要么当场修，要么开 GitHub Issue（Durable Handoff Brief 格式）
- Worker Open Items 在 Pack Review **之前**处理——`[out-of-scope]` 立即开 issue，`[needs-evaluation]` Coordinator 评估归类
- Closing 积极主动——提交 + 推送 + PR 自动执行，`guard-premature-push.sh` 确保完成后才放行
- Review 无独立 agent——全部通过 `codex-companion.mjs` 四步协议（submit → poll → result → budget hook）
- Budget 由 PostToolUse hook 自动追踪——prompt 写入 `review-prompts/<gate>.md`，结果存 `review-results/<gate>.md`
- Pre-dispatch Context Transfer 强制——每个 pack dispatch 前必须从磁盘 re-read plan（防 compaction 后信息丢失）；Pack Brief 不允许"见 plan"等间接引用
- Direct Repair mini-route 不创建 Budget File——已有 approved design 的实现偏差走单 worker + 1 review + ≤ 2 repair

---

## 与 Codex Runtime 的关系

Plugin-v2 和 `.agents/skills/`（Codex runtime）是**两套并行代码**，30+ 文件已不同步。同步方向单向：`.agents/skills/` → 外部 repo（通过 `install-orchestrate-runtime.sh`）。

| 维度 | Plugin V2 | Codex Runtime |
|------|-----------|---------------|
| Skill 调用语法 | `Skill({ skill: "multi-model-workflow:..." })` | 裸名 `orchestrate-*` |
| 状态文件路径 | `.claude/multi-model-workflow/` | `.codex/multi-model-workflow/` |
| Review 派发 | `codex-companion.mjs` Bash 调用 | `claude-subscription-review.sh` |
| Agent 命名 | `plan-writer`（连字符） | `plan_writer`（下划线） |
| Worker 隔离 | `isolation: "worktree"` | disjoint write sets |

---

## 编辑同步清单

- 改 disposition 表 → 同步 4 个 phase 文件（execution-pack-review-cycle / final-review-disposition / plan-review-resolution / merge-integration-review）
- 改 disposition `needs context` 前置检查 → 同步全部 5 个 disposition 文件（含 design-review-angles）
- 改 Forbidden Shortcuts → 同步 execution-review-dispatch.md + final-review-angles.md
- 改 verdict 值 → `rg` 验证所有 producer 和 consumer
- 改 dispatch template → 检查 agent 定义的模式检测表是否对齐
- 改 agent 通用规则 → 检查所有相关 agent 定义
- 改 NEEDS_EXECUTION 上限 → 同步 final-review-repair.md + final-review-completion.md + workflow-formal-orchestrate.md
- dispatch template 不放 agent 定义已有的规则（TDD、自检、Git 纪律等）

# Plugin-V2 Rebuild Plan

基于 `architecture-draft.md` 的 14 条对齐结论，定义从当前 8 个 skill → 目标 6 个 skill 的重构映射。

## 当前 vs 目标

### 当前 8 个 Skill

| Skill | 当前职责 |
|-------|---------|
| orchestrate-workflow | Entry gate + routing |
| orchestrate-discovery | Design document creation（Q&A 迭代） |
| orchestrate-design-review | Design review dispatch（2 baseline Codex） |
| orchestrate-plan-writing | Plan writing（双角色：coordinator dispatch + plan-writer 执行） |
| orchestrate-plan-review | Plan review dispatch（3 baseline Codex） |
| orchestrate-execution | Pack loop |
| orchestrate-final-review | Final review + Phase C closing |
| orchestrate-direct-repair | Bug fix / Direct Repair dispatch |

### 目标 6 个 Skill

| # | Skill | 变更类型 | 说明 |
|---|-------|---------|------|
| 1 | orchestrate-workflow | 大幅重写 | 吸收 design-review + plan-review + direct-repair 的 coordinator 职责，加入 Bug 路线和 Closing |
| 2 | orchestrate-discovery | 重大修订 | 集成 grill-with-docs（CONTEXT.md 共进化）+ prototype + frontend-design 等外部 skill |
| 3 | orchestrate-plan-writing | 重构 | 拆为 agent-facing only；coordinator 调度逻辑移入 orchestrate-workflow |
| 4 | orchestrate-execution | 中等修订 | 对齐图 2 循环结构、修复分流规则、结论 10（不存在非阻塞项） |
| 5 | orchestrate-final-review | 中等修订 | 拆出 Closing → workflow；对齐结论 9/10/12 |
| 6 | orchestrate-multi-pr-merge | **新建** | 实现图 3：多 PR 并行分析 + 冲突解决 + 集成审查 |

### 删除 3 个 Skill

| 删除 | 内容去向 |
|------|---------|
| orchestrate-design-review | SKILL.md → workflow 内联逻辑；design-review-angles.md → workflow/references/ |
| orchestrate-plan-review | SKILL.md → workflow 内联逻辑；plan-review-angles.md → workflow/references/ |
| orchestrate-direct-repair | Bug 路线 → workflow Entry Gate；repair-grading.md → workflow/references/ |

**不能删除 orchestrate-plan-writing 的原因**：plan-writer agent 在 frontmatter 中声明 `skills: ["orchestrate-plan-writing"]`，agent 启动时自动加载此 skill。删除会导致 agent 无法获取写作流程、plan 合同和自检清单。

## 外部 Skill 完整清单

orchestrate 系统依赖两类外部 skill：agent 自动加载的（agent frontmatter `skills:` 字段）和 coordinator 按需调用的（主线程 `Skill tool`）。

### Agent-Bound Skills（agent 启动时自动加载）

| 外部 Skill | 绑定 Agent | 作用 |
|-----------|-----------|------|
| **tdd** | pack-executor, complex-pack-executor, root-cause-analyst | Red-Green-Refactor 开发纪律 |
| **diagnose** | root-cause-analyst, pack-executor, complex-pack-executor | Bug 诊断循环：reproduce → hypothesise → instrument → fix |
| **prototype** | pack-executor, complex-pack-executor | 状态/UI 原型验证 |
| **improve-codebase-architecture** | complex-pack-executor, plan-writer | 代码库深度重构分析 |
| **grill-with-docs** | docs-worker | 术语对齐 + CONTEXT.md 维护 |
| **triage** | docs-worker | Issue 状态机管理 |

### Coordinator-Invoked Skills（主线程按需调用）

| 外部 Skill | 调用阶段 | 作用 |
|-----------|---------|------|
| **grill-with-docs** | Discovery | 与设计文档同步生成/更新 CONTEXT.md；挑战术语一致性 |
| **prototype** | Discovery | mockup 生成、状态/UI 方向验证 |
| **to-issues** | Design Review 通过后 | 设计文档 → vertical large issues → small issues |
| **improve-codebase-architecture** | Execution 中 architecture friction 时 | 分析模块边界、合同表面、深度重构机会 |
| **zoom-out** | 任何阶段需要代码地图时 | 模块地图、调用链、边界上下文 |
| **triage** | Issue 管理时 | Issue 分类、ready state、AFK/HITL 判定 |
| **diagnose** | Bug 路线或 Execution 中需要重现/假设时 | 构建反馈循环 → 重现 → 假设 → 验证 |

### 外部 Plugin Skills（可选，按需使用）

| Plugin Skill | 调用阶段 | 作用 |
|-------------|---------|------|
| **frontend-design** | Discovery（UI 项目） | 生成高品质 UI 原型和前端界面 |

### 关键设计：Discovery 阶段的 CONTEXT.md 共进化

Discovery 不只产出设计文档——它还通过 **grill-with-docs** 同步维护 CONTEXT.md：

- 每次讨论中术语被确认或修正时，立即更新 CONTEXT.md
- 设计文档和 CONTEXT.md **共同进化**，确保项目的领域模型始终与设计保持一致
- Discovery 阶段是灵活多变的：grill-with-docs 做术语对齐、prototype 做状态/UI 验证、frontend-design 做前端原型、improve-codebase-architecture 做架构分析——按需组合

orchestrate-discovery 的 SKILL.md 不应该硬编码一条固定流程，而是提供一组可调用的工具菜单，让 coordinator 根据讨论方向灵活选择。

## Per-Skill 详细映射

### 1. orchestrate-workflow（大幅重写）

**新增职责**：
- Design Review 调度（读 angles → 派 Codex → 修 findings → 一轮结束）
- Plan Review 调度（同上）
- Plan Writing 调度（派 plan-writer agent）
- Bug 路线（root-cause-analyst → fix → Codex review → done | → 路线 1）
- Closing（business-report + commit + push + PR）

**SKILL.md 结构**（保持精简路由器，详细规则在 references）：
```
Entry Gate（3 路线 + Direct Repair 入口）
→ Resume Gate
→ Scope Contract
→ Git Checkpoint

路线 1（新设计/优化）:
  Discovery → Design Review → to-issues → Plan Writing → Plan Review
  → orchestrate-execution → orchestrate-final-review → Closing

路线 2（Bug）:
  root-cause-analyst → 简单 fix + Codex review → Closing
                     → 深层问题 → 汇入路线 1

路线 3（多 PR 合并）:
  → orchestrate-multi-pr-merge → Closing

Direct Repair（目标行为清楚的明确修复）:
  Coordinator 直接修 / 派 worker → 按风险分级 review → Closing
```

**Per-skill references**：

| 文件 | 来源 | Coordinator 读取时机 |
|------|------|---------------------|
| references/design-review-angles.md | ← orchestrate-design-review | Design Review 构建 Codex prompt |
| references/plan-review-angles.md | ← orchestrate-plan-review | Plan Review 构建 Codex prompt |
| references/plan-writing-dispatch.md | ← plan-writing/coordinator-dispatch.md | 派发 plan-writer agent |
| references/repair-grading.md | ← orchestrate-direct-repair | Direct Repair / Bug fix review 分级 |
| references/business-report.md | ← orchestrate-final-review | Closing 阶段业务汇报 |

**需从 `.agents/` 集成的规则**：
- Reader Boundary 表（sub-agent 不读 SKILL.md 和 references）
- Reference Map（节点 → 到达条件 + 必读 + 动作 + 下一跳）— 简化为新架构版本
- Handoff Status 表（verdict → 下一步的完整映射）
- Hard Gates（不可跳过的约束）
- Design/Plan review 阶段的修复分流（coordinator 直接修）

### 2. orchestrate-discovery（重大修订）

**变更**：
- 集成 **grill-with-docs**：设计讨论过程中同步维护 CONTEXT.md，确保术语和领域模型与设计文档共同进化
- 集成 **prototype**：需要验证状态/UI 方向时调用，生成 throwaway 原型回答设计问题
- 集成 **frontend-design**（可选）：UI 项目需要高品质前端原型时调用
- SKILL.md 从固定线性流程改为**灵活工具菜单**：coordinator 根据讨论方向按需组合调用
- 现有 Q&A 迭代 → design document 核心流程保留
- 边界规则、返回格式保留

**Discovery 阶段可调用的外部 Skill**：

| Skill | 触发条件 | 产出 |
|-------|---------|------|
| grill-with-docs | 讨论中出现模糊术语、领域冲突、需要对齐概念时 | 更新 CONTEXT.md（术语表 + ADR） |
| prototype | 需要验证状态模型、UI 方向、接口形态时 | throwaway 原型 + verdict |
| frontend-design | UI 项目需要高品质前端原型时 | 前端界面原型 |
| improve-codebase-architecture | 需要理解现有模块边界和合同表面时 | 架构分析 + deepening 建议 |
| zoom-out | 需要代码地图、调用链、模块关系时 | 模块地图 + 边界上下文 |
| diagnose | 从 bug/regression 出发需要构建反馈循环时 | 重现路径 + 假设 + 关键接口 |

**Per-skill references**（全部保留）：

| 文件 | 动作 |
|------|------|
| references/discovery-input.md | 保留 |
| references/discovery-checklist.md | 保留 |
| references/design-document-contract.md | 保留 |

### 3. orchestrate-plan-writing（重构为 agent-facing）

**变更**：
- coordinator-dispatch.md 移出 → orchestrate-workflow/references/plan-writing-dispatch.md
- SKILL.md 从"双角色 2 行指引"重写为 agent 的完整执行指引
- plan-writing-flow.md、plan-contract.md、plan-checklist.md 保留给 agent 用

**Agent 依赖链**：
```
plan-writer agent
  └─ skills: ["orchestrate-plan-writing"]
      └─ SKILL.md（agent 启动时自动加载）
          ├─ references/plan-writing-flow.md（执行流程）
          ├─ references/plan-contract.md（plan 模板/合同）
          └─ references/plan-checklist.md（自检清单）
```

**Per-skill references**：

| 文件 | 动作 |
|------|------|
| references/coordinator-dispatch.md | **移出** → orchestrate-workflow |
| references/plan-writing-flow.md | 保留（agent 用） |
| references/plan-contract.md | 保留（agent 用） |
| references/plan-checklist.md | 保留（agent 用） |

### 4. orchestrate-execution（中等修订）

**变更**：
- SKILL.md 对齐图 2 的完整循环结构（worker dispatch → Pack Review → 修复分流 → targeted re-review → 还有 pack? → Final Review）
- 修复分流规则的 4 个完整判断条件（≤2 文件、不触碰合同边界、不需新增测试、意图明确）
- 结论 10：Coding Worker 规则——不存在"非阻塞项"，要么当场修，要么开 GitHub Issue
- 第 2 轮 repair 仍失败时截断 worker 循环 → root-cause-analyst 介入

**Per-skill references**（全部保留）：

| 文件 | 动作 |
|------|------|
| references/pack-dispatch.md | 保留，对齐 |
| references/pack-review.md | 保留，对齐 |
| references/worktree-merge.md | 保留 |

### 5. orchestrate-final-review（中等修订）

**变更**：
- **拆出** Phase C（business-report + branch finishing）→ orchestrate-workflow Closing
- 保留：意图验证（代码是否偏离设计/计划）+ 清扫遗留尾巴（结论 9）
- 保留：Release Review dispatch（只做一次，在 Final Review 之后，结论 12）
- 对齐结论 10：不存在"非阻塞项"

**Per-skill references**：

| 文件 | 动作 |
|------|------|
| references/final-review-angles.md | 保留 |
| references/business-report.md | **移出** → orchestrate-workflow |

### 6. orchestrate-multi-pr-merge（新建）

**实现图 3**：
1. Coordinator 阅读全部文档（大设计 + 大计划 + 大 Issue + 各 PR 小文档）
2. 建立"合并后正确状态"的理解
3. 并行派发 code-explorer 验证 PR 间代码/功能/意图关系（结论 14）
4. 修复分流：简单 → Coordinator 直接修；复杂/系统性 → 派 coding worker
5. Coordinator 验证修复（不是 Explorer，结论 13/14）
6. 所有冲突解决后 → Codex 全量 Review（跨 PR 集成审查）
7. 按计划顺序合并 PR

**Per-skill references**：

| 文件 | 动作 |
|------|------|
| references/multi-pr-review-angles.md | **新建** |

## 共享 References（5 个，全部保留）

| 文件 | 动作 | 使用者 |
|------|------|--------|
| dispatch-primitives.md | 修订对齐新架构 | workflow, execution, final-review, multi-pr-merge |
| review-budget.md | 修订预算公式 | workflow, execution, final-review |
| coordinator-tools.md | 修订 Handoff Status + Direction Check | workflow |
| contract-boundary.md | 保留不动 | workflow, execution, final-review, multi-pr-merge |
| custom-agents.md | 保留不动 | workflow, execution, multi-pr-merge |

## Agent 依赖检查

每个 agent 的 `skills:` 字段决定它启动时自动加载哪些 skill。这些绑定关系不可遗漏。

| Agent | 角色 | skills 绑定 | 本次重构影响 |
|-------|------|------------|-------------|
| plan-writer | Plan 写作 | **orchestrate-plan-writing**, improve-codebase-architecture | orchestrate-plan-writing 重构为 agent-facing，不删除 |
| pack-executor | 普通 coding | **tdd**, diagnose, prototype | 无影响（全部外部 skill） |
| complex-pack-executor | 高风险 coding | **tdd**, diagnose, improve-codebase-architecture, prototype | 无影响 |
| root-cause-analyst | Bug 调查 + 修复 | **diagnose**, tdd | 无影响 |
| docs-worker | 文档清理 | **grill-with-docs**, triage | 无影响 |
| code-explorer | 窄范围代码探索 | 无 | 无影响 |
| complex-code-explorer | 多模块调查 | 无 | 无影响 |

**设计原则**：
- **tdd** 绑定给两个 pack-executor + root-cause-analyst → 所有写代码的 agent 都遵循 Red-Green-Refactor
- **diagnose** 绑定给 root-cause-analyst → 根因调查的完整方法论
- **grill-with-docs** 绑定给 docs-worker → 文档工作始终对齐 CONTEXT.md
- **improve-codebase-architecture** 绑定给 complex-pack-executor + plan-writer → 高风险工作和计划写作都能分析架构

## Reference 文件迁移总表

| 当前位置 | 目标位置 | 动作 |
|---------|---------|------|
| design-review/refs/design-review-angles.md | workflow/refs/design-review-angles.md | 移动 |
| plan-review/refs/plan-review-angles.md | workflow/refs/plan-review-angles.md | 移动 |
| plan-writing/refs/coordinator-dispatch.md | workflow/refs/plan-writing-dispatch.md | 移动+重命名 |
| plan-writing/refs/plan-writing-flow.md | plan-writing/refs/plan-writing-flow.md | 保留 |
| plan-writing/refs/plan-contract.md | plan-writing/refs/plan-contract.md | 保留 |
| plan-writing/refs/plan-checklist.md | plan-writing/refs/plan-checklist.md | 保留 |
| direct-repair/refs/repair-grading.md | workflow/refs/repair-grading.md | 移动 |
| final-review/refs/business-report.md | workflow/refs/business-report.md | 移动 |
| final-review/refs/final-review-angles.md | final-review/refs/final-review-angles.md | 保留 |
| discovery/refs/* (3 files) | discovery/refs/* | 保留 |
| execution/refs/* (3 files) | execution/refs/* | 保留 |

## 待确认：Direct Repair 的非 Bug 场景

架构结论 1 将 Direct Repair 归为 Bug Investigation 的子路径。但当前 orchestrate-direct-repair 覆盖的场景更广——"已有批准 design/plan/mockup/acceptance/failing test，目标行为清楚"包括非 bug 修复（如用户说"把这个 typo 改了"、"按 reviewer 的 finding 改"）。

**建议**：在 orchestrate-workflow Entry Gate 保留"Direct Repair"入口——Coordinator 直接修 / 派 worker → 按风险分级 review → done。不经过 root-cause-analyst。这不是第四条路线，而是路线 1 和路线 2 的快速通道。

## 实施顺序

从无依赖到有依赖，从边缘到核心：

| 步骤 | 动作 | 理由 |
|------|------|------|
| 1 | 新建 orchestrate-multi-pr-merge | 无依赖，纯新建 |
| 2 | 重构 orchestrate-plan-writing | plan-writer agent 依赖此 skill，需要先改好 |
| 3 | 修订 orchestrate-final-review | 拆出 Closing，为 workflow 准备 |
| 4 | 修订 orchestrate-execution | 对齐循环结构 |
| 5 | 修订 orchestrate-discovery | 集成方法论参考 |
| 6 | 重写 orchestrate-workflow | 吸收所有内容，最复杂 |
| 7 | 移动 reference 文件 | 按迁移总表执行 |
| 8 | 删除 3 个废弃 skill 目录 | 确认无残留引用后删除 |
| 9 | 修订共享 references | dispatch-primitives + review-budget + coordinator-tools |

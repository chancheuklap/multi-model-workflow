# Navigation Signpost Fix — 设计文档

## 1. 问题

用户反馈：使用 plugin-v2 执行 orchestrate 工作流时，agent 经常跳步或漏掉步骤。Plugin 的渐进式加载模式要求 agent 在 SKILL.md 和 reference 文档之间来回跳转，每次跳转都是一次 context 切换，agent 必须记住"我从哪来、回到哪去"。

## 2. 根因：脊柱碎片化（Spine Fragmentation）

gstack 调研揭示了核心问题：我们的 workflow spine（执行主线）分散在 35+ 个文件里。一次完整的 Route 1 执行需要 Claude 跨 30+ 个文件跳转。gstack 把同样复杂度的 workflow 全部内联在一个 3000 行 SKILL.md 里——它根本不存在导航问题。

我们不能照搬 gstack 的模式（它有 TypeScript 构建系统、.tmpl + 45 个 resolver），但 gstack 的思路——减少跳转、把 hot-path 内联、用结构化标记代替自由散文——可以渐进式引入。

## 3. Plan-Writing 内部基准

### 为什么 plan-writing 全部合格而 execution 频繁跳步

**plan-writing**（81 行 SKILL.md，6 个 reference，全部通过审计）：
- SKILL.md 持有控制流——Steps 9-10 有 5 步内联循环（遍历 issues/ → 逐个派 plan-writer → 映射文件名 → 处理返回 → 迭代）
- References 只提供模板/方法论/标准，不含控制流逻辑
- 每个 reference 的 entry signpost 都包含 "完成后 → next.md" 链

**execution**（62 行 SKILL.md，7 个 reference，最严重跳步）：
- SKILL.md 把控制流本身委托给 pack-review-cycle.md（"Read ... 并严格执行"）
- pack-review-cycle.md (109行) 再委托到 worker-dispatch.md 和 review-dispatch.md
- 3 层间接跳转：SKILL.md → pack-review-cycle → worker-dispatch + review-dispatch
- Agent 需同时持有 3 个文件的上下文才能执行一个 pack

**结论**：控制流必须留在 SKILL.md 里，references 应该只提供模板和方法论。plan-writing 在自己的仓库里证明了这个模式。

## 4. 设计讨论中的关键决策

### 4.1 Hooks — 放弃

PostToolUse 在 Read 之后立刻触发，但 reference 文档不是"读完就走"的——里面有要执行的步骤。如果 hook 在 Read 后立刻把出口路标推到 Claude 面前，Claude 很可能看到出口就直接走了，中间的步骤全跳过。**Hook 在这个场景下找不到正确的触发时机**——Read 之后太早，"执行完文档内容"这个事件在 hook 系统里不存在。

### 4.2 命令形式路标 — 放弃

把路标写成 `Read references/next.md` 命令 vs 文字 `→ Step X（next.md）`，效果相同。**失败点不在"怎么理解路标"，而在"有没有看到路标"**。路标的格式不是关键变量，路标的位置才是。文档底部路标恰恰因为在内容最后面——Claude 必须先经过所有步骤，才能看到出口。

### 4.3 统一路标格式 — 采用

路标格式和语言在所有文档里统一，避免 agent 理解模糊。两端锚定：

**顶部入口**（标准化措辞）：
```
> **流程位置**：`skill-name` Steps X-Y · 简述职责 · 入口条件
```

**底部出口**（紧贴文档末尾，前面用 `---` 分隔）：
```
---
> **下一步**：[路由]
```

4 种标准句式：

| 类型 | 适用场景 | 句式 |
|------|---------|------|
| 线性 | 下一步固定 | `→ Step X（filename.md）` |
| 分支 | 按条件走不同路 | `通过 → Step X。needs repair → Step Y。BLOCKED → 返回 verdict。` |
| 返回调用方 | 模板/参考类文档 | `回到 SKILL.md Step X 继续` |
| 终止 | 流程终点 | `流程到此结束。` |

纯参考文档（格式参考、方法论参考）用变体：
```
> **参考文档**：`skill-name` 用途说明 · 非流程步骤
```

### 4.4 三层防护模型

| 层 | 机制 | 抗什么风险 |
|---|------|-----------| 
| 出发锚 | SKILL.md 的 Read 指令里写明回程 | 防"跳过去就忘了从哪来" |
| 位置书签 | Budget file 记录 current_phase/current_reference | 防 context 压缩后失忆 |
| 到达锚 | reference 文档底部出口路标 | 防"读完不知道去哪" |

出发锚 + 到达锚是必须做的（纯文档层面，零成本）。位置书签通过 budget file 的状态字段实现（Layer 3）。

## 5. 三层修复方案

### Layer 1：减少跳转（最高杠杆）

把"每次都会读"的 hot-path control-flow reference 内联回 SKILL.md。plan-writing 的基准告诉我们：**控制流应内联，模板/方法论应委托**。

#### 5.1.1 orchestrate-execution：内联 pack-review-cycle

**原始方案**提议内联 worker-dispatch (63行) + review-dispatch (93行)。**Plan-writing 基准**表明：控制流（循环逻辑）才应该内联，模板可以继续委托。pack-review-cycle.md 包含的是 Steps 4-9 的循环控制流，worker-dispatch 和 review-dispatch 是模板定义。

**两个选项**：

- **选项 A（原始方案）**：内联 worker-dispatch + review-dispatch（模板），保留 pack-review-cycle（控制流仍委托）。消除模板跳转，但循环逻辑仍在 reference 里。SKILL.md ~220行。
- **选项 B（plan-writing 对齐）**：内联 pack-review-cycle（控制流），保留 worker-dispatch + review-dispatch（模板继续委托）。循环逻辑在 SKILL.md，匹配 plan-writing 的成功模式。SKILL.md ~140行。

两个选项都把每 pack 跳转从 4-6 次降到 2 次。选项 B 与 plan-writing 结构一致（控制流内联、模板委托），且 SKILL.md 更短。**本文档按选项 B 展开（已确认）。**

按选项 B 的文件处置：

| 文件 | 行数 | 处置 | 理由 |
|------|------|------|------|
| execution-pack-review-cycle.md | 109 | **内联到 SKILL.md → 删除原文件** | 控制流，plan-writing 模式要求内联 |
| execution-worker-dispatch.md | 63 | 保留为 reference | 模板定义，非控制流 |
| execution-review-dispatch.md | 93 | 保留为 reference | 模板定义，非控制流 |
| execution-preparation.md | — | 保留为 reference | 一次性准备步骤 |
| execution-repair-truncation.md | — | 保留为 reference | 条件触发（仅 needs repair） |
| execution-release-gate.md | — | 保留为 reference | 条件触发（仅触碰风险面） |
| execution-completion.md | — | 保留为 reference | 循环结束后执行 |

内联后 SKILL.md 结构（62行 → ~140行）：

```
Steps 1-3  → execution-preparation.md（出发锚：读完回到 Step 4 开始循环）
Step 4     内联：Worker 类型选择表（risk flags → agent 映射）
Step 5     内联：Pre-dispatch Context Transfer + Pack Brief 填充规则
           → execution-worker-dispatch.md（出发锚：读完回到 Step 5b 继续）
Step 6     内联：Agent() 派发 + 记录 agentId
Step 7     内联：Worker 返回路由表 + scope drift 检测 + Open Items 即时处置
Step 8     内联：派发 Codex Reviewer
           → execution-review-dispatch.md（出发锚：读完回到 Step 9 继续）
Step 9     内联：per-finding disposition 表 + needs evidence 补证
Steps 10-12 → execution-repair-truncation.md（出发锚：修复后回到 Steps 4-9 或 Step 13）
Step 13    → execution-release-gate.md（条件触发）
Steps 14-16 → execution-completion.md
```

跳转从 4-6 次/pack 降到 2 次/pack（worker 模板 + review 模板）。

**内联内容详细清单**（从 pack-review-cycle.md 提取）：

**Step 4 — Worker 类型选择**（~6行）：Risk flags → Agent 映射表。

**Step 5 — Pack Brief 构造**（~20行精简）：
- 5a Pre-dispatch Context Transfer：确认 plan 文件在上下文中、提取 pack 字段
- 5b Pack Brief 填充：逐字段填入模板、Implementation tasks 完整粘贴、prompt 自足验证

**Step 6 — 派发 Worker**（~5行）：Agent() 调用代码块 + 记录 agentId + 并行 pack 说明。

**Step 7 — 接收 Worker 返回**（~25行精简）：
- Verdict 路由表：pass → 7a → 8 / needs repair → 10 / needs context → SendMessage / blocked → 用户
- Scope drift 检测：Changed files vs Owned files
- Step 7a Open Items 即时处置表：out-of-scope / needs-evaluation / bug / 无标记 → 各自处置
- GitHub Issue 格式引用（Durable Handoff Brief）

**Step 8 — 派发 Codex Reviewer**（~2行）：Read execution-review-dispatch.md + 出发锚。

**Step 9 — Disposition**（~20行精简）：
- 前置检查：整体 needs context → 补充后重新 dispatch
- 亲验规则：Coordinator 必须亲验每条 finding
- Disposition 表：accepted / rejected（不让同一 finding 反复进入 review）/ needs evidence / duplicate / out of scope（Durable Handoff Brief 格式，先查重）/ needs evaluation / user decision
- needs evidence 补证：code-explorer（窄范围）/ complex-code-explorer（多模块）
- 路由：通过 → Step 13 / Needs repair → Step 10

#### 5.1.2 orchestrate-workflow：内联 formal-orchestrate

formal-orchestrate.md (104行) 是 Route 1 的 phase dispatch + verdict routing——纯控制流。Routes 2 和 3 已经在 SKILL.md 中内联（Bug Investigation 有 reference 但 dispatch 内联，Multi-PR Merge verdict 表内联），只有 Route 1 全部委托。内联后一致。

| 文件 | 行数 | 处置 | 理由 |
|------|------|------|------|
| workflow-formal-orchestrate.md | 104 | **内联到 SKILL.md → 删除原文件** | Phase dispatch + verdict 路由，纯控制流 |
| workflow-infrastructure.md | — | 保留 | 一次性 setup + resume |
| bug-investigation-route.md | — | 保留 | 条件触发（Route 2） |
| workflow-closing.md | — | 保留 | 所有 Route 的终点 |
| workflow-direct-repair.md | — | 保留 | 条件触发（READY_FOR_REPAIR） |

内联后 SKILL.md 结构（72行 → ~175行）：

```
Step 1     内联：Entry Gate（已有内联路由表）
Step 2     内联：Within-Conversation Resume
Steps 3-6  → workflow-infrastructure.md（出发锚）
Step 7     内联：Skill({ skill: "orchestrate-discovery" })
Step 8     内联：Handle Discovery Return（verdict 路由表 + to-issues 上下文传递 + Direct Repair mini-route 引用）
Step 9     内联：Skill({ skill: "orchestrate-plan-writing" })
Step 10    内联：Handle Plan-writing Return（verdict 路由表 + Budget 更新）
Step 11    内联：Skill({ skill: "orchestrate-execution" })
Step 12    内联：Handle Execution Return（verdict 路由表 + Budget 更新）
Step 13    内联：Skill({ skill: "orchestrate-final-review" })
Step 14    内联：Handle Final Review Return（verdict 路由表 + Budget 更新 + reflux 计数）
Steps 15-18 → bug-investigation-route.md（出发锚）
Steps 19-20 内联：Multi-PR Merge dispatch + verdict（已有）
Steps 21-24 → workflow-closing.md（出发锚）
```

#### 5.1.3 其他 Skill — 不内联

| Skill | 理由 |
|-------|------|
| orchestrate-discovery | 全部 reference 条件触发，无 hot-path 控制流委托 |
| orchestrate-plan-writing | 已全部通过审计，是成功基准 |
| orchestrate-final-review | 全部 reference 条件触发 |
| orchestrate-multi-pr-merge | 全部 reference 条件触发 |

---

### Layer 2：强化仍需跳转的文档（中等杠杆）

#### 5.2.1 底部出口路标（16 个文档）

审计结果：2 个缺入口+出口，10 个缺出口，4 个出口偏弱。

**A. 入口 + 出口全缺（2 个）**

**discovery-formats.md**（纯格式参考）：
```
顶部加：
> **参考文档**：`orchestrate-discovery` 全程可查阅 · CONTEXT.md + ADR 格式参考 · 非流程步骤

底部加：
---
> **回到**：你之前正在执行的步骤继续。本文档是格式参考，不是流程步骤。
```

**rca-pr-conflict-methodology.md**（方法论参考）：
```
标题后加：
> **参考文档**：`orchestrate-multi-pr-merge` Step 9 · Root-Cause-Analyst 派发时随 prompt 传入 · 非流程步骤

底部加：
---
> **回到**：`merge-rca-investigation.md` 的 Analyst Resolution 路由继续。
```

**B. 出口缺失（10 个）**

| # | 文件 | 出口类型 | 新增底部路标文本 |
|---|------|---------|----------------|
| 1 | workflow-closing.md | 终止 | `> **流程到此结束**。orchestrate-workflow 返回 verdict，不再读取其他 reference。` |
| 2 | workflow-formal-orchestrate.md | — | Layer 1 内联后删除，不需要出口路标 |
| 3 | workflow-infrastructure.md | 分支 | `> **下一步**：Route 1 → SKILL.md Steps 7-14（内联 Formal Orchestrate）。Route 2 → Steps 15-18（bug-investigation-route.md）。Route 3 → Steps 19-20（SKILL.md 内联）。` |
| 4 | design-review-angles.md | 分支 | `> **下一步**：Design Review 通过 → 回到 SKILL.md Step 12（过渡到 to-issues）。needs repair → Coordinator 直接修设计文档 → targeted re-review。` |
| 5 | execution-worker-dispatch.md | 返回 | `> **回到**：SKILL.md Step 5b 继续填充 Pack Brief → Step 6 派发 Worker。` |
| 6 | execution-review-dispatch.md | 返回 | `> **回到**：SKILL.md Step 9（接收 Review Findings + Disposition）。` |
| 7 | execution-release-gate.md | 分支 | `> **下一步**：通过 → Step 14（execution-completion.md）。需修复 → targeted release re-review。BLOCKED → 返回 verdict。` |
| 8 | final-review-preconditions.md | 分支 | `> **下一步**：前置条件通过 → Steps 4-5（final-review-angles.md）。缺件 → 按上方路由表返回对应 upstream phase。` |
| 9 | final-review-angles.md | 线性 | `> **下一步**：两个 baseline 提交后 → Steps 6-8（final-review-disposition.md）。` |
| 10 | final-review-completion.md | 分支 | `> **下一步**：verdict 确定后回到 SKILL.md 返回区组装最终返回值。NEEDS_EXECUTION → orchestrate-execution。BLOCKED → 报告用户。` |

**C. 出口偏弱（4 个）——底部加强**

| # | 文件 | 现状 | 新增底部路标 |
|---|------|------|------------|
| 1 | discovery-discussion.md | 出口只在顶部 banner | `> **下一步**：讨论充分后 → Steps 7-9（discovery-design-document.md）生成设计文档。` |
| 2 | discovery-design-document.md | 出口只在顶部 banner | `> **下一步**：用户确认设计文档后 → Steps 10-11（design-review-angles.md）进入 Design Review。` |
| 3 | merge-conflict-discovery.md | 三分支路由只在顶部 | `> **下一步**：无冲突 → Step 16（merge-integration-review.md）。简单冲突已修 → Step 14（Coordinator 验证）。复杂冲突 → Step 12（merge-conflict-repair.md）。系统性冲突 → Step 9（merge-rca-investigation.md）。` |
| 4 | merge-completion.md | 说"回到 SKILL.md 返回区"但不具体 | `> **下一步**：verdict 确定后回到 SKILL.md 返回区。MERGE_COMPLETE → orchestrate-workflow Closing。` |

#### 5.2.2 出发锚（SKILL.md Read 指令加回程说明）

每个 SKILL.md 的 Read 指令都应包含回程说明，形成双向锚定。

**改写规则**：在现有 Read 指令的括号说明中加入回程目标。

Before:
```
**Read** `references/execution-preparation.md` 并严格执行（读 plan inventory + 构建执行队列 + 验证 Scope Contract / Git / Budget）。
```

After:
```
**Read** `references/execution-preparation.md` 并严格执行（读 plan inventory + 构建执行队列 + 验证 Scope Contract / Git / Budget）。读完回到 Step 4 开始 pack 循环。
```

以下列出每个 SKILL.md 的所有 Read 指令及其回程目标：

**orchestrate-workflow/SKILL.md**（Layer 1 内联后）：
```
Step 3:  → references/workflow-infrastructure.md（读完按 Route 进入对应 phase）
Steps 15-18: → references/bug-investigation-route.md（读完进入 Closing）
Steps 21-24: → references/workflow-closing.md（流程终点）
```

**orchestrate-discovery/SKILL.md**：
```
Steps 3-6: → references/discovery-discussion.md（读完进入 Steps 7-9 生成设计文档）
Steps 7-9: → references/discovery-design-document.md（读完进入 Steps 10-11 Design Review）
Steps 10-11: → references/design-review-angles.md（通过后回到 Step 12 过渡 to-issues）
```

**orchestrate-plan-writing/SKILL.md**（已合格，补出发锚保持一致性）：
```
Steps 0-2: Read references/plan-preconditions.md（读完进入 Steps 3-8 方法论）
Steps 3-8: Read references/plan-writing-methodology.md（Coordinator 理解后进入 Steps 9-10 派发）
Steps 9-10: Read references/plan-writer-dispatch.md（派发后进入 Steps 11-12a gate）
Steps 11-12a: Read references/plan-gates.md（通过后进入 Steps 13-14 review）
Steps 13-14: Read references/plan-review-dispatch.md（派发后进入 Steps 15-18 disposition）
Steps 15-18: Read references/plan-review-resolution.md（通过后回到 Step 19 Git Checkpoint）
```

**orchestrate-execution/SKILL.md**（Layer 1 内联后）：
```
Steps 1-3: Read references/execution-preparation.md（读完回到 Step 4 开始 pack 循环）
Step 5 (内联): Read references/execution-worker-dispatch.md（读完回到 Step 5b 填充 Pack Brief）
Step 8 (内联): Read references/execution-review-dispatch.md（读完回到 Step 9 接收 Findings）
Steps 10-12: → references/execution-repair-truncation.md（修复后回到 Steps 4-9 继续循环或 Step 13）
Step 13: → references/execution-release-gate.md（通过后 → Step 14）
Steps 14-16: → references/execution-completion.md（完成后回到 SKILL.md 返回区）
```

**orchestrate-final-review/SKILL.md**：
```
Steps 1-3: → references/final-review-preconditions.md（通过后进入 Steps 4-5）
Steps 4-5: → references/final-review-angles.md（派发后进入 Steps 6-8）
Steps 6-8: → references/final-review-disposition.md（通过 → Step 13；有 findings → Step 9）
Steps 9-12: → references/final-review-repair.md（修复后回 Step 11 re-review 或 Step 13）
Steps 13-20: → references/final-review-completion.md（完成后回到 SKILL.md 返回区）
Steps 16-18: → references/final-review-release-gate.md（通过后回 Step 19）
```

**orchestrate-multi-pr-merge/SKILL.md**：
```
Steps 1-3: → references/merge-preparation.md（读完进入 Steps 4-8 冲突发现）
Steps 4-8: → references/merge-conflict-discovery.md（按冲突分类路由到 Step 8/9/12/16）
Steps 9-11: → references/merge-rca-investigation.md（调查后路由到 repair 或报告）
Steps 12-15: → references/merge-conflict-repair.md（修复后 → Step 14 验证 → 循环或 Step 16）
Steps 16-18: → references/merge-integration-review.md（通过后 → Steps 19-22）
Steps 19-22: → references/merge-completion.md（完成后回到 SKILL.md 返回区）
```

#### 5.2.3 Stop/Continue 表

每个 SKILL.md 顶部加 Stop/Continue 表（放在 frontmatter 和标题之间的 `---` 分隔线后、Steps 1 之前），枚举什么情况停、什么情况继续。借鉴 gstack 的 "Only stop for / Never stop for" 模式。

**orchestrate-workflow**：
```
**Only stop for：**
- 模糊输入需要收窄（一次只问一个）
- BLOCKED verdict
- 用户业务决策

**Never stop for：**
- Phase 之间过渡（连续执行，不问"要不要继续"）
- Upstream verdict 路由（自动进入对应 phase）
```

**orchestrate-discovery**：
```
**Only stop for：**
- 需要用户确认设计方向
- 需要用户确认设计文档
- BLOCKED

**Never stop for：**
- 讨论中间环节（一问一答持续迭代）
- Design Review findings（Coordinator 直接修复，不问用户）
```

**orchestrate-plan-writing**：
```
**Only stop for：**
- Plan-writer 返回 upstream verdict 需要用户决策
- BLOCKED

**Never stop for：**
- Issue 之间的切换（连续逐 issue 派发 plan-writer）
- Plan Review findings（按修复分流处理）
```

**orchestrate-execution**：
```
**Only stop for：**
- Worker 返回 blocked（业务阻塞才停，技术阻塞自行处理）
- Review 的 user decision disposition
- BLOCKED

**Never stop for：**
- Pack 之间（连续执行，不暂停汇报）
- Worker 返回 needs repair（进入修复分流）
- Review findings 需要 disposition（Coordinator 逐条处理）
```

**orchestrate-final-review**：
```
**Only stop for：**
- 需要用户决策的 finding
- BLOCKED

**Never stop for：**
- Accepted findings（进入修复分流）
- 遗留清扫发现（当场处置或开 issue）
- Release Gate findings（走 release review 流程）
```

**orchestrate-multi-pr-merge**：
```
**Only stop for：**
- 冲突解决需要用户决策（NEEDS_USER_DECISION）
- BLOCKED

**Never stop for：**
- 简单冲突（Coordinator 直接修）
- 复杂冲突（派 Worker 修复）
- 系统性冲突（Analyst 调查 → Worker 修复）
```

#### 5.2.4 Pre-phase 验证清单

进入 phase 前，内联一个快速检查清单。不是替代 preparation reference（那里做详细验证），而是 SKILL.md 里的快速 gate，防止在明显缺件时进入。

**orchestrate-execution SKILL.md — Steps 1-3 前**：
```
**Pre-execution（进入前快速验证）：**
- [ ] Plan Review 通过（所有 plan 文件）
- [ ] Budget file 存在且 budget_total > 0
- [ ] Scope Contract 存在
- [ ] Git 在 work branch 上
```

**orchestrate-final-review SKILL.md — Steps 1-3 前**：
```
**Pre-final-review（进入前快速验证）：**
- [ ] 所有 pack 通过 Pack Review + Git Checkpoint
- [ ] Source design 存在且已通过 Design Review
- [ ] Scope Contract 和 Budget file 存在
```

**orchestrate-plan-writing SKILL.md — Steps 0-2 前**：
```
**Pre-plan-writing（进入前快速验证）：**
- [ ] Design Review 通过
- [ ] Issue hierarchy 已就绪（docs/orchestrate/issues/<slug>/）
- [ ] Scope Contract 和 Budget file 存在
```

#### 5.2.5 Required Outputs 清单

返回 verdict 前，内联一个必需输出清单。防止 agent 在关键产物缺失时就返回。

**orchestrate-execution SKILL.md — 返回区前**：
```
**Required before returning（返回前验证）：**
- [ ] 所有 pack 有 pass 或 blocked 状态
- [ ] 所有 Open Items 已处置（issue 已开或已修）
- [ ] Git Checkpoint 完成
- [ ] Plan checkboxes 已更新
- [ ] Budget 消耗已记录
```

**orchestrate-final-review SKILL.md — 返回区前**：
```
**Required before returning（返回前验证）：**
- [ ] 两个 baseline review 有结果
- [ ] 所有 accepted findings 已修复并通过 re-review
- [ ] 遗留清扫完成（无未处置项）
- [ ] Release Gate 通过（如触发）
- [ ] 业务汇报已组装
```

**orchestrate-plan-writing SKILL.md — 返回区前**：
```
**Required before returning（返回前验证）：**
- [ ] 所有 issue 的 plan 文件已写完
- [ ] Plan Entry Gate + Task Pack Inventory Gate 通过
- [ ] budget_total 已赋值（2N + 12）
- [ ] Plan Review 通过
- [ ] Git Checkpoint 完成
```

#### 5.2.6 Phase-Transition Summary

Phase 之间，**Claude 必须在运行时输出**一句过渡总结（不是文件里的静态文本，是 Coordinator 在 phase 切换时的必做动作）。在 orchestrate-workflow 的每个 Handle Return 步骤中加入要求：

```
> **Phase complete.** [Phase]: [关键指标]。Passing to [next phase]。
```

示例：
```
> **Phase complete.** Discovery: design doc created, Design Review passed (2 baselines, 1 repair round). Passing to to-issues.
> **Phase complete.** Plan-writing: 3 plans created, 8 task packs, budget 28. Passing to Execution.
> **Phase complete.** Execution: 8/8 packs passed, 5 repair rounds, budget 18/28 used. Passing to Final Review.
```

---

### Layer 3：状态锚加固（NLAH 论文验证的最强恢复机制，+5.5 分）

在现有 budget file 中增加 3 个字段，供 compaction 后恢复精确位置：

```json
{
  "run_id": "formal-20250521-143000",
  "budget_total": 28,
  "budget_used": 14,
  "pack_count": 8,
  "starting_commit": "abc1234",
  "execution_reflux_count": 0,
  "last_gate_phase": "execution",
  "last_gate_timestamp": "2025-05-21T14:30:00Z",
  "current_phase": "execution",
  "current_reference": "execution-worker-dispatch.md",
  "current_step": "5b",
  "dispatches": []
}
```

**新增字段**：

| 字段 | 类型 | 更新时机 | 用途 |
|------|------|---------|------|
| `current_phase` | string | 进入/退出 phase skill 时 | Compaction 后知道在哪个 phase |
| `current_reference` | string \| null | Read reference 前写入，执行完写 null | Compaction 后知道在哪个 reference 里 |
| `current_step` | string | 每个 step 开始时 | Compaction 后知道在哪个步骤 |

**更新规则**：
- 进入 phase skill → 写 `current_phase`，清空 `current_reference` 和 `current_step`
- Read reference 前 → 写 `current_reference`
- 执行完 reference 回到 SKILL.md → `current_reference` 设为 null
- 开始新 step → 写 `current_step`

**恢复规则**（compaction 后）：
1. 读 budget file 的 `current_phase` / `current_reference` / `current_step`
2. 如果 `current_reference` 不为 null → 重新 Read 该 reference，从 `current_step` 位置继续
3. 如果 `current_reference` 为 null → 在 SKILL.md 的 `current_step` 位置继续

**与现有 `last_gate_phase` 的区别**：`last_gate_phase` 记录最近通过的 gate（粗粒度，phase 级），`current_phase` + `current_reference` + `current_step` 记录实时位置（细粒度，step 级）。两者共存，用于不同场景：
- Cross-conversation resume（新对话接手）→ 用 `last_gate_phase`（从上次通过的 gate 继续）
- Compaction recovery（同对话压缩）→ 用 `current_*`（从压缩前的精确位置继续）

**Budget / Route 限制**：Layer 3 仅适用于 Formal Orchestrate route（有 budget file）。Bug route 和 Multi-PR route 不创建 budget file，不使用状态锚。

---

## 6. 不做什么（及理由）

| 不做 | 理由 |
|------|------|
| Hooks 作为导航机制 | PostToolUse 在 Read 之后、执行之前触发，会导致 agent 跳过文档步骤直接去下一步（§4.1） |
| 命令形式路标 | 失败点在"有没有看到路标"不在"怎么理解路标"，格式不是关键变量（§4.2） |
| gstack build-time template 系统 | 引入构建步骤、TypeScript codegen，收益不足以覆盖复杂度 |
| gstack 700 行 shared preamble | 我们没有这个问题，不制造问题 |
| 所有 reference 合并成单文件 | 条件触发的 reference 应该保持独立，不浪费 token budget |
| TaskCreate 位置书签 | Budget file 状态锚（Layer 3）比 TaskCreate 更持久、更结构化，已替代 |
| plan-writing 的结构和控制流改动 | 它是成功基准，结构不动；只补 Layer 2 中适用的统一格式（出发锚 / Pre-phase / Required Outputs） |

---

## 7. 实施计划

### 实施顺序

按用户批准的 ROI 排序：

1. **Layer 1：Hot-path 内联**——pack-review-cycle 内联到 execution，formal-orchestrate 内联到 workflow，删除原文件，更新所有交叉引用
2. **Layer 2A-B：出口路标 + 出发锚**——16 个文档补路标 + 6 个 SKILL.md 的 Read 指令加回程
3. **Layer 2C-F：结构化模式**——Stop/Continue 表 + Pre-phase 清单 + Required Outputs + Phase-transition 模板
4. **Layer 3：状态锚字段**——budget file schema 更新 + 各 phase skill 中加 current_* 字段写入点

每层完成后可独立验证、独立提交。

### 交叉引用更新清单（Layer 1 内联后）

**删除 pack-review-cycle.md 后**：
- `execution-preparation.md` entry signpost：`execution-pack-review-cycle.md` → `SKILL.md Steps 4-9`
- `execution-repair-truncation.md` exit signpost：`execution-pack-review-cycle.md` → `SKILL.md Steps 4-9`
- `architecture-draft.md` 编辑同步清单：`execution-pack-review-cycle` → `orchestrate-execution/SKILL.md Step 9`

**删除 workflow-formal-orchestrate.md 后**：
- `bug-investigation-route.md` 中引用它 → 改为 `SKILL.md Steps 7-14`
- `workflow-infrastructure.md` entry signpost 可能引用它 → 改为 `SKILL.md Steps 7-14`
- `architecture-draft.md` 中如有引用 → 更新

### 验证标准

1. **结构验证**：每个 reference 文件有 entry signpost，每个非终止 reference 有 exit signpost，每个 SKILL.md Read 指令有出发锚
2. **引用验证**：`grep -rn "pack-review-cycle\|workflow-formal-orchestrate" plugin-v2/` 返回空
3. **JSON 验证**：`python3 -m json.tool plugin-v2/.claude-plugin/plugin.json` 和 `hooks.json` 通过
4. **行为验证**：冷启动阅读修改后的 execution SKILL.md，Steps 4-9 的循环逻辑能独立理解，不需要跳到其他文件获取控制流信息

### 重复内容维护立场

- **删除原文件**：内联后的 pack-review-cycle.md 和 workflow-formal-orchestrate.md 都删除。控制流只存在于 SKILL.md 里，不维护双份。
- **模板文件保留**：worker-dispatch.md 和 review-dispatch.md 保留为 reference，它们是模板定义，SKILL.md 不重复其内容。修改模板时只改 reference 文件。
- **architecture-draft.md 同步**：编辑同步清单中的文件名引用必须更新。

---

## 8. 变更文件汇总

| 文件 | 变更类型 | Layer |
|------|---------|-------|
| orchestrate-execution/SKILL.md | 重写（内联控制流 + Stop/Continue + Pre-phase + Required Outputs + 出发锚） | 1+2 |
| orchestrate-execution/references/execution-pack-review-cycle.md | **删除** | 1 |
| orchestrate-workflow/SKILL.md | 重写（内联控制流 + Stop/Continue + 出发锚 + Phase-transition） | 1+2 |
| orchestrate-workflow/references/workflow-formal-orchestrate.md | **删除** | 1 |
| orchestrate-discovery/SKILL.md | 修改（Stop/Continue + 出发锚） | 2 |
| orchestrate-plan-writing/SKILL.md | 修改（Pre-phase + Required Outputs + 出发锚） | 2 |
| orchestrate-final-review/SKILL.md | 修改（Stop/Continue + Pre-phase + Required Outputs + 出发锚） | 2 |
| orchestrate-multi-pr-merge/SKILL.md | 修改（Stop/Continue + 出发锚） | 2 |
| discovery-formats.md | 加入口 + 出口 | 2 |
| rca-pr-conflict-methodology.md | 加入口 + 出口 | 2 |
| workflow-closing.md | 加终止路标 | 2 |
| workflow-infrastructure.md | 加出口路标 | 2 |
| design-review-angles.md | 加出口路标 | 2 |
| execution-worker-dispatch.md | 加出口路标 | 2 |
| execution-review-dispatch.md | 加出口路标 | 2 |
| execution-release-gate.md | 加出口路标 | 2 |
| final-review-preconditions.md | 加出口路标 | 2 |
| final-review-angles.md | 加出口路标 | 2 |
| final-review-completion.md | 加出口路标 | 2 |
| discovery-discussion.md | 底部加强出口 | 2 |
| discovery-design-document.md | 底部加强出口 | 2 |
| merge-conflict-discovery.md | 底部加强出口 | 2 |
| merge-completion.md | 底部加强出口 | 2 |
| execution-preparation.md | 更新 entry signpost（交叉引用） | 1 |
| execution-repair-truncation.md | 更新 exit signpost（交叉引用） | 1 |
| bug-investigation-route.md | 更新交叉引用（workflow-formal-orchestrate → SKILL.md Steps 7-14） | 1 |
| architecture-draft.md | 更新编辑同步清单 | 1 |
| budget file schema | 新增 current_phase / current_reference / current_step | 3 |
| workflow-infrastructure.md | 新增 current_* 写入说明（compaction recovery 读取点已有） | 3 |
| 各 phase skill references 中的 preparation/precondition 文件 | 新增 current_* 写入时机说明 | 3 |

**总计**：6 个 SKILL.md 修改 + 16 个 reference 加/改路标 + 2 个 reference 删除 + 3 个交叉引用更新 + 状态锚 schema + 写入点 = **~30 处变更**。

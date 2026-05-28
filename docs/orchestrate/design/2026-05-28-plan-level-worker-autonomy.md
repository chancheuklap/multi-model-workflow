# 设计文档：Plan-level Worker 自治 + Document-as-Context 原则

状态：**Living Draft**（与用户讨论中，持续补充）
作者：Orchestrator + 用户
日期：2026-05-28

---

## 背景与痛点

### 1. Token 重复消耗

当前 execution 阶段是两层循环：外层逐 Plan，内层逐 Pack 派 Worker。用户实际规模观察：

- 一次任务通常拆 7-11 个大 issue → 7-11 个 plan 文档
- 每个 plan 平均 5 个 Pack
- **总 Worker dispatch 数：35-55 次**

每次 Pack dispatch 的固定开销（被 35-55 倍重复消耗）：

1. Agent system prompt + `pack-executor.md` / `complex-pack-executor.md` 全文
2. CLAUDE.md 全文（user 全局 + project + memory）
3. Tools schema
4. Coordinator 临场构造的 Pack Brief
5. Worker 启动后重新加载同 Plan 内重叠的 source code

### 2. Coordinator session 累积

每 Pack 返回 Coordinator 都要：读 pack-returns、判断 verdict、处置 open items、commit、决定 next、构造下一 Pack Brief。45 次循环让 Coordinator session token 消耗与 Worker 重复开销同量级。

### 3. Dispatch Prompt 干扰文档为源

文档（design / plan）本应是上下文传递的唯一介质。但 Coordinator 在每次派发 Worker / Reviewer 时还要临场编写大量 dispatch prompt 来"补全"上下文。这带来三重代价：

- **额外 token 消耗**：dispatch prompt 重复编写（每个 Pack 都要写一遍 Pack Brief 提取）
- **Coordinator 思考负担**：每次派发都要重新"理解 + 提取 + 改写"
- **任务被 dispatch prompt 干扰**：Worker 收到的不只是文档，还有 Coordinator 现场的解释/侧重，可能与原始文档意图偏离

## 核心原则

### Document-as-Context（文档即上下文）

**既然选择用文档承载上下文，文档必须自足**。

不管是 reviewer、plan writer 还是 executor，都应该**只通过**以下两类输入就能了解任务全貌：

1. **完整文档**：他所负责的那份 design / issue / plan / pack 文档
2. **固定 reference**：对应 skill `references/` 下的角色提示词

**Coordinator 在 dispatch 时只传递：**
- 文档路径
- 必要的运行时变量（run_id、所属 phase、agent_id、idempotency_key）
- 极少量临场决策（如续派 vs 新派、SendMessage vs Agent）

**Coordinator 不再做：**
- 把文档里的 Implementation tasks 重新粘贴一遍
- 把文档里的 Acceptance criteria 重新粘贴一遍
- 临场改写、侧重、解释文档内容

### Worker 自治（Plan-level Autonomy）

Execution 阶段从「Coordinator 逐 Pack 监督 Worker」改为「Coordinator 派 1 个 Worker 自治整个 Plan」。

Worker 一次性接收 Plan 文档路径，内部按 Pack Dependencies 串行做完所有 Pack，每个 Pack 独立 commit。Coordinator 只在 Plan 边界介入。

## 方案 A：Plan-level Worker 自治

### 执行模型

**Coordinator 视角**（外层 FOR EACH Plan，按依赖排序）：

```
for plan in plans:
  1. 选 Worker 类型（按 Plan 内最高 Risk flags）
  2. 派 1 次 Worker：
     Agent({
       subagent_type: "plan-executor" | "complex-plan-executor",
       prompt: <DISPATCH_ENVELOPE> + <Plan 文档路径> + <run_id 等运行时变量>
     })
     # 不再粘贴 Plan/Pack 任何字段；Worker 自己 Read plan 文件
  3. 接收 plan-level 返回
  4. 批量处置 open items（gh issue 查重 + 开 issue）
  5. apply plan-doc 勾选 patch + commit
  6. 派 Plan Implementation Review（不变）
  7. Disposition + repair（SendMessage 同 Worker）
```

**Worker 视角**（收到 Plan 文档路径后）：

```
1. Read plan 文档
2. Read 对应 skill reference（execution-worker-handbook.md，固定提示词）
3. for pack in plan.packs (按 Dependencies 排序):
     a. TDD: red → green → refactor
     b. 跑 Verification commands
     c. Scope drift 自检 (changed files ⊆ owned files)
     d. 写 pack-returns/<run_id>/<pack-id>.json
     e. git commit "Pack N.M: <title> — <summary>"  # hook 校验
     f. 收集 Open Items 到 plan-returns 暂存
     g. 失败 → 写 partial 返回 + break
4. 写 plan-doc 勾选 patch 到 plan-returns/<plan-id>/doc-patch.diff
5. 返回 plan-level verdict + per-pack 状态 + open items 汇总
```

### Dispatch Prompt 极简化（关键）

旧 Pack Brief（~2-5k tokens × 45 次）：

```
Pack: 1.1 用户登录表单
Goal behavior: ...
Implementation tasks:
  <粘贴 plan 中 1.1 所有 task 原文>
Owned files:
  - Create: ...
Read first:
  - ...
Acceptance criteria:
  - [ ] ...
Verification commands:
  - ...
... (省略 200 行)
```

新 Plan Dispatch Prompt（~300 tokens × 9 次）：

```
<DISPATCH_ENVELOPE>
{
  "protocol_version": "1",
  "run_id": "...",
  "phase": "execution",
  "agent_role": "plan-executor",
  "agent_id": null,
  "plan_id": "001",
  "idempotency_key": "...",
  "correlation_id": "..."
}
</DISPATCH_ENVELOPE>

你的任务：执行 Plan 001。

Plan 文档（自足，包含所有 Pack 完整定义）：
- 路径：docs/orchestrate/plans/<slug>/001-<name>.md

固定角色提示词：
- 路径：${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-execution/references/execution-worker-handbook.md

运行时变量：
- STATE_DIR: <absolute path>
- run_id: <id>

请按 handbook 中的 Worker Loop 执行。
```

**节省**：每 Plan dispatch prompt 从 ~2-5k × 5 = 10-25k 降到 ~300。总省 50-200k tokens（lower bound for execution phase only）。

### Coordinator 监督的真正删减

| 原 Coordinator 每 Pack 做的事 | 新方案 |
| --- | --- |
| 校验 Worker verdict | Worker 自检（与 verification commands 联动） |
| 跑 Verification commands | Worker 自跑 |
| Scope drift 检测 | Worker 自检 + PostToolUse Edit hook 兜底 |
| Git commit `Pack N.M: ...` | Worker commit + `enforce-pack-commit.sh` hook 校验格式 |
| 写 pack-returns | Worker 写 |
| Open Items 即时处置 | 收集到 plan-returns，**Plan 结束 Coordinator 批量处置** |
| 勾选 plan doc | Worker 写 patch，**Plan 结束 Coordinator apply + commit** |
| 决定 next pack | Worker 自决（依赖 + 上一 Pack verdict） |

## 架构改动清单（Execution 阶段）

### 1. Skill / Reference

- `orchestrate-execution/SKILL.md` 重写 Step 4-7：从「逐 Pack 派发」改为「逐 Plan 派发 + 批量收尾」
- 新增 `orchestrate-execution/references/execution-worker-handbook.md`：固定提示词，包含 Worker Loop、TDD 纪律、commit 规范、return contract、failure modes
- 删除大部分 Coordinator 临场构造内容（Pack Brief 模板等）

### 2. Sub-agent

- `pack-executor.md` → `plan-executor.md`（重写为 Plan-level 自治）
- `complex-pack-executor.md` → `complex-plan-executor.md`（同上，Opus 4.7）

### 3. Build Templates

- 新增 `build/templates/plan-dispatch.md.tmpl`（极简模板，仅文档路径 + 运行时变量）
- 删除/简化 `pack-dispatch.md.tmpl`（如存在）

### 4. State

- `execution-state.plans[N]` 加 `worker_agent_id` 字段
- `state.sh agent-id set` 支持 plan-level
- schema：`state-schema/execution-state.schema.json` 同步更新

### 5. Hooks

- `validate-pack-dispatch.sh` → `validate-plan-dispatch.sh`：校验 plan_id、Plan 未 in-progress、文档存在、execution-state 有 plans entry
- `enforce-pack-commit.sh`：**不变**（Worker 仍每 Pack 一 commit）
- `track-execution-state.sh`：**不变**
- `agent-return-handler.sh`：从返回中解析 plan-level verdict + per-pack 状态映射
- `guard-doc-edit.sh`：允许 Worker 写 `plan-returns/<plan-id>/doc-patch.diff`（doc 勾选 staging）
- `hooks.json` matcher 更新（Agent + SendMessage）

### 6. Tests / Maturity

- 新增：plan-level dispatch 测试、worker loop fixture、partial-fail 恢复测试
- `verify-maturity.sh` C2/C4 检查同步

## 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| Worker 上下文累积（25-100k per Plan）| Worker handbook 含"context 自监控"指令，超阈值主动报 `need-fresh-worker` |
| Risk 模型按 Plan 决定（trivial pack 升级 Opus）| plan-writing 时约束「单 Plan 内 risk 同质」；混合时按最高 risk |
| 失败反馈延迟（Pack 3 失败前 2 已 commit，Coordinator 直到 Plan 返回才知）| Worker partial-pass 返回（带详细 per-pack 状态），失败 Pack ID 明确 |
| Worker 自治后 Coordinator 失去中途介入点 | 兜底用 hook（commit message 格式 / scope drift / state 写入）|
| 文档不自足时 Worker 卡住 | Worker handbook 含「文档缺字段时返回 `NEEDS_PLAN_REVISION`」 |

## Document-as-Context 原则的全局推广（待调查）

执行阶段是这次架构变更的起点，但 **Document-as-Context 原则适用于所有 skill**。下一步要系统性调查每个 skill 是否存在「Coordinator 临场编写 dispatch prompt」的可改善点：

1. `orchestrate-discovery`：Discovery → Design 阶段 dispatch
2. `orchestrate-plan-writing`：Plan Writer 派发 + Plan Review
3. `orchestrate-execution`：本文重点
4. `orchestrate-final-review`：Final Review 派发 + 修复 SendMessage
5. `orchestrate-multi-pr-merge`：merge 冲突修复 + 集成 review
6. `orchestrate-workflow`：主入口路由 + Entry Gate
7. `codex-review`：ad-hoc review 派发

调查结论会回写本设计文档「调查结果」章节。

## 用户的预期工作流（Document-as-Context 的最终形态）

| 步骤 | 输入 | 文档（自足）| 角色 reference（固定）|
| --- | --- | --- | --- |
| Discovery → Design | 用户与 Coordinator 讨论 | `design/<slug>.md` | Coordinator 用 `orchestrate-discovery/references/*` |
| 大 Issue 拆分 | Design 文档 | `issue-hierarchy/<slug>.md`（或 GitHub issues）| Coordinator 用 `orchestrate-discovery/references/*` |
| Plan Writing | Design 文档 + 该 issue | `plans/<slug>/<NNN>-<name>.md` | Plan Writer 用 `orchestrate-plan-writing/references/plan-writer-handbook.md`（新建）|
| Execution | 该 Plan 文档 | （以 plan 为唯一源）| Plan Executor 用 `orchestrate-execution/references/execution-worker-handbook.md`（新建）|
| Review | 待审 commits + 对应 plan 文档 | `reviews/<slug>/<gate>.md` | Codex Reviewer 用 `orchestrate-*/references/*-review-angles.md` |

**Coordinator 在 dispatch 时只填运行时变量 + 文档路径，不再传内容**。

## 待讨论 / 待补充

下列内容需要与用户进一步讨论后补充：

1. Worker handbook 应包含哪些固定章节？
2. Plan 文档 schema 是否需要补字段（如显式 "execution contract"）让其更自足？
3. 大 Issue 拆分是否生成独立文件 vs 写到 GitHub issues vs 一个 issue-hierarchy.md？
4. Review 角色 dispatch 是否同样可以走「只传 commit + plan 路径」？
5. Coordinator 必须保留的临场判断有哪些（路由、降级、失败兜底）？
6. 7 个 skill 的 dispatch prompt 现状调查 → 改善优先级排序

---

## 调查结果（两轮调查，最终结论：重新编排，不新增）

### 调查方法

- **第一轮**：7 个 sub-agent 从 dispatch 视角扫描每个 skill，识别 Coordinator 临场创作内容，初步提议 16 份新 handbook + 5 类新中介文档
- **用户反馈**：「不是要搞复杂，是重新编排，不要新增更多东西」
- **第二轮**：5 个 sub-agent 从全局视角深度挖掘，验证「现有 3 层架构已经能承担 99% 的复用职责」

**最终结论**：第一轮提案严重过度设计。真正需要新增的内容极少，绝大多数工作是「把粘贴改为引用、把重复合并、把规范沉到现有载体」。

### 现有 3 层复用架构（已经存在，被忽视）

| 层 | 数量 | 职责 | 文件示例 |
| --- | --- | --- | --- |
| `agents/*.md` | 8 | 角色 system prompt（行为规范）| pack-executor / plan-writer / code-explorer / root-cause-analyst |
| `build/templates/*.tmpl` | 12 | 跨 skill 复用的协议骨架（锚点编译时注入）| review-dispatch / control-envelope / disposition-table / repair-routing |
| `skills/*/references/*.md` | 53 | Phase-specific 方法论 + dispatch 模板 | execution-review-dispatch / plan-writing-methodology / final-review-angles |

**关键证据**：
- `review-dispatch.md.tmpl` 已经把 confidence rubric / pre-emit gate / 证据表 / bias indicators / compaction recovery 物理注入到 **11 个 review skill 文件**——这正是第一轮提议的"8 份 reviewer handbook"的核心内容，**已经存在**
- `plan-writing-methodology.md` (305 行) 已经是完整的 plan-writer handbook
- `final-review-angles.md` (320 行) 已经覆盖 baseline 1 + 2 的全部 review angles
- `merge-integration-review.md` (342 行) 已经是完整的 multi-PR integration review handbook
- `agents/pack-executor.md` 已经覆盖 95% 的 worker 行为规范

### 第一轮提案 vs 第二轮结论对照

| 第一轮提案 | 第二轮结论 |
| --- | --- |
| 新建 **16 份 handbook** | 真正需要**新建 0 份**；现有 reference + agents + templates 已覆盖 13/16，剩余 3 项是"补全"现有文件而非新建 |
| 新建 **5 类中介文档** | 真正需要**新建 1 类**（`merge-brief.md`，多 PR 合并合成模型无现成载体），其余 4 类全部能复用 |
| 16 份 handbook 涉及大量改造 | 真正改造是**删除 1000+ 行重复粘贴内容**，改为 Read 指针引用现有 reference |

### 真正的违反模式（第二轮重新识别）

**严重程度排序**：

1. **SKILL.md 内嵌 dispatch reference 全文**（最大头）
   - `orchestrate-execution/SKILL.md` 881 行中约 350 行（40%）是从 `execution-worker-dispatch.md` / `execution-review-dispatch.md` 复制
   - 修法：SKILL.md 只保留「流程位置 + Read references/X.md」指针，删除内嵌全文
   - 参考：`orchestrate-final-review/SKILL.md` 已经做到 238 行（lean 模式），证明可行

2. **11 个文件复制同一个 78 行 review-dispatch 块**
   - 通过 build template 注入是有意复制（保证一致），但这意味着 SKILL.md 已经物理包含了该块——agent 读 SKILL.md 时自然看到，handbook 重复 = **三重浪费**

3. **dispatch reference 强制 Coordinator 粘贴文档内容**
   - 最严重违反：`execution-worker-dispatch.md` 显式说"不让 worker 读 plan 文件"
   - `plan-writer-dispatch.md` 让 Coordinator 把 design 摘要 + issue 内容粘贴到 prompt，**同时**要求 plan-writer 自己 Read design
   - 修法：删除粘贴指令，dispatch 只传文档路径，Worker/plan-writer 自己 Read

4. **6 处 disposition 纪律重复 / 3+ 处 state-write 块重复**
   - 已被 build template 注入到多文件，但 Coordinator 还在 SKILL.md 中再写一遍
   - 修法：信任 template，删 SKILL.md 的副本

### 端到端 workflow 文档流转（验证可行性）

通过端到端分析，**Coordinator 真正必须临场创作的内容只有 6 项**，**全部集中在 Coordinator↔User 界面**（与 sub-agent dispatch 无关）：

1. 用户讨论对话（Discovery）— 业务决策，不能模板化
2. DISPATCH_ENVELOPE 运行时变量 — 是「填空」不是「创作」
3. Route 判定（Entry Gate）— 一次性业务判断
4. 每条 finding 的亲验结论（disposition evidence）— 现场证据
5. 业务汇报正文（Final Review）— 灰色地带，用户拍板**保留临场**
6. BLOCKED 报告 + Decision Brief — 用户界面结构化

**Sub-agent dispatch 的「创作型 prompt」理论上可全部消除**。这正是用户原意。

### 改造分类（重新定义）

#### A. 删除重复内容（最大工作量 = 最大收益）

| 操作 | 涉及范围 | 节省 |
| --- | --- | --- |
| SKILL.md 删除内嵌 dispatch reference 全文，改为「Read references/X.md」指针 | 7 个 SKILL.md，特别是 execution（~350 行 ↓）| ~600+ 行 |
| 删除 dispatch reference 中"Coordinator 必须粘贴"的指令，改为「dispatch 只传文档路径 + Read pointer」 | 全部 dispatch reference | 每 dispatch 节省 1-5k tokens |
| 移除手工同步注释 `TEMPLATE_DEPS`（codex-review/SKILL.md L8-9）| 1 处 | 消除一个反模式信号 |
| 删除孤儿 template `decision-brief.md.tmpl`（已被 preamble 吸收，0 文件引用）| 1 处 | 清理 |

#### B. 补字段到现有文档（无新增文档）

| 文档 | 补字段 | 服务下游 | 消除的临场内容 |
| --- | --- | --- | --- |
| `design/<slug>.md` | `## Review History`（baseline 通过记录 + 重点建议 + gotcha）| plan-writer / final-reviewer | Coordinator 临场粘贴的"Design Review 重点建议" |
| `design/<slug>.md` | `## Cross-Plan Contract Anchors`（前移自 `cross-plan-contract-map.md`）| plan-writer / reviewer | Contract anchors 粘贴 |
| `design/<slug>.md` | `## Business Summary Inputs`（每 plan 一段业务化描述）| final-reviewer | 让 reviewer 出业务汇报草稿；Coordinator 只做润色（不创作）|
| `issues/<slug>/NNN-*.md` | `## Design context refs`（指向 design.md 段落锚点）| plan-writer | Coordinator 临场提取"与本 issue 相关的设计要点" |
| `plans/<slug>/NNN-*.md` | `## Plan Review History`（同 design）| plan-executor / reviewer | review 上下文粘贴 |
| `plans/<slug>/NNN-*.md` | `## Pack Execution Manifest`（pack_id → goal/acceptance/verification 索引）| plan-executor | Pack Brief 大头粘贴 |
| `workflow-state.review_dispositions[]` schema | `plan_id`（可选）+ `coordinator_verified_evidence`（可选 string）| repair worker / re-reviewer | disposition payload 临场组织 |
| `execution-state.plans[N]` schema | `pack_summary`（pack-returns 聚合视图）| final-reviewer | Pack summary 表临场拼装 |

**核心**：所有"决策档案中介文档"需求都能通过补字段满足，**唯一例外**是 multi-PR 合并的合成模型。

#### C. 真正需要新增（最小集）

| 新增 | 类型 | 必要性 |
| --- | --- | --- |
| `merge-brief-<run_id>.md` | 中介文档 | 多 PR 合成模型无现成载体（Scope Contract 是范围非合成模型；单 PR design/plan 是局部视角；workflow-state 不存合成内容）|
| `pack-executor.md` 追加 Worker Loop 段（约 50 字） | agent 补段 | Plan-level 自治 Worker 的新行为：按 Dependencies 自走 Pack 循环 |
| `pack-executor.md` 追加 context 自监控段（约 50 字） | agent 补段 | 累积阈值 + `need-fresh-worker` 自报机制 |
| `review-dispatch.md.tmpl` 追加"targeted re-review 收窄 scope"段（约 80 字） | template 补段 | 让 targeted 流程也走单点维护 |

**总计真正新增**：1 个中介文档 + 3 段共约 180 字的现有文件补充。

#### D. 必须保留临场（运行时变量 + 用户界面）

完全不动。详见上文「Coordinator 真正必须临场创作的 6 项」。

### 灰色地带（用户已拍板）

1. **业务汇报谁写**：保留 Coordinator 临场判断的灵活性。Reviewer 出技术总结作为输入材料，Coordinator 翻译为业务语言——这是 Coordinator↔User 界面，不算 sub-agent dispatch。
2. **Worker 类型选择**：保留 Coordinator 临场判断的灵活性。Risk-based 选择不强制由 plan 字段决定。

### Skill 改造工作量重新评估（基于第二轮发现）

| Skill | 第一轮估算 | 第二轮估算 | 主要工作 |
| --- | --- | --- | --- |
| orchestrate-execution | 大 | 中 | SKILL.md 瘦身 + execution-worker-dispatch.md 反转（让 worker 读 plan）+ pack-executor.md 补 Worker Loop |
| orchestrate-plan-writing | 中 | 小 | plan-writer-dispatch.md 删粘贴段，prompt 缩到 ~300 token |
| orchestrate-final-review | 中 | 小 | SKILL.md 删内嵌 review prompt 全文，改 Read pointer；business report 字段补到 design |
| orchestrate-discovery | 小 | 小 | review prompt 中的「Read first 路径列表」改为引用现有 reference |
| orchestrate-multi-pr-merge | 中 | 中 | 新增 `merge-brief-<run_id>.md` 模板 + Step 2 强制写文件而非工作笔记 |
| orchestrate-workflow | 中 | 小 | Route 2/8a 的 return contract 沉到 agent 定义 |
| codex-review | 小 | 极小 | 删 TEMPLATE_DEPS 注释 + 改用 `cat references/review-dispatch.tmpl 注入内容` 模式 |

### 跨 skill 共同违反模式

#### 模式 1：「如何做」内联在 dispatch prompt
**100% 违反原则，所有 7 个 skill 都存在**。

Review angles / Return contract / Calibration / Pre-emit Verification Gate / 证据表 / Bias indicators / TDD 纪律 / Confidence rubric 都是**角色行为规范**，每次 dispatch 都重新写入 prompt。这些内容跟具体任务无关，跨任务完全一致，应该一次性沉到角色 handbook，由角色自己 Read。

**最极端的例子**：
- `codex-review/SKILL.md` 自带 `TEMPLATE_DEPS` 注释，承认自己手工维护与 `review-dispatch.tmpl` 的同步——这正是 Document-as-Context 反对的"副本漂移"
- `orchestrate-execution/references/execution-worker-dispatch.md` 显式说"不让 worker 读 plan 文件"，所以把 Pack Brief 全文粘贴——与原则**正面冲突**

#### 模式 2：上下文从文档复制粘贴到 prompt
**6 个 skill 存在**（codex-review 例外，没有上游文档）。

Coordinator 在 dispatch 时把 design / plan / issue 文档的内容**逐字段提取再粘贴**，而下游 agent 通常被告知"不要读原始文档"或者"独立读取"——两者并存导致**双重浪费**：
- Coordinator 花 token 提取粘贴
- 下游 agent 仍然要花 token 重新读（或更糟，被禁止读）

最常见违反：
- 设计摘要 / 合同 anchors / mockup specs / 风险表 / Acceptance criteria

#### 模式 3：临场决策没有落到 durable doc
**5 个 skill 存在**。

Coordinator 内部做了大量"决策性"判断（修复方向、风险评估、合并状态模型、disposition 结论），但**只存在工作笔记或 prompt 中**，没有 durable 文档。结果：
- compaction 后重建困难
- 下一个 dispatch 又要把决策粘贴一遍
- 用户回头看不到决策依据

具体缺失的中介文档：
- `bug-seed-<run_id>.md`（Bug Investigation 入口）
- `repair-brief-<run_id>.md`（Direct Repair 入口）
- `merge-brief-<run_id>.md`（Multi-PR Merge 必备，目前是工作笔记）
- `disposition-<run_id>-<plan>-<round>.json`（每轮 review 修复 payload）
- `review-brief-<timestamp>.md`（Ad-hoc review 入口）

### 三层分类（每个 dispatch 内容归一类）

#### A. 可前移到固定 reference（handbook 模式）
**100% 安全，零业务决策**。每个角色一份 handbook，包含所有"如何做"的规范。

需要新建的 reference 清单：

| Handbook | 服务的角色 | 吸收的内容 |
| --- | --- | --- |
| `execution-worker-handbook.md` | plan-executor / complex-plan-executor | Worker Loop / TDD / commit 规范 / scope drift 自检 / Return contract / Open Items 三标签 / Repair Mode / Context 自监控 |
| `plan-writer-handbook.md` | plan-writer | Out of scope / Return contract / Mockup 强制 / 方法论入口 / 自检流程 |
| `plan-impl-review-handbook.md` | codex-reviewer (execution) | 4 review angles / Calibration / Pre-emit Gate / 证据表 |
| `plan-review-handbook.md` | codex-reviewer (plan-writing) | 4 review angles (Issue Quality / Coverage / Compliance / Cross-Verification) |
| `design-content-review-handbook.md` | codex-reviewer (discovery baseline 1) | content review angles + calibration |
| `design-alignment-review-handbook.md` | codex-reviewer (discovery baseline 2) | project alignment angles |
| `final-review-baseline-1-handbook.md` | codex-reviewer (final-review B1) | Regression / Intent / Cross-Plan angles |
| `final-review-baseline-2-handbook.md` | codex-reviewer (final-review B2) | Code-Level Audit angles |
| `release-gate-handbook.md` | codex-reviewer (release gate) | Risk surface / blocker 定义 / Review focus |
| `codex-review-angles.md` | codex-reviewer (ad-hoc) | 4 通用 angles + rubric + verification gate |
| `multi-pr-explorer-protocol.md` | code-explorer / complex-code-explorer (merge) | 5 维冲突分析 + 严重程度 |
| `multi-pr-conflict-worker-protocol.md` | pack-executor (merge conflict repair) | Scope / Acceptance 通用 |
| `multi-pr-integration-review-protocol.md` | codex-reviewer (merge integration) | 7 review angles |
| `targeted-rereview-handbook.md` | 通用（所有 review skill 共享） | 收窄 scope 规则 / 受影响 angle |
| `explorer-handbook.md` | code-explorer / complex-code-explorer 通用 | Return contract / 调查方向规范 |
| `rca-handbook.md` | root-cause-analyst 通用 | Return contract / 调查方向规范 |

总计 **16 份 handbook**。其中部分可合并（如 explorer-handbook + rca-handbook 已部分存在）。

#### B. 可替换为文档路径引用
**安全，前提是下游 agent 被明确指示要 Read 路径**。

| 当前粘贴内容 | 应改为引用 |
| --- | --- |
| 设计文档摘要 / Goal / Architecture | design 文档路径 |
| Issue title / What to build / Small issues | issue 文档路径 |
| Pack Brief 全文 | plan 文档路径（Worker 自治后 worker 自己 Read）|
| Contract anchors | design / plan 内的「合同边界」段 |
| Mockup specs | plan 内的「Mockup specs」段 |
| Plan / Pack completion summary 表 | `execution-state-<run_id>.json`（reviewer 自跑 jq）|
| Aggregate diff | `git diff <start>..<end>` 命令（reviewer 自跑）|
| 「Read first」列表 | reference handbook 的「默认上下文」段 |

#### C. 需要新增「决策档案」中介文档
**架构性新增**，让 Coordinator 临场决策落到 durable doc。

| 新中介文档 | 触发场景 | 内容 |
| --- | --- | --- |
| `bug-seed-<run_id>.md` | Bug Investigation 入口 | 用户原话 / 重现 / 相关文件 / 已尝试 |
| `repair-brief-<run_id>.md` | Direct Repair 入口 | 偏差描述 / 修复 scope / Acceptance |
| `merge-brief-<run_id>.md` | Multi-PR Merge 入口 + 持续更新 | Big Picture / 合并后正确状态 / Conflict Findings / RCA / Resolution Log / Integration Review Pointers |
| `disposition-<run_id>-<plan>-<round>.json` | 每轮 review disposition 后 | accepted findings / Coordinator 亲验证据 / 修复方向 |
| `review-brief-<timestamp>.md` | Ad-hoc review 入口 | 审查对象 / REVIEW_CONTENT / 用户重点 |

#### D. 必须保留临场（真正的运行时变量）

| 字段 | 出现位置 | 原因 |
| --- | --- | --- |
| DISPATCH_ENVELOPE 全部字段 | 所有 dispatch | 协议本身 |
| `agent_id` | SendMessage 续派 | 来自 state |
| JOB_ID | Codex resume | 来自 baseline reviewer |
| `escalation_reason` / `original_agent_id` / `context_ref` | 升级派发 | 跨 agent 链路 |
| `disposition_refs` | 修复 / targeted re-review | 当轮 disposition 产物 |
| `gate` 名 / `repair_round` / `idempotency_key` | 所有 dispatch | 调度元数据 |
| Worker 类型选择（pack vs complex）| Pack 派发 | Risk-based 临场判断（虽可由 plan risk 字段决定，但需 Coordinator 兜底）|
| Risk surface 触发列表 | Release Gate | 来自当次 diff 扫描 |
| 业务汇报（待拍板谁写）| Final Review 收尾 | 当前由 Coordinator 临场创作（可改为 reviewer 出技术总结 + Coordinator 翻译）|

### 推荐改造顺序（基于第二轮发现，全部是「重新编排」）

**Phase 0：清理（最低风险）**
- 删除 codex-review/SKILL.md L8-9 的 `TEMPLATE_DEPS` 手工同步注释（反模式信号）
- 删除孤儿 `decision-brief.md.tmpl`

**Phase 1：补字段到现有文档（最小新增）**
- design 文档 schema 加 `## Review History` + `## Cross-Plan Contract Anchors` + `## Business Summary Inputs`
- issue 文档 schema 加 `## Design context refs`
- plan 文档 schema 加 `## Plan Review History` + `## Pack Execution Manifest`
- workflow-state.review_dispositions[] 加 `plan_id` + `coordinator_verified_evidence`（可选字段）
- execution-state.plans[N] 加 `pack_summary`

**Phase 2：SKILL.md 瘦身（最大收益的删除工作）**
- 每个 SKILL.md 删除内嵌的 dispatch reference 全文，改为「流程位置 + Read references/X.md」指针
- 重点：`orchestrate-execution/SKILL.md` 881 → 预期 ~250 行
- 参考样板：`orchestrate-final-review/SKILL.md` 已是 238 行 lean 模式

**Phase 3：dispatch reference 反转（核心原则落地）**
- `execution-worker-dispatch.md` 反转：从"Coordinator 粘贴 Pack Brief"改为"Worker 自读 plan 文件指定章节"
- `plan-writer-dispatch.md` 反转：从"Coordinator 粘贴 design 摘要 + issue 内容"改为"plan-writer 自读 design + issue 路径"
- 所有 review dispatch reference 类似反转：从"Coordinator 拼 Pack summary / contract anchors / mockup specs"改为"reviewer 自跑 jq + git diff，自读 plan/design"

**Phase 4：Worker Loop 落地（唯一真正新增的行为）**
- `pack-executor.md` 追加 Worker Loop 段（按 Dependencies 自走 Pack 循环）
- `pack-executor.md` 追加 context 自监控段（`need-fresh-worker` 自报机制）
- `validate-pack-dispatch.sh` → 校验 plan_id（Worker 自治模式）
- `agent-return-handler.sh` 解析 plan-level verdict + per-pack 状态映射

**Phase 5：multi-pr-merge 新增（唯一真新增文档）**
- 新建 `merge-brief-<run_id>.md` 模板（合成模型 / 合同地图 / 文件矩阵 / 冲突追加段 / 解决日志）
- `merge-preparation.md` Step 2 强制写文件而非工作笔记

**Phase 6：通用收尾**
- `review-dispatch.md.tmpl` 追加"targeted re-review 收窄 scope"段
- 验证测试 + verify-maturity 检查同步

### 关键洞察（最终版）

1. **「重新编排」是 99% 的工作**。第二轮分析证明：1000+ 行重复粘贴可通过"改 Read 指针"消除；16 份 handbook 提案中 0 份真正需要新建；5 类中介文档提案中 4 类能复用现有载体。
2. **现有 3 层复用架构已经够用**：agents/*.md（行为规范）+ build/templates/*.tmpl（协议骨架）+ skills/*/references/*.md（phase 方法论）。第一轮提议的"第 4 层 handbook"是误增。
3. **Reader 决定机制**：Coordinator/Skill 自己读的内容用 build template（注入 SKILL.md / agents.md，零运行时成本）；sub-agent 独立 context 读的内容用 runtime read reference。**不要混用产生冗余**。
4. **真正必须 Coordinator 临场创作的 6 项全部集中在 Coordinator↔User 界面**，与 sub-agent dispatch 无关。Sub-agent dispatch 的「创作型 prompt」理论上可全部消除。
5. **真正新增的代码工作**：1 个中介文档（merge-brief）+ 3 段补充（Worker Loop / context 自监控 / targeted scope 收窄）共约 200 字 + 7 处文档 schema 字段补全。其余全部是删除和引用替换。
6. **TEMPLATE_DEPS 手工同步注释是反模式自承认**。删掉它，信任 build template 是单点维护源。
7. **Plan-level Worker 自治是 Document-as-Context 的最大单点应用**，但不是孤立改造——所有 skill 都按同一原则收敛 dispatch。


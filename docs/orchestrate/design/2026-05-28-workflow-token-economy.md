# Workflow Token Economy 设计文档

> **Slug**：`2026-05-28-workflow-token-economy`
> **Run ID**：`2026-05-28-token-economy-45273`
> **Route**：Formal Orchestrate（Route 1）
> **Baseline**：v3.8.0（Plan-level Worker Autonomy 完成后）
> **设计目标**：在不动 Worker Loop / Document-as-Context 主线的前提下，对整个 plugin 进行系统级 token 减负 + 流畅度优化

---

## 1. 背景和问题

### 1.1 现状

上一轮 Plan-level Worker Autonomy 改造（v3.8.0）已经把执行阶段的 Pack-level 派发收敛为 Plan-level Worker 自治，把 35-55 次 Pack-level dispatch 压到 7-11 次。但 plugin 本身的 token 开销没有同步压缩，反而因为新增的辅助机制（doc-patch 系统 / Pack Manifest 三方对账 / merge-brief 状态机 / Worker Loop 5 步启动）变得更重。

通过 5 个并行调研（token 热点 / hook 阻断分层 / state.sh + scripts 真实使用率 / reference 跳跃路径 / 外部 skill 集成现状）+ 上一轮架构重写过程中的观察，得到一组可观测的事实：

| 维度 | 当前数字 | 痛点 |
|------|---------|-----|
| 最大 SKILL.md | orchestrate-execution **530 行 / 28507 chars** | 进入一次 Execution phase 单 SKILL.md 就 ≈7000 tokens |
| Phase 进入 baseline 加载 | final-review **84855 chars** / execution **83114 chars** | 进入一次 phase ≈21000 tokens 起步 |
| 单个 reference 最大 | `merge-integration-review.md` **358 行 / 23269 chars** | 单 reference ≈6000 tokens |
| Build 模板 review-dispatch 注入 | 11 个 .md 文件 × 79 行 = **869 行复制** | 同一段内容随各 phase SKILL.md 重复加载 |
| Build 模板 repair-routing 注入 | 9 个 .md 文件 × 42 行 = 378 行复制 | 同上 |
| Build 模板 disposition-table 注入 | 6 个 .md 文件 × 47 行 = 282 行复制 | 同上 |
| 孤儿 reference 文件 | 7 个文件 / **共 ~700 行无人引用** | plugin 装载时仍占体积 |
| state.sh 子命令 | 20 个顶层，其中 **3 个 0 生产调用** | dead code |
| scripts/lib 库 | 6 个，其中 **2 个 0 生产 source** | dead code |
| Reference 总数 | 50 个 `.md` reference 文件 | 24% 无顶部路标，含多层跳 |
| 4-7 路线 route-extensions | workflow 和 execution 各 4 份共 **8 个文件**，execution 副本是 DEPRECATED | 重复 |
| 外部 skill 内联 | `to-issues` 等 4 个外部 skill 完全 inline 到 references，共 **~650 行** | 应可外部调用 |

### 1.2 问题归纳

把这些事实归纳成五类问题：

**问题 A：同一内容在 6+ 个文档里复制粘贴**
Build 模板系统本意是 DRY，但实现成了"把同样的内容 inject 到 N 个文件里"——加载时还是要把 N 份重复内容读进 Coordinator 的上下文。`review-dispatch`（79 行）×11、`repair-routing`（42 行）×9、`disposition-table`（47 行）×6、`voice-directive` 各 variant 各一份在 6 个 SKILL.md。这违背了 DRY 的本意。

**问题 B：为了绕开自己设的规矩，造了一整套工具**
最典型是 doc-patch 系统：Worker 想给 plan 文档勾几个 checkbox，但被 `guard-doc-edit.sh` 拦住，于是发明了"Worker 写 `doc-patch.diff` → `guard-plan-doc-patch.sh` 验证 → `doc-patch-apply.sh` lib 等审查通过再 apply → Decision 6 描述时机"——一个 schema + 一条 hook + 一个 lib + 一个 decision。同类还有 Path A 修复路径（4 个状态字段 + 1 个 hook 检查 + 1 个独立 reference）、bug-seed-file（RCA 发现根因不直接回 Discovery，先造 seed file 再进）、`agent-context-check` state.sh 子命令（Worker 数自己的 Pack 数还要绕一圈）。

**问题 C：7 条路线本质是 1 条主线 + 几个开关**
Route 1（Formal）+ Route 2（Bug）+ Route 3（Multi-PR）是真正不同的流程。Routes 4-7（Hotfix/Quickfix/Spike/Maintenance）都是"Route 1 跳过某些 phase + budget 不限"，却被当作独立 route，配了独立 `route-extensions/` 目录（workflow 和 execution 各一份，共 8 个文件）+ 独立 budget 策略 + 独立 commit 格式。

**问题 D：Hook 缺少分层，把"提醒"做成了"硬阻断"**
用户阐明的设计意图：hook 是关键时刻的提醒和规范，不应过度死板。当前 13 条 hook 脚本里：
- 5 条是必要的硬墙（session-start / guard-doc-edit / guard-premature-push / enforce-plan-commit / track-execution-state pack ID 提取依赖的格式）
- 4 条是必要的记账（agent-return-handler / track-review-budget / track-execution-state / track-effort-budget）
- 4 条混杂了"该阻断"和"该提醒"的逻辑（validate-plan-dispatch / validate-multi-pr-dispatch / gate-codex-review）
- 多条因为服务于自挖坑的工具而存在（guard-plan-doc-patch 服务 doc-patch / 部分 validate-plan-dispatch 步骤服务 Path A）

**问题 E：渐进式加载做过头，agent 在文档间反复跳**
50 个 reference 文件、24% 缺顶部路标、若干 reference 内部又引用另一个 reference 形成 3 层跳。3 个 multi-pr handbook 是孤儿（没有任何 .md 引用它们）。`execution-worker-handbook.md` 在 SKILL.md 里被引用但文件实际不存在（实际文件是 `execution-worker-dispatch.md`，文件名 bug）。`route-extensions/` 在 workflow 和 execution 各存一份，execution 副本已经是 DEPRECATED 但没删。

### 1.3 用户阐述的设计原则（必须遵循）

用户在本次会话中明确阐述了 plugin 的设计原则，本次优化必须沿着这些原则走，不能背离：

1. **文档传递上下文 = 防压缩 + 可回顾审查**：design / issue / plan / merge-brief 是唯一的上下文媒介，Coordinator 在 compaction 后能从磁盘恢复
2. **Sub-agent 分担 Coordinator 上下文 + 提升专项输出质量**：把专项工作（写设计 / 写 plan / 写代码 / 调研根因）下放
3. **每阶段 Codex Review 防止下游偏离上游**：design / issue / plan / code 各有 Review
4. **Review 配额防止无限循环**：review budget = 3P + 12，硬封顶
5. **Schema / contract 减少 agent I/O 随机性 + 减少思考时间**：DISPATCH_ENVELOPE / plan-return / merge-brief 等都是为此
6. **模板 = 让 agent 不漏细节**：build template 注入的内容是行为契约
7. **运行时记录 = 对抗 compaction 进度丢失**：workflow-state / execution-state / pack-returns / plan-returns
8. **Hook = 关键时刻提醒和规范，不应过度死板造成意外断点**
9. **渐进式加载 vs 过度拆分**：renderless 加载好，但拆得太碎会让 agent 反复跳；每个文档要有"路标"指引进入和离开
10. **外部 skill 集成有三种模式**：(a) 作为外部 Skill 调用 (b) 内容 inline 到 plugin reference (c) 放到 sub-agent 定义里直接指导

这十条原则是衡量本次优化每个改动的标尺。

---

## 2. 目标结果

### 2.1 可观测目标

完成本轮优化后，达到以下可验证状态：

| 指标 | 当前 | 目标 |
|------|------|-----|
| `orchestrate-execution/SKILL.md` 行数 | 530 | ≤ 300 |
| `orchestrate-execution` phase 进入 baseline 加载（chars） | 83114 | ≤ 50000 |
| `orchestrate-final-review` phase 进入 baseline 加载（chars） | 84855 | ≤ 50000 |
| `orchestrate-multi-pr-merge` phase 进入 baseline 加载（chars） | 74557 | ≤ 50000 |
| Build 模板 inject 到 5+ 文件的锚点数 | 3（review-dispatch / repair-routing / disposition-table） | 0 — 改为引用 canonical reference |
| 单个 reference 最大行数 | 358 | ≤ 250 |
| 孤儿 reference（无任何 .md 引用） | 7 | 0 — 删除或被引用 |
| state.sh 0 生产调用的子命令 | 2（business-summary / plans；idempotency 调研误判已纠正为 4 处生产调用） | 0 — 删除（path-a-escalation / agent-context-check 因决策 3/6 一并删除） |
| scripts/lib 0 生产 source 的库 | 2 | 0 — 删除或合并 |
| route-extensions 副本目录数 | 2（workflow + execution） | 1（只在 workflow） |
| Route 枚举值 | 8（formal / bug-investigation / multi-pr-merge / hotfix / quickfix / spike / maintenance / direct-repair） | 4（保留 runtime 全称 formal / bug-investigation / multi-pr-merge / direct-repair） + phase_skip[] flags |
| Hook 脚本数 | 13 | ≤ 10 |
| Reference 无顶部路标数 | 8 / 50（16%） | 0 / N |
| 不变量：Worker Loop 6 段合同 | 保持 | 保持 |
| 不变量：Document-as-Context 主线 | 保持 | 保持 |
| 不变量：Codex Review 5 步派发协议 | 保持 | 保持 |

### 2.2 不可观测但必须保证的能力

- Coordinator 在 compaction 后能从 workflow-state + scope + 设计/计划/issue/merge-brief 完整恢复进度
- 每个 phase 之间通过 review 抓住下游偏离上游的风险
- Worker 能在一次 dispatch 中完整执行一个 Plan 的所有 Pack
- 长任务（≥ 30 Pack）能完整落地不漏 Pack

---

## 3. 用户场景

本任务是 plugin 自身的优化，"用户"是开发者（项目负责人）通过 plugin 调度 workflow。场景：

### 3.1 Happy Path

开发者发起一次中等规模的功能开发任务（≈ 5 Plan / 25 Pack）：
1. Coordinator 进 Discovery → 写设计文档 → Design Review pass
2. Coordinator 拆大 issue → 走 Plan Writing → 5 个 plan-writer 并行写 5 份 plan → Plan Review pass
3. Coordinator 进 Execution，逐 plan 派 Worker：
   - 每个 Worker 在一次 dispatch 内串行做完 5 Pack，写 plan-return.json
   - Coordinator 派 Plan Implementation Review，pass 后直接 Edit plan 文档勾选 checkbox（不再有 doc-patch 中间步骤）
4. 全部 Plan pass → Final Review → Closing

期望：整个流程 Coordinator 消耗 ≤ 上一轮同等任务的 65%。

### 3.2 Repair Path

Plan Implementation Review 报 needs_repair，Coordinator 验证 finding → 走 SendMessage Path B 给原 Worker（不再有 Path A 自修分叉）→ Worker 修完写 plan-return.json → targeted re-review。

期望：repair 路径状态字段减少 4 个（path_a_escalation / blocked_for_self_fix / 等），相关 hook 检查减少。

### 3.3 Compaction Recovery

会话在 Execution 中途 compact。Coordinator 恢复：
1. SessionStart hook 注入恢复规则
2. Coordinator 读 workflow-state 的 `cursor.phase` 和 `cursor.reference` 确定位置
3. Coordinator 读 scope + design + plan + execution-state 重建上下文
4. 从 cursor.step 继续

期望：恢复时读取的文档总量 ≤ 当前的 65%（因为各文档已瘦身、模板内容不再 6 处重复）。

### 3.4 Hotfix

紧急生产事故，用户喊"hotfix"：
1. Coordinator 不再走独立 Route 4，而是 Route 1 with `phase_skip: [discovery, plan-writing, final-review]` + `budget_status: unlimited`
2. 单 Pack 执行 + 单 review
3. 先 push 再事后 review（保留现有 pending_post_push_reviews 机制）

期望：route-extensions/route-4-hotfix.md 不再是独立文件，行为通过 Route 1 + flags 实现。

---

## 4. 方案设计

### 4.1 业务对象、角色和状态

**保持不变的对象 / 角色 / 状态**：
- `Coordinator` / `Worker` / `Plan-writer` / `Code-explorer` / `Root-cause-analyst` / `Docs-worker` 角色
- `Workflow phase` 枚举：discovery / plan-writing / execution / final-review / closed
- `Plan` / `Task Pack` / `Pack execution status` 五值（pending / in_progress / committed / blocked / skipped）
- DISPATCH_ENVELOPE 核心字段（protocol_version / run_id / phase / agent_role / repair_round / idempotency_key / plan_id / pack_id）
- Worker Loop 6 段合同（启动 / 循环 / verdict / repair / context / artifact）
- Plan-return / pack-returns / open-items / merge-brief schema 顶层结构

**简化的对象 / 状态**：
- `Route` 枚举从 8 值简化为 4 值（**保留 runtime 既有全称**：`formal` / `bug-investigation` / `multi-pr-merge` / `direct-repair`；不重命名为短名）+ flags（`phase_skip` 数组 + `budget_status` 已有）。删除 4 个：`hotfix` / `quickfix` / `spike` / `maintenance`，由 `phase_skip[] + budget_status` 实现
- `Path A escalation` 状态字段 + `blocked_for_self_fix` 字段 — 删除
- `bug_seed_path` 概念 — 删除（RCA findings 直接作为 Discovery 输入）
- `doc_patch_path` 字段（plan-return-v1.json）— 删除
- Worker `agent-context-check` 状态查询 — 改为 Worker 本地决策（不调 state.sh）

### 4.2 实现决策（核心改动 19 类）

> Round 2 决策分两批：
> - **决策 1-12**：v3.8.0 → token economy 基础重构（模板去重 / 死代码删除 / route 折叠 等）
> - **决策 13-19**：用户讨论 Discovery 环节后补充（删 targeted re-review / Explorer 集成 / grill-with-docs 升级 / 外部精华占位 / Discovery 压缩 / Sub-agent 事实校验 / **Mockup 生成留空间**）

> 这一节列出本轮改动的全部范畴。每一条都对应后续大 issue 拆分时的一个候选 vertical slice。具体实现细节由计划文档承担，本节只到决策层面。

#### 决策 1：模板系统去重——5 个高频 inject 锚点改为 canonical reference

**当前**：`review-dispatch` / `repair-routing` / `disposition-table` 通过 build template 注入到 11 / 9 / 6 个 .md 文件。每次加载文件都读一遍。

**改动**：
- 把 `review-dispatch.md.tmpl` / `repair-routing.md.tmpl` / `disposition-table.md.tmpl` 三个模板的内容**抽到独立 reference 文件**，位置统一为 **`plugin/skills/_shared/`**（plugin-rooted；**不**放在某个 phase 的 `references/_shared/` 下，避免跨 phase 相对路径解析问题）。完整路径见 §5.5。
- SKILL.md 和原本 inject 这些锚点的 reference 文件，改为在需要时**用 plugin-rooted 绝对路径 `Read plugin/skills/_shared/<name>.md`** 引用，不再 inject 内容；禁止使用相对路径（`_shared/...` / `../_shared/...`）。
- 修改 `build.sh`：保留锚点系统，但这 3 个模板不再 active；模板文件可以保留作为内容源（避免破坏向后兼容），但 BEGIN/END 注释从所有目标文件中移除。
- 保留 inject 模式的锚点：`worker-loop`（仅 2 个 agent，DRY 合理）/ `control-envelope`（3 个紧密耦合文件）/ `preamble` 和 `voice-directive`（每个 SKILL.md 自己的 persona，逻辑上是文件元数据不是共享内容）。

**收益估算**：减少 (11+9+6) × ~50 行平均 = ≈1300 行复制；每次进 phase 节省 ≈5-8k tokens。

#### 决策 2：删除死模板和孤儿文件

**模板清理（含同步 verify-maturity / build check）**：
- `forbidden-shortcuts.md.tmpl` + resolver — 当前 **2 个 active anchors**（orchestrate-execution/SKILL.md + orchestrate-final-review/SKILL.md）；先 **inline 到目标 SKILL.md**，再删除模板 + resolver + build check 同步
- `state-write.md.tmpl` + resolver — 单一目标使用（orchestrate-execution/SKILL.md），**inline 后删模板**
- `trust-boundary.md.tmpl` + resolver — 单一目标使用（orchestrate-execution/SKILL.md `[variant=worker]`），**inline 后删模板**
- `review-dispatch.content-only.md.tmpl` — **本轮不动**（§10 第 15 条明确不动 codex-review skill；该模板仅 codex-review/SKILL.md 1 处用，留作下轮）

**孤儿 reference 文件清理**：
- `multi-pr-conflict-worker-handbook.md` / `multi-pr-explorer-handbook.md` / `multi-pr-integration-review-handbook.md`（共 455 行 / 16721 chars）— **删除**（内容已被 merge-brief 覆盖；merge-brief 是唯一权威源）。**同步**：删除 `verify-maturity.sh` 中的 6.11 节 6 项 existence checks（3 个 -f 检查 + 3 个 Self-Read 检查）；改为验证 merge-brief / merge-* references 已覆盖各角色 Self-Read 内容
- `learnings-confidence-audit.md`（60 行）— **折回** orchestrate-execution/SKILL.md 的 Worker 返回处理段
- `learnings-trust-gate.md`（21 行）— **折回** 同上
- `path-a-re-review.md`（59 行）— **删除**（决策 3 删除 Path A）
- `execution-worker-handbook.md` 文件名 bug — SKILL.md 引用此文件但实际文件是 `execution-worker-dispatch.md`，**修正 SKILL.md 引用** 或在仓库中创建正确名称的文件

**目录清理**：
- 删除 `plugin/skills/orchestrate-execution/references/route-extensions/` 整个目录（4 个 DEPRECATED 副本），保留 workflow 一侧的 route-extensions/（但决策 10 会进一步折叠它）

**收益估算**：删除 ≈800-1000 行 + 模板系统 3 项（不再含 review-dispatch.content-only）

#### 决策 3：删除 Path A 自修分叉，所有修复走 Path B SendMessage

**当前**：审查发现问题后两条路径——Coordinator 自己改（Path A，限 ≤2 文件 + 置信 ≥7）/ 派 Worker（Path B）。Path A 加了 4 个状态字段 + 1 条 hook 检查 + 强制 targeted re-review + 自动升级。

**改动**：
- 删除 `state.sh path-a-escalation` 子命令 + 4 个状态字段（path_a_escalation / blocked_for_self_fix / path_a_count 等）
- 删除 `gate-codex-review.sh` 中 path-a-re-review 分支检查
- 删除 `path-a-re-review` review_intent 枚举值（dispatch-envelope-v1.json）
- 删除 `path-a-re-review.md` reference（决策 2 已包含）
- 删除 `disposition-table` 中的 `path-a` disposition 选项 — disposition 枚举从 10 个降到 9 个（accepted / rejected / suppress / **path-b** / needs-evidence / duplicate / out-of-scope / needs-evaluation / user-decision）
- 所有 repair → SendMessage 原 Worker
- 边角情况：单 Plan 已 closed / Worker 不可达时 → 新 dispatch（envelope 含 `resume_from_pack_id`），不是新增 Path 类型

**理由**：用户已表达 effort budget 加权计算（Decision 5）后，Worker 修一次 finding 的 effort 成本本就很低；省一次 dispatch 不值得 4 字段 + 1 hook + 1 reference 的复杂度。

#### 决策 4：删除 doc-patch 系统，Coordinator 直接 Edit plan checkbox

**当前**：Worker 写 `doc-patch.diff` 到 `plan-returns/<plan_id>/` → guard-plan-doc-patch hook 验证只勾 checkbox → Coordinator 在 Plan Implementation Review 通过后调用 `doc-patch-apply.sh` lib `git apply` 并 `git add`。

**改动**：
- 删除 `plugin/hooks/guard-plan-doc-patch.sh` 和 `hooks.json` 中对应条目
- 删除 `plugin/scripts/lib/doc-patch-apply.sh`
- 删除 `plan-return-v1.json` 中 `doc_patch_path` 字段（保留 `per_pack` — 已含足够信息）
- 删除 Decision 6 的"timing"决策（apply 时机）— 不再需要
- 修改 `agent-return-handler.sh`：verdict=pass 时不再暂存 doc-patch.diff；改为输出 NEXT 指令包含"Coordinator: Plan Implementation Review pass 后，Edit plan 文件勾选 per_pack[*].status=committed 的 Pack"
- Worker Loop 模板（worker-loop.md.tmpl）：删除"写 doc-patch.diff"步骤；plan-return.json 的 `per_pack` 字段是唯一权威信息源
- Coordinator 在 Plan Implementation Review pass 后用 Edit 工具勾选（直接 toggle `- [ ]` → `- [x]`），不通过 lib

**理由**：Worker 不能改 docs/ 仍然成立（guard-doc-edit.sh 保留），但 Coordinator 可以改——它本来就是 plan 文档的唯一作者方。doc-patch 这一整套系统是为绕开自己设的规矩造的，移除它对 Document-as-Context 主线无影响。

#### 决策 5：删除 bug-seed-file 中间文档，RCA findings 直接进 Discovery

**当前**：root-cause-analyst 返回 `root cause in design/plan` → Coordinator 创建 `bug-seed-<run_id>.md` 中间文档 → 更新 Scope Contract 加入此 seed → 以 seed 为种子进 Route 1。

**改动**：
- 删除 bug-seed-file 创建步骤
- RCA agent 返回 verdict=`root cause in design/plan` 时，其完整 findings 报告**直接作为 Discovery 的 Source artifact**（写到 scope.md 的 Source artifacts 段）
- 删除 architecture-draft §17（Bug Seed File）
- 删除 bug-investigation-route.md 中相关步骤
- 删除 scope contract 中可选的 `bug_seed_path` 字段（如有）

**理由**：RCA 报告本身已经足够结构化（Bug Investigation route 输出严格规范）；额外建一个中间文档是多此一举。

#### 决策 6：删除 state.sh `agent-context-check` 子命令，Worker 本地判断

**当前**：Worker 完成一个 Pack 后调用 `state.sh agent-context-check`，state.sh 读 execution-state JSON 返回 `need-fresh-worker` 或 `ok`。

**改动**：
- 删除 `state.sh agent-context-check` 子命令
- Worker Loop 模板更新：Worker 在内存里维护一个 `packs_in_session` 计数（每完 Pack +1），不再调 state.sh；判断逻辑就是 `if packs_in_session >= 5 and remaining >= 2: verdict = need-fresh-worker`
- 删除 18 个 state.sh agent-context-check 的引用方调用代码（多数在 worker-loop.md.tmpl 内）

**理由**：Worker 自己手上就有 packs_in_session 信息（每完一个 Pack 自增），绕一圈 state.sh 没有意义。

#### 决策 7：删除 state.sh 死命令 + scripts/lib 清理

**state.sh 死子命令（已亲验 0 生产调用）**：
- `business-summary` — 0 生产调用，**删除子命令**
- `plans` — 0 生产调用（仅在 hook 错误消息字符串中提及，非真实调用），**删除子命令**

**注意：idempotency 子命令保留不动**：调研误判为 0 调用，实际有 4 处生产调用方（`validate-route-worker-dispatch.sh` / `record-route-worker-dispatch.sh` / `validate-plan-dispatch.sh` / state.sh init 字段维护）。Codex Content Review C1 + Alignment Review C2 已纠正。**保留 `state.sh idempotency check/append`**。

**scripts/lib 清理（按用户 D3 确认）**：
- `review-effectiveness.sh` — 0 生产 source，**删除 lib 文件**。**同步删除 `workflow-state-v1.json` 中 `review_effectiveness` 字段**（schema required 列移除 + properties 段移除）；同步删除 `state.sh init` 中该字段的初始化（state.sh 第 ~170 行）+ tests 中相关 fixture + verify-maturity 中对该 lib 存在性的检查。**Consumer 引用清理**（grep `review_effectiveness` / `review-effectiveness` 全仓库）：包括但不限于 `scripts/lib/learnings-confidence-audit.sh` 中读取该字段的代码、`scripts/run-summary.sh` 中聚合该字段的代码、任何 SKILL.md / reference 中提及该字段的描述、architecture-draft.md 中的相关章节
- `learnings-jsonl.sh` + `learnings-poison-detector.sh` — 合并成一个脚本（`learnings-jsonl.sh` 内联 poison detector 调用，poison-detector 作为 function 而非独立脚本）

#### 决策 8：合并 review-dispatch / route-worker-dispatch 重复脚本对

**当前**：
- `record-review-dispatch.sh` + `validate-review-dispatch.sh` 总是成对出现于同一 skills（≈13-15 处引用）
- `record-route-worker-dispatch.sh` + `validate-route-worker-dispatch.sh` 同模式（≈11 处引用）

**改动**：
- 合并为 `dispatch-review.sh`，子命令 `validate` / `record` 二合一
- 合并为 `dispatch-route-worker.sh`，同模式
- 修改所有 skills / build / templates 引用方（详见 §5.8 scripts CLI 合同变化）
- 兼容策略：保留旧 4 个脚本作为 shim（内部转发到新合并脚本），允许渐进迁移（每个 SKILL.md / reference / build template 在自己的 Pack 内迁移）。所有 producer 迁移完成 + 一轮 Plan Implementation Review 通过后再删除 shim

**理由**：每次派发 review 或 route worker 总是先 validate 再 record；分两脚本意味着每次至少调两次 bash，合一减半。

**注意**：本决策对应的合同变化（旧脚本名 → 新脚本名 + subcommand）已列入 §5.8。Codex Content Review C4 提示必须在 §5 闭合 scripts CLI 合同，否则 Pack 拆分会遗漏 producer/consumer。

#### 决策 9：Hook 行为降级（阻断 → WARN，已收窄至 1 项）

经过 Codex Alignment Review C4 + C5 的纠正，**multi-pr-dispatch (b)(d)** 和 **gate-codex-review --resume** 三处**不能降级**——它们是 Document-as-Context 单一权威源和 targeted re-review durability/registry 合同的硬保护。本轮只降级 1 项：

| Hook | 检查 | 当前 | 改为 |
|------|------|------|------|
| validate-plan-dispatch.sh | Step 6: Manifest 缺失 | exit 2 | WARN（Worker 可从 plan 正文工作） |
| validate-plan-dispatch.sh | Step 8: Path A 检查 | exit 2 | 删除（决策 3 已删 Path A） |
| validate-multi-pr-dispatch.sh | (b): repair_round≥1 + stage=init | exit 2 | **保持 exit 2**（Alignment Review C5：repair 不能在 init 状态执行，会污染 merge-brief resolution log） |
| validate-multi-pr-dispatch.sh | (d): prompt 含 merge-brief 路径字符串 | exit 2 | **保持 exit 2**（Alignment Review C5：缺路径会让 agent 走 paste-content anti-pattern，破坏 Document-as-Context 单一权威源 + compaction 恢复） |
| gate-codex-review.sh | targeted-re-review 必须 `--resume` | exit 2 | **整段删除**（决策 13：targeted re-review 机制全局删除，--resume 检查无意义） |

**保留 exit 2 的检查**（不动）：
- session-start.sh 全部
- enforce-plan-commit.sh（track-execution-state 依赖此格式）
- validate-plan-dispatch.sh 的幂等 / budget 已初始化 / Direction Check pending / plan_path 存在 / execution-state 注册 / plan 未占用 / Pack 状态 / disposition refs evidence
- validate-pack-manifest.sh 全部三方对账（A≠B / stray_C 都是真错误）
- validate-multi-pr-dispatch.sh (a)(c)（文件存在 + conflict_id 状态）
- guard-doc-edit.sh（Worker 不能改 docs/ 是核心硬墙）
- gate-codex-review.sh uncommitted packs 检查
- guard-premature-push.sh

#### 决策 10：Routes 4-7 折叠为 Route 1 + flags

**当前**：8 个 Route 枚举值 + workflow 和 execution 各 4 份 route-extensions 文件

**改动**：
- `workflow-state-v1.json` 的 `route` 枚举从 8 值收敛为 4 值：**保留 runtime 既有全称** `formal` / `bug-investigation` / `multi-pr-merge` / `direct-repair`（不重命名为短名 — 避免对 state.sh / hooks / tests / skills 中已存在的字符串引用造成跨模块迁移）。删除 4 个：`hotfix` / `quickfix` / `spike` / `maintenance`
- 新增字段 `phase_skip`（array of phase enum，默认空数组）
- `budget_status` 已有，复用：`initialized` / `unlimited` / `pending_plan_count`
- 新增字段 `commit_format_override`（string \| null，默认 null；hotfix 时设为 `"hotfix-unreviewed"`）
- `orchestrate-workflow/SKILL.md` 的 Entry Gate 入口判定关键词路由：识别到"hotfix"/"quickfix"/"spike"/"maintenance"关键词 → 还是 Route 1，但同时设置对应的 `phase_skip` + `budget_status: unlimited`
- 删除 `orchestrate-workflow/references/route-extensions/` 中 4 个文件，把每个文件的核心规则（≈20-30 行/文件）整合为 SKILL.md 中一个统一的"Route 1 Variant Table"小节（≈80-120 行）
- 删除 `orchestrate-execution/references/route-extensions/` 整个目录（已是 DEPRECATED 副本）
- Hotfix 的 `pending_post_push_reviews` 机制保留（这是真正特殊的状态字段）

**收益估算**：减少 8 个文件 + ≈600 行，且 entry routing 逻辑统一在 SKILL.md 一处。

#### 决策 11：外部 Skill 集成对齐 + agent frontmatter 瘦身

**外部 Skill 调用规范化**：用户列出的外部参考（grill-with-docs / brainstorming / to-PRD / to-issue / Writing Plans / TDD）当前几乎全部 inline 到了 plugin 的 reference 文件。本次保持基本 inline 模式（因为这些 inline 内容已经经过 plugin 上下文裁剪），但做以下对齐：
- `orchestrate-discovery/SKILL.md` 的 Steps 3-6 段落显式加入 `Skill({ skill: "grill-with-docs" })` 调用指令（当前只在文末"外部 Skill"汇总段提及"全程使用"）
- `discovery-discussion.md` 第 80 行的描述文字改为可执行的 `Skill()` 调用引导
- 不引入对 `to-issues` / `to-PRD` skill 的外部调用（避免依赖外部 plugin 状态；当前 inline 经过裁剪已足够）

**Sub-agent frontmatter 瘦身**：
- `docs-worker.md` frontmatter `skills: grill-with-docs` — **移除**，改为 body 按需 `Skill({ skill: "grill-with-docs" })` 调用（很多 docs-worker 任务是机械整理，不需要 grill）
- `plan-writer.md` frontmatter `skills: improve-codebase-architecture` — **移除**，改为 body 在 Step 3d 按需调用（不是每个 plan 都涉及架构）
- 保留：`pack-executor` / `complex-pack-executor` 的 `tdd`、`root-cause-analyst` 的 `diagnose, tdd`（这些每次都用得到）

#### 决策 12：Reference 跳跃精简 + 路标补齐

**消除多层跳**：
- `execution-completion.md` 内部对 `execution-release-gate.md` 和 `execution-repair-truncation.md` 的引用 — 改为 SKILL.md 中"Step 13/14"直接列出条件分支，不在 reference 中嵌套引用
- `final-review-completion.md` 内部对 `final-review-release-gate.md` 的引用 — 同处理
- `merge-rca-investigation.md` Self-Read Protocol Step 4 对 `rca-pr-conflict-methodology.md` 的跳 — 把方法论正文折回 `merge-rca-investigation.md` 作为 `## 方法论` 章节

**补全路标**（执行时先 grep 顶部缺路标的全部 reference，下列为已知样本，**完整清单由 Pack 执行时枚举**）：
- `merge-brief-template.md`：补顶部 `> 使用场景 + 完成后回到` blockquote
- `learnings-trust-gate.md`（如保留为独立 reference）：补顶部 `> 流程位置`（如折回 SKILL.md 则不需要 — 决策 2 已处理）
- 注意：`route-6-spike.md` / `route-4-hotfix.md` / `route-5-quickfix.md` / `route-7-maintenance.md` 由决策 10 整体删除并折叠回 SKILL.md，不在此处补路标

**Verify-maturity 加检查**：所有 `plugin/skills/*/references/*.md`（除 `_shared/`）顶部 5 行内必须含 `> 流程位置` / `> 使用场景` / `> 完成后回到` 任一路标 blockquote，无则报错

#### 决策 13：删除 Targeted Re-review 机制（全局 / 最高优先级）

**当前**：Codex Review 体系含两类 review intent：
- `baseline`：首轮全量审查
- `targeted-re-review`：Coordinator 修复后再请 reviewer 对 specific finding 复核闭合

`targeted-re-review` 是 plugin 自身最大的 token 漏洞——每次小修复都触发一次 reviewer 重启（即使带 `--resume`，prompt + 工作树读取仍是新 round 的开销），review budget `3P + 12` 中的 `+12` 主要给 targeted re-review 用。

**改动**：**全局删除 targeted re-review 机制**。每个产出（design / plan / pack / final / multi-pr）只走一轮 review + 一轮修复，封顶。

- **review_intent enum**（dispatch-envelope-v1.json）：从 `baseline / targeted-re-review` 收敛为 `baseline` 单值（或直接删除 review_intent 字段）
- **gate-codex-review.sh**：删除 `targeted-re-review` 分支全部代码（约 20 行）+ `--resume` 强制检查 + `exception_code` 强制检查
- **parse-envelope.sh**：删除 review_intent 枚举约束 + targeted-re-review 必须含 exception_code 的 validation
- **review-dispatch.md.tmpl**：删除 `[variant=targeted-re-review]` 子模板及对应 resolver 入参
- **validate-review-dispatch.sh / record-review-dispatch.sh**（合并后 `dispatch-review.sh`）：删除 targeted re-review 的 agent_id 匹配 / baseline JOB_ID 复用 / disposition_refs 必填 等逻辑
- **workflow-state-v1.json**：删除 `self_verifications` 数组中 targeted-re-review 相关字段（exception / exception_code）；保留 `disposition_refs` 作为 Coordinator 自验的可选证据
- **all SKILL.md / references**：grep 删除所有"targeted re-review" / "targeted-re-review" 描述（架构 / Hook / dispatch 模板 / 流程图 全清）
- **architecture-draft.md**：删除 §11.4 targeted re-review 章节 + §13 review intent 表中对应行 + 任何流程图中的 targeted re-review 分支
- **review budget 公式**：`3P + 12` → **`2P + 6`** 或 `1.5P + 6`（具体由 plan 阶段实测决定）。`+6` 仅保留给 Discovery / Plan-writing / Final / Multi-PR 各 1 次 baseline review
- **修复后处置**：每次 baseline review → Coordinator 验证 findings → Worker 修复 → **不再 review 闭合**。改为：
  - Coordinator 自验闭合（用 grep + Read 验证修复点已落地）
  - 留作 disposition 痕迹写入 workflow-state.review_dispositions 即可
  - 若 Coordinator 自验仍有疑虑 → 升级 BLOCKED 报告用户，由用户决定是否人工请 Codex 再审；不在自动流程内
- **修复仍失败的极端情况**：进入 `root-cause-analyst` 调查路径（已有），不再走 targeted re-review

**理由**：用户明确指出 — 产出 review 一次 + 修复一次封顶就够。targeted re-review 在 baseline review 已给出 evidence locator 的前提下，本身是 redundancy；Coordinator 验证 finding + Worker 修复 + Coordinator 自验是更便宜的闭合方式。该机制是 plugin 自身最大的 token 漏洞之一。

**收益估算**：每个 phase review 平均省 1-2 次 targeted re-review × ≈10k tokens / 次 = 节省 **≈20-40k tokens / phase**；review budget 总量约减 50%。

**注意**：决策 9 中关于 `gate-codex-review.sh --resume` "保持 exit 2" 在本决策落地后**自动作废**（targeted-re-review 不复存在，无 `--resume` 强制约束）。决策 9 / §5.6 / §7.1 verify-maturity 需要同步更新——这部分由 plan-writing 时一次性处理。

#### 决策 14：Discovery 阶段 Explorer agent 并行派发集成（与 Plan-writing 对称）

**当前**：调研 A 确认 — orchestrate-discovery/SKILL.md **零次** `Agent({ code-explorer })` 调用；Coordinator 在 Steps 1-2 自己读 CLAUDE.md / SPEC / ADR / CONTEXT.md / commits，承担全部仓库探索上下文压力。code-explorer / complex-code-explorer 仅在 design-review-angles.md L274 / L295 作为 Review 补证用，**主流程未利用**。Plan Writing 阶段并行派 plan-writer，Discovery 阶段无对称机制。

**改动**：
- **orchestrate-discovery/SKILL.md Steps 1-2 重写**：把"Coordinator 自己读"改为"Coordinator 判断范围后**并行派 N 个 Explorer**"：
  - 窄范围（单模块 / 单文件链）→ `code-explorer`
  - 多模块 / 历史行为 / 架构摩擦 → `complex-code-explorer`
  - 已知根因不清且涉及 bug → `root-cause-analyst`
- **派发模式**：模糊设计意图触发**多 Explorer 并行**调研（5 个并行是常见模式，如本次 Round 2 Discovery 自身已使用过）
- **Coordinator 职责收窄**：Coordinator 主要读 sub-agent 返回的浓缩报告 + 与用户讨论；不主动 grep 大范围仓库
- **派发清单**写入 SKILL.md 主流程（不是 references / 附录），与 plan-writing 的并行派发对称
- **删除 SKILL.md 中"Coordinator 自己读 CLAUDE.md / SPEC / ADR / CONTEXT.md / agents.overrides.md / 近期 commits"措辞**，改为"按需派 Explorer 调研，Coordinator 仅读 Explorer 返回的浓缩报告 + 用户原话"

**收益估算**：Coordinator 在 Discovery 阶段消耗减半（不再读大量原始代码 / 文件），上下文密度大幅提高。

**对齐**：本决策让 Discovery 与 Plan-writing 在 sub-agent 派发密度上对称——这是用户明确的设计意图（充分利用自定义 sub-agent 代替 Claude Code 内置 general-purpose agent）。

#### 决策 15：grill-with-docs 提升为 Discovery 主流程同步入口，CONTEXT.md 与 Design 同等地位

**当前**：调研 B 确认 — grill-with-docs 在 SKILL.md 仅出现 1 次（L134"外部 Skill"汇总段，标注"全程使用"）；discovery-discussion.md L80 称其为"Domain Alignment 核心执行方式"，**但 SKILL.md 主流程 Steps 3-6 / 7-9 未显式 surface**。CONTEXT.md 在 Step 1-2 只是"读"输入；**无"设计文档落笔前 CONTEXT.md 已就绪"门控**；无"第一轮对话前同步启动 grill-with-docs"指引。

**改动**：
- **orchestrate-discovery/SKILL.md Step 0 新增**（在 Steps 1-2 之前）："**Step 0：同步启动 grill-with-docs**。在第一轮用户对话前调用 `Skill({ skill: "grill-with-docs" })`，由该 skill 全程负责 CONTEXT.md 维护。CONTEXT.md 与 design document 是 Discovery 阶段的**双交付物**，地位等同。"
- **CONTEXT.md 路径写入 Scope Contract** 作为 Discovery 权威文档之一（与 design path 并列）
- **discovery-design-document.md Step 7（写设计文档前）增加门控**：grep 设计文档草稿中所有术语，必须在 CONTEXT.md 中有定义；缺失术语先回 grill-with-docs 补齐再继续
- **CONTEXT.md schema**：术语表 + 对象关系 + 角色 + 状态四段（已有，强化）。新增"Discovery 完成时 CONTEXT.md 必须包含本次设计涉及的所有领域术语"硬约束
- **删除 discovery-discussion.md L80 单独的"grill-with-docs 的角色"段**（200 chars 与 SKILL.md L134 重叠，移到 SKILL.md Step 0）
- **architecture-draft.md Document-as-Context 主线段同步**：把 CONTEXT.md 提升为与 design / issue / plan / merge-brief 同级的"领域级权威文档"，明确"CONTEXT.md 跨多次 Discovery 累积，design 是单次 Discovery 产出"

**收益估算**：设计文档术语一致性硬保证；下游 plan / pack 不再因术语漂移产生隐性 review finding。

#### 决策 16：Discovery 外部精华轻量引入（3 条，零/负 token 增量）

经过"是否加重流程/token"的逐条评估，从 10 条候选中筛选出 3 条**不明显加重流程和 token**的精华引入：

**1. to-PRD synthesize fast-path（减负型 — token 净负增量）**：
- `orchestrate-discovery/SKILL.md` Step 1-2 增加一句：
  > 若用户传入的 PRD / issue / 完整上下文已覆盖 Problem / Solution / Acceptance，跳过 Steps 3-6 一问一答 fast-path，直接进入 Steps 7-9 起草设计文档，最后让用户审稿。
- 收益：上下文足够的场景省一整轮多回合追问

**2. prototype-snippet 例外类型列出（措辞精确化 — 加几个字）**：
- `discovery-design-document.md` L29 现有"不写具体 file path 或 code snippet（prototype snippet 例外）"补一句：
  > 例外类型仅限：state machine / reducer / schema / type shape。
- 收益：防止 design 文档被滥用嵌入大段实现代码

**3. Push twice 规则（一句话规则进 voice-directive）**：
- `build/templates/voice-directive.md.tmpl` Anti-Sycophancy 段增加一行：
  > Push twice：第一个回答默认是抛光过的，至少追问一轮才相信。
- 收益：与现有"立场+证据+质疑最强版本"互补；暴露用户初次回应中的妥协式回答

---

**不引入的 7 条**（理由列在表中，记录决策痕迹）：

| 候选 | 不引入理由 |
|------|----------|
| Brainstorming Visual Companion 独立消息协议 | 已被决策 19 覆盖（用户主动驱动 mockup）|
| to-PRD Deep modules sketch 显式 Step | 加上游 token 流程过重；决策 14 Explorer 并行调研已隐含承担"模块边界探查" |
| office-hours Forcing Questions 三问锚点 | 用户判断不引入——增量虽轻（≈3 行）但属于"业务直觉"层，不应硬编码在 plugin 流程文本里 |
| office-hours Premises 显式 gate | 与"分段呈现，每段确认"重叠（每段开头就是 premise）|
| GSTack Alternatives 三档结构化 + 五字段 | 当前"2-3 方案对比 + 推荐 + YAGNI"已覆盖核心；强制三档是过度规范化 |
| plan-ceo-review 10-star / Scope Modes | 不属 Discovery 范畴 |
| autoplan Dual-Voice / 自动流水线 | 与本地 review budget + phase skill 显式编排架构冲突 |

---

**复查现有提示词的已吸收精华**（结合亲验 grep，本节无需动作）：

| 已吸收精华 | 本地位置 | 来源 |
|---|---|---|
| Hard Gate "每项目都走 Discovery" | `orchestrate-discovery/SKILL.md:31` | Brainstorming |
| Anti-Sycophancy 立场+证据+质疑最强版本 | `build/templates/voice-directive.md.tmpl:81-83` | office-hours |
| 2-3 方案对比 + 推荐 + YAGNI | `discovery-discussion.md:50-52` | Brainstorming + GSTack |
| Spec Self-Review 四查 | `discovery-design-document.md:92, 105` | Brainstorming |
| Vertical Slice + AFK/HITL + AFK 优先 | `issue-splitting.md:21-31` | to-issues |
| 不写 file path（prototype 例外）| `discovery-design-document.md:29` | to-PRD |
| 一问一答 + 多选 + 推荐 | `discovery-discussion.md:9-16` | Brainstorming |
| 按输入类型澄清维度（更细于 GSTack）| `discovery-discussion.md:20-49` | 本地原创 |
| "先读代码再问问题"（精神层） | 决策 14 Explorer 并行调研隐含 | spec |

**结论**：现有提示词已较完整吸收外部精华；本决策只补 4 条且都是轻量增量。决策 16 本身落地后，Discovery 阶段对外部精华的吸收度从"已较完整"提升至"完整且与本地架构一致"。

#### 决策 17：Discovery 文档压缩（在保留所有精华前提下）

调研 E 给出具体压缩清单，本决策落地：

**死内容删除**（已用户亲验 — sub-agent 误判已剔除）：
- 删除 `design-review-angles.md` L5-13 `Self-Read Protocol` 段 — 该段写"你是 codex-reviewer"，但 Coordinator 读此文件时是派发者不是 reviewer；reviewer 角色由 Coordinator 写出的 review prompt 自己声明 — 省 614 chars
- 删除 SKILL.md L37 `Route Dispatch` 行（preamble T2 内的错位内容，Discovery 是 route 终点非 router）— 省 60 chars
- 删除 discovery-discussion.md L80 "grill-with-docs 的角色"段（已被决策 15 移到 SKILL.md Step 0）— 省 200 chars

**Sub-agent 误判已纠正（不动）**：
- `discovery-formats.md` — **保留**。它有两处指针引用（`architecture-draft.md:284` reference 清单 + `SKILL.md:104` 按需读指针），是有效的"指针式渐进加载"，不是孤儿。Sub-agent 把"无 `**Read**` 强制指令"等同于"未加载"，这是错误推论。本文件按需读模式是合理的——CONTEXT.md / ADR 格式不是每次 Discovery 都用得到。
- `zoom-out` skill — **保留引用**。实际位于 `/Users/cheuklapchan/.claude/skills/zoom-out`（mattpocock-skills 软链）。Sub-agent 只 grep 了 plugin 内而未查用户 skills 目录，误判为"不存在"。

**结构优化**：
- 合并 issue-splitting.md 中两套 issue body 模板（本地大 issue 文件 + GitHub Issue body）为一套 — 本地文件 = GH body + `## Design context refs` + `## Small issues` 两节
- design-review-angles.md：`Coordinator 端最小职责` 段上移至 review-dispatch 块内（L19 前），逻辑顺序优化

**GitHub Issue 发布改为可选**（流程减负）：
- 当前 issue-splitting.md Step 12f 强制为每个大 issue 发布 GitHub Issue
- **改为按需发布**：默认跳过；用户在 Discovery 时明确说"需要发布 GH Issue"才走这一步
- **本地大 issue 文件永远写入**（不可选）— Document-as-Context 单一源不动
- 若用户未要求发布但项目有团队协作需要，用户可手动 `gh issue create` 或事后追加
- 理由：plugin 主要使用场景是个人项目，GH Issue 在当前场景下无真实功能价值（本地 issue 文件 + workflow-state 已覆盖跟踪 / 依赖 / Blocked by）；保留能力但不强制，与决策 13（删 targeted re-review = 留能力降默认）一致的设计哲学

**保留**：
- review-dispatch / disposition-table 模板注入（决策 1 已处理 — 改为 canonical reference）
- discovery-discussion.md / discovery-design-document.md / issue-splitting.md 三个核心 reference（这些是外部 skill 精华的本地化版本，是真正不可减的内容）

**收益估算**：Discovery phase baseline 加载从 ≈38,453 chars 降至 ≈32,000 chars（≈17% 减），与决策 1 / 2 叠加后 ≤30,000 chars。

#### 决策 18：Sub-agent 返回事实校验机制（横切 / 写入 plugin）

**背景**：当前 plugin 没有 "Coordinator 必须验证 sub-agent 返回事实" 的硬规则——只有用户全局 `~/.claude/CLAUDE.md` 里有「子代理返回的任何事实声明（数字、文件路径、行号、计数、'存在/不存在'），在写入交付物或汇报给用户之前，必须亲自用 Read/grep/curl 验证」。但 plugin 自身的 SKILL.md / agent definition / hook 没有任何对应约束。

**问题**：决策 14 让 Coordinator 在 Discovery 阶段并行派 N 个 Explorer 收集仓库事实。如果 Coordinator 不验证就直接写进设计文档，**单个 Explorer 误判 = 设计文档错误结论**。本次 Round 2 Discovery 中已经出现 2 个真实案例：
- Explorer 报告"`zoom-out` skill 不存在"——实际在 `/Users/cheuklapchan/.claude/skills/zoom-out`（mattpocock-skills 软链）。Explorer 只 grep plugin/ 内没查用户 skills 目录
- Explorer 报告"`discovery-formats.md` 是孤儿"——实际被 architecture-draft.md:284 + SKILL.md:104 引用。Explorer 把"无 `**Read**` 强制指令"等同"未加载"

这两条都被采信并写进了设计文档，直到用户指正才被发现。

**改动（横切 — 写入 plugin 强制层）**：
- **agents/*.md frontmatter description**：所有调研类 sub-agent（code-explorer / complex-code-explorer / root-cause-analyst）必须在 description 中明确：返回的事实声明（行号 / 计数 / 存在性 / 引用关系）由 Coordinator **必须亲验**，sub-agent 自身不承担 ground truth 责任
- **orchestrate-discovery/SKILL.md 新增 Step 1.5（在 Step 1-2 派 Explorer 之后，Step 3 与用户讨论之前）**：
  ```
  **Step 1.5：Explorer 报告校验门控**
  对每个 Explorer 返回的报告：
  1. 高置信度声明（confidence ≥7）：抽样验 — 至少 grep 1 个关键事实
  2. 中低置信度（≤6）或"存在性 / 不存在性"声明：逐条 grep / Read 验
  3. 跨用户 skills / 跨外部仓库 / 跨主仓库 的事实：必须二次验（Explorer 默认只读 plugin/，会漏外部）
  4. 任何验证失败 → 该声明从设计文档输入中剔除，重派 Explorer 或 Coordinator 亲查
  ```
- **orchestrate-plan-writing / orchestrate-execution / orchestrate-multi-pr-merge SKILL.md 同步加 Step**：plan-writer / pack-executor / root-cause-analyst 返回的事实声明（pack 状态、文件路径、行号、grep 结果）也必须 Coordinator 抽验
- **agent-return-handler.sh hook 增强**：sub-agent 返回报告时，在 Coordinator NEXT 指令中明确生成一行"⚠️ 写入交付物前必须校验本次返回的事实声明"提醒
- **architecture-draft.md 新增章节**：「Sub-agent 信任边界」——明确 Coordinator 是事实的唯一 ground truth，sub-agent 是劳动力不是信源

**与决策 14 的关系**：决策 14 让 Discovery 充分使用 Explorer 分担上下文压力；决策 18 是配套的"信任边界"——派得多必须验得严，否则上下文压力虽然分担了，但 Coordinator 的结论质量没保证。

**收益估算**：避免"sub-agent 误判 → 设计文档错 → 下游 plan/pack 全错"的连锁失败。Coordinator 校验本身消耗很小（grep / Read 几次），但救一次大错节省的成本巨大。

**注意**：决策 18 不引入新的 Hook 阻断（保持决策 9 hook 简化方向）；只在 SKILL.md / agent description / agent-return-handler 输出层加提醒。强约束在主流程文本中体现，不在 Hook 中。

#### 决策 19：Discovery 阶段给 mockup 生成留出时间和空间

**当前**：plugin 已经完整覆盖了 mockup 的下游链路——"mockup 与设计文档地位平等"明示 4 处 / 原子级拆解到 pack acceptance criteria 硬要求 / "不能只写 mockup 目录"反向硬限 / Review 平等审查。这一部分**已足够，不动**。

**唯一缺口**：Discovery 主流程没有显式承认"用户可能在设计文档涉及 UI/UX 时主动暂停讨论去生成 mockup"这一行为模式。Coordinator 可能因为追求流程推进而催促用户、并行启动其他 Step、或没意识到"等 mockup 定稿"是合理状态。

**改动**（最小）：
- `orchestrate-discovery/SKILL.md` Step 3-9 之间增加**一段轻量说明**：
  > 当设计涉及 UI/UX 且用户表达要生成 mockup 时，Coordinator 暂停当前 Step，给用户调用 `frontend-design` / `prototype` / 其他用户选用的 UI 设计 skill 留出完整时间和空间。Mockup 的生成方式、迭代节奏由用户主动驱动，Coordinator 不催促、不并行启动后续 Step、不替用户决定何时定稿。Mockup 与设计文档地位平等且迭代可能交叉——用户切回设计讨论 Step 时，按当前 Step 继续。

**不做的事**（避免过度设计）：
- 不规定 mockup 何时该生成（用户判断）
- 不规定 mockup 由哪个 skill 生成（用户选择 frontend-design / prototype / Impeccable / 其他）
- 不引入 mockup ↔ design ↔ CONTEXT.md 三方自动同步机制
- 不引入 mockup 变更触发已派 pack 重夸 needs-context 的硬机制
- 不规定 mockup 迭代轮次或定稿门控

**理由**：已实现的下游硬规则保证 mockup 一旦定稿就能原子级进入 plan / pack。Discovery 阶段唯一需要的是"给空间"——剩下都是用户主动行为，plugin 不该越俎代庖。

### 4.3 改动总览图

```
v3.8.0                         本轮 round 2 后
─────────────────────         ────────────────────
13 hooks                      ≤ 10 hooks（删 guard-plan-doc-patch + 降级 1 项 + 简化 gate-codex-review）
13 build templates            10 build templates（删 forbidden-shortcuts / state-write / trust-boundary；review-dispatch.content-only 本轮保留 §10 第 15 条）
50 references                 ≤ 39 references（删孤儿 7 + 合并多层跳 3）+ 3 个 _shared canonical（discovery-formats 保留 — sub-agent 误判已纠正）
20 state.sh subcommands       16 subcommands（删 business-summary / plans / path-a-escalation / agent-context-check；idempotency 保留）
6 scripts/lib                 3 scripts/lib（合并/删 doc-patch-apply / review-effectiveness / learnings-poison-detector）
13 scripts                    10 scripts（合并 review-dispatch 对 / route-worker-dispatch 对 + shim 兼容期）
8 route enum values           4 route enum values（runtime 全称 formal / bug-investigation / multi-pr-merge / direct-repair）+ phase_skip[] flags
6 SKILL.md phase variants     6 SKILL.md（瘦身 30-40%）
2 修复路径（A + B）           1 修复路径（B / SendMessage）
独立 bug seed 文件             直接以 RCA findings 进 Discovery
doc-patch 系统                 Coordinator 直接 Edit plan checkbox
review_intent: 2 值            review_intent: 1 值（baseline 单值，删除 targeted-re-review；review budget 3P+12 → 2P+6）
Discovery: Coordinator 自读     Discovery: 并行派 N 个 Explorer + Coordinator 读浓缩报告
grill-with-docs: 全程提及       grill-with-docs: Step 0 同步入口；CONTEXT.md 与 Design 同级
```

---

## 5. 合同边界

本节列出所有跨 Plan / 跨模块的合同变化。计划写作和 review 必须重点对照本节。

### 5.1 DISPATCH_ENVELOPE schema 变化

`plugin/state-schema/dispatch-envelope-v1.json`：

| 字段 | 当前 | 改为 |
|------|------|-----|
| `review_intent` enum | `baseline / targeted-re-review / path-a-re-review` | **`baseline` 单值**（决策 13 删 targeted-re-review + 决策 3 删 path-a-re-review）；可考虑直接删除该字段 |
| `exception_code` | string\|null | **删除**（仅服务 targeted-re-review，机制被删） |
| `disposition_refs` | array of finding-id | 保留（baseline review 后 Coordinator 修复时仍可填，作为自验痕迹） |

**Owner**：plan 涉及决策 3（删 Path A）的 plan
**Producer**：所有 dispatch Codex review 的 reference（review-dispatch.md.tmpl 或 canonical reference 文件）
**Consumer**：`gate-codex-review.sh` / `parse-envelope.sh`

### 5.2 workflow-state-v1.json schema 变化

| 字段 | 当前 | 改为 |
|------|------|-----|
| `route` enum | 8 值 | 4 值（**保留 runtime 全称**）：`formal / bug-investigation / multi-pr-merge / direct-repair`；删除 `hotfix / quickfix / spike / maintenance` |
| `phase_skip` | — | 新增 array of phase enum，默认 `[]` |
| `commit_format_override` | — | 新增 string\|null，默认 null |
| `path_a_escalation` | object | 删除 |
| `blocked_for_self_fix` | boolean | 删除 |
| `review_dispositions[*].disposition` enum | 10 值含 `path-a` | 9 值不含 `path-a` |
| `bug_seed_path` | string\|null | 删除（如存在） |
| `review_effectiveness` | object | 删除（D3：lib 删除 + 字段删除 + state.sh init 中初始化删除 + tests fixture 同步 + **所有 consumer 引用清理**：`scripts/lib/learnings-confidence-audit.sh` / `scripts/run-summary.sh` / architecture-draft.md 相关章节 / 任何 SKILL.md 提及） |

**Owner**：决策 3（Path A 删除）+ 决策 5（bug seed 删除）+ 决策 10（路线折叠）的 plan
**Producer**：`state.sh init / update / disposition append`
**Consumer**：所有读 workflow-state 的 hook 和 SKILL.md

### 5.3 plan-return-v1.json schema 变化

| 字段 | 当前 | 改为 |
|------|------|-----|
| `doc_patch_path` | string\|null | 删除 |

**Owner**：决策 4（doc-patch 系统删除）的 plan
**Producer**：Worker Loop (worker-loop.md.tmpl)
**Consumer**：`agent-return-handler.sh` + `plan-return-parser.sh`

### 5.4 Build template anchor 合同变化

| 锚点 | 当前 | 改为 |
|------|------|-----|
| `review-dispatch` | inject 到 11 文件 | inject 到 0 文件（删 BEGIN/END 注释）；保留 .tmpl 文件作为 canonical reference 内容源 |
| `repair-routing` | inject 到 9 文件 | inject 到 0 文件 |
| `disposition-table` | inject 到 6 文件 | inject 到 0 文件 |
| `forbidden-shortcuts` | inject 到 2 文件 | 整个模板 + resolver 删除 |
| `state-write` | inject 到 1 文件 | inline 后删除 |
| `trust-boundary` | inject 到 1 文件 | inline 后删除 |
| `review-dispatch [variant=content-only]` | inject 到 1 文件 | **本轮保留，不迁移，不删除**（§10 第 15 条：codex-review skill 不动；留待下轮） |
| `worker-loop` / `control-envelope` / `preamble` / `voice-directive` / `signpost` / `sendmessage-resume` | 保留 | 保留 |

**Owner**：决策 1 + 决策 2 的 plan
**Producer**：`build/templates/*.tmpl` + `build/resolvers/*.sh`
**Consumer**：所有含 `<!-- BEGIN: -->` 锚点的 SKILL.md / agent.md / reference.md

### 5.5 Canonical reference 新增

新增 3 个 canonical reference，**统一放在 `plugin/skills/_shared/`**（plugin-rooted，**不**放在某个 phase 的 references/ 下——避免 phase 互相依赖 + 路径相对解析问题）：
- `plugin/skills/_shared/review-dispatch.md`（≈79 行，从 review-dispatch.md.tmpl 抽取）
- `plugin/skills/_shared/repair-routing.md`（≈42 行）
- `plugin/skills/_shared/disposition-table.md`（≈47 行）

各 phase 的 SKILL.md / reference 文件需要这些内容时，**用 plugin-rooted 绝对路径引用**：

```
**Read** `plugin/skills/_shared/review-dispatch.md` 并按其格式派 Codex review。
```

**禁止使用相对路径**（`../_shared/...` 或 `_shared/...`）——sub-agent 在不同 cwd 下调用 Read 会解析失败。所有引用一律 plugin-rooted 绝对路径。

**Owner**：决策 1 的 plan
**Producer**：新建 3 个文件 + 新建 `plugin/skills/_shared/` 目录
**Consumer**：6 个 SKILL.md + ≈10 个其他 reference 文件（grep `<!-- BEGIN: review-dispatch -->` / `<!-- BEGIN: repair-routing -->` / `<!-- BEGIN: disposition-table -->` 找全）
**Verify-maturity 加检查**：所有原 inject 锚点位置必须替换为 plugin-rooted `Read` 引用，不允许出现相对路径形式

### 5.6 Hook 行为契约变化

| Hook | 当前 | 改为 |
|------|------|-----|
| `guard-plan-doc-patch.sh` | exit 2 阻断 | 整脚本删除 |
| `validate-plan-dispatch.sh` Step 6 Manifest 检查 | exit 2 | WARN |
| `validate-plan-dispatch.sh` Step 8 Path A | exit 2 | 删除（无 Path A 概念） |
| `validate-multi-pr-dispatch.sh` (b) | exit 2 | **保持 exit 2**（Alignment Review C5） |
| `validate-multi-pr-dispatch.sh` (d) | exit 2 | **保持 exit 2**（Alignment Review C5：Document-as-Context 单一权威源保护） |
| `gate-codex-review.sh` `--resume` 检查 | exit 2 | **整段删除**（决策 13：targeted re-review 机制被删，无 --resume 强制约束） |
| `gate-codex-review.sh` `targeted-re-review` 分支 | exit 2 | **整段删除**（决策 13） |
| `gate-codex-review.sh` `path-a-re-review` 分支 | exit 2 | **整段删除**（决策 3 已删 Path A） |
| 其他 hook 行为 | — | 保持 |

**Owner**：决策 9 的 plan（+ 决策 4 关于 guard-plan-doc-patch）
**Producer**：`plugin/hooks/*.sh`
**Consumer**：Claude Code hooks 触发系统

### 5.7 state.sh 子命令合同变化

| 子命令 | 当前 | 改为 |
|--------|------|-----|
| `business-summary` | exists | 删除（0 生产调用） |
| `plans` | exists | 删除（0 生产调用） |
| `path-a-escalation` | exists | 删除（决策 3） |
| `agent-context-check` | exists | 删除（决策 6 — Worker 本地决策） |
| `idempotency check/append` | exists | **保留**（4 处生产调用——调研误判已纠正） |

**Owner**：决策 3 / 6 / 7 的 plan
**Producer**：`plugin/scripts/state.sh`
**Consumer**：所有 grep `state.sh <subcommand>` 调用方（删除前用 grep 全验证 0 残留）

### 5.8 Scripts CLI 合同变化（决策 8）

`record-review-dispatch.sh` / `validate-review-dispatch.sh` → 合并为 `dispatch-review.sh`：

| 旧调用 | 新调用 |
|--------|--------|
| `bash plugin/scripts/validate-review-dispatch.sh <args>` | `bash plugin/scripts/dispatch-review.sh validate <args>` |
| `bash plugin/scripts/record-review-dispatch.sh <args>` | `bash plugin/scripts/dispatch-review.sh record <args>` |

`record-route-worker-dispatch.sh` / `validate-route-worker-dispatch.sh` → 合并为 `dispatch-route-worker.sh`：

| 旧调用 | 新调用 |
|--------|--------|
| `bash plugin/scripts/validate-route-worker-dispatch.sh <args>` | `bash plugin/scripts/dispatch-route-worker.sh validate <args>` |
| `bash plugin/scripts/record-route-worker-dispatch.sh <args>` | `bash plugin/scripts/dispatch-route-worker.sh record <args>` |

**兼容策略**：旧 4 个脚本保留为 shim（内部转发 `exec "$DIR/dispatch-<x>.sh" <validate|record> "$@"`），允许 producer 渐进迁移。所有 producer（SKILL.md / reference / build template / hook） 完成迁移 + 一轮 Plan Implementation Review 通过后再删除 shim。

**Owner**：决策 8 的 plan
**Producer**：新建 2 个合并脚本 + 改写 4 个旧脚本为 shim
**Consumer**：
- ≈13-15 处 review-dispatch 调用（SKILL.md / references / build templates）
- ≈11 处 route-worker-dispatch 调用
- hook（如 `validate-plan-dispatch.sh` 内部 source 这些 lib）
- tests/*.sh

**Verify-maturity 加检查**：shim 期结束后 grep 全仓库无 `record-review-dispatch.sh` / `validate-review-dispatch.sh` / `record-route-worker-dispatch.sh` / `validate-route-worker-dispatch.sh` 直接调用

---

## Cross-Plan Contract Anchors

> 本节由 plan-writing Step 12b 在所有 plan 完成后写入。当前 placeholder。

```
TBD（plan writing 完成后填充）
```

---

## 6. 发布风险和人工门禁

### 6.1 高风险点

**风险 1：模板系统去重可能引入"找不到内容"**
- 风险：把 `review-dispatch` 从 inject 改为 canonical reference，如果某个 SKILL.md 路径里漏了 `Read _shared/review-dispatch.md` 指令，Coordinator 不知道怎么派 review
- 缓解：grep 全量验证旧 `<!-- BEGIN: review-dispatch -->` 锚点位置 → 每处对应替换为 `Read` 指令，verify-maturity 加新检查
- HITL：Plan Implementation Review 需要 Coordinator 亲跑一次完整 Codex review 派发，验证 SKILL.md 引用链完整

**风险 2：Route 折叠破坏 hotfix 路径**
- 风险：hotfix 流程依赖某些只在 route-4-hotfix.md 里描述的边角逻辑，折叠到 SKILL.md 后可能遗漏
- 缓解：折叠前并行对照原文，列出所有"特殊行为"逐项归入 SKILL.md Route 1 Variant Table
- HITL：需要用户确认 hotfix 流程在 Route 1 + flags 下能完整跑通（决策 10 的 Open Decision 之一）

**风险 3：Path A 删除影响已有 review 流程**
- 风险：当前 Plan Implementation Review pass 后还会清理 path-a-escalation 状态；删除字段后旧 workflow-state JSON 可能出现 dangling references
- 缓解：在 hooks 中加 graceful fallback（字段不存在视为已清理）
- HITL：决策 3 是否完全删 Path A vs 保留作为 deprecated path 由用户决定

**风险 4：doc-patch 删除后 Coordinator 漏勾 checkbox**
- 风险：当前是 Worker 写 diff + Coordinator 自动 apply；改后 Coordinator 必须主动 Edit
- 缓解：`agent-return-handler.sh` 输出明确 NEXT 指令包含勾选清单；Plan Implementation Review pass 后的 SKILL.md Step 13 加入"Coordinator 必须 Edit plan 文档勾选 committed Pack" 硬约束 + `guard-premature-push.sh` 已有"plan 未勾完不能 push"的 hook，作为兜底
- HITL：无

### 6.2 不变量必须保持

- Worker Loop 6 段合同不动（启动 5 步 / Pack 循环 / 6 verdict / repair mode / context 自监控 / artifact schema）
- Document-as-Context 主线不动（design / issue / plan / merge-brief 文档链）
- Codex Review 5 步派发协议不动（write prompt → select model → submit → poll → result）
- guard-doc-edit.sh Worker 写 docs/ 硬墙不动
- track-execution-state.sh + agent-return-handler.sh 自动状态机不动

### 6.3 Release Gate

本轮不涉及任何"用户能感知"的功能变化——是 plugin 自身重构。Release Gate **不触发**，无需 Release Review。

---

## 7. 测试和验收

### 7.1 自动化测试

- 所有现有 `plugin/hooks/tests/*.sh` 套件继续通过（57 suites baseline）
- 所有现有 `plugin/scripts/tests/*.sh` 套件继续通过
- 新增 / 修改 `verify-maturity.sh` 检查项：
  - **Canonical reference**：`plugin/skills/_shared/{review-dispatch,repair-routing,disposition-table}.md` 存在 + 所有原 inject 位置已替换为 plugin-rooted `Read` 指令（grep 无残留 `<!-- BEGIN: review-dispatch -->` / `<!-- BEGIN: repair-routing -->` / `<!-- BEGIN: disposition-table -->` 锚点；引用一律 plugin-rooted 绝对路径，不允许 `../_shared/` 相对形式）
  - **Phase 进入 baseline chars 上限**：每个 phase 的 SKILL.md + frontmatter `read:` 列出的 references 总 chars ≤ §2.1 目标（execution / final-review / multi-pr-merge 各 ≤ 50000）
  - **每个 SKILL.md 行数上限**（独立于 phase chars，直接 `wc -l` 检查）：
    - `orchestrate-execution/SKILL.md` ≤ 300 行（§2.1）
    - 其他 5 个 SKILL.md（discovery / workflow / plan-writing / final-review / multi-pr-merge）≤ 当前基线 × 0.7 — 具体值由 plan 阶段从当前 wc -l 计算填入 verify-maturity
  - **单 reference 最大行数** ≤ 250（决策 §2.1）
  - **死锚点清理**：无 `<!-- BEGIN: forbidden-shortcuts -->` / `<!-- BEGIN: state-write -->` / `<!-- BEGIN: trust-boundary -->` 锚点存在（决策 2）；review-dispatch.content-only 本轮不删
  - **死字符串清理**：所有 .md 无 `path-a` 字符串（决策 3）；无 `doc-patch` 字符串（决策 4，除 git 历史和 deprecated 标注）；无 `bug-seed-path` / `bug-seed-file` 字符串（决策 5）
  - **State machine 命令删除**：state.sh 不再支持 `business-summary` / `plans` / `path-a-escalation` / `agent-context-check` 4 个子命令；**仍支持** `idempotency check/append`
  - **Lib 死代码删除**：`scripts/lib/review-effectiveness.sh` 不存在；`scripts/lib/learnings-poison-detector.sh` 不存在（合并入 learnings-jsonl.sh）；`scripts/lib/doc-patch-apply.sh` 不存在
  - **review_effectiveness consumer 引用全清**：grep `review_effectiveness` / `review-effectiveness` 全仓库无非历史引用（git history 除外）；特别检查 `scripts/lib/learnings-confidence-audit.sh` / `scripts/run-summary.sh` / `plugin/architecture-draft.md` / 所有 SKILL.md 已清理
  - **Hook 数**：`plugin/hooks/*.sh` 数量 ≤ 10；`hooks.json` 无 `guard-plan-doc-patch` 条目
  - **Route enum 长度**：`workflow-state-v1.json` 的 `route` enum 值数 = 4
  - **Route extensions 副本**：`plugin/skills/orchestrate-execution/references/route-extensions/` 目录不存在；`plugin/skills/orchestrate-workflow/references/route-extensions/` 目录不存在（已折叠回 SKILL.md）
  - **路标完整性**：所有 `plugin/skills/*/references/*.md`（除 `_shared/`）顶部 5 行内必须含路标 blockquote
  - **Orphan reference**：无 .md reference 文件未被任何 SKILL.md / 其他 reference / agent.md / build template 引用
  - **Dispatch script shim 期检查**：合并完成期内允许 `record-/validate-review-dispatch.sh` / `record-/validate-route-worker-dispatch.sh` shim 存在；shim 期结束后必须全部删除（由 Plan 关闭时切换检查模式）
  - **Workflow-state JSON 不含废弃字段**：新 init 的 workflow-state 不包含 `path_a_escalation` / `blocked_for_self_fix` / `bug_seed_path` / `review_effectiveness`（旧 run 通过 graceful ignore 容忍）
- 全量 `bash plugin/scripts/run-all-tests.sh` 通过

### 7.2 验收路径

完成本轮后，跑一次完整 mock 流程（用 fixture）：
1. Mock Coordinator 走 Discovery → Plan Writing → Execution → Final Review
2. 测量每个 phase 进入时 Read 到的总 chars 量，对照 §2.1 目标
3. Mock 一次 needs_repair → Path B SendMessage 修复
4. Mock 一次 multi-pr-merge 完整流程
5. Mock 一次 hotfix（Route 1 + phase_skip flags）

### 7.3 人工验收清单

完成后 Coordinator 必须能在不依赖任何 build template inject 的 inject 行为下：
- [ ] 拿到一份 design 写一份 plan
- [ ] 派 Worker 完成 Plan
- [ ] 派 Codex review
- [ ] 处置 finding
- [ ] 派 SendMessage repair
- [ ] 推 Closing

每条流程都能从 SKILL.md / canonical reference / 自己的认知中找到下一步指引，**不需要新增任何文件**。

---

## 8. UI/UX 状态

不适用（plugin 内部重构，无 UI）。

---

## 9. 失败场景和异常处理

### 9.1 关键失败场景

**场景 1：Coordinator 在 Plan Implementation Review pass 后忘记 Edit plan checkbox**
- 检测：`guard-premature-push.sh` 在 push 时扫到未勾选的 `- [ ]` → exit 2 阻断
- 恢复：Coordinator 收到阻断 → 回头 Edit plan → 重新 push

**场景 2：模板系统改动后某个 SKILL.md 漏了 canonical reference 引用**
- 检测：verify-maturity.sh 加检查："所有原 BEGIN review-dispatch 锚点位置必须替换为 Read 引用"
- 恢复：Plan Implementation Review 抓到 → repair

**场景 3：旧 workflow-state JSON 含已删除字段**
- 检测：`state.sh validate` 警告
- 恢复：state.sh read/update 对未知字段 graceful ignore；不强制 migration（每个新 run 自带 fresh state）

**场景 4：Path A 删除后某个旧 reference 仍提到 Path A**
- 检测：verify-maturity grep 检查
- 恢复：plan 完成前清理

**场景 5：Worker 在 Loop 中途 compact，本地 `packs_in_session` 计数丢失（决策 6）**
- 背景：决策 6 把 `state.sh agent-context-check` 删除，改为 Worker 内存计数。但 Worker 自身也可能 compact，导致内存丢失
- 检测：Worker 在 compaction 恢复时 SessionStart hook 注入恢复指令
- 恢复：Worker Loop 启动 Step 3 增加"如内存计数缺失，读 `execution-state.plans[plan_id].packs[*].status` 统计 `status=committed` 的 Pack 数 = `packs_in_session` 初值"。`execution-state` 由 `track-execution-state.sh` 自动维护，是单一真相源
- 不变量：恢复后的计数精确反映已完成 Pack；Worker 不需要"猜"

**场景 6：合并的 dispatch script shim 期内 producer 漏迁移**
- 检测：每个 Plan 完成时 grep 该 Plan 触及的 producer 文件是否仍含旧脚本名
- 恢复：Plan Implementation Review 抓到 → repair；所有 producer 完成迁移后 + 一轮 PIR 通过后再删除 shim

### 9.2 不可恢复失败

- 用户在 Round 2 落地中途要求中止 → 已 committed 的改动留存（每个 Pack 独立 commit，可 cherry-pick）；未 committed 的 Worker 进度通过 `state.sh agent-id` 找到 worker_agent_id 后 SendMessage 续修或新 dispatch

---

## 10. 不在本次范围

本轮**明确不做**的事项（即使发现也不触碰）：

1. 不改 Worker Loop 6 段合同（启动 5 步 / Pack 循环 / 6 个 verdict / repair mode / context 自监控 / artifact schema）。决策 4 删除 doc-patch 不算改 6 段——artifact 段保留 plan-return.json + pack-returns/，只是 `doc_patch_path` 可选字段被删除，per_pack 必填结构不动
2. 不改 Document-as-Context 主线（设计 → issue → plan → merge-brief → 代码 链路）
3. 不改 Codex Review 5 步派发协议（`codex-companion.mjs task --background ... result`）
4. ~~不改 review budget 公式~~ — **决策 13 推翻**：删除 targeted re-review 后，review budget 从 `3P + 12` 降为 `2P + 6`（baseline review 每 phase 1 次 + 修复后 Coordinator 自验闭合，不再 reviewer 闭合复审）。effort budget 公式 `2 × review_total` 保持
5. 不引入新的 sub-agent 类型（继续用现有 7 个）
6. 不引入新的 review provider（仍只用 Codex）
7. 不改 mockup 系统 / frontend-design skill 集成
8. 不改 Route 2（Bug Investigation）和 Route 3（Multi-PR Merge）的主流程结构（决策 5 仅简化 bug-seed-file 这个边角概念）
9. 不动 plan-return-v1.json 的 `per_pack` 必填字段结构（仅删 `doc_patch_path` 可选字段）
10. 不动 merge-brief-v1.json 的 9 段结构（仅可选简化 stage 状态机若发现冗余 — 这条留作 Open Decision）
11. 不引入新的状态文件类型
12. 不动 `guard-doc-edit.sh` Worker 写 docs/ 硬墙
13. 不动 `cleanup-before-push.sh` 清理逻辑
14. 不引入"分支管理"功能（continue stay on the current `claude/upbeat-mclaren-d7ef86` branch；本轮成果与 round 1 一并 push）
15. 不动 codex-review skill（独立 ad-hoc 路径，已最小化）

---

## 11. Decisions（用户已确认 2026-05-28）

> 4 个 Open Decisions 已由用户全部采纳推荐选项 A。本节作为审计追溯。

### D1 — Path A 完全删除 ✅

**问题**：决策 3 提议彻底删 Path A（Coordinator 自修分叉）。当前 Path A 是节省一次 Worker dispatch 的优化路径，但代价是 4 个状态字段 + 1 条 hook 检查 + 路径升级机制。是否完全删除？

**通俗说明**：现在审查发现问题后，Coordinator 可以选择自己改（路径 A）或派 Worker 改（路径 B）。路径 A 是优化但加了一堆"防止滥用"的辅助机制。删了之后所有修都派 Worker，多花一次 dispatch 但代码简洁很多。

**选项**：
- **A（推荐）**：完全删除 Path A，所有 repair → Path B（SendMessage Worker）
  优势：删 4 状态字段 + 1 hook + 1 reference + 1 review_intent enum + 1 disposition 选项；状态机大幅简化
  代价：每次小修都派一次 Worker（≈每次小修多 1 个 effort 单元；按重构后 Decision 5 加权计算，单 finding 修复 effort = 1-2，影响可控）
- **B**：保留 Path A 作为 deprecated path（不再激活但代码留作向后兼容）
  优势：旧 run 不会因恢复时找不到字段而炸
  代价：复杂度没真正消除；新代码里仍要处理 path-a-related 字段

**用户决策**：A — 完全删除 Path A。向后兼容靠 graceful ignore（state.sh validate 对未知字段 warn 不 fail）。

### D2 — 外部 Skill 保持 inline ✅

**问题**：决策 11 当前保留 inline 模式，不引入对 `to-issues` / `to-PRD` / Writing Plans 等外部 skill 的 `Skill()` 调用。

**通俗说明**：你列举了 Plugin 借鉴的几个外部 Skill（MattPocock to-issue / Superpowers Writing Plans 等），它们的方法论现在 inline 在 Plugin 内部的 reference 文件里。本来可以改为运行时调用外部 Skill 节省 plugin 体积，但运行时调用会引入外部依赖（如果外部 plugin 更新或卸载，我们这边会断）。

**选项**：
- **A（推荐）**：保持 inline（决策 11 当前方案）
  优势：plugin 自洽，无外部依赖；inline 内容已经过 plugin 上下文裁剪
  代价：plugin 体积稍大
- **B**：把 `to-issues` / Writing Plans 改为外部 `Skill()` 调用
  优势：plugin 减重 ≈300-500 行 reference 内容
  代价：依赖外部 plugin 持续可用；如果外部 plugin 接口变动，我们要跟随升级

**用户决策**：A — 保持当前 inline。plugin 自洽，不引入外部依赖。

### D3 — review_effectiveness 字段 + lib 删除 ✅

**问题**：决策 7 提议删除 `scripts/lib/review-effectiveness.sh`（0 生产 source）。但 `workflow-state.review_effectiveness` 字段本身有用吗？

**通俗说明**：这是个观察指标——统计 reject/suppress/path-a 比例，超阈值发警告。当前是自动聚合，但没人真的看告警；用户主要靠 plan-level review verdict 判断质量。

**选项**：
- **A（推荐）**：删除 lib + 字段
  优势：彻底简化；可选诊断本来就没真正起到 review gate 作用
  代价：失去一个可选观察维度
- **B**：保留字段，删除 lib，Coordinator 手动统计填字段（只在 Final Review 时）
  优势：保留观察价值
  代价：Coordinator 多一步手工动作

**用户决策**：A — 删除 lib + 字段。可选诊断本来就没真正起到 review gate 作用。

### D4 — merge-brief 状态机本轮不动 ✅

**问题**：决策"不在本次范围"列了 merge-brief 9 段结构不动，但 `current_stage` 7 值枚举（init / conflict_discovery / rca / repair / integration_review / merging / complete）+ `state.sh merge-brief init/stage/verify` 三 helper 是否过细？

**通俗说明**：multi-pr-merge 流程的"阶段标记"现在有 7 个值 + 3 个 state.sh 子命令做状态机。可能可以简化为 4 阶段（discover / fix / review / merge）。

**选项**：
- **A（推荐）**：本轮不动 merge-brief 状态机，作为下轮课题
  优势：本轮已经够大；merge-brief 还较新，运行不久，让真实使用反馈攒一会儿
  代价：暂时保留这部分冗余
- **B**：本轮一并简化为 4 阶段
  优势：一次性收尾
  代价：multi-pr-merge 路线本身使用频次低，得失比难判断；可能改完发现重要细节漏掉

**用户决策**：A — 本轮不动 merge-brief 状态机，作为下轮课题。

---

## 12. Business Summary Inputs

> 由 Final Review 时 Coordinator 写入。当前 placeholder。

```
TBD（Final Review 时填充）
```

预填关键点（供 Final Review 时参考）：
- 系统级 token 减负：plugin 进入每个 phase 的 baseline 加载减少 ≈30-40%
- Worker dispatch 数：与 round 1 持平（不再有 Path A 优化，但通过模板去重抵消）
- 流程稳定性：Worker Loop 6 段合同 + Document-as-Context 主线 + Codex Review 5 步协议 全部保留
- 复杂度净减：13 → ≤10 hooks / 50 → ≤40 references / 20 → 17 state.sh subcommands / 8 → 4 routes / 13 → 9 build templates / 6 → 3 scripts/lib

---

## Review History

> 由 `state.sh review-history append` 写入。当前 placeholder。

| Round | Verdict | Reviewer | Findings | Disposition Summary |
|-------|---------|----------|----------|--------------------|
| TBD   | TBD     | TBD      | TBD      | TBD                |

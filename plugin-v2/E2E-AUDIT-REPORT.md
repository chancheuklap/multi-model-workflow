# Plugin V2 端到端演练审计报告

**日期**：2026-05-19
**路线**：Route 1 Formal Orchestrate（最长最复杂路线）
**模拟场景**：为 SaaS 产品 TaskFlow 添加分级订阅系统（billing migration + permission catalog + Dashboard UI + rollback strategy）
**budget 消耗**：18/22 dispatches

---

## 一、结论

端到端主路径**可以走通**。从 Entry Gate → Discovery → Design Review → to-issues → Plan Writing → Plan Review → Execution (5 packs) → Final Review → Release Gate → Closing，完整链条无断裂，无死循环，无悬空引用。所有文件路径引用正确（25 个 reference 文件全部存在）。Agent name 与 dispatch subagent_type 完全对齐。

但走通的代价是**极高的认知负荷和严重的内容冗余**。一个 Coordinator agent 需要在运行中读取 6 个 SKILL.md + ~25 个 reference 文件，总计约 4000 行指令文本。其中大量内容是重复的（Disposition 表 4 份、修复路由 3 份、Forbidden Shortcuts 2 份）。

---

## 二、问题清单

### 🔴 严重（影响流程运行或可能导致错误行为）

#### S1. Release Gate "独立预算" 实际不独立

**位置**：`execution-release-gate.md`、`final-review-release-gate.md`、`hooks/track-review-budget.sh`

**问题**：文档说"Release gate 有独立预算（最多 2 个 dispatch，含 early + final）"。但 SubagentStop hook 对所有 `codex:codex-rescue` dispatch 一律递增 `budget_used`——包括 Release Gate dispatch。budget_total 公式 `2N+12` 的推导中最后的 `+2` 就是 Release Gate。所以 Release Gate dispatch 计入了全局 budget。

**影响**："独立预算"的描述误导 Coordinator，可能导致对剩余 budget 的误判。特别是当同一 session 中 Early Release Gate 和 Final Release Gate 都触发时。

**修复建议**：删掉"独立预算"的说法，改为"Release Gate 的 2 个 dispatch 已包含在 `2N+12` 总预算中"。或者修改 hook 不对 Release Gate dispatch 递增（需要 hook 能区分 release 和非 release dispatch）。

#### S2. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 未设置时修复链路静默降级

**位置**：`hooks/session-start.sh`、`agents/pack-executor.md`（模式 2a）、`agents/plan-writer.md`、`final-review-repair.md`

**问题**：`session-start.sh` 在环境变量 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 未设置时打印警告："SendMessage to existing agents will not work. All repairs will require new agent spawns."

整个修复链路依赖 SendMessage：
- pack-executor 模式 2a（SendMessage 发送 accepted findings 给已有 worker 继续修复）
- plan-writer 收到 Plan Review findings 后通过 SendMessage 修订
- Final Review repair 路径 B（SendMessage 给原 worker）

如果 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 未设置，这些路径**全部降级为新建 agent**——新 agent 没有原始实现上下文，修复效率大幅降低，且消耗额外 context 窗口。

**影响**：这是一个**链条断裂**——文档和流程假设 SendMessage 可用，但运行时条件可能不满足。降级行为没有在 SKILL.md 或 references 中说明，Coordinator 不知道该怎么应对。

**修复建议**：(1) 在 SKILL.md Global Constraints 中明确声明 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 是必需的运行时依赖；(2) 或者在每个使用 SendMessage 的修复路径中加 fallback 说明："SendMessage 不可用时新建同类 agent，在 prompt 中提供完整上下文（pack brief + 前轮 findings + 前轮修复内容）"。

#### S5. Codex reviewer 返回 `needs context` 整体 verdict 时无处理路径

**位置**：所有 Codex dispatch template 的 Return Contract 都列出 `needs context` 作为可能的 verdict；但 `execution-pack-review-cycle.md` Step 9、`plan-review-resolution.md` Step 15、`final-review-disposition.md` Steps 6-7 的 Disposition 表只处理 per-finding 的 disposition

**问题**：每个 Codex dispatch template 说 reviewer 可以返回 `Verdict: needs context`。但 Coordinator 的 Disposition 表只定义了 per-finding 的 6 种 disposition（accepted / rejected / needs evidence / duplicate / out of scope / user decision）。如果 reviewer 整体返回 `needs context`（不是某条 finding 需要证据，而是 reviewer 自己无法完成审查），Coordinator 没有处理路径。

**影响**：悬空 verdict——Coordinator 收到 `needs context` 后不知道该走哪条路。

**修复建议**：在 Disposition 逻辑前加一层"Overall Verdict 处理"：`needs context` → 补充 reviewer 所需的上下文后重新 dispatch（消耗 1 次 budget）。

#### S6. Starting commit 未持久化存储

**位置**：`final-review-preconditions.md` Step 1、`workflow-infrastructure.md` Step 5

**问题**：Final Review 需要 `git diff <starting_commit>..HEAD` 来获取完整变更。`starting_commit` 被描述为"orchestrate-workflow 在 Infrastructure Setup 创建的 Git Checkpoint commit（work branch 的第一个 commit 或 execution 开始前的 HEAD）"。但这个值**没有被存储在任何持久化文件中**——budget file 不存，scope contract 不存。

**影响**：Cross-Conversation Resume 时，Final Review 无法确定正确的 starting commit。可能用错误的 base commit 生成 diff，导致 reviewer 看到不完整或过多的变更。

**修复建议**：在 budget file 中增加 `starting_commit` 字段，在 Git Checkpoint（Step 5）时记录。

#### S3. plan-writer 加载了完整 SKILL.md（含大量 Coordinator 指令）

**位置**：`agents/plan-writer.md` (`skills: ["orchestrate-plan-writing"]`)、`skills/orchestrate-plan-writing/SKILL.md`

**问题**：plan-writer 通过 `skills:` 自动加载整个 `orchestrate-plan-writing` SKILL.md。这包括 Steps 0-2（前置条件检查，Coordinator 职责）、Steps 11-12a（Plan Gates，Coordinator 职责）、Steps 13-18（Plan Review + Disposition + 修复，Coordinator 职责）、Step 19-20（Git Checkpoint + 返回，Coordinator 职责）。plan-writer 只需要 Steps 3-8（写作方法论）。

**影响**：浪费 plan-writer 的上下文窗口（约 60% 的 SKILL.md 内容与 plan-writer 无关），且 Coordinator 级指令（如"派 codex:codex-rescue"、"budget check"）可能混淆 plan-writer 的行为。

**修复建议**：将 Steps 3-8 的方法论提取到独立文件（已有 `references/plan-writing-methodology.md`），让 plan-writer 只加载方法论文件而非整个 SKILL.md。或者拆分 SKILL.md 为 coordinator 部分和 writer 部分。

#### S4. Cross-Conversation Resume 时 Design Review per-phase allowance 可能失效

**位置**：`design-review-angles.md`（per-phase allowance 检查）、`workflow-infrastructure.md`（Cross-Conversation Resume）

**问题**：Design Review 使用独立的 per-phase allowance（4 dispatches），检查方式为 `budget_used + 2 ≤ 4`。但 `budget_used` 是全局累计值，由 hook 自动递增。如果上一个 session 在 Design Review 中途断了（已消耗 2 dispatches），新 session resume 后 `budget_used=2`，此时 `2+2=4 ≤ 4` 刚好通过。但如果上一个 session 在 Design Review 后又做了 1 次 targeted re-review（`budget_used=3`），resume 后 `3+2=5 > 4` → **检查失败，无法继续 Design Review**。

**影响**：Cross-Conversation Resume 在 Design Review 阶段可能卡住。

**修复建议**：per-phase allowance 检查应基于"本 phase 已消耗"而非全局 `budget_used`。或者 budget file 中记录每个 phase 的消耗。

---

### 🟡 中等（过度设计 / 冗余 / 模糊，影响可维护性和 agent 认知）

#### M1. Disposition 表重复 4 次

**位置**：
- `execution-pack-review-cycle.md` Step 9
- `final-review-disposition.md` Steps 6-7
- `plan-review-resolution.md` Step 15
- `merge-integration-review.md`（未完整读取但按 agents.overrides.md 确认）

**问题**：完全相同的 6 行 Disposition 定义（accepted / rejected / needs evidence / duplicate / out of scope / user decision）+ Reception Rules + needs-evidence 补证说明，在 4 个文件中全文复制。

**成本**：~400 行重复内容。agents.overrides.md 已承认需要"同步所有 4 个 phase 文件"，但这实际上是一个同步漂移定时炸弹。

**缓解**：agents.overrides.md 说"信息密度规则 → Disposition 表自足内联"作为有意设计。但自足的代价是 4 份独立维护——任何改动需要手动同步 4 处。建议保持自足但缩短到关键差异行（如果 4 份完全相同则只需引用一处通用定义+各 phase 的特殊规则）。

#### M2. 修复路由重复 3 次（Path A/B/C + 截断 + RCA）

**位置**：
- `plan-review-resolution.md` Steps 16-18
- `execution-repair-truncation.md` Steps 10-12
- `final-review-repair.md` Steps 9-12

**问题**：修复路由（Path A: Coordinator 直接修 / Path B: Worker 修 / Path C: Explorer 调查）+ 截断逻辑（2-3 轮上限 + RCA dispatch）在三个文件中几乎相同。差异仅在于：(1) Plan 允许 2 轮、Execution/Final 允许 3 轮；(2) Final Review 多了 "回 Execution 判定"。

**成本**：~300 行重复内容。

#### M3. Forbidden Shortcuts 列表重复 2 次

**位置**：
- `execution-review-dispatch.md`（Pack Review Codex dispatch template）
- `final-review-angles.md`（Final Review Baseline 2 Codex dispatch template）

**问题**：完全相同的 10 项 Forbidden Shortcuts 列表（bare dict、临时拼 nested dict、route-local schema/helper、public API dict[str,Any] 等）在两个文件中全文复制。

**成本**：agents.overrides.md 承认"改 Forbidden Shortcuts 时同步"。但如果只改了一处漏了另一处，reviewer 在 Pack Review 和 Final Review 会用不同标准审。

#### M4. Budget 系统层级过多且预算偏紧

**位置**：全局分散

**问题**：存在 5 层重叠的 budget 控制：
1. Per-phase allowance（Discovery: 4 dispatches）
2. Global budget_total（`2N+12`）
3. Direction Check（80% 触发）
4. Release Gate "独立预算"（max 2，实际不独立，见 S1）
5. Per-phase 内部 soft cap（Final Review: 10）

实际运行中 Coordinator 需要在每次 dispatch 前做 3-4 种不同的 budget 检查，且不同 phase 的检查方式不同（Discovery 用 per-phase allowance，Plan Review/Execution/Final Review 用 global budget_total）。

此外，本次模拟（5 packs）总预算 `2×5+12=22`。实际消耗 18/22——这还是**完全顺利、无修复、无截断**的理想路径。一个稍有波折的真实运行（1 次 Plan Review repair + 1 次 Pack Review repair + 1 次 Final Review repair = +3 dispatches）就达到 21/22，几乎耗尽。2 个 pack 出问题就直接超预算。

**修复建议**：统一为"全局 budget + Direction Check"两层。Discovery 的 2 个 baseline 就是 budget 的前 2 次消耗，不需要独立机制。Release Gate 不需要"独立预算"说法。考虑将公式调整为 `2N+16` 或 `3N+12` 以容纳正常修复消耗。

#### M5. Direction Check 规则过于复杂且分散

**位置**：`execution-pack-review-cycle.md` Step 8、`final-review-preconditions.md` Step 3

**问题**：Direction Check 有 5 个触发条件，分散在至少 2 个文件中。条件包括"同一 finding 2 个 repair rounds"、"追加非 baseline reviewer"、"spawn 目的无法归类"、"findings 互相冲突"——这些判断需要 Coordinator 做大量元认知工作。

**实际效果**：Direction Check 本质是"停下来想想是否在正确方向上"。任何有经验的 orchestrator 在消耗了 80% budget 时自然会这么做。5 个离散触发条件增加了认知负荷但不增加决策质量。

**修复建议**：简化为"达到 budget 80% 时做一次 Direction Check"，删掉其他 4 个条件。

#### M6. "不存在非阻塞项" 重复 5+ 次

**位置**：architecture-draft.md 结论 10、orchestrate-workflow SKILL.md、execution-completion.md、final-review-completion.md、final-review-disposition.md

**问题**：同一条规则在 5 个以上的地方重复声明。规则本身非常重要，但重复 5 次不会让它更有效——反而稀释了其他规则的注意力。

**修复建议**：写一次放 SKILL.md 的 Global Constraints，其他地方引用而非重复。

#### M7. Execution completion 的步骤编号与主 SKILL.md 冲突

**位置**：`execution-completion.md` 内部编号从 Step 13 开始、`orchestrate-execution/SKILL.md` 也有 Step 13

**问题**：execution-completion.md 的 "Step 13: Early Release Gate" 与 SKILL.md 的 "Step 13: Early Release Gate" 是同一步，但读起来像两个不同的引用。reference 文件自己也有 Steps 14-16，与 SKILL.md 的编号重叠。

**影响**：Coordinator 按编号跳转时可能混淆。

**修复建议**：reference 文件不独立编号——只用标题和锚点，让 SKILL.md 的编号作为唯一权威。

#### M8. TDD strict 没有逃生阀

**位置**：`agents/pack-executor.md`（模式 1 TDD）、`agents/complex-pack-executor.md`（模式 1 TDD）

**问题**：所有 pack-executor 都强制 TDD strict（红-绿-重构循环）。但许多 task 是微调性的——比如"加一个常量 `FREE_TIER_LIMIT = 5` 并在一处消费"、"更新 README"、"改一个 CSS 样式"。对这些 task 强制 TDD 是表演，不是质量控制。

Plan 中有 `risk_flags`（`migration`、`billing`、`auth`、`shared-contract`）用来判断是否升级到 complex-pack-executor，但没有对称的低风险标记（如 `trivial`）来降级 TDD 要求。

**修复建议**：增加 `risk_flags: trivial` 或等效机制，当 pack 只包含配置变更、常量添加、文档更新时跳过 strict TDD。

#### M9. Final Review ↔ Execution 回流无显式次数限制

**位置**：`final-review-repair.md` Step 10（"回 Execution 判定"）、`workflow-formal-orchestrate.md` Step 14 verdict 路由

**问题**：Final Review 发现 implementation gap 较大时可以回流到 Execution（`NEEDS_EXECUTION`），Execution 完成后又回到 Final Review（`EXECUTION_PASSED`）。这个循环没有显式的次数上限。

**缓解**：全局 budget（`2N+12`）在实践中是隐式 cap——每轮回流消耗 2+ dispatches（worker + review），budget 很快耗尽会触发 Direction Check。但 Coordinator 不会直觉地把"budget 快用完了"理解为"该停止回流了"，因为文档没有把这两件事联系起来。

**修复建议**：在 final-review-repair.md 的截断规则中加一条："NEEDS_EXECUTION 最多触发 1 次；第 2 次 → BLOCKED 报告用户"。

---

### 🟢 轻微（可优化，不影响功能）

#### L1. Design Review 2 baseline vs Plan Review 1 baseline 的设计理由不明

**位置**：`design-review-angles.md`（2 baseline）、`plan-review-dispatch.md`（1 baseline with 3 angles）

**问题**：Design Review 派 2 个独立 Codex reviewer，Plan Review 只派 1 个（整合 3 个角度）。Final Review 又派 2 个。这个不对称没有在任何地方解释设计理由。

---

## 三、Route 2（Bug Investigation）审计

**模拟场景**：用户报告"TaskFlow 升级订阅后 Dashboard 仍显示旧配额，刷新后正常"
**路径**：Entry Gate → Steps 4-5（Scope + Git）→ Step 15（dispatch analyst）→ Step 16（handle return）→ Step 17/18（review/worker）→ Closing

### 已修复

| 编号 | 问题 | 修复 |
|------|------|------|
| R2-1 | Entry Gate 路由写 "Step 4 → reference"，实际 Bug Investigation 在 Steps 15-18，中间跳过 Steps 6-14 没有说明 | Entry Gate 改为 "Steps 4-5（Scope + Git，跳过 Budget）→ Step 15" |
| R2-2 | Step 17 Codex review 缺少 `needs context` 整体 verdict 处理（与 S5 同类） | 加了前置检查 |
| R2-3 | Step 18 worker 返回后只有一行 "→ Codex review → Closing"，没有 verdict routing | 补了完整的 4 种 verdict 路由表 |

### 剩余问题

#### R2-M1. Route 2 → Route 1 转换的 seed 传递机制隐式

**位置**：`bug-investigation-route.md` Step 16 `root cause in design/plan` 路径

**问题**：Analyst 发现根因在设计层面时，文档提供了 "Bug-seeded Discovery" 模板，但没有说明这个 seed 信息如何传递给 `orchestrate-discovery` skill。Coordinator 在调用 `Skill({ skill: "orchestrate-discovery" })` 时，seed 靠对话上下文隐式传递——如果发生 context compaction，seed 可能丢失。

**修复建议**：seed 信息写入 Scope Contract 的 Source artifacts 部分（已有指导），但应额外强调 Scope Contract 是 compaction-durable 的信息载体。

#### R2-M2. Route 2 没有任何 budget 机制

**位置**：全局

**问题**：Route 2 没有 budget file。Step 17 Codex review + targeted re-review 的次数只靠 "最多 2 轮" 文字约束。如果 analyst `unable_to_determine` 后用户要求继续，多次 analyst dispatch + Codex review 没有全局计数器。

**影响**：小问题——Bug Investigation 通常很短（1 analyst + 1-2 Codex），不太会失控。但与 Route 1 的严格 budget 管控形成对比。

---

## 四、Route 3（Multi-PR Merge）审计

**模拟场景**：3 个 PR（Billing migration + Permission catalog + Dashboard UI）来自同一订阅系统设计
**路径**：Entry Gate → Steps 4-5（Scope + Git）→ orchestrate-multi-pr-merge（Steps 1-22）→ Closing

### 已修复

| 编号 | 问题 | 修复 |
|------|------|------|
| R3-1 | `merge-integration-review.md` Step 17 缺少 `needs context` 前置检查（Route 1 修复时遗漏） | 加了前置检查 |
| R3-2 | Analyst ↔ Explorer 循环无次数限制 | 加了 "最多 1 次循环" |
| R3-3 | `git merge <pr-branch>` 假设本地分支，远程 PR 无 fetch 指导 | 加了 `git fetch origin` |

### 剩余问题

#### R3-M1. 修复引入新冲突的递归无上限

**位置**：`merge-conflict-repair.md` Step 14

**问题**：Step 14 说 "修复引入新冲突 → 新冲突进入 Step 7 分类"。每个冲突有 3 轮修复上限，但修复可以创造新冲突，新冲突又有自己的 3 轮上限。理论上：修 A 引出 B，修 B 引出 C…… 没有全局递归深度限制。

**实际风险**：低——冲突通常越修越少，不会无限增殖。但没有显式 cap 是一个设计缺口。

**修复建议**：加全局新冲突上限——"修复引入的新冲突最多处理 2 轮；之后 BLOCKED"。

#### R3-M2. `${CLAUDE_PLUGIN_ROOT}` 变量在 agent context 中是否可用

**位置**：`agents/root-cause-analyst.md` 模式 3 方法论读取指令

**问题**：agent 定义说 "读取 `${CLAUDE_PLUGIN_ROOT}/skills/orchestrate-multi-pr-merge/references/rca-pr-conflict-methodology.md`"。`${CLAUDE_PLUGIN_ROOT}` 是 Claude Code runtime 注入的变量，但 agent 是在子会话中运行——需要确认这个变量在子会话中是否解析。

**影响**：如果变量未解析，agent 找不到方法论文件，会使用 fallback 的通用调查方法。不会链条断裂，但会降低调查质量。

---

## 五、全路线总体评估

### 做得好的
- **文件引用零悬空**：所有 reference 文件（Route 1: ~25 个 + Route 3: 7 个）全部存在且正确引用
- **Agent 模式检测设计合理**：root-cause-analyst 的 3 模式各有独立 Resolution 值和方法论，dispatch template 的信号词与模式检测表对齐
- **Route 3 的 5 维度冲突分析**很全面：代码 / 功能 / 意图 / 合同 / 隐式依赖
- **Route 2 的 5 路径 Resolution 覆盖完整**：从 "修好了" 到 "需要重做设计" 到 "复现不了" 全有处理

### 三条路线的成熟度对比
- **Route 1**：最成熟——经过这轮审计修了 17 个问题后，链条完整，budget 控制严格，修复和截断路径清晰
- **Route 3**：中等——架构设计很好（冲突三级分类、Analyst 调查、集成审查），但边界情况（新冲突递归、变量解析）有缺口
- **Route 2**：最薄——流程最短但也最粗糙，verdict 路由不完整（已修），没有 budget 机制，seed 传递靠隐式上下文

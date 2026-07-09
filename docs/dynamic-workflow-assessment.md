# multi-model-workflow Plugin × Claude Code Dynamic Workflow —— 借鉴与转换评估

> 评估日期：2026-05-29 · Plugin 版本：v3.9.4 · Dynamic Workflows：research preview（需 Claude Code ≥ 2.1.154）
> 方法：1 个 hook-seam 实证探针 + 12-agent 调研工作流（6 路 ground-truth → 3 路 design lens → 3 路 adversarial 反驳），所有 load-bearing 事实由 Coordinator 亲自用 Read/grep 复核后写入。

---

## 0. 一句话结论

**借鉴——强烈推荐，而且大部分根本不需要用 Workflow 这个工具**；**整体转换为一个 Dynamic Workflow——不可行，会把这个 plugin 的存在理由（人在环、跨会话、跨模型审查）整套丢掉**；**让 Coordinator 在特定环节调用 Workflow——可行但窄，只有 3 个只读并行环节够格，真正回报只在大规模 Multi-PR 扫描时才显现**。

调研过程中还顺带查出一个**真实的文档/代码 bug**（预算公式文档写 `2P+6`，代码实际 `3P+12`），见 §5。

---

## 1. 两个系统到底是什么（避免"看起来很像"的误判）

它们表面都在"编排 subagent"，但在**三条决定性的轴**上正好相反：

| 轴 | 本 Plugin | Dynamic Workflow |
|----|-----------|------------------|
| **谁在环里** | 人在环：Coordinator 随时停下来问用户（设计确认、80% Direction Check、user-decision、push/PR 授权、BLOCKED 汇报） | 无人在环：launch 后**后台 fire-and-forget**，官方文档原话 "No mid-run user input"，只在 workflow **之间**通知主线程 |
| **会话寿命** | 跨会话 + 抗 compaction：靠磁盘状态平面（`active-run-id` / `workflow-state` / `execution-state` / scope contract）+ `session-start.sh` 在 startup/clear/compact 时重建游标 | **同会话 only**：官方原话 "Resume works within the same Claude Code session. If you exit Claude Code while a workflow is running, the next session starts the workflow fresh." 只持久化**脚本**，不持久化**运行进度** |
| **什么是确定性的** | 确定性在**边缘**（hooks/state.sh/bash 在 tool 边界 exit 2 强制）；控制流在 Coordinator 读 SKILL.md prose 的**头脑里** | 确定性在**控制流**（JS 脚本里的 loop/conditional/fan-out）；叶子（agent）是模型 |

**一句话翻译**：本 plugin 是一个"会跟你对话、能跨天续命、靠 GPT 独立审查 Claude 代码"的正式开发流程编排器；Dynamic Workflow 是一个"发射后不管、当场跑完、用 Claude 子代理大规模并行"的后台批处理引擎。设计理念相似，定位互补，不是替代关系。

### 1.1 实证锚点（不是推断）

- **Hook 探针（已验证）**：我让一个 Workflow 派生的 agent 执行 `git merge --squash`，本 plugin 的 `guard-premature-push.sh` 把它**拦下了**（`saw_plugin_block_message: true`，同一仓库 cwd）。→ Workflow agent **自己的** Bash/Edit/Write tool 调用**确实**会过 session 的 PreToolUse tool-matcher hook。
- **官方文档（已 web 核实）**：Dynamic Workflows = research preview；并发上限 16；单 run 上限 1000 agents；同会话 resume；无 mid-run 用户输入；脚本内无文件系统/shell 访问。全部与工具内置规格一致，无冲突。

---

## 2. 问题二：能否转换为 Dynamic Workflow？（三种含义分开答）

### 2a. 整体转换（整个生命周期 = 一个后台 Workflow 脚本）—— 不可行

四个**各自独立、各自致命**的结构性阻断，全部经代码核实：

1. **对话入口 + 人在环业务门全死。** 整个 plugin 里 `AskUserQuestion`/`ExitPlanMode` **一个都没有**（grep 实测为空）——每次暂停都是 Coordinator 结束本轮、用业务语言问用户。Workflow 后台 fire-and-forget、无用户输入原语，所以设计方向确认（Discovery 硬门）、80% Direction Check、user-decision 处置、push/PR/merge 授权**无法在 run 中向人索取**。
2. **跨会话 / 抗 compaction 不兼容。** Plugin 的韧性来自磁盘状态平面 + `session-start.sh:71-93` 在新会话重建游标；Workflow resume 明确"同会话 only"且是 agent() 缓存前缀重放——**机制不同，能力缺失**。
3. **派发门 hooks 失效。** Workflow `agent()` 是运行时原语，不走 Agent tool；`agent-return-handler.sh:25` 字面 `if [ "$TOOL_NAME" != "Agent" ]; then exit 0`——所以 verdict 路由、`validate-plan-dispatch`（envelope/幂等/单 worker/plan-level/repair 证据，`:29-137`）、`validate-pack-manifest`、`track-effort-budget` 全部不再触发。`agentType:'pack-executor'` 也救不了——hook 匹配的是 **tool seam**，不是 subagent 类型。
4. **状态平面 bootstrap gap，连"会触发"的 Bash hooks 也被架空。** Workflow 脚本碰不了文件系统，永远不会创建 `active-run-id`/`worker-active` marker——于是 `enforce-plan-commit`、`track-execution-state`、`track-review-budget`、`guard-doc-edit`、`gate-codex-review` 全部在缺文件时 early-exit 空转（如 `guard-doc-edit.sh:32` 无状态目录即放行）。**hook 触发了，但保证被中和。**

> **这是给你的业务决策，不是我单方面的判决**：整体转换在技术上不是"做不到"，而是它会把这个 plugin 变成**另一个产品**——一个发射后不管的自动跑批器，恰恰丢掉它现在所有的核心价值。除非你的目标本来就是"不要人参与、当场跑完的自治流水线"，否则强烈不建议。证据强度：四个独立阻断点全部成立。

### 2b. Coordinator 调用 Workflow（保留对话/跨会话/HITL 大脑，只把特定并行环节外包）—— 可行但窄

**准入规则**（四条全满足才够格）：(a) 纯 Claude-agent 并行 fan-out；(b) 全程自治、无 mid-run HITL；(c) 内部不含 Codex；(d) 其保证不依赖磁盘状态平面。

**够格的 3 个环节：**

| 环节 | 位置 | 为什么够格 |
|------|------|-----------|
| Discovery 仓库探查 | N 个 code-explorer 并行（`orchestrate-discovery/SKILL.md:117-124`） | 最佳契合：纯只读并行，无 HITL、无 Codex、无状态写 |
| Multi-PR 冲突**发现** | 1-N explorer 跨 PR 分支扫（`merge-conflict-discovery.md:13-30`） | 契合，且 16 路并发在大扫描时**真有回报**（不含其后的串行依赖序合并） |
| per-finding "needs evidence" 取证 | 目前**串行**（`orchestrate-execution/SKILL.md:352`） | 可改为 adversarial-verify 并行——**仅取证，不替代审查判定** |

**明确不能转的（执行陷阱，务必在任何设计稿里标红）：**
- **Execution 是最差候选**，不是最好。它本来就串行（一个 Plan 一个自治 Worker，worktree-per-worker 已评估否决），且它的派发完整性骨架（envelope/单 worker/plan-level/commit 格式/docs 写保护/scope drift）同时依赖 **Agent seam + 状态平面**——进了 Workflow 全被中和。转 Execution = 用"并不存在的并行"换掉"全部派发完整性保证"。
- **所有 review gate** 不能转——它们就是 Codex 派发，原生转换会丢跨模型独立性。
- 两个 baseline Design/Final review 也不行——它们是 Codex (GPT-5.x) 后台任务，不是 Claude agent。

**诚实的性价比账**：Coordinator **现在已经**能用 Agent tool 并行派 N 个 explorer。所以这一步主要是"换一种并行机制"，**真正净增益**是：(1) `parallel()` 给的确定性 barrier（自动 await 全部、失败→null）；(2) `schema` 强制结构化返回；(3) run 期间**会话保持响应**；(4) 大 Multi-PR 扫描时的 16 路并发。小规模下增益有限。

> 官方文档恰好给了这条路线的"祝福"：**"For sign-off between stages, run each stage as its own workflow."** ——这正是"Coordinator 留作对话/HITL 大脑，每个自治阶段当作一个独立 workflow 跑"的模式。

### 2c. 借鉴模式（不碰 Workflow 工具，只吸收设计理念）—— 见 §3，这才是主菜

---

## 3. 问题一：能否借鉴 Dynamic Workflow 做系统性升级？—— 能，且最高价值的部分不需要那个工具

最深的洞察来自控制流分类（D2）：**plugin 里很大一块"看起来像 hook 强制"的逻辑其实是 advisory（always exit 0，只发 NEXT 提示，真正分支仍靠模型读 prose 照做）**——`agent-return-handler`、`track-execution-state`、`track-review-budget`、`track-effort-budget`、`detect-worker-scope-drift` 都只做账本、从不 block。

Dynamic Workflow 的核心理念——**把控制流变成确定性代码**——正好映射到这个 advisory 层。这就是"借鉴"的金矿。

### 借鉴清单（按性价比排序）

| # | 借鉴项 | 价值 | 工作量 | 风险 | 要不要 Workflow 工具 |
|---|--------|------|--------|------|--------------------|
| B1 | **修预算公式文档漂移**（`3P+12` vs `2P+6`，见 §5） | 中——消除模型用错预算上限的活 bug | 极小（2 处文档 + 加 1 个 test） | 极低 | 否 |
| B2 | **把 verdict→action 路由确定化**：`agent-return-handler.sh` 现在 advisory（exit 0，`:103-129`），verdict 是闭枚举。移进 `state.sh` transition matrix，非法转换 exit 2 | 高——头号"算了但没强制"的分支变成保证 | 中（扩 `state.sh:73-114` + tests） | 低-中（未知 verdict → BLOCKED 兜底） | 否 |
| B3 | **结构化返回 schema 扩面**：plan-return 已 schema 校验（`plan-return-v1.json`），但 explorer/plan-writer/取证返回仍是 prose 手解。每类返回定 JSON schema、收到即校验 | 中——消灭一类静默解析错误，verdict 路由基于 typed 字段 | 低-中（schema + 薄校验，复用 `lib/plan-return-parser.sh`） | 低（加性的，校验失败回退 prose） | 否（理念来自 Workflow `opts.schema`） |
| B4 | **per-finding 取证并行化**：今天串行（`:352`），改为每个中/低置信 finding 并行派 1 个 explorer，再由 Coordinator 批量亲验+处置（adversarial-verify 模式，**仅取证**） | 中——缩短处置 wall-clock，保持"先验后接受"纪律 | 低（复用现有 explorer，派发循环 串→并） | 低-中（须守住：处置永远是 Coordinator 步，不能让并行取证被自动采信） | 否（可选用 `parallel()`） |
| B5 | **完成 prose 控制流向脚本的迁移**：plan/pack toposort 排序、repair-round 计数封顶——从 prose 表移进脚本（文件读仍留 hook/Bash） | 中——排序不会被错 toposort、repair 上限不会被数错 | 中 | 低-中（务必保留 prose 里**该模糊的判断**） | 否（理念来自 loop-until-dry / JS 控制流） |

### 明确**不要**借鉴 / 不要做的

- **不要把模糊判断 ossify 成 exit-2 门**：route/variant 选择、worker 选型（Risk×Context）、finding disposition、repair-path 路由——它们活在 prose **正是因为**需要读意图。变成状态机检查 = 买到确定性、赔掉判断力，产生模型本来能优雅处理的脆性误路由。
- **不要用 Workflow 的 `budget` 原语替换本 plugin 的双预算**：Workflow `budget` 是 **token** 目标，plugin 是 **dispatch 次数**（review_used++ / 加权 effort）。单位不同，硬套会失真。借的是"loop-until-budget 封顶"的**形**，不是 budget 计量。

---

## 4. 不可动的红线（转换/借鉴都不能碰）

1. **跨模型审查独立性 = plugin 的字面存在理由**（"multi-model"）。`architecture-draft.md:320` 明确：故意没有 Claude `code-reviewer`/`release-reviewer` agent；全部 review 走 `codex-companion.mjs`（GPT-5.x）。7 个 Claude agent 全是 implementer/explorer/analyst。Workflow `agent()` 只能派 **Claude**，registry 里**没有 reviewer**——原生 judge-panel/adversarial-verify 就是 **Claude 评 Claude**：盲区相关、假信心、且因为结构一模一样而**静默劣化**。→ 原生审查**绝不能**替代 Codex gate；adversarial-verify 只能用于 Claude 侧**取证**，不能用于审查**判定**。
   - （注：Workflow agent 的内部 Bash 能 shell out 到 `codex-companion.mjs` 拿真 GPT review——已验证 hook 会触发——但那是把现有 CLI 硬塞进去、放弃原生原语，还继承 CLI 的 headless/cron 交互式鉴权坑。）
2. **人在环业务门**：fire-and-forget 后台无法索取人的决策。这些门必须留在主线程 Coordinator。
3. **跨会话/抗 compaction 状态平面**：Workflow 同会话 resume 无法重建跨会话磁盘状态。这是 plugin 韧性的根，必须保留。

---

## 5. 顺带查出的真实 bug：预算公式文档漂移

| 来源 | 公式 | 证据 |
|------|------|------|
| **代码（权威）** | `review_total = 3 * plan_count + 12`，`effort_total = ×2` | `plugin/scripts/state.sh:916` |
| **测试（确认代码）** | P=4 → review_total=24、effort_total=48 | `plugin/scripts/tests/test_state.sh:76-80` |
| **文档（错）** | `2P + 6` | `plugin/skills/orchestrate-plan-writing/SKILL.md:174` + `references/plan-gates.md:46` |

P=4 时文档说 14/28、代码实际 24/48——近 2 倍偏差。Coordinator 若按文档推理预算余量会用错上限。**建议立即修**：把两处文档改为 `3P+12`，并补一个 doc-vs-code 一致性检查。这与是否采用 Workflow 完全无关，是独立的修复项。

---

## 6. 推荐路线

**现在就做（与 Workflow 无关，纯收益）：**
1. 修 §5 预算公式漂移（B1）。
2. 把 verdict→action 路由从 advisory 升级为 transition-matrix 强制（B2）。
3. 结构化返回 schema 扩面到 explorer/plan-writer/取证返回（B3）。

**想试 Workflow 工具时，严格限定在 3 个只读并行 fan-out**（Discovery 探查 / Multi-PR 冲突发现 / per-finding 取证），用准入规则把关；**别碰 Execution、别碰任何 review gate、别碰串行依赖序合并、别碰任何写状态平面或要问用户的环节**。预期真正回报只在大 Multi-PR 扫描（16 路并发）+ 长扫描期间保持会话响应。

**永远不要：**整体转换为单一 Workflow；用原生 Claude review 替代 Codex；把模糊判断 ossify 成 exit-2 门。

**成本提示（你关心的计费）：** Dynamic Workflows 无独立计费档，按标准 token 计入计划用量（Max/Pro 订阅内含）——但**单次 run 因为派很多 agent，token 消耗显著高于普通会话**。这与你"1M 上下文只升 Opus"的成本取舍同源：Workflow 不引入新计费规则，但会放大 token 体量，适合按 scoped 任务试水。另注：Workflow 功能要求 Claude Code ≥ 2.1.154，本 plugin `session-start.sh` 现在硬要求 ≥ 2.1.147——若要用 Workflow，门槛抬到 2.1.154。

---

## 附录 A：调研方法与可信度

- **Hook-seam 实证探针**（1 agent）：直接在 Workflow 内派 agent 跑被 hook 守护的命令，观测拦截——这是整份评估唯一"实测"的事实，其余 hook 行为为同类 seam 推断（INFERRED），已在 §2a/§4 标注。
- **主调研工作流**（12 agent，~746K token）：6 路 ground-truth（DW 外部核实 / 控制流分类 / HITL+跨会话 / 并行+机械编排 / review 机制 / hook-seam 依赖图）→ 3 路 design lens（native-first / preserve-strengths / pragmatic-hybrid）→ 3 路 adversarial 反驳。
- **三条决定性结论的对抗性检验全部"未被推翻"**（refuted=no）：(1) 整体转换丢 HITL；(2) Workflow 同会话 resume ≠ plugin 跨会话韧性；(3) Agent-matcher 派发门被 `agent()` 绕过。
- **Coordinator 亲验（plugin 侧）**：预算公式 bug（`state.sh:916` / `test_state.sh:76` / 两处文档）、`agent-return-handler.sh:25` 的 `tool_name != "Agent"` 早退、全 plugin 零 `AskUserQuestion`、Codex 为唯一 reviewer（`architecture-draft.md:320`）——均由我本人 Read/grep 复核，未直接采信子代理。
- **Coordinator 亲验（web 侧，`code.claude.com/docs/en/workflows`）**：research preview、`v2.1.154`、sign-off 原文（"For sign-off between stages, run each stage as its own workflow"）、计费（"available on all paid plans … Runs count toward your plan's usage and rate limits"）四条 load-bearing 事实由我本人 WebFetch 复核，未直接采信子代理。另核到两条强化结论的官方事实：(1) Workflow 派生 agent **永远以 `acceptEdits` 跑、文件编辑自动批准**（说明 plugin 的 docs/ 保护若进 workflow，须靠 exit-2 hook 而非权限模式兜底——与 §4 一致）；(2) 内置 `/deep-research` 的 cross-check 是 **Claude 给 Claude 投票**——直接坐实 §4 红线 1（原生审查 ≠ 跨模型独立审查）。
- **范围**：仅 `plugin/`；未读 `.agents/`/`codex/`/`archive/`（禁区）。
- **已知偏差**：design lens L3（pragmatic-hybrid）部分字段返回占位符，其 borrow 建议（verdict 路由确定化）已并入 §3 B2；hybrid 结论由 L1/L2 充分覆盖，未重跑。

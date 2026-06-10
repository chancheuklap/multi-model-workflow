# Orchestrate 流程脚本化 + Execution 并行 设计文档

## 背景和问题

本 plugin（multi-model-workflow）是一套「讨论定设计 → 文档 → 放手落地」的正式开发流程编排器，核心价值是人在环、跨会话韧性、跨模型（Codex）独立审查。当前版本 v4.0.0/4.0.1 在三个方面存在结构性短板，已由 5 路并行代码调研 + Coordinator 逐条 grep 亲验确认：

1. **半数据化导致流程不稳 + 费 token**。外层 phase 状态机已数据化（`routes-v1.json` + `state.sh transition`，健康），但一批本应机械执行的控制流仍散落在 SKILL.md 散文里，靠模型读表照做：
   - 6 张 workflow-level verdict 路由表（`orchestrate-workflow/SKILL.md:157-254`）**完全没有脚本实现**，而 plan-level 同类路由早已 hook 化（`agent-return-handler.sh:101-127`），两侧不对称——这是最大的不稳定来源。
   - checkbox 勾选（`orchestrate-execution/SKILL.md:287-291`）、DISPATCH_ENVELOPE 拼装是纯机械动作，却靠模型手做。
   - 预算公式双轨：`routes-v1.json:37` 声明 `"3P+12"`、`state.sh:9-10` 又硬编码常量，且声明那份**无运行时读取点**。
   - `gate_exemptions`（`routes-v1.json`：formal 为 `[]`、light 为 `["discovery","plan-review"]`；`routes-v1.schema.json` required 列表 + `test_routes_manifest.sh:40,45` / `test_route_keyword_routing.sh:44` 锁定其存在）无任何运行时读取点；`global_transitions` 里一批 work-item 状态机条目（`agent-return-handler`/`track-execution-state` 等 actor）也无运行时调用方——声明了没接线。

2. **Execution 串行，耗时长**。`orchestrate-execution/SKILL.md:76,116,298` 明文「逐 Plan 串行循环」。多份计划即使互不依赖也只能一个接一个跑，wall-clock = 各 Plan 之和。这是用户头号不满。

3. **控制流脚本化程度不足**，流程稳定性依赖模型「读散文照做」的自觉，而非机器强制。

用户视角：每次启动一个正式开发，几份计划文档只能串行展开，等待时间长；plugin 本身单独消耗的 token 偏多；流程不像脚本那样可被确定性地管理。

## 目标结果

完成后，本 plugin 能稳定做到：

1. **机械控制流由脚本/数据驱动**：workflow-level verdict 路由、checkbox 勾选、dispatch envelope 生成、预算公式单源化——这些确定性动作不再靠模型读散文执行，流程更稳定、SKILL.md 散文体量下降带来 token 改善。判断类步骤（finding 处置、route 选择、scope drift、Pack 排序、BLOCKED 措辞）保持散文，不僵化。
2. **Execution 阶段独立 Plan 并行执行**：无 Blocked-by 依赖的 Plan 自动并行（激进默认），各自在隔离工作树工作；某 Plan 失败时自动隔离、不污染其他、必要时单独回退串行；完成后按依赖顺序轻量合并回主干。wall-clock 从「各 Plan 之和」降到「最长依赖链」。
3. **五条 route 全部保留且不僵化**：formal / light / direct-repair / bug-investigation / multi-pr-merge 在脚本化后行为不变，路径灵活性不丢。
4. **三根命脉不受损**：人在环业务门、跨会话/抗 compaction 状态平面、跨模型 Codex 独立审查——脚本化与并行都不触碰。

## 用户场景

actor / action / benefit，覆盖 happy path、失败、空状态、并发、回滚：

| Actor | 场景 | 行为 | 收益 / 预期结果 |
| --- | --- | --- | --- |
| 用户 | happy path（多独立 Plan） | 启动 formal 流程，3 份无依赖 Plan | 3 份并行执行，wall-clock ≈ 1 份的时间，而非 3 份之和 |
| Coordinator | 依赖链 Plan | Plan B `Blocked by` Plan A | A、B 串行；与 A 无关的 Plan C 与 A 并行 |
| Coordinator | 单 Plan 项目 | 只有 1 份 Plan | 退化为串行，无并行开销（不建多余 worktree） |
| Worker | 并行执行 | 每个并行 Plan 一个隔离 worktree | 各 Worker 在独立工作树 commit，互不踩踏 |
| Coordinator | 某 Plan 并行失败 | Plan B 的 Worker 返回 blocked / 验证失败 | B 隔离，A/C 继续；B 失败不回滚 A/C 的产出；B 视情况单独回退串行重试 |
| Coordinator | 回收合并 | 并行 Plan 全部通过各自 Plan Implementation Review | 按依赖顺序逐个 `git merge --no-ff` 回 Coordinator 分支；冲突走借鉴 multi-pr-merge 方法论的发现/RCA |
| Coordinator | verdict 路由 | phase skill 返回 verdict | 机械跳转部分由声明数据驱动（verdict→target），判断分支仍读散文 |
| Coordinator | checkbox 勾选 | Plan Implementation Review pass | 脚本按 plan-return committed 列表自动 toggle，不靠模型手 Edit |
| 用户 | route 不变性 | 走 light / direct-repair / bug-investigation | 脚本化后这些 route 行为与现状一致 |
| Coordinator | 多 Worker 同时返回 | 批次内两个 Worker 几乎同时返回 | 按到达顺序串行处理（先到先审），处理期间其余 Worker 继续执行，无返回丢失 |
| Coordinator | compaction 恢复 | 并行执行中途 compaction | 从状态平面恢复所有 in-flight Plan（active_plan_ids），不丢并行进度 |

## 方案设计

分两大工作块。**A（脚本化）优先级高于 B（并行）**：A 是低风险纯收益，B 重开了已否决的 worktree-per-worker 决策、风险高。两块都完整设计，落地按优先级推进，不允许只做 A。

### A. 机械控制流脚本化下沉

倒置原则不变：Coordinator 是对话模型、始终在最外层；脚本下沉到其底下。下沉对象一律是闭枚举 / 查表 / 计数 / 套模板 / 数据搬运。

- **A1. Workflow-level verdict 路由数据化（最小版本）**。把 6 张 verdict 路由表的**机械跳转部分**（verdict → 目标 phase/step 的纯映射）抽成声明数据：`routes-v1.json` 内新增 `verdict_routing` 段，**不另开新文件**（已定，原 Open Decision 收口）。
  **6 张表的精确清单（范围边界，防蔓延）**：`orchestrate-workflow/SKILL.md` 内 5 张（Discovery `:157` / Plan-writing `:185` / Execution `:210` / Final Review `:230` / Multi-PR Merge `:249`）+ `references/workflow-direct-repair.md:84` 1 张。references 里其余 verdict 表（bug-investigation 2 张、multi-pr-merge 各 reference、plan-writer-dispatch、release-gate、execution SKILL `:217` plan worker 表）是 **phase 内部表，不在 A1 范围**——其中 plan worker 表已由 `agent-return-handler.sh` hook 化，无需重复。`state.sh` 新增一条查询命令返回 verdict 对应的机械动作；含判断的分支（如 `NEEDS_ISSUES` 判缺件类型、`NEEDS_ARCHITECTURE` 判影响范围）在散文里保留为「数据给出候选动作 + 散文补判断」。`NEEDS_EXECUTION` 的 `execution_reflux_count` 计数路由是纯机械且有状态，是唯一**完全下沉**项。
  **预期边界（防止高估收益）**：plan-level 路由之所以能 hook 强制，是因为 Worker 是子代理、返回时有 `agent-return-handler` 拦截点；而 5 个 phase skill 在主对话内运行，返回的 verdict 只是对话文本，**不存在 hook 拦截点**。A1 做完后仍是「Coordinator 主动查命令」，收益是散文 token 下降 + 路由单源可测试，**不是机器强制**；phase 跳转合法性本就由 `phase_transitions` + `state.sh transition` 兜底。因此 A1 按最小版本实施，不为它新增 hook、不追求强制力。
- **A2. Checkbox toggle 脚本化**。新增 `state.sh checkbox toggle --run-id --plan-id`：读 `plan-return.per_pack[*] where status==committed`，按 Pack ID 正则在 plan 文档里把 `- [ ] **Pack N.M**` toggle 为 `- [x]`。零判断，替代模型手 Edit。
- **A3. DISPATCH_ENVELOPE 生成器**。新增 `state.sh envelope build`：按现行字段集生成 envelope 骨架（required 6 字段：`protocol_version` / `run_id` / `phase` / `agent_role` / `repair_round` / `idempotency_key`；可选：`agent_id` / `pack_id` / `plan_id` / `disposition_refs` / `review_intent` / `exception_code` / `correlation_id`），可变 payload（repair_context / bug_context / merge）由调用方补。校验已在 `hooks/lib/parse-envelope.sh`（注意在 `lib/` 下），生成对称下沉。
  **顺手修正一个现存缺口**：SKILL.md 模板里 `idempotency_key` 写死 `<run_id>/<pack_id>/r<n>`，但 plan-level 派发时 `pack_id` 为 null——生成器统一为 `<run_id>/<plan_id|pack_id>/r<n>`（plan-level 用 plan_id，pack-level 用 pack_id），消除歧义。
  envelope 字段集新增 `worktree_path`（并行模式必填、串行模式指向 Coordinator 工作树），为 B 块的 Worker 路径纪律提供载体。
- **A4. 预算公式单源化（常量为源，已定）**。消除双轨的方向锁定为：**`state.sh` 常量为唯一权威源**。调查坐实：三档 profile 全在 `state.sh` `cmd_budget_initialize`（standard 3P+12 / generous 4P+16 / tight 2P+6），预算计算的真实权威本就在脚本里；给 bash 写 `"3P+12"` 字符串解析器属于过度设计，不做。死字符串只有一处——routes 五条 route 里仅 formal 有 `formula: "3P+12"`，其余四条均为 `null`，直接删除该字段最干净（schema 同步），并补一条「routes 声明与 `state.sh` 常量一致」的测试杜绝漂移（若保留为文档字段）。
- **A5. gate_exemptions 删除（默认方向）**。`gate_exemptions` 当前声明无消费者，且其语义已被现有字段编码：light 跳过 discovery 这件事由 `phases` 数组本身表达（light 的 phases 里没有 discovery），review 豁免由 `review_required` 表达。为同一语义再接一条 gate 豁免读取链路是重复建设，**不接线，直接删除字段**。删除时同步三处依赖：`routes-v1.schema.json` 的 required 列表、`test_routes_manifest.sh:40,45`、`test_route_keyword_routing.sh:44`；顺带清掉 `workflow-state-v1.json:20` 引用它的 DEPRECATED 注释。唯一保留条件：Design Review 找到 `phases` + `review_required` 覆盖不了的豁免场景——届时再改接线，否则删。
- **A6. work-item transition 空挂条目厘清**。`global_transitions` 里 `agent-return-handler`/`track-execution-state` 等 actor 的 work-item 条目无运行时调用方。两条路：(a) 让这些 hook 真调 `state.sh transition` 把 work-item 机也纳入统一校验；(b) 确认 work-item 机走 execution-state 路径已足够后，删除这批无消费者条目。同时收口 pack-progress 白名单（`state.sh:798-804` 的 `committed|blocked|skipped`）与 schema enum（`execution-state-v1.json:45` 的 `pending/dispatched/returned/committed/blocked`）的不一致。

### B. Execution 并行 + 轻量回收

- **B1. Plan 依赖图与并行批次**。plan header 的 `Blocked by` 从「串行排序键」升级为机器可读 DAG。`state.sh` 新增命令计算可并行批次（topo level）：同一 level 内的 Plan 互不依赖、可并行；level 间串行。无依赖时所有 Plan 在 level 0，全并行；单 Plan 退化串行。
  **落地必踩的坑（调查发现）**：现状 plan 文档头部的 `**Blocked by:**` 写的是**从 issue 文件继承的 issue 编号**（`plan-writing-methodology.md:122`），不是 plan 编号。DAG 解析前必须先收口约定：plan-writer 写 plan 时把 `Blocked by` 翻译成 **plan 编号**（或 "None"），`plan-writing-methodology.md` 模板同步改；`state.sh dep-batches` 只认 plan 编号，遇到非 plan 编号值报错而非猜测。
- **B2. 隔离工作树（硬约束）+ Worker 路径纪律**。并行批次内每个 Plan 由 Coordinator 显式 `git worktree add <path> HEAD` 创建隔离工作树，**以当前讨论 worktree 的 HEAD 为基**。禁用 harness 自动 worktree（`isolation: worktree` + `baseRef: head` 在嵌套场景解析到主 checkout 的 HEAD=main，2026-05 实测，是当年否决 worktree-per-worker 的根因之一）。Worker 在分配给它的隔离工作树内执行、commit、写 plan-return。
  **Worker 路径纪律**（真实失败模式，必须前置防住）：plan 文档里写的全是仓库相对路径，Worker 作为子代理继承主会话 cwd，极易把相对路径拼到 Coordinator 工作树上写错地方。防线两道：(1) dispatch envelope 携带 `worktree_path`（A3 生成器产出），Worker prompt 模板写死「所有文件操作以 `envelope.worktree_path` 为根解析」；(2) 路径守卫——扩展 `guard-doc-edit.sh`（见下方守卫规则）。一攻一守配套，不另建机制。
  **路径守卫规则（受 hook 能力约束的设计）**：调查确认 PreToolUse hook 的输入**拿不到调用者的 agent 身份**（现有 `guard-doc-edit.sh` 就是靠全局 marker 文件判断上下文，不分谁在调），所以守卫不能做成「按 Worker 区分各自 worktree」，必须是对所有调用者都安全的全局规则：**并行飞行期间（存在任一 `worker-active-<plan_id>` marker），Coordinator 主工作树进入只读源码区**——具体放行/拦截：① docs/ 照现状拦；② 主树 `.claude/multi-model-workflow/` 控制面（plan-returns 等）放行（Worker 写 plan-return 的合法通道）；③ 主树其余路径（源码）拦截；④ 已登记 worktree 内的路径全放行（marker 文件内容携带该 Plan 的 `worktree_path`，守卫由此获得登记清单）。该规则与「Coordinator 在 formal 流程中不直接写生产代码」的现有 hard gate 自洽，Coordinator 不会被误伤；markers 清空后主树恢复可写。
- **B3. 状态平面并行化改造**。`execution-state-v1.json`：`current_plan_id`（单数）→ `active_plan_ids[]`（或以 plan-level `status==in_progress` 推断同时在飞的 Plan）；plan-level 新增 `worktree_path` / `branch` / `isolation_status`（active/isolated/merged）字段。`worker-active` 单一全局 marker → per-Plan marker（`worker-active-<plan_id>`，**文件内容写该 Plan 的 `worktree_path`**，供路径守卫读取登记清单），`guard-doc-edit.sh` 改读 per-Plan marker，避免一个 Worker 收尾误清其他在跑 Worker 的保护。
- **B4. Commit 记账修正（已收口：Worker 上报）**。`track-execution-state.sh:28` 当前 `git rev-parse HEAD` 取 Coordinator 工作树 HEAD——并行隔离工作树下失效（Worker 在 worktree 里 commit，hook 在主会话 cwd 取 SHA，必错）。调查发现**上报通道已经存在**：`plan-return-v1.json` 的 `per_pack[*].commit_sha` 字段早已定义（"Git commit SHA of the Pack commit (only when status=committed)"），改动量比预想小三件套：① Worker handbook 明确要求填自己 worktree 里的真实 SHA；② `state.sh plan-returns ingest` 把 per_pack.commit_sha 回填 execution-state（覆盖 hook 写的错值）；③ `track-execution-state.sh` 的 `rev-parse HEAD` 降级为串行模式 fallback（并行模式以 ingest 回填为准）。`start_commit..end_commit` 的 Plan Review diff 基底改为 per-worktree 记录。另一并行顾虑已排除：Pack ID `N.M` 的 N 即 plan 号、全局唯一，多 worktree 同时 commit 不会互相误记，唯一问题就是 SHA 来源，本条已解。
- **B5. 失败自动隔离**。某并行 Plan 的 Worker 返回 blocked / Plan Implementation Review 失败时：标记该 Plan `isolation_status=isolated`，其隔离工作树保留不合并、不回滚其他 Plan 的产出；该批次其余 Plan 继续。被隔离的 Plan 视情况单独回退串行重试（基于最新主干 HEAD 重建工作树）。失败隔离是激进默认的兜底前提——没有它，激进并行不成立。
- **B6. 轻量串行回收**。一个并行批次全部通过各自 Plan Implementation Review 后，Coordinator 按依赖顺序逐个 `git merge --no-ff <plan-branch>` 合并回 Coordinator 分支。合并冲突的**发现与根因分析借鉴 multi-pr-merge 方法论**（派 explorer 发现冲突、系统性冲突走 root-cause-analyst），但**不套用 multi-pr-merge 整套**（它假设已 push 的远程 PR 分支 `git fetch origin`，与本地 worktree 分支不匹配）。multi-pr-merge 整套路线保留给真·跨 PR 场景。回收完成后清理已合并的隔离工作树。
- **B7. 并行返回的事件驱动处理模型（机制零新发明）**。调查确认现有派发**本来就是后台模式**：execution SKILL Step 5 的 Agent 调用已是 `run_in_background: true`（agentId 提取依赖它，串行时也必需），且 `agent-return-handler.sh` 挂在 PostToolUse Agent 上、**每个 Worker 返回各自触发一次**并 emit NEXT 指令——事件驱动的全部机制零件已在运行，并行批次派发只是「连续发 N 个后台 Agent」，无新机制。并行后 execution 的控制流从「FOR EACH Plan → 派 → 等 → 收」的同步循环，改写为「**批次派发 + 返回事件处理**」双层结构：Coordinator 一次性并行派发同一 level 的全部 Worker，之后进入返回处理态——Worker 返回陆续到达，Coordinator **串行**处理（先到先审），处理一个返回（Plan Implementation Review → Disposition → 该 Plan 标记完成或隔离）期间，其余 Worker 不受影响继续执行；多个返回同时排队时按到达顺序逐个消化，不丢、不并发处理。该批次全部 Plan 达到终态（completed / isolated）后才进入 B6 回收，再开下一 level。execution SKILL.md 的循环段按此模型改写。

### 业务对象、角色和状态

| 对象 | owner | writer | reader | verifier | 状态 / 生命周期 |
| --- | --- | --- | --- | --- | --- |
| `routes-v1.json`（+ 可能的 verdict_routing） | Coordinator/维护者 | 维护者（设计期） | `state.sh`、hooks | 测试套件 | 静态声明数据 |
| `execution-state-<run_id>.json` | Coordinator | `state.sh`、hooks（经 state-lock） | Coordinator、hooks | `state.sh validate` | per-run，随 worktree 删除清除 |
| Plan 隔离工作树 | Coordinator | Coordinator（建/合/删）、Worker（commit） | — | git / 测试 | active → (isolated \| merged) → cleaned |
| Plan 依赖 DAG | Coordinator | plan-writer（声明 Blocked by） | `state.sh` 批次计算 | — | 随 plan 文档 |
| plan-return.json | Worker | Worker | Coordinator、`agent-return-handler` | Coordinator 亲验 | per-plan，含上报的 commit_sha（B4 新增） |

### 实现决策

- 脚本化采用渐进下沉，不引入统一 driver 脚本——driver-on-top 会破坏倒置原则、丢三根命脉（等于变成 Dynamic Workflow，已评估否决）。
- 并行粒度限定 Plan 级，不做 Pack 级（Pack 级要推翻「Worker 自治排 Pack 顺序」的现有裁决）。
- 失败隔离优先于并行速度：宁可某 Plan 回退串行，也不让失败污染其他并行 Plan。

## 合同边界

| boundary | 类型 | owner | provider | consumer | 关键字段/路径 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| routes 声明数据 | JSON 数据 | 维护者 | `routes-v1.json`（+ verdict_routing 段） | `state.sh`、gate/dispatch hooks | `verdict_routing`（新增）、`budget.formula`（降级文档字段）、`gate_exemptions`（删除） | A1/A4/A5 |
| execution-state schema | JSON schema + 手写 jq 校验 | Coordinator | `execution-state-v1.json` | `state.sh`、`track-execution-state.sh`、`validate-plan-dispatch.sh` | `active_plan_ids`、`plans[].worktree_path/branch/isolation_status` | B3 |
| plan-return schema | JSON + 手写 jq 校验 | Worker | `plan-return-v1.json` | `plan-return-parser.sh`、`agent-return-handler.sh` | `per_pack[].commit_sha`（字段已存在，B4 接通 ingest 回填） | B4 |
| state.sh 新命令 | CLI 接口 | Coordinator | `state.sh` | SKILL.md 流程、hooks | `checkbox toggle`、`envelope build`、`dep-batches`、`verdict-route` | A1/A2/A3/B1 |
| hook 行为 | exit code + additionalContext | 维护者 | `track-execution-state.sh`、`guard-doc-edit.sh`、`agent-return-handler.sh` | Coordinator | commit_sha 来源、per-plan marker、写路径越界守卫 | B2/B3/B4 |
| build 模板 | 锚点 + .tmpl | 维护者 | `build/templates/` | 各 SKILL.md / agent.md | 新增共享脚本化指令片段须走模板五步流程 | 跨 A/B |

注：本设计无 JSON-Schema 校验器（全仓无 jsonschema/ajv），运行时校验一律手写 jq 字段检查——「schema 扩面」实际是「补手写校验 + 闭枚举」，不是引入校验框架。

## 发布风险和人工门禁

- **改动对象是 plugin 自身运行时核心**（state.sh / hooks / routes / execution skill），风险高于改业务代码。任何改动提交前必须跑 `run-all-tests.sh`（全套件）+ `verify-maturity.sh` + `build.sh --check`。
- **北极星不变量（不可触碰）**：人在环业务门、跨会话/抗 compaction 状态平面、跨模型 Codex 独立审查独立性。脚本化和并行均不得损害。
- **并行失败隔离是关键风险点**：必须有测试覆盖「某 Plan 失败不污染其他、不回滚已通过 Plan、可单独回退串行」。
- **版本号同步**：`plugin.json` + 根 `marketplace.json` 两处版本号必须同步更新。
- **构建系统**：改 SKILL.md 锚点内内容须同步 `.tmpl` 模板并 `build.sh --apply`；新增共享脚本化指令片段走模板五步流程。
- 人工门禁：本设计涉及重开「worktree-per-worker」已否决决策——已经用户明确授权重开（2026-06-09）。

## 测试和验收

- **回归基线**：现有全部测试套件保持全绿；`build.sh --check` 0 diff；`verify-maturity.sh` 通过。
- **新增测试**：
  - A1 verdict 路由数据化：每个 verdict 解析到正确机械动作；判断分支不被误僵化。
  - A2 checkbox toggle：committed pack 被勾选、非 committed 不勾选、Pack ID 精确匹配。
  - A3 envelope 生成：字段完整（含 `worktree_path`）、idempotency_key 格式正确、可变 payload 留空位。
  - A4 预算单源（常量为源）：routes 文档字段与 `state.sh` 常量一致性（P=4 → 24/48，杜绝当年 `3P+12` vs `2P+6` 漂移类问题）。
  - A5 删除收口：`gate_exemptions` 全仓无残留引用（schema required、两个测试文件、workflow-state DEPRECATED 注释同步清净）。
  - A6：pack-progress 白名单与 schema enum 对齐。
  - B1 依赖批次：无依赖全 level 0、依赖链正确分层、单 Plan 退化；`Blocked by` 含非 plan 编号值时报错不猜测。
  - B2 隔离工作树：以讨论 worktree HEAD 为基（非 main）；路径守卫四规则——docs/ 拦、主树控制面（`.claude/multi-model-workflow/`）放行、主树源码拦、登记 worktree 内放行；markers 清空后主树恢复可写。
  - B4 记账：ingest 回填的 per_pack.commit_sha 覆盖 hook fallback 值；串行模式 fallback 仍工作。
  - B5 失败隔离：失败 Plan 不污染其他、不回滚已通过、可回退串行。
  - B6 轻量合并：依赖序合并、冲突触发借鉴 multi-pr-merge 的发现路径。
  - B7 返回处理：多 Worker 返回排队时按到达顺序逐个处理、不丢返回；处理期间其余 Worker 状态不受影响。
- 五条 route 行为不变的回归验证（light / direct-repair / bug-investigation / multi-pr-merge / formal）。

## UI / UX 状态

不适用——本设计无用户界面，全部为 plugin 内部流程 / 脚本 / 数据结构改动。

## 失败场景和异常处理

- **并行工作树创建失败**：回退该 Plan 串行执行，记录原因。
- **并行 Plan 合并冲突**：触发借鉴 multi-pr-merge 的冲突发现（explorer）/ 系统性冲突 RCA；冲突期间不破坏其他已合并 Plan。
- **Worker 越界写（污染的唯一途径）**：worktree 是物理隔离的，跨 Plan 污染的唯一途径是 Worker 把文件写到自己 worktree 之外。不做合并前的内容级污染扫描（为不该发生的事建机制，过度设计），改为**前置路径守卫**：guard hook 校验 Worker 写路径在其分配 worktree 内，越界即拦并记入该 Plan 的异常；若守卫记录显示某 Plan 曾越界写成功（守卫失效场景），该 Plan 标记 isolated，人工裁决后再合并。
- **状态平面并发写竞态**：沿用现有 `state-lock.sh` 目录锁（架构 Ruling 2 已为 pack-level 并发写做文件分离 + 锁，对并行友好）。
- **compaction 中途恢复**：从 `active_plan_ids` + plan-level `isolation_status` 恢复所有 in-flight / isolated Plan，不丢并行进度。
- **routes 数据不可读**：所有读 routes 的脚本/hook 保持 fail-open（退化到内建 fallback，never stricter），与现状一致。

## 不在本次范围

- 整体转换为 Dynamic Workflow（已评估否决）。
- Pack 级并行（会推翻 Worker 自治排 Pack 顺序裁决）。
- 用原生 Claude review 替代 Codex 审查（红线）。
- light / direct-repair / bug-investigation 等非并行 route 的串行执行改造（这些 route 的串行不在并行化范围）。
- 计费 / 权限 / 数据权威等业务红线逻辑（plugin 不引入业务红线）。
- 引入 JSON-Schema 校验框架（维持手写 jq 校验风格）。

## Open Decisions

- A6：work-item transition 空挂条目——接线（hook 真调 `state.sh transition`）还是删除？（取决于 work-item 机走 execution-state 路径是否已足够；落地前由实现者按「删空挂、不留兼容」纪律核实后定，倾向删除 + enum 对齐）

已收口（2026-06-10，原 Open Decision）：
- A1：verdict 路由数据放 `routes-v1.json` 内新增段，不另开新文件；按最小版本实施（见 A1 预期边界）；范围限定 6 张表精确清单。
- A4：预算单源取「`state.sh` 常量为源」，不写公式解析器；routes 死字符串仅 formal 一处，删除（或降级文档字段 + 一致性测试）。
- A5：`gate_exemptions` 默认删除不接线（语义已被 `phases` + `review_required` 编码）；仅当落地核查发现未覆盖豁免场景才改接线。
- B4：commit_sha 来源取「Worker 上报」——`plan-return-v1.json` 的 `per_pack[*].commit_sha` 字段已存在，改动收敛为 handbook 要求 + ingest 回填 + hook rev-parse 降级 fallback 三件套（见 B4）。

## Review History

| Round | Verdict | Reviewer | 重点建议 | 已知 gotcha | 日期 |
| --- | --- | --- | --- | --- | --- |
| — | — | — | （首版待 Design Review） | — | — |

## Cross-Plan Contract Anchors

跨 Plan 共享的合同 / 接口 / 文件所有权（统一在本 design 内维护，单一源）。本设计的 Plan 拆分将在大 issue 拆分阶段确定，已知的跨 Plan 共享面：

| Surface | 类型 | Owner Plan | Provider Plan | Consumer Plan(s) | 关键字段/路径 |
| --- | --- | --- | --- | --- | --- |
| `routes-v1.json` 数据扩展 | JSON 数据 | 脚本化 Plan | 脚本化 Plan | gate/dispatch hooks、state.sh | verdict_routing 新增 / budget.formula 降级 / gate_exemptions 删除 |
| `execution-state-v1.json` schema | JSON schema | 并行 Plan | 并行 Plan | track-execution-state / validate-plan-dispatch | active_plan_ids / worktree_path / isolation_status |
| `state.sh` 新命令集 | CLI | 脚本化 Plan | 脚本化 Plan | 并行 Plan、SKILL.md | checkbox toggle / envelope build（含 worktree_path） / dep-batches / verdict-route |
| `plan-return-v1.json` commit_sha | JSON | 并行 Plan | Worker | track-execution-state、回收逻辑 | per_pack[].commit_sha 或 plan 级 |

（plan-writer 写 Pack 时 Read 本 section 同步 Contract anchors；Coordinator 在 Plan Review / Final Review 以本 section 为权威）

## Business Summary Inputs

（每个 Plan 完成后由 Coordinator 追加，供 final-reviewer 起草业务汇报草稿）

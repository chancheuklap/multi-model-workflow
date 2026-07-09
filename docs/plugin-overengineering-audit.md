# Plugin 过度设计审计 —— 可安全删减清单

> 审计日期：2026-05-29 · Plugin 版本：v3.9.4
> 方法：12 路并行扇出（按统一 rubric 找候选）→ 1 路综合去重排序 → 10 路删除安全性验证（追 consumer / breaking tests / 迁移步骤）。
> 78 个原始 finding，扫描 13692 行。所有"整删 / safe-to-cut"结论由 Coordinator 亲自 grep 复核后写入。
> 角度：本审计回答**「哪些能直接删」**，与已有两份评估互补——`dynamic-workflow-assessment.md` 答「要不要用 Dynamic Workflow 工具」，`plugin-control-flow-codification.md` 答「把控制流从散文搬进代码」。

---

## 0. 一句话结论

过度设计的主形态是三类：**(1) 同一事实多 home + 真相源已在代码却用散文复述（纯重复，删）；(2) 已迁移/废弃的死机器（脚本、模板、shim）从不触达（死代码，删）；(3) 刻意建好、但读取侧从未接线的功能（learnings 子系统、pack_summary 等）——这类不是"误产生的冗余"，是 built-but-unwired，要由你决定「删掉 or 补完接线」，不是单纯去重。**

最该动的不是裸行数最多的，而是**「每次 dispatch 全价烧 sub-agent context」**的部分——因为 Worker / explorer / merge-worker 是独立子上下文，它们启动时背的规则不享受主线程的 prompt cache，每次派发全价重吃。主线程 SKILL.md 散文虽然也冗余，但暖缓存下边际成本只有约 10%（这点 codification 评估已指出，本审计认同）。

**裁决排序轴 = agent-context 烧，不是行数。** 据此，state.sh 内部只写不读的审计账本（mutations / self_verifications，~250 行）判**保留/最低优先**——worker 永不读，删了省 0 agent token 却要改一堆 writer + validate + 测试。

---

## 1. 删减清单（按杠杆排序）

每条标注：**行数** / **context 性质**（🔴=sub-agent 每次 dispatch 全价 · 🟡=主线程散文受缓存摊薄 · ⚪=维护期才读、不烧 agent context）/ **安全等级** / **删了会坏什么（已验证）**。

### Tier A — 整删候选（已亲验当前无 consumer）

> 注意两种性质：**死代码/纯重复**（A2-A7，删=零损失）与 **built-but-unwired 功能**（A1，建好但读取侧从未接线，删=去掉一个从未启用的能力）。后者删除建议不变，但本质是「你要不要这个能力」的产品决策，不是单纯去冗余。

| # | 删什么 | 行数 | context | 删了会坏什么（已 Coordinator grep 复核） |
|---|--------|------|---------|------------------------------------------|
| A1 | **整个 learnings 子系统**：`scripts/learnings-jsonl.sh`(330) + 3 个 test + SKILL.md Step 6c 死散文(`:299-332`) + calibration 表 | ~383 | 🟡+⚪ | **built-but-unwired（删 or 补完接线，你拍）。** 这是刻意建好的自学习/校准能力（投毒检测+时间衰减+calibration 触发+architecture §11.4 整段），但读取侧从未接线：亲验 ①无任何 by-name 调用者（编排器从不运行它）；②`scripts/lib/` 只有 plan-return-parser + state-lock，SKILL.md:304 指向的 `lib/learnings-poison-detector.sh` **根本不存在**（脚本第12行自承已内联）；③`learnings.jsonl` 零下游读回。它不在恢复源集合内。**若你不要"自动从历史学经验"这个能力 → 整删；若要 → 应补完读取侧而非留半成品。** **迁移**：同步 retarget `verify-maturity.sh` 4 条死断言（:74/138/219-220）+ 清 architecture-draft.md 引用。 |
| A2 | **3 对已迁移的死构建模板+resolver**：`review-dispatch.md.tmpl` / `repair-routing.md.tmpl` / `disposition-table.md.tmpl` + 2 个 resolver | ~189 | ⚪ | **无功能损失。** 亲验 `build.sh:53-59`：这三个 anchor 非 content-only variant 直接 `return 1` 不注入；skills/ 里唯一活锚点是 codex-review 的 `[variant=content-only]`。canonical 内容早已迁到 `_shared/*.md`，模板与 canonical 已漂移（"改了死模板以为生效"的陷阱）。**保留** content-only 模板+resolver（codex-review 仍用）。**迁移**：3 条 verify-maturity C2 断言(:170/172/174)重指 `_shared/review-dispatch.md`（已亲验含全部 4 字符串）+ 删/重指 5 个 build test。 |
| A3 | **4 个死 shim**（`validate/record-review-dispatch.sh` + `validate/record-route-worker-dispatch.sh`，各 3 行） | ~12 | ⚪ | **无功能损失。** 亲验：仅 canonical `dispatch-review.sh` / `dispatch-route-worker.sh` 注释里提到它们（"replaces..."），无活调用者。**迁移**：删 verify-maturity :44-49 6 项存在性断言 + `test_dispatch_review_shim.sh`。 |
| A4 | **run-summary 假产物**：`scripts/run-summary.sh`(73) + test + closing Step 22a | ~80 | ⚪ | **无功能损失。** 亲验：脚本只 echo 到 stdout、不写任何盘；workflow-closing.md:62 谎称它写 `.json` 供 "effort budget 校准"——effort_total 是纯公式(`state.sh:917`)不读历史，从未接线；SKILL.md:313 的 "run-summary adversarial 段" 根本不存在。**迁移**：删 closing Step 22a + 改 SKILL.md:313 兜底句。 |
| A5 | **孤儿 reference** `discovery-formats.md` | ~106 | 🟡 | **无功能损失。** 亲验：唯一引用是 SKILL.md:105 一个格式指针，自称的调用方（discovery-discussion/design-document）无回链；grill-with-docs Step0 自带 CONTEXT/ADR 格式。**迁移**：删 SKILL.md:105 指针（context 维护已全程委托 grill-with-docs）。 |
| A6 | **孤儿 reference** `execution-completion.md` | ~57 | 🟡 | **无功能损失。** 亲验：SKILL.md 从不 Read 它（grep 0 命中），内容（Backflow/Re-Entry/Release-Gate）已全在 SKILL.md 主体 Step 13-16。唯一入边是 execution-release-gate.md:125 一句陈旧"下一步"指针。**迁移**：改那句指针指回 SKILL.md Step 14。 |
| A7 | **死字段 `context_pressure`**（plan-return-v1 schema + 两 executor 写指令） | ~20 | 🔴 | **无功能损失。** 亲验：所有 .sh 里 `context_pressure` **零 grep 命中**（parser/ingest 都不读它，packs_in_session 续传靠 `execution-state...status==committed`）。停写它省 worker 每次写盘开销。 |

**Tier A 小计 ~847 行**（其中 ~520 行是脚本/模板/test 的⚪维护代码，~327 行是🟡主线程散文+🔴worker 死字段）。这是最大纯删面，**风险最低**——全部已亲验无活 consumer。

### Tier B — 高 context 杠杆 simplify（红线相关，只去重不删语义）

| # | 改什么 | 行数 | context | 关键约束 |
|---|--------|------|---------|---------|
| B1 | **Worker 启动序列去重**：`worker-loop.md.tmpl` 锚点 与 启动必读 handbook `execution-worker-dispatch.md` 逐字重复 TDD/commit/failure/verdict；pack-executor.md body 又复述一遍；three-failure 单 agent 内出现 **4 次** | ~113 | 🔴🔴 | **最高真实 token 杠杆**（Worker 是 5+ pack 自治长跑，每 dispatch 全价）。**红线1**：worker-loop 含 compaction 恢复骨架（Step3 读 execution-state 重建 packs_in_session、status==committed 跳过、artifact 写入）——**只删与 handbook 逐字重复的执行细则散文，保留恢复骨架 + 交叉引用**。AGENT-02 顺带消除 body 里 pack-level 旧 verdict 枚举 vs plan-level 的漂移。改 `.tmpl` 后跑 build.sh。 |
| B2 | **envelope 契约去 worker 端死负载**：完整 DISPATCH_ENVELOPE 撰写模板逐字注入 3 处（execution SKILL / plan-writing SKILL / worker handbook），但 **worker 不派 pack、只读 envelope 个别字段** | ~25 | 🔴 | envelope 是 Tier-1 硬门（validate-plan-dispatch/parse-envelope）真校验的契约，**不删**，但合并到单一 home + worker handbook 端降为"你要读的字段：plan_path/repair_round/disposition_refs/resume_from_pack_id"。注意同步放宽 verify-maturity:116 的存在性 grep。 |
| B3 | **preamble + signpost 合并到 `_shared` 单一 home**：signpost(17行×5 skill)+preamble(T1/T2/T3 公共核三遍 + Decision Brief 23 行注入 5 skill) | ~104 | 🟡×5-6 | **最高注入杠杆**（一处 .tmpl 改传播全部 skill；多 phase session 每转 phase 重吃）。**红线3**：Decision Brief 是人在环业务门格式——只去重不删语义。**护栏**：必须保留 ≥1 个 canonical preamble/signpost 锚点（verify-maturity L29/L65/I1/I3 + 3 个 build test 硬要求 resolver≥9、≥1 锚点）；逐 skill 保留 transition 指令（写 cursor.phase 恢复源）。沿用已验证的 `_shared` @引用先例（10+ 文件在用）。 |

### Tier C — 中等 simplify

| # | 改什么 | 行数 | context | 备注 |
|---|--------|------|---------|------|
| C1 | **execution SKILL 散文瘦身**：5 个 state.sh 子命令完整 bash 语法手册(`:222-257`)压成一行指针；删内嵌 confidence 表(`:316-322`，与 _shared 波段漂移 5-7 vs 4-6)；去重 Plan 必备字段清单第二/三份 + cursor 指令两份 | ~50 | 🟡 | execution SKILL 是 455 行最重 skill。confidence 表删内嵌副本顺带消除波段漂移（权威在 _shared）。 |
| C2 | **删 hook 产的无 act 字段**：`pack_summary`（built-but-unwired——注释"reviewers jq this"是从未实现的预期 consumer，reviewer 实际直读 pack-returns/ 源；删 or 补完同 A1 逻辑）+ `drift_warnings[]`（真 guard 是 worker 自 revert，数组无人 act，但 136 行每次 Edit/Write 重跑 plan-parse）+ `pack-returns.open_items`(vestigial) | ~104 | 🔴+⚪ | **保留** `open-items.json`（真 triage 恢复源，agent-return-handler 读它做 BLOCKED）。删 detect-worker-scope-drift 整脚本需同步删 hooks.json 2 条注册 + 2 个 test。drift WARN 实时信号靠 hook additionalContext，删数组不影响。 |
| C3 | **merge route 散文去重**：3 个 merge reference 开头的 Self-Read Protocol 三处近逐字；冲突分类法在 discovery 顶部表+dispatch prompt 二次罗列；merge-brief-template 各段引导注释 + 35 行示例 mini-brief | ~75 | 🔴 | **红线1**：merge-brief 是 cursor.reference 恢复源——9 段标题/META/§4 conflict 结构**不动**（check b/c/verify/schema 共同解析）。只删引导散文密度+示例块。强制力由 validate-multi-pr-dispatch check(d) 保证，散文收口不减强制。 |
| C4 | **删 4 处冗余手动 update 指令**：workflow SKILL.md:105/140/162/185 手动写 `last_gate_phase/timestamp` | ~12 | 🟡 | 亲验 `cmd_transition(state.sh:314)` 已在同一时刻自动写。WF-03 零功能影响。同步把 workflow-infrastructure.md:201 语义说明改为"transition 自动写的目标 phase"。 |

### Tier D — 低优先 / 可选

| # | 改什么 | 行数 | 备注 |
|---|--------|------|------|
| D1 | legacy `cross-plan-contract-map` 迁移提示在 6 处复读 → 压成架构文档单处注脚 | ~10 | 这是"变更历史"性质散文，违反全局规范"文档禁写历史"。 |
| D2 | mockup-as-acceptance 规则单 component 内复述 6 次 → 留一处权威+终引用 | ~8 | **规则本身被 user memory 锁定，绝不删**，只收冗余复述。 |
| D3 | explorer 选型规则 4+ 处复述去 re-inline；顺带修预算公式文档漂移（3P+12 真值，部分文档写 2P+6） | ~12 | 预算漂移已在两份旧评估点名，独立修复项。 |
| D4 | `merge-brief-v1.json` schema body 瘦身（293→META+段落描述） | ~180 | ⚪ schema 是 spec-only 无 runtime 加载；但兼作 Coordinator authoring spec，过度塌缩丢段落契约。Route3 罕用，最低优先。护栏：保留 10 个顶层 key（verify-maturity 6.1 要 ≥10，零余量）。 |
| D5 | `agent-return-handler.sh` 7 路 emit verbose 文案塌缩 | ~30 | **⚠ 与 codification 方向冲突**（见 §3）。load-bearing 的是 `:87` ingest 调用（恢复写，必留），不是 emit 文案。塌缩须保留每路路由关键词否则 e2e test 红。**先看 user 是否走 code-spine 再动。** |

---

## 2. 各 Agent 准备税（干核心活前背的规则负载）

| Agent | 真正干活 | 启动前规则负载 | 最大可削 |
|-------|---------|---------------|---------|
| **Worker**（pack/complex-pack-executor）🔴 | 按 plan 写代码跑 TDD commit | **~260 行**：worker-loop 锚点(128) + 必读 handbook 两层逐字重复 verdict/three-failure/commit/项目感知/repair；three-failure 单 agent 内 **4 次**；envelope 完整模板（worker 根本不派 pack） | B1+B2+AGENT-01/02/05/06/07：去重保留恢复骨架，**worker 准备税是每次 dispatch 全价烧——最高 context 价值** |
| **Coordinator（execution）** 🟡 | 派 Worker + 记 agentId + 处置 findings + 推进 checkbox | **~120 行**（SKILL 455 最重）：state.sh 语法手册 + confidence 表(漂移) + learnings 死散文(指向不存在脚本) + 字段清单复述×3 + cursor 指令×2 + Decision Brief 23 行 | A1+C1：净瘦 SKILL ~80 行 |
| **merge-worker/explorer/analyst** 🔴 | 发现/分类/修冲突 | **~80 行**：3 reference 各自 Self-Read Protocol 近逐字 + 冲突分类二次罗列 + 9 段引导散文+示例；还指挥自监控一个 **v3.9.4 已删除的 turn 上限** | C3 + 删 4 agent 死 Turn Budget 段 |
| **任意 phase Coordinator** 🟡×5-6 | 本 phase 业务 | **~76 行**：每 phase skill 顶部 preamble+signpost 公共样板逐字；final-review 还被注入与本 phase 无关的 misfit 行 | B3：抽公共核到 _shared，variant 只留差异 |

---

## 3. 需要你拍板的业务决策（本审计「删」vs 代码化方案「加」的真冲突）

这三处本审计建议删/缩，但 `plugin-control-flow-codification.md` 建议加/留，**方向相反，是你的架构方向决策，我不替你定**：

1. **要不要给 explorer / plan-writer / analyst / merge-worker 加结构化 return schema？**（codification M5 加 vs 本审计 AGENT-01/02 直接 trim 散文）
   - 走 M5 = 花前置成本（schema+parser+测试）把路由强制力从 Tier-3(自愿) 升到 Tier-2(hook 强制)。**若走 M5，部分"冗余"散文会变成 schema 的 spec 来源，删法要变（保留字段定义、删人话复述）。**
   - 不走 M5 = AGENT-01/02 可直接 trim。

2. **agent-return-handler 的 emit 文案是冗余复述还是单一权威路由？**（codification §4 扩 emit 为路由权威 vs 本审计 D5 缩 emit）
   - 走 code-spine = emit 文案应留为权威、SKILL.md 散文反而该删（方向反转）。
   - 不走 = D5 缩减成立。

3. **state.sh 内部审计账本（mutations / self_verifications / review-history）保留还是精简？**
   - 本审计按 "context 烧" 轴判**保留**（worker 永不读，删了省 0 agent token，churn 高）。
   - 但若你另有"可追溯性 vs 极简"的诉求，可单独处理。`review-history` 三者中最该留（有活跃 hook 消费者 + 写进 design/plan 文档的人类可读复审历史表）。

---

## 4. 红线（删减绝不触碰）

- **磁盘状态平面 = compaction/跨会话恢复唯一真相源**：active-run-id / workflow-state(cursor.phase/last_gate_timestamp) / execution-state(packs status) / scope-contract / merge-brief(9 段+META+§4)。worker-loop 的恢复骨架、open-items.json、ingest 写入路径属此。
- **跨模型审查独立性**：codex-companion.mjs 派发链、review gate、content-only review-dispatch 模板。
- **人在环业务门**：Decision Brief 格式、Direction Check、Business report 段、verdict ENUM 路由行。
- **Tier-1 硬门**：guard-premature-push / guard-doc-edit / validate-*-dispatch / enforce-plan-commit / gate-codex-review / session-start 环境检查。

---

## 5. 建议执行顺序

1. **先做 Tier A（纯删，~847 行，零功能损失，已亲验）**——风险最低、立刻减维护面 + 消除"改死模板/死路径"陷阱。每删一项同步其 verify-maturity 断言与 test，跑 `run-all-tests.sh` + `verify-maturity.sh` 全绿。
2. **再做 Tier B（最高 context 杠杆 simplify）**——B1 worker 启动序列去重是真实 token 收益最大处（每 dispatch 全价）。改 `.tmpl` 必跑 `build.sh --apply → --check`，逐项守住红线护栏。
3. **Tier C/D 按余力**。
4. **§3 三个业务决策先问你**——尤其 M5（决定 AGENT-01/02 和 D5 的删法），不要让本审计与 codification 两个方案同时落地产生矛盾。
5. **验证边界说清楚**：我亲验的是 **consumer 缺席**（删了没人引用 = 删除安全），**不是迁移正确性**。每条的"迁移"步骤（如"retarget verify-maturity:170 到 _shared/review-dispatch.md"、"这 5 个 build test 会坏"、"删这些断言"）是子代理的**预测，尚未实测**。"safe-to-cut" 的唯一证明是**删后测试套件全绿**——执行时一项一删，每删一项跑 `run-all-tests.sh`+`verify-maturity.sh`，绿了才确认下一项，把每条迁移步骤当未验证对待。
6. **同文件改动要排序**：多条 cut 触同一文件（execution SKILL.md ← A1+C1+B1 相邻；SKILL.md:313 ← A1 与 A4 都碰），按顺序串行改，避免 edit 冲突、保持测试逐步全绿。

> 诚实提示：行数 ≠ token 节省。🟡 主线程散文受 prompt cache 摊薄（暖缓存边际 ~10%）；🔴 sub-agent（worker/explorer/merge-worker）启动负载每次 dispatch 全价，是真实 token 大头；⚪ 脚本/模板/test 是维护面收益不烧 agent context。**最高 ROI 集中在 Tier A 的纯删（消陷阱）+ Tier B1 的 worker 去重（真省 token）。**

# 分册 08：迁移、灰度与验收

> **本分册职责**：把 `01`–`07` 的目标设计排成**低风险、可分期、可回滚**的落地路径，给出现状↔目标差异对照、量化验收信号、不变量回归测试矩阵、回滚策略与版本号同步。本分册不提出新设计，只做"排期 + 验收 + 守门"。
>
> - 绑定上游：`00-overview.md`（灵魂契约）。本分册与骨架冲突 = 本分册错。
> - 适用对象：`plugin/`（当前 v3.10.0，已亲自 `jq` 核验 `plugin.json` 与 `marketplace.json` 同为 `3.10.0`）。
> - 消费方：`orchestrate-plan-writing` 直接把本分册的分期表拆成 plan/pack；每期的回归测试矩阵直接进 pack 的 acceptance criteria。
> - 方法论基线：`bash plugin/scripts/run-all-tests.sh`（43 个测试套件，已逐目录核验：scripts/tests 12 + hooks/tests 18 + build/tests 13）、`bash plugin/scripts/verify-maturity.sh`（§8 端到端成熟度）、`bash plugin/build/build.sh --check`（当前 **exit 0 干净**，已核验）。

---

## 0. 结论先行（给 plan-writing 直接消费）

1. **一条铁律统领全部排期**：**先建机器执行点，再删假机制**。删假字段（`phase_skip`）、删死代码（`cleanup-before-push.sh:51`）、降级 schema（merge-brief）这类"减法"动作，必须排在它们的"替代机器点"就位且测试通过之后。顺序错 = 制造孤儿（删了唯一记录档位的字段、却没有 routes 清单接住）。这是 `03` §5、`07` §6、`02` §4 共同的时序硬约束，本分册把它落成 6 期的依赖图。

2. **关键路径只有一条**：`P1 (routes 清单建数据) → P2 (state.sh/hook 改读清单) → P3 (Light Lane 接 hook 豁免 + 升级门) → P6 (删假 phase_skip)`。`02` 是整条链的地基（`03`/`05`/`07` 多处标"02 必须先就位"），必须最先做。其余三期（`P4` 预算降仪表、`P5` skill/agent/hook 重构与漂移根治）**与关键路径解耦、可并行**，因为它们不依赖 routes 清单的查询入口（`04` 只需 routes 携带 `budget` 占位字段，`05`/`06`/`07` 的多数动作是 build/agent/文档层独立重构）。

3. **唯一从无到有的新建机器守卫是核心红线自动升级**（`01` §3.5 标为不变量 3.5 的唯一新建项）。它在 `P3` 落地（Entry 判定线 + 升级门），是 D1 激进默认轻档的安全闸；本分册在 `P3` 的回归测试里强制一条"红线关键词改动被升 formal"用例，否则 D1 不安全。

4. **每期都是独立可提交可验证的闭环**：每期结束跑"该期受影响的测试子集 + `verify-maturity.sh` + `build --check`"三件套，全绿才 commit（频繁 scoped commit，`IMPLEMENTATION-LOG.md` R1）。版本号在**每期收尾**按 semver 递增并同步 `plugin.json` + `marketplace.json` 两处（CLAUDE.md 硬规则，本分册 §6）。

5. **回滚粒度 = 期**：每期一个（或一组）commit，routes 清单读取处全程保留 **fail-open 回退**（`02` §6.2：查不到 route 回退全量旧矩阵），所以即使某期 hook 改读清单出错，行为退化为现状而非更严——这让回滚的最坏情况是"退一期 commit"，不是"系统卡死"。

---

## 1. 分期顺序与依赖图

### 1.1 期的划分原则

- **加法先于减法**：建 routes 清单（加）→ 改读（加）→ 接豁免/升级门（加）→ 删假字段（减）。
- **承重守卫零窗口期**：北极星不变量（`01` §3）对应的机器守卫（idempotency / doc-guard / push-block / merge-brief verify）在任何一期都不得出现"旧的删了、新的没接上"的中间态。涉及它们的改造（如 `07` merge-brief schema 降级）必须"保字段名+枚举 + 回归 test 守在同一 commit 内"。
- **解耦优先并行**：不在关键路径上的期（`P4`/`P5`）可与关键路径并行推进，缩短总周期，但各自独立 commit、独立验收。

### 1.2 六期依赖图

```text
                    ┌─────────────────────────────────────────────┐
关键路径（串行）：    │  P1 ──► P2 ──► P3 ──────────────────► P6      │
                    │ routes  改读   Light Lane+升级门   删假字段    │
                    │ 清单    清单                       (收尾减法)  │
                    └─────────────────────────────────────────────┘
                            ▲
解耦可并行：         P4 (预算降仪表) ── 仅需 P1 的 routes.budget 占位字段
                    P5 (skill/agent/hook 重构 + 漂移根治) ── 多数子项零依赖；
                       其中"validate-* 改读 routes""轮次截断 hook"挂 P2 之后
```

**严格依赖边（每条都有分册出处）**：

| 依赖边 | 出处 |
| --- | --- |
| `P3 → P1/P2`（Light Lane 的 hook 豁免/transition 直跳依赖 routes 清单与查询入口） | `03` §4 L5/L6 标 "02 必须先就位"；`03` §8 |
| `P6 → P3`（删 `phase_skip` 必须在 routes 清单 + hook 豁免 + 升级门 + 子模式锚点全就位后） | `03` §5 时序硬约束；`03` §4 L11 "L1–L10 全部就位" |
| `P4 → P1`（`cmd_budget_reinitialize` 公式与 routes 的 `budget` 占位字段对齐；预算降仪表只需占位） | `02` §3.2 budget 占位；`04` §7 "被 02 约束" |
| `P5(validate-* routes 化 / enforce-repair-round-cap) → P2` | `07` §2.3 / §6 P5 "须等 02 routes 库就绪"；`05` §3.3 截断 hook 依赖 routes 的 `repair_policy` |
| `P3(升级门 budget reinitialize 公式) → P4`（公式参数化） | `03` §3.6.1 "公式随 04 参数化"；`03` §8 "依赖 04" |

> **P3 与 P4 的相互软依赖说明**：`P3` 的升级门 `cmd_budget_reinitialize` 用到 `P4` 参数化后的公式；`P4` 的 `attendance_mode` 标志可被 `P3` 的 Entry 判定复用（`04` §7）。处置：`P4` 在公式参数化这一子项上**先于** `P3` 的升级门子项落地（`P4` 整体可与 `P1`/`P2` 并行，但其"公式抽常量"子任务排在 `P3` 升级门之前）。这不构成环——只是 `P3` 内部"升级门"这一 pack 等 `P4` 的"公式参数化"pack 完成。

### 1.3 各期内容 + 独立闭环边界

| 期 | 名称 | 落地内容（引分册） | 关键路径 | 独立闭环验收（除三件套外） |
| --- | --- | --- | --- | --- |
| **P1** | routes 清单建数据 | 新建 `state-schema/routes-v1.json` + meta-schema，如实编码现 4 enum 形态（formal/direct-repair/bug-investigation/multi-pr-merge）+ 预置 `light` 子形态（不接 hook）；新建 `test_routes_manifest.sh`（`02` §4.4/§5.1） | ✅ | `routes-v1.json` 可被 `jq` 解析；每个 enum route 有记录；`route` enum、idempotency、cursor 全未动 |
| **P2** | state.sh/hook 改读清单 | `transition_allowed()` 读 `global_transitions ∪ routes[r].phase_transitions`（fail-open 回退旧矩阵）；`cmd_init` 读 `budget.init`；三 hook（`validate-plan-dispatch.sh:75` / `dispatch-route-worker.sh:48-54` / `validate-pack-manifest.sh:45-48`）改读 `dispatch_shape`；删 `state.sh:75` 行尾历史注释、`cleanup-before-push.sh:51` 死 `route=="hotfix"` 改读 `commit_format`（`02` §3.4/§4） | ✅ | 旧 state 文件零迁移可读（续传不破）；现有 transition 测试集全绿；`grep 'Pack 2.14\|Plan 005' state.sh` 零命中 |
| **P3** | Light Lane + 升级门 + 子模式 | schema route enum 加 `light`；Entry 判定线 + **核心红线升级关键词表**（不变量 3.5 唯一新建）；hook gate 豁免读清单（点 A）；transition light 直跳（点 B）；新命令 `cmd_budget_reinitialize`（unlimited→bounded + 翻 formal）；Closing 读 `pending_post_push_reviews`（修 hotfix 缺口）；spike 临时目录隔离（`03` §3–§4 L1–L10） | ✅ | 升级门测试；红线改动被升 formal 用例；hotfix 事后补审兑付；spike 不占编号 |
| **P4** | 预算降仪表 | `attendance_mode`（default afk）/ `review_credit` / `budget_profile` 加 schema（给 default）；公式抽常量 + per-run 覆盖；双模式 80%/100% 分叉（删 80% 硬 DC，AFK 软续到顶停）；`cmd_budget_credit`（reflux 归还）；`track-effort-budget.sh` 删或降（删 effort 2×）（`04` §3–§4） | ⛔（并行） | AFK 80% 不被 exit 2 拦；在场 80% 仍停；reflux 归还生效；公式可覆盖；到顶 100% 仍硬停 |
| **P5** | skill/agent/hook 重构 + 漂移根治 | 参数化切片（`_shared` fragment 物化）；SKILL 流程散文移出；三套截断统一 `repair_policy` + 轮次截断 hook（挂 P2 之后）；agent twin 收口（failure-protocol/explorer-shared）+ 删 voice dead variant；build resolver 7→3 塌缩 + 禁止词 footer 单源；embed 矩阵；zoom-out 处置；mockup 接线；mutations/self_verifications 降 DEBUG；merge-brief schema 降散文；architecture-draft 重写校准（`05`/`06`/`07`） | ⛔（多数并行；validate-* routes 化 + 截断 hook 挂 P2） | build `--check` 零 diff；切片后逻辑面省 ≥30%；voice 每路径仍带 Anti-Sycophancy；merge-brief 承重字段保留 |
| **P6** | 删假 phase_skip（收尾减法） | 删 `state.sh:152` 写入 + `SKILL.md:68,70-75` Variant Table + `schema:19-23` + 2 个 test 断言；architecture-draft routes/切片/截断新事实回填（`03` §5、`05` §4.1 第 3 条） | ✅ | `grep -rn phase_skip plugin/` 零命中（除 08 决定保留的 deprecated 注释）；architecture-draft 与源码一致 |

> **`commit_format_override` 不删**（`03` §5 注、`02` §4.3）：hotfix 仍用 `hotfix-unreviewed` 标记。P6 只删 `phase_skip` 这个零消费假机制。

### 1.4 排期推荐序列（含并行）

```text
时间轴 ─────────────────────────────────────────────────►

关键路径:   [P1]──[P2]──────────────[P3]──────────────────────[P6]
并行轨 A:              [P4 公式参数化]──[P4 其余]
并行轨 B:   [P5 零依赖子项: 切片/twin收口/resolver塌缩/漂移根治/embed/zoom-out/mockup]
                          [P5 挂P2子项: validate-* routes化 + enforce-repair-round-cap]──┘
```

- **P1 必须最先、单独成期**：它只新增一个只读文件，零行为变更，风险最低，是所有下游的地基。
- **P4 公式参数化子项早做**：因为 P3 升级门要用。P4 其余（双模式/credit/删 effort）可滞后。
- **P5 零依赖子项随时插空**：build resolver 塌缩、agent twin 收口、漂移根治（architecture-draft 版本号 + bug-seed 描述）、embed 矩阵、zoom-out 处置、mockup 接线——这些不碰 routes，可在 P1–P3 任意时段并行 commit。
- **P5 挂 P2 子项**（validate-* 改读 routes、轮次截断 hook）排在 P2 完成后。
- **P6 绝对最后**：所有真机器点（P1–P5 含 P3 的 Light Lane）就位并测试通过后才执行减法。

---

## 2. 现状↔目标差异对照表（逐层 before/after）

> 每行给"现状源码锚点 → 目标 → 落地期"。锚点均来自 01–07 已核验 `file:line`，本分册抽取归并。

### 2.1 流程形态层（02/03）

| 维度 | 现状（before） | 目标（after） | 期 |
| --- | --- | --- | --- |
| 合法跳转 | `TRANSITION_MATRIX` bash 硬编码 27 行（`state.sh:73-98`），route 无关地全列 phase 推进 | `routes-v1.json`：`global_transitions`（route 无关 work-item）+ `routes[r].phase_transitions`（route-aware） | P1/P2 |
| route→budget 初始档 | `cmd_init` case 硬编码（`state.sh:134-145`） | 读 `routes[r].budget.init` | P2 |
| execution=plan-level | 字面量 `if [[ "$PHASE"=="execution" ]]`（`validate-plan-dispatch.sh:75`） | 读 `routes[r].dispatch_shape[PHASE]=="plan-level"` | P2 |
| 非-execution phase 白名单 | 硬编码 case 含已漂移的 hotfix/quickfix/spike/maintenance（`dispatch-route-worker.sh:48-54`） | 读 `dispatch_shape[PHASE]=="route-worker"` | P2 |
| manifest 仅 execution 查 | `case "$PHASE" in execution)`（`validate-pack-manifest.sh:45-48`） | 读 `dispatch_shape[PHASE]=="plan-level"` | P2 |
| 轻量旁路 | 假 `phase_skip`（零 hook 消费，`state.sh:152` 写 `[]`） | Light Lane = routes 一条数据 + hook 真豁免 gate + 一键升级门 | P3 |
| 轻档跳步强制 | 散文自觉（SKILL Variant Table），与 Hard Gate `SKILL.md:7,220` 打架 | 机器层 transition 不存在即拦（light 无 `workflow:discovery`，`02` §3.3） | P2/P3 |
| 升级门 unlimited→bounded | 不存在（`cmd_budget_initialize:909-914` 只从 pending_plan_count 进） | 新命令 `cmd_budget_reinitialize`（只从 unlimited 进 + 翻 formal） | P3/P4 |
| 核心红线自动升级 | **无任何机器实现**（`01` §3.5） | Entry 关键词表 + 升级门兜底（启发式 + 不变量兜底） | P3 |
| hotfix 事后补审 | `pending_post_push_reviews` 字段存在但 Closing 不读（`03` §1.6） | Closing 读它派事后审 + 清空 | P3 |
| spike 产出即弃 | 纯散文，无隔离 | 临时目录物理隔离 + 不占编号命令 | P3 |
| 死 hotfix 路由 | `cleanup-before-push.sh:51` 永不命中死代码 | 改读 `commit_format` 标志 | P2 |
| 历史注释 | `state.sh:75/:78/:96` 带 `Pack 2.14 / Plan 005` | 迁入 `global_transitions` 天然去注释 | P2 |

### 2.2 预算层（04）

| 维度 | 现状（before） | 目标（after） | 期 |
| --- | --- | --- | --- |
| 唯一硬阻断 | `validate-plan-dispatch.sh:66-72` 80% DC pending → exit 2 拦所有非 reviewer | 保留为 DC 执行点，但 80% 在 AFK 不写 DC，只在"在场过半"和"任意到顶"触发 | P4 |
| 公式 | `3*plan_count+12` / `effort=2×` 硬编码（`state.sh:916-917`），initialized 后不可变 | 抽常量 `REVIEW_PER_PLAN/REVIEW_FIXED_RESERVE` + `--review-total`/`--profile` 覆盖；执行期仍不可变 | P4 |
| reflux 重置 | `review_used` 只增不减（`SKILL.md:179` 明文不重置） | `review_credit` 字段 + `cmd_budget_credit`，`effective_used=review_used-review_credit` | P4 |
| AFK/在场标志 | 无 session-level 标志（`04` §1.5） | 新增 `attendance_mode`（default afk） | P4 |
| effort 维度 | `track-effort-budget.sh` 零独立 gate，唯一作用抢 DC 槽位（`04` §2 P4） | 删（方案 A）或降咨询（方案 B）；无论如何删"写 DC"能力 | P4 |

### 2.3 Skill/Context 层（05）

| 维度 | 现状（before） | 目标（after） | 期 |
| --- | --- | --- | --- |
| `_shared` 注入 | 每个派发 review 的 phase 整份 Read（review-dispatch 6576B / repair-routing 5753B / disposition-table 2760B），review-dispatch 被 10 处、repair-routing 被 9 处整份读 | build resolver 物化 fragment，step 只读需要的片段（运行时真省） | P5 |
| SKILL 流程散文 | signpost 硬编码 phase 序列（`signpost.md.tmpl:11-12`，注入 5 SKILL）+ 流程位置散文散落 | phase 序列移进 routes 数据；SKILL 留薄 step→reference 索引 | P5（依赖 P1/P2） |
| 三套截断 | execution(2+1)/final-review(1+1)/plan-review(2) 各写散文，**无 hook 设上限** | 统一 `repair_policy` 参数 + 轮次截断 hook（`enforce-repair-round-cap.sh`）机器强制 | P5（hook 挂 P2） |
| architecture-draft 漂移 | `:5` 自标 3.8.0（实际 3.10.0）；`:1226` bug-seed 过时描述 | 校准版本头 + bug-seed 描述对齐 `bug-investigation-route.md:63`；routes/切片/截断新事实回填 | P5（回填挂 P6） |
| Path A | 文档内无"已删"假声明，canonical 全程活着 | **不删**，确认保留（避免误读骨架去补删） | P5（纪律项） |

### 2.4 外部 Skill 层（06）

| 维度 | 现状（before） | 目标（after） | 期 |
| --- | --- | --- | --- |
| embed 矩阵 | 4 agent 未嵌 skill；plan-writer/docs-worker 正文 invoke 但 frontmatter 无声明 | complex-code-explorer/plan-writer 加 `improve-codebase-architecture`；docs-worker 加 `frontend-design` | P5 |
| zoom-out | 6 处引用 + session-start 声明已装，但运行环境不可用（悬空） | 默认 B：删声明 + 路由改 code-explorer/improve-codebase-architecture | P5 |
| impeccable | 全仓零引用 | Discovery mockup 段接线（生成态 invoke 可选） | P5 |
| frontend-design | 被引用但不在 session-start:58 声明 | 补进声明（消除引用未声明裂缝） | P5 |
| internalize（to-issues） | `issue-splitting.md` 内化，原 skill 零引用 | 退回 invoke 优先 + 项目专属薄层；不可用则保内化 + 溯源注释 | P5 |

### 2.5 Agent/Hook/Build 层（07）

| 维度 | 现状（before） | 目标（after） | 期 |
| --- | --- | --- | --- |
| executor twin 非-worker-loop 重叠 | 双份手写（失败协议表等） | 新增 `failure-protocol` anchor 单源 | P5 |
| explorer twin | 除 voice 外完全双份手写 | 新增 `explorer-shared` anchor 单源 | P5 |
| voice dead variant | `voice-directive.md.tmpl:53-56` codex-reviewer 块零注入 | 删除 | P5 |
| 禁止词 footer | 13 个 variant 各写一遍 | 公共 footer 单源注入一次 | P5 |
| build resolver | 7 个文件（已核验：control-envelope/preamble/review-dispatch/sendmessage-resume/signpost/voice-directive/worker-loop） | 塌缩为 build.sh 内 3 类内联 case | P5 |
| fire-on-every-Bash hook | gate-codex-review/track-review-budget 无 if（脚本内自闸门） | 加 `if:` 降频（双层保险）；guard-premature-push 保留无 if（双责硬闸门） | P5 |
| mutations/self_verifications | 每次 update/transition append，运行时零消费 | 降 `STATE_DEBUG=1` 开关，init 仍初始化空数组 | P5 |
| merge-brief schema | 293 行嵌套 JSON Schema，运行时不读（正则消费 markdown） | 降 ~50 行散文骨架，**保字段名+枚举** | P5 |
| validate-* phase 字面量 | `validate-plan-dispatch.sh:75` / `validate-multi-pr-dispatch.sh:47` / `gate-codex-review.sh:30` | 改读 routes 清单 | P5（挂 P2） |
| state.sh 死行 | `:75` 确认死；`:78`/`:96` 待 02 复验 | 删 `:75`；`:78`/`:96` 复验后处理 | P2/P5 |

---

## 3. 量化验收（对齐骨架 §8）

> 骨架 §8 给六个验收信号。本分册把每个落到**可观测指标 + 测量方法 + 归属期**。所有"降 token"数字按 `05` 口径为**保守量级估算**，最终精确值以本分册 §3.4 的实测流程为准——这里给方法不给承诺值。

### 3.1 明显降 token（骨架 §8.1，对应 P3/P5）

| 信号 | 测量方法 | 期 |
| --- | --- | --- |
| Light Lane 小改完全跳过 Discovery | 跑一个 `init --route light` 的小改，断言流程**不经** discovery/plan-writing/plan-review/final-review；省下 Discovery 的 ~9.5KB 指令 + 2 次 xhigh Codex job（骨架 §8.1/`03` §7.1） | P3 |
| execution 单循环 `_shared` 逻辑面注入 ↓ ≥30% | 切片前后对比一次完整 plan review + disposition + repair 的 `_shared` 注入字符数：现 ≈15089B（review-dispatch 6576 + disposition-table 2760 + repair-routing 5753）→ 切片后逻辑面 ≈9100B（`05` §1.4）。**方法**：以 `wc -c` 量 step 实际 Read 的 fragment 文件之和 | P5 |
| SKILL 流程散文移出 | execution SKILL.md 字符数较 20214B 下降（signpost phase 序列行 + 重复 Only/Never stop + 重复流程位置，估 2000–3500B，`05` §2.4）。**方法**：`wc -c skills/orchestrate-execution/SKILL.md` 前后对比 | P5 |
| embed 净增 << invoke 省量 | embed 矩阵增的 subagent 常驻 context vs invoke 散文重复 Read 的省量（`06` §8.1）。**方法**：抽样 explorer/plan-writer/docs-worker 启动 context 字节 + 散文 invoke 提示行净变 | P5 |

> **测量基线锚点（已核验）**：`review-dispatch.md=6576B`、`repair-routing.md=5753B`、`disposition-table.md=2760B`、`execution/SKILL.md=20214B`（`05` §1.1/§2.1，本分册采信其 `wc -c` 口径）。`build --check` 当前 exit 0，提供切片重构前的渲染基线。

### 3.2 明显提速（骨架 §8.2，对应 P3/P4）

| 信号 | 测量方法 | 期 |
| --- | --- | --- |
| 日常小改轻档直达 | 同 §3.1 第 1 行：从输入到 commit 不被完整流程拖 | P3 |
| 预算不再中途硬卡 | `attendance_mode=afk` + formal，跑到 80% 派发**不被 exit 2 拦**（§3.5 回归测试），只到 100% 一次 escape hatch（`04` §6.1） | P4 |

### 3.3 流程相对稳定（骨架 §8.3 地板，对应 P2/P3/P5）

| 信号 | 测量方法 | 期 |
| --- | --- | --- |
| 轻档跳步机器拦 | `transition --from workflow --to discovery` 对 `route==light` 返回非 0（机器拒绝误跳），对 formal 仍合法（`02` §8.2、`03` §7.2） | P2/P3 |
| 轮次截断机器强制 | 派发修复时 `repair_round` 超 `max_repair_rounds`（含 RCA 余量）被 `enforce-repair-round-cap.sh` exit 2 拦（`05` §3.5、`07` §2.4） | P5 |
| 该调的 skill 由 frontmatter 保证 | embed 矩阵：`grep skills: plugin/agents/*.md` 匹配 `06` §3.2 矩阵 | P5 |

### 3.4 实测复核流程（本分册收口，骨架要求"量化以 08 实测为准"）

`05`/`06` 多处把精确数字标"待 08 实测"。本分册定义实测方法（不在文档里写死承诺值，避免造新漂移）：

1. **切片省量实测**：在 P5 落地后，对 execution 一次完整 review-repair 循环，逐 step 用 `wc -c` 量"实际被 Read 指令指向的文件"字节和，与切片前整份 `_shared` 字节和对比，记入 `IMPLEMENTATION-LOG.md`。
2. **SKILL 瘦身实测**：`wc -c` 量 6 个 orchestrate SKILL.md 改造前后字节，记差值。
3. **Light Lane 提速实测**：跑一个真实小改的 light run，记录经过的 phase 数与省下的 Codex job 数。
4. **结论只写量级 + 实测值，不预先承诺**（`05` §1.4/§2.4 已声明本分册口径）。

### 3.5 逃逸旁路真实可用（骨架 §8.4，对应 P3）

| 信号 | 测量方法（→ 回归测试） | 期 |
| --- | --- | --- |
| Light Lane 有机器执行点 | `route==light` 时 `validate-plan-dispatch.sh` 跳过 Step 4 budget-init（light 未 budget initialize 仍能 dispatch）；transition 允许 `workflow→execution` 直跳 | P3 |
| 一键升级门存在且经测试 | `init --route light`(unlimited) → `budget reinitialize --plan-count N` → 断言 `budget_status=initialized` + `route=formal` + `review_total=公式值` + 后续 dispatch Step 4 门重新生效（`03` §7.3） | P3 |
| 核心红线升级用例 | 构造一个命中计费关键词（billing/quota/idempotency 等）的改动，断言被强制升 formal（`01` §6.4 新建测试）。**这是不变量 3.5 的回归** | P3 |

### 3.6 漂移归零（骨架 §8.5，对应 P5/P6）

| 信号 | 测量方法 | 期 |
| --- | --- | --- |
| 版本一致 | `diff <(jq -r .version plugin/.claude-plugin/plugin.json) <(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)` 空；architecture-draft 版本头与 plugin.json 一致 | P5/每期收尾 |
| bug-seed 描述对齐 | `architecture-draft.md:1226` 与 `bug-investigation-route.md:63` 一致（不再说"创建 seed file"） | P5 |
| 假字段归零 | `grep -rn phase_skip plugin/` 零命中（除 deprecated 注释） | P6 |
| 死代码归零 | `grep 'Pack 2.14\|Plan 005' plugin/scripts/state.sh` 零命中；`cleanup-before-push.sh` 无死 `route=="hotfix"` 分支 | P2 |
| 无"文档说删代码还活/代码删文档还描述" | 漂移对账（§3.6 + `01` §6.5 承重字段 grep 对账） | P5/P6 |

### 3.7 能力零丢失（骨架 §8.6，对应全程 → §4 不变量回归）

见 §4：17 项保留项逐条映射到现有/新建测试，每期跑对应子集守住。

---

## 4. 不变量回归测试矩阵（守骨架 §6 + §5）

> **铁律**：每期跑"该期受影响测试子集 + `verify-maturity.sh` + `build --check`"。本节给①北极星 5 不变量的测试守卫；②17 保留项的测试映射；③每期必跑清单；④voice-directive 去重后 Anti-Sycophancy 的逐路径验证法。

### 4.1 北极星 5 不变量 × 测试守卫（`01` §3）

| 不变量 | 现有机器守卫锚点 | 守卫测试（已核验存在） | 风险期 |
| --- | --- | --- | --- |
| 计费/LINEAGE（idempotency） | `validate-plan-dispatch.sh:40,52-56,141` | `test_idempotency_replay.sh`（已核验：check→NEW、append、second check→DUPLICATE）、`test_validate_plan_dispatch.sh`、`test_agent_id_hook_guard.sh` | P2/P3/P4（任何 dispatch 改造） |
| 状态权威（磁盘续传） | `state.sh:155,313-314`、`state-lock.sh`、`track-execution-state.sh:42-49` | `test_state.sh`、`test_state_cursor_reference.sh`、`test_track_execution_state_next_suppression.sh` | P2（transition 改读清单）/P5（mutations 降级） |
| 数据权威（Worker 禁改 docs/） | `guard-doc-edit.sh:37-41` | `verify-maturity.sh`（guard-doc-edit 间接）、`test_validate_plan_dispatch.sh` | P3（Light Lane 不豁免） |
| 质量门最小集（必验/doc-guard/push-block） | `guard-premature-push.sh:17-20,66-76` | `test_enforce_plan_commit.sh`、push-block（verify-maturity） | P3（Light Lane）/P5（hook if 降频） |
| **核心红线自动升级（新建）** | **无 → P3 新建** | **新建用例**（§3.5 第 3 行）：红线关键词改动被升 formal | **P3（唯一从无到有）** |

### 4.2 17 保留项 × 测试映射（`01` §1）

| 保留项 | 守卫测试 / 验证法 | 风险期 |
| --- | --- | --- |
| 1 Document-as-Context envelope | `test_envelope_parse.sh`、`test_envelope_plan_id_consumers.sh`、`test_validate_plan_dispatch.sh` | P2 |
| 2 Plan 级自治 Worker | `test_state_agent_id_plan_level.sh`、`test_agent_return_handler_plan_level.sh`、`test_worker_loop_e2e.sh` | P2 |
| 3 磁盘状态续传 | `test_state.sh`、`test_state_cursor_reference.sh`、`test_state_pack_progress.sh` | P2/P5 |
| 4 Source Stability（last_gate） | `01` §6.2：grep `state.sh:313` 语义未删 + transition 仍写 `last_gate_timestamp` | P2 |
| 5 子代理必验 | 散文（无 test）；prompt 注入守 | 全程 |
| 6 Codex 外审 + 模型分层 | `test_gate_codex_review.sh`、`test_review_model_tiers.sh` | P3（Light 免外审不删门）/P5 |
| 7 抑制幻觉四件套 | `test_review_evidence_table.sh`、`test_confidence_injection.sh` | P5（切片移文件不删内容） |
| 8 Discovery 双文档 + Explorer 门控 | 散文；`05` 瘦身不删门控 | P5 |
| 9 Mockup 原子拆解 | Plan Review reviewer 门控（散文）；`06` mockup 接线 | P5 |
| 10 Worker 禁改 docs/ + checkbox | `guard-doc-edit`（verify-maturity 间接） | P3/P5 |
| 11 Anti-Sycophancy（voice-directive） | `test_voice_injection.sh` + §4.4 逐路径验证 | **P5（去重最高风险）** |
| 12 vertical-slice/tracer-bullet + to-issues | 散文 + `06` 退 invoke | P5 |
| 13 idempotency_key | `test_idempotency_replay.sh`（见 §4.1） | P2/P3 |
| 14 成本护栏防无限烧 | `test_budget_direction_check.sh`、`test_effort_budget_*.sh`、`test_need_fresh_worker_continuation.sh` | **P4** |
| 15 gstack 不借鉴 | 设计记忆（无 test，勿再提） | — |
| 16 merge --squash 禁 + 未勾选阻断 push | `test_enforce_plan_commit.sh`、push-block | P5 |
| 17 merge-brief 字段约定 | `test_state_merge_brief.sh`、`test_validate_multi_pr_dispatch.sh`、`test_multi_pr_merge_e2e.sh` | **P5（schema 降级最高风险）** |

### 4.3 每期必跑清单

> 套件名均来自 `run-all-tests.sh` 扫描的 `scripts/tests/` + `hooks/tests/` + `build/tests/`（已核验存在）。

| 期 | 必跑测试子集 | 全局闸门 |
| --- | --- | --- |
| **P1** | `test_routes_manifest.sh`（新建）、`test_route_keyword_routing.sh`、`test_state.sh` | `run-all-tests.sh`（确认零回归）+ `verify-maturity.sh` |
| **P2** | `test_state.sh`、`test_validate_plan_dispatch.sh`、`test_validate_pack_manifest.sh`、`test_envelope_plan_id_consumers.sh`、`test_state_cursor_reference.sh`、`test_idempotency_replay.sh`、`test_routes_manifest.sh` | `run-all-tests.sh` + `verify-maturity.sh`（含 `state.sh transition matrix enforced` / `init formal defers budget` / `transition` 续传断言） |
| **P3** | `test_hotfix_post_push_review.sh`、`test_route_keyword_routing.sh`、新建升级门 test、新建红线升级 test、新建 spike 隔离 test、`test_validate_plan_dispatch.sh`、`test_idempotency_replay.sh` | `verify-maturity.sh`（R3-05 hotfix/spike/maintenance grep）+ `run-all-tests.sh` |
| **P4** | `test_budget_direction_check.sh`、`test_effort_budget_weighting.sh`、`test_effort_budget_plan_level.sh`、`test_need_fresh_worker_continuation.sh`、`test_state.sh`、新建 attendance/credit/双模式 test | `verify-maturity.sh:79-90`（budget defer/initialize 断言需随公式参数化更新）+ `run-all-tests.sh` |
| **P5** | `build/tests/` 全套（尤 `test_voice_injection.sh`、`test_review_evidence_table.sh`、`test_resolvers.sh`、`test_build_check.sh`）、`test_state_merge_brief.sh`、`test_validate_multi_pr_dispatch.sh`、`test_multi_pr_merge_e2e.sh`、新建 `enforce-repair-round-cap` test | `build --check` **exit 0 零 diff**（塌缩/切片核心闸门）+ `verify-maturity.sh` + `run-all-tests.sh` |
| **P6** | `test_route_keyword_routing.sh`（断言改写）、`test_hotfix_post_push_review.sh`（断言改写）、`test_state.sh` | `grep -rn phase_skip plugin/` 零命中 + `run-all-tests.sh` + `verify-maturity.sh` |

> **测试断言会被改动的提醒（给 plan-writing：改/删断言进同一 pack 验收）**：
> - P4 删 effort 维度破坏：`test_effort_budget_weighting.sh`、`test_effort_budget_plan_level.sh`、`test_need_fresh_worker_continuation.sh`、`test_state.sh`、`verify-maturity.sh:89`（effort_total=36 断言）——必须随删维度同步改/删（`04` §3.6/§5 R4）。
> - P5 mutations/self_verifications 降 DEBUG 破坏：`test_state.sh`（mutations/self-verify 断言）、`verify-maturity.sh:272-274`（R3-12 mutations grep）——改为"DEBUG 模式才断言"或删（`07` §3.2）。
> - P6 删 phase_skip 破坏：`test_route_keyword_routing.sh:34-36`、`test_hotfix_post_push_review.sh:22-25`——改为 light route + submode 断言（`03` §5 C5/C6）。
> - P5 SKILL Variant Table 重写若删 hotfix/spike/maintenance 字样：`verify-maturity.sh:239-244`（R3-05 grep，已核验）会红——这些关键词应仍在 SKILL Variant Table（`02` §4.4），grep 仍通过；P6 改 Variant Table 时须保留关键词或同步改 check。

### 4.4 voice-directive 去重后 Anti-Sycophancy 逐路径验证（P5 最高风险）

`07` §4.3 把派发路径分三类，去重（删 dead variant + 禁止词 footer 单源）后**每条仍带 Anti-Sycophancy** 的验证法：

| 派发路径 | 验证方法 |
| --- | --- |
| 7 个 sub-agent（executor×2/explorer×2/plan-writer/docs-worker/root-cause-analyst） | `--apply` 后 `grep` 每个 agent `.md` 的 voice anchor 内含禁止词 footer 行；`test_voice_injection.sh` 全 PASS（已核验存在） |
| 6 个 Coordinator phase SKILL（workflow + discovery/plan-writing/execution/final-review/multi-pr-merge） | 同上 grep 6 个 SKILL 的 voice anchor 渲染产物含 footer |
| codex-review / adhoc | **不走 voice footer**（现状即如此，非去重引入）——其 Anti-Sycophancy 等价物是 `review-dispatch.content-only` 的反幻觉四件套，由 `test_review_evidence_table.sh` 守（已核验存在）。删 voice dead variant 不影响此路径 |

**新增断言（`07` §4.3 要求，防 footer 单源化漏某 variant）**：在 `build/tests/` 加"每个 voice variant 渲染产物末尾含禁止词 footer 行"的检查。**零 diff 铁律**：禁止词 footer 单源化的换行/位置须逐字节对齐——`--apply` 出基线 → 单源化 → `--check` 必须 exit 0（渲染等价），否则全红（`07` §4.5）。

---

## 5. 回滚策略

### 5.1 分期回滚（粒度 = 期）

- 每期是一个或一组 scoped commit（`IMPLEMENTATION-LOG.md` R1：main 上 frequent scoped commit，AFK 不 push）。回滚一期 = `git revert` 该期 commit 区间。
- **关键路径回滚的安全网是 fail-open**：`02` §6.2/§7 规定 `transition_allowed` 查不到 route 回退全量旧矩阵、hook 读清单失败回退"按 execution 字面量"旧行为。所以即使 P2 改读清单的代码有 bug，行为**退化为现状而非更严**（绝不卡死正在跑的 run）。这让 P2 的回滚最坏情况是"退 commit"，不是"线上事故"。
- **P1 天然零回滚成本**：只新增一个只读 `routes-v1.json`，无读取方，不改任何行为；即使内容错，无人读 = 无影响。

### 5.2 减法期（P6）的回滚特殊性

- P6 删 `phase_skip` 是**不可 fail-open 的减法**——一旦删了字段，旧逻辑若还引用就报错。因此 P6 的回滚 = 把删除的字段/写入/断言 revert 回来。
- **缓解**：P6 排在最后，且 `03` §5 C4 给了过渡选项——schema 的 `phase_skip` 属性可"保留为 deprecated 注释一个版本周期"（本分册裁决：**采纳**，P6 先标 deprecated，下一个版本周期再物理删 schema 属性，降低回滚面）。`state.sh:152` 的写入与 SKILL Variant Table 可直接删（它们是写入方/散文，删了无运行时读取方）。

### 5.3 承重守卫的"同 commit"回滚约束

涉及承重字段的改造（P5 merge-brief schema 降级），其"保字段名+枚举"与"回归 test"必须在**同一 commit**。回滚时整 commit 一起退，不存在"退了 schema 降级却留着改坏的正则"的中间态（`07` §3.3/§3.4）。

### 5.4 回滚决策线（业务语言）

| 触发 | 动作 |
| --- | --- |
| 某期三件套（子集 test + verify-maturity + build --check）任一红 | 不 commit，本期内修；修不动则 revert 本期 |
| `build --check` 非零 diff（P5 塌缩/切片） | 立即停，逐字节对齐或 revert——这是漂移信号 |
| 续传回归（旧 state 文件读不了 / transition 卡死） | 立即 revert P2（fail-open 应已兜住；若仍卡死说明回退逻辑也错，整期退） |

---

## 6. 版本号同步（CLAUDE.md 硬规则）

> CLAUDE.md 明确：改版本号必须同时更新 `plugin/.claude-plugin/plugin.json` 的 `version` 与仓库根 `.claude-plugin/marketplace.json` 的 `plugins[0].version`，保持一致。已核验当前两处均 `3.10.0`。

### 6.1 每期收尾递增 + 双处同步

| 期 | 建议版本（semver minor 递增；本方案是结构重排，非破坏性对外 API） | 同步动作 |
| --- | --- | --- |
| P1 | 3.11.0 | 改两处 → `diff` 验证 |
| P2 | 3.12.0 | 同上 |
| P3 | 3.13.0 | 同上 |
| P4 | 3.14.0（可与 P2/P3 并行，版本按合入顺序取号） | 同上 |
| P5 | 3.15.0 | 同上 + architecture-draft 版本头同步校准到该版本 |
| P6 | 3.16.0（或并入 P5 收尾，视合入节奏） | 同上 |

> 版本号取号按**实际合入 main 的顺序**，并行期合入时顺延。建议每期 minor +1（结构重排是新增能力/重构，不删对外可见合同；Light Lane 是新增，预算降仪表是行为改进——均非 breaking）。

### 6.2 版本同步的机器验证（已是 verify-maturity 的一部分）

`verify-maturity.sh:137-146` 已含 "Version Sync" check（`jq` 比 plugin.json 与 marketplace.json）。每期收尾跑 `verify-maturity.sh` 即自动守住版本一致。额外可直接：

```bash
diff <(jq -r .version plugin/.claude-plugin/plugin.json) \
     <(jq -r '.plugins[0].version' .claude-plugin/marketplace.json)
```

P5 额外：`architecture-draft.md:5` 版本头与 `plugin.json` 一致（`05` §4.5），并入 P5 漂移根治的验收。

---

## 7. 风险与缓解（本分册视角）

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| **R1 顺序倒置造孤儿** | 在 P3 之前删 `phase_skip`，档位无处记录 | P6 硬排最后；plan-writing 把 P6 的 `blockedBy` 绑死 P1–P5（含 P3 全绿） |
| **R2 红线升级落地不严** | 不变量 3.5 是唯一新建守卫，启发式关键词表有误判（`01` open_risk、`03` R1） | P3 必含红线升级回归用例（§3.5）；北极星靠"升级门存在"兜底而非"判定零误报"；拿不准升 formal |
| **R3 merge-brief 正则失配** | P5 schema 降级若改章节结构/字段书写形式，就近正则（500B 窗口）失配静默放行（`01` open_risk、`07` §3.3） | 保字段名+枚举+section heading 字面量；`test_state_merge_brief.sh` + `test_validate_multi_pr_dispatch.sh` 同 commit 守 |
| **R4 build 塌缩 13 注入点同坏** | `resolve_anchor` 是唯一入口，塌缩 bug 全坏（`07` §4.5） | 塌缩前 `--apply` 出基线 → 塌缩后 `--check` 零 diff → 跑全套 `build/tests/`；不零 diff 即停 |
| **R5 budget 公式 route 分叉漏核** | 本分册未独立复核 3P+12 是否仅 formal route 走 budget initialize（`01` open_risk #5） | P4 落地时自核：`state.sh:134-145` unlimited 分支（direct-repair/multi-pr-merge/bug-investigation/light）不进公式参数化，仅 formal 的 pending_plan_count 走公式 |
| **R6 测试断言批量改漏账** | P4/P5/P6 多处断言要改/删，漏一个 run-all-tests 红 | §4.3 "断言会被改动"清单逐条进对应 pack 验收；每期 `run-all-tests.sh` 全绿才 commit |
| **R7 checkbox toggle 事后拦截** | checkbox 翻是 Coordinator 散文（hook 只 emit），compaction 后漏翻靠 push-block 事后兜（`01` open_risk #3） | 不在本方案范围扩机器化（不过度设计）；push-block（`guard-premature-push.sh:66-76`）事后兜底保留，Light Lane 也不豁免 |
| **R8 Explorer 跨仓库幻觉条款误删** | P5 瘦身 Discovery SKILL 若误删"跨仓库事实二次验"条（`01` open_risk #4） | P5 瘦身 Discovery 时保留门控散文（`05` §2.3 "去重不删门控"）；漂移对账确认 Explorer 校验门控散文仍在 |

---

## 8. 验收信号（本分册落地后可观测）

1. **分期依赖图被 plan-writing 直接消费**：6 期的 `blockedBy` 关系（§1.2）成为 TaskList/plan 的顺序约束；P6 绑死 P1–P5。
2. **每期闭环可验证**：每期 commit 后三件套（子集 test + `verify-maturity.sh` + `build --check`）全绿，记入 `IMPLEMENTATION-LOG.md`。
3. **量化实测有方法**：§3.4 的切片/瘦身/Light Lane 提速实测流程被执行，实测值（非预先承诺值）记入日志。
4. **17 保留项零丢失**：§4.2 映射的测试在对应期全绿；散文项（必验/双文档/mockup）门控散文确认未删。
5. **5 不变量守住**：§4.1 的守卫测试每期跑；核心红线自动升级（唯一新建）在 P3 有回归用例。
6. **voice 去重后 Anti-Sycophancy 全路径在**：§4.4 逐路径 grep + `test_voice_injection.sh` + `test_review_evidence_table.sh` + 新增 footer 断言全绿。
7. **版本双处同步**：每期收尾 `diff` plugin.json/marketplace.json 为空；P5 后 architecture-draft 版本头一致。
8. **回滚粒度 = 期**：fail-open 保证 P1/P2 回滚最坏只退 commit；P6 deprecated 过渡降低减法回滚面。

---

## 9. 与其他分册的接口（cross-ref）

- `01-preserve-and-invariants`：消费其 §6 验收信号、§5 承重字段对账、17 保留项守卫锚点 → 本分册 §4 测试矩阵。
- `02-routes-as-data`：消费其 §4 死行清理、§4.4 测试更新、§6 fail-open 回退 → 本分册 P1/P2 + §5 回滚安全网。
- `03-light-lane`：消费其 §4 L1–L11 落地表、§5 删 phase_skip 时序、§7 验收 → 本分册 P3/P6 + §1 依赖图。
- `04-budget`：消费其 §4 落地排序、§3.6 effort 删/降、§5 R4 测试影响 → 本分册 P4 + §4.3 断言改动清单。
- `05-skill-context`：消费其 §1.4/§2.4 量化、§6 落地清单（强依赖标注）、§4 漂移根治 → 本分册 P5 + §3 量化实测。
- `06-external-skill`：消费其 §7 L1–L8（L1–L3 可独立先行）、§9 验收 → 本分册 P5。
- `07-agent-hook`：消费其 §6 落地分期（P1–P5）、§4.3 voice 承重守卫、§3 测试影响 → 本分册 P5 + §4.4。
- 上游 `00-overview`：§8 六验收信号 → 本分册 §3 量化映射；§6 五不变量 → §4.1 守卫矩阵。

# Plugin 控制流代码化评估（Code-Spine Codification）

> 主题：借鉴 Dynamic Workflow「把控制流写进代码」这一点，系统性梳理 plugin 哪些路由/转移/关卡可以从提示词搬进代码、哪些必须留给模型、目标架构与迁移路径。
> 评估日期：2026-05-29 · Plugin 版本：v3.9.4
> 方法：9-slice inventory（193 个决策点）+ 1 路 synthesis，所有 load-bearing 事实由 Coordinator 亲自 Read/grep 复核后写入。

---

## 0. 一句话结论

你的直觉**基本正确，但要分层**：

- **193 个控制流决策点里，145 个（75%）的触发是机器可判定的谓词**（文件存在、verdict token == X、未勾选 checkbox 计数、JSON schema 合法、exit code）。其中一大块今天活在 SKILL.md / references 散文里，靠 Coordinator 每一轮重读决策树才能路由——这正是你说的**烧 token + 跳步**的来源。
- **但「整个 workflow 全用代码规划、不写提示词」这个极端不成立**，有三道硬约束：(1) 运行时永远是一个**对话式 Coordinator 模型**，hook 是被动的（在 tool 边界触发、只能发指令），**不能主动驱动模型**；(2) 约 **14% 的决策点不可约**——生成、语义判断、模糊入口分类、何时暴露业务决策、对未枚举状态的鲁棒兜底；(3) phase-skill 之间的「返回」没有工具边界，hook 接不住，只能做成 Coordinator 主动调的 helper。
- **正解 = 扩展一个 plugin 里已被验证的模式**（`agent-return-handler.sh`）：**代码计算并强制/emit 下一步动作，模型只产 verdict token + 执行**。不是推翻 model-driven 设计，是把更多软提示词路由收口进代码。

**你的两个动机，诚实排序**（这关系到该不该做、按什么顺序做）：

1. **防跳步 / 稳定性 = 更确定的赢面**。确定性代码路由不会像「模型每轮重新解读散文决策树」那样漂移。但**注意**：只有把路由搬到**有工具边界**的地方（PreToolUse `exit 2` 或 Agent 返回 hook）才是 harness 硬强制；phase-skill 之间的返回没有工具边界，搬进代码也只是「路由表单一权威」，强制力仍靠 Coordinator 自觉调用（见 §5 三层）。
2. **省 token = 真实但被 prompt caching 摊薄**。Claude Code 缓存 SKILL.md/references 前缀（缓存 TTL 约 5 分钟），**暖缓存下每轮重读的边际成本只有约 10%**。所以「每轮都全价重读散文」是高估。真实节省来自：(a) context 窗口更小、(b) **缓存失效 / compaction 后 / 首次按需读某个 references 文件**时少读的那部分（这些是全价）。量级（估算）：可收缩路由散文约 **1000–1400 行**，但折算成实际 token 收益要按上述「全价命中率」打折，**不是每轮稳态都省 1.2–1.8 万**。别拿「大大省 token」当唯一卖点——稳定性才是。

---

## 1. 现状盘点（已核实）

### 1.1 控制流体量

| 表达载体 | 行数 | 说明 |
|---|---|---|
| SKILL.md 提示词 | **1710** | 7 个 skill（execution 455 最重） |
| references/ 决策树文档 | **4479** | multi-pr 969 / final-review 792 / plan-writing 789 / execution 695 / workflow 656 / discovery 578 |
| **散文小计** | **≈6189** | **Coordinator 要反复读的** |
| backbone 代码 | **≈3099** | hooks/*.sh + state.sh，12 个 hook 脚本 |

> 散文是确定性代码的 2 倍。其中 references 比 SKILL.md 本身还重 2.6 倍。

### 1.2 193 个决策点的分类（自验计数）

| move_verdict | 数量 | 占比 | 含义 |
|---|---|---|---|
| `already-coded` | 89 | 46% | 已经在 hook/state.sh 里（终态样板） |
| `coded-edge-model-payload` | 44 | 23% | 模型出 token、代码路由（**最大可推广面**） |
| `movable-to-code` | 33 | 17% | 现在是散文、触发却是纯谓词（**纯赚**） |
| `model-irreducible` | 19 | 10% | 必须留模型 |
| `brittle-if-coded` | 8 | 4% | 硬编码会变脆（长尾/怪异状态） |

| trigger_type | 数量 | 占比 |
|---|---|---|
| machine-checkable-predicate | 145 | **75%** |
| semantic-content-judgment | 19 | 10% |
| mixed | 17 | 9% |
| fuzzy-input-classification | 10 | 5% |
| content-generation | 2 | 1% |

**读法**：89 已编码 + 33 可搬 + 44 可代码化边 = **166/193（86%）要么已是代码、要么有可代码化的边**。真正不能动的只有 19（不可约）+ 8（脆性）= 27（14%）。

---

## 2. model-driven 买到了什么（不删，locked prior）

这不是「修一个坏掉的设计」，而是「扩展一个已被证明的模式」。现在的 model-driven orchestration 真实买到三样东西，本方案**原封保留**：

1. **对未枚举状态的鲁棒性**。入口元策略（`orchestrate-workflow/SKILL.md` 的 "Only stop for / Never stop for"）、Explorer 非结构化报告处置、Worker Context 维度「塞不塞得进 200K」的体量估计、release gate 的 billing/permission/runtime 语义风险面、merge 依赖图建立——输入空间开放，硬编码会把灵活分流换成脆性误判。
2. **模糊入口的语义分类**。Entry Gate（bug vs 新功能 vs 概念问题）、Explorer 选型、把「帮我审刚改的那块」映射到 git 范围——没有机器谓词，必须读自然语言意图。
3. **业务决策的暴露时机**。Direction Check 该不该让用户拍板、遗留尾巴修/开 issue/保留、修复路径 A/B/C 选择——是语义 + 业务判断。

**关键观察**：这些不可约节点的总量小。backbone 两 slice 证明 ~90% 的控制流本就能活在代码里（其 routing prose 占比已塌到 90%/22% **的代码侧**）；phase slice 的 routing prose 占 32%~64%，其中绝大多数是 **verdict-token 路由表**——模型只产 token，路由边纯查表。model-driven 买到的是那 **12%~38% 的 judgment_rubric**，不是那 32%~64% 的 routing。本方案就是把后者搬走、原封保留前者。

---

## 3. 三分类（代表例，已核实锚点）

### 3.1 可搬进代码（已是散文、触发是纯谓词）
- **5 张 Handle Return 散文表**（`orchestrate-workflow/SKILL.md:97~200`）：Discovery / Plan-writing / Execution / Final-Review / Multi-PR 返回后，按 verdict token 路由到下一步——纯查表，模型只产 token。
- **回流/截断上限**（`SKILL.md:180` execution_reflux_count 0→1→BLOCKED；`plan-review-resolution.md:87` Plan Review ≤2 round；`execution-repair-truncation.md:113` 2 worker + 1 RCA = 3 round）：纯计数谓词，**当前完全靠模型读散文手算 count，state.sh 只存计数（`:172`）不强制上限**——这是无代码兜底的超循环/budget 失控风险。
- **环境检测 + 断点续传路由**（`workflow-infrastructure.md:11~55`）：`.git` 是文件还是目录 + active-run-id 是否存在 + 上次 gate 后 source 是否被改——全谓词，现在是 prose 表让模型手敲 bash。
- **入口前置门**（final-review 四条前置、plan-writing 入口缺件）：纯文件/字段存在性，与 `gate-codex-review.sh:45-49` 同构。

### 3.2 不可约（必须留模型）
- 生成：plan/代码/设计文本、合同锚点提取、vertical slice 拆分。
- verdict 判断载荷：每条 finding 是否成立 + 证据是否充分、Worker 自评、reviewer pass/needs-repair——**代码消费 token 路由，token 本身是语义裁决**。
- 模糊入口分类：Entry Gate、Explorer 选型、自然语言→git 范围。
- 业务决策暴露时机：Direction Check、遗留尾巴、修复路径选择。

### 3.3 搬了会脆（保留 model-driven）
入口 stop/continue 元策略的 "Only stop" 一侧、Explorer 非结构化报告、Context 维度体量估计、release 语义风险面、merge 依赖图、缺件软行处置——**不得为追求「全代码化」硬编码这 8 个点**。

---

## 4. 样板：`agent-return-handler.sh`（existence proof，逐行核实）

这是整套方案的样板。三段式：

1. **取证门**（`:62-81`）——plan_id 非空时检查 plan-return.json 存在/合法 JSON/过 schema/ingest 成功，任一失败 emit BLOCKED。纯文件存在性 + JSON 合法性 + exit code 谓词。
2. **计算**（`:93-98`）——jq 在 execution-state 上算出第一个非 committed/skipped 的 pack 作为 resume_from_pack_id。确定性计算。
3. **verdict 路由**（`:101-127`）——`case "$VERDICT"` 6 路，每路 emit 一条 NEXT/BLOCKED additionalContext。**模型只产 verdict token（语义判断发生在 Worker 内部、写进 plan-return.json），代码计算并强制下一步动作文案，模型执行。**

两个让推广变便宜的结构事实（已核实）：
- `hooks.json:110` 把 agent-return-handler 注册为**无 if 条件的 PostToolUse Agent 钩子**——每次 Agent 返回都触发，靠脚本内 `:28-31` 的 case 自筛 agent_type。给 plan-writer/explorer/analyst/merge-worker 的返回加路由分支，**无需改 hooks.json**，只在脚本里加 case。
- `gate-codex-review.sh`（review_intent 路由）、`track-review-budget.sh`（80% trip-wire）、`state.sh` transition matrix（`:73-114`）已是同款谓词门 + token 路由，外加共享 `parse-envelope.sh` 原语——「加一条 coded edge」的边际成本很低。
- `track-execution-state.sh:108-116` 已用 `worker_agent_id` 非空抑制重复 emit，保证 agent-return-handler 是单一权威路由点——这是多 hook 协调的现成约定。

---

## 5. 目标架构（Code-Spine）

> 运行时仍是对话式 Coordinator；代码层只能「计算并强制/emit 下一步动作」，模型执行。不把 plugin 重写成脚本，不引入 Dynamic Workflow，不做 Workflow 工具 hybrid（均已在上一份评估否决）。

### 三个执行层级（必须区分，不可混淆）

| Tier | 机制 | 强制力 | 触发点 |
|---|---|---|---|
| **Tier 1** | PreToolUse `exit 2` 硬门 | 模型**无法跳过** | tool 边界（no-push-with-unchecked、no-squash、envelope 校验、budget 耗尽、Direction Check pending、transition matrix）——**已全部代码化** |
| **Tier 2** | PostToolUse hook 算路由并 emit NEXT | 强 nudge（路由由代码算，模型仍要执行 emit 的指令） | **Agent 工具返回**（经 Agent 边界，hook 可挂） |
| **Tier 3** | Coordinator 自愿调 `state.sh next-action` helper | 比纯 prose 强（路由表在代码里单一权威），但靠 Coordinator 纪律 | **phase-skill 返回**（无工具边界，hook 接不住） |

### 两条返回路径的接缝差异（核心架构事实）

- **Agent-tool 返回**（plan-writer / explorer / analyst / merge-worker）→ 经 Agent 工具边界 → `agent-return-handler.sh` 可接管（Tier 2）。**前置**：这些 agent 的 verdict 现在只在自由文本 `### Verdict` 区块里（`agents/plan-writer.md:51` = `pass｜needs revision｜blocked`；`agents/root-cause-analyst.md:142` = `pass/blocked/needs repair/needs context`），不是可 parse 的 JSON——必须先加 return schema 才能让 hook 从文件解析。
- **phase-skill 返回**（5 张 Handle Return 表）→ **没有 Agent 工具边界**，Coordinator 只是在 in-context 继续读 prose verdict。`hooks.json` 没有 Skill matcher，没有 PostToolUse hook 能在此触发。这些只能搬成 `state.sh next-action --from <phase> --verdict <token>` 计算器，由 Coordinator 主动调（Tier 3）。

两者共用一张「verdict→action」映射表（建议内置进 state.sh，成为单一真值表），区别只是触发者。

### SKILL.md 的终态形状
从「决策树」缩成两样：
- **判断准则**（judgment_rubric）：什么算设计成熟、什么算 finding 成立、confidence 校准档位、模糊输入定义、release blocker 定义、vertical slice 拆分原则——发给模型的 payload，**原封保留**。
- **verdict 词表**（每个 phase 能返回哪些 token + 一句话语义）+ 一行「返回后调 `state.sh next-action`」——取代整张 Handle Return 散文表。
- reference_knowledge（模板/dispatch 脚手架/PR body/CONTEXT schema）留作 reference 或随 dispatch 注入。

净效果：SKILL.md 的 routing prose 塌缩到接近 backbone 水平，judgment_rubric 与 reference 留存。

---

## 6. 迁移路径

**顺序取决于你哪个目标优先**（两个目标的最优起点不同）：

- **若「省 token / 瘦身散文」优先 → M1 先行**：phase-return 路由表占 routing prose 最大头，搬进 `state.sh next-action` 立刻减散文。但 M1 是 Tier 3，**不防跳步**（Coordinator 若不调 helper，没有东西强制）。
- **若「防跳步 / 稳定性」优先 → M2 + M5 先行**：这两个才是 harness 硬强制（Tier 1/2）。**已核实 M2 能做成真 Tier 1**：Worker re-dispatch 是 Agent 工具调用，`validate-plan-dispatch.sh`（PreToolUse Agent hook）已经在读 `repair_round`（`:39`）并 `exit 2`——把回流/repair 上限检查加在这里就是工具边界硬拦截，不是「state.sh 算个数让模型读」那种可跳过的软兜底。

下表按「省 token」口径排（M1 先），若你选「防跳步」优先，把 M2/M5 提前。

| 步 | 做什么 | 为什么这个顺序 |
|---|---|---|
| **M1** | 把 5 张 Handle Return 表搬成 `state.sh next-action --from <phase> --verdict <token>` 计算器，含 reflux_count 递增+上限判定。SKILL.md 换成 verdict 词表 + 一行调用。 | **最高 ROI 且零前置**：verdict token 此刻已在 Coordinator context 里（它读了 phase Result），不需要任何 return schema。entry-router 是全 plugin routing prose 占比最高的 slice（64%）。 |
| **M2** | 把所有回流/截断计数上限做成 **PreToolUse Agent 派发门**（挂在已有的 `validate-plan-dispatch.sh` 上，re-dispatch 时读 `repair_round`/reflux 超限即 `exit 2`），不要只做成 state.sh 让模型读的数字。reflux ≤1、Plan Review repair ≤2、Execution repair ≤3、multi-pr 各上限。 | 防 budget 失控的安全护栏，当前散在 reference 靠模型读散文记账（**无代码兜底**）。做在派发门上 = 真 Tier 1 硬拦截。计数谓词零语义、失守后果严重（成本失控），与 budget cap 同级。 |
| **M3** | 加 `state.sh phase-precheck --phase <p>` 覆盖 plan-writing 与 final-review 入口前置门，缺件返回 BLOCKED + 缺件清单。 | 纯文件/字段存在性，与 `gate-codex-review.sh:45-49` 同构。防止缺件状态下空跑一个 phase。 |
| **M4** | checkbox toggle 自动化：脚本读 plan-return.json `per_pack[*].status==committed`，直接 patch plan 文件 `- [ ]`→`- [x]`。 | 零语义的 JSON 过滤 + 行替换，当前靠 Coordinator 逐条 Edit 易错。下游 `guard-premature-push.sh:66-76` 已对未勾选 checkbox 阻断 push——自动化能消除「忘勾导致 push 被挡」的摩擦。 |
| **M5** | 为 plan-writer / root-cause-analyst / explorer / merge-worker 定义结构化 return JSON schema（仿 plan-return-v1），落到已知路径；扩 `agent-return-handler.sh` 的 case 按 agent_type 路由。 | 把 phase-skill 路由（Tier 3 自愿调）**升级为 Agent-tool hook 强制路由（Tier 2）**。**有真实前置成本**：当前 verdict 在自由文本里（已核实），需先改 agent 定义 + 加 schema + parser + 测试，且要保证模型守格式。排在 M1 之后是因为 M1 已用更便宜的方式拿到大头。 |
| **M6** | 收尾剩余 movable 谓词（variant payload、环境检测+续传路由、路径派生与 lint、codex-review ad-hoc dispatch 脚本化），删 SKILL.md 已代码化流程的散文镜像（保留一行人类可读说明 + verdict 词表 + 判断准则）。 | 长尾低风险，单点收益小但累加是 SKILL.md 瘦身的最后一公里。 |

### 风险
- **M5 前置成本易被低估**：自由文本 verdict → 结构化 JSON，要改 agent + schema + parser + 测试，且模型不总守格式。故 M1 先行。
- **Tier 3 强制力受限**：phase-skill 返回无工具边界，`next-action` 是 Coordinator 自愿调。若忘调或绕过，路由真值在代码但不被执行——比 prose 略好（单一权威）但非硬保证。缓解：SKILL.md verdict 词表旁明写「返回后必须调 next-action」，并在 compaction recovery（session-start）注入提醒。
- **散文删过头**：删 routing prose 时若误删判断准则或 verdict 语义说明，模型会产错 token，下游代码忠实地把错 token 路由到错分支——错误更隐蔽。缓解：只删纯转移表，保留每个 token 的一句话语义。
- **构建系统约束**（CLAUDE.md）：SKILL/agent 的 .md 有 `BEGIN/END` 锚点由 `.tmpl` 模板管。改锚点内内容必须同步回 `.tmpl` 并跑 `build.sh --apply/--check`，否则下次构建覆盖。M1/M6 改 SKILL.md 时易踩。
- **三层 verdict 词表一致性**：同一组 verdict（pass/blocked/needs-repair/resolution）现散落在 agent .md、SKILL.md 表、state.sh enum。代码化后必须三处同源（建议 state.sh 为单一真值表），否则 agent 产的 token 与 router 认的集合不一致会落到 `*) BLOCKED`——见 §7 第 2 条就是这个隐患的现成实例。

---

## 7. 必须先修的漂移（代码化会把它们固化进路由器，已亲验）

> 三条都已由 Coordinator 用 Read/grep 全链路核实，不是子代理转述。

1. **预算公式 doc 落后于 code**（修复方向已确定）：`scripts/state.sh:916` = `3*plan_count + 12`，且 `scripts/tests/test_state.sh:76` 断言 `review_total == 24`（P=4，注释写明 `3*4+12`）——**test 和 code 一致，落后的是文档**。`orchestrate-plan-writing/references/plan-gates.md:46` 写 `2P + 6` 是过时值。**修 doc，不要改 code**（改 code 会让 test 红）。

2. **ad-hoc Codex 审查入口结构性失效**（确认的真 bug，静态全链路追踪）：`codex-review/SKILL.md:49` 派发 envelope 带 `agent_role:"codex-reviewer"` + `review_intent:"ad-hoc"`，实际命令 `node "$CODEX_SCRIPT" task --background --prompt-file`（`:114`）命中 `gate-codex-review.sh:12` 触发正则 → 调 `parse-envelope.sh` → 其 `:60-72` 对 codex-reviewer 角色**只放行 `baseline`**，`ad-hoc` 触发 `exit 2` →（`gate-codex-review.sh:20` 的 `2>/dev/null` 吞掉真因）报误导性的「missing/malformed DISPATCH_ENVELOPE」。**按当前代码，ad-hoc 派发这条路是堵死的**。证据这是 bug 而非有意设计：`gate-codex-review.sh` 自己的 `case` 末尾 `*) exit 0` 本来是**放行非 baseline** 的——是共享的 `parse-envelope.sh` 抢先拦死了，两者意图矛盾。这也是 §6 风险「三层 verdict 词表不同源」的现成实例。修向二选一（业务决策）：放宽 parse-envelope 接受 ad-hoc，或把 codex-review 改用 baseline——需先定义 ad-hoc 与 baseline 语义是否应等价。（注：这是静态代码追踪，非运行时复现。）

3. **`final-review_done` 命名漂移**（非破坏性，标为漂移）：`orchestrate-final-review/SKILL.md:168` 的验收清单里写「`cursor.phase` transition 到 `final-review_done`」，但 `state.sh` 的 TRANSITION_MATRIX 只有 `Coordinator:final-review:closed`，没有 `final-review_done` 这个目标态（全仓库 grep 仅此一处）。**未确认该行真会发出 `transition --to final-review_done` 命令**（它在一个 checkbox 描述里），所以不当作破坏性 bug，按命名漂移处理、代码化前对齐即可。

---

## 8. 红线与护栏

- **运行时永远是对话式 Coordinator**。代码层只能算+强制/emit，模型执行。不重写成脚本、不引入 Dynamic Workflow、不做 Workflow hybrid。
- **Tier 1 硬门已代码化且本来就不可跳**——别把「代码消除跳步」这个宣称扩张到它们身上。真正的跳步风险只存在于 **Tier 3 软提示词路由**（Coordinator 读 SKILL.md 散文表手动选边）。本方案的价值是把 Tier 3 → Tier 2（M5）或 Tier 3 强化版（M1，路由表进代码但仍 Coordinator 调）。
- **M1/M5 不创造新的 Tier 1 硬门**：phase-skill 返回无工具边界，最多到「Coordinator 必须调 next-action」；强制力来自 Coordinator 纪律而非 harness。只有经 Agent 工具边界的返回（M5 后）才升到 hook 强制。
- **brittle-if-coded 的 8 个节点保留 model-driven**，不为「全代码化」牺牲对未枚举状态的鲁棒性。
- **judgment_rubric 与 reference_knowledge 不删**；SKILL.md 瘦身只针对 routing prose。
- **子代理纪律不变**：代码路由 verdict token **不替代** Coordinator 对 Worker/reviewer 返回 finding 成立性的亲验。
- **一个系统性代价（要权衡，不是反对）**：把路由搬进代码会让它对 Coordinator **变得不透明**——Coordinator 调一个 helper、拿回一条指令，而不再在 context 里看到路由逻辑本身。happy path 上这是好事（少读散文）；代价恰好落在 brittle-8 边界——出现没人枚举过的怪异状态时，Coordinator 手里能用来即兴应变的上下文更少了。「保留 verdict 语义 + 判断准则在 SKILL.md」这条 mitigation 覆盖了大部分，但这个 trade 要让你知道、由你权衡，而不是迁移完才发现。

---

## 附录 A：方法与核实

- **9-slice inventory**（9 explorer 并行，193 决策点）：7 个 orchestrate skill + 2 个 backbone（hooks / state）。每个决策点带 file:line、trigger_type、current_mechanism、move_verdict、理由 + 该 slice 的 prose 类型占比。
- **1 路 synthesis**：三分类 + 目标架构 + 迁移路径 + token 估算。
- **Coordinator 亲验**（本人 Read/grep，未直接采信子代理）：
  - 散文行数底座（SKILL.md 1710 / references 4479 / backbone 3099）与各 slice 占比分母吻合。
  - 三个漂移/bug 全链路核实（§7），其中子代理把 `final-review_done` 误标在 workflow SKILL.md，实为 `orchestrate-final-review/SKILL.md:168`，已纠正。
  - 样板锚点：`agent-return-handler.sh:62-127`、`hooks.json:110` 无条件 Agent hook、`track-execution-state.sh:108-116` 单一权威抑制、`parse-envelope.sh:60-72`、`gate-codex-review.sh:12/20`、agent verdict 自由文本（`plan-writer.md:51`/`root-cause-analyst.md:142`）、reflux/repair 上限锚点（`SKILL.md:180`/`plan-review-resolution.md:87`/`execution-repair-truncation.md:113`/`state.sh:172`）。
- **prose 类型占比是 explorer 估算**（按章节行数粗算，非精确分词）。token 收益是「可收缩散文行数」的上界，**未计 prompt caching 折扣**——暖缓存下边际重读成本约 10%，真实节省按全价命中率（缓存失效/compaction/首次按需读 references）打折，见 §0。故本评估把稳定性而非 token 列为首要收益。
- **范围**：仅 `plugin/`；未读 `.agents/`/`codex/`/`archive/`（禁区）。
- **已知偏差**：synthesis 的 `coded_edge_model_payload` 字段返回空（schema 占位符退化），其内容已被 §3 + §4 覆盖。

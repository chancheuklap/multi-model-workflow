# 分册 01 · 保留契约与不变量（承重清单）

> **本分册职责**：把 `00-overview.md` §5 保留清单（17 项）与 §6 北极星不变量（5 条）展开为**逐条可验收的承重契约**。每条给：现状源码锚点 → 当前是否已机器化守卫 → 若被破坏会丢什么 → 新架构里如何继续守住。
>
> - 绑定上游：`00-overview.md`（灵魂契约）。本分册与骨架冲突 = 本分册错。
> - 适用对象：`plugin/`（v3.10.0）。所有 `file:line` 均由本分册作者亲自 `Read`/`grep` 核验。
> - 消费方：`02`–`08` 各分册改造任何机制前，必须先在本分册查到对应保留契约，确认其守卫不被削弱。

---

## 0. 结论先行（给 plan-writing 阶段的硬约束）

1. **17 项保留项里只有 9 项有真正的机器守卫**（脚本/hook/schema 会 `exit 2` 或正则扫描拦截）；**8 项纯靠散文自觉**，是新架构的脆弱点。散文项里有两类要区别对待：一类是**设计纪律**（如子代理必验、模型分层）——本身无法完全机器化，靠 prompt 注入+人盯；一类是**可机器化但今天没做**（如轻量旁路、Explorer 报告抽样验的执行点），这些在新架构里**应当**补机器钩子。
2. **三条骨架待验项已逐条复核通过**（见 §3）：worker-dispatch envelope 确实只传 `plan_id+plan_path`；`last_gate_timestamp` 确实由 `transition` 自动写、与 `cursor.*` 职责正交；`merge-brief` 的 `conflict_id`/`status` 枚举确实被 `state.sh:1582` 起的 `cmd_merge_brief_verify` 正则消费。
3. **降级/瘦身时的红线**：凡是被运行时（脚本/hook/schema/正则）消费的字段名与枚举值，改任何一个都要同步改消费点，否则静默失守。本分册逐条标注了这些"运行时承重字段"。
4. **新架构对保留项的总策略**：能力一个不丢；机器守卫只增不减；散文项凡可机器化且值得（高频踩、破坏后果大）的，在 `02`/`03`/`07` 补钩子；纯设计纪律项保持 prompt 注入但收口到 build 单源（`07`），避免去重时漏注入。

---

## 1. 守卫现状总表（17 保留项 × 守卫强度）

| # | 保留项（§5） | 守卫强度 | 机器守卫锚点（若有） | 破坏后果等级 |
| --- | --- | --- | --- | --- |
| 1 | Document-as-Context 派发层（envelope 只传 `plan_id+plan_path`） | **机器** | `validate-plan-dispatch.sh:75-93`（execution 必 plan-level、plan_path 必存在） | 高（退回粘贴 Pack=烧 token+漂移） |
| 2 | Plan 级自治 Worker（一 Plan 一 Worker，单一共享工作树） | **机器（部分）** | `validate-plan-dispatch.sh:80-83`（禁 pack-level execution）、`:108-114`（同 plan 不重复派） | 高（回退到 35–55 次 pack 派发） |
| 3 | 磁盘状态抗断点续传（cursor + per-pack committed + mkdir 锁） | **机器** | `state.sh:155`(cursor)、`state-lock.sh:8-31`(mkdir 原子锁)、`track-execution-state.sh:42-49`(committed) | 致命（compaction 后失忆） |
| 4 | Source Stability 自动重审门（`last_gate_timestamp`+`git log --since`） | **半机器** | `state.sh:313-314`(自动写)；`git log --since` 在散文（`workflow-infrastructure.md:34-41`） | 高（review 后改 source 不重审） |
| 5 | 子代理返回必验纪律 | **散文** | 无 hook；散文（`orchestrate-discovery/SKILL.md:104-113` 等） | 高（采信幻觉路径/计数） |
| 6 | Codex 外部对抗评审 + 模型分层（GPT-5.5/5.4 xhigh） | **散文（选型）+机器（门）** | 选型散文（`review-dispatch.md:16-18`）；门 `gate-codex-review.sh:29-52` | 中（丢外部对抗价值） |
| 7 | 抑制外部模型幻觉四件套 | **散文（注入）** | 内容单源 `review-dispatch.md:32-69`（被注入 review prompt） | 高（reviewer 幻觉混入主报告） |
| 8 | Discovery 双文档对等 + grill-with-docs + Explorer 报告校验门控 | **散文** | 无 hook；`orchestrate-discovery/SKILL.md:72-87`、`:104-113` | 中（术语漂移/采信未验事实） |
| 9 | Mockup 与文字设计平级、原子拆解为视觉规格表 | **散文（门控散文）** | `plan-gates.md:30`、`plan-review-dispatch.md:37`（Plan Review reviewer 检查项） | 中（UI 实现走样） |
| 10 | Worker 禁改 docs/ + checkbox toggle Coordinator 专属 | **机器** | `guard-doc-edit.sh:37-41`(worker-active marker → exit 2) | 高（数据权威被 worker 改） |
| 11 | Anti-Sycophancy + Push twice + Honesty + Decision Brief（voice-directive 载体） | **机器（注入）+散文（行为）** | build 单源 `voice-directive.md.tmpl`（注入各派发路径） | 中（去重时漏注入=丢基调） |
| 12 | vertical-slice / tracer-bullet + AFK 优先 HITL 拆分内核 | **散文** | 无 hook；散文+`to-issues` skill（接线缺，见 `06`） | 低-中（拆分质量退化） |
| 13 | idempotency_key 防 compaction 后重复派/重复计费 | **机器** | `validate-plan-dispatch.sh:40,52-56`(exists→exit 2)、`:141`(append) | 致命（重复计费=计费不变量） |
| 14 | 成本护栏核心诉求（机制可重做，诉求保留） | **机器（机制）** | `track-effort-budget.sh`/`track-review-budget.sh` + `state.sh:916`（公式） | 中（长 session 无限烧） |
| 15 | gstack §7"明确不借鉴"清单 | **设计记忆** | 无（反向决策，勿再提） | 低（重蹈被否决方案） |
| 16 | `git merge --squash` 禁令 + 未勾选任务阻断 push | **机器** | `guard-premature-push.sh:17-20`(squash)、`:66-76`(unchecked→exit 2) | 高（破坏 merge 历史/带病 push） |
| 17 | merge-brief §4/§5/§6 字段约定（conflict_id/status 枚举）运行时消费 | **机器** | `state.sh:1582` 起 `cmd_merge_brief_verify`（正则扫 `conflict_id`/`status`） | 高（降级 schema 改字段名=静默失守） |

**口径说明**：
- **机器** = 有脚本/hook/schema 在运行时 `exit 2` 或正则拦截，违反会被物理阻断。
- **半机器** = 关键状态由脚本自动维护，但消费动作（如 `git log --since` 判定）写在散文里靠主线程执行。
- **散文** = 仅靠 SKILL.md / agent prompt 文字约束，无机器执行点。
- **设计记忆** = 一次性反向决策，无需机器，只需不重蹈。

> **脆弱点清单（散文/半机器项）**：#4(半)、#5、#7(注入半机器)、#8、#9、#12、#15(无需)。新架构对它们的处置见 §4 各条"目标守卫"。

---

## 2. 三条骨架待验项 · 复核结论（写文档前已 Read 源码确认）

### 2.1 worker-dispatch-minimal —— ✅ 确认 envelope 只传 `plan_id+plan_path`

- **复核来源**：`plugin/skills/orchestrate-execution/references/execution-worker-dispatch.md:8-13`、`:81`。
- **事实**：
  - `:8` 明文 "Coordinator 派发时只在 DISPATCH_ENVELOPE 写 `plan_id` + `plan_path` + 运行时变量，**不粘贴任何 Pack 内容**"。
  - `:13` "Coordinator 只在 envelope 写明 `plan_id` + `plan_path` + 运行时变量。每个 Pack 的完整定义……由你从 plan 文件自读"。
  - `:81` Coordinator 端最小职责第 1 条："写 `DISPATCH_ENVELOPE`，填入 `run_id`、`plan_id`、`plan_path`、`phase=execution`、`agent_role`"。
- **机器守卫**：`validate-plan-dispatch.sh:88-93` 在 envelope 携带 `plan_id` 时强制 `plan_path` 必须解析为存在文件，否则 `exit 2`。这是"派发即自读"契约的物理兜底——但 hook 不检查"是否粘贴了 Pack 内容"（粘不粘是 prompt 体积问题，无法机器测）。
- **结论**：契约成立。envelope 是窄接口（`plan_id`/`plan_path`/运行时变量），Pack 定义靠 Worker 自读。**这是"不烧 token"的承重设计，新架构不得为了"省一次 Read"把 Pack 内容塞回 envelope。**

### 2.2 last_gate 自动重审门 —— ✅ 确认依赖 `last_gate_timestamp`，与 cursor 正交

- **复核来源**：`plugin/scripts/state.sh:313-314`（写入点）、`plugin/skills/orchestrate-workflow/references/workflow-infrastructure.md:34-41`（恢复段）、`:200-201`（与 cursor 的区别说明）。
- **事实**：
  - 写入点 `state.sh:313-314`：`cmd_transition` 在每次 phase 流转时 `jq '.cursor.phase = $phase | .last_gate_phase = $phase | .last_gate_timestamp = $ts'`——**`last_gate_timestamp` 由 transition 自动写，无需 Coordinator 手动维护**。
  - 恢复段 `workflow-infrastructure.md:36-41`：用 `git log --oneline --since="<last_gate_timestamp>" -- <design/plans/issues 路径>` 检测 source artifacts 自上次 gate 通过后是否被改；命中则按 `:43-51` 路由回对应 Review。
  - 正交性 `workflow-infrastructure.md:200-201` 明文："`last_gate_phase` / `last_gate_timestamp` 由 `state.sh transition` 自动写入（phase 级粗粒度……timestamp 供 Source Stability 检查的 `git log --since`），`cursor.*` 记录当前精确位置（reference + step 级，用于 compaction recovery）。**两者共存。**"
- **结论**：两者**职责正交、不可二选一**——`cursor.*` 答"我在哪一步"（compaction 后从哪续），`last_gate_timestamp` 答"上次 gate 之后 source 有没有被改"（要不要重审）。骨架 §5#4 的判断成立。**新架构若把 cursor 与 last_gate 合并为一个字段，会丢掉"review 后 source 被改 → 强制重审"的检测能力。**
- **脆弱点**：写入是机器（transition 自动），但**判定动作（`git log --since` + 路由表）写在散文**，靠主线程恢复时执行。这是半机器项——见 §4 关于是否机器化的建议。

### 2.3 merge-brief 字段被运行时消费 —— ✅ 确认按 `conflict_id`/`status` 字段名+枚举正则扫描

- **复核来源**：`plugin/scripts/state.sh:1582`（`cmd_merge_brief_verify` 入口）起至 `:1724`；schema `state-schema/merge-brief-v1.json`。
- **事实**：
  - `:1617` 校验 META 必填字段 `['schema_version','run_id','slug','created_at','last_updated_at','current_stage']`。
  - `:1623-1625` 校验 `current_stage` 枚举 ∈ `['init','conflict_discovery','rca','repair','integration_review','merging','complete']`，越界 `exit 1`。
  - `:1637-1644` 校验 9 个章节标题全在（`## 1. Meta` … `## 9. Verdict`），缺一即 `errors`。
  - `:1661-1667` + `:1686-1691` 用正则 `conflict_id[^:]*:\s*[`"]?([^`"\s,]+)` 抽取 §4 内所有 `conflict_id`，再就近正则 `\bstatus[^:]*:\s*...` 抽 `status`。
  - `:1694-1702` 按枚举做自洽：`status == 'resolved'` 必在 §6 (Resolution Log) 有对应条目，否则 `ERROR`；`status == 'rca-in-progress'` 必在 §5 (RCA) 有条目。
  - 任一 `errors` → `:1718-1723` `BLOCKED` 并 `exit 2`。
- **结论**：`conflict_id` / `status` 是**运行时承重字段名**，枚举 `resolved` / `rca-in-progress`（以及 `current_stage` 的 7 个值）是**运行时承重枚举值**——由正则按字面匹配。骨架 §5#17 与 §7.07 所述"降级 schema 时字段名/枚举必须原样保留"成立。**`07` 做 merge-brief schema 降级时，凡改这些字面量，必须同步改 `state.sh:1582-1723` 的正则与枚举数组，否则 verify 静默放行带病 brief。**

---

## 3. 北极星不变量逐条承重契约（§6 · 不可破）

> 这 5 条违反 = 方案作废。每条给：源码锚点 + 守卫 + 破坏后果 + 新架构守住方式。

### 3.1 计费 / LINEAGE —— idempotency_key 防重复计费

- **锚点**：`validate-plan-dispatch.sh:40`(取 key)、`:52-56`(key 已存在 → `BLOCKED` + `exit 2`)、`:141`(派发放行后 append key)；`lib/parse-envelope.sh:39`(key 列必填字段)。
- **守卫强度**：**机器**。PreToolUse Agent hook 在派发前做幂等检查，重复派发被物理阻断。
- **破坏后果**：compaction 后主线程"忘了已派"重新派同一 Worker → 重复执行 + **重复计费**。这是计费不变量的核心。
- **新架构守住**：`02` 把 transition 改读 routes 清单时，**不得绕过这一步**；`03` Light Lane 即使免外审，dispatch 仍走同一 idempotency 门；`04` 预算降级为仪表不触碰 idempotency（两者正交：idempotency 防"重复派"，budget 管"派几次"）。**任何派发去重逻辑改写，回归测试必须覆盖 `test_validate_plan_dispatch.sh` 的 "duplicate idempotency_key → block"（该测试已存在）。**

### 3.2 状态权威 —— 磁盘状态是 compaction/断点续传唯一可信源

- **锚点**：`state.sh:155`(cursor 初始化)、`:313-314`(transition 自动写 cursor.phase/last_gate)、`workflow-infrastructure.md:173-201`(状态锚字段表 + 恢复规则)；`state-lock.sh:8-46`(mkdir 原子锁)；`track-execution-state.sh:42-49`(per-pack committed + commit_sha)。
- **守卫强度**：**机器**。状态由脚本写盘，锁保证并发安全，恢复规则按字段路由。
- **破坏后果**：把关键状态只留主线程上下文 → compaction 即失忆 → 重派/跳步/重复计费。
- **新架构守住**：`02` routes 清单是**新增的声明式数据**，但**运行时游标仍写 workflow-state 磁盘**——routes 是"流程形态定义"（静态），cursor/last_gate 是"当前进度"（动态），两者分离。`05` 瘦身 SKILL.md 不得把任何运行时状态从磁盘挪进散文。**红线：routes 清单可以是新文件，但 `cursor.*`/`last_gate_*`/`committed`/`idempotency_keys` 必须继续写盘。**

### 3.3 数据权威 —— docs/ 是 source of truth；Worker 不得改 docs/；checkbox 由 Coordinator 翻

- **锚点**：`guard-doc-edit.sh:26`(只 guard `docs/` 路径)、`:37-41`(worker-active marker 存在 → `BLOCKED` + `exit 2`)、`:11-16`(plan-returns 写盘合法，在 docs/ 外)；checkbox toggle 由 Coordinator 按 plan-return 执行 `agent-return-handler.sh:103-106`(emit "toggle committed-pack checkboxes per execution SKILL Step 14")。
- **守卫强度**：**机器**（Worker 禁改 docs/ 由 PreToolUse Edit/Write hook 拦）；checkbox toggle 是**散文指令**（hook 只 emit 提示，实际翻由 Coordinator 执行）。
- **破坏后果**：Worker 改设计/计划 → 数据权威污染、reviewer 对着被改文档审 → 整条 LINEAGE 失真。
- **新架构守住**：`07` 改 hook 层时 `guard-doc-edit.sh` 的 worker-active marker 机制**原样保留**；`03` Light Lane 即使跳过 Design Review，Worker 在 worktree 里仍受 marker 约束（Light Lane 不改 worker 边界，只改流程形态）。**`00`§6 已把"Worker 禁改 docs/"列入质量门最小集——Light Lane 也保留。**

### 3.4 质量门最小集（Light Lane 也保留）

- **三件**：①子代理返回必验（散文，`orchestrate-discovery/SKILL.md:104-113`）；②Worker 禁改 docs/（机器，见 3.3）；③未勾选任务阻断 push（机器，`guard-premature-push.sh:66-76`）。
- **守卫强度**：①散文、②机器、③机器。
- **破坏后果**：去掉任一 → Light Lane 退化为"无质量底线的快车道"，违反 D1+D4 的"稳定地板"。
- **新架构守住**：`03` 设计 Light Lane 时，routes 清单里 Light Lane 这条数据**不得豁免这三件**——可以豁免 Design Review/Plan Review/Codex 外审（D1/D2），但 doc-guard + push-block + 必验三件是所有 lane 的公共底座。**`02` 的 gate 豁免逻辑必须区分"流程门"（可豁免）与"质量门最小集"（不可豁免）。**

### 3.5 核心红线自动升级 —— 触碰计费/权限/数据权威/用户可见合同 → 必走 Formal Lane

- **锚点**：**目前无机器实现**（这是新架构 `03` 要新建的 Entry 判定）。现状 D1 是"激进默认轻档"的设计决策（`00`§3 D1），核心红线升级是其安全护栏。
- **守卫强度**：**待建（散文→应机器化）**。今天没有任何 hook 检测"改动是否触碰计费/权限"。
- **破坏后果**：激进默认轻档后，若一个触碰计费的改动被误走 Light Lane（无 reviewed design）→ 高危改动绕过对抗评审。
- **新架构守住**：`03` 的 Light Lane Entry 判定线必须包含"核心红线检测"——一旦命中计费/权限/数据权威/用户可见合同关键词或路径，**强制升级 Formal Lane**（有 reviewed design）。这是 D1"激进"的安全闸。**本条是新架构唯一一个"从无到有新建机器守卫"的不变量——`03`/`02` 必须落地它，否则 D1 激进默认不安全。**

---

## 4. 散文/半机器脆弱点 · 新架构处置建议（给 plan-writing）

> 把 §1 总表里 7 个非纯机器项逐一定性：**该补机器**还是**保持散文注入**。判定线（用户核心原则 #14，不过度设计）：高频踩 + 破坏后果大 + 可机器化 → 补；纯主观/无法机器判定 → 保持注入并收口 build 单源。

| 项 | 现状守卫 | 建议处置 | 理由 | 落地分册 |
| --- | --- | --- | --- | --- |
| #4 Source Stability 重审 | 写入机器、判定散文 | **保持半机器**（写入已机器，判定靠主线程 `git log --since`） | 判定需理解"哪些 source 算改动"，路由表语义复杂；写入已是机器，不必再包一层 hook。但 `02` 改 transition 时**必须保留 `last_gate_timestamp` 自动写**。 | `02`（保留写入）/`08`（回归测试） |
| #5 子代理必验 | 散文 | **保持散文（注入）** | "必验"是主线程行为纪律，无法机器替它 grep；可机器化的只是"Explorer 报告抽样验"的提示。收口到 voice/preamble 单源避免漏注入。 | `05`/`07`（单源注入） |
| #7 幻觉四件套 | 内容单源注入 | **保持注入 + 守住单源** | 已是 build 单源（`review-dispatch.md`），注入各 review prompt。`07` 去重时**每条派发路径必须仍注入这四件**，否则 reviewer 幻觉混入。 | `07`（承重守卫） |
| #8 双文档+Explorer 门控 | 散文 | **保持散文**；Explorer 抽样验可考虑轻提示 hub，但不强制 | 双文档对等是 Discovery 方法论；Explorer 校验门控是主线程判断，机器只能提示不能替判。 | `05`（瘦身不删门控散文） |
| #9 Mockup 原子拆解 | Plan Review reviewer 检查项（散文） | **保持散文（Plan Review 门控）** | 已被 `plan-gates.md:30`/`plan-review-dispatch.md:37` 列为 reviewer reject 条件，等于有评审门兜底；机器无法判"视觉规格够不够原子"。 | `06`（mockup skill 接线） |
| #12 拆分内核 | 散文+skill | **保持散文 + 补 to-issues 接线** | 拆分质量靠方法论；`to-issues` 零引用是接线缺口（`00`§2 已记），补接线即可。 | `06` |
| 红线自动升级 | 无 | **新建机器**（唯一必补） | 见 3.5——D1 激进默认的安全闸，必须机器检测。 | `03`/`02` |

**净结论**：新架构只需**新建 1 个机器守卫**（红线自动升级 3.5），**守住 1 个单源注入**（幻觉四件套 #7），**保留 1 个自动写入**（last_gate #4）；其余散文项保持注入并收口 build 单源即可。不引入"为机器化而机器化"的冗余 hook（符合 #14）。

---

## 5. 降级/瘦身红线索引（运行时承重字段，改一个就要改消费点）

> `05`/`07`/`08` 做 schema 降级、字段瘦身、文档重写时，下表字段**改名/改枚举即静默失守**，必须同步改消费点。

| 承重字段/枚举 | 消费点 | 改它要同步改 |
| --- | --- | --- |
| `idempotency_key` / `idempotency_keys[]` | `validate-plan-dispatch.sh:40,52,141`、`parse-envelope.sh:39` | hook + envelope schema + 全部 `test_*` |
| `plan_id` / `plan_path` | `validate-plan-dispatch.sh:36-38,75-93` | execution dispatch 契约 + worker-dispatch.md |
| `cursor.phase` / `cursor.reference` / `cursor.step` | `state.sh:155,313`、恢复规则 `workflow-infrastructure.md:196-201` | state schema + recovery 散文 |
| `last_gate_phase` / `last_gate_timestamp` | `state.sh:313-314`、`workflow-infrastructure.md:36-41` | transition 写入 + Source Stability `git log --since` |
| `status == "committed"` / `commit_sha` | `track-execution-state.sh:42-49`、`gate-codex-review.sh:45-47`、`agent-return-handler.sh:96` | execution-state schema + 三处消费 |
| `pending_direction_check.ack_status == "pending"` | `validate-plan-dispatch.sh:66-71` | 预算降级（`04`）时若改 direction-check 机制，同步改此判定 |
| `worker-active`（marker 文件名） | `guard-doc-edit.sh:37` | doc-guard marker 约定 |
| merge-brief `conflict_id` / `status`(`resolved`/`rca-in-progress`) / `current_stage`(7 值) | `state.sh:1606-1702` | merge-brief schema 降级（`07`）必须同步正则+枚举数组 |
| voice-directive `[variant=...]` 块 | build resolver 注入各 SKILL/agent | `07` 去重 twin 时每条派发路径仍要注入对应 variant |

---

## 6. 验收信号（本分册落地后可观测）

1. **17 项保留项映射完整**：`08` 的回归测试套件能逐项指向本分册的守卫锚点；机器项有对应 `test_*`（已存在的：idempotency、doc-guard、premature-push、execution-state、merge-brief verify）。
2. **三待验项无回归**：`02` 改 transition 后，`last_gate_timestamp` 仍由 `transition` 自动写（grep `state.sh` 确认 `:313` 语义未删）；worker-dispatch envelope 仍只传 `plan_id+plan_path`（grep `execution-worker-dispatch.md:8` 文案在）；merge-brief verify 的 `conflict_id`/`status` 正则与枚举未被 schema 降级改漂移。
3. **质量门最小集贯穿所有 lane**：`03` 的 Light Lane routes 数据经测试确认仍触发 doc-guard + push-block + 必验三件（不被 gate 豁免逻辑误关）。
4. **红线自动升级机器化**：`03` 落地后，构造一个触碰计费关键词的改动，验证它被强制升级 Formal Lane（新建测试）。
5. **承重字段零漂移**：`08` 提供一个"字段名/枚举 grep 对账"检查，确认 §5 表中每个承重字段在 schema 与消费点字面一致。

---

## 7. 与其他分册的接口（cross-ref）

- `02-routes-as-data`：消费本分册 3.1/3.2（idempotency 与磁盘状态权威不得被 routes 改写绕过）、§5（transition 改写要保 `last_gate_timestamp`）。
- `03-light-lane`：消费 3.4（质量门最小集贯穿 Light Lane）、3.5（红线自动升级必须新建）。
- `04-budget`：消费 3.1（budget 与 idempotency 正交）、§5（`pending_direction_check.ack_status` 判定）。
- `05-skill-context`：消费 §4（#5/#8 散文项瘦身不删门控）、§5（cursor 不挪进散文）。
- `06-external-skill`：消费 §4（#9 mockup、#12 to-issues 接线）。
- `07-agent-hook`：消费 §2.3（merge-brief 降级红线）、§4（#7 幻觉四件套单源注入）、§5（voice-directive variant 注入）。
- `08-migration`：消费 §6（验收信号）、§5（承重字段对账检查）。

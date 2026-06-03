# 04 · 预算从硬闸门降为仪表

> **分册职责（受 `00-overview.md` 绑定）**：把成本护栏从"到一半硬 `exit 2` 卡死等人 ack"改为"仪表 + 业务决策检查点"，落地 D3（软继续 + 到顶停），根治无人值守自主跑动名存实亡。
>
> - 锁定决策约束：**D3**（AFK 过半软提醒+继续、100% 才 escape hatch；在场过半停顿）。
> - 北极星不变量约束：保留 §5.14「长 session 防无限烧 token」诉求；不触碰 idempotency_key 去重（§6 计费）。
> - 与骨架冲突 = 本分册错。

---

## 0. 结论先行（给 plan-writing 直接消费）

1. **病根**：成本护栏被实现成"硬阻断闸"，而不是"仪表"。当前唯一的强制点是 `validate-plan-dispatch.sh:66-72` 在 `pending_direction_check.ack_status == "pending"` 时 `exit 2`，拦掉所有非 `codex-reviewer` 的 Worker 派发。一旦触发，AFK 自主跑就停在这里**等一个永远不会来的人**。
2. **三因叠加才致死**（缺一不足以卡死）：① 静态总额 `review_total = 3*plan_count+12`（`state.sh:916`）一旦初始化即不可变；② reflux/重写时 `review_used` **从不重置**（`SKILL.md:179` 明文「回流不重置 budget usage」）；③ 到 80% 即 `exit 2` 硬阻断。三者叠加 = 总额吃满 → 永久阻断 → 等人。
3. **目标设计**：
   - 双模式（AFK / 在场），用**显式 session-level 模式标志** `attendance_mode` 区分（现状没有这个标志，AFK/HITL 只是 issue/pack 级标签，不影响 budget 行为）。
   - 删 80% 硬 `exit 2`：80% 降为"下次返回时 `additionalContext` 软信号"；**只在 100%（到顶）才硬停**，且硬停在 AFK 下也是 escape hatch（一次性放行而非永久卡死）。
   - `review_used` 在 reflux/重写时按"本轮实际复杂度增量"重置（增加 `cmd_budget_credit` 子命令）。
   - 公式 `3P+12` 提取为可配置上限 + per-run 覆盖；删派生的 `effort_total = 2×review_total`（effort budget 零独立 gate，已 grep 确认），`track-effort-budget.sh` 降为咨询计数器或整体删除。
4. **不丢的诉求**：长 session 防无限烧 token 仍在——靠"到顶硬停 + 仪表持续可见 + 在场模式过半停顿"实现，不靠"过半就拦死"。

---

## 1. 现状（源码锚点）

### 1.1 预算的产生与公式

| 事实 | 锚点 |
| --- | --- |
| Formal route 初始化时 `budget_status='pending_plan_count'`、`review_total=null`、`effort_total=null` | `scripts/state.sh:133-146` |
| `direct-repair / multi-pr-merge / bug-investigation` route → 三项全 `unlimited` | `scripts/state.sh:135-139` |
| 公式：`review_total = 3*plan_count + 12`；`effort_total = review_total * 2` | `scripts/state.sh:916-917` |
| 公式语义：`3P`=每 Plan 3 次 review（1 baseline + 2 repair re-review）；`+12`=固定预留（Design 2-4 + Plan 1 + Final 2 + Release 2 + 修复余量 3-5） | `skills/orchestrate-plan-writing/references/plan-gates.md:48` |
| budget 一旦 `initialized`，`review_total`/`effort_total` **不可变**，执行/Final Review 阶段均不得改 | `skills/orchestrate-workflow/references/workflow-infrastructure.md:171` |
| Light Lane 变体（hotfix/quickfix/spike/maintenance）→ 全部 `unlimited`（`state.sh init` 后立即设） | `skills/orchestrate-workflow/SKILL.md:68,72-75` |

### 1.2 计数：两个 PostToolUse 钩子（纯观察，零阻断）

`track-review-budget.sh` 与 `track-effort-budget.sh` 是 PostToolUse 钩子，**全文只有 `exit 0`，没有任何 `exit 2`**（已 grep 确认）。它们做两件事：自增计数 + 在 80% 时写 `pending_direction_check`。

| 钩子 | 触发面 | 计数语义 | 80% 行为 | 100% 行为 |
| --- | --- | --- | --- | --- |
| `track-review-budget.sh` | PostToolUse / Bash，命中 `codex-companion ... result` 且 exit 0（`:10-14`） | `review_used += 1`，cap-guard 不超额计数（`:33-41`） | 写 `additionalContext`「DIRECTION CHECK ...≥80%」+ 若无 pending DC 则调 `state.sh direction-check trigger`（`:50-67`） | `additionalContext`「BUDGET EXHAUSTED ... Stop ... report」（`:48-49`），**不阻断**（`exit 0`） |
| `track-effort-budget.sh` | PostToolUse / Agent，按 agent_role 加权（`:37-75`） | `effort_used += increment`（plan-level=committed pack 数，`:52-61`；explorer=1；root-cause=2；need-fresh-worker +0.5） | 写 `pending_direction_check`（`:87-92`）+ `additionalContext`（`:93`） | `additionalContext`「EFFORT BUDGET EXHAUSTED ... Stop and report」（`:85`），**不阻断**（`exit 0`） |

注册见 `hooks/hooks.json:89`（review）/`:115`（effort）。

### 1.3 唯一的硬阻断点：`validate-plan-dispatch.sh`

```text
validate-plan-dispatch.sh:66   DC=$(jq -r '.pending_direction_check.ack_status // empty' "$SF")
                          :67   if [[ "$DC" == "pending" ]]; then
                          :68     if [[ "$AGENT_ROLE" != "codex-reviewer" ]]; then
                          :69       echo "...BLOCKED: Direction Check pending." >&2
                          :70       exit 2
```

PreToolUse / Agent 钩子。两个 budget 计数钩子写出的 `pending_direction_check` 都流向**这同一个槽位**；这是整套预算唯一会 `exit 2` 卡住派发的地方。

`pending_direction_check` 的写入/清除：
- 写入：`state.sh direction-check trigger`（`state.sh:1120-1122`，`ack_status="pending"`）；或 `track-effort-budget.sh:91` 直接写。
- 清除/转移：`state.sh direction-check ack --action {continue|stop|adjust}`（`state.sh:1148-1165`）→ `acknowledged` / `stopped` / `null`。
- 流程描述见 `references/direction-check.md:32-36`（Step 2 Block）。

### 1.4 reflux/重写从不重置 `review_used`（致死因之一）

| 事实 | 锚点 |
| --- | --- |
| 「回流不重置 budget usage」明文 | `skills/orchestrate-workflow/SKILL.md:179` |
| `NEEDS_EXECUTION` 回流被 `execution_reflux_count` 硬限一次（0→1 可回流，≥1→BLOCKED） | `skills/orchestrate-workflow/SKILL.md:174`；`final-review-repair.md:118` |
| `review_used` 全仓只增不减（`state.sh:1058` `+=1`、`track-review-budget.sh:39` `+=1`），**无任何减少/重置/credit 路径** | grep `review_used`：写入仅 `+=1` 两处 |
| Plan revision 改 plan count → plan-writing Step 12a 重新确认 budget，但 `budget initialize` 只能从 `pending_plan_count` 进，已 `initialized` 拒绝改 | `state.sh:911-914`；`SKILL.md:179` |

### 1.5 没有"AFK vs 在场"的机器标志（双模式缺失）

- grep `autonomous|AFK|HITL|unattended` 全仓：`AFK`/`HITL` **只作为 issue/pack 级标签**出现在 plan/issue 文档（`issue-splitting.md:29-38`、`plan-writing-methodology.md:44` 等），**不影响 budget 钩子行为**。
- "autonomous mode" 一词在代码里指的是 **Plan-level Worker 自治派发模型**（`validate-plan-dispatch.sh:6`、`agent-return-handler.sh:4`），不是"用户离场无人值守"。
- workflow-state schema（`state-schema/workflow-state-v1.json`）**没有任何 session-level 的 attended/unattended 字段**。
- 结论：今天 budget 的硬阻断行为对"用户在不在场"一视同仁。D3 要求的双模式分叉**当前完全不存在**，是本分册要新增的机器标志。

---

## 2. 问题

| # | 问题 | 后果 | 与骨架对应 |
| --- | --- | --- | --- |
| P1 | 80% 即 `exit 2`，AFK 无人 ack | 自主跑停死等人，「无人值守」名存实亡 | §2 僵硬（控制越权）；§5.14 诉求被实现成阻断 |
| P2 | 静态总额 + reflux 不重置 + 80% 硬阻断三因叠加 | 一次正常的回流重写就吃满预算 → 永久卡死 | §2「死池+不重置+80%硬阻断」 |
| P3 | 无 AFK/在场标志 | 无法实现 D3 的双模式（在场过半停 vs AFK 过半续） | D3 |
| P4 | `effort_total=2×review_total` 派生、`track-effort-budget.sh` 零独立 gate | 多一套加权计数 + 抢同一个 DC 槽位，复杂无收益 | §2 复杂；§4 表「删 effort 2×」 |
| P5 | 公式 `3P+12` 硬编码、不可 per-run 覆盖 | 大改造/小批量都套同一公式，要么太松要么太紧 | §4 表「可配置上限」 |

**P4 深入（已 grep 确认 effort 零独立 gate）**：`track-effort-budget.sh` 全文无 `exit 2`；它写 `pending_direction_check` 的代码（`:87-92`）只在该槽位为 `null` 时才写。也就是说当 review 已抢先写了 DC，effort 命中 80% 时 `DC != null`，分支落到 `:95` 输出一行非触发的「Effort budget: X/Y.」纯文本就 `exit 0`。**effort budget 的唯一真实作用是和 review 抢同一个 `pending_direction_check` 槽位**——它没有自己的阻断、没有自己独立的检查点语义，纯属冗余维度。

---

## 3. 目标设计

### 3.1 数据模型变更（workflow-state）

在 `budget` 块外新增一个 **session-level 模式标志**，并把上限拆成"基线公式参数 + per-run 覆盖"。

```jsonc
{
  "attendance_mode": "afk",          // 新增："attended" | "afk"，默认 "afk"（D1 激进默认无人值守友好）
  "budget": {
    "budget_status": "initialized",  // 不变
    "review_total": 30,              // = 仍是数值上限，但来源可配置（见 3.2）
    "review_used": 11,
    "review_credit": 0,              // 新增：reflux/重写归还的额度（见 3.4），check 时用 used - credit
    "budget_profile": "standard",    // 新增：上限来源画像（见 3.2），仅供展示/审计
    // effort_total / effort_used：见 3.6，建议删除或保留为咨询字段
    "direction_check_count": 0
  },
  "pending_direction_check": null    // 不变，仍是 DC 槽位
}
```

> schema 改动落在 `state-schema/workflow-state-v1.json`：新增 `attendance_mode`（top-level enum，default `"afk"`）、`budget.review_credit`（number，default 0）、`budget.budget_profile`（string）。`effort_total`/`effort_used` 视 3.6 决定保留为咨询或删。**所有新增字段给 default**，确保历史 state 文件（无这些字段）读取时不报错——这是迁移期向后兼容硬要求。

### 3.2 公式参数化 + per-run 覆盖（P5）

把 `state.sh:916` 的硬编码公式抽成"画像表 + 覆盖入口"。

- **基线公式仍是 `3P + 12`**（骨架 §2 已记录：曾提议 2P+6 被 commit `743f447` 改回，本分册**不动公式数值**，只让它可被覆盖）。把 `3`、`12` 抽成命名常量（`REVIEW_PER_PLAN=3`、`REVIEW_FIXED_RESERVE=12`），写在 `state.sh` 顶部或一个 `lib/budget-profile.sh`，便于审计与未来调参，不引入外部配置文件（避免过度设计，用户核心原则#14）。
- **per-run 覆盖**：`budget initialize` 增加可选 `--review-total N`（直接指定上限，跳过公式）与 `--profile <name>`（选画像）。
  - 无覆盖 → 走基线公式，`budget_profile="standard"`。
  - `--review-total N` → 直接用 N，`budget_profile="custom"`。
- **画像建议（最小集，不滥造）**：`standard`（=`3P+12`）、`generous`（大改造，如 `4P+16`）、`tight`（小批量/Light Lane 升格而来）。画像只是公式参数组，不是新机制。Light Lane 本身仍走 `unlimited`（见分册 03），画像服务的是"明确说大改造"升 Formal Lane 后的额度档位。

> **落地要点**：`cmd_budget_initialize`（`state.sh:888-924`）解析新 flag；公式行 `:916` 改为读常量/画像；写入时同时记 `budget_profile`。`workflow-infrastructure.md:171` 的「不可变」措辞要补一句"上限在 initialize 时按 profile/覆盖确定，确定后不可变"——保持"执行期不可变"不破。

### 3.3 双模式：AFK vs 在场（D3 / P1 / P3）

#### 如何判定 AFK / 在场

不靠猜，用**显式标志 + 安全默认**，三层来源（优先级从高到低）：

1. **显式命令**：`state.sh set-attendance --mode {attended|afk}`（新增子命令），用户/Coordinator 可随时切。Entry Gate 阶段 Coordinator 按用户措辞设定。
2. **Entry 措辞启发**：用户说"我盯着""我在""一步步来"→ `attended`；说"你自己跑完""我先离开""跑完叫我""AFK"→ `afk`。这是 Coordinator 在 Step 1 Entry Gate 的轻量判断，写进 `attendance_mode`，不是机器 NLP。
3. **默认值**：`afk`。理由：D1 是激进默认轻档 + AFK 优先（§5.12「AFK 优先于 HITL」），且 AFK 模式下的"过半续跑"对在场用户也无伤（在场用户随时能打断），反之"过半停死"对 AFK 用户是致命的。**安全默认偏向不卡死。**

> 设计主张（非源码事实）：默认 `afk` 是有意选择——把"卡死"这个最危险的失败模式放到需要显式 opt-in（切 `attended`）才会发生。

#### 双模式机制（替换现有 80% 行为）

| 进度 | `attended`（在场） | `afk`（无人值守） |
| --- | --- | --- |
| < 80% | 仪表：每次计数后 `additionalContext` 报「X/Y」 | 同左 |
| ≥ 80%（过半段） | **停顿**：写 `pending_direction_check`，`validate-plan-dispatch.sh` 拦非 reviewer 派发 → 用户做业务决策（continue/stop/adjust，沿用 `direction-check.md` 三选项） | **软提醒并继续**：只写 `additionalContext`「⚠ 已用 X/Y（≥80%），继续中。到顶将停。」**不写 `pending_direction_check`，不阻断** |
| ≥ 100%（到顶） | 同 AFK：硬停 | **escape hatch 硬停**：写 `pending_direction_check`（threshold_type=`exhausted`）→ 拦派发一次 → Coordinator 必须向用户报告并显式 `--allow-over-budget --override-reason` 或 stop。**这是唯一的硬停点。** |

落点：
- `track-review-budget.sh` 与 `track-effort-budget.sh`（若保留）读 `attendance_mode`，按上表分叉：`attended` 在 80% 写 DC；`afk` 在 80% 只写软文案、在 100% 才写 DC。
- `validate-plan-dispatch.sh:66-72` **保留**作为 DC 的执行点——它本身没问题，问题是上游 80% 就写 DC。改成"80% 在 AFK 下不写 DC"后，这个 `exit 2` 自然只在"在场过半"和"任意模式到顶"两种该停的时刻触发。
- escape hatch 语义：到顶的 `exit 2` 不是"永久卡死"，而是"停一次让 Coordinator 决策"。Coordinator 用 `budget check --allow-over-budget --override-reason "<reason>"`（已存在，`state.sh:967-1014`）放行后清 DC（`ack --action continue`），自主跑可续。**AFK 下 Coordinator 可在 escape hatch 自动按预设策略决策**（如"到顶后再放行一轮"），但仍受 100% 触发——保证不会无限烧。

> **§5.14 诉求如何不丢**：长 session 防无限烧 token = ① 到顶 100% 必有一次硬停（任何模式）；② 仪表全程可见（每次派发都报 X/Y）；③ 在场模式保留过半停顿。我们删的是"过半就永久卡死等人"，保留的是"到顶必停 + 全程可见"。无限烧的物理上限仍在。

### 3.4 reflux/重写按实际复杂度增量重置 `review_used`（P2）

现状：reflux 一次（`execution_reflux_count` 0→1）回到 Step 11 重跑 Plan，但 `review_used` 不减——重跑产生的 review 全部叠加到旧值上，极易吃满。

目标：reflux/Plan revision 时，按**本轮实际要重做的范围**归还额度，而非清零（清零会丢掉"已用"的审计真相）。引入 `review_credit` 字段 + 新子命令：

```bash
state.sh budget credit --run-id <id> --reason reflux --plans <n> [--reviews <m>]
```

语义：
- `check` / 钩子判断阈值时用 **`effective_used = review_used - review_credit`**，而不是裸 `review_used`。这样保留 `review_used` 作为"历史累计真相"，`review_credit` 记"因合理回流归还的额度"。
- 归还量 = 本轮 reflux 实际涉及的 Plan 数 × `REVIEW_PER_PLAN`（默认 3），即"把这些 Plan 的 review 配额重新发一次"。`--reviews m` 可显式覆盖。
- 触发点（Coordinator 侧，写进 `SKILL.md:179` 与 `final-review-repair.md:118`）：
  - `NEEDS_EXECUTION` 回流（`execution_reflux_count` 0→1）→ `budget credit --reason reflux --plans <受影响 Plan 数>`。
  - `NEEDS_PLAN_REVISION` 回 plan-writing 修订并改了 plan count → 在 Step 12a 重算时，对被重写的 Plan 归还。
- **不破"上限不可变"**：我们没改 `review_total`，只引入一个独立的归还计数器作用于"有效用量"，`review_total` 仍冻结。

> 设计主张：用 `review_credit` 而非直接 `-=` 减 `review_used`，是为了让 `direction-check.md:41` 的展示「已用 X/Y」能同时给出"累计 X / 有效 X-credit / 上限 Y"，审计透明，且 escape hatch 决策时用户看得见"是因为合理回流才接近上限"。

### 3.5 删 80% 硬阻断的安全替代论证（P1，核心）

| 维度 | 现状（硬阻断） | 目标（仪表+检查点） | 安全性论证 |
| --- | --- | --- | --- |
| 触发即停 | 80% `exit 2` 拦所有非 reviewer 派发 | 80% 在 AFK 只软信号 | 软信号通过 `additionalContext` 进下一次 Coordinator 返回——Coordinator **看得到**，可主动决策，不是黑箱续跑 |
| 防无限烧 | 靠"过半卡死" | 靠"到顶 100% 硬停" | 物理上限不变；只是把停顿点从 80%（且永久）后移到 100%（且一次性 escape hatch） |
| 在场体验 | 过半停（合理） | 过半停（保留） | 在场用户本就在，停顿即决策，无 AFK 卡死问题 |
| 误判成本 | AFK 卡死 = 整个自主跑作废 | AFK 多烧 ≤ (100%-80%) = 20% 额度后到顶停 | 最坏情况是多烧 20% 额度，远小于"整轮作废" |

**"下次返回时 `additionalContext` 软信号"的机制**：PostToolUse 钩子的 `additionalContext` 会在下一次 Coordinator 收到工具结果时注入上下文。AFK 模式下 80% 的软信号即走这条路——Coordinator 在自主循环的下一跳就看到"已 80%，继续中，到顶将停"，可据此调整策略（如收敛 review 轮次）。这比"硬 `exit 2` 让派发直接失败、Coordinator 还要解析 stderr 才知道发生了什么"更平滑，且不依赖人 ack。

### 3.6 删派生 effort 维度（P4）

基于 §2 P4 已确认的事实（effort 零独立 gate，唯一作用是抢 DC 槽位），**降级方案二选一，推荐 A**：

- **方案 A（推荐，删）**：删 `track-effort-budget.sh` 钩子（从 `hooks.json:115` 摘除注册）；`state.sh:917` 删 `effort_total` 派生；schema 把 `effort_total`/`effort_used` 标 deprecated 或移除。理由：review budget（按 Codex review 次数计）已经是成本的主要代理量，且 review 钩子已能写 DC；effort 的加权 agent 计数与 review 高度相关，独立价值低，删它直接消一套维度（呼应 §2「太复杂」「冗余」）。
- **方案 B（保守，留为咨询计数器）**：保留 `effort_used` 计数与 `additionalContext` 展示，但**永不写 `pending_direction_check`**（删 `track-effort-budget.sh:87-92`），只作为"派发了多少 agent"的可见仪表。适用于若后续想观察 agent 派发量趋势。

> 决策建议：选 A。effort 维度从未独立阻断过任何东西，保留它只是多一套要维护、要测、要解释的计数。若 plan-writing 阶段评审认为需要保留 agent 派发量可观测性，再退到 B。**无论 A/B，都要删 effort 写 `pending_direction_check` 的能力**——避免它和 review 抢槽位造成"到底哪个触发的 DC"的混淆。

相关测试影响（删 effort 时需处理）：`hooks/tests/test_effort_budget_weighting.sh`、`test_effort_budget_plan_level.sh`、`test_need_fresh_worker_continuation.sh:125-126,198-199`、`test_state.sh:69-70,79-80`、`verify-maturity.sh:89` 均断言 `effort_total`/`effort_used`，删维度时这些断言要删或改。

---

## 4. 落地要点（给 plan-writing 拆 task）

按依赖排序：

1. **schema 先行**：`workflow-state-v1.json` 加 `attendance_mode`（default `afk`）、`budget.review_credit`（default 0）、`budget.budget_profile`；effort 字段按 §3.6 决定。所有新字段给 default 保证旧 state 兼容。
2. **state.sh 命令面**：
   - `cmd_budget_initialize`（`:888`）加 `--review-total` / `--profile`；公式行 `:916` 抽常量。
   - 新增 `cmd_budget_credit`（reflux 归还）。
   - 新增 `cmd_set_attendance`（写 `attendance_mode`）。
   - `cmd_budget_check`（`:967`）阈值判断改用 `effective_used = review_used - review_credit`。
3. **钩子分叉**：`track-review-budget.sh` 读 `attendance_mode`，按 §3.3 表分叉 80%/100% 行为；`track-effort-budget.sh` 按 §3.6 删或降级。
4. **执行点保留**：`validate-plan-dispatch.sh:66-72` 不动逻辑（仍是 DC 的 `exit 2` 执行点），但其触发频率因上游改动自然下降。
5. **SKILL/references 同步**：
   - `SKILL.md:179`「回流不重置 budget usage」→ 改为「回流按受影响 Plan 数 `budget credit` 归还额度」。
   - `direction-check.md` 加双模式说明（AFK 80% 不停、100% escape hatch；attended 80% 停）+ 展示模板加「有效用量 = 累计 - credit」。
   - `plan-gates.md:46-48` 公式描述加"可 per-run 覆盖"。
   - `workflow-infrastructure.md:171`「不可变」措辞补"initialize 时按 profile 确定"。
6. **构建系统**：以上若触碰锚点内内容，跑 `build.sh --apply` 再 `--check`（CLAUDE.md 检查清单）。

---

## 5. 风险

| # | 风险 | 缓解 |
| --- | --- | --- |
| R1 | AFK 默认续跑 + escape hatch 自动放行 → 仍可能在到顶后被 Coordinator 反复 override 无限烧 | escape hatch 的 `--allow-over-budget` 每次只放行到下一次"到顶"；可在 schema 记 override 次数，超 N 次硬 BLOCKED 报用户（防 Coordinator 失控自我放行）。N 取小值（如 2）。 |
| R2 | `review_credit` 归还过多 → 变相无限额度 | 归还量严格 = 受影响 Plan 数 × `REVIEW_PER_PLAN`，且 reflux 本身已被 `execution_reflux_count` 硬限一次（`SKILL.md:174`）；归还有天然次数上限。 |
| R3 | `attendance_mode` 误设 attended → AFK 跑被过半停 | 默认 `afk`（安全默认）；Entry Gate 显式确认；用户可随时 `set-attendance` 切换。 |
| R4 | 删 effort 维度破坏现有测试 / verify-maturity | §3.6 已列受影响测试清单；plan-writing 把"改/删断言"作为同一 task 的验收项。 |
| R5 | 旧 state 文件无新字段 | 全部新字段给 default；`state.sh` 读取处用 `// default`；session-start resume 不依赖新字段。 |
| R6 | 与分册 03 Light Lane 的 `unlimited` 重叠 | 本分册只管 Formal Lane 的 bounded budget 行为；Light Lane 走 `unlimited`（03 负责），不进本分册的阈值逻辑。明确分界：`budget_status==unlimited` 时所有阈值/双模式逻辑短路（现状 `track-effort-budget.sh:32`、`track-review-budget.sh:44` 已对 unlimited 短路，保留）。 |

---

## 6. 验收信号（可观测）

1. **AFK 不再卡死**：`attendance_mode=afk` + Formal Lane，跑到 review_used ≥ 80% 时，**派发不被 `exit 2` 拦**，`additionalContext` 出现「≥80%，继续中」软信号；只有到 100% 才出现一次 escape hatch 停顿。（回归测试：构造 state 至 80%，发非 reviewer Agent，断言 `validate-plan-dispatch.sh` exit 0。）
2. **在场仍停顿**：`attendance_mode=attended` 跑到 80%，写 `pending_direction_check`，派发被拦 `exit 2`。（回归测试断言 exit 2 + DC pending。）
3. **reflux 归还生效**：`budget credit --reason reflux --plans 2` 后，`check` 的有效用量下降 `2×3=6`，原本会触发阈值的状态回到阈值下。（回归测试。）
4. **公式可覆盖**：`budget initialize --plan-count 4 --review-total 50` → `review_total=50` 且 `budget_profile=custom`；不带覆盖 → `3*4+12=24` 且 `profile=standard`。
5. **effort 维度消失/降级**：方案 A 下 `hooks.json` 无 `track-effort-budget` 注册、schema 无 effort 字段（或标 deprecated）；任何模式下 effort 不再写 `pending_direction_check`。
6. **防无限烧仍在**：到顶 100% 必有一次硬停（grep 钩子确认 100% 分支写 DC）；override 次数有上限（R1）。
7. **漂移归零**：`SKILL.md:179`、`direction-check.md`、`plan-gates.md` 与新代码一致，不存在"文档说不重置、代码已归还"的矛盾。

---

## 7. 与其他分册的接口

- **依赖 03（Light Lane）**：Light Lane = `unlimited`，短路本分册全部阈值逻辑；`budget_profile` 的 `tight` 档服务"Light 升 Formal"后的小额度场景。本分册的 `attendance_mode` 标志也可被 03 的 Entry 判定复用。
- **被 02（routes-as-data）约束**：`validate-plan-dispatch.sh` 从读 `PHASE==execution` 字面量改为读 routes 清单（02 负责）；本分册只保证 DC 的 `exit 2` 执行点语义不被 02 改动破坏。
- **被 01（保留清单）约束**：§5.14「防无限烧 token」是承重项，本分册的"到顶硬停 + 仪表 + 在场过半停"是它的新载体，01 复验时以本分册 §3.3/§3.5 为准。
- **被 07（hook 层）约束**：删 `track-effort-budget.sh` 是 07「hook 重排/删假门」的一部分；本分册给出语义依据，07 给出整体 hook 表的落点。

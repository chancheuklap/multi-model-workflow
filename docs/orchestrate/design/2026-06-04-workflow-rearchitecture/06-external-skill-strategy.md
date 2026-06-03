# 06 · 外部 Skill 战略支柱（新维度）

> 本分册在 `00-overview.md` 锁定决策 **D5（外部 skill = 战略杠杆）** 约束下展开，受 §6 北极星不变量约束。与骨架冲突以骨架为准。
>
> - 适用对象：`plugin/`（v3.10.0）
> - 方法论：plugin 源码为唯一 ground truth；每条事实主张引 `file:line`，均经本分册作者亲自 `Read`/`grep` 核验。
> - 上游事实：marketplace 描述自陈 "Multi-model orchestration layer **on top of Superpowers**"（`.claude-plugin/marketplace.json` `description` 字段）——本插件的能力 skill 大多来自 obra/superpowers 等外部仓库，这是 D5 的物理基础。

---

## 0. 结论先行（给 plan-writing 阶段直接消费）

1. **三机制定调**：`embed`（frontmatter `skills:` 嵌 subagent，给常用专项能力）/ `invoke`（运行时 `Skill()`，按任务需要）/ **禁止 `internalize`（抄散文进 reference）**。内化 = 主动放弃上游更新，是反模式，本方案不再新增、并标记现存内化点。
2. **嵌入矩阵**：4 个未嵌 skill 的 agent（`code-explorer` / `complex-code-explorer` / `plan-writer` / `docs-worker`）按职责补 `skills:` 字段；已嵌的 3 个（`pack-executor` / `complex-pack-executor` / `root-cause-analyst`）保持不动或微调。详见 §3。
3. **补接线**：`frontend-design` / `impeccable` 在 Discovery + mockup 环节正式接入（用户珍视前端 mockup 能力，§5 保留清单第 9 条）；`docs-worker` 嵌 `frontend-design`，承接 mockup 视觉规格补全。
4. **清悬空**：`zoom-out` 在源码 6 处被引用、且被 `session-start.sh:58` 声明为已安装 user-level skill，但**不在本运行环境的可用 skill 列表中**（见 §4 核验）——判定为悬空引用，统一替换为 `improve-codebase-architecture` + `code-explorer` 组合或删除。
5. **关键正交约束**：能力 skill 的触发由"**任务需要**"驱动，与"**流程档位轻重**"正交。即使任务走 Light Lane（D1），只要它是前端 UI 任务，就应触发 mockup design skill——档位决定流程步骤多少，不决定专项能力调不调。
6. **上游汲取 routine**：给一个轻量"季度/触发式 upstream-sync"设想（§6），避免 fork 后僵死。

---

## 1. 现状（源码锚点）

### 1.1 三种机制现实并存，无统一策略

| 机制 | 现状定义 | 已核验锚点 |
| --- | --- | --- |
| **embed**（frontmatter 嵌） | agent 在 YAML frontmatter 写 `skills:` 列表，subagent 启动即带该能力 | `pack-executor.md:20-21`（`skills: [tdd]`）、`complex-pack-executor.md:20-21`（`skills: [tdd]`）、`root-cause-analyst.md:22-24`（`skills: [diagnose, tdd]`） |
| **invoke**（运行时调用） | SKILL.md / reference / agent 正文写 `Skill({ skill: "..." })`，按需在主线程或 subagent 内触发 | 见下表"运行时调用清单" |
| **internalize**（散文内化） | 把外部 skill 的方法论抄成本仓 reference 散文，不再调用原 skill | `issue-splitting.md` 整篇即 `to-issues` 方法论的内化（tracer bullet / vertical slice）：`issue-splitting.md:21-31` 写 "Step 12c：拆分 vertical slice"、"tracer bullet 大 issue"、"thin vertical slice 切穿所有集成层" |

**运行时 `Skill()` 调用清单（已核验，grep `Skill(` 全量）**：

- `grill-with-docs`：`orchestrate-discovery/SKILL.md:85,87,137`（Step 0 同步启动，全程 context 维护）、`plan-review-resolution.md:66`、`orchestrate-execution/SKILL.md:311`
- `improve-codebase-architecture`：`orchestrate-discovery/SKILL.md:137`、`discovery-discussion.md:33,56`、`issue-splitting.md:19`、`orchestrate-workflow/SKILL.md:134,155`、`plan-review-resolution.md:19,65,98`、`plan-writing-methodology.md:100`、`plan-preconditions.md:36`、`plan-writer-dispatch.md:110`、`final-review-disposition.md:37`、`orchestrate-execution/SKILL.md:310`
- `prototype`：`orchestrate-discovery/SKILL.md:137`、`discovery-discussion.md:63`、`plan-preconditions.md:35`、`pack-executor.md:53`（agent 正文）、`complex-pack-executor.md:34`
- `frontend-design`：`orchestrate-discovery/SKILL.md:91,137`、`discovery-discussion.md:63`、`workflow-infrastructure.md:77`（产出目录注释）
- `triage`：`orchestrate-discovery/SKILL.md:137`、`discovery-discussion.md:41`、`orchestrate-workflow/SKILL.md:131`、`plan-preconditions.md:32`、`plan-writer-dispatch.md:107`、`docs-worker.md:35`（agent 正文）
- `diagnose`：`orchestrate-discovery/SKILL.md:137`、`discovery-discussion.md:31`、`orchestrate-workflow/SKILL.md:132`、`plan-preconditions.md:34`、`plan-writer-dispatch.md:108`、`orchestrate-execution/SKILL.md:313`、`pack-executor.md:53`、`complex-pack-executor.md:34`
- `zoom-out`：`orchestrate-discovery/SKILL.md:137`、`orchestrate-workflow/SKILL.md:135`、`plan-review-resolution.md:98`、`plan-preconditions.md:37`、`plan-writer-dispatch.md:111`、`orchestrate-execution/SKILL.md:312`

### 1.2 已嵌 / 未嵌 agent 现状（8 个 .md 全核验）

| agent | model / effort | `skills:` frontmatter | 正文 `Skill()` |
| --- | --- | --- | --- |
| `pack-executor` | sonnet / xhigh | `tdd`（`:20-21`） | `diagnose` / `prototype`（`:53`） |
| `complex-pack-executor` | opus-1m / high | `tdd`（`:20-21`） | `diagnose` / `improve-codebase-architecture` / `prototype`（`:34`） |
| `root-cause-analyst` | opus-1m / xhigh | `diagnose, tdd`（`:22-24`） | —（已嵌即用） |
| `code-explorer` | sonnet / high | **无**（`:13-18` 仅 tools，含 `Skill`） | 无 |
| `complex-code-explorer` | opus-1m / high | **无**（`:13-18` 仅 tools，含 `Skill`） | 无 |
| `plan-writer` | opus-1m / xhigh | **无**（`:11-19` 仅 tools，含 `Skill`） | `improve-codebase-architecture`（`:24`） |
| `docs-worker` | sonnet / high | **无**（`:11-19` 仅 tools，含 `Skill`） | `grill-with-docs` / `triage`（`:35`） |
| `persona.md` | —（规格文件，非 agent） | n/a | n/a |

**关键不对称（病灶）**：`plan-writer` 和 `docs-worker` 正文已经在用 `Skill({...})` invoke，但 frontmatter 没有对应 `skills:` 声明——能力靠"正文散文请求 + agent 自觉调用"维系，没有 frontmatter 的机器级保证。这正是 §2 病根的微观体现。

### 1.3 build 系统现状：`skills:` 字段尚未单源化

`build/templates/` 下 7 个模板（`preamble` / `voice-directive` / `worker-loop` / `control-envelope` / `review-dispatch.content-only` / `sendmessage-resume` / `signpost`），**无一管理 frontmatter `skills:` 字段**（grep `skills:` 在 `build/templates/` 零命中）。即每个 agent 的 `skills:` 现在是手维护、散落各文件——与 `07` 要处理的 twin 90% 重叠同源（embed 矩阵落地时应一并纳入 build 单源，见 §3.4 与 `07` 交接）。

### 1.4 三个悬空 / 零接线点（已核验）

| skill | 全仓引用计数 | 判定 | 锚点 |
| --- | --- | --- | --- |
| `impeccable` | **0**（`grep -rni impeccable plugin/` → EXIT=1） | 已知珍视能力（前端打磨），但完全未接线 | 仅出现在 `CLAUDE.md:96`（外部源仓库 URL `pbakaus/impeccable`） |
| `to-issues` | **0**（`grep -rni to-issues plugin/` → EXIT=1） | 方法论已内化进 `issue-splitting.md`，原 skill 名零引用 | `issue-splitting.md:21-31` 是其内化体 |
| `zoom-out` | 6 处引用，但运行环境无此 skill | 悬空引用：声明已装、实际不可调 | 见 §4 |

---

## 2. 问题（病因，对齐骨架 §2）

1. **三机制无策略 = 调用全靠主线程/agent 自觉**：embed 给了机器保证（subagent 启动即带），invoke 写在散文里靠读完执行，internalize 直接切断上游。三者混用且无判定规则，导致：① 该常驻的能力（如 explorer 的架构理解）没嵌 frontmatter，每次靠正文提醒；② 该按需的能力（如 triage）有时嵌死有时散文请求，不一致。

2. **internalize 是慢性自残**：`to-issues` 被抄成 `issue-splitting.md` 后，上游 obra/superpowers 对 tracer-bullet 拆分方法的任何改进都进不来——本仓的散文成了一份"上游某历史版本的快照"，越用越旧。骨架 §5 第 12 条保留的是 vertical-slice/tracer-bullet **内核**（要保留），但保留内核 ≠ 必须靠内化散文实现。

3. **珍视能力零接线**：`impeccable`（前端界面打磨/审计，用户可用的强能力）全仓零引用；`frontend-design` 虽被引用却**不在 `session-start.sh:58` 的 user-level 已安装清单里**（该行只列 `diagnose, prototype, improve-codebase-architecture, zoom-out, triage, grill-with-docs`）——存在"引用了但未声明安装"的接线裂缝。用户珍视的 mockup 能力（§5 第 9 条）依赖的两个 skill 一个零接线、一个接线不全。

4. **悬空引用污染路由表**：`zoom-out` 被 6 处路由表当作合法 disposition 出口（`NEEDS_CONTEXT` → `zoom-out`），一旦它实际不可调，这些路由分支就是死分支——主线程按散文路由过去会扑空，又退回"自觉处理"，加剧骨架 §2 的"僵硬靠自觉"病根。

---

## 3. 目标设计

### 3.1 三机制决策树（统一策略）

```
收到一个"要不要用某 skill X"的判断：

  X 是否本 agent 角色的【高频常驻专项能力】？
  （即：该 agent 几乎每次任务都会用到 X 才能尽责）
    ├─ 是 → embed：写进 agent frontmatter skills: 字段
    │        理由：机器级保证（subagent 启动即带），不靠散文自觉
    │        例：pack-executor 几乎每个 pack 都 TDD → embed tdd
    │
    └─ 否 → X 是否【特定情况才需要、但情况会发生】？
            ├─ 是 → invoke：在 SKILL.md / reference / agent 正文写 Skill({skill:"X"})
            │        理由：按任务需要触发，不污染常驻 context
            │        例：Discovery 偶遇 UI 任务 → invoke frontend-design
            │
            └─ 否（永远不需要）→ 不接线

  ⛔ 任何情况都【禁止 internalize】（把 X 的方法论抄成本仓散文 reference）：
     internalize = 放弃上游更新 = 反模式。
     已存在的内化点（issue-splitting.md = to-issues）标记为技术债，
     不新增、不扩大；迁移期评估能否退回 invoke（见 §3.3）。
```

**embed vs invoke 的判定线（可操作）**：

- **embed**：能力与 agent 角色"同生命周期"——不带它 agent 就不完整。代价：subagent 每次启动加载该 skill 的 context（轻微常驻成本）。
- **invoke**：能力是"路径分支上才出现"——主路径不需要。代价：触发点写在散文里，需要被 Read 到才会执行（接受，因为它本就是低频）。
- **判定冲突时偏向 invoke**：embed 是常驻成本，invoke 是按需成本；D4 要降 token，能力非高频则不嵌。

### 3.2 skill → subagent 嵌入矩阵（逐 agent 建议）

> 原则：embed 只放"该角色高频专项能力"；低频按需的留 invoke。已嵌的不无故扩。

| agent | 现 `skills:` | 建议 `skills:`（embed） | 保留为 invoke | 理由 |
| --- | --- | --- | --- | --- |
| `pack-executor` | `tdd` | `tdd`（不变） | `diagnose` / `prototype` | TDD 是每 pack 必走 → embed；diagnose 仅遇不可解 bug、prototype 仅验技术方案 → 低频 invoke（`:53` 现状已对） |
| `complex-pack-executor` | `tdd` | `tdd`（不变） | `diagnose` / `improve-codebase-architecture` / `prototype` | 同上；架构判断虽常见但属"特定决策点"，留 invoke（`:34` 现状已对） |
| `root-cause-analyst` | `diagnose, tdd` | `diagnose, tdd`（不变） | — | diagnose 是其核心方法（每次根因调查必走）、tdd 用于写回归测试 → 两者皆高频 → embed 正确 |
| `code-explorer` | 无 | **不嵌**（保持空） | `improve-codebase-architecture`（新增正文 invoke 提示） | 窄范围只读调查，多数任务用 rg/grep 即可；架构理解仅"模块边界"类问题才需 → 低频 invoke。不嵌避免无谓常驻成本 |
| `complex-code-explorer` | 无 | **`improve-codebase-architecture`** | `diagnose`（根因模式时） | 多模块/架构摩擦调查是其主业（`:23` "架构摩擦"、`:38` deletion test/seam/module depth），几乎每次都需架构透镜 → 高频 → embed |
| `plan-writer` | 无 | **`improve-codebase-architecture`** | `to-issues`（若退内化，见 §3.3）/ `grill-with-docs` | 正文 `:24` 已每次用 `improve-codebase-architecture` 理解模块边界/合同表面 → 既然每次都用，应 embed 而非散文请求（消除 §1.2 不对称） |
| `docs-worker` | 无 | **`frontend-design`** | `grill-with-docs` / `triage` | docs-worker 职责含"为 UI 补齐 mockup anchors / viewport / states"（`:8`、`:41`）→ 承接 mockup 视觉规格补全需前端透镜 → embed frontend-design；grill/triage 仅特定文档类型才用 → 留 invoke（`:35` 现状） |

**矩阵净变更（plan-writing 可直接消费的 diff 清单）**：

1. `complex-code-explorer.md` frontmatter 增 `skills: [improve-codebase-architecture]`。
2. `plan-writer.md` frontmatter 增 `skills: [improve-codebase-architecture]`；正文 `:24` 的 `Skill({...})` 散文请求可保留为冗余提示或删（embed 后已机器保证）。
3. `docs-worker.md` frontmatter 增 `skills: [frontend-design]`。
4. `code-explorer.md` 不动 frontmatter；正文可加一行"模块边界类问题 → `Skill({ skill: "improve-codebase-architecture" })`"的 invoke 提示（非必须）。
5. 其余 3 个执行/根因 agent 的 `skills:` 不变。

### 3.3 internalize 退场策略（`to-issues` / `issue-splitting.md`）

- **保留内核，退回 invoke 优先**：骨架 §5 第 12 条要求保留 vertical-slice/tracer-bullet 内核——这是"能力要在"，不是"必须靠本仓散文"。目标：Discovery Step 12 拆大 issue 处，把"严格执行 `issue-splitting.md` 散文"改为"`Skill({ skill: "to-issues" })` 驱动 + 本仓只保留**项目专属约束薄层**"（写入路径 `docs/orchestrate/issues/<slug>/`、编号约定、AFK/HITL 标记等本仓特有规则，`issue-splitting.md:51-64`）。
- **若 `to-issues` 在目标环境不可用**（需 §4 同款核验确认安装状态）：则保持现状内化，但在 `issue-splitting.md` 顶部加一行溯源注释"本方法论内化自 `to-issues`，上游更新需手动同步（见 06 §6 routine）"，把隐性技术债显性化。
- **不做**：把更多 invoke 的 skill 内化进散文。这是单向闸门——只退不进。

### 3.4 embed 字段纳入 build 单源（与 `07` 交接）

当前 `skills:` 手维护、散落（§1.3）。embed 矩阵落地后，frontmatter `skills:` 字段应与 `07` 的 agent twin 收口同批纳入 build 单源管理（新增一个 resolver 步骤或在现有 agent frontmatter 模板化时一并处理），避免再次出现"6 个 agent 各写一份、改一处漏一处"的漂移。**本分册不规定 build 实现细节**（属 `07` / `build/README.md` 边界），仅声明依赖关系：embed 矩阵的"单源化"挂在 `07` 的 build 重排下。

---

## 4. `zoom-out` 悬空核验与处置

**核验过程（亲自执行）**：

1. `grep -rni 'zoom-out' plugin/` → 6 处引用（`session-start.sh:58`、`orchestrate-workflow/SKILL.md:135`、`plan-review-resolution.md:98`、`plan-preconditions.md:37`、`plan-writer-dispatch.md:111`、`orchestrate-execution/SKILL.md:312`）。
2. `session-start.sh:58` 把 `zoom-out` 与 `diagnose / prototype / improve-codebase-architecture / triage / grill-with-docs` 并列声明为"User-level skills（已安装）"。
3. **但本运行环境的可用 skill 列表中没有 `zoom-out`**：可用的同源 skill 有 `diagnose` / `prototype` / `improve-codebase-architecture` / `grill-with-docs` / `triage` / `frontend-design` / `impeccable`——独缺 `zoom-out`。

**判定**：`zoom-out` 是悬空引用。它被 `session-start.sh:58` 当作已安装、被 5 处路由表当作合法 `NEEDS_CONTEXT` 出口，但实际不可调（至少在当前环境）。所有指向它的路由分支都是潜在死分支。

> 诚实标注：本核验确认的是"`zoom-out` 不在当前运行环境的可用 skill 列表中"。它是否在用户某个未启用的外部仓库里、或曾被 obra/superpowers 移除——本分册无法从 plugin 源码确证（外部仓库属禁区/不可读）。plan-writing 前应让用户或一次 upstream-sync（§6）拍板"补装 or 替换"。

**处置（二选一，建议默认 B）**：

- **A. 补装**：若用户确认 `zoom-out` 仍是想要的外部能力 → 在对应外部仓库重新启用，6 处引用不动。
- **B. 替换/删除（默认）**：`zoom-out` 的语义是"拉远看模块地图/上下文"，与 `improve-codebase-architecture`（模块边界/深度）+ `code-explorer`（窄范围事实）高度重叠。处置：
  - `session-start.sh:58` 删 `zoom-out`。
  - 5 处 `NEEDS_CONTEXT → zoom-out` 路由统一改为 `NEEDS_CONTEXT → code-explorer`（已是各处的并列选项，如 `:135` 已写"派 `code-explorer` / `Skill({ skill: "zoom-out" })`"）+ 模块边界需求转 `improve-codebase-architecture`。
  - 净效果：消除 6 处死分支，无能力损失（语义被现有 skill 覆盖）。

---

## 5. mockup / 前端能力正式接线（`impeccable` + `frontend-design`）

> 用户珍视前端 mockup 能力（骨架 §5 第 9 条："Mockup 与文字设计平级、原子拆解为视觉规格表"）。当前 `impeccable` 零接线、`frontend-design` 接线不全。这是 D5 下用户重点强调维度，写充分。

### 5.1 接线裂缝（现状）

- `frontend-design` 被 `orchestrate-discovery/SKILL.md:91,137` 与 `discovery-discussion.md:63` 引用（"生成高品质前端原型"），但**不在 `session-start.sh:58` 已安装声明里**——引用了未声明，与 `zoom-out` 相反方向的裂缝。
- `impeccable` 全仓零引用，但它正是"界面打磨/审计/视觉层级/可访问性/anti-pattern"的强能力（用户珍视的打磨维度）——完全未纳入工作流。
- mockup 产出目录已有占位：`workflow-infrastructure.md:77` `└── mockups/ # prototype / frontend-design 产出`——基础设施在，能力接线缺。

### 5.2 目标接线（分两个生命周期阶段）

**阶段一·Discovery 生成 mockup（生成态，invoke）**：

- `orchestrate-discovery/SKILL.md:89-91` 的"Mockup 生成留空间"段已正确放手给用户驱动 `frontend-design` / `prototype`。目标：
  1. 把 `frontend-design` 补进 `session-start.sh:58` 的已安装 user-level skill 声明（消除引用未声明裂缝）。
  2. 在该段显式补 `impeccable` 为"mockup 打磨/审计"的可选 skill：`frontend-design` 负责**生成**，`impeccable` 负责**打磨与审计**（视觉层级、可访问性、anti-pattern、UX copy）。二者职责互补、非替代。
  3. 维持"用户主动驱动、Coordinator 不催促不并行"的现有纪律（`:91`）——接线只是把能力摆上桌，不改变驱动权归属。

**阶段二·mockup → 视觉规格表（落档态，embed）**：

- 骨架 §5 第 9 条要求 mockup 原子拆解为视觉规格表（不只传目录路径），由 `docs-worker` 承接（其职责含"为 UI 补齐 mockup anchors / viewport / states / interaction / acceptance"，`docs-worker.md:8,41`）。
- 目标：`docs-worker` embed `frontend-design`（§3.2 矩阵第 6 行），让它带前端透镜把 mockup 拆成 anchors/viewport/states/interaction 的结构化规格，写入 acceptance criteria。
- 可选增强：`docs-worker` 在做 UI 文档自足性审计时 invoke `impeccable` 校验"规格是否覆盖 empty state / error state / responsive"等边界（impeccable 强项），但属低频 → invoke 不 embed。

### 5.3 与 D1/D4 正交约束（关键，§0 第 5 条展开）

- mockup design skill 的触发由**任务是否前端 UI**驱动，**不由档位轻重驱动**。
- 即使某改动走 Light Lane（D1 激进默认轻档、跳过 Discovery 重型评审），只要它是"加个前端按钮/调个页面布局"，就应触发 `frontend-design`（生成）/ `impeccable`（打磨）。
- 落地点：Light Lane 的 routes 数据（`03` 分册）应允许"轻档 + UI 子标记"组合——轻档省的是流程评审步骤（Codex 外审、双文档对等），不省任务本身需要的专项能力。mockup skill 接在"任务类型=UI"这条正交轴上，与 lane 轴独立判定。
- **反例（要避免）**：把"调 mockup skill"绑死在"走 Formal Lane"上 → 后果是所有轻档 UI 改动都失去前端能力，违背 D5"嵌进流程提升专项能力"的本意。

---

## 6. 上游持续汲取机制（轻量 routine，避免 fork 僵死）

> D5 第 ② 条："靠上游持续更新、汲取外部方法"。当前无任何同步机制，外部 skill 一旦内化（如 `to-issues`）即与上游断联。给一个轻量设想，不过度设计。

### 6.1 外部源仓库台账（已核验，来自 `CLAUDE.md:94-100`）

| 来源 | URL | 本仓用途 |
| --- | --- | --- |
| obra/superpowers | `https://github.com/obra/superpowers`（`CLAUDE.md:100`） | 主依赖（marketplace 自陈 "on top of Superpowers"）；diagnose/prototype/improve-codebase-architecture/triage/grill-with-docs/zoom-out 等能力 skill 来源 |
| mattpocock/skills/engineering | `CLAUDE.md:94` | 工程方法论汲取来源 |
| pbakaus/impeccable | `CLAUDE.md:96` | 前端界面打磨能力（待接线，§5） |
| garrytan/gstack | `CLAUDE.md:98` | 已有 §7"明确不借鉴"清单（骨架 §5 第 15 条，勿再提） |

### 6.2 轻量 upstream-sync routine（设想，非本分册落地物）

**目标**：定期"汲取方法"而非"机械 merge"——外部 skill 更新时，看其方法论变化是否值得吸收，而不是 fork 一份僵死。

**触发**（任一即可，不设强制 cron 阻断）：

1. **季度触发**：每季度一次轻量巡检（手动或挂 `weekly-memory-consolidation` 同款低频 routine）。
2. **事件触发**：要新接一个外部 skill 时（如本方案接 `impeccable`），顺手记录其当前 commit/版本作为基线。
3. **内化债触发**：每次要改 `issue-splitting.md` 这类内化体时，先看上游对应 skill 是否已演进。

**步骤（一条轻链）**：

1. 对 §6.1 台账每个源，`gh api` 或浏览看自上次基线以来的 changelog / 显著 commit（只看 skill 的方法论部分，不看全仓）。
2. 判定三类：① 纯实现/无关 → 跳过；② 方法论改进且本仓用 invoke → 无需动作（运行时自动吃到最新，前提是 skill 已安装可调）；③ 方法论改进但本仓已 internalize（如 `to-issues`）→ 评估手动同步散文 or 退回 invoke（§3.3）。
3. 把基线 commit / 版本记进一处轻量台账（建议 agent-memory 或本仓一个 `external-skill-baselines.md`，非强制）。
4. 无变化静默；有值得吸收的 → 走正常 design/plan 流程评估，不直接动代码。

**关键设计取舍**：

- **不 fork、不 vendor 进本仓**：能 invoke 的 skill 保持外部安装态，运行时吃最新——这本身就是"持续更新"的最省力形态。internalize 是唯一会断联的形态，故 §3 把它设为单向只退闸门。
- **routine 是仪表不是闸门**（与骨架 D3/D4 同构）：upstream-sync 只提醒、不阻断任何流程。避免引入"同步没做完不让干活"的保守门禁（用户核心原则 #14，不过度设计）。

---

## 7. 落地要点（plan-writing 可直接拆 pack）

| # | 改动 | 文件锚点 | 类型 |
| --- | --- | --- | --- |
| L1 | `complex-code-explorer` frontmatter 增 `skills: [improve-codebase-architecture]` | `complex-code-explorer.md:13-21` | embed 矩阵 |
| L2 | `plan-writer` frontmatter 增 `skills: [improve-codebase-architecture]`；正文 `:24` invoke 提示可降冗余 | `plan-writer.md:11-24` | embed 矩阵 |
| L3 | `docs-worker` frontmatter 增 `skills: [frontend-design]` | `docs-worker.md:11-19` | embed 矩阵 |
| L4 | `frontend-design` 补进 `session-start.sh:58` user-level 已安装声明 | `session-start.sh:58` | 接线 |
| L5 | `impeccable` 接进 Discovery mockup 留空间段（生成态 invoke 可选）+ docs-worker UI 审计可选 invoke | `orchestrate-discovery/SKILL.md:89-91` | 接线 |
| L6 | `zoom-out` 处置（默认 B）：删 `session-start.sh:58` 声明 + 5 处路由改 `code-explorer`/`improve-codebase-architecture` | §1.1 / §4 的 6 处锚点 | 清悬空 |
| L7 | `issue-splitting.md` internalize 债显性化（顶部溯源注释）或退回 `to-issues` invoke（视安装状态） | `issue-splitting.md:1-31,51-64` | internalize 退场 |
| L8 | embed 矩阵 `skills:` 字段纳入 `07` 的 build 单源（依赖项，非本分册落地） | `build/templates/`（现无 skills 模板） | 与 07 交接 |

---

## 8. 风险

1. **embed 增常驻成本**：给 explorer/plan-writer/docs-worker embed skill 会增加每次 subagent 启动的 context 加载。缓解：矩阵严格按"高频专项"判定，只嵌 1 个/agent，低频一律留 invoke；与 D4 降 token 目标的净影响在 `08` 量化（embed 增量 << invoke 散文重复 Read 的省量）。
2. **`zoom-out` 替换误删能力**：若用户实际仍依赖 `zoom-out` 的独立语义，删除会丢能力。缓解：默认 B 前先经 §6 upstream-sync 或用户一次确认；A/B 二选一交用户拍（属业务可见决策边界）。
3. **`impeccable`/`frontend-design` 外部 skill 不可用风险**：接线后若环境未装，触发即扑空（同 `zoom-out` 病）。缓解：L4/L5 落地前先做 §4 同款"运行环境可用性核验"；只对已确认可调的 skill 接线。
4. **internalize 退回 invoke 引入运行时依赖**：`issue-splitting.md` 退回 `to-issues` invoke 后，拆 issue 这一关键步骤变为依赖外部 skill 可用。缓解：保留本仓项目专属薄层（路径/编号/AFK 标记），即使 `to-issues` 不可用，薄层 + 内核仍能手工拆；这也是 §3.3 设"若不可用则保持内化 + 溯源注释"兜底的原因。
5. **build 单源化（L8）耦合 `07`**：embed 矩阵若先于 `07` 落地，`skills:` 仍手维护，可能与 `07` 的 build 重排二次冲突。缓解：排期上 L1-L3 的 frontmatter 改动可独立先行（纯数据增字段），单源化挂 `07` 之后做，不阻塞矩阵生效。

---

## 9. 验收信号

1. **三机制有据可查**：每个 agent 的 `skills:` 字段与本分册矩阵（§3.2）一致；新增 invoke 点不引入新 internalize。可验：`grep skills: plugin/agents/*.md` 输出匹配矩阵。
2. **零悬空引用**：`grep -rni 'zoom-out' plugin/` 命中数与处置方案一致（默认 B → 仅剩可被 `code-explorer`/`improve-codebase-architecture` 覆盖的语义，无死路由）；`session-start.sh:58` 声明的 skill 全部在运行环境可调。
3. **mockup 能力可触发**：`frontend-design` 在 `session-start.sh:58` 声明完整；Light Lane + UI 任务能触发 mockup skill（与档位正交，§5.3）——可由一条 routes 数据（UI 子标记，`03` 提供）+ 一次手测验证。
4. **`impeccable` 接线非零**：`grep -rni impeccable plugin/` 不再 EXIT=1（至少 Discovery mockup 段有一处接线）。
5. **internalize 债显性**：`issue-splitting.md` 要么退回 `to-issues` invoke，要么顶部有溯源注释——不再是"隐性快照"。
6. **upstream-sync routine 存在且为仪表**：有一处轻量同步设想/台账，且不阻断任何流程（无新增 `exit 2` 类闸门）。
7. **能力零丢失**：骨架 §5 第 9（mockup 平级）、第 12（vertical-slice/tracer-bullet 内核）、第 8（grill-with-docs 维护术语）经此分册改动后仍可用——`08` 给回归测试。

---

## 10. 与其他分册的交接

- **依赖 `03`（Light Lane）**：§5.3 的"UI 子标记与 lane 正交"需 `03` 在 routes 数据里提供"轻档 + UI"组合的合法表达。
- **依赖 `07`（agent/hook 层）**：§3.4 / L8 的 embed `skills:` 字段单源化挂 `07` 的 build 重排；agent twin 收口与 frontmatter 模板化同批处理。
- **被 `08`（迁移验收）消费**：§9 验收信号 + §8 风险缓解的排期（L1-L3 可独立先行）进 `08` 的分期依赖图与量化验收。
- **受 `05`（skill/context economy）约束**：embed 增量与 invoke 散文重复 Read 省量的净 token 影响，由 `05`/`08` 量化口径统一计算。

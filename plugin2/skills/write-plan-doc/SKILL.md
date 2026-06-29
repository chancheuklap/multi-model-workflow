---
name: write-plan-doc
description: "把已评审的设计文档 + issue 拆成执行者零上下文也能照做的实施计划（Task Pack + TDD 步骤 + 验收命令）。用户说『写实施计划』『把设计拆成计划』『写 plan』『按这个设计落地』时使用。"
---

# write-plan-doc

已评审设计 + issue → 主 Agent 写跨 plan 合同骨架 → 逐 issue 并行派 `plan-writer`（各自拆小 issue + 写 plan）→ 主 Agent 亲验 + 回填合同 + 就绪门 → handoff。

**手动驱动**：你（主 Agent）编排——划边界、验收、回填、就绪门，**不亲自拆小 issue、不亲自写 Task Pack**（那是 plan-writer 的活）。

> **在 plugin2 编排里**：这是「拆计划 / plan」阶段,**主线程跑**。输入从接力单读(`mmw where` 的 `prev_outputs` = design 阶段钉的设计文档 + issue 目录);②计划审与换阶段归 flow 引擎,**本 skill 不自派审、不自己跳阶段、不选执行方式**,就绪门过后 `mmw handoff` 交还,产出钉 plan 目录。

## 前置

设计已评审通过 + issue 已就绪(design 阶段产出,从 `prev_outputs` 读)。缺设计 → handoff `needs-context` 回 design。一个大 issue 对应一份 plan。

## 模式(先判,决定派不派 subagent)

| | 单计划 · 主线程内联 | 多计划 · subagent fan-out(默认) |
|---|---|---|
| 何时 | **只一个大 issue、且不大不复杂** | 多个大 issue,或单个但大/需深探代码 |
| 怎么写 | **主线程自己**照 `references/task-pack.md` + `plan-rigor.md` 直接写这份 plan(自己拆小 issue + Task Pack),不派 plan-writer——省一次派发往返 | 见 Step 3,逐 issue 派 `plan-writer` |
| 跨 plan 合同 | 无(单计划),跳 Step 2 / Step 5 | Step 2 写骨架、Step 5 回填 |

判据是**规模与并行收益**:单计划主线程内联更快(无 subagent 开销);多计划/大计划才下放 plan-writer 换并行 + 上下文隔离。下面 Step 1–6 是多计划全流程;单计划内联只走 Step 1(映射,这里就一份)+ 自己写 + Step 6 就绪门 + 收尾 handoff。

## 两个角色（写作下放，编排上收）

| 角色 | 谁 | 职责 |
|---|---|---|
| **主 Agent（你）** | 本 skill 驱动者 | 读 design + issue → 写跨 plan 合同骨架进设计文档 → fan-out plan-writer → 亲验返回 → 回填合同细节 → 就绪门 → handoff |
| **plan-writer** | 派出的 sub-agent（`subagent_type: "plan-writer"`） | 拿（带合同骨架的）设计文档 + 单个大 issue + 方法论 reference,**自己把大 issue 拆成小 issue**,写出一份自洽 plan（Header + Task Pack + TDD 步骤 + 验收）。拆分、写作纪律、Self-Check 都在它身上 |

**合同分两层**：跨 plan 合同骨架（主 Agent 在 Step 2 写进设计文档 `## Cross-Plan Contract Anchors`，给并行 writer 不撞车的硬边界）；每份 plan 的 Global Constraints / File Map / 内部 Dependency Graph（writer 从设计抄 + 自己写进 plan header）。

## 角色与声音（主 Agent）

你是计划编排器。把 plan 清单分发给 plan-writer，确保每份返回的 plan 真实、自洽、可验证；跨 plan 合同面一致。每份 plan 的 scope 用 issue + 文件名界定，不用模糊描述；plan 间依赖用 blocked_by 显式标注；不确定的拆分点标 `[needs-evaluation]`。

Good: "Plan 拆 4 个 pack。1→2→3→4 串行，2 依赖 1 的 schema。派 4 个 plan-writer，互不依赖的 1/3 并行。"
Bad: "制定了全面的实施计划，涵盖所有功能模块。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal。

## Step 1：读 design + issue，映射 plan 清单

读源设计文档（`prev_outputs` 里的设计文档路径），提取 goal / architecture / 合同边界 / 测试 seam——**只读，作为派发时给 plan-writer 的上下文**，不在主线程展开写作。

读每个大 issue（design 阶段在 `docs/issues/<slug>/` 立的骨架），提取 What to build、Blocked by，定 **plan 清单**（一个大 issue → 一份 plan → 一个 plan-writer）。**小 issue 不在这拆**——它的 `## Small issues` 通常是 `<!-- PENDING -->`（设计阶段故意留白），由 plan-writer 接手时自己拆，逼它认真读代码 + 规划。主 Agent 只到大 issue 粒度。

**映射规则**：源设计 → 全局上下文（喂每个 writer，只读）；大 issue → 一份 plan；小 issue → 一个 Task Pack（writer 拆 + 写）；小 issue 验收 → Pack 验收；小 issue blocked-by → Pack dependencies。
映射不成立：术语 / 验收不清 → handoff `needs-repair` 回 design；架构假设与代码现实不符 → 用 `codebase-design` skill 厘清后再派。

**轻量核现状**：用 `rg`/`find` 确认设计涉及的 plan 落点目录、关键路径真实存在——够判断派几个 writer、各管哪个 issue 即可。**深度代码理解由 plan-writer 各自用 `codebase-design` 做**，主 Agent 不抢着探全。

## Step 2：写跨 plan 合同骨架进设计文档（多 plan 时；单 plan 跳过）

派 writer **之前**，从设计文档 `## 合同边界` + architecture + 大 issue 依赖图，判断有没有跨 plan 连接面（共享文件 / 模块 / schema、一份 plan 产出另一份消费的接口）。有就把**骨架**写进设计文档的 `## Cross-Plan Contract Anchors` 占位：

- **文件所有权划分**：哪份 plan 可碰哪些共享文件——一文件一 owner，防两个 writer 并行改同一文件。
- **跨 plan 接口**：owner / provider / consumer 按 plan 编号写（"001 provide 鉴权 token 接口,002 consume"），命名到位、**精确字段 / 签名先标 `(字段待 plan 回填)`**——这是骨架,细节 Step 5 回填,不是 TBD。

无跨 plan 连接面 → 写明"无跨计划共享合同"，跳 Step 3。骨架是给 writer 的硬边界：dispatch 时随设计文档进 writer 上下文，writer 不许认领别的 plan owner 的文件。

## Step 3：Fan-out 派 plan-writer

每个大 issue 派一个 `plan-writer`（`subagent_type: "plan-writer"`）。**互不依赖的 plan 用 `run_in_background: true` 并行；有 blocked_by 链的按依赖序派。** 每个 dispatch 给（且只给）该 writer 它那份 plan 需要的：

- **落点**：`docs/plans/<YYYY-MM-DD>-<slug>/00N-<issue-slug>.md`（slug 与源设计 / issue 对齐；多 plan 同一目录）
- **源设计文档路径**（含 Step 2 的合同骨架：architecture / `## 合同边界` / `## Cross-Plan Contract Anchors`——writer 据此知道能碰哪些文件、provide/consume 哪些接口）
- **该 writer 负责的 issue 文件路径**（`## Small issues` 多为 `<!-- PENDING -->`，writer 自己拆 + 写回）
- **方法论 reference 路径**：`${SKILL_DIR}/references/task-pack.md` + `${SKILL_DIR}/references/plan-rigor.md`
- **mockup 目录**（若 `docs/mockups/<slug>/` 存在）

**不要**把别的 writer 的历史 / 别的 plan 内容粘进去——每个 dispatch 独立、零交叉污染。单 issue → 单 plan：派一个就行，不强行并行。

## Step 4：亲验返回

每份 `plan-writer` 返回 `pass` 后，对它声明的事实（plan 文件存在、Pack 数量、引用的 `file:line`、**小 issue 已写回 issue 文件 `## Small issues`**）至少抽验 1 个（`grep`/`Read`）再采信。失实 → 重派该 writer 或主 Agent 亲查修正。任一返回 `needs context` / `needs repair` / `blocked` → 按其内容补上下文或修源设计后重派；返回 `needs redirection`（探代码撞破设计方向）→ handoff `needs-redirection` 交用户拍方向。全部 `pass` + 验过 → Step 5。

## Step 5：回填合同细节 + 核边界（多 plan 时）

Step 2 的骨架已划好边界，本步把**精确字段 / 签名**填实并核 writer 有没有越界。扫每份 plan 的 File/Responsibility Map + Contract anchors + migration/registry（plan-writer 返回的 `Cross-plan touchpoints` 区块是入口），把 Step 2 标 `(字段待 plan 回填)` 的格子补成真实 owner / provider / consumer / 字段，写回设计文档 `## Cross-Plan Contract Anchors`（单一源）。核边界：writer 有没有认领别人 owner 的文件、provider 接口与 consumer 期望对不对得上。provider/consumer 缺失、ownership 冲突、接口签名不匹配 → `SendMessage` 对应 writer 修。

## Step 6：就绪门 + 跨 plan 覆盖自检（→ 读 `references/plan-self-check.md` 全文）

plan-writer 已各自过 Pre-delivery Self-Check（保自己那份）。主 Agent **打开 `references/plan-self-check.md`**，从**跨 plan 视角**再过一遍覆盖与 ownership——跨 plan 一致性归你，判据按那份文件。

## Git 纪律

写 plan 阶段不 commit、不 push，改动保持 unstaged，落地通过后统一提交。**plan-writer 不 commit；主 Agent 统一提交**（设计文档回填和 plan 文档分别提交）。

## 收尾：钉产出 → handoff（交还 flow,不自己选执行方式)

就绪门过后,**钉 plan 目录进接力单 + 一条 handoff**（执行方式由 build 阶段定,本 skill 不交接 tdd/tdd-executor;②计划审由 flow 触发，不自派):

- 计划就绪 → `mmw handoff --conclusion pass --produced docs/plans/<slug>/` → flow 触发 ②计划审（Codex 独立审），审过再进 build。
- 设计 / 验收不清没法拆 → `--conclusion needs-repair`（回 design）或 `needs-context`（问用户）。
- 探代码撞破设计方向 → `--conclusion needs-redirection`。
- ②计划审打回 → flow 回 plan（`needs-repair`），停在本 skill 改、改完 handoff 重审。**Critical 必须修掉才能进 build。**

## 边界

没有就绪的 plan 不进 build。plan-writer 返回的事实未经主 Agent 亲验不采信——它是劳动力不是 ground truth。

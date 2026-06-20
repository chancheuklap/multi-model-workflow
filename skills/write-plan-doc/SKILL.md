---
name: write-plan-doc
description: "把已评审的设计文档 + issue 拆成一份执行者零上下文也能照做的实施计划文档（Task Pack + TDD 步骤 + 验收命令）。用户说『写实施计划』『把设计拆成计划』『写 plan』『按这个设计落地』时使用。"
---

# write-plan-doc

已评审的设计文档（含框架合同）+ issue → 逐 issue 并行派 `plan-writer` agent 各写一份 plan → 主 Agent 亲验 + 跨 plan 锚点回填 + 就绪门。

**手动驱动**：你（主 Agent）读 design + issue 映射出 plan 清单，逐 issue 派 `plan-writer` sub-agent（互不依赖的并行）各写各的 plan；你只编排、验收、回填、路由，不亲自写 Task Pack。无自动派发或 gate 脚本。需要第二意见时主动把 plan 交给 `second-model-review` / `/code-review`。落地用 `tdd` skill 或 `tdd-executor` agent。

## 两个角色（写作下放，编排上收）

| 角色 | 谁 | 职责 |
|---|---|---|
| **主 Agent（你）** | 本 skill 驱动者 | 读 design + issue → 映射 plan 清单 → fan-out plan-writer → 亲验返回 → 跨 plan 锚点回填设计文档 → 就绪门 → 路由 |
| **plan-writer** | 派出的 sub-agent（`agents/plan-writer.md`） | 拿到设计文档 + 单个 issue + 方法论 reference，写出一份自洽 plan（Header + Task Pack + TDD 步骤 + 验收）。写作纪律、核心原则、Self-Check 都在它身上 |

**框架合同已在设计文档里**（architecture / global constraints / 测试 seam / `## Cross-Plan Contract Anchors` 占位）——主 Agent 不另写合同，连同 issue 一起喂给 plan-writer，它从设计文档逐字抄 Global Constraints 进自己的 plan header。

## 渐进式加载（走到那步再读对应 reference，读全文，别凭记忆）

| 角色 | 走到这步 | 读这个 reference |
|---|---|---|
| plan-writer | 写 Task Pack / 规划测试 / 查反模式 | `references/task-pack.md` + `references/plan-rigor.md`（dispatch 给它路径，它现读——主 Agent 不复述写作细则） |
| 主 Agent | 就绪门 + 跨 plan 覆盖自检 | `references/plan-self-check.md` 全文 |

## 角色与声音（主 Agent）

你是计划编排器。把 plan 清单分发给 plan-writer，确保每份返回的 plan 真实、自洽、可验证；跨 plan 合同面一致。

- 每份 plan 的 scope 用 issue + 文件名界定，不用模糊描述；plan 间依赖用 blocked_by 显式标注；不确定的拆分点标 `[needs-evaluation]`。

Good: "Plan 拆为 4 个 pack。1→2→3→4 串行，2 依赖 1 的 schema。派 4 个 plan-writer，互不依赖的 1/3 并行。"
Bad: "制定了全面的实施计划，涵盖所有功能模块。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal。

## 前置

设计文档已评审通过 + issue 已就绪。缺设计 → 先回 `write-design-doc`。一个大 issue 对应一份 plan。

## Step 1：读 design + issue，映射 plan 清单（主 Agent）

读源设计文档，提取 goal / architecture / 合同边界 / 测试 seam——**只读，作为派发时给 plan-writer 的上下文**，不在主线程展开写作。

读 issue，提取 What to build、Blocked by。检查每个大 issue 的 `## Small issues`：已有完整列表 → 映射；为空 / `<!-- PENDING -->` → 用 `to-issues` skill 拆（vertical-slice / tracer-bullet、HITL·AFK、依赖、粒度与用户确认都在它那），拆完写回再回来。**拆分方法论不在本 skill 复述——`to-issues` 是单一权威。**

**映射规则：** 源设计 → 全局上下文（喂给每个 writer，只读）；大 issue → 一份 plan（一个 plan-writer 负责）；小 issue → 一个 Task Pack（writer 写）；小 issue 验收 → Pack 验收；小 issue blocked-by → Pack dependencies。
映射不成立：术语 / 验收不清 → 回 `write-design-doc`；架构假设与代码现实不符 → 用 `codebase-design` skill 厘清后再派。

**轻量核现状**：用 `rg`/`find` 确认设计涉及的 plan 落点目录、关键路径真实存在——够你判断派几个 writer、各管哪个 issue 即可。**深度代码理解由 plan-writer 各自用 `codebase-design` 做**，主 Agent 不抢着探全。

## Step 2：Fan-out 派 plan-writer

每个大 issue 派一个 `plan-writer` agent（`subagent_type: "plan-writer"`）。**互不依赖的 plan 用 `run_in_background: true` 并行；有 blocked_by 链的按依赖序派。**

每个 dispatch 给（且只给）该 writer 它那份 plan 需要的：

- **落点**：`docs/plans/<YYYY-MM-DD>-<slug>/00N-<issue-slug>.md`（slug 与源设计 / issue 对齐；多 plan 时同一 plan 目录）
- **源设计文档路径**（框架合同在此：architecture / global constraints / `## Cross-Plan Contract Anchors` 占位）
- **该 writer 负责的 issue 文件路径**
- **方法论 reference 路径**：`skills/write-plan-doc/references/task-pack.md` + `skills/write-plan-doc/references/plan-rigor.md`
- **mockup 目录**（若 `docs/mockups/<slug>/` 存在）

**不要**把别的 writer 的历史 / 别的 plan 内容粘进去——每个 dispatch 独立、零交叉污染。单 issue → 单 plan：派一个就行，不强行并行。

## Step 3：亲验返回（主 Agent）

每份 `plan-writer` 返回 `pass` 后，对它声明的事实（plan 文件存在、Pack 数量、引用的 `file:line`）至少抽验 1 个（`grep`/`Read`）再采信。失实 → 重派该 writer 或主 Agent 亲查修正。任一返回 `needs context` / `needs revision` / `blocked` → 按其内容补上下文或修源设计后重派。全部 `pass` + 验过 → Step 4。

## Step 4：跨 plan 合同锚点回填（多 plan 时，主 Agent）

全部 plan 到齐后，扫每份 plan 的 File/Responsibility Map + Contract anchors + migration/registry（plan-writer 返回的 `Cross-plan touchpoints` 区块是入口），只取跨 plan 连接面，把共享合同 / 接口 / 文件所有权汇总**回填进设计文档的 `## Cross-Plan Contract Anchors` 占位**（单一源，覆盖设计阶段留的注释占位）：记 owner / provider / consumer / 关键字段。provider 或 consumer 缺失、ownership 冲突 → 标 `needs plan repair`，`SendMessage` 对应 writer 修。无跨 plan 连接面时写明"无跨计划共享合同"。

## Step 5：就绪门 + 跨 plan 覆盖自检（→ 读 `references/plan-self-check.md` 全文）

plan-writer 已对各自 plan 过了 Pre-delivery Self-Check。主 Agent **打开 `references/plan-self-check.md`**，从跨 plan 视角再过一遍：每个大 issue 都映射到一份 plan、File-Responsibility Map 每路径被某 Pack 消费、plan 间引用一致、无 ownership 冲突。重大或触碰红线 → 交 `second-model-review` 阶段②独立审（reviewer prompt + findings 处置在那边）。

## 执行交接

plan 存好后给落地者选执行方式：

- **子代理逐 task 驱动（推荐）**：每个 Task Pack 派一个 `tdd-executor` agent，task 间过 review，全部完成做一次整分支 review；互不依赖的 pack 用 isolation worktree 并行。每个 dispatch 只给该 pack 的 brief + Interfaces + Global Constraints，**不要把前面 task 的历史粘进去**。
- **本会话内联**：用 `tdd` skill 按步骤逐个跑，带 checkpoint。

节奏（两种都遵守）：TDD 走预先定下的 seam；regularly 跑 typecheck 和单个测试文件；**末尾跑相关套件 + 针对性命令（不强制全套；大套件含已知垃圾测试的项目优先针对性测试 + 真机 E2E）**；落地完用 `/code-review` / `second-model-review` 收口；commit 到当前分支、不 push。

## Git 纪律

写 plan 阶段不 commit、不 push，改动保持 unstaged，落地通过后统一提交。**plan-writer 不 commit；主 Agent 统一提交**（设计文档回填和 plan 文档分别提交）。落地执行用 `tdd` skill 或 `tdd-executor` agent。

## 下一步路由（本 skill 完成后，向用户报下一站）

计划写好、亲验 + 回填 + 就绪门过后，按产出状态给一句建议：

- 重大 / 碰红线 → 交 `second-model-review` 阶段②独立审
- 计划通过、落地 → 见上「执行交接」：`tdd` skill（内联单块）或 `tdd-executor` agent（隔离 worktree 并行，逐 Pack）
- 落地遇未知根因 bug → `root-cause-analyst` agent
- 一个 plan 全 Pack 提交 → `second-model-review` 阶段③（落地审）；全部 plan 合并 → 阶段④ final

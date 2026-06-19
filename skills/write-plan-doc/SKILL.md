---
name: write-plan-doc
description: "把已评审的设计文档 + issue 拆成一份执行者零上下文也能照做的实施计划文档（Task Pack + TDD 步骤 + 验收命令）。用户说『写实施计划』『把设计拆成计划』『写 plan』『按这个设计落地』时使用。"
---

# write-plan-doc

已评审的设计文档 + issue → 一份完整的实施计划文档。

**手动驱动**：你（或你派的执行者）按设计和 issue 写出 plan，让落地者照做。没有 budget / DISPATCH_ENVELOPE / 自动 Codex 派发 / gate 脚本。需要第二意见时主动把 plan 交给 Codex / `/code-review`。落地用 `tdd` skill 或 `tdd-executor` agent。

## 渐进式加载（走到那步再读对应 reference，读全文，别凭记忆）

本骨架常驻；阶段性大块细则放 reference，**到那一步现读最新上下文**，避免一次读完后期被稀释。

| 走到这步 | 读这个 reference |
|---|---|
| 写 Task Pack + Implementation 步骤（每个 pack） | `references/task-pack.md` 全文 |
| 规划测试 / Issue 质量 / 查反模式 | `references/plan-rigor.md`（覆盖追踪 / E2E·EVAL·unit 矩阵 / ★ 评级 / 回归铁律 / Issue 质量标准 / 反模式） |
| 写完自检 + Pack 就绪门 | `references/plan-self-check.md` 全文 |

## 角色与声音

你是计划编排器，把已评审的设计翻译为 Task Pack 序列。

- 每个 pack 的 scope 用文件名界定，不用模糊描述；依赖用 blocked_by 显式标注，不靠阅读顺序暗示；不确定的拆分点标 `[needs-evaluation]`，不假装确定。

Good: "Plan 拆为 4 个 pack。1→2→3→4 串行，2 依赖 1 的 schema。"
Bad: "制定了全面的实施计划，涵盖所有功能模块。"

禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal。

## 核心原则

写 plan 时假设落地者**对当前代码库零上下文、对问题领域一无所知、品味存疑、测试设计能力一般**。文档里必须包含他需要知道的一切：每个任务看哪些文件、改什么、怎么测、相关文档在哪。bite-sized task、DRY、YAGNI、TDD、频繁提交。

**每个 task 必须能单独抽出来当一份自洽 brief**（落地者通常只看自己那个 task，不读全 plan、可能乱序读）：不写 "similar to Task N"（重复写出来）、不引用未在本 task 或前文定义的 type/function/field、要传给下个 pack 的信息写进本 task 的 Interfaces，不靠"看上一个 pack"。

**前置**：设计文档已评审通过 + issue 已就绪。缺设计 → 先回 `write-design-doc`。一个大 issue 对应一份 plan。

## Step 1：读 source design + mockup + issue

提取 goal、architecture、tech stack、合同边界、**设计期定下的测试 seam**（plan 的 verification 锚到它）；只聚焦与本 issue 相关的部分。

**Mockup 与文字设计平等**：若 `docs/orchestrate/mockups/<slug>/` 存在，读索引 + 设计文档 `## UI / UX 状态` 视觉规格表，提取每页视觉规格 / 交互 / 状态变体写进对应 pack 的 acceptance criteria——**作为具体可验证的视觉目标，不是"去看 mockup 目录"的指针**。

读 issue，提取 What to build、Blocked by。检查 `## Small issues`：已有完整列表 → Step 2；为空 / `<!-- PENDING -->` → 用 `to-issues` skill 拆(vertical-slice / tracer-bullet 方法论、HITL·AFK、依赖、粒度与用户确认都在它那)，拆完写回 `## Small issues` 再回来做映射。**拆分方法论不在本 skill 复述——`to-issues` 是单一权威,它更新本 skill 不漂移。**

**映射规则：** source design → plan 全局上下文（只读）；issue 文件 → plan scope；小 issue → 一个 Task Pack；小 issue 验收 → Pack 验收；小 issue blocked-by → Pack dependencies。
映射不成立：术语 / 验收不清 → 回 `write-design-doc`；架构假设与代码现实不符 → 用 `codebase-design` skill 的深模块视角厘清后再写。

**探索代码库 + 核实现状**：用 `rg` / `find` 验证 source design 涉及的路径、模块、合同面、已有模式；现状描述引具体 `file:line` + 真实行为，可能漂移的标核实日期。读项目根 CLAUDE.md 及链入规则（模块边界、测试路由、合同墙、命名）。**测试框架探测**：先读 CLAUDE.md `## Testing` 拿权威测试命令 / 框架，没有再按 `pyproject.toml`/`package.json`/`go.mod` 探测。**写进 plan 的每条路径 / 类型 / 函数 / fixture，要么前文定义，要么 `rg`/`find` 验真，不凭印象。**

## Step 2：确定文件结构

定义 task 前先规划哪些文件被创建 / 修改、各负责什么——分解决策锁在这里。每文件一个明确职责；小而聚焦优于大杂烩；一起变更的文件住一起（按职责拆不按技术层拆）；遵循既有模式（既有代码库用大文件别擅自重构，但你正改且已臃肿的文件可在 plan 里含一次拆分）。

## Step 3：写 Plan Header

```markdown
# <Issue Title> Implementation Plan

**Goal:** <一句话目标>
**Source design:** docs/orchestrate/design/<slug>.md
**Source issue:** docs/orchestrate/issues/<slug>/00N-<issue-slug>.md
**Blocked by:** <其他 plan 编号或 "None">
**Architecture:** <与本 issue 相关的实现方向>
**Tech stack:** <实际涉及的框架、服务、测试工具>

## Global Constraints
项目级硬约束，每条一行，**值从设计 / 项目规则逐字抄来**（版本下限、依赖限制、命名与文案规则、平台要求、项目不变量、计费/权限红线等——agentflow 例:北极星不变量）。**每个 Task Pack 的要求都隐含包含本节**——执行者和审查者都以它为准绳。

## File / Responsibility Map
**Create / Modify / Test / Docs·rules·registry·migration:** `path` — responsibility / behavior / why it changes

## Dependency Graph（多 pack 时画 ASCII + 排序理由"为什么这个顺序、打乱会怎样"）
Pack 1 基础 ─┬─> Pack 2 ...
             └─> Pack 3 ...

## 发布风险和人工门禁
| 风险面 | Task Pack | Risk flag | 提前 review | Manual gate owner |
```

## Step 4-5：写 Task Pack + Implementation 步骤（→ 读 `references/task-pack.md` 全文）

每个 small issue 对应一个 Task Pack。**写每个 pack 前打开 `references/task-pack.md`**，按它的 Task 大小判据 + Task Pack 模板 + TDD Implementation 步骤 + 验证规划 + 无 Placeholder 规则 + 不合格信号写。pack 骨架（知道有哪些字段，细则在 reference）：Goal behavior / Why this matters / Owned files / Verified current state / Read first / **Interfaces(Consumes·Produces)** / Contract anchors / Schema-API shapes / Mockup specs / Do Not Touch / Root cause / Acceptance criteria / Verification commands / Testing pyramid / Rollback / **Complexity(cheap·standard·capable)** / Commit boundary / Risk flags / Dependencies / Out of scope。Implementation 步骤走 RED→GREEN→Refactor 垂直切片。测试规划细则查 `references/plan-rigor.md`。

## Step 6：自检 + Pack 就绪门（→ 读 `references/plan-self-check.md` 全文）

plan 写完后**打开 `references/plan-self-check.md`**：按 spec 覆盖 / 类型一致 / 过度·不足·覆盖自检逐条过；逐 pack 走 Pack 就绪门；重大或触碰红线时交 `second-model-review` skill 阶段②(计划文档 review)独立审——审查角度和 findings 处置在那边。

## 多 plan：跨计划合同锚点

涉及多份 plan 时，全部写完后把跨 plan 共享的合同 / 接口 / 文件所有权汇总进设计文档的 `## Cross-Plan Contract Anchors`（单一源）：扫每份 plan 的 File/Responsibility Map + Contract anchors + migration/registry，只取跨 plan 连接面，记 owner / provider / consumer / 关键字段；provider 或 consumer 缺失、ownership 冲突 → 标 `needs plan repair` 先修。无跨 plan 连接面时写明"无跨计划共享合同"。

## 执行交接

plan 存好后给落地者选执行方式：
- **子代理逐 task 驱动（推荐）**：每个 Task Pack 派一个 `tdd-executor` agent，task 间过 review，全部完成做一次整分支 review；互不依赖的 pack 用 isolation worktree 并行。每个 dispatch 只给该 pack 的 brief + Interfaces + Global Constraints，**不要把前面 task 的历史粘进去**。
- **本会话内联**：用 `tdd` skill 按步骤逐个跑，带 checkpoint。

节奏（两种都遵守）：TDD 走预先定下的 seam；regularly 跑 typecheck 和单个测试文件；**末尾跑相关套件 + 针对性命令（不强制全套;大套件含已知垃圾测试的项目优先针对性测试 + 真机 E2E——agentflow 即如此）**；落地完用 `/code-review` / `second-model-review` 收口；commit 到当前分支、不 push。

## Git 纪律 + 收尾自检

写 plan 阶段不 commit、不 push，改动保持 unstaged，落地通过后统一提交。落地执行用 `tdd` skill 或 `tdd-executor` agent。

**收尾自检**：写 Task Pack、做自检/就绪门这几步，是否每步都现读了对应 reference 全文、没凭骨架记忆默写？漏了就回去补读再过一遍。

## 下一步路由（本 skill 完成后，向用户报下一站）

计划写好、自检 + Pack 就绪门过后，按产出状态给一句建议：

- 重大 / 碰红线 → 交 `second-model-review` 阶段②独立审
- 计划通过、落地 → 见上「执行交接」：`tdd` skill（内联单块）或 `tdd-executor` agent（隔离 worktree 并行，逐 Pack）
- 落地遇未知根因 bug → `root-cause-analyst` agent
- 一个 plan 全 Pack 提交 → `second-model-review` 阶段③（落地审）；全部 plan 合并 → 阶段④ final

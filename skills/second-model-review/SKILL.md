---
name: second-model-review
description: "派第二个模型(多为 CC 派 Codex)独立审你的产物,再亲验处置它的 findings。触发词:用 Codex 审 / second opinion / 独立审查 / review 这个设计 / 计划 / 落地 / 分支。"
---

# second-model-review

你是 coordinator。用户让你审什么,你按本文件派 Codex 去审,收回后亲验处置。**references/ 全是给 reviewer(Codex)读的,你不读、只点名让它读;你只读本文件。**

## 选阶段（决定让 Codex 读哪份 reference）

| 阶段 | 时机 | reviewer 读 |
|---|---|---|
| ① 设计文档 | 写计划前 | `references/design-review.md` |
| ② 计划文档 | 写代码前 | `references/plan-review.md` |
| ③ 计划落地 | 一份 plan 的 Pack 全提交后 | `references/plan-impl-review.md` |
| ④ final | 所有 plan 合并后 | `references/final-review.md` |

③ 审单个 plan 实现;④ 审整个合并结果(plan 之间缝隙 / 互相破坏)。ad-hoc commit / 文件就近用 ③。

## Step 1 确定审查对象
按用户说的取内容:commit→`git show <hash>`;分支→`git diff <base>...HEAD`;未提交→`git diff HEAD`;文件 / 文档→路径。

## Step 2 派 Codex（两个并行）
每阶段派**两个**独立 reviewer(①②③ = 轴 A + 轴 B;④ = 基线 1 + 基线 2),单条消息并行起、各自干净 context。给每个的指令:
> 读 `<本skill>/references/quartet.md` + `references/<阶段>.md` 的〔轴 A / 基线 1〕,按它审。Source:〔源意图路径 + 待审内容 / diff〕。

跑 `codex exec -C . --sandbox read-only - < <prompt>`(或 `/code-review`),`run_in_background: true`。Codex 侧没装本 skill 时,把 `quartet.md` + 该段拼成自包含 prompt 给它。
模式(默认 Review):Review 过闸 / Challenge 假设它错找证据 / Consult 开放咨询。高风险加 specialist(按 diff 选):security / performance / data-migration / api-contract / red-team / testing。

## Step 3 处置 findings（两个结果分开处置，不合并不重排）
findings 和派发隔了很多轮,别凭记忆。整体 `needs context`(非某条 `needs evidence`)= reviewer 没完成,补上下文重派。逐条:

1. **亲验**:Read / grep / 对照源产物核事实主张。
2. **接收纪律**:禁表演式回应(用动作代替言语);验五问(技术对吗 / 破坏既有吗 / 当前实现有 legacy 理由吗 / 跨平台版本成立吗 / reviewer 懂全局吗);YAGNI-grep("实现更完整"先 grep 用法,没人调用就删);不清楚的先全澄清再动手。
3. **按置信度**:8-10 亲验后多 accept / reject;5-7 补证(自查或派只读 explorer)再定;1-4 压制记一行。
4. **处置选项**:`accepted`(翻成具体修复指令,只有它往下走)/ `rejected`(记反证,不让同条反复回审)/ `needs evidence`(补证前不修)/ `duplicate`(链已有)/ `out of scope`·`needs evaluation`(立即开 issue,先查重)/ `user decision`(停,一次一个业务问题)。
5. 冲突按证据质量,不按 reviewer 投票。源产物明写要的、评审判为缺陷的 → human decides。

## Step 4 accepted finding 修在哪（Gap 路由）

| Gap | 含义 | 去哪 |
|---|---|---|
| Implementation | 设计对、代码没做到 | 当前层改(小)/ 派 `tdd-executor`(大) |
| Design | 设计承诺不可实现 / 漏约束 | 回 `write-design-doc` → 再审 |
| Context | 需确认术语 / owner / target | `grill-with-docs` / 回讨论 → 写回 |
| Plan | plan 与代码不一致 / 遗漏 | 回 `write-plan-doc` → 再审 |
| Architecture friction | 反复撞同一结构 | `improve-codebase-architecture` → 写回 |
| Unverifiable | 环境 / 账号 / 生产 gate 缺 | 写清证据 + manual gate owner,不算 blocker |

修复顺序:阻塞 / 安全 → 简单(typo / import)→ 复杂(重构 / 逻辑),每条单独测、验无回归。回归证据按类型:behavior bug→behavior test;合同 / schema / migration→对应 check;UI→browser smoke;billing / runtime / 权限→integration 或带 owner 步骤的 manual gate。别用代码 patch 盖设计 / 计划的洞。

## 收尾自检
- 派了两个并行 reviewer、各指向对应阶段段、给了 Source?
- findings 分开亲验、只动 accepted、按 Gap 路由?
- 向用户汇报 verdict + 每条一句话摘要 + 修复方向,不自动越权修。

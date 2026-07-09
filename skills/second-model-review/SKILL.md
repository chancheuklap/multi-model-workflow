---
name: second-model-review
description: "派第二个模型(多为 CC 派 Codex)独立审你的产物,再亲验处置它的 findings;用户也可叫你亲自充当 reviewer(自审第二路径)。触发词:用 Codex 审 / 你来审 / second opinion / 独立审查 / review 这个设计 / 计划 / 落地 / 分支。"
---

# second-model-review

你是 coordinator。用户让你审什么,你按本文件让**第二个模型**审,收回后亲验处置。

**"第二个模型" = 与作者不同上下文的 reviewer**——独立性来自 reviewer 与作者**不同上下文**,不来自具体哪个模型。两条路:

- **默认 · 派发(Step 2a)**:你派另一模型审(Claude 驱动多派 Codex / 全新实例),独立 context。`references/` 你不读、只点名让 reviewer 读;你只读本文件。
- **第二路径 · 自审(Step 2b)**:用户明确叫你充当 reviewer 时,你不派、亲自审——这时你**就是** reviewer,自己读 `references/`。独立性更弱(可能与作者同上下文),用同样纪律补偿,见 2b。

Step 1 / Step 3 / Step 4 两路通用(确定对象 / 处置 findings / Gap 路由 与"谁审"无关)。

## 选阶段（决定 reviewer 读哪份 reference）

| 阶段 | 时机 | reviewer 读 |
|---|---|---|
| ① 设计文档 | 写计划前 | `references/design-review.md` |
| ② 计划文档 | 写代码前 | `references/plan-review.md` |
| ③ 计划落地 | 一份 plan 的 Pack 全提交后 | `references/plan-impl-review.md` |
| ④ final | 所有 plan 合并后 | `references/final-review.md` |

③ 审单个 plan 实现;④ 审整个合并结果(plan 之间缝隙 / 互相破坏)。ad-hoc commit / 文件就近用 ③。

## Step 1 确定审查对象
按用户说的取内容:commit→`git show <hash>`;分支→`git diff <base>...HEAD`;未提交→`git diff HEAD`;文件 / 文档→路径。

## Step 2a 派发审查（默认）
每阶段派**两个**独立 reviewer(①②③ = 轴 A + 轴 B;④ = 基线 1 + 基线 2),单条消息并行起、各自干净 context。给每个的指令:
> 读 `<本skill>/references/quartet.md` + `references/<阶段>.md` 的〔轴 A / 基线 1〕,按它审。Source:〔源意图路径 + 待审内容 / diff〕。

**只给 Source + 点名 references,别塞你自己的问题清单 / 引导。** Codex 在仓库里、能读到一切,设计就是让它自由发挥。塞窄问题 = 拿你的视角把它框死,它就跳不出来质疑地基(栽过:手搓文档解析器、每轮只让它"验这个实现对不对",审 10 轮没一次说"该用现成库")。地基质疑已焊进 quartet 的「先挑地基,再过闸」(默认必跑),无须你再提示。

跑 `codex exec -C . --sandbox read-only - < <prompt>`(或 `/code-review`),`run_in_background: true`。Codex 侧没装本 skill 时,把 `quartet.md` + 该段拼成自包含 prompt 给它。
模式:**质疑地基 = 默认**(quartet 已焊,每轮必先挑地基[重造轮子 / 样本非证据 / 抽象选错]再过闸);Review 过闸 / Consult 开放咨询是侧重变体,Challenge(假设它错、专找反证)按需加压。高风险加 specialist(按 diff 选):security / performance / data-migration / api-contract / red-team / testing。

## Step 2b 自审（第二路径——用户叫你充当 reviewer 时）
不派,你亲自审,但**reviewer 纪律一分不减**:像派给 Codex 一样,自己先 Read `references/quartet.md` + `references/<阶段>.md` 对应轴,按它审——先挑方向、再挑地基、最后过闸,防幻觉四件套(置信度 / 引 `file:line` 原文 / 不自我合理化 / 证据表),产出 quartet 的 Return Contract。

独立性补偿(你可能与作者同上下文,这是这条路唯一短板):
- **审你自己刚写的最危险**——主动找反证、假设自己错(Challenge 模式),别复述当时的理由。高风险产物(计费 / 合同 / 数据权威 / 迁移)优先回 2a 派发;自审只作快速低风险、或你没参与撰写时用。
- 两轴 / 两基线仍**分两遍**跑(同一次自审里切两个视角,别一遍混过)。
- reviewer 和 coordinator 都是你,**Step 3 的亲验照样逐条做**——自己审出的 finding 也要 Read/grep 坐实,不因"自己审的"就免验。

## Step 3 处置 findings（两个结果分开处置，不合并不重排）
findings 和派发隔了很多轮,别凭记忆。整体 `needs context`(非某条 `needs evidence`)= reviewer 没完成,补上下文重派。整体 `needs redirection` = reviewer 判源意图/方向本身存疑:**别当普通 finding 修产物**,停下来把方向怀疑原样转给用户决策(一次一个业务问题),用户拍「换方向」就回 `write-design-doc` 重做、拍「方向不变」才继续处置其余 findings。逐条:

1. **亲验**:Read / grep / 对照源产物核事实主张。
2. **接收纪律**:禁表演式回应(用动作代替言语);验五问(技术对吗 / 破坏既有吗 / 当前实现有 legacy 理由吗 / 跨平台版本成立吗 / reviewer 懂全局吗);YAGNI-grep("实现更完整"先 grep 用法,没人调用就删);不清楚的先全澄清再动手。
3. **按置信度**:8-10 亲验后多 accept / reject;5-7 补证(自查或派只读 explorer)再定;1-4 压制记一行。
4. **处置选项**:`accepted`(翻成具体修复指令,只有它往下走)/ `rejected`(记反证,不让同条反复回审)/ `needs evidence`(补证前不修)/ `duplicate`(链已有)/ `out of scope`·`needs evaluation`(立即开 issue,先查重)/ `user decision`(停,一次一个业务问题)。
5. 冲突按证据质量,不按 reviewer 投票。源产物明写要的、评审判为缺陷的 → human decides。

## Step 4 accepted finding 修在哪（Gap 路由）

| Gap | 含义 | 去哪 |
|---|---|---|
| Implementation | 设计对、代码没做到 | 当前层改(小)/ 派 `tdd-executor`(大) |
| Direction | 源意图/方向本身错(解错问题 / 该换框架 / 不该做) | 停 → 用户拍方向 → 回 `write-design-doc` 重框 → 再审 |
| Design | 设计承诺不可实现 / 漏约束 | 回 `write-design-doc` → 再审 |
| Context | 需确认术语 / owner / target | `domain-modeling` / 回讨论 → 写回 |
| Plan | plan 与代码不一致 / 遗漏 | 回 `write-plan-doc` → 再审 |
| Architecture friction | 反复撞同一结构 | `improve-codebase-architecture` → 写回 |
| Unverifiable | 环境 / 账号 / 生产 gate 缺 | 写清证据 + manual gate owner,不算 blocker |

修复顺序:阻塞 / 安全 → 简单(typo / import)→ 复杂(重构 / 逻辑),每条单独测、验无回归。回归证据按类型:behavior bug→behavior test;合同 / schema / migration→对应 check;UI→browser smoke;billing / runtime / 权限→integration 或带 owner 步骤的 manual gate。别用代码 patch 盖设计 / 计划的洞。

## 收尾自检
- 两个 reviewer 视角都过了(派发 = 两个并行 / 自审 = 两轴分两遍)、各对应阶段段、Source 给/读齐?
- findings 分开亲验、只动 accepted、按 Gap 路由?
- 向用户汇报 verdict + 每条一句话摘要 + 修复方向,不自动越权修。
- 需留档时,审查报告 / findings 落 `docs/working/<YYYY-MM-DD>-<slug>-review.md`(scratch 审计与评审产物的统一落点)。

## 下一步路由（汇报 verdict 后，向用户报下一站）

上面 Gap 路由表是「单条 accepted finding 修到哪」;这里是「整轮审完整体走哪」,按阶段 + verdict:

- 任意阶段 `needs redirection` → 停,把方向怀疑交用户拍;换方向 → 回 `write-design-doc` 重框再走全流程
- 阶段① pass → `to-tickets` 拆 issue / `write-plan-doc`;needs repair(design gap)→ 回 `write-design-doc`
- 阶段② pass → 落地(`tdd` / `tdd-executor`);needs repair → 回 `write-plan-doc`
- 阶段③ pass → 下个 plan 落地 或 阶段④;有 accepted 落地 finding → 派 `tdd-executor` 定向修后重审
- 阶段④ pass → `verify` / `code-review` 收口 → done

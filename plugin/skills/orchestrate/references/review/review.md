# Review · 审核(阶段操作指南)

> 审核操作指南。**主线程直接派审者**;审查方法 + 各 stage 角度单源在已装的 **`worktree-review` skill**。plugin 侧只留 `plan-impl.md`(③合同门)与本文(编排)。
>
> 谁审 / 几路视角 / 模型档,全由 `mmw review start` 机器生成进 brief——**照 brief 派即可**,本文不复制派发矩阵(免漂移)。
>
> **审不记账**:没有覆盖清单登记、没有轮账。收口看产物——findings 原样落盘留痕文件,亲验标处置,文末写总 verdict;审闸 pass 时引擎只核「留痕文件在且含 verdict」(报告在 = 审真跑过,这是写者≠审者的证据面);质量与 Critical 处置是你的判断,机器不数你的动作。

红线:**写者≠验者**(设计/计划作者与审者模型不同家)。

---

## 0. 触发方式

| 审 | 触发 | stage | 视角 |
|---|---|---|---|
| 设计预审 | design 自检过后**agent 自起**(不是闸;结果给用户参考,人闸是 `/approve-design`) | `design` | 轴A 设计内容 / 轴B 项目对齐 |
| ② 计划审 | plan pass → 引擎审闸(phase 冻住,`mmw where` 吐 `review_start` 照跑) | `plan` | 轴A 覆盖与质量 / 轴B 合规与交叉验证 |
| ④ final | build pass → 引擎审闸(同上) | `final` | 基线1 回归+意图+跨plan / 基线2 独立代码审计;**审者数 review.sh 机器判**:small-change/bug=1 · develop=2 或 4(按 Complexity / diff) |

另有 **③ 落地合同门**:build 内部机器合同检查(`--stage plan-impl`,不派审者)——anchors 节为空脚本直接放行;有实体合同由 build 流程驱动(build-b B5)人工核,方法论在 `plan-impl.md`。

## 1. 一条命令起审 → 直接派审者

1. ```bash
   mmw review start --stage <design|plan|final> --source "<源意图路径/待审内容>"
   ```
   审闸内直接用 `mmw where` 吐的 `review_start` 整行(stage 与 `--source` 都填好)。它出**派发指南**(`状态平面/review-brief.md`),你照打印的往下走。
2. **直接派审者**:读 brief 按「派审者」段派(Claude 会话内 sub-agent / Codex 后台 CLI),审者各自干净 context 并行起、读 `worktree-review` skill 出结构化 findings。**别给审者 plugin 内路径、别塞你自己的问题清单。**
3. **留痕(收口的硬核)**:全部审者的结构化 findings **原样落盘**到 `docs/reviews/<slug>-<stage>.md`(不重写、不摘要);亲验后每条的 verdict/处置(accepted / rejected / duplicate / needs-evidence)就近标在该条下,文末写一句总 verdict。收口只回读 verdict 段,findings 全文压在留痕里、不长驻主线程 context。留痕是过程产物(docs/.gitignore 已忽略,随 worktree 删)。

## 2. 收口(findings 亲验标完处置后)

- 每条 finding 自己 Read/grep/跑坐实(审者是劳动力不是信源),引不出 `file:line` 降置信;承重 finding 亲验后才 accept。
- **无开口 Critical**(修掉或有理有据 reject,留痕里写明)→ `mmw handoff --conclusion pass` 进下一阶段(引擎核留痕在且含 verdict)。
- 有 accepted 缺陷 → 按 Gap 选结论词:
  - 缺陷在**当前被审阶段**(②审=plan、④final=build)→ `needs-repair`,改完 handoff 重审。**④final 的代码缺陷**:`mmw where` 指回 build(build-b 有返修入口),照 accepted findings 的 `file:line`+remediation 派全新写码工人定点修,修完 handoff pass 重进 ④全新审者重审。
  - 根因在**更上游**(②审发现 design 问题、④final 撞破 plan/design)→ `needs-redirection --to-phase <design|plan|build>`(涉已确认设计的改动,改完请用户 `/approve-design` 重新确认)。
  - Direction(解错问题)→ `needs-redirection`;Context(缺输入)→ `needs-context`。
- 收敛判据:全部审者跑完追一轮无新高置信 finding = 收敛;反复打转不收敛 → 向用户汇报卡点,别硬磨。
- ④final pass 前**先写终审报告**到 `docs/<slug>-final-review.md`(照 `mmw where` 的 `then` 钉 `--produced`),三段:终审结论(verdict + 两基线结果 + waived 项带 owner)· 意图清单逐条(达成/未达成 + 证据)· **业务语言交付摘要**(新增能力/验证证据/残余风险,不用技术术语)。

## 3. 守住的红线

- 写者≠验者:设计预审与④用 Codex+Claude 跨模型、②计划审用 Claude(计划是 Codex 写的)。不用 `codex review`(内置提示词绕过方法论)。prompt 一律指向已装 `worktree-review` skill。
- 每条 finding 引 `file:line` 原文才采信;主线程亲验后才 accept。
- ③ 不判断、只核合同;重判预算砸 ④final。

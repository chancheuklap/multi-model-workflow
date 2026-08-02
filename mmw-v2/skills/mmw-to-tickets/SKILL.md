---
name: mmw-to-tickets
description: 把一份 spec 拆成一组 tracer bullet ticket，每张声明被谁阻塞，按依赖顺序发布到 issue tracker。用户说要拆 ticket、要把 spec 拆成 issue、要定先做哪一块时用它；刚写完 spec 的技能也移交这里。
---

把一份 spec、一份计划或当前这段对话拆成一组 **ticket**——每张是一条 tracer bullet 垂直切片，并声明**阻塞**它的那些 ticket。

issue tracker 和标签词汇按 `docs/agents/issue-tracker.md` 与 `docs/agents/triage-labels.md`；读不到先跑 `/mmw-setup`。

## 1. 取上下文

从这段对话里已有的材料开始。用户给了引用（spec 路径、issue 编号或链接），就取回来把正文和评论整个读完。

## 2. 探代码（可选）

还没探过代码就探一遍，弄清现状。ticket 的标题和描述用项目领域术语表里的词，遵守这块地方的 ADR。

找一找可以先做 prefactor 的地方，让后面的实现更容易。「先把改动变容易，再做这个容易的改动。」

## 3. 起草垂直切片

拆成 **tracer bullet** ticket。

<vertical-slice-rules>

- 每一片切出一条窄但**完整**的路径，穿过每一层（schema、API、界面、测试）——是垂直的，**不是**某一层的横切
- 一片做完，它自己就能演示或验证
- 每一片的大小正好是一张 ticket 的活——一个行为，工人能端到端接下来
- prefactor 排在最前面

</vertical-slice-rules>

给每张 ticket 标上**阻塞边**——必须先做完它才能开工的那些 ticket。没有阻塞边的可以立刻开工。

**大范围重构是垂直切片的例外。** **大范围重构**是一次机械改动——改一个列名、给一个共享符号换类型——它的 **blast radius** 铺满整个代码库，一次编辑就打断上千个调用点，没有哪一片垂直切片能落地还是绿的。不要把它硬塞进 tracer bullet，按 **expand–contract** 排序。先 expand：新形式加在旧形式旁边，什么都不打断。再按 blast radius 分批迁移调用点（一个包一批、一个目录一批），每一批是自己那张 ticket、被 expand 阻塞，因为旧形式还在，批与批之间 CI 一直是绿的。最后 contract：没有调用方了就删掉旧形式，这张 ticket 被每一批迁移阻塞。连分批都单独绿不了时，序列照排，但让它们共用一条集成分支，全部阻塞最后那张集成并验证的 ticket——绿只在那里承诺。

## 4. 编号，把清单亮给用户

按依赖顺序编号，从 `01` 起，阻塞方在前。每张列三样：

- **Title**：一句话的名字
- **Blocked by**：哪几张必须先做完
- **What it delivers**：这张让什么端到端行为跑起来

**亮完就往下走，不等确认。** 人闸在 `/mmw-to-spec` 第 7 步，spec 过了那道闸之后这条线是流水线态；切分粒度和阻塞边对不对，由 `/mmw-to-plan` 那道计划审兜住。用户看了要改，回第 3 步改完再亮一次。

## 5. 发布

按 `docs/agents/issue-tracker.md` 发布，一张 ticket 一张 issue，**按依赖顺序发**——阻塞方先发出去，后面那张才引得到真编号。阻塞关系用 tracker 原生的依赖边；每张挂在 spec issue 底下作子 issue。

打 `ready-for-agent`。打在 ticket 上的含义是「这张可以派工人开工」，跟打在 spec issue 上那个（人闸的凭据）不是一回事。

发布顺序沿 **frontier** 走：阻塞它的都已发布的那些。纯线性链就是从上到下。

父 issue 不要关，也不要改。

<issue-template>

## Parent

指向这批 ticket 所属的 spec issue。

## What to build

这张 ticket 让什么端到端行为跑起来，从用户角度写——不是逐层的实现清单。

## Plan

`docs/plans/<slug>/<NN>-<ticket-slug>.md`，`<NN>` 就是第 4 步给这张定的编号。文件由 `/mmw-to-plan` 写，这里先把路径占住。

## Acceptance criteria

- [ ] 判据 1
- [ ] 判据 2

## Blocked by

- 指向每一张阻塞它的 ticket，或者「None — can start immediately」。

</issue-template>

正文里不要写具体文件路径和代码片段——它们过期得快，那些东西属于 plan。例外：原型产出了一段代码，它比散文更精确地编码了某个决定（状态机、reducer、schema、类型形状），就内联进去，并简短注明它来自原型。只留有决定含量的部分——不是一个能跑的 demo，只要要紧的那几行。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| ticket 全部发布完 | **移交**：`/mmw-to-plan`，一张 ticket 写一份 plan。文件路径和代码属于那里 |
| 第 4 步用户要改切分 | **自己继续**：回第 3 步改，改完重亮一次清单 |
| spec issue 没带 `ready-for-agent` | **停**：这份 spec 还没过人闸，回 `/mmw-to-spec` 第 7 步 |

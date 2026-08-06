---
name: mmw-to-tickets
description: 把一份 spec 拆成一组 tracer bullet ticket，按依赖顺序发布。用户说要拆 ticket、要定先做哪一块时用它；刚写完 spec 的技能也移交这里。
---

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

把一份 spec、一份计划或当前这段对话拆成一组 **ticket**——每张是一条 tracer bullet 垂直切片，并声明**阻塞**它的那些 ticket。

issue tracker 是 GitHub Issues。要连着发好几个请求的动作走 `mmw issue`，读一张、评论、打标签这类一条命令做得完的直接用 `gh`。标签清单在仓库根 `.mmw.json` 的 `tracker.labels`。

**issue 承载身份，文件承载内容。** issue 正文只放这件事是什么、现在什么状态、内容在哪；真正要反复打磨的长文放任务分支上的文件里。三层是这样分的：

| 层 | 正文放什么 | 唯一事实来源 | 结局 |
| --- | --- | --- | --- |
| map（跑了 `/mmw-wayfinder` 才有） | `Destination`、`Decisions so far` 的一行索引、`Out of scope`、`Not yet specified` | 就在正文 | 关掉，不上 Wiki |
| spec | 一段摘要说清要解决什么问题、指向分支上 spec 文件的路径、ticket 清单 | 任务分支的 `docs/specs/<slug>/` | 落地后转成一页 Wiki |
| ticket | 一段摘要、指向分支上该 ticket 计划的路径、阻塞关系 | 任务分支的 `docs/plans/<slug>/` | 并进 spec 那页 Wiki 的一节 |

本技能建的是第三层。

## 1. 上下文清单

| 上下文 | 何时读取 | 读取范围 | 不读取 | 向下传递 |
| --- | --- | --- | --- | --- |
| 对话、spec、issue 或链接 | 始终 | 正文和评论全文 | 无关 issue | 每张 ticket 需要的目标、验收和阻塞关系 |
| prototype | 上游引用时 | 索引、相关选中产物、明确相关的走查或长期证据 | 整个产物目录、无关过程材料；落选变体只在 ticket 必须落实其否定约束时读取 | 只传给消费该决定的 ticket |
| research | 上游引用时 | research 索引和本批 ticket 需要的精确文件 | research 的上级目录、subagent 原始报告 | 只传给消费该事实的 ticket |

prototype 索引缺少问题、逐轮用户结论、选中产物、落选约束或长期证据时，回 `/mmw-prototype` 补齐；没有的项目写「无」。

## 2. 找 prefactor

**按 `/mmw-research` 的内部方向派一个 subagent**，题目是：这次要改的地方，有哪些可以先做 prefactor，让后面的实现更容易。「先把改动变容易，再做这个容易的改动。」

上游 spec 的现状 research 已经覆盖实现时，只做 prefactor research。没有 spec 时，把现状一起纳入。

收回来按 `/mmw-verifying-agent-output` 验证过才写进 ticket。

ticket 的标题和描述用项目领域术语表里的词，遵守这块地方的 ADR。

## 3. 起草垂直切片

拆成 **tracer bullet** ticket。

<vertical-slice-rules>

- 每一片切出一条窄但**完整**的路径，穿过每一层（schema、API、界面、测试）——是垂直的，**不是**某一层的横切
- 一片做完，它自己就能演示或验证
- 每一片的大小正好是一张 ticket 的活——一个行为，`worker` 能端到端接下来
- prefactor 排在最前面

</vertical-slice-rules>

给每张 ticket 标上**阻塞边**——必须先做完它才能开工的那些 ticket。没有阻塞边的可以立刻开工。

**大范围重构是垂直切片的例外。** **大范围重构**是一次机械改动——改一个列名、给一个共享符号换类型——它的 **blast radius** 铺满整个代码库，一次编辑就打断上千个调用点，没有哪一片垂直切片能落地还是绿的。不要把它硬塞进 tracer bullet，按 **expand–contract** 排序：

| 阶段 | ticket 形状 | 阻塞关系 |
| --- | --- | --- |
| expand | 在旧形式旁加入新形式，不打断现有调用方 | 无 |
| migrate | 按包或目录分批迁移调用点 | 每批被 expand 阻塞 |
| contract | 没有调用方后删除旧形式 | 被全部 migrate ticket 阻塞 |

连分批都单独绿不了时，序列照排，但让它们共用一条集成分支，全部阻塞最后那张集成并验证的 ticket——绿只在那里承诺。

## 4. 编号，请用户批准清单

按依赖顺序编号，从 `01` 起，阻塞方在前。每张列三样：

- **Title**：一句话的名字
- **Blocked by**：哪几张必须先做完
- **What it delivers**：这张让什么端到端行为可用

清单后面明确问三件事：

- 粒度是否合适，哪些太粗或太细。
- Blocking edge 是否只包含真正会阻塞开工的 ticket。
- 哪些 ticket 应合并或继续拆分。

用户提出修改时，回第 3 步重新切分，再展示完整清单。只有用户明确批准清单，才能进入第 5 步。这是 ticket 拆分的人工审批关卡；共同理解和 spec 定稿的确认不能替代它。

## 5. 发布

一张 ticket 一张 issue：

```bash
mmw issue create --title "<标题>" --body-file <正文文件> \
  --parent <spec issue 编号> --blocked-by <编号,编号> --label ready-for-agent
```

它一次做完建 issue、挂到 spec issue 底下、连阻塞边、打标签四件事，输出新 issue 的编号。

**按依赖顺序发，阻塞方先发**：`--blocked-by` 要的是已经存在的编号，挡它的那张还没发就填不进去。发布顺序沿 **frontier** 走——阻塞它的都已发布的那些。

**顺序不是随便的。** 下游取下一张 ticket 靠 `mmw issue frontier`，那个命令按 issue 编号升序给，所以「按依赖顺序发」直接决定了后面开工的顺序。

`ready-for-agent` 打在 ticket 上的含义是「这张可以派 `worker` 开工」，跟打在 spec issue 上那个（人工审批关卡的凭据）不是一回事。

父 issue 不要关，也不要改。

<issue-template>

## Parent

指向这批 ticket 所属的 spec issue（来源不是一张 issue 就省掉这一节）。

## What to build

这张 ticket 让什么端到端行为可用，从用户角度写——不是逐层的实现清单。

## Plan

`docs/plans/<slug>/<NN>-<ticket-slug>.md`。`<slug>` 跟这次的 spec 目录同名（`docs/specs/<slug>/`），`<NN>` 是第 4 步给这张定的编号。文件由 `/mmw-to-plan` 写，这里先把路径占住。

## Acceptance criteria

- [ ] 判据 1
- [ ] 判据 2

## prototype 资产

- prototype 资产索引：对应的 `README.md` 精确路径。
- 选中产物：这张 ticket 消费的精确路径。
- 走查或长期证据：与这张 ticket 明确相关的精确路径。
- 没有资产时写「无 prototype 资产」。

## research

- research 索引：对应的 `README.md` 精确路径。
- research 文件：这张 ticket 消费的精确路径。
- 没有时写「无 research」。

## Blocked by

- 指向每一张阻塞它的 ticket，或者「None — can start immediately」。

</issue-template>

正文里不要写实现文件路径和代码片段，那些东西属于 plan。prototype 的精确出处和当前 ticket 消费的 research 是例外。prototype 产出的一段代码若比散文更精确地编码决定，可以内联并注明选中产物路径；只保留决定含量，不粘贴完整 demo。

下表准备移交下一技能时，先读 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按顺序判断是否留在当前会话。自己继续和因 blocker 停下不触发阶段边界判断。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 用户批准清单，ticket 全部发布完 | **移交**：`/mmw-to-plan`，一张 ticket 写一份 plan |
| 第 4 步用户要改切分 | **自己继续**：回第 3 步改，改完重新展示完整清单 |
| 第 4 步仍在等待用户批准 | **停**：不调用 tracker 写入命令，等待用户确认或修改 |
| 来源是一份 spec，但那张 spec issue 没带 `ready-for-agent` | **停**：回 `/mmw-to-spec` 第 7 步 |

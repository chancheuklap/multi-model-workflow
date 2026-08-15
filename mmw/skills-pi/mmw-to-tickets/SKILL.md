---
name: mmw-to-tickets
description: 把已发布 spec 拆成有阻塞关系的 tracer bullet tickets。用户在 spec 发布后要求拆 tickets 时使用。
---

开始前，遵守目标仓库 `AGENTS.md` 的领域上下文规则。

把一份已发布的 spec 拆成一组 **ticket**——每张是一条 tracer bullet 垂直切片，并声明**阻塞**它的那些 ticket。

issue tracker 是 GitHub Issues。要连着发好几个请求的动作走 `mmw issue`，读一张、评论、打标签这类一条命令做得完的直接用 `gh`。标签清单在仓库根 `.mmw.json` 的 `tracker.labels`。

**issue 承载身份，文件承载内容。** 本技能为每张 tracer bullet ticket 创建一张 issue。issue 正文保存摘要、plan 的完整落点命令和阻塞关系。`/mmw-to-plan` 后续把实施内容写入命令输出的 plan 文件。

先确认当前在一条任务分支上：`git symbolic-ref --quiet --short HEAD` 有输出，且不在主检出里。`<spec issue 编号>` 由调用方移交。缺少任意一项就停下，说明缺少哪项输入。来源是一份 spec、但那张 spec issue 没带 `ready-for-agent` 时停下，回 `/mmw-to-spec` 第 6 步——那份 spec 还没过用户那道批准关卡。

## 1. 上下文清单

| 上下文 | 何时读取 | 读取范围 | 不读取 | 向下传递 |
| --- | --- | --- | --- | --- |
| spec、对应 issue 或链接 | 始终 | 正文和评论全文 | 无关 issue | 每张 ticket 需要的目标、验收和阻塞关系 |
| prototype | 上游引用时 | 索引、相关选中产物、明确相关的走查或长期证据 | 整个产物目录、无关过程材料；落选变体只在 ticket 必须落实其否定约束时读取 | 只传给消费该决定的 ticket |
| research | 上游引用时 | research 索引和本批 ticket 需要的精确文件 | research 的上级目录、subagent 原始报告 | 只传给消费该事实的 ticket |

先读取 spec issue 正文的 `## 输入出处`。它提供 map 名称及其 URL 或编号，以及 prototype 与 research 的来源链。再读取 spec 元数据块的 `artifact_refs`。它提供下游要解析的产物引用。

`## 输入出处` 或 spec 元数据块的 `artifact_refs` 缺失时停止，说明缺少上游声明。

### 解析产物引用

每条运行 `mmw artifact path`，再读输出路径的索引和索引列出的文件。命令失败或缺少 `name` 时停止。值为 `无` 或 `[]` 时不读取产物。

prototype 索引缺少问题、逐轮用户结论、选中产物、落选约束或长期证据时，回 `/mmw-prototype` 补齐；没有的项目写「无」。

按当前 ticket 实际需要的条目原样写进该 ticket 的 `## 产物引用`。写法见下面的 issue 模板。没有要传递的条目时写 `无`。

## 2. 检查现状与 prefactor

从已有 spec 和现状调查中找能让后续实现更容易的 prefactor。「先把改动变容易，再做这个容易的改动。」材料没有覆盖相关代码时，主 agent 直接读取实施范围内的入口、调用方和测试。只有范围跨多个模块、需要从调用链、数据流或影响面等独立角度系统取证时，才调用 `/mmw-research`。

没有值得单独落地的 prefactor 就直接进入第 3 步，不为填这一步制造 ticket。
使用 subagent 取得报告时，按报告写进 ticket。

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

每张 ticket 的验收标准按四条判据写。下游每一道检查都拿它当判断基准，写含糊了那些检查全都会形式上通过：

1. 每条写可观察的外部行为，从 spec 已确认的 seam 或用户可见界面观察，不写内部实现。
2. 精确值（数字、文案、状态名、字段名）从 spec 或 prototype 选中产物逐字照抄。禁止「合适的」「正确的」「符合预期」这类需要再解释的说法。
3. 一条验收只判定一个行为，能独立判定真假；复合的拆开。
4. 每条验收写得出验证落点：spec 已确认 seam 上的测试，或人工浏览器审批项。写不出落点说明 spec 缺一项决定——停下回 `/mmw-to-spec`，不硬写。

**大范围重构是垂直切片的例外。** **大范围重构**是一次机械改动——改一个列名、给一个共享符号换类型——它的 **blast radius** 铺满整个代码库，一次编辑就打断上千个调用点，没有哪一片垂直切片能落地还是绿的。不要把它硬塞进 tracer bullet，按 **expand–contract** 排序：

| 阶段 | ticket 形状 | 阻塞关系 |
| --- | --- | --- |
| expand | 在旧形式旁加入新形式，不打断现有调用方 | 无 |
| migrate | 按包或目录分批迁移调用点 | 每批被 expand 阻塞 |
| contract | 没有调用方后删除旧形式 | 被全部 migrate ticket 阻塞 |

连分批都单独绿不了时，序列照排，但让它们共用一条集成分支，全部阻塞最后那张集成并验证的 ticket——绿只在那里承诺。

## 4. 编号，请用户批准清单

按依赖顺序编号，从 `01` 起，阻塞方在前。每张列四样：

- **Title**：一句话的名字。它同时是这张 ticket 的 plan 文件名来源（怎么压成 slug 见下面的 ticket 正文模板）
- **Blocked by**：哪几张必须先做完
- **What it delivers**：这张让什么端到端行为可用
- **Acceptance criteria**：第 3 步按四条判据写出的验收标准。用户批准这份清单时必须看得到它

清单后面明确问四件事：

- 粒度是否合适，哪些太粗或太细。
- Blocking edge 是否只包含真正会阻塞开工的 ticket。
- 哪些 ticket 应合并或继续拆分。
- 每张的验收标准是否就是用户想要的可观察结果，精确值对不对。

用户提出修改时，回第 3 步重新切分，再展示完整清单。只有用户明确批准清单，才能进入第 5 步。这是 ticket 拆分的人工审批关卡；共同理解和 spec 定稿的确认不能替代它。

## 5. 发布

一张 ticket 一张 issue。先运行 `mmw artifact path scratch --sub outbox/ticket-<NN>.md`。把正文写入输出文件。再逐张发：

```bash
mmw issue create --title "<标题>" --body-file <上一步输出文件> \
  --parent <spec issue 编号> --blocked-by <编号,编号>
```

它一次做完建 issue、挂到 spec issue 底下和连阻塞边三件事，输出新 issue 的编号。

**按依赖顺序发，阻塞方先发**：`--blocked-by` 要的是已经存在的编号，挡它的那张还没发就填不进去。

**顺序不是随便的。** 下游取下一张 ticket 靠 `mmw issue frontier`，那个命令按 issue 编号升序给，所以「按依赖顺序发」直接决定了后面开工的顺序。

父 issue 不要关，也不要改。

<issue-template>

## Parent

指向这批 ticket 所属的 spec issue。

## What to build

这张 ticket 让什么端到端行为可用，从用户角度写——不是逐层的实现清单。

## Plan

它的输出是这张 ticket 的 plan 文件：

```bash
mmw artifact path plan --sub <NN>-<ticket-slug>.md
```

两段各自这么取：

| 段 | 取值 |
| --- | --- |
| `<NN>` | 第 4 步给这张定的两位编号 |
| `<ticket-slug>` | 按第 4 步 Title 的意思，用 `/mmw-start` 第 2 步的规则写成英文 kebab，控制在三四个词以内。Title 本身可以是中文 |

文件由 `/mmw-to-plan` 写，这里先把路径占住。

## Acceptance criteria

按第 3 步的四条判据写，一条一个可观察行为：

- [ ] 判据 1
- [ ] 判据 2

## 产物引用

- category=<类别> name=<名字段>

类别需要范围段或类别内细分时，在同一行追加 `issue=<编号>` 或 `sub=<类别内细分>`。

没有条目时写单独一行 `无`。

## prototype 资产

- 从 `artifact_refs` 解析的 prototype 产物引用。
- 只读取该引用点名的索引、选中产物和走查或长期证据。
- 没有资产时写「无 prototype 资产」。

## research

- 从 `artifact_refs` 解析的 research 产物引用。
- 只读取该引用点名的索引和 research 文件。
- 没有时写「无 research」。

## Blocked by

- 指向每一张阻塞它的 ticket，或者「None — can start immediately」。

</issue-template>

正文里不要写实现文件路径和代码片段。两个理由：它们属于 plan 那一层；而且**它们很快就会过期**——ticket 在 tracker 上可能放上几周，路径改名、函数搬家之后，写死的位置会把 `worker` 带到不存在的地方。同一条风险在 plan 里同样成立，plan 只是过期得慢一些。prototype 的精确出处和当前 ticket 消费的 research 是例外。prototype 产出的一段代码若比散文更精确地编码决定，可以内联并注明选中产物路径；只保留决定含量，不粘贴完整 demo。

用户批准清单、ticket 全部发布完之后，报告已发布的 ticket。问用户：写 plan，还是到这里停。

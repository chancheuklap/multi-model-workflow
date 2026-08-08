---
name: mmw-to-spec
description: 把已经谈定的内容综合、审查并发布成一份 spec。用于用户直接要求写 spec，或者 `/mmw-grilling`、`/mmw-prototype`、`/mmw-wayfinder` 已经把这件事谈定、接下来需要一份 spec 交给下游实现。
---

本技能把已经谈定的内容和你对这个代码库的理解，综合成一份 spec。**不要**访谈用户，只综合已经有的东西。

已经谈定的内容不一定在当前对话里。从 `/mmw-wayfinder` 进来时，那些决定分散在一张 map 和它的 decision ticket 上，当前对话里什么都没有。所以先看下一节，把它们读出来，再开始写。

开始前按 `/mmw-domain-modeling` 的「读领域文档」读取这个仓库的领域文档。整份 spec 使用其中定义的术语。

## 读取已经形成的产物

先确定当前情况，再按匹配行读取已经形成的产物。

| 当前情况 | 要读取的已有产物 | 产物位置 | 怎样找到属于这份 spec 的内容 |
| --- | --- | --- | --- |
| 用户直接调用 `/mmw-to-spec` | 当前对话中已经谈定的内容 | 当前对话 | 从用户提出本次需求的位置开始，读取已经明确形成的决定。不要使用尚未得到确认的建议或问题 |
| `/mmw-grilling` 完成后进入 To Spec | 用户已经确认的共同理解 | 当前对话中 `/mmw-grilling` 最后一次总结的问题、约束、决定、取舍和范围 | 找到用户明确确认的最后一份完整总结。`/mmw-grilling` 调用过 `/mmw-research` 或 `/mmw-prototype` 时，同时读取这份总结引用的结论和精确产物路径 |
| `/mmw-prototype` 完成后直接进入 To Spec | prototype 的 `README.md`，以及它列出的用户走查结论、选中产物、被否掉的方向和可复用内容 | `/mmw-prototype` 交回来的那个精确路径，指向一份 `README.md` | 读交回来的那份 `README.md`。确认它写的「当前问题」属于这份 spec，再顺着它读它点名的选中产物和可复用内容。不要去翻别的 prototype 目录 |
| `/mmw-wayfinder` 关闭 map 后进入 To Spec | 已关闭的 map，跟这份 spec 有关的那几张 decision ticket 的结论，以及这些结论里点名的 prototype 和 research | `/mmw-wayfinder` 交回的 map URL 或编号。运行 `gh issue view <map 编号> --comments` 打开它 | 先确认 map 的 `Destination` 写的就是这份 spec。map 的 `Decisions so far` 一节每行都带着一张 decision ticket 的链接，顺着链接逐张运行 `gh issue view <ticket 编号> --comments`。每张 ticket 关闭前都留了一条写结论的评论，读这条评论和它里面写出的精确文件路径。跟 `Destination` 无关的 ticket 不要读 |

匹配行要求的产物不存在，或者产物中仍缺少一项产品、设计或架构决定时，写清缺少的完整内容和已经检查的位置，然后停止。不要在本技能中重新访谈，也不要猜测缺失产物的位置。

## 确定任务 slug

spec 的落点由任务 slug 决定。按下表取得，不要自己另起一个：

| 当前情况 | 任务 slug |
| --- | --- |
| `/mmw-wayfinder` 关闭 map 后进入 | 使用 `/mmw-wayfinder` 交回的任务 slug，也就是 map 的 slug |
| `/mmw-prototype` 完成后进入 | 使用这次 prototype 使用的 `产物目录` |
| 当前任务已经有任务 slug | 复用已有值 |
| 用户直接调用，而且当前任务还没有任务 slug | 根据这份 spec 要交付的东西提议一个名字，请用户确认后再使用 |

这个名字必须是单个路径段：首字符是字母或数字，其余只能是字母、数字、点、下划线、连字符，不能含斜杠。

定下 slug 之后，这份 spec 的落点就是 `docs/specs/<任务 slug>/<任务 slug>.md`。

## 流程

1. 如果还没有探索过仓库，就探索仓库，以理解代码库当前状态。读取 `docs/adr/` 下与本次范围相关的 ADR，spec 里的决定不能和它们冲突。

2. 勾勒将用于测试这项功能的 seam。已有 seam 应优先于新 seam。使用尽可能高层的 seam。确实需要新 seam 时，在能够达到的最高层提出。整个代码库中的 seam 越少越好；理想数量是一个。

每个 seam 写清公开 interface、将在这个 seam 上验证的外部行为，以及选择这一层的原因。

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |

向用户确认这些 seam 是否符合预期。用户确认前不要写 spec。

3. 完整读取 [spec-template.md](spec-template.md)，使用该模板编写 spec。把 spec 写入 `docs/specs/<任务 slug>/<任务 slug>.md`。

只记录已经形成的决定。写作中发现缺少决定时，写清缺少的完整内容和已经检查的位置，然后停止。

从 Wayfinder 进入时，把相关 decision ticket 中互相链接的决定综合成这一份 spec。prototype 的完整可运行资产继续留在 prototype 目录；spec 只吸收用户确认的决定，以及选中产物中能够比文字更精确地表达某项决定的片段。research 只使用主 agent 已经验证并综合的事实。

4. 调用 `/mmw-review` 发起一次 ① spec 审。传给它 spec 的精确路径，以及这份 spec 实际引用到的 prototype `README.md`、选中产物、research `README.md` 和精确文件；某一项没有就写「无」。

   `/mmw-review` 会返回一批问题，并说明每一条你打算怎么处理。你决定接受的那些，改完之后要回到 `/mmw-review` 让它确认改到位了。全部处理完再进第 5 步。

5. 向用户展示完整 spec、① spec 审结果和已经确认的 seam 清单，询问是否批准定稿和发布。用户在这里点头之前，这份 spec 不算定稿。用户要求修改时，按用户意见修改 spec，再次展示完整结果。用户明确批准前不提交，也不发布。

展示之前先通读一遍整份 spec，确认里面没有任何一处还写着待定、二选一、待确认或类似说法。一份合格的 spec 里每一项决定都已经有答案；下游拿到它就直接开工，没有人会回来替它做决定。发现还有没定的地方时，写清是哪一项、缺什么，然后停止，不要把它作为待定项写进 spec 发出去。

6. 用户明确批准后，先提交 spec 文件，再把它发布到项目 issue tracker，添加 `ready-for-agent` triage 标签，不需要再次 triage。issue 正文保存 spec 摘要、spec 的精确路径，以及本 spec 实际使用的输入出处；从 Wayfinder 进入时，输入出处包含 map 名称及其 URL 或编号。

```bash
mmw issue create --title "<spec 名称>" --body-file <摘要文件> --label ready-for-agent
```

这一步做完的标志是三件事都成立：spec 文件已经提交；这张 spec issue 的正文指向那个文件；这张 issue 带着 `ready-for-agent`。这个标签的意思是用户已经批准了这份 spec，不是说可以照着它一口气实现完。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 已经提交并发布，而且对应 issue 带 `ready-for-agent` | **移交**：`/mmw-to-tickets`，把 spec 拆成 tracer bullet ticket |
| 入口要求的产物不存在，或者其中缺少一项产品、设计或架构决定 | **停**：报告缺少的完整内容和已经检查的位置，等用户补齐或指出正确位置 |
| 已经开始写 spec，但发现某项决定尚未形成 | **停**：报告缺少的完整内容和已经检查的位置；这项决定需要先谈定，不在本技能中访谈 |
| 用户看过完整 spec 和 ① spec 审结果后要求修改 | **停**：按用户意见修改 spec，再次展示完整结果，等待批准 |

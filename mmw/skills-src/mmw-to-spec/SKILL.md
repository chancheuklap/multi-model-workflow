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
| 被交来一张已经分诊过的 issue 编号（`/mmw-start` 或 `/mmw-triage` 判定它要拆成多张 ticket） | 那张 issue 的正文、agent brief 和讨论 | 交回来的那个 issue 编号。运行 `gh issue view <编号> --comments` 打开它 | 读正文和 agent brief，认出这次要交付的产品行为。它是这份 spec 的输入，不是 spec 本身——决定不够写成 spec 时按本节末尾停下 |
| `/mmw-wayfinder` 关闭 map 后进入 To Spec | 已关闭的 map，跟这份 spec 有关的那几张 decision ticket 的结论，以及这些结论里点名的 prototype 和 research | `/mmw-wayfinder` 交回的 map URL 或编号。运行 `gh issue view <map 编号> --comments` 打开它 | 先确认 map 的 `Destination` 写的就是这份 spec。从 map 的 `## 工作名` 记下交来的工作名。map 的 `Decisions so far` 一节每行都带着一张 decision ticket 的链接，顺着链接逐张运行 `gh issue view <ticket 编号> --comments`。每张 ticket 关闭前都留了一条写结论的评论，读这条评论和它里面写出的精确文件路径。跟 `Destination` 无关的 ticket 不要读 |

匹配行要求的产物不存在，或者产物中仍缺少一项产品、设计或架构决定时，写清缺少的完整内容和已经检查的位置，然后停止。不要在本技能中重新访谈，也不要猜测缺失产物的位置。

## 确定工作名

从 `/mmw-wayfinder` 进入时，先从 map 的 `## 工作名` 取得 `<map 工作名>`。需要进树时，用它作为 `<工作名>`。

先运行 `mmw task state`。第一个词是 `bound` 时，运行 `mmw task name` 取工作名。

输出是 `detached` 时，先分别确定任务分支名和工作名。运行 `mmw task bind <任务分支名> "<用户原话>" --name <工作名> [--from <父分支或基点 SHA>]`。

输出是 `local` 时，先分别确定任务分支名和工作名。[[mmw-enter-worktree]]

输出是 `outside` 时，向用户索取目标仓库路径。拿到路径后进入该仓库，再重新运行 `mmw task state`。

两种建树动作之后都重新运行 `mmw task state`。第一个词确认是 `bound` 后，运行 `mmw task name` 取工作名。

从 `/mmw-wayfinder` 进入时，比较 `<map 工作名>` 与 `mmw task name` 的输出。不一致时，报告两者冲突并交给用户决定；不要自己选一个。

## 流程

1. 如果还没有探索过仓库，就探索仓库，以理解代码库当前状态。读取 `docs/adr/` 下与本次范围相关的 ADR，spec 里的决定不能和它们冲突。

2. 勾勒将用于测试这项功能的 seam。已有 seam 应优先于新 seam。使用尽可能高层的 seam。确实需要新 seam 时，在能够达到的最高层提出。整个代码库中的 seam 越少越好；理想数量是一个。

每个 seam 写清公开 interface、将在这个 seam 上验证的外部行为，以及选择这一层的原因。

| Seam | 验证的外部行为 | 选择这一层的原因 |
| --- | --- | --- |

向用户确认这些 seam 是否符合预期。用户确认前不要写 spec。

3. 完整读取 [spec-template.md](spec-template.md)。使用该模板编写 spec。运行 `mmw artifact path spec`。把 spec 写入输出文件。

   元数据块固定写六个字段。`slug` 写工作名。`summary` 写一句交付说明。`date` 写当天的 `YYYY-MM-DD`。`branch` 写当前任务分支名。`spec_issue` 在发布前暂写模板占位编号。`artifact_refs` 始终存在；当前没有产物引用时写 `[]`。

   把这份 spec 实际使用的 prototype 资产和 research 写成产物引用。每条都写显式工作名。使用下面的 YAML 映射列表。类别需要范围段或类别内细分时才写 `issue` 或 `sub`。没有引用时写 `artifact_refs: []`。

   ```yaml
   artifact_refs:
     - category: <类别>
       name: <工作名>
       issue: <编号>
       sub: <类别内细分>
   ```

   写完或修完 spec 后，先运行 `mmw artifact check`。命令非零时先修产物引用声明。命令通过后再自检和发起 ① spec 审。

只记录已经形成的决定。写作中发现缺少决定时，写清缺少的完整内容和已经检查的位置，然后停止。

从 Wayfinder 进入时，把相关 decision ticket 中互相链接的决定综合成这一份 spec。prototype 的完整可运行资产继续留在 prototype 目录；spec 只吸收用户确认的决定，以及选中产物中能够比文字更精确地表达某项决定的片段。research 只使用主 agent 已经验证并综合的事实。

   写完之后、发起审查之前，通读整份 spec 做一遍**自检**。审查者不替你兜底——审查是为了发现你看不见的问题，不是替你收没写完的尾。逐项过：

   - 模板每个必写 section 都有内容，条件式 section 该出现的出现了。
   - 每项决定都能指回一个已确认的来源：对话中的用户确认、decision ticket 的结论评论、prototype 走查结论或验证过的 research 事实。指不回来源的不是决定，是你的发明——删掉或回去确认。
   - 没有任何一处写着待定、二选一、待确认或类似说法。下游拿到 spec 就直接开工，没有人会回来替它做决定。
   - seam 表与第 2 步用户确认的一致，没有悄悄增删。
   - 引用的 prototype 与 research 路径每一条都真实存在。

   有一项不过就先修再审。修不了的（缺决定、缺来源），写清缺什么、查过哪里，然后停止。

4. 调用 `/mmw-review` 发起一次 ① spec 审。传给它 spec 的精确路径，以及这份 spec 实际引用到的 prototype `README.md`、选中产物、research `README.md` 和精确文件；某一项没有就写「无」。

   `/mmw-review` 会返回一批问题，并说明每一条你打算怎么处理。你决定接受的那些，改完之后要回到 `/mmw-review` 让它确认改到位了。全部处理完再进第 5 步。

5. 向用户展示完整 spec、① spec 审结果和已经确认的 seam 清单，询问是否批准定稿和发布。用户在这里点头之前，这份 spec 不算定稿。用户要求修改时，按用户意见修改 spec，再次展示完整结果。用户明确批准前不提交，也不发布。

展示之前把第 3 步末尾那份自检再过一遍——处理审查意见的修改可能引入新的未定项或悬空引用。有一项不过就先修好再展示。

6. 用户明确批准后，先提交 spec 文件，再把它发布到项目 issue tracker，添加 `ready-for-agent` triage 标签，不需要再次 triage。issue 正文保存 spec 摘要、spec 的精确路径，以及本 spec 实际使用的输入出处；从 Wayfinder 进入时，输入出处包含 map 名称及其 URL 或编号。

   正文固定写出以下一节。它记录 spec 元数据块装不下的来源链，例如 map 名称及其 URL 或编号、prototype 与 research 的来源。

   ```markdown
   ## 输入出处

   <本次实际输入>
   ```

正文先落盘再发。运行 `mmw artifact path scratch --sub outbox/spec-issue-body.md`。把正文写入输出文件。这份正文发完就没用了。

```bash
mmw issue create --title "<spec 名称>" --body-file <上一步输出文件> --label ready-for-agent
```

记下 `mmw issue create` 返回的 issue 编号。入口是已分诊 issue 且它带 agent brief 时，先运行 `mmw issue set-parent <原 issue 编号> --parent <spec issue 编号>`。命令失败时停止，保留原 issue 为 open。命令成功后运行 `gh issue close <原 issue 编号>`。没有原 issue 时跳过这两步。

立刻用这个编号替换 spec 元数据块中的 `spec_issue` 占位编号，再提交这次回填。最终 spec 不得保留占位编号。移交时把这个编号一起交出去——下游三个技能都要用它。

这一步做完的标志是四件事都成立：spec 文件已经提交；spec 元数据块的 `spec_issue` 已经回填为实际编号；这张 spec issue 的正文指向那个文件；这张 issue 带着 `ready-for-agent`。这个标签的意思是用户已经批准了这份 spec，不是说可以照着它一口气实现完。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 已经提交并发布，而且对应 issue 带 `ready-for-agent` | **移交**：`/mmw-to-tickets`，交给它工作名和这张 spec issue 的编号，把 spec 拆成 tracer bullet ticket |
| 入口要求的产物不存在，或者其中缺少一项产品、设计或架构决定 | **停**：报告缺少的完整内容和已经检查的位置，等用户补齐或指出正确位置 |
| 已经开始写 spec，但发现某项决定尚未形成 | **停**：报告缺少的完整内容和已经检查的位置；这项决定需要先谈定，不在本技能中访谈 |
| 用户看过完整 spec 和 ① spec 审结果后要求修改 | **停**：按用户意见修改 spec，再次展示完整结果，等待批准 |

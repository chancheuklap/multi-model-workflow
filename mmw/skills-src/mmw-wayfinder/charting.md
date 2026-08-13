# Chart the map

用户带着一个松散的想法调用。这个会话把 map 建出来就结束，不去解那些需要讨论的 ticket；只有 `wayfinder:research` 这一种例外，因为它不需要用户参与，可以在这个会话里并行跑完（第 5、6 步）。

这个会话的任务分支就是 map 分支。后面每张 decision ticket 都从它派生。先分别确定任务分支名和工作名。任务分支名取这项 effort 的短名。

先跑 `mmw task state`。它输出一行，第一个词决定这棵树要不要你自己建：

| 第一个词 | 什么意思 | 你做什么 |
| --- | --- | --- |
| `bound` | 你已经在一棵绑好的任务 worktree 里 | 什么都不用建。运行 `mmw task name` 取工作名，记下它 |
| `detached` | 宿主把你放在一棵干净的树上了，还没绑分支 | 绑定：`mmw task bind <任务分支名> "<用户原话>" --name <工作名> [--from <父分支或基点 SHA>]`。重新运行 `mmw task state`。确认输出是 `bound`。再运行 `mmw task name` 取工作名 |
| `local` | 你在主检出里 | [[mmw-enter-worktree]] |
| `outside` | 你根本不在仓库里 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新运行 `mmw task state`，按新输出重新选行 |

两条路都一样：工作区不干净、分支已经存在、或者父分支里没有这次任务需要的决定时，**停下来**——不要在错的基点上补提交。

1. **给 destination 命名。** 运行一场 `/mmw-grilling` session；它在同一场讨论中应用 `/mmw-domain-modeling`，确定这张 map 正在寻找的 spec、决定或改动。destination 固定范围，所以先确定它。

   给这项 effort 定一个工作名。它是这项 effort 的 prototype、research 和过程材料共用的名字。它必须是单个路径段：首字符是字母或数字，其余只能是字母、数字、点、下划线、连字符，不能含斜杠。map 建好之后这个值不再改。

2. **map frontier。** 再运行一场 `/mmw-grilling` session，这次采用**广度优先**方式：在整个空间铺开，不在任何一条问题线上深入。找出 open 的决定，以及当前可以采取的起始步骤。

   本场的目的是让 open 的决定暴露出来，不是定下它们的答案。这里只识别当前能够精确表述的问题和仍处于 fog 中的区域。整个空间已经铺开、open 决定和 fog 区域都已识别时，本场结束。不要把 frontier 追到为空。

   如果这一步没有发现 fog，通往 destination 的路线已经清楚，整个过程也足够小，能够放进一个 session，因此不需要 map。向用户说明这个判断，询问接下来怎样进行，然后停止。不要执行第 3—6 步。

3. **创建 map**，并添加 `wayfinder:map` 标签。map 名称就是这张 issue 的标题，按这项 effort 起。填写 Destination 和 Notes；Decisions so far 留空；把 fog 的轮廓写入 **Not yet specified**。

   同时把第 1 步确定的工作名写入 map 正文的 `## 工作名`，并把 `mmw task state` 报的当前分支名写进 `## 分支`——这个会话的任务分支就是 map 分支，后来的会话只能从这里拿到它。运行 `mmw artifact path scratch --sub outbox/map-body.md`。把完整的 map 正文写进输出文件，再用它创建 issue：

   ```bash
   mmw issue create --title "<map 名称>" --body-file <上一步输出文件> --label wayfinder:map
   ```

4. 把**当前能够精确表述的问题全部建成 ticket**，作为 map 的子 issue。当前仍说不清楚的内容继续留在 **Not yet specified** 一节。

   分两遍做，因为 issue 要先有编号才能互相引用。第一遍全部建出来，按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节为每张选一个 `wayfinder:<type>`。ticket 名称就是它的 issue 标题，按那个问题起。每张正文都写 `## Question` 和 `## 必读材料声明`。后者列当时已经知道、且与这张 Question 相关的仓库产物引用与结论评论 issue 编号。没有材料时写 `无`。每张先运行 `mmw artifact path scratch --sub outbox/ticket-<序号>.md`。把正文写入输出文件，再发：

   ```bash
   mmw issue create --title "<ticket 名称>" --body-file <上一步输出文件> \
     --parent <map 编号> --label wayfinder:<type>
   ```

   第二遍连阻塞关系，一次一条：

   ```bash
   mmw issue link <被挡住的编号> --blocked-by <挡住它的编号>
   ```

   连完之后运行 `mmw issue frontier <map 编号>`。它只列没有被挡住、也没有人认领的 ticket；这一步刚建出来的都还没人认领，所以出现在输出里就等于没被挡。对照你刚才连的关系逐张核一遍：该被挡的不在输出里，不该被挡的在。

5. **启动 research。** 对刚创建的每张 `wayfinder:research` ticket，先运行 `mmw issue claim <编号>`。claim 失败的 ticket 已由其他 session 占用，不重复派发。

   claim 成功后，运行 `mmw artifact list --name <工作名> --map <map 编号>`。从候选中选出与这张 Question 相关的材料，补进自己的 `## 必读材料声明`；保留已有条目。开工前读取声明的每项材料。仓库产物逐条运行 `mmw artifact path` 解析，再读它的索引与索引列出的文件。结论评论逐条读取对应 issue 中以 `<!-- mmw:conclusion -->` 开头的评论。

   声明的材料缺失时先分类。生产 ticket 按设计未运行，或用户选择不保存 research，是预期缺失，继续。生产方已经运行而声明内容应当存在却找不到，是异常缺失，停下问用户，不编造内容。问的时候给出两个选项：重新解决生产它的那张 decision ticket，或者由用户直接提供文件。

   分别运行 `mmw artifact path research --issue <编号> --sub <主题>` 和 `mmw artifact path scratch --issue <编号> --sub evidence`。把 ticket 的 Question、必读材料声明中的全部仓库产物引用、全部结论评论 issue 编号、工作名、范围段 `issue-<编号>`，以及两条输出路径一起传给 `/mmw-research`。每张 ticket 作为一项独立 research 并行处理；`/mmw-research` 根据取证角度决定 `investigator` 的数量。

   查证、验证、综合、保存和清理过程材料都由 `/mmw-research` 自己完成，你只等它交回。`/mmw-research` 对 ticket 派来的调查直接保存，不会停下来问用户；它交回的内容里有 research 的 `README.md` 精确路径。

   等待本次派出的 research 全部交回，再进入第 6 步。

6. **记录 research 结果并提交。** 对每张已经交回的 research ticket，按顺序完成：

   1. 运行 `mmw artifact path scratch --issue <编号> --sub outbox/answer.md`。输出文件第一行写 `<!-- mmw:conclusion -->`。随后依次写 `## 答案`、`## 产物引用` 和 `## 材料使用记录`。产物引用逐行写键值形态；没有仓库产物时写 `无`。材料使用记录逐条覆盖 `## 必读材料声明` 里的每项材料，写明用上了没有；未用时写出理由。然后评论：`gh issue comment <编号> --body-file <上一步输出文件>`。
   2. 关闭这张 ticket：`gh issue close <编号>`。
   3. 在 map 的 `Decisions so far` 追加一行：`mmw issue append <map 编号> --section "Decisions so far" --line "<ticket 名称的链接与一句话概要>"`。
   4. research 让一部分原本说不清楚的问题变得说得清楚时，按第 4 步的两遍做法建成新 ticket；仍说不清楚的留在 `Not yet specified`。

   然后把这个会话在 map 分支上写下的全部内容提交：research 目录，以及讨论过程中调用 `/mmw-domain-modeling` 写下的领域文档和 ADR。这一轮没有动过仓库文件时，不要制造一个空提交。

   charting 到这里完成。其他 decision ticket 由后续 session claim，每个 session 一张。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 2 步没有发现 fog | **停**：说明路线已经清楚、不需要 map，询问用户接下来怎样进行 |
| map、当前能够精确表述的 ticket 和 blocking edge 已建立，research 已全部交回并提交 | **停**：报告 destination、工作名、map 名称和当前 frontier 上的 ticket 名称，并说明每张 decision ticket 使用一个新会话。同时列出每张 frontier ticket 的任务 slug，并写明父分支是 map 分支。不要 claim 这些 ticket |

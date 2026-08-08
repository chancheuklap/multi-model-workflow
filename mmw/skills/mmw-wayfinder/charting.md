# Chart the map

用户带着一个松散的想法调用。这个会话把 map 建出来就结束，不去解那些需要讨论的 ticket；只有 `wayfinder:research` 这一种例外，因为它不需要用户参与，可以在这个会话里并行跑完（第 5、6 步）。

这个会话的任务分支就是 map 分支，后面每张 decision ticket 都从它派生。运行 `mmw task state` 确认输出以 `bound` 开头；不是时执行宿主动作：

先跑 `mmw task state`。它输出一行，第一个词决定这棵树要不要你自己建：

| 第一个词 | 什么意思 | 你做什么 |
| --- | --- | --- |
| `bound` | 你已经在一棵绑好的任务 worktree 里 | 什么都不用建。第二个词是任务分支名，第三个词是当前 HEAD，记下它们 |
| `detached` | 宿主把你放在一棵干净的树上了，还没绑分支 | 绑定：`mmw task bind <分支名> "<用户原话>"`。`<分支名>` 用这个任务的 slug；宿主对任务分支有固定命名空间（Codex App 是 `codex/`）时带上它。知道预期基点就加 `--from <父分支或基点 SHA>`，它只是一道校验，不确定就不加。命令必须返回任务分支名和起始提交 |
| `local` 或 `outside` | 你在主检出里，或者根本不在仓库里 | 这棵树要你自己建：`mmw task new <slug> "<用户原话>"`，从 map 分支派生时加 `--from <map 分支>`。命令返回绝对路径，用宿主切换工作目录的能力进去 |

两条路都一样：工作区不干净、分支已经存在、或者父分支里没有这次任务需要的决定时，**停下来**——不要在错的基点上补提交。

1. **给 destination 命名。** 运行一场 `/mmw-grilling` session；它在同一场讨论中应用 `/mmw-domain-modeling`，确定这张 map 正在寻找的 spec、决定或改动。destination 固定范围，所以先确定它。

   给这项 effort 定一个 `产物目录`。它是这项 effort 的 prototype、research 和过程材料共用的一个目录名。它必须是单个路径段：首字符是字母或数字，其余只能是字母、数字、点、下划线、连字符，不能含斜杠。map 建好之后这个值不再改。

2. **map frontier。** 在当前 charting session 中采用**广度优先**方式：在整个空间铺开，不在任何一条问题线上深入。找出 open 的决定，以及当前可以采取的起始步骤。这里只识别当前能够精确表述的问题和仍处于 fog 中的区域，不解决这些 open 决定。

   如果这一步没有发现 fog，通往 destination 的路线已经清楚，整个过程也足够小，能够放进一个 session，因此不需要 map。向用户说明这个判断，询问接下来怎样进行，然后停止。不要执行第 3—6 步。

3. **创建 map**，并添加 `wayfinder:map` 标签。填写 Destination 和 Notes；Decisions so far 留空；把 fog 的轮廓写入 **Not yet specified**。

   同时把第 1 步确定的 `产物目录` 写入 map 正文，并把 `mmw task state` 报的当前分支名写进 `## 分支`——这个会话的任务分支就是 map 分支，后来的会话只能从这里拿到它。把完整的 map 正文写进 `.scratch/<产物目录>/map-body.md`，再用它创建 issue：

   ```bash
   mmw issue create --title "<map 名称>" --body-file .scratch/<产物目录>/map-body.md --label wayfinder:map
   ```

4. 把**当前能够精确表述的问题全部建成 ticket**，作为 map 的子 issue。当前仍说不清楚的内容继续留在 **Not yet specified** 一节。

   分两遍做，因为 issue 要先有编号才能互相引用。第一遍全部建出来，按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节为每张选一个 `wayfinder:<type>`。每张的正文只写 `Question`，先写进 `.scratch/<产物目录>/ticket-<序号>.md`，再发：

   ```bash
   mmw issue create --title "<ticket 名称>" --body-file .scratch/<产物目录>/ticket-<序号>.md \
     --parent <map 编号> --label wayfinder:<type>
   ```

   第二遍连阻塞关系，一次一条：

   ```bash
   mmw issue link <被挡住的编号> --blocked-by <挡住它的编号>
   ```

   连完之后运行 `mmw issue children <map 编号>`，它的第四列是每张 ticket 还被几张开着的 issue 挡着。对照你刚才连的关系逐张核一遍：该被挡的这一列不是 0，不该被挡的是 0。

5. **启动 research。** 对刚创建的每张 `wayfinder:research` ticket，先运行 `mmw issue claim <编号>`。claim 失败的 ticket 已由其他 session 占用，不重复派发。

   claim 成功后，把 `docs/research/<产物目录>/issue-<编号>` 和 `.scratch/<产物目录>/issue-<编号>` 这两条路径连同 ticket 的 Question 一起传给 `/mmw-research`。每张 ticket 作为一项独立 research 并行处理；`/mmw-research` 根据取证角度决定 `investigator` 的数量。

   在传给 `/mmw-research` 的内容里明确写一句：这次直接保存，不用问用户。理由是这张 ticket 本身就是用户对这次调查的批准，而且这里同时跑着好几张，各自停下来等人回答就没法并行了。

   查证、验证、综合、保存和清理过程材料都由 `/mmw-research` 自己完成，你只等它交回。

   等待本次派出的 research 全部交回，再进入第 6 步。

6. **记录 research 结果并提交。** 对每张已经交回的 research ticket，按顺序完成：

   1. 把答案作为一条评论发在这张 ticket 上：`gh issue comment <编号> --body-file .scratch/<产物目录>/issue-<编号>/answer.md`。内容是验证后的事实、research 的 `README.md` 精确路径，以及没查清楚的部分。
   2. 关闭这张 ticket：`gh issue close <编号>`。
   3. 在 map 的 `Decisions so far` 追加一行：ticket 名称包着它的链接，加一句话概要。改 map 正文之前先 `gh issue view <map 编号>` 重新读一遍最新的，改完再读一遍确认自己那行在。
   4. research 让一部分原本说不清楚的问题变得说得清楚时，按第 4 步的两遍做法建成新 ticket；仍说不清楚的留在 `Not yet specified`。

   然后把这个会话在 map 分支上写下的全部内容提交：research 目录，以及讨论过程中调用 `/mmw-domain-modeling` 写下的领域文档和 ADR。这一轮没有动过仓库文件时，不要制造一个空提交。

   charting 到这里完成。其他 decision ticket 由后续 session claim，每个 session 一张。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 2 步没有发现 fog | **停**：说明路线已经清楚、不需要 map，询问用户接下来怎样进行 |
| map、当前能够精确表述的 ticket 和 blocking edge 已建立，research 已全部交回并提交 | **停**：报告 destination、`产物目录`、map 名称和当前 frontier 上的 ticket 名称，并说明每张 decision ticket 使用一个新会话 |

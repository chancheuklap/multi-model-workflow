# Chart the map

<!-- upstream: 103-116 -->

用户带着一个松散的想法调用。

1. **给 destination 命名。** 运行一场 `/mmw-grilling` session；它在同一场讨论中应用 `/mmw-domain-modeling`，确定这张 map 正在寻找的 spec、决定或改动。destination 固定范围，所以先确定它。

   给这项 effort 确定一个 `产物目录`。它是 prototype、research、evidence 和 scratch 共用的单个安全路径段。运行 `mmw path scratch <产物目录>` 验证该值；map 创建后保持不变。

2. **map frontier。** 再次 grilling，这次采用**广度优先**方式：在整个空间铺开，不在任何一条问题线上深入。找出 open 的决定，以及当前可以采取的起始步骤。

   如果这一步没有发现 fog，通往 destination 的路线已经清楚，整个过程也足够小，能够放进一个 session，因此不需要 map。向用户说明这个判断，询问接下来怎样进行，然后停止。不要执行第 3—6 步。

3. **创建 map**，并添加 `wayfinder:map` 标签。填写 Destination 和 Notes；Decisions so far 留空；把 fog 的轮廓写入 **Not yet specified**。

   同时把第 1 步确定的 `产物目录` 写入 map 正文。使用完整的 map 正文文件创建 issue：

   ```bash
   mmw issue create --title "<map 名称>" --body-file <正文文件> --label wayfinder:map
   ```

4. 把**当前能够精确表述的 ticket 全部创建出来**，作为 map 的子 issue。随后在**第二遍** wire blocking edge，因为 issue 取得 id 后才能互相引用。wire 完成后，这些 ticket 会分成 frontier 和 blocked 两组。当前仍无法精确表述的所有内容继续留在 fog，也就是 **Not yet specified** 一节。

   按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节为每张 ticket 选择 `wayfinder:<type>`。创建时先在正文写 `Question` 和从 map 原样继承的 `产物目录`：

   ```bash
   mmw issue create --title "<ticket 名称>" --body-file <正文文件> \
     --parent <map 编号> --label wayfinder:<type>
   ```

   命令返回编号后，在正文回填 `issue 子目录`，值为 `issue-<编号>`，再用 `gh issue edit <编号> --body-file <正文文件>` 更新。全部 ticket 创建并回填后，第二遍 wire blocking edge：

   ```bash
   mmw issue link <被阻塞的 ticket> --blocked-by <blocker>
   ```

   最后运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`，确认 frontier 和 blocked 两组符合已经 wire 的 blocking edge。

5. **启动 research subagent。** 对刚创建的每张 `wayfinder:research` ticket，先运行 `mmw issue claim <编号>`。claim 成功后，运行 `mmw path research <产物目录> issue-<编号>` 和 `mmw path scratch <产物目录> issue-<编号>`，把实际输出和 ticket 的 Question 传给 `/mmw-research`，各派一个 `investigator` 并行解决；每个 `investigator` 只处理一张 ticket。claim 失败的 ticket 已由其他 session 占用，不重复派发。等待本次派出的 research 全部交回。

   `/mmw-research` 负责报告验证、综合、保存人工审批关卡和清理自己的 scratch，本文不重复这些步骤。全部 research 交回后，提交用户批准保存的 research 和本会话已经形成的其他仓库改动；没有仓库改动时不制造空提交。然后在每张 ticket 的 resolution comment 写入验证后的事实和未查清项；用户选择保存时，再加入 research 索引的精确路径。关闭 ticket，并在 map 的 Decisions so far 中追加 context pointer。修改 map 前重新读取最新正文，修改后再次读取，确认 context pointer 存在。research 新显露的精确问题继续使用第 4 步的 create-then-wire；仍无法精确表述的内容留在 Not yet specified。

6. **完成 charting。** charting 是一个 session 的工作。除第 5 步并行处理的 research ticket 外，这个 session 不解决其他 decision ticket。

   确认没有漏交的仓库改动。准备 destination、map 名称和当前 frontier，交给文末“下一步”报告；其他 decision ticket 由后续 session claim。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| map、当前能够精确表述的 ticket 和 blocking edge 已建立，research 已全部交回 | **停**：报告 destination、map 名称和当前 frontier |

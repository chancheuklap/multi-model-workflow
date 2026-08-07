# 沿 map 推进

用户带着一张 map 调用，可以使用 URL 或编号。ticket 是可选项；用户没有指定 ticket 时，由你选择下一个决定，不要求用户选择。

1. 加载 **map**，也就是低分辨率视图，不加载每张 ticket 的正文。

   读取 map 正文中的 `产物目录`，再运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`。

   用户指定 ticket 时，运行 `mmw issue children <map 编号>`，在输出中确认这张 ticket 是当前 map 的子 issue，带 `wayfinder:` 标签，状态是 open，没有 assignee，而且被阻塞数量为零。五项全部成立时继续第 2 步；任何一项不成立时，报告实际状态并停止，不 claim 或解决这张 ticket。

   用户没有指定 ticket 时，frontier 至少有一张 ticket 就继续第 2 步。frontier 为空时，立即运行 `mmw issue children <map 编号>`：

   | 查询结果 | 处理 |
   | --- | --- |
   | 仍有带 `wayfinder:` 标签的 open decision ticket | 报告这些 ticket 已被 claim 或仍被 blocking，保持 map open，并停止本次 session；不要进入第 2 步 |
   | 没有带 `wayfinder:` 标签的 open decision ticket | 读取 [closing.md](closing.md)；不要进入第 2 步 |

2. 选择 ticket。用户点名一张时使用那一张；用户没有点名时，按顺序取得第一张 frontier ticket。**claim 它**：开始任何工作前先把 ticket 指派给自己。

   使用 `mmw issue claim <编号>` claim。失败说明另一个 session 已经 claim 这张 ticket，改取下一张。所有 frontier ticket 都 claim 失败时，报告这些 ticket 已被其他 session 认领，然后停止；不要进入第 3 步。

3. 解决 ticket。根据需要 **zoom**：按需取得相关或已关闭 ticket 的完整正文；调用 `## Notes` 区块点名的技能。不确定时，使用 `/mmw-grilling`；它在同一场讨论中应用 `/mmw-domain-modeling`。

   按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节处理。把 map 的 `产物目录` 和当前 ticket 的 `issue-<编号>` 原样交给需要资产路径的下游技能；精确路径由实际写入资产的技能计算：

   | 标签 | MMW 接口 |
   | --- | --- |
   | `wayfinder:grilling` | 调用 `/mmw-grilling` |
   | `wayfinder:prototype` | 把 `Question`、`产物目录` 和 `issue-<编号>` 交给 `/mmw-prototype` |
   | `wayfinder:research` | 把 `Question`、`产物目录` 和 `issue-<编号>` 交给 `/mmw-research` |
   | `wayfinder:task` | agent 能完成时直接完成；必须由用户完成的多步流程调用 `/wizard`，并交给它 `产物目录` 和 `issue-<编号>` |

   `wayfinder:task` 必须等待用户操作时，给出精确操作并停止本步骤。用户返回后继续处理同一张 ticket；不要提前执行第 4 步。

   HITL ticket 只能由用户与 agent 共同解决。`wayfinder:grilling` 已经通过 `/mmw-grilling` 在同一段对话中应用 `/mmw-domain-modeling`，并完成本次讨论需要的领域模型修改；不要为同一项结果重复调用 `/mmw-domain-modeling`。

   `wayfinder:prototype`、`wayfinder:research` 或 `wayfinder:task` 得到结果后，检查它是否形成需要长期保留的领域术语、bounded context、bounded context 之间的关系，或者符合 ADR 三项判据的决定。形成其中任何一项时，调用 `/mmw-domain-modeling`；没有形成时，不增加领域文档步骤。答案明确否决一个 enhancement 时，按 tracker 合同把理由保存到 `.out-of-scope/`。这些仓库改动在更新 tracker 之前完成。

   scratch 清理和 worktree 判定由实际创建文件的下游技能负责。Wayfinder 不为每张 decision ticket 另建一套 worktree 或分支集成流程。存在持久仓库内容时，确认下游技能已经完成自己的清理，并在继续第 4 步前提交仍未提交的持久内容；没有仓库改动时不制造空提交。

4. 记录解决结果：把答案发布为一条 **resolution comment**，**关闭** issue，并在 map 的 Decisions so far 中追加一个 context pointer。

   resolution comment 链接这张 ticket 实际形成的 prototype、research 或 evidence；没有资产时只记录答案。修改 map 前重新读取最新正文，修改后再次读取，确认本次 context pointer 存在，并保留其他 session 的并发修改。

5. 添加 newly-surfaced ticket，采用 **create-then-wire**：先创建，再连接 blocking edge。把这次答案已经变得可以精确表述的 fog 转成 ticket；每块转成 ticket 的 fog 都要从 **Not yet specified** 删除，使它只存在于新 ticket 中。如果答案表明某张 ticket 位于 destination 之外，无论是当前 ticket 还是另一张 ticket，都把它 **rule out of scope**，不要把它当作路线上的决定来解决。如果这项决定使 map 的其他部分失效，更新或删除对应 ticket。

   新 ticket 原样继承 map 的 `产物目录`，取得 tracker 编号后回填自己的 `issue-<编号>`，然后第二遍 wire blocking edge。rule out of scope 时，在 Out of scope 留下概要、越界理由和 ticket 链接；明确否决 enhancement 的 `.out-of-scope/` 理由已经在第 3 步保存并提交。

用户可以并行处理没有阻塞的 ticket。因此，要预期其他 session 会同时编辑 tracker。

完成第 5 步后重新运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`。frontier 为空时，再运行 `mmw issue children <map 编号>`。当前 ticket 的处理到这里完成；按照文末“下一步”处理查询结果，不继续 claim 新 ticket。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 当前 ticket 已记录并关闭，frontier 仍有 ticket | **停**：报告本次决定和当前 frontier；其他 session claim 下一张 ticket |
| 当前 ticket 已记录并关闭，而且没有带 `wayfinder:` 标签的 open decision ticket | **自己继续**：读取 [closing.md](closing.md) |
| 当前 ticket 已记录并关闭，frontier 为空，但仍有已被 claim 或仍被 blocking 的 open decision ticket | **停**：报告这些 ticket 的当前状态，map 保持 open |

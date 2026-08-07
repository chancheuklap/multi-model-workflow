# 走完整张 map

<!-- upstream: 118-128 -->

用户带着一张 map 调用，可以使用 URL 或编号。ticket 是可选项；用户没有指定 ticket 时，由你选择下一个决定，不要求用户选择。

1. 加载 **map**，也就是低分辨率视图，不加载每张 ticket 的正文。

   读取 map 正文中的 `产物目录`，再运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`。frontier 至少有一张 ticket 时，继续第 2 步。frontier 为空时，立即运行 `mmw issue children <map 编号>`：

   | 查询结果 | 处理 |
   | --- | --- |
   | 仍有带 `wayfinder:` 标签的 open decision ticket | 报告这些 ticket 已被 claim 或仍被 blocking，保持 map open，并停止本次 session；不要进入第 2 步 |
   | 没有带 `wayfinder:` 标签的 open decision ticket | 拥有 map 分支的任务读取 [closing.md](closing.md)；不要进入第 2 步 |

2. 选择 ticket。用户点名一张时使用那一张；用户没有点名时，按顺序取得第一张 frontier ticket。**claim 它**：开始任何工作前先把 ticket 指派给自己。

   使用 `mmw issue claim <编号>` claim。失败说明另一个 session 已经 claim 这张 ticket，改取下一张。所有 frontier ticket 都 claim 失败时，报告这些 ticket 已被其他 session 认领，然后停止；不要进入第 3 步。claim 成功后，从 map 分支当前已提交的 HEAD 建立这张 decision ticket 的任务 worktree；任务 slug 只识别任务，不决定产物路径。

   [[mmw-host-action:prepare-task-worktree]]

3. 解决 ticket。根据需要 **zoom**：按需取得相关或已关闭 ticket 的完整正文；调用 `## Notes` 区块点名的技能。不确定时，使用 `/mmw-grilling`；它在同一场讨论中应用 `/mmw-domain-modeling`。

   按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节处理，只计算该分支需要的路径：

   | 标签 | MMW 接口和路径 |
   | --- | --- |
   | `wayfinder:grilling` | 调用 `/mmw-grilling`；不计算资产路径 |
   | `wayfinder:prototype` | 运行 `mmw path prototype <产物目录> issue-<编号>` 和 `mmw path scratch <产物目录> issue-<编号>`，把实际输出传给 `/mmw-prototype`；需要外部系统实测时再运行 `mmw path evidence <产物目录> issue-<编号>` |
   | `wayfinder:research` | 运行 `mmw path research <产物目录> issue-<编号>` 和 `mmw path scratch <产物目录> issue-<编号>`，把实际输出传给 `/mmw-research` |
   | `wayfinder:task` | agent 能完成时直接完成；必须由用户完成的多步流程调用 `/wizard`，只有该流程需要 scratch 时才运行 `mmw path scratch <产物目录> issue-<编号>` |

   `wayfinder:task` 必须等待用户操作时，给出精确操作并停止本步骤。用户返回后继续处理同一张 ticket；不要提前执行第 4 步。

   HITL ticket 只能由用户与 agent 共同解决。`wayfinder:grilling` 已经通过 `/mmw-grilling` 在同一段对话中应用 `/mmw-domain-modeling`，不要重复调用。其他 HITL ticket 的结果确实形成需要长期保留的领域术语、bounded context、bounded context 之间的关系，或者符合 ADR 三项判据的决定时，调用 `/mmw-domain-modeling`；没有形成需要长期保留的领域术语、bounded context、bounded context 之间的关系或符合 ADR 三项判据的决定时，不增加领域文档步骤。答案明确否决一个 enhancement 时，按 Tracker 合同把理由保存到 `.out-of-scope/`。这些仓库改动在更新 tracker 之前完成。

   prototype、research 或 `/wizard` 使用了 scratch 时，清理 `mmw path scratch <产物目录> issue-<编号>` 返回的当前 ticket scratch。存在仓库改动时提交结果分支，并交回结果分支名、HEAD SHA、基点 SHA 和报告。结果分支在这里停止，不执行第 4 步。拥有 map 分支的任务先运行 `mmw result verify <结果分支> <HEAD SHA> <基点 SHA>`，再运行 `mmw result integrate <结果分支> <HEAD SHA> <基点 SHA>`；没有仓库改动时不制造空提交或空集成。仓库改动完成集成后，由拥有 map 分支的任务继续第 4 步。

4. 记录解决结果：把答案发布为一条 **resolution comment**，**关闭** issue，并在 map 的 Decisions so far 中追加一个 context pointer。

   resolution comment 链接这张 ticket 实际形成的 prototype、research 或 evidence；没有资产时只记录答案。修改 map 前重新读取最新正文，修改后再次读取，确认本次 context pointer 存在，并保留其他 session 的并发修改。

5. 添加 newly-surfaced ticket，采用 **create-then-wire**：先创建，再连接 blocking edge。把这次答案已经变得可以精确表述的 fog 转成 ticket；每块转成 ticket 的 fog 都要从 **Not yet specified** 删除，使它只存在于新 ticket 中。如果答案表明某张 ticket 位于 destination 之外，无论是当前 ticket 还是另一张 ticket，都把它 **rule out of scope**，不要把它当作路线上的决定来解决。如果这项决定使 map 的其他部分失效，更新或删除对应 ticket。

   新 ticket 原样继承 map 的 `产物目录`，取得 tracker 编号后回填自己的 `issue-<编号>`，然后第二遍 wire blocking edge。rule out of scope 时，在 Out of scope 留下概要、越界理由和 ticket 链接；明确否决 enhancement 的 `.out-of-scope/` 理由已经在第 3 步随结果分支集成。

用户可以并行处理没有阻塞的 ticket。因此，要预期其他 session 会同时编辑 tracker。

完成第 5 步后重新运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`。frontier 为空时，再运行 `mmw issue children <map 编号>`。当前 ticket 的处理到这里完成；按照文末“下一步”处理查询结果，不继续 claim 新 ticket。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 当前 ticket 已记录并关闭，frontier 仍有 ticket | **停**：报告本次决定和当前 frontier；其他 session claim 下一张 ticket |
| 当前 ticket 已记录并关闭，而且没有带 `wayfinder:` 标签的 open decision ticket | **移交**：拥有 map 分支的任务读取 [closing.md](closing.md) |
| 当前 ticket 已记录并关闭，frontier 为空，但仍有已被 claim 或仍被 blocking 的 open decision ticket | **停**：报告这些 ticket 的当前状态，map 保持 open |

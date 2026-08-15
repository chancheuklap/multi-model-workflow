# 沿 map 推进

用户带着一张 map 调用，可以使用 URL 或编号。ticket 是可选项；用户没有指定 ticket 时，由你选择下一个决定，不要求用户选择。这个会话只解决一张 decision ticket。

1. 加载 **map**，也就是低分辨率视图，不加载每张 ticket 的正文。

   运行 `gh issue view <map 编号>` 读取 map 正文，记下 map 标题、`## 分支` 和 Notes 点名的技能。再运行 `mmw issue frontier <map 编号> --label-prefix wayfinder:`。

   用户指定 ticket 时，运行 `mmw issue children <map 编号>`，在输出中确认这张 ticket 是当前 map 的子 issue，带 `wayfinder:` 标签，状态是 open，没有 assignee，而且被阻塞数量为零。五项全部成立时继续第 2 步；任何一项不成立时，报告实际状态并停止，不 claim 或解决这张 ticket。

   用户没有指定 ticket 时，frontier 至少有一张 ticket 就继续第 2 步。frontier 为空时，立即运行 `mmw issue children <map 编号>`：

   | 查询结果 | 处理 |
   | --- | --- |
   | 仍有带 `wayfinder:` 标签的 open decision ticket | 报告这些 ticket 已经被别人认领或仍被挡着，map 保持 open，然后停止；不要进入第 2 步 |
   | 没有带 `wayfinder:` 标签的 open decision ticket | 读取 [closing.md](closing.md)；不要进入第 2 步 |

2. 选择 ticket。用户点名一张时使用那一张；用户没有点名时，按顺序取得第一张 frontier ticket。

   任务 slug 由两段拼成：map 分支 slug（读 `## 分支`，去掉宿主命名空间）+ 这张 Question 的英文三四个词。规则同 `/mmw-start` 第 2 步。宿主对任务分支有固定命名空间时加在前面。父分支是 map 分支，起点是它当前已提交的 HEAD——先运行 `git rev-parse <map 分支>` 记下它，交回结果时要用。

   写产物、列产物和交给下游时都传 `--name <map 分支 slug>`，不要用 ticket 分支名。取值读 map 正文的 `## 分支`。

   运行 `git symbolic-ref --quiet --short HEAD`。当前分支等于 map 正文 `## 分支` 的值时：不要 claim，不要进入第 3 步。停下，请用户为这张 ticket 另开一棵工作树再开会话。不要占用 map 分支所在的树。

   **claim 它**：开始任何工作前先把 ticket 指派给自己。

   使用 `mmw issue claim <编号>` claim。失败说明另一个 session 已经 claim 这张 ticket，改取下一张。所有 frontier ticket 都 claim 失败时，报告这些 ticket 已被其他 session 认领，然后停止；不要进入第 3 步。

   claim 成功后，当前没有分支时先确认 HEAD 等于第 2 步记下的 map 分支 HEAD。不等就停。

   先确认当前仓库位置。判定从上到下，命中一行就停。

| 情况 | 怎么判断 | 你做什么 |
| --- | --- | --- |
| 不在 git 仓库里 | `git rev-parse --is-inside-work-tree` 失败 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新判断 |
| 在主检出里 | `git rev-parse --path-format=absolute --git-dir` 等于 `--git-common-dir` | 停下，请用户用当前宿主开一棵工作树再开会话 |
| 没有分支 | `git symbolic-ref --quiet --short HEAD` 为空 | 按上文已定的任务分支名运行 `git switch -c <完整任务分支名>` |
| 已有任务分支 | 上面都不成立 | 用当前分支 |


   当前分支不是这张 ticket 的预期分支时停，报告当前分支和预期 slug。不要进入第 3 步。
   工作区不干净、或者分支已经存在于别处时，停下来。

3. 解决 ticket。先运行 `gh issue view <编号>` 取得这张 ticket 的完整正文，它的 `Question` 一节就是要解决的问题。随后运行 `mmw artifact list --name <map 分支 slug> --map <map 编号>`。从候选中选出与 Question 相关的材料，补进自己的 `## 必读材料声明`，并保留已有条目。

   开工前按 [SKILL.md](SKILL.md) 的「解析必读材料声明」读取全部条目。

   需要更多背景时，按需取得相关或已关闭 ticket 的完整正文，不要一次把所有 ticket 都读进来。调用 map `## Notes` 区块点名的技能。不确定用什么时，使用 `/mmw-grilling`；它在同一场讨论中应用 `/mmw-domain-modeling`。

   需要资产路径时：

   | 资产 | 命令 |
   | --- | --- |
   | prototype | `mmw artifact path prototype --name <map 分支 slug> --issue <编号> --sub <类别内细分>` |
   | research | `mmw artifact path research --name <map 分支 slug> --issue <编号> --sub <主题>` |
   | 过程材料 | `mmw artifact path scratch --name <map 分支 slug> --issue <编号> --sub evidence` |

   按 [SKILL.md](SKILL.md) 的“Ticket 类型”一节处理。四类交接都传五项：Question、必读材料声明中的全部仓库产物引用、全部结论评论 issue 编号、名字段（map 分支 slug）和范围段 `issue-<编号>`。下游自己用 `mmw artifact path` 解析仓库产物引用；写产物时必须带 `--name <map 分支 slug>`。

   | 标签 | MMW 接口 |
   | --- | --- |
   | `wayfinder:grilling` | 把五项交给 `/mmw-grilling` |
   | `wayfinder:prototype` | 把五项交给 `/mmw-prototype`；它需要的 prototype 产物与 scratch 路径由传入的名字段和范围段解析 |
   | `wayfinder:research` | 把五项交给 `/mmw-research`；它需要的 research 产物与 scratch 路径由传入的名字段和范围段解析。这张 ticket 就是用户对这次调查的批准，research 直接保存，不再询问。这个问题只有把外部系统真跑起来才能答时，`/mmw-research` 会自己升级成实测；实测里要动真实凭证、生产环境或者会花钱的操作，仍然要停下来找用户点头 |
   | `wayfinder:task` | 把五项交给完成任务的一方。agent 能完成时直接完成；必须由用户完成的多步流程调用 `/wizard` |

   `wayfinder:task` 必须等待用户操作时，给出精确操作并停止本步骤。用户返回后继续处理同一张 ticket；不要提前执行第 4 步。

   HITL ticket 只能由用户与 agent 共同解决。`wayfinder:grilling` 已经通过 `/mmw-grilling` 在同一段对话中应用 `/mmw-domain-modeling`，并完成本次讨论需要的领域模型修改；不要为同一项结果重复调用 `/mmw-domain-modeling`。

   `wayfinder:prototype`、`wayfinder:research` 或 `wayfinder:task` 得到结果后，看这次结果里有没有需要长期留下来的领域术语、bounded context、bounded context 之间的关系，或者一项值得记进 ADR 的决定。有其中任何一项时调用 `/mmw-domain-modeling`，由它判断和落笔。

   这次要写 ADR 时，文件先命名成 `draft-<这张 ticket 的编号>-<英文短名>.md`，不要现在去取正式编号：别的会话可能正在同时写另一份 ADR，两边会拿到同一个号。正式编号在结果合回 map 分支之后统一分配。

   这次的答案明确否掉了一个功能需求时，把否掉它的理由写进仓库根目录的 `.out-of-scope/`，一个概念一份文件，格式见 [`../mmw-triage/OUT-OF-SCOPE.md`](../mmw-triage/OUT-OF-SCOPE.md)。这个文件要在更新 tracker 之前写好。

   过程材料的清理由实际创建它们的下游技能负责，你不用管。你这个会话写下的持久内容，全部提交在这条任务分支上。

4. 记录这次的答案。三件事：

   1. 运行 `mmw artifact path scratch --name <map 分支 slug> --issue <编号> --sub outbox/answer.md`。输出文件第一行写 `<!-- mmw:conclusion -->`。随后依次写 `## 答案`、`## 产物引用` 和 `## 材料使用记录`。

      `## 答案` 完整承载这次得到的结论。这条评论是这次工作留在 tracker 上的唯一记录，读它的会话没有这次的对话。判据：这次交回的每一项结论，在这一节里各找得到一条，理由和数字随条目一起写出来。

      `wayfinder:grilling` 另有一条：把 `/mmw-grilling` 交回的那份共同理解记录的 `## 共同理解` 整段转录进来，标题层级照原样。

      仓库产物按「必读材料声明」的写法逐行写；没有仓库产物时写 `无`。材料使用记录逐条覆盖 `## 必读材料声明` 中的每项材料，写明用上了没有；未用时写出理由。然后评论：`gh issue comment <编号> --body-file <上一步输出文件>`。
   2. 关闭这张 ticket：`gh issue close <编号>`。
   3. 在 map 的 `Decisions so far` 追加一行：`mmw issue append <map 编号> --section "Decisions so far" --line "<ticket 名称的链接与一句话概要>"`。

5. 这次的答案会让一部分原本说不清楚的问题变得说得清楚。每一个这样的问题，先跑 `mmw issue children <map 编号>` 看 map 上是不是已经有人在问它；标题看着像的，用 `gh issue view <编号>` 读它的 `Question` 确认。

   | 这个问题 | 怎么处置 |
   | --- | --- |
   | 已经有一张 open decision ticket 在问它 | 把这次说清楚的部分发成那张 ticket 上的一条评论。不另建一张，也不 claim 它——它仍然由认领它的会话去解 |
   | map 上没有 | 建成新的 decision ticket。正文写 `## Question` 和 `## 必读材料声明`。后者列当时已经知道的相关仓库产物引用和结论评论 issue 编号；没有材料时写 `无`。新 ticket 先全部建出来，取得编号之后再连阻塞关系（issue 要先有编号才能互相引用） |

   两条路都一样：处置掉的那块内容要从 `Not yet specified` 里删掉，让它只存在于对应的那张 ticket。

   如果这次的答案说明某张 ticket 其实越过了 destination——不管是当前这张还是别的哪张——就关掉它，在 `Out of scope` 留一行：概要、为什么越界、以及指向这张已关闭 ticket 的链接。不要把它当成路线上的一个决定去解。如果这次的决定让 map 的其他部分失效了，同步更新或删掉对应 ticket。

6. 提交，然后把结果交回去。

   提交这条任务分支上还没提交的全部持久内容。这一轮没有动过仓库文件时，不要制造一个空提交。

   然后把三个值追加成这张 ticket 上的一条评论。第一行写 `<!-- mmw:handback -->`。在 `## 交回` 下分别写任务分支名、`git rev-parse HEAD` 的输出和第 2 步记下的基点 SHA。ticket 已经关闭也照发——这条评论是这三个值的持久记录。

   最后停下来，向用户报告这次的决定和这三个值。集成认分支不认会话：第 7 节由任何一个在 map 分支上的会话执行——建 map 的会话还在就是它，不在就用 `/mmw-start` 带 map 编号恢复 map 的任务上下文再做。

   到这里你解这张 ticket 的工作就结束了。第 7 节在 map 分支上做，你不执行。

7. **只有当前分支是 map 分支时才做这一节。** 拿到一张 decision ticket 的分支名、HEAD SHA 和基点 SHA 之后——现场没有交回报告时，从以 `<!-- mmw:handback -->` 开头的评论的 `## 交回` 取得这三个值：

   先运行 `mmw result verify <结果分支> <HEAD SHA> <基点 SHA>`，三个值都用交回来的那份。命令通过后，从输出取得结果 worktree 路径。这一步不合入结果分支。

   读交回的报告，并在这条路径里读 diff，确认两件事：ticket 上那条答案评论和 diff 说的是同一件事；这次改动的领域文档和 ADR 草稿只涉及这张 ticket 的决定，没有顺手改别的。两件都成立才合并：

   本技能规定的验收全部通过后，运行 `mmw result integrate <结果分支> <HEAD SHA> <基点 SHA>`。命令成功后，结果提交才算进入当前任务分支。

   合并之后，把这次带回来的 `draft-<编号>-<短名>.md` 逐个换成正式编号：每份跑一次 `mmw domain adr-next` 取一个号，按 `<编号>-<短名>.md` 重命名，然后提交。这一轮没有 ADR 草稿就跳过。

   最后跑 `mmw issue frontier <map 编号> --label-prefix wayfinder:`。frontier 上还有 ticket 时，报告这次的决定，以及 frontier 上还剩哪几张（用名称，不用编号）；下一张由另一个会话认领，不要接着认领。frontier 为空时再跑 `mmw issue children <map 编号>`：已经没有带 `wayfinder:` 标签的 open ticket 时，读取 [closing.md](closing.md)；还有 open ticket 已被别人认领或仍被挡着时，报告这些 ticket 现在是什么状态，map 保持 open。

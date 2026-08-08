---
name: mmw-wayfinder
description: 把一件超出一次 agent session、而且从这里到终点的路线还看不清楚的大工作，组织成 issue tracker 上由 decision ticket 组成的共享 map。用于建这张 map、认领并解决其中一张 decision ticket，或者所有 ticket 都解完之后检查路线是否清楚并交给下游。
argument-hint: "[map 编号、ticket 编号，或者要做的事]"
---

本次输入：`$ARGUMENTS`

一个松散的想法出现了。它太大，一次 agent session 容纳不下，而且被 fog 包围：从这里到 **destination** 的路线还看不见。Wayfinding 负责找到这条路线，不是径直冲向 destination。本技能把这条路线 chart 成仓库 issue tracker 上的一张**共享 map**，再逐张处理它的 **decision ticket**。Decision ticket 承载的问题在解决后得到一个决定，不是等待执行的构建切片。每次处理一张，直到路线清楚。

destination 随 effort 而异。给它命名是 charting 的第一个动作，因为它会塑造后面的每一张 ticket。destination 可能是一份要交出去并继续迭代的 spec，可能是开始规划前必须锁定的一个决定，也可能是一次就地完成的改动，例如数据结构迁移。map 与领域无关；工程工作、课程内容或其他符合这种形态的工作都可以使用。

## 规划，不执行

Wayfinder 默认负责**规划**。每张 ticket 解决一个决定；当路线清楚时，map 就完成了：在有人开始执行那件事之前，已经没有决定尚待解决。想要直接开始执行，通常说明你已经抵达 map 的边界，现在应该交给下游。某项 effort 可以在 **Notes** 中覆盖这项默认行为，把执行也带进 map。没有这项覆盖时，产出决定，不产出交付物。

## 用名称称呼

每张 map 和 ticket 都是一张 issue，因此都有一个**名称**，也就是它的标题。在所有给人阅读的内容中，包括叙述和 map 的 Decisions so far，都使用名称称呼它；绝不使用裸的 id、编号或 slug。一整面 `#42, #43, #44` 无法阅读，名称则能让人一眼看懂。id 和 URL 不会消失；名称包裹对应链接。id 和 URL 位于名称内部，绝不代替名称单独出现。

## Map

map 是当前仓库 issue tracker 上的一张 issue，带 `wayfinder:map` 标签。这项 effort 的状态以它为准。map 的 ticket 是它的子 issue。

map 是**索引**，不是存储库。它列出已经形成的决定，并指向保存细节的 ticket。一个决定只存在于一个地方，也就是它自己的 ticket。因此，map 绝不复述决定，只写一句概要并提供链接。

### map 正文

map 正文是整个 map 的低分辨率视图。每个 session 加载一次。open ticket **不**列在正文中；它们是 open 的子 issue，通过查询取得。

```markdown
## Destination

<抵达这张 map 的终点时是什么状态；这项 effort 正在寻找的 spec、决定或改动。一到两行；每个 session 选择 ticket 前都先用它校准方向。>

## 产物目录

<这项 effort 的 prototype、research 和过程材料共用的一个目录名。建 map 时定下，之后不再改。>

## Notes

<领域；每个 session 都应该查阅的技能；这项 effort 长期生效的偏好>

## Decisions so far

<!-- 索引。每张已关闭的 ticket 一行；内容足以判断相关性，然后沿链接 zoom 到 ticket 保存的细节。 -->

- [<已关闭的 ticket 名称>](链接) —— <答案的一句话概要>

## Not yet specified

<!-- 见“Fog of war”：范围内、当前还无法建立 ticket 的 fog；它会随着 frontier 推进而转成 ticket。 -->

## Out of scope

<!-- 见“Out of scope”：已经判定越过 destination 的工作；关闭，并且永远不会转成 ticket。 -->
```

### Tickets

每张 ticket 都是 map 的一个**子 issue**；tracker 的 issue id 就是它的身份。ticket 正文承载问题，必须能在一次 agent session 内解决：

```markdown
## Question

<这张 ticket 要解决的决定或调查问题>
```

ticket 正文只有 `Question` 这一节，不写别的。解决 ticket 时需要的 `产物目录` 从 map 正文读，需要的子目录就是 `issue-` 加上这张 ticket 自己的编号。

每张 ticket 都带一个 `wayfinder:<type>` 标签。type 是 `research`、`prototype`、`grilling` 或 `task` 中的一个，见下方“Ticket 类型”一节。

一个 session 通过把 ticket 指派给推动这张 map 的开发者来 **claim** 它。claim 必须发生在任何工作之前，使并发 session 能够跳过这张 ticket。assignee 就是 claim：open 且没有 assignee 的 ticket 是 unclaimed。

blocking 使用 tracker 的**原生依赖关系**。这一点很重要，因为 tracker 会在自己的 UI 中把 frontier **可视化**，人不需要打开 map 就能看见当前可以处理的内容。一张 ticket 的所有 blocker 都已关闭时，它才是 unblocked。**frontier** 是 open、unblocked、unclaimed 的子 issue，也就是已知区域的边缘。

答案不属于 ticket 正文。答案在 ticket 解决时记录，见 [walking.md](walking.md) 的“沿 map 推进”流程。解决 ticket 期间建立的资产从 issue 链接，不粘贴进正文。

## 并发会话

一张 map 通常由多个会话分头推进：一个会话建 map，其余会话各解一张 decision ticket。用户可以并行处理没有阻塞的 ticket，所以要预期其他 session 同时在编辑 tracker 和仓库。以下四条约束对两个入口都适用。

- **一个 session 绝不解决超过一张 decision ticket。** 唯一例外是 charting 会话可以为刚建好的多张 `wayfinder:research` ticket 并行派 research。
- **claim 在动手之前。** 把 ticket 指派给推动这张 map 的开发者就是 claim。claim 完成之前不做任何工作。
- **改 map 正文之前重新读取最新正文。** 编辑 issue 正文是整体替换。写完再读一次，确认本次那一行在；不在就重做一遍。
- **每个 session 只在自己的任务 worktree 里写文件。** 建 map 的会话拥有 map 分支；每张 decision ticket 用一条从 map 分支派生的任务分支，解决期间写下的领域文档、ADR 和资产都提交在这条任务分支上，再交回给拥有 map 分支的那个会话合并。这一条不能省：两个会话同时改同一份领域文档时，各自一个 worktree 会让冲突在合并时暴露出来，而共用一个工作目录会让后写的那个直接覆盖先写的，谁都不会发现。

## Ticket 类型

每张 ticket 要么是 **HITL**，即 human in the loop，由一个亲自表达意见的人与 agent 共同处理；要么是 **AFK**，由 agent 独立推动。HITL ticket 只能通过这场实时交流解决；agent 绝不代替人的一方回答。一个 grilling agent 自己回答自己的问题，就已经破坏了这项合同。

- **Research**（AFK）：阅读文档、第三方 API 或本地知识库等资源，找出某项决定正在等待的事实。由 `/mmw-research` 解决。需要当前工作目录之外的知识时使用。
- **Prototype**（HITL）：制作一个具体的可运行资产，提高讨论的保真度。由 `/mmw-prototype` 解决。初版可以粗糙；用户持续走查并迭代，把这个想法磨清楚。想法磨清楚之后，prototype 里承载它的脚本、接口合同、状态模型和界面就是下游可以直接参考或复用的内容。把 prototype 作为资产链接到 ticket。关键问题是“它应该长什么样”或“它应该怎样表现”，而且只靠讨论无法决定时使用。
- **Grilling**（HITL）：对话。默认情况。由 `/mmw-grilling` 解决；它在同一场讨论中应用 `/mmw-domain-modeling`。
- **Task**（HITL 或 AFK）：形成一个**决定**之前必须完成的手工工作。此时没有需要讨论的决定，也不需要 prototype 或 research，但讨论必须等这项工作完成才能继续。例如注册一个服务以便评估它的 API、开通访问权限，或者移动数据以便看清数据形状。这是唯一一种执行操作而不形成决定的类型。它通过解除一个决定的 blocker 取得存在理由，不通过交付 destination 取得存在理由。agent 能独立推动时，由 agent 独立完成（AFK）；否则，向用户提供精确清单（HITL），需要用户按顺序做很多步时由 `/wizard` 生成这份清单。工作完成时，ticket 才算解决。答案记录完成了什么，以及后续 ticket 依赖的结果事实，例如凭证位置、新 URL 和行数。

## Fog of war

map 是**刻意**不完整的：不要 chart 当前还看不见的内容。open ticket 之外是 **fog of war**。那里是一些决定和调查问题的模糊轮廓；你知道它们将会出现，却还无法确定具体问题，因为它们依赖仍然 open 的问题。解决一张 ticket 会驱散前方的 fog，把此时已经能够精确表述的内容转成新的 ticket。每次处理一张，直到通往 destination 的路线清楚，而且没有尚待解决的 ticket。

map 的 **Not yet specified** 一节记录这片模糊视野：怀疑存在的问题，以及以后需要回看的区域。它是朝向 destination、尚未发现的 frontier。这里的所有内容都在范围内，只是还不够清晰，无法建立 ticket。按照当前视野允许的程度书写，可以很松，也可以很完整。它同时是给协作者看的路标，让协作者知道这项 effort 正朝哪里发展。

**Fog 还是 ticket？** 判据是现在能否精确陈述问题，**不是**现在能否回答问题。

- **建立 ticket 的情况**：问题已经足够清晰。即使它仍被阻塞，而且当前无法采取行动，也要建立 ticket。
- **写入 Not yet specified 的情况**：当前还无法把问题表达得足够清晰。不要提前把 fog 切成 ticket 大小的部分；fog 比 ticket 更粗。当 frontier 抵达那里时，一块 fog 可能转成多张 ticket，也可能一张都不产生。

**Not yet specified** 不包含已经决定的内容（Decisions so far）、已经存在的 open ticket，以及范围外内容（见下一节）。

## Out of scope

fog 只朝 destination 聚集。destination 固定范围，所以越过 destination 的工作属于 **out of scope**。它不是 fog，也不属于 **Not yet specified**。map 使用独立的 **Out of scope** 一节记录已经明确排除在当前 effort 之外的工作。范围决定一项工作是否进入这里，清晰度不决定。

out-of-scope 工作永远不会转成 ticket；frontier 在 destination 停止。只有 destination 被 redraw 时，这项工作才会回来，而且它会成为一项新的 effort，不是恢复当前 effort。

rule out of scope 是一项范围决定，不是路线上的一步。如果一张已经存在的 ticket 后来被证明位于 destination 之外，例如 charting 时错误地把它纳入范围，或者某次解决结果暴露了这个事实，就**关闭它**。关闭的 ticket 会明确地离开 frontier。随后在 **Out of scope** 中留下一行：概要、越界理由，以及指向已关闭 ticket 的链接。它不进入 **Decisions so far**；后者只记录实际走过的路线，而范围边界不是路线上的一步。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 用户带着一个松散的想法调用 | **自己继续**：读取 [charting.md](charting.md)，执行 Chart the map |
| 用户带着一张 map 调用，可以使用 URL 或编号；ticket 可以指定，也可以不指定 | **自己继续**：读取 [walking.md](walking.md)，沿 map 推进 |

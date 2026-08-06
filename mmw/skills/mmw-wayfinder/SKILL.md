---
name: mmw-wayfinder
description: Wayfinding：把同时超出一次 agent session 且存在 fog of war 的 effort 组织成共享 map。用于新建 map、认领 decision ticket、frontier 为空时收尾，或用户显式标记 big。
argument-hint: "[map 编号，或者要做的事]"
---

本次输入：`$ARGUMENTS`

一个还很松的想法来了，超出一次 agent session 能容纳的范围，而且路上罩着 fog of war：从这里到 **destination** 的路线看不见。本技能要做的是找到路线，不是直接朝 destination 推进。它把路线画成 issue tracker 上一张**共享的 map**，map 底下挂 **decision ticket**。每张 decision ticket 解出一个决定，不是一次构建里的切片。各会话一次解决一张，直到路线清楚。

destination 每个 effort 各不相同。给它命名是画 map 的第一个动作：它固定范围，也塑造后面每一张 ticket。它可能是一份要交出去继续做的 spec，可能是开始做计划之前必须锁死的一个决定，也可能是一次就地完成的改动，比如一次数据结构迁移。

下表准备移交下一技能时，先读 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按顺序判断是否留在当前会话。自己继续和因 blocker 停下不触发阶段边界判断。

## 下一步

三个入口都先读 [map-anatomy.md](map-anatomy.md)：map 和 ticket 长什么样、每张 ticket 是 HITL 还是 AFK、四个 `wayfinder:<类型>` 标签各自什么时候打、怎么认领、阻塞关系怎么表达，全在那里。

| 情况 | 下一步 |
| --- | --- |
| 用户带来一个还很松的想法，还没有 map | **自己继续**：读 [drawing.md](drawing.md)，建这张 map |
| 用户报了一张 map 的编号或链接 | **自己继续**：读 [walking.md](walking.md)，认领一张 decision ticket |
| 那张 map 的 frontier 上一张 ticket 都不剩 | **自己继续**：读 [closing.md](closing.md)，收尾 |

看不出是哪一个，就按他给的编号查一次 frontier：frontier 上还有 ticket 就走 walking.md，空了就走 closing.md。

## 只产出决定，不产出交付物

每张 ticket 解掉一个决定，路清楚了这张 map 就完成——在有人真去实现之前，没有什么还需要决定。想直接动手实现，通常说明 map 已经走到边界，该收尾了。某个 effort 要破例，在 map 的 `Notes` 一节里写明；没写就只产出决定。

## 用名字称呼

每一张 map 和 ticket 都是一张 issue，它有一个名字，就是它的标题。凡是人要读的地方——你的叙述、map 的 `Decisions so far`——都用这个名字称呼它，不要用裸的编号。编号包在名字外面的那个链接里。

## 几个会话同时跑这张 map

一张 map 通常由好几个会话分头做：一个会话建 map，其余会话各认领一张 decision ticket。这带来四条硬约束，三个入口都适用。

**一个会话只解一张 decision ticket。** 回填、提交和交回 map 任务后停止。新出现的 frontier 由另一个会话认领。唯一例外是建图会话可以为刚创建的多张 `wayfinder:research` ticket 并行派调查者；每个调查者仍只解一张 ticket。

**认领在动手之前。** 把 ticket 指派给自己就是认领。指派完成之前不要做任何事。

**改 map 正文之前先重新拉一次最新的。** GitHub 编辑 issue 正文是整体替换。写完再读一次，确认自己那行在；不在就重来一遍。

**每个任务只使用自己的 worktree。** map 任务拥有 map 分支；每张 decision ticket 和每份 spec 使用从 map 分支派生的独立任务分支。任务之间只交回分支名、HEAD SHA、基点 SHA 和报告，由拥有目标分支的任务验证并集成。主 agent 不切换到另一个任务的工作目录。

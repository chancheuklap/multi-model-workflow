---
name: mmw-wayfinder
description: 把一个超出一次 agent session、而且路线还看不清的 effort 规划成 issue tracker 上一张共享的 map。用户带来一个很大、很松、暂时看不到边界的想法时用它；报出一张已有 map 的编号、要认领一张 decision ticket 时也用它。
argument-hint: "[map 编号，或者要做的事]"
---

本次输入：`$ARGUMENTS`

本技能处理同时满足两个条件的 effort：

1. 超出一次 agent session。
2. 从当前位置到 **destination** 的路线仍有 fog of war。

产物是 issue tracker 上的共享 **map**。map 下的每张 **decision ticket** 解决一个决定，不是构建切片。每个会话解决一张，直到路线清楚。

本技能负责找到路线，不直接实现 destination。

destination 是画 map 的第一项决定。它固定 effort 的范围，并决定后续 ticket。destination 可以是 spec、计划前必须确定的决定，或数据结构迁移等就地改动。

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

三个入口都遵守以下并发合同：

- **一个会话只解一张 decision ticket。** 回填、提交并交回 map 任务后停止。新出现的 frontier 由另一个会话认领。建图会话可以并行派发多张 `wayfinder:research` ticket；每个调查者仍只解一张。
- **认领在动手之前。** 把 ticket 指派给自己就是认领。
- **编辑 map 前后都重新读取最新正文。** 写完确认自己的内容仍在。
- **每个任务只使用自己的 worktree。** map、每张 decision ticket 和每份 spec 各用自己的任务分支与 worktree。任务之间只交回分支名、HEAD SHA、基点 SHA 和报告。拥有目标分支的任务负责验证并集成。主 agent 不切换到其他任务的工作目录。

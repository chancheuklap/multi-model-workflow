---
name: mmw-wayfinder
description: 把一个大到要拆成好几份 spec 的 effort 规划成 issue tracker 上一张共享的 map。用户带来一个很大、很松、暂时看不到边界的想法时用它；报出一张已有 map 的编号、要认领一条链接着往下走时也用它。
argument-hint: "[map 编号，或者要做的事]"
---

本次输入：`$ARGUMENTS`

一个还很松的想法来了，大到要拆成好几份 spec 才做得完，而且路上罩着 fog of war：从这里到 **destination** 的路看不见。本技能要做的是找到这条路，不是直接朝 destination 推进。它把这条路画成 issue tracker 上一张**共享的 map**，map 底下挂 **decision ticket**——每一张解出来是一个决定，不是一次构建里的切片——然后一条链一条链地解，直到路清楚。

destination 每个 effort 各不相同。给它命名是画 map 的第一个动作：它固定范围，也塑造后面每一张 ticket。它可能是一份要交出去继续做的 spec，可能是开始做计划之前必须锁死的一个决定，也可能是一次就地完成的改动，比如一次数据结构迁移。

## 下一步

三个入口都先读 [map-anatomy.md](map-anatomy.md)：map 和 ticket 长什么样、每张 ticket 是 HITL 还是 AFK、四个 `wayfinder:<类型>` 标签各自什么时候打、怎么认领、阻塞关系怎么表达，全在那里。

| 情况 | 下一步 |
| --- | --- |
| 用户带来一个还很松的想法，还没有 map | **自己继续**：读 [drawing.md](drawing.md)，建这张 map |
| 用户报了一张 map 的编号或链接 | **自己继续**：读 [walking.md](walking.md)，认领一条链 |
| 那张 map 的 frontier 上一张 ticket 都不剩 | **自己继续**：读 [closing.md](closing.md)，收尾 |

看不出是哪一个，就按他给的编号查一次 frontier：frontier 上还有 ticket 就走 walking.md，空了就走 closing.md。

## 只产出决定，不产出交付物

每张 ticket 解掉一个决定，路清楚了这张 map 就完成——在有人真去实现之前，没有什么还需要决定。想直接动手实现，通常说明 map 已经走到边界，该收尾了。某个 effort 要破例，在 map 的 `Notes` 一节里写明；没写就只产出决定。

## 用名字称呼

每一张 map 和 ticket 都是一张 issue，它有一个名字，就是它的标题。凡是人要读的地方——你的叙述、map 的 `Decisions so far`——都用这个名字称呼它，不要用裸的编号。编号包在名字外面的那个链接里。

## 几个会话同时跑这张 map

一张 map 通常由好几个会话分头做：一个会话建 map，其余的各认领一条链。这带来四条硬约束，三个入口都适用。

**一个会话只解一条链。** 一条链在两种情况下到头，任一成立就停下来交回用户，让他另开一个会话认领下一条：解开的这张 ticket 没解锁出任何一张归你的（阻塞没清完，或者已经被别的会话认领走了），或者解锁出来的那张是 HITL 的。判法和理由在 [walking.md](walking.md) 第 5 步。

**认领在动手之前。** 把 ticket 指派给自己就是认领。指派完成之前不要做任何事。

**改 map 正文之前先重新拉一次最新的。** GitHub 编辑 issue 正文是整体替换。写完再读一次，确认自己那行在；不在就重来一遍。

**一个会话只进一次 worktree。** 认领一条链和收尾这两个入口，会话先在主仓库里读 map（`gh issue view`）和 map 分支上的文件（`git show <map 分支>:<路径>`），选定这次要做什么，再建自己那棵 worktree 并进去。建这张 map 那个入口没有 map 可读，`/mmw-start` 已经替它建好 map 的 worktree 并进去了，它不再建第二棵。从一棵 worktree 直接跳到另一棵会被拒绝；需要动别的 worktree 时用 `git -C <那棵 worktree 的路径> <git 命令>`，不切会话目录。

# 建这张 map

用户带着一个还很松的想法来。这个会话只做一件事：把 map 建出来。**它一张 ticket 都不亲手解。**

前置：`/mmw-start` 已经建立并绑定 map 任务 worktree，第一个提交记录用户原话。`mmw task state` 不以 `bound` 开头时，回 `/mmw-start` 完成绑定。

## 1. 给 destination 命名

跑一场 `/mmw-grilling`，把这张 map 要找的东西定死：那份 spec、那个决定或那次改动。它固定范围，所以第一个定下来。

完成的标志：一两行话说得出走到尽头是什么样子，而且用户认了这句话。

## 2. 广度优先横扫

再 grill 一次，这次**广度优先**：在整个空间上铺开，不在任何一条线上扎深。要找出来的是还开着的决定，以及现在就能迈的第一步。

**这一步找不出任何 fog of war，就不需要 map**——通往 destination 的路已经清楚，一份 spec 就说得完。处置见本文「下一步」一节。

## 3. 建 map

打 `wayfinder:map` 标签。`Destination` 和 `Notes` 填好，`Decisions so far` 留空，横扫出来的 fog of war 写进 `Not yet specified`。

## 4. 建第一批 ticket，再连阻塞关系

现在就能精确表述的问题，各建一张 decision ticket，各带一个 `wayfinder:<类型>` 标签。**四个标签各自什么时候打，见 [map-anatomy.md](map-anatomy.md) 的「四个类型」一节**，不要凭感觉打。还说不清楚的全部留在 `Not yet specified`。

建的时候用 `mmw issue create --title <标题> --body-file <文件> --parent <map 编号> --label wayfinder:<类型>`，它一次做完建 issue、挂到 map 底下、打标签三件事，输出新 issue 的编号。

然后用**第二遍**把阻塞关系连上：`mmw issue link <被挡的> --blocked-by <挡它的>`。要分两遍是因为 issue 要先有编号才能互相引用。连完边，这批 ticket 自然分成 frontier 和被阻塞的两类，用 `mmw issue frontier <map 编号>` 看。

## 5. 派调查 subagent，收报告

刚建的每一张 `wayfinder:research` ticket，各派一个 subagent 去查，按 `/mmw-research`。它们只查事实、互不依赖，可以并行。

**报告收齐、验证完、写进 ticket 评论，这一步才算完。** 验证过的事实写进对应 ticket 的评论，没查清的另起一节列出来。查清了的那张 ticket 当场关掉，并往 map 的 `Decisions so far` 追加一行。

## 6. 提交

把这场谈话期间落下的东西提交进 map 分支：新写进相关 leaf 的术语、按 `/mmw-domain-modeling` 三个条件写下的 ADR。不要留未提交的改动。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 2 步横扫下来，没有说不清楚的部分 | **移交**：调起 `/mmw-to-spec`，把用户原话原样传过去 |
| map 建好，第一批 ticket 建好，research 报告已经写进 ticket 评论，改动已提交 | **停**：报 map 已经建好、frontier 上有几张可以认领，并说明每张 decision ticket 使用一个新会话 |

停下来时报三件事：这张 map 的 destination 是什么、frontier 上现在有哪几张 ticket（用名字，不用编号）、哪些 ticket 可以并行认领。

---
date: 2026-09-10
amends: [0009, 0018]
---

# 票的状态是它的事件折叠出来的：评论首行不再是协议，谁在跑这张票写在票上

一张票走到哪一步、谁占着它，不存在任何地方，是算出来的：这张票下每一条评论按 comment id 顺序读，其中的事件从空白全量重放一遍，这就是折叠（fold）。每一条协议评论都是一个事件：首行和其后的正文给人读，措辞可以随时改；末尾一个在 GitHub 上看不见的 `<!-- mmw {...} -->` 块是程序唯一读的东西，事件名是 `subject.verb`，名字里不带值。`dispatch.sh start` 把会话写进 `worker.started` / `reviewer.started` / `verifier.started` 的载荷（session 与 runner 成对，另有 host、model、effort、grade、工作树绝对路径、分支、base commit），之后每一条命令都从这里找会话。一张票从 `ticket.claimed` 或某个 `*.started` 起被占着（held），直到 `ticket.landed`、`ticket.returned`、`ticket.released`、`spec.suspended`，或那一对 (runner, session) 的 `worker.retracted` / `worker.lost` / `worker.replaced`；`ticket.passed` 不结束占用，label 永远不遮住占用。frontier 解锁被阻塞的票看阻塞者的 `ticket.landed`，不看它关没关。一条读不懂的事件块让所有据折叠做决定的命令拒绝，不当作没有。词汇、格式与折叠规则由 spec #315 定，代码在 `mmw-v2/skills/verify-ticket/scripts/events.py`。

## 要修的是什么

- `status.py` 从评论正文反推 `phase`：判据散在读的人手里，换个读法就换个结论，加一个阶段就要改推断逻辑。
- 评论首行是协议，而且有五种形状：`ALL MET`、`NOT_READY:`、`HANDOFF REQUIRED:`、带一个尾空格的 `REVIEW `、把值编进名字的 `SUB-ISSUE review from #47`。改一句人话就可能改坏一条协议。
- 谁在跑一张票不在票上：会话号只在 `RUNNER` 行和 runner 的标签里，`status.py` 与 `advance` 用 `paseo ls` 认活 worker。runner 只答得出这一台机器的事，于是 Orca、Herdr 或另一台机器上的 worker 读起来像已经走了，`advance` 会放掉它的认领、再派第二个 worker。
- 「关闭」被当成「可以开工」。今天没出错，只因为 `advance` 先合并再读 frontier；一旦两件事分开发生，被阻塞的票会从还没有阻塞者代码的主干上切出工作树。

## Considered Options

- **增量更新状态，不每次重放。** 否决。状态会倒退——`ticket.regressed` 收回通过与落地，`ticket.released` 收回认领，`worker.retracted` 撤回一次起——增量要为每一种倒退写一个逆操作；重放没有逆操作，几十条评论重放一次是微秒级的事。
- **按评论时间戳排序。** 否决。GitHub 的时间戳只到秒，`worker.started` 与被起 worker 的 `ticket.claimed` 会落在同一秒，而两者的先后决定读到的是「起了还没认领」还是「已认领」。comment id 单调递增。
- **保留首行协议，只把五种形状统一成一种。** 否决。只要程序读首行，给人读的那一行就不能随便改；机器读的部分挪进隐形块，两件事才分开。
- **继续向 runner 问谁还活着。** 否决。runner 答的是一台机器，票任何机器都读得到。代价是：一个死掉却没有事件结束其占用的 worker 会一直占着票，直到有人 `retract` 或判活写下 `worker.lost`（spec #317）。占着并且说出来，好过静默地派出第二个 worker。
- **读不懂的事件块当作普通散文跳过。** 否决。跳过它，这张票读起来和没有那条事件一模一样（`docs/adr/0008-silence-is-never-a-pass.md`）。

## Consequences

- 改写 0009 Consequences 的两条：`status.py` 只读 tracker，不再问 `paseo ls` / `paseo inspect`；`phase` 不再从评论推出，它是折叠里最新一条事件的名字，只显示，不据以判断。`wait` 打印结果事件的名字与关键字段，不再读结果首行。0009 其余不变：脚本只做工具，判断归 main agent。
- 改写 0018 Consequences「四处仍直接问 Paseo」中 `status.py` 那一处：它已不问任何 runner。0018 的决定不变，事件里的 `runner` 就是那条边界上被点名的 runner；0018 正文里 `start` 写的东西随之从 `RUNNER` 行改成 `*.started` 事件。
- verifier 的判决改由 `verify-ticket.py <n> --verdict` 发出：通过还是失败由最新的 `reverify` 定，commit 由脚本读 `HEAD`。用 `gh issue comment` 手敲的 `VERDICT` 不带事件，关不了票。
- 程序仍按首行找的只剩四种不是事件的评论：`self-run`、`reverify`、`TOUCHED BY`、`CHECKS FAILED`。#315 第 2 节把它们定为 `ticket.checked` 与 `worker.touched`，与分类 label、child 改名、一次 GraphQL 读整棵树、槽位推到验收之前一起，属于 #315 的第二步，本份不涉及。
- `worker.lost`、`worker.replaced`、`child.closed`、`spec.opened` 在词汇里，折叠会读，但还没有脚本写它们。因此 `NIGHT SUMMARY` 把没有 `child.closed` 的已关闭 review 子 issue 计为 `unread`。

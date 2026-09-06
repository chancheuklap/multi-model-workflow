---
date: 2026-09-06
amends: [0009]
---

# agent 之间靠事件互相叫醒，谁都不许轮询另一个 agent

一个 agent 起了另一个 agent 之后就结束回合。它不等、不轮询、不留着回合开着，因为被叫醒是有保证的：

- **verifier 与 reviewer 干完时**，Paseo 自动通知起它们的那个会话，通知带着子 agent 最后一句回复，上级的上下文原样保留。
- **worker 把票办到头时**，`verify-ticket.py` 给起它的会话发一条 **ticket message**，首行是 `#<n> ALL MET`、`#<n> HANDOFF REQUIRED`、`#<n> NOT_READY` 或 `#<n> SUB-ISSUE pipeline`。

两条路不对称，是因为 Paseo 的通知配额本身就不对称：**一次 `create_agent` 只给上级一次终结通知，用在被起的那个 agent 第一次结束回合的时候**。verifier 与 reviewer 一辈子只结束一次回合，那一次就是它们干完的时刻，配额落在对的地方；worker 要结束好几次（每起一个下级就睡一次），配额必然落在一个没有内容的中间态上。所以 worker 用 `notifyOnFinish: false` 起，改由脚本报信。

## 为什么通知那一步在脚本里，不在 agent 的步骤里

因为它和「把结论写到票上」是同一次脚本调用。票关了通知必然发出，agent 没有机会忘、没有机会写一半、没有机会自己改写内容。`verify-ticket.py` 本来就是票能落地的唯一路径（hook 拦住手动关票），所以把报信挂在它的四个终点上，等于让每一次落地都自带一次报信。

这条推广开是三句：

1. 状态落地和「告诉需要知道的人」必须在同一次脚本调用里。拆成两步就会漏。
2. agent 只做三件事：判断、发起、把结论写成文件交给脚本。
3. agent 永远不轮询另一个 Paseo 会话。host 内部阻塞的工具调用不算——那是一次读取，不是一个循环。

## Considered Options

- **worker 轮询 `dispatch.sh wait` 直到退 0。** 这是 2026-09-06 之前的做法，两条实测把它否掉。一是 Paseo 本来就会把子 agent 的完成通知投给上级并唤醒它，那个循环什么也没买到。二是没有一个 host 会杀掉超出 shell 工具时限的命令：Cursor 30 秒、Grok Build 与 Claude Code 120 秒，一律转后台且不交回退出码——而 `wait` 的整套语义就是退出码。按一个 host 写死的 90 秒，换到另一个 host 上就是每一次都拿不到结果。
- **worker 结束回合，main 靠 heartbeat 每十分钟查一次表。** 否决。这只是把轮询从 worker 搬到 main：一夜约 48 次唤醒，每次都要跑一遍 `status` 并读表。user 2026-09-06：「本质上是把 worker 的轮询成本转嫁到 main 上面来，一点都不解决根本问题。」
- **三段衔接统一用脚本发消息。** 否决。verifier 与 reviewer 那两段，Paseo 的自动通知已经落在正确的时刻，再加一条脚本消息是同一件事说两遍，而且脚本消息会打断收信方正在跑的命令，自动通知不会。

## Consequences

- `dispatch.sh` 打印的 `create_agent` 对象自带 `notifyOnFinish`：`worker` 是 `false`，其余是 `true`。调用方照抄，不再自己决定。
- `verify-ticket.py` 的 `notify_parent` 挂在四个终点：`--closeout` 的两个分支、`--preflight` 的拒绝、`--sub-issue pipeline`。`decision` 那种 sub-issue 不发，因为 worker 还在干。发不出去只写一行 stderr，不改退出码——票已经落地了。
- ticket message 会**打断**收信方正在跑的命令，收信方看到的是「命令被中断」。所以 `night.md` 第 3 步第一件事是把那条命令重跑一遍。`advance` 本来就写成可以随时重跑（已并的分支跳过、空 frontier 什么都不起、建好没用的 workspace 下次复用），所以打断留下的中间状态下一次都能接上。
- 夜里的 heartbeat 从每十分钟改成每小时，定位从主循环降成保险：正常的一夜一次都用不到它，它覆盖的是一个会话停了却没说的情况。
- `dispatch.sh wait` 留着，只剩一种用途：被叫醒了但票上还没有结果评论时读一次。它进门先读票，通常立刻返回。
- 代价记一条：worker 静默之后，它卡在权限提示上这件事不会主动传到 main，只作为 `status` 表的 `needs permission` 那一格存在，最坏要等一次 heartbeat 才被看见。worker 跑在全权限下，权限提示本来就少；拿这个换掉每十分钟一次的全量查表，是划算的。
- 这份改写了 0009 的 Consequences 第一条（「main agent 靠 finish notification 与 heartbeat 被叫醒」）。0009 的其余部分不变：判断仍然全在 main agent，脚本仍然只做工具。

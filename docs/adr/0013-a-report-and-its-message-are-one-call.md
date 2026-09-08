---
date: 2026-09-08
amends: [0010]
---

# reviewer 与 worker 一样，报告落地和报信是同一次脚本调用

reviewer 写完评审报告不再只是结束回合等 Paseo 通知起它的 worker。它把报告交给 `verify-ticket.py <n> --review <file>`：贴出评论，并在同一次调用里给 worker 发一条首行 `#<n> REVIEW` 的消息。verifier 不变，仍然靠 Paseo 的完成通知。

## 0010 的哪一句不成立

0010 把三段衔接分成两类，依据是「一个 agent 一辈子结束几次回合」：worker 要结束好几次（每起一个下级睡一次），所以 Paseo 那一次终结通知必然花在中间态，改由脚本报信；verifier 与 reviewer「一辈子只结束一次回合，那一次就是它们干完的时刻，配额落在对的地方」。

后半句对 verifier 成立，对 reviewer 不成立。reviewer 把三个轴交给三个 subagent，而**它是否在派完之后结束回合，是模型临场决定的**——`code-review` 技能只写「一条消息三个调用，并行」，没写等不等；有的 host 的 subagent 默认后台跑，结束回合是自然结果。一旦结束，那一次通知就落在报告还不存在的时刻，而且**用掉了就没有第二次**：Paseo 的通知在第一次 running→idle 时发出并注销自己。等它的 worker 于是只剩下反复问一条路——正是 0010 立下「谁都不许轮询另一个 agent」要禁的那件事。

## 两处一起改

- `code-review` 技能第 2 节要求 dispatcher 在三个轴都回话之前不结束回合，对「subagent 默认后台跑」的 host 明写要等。这让常见情况回到 0010 假设的样子。
- `--review` 让报告落地与报信成为同一次调用。这让**不常见的情况也不再取决于模型听不听话**：无论回合怎么分，评论一贴，worker 一定收到。

第一处是提示词，第二处是脚本。只做第一处，保证的强度就是一句提示词的强度。

## Considered Options

- **只加第一处，靠 `dispatch.sh wait` 兜底。** 否决。`wait` 兜的是「被叫醒了但评论还没到」，它每问一次花掉 worker 一个回合；一次十分钟的评审按九十秒一轮是七个回合，而且那正是 0010 禁掉的轮询。兜底仍然保留（reviewer 在写出报告之前就死掉时它是唯一的路），但它不能是常态。
- **reviewer 也改成 `notifyOnFinish: false`，全靠消息。** 否决。reviewer 在贴出报告之前死掉时脚本没有机会跑，那时 Paseo 的通知（`errored` / `was closed`）是 worker 唯一会收到的东西。所以通知继续开着，只是从「唯一的报信方式」降级成「失败时的报信方式」。代价是成功路径上 worker 会被叫醒两次——先消息后通知；通知不打断，读到的是同一条评论。
- **Paseo 提供阻塞式调用，让 worker 直接等。** 查证后否决，两层原因。一是 Paseo 全部五条阻塞路径（MCP 的 `send_agent_prompt` 非后台、CLI 的 `paseo run` / `paseo send` 前台、`paseo wait`）等的都是同一个信号「第一次从忙转闲」，reviewer 中途结束回合时它们和通知一样提前返回；MCP 也没有任何等待类工具。二是 agent 发起的 `create_agent` 根本没有这个开关——Paseo 把它写死为后台。至于命令行的阻塞形式，0010 已经记过：没有 host 会让一条 shell 命令超出自己的工具超时，超时后转后台且不交回退出码。

## Consequences

- **ticket message 多一种首行**：`#<n> REVIEW`，收信方是 worker 而不是 main agent。前四种（`ALL MET`、`HANDOFF REQUIRED`、`NOT_READY`、`SUB-ISSUE pipeline`）不变。
- `--review` 只在跑它的 session 带着 `mmw.kind=reviewer` 标签时才报信。`dispatch` 技能的兜底路上，是 worker 在自己这边重跑评审，它的上级是 main agent；不判这一下，一条评审消息会送给唯一用不上它的那个 session。
- 首行不是 `REVIEW <base commit>..<HEAD commit>` 的文件被拒绝，不贴。worker 在票上认的就是这一行，认不出的报告等于没到。
- 0010 的三句推广第一句「状态落地和告诉需要知道的人必须在同一次脚本调用里」不变，适用范围从 worker 扩到 reviewer。第三句「agent 永远不轮询另一个 Paseo 会话」不变，而这次改动正是把它从「多数时候成立」变成「结构上成立」。0010 其余部分不变。
- `dispatch.sh wait` 现在自己保证最短等待，因为 `paseo wait` 对一个已经闲着的 agent 立即返回。它仍然是兜底，但兜底有了节拍。

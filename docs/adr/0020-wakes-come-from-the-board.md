---
date: 2026-09-10
amends: [0010, 0013, 0017, 0018]
---

# 唤醒从 board 上发出：中继读票上的结果事件，经 runner 的送消息动词送到等它的那个会话，任何脚本都不再报信

一个会话起了另一个 agent 就结束回合；叫醒它的是中继（`mmw-v2/skills/dispatch/scripts/relay.py`），不是被起的 agent，不是写票的脚本，也不是 runner 的完成通知。中继每 30 秒读一遍它看守的票的评论，读到 `reviewer.reported`、`verifier.passed`、`verifier.failed` 就给那张票最新一条 `worker.started` 点名的 worker 排一行唤醒，读到 `ticket.passed`、`ticket.returned`、`ticket.refused`、`child.opened`（kind `pipeline` 或 `decision`）、`worker.lost` 就给 main agent 排一行，再经收件会话自己 runner 的 `send` 把 `#<n> <event>` 送过去；收件人读完票上那条事件、处理完，用 `dispatch.sh ack <n> <event>` 确认，行才出队。main agent 在开夜时用 `dispatch.sh open <spec>` 把自己登记给中继：它的 runner 与会话号由那个 runner 适配器的 `self` 从本进程的环境读出（Paseo 的 `PASEO_AGENT_ID`、Orca 的 `ORCA_TERMINAL_HANDLE`、Herdr 的 `HERDR_PANE_ID` 所在 pane 上那个 agent 的名字），读不出就拒绝；同一步把中继作为独立进程拉起（`relay.lock` 保证一个仓库一个中继），并在 spec 上写 `spec.opened`。`summary` 与 `suspend` 停中继；夜外的单票用 `open-ticket <n>` 开、`land <n>` 停。没有中继看守的票，`start` 与 `advance` 拒绝起它。main agent 每收到一条唤醒跑一次 `advance`。设计与理由在 spec #316。

## 要修的是什么

旧的唤醒是两块补丁打在 runner 的一个洞上：Paseo 一次 `create_agent` 只给上级一次终结通知，worker 用 `notifyOnFinish: false` 起、改由 `verify-ticket.py` 的 `notify_parent` 报信（0010）；reviewer 提前结束回合会把那一次通知花掉，于是 `--review` 也报信（0013）。两块都只在 Paseo 上存在：Orca 与 Herdr 上的调用方只能反复跑 `wait`（0018 最后一条），正是 0010 禁的轮询。`notify_parent` 在没有 `PASEO_AGENT_ID`、上级已归档或 `paseo send` 出错时只写一行 stderr 就放弃，丢失无人知道。谁该知道什么，runner 不知道，票知道。

## Considered Options

- **把 `notify_parent` 搬进适配器的 `send`，三个 runner 都报信。** 否决。报信仍然是写票之后的第二个动作：进程死在两者之间，或者上级读不出来，消息就静默地丢了；写票的脚本还得知道谁在等，这是 board 才有的知识。中继从票上读，落地就是报信，漏掉的由下一次轮询与启动时的全量对账补回。
- **用 Orca 自带的 orchestration 队列。** 否决（spec #316 第 3 节）。它的行装的是 runner 的投放消息，我们的行装的是 board 上的事件；合成一条就把 board 搬进了 runner，换 runner 时唤醒路径要跟着搬。
- **推送（`gh webhook forward`）当真相。** 否决。进程断掉那段时间的事件无声无息地丢了（`docs/adr/0008-silence-is-never-a-pass.md`）。轮询是真相；推送只能做加速器，这一步没有做。
- **main agent 的会话号靠问 runner 猜（按标题找 Orca 终端、`paseo inspect`）。** 否决。runner 给每个会话设的环境变量就是 `send` 接受的那个号，读它不用猜；Herdr 按名字寻址，pane 上的 agent 没有名字就拒绝，并给出 `herdr agent rename`。嵌套时先问最里层（Paseo、Herdr、Orca 的顺序）：送给外层终端的字会打进它此刻显示的任何东西。
- **没有中继时 `start` 照起、只打一行警告。** 否决。结果落在票上而没人被叫醒，夜就静默地停了，这是一道靠什么都不做通过的闸口（0008）。
- **唤醒里带流水号，按号确认。** 否决。唤醒只带票号和事件名（spec #316 第 3 节）；收件人按它读到的那两样确认，中继从中找出对应的行。

## Consequences

- 0013 整份作废：`--review` 只贴报告，不给任何人发消息。`verify-ticket.py` 不再调用任何 runner，也不读任何 runner 的会话变量；`test_notify_parent.py` 随 `notify_parent` 删掉。
- 0010 的核心不变：谁都不许轮询另一个 agent；中继轮询的是 GitHub，agent 侧成本为零。改写的是它的机制：Consequences 第一、二条（`create_agent` 的 `notifyOnFinish`、`notify_parent` 挂在四个终点）不再成立，唤醒会打断正在跑的命令这一条保留；`wait` 只是一次读，读票上的结果事件。
- 0017 的决定不变，夜里没有叫醒 agent 的时钟。改写的是它标题下那句「叫醒主 agent 的只剩 ticket message」：现在是中继的唤醒；它说的「一条丢了的消息让夜提前结束」由中继的持久队列与重启对账接住。`mmw-night-<spec>` 那个 heartbeat 已由 0017 删掉，这里没有要动的。
- 0018 的边界多一个动词 `self`（本进程所在会话的号：0 打出、3 不在这个 runner 里、1 在但读不出）。它 Consequences 的最后两条不再成立：`verify-ticket.py` 不再用 `paseo send`，Orca 与 Herdr 上的调用方不再靠反复 `wait`。Orca 的 `send` 回执按实测的形状读（`result.send.prompt.stages`、`result.warnings`），Orca 观察不到终端里程序的回执答不知道（4）。
- runner 对 main agent 仍然承重（spec #316 第 8 节）：main agent 必须跑在一个适配器读得出会话号的 runner 会话里，换 runner 时这一处要跟着换。
- 代价：唤醒最多晚一个轮询间隔（30 秒）到；一个仓库在一台机器上同时只有一个中继，所以同时只有一夜；reviewer 或 verifier 没写结果就死掉时票上什么都没发生，worker 不会被叫醒，这个缺口归判活（spec #317）；一台机器第一次对一个 spec 开夜，中继的全量对账会把这个 spec 往夜留在票上的结果事件也排成唤醒，main agent 对每条跑一次什么都不做的 `advance` 再确认。

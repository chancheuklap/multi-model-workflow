---
date: 2026-09-10
amends: [0010]
---

# 这一夜没有任何时钟

夜里不再有定时器。`check` 不再建 `mmw-night-<spec>` 这个 heartbeat，`dispatch.sh` 不再写也不再删 `.git/mmw-heartbeat-<spec>`，heartbeat 每次点火要跑的 `land --sweep` 跟着一起去掉。叫醒主 agent 的只剩一样：worker 把票办到头时 `verify-ticket.py` 发的那条 ticket message。被叫醒之后只有一条路，`advance <spec>`。

## 它要覆盖的那次丢失，到底是什么样

heartbeat 存在的理由只有一个：一张票落地了，而说这件事的消息没送到。`notify_parent` 放弃报信有三种情形，处置各不相同：

- **没有 `PASEO_AGENT_ID`。** 这条流水线里到不了：worker 只由 `create_agent` 起，起出来的就是一个 Paseo 会话，一定带着自己的 id。
- **`paseo send` 报错或超时。** 消息丢了，但看得见：`verify-ticket.py` 在 stderr 上落下一行 `could not tell <parent>: <err>`。票已经落地，退出码不变。
- **`paseo inspect` 答不出上级的 id**，上级已经被 archive，或者 daemon 一时答不上来。这一种是静默的。可是 heartbeat 也覆盖不了它：heartbeat 是 `check` 拿主 agent 自己的会话 id 建的，上级不在了，定时器要打的那个会话就是同一个不在了的会话。

所以定时器唯一真能覆盖的是第二种，而第二种自己会出声。一次没人知道的丢失，是一道靠什么都不做通过的闸口（`docs/adr/0008-silence-is-never-a-pass.md`）；一次带着 stderr 的丢失不是，它不需要一个每小时点两次火的定时器来复查。

## Considered Options

- **频率再降一档，留着当保险。** 否决。它在本机一次都没有救过一夜，而每次点火都要主 agent 花掉一个回合跑 `land --sweep` 加 `status`，读一张它已经读过的表。
- **只删定时器，`land --sweep` 留着。** 否决。删掉定时器之后它一个自动调用方都没有；早晨的恢复由 `advance <spec>` 做，范围不同的那两类残余（本 spec 之外的票、已关闭但 claim 还挂着的票）走 `land <n>` 这条手动路径。
- **报信改成重试，或者写一个待办文件让下一条命令捡起来。** 否决。这是把保险换个地方再建一遍，而且违反 0010 的那条规矩：落地和报信必须在同一次脚本调用里，重试和待办文件都是第二次调用。
- **主 agent 自己定时查表。** 0010 已经否决过：那只是把轮询从 worker 搬到 main。

## Consequences

- 真出现没人叫醒主 agent 的情况，夜就停在那里，早上跑一次 `advance <spec>` 从原地接着走：worktree、分支、claim、已经落地的评论都在。代价是「夜提前结束」，不是「一夜白做」。
- `.git/mmw-heartbeat-<spec>` 不再存在。`summary` 与 `suspend` 不再删心跳，它们的退出码里也不再有「心跳没删掉」这一支。
- `install.sh` 从来没有为这一层装过任何东西，所以没有要卸的。以前的夜建出来的 heartbeat 靠它自己的 `--expires-in 16h` 到期，最迟第二天中午自己消失。
- `dispatch.sh land <n>` 留着。一张夜外派出的票不属于任何 spec，永远不会有 `advance` 来收它，`land <n>` 是它唯一的结束。
- 这份改写了 0010 的 Consequences 第四条（「夜里的 heartbeat 从每十分钟改成每小时，定位从主循环降成保险」）与第六条句末「最坏要等一次 heartbeat 才被看见」：worker 卡在权限提示上这件事，现在只作为 `status` 表里 `needs permission` 那一格存在，由下一次被叫醒之后的那一遍 `status` 看见。

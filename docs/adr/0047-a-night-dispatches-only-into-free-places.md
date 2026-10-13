---
date: 2026-10-13
amends: []
---

# 一夜同时被持有的票数以 `models.json` 的 `max_workers` 为上限（默认 3），`advance` 只派出上限剩下的空位

这不是加回 v4 删掉的产品槽位。没有登记、租约、排队，也没有为空位发的叫醒。`status.py` 数这一夜自己的票上的事件，等着的票由 orchestrator 每次被叫醒都跑的 `advance` 派出。删掉的产品槽位见 `mmw-v4/docs/removed-from-dispatch.md` 的 `Product slots`。ADR [0033](0033-a-full-machine-is-a-blocked-ticket.md) 记录了排队为何没有用，715 次叫醒里 0 次为槽位。

## 上限管什么

这一夜是当前 spec 的子票。持有沿用 `status.py` 的 `holder_of`，从认领或会话启动起，直到票上的事件结束持有。通过但未落地、只有认领而没有会话接手的票各占一个空位。worker 和 reviewer 同时活着也只算一张票。`advance_plan` 每次现读事件，按票号从小到大派出剩余空位容得下的票。

这是每一夜的上限。v4 没有跨仓库的「谁在跑」登记，整机保护由产品一侧的实例上限负责，agentflow 由 local-prod 的 ensure 执行。白天的会话、夜外的 One ticket 和手动 `dispatch.sh start <n> worker` 不经过 plan，不受它管。

## Considered Options

- **整机跨仓库登记。** 否决。需要跨仓库、跨夜的共享状态，正是删掉的槽位登记。整机保护归产品一侧。
- **在 `dispatch.sh` 里数会话。** 否决。持有只由 `status.py` 从事件算，两处计数会对不上，而且一张票可以同时有 worker 和 reviewer。
- **把等着的票排队，空位出来时专门叫醒。** 否决。ADR 0033 的实际运行没有用到槽位叫醒，而 `advance` 本来每次被叫醒都跑。

## Consequences

- 一个很大的 frontier 不会在同一夜启动超过上限容得下的票。持有数高于新上限时不再派新票，不停止已有会话。
- 每张等待的票在 stderr 点名上限和占着空位的票。stdout 仍只有 `MERGE`、`RELEASE`、`DISPATCH` 三种 plan line。
- `MERGE` 和 `RELEASE` 不受上限影响。配置读不了或上限不合法时，plan 打印完这些行后退出 3，只停派新票，并点名配置路径、错误和修正命令。`advance` 照常执行这些行，处理落地失败和启动拒绝后，以退出 2 报告上限错误，避免没有活着的 agent 时整夜无声停住。
- `models.py config set max_workers <n>` 的改动在下一次 `advance` 生效，不需要重启或重装。读上限不另造校验。

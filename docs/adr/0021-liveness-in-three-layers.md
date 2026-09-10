---
date: 2026-09-10
amends: [0017, 0020]
---

# 判活分三层，都不是 agent：回合守卫在主 agent 的回合结束时重新武装看门进程，看门进程看中继并问沉默票的 runner，`worker.lost` 只由它写

一张票的 worker 死了，票上什么都不会发生，board 上的沉默和还在干活长得一样（`docs/adr/0008-silence-is-never-a-pass.md`）。现在由三层接住，没有一层是 agent，也不花 token。第一层是回合守卫 `mmw-v2/skills/dispatch/scripts/turn-guard.py`，`install.sh` 把它挂在五个 host 的回合结束事件上（Claude、Codex、Grok 的 `Stop`，Cursor 的 `stop`，Pi 由扩展接 `agent_settled`）：只对中继登记的主 agent 那个会话起作用；看门进程不健康就重新拉起它，还有票被占着而它仍起不来，就不让这一回合结束（Claude、Codex、Grok 用 exit 2），拦不住的 host 塞一条消息（Cursor 的 `followup_message`、Pi 扩展的 follow-up）。第二层是看门进程 `watchdog.py`，一个仓库一个，锁 `watchdog.lock` 记 pid 与进程身份，每轮写心跳 `watchdog.json`；心跳新旧的容差是 `max(300, poll + 60)` 秒；每一轮也看中继的锁记录与最近一次成功轮询。第三层在同一个进程里：一张被占着、不在等槽位（折叠结果的 `waiting`）、超过十分钟没有新事件的票，只问它 `worker.started` 写的那个 runner 那个会话还在不在——`stopped` 就在票上写 `worker.lost`，由中继叫醒主 agent；`unknown` 记为不知道，从不当成活着，也从不写 `worker.lost`。设计与理由在 spec #317。

## 几个 spec 没写死、这里定下来的地方

- **守卫只守主 agent 那一个会话。** 同一个 host 上的 worker 也会触发同一条回合结束钩子。守卫对每个有开着的夜的状态目录，用中继 `recipient.json` 里那个 runner 的 `self` 问本进程是哪个会话，对得上才管；`self` 答不出（exit 1）时当它是主 agent——多守一次的代价是一次检查，漏守的代价是一夜。
- **「夜开着」读中继留下的文件，不另记一份。** `relay.json` 在，或者中继的 `beat.json` 还记着最近一次成功轮询，就是开着；`relay.py stop`（`summary`、`suspend`、`land` 都经它）两样都清掉。中继死了至少留下其中一样，所以死掉的中继是「开着的夜没有中继」，不会被读成「夜结束了」。
- **看门进程的发现直接经主 agent 的 runner 的 `send` 送达，不进中继的队列。** 中继可能正是出事的那一个。每条发现按它说的事与那张票最新的事件只送一次，跨进程重启也不重送；没有队列行，所以不用 ack。`send` 答 0（送到且回合开始了）时看门进程退出——一次性，由那个回合结束时的守卫重新武装；答 4（交出去了没确认）不重送、继续跑，因为这时不能指望一个回合结束来重新武装它。
- **一张被占着、却没有活的 worker 会话可问的票，也是一条发现。** 手工认领没有起会话，或者 worker 已经 lost 而 reviewer / verifier 还占着，都没有「那个会话」可问；它是「不知道」的一种，照报。
- **第三层只问 worker 的会话。** `worker.lost` 是关于 worker 的事件。worker 睡在自己的 reviewer 上而 reviewer 死了，这张票上 worker 的会话仍然答活着，这一层对它不做什么。

## Considered Options

- **Claude 用 `asyncRewake` 把看门进程挂在钩子上异步跑，退出码 2 叫醒主 agent（firstmate 的做法）。** 否决。只有 Claude 有这个机制；Cursor 没有，firstmate 记下过 Grok 在守卫失灵时把它同步跑满 28800 秒、那一回合再没结束。每个 host 都用同一种方式：钩子把看门进程作为独立会话的进程拉起就返回，由 runner 的 `send` 叫醒主 agent。主 agent 本来就必须跑在一个 runner 会话里（`docs/adr/0020-wakes-come-from-the-board.md`）。
- **守卫从 GitHub 现读哪些票被占着。** 否决。回合结束钩子在主 agent 的每一回合末尾都跑，一次网络请求加折叠太慢；它读看门进程最近一轮心跳里的 `held`。没有心跳，或者那一轮没读全，就不算「什么都没占着」。
- **判「等槽位」看最新一条事件是不是 `worker.queued`。** 否决。一次等待中间还可能落别的事件；等待是否结束由 `events.py` 的折叠结果 `waiting` 回答（到下一条 `ticket.checked` 或结束占用的事件为止），这一层不另起判据。
- **runner 是 Orca 时直接读它的 Dispatch 状态。** 否决，理由在 spec #317 的 Out of Scope：那是第四个动词。

## Consequences

- 0017 说的「这一夜没有任何时钟」不变：没有定时器叫醒任何 agent。看门进程每分钟一轮，但它不是 agent，只在发现东西时发一条消息。
- 0020 最后一条代价里「reviewer 或 verifier 没写结果就死掉时 worker 不会被叫醒，这个缺口归判活」只补上了一半：reviewer / verifier 自己死了仍然没有人发现，除非 worker 也已经不在（那时这张票成为「没有 worker 会话可问」的发现）。
- 五个 host 的回合结束能力按 2026-09-10 实测记在 `turn-guard.py` 头部。与 spec #317 第 1 节那张表有两处不同：Grok 1.0.27 用 exit 2 真的拦住了回合（同一进程里跑了第二轮）；Pi 0.85.1 拦不住，只能由扩展塞 follow-up，而 `pi -p` 在那一轮回复前就退出了。Cursor 在 `cursor-agent -p` 里根本不触发 `stop`，只在交互会话里验过。
- Herdr 上一个被 `kill -9` 的 agent 在 0.07 秒和 0.29 秒内从 `agent list` 消失（两次），容差定 1 秒，记在 `runners/herdr.sh` 头部。
- `install.sh` 写给 Claude 的每一条命令（`hook.py` 的两条和守卫这一条）前面都带 `GROK_AGENT` / `GROK_HOOK_EVENT` 守卫；装过旧版的机器上 `install.sh --check` 在重装之前会报这几条「缺」与「残留」。
- 第一层所在的 host 整个崩掉时，三层都发现不了，只有人能发现。

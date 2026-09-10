---
date: 2026-09-10
amends: [0017, 0020]
---

# 判活分三层，都不是 agent：回合守卫在主 agent 的回合结束时重新武装看门进程，看门进程看中继并问沉默票的 runner，`worker.lost` 只由它写

一张票的 worker 死了，票上什么都不会发生，board 上的沉默和还在干活长得一样（`docs/adr/0008-silence-is-never-a-pass.md`）。现在由三层接住，没有一层是 agent，也不花 token。第一层是回合守卫 `mmw-v2/skills/dispatch/scripts/turn-guard.py`，`install.sh` 把它挂在五个 host 的回合结束事件上（Claude、Codex、Grok 的 `Stop`，Cursor 的 `stop`，Pi 由扩展接 `agent_settled`）：只对中继登记的主 agent 那个会话起作用；看门进程不健康就重新拉起它，还有票被占着而它仍起不来，就不让这一回合结束（Claude、Codex、Grok 用 exit 2），拦不住的 host 塞一条消息（Cursor 的 `followup_message`、Pi 扩展的 follow-up）。第二层是看门进程 `watchdog.py`，一个仓库一个，锁 `watchdog.lock` 记 pid 与进程身份，每轮写心跳 `watchdog.json`；心跳新旧的容差是 `max(300, poll + 余量)` 秒，余量是一次适配器调用加一次 gh 读的超时（60 + 120 秒），看门进程两次心跳之间最多等这么久；读不了 board 超过容差同样算不健康；每一轮也看中继的锁记录与最近一次成功轮询。第三层在同一个进程里：一张被占着、超过十分钟没有新事件的票，或者正在等槽位（折叠结果的 `waiting`）的票——等槽位不算死，但也不免检，它不看沉默多久、每一轮都问——对还占着它的每一个会话——worker，以及结果还没落在票上的 reviewer / verifier——只问它的 `*.started` 写的那个 runner 那个会话还在不在：`stopped` 就在票上写 `worker.lost`、`reviewer.lost` 或 `verifier.lost`，中继把第一种送给主 agent，后两种送给这张票的 worker；`unknown` 记为不知道，从不当成活着，也从不写 `*.lost`。设计与理由在 spec #317。

## 几个 spec 没写死、这里定下来的地方

- **守卫只守主 agent 那一个会话。** 同一个 host 上的 worker 也会触发同一条回合结束钩子。守卫对每个有开着的夜的状态目录，用中继 `recipient.json` 里那个 runner 的 `self` 问本进程是哪个会话，`self` 答出的 (runner, session) 与登记的主 agent 一致才管；读不到登记、没有适配器、`self` 答不出，一律当作不是主 agent、不拦。真正的主 agent 总对得上：`dispatch.sh open` 拒绝登记 `self` 读不出的会话。
- **只问本机起的会话。** 每条 `*.started` 记下起它的机器（`machine`，主机名）；runner 只答得出本机的事，拿本机的适配器问别的机器上起的会话会答「已停止」。别的机器上的会话记为不知道、照报，从不问，也从不写 `*.lost`。
- **reviewer / verifier 的结果结束它自己的占用。** `reviewer.reported`、`verifier.passed`、`verifier.failed` 结束那一个会话的占用（结果没点名会话时，结束同类里最新的那个活的）。否则一个做完的 reviewer 在 worker lost 或被 retract 之后仍然占着票，`advance` 永远不会重起它。
- **「夜开着」读中继留下的文件，不另记一份。** `relay.json` 在，或者中继的 `beat.json` 还记着最近一次成功轮询，就是开着；`relay.py stop`（`summary`、`suspend`、`land` 都经它）两样都清掉。中继死了至少留下其中一样，所以死掉的中继是「开着的夜没有中继」，不会被读成「夜结束了」。
- **看门进程的发现直接经主 agent 的 runner 的 `send` 送达，不进中继的队列。** 中继可能正是出事的那一个。每条发现按它说的事与那张票最新的事件只送一次，跨进程重启也不重送；没有队列行，所以不用 ack。`send` 答 0（送到且回合开始了）时看门进程退出——一次性，由那个回合结束时的守卫重新武装；答 4（交出去了没确认）不重送、继续跑，因为这时不能指望一个回合结束来重新武装它。
- **一张被占着、却没有会话可问的票，也是一条发现。** 手工认领没有起会话，或者还占着它的只剩结果已经落下的会话，都没有「那个会话」可问；它是「不知道」的一种，照报。
- **结果已经落下的 reviewer / verifier 不问。** 它的 `reviewer.reported` 或判定在它的 `*.started` 之后已经在票上，它的进程结束是做完了，不是丢了。
- **reviewer / verifier 丢了叫醒的是 worker，不是主 agent。** 等它结果的是起它的那个 worker；新增的 `reviewer.lost`、`verifier.lost` 与 `worker.lost` 同形（runner、session 成对），只结束那一个会话的占用，不结束 worker 在等槽位的那一次运行。事件表因此是 28 个。

## Considered Options

- **Claude 用 `asyncRewake` 把看门进程挂在钩子上异步跑，退出码 2 叫醒主 agent（firstmate 的做法）。** 否决。只有 Claude 有这个机制；Cursor 没有，firstmate 记下过 Grok 在守卫失灵时把它同步跑满 28800 秒、那一回合再没结束。每个 host 都用同一种方式：钩子把看门进程作为独立会话的进程拉起就返回，由 runner 的 `send` 叫醒主 agent。主 agent 本来就必须跑在一个 runner 会话里（`docs/adr/0020-wakes-come-from-the-board.md`）。
- **守卫从 GitHub 现读哪些票被占着。** 否决。回合结束钩子在主 agent 的每一回合末尾都跑，一次网络请求加折叠太慢；它读看门进程最近一轮心跳里的 `held`。没有心跳，或者那一轮没读全，就不算「什么都没占着」。
- **等槽位的票整张跳过。** 否决（spec #317 第 4 节「等槽位不算死，但也不免检」）：一个在排队时死掉的 worker 会永远占着它的票，没有任何事件结束这个占用。
- **判「等槽位」看最新一条事件是不是 `worker.queued`。** 否决。一次等待中间还可能落别的事件；等待是否结束由 `events.py` 的折叠结果 `waiting` 回答（到下一条 `ticket.checked` 或结束占用的事件为止），这一层不另起判据。
- **runner 是 Orca 时直接读它的 Dispatch 状态。** 否决，理由在 spec #317 的 Out of Scope：那是第四个动词。

## Consequences

- 0017 说的「这一夜没有任何时钟」不变：没有定时器叫醒任何 agent。看门进程每分钟一轮，但它不是 agent，只在发现东西时发一条消息。
- 0020 最后一条代价里「reviewer 或 verifier 没写结果就死掉时 worker 不会被叫醒，这个缺口归判活」由 `reviewer.lost` / `verifier.lost` 补上：沉默满十分钟之后，它的 runner 说它停了，worker 就被叫醒。
- 五个 host 的回合结束能力按 2026-09-10 实测记在 `turn-guard.py` 头部。与 spec #317 第 1 节那张表有两处不同：Grok 1.0.27 用 exit 2 真的拦住了回合（同一进程里跑了第二轮）；Pi 0.85.1 拦不住，只能由扩展塞 follow-up，而 `pi -p` 在那一轮回复前就退出了。Cursor 在 `cursor-agent -p` 里根本不触发 `stop`，只在交互会话里验过。
- Herdr 上一个被 `kill -9` 的 agent 在 0.07 秒和 0.29 秒内从 `agent list` 消失（两次），容差定 1 秒，记在 `runners/herdr.sh` 头部。
- `install.sh` 写给 Claude 的每一条命令（`hook.py` 的两条和守卫这一条）前面都带 `GROK_AGENT` / `GROK_HOOK_EVENT` 守卫；装过旧版的机器上 `install.sh --check` 在重装之前会报这几条「缺」与「残留」。drive-target 的 `hook.py` 分辨「是不是 Cursor 在跑 Claude 那一份」也改成只读 payload 里的 `cursor_version`。
- Codex 对 hooks.json 里每一条处理器要一次信任（config.toml 的 `[hooks.state."<路径>:<事件>:<组>:<处理器>"] trusted_hash`）。`install.sh` 照 Codex 自己的算法（codex-rs `hook_hash` 与 `version_for_toml`）替本仓库写的处理器算出哈希写进去，不用再在 Codex 里按 t；实测不带 `--dangerously-bypass-hook-trust` 的 `codex exec` 照样跑了守卫，把这几行拿掉它就不跑。Codex 换算法时这几行对不上，Codex 会照旧要求 review。
- 第一层所在的 host 整个崩掉时，三层都发现不了，只有人能发现。

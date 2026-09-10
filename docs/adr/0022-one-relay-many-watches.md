---
date: 2026-09-11
amends: [0020, 0021]
---

# 唤醒按 watch 分：一个仓库一个中继，同时看多个 watch，每个 watch 叫醒开它的那个主 agent；等槽位的 worker 也由中继叫醒

watch 是中继看管的一个对象：一夜的 spec（它的子票每轮重列），或者夜外的几张票。`dispatch.sh open`、`open-ticket`、`adopt` 各开一个 watch，开它的会话就是这个 watch 的主 agent，记在状态目录的 `watches.json`（`spec:<n>` 或 `tickets:<n>[,<n>...]`）。`relay.py start` 先查后写：runner 没有适配器、runner 说这个会话已停止、这个 watch 和已开的 watch 共用一张票（夜里的票又被单独开、或者单独开着的票所在的 spec 要开夜；为此现读 board，读不到也拒绝），都拒绝，而且什么都不写；全部通过才在队列锁下写入。同一个 watch 再开一次只换它自己的主 agent。一个仓库仍然只有一个中继进程（`relay.lock`），它读所有 watch 的票的并集，给主 agent 的唤醒送到那张票所属 watch 的主 agent，`relay.recovered` 给每个 watch 的主 agent 各一条；`stop` 只关指定的 watch，最后一个关掉时进程才退出。中继每 10 轮问一次各 watch 的主 agent 还在不在，runner 连续一小时答 `stopped` 的，它的 watch 照 `stop` 关掉。worker 自己跑验收时没有空槽位，就发 `worker.queued`、退 3、结束回合；任何被看管的票上落下一条交还槽位的事件（`SLOT_ENDS` 里除 `spec.suspended` 以外的那几条），中继给每张还在等、且等得比这条事件早的票的 worker 排一行 `#<m> worker.queued`；送出之前这张票已经不等了，这一行就丢掉。

## 要修的是什么

- `open_relay` 先登记主 agent、后启动中继，启动被拒时登记不撤回：夜里再跑一次 `open-ticket` 或 `adopt`，哪怕被拒，也把整夜的唤醒、看门进程的发现、回合守卫都指到了那个被拒的会话上。已复现。
- 一个仓库一把锁、一个 watch，所以同一个仓库同时只能有一夜，夜里也不能单独开一张票。夜可以从任意分支或工作树开（`372dc811`）以后，这个限制更容易撞上。
- 排队等槽位的 worker 在命令里等 90 秒后退 3，重跑一次又等 90 秒：槽位被占多久，它就每 90 秒花一个模型回合。
- 主 agent 被关掉而夜没有 `summary` 或 `suspend`，中继会一直读下去，每小时几千次 REST 请求。

## Considered Options

- **一个 watch 一个中继进程、一个状态目录。** 否决。槽位按机器数，不按夜数：一夜交还的槽位要叫醒另一夜排队的 worker，两个进程互相看不见；队列、确认、断档公告也会各有一份。
- **维持一个 watch，第二次 `open` 一律拒绝。** 否决。那只修了"被拒的登记不撤回"，夜里仍不能单独开票。
- **worker 继续在命令里轮询槽位。** 否决。这是 0010 禁的轮询换了个地方，而且每一轮都花 token。
- **槽位空出来叫醒所有 worker，或者任何事件都叫醒排队的 worker。** 否决。只有交还槽位的事件能让排队的 worker 拿到槽位；叫醒别的都是空跑。
- **主 agent 第一次被答 `stopped` 就关它的 watch。** 否决。这时可能还有 reviewer、verifier 在跑，它们的结果要叫醒各自的 worker；一小时之后再关，下一次 `open` 会全量重读。

## Consequences

- 0020 的代价里"一个仓库在一台机器上同时只有一个中继，所以同时只有一夜"不再成立：还是一个中继，但可以同时有几夜、几张夜外的票，各叫各的主 agent。`relay.py register` 与 `recipient.json` 删掉，开 watch 是命名主 agent 的唯一方式；`add` 是不起进程的 `start`。队列里每一行多记它所属的 `watch`，watch 关了、主 agent 换了、或者 `worker.queued` 那张票已经不等了，这一行不发就丢。
- 0021 改三处。回合守卫对任一开着的 watch 的主 agent 生效，不再只认 `recipient.json` 那一个。"夜开着"只看 `watches.json` 里有没有 watch：死掉的中继留下它的 watch，所以仍是"开着的夜没有中继"。看门进程读所有 watch 的票的并集，但不读 spec 下已关闭的子票；关于某张票的发现只送那张票所属 watch 的主 agent，`relay down` 和读不到 board 送每个主 agent。另加一条发现：一张被占着的票沉默满 `--idle` 秒（默认 3600），它的 worker 活着，却没有在等 reviewer、verifier 或槽位，也还没通过，就说明这个 worker 结束了回合、而没有任何东西会叫醒它。这补上了 night.md 原来要靠某个 runner 自己的日志命令才能看到的那种情况。
- 0021 里"等槽位的票每轮都问 runner"不变；变的是 worker 不在命令里等：`verify-ticket.py` 的 worker 自跑没有空槽位时立即退 3，reverify 仍在命令里等（它的工作树通常已经占着槽位）。
- 升级时：这次改动之前起的中继进程内存里还是旧代码，不读 `watches.json`，所以 `start` 与 `add` 在它旁边拒绝，并说先 `relay.py stop`。装上新版以后，开着的夜要先停再开一次。

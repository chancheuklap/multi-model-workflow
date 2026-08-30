# 夜间编排主循环：`to-tickets` 之后到早上之前，谁做什么

`15-monitor-tab-and-wakeup-loop.md` 回答的是「下级停了上级怎么重新 prompt」，`14-herdr-utilization.md` 回答的是「Herdr 能看到什么」。本文把 #60 Out of Scope 留下的两段——「夜间编排主循环」与「监控与唤醒」——连成一条线，并回答 #87「要你先定的四件」。本文是方案全文；每条裁决登记在 `12-decisions.md` 块 J，本文按其编号引用。用词全部取自根 `CONTEXT.md`（本轮新增的词条在 Dispatch 一节：`board.py`、监控 tab、唤醒闭环、夜间编排主循环、`idle` 而 `phase` 未到 `closed`/`handoff`、重新 prompt、重派、`BLOCKED:`、`REDISPATCHED:`、`WAKEUP LIMIT:`、`TIME LIMIT:`、`NIGHT SUMMARY`、`mmw-main`、`wake`、七个常量）。

取证时间 2026-08-30 至 08-31。读过的原件：#60 全文与 2026-08-30 评论、#71–#73、#75、#87、#88；`12-decisions.md` 全文；`09`、`13`「五个宿主的 hook 能力」、`14`、`15`、`16`；`mmw-v2/skills/dispatch/`；`mmw-v2/skills/verify-ticket/`（`SKILL.md`、`scripts/hook.py`、`scripts/verify-ticket.py` 的 `report_phase`）；`mmw-v2/agents/verifier/body.md`；`to-tickets/SKILL.md`、`implement/SKILL.md`；根 `CONTEXT.md`；`docs/agents/issue-tracker.md`、`triage-labels.md`；`herdr api schema`；本机三个 herdr 插件的 manifest。

## 1. 现在已经硬了的，和还缺的

一张票内部（从 `implement #<n>` 到 `--closeout`）已经是一条完整的链，每一环都有脚本或 hook 兜底：

| 环 | 已落地 | 出处 |
| --- | --- | --- |
| 派一个会话 | `dispatch.sh <n> <role>`：查票、开 tab、注入 `MMW_TICKET`、`agent start`、等 idle、发派发词 | #67 |
| 开工守卫与认领 | `verify-ticket.py <n> --preflight`，失败评论 `NOT_READY:` | #63，S6/S7 |
| 自跑、复验、三轮上限 | `verify-ticket.py <n>` / `--reverify`，`ROUND LIMIT` | #62/#63，I5 |
| 独立判定 | verifier 写 `VERDICT` | #69 |
| 一轮 code review | `dispatch.sh <n> reviewer <base-commit>` + `dispatch.sh wait <n> "^REVIEW "`，超时跳过 | #67/#70，S9 |
| 关票门 | `--closeout` 核十项；`hook.py pretool` 拦手工关票 | #63/#64 |
| 两条出口 | `ALL MET` 关票；`HANDOFF REQUIRED` 交回 `needs-triage` | I3 |
| 此刻在哪一步 | `phase` 六值，`verify-ticket.py` 写 | H1 第 3 条 |
| 早上入口 | spec 页 sub-issue 面板 + 两个书签 | H8 |

票与票之间、会话与会话之间，什么都没有：

| 缺的 | 现状 | 谁提过 |
| --- | --- | --- |
| frontier 查询与按序派发 | `to-tickets/SKILL.md` 只说「Work the frontier」；#75 步 4 让主 agent 手敲 `dispatch.sh` | #60 Out of Scope |
| 一张票做完后派下一张、同时在跑几张 | 无 | — |
| `idle` 而 `phase` 未到 `closed`/`handoff` 的 worker | 判据有（H1 第 3 条），处置没有 | #87 |
| `unknown` 或 pane 消失 | 判据有，处置没有 | `15` §5 |
| worker `blocked` | `agent prompt` 被拒，无人处理 | #60 Out of Scope「worker 的提问出口」 |
| 主 agent 怎么被重新 prompt | 无 | #87 第 2 件 |
| 夜间总结 | `08` §6 第 3 条提过，没落点 | — |

## 2. 形状：一个常驻程序，主 agent 夜里只被重新 prompt 两种情况

```
白天  用户 ⇄ 主 agent：… → to-tickets → 票带 ready-for-agent 与阻塞边
        │
夜里  主 agent 敲一条：dispatch.sh run <spec> [--role junior-worker] [--parallel 2]
        │   ├─ install.sh --check，有缺就拒绝
        │   ├─ herdr agent rename $HERDR_PANE_ID mmw-main
        │   ├─ herdr tab create --label "mmw board"          （监控 tab）
        │   └─ herdr pane run <id> "board.py --watch <spec> …"
        │
      board.py --watch  每次 pane 事件或每 SNAPSHOT_INTERVAL 做一轮：
        │   1. 读：gh（spec 的 sub_issues、标签、assignee、blockedBy、最后一条评论首行）
        │        + herdr api snapshot（每个 pane 的 agent_status 与 tokens）
        │   2. 唤醒闭环：每个 kind=worker 的 pane 按 §4 查表                → herdr agent prompt issue-<n> "implement #<n>"
        │        （先做这一步：到 closed/handoff 的关掉 pane，位子当轮腾出）
        │   3. 派发：frontier 上的票，按票号从小到大，补到 PARALLEL          → dispatch.sh <n> <role>
        │   4. 评论到票：交回 needs-triage 的贴评论换标签                  → gh issue comment / edit
        │   5. 只在上限到了、夜间结束时                                  → herdr agent prompt mmw-main "mmw board: …"
        │   6. 没有开着的 ready-for-agent 票、也没有活着的 worker → 在 spec 上写 NIGHT SUMMARY，退出
        │
      主 agent 被重新 prompt → board.py --once 读一眼 → 回到 idle
        │
早上  用户打开 spec 页（H8）；NIGHT SUMMARY 就是 spec 页最后一条评论
```

为什么是这个形状，而不是让主 agent 自己转循环：

- G0「固定操作写成脚本」：查表、派发、退避、计数都是固定操作，没有一步需要模型。`15` §5 说「只有重新 prompt 时说什么需要模型」——本文把那句话定为派发词本身（§6），于是整条循环里没有一步需要模型。
- P0「主 agent 派完只读票」：主 agent 夜里不敲第二条命令。#75 步 4–5 与 AC3 的措辞随之改（§8）。
- H2「账本与通知分开」：`board.py` 的计数留在 Herdr token，票上只落结论（`REDISPATCHED:`、`WAKEUP LIMIT:`、`TIME LIMIT:`、`BLOCKED:`、`NIGHT SUMMARY`）。
- `10-previous-attempt-postmortem.md` §3.a.4：上限只在散文里、编排者整夜自己记。这次每个数字都是 `board.py` 顶部的常量。

## 3. 数据源、事件源、开跑前核对

**数据源只有两个，不持有状态文件**（B8、G1）：

| 要知道什么 | 从哪读 | 备注 |
| --- | --- | --- |
| 今晚的票是哪些 | `gh api repos/{owner}/{repo}/issues/<spec>/sub_issues` | A3：从锚点顺原生关系导出，不搜索。夜里 worker 开的 sub-issue 也在里面，按标签区分（`needs-triage` 的只登记不派） |
| 每张票的状态 | `gh issue view <n> --json state,labels,assignees,blockedBy,comments` | frontier = open ∧ `ready-for-agent` ∧ blocker 全 CLOSED ∧ 无 assignee ∧ 无活会话，定义在 `mmw-v2/skills/dispatch/scripts/board.py` 的 `frontier()` |
| 每个会话在哪一步 | `herdr api snapshot` 的 `agents[].tokens`：`ticket`、`role`、`phase`、`ac`、`model`、`wake` | `ticket`/`role`/`model` 由 `dispatch.sh` 派发时写（J7，已落地）；`phase`/`ac` 由 `verify-ticket.py` 写；`wake` 由 `board.py` 写 |

**事件源**：socket `events.subscribe`，订 `pane.updated`（每次推完整 `PaneInfo`，含 `agent_status` 与 `tokens`，不要求 pane_id）与 `pane.closed`。`pane.agent_status_changed` 必须带 `pane_id`（2026-08-31 实测：不带则 `invalid_request: missing field pane_id`），看全局的进程不用它。断线重连不必单独设计：不持状态，每一轮全量重读，连接断了就重连，重连失败也每 `SNAPSHOT_INTERVAL` 跑一轮。插件形态（manifest `[[events]]` 每次事件 spawn 一个短命进程）本轮不采（H2）。

**开跑前核对**：`dispatch.sh run` 第一步跑 `install.sh --check`，有「缺」就拒绝（exit 2）。2026-08-31 00:22 实测撞上的事：另一处 checkout 跑了一次 `install.sh`，`~/.agents/skills/verify-ticket`、`dispatch` 两条软链与 Claude 的 PreToolUse hook 一并指没，此后每条 Bash 都被 hook 报错拦下。夜里没有人会发现，只能在那一刻查。

## 4. 唤醒闭环的查表（#87 第 1 件；J1）

`15` §5 六行全部采用；`closeout-rejected` 并进第三行；另加四行：`dispatch.sh` 退出 1、退出 2、`MAX_HOURS`、夜间结束。只对 `tokens.kind=worker` 的 pane 动作；`kind=reviewer` 的 pane 只显示——reviewer 挂了由 worker 的 `dispatch.sh wait` 超时承接（S9）。

| 观察到（`agent_status` × `phase` × 票） | `board.py` 做什么 | 上限 | 重新 prompt `mmw-main` |
| --- | --- | --- | --- |
| `working` | 不动 | — | 否 |
| `idle`/`done` ∧ `phase ∈ {closed, handoff}` | 收尾评论已在票上。登记一行，`herdr pane close` 关掉它的 pane（tab 随之关，`issue-<n>` 这个名释放；读者在 GitHub 不在 Herdr，H0）；不再计入 `PARALLEL` | — | 否 |
| `idle`/`done` ∧ `phase` 是别的值或没有（含 `closeout-rejected`） | 等 `COOLDOWN_SECONDS`（宿主的一次 idle 可能只是回合间隙），再确认一次仍 idle，按 `15` §3 七条前提重新 prompt：`herdr agent prompt issue-<n> "implement #<n>"`；`wake` 加一 | `wake` ≥ `WAKE_LIMIT` → 评论 `WAKEUP LIMIT:` + `gh issue edit --remove-label ready-for-agent --add-label needs-triage` | 到上限时一次（告知） |
| `blocked` | **worker 在等一个回答，而纪律是不问**（`implement` 写码段：取默认值继续、记进「Decisions I made on my own」、装不下开 sub-issue）。`herdr agent read --source visible --lines 60` 取屏底最后 `FORM_LINES`（20）个非空行评论到票 `BLOCKED: <表单原文>`（表单画在视口最下面，上面是引出它的那一轮，从头截会截不到表单）；按宿主的关闭键关表单（grok `shift+x`、cursor `esc`；2026-08-31 实测两家关掉后都续得上）；重新 prompt `implement #<n>`；`wake` 加一。不替答（实测 `send-text` + `enter` 让表单选了第一项）。cursor 的表单原本在 Herdr 眼里是 `idle`，已用一条本地检测规则修成 `blocked`（§10），`board.py` 不为它写兼容 | 同 `wake` 上限 | 否 |
| `unknown` 或 pane 消失 ∧ 票 open ∧ 有 assignee（没有 assignee = 从没派过，走派发）∧ 没有 `ALL MET`/`HANDOFF REQUIRED` 评论 | **重派**：评论 `REDISPATCHED: session issue-<n> ended at phase=<p>; started again as <role>`；`herdr pane close` 旧 pane；`dispatch.sh <n> <role>`。次数数票上 `REDISPATCHED:` 评论（I5 同法） | `REDISPATCH_LIMIT`；第二次 → 评论 + `needs-triage` | 到上限时一次 |
| `dispatch.sh` 退出 1（起来了没收到派发词） | 会话已起，占一个 `PARALLEL` 位；下一轮按 `idle` 且 `phase` 为空重新 prompt | 计入 `wake` | 否 |
| `dispatch.sh` 退出 2（票不满足派发条件） | 那张票本轮不在 frontier；下一轮重查 | — | 否 |
| `agent_prompt_stalled` | 计入 `wake`，退避后再试 | 同 `wake` 上限 | 否 |
| 派出后超过 `MAX_HOURS` 仍未到 `closed`/`handoff` | 评论 `TIME LIMIT:` + 交回 `needs-triage`；不杀会话 | — | 一次 |
| 没有开着的 `ready-for-agent` 票 ∧ 没有活着的 worker | 写 `NIGHT SUMMARY`（§7），退出 | — | **是** |

与 `15` §5 的三处差别（六行之内的）：`closeout-rejected` 归入 `idle` 而 `phase` 未到 `closed`/`handoff`（它的 `phase` 也不是 `closed`/`handoff`）；重派一次、同角色、不升级（上次五条互相打架的升级规则不引入，`10` §3.a.4）；`blocked` 由 `board.py` 处理而不交人（H0 第二条）。

## 5. 主 agent 夜里的两种情况（#87 第 2 件；J2）

**机制**：`dispatch.sh run` 把主 agent 所在 pane 命名为 `mmw-main`（`herdr agent rename`；2026-08-31 实测手工起的会话改名后能被 `agent prompt`）。`board.py` 重新 prompt 它就是 `herdr agent prompt mmw-main "mmw board: <case> #<n> — run ~/.agents/skills/dispatch/scripts/board.py --once <spec>"`，遵守 `15` §3 全部七条；它在 `working` 就留到下一轮。

| 情况 | 主 agent 做什么 | 不许做什么 |
| --- | --- | --- |
| 一：`WAKEUP LIMIT:` / `REDISPATCHED:` 到上限 / `TIME LIMIT:` | `board.py --once` 读一眼，不动——`board.py` 已经贴了评论换了标签 | 再派、再 prompt、替 worker 答问题 |
| 二：夜间结束 | 读 `NIGHT SUMMARY`；若用户白天要求「跑完告诉我」，此时用宿主的通知手段说一句 | — |

worker 的 `blocked` 不惊动它（§4）。这与 P0 完全一致——主 agent 夜里一件事都不做，只被告知。

## 6. 重新 prompt 时说什么（#87 第 4 件；J4）

**就是派发词 `implement #<n>`，一个字不多。** 词表「派发词」定的是「技能名 + 票号，nothing else；固定的东西一律在技能或定义文件里」，P1 定的是「票是唯一的事实存放处，不转述」。worker 停在哪一步，票上已经写着：`self-run` / `VERDICT` / `REVIEW` 各是一条评论，`closeout-rejected` 是一个 `phase`。所以 `board.py` 不需要告诉它，`implement` 收尾段多一句就够：「票上已有 `self-run`、`VERDICT` 或 `REVIEW` 评论的，从最新那条之后的一步续，不从头再走收尾」（已加，见 `mmw-v2/merge-notes/implement.md`）。`blocked` 关掉表单之后发的也是这一句——不问的纪律本来就在技能里。

## 7. `NIGHT SUMMARY`

写成 spec issue 的一条评论（H8：给人读的东西必须在 GitHub 网页上打得开；spec 页正是早上的入口），首行 `NIGHT SUMMARY <日期>`，正文四段：关了哪些（票号 + `ALL MET`）、交回 `needs-triage` 的（票号 + 首行：`HANDOFF REQUIRED: …` / `WAKEUP LIMIT:` / `REDISPATCHED:` / `TIME LIMIT:` / `BLOCKED:`）、因上游未关而没派的（`08` §6 第 3 条，从 `blockedBy` 算）、夜里新开的 sub-issue。只列票号与首行，不转述内容。

## 7b. 监控 tab：`board.py` 的三种形态

`15` §4 照做，与唤醒闭环是同一个程序的输出面：

| 形态 | 谁用 | 输出 |
| --- | --- | --- |
| `board.py --once` | 主 agent 被重新 prompt 后第一件事；任何 agent 想看全局时 | 一屏表格，打印完退出 |
| `board.py`（无参） | 人，在监控 tab 里 | 常驻，每次事件追加一行；不重绘、不进备用屏，所以 `herdr pane read --source recent-unwrapped` 也读得到 |
| `board.py --watch <spec>` | 夜里唯一跑着的那个 | 同无参，并按 §4 查表动手 |

`--once` 的表，一行一张票，列固定为 `board.py` 的 `COLUMNS` 七列（`ticket`、`agent`、`agent_status`、`phase`、`ac`、`wake`、`note`）：

```
mmw board · 02:14 · spec #60 · 5 tickets · PARALLEL 2/2

 ticket  agent             agent_status  phase              ac     wake  note
 #61     issue-61          working       implement          -      0
 #62     -                 -             closed             5/5    -     ALL MET, pane closed
 #63     issue-63          blocked       verify             5/5    1     BLOCKED: commented, form dismissed
 #64     -                 -             closed             6/6    -     ALL MET, pane closed
 #65     -                 -             -                  -      -     waiting on #63
```

常驻形态一行一件事，时间戳打头，第二列是票号或 `board`，第三列是 `say()` 打的动作词：

```
01:58:04  board     watch      spec #60 role=junior-worker parallel=2 max-hours=4
01:58:09  #61       dispatch   issue-61 is working on #61 in pane w1:p1 on cursor-grok-4.6-high
01:58:12  #62       dispatch   issue-62 is working on #62 in pane w1:p2 on cursor-grok-4.6-high
02:05:12  #62       idle       phase=selfcheck ac=3/5  COOLDOWN 120s
02:07:14  #62       prompt     implement #62 (wake=1)
02:11:40  #62       idle       phase=closed  ALL MET
02:11:43  #63       dispatch   issue-63 is working on #63 in pane w1:p3 on cursor-grok-4.6-high
02:13:58  #63       comment    BLOCKED: Do you prefer red or blue? 1. red 2. blue
02:13:59  #63       esc        form dismissed
02:14:01  #63       prompt     implement #63 (wake=1)
03:14:02  #63       idle       phase=closed  ALL MET
03:14:05  #65       dispatch   issue-65 is working on #65 in pane w1:p5 on cursor-grok-4.6-high
03:22:10  #61       idle       phase=selfcheck ac=4/6  COOLDOWN 480s
03:30:14  #61       comment    WAKEUP LIMIT: re-prompted 3 times and it went idle again at phase=selfcheck. Handed back to needs-triage; the ticket stays open.
03:30:16  #61       label      needs-triage
```

两种输出里的词全部沿用词表：`phase` 六值、Herdr 五个状态词、`ALL MET` / `HANDOFF REQUIRED`、`VERDICT` 五级、§4 的几个首行。开监控 tab 走 `15` §4.4 最短路：`herdr tab create --label "mmw board" --cwd <仓库根> --no-focus`，`herdr pane run <id> "python3 <dispatch 技能路径>/scripts/board.py --watch <spec> …"`。包成 Herdr 插件留到稳定之后（H2）。

## 8. 落点

| 件 | 改动 | 归哪个技能 |
| --- | --- | --- |
| `mmw-v2/skills/dispatch/scripts/board.py` | 三种形态；§3 数据源；§4 查表；§7 总结；重新 prompt 只发派发词。常量在顶部。不持状态 | dispatch（G9） |
| `dispatch.sh run <spec> [--role R] [--parallel N] [--max-hours H]` | 先 `install.sh --check`，有缺就拒绝；`agent rename … mmw-main`；开监控 tab；起 `board.py --watch`（套退出即重起） | dispatch |
| `dispatch.sh <n> <role>` | 派发时写 `ticket`/`role` token（J7，已落地 `e1db5a46`） | dispatch |
| `mmw-v2/skills/dispatch/herdr/agent-detection/cursor.toml` + `install.sh` | Herdr 检测规则的本地覆盖：cursor 提问表单 = `blocked`。`install.sh` 复制到 `~/.config/herdr/agent-detection/` 并 `herdr server reload-agent-manifests`，`--check` 核对；同时向 herdr 上游提 PR，合入后删本地覆盖（J10） | dispatch |
| `dispatch/SKILL.md` | 加 `run` 调用形；加「主 agent 被重新 prompt 后做的两件事」（§5） | dispatch |
| `implement/SKILL.md` | 收尾段一句：票上已有 `self-run`/`VERDICT`/`REVIEW` 的从最新那条之后续（已加，merge-note 已记） | implement |
| `verify-ticket.py` / `hook.py` | 不改 | — |
| 根 `CONTEXT.md` | Dispatch 节新词条（已登记） | — |
| #75 | 步 4 改「主 agent `dispatch.sh run <spec> --role junior-worker`；之后只在被重新 prompt 时 `board.py --once`」；步 5 改「`board.py` 派 worker、等收尾；主 agent 不敲 `dispatch.sh wait`」；AC3 改「Herdr 的 prompt 记录里，发给 worker 的只有 `implement #<n>`，发给 `mmw-main` 的只有 `mmw board: …`」（J8） | — |
| 测试 | 自写脚本层：`tests/test_board.py` 用写死的 snapshot JSON 与票 JSON 跑查表，不调真实 `gh`/`herdr`；技能行为层：`[fixture]` 票 + 一个 `claude --model haiku` 的假 worker，prompt 让它做到自跑就停，看 `board.py` 重新 prompt；关掉它的 pane，看重派 | #60 Testing Decisions 三层 |

## 9. 常量（#87 第 3 件；J3）

| 常量 | 值 | 依据 |
| --- | --- | --- |
| `PARALLEL` | 2 | 一张票两个可见 agent（`14` §2.1），四个 pane 一屏看得清；Owns 不相交已由 `--lint` 保证 |
| `COOLDOWN_SECONDS` | 120 | 宿主回合间的 idle 常见于几十秒内 |
| `WAKE_BACKOFF` | 120 → 240 → 480 | `15` §3 第 4 条「递增且有上限」 |
| `WAKE_LIMIT` | 3 / 会话 | 与三轮上限同一档（S11） |
| `REDISPATCH_LIMIT` | 1 / 票 | 第二次交 `/triage` 判 |
| `MAX_HOURS` | 4 / 票 | 只交回不杀 |
| `SNAPSHOT_INTERVAL` | 60 秒 | 事件丢了一分钟内补上 |

计数不存文件：`wake` 在 pane token（H2 通知层），重派次数数票上 `REDISPATCHED:` 评论；`COOLDOWN_SECONDS` 与 `WAKE_BACKOFF` 的计时在 `board.py` 进程内存里，重起归零。

## 10. 先验（probe first）：2026-08-31 实测结果

| 要验的 | 做法 | 结果 |
| --- | --- | --- |
| cursor / grok 会话的 idle 能否被 Herdr 认出 | `herdr agent start … --kind cursor`，`agent prompt … --wait`；grok 同法 | **能。** cursor：`working` → `idle` 6 秒，事件推送到；grok：`--wait` 8 秒返回 `idle` |
| `blocked` 能否被认出、表单能否读到、prompt 是否被拒 | 让 grok 用提问工具问「red or blue」 | **三项成立。** `agent wait --until blocked` 5 秒命中；`agent read --source visible` 读到整个表单；`agent prompt` 返回 `agent_blocked` |
| 手工起的会话改名后能否被 prompt | `pane run "claude …"`，`agent rename <pane> probe-hand`，`agent prompt probe-hand … --wait` | **能。** `mmw-main` 这条路成立 |
| cursor 的提问表单在 Herdr 眼里是 `idle`（远端 manifest `cursor.toml` 没有提问表单的规则；grok 有 `question_dialog_hints_blocked`） | 本地覆盖 `~/.config/herdr/agent-detection/cursor.toml`：远端原样 + `ask_question_blocked`（`region = "whole_recent"`，`contains = ["esc to skip"]`，`any` 里 `space select` / `question 1 of`；版本号必须纯数字点分），`herdr server reload-agent-manifests`；`herdr agent explain --file <屏幕文本> --agent cursor` 离线验 | **修好了。** 离线：表单屏 → `blocked`，空闲屏仍 `idle`；真机：`agent wait --until blocked` 命中，`agent prompt` 返回 `agent_blocked`，`esc` 后续上 |
| 关掉提问表单后再 prompt 能否续上 | grok：`blocked` → `send-keys shift+x` → `idle` → prompt；cursor：`send-keys esc` → 表单消失 → prompt | **两家都能。** 关闭键各家不同（grok `esc` 无效、`shift+x` 有效；cursor `esc`） |
| 用按键替 worker 答表单 | `pane send-text <pane> blue` + `send-keys enter` | **不可靠。** grok 与 cursor 的表单都把 Enter 当成选第一项。`board.py` 一律不替答 |

`events.subscribe` 断线重连：§3 已把它降成兜底问题。`15` §8 第 3 条「评论首行能否被 `gh issue list --search` 命中」不再需要：`board.py` 逐票读评论。

## 11. 落地顺序

按 F1「一次只改一处、改一处测一处」五步，每步一个 commit；每一步由主 agent 手工做、手工测，不经夜间编排主循环本身：

| 步 | 改什么 | 用 `[fixture]` 票怎么测 |
| --- | --- | --- |
| 1 | `dispatch.sh <n> <role>` 派发时写 `ticket`/`kind` token | 派一次，snapshot 里该 pane 的 tokens 有 `ticket=<n> kind=worker` |
| 2 | `board.py --once` 与无参形态：§3 数据源、§7b 两种输出 | 对着现有会话跑 `--once`，表里每行与 `herdr agent list` + `gh issue view` 对得上；无参形态在 tab 里跑十分钟，`pane read` 读得回追加的行 |
| 3 | `board.py --watch`：§4 的派发、`closed`/`handoff`、`idle` 而 `phase` 未到 `closed`/`handoff`、`TIME LIMIT:` 四行；重新 prompt 只发派发词 | `claude --model haiku` 假 worker，prompt 让它做到自跑就停：看 `board.py` 等 `COOLDOWN_SECONDS` 后重新 prompt、`wake` 加一、到 `WAKE_LIMIT` 后交回 `needs-triage` |
| 4 | §4 其余行：`blocked`、`unknown` 重派、`dispatch.sh` 退出 1/2、`NIGHT SUMMARY`、重新 prompt `mmw-main` | 让假 worker 弹提问表单，看 `BLOCKED:` 评论与关表单后续上；`pane close` 假 worker，看 `REDISPATCHED:` 评论与重派；全部关完看 spec 上的 `NIGHT SUMMARY` |
| 5 | `dispatch.sh run`、`dispatch/SKILL.md`、`cursor.toml` 随 `install.sh` 装、#75 措辞 | `install.sh --check` 有缺时 `run` 拒绝；正常时监控 tab 开着、`mmw-main` 在 `herdr agent list` 里 |

第 5 步之后才轮到 #75 的真票。

## 12. 与既有定案的关系

- 沿用不动：P0、P1、G0、G9、H0、H1、H2、H3、I3、I5、`16` §5 的防转圈设定。
- 登记在块 J：J1 查表（§4）、J2 主 agent（§5）、J3 常量（§9）、J4 重新 prompt 的内容（§6）、J5 `board.py` 与监控 tab（§7b、§8）、J6 开跑前核对（§3）、J7 token（§8）、J8 #75 措辞（§8）、J9 不做的、J10 cursor 检测修在 Herdr、J11 词汇归一。
- 明确不做：升级链（junior → senior）、按票分型、杀会话、包成插件、给 Herdr 侧栏加行、`board.py` 替 worker 答表单、`board.py` 发派发词以外的任何话给 worker。

## 13. 还剩的实测项

| # | 事 | 怎么关掉 |
| --- | --- | --- |
| 1 | 重派时 cursor `-w issue-<n>` / grok `--worktree=issue-<n>` 对已存在的同名 worktree 是复用还是报错——复用正是重派要的（半途 commit 在那条分支上，`--preflight` 也要分支名 `issue-<n>`） | 落地第 4 步各起两次看 |
| 2 | `board.py` 进程本身的健壮性：未捕获异常、Herdr 重启、机器睡眠 | 实现规则：主循环 try/except；`dispatch.sh run` 起它时套 `until … ; do sleep 5; done`；不持状态所以重起无损 |
| 3 | 只发派发词能不能让一个跑到一半的 `implement` 从正确的一步续上 | 用假 worker 验；`implement` 收尾段那一句是它的依据 |

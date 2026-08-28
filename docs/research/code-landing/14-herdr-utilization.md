# Herdr 还能怎么用：pane 编排、命名、状态互知，以及 coordinator 之外的用法

`09-herdr-dispatch-model.md` 查的是「派发在机制上怎么成立」，用的是 `~/.claude/skills/herdr/SKILL.md` 写到的那部分 CLI。本文把 herdr 0.8.2 的九个命令组、socket API 的 91 个方法与 27 种订阅、以及本机已经在跑的三个 herdr 插件读了一遍，找出 `09` 没覆盖的能力，按 #60 的十一节与 #61–#75 给出落点。本文只调查、只提议，不定案。

取证时间 2026-08-29，本机 herdr 0.8.2、socket protocol 20、schema_version 1。取证方式：`herdr --help`、九个命令组不带子命令打印的清单、`herdr api schema`（255 KB）、`herdr api snapshot`、`~/.config/herdr/config.toml`（144 行）、`~/.pi/packages/integrations/herdr/` 下三个插件的源码、`~/.claude/hooks/herdr-task-state.sh`，以及在本会话所在 pane（`w2K:pT`）上做的九项实测（下文标「实测」处）。实测新建的 pane 与 tab 全部关闭，写进本 pane 的 `title`、`state_labels`、token 全部清除。

名词沿用 `09-herdr-dispatch-model.md`：**主 agent / coordinator**、**worker**、**verifier**、**reviewer 会话**。

## 1. `09` 之外的十项能力

| 能力 | 命令或方法 | `09` 的说法 | 本次核实 |
| --- | --- | --- | --- |
| 事后给 agent 命名 | `herdr agent rename <target> <name>\|--clear` | §1.2 只写 `agent start <name>`，并说「名字跟着 pane 里当前的占用者走」 | **实测**：对本会话（手工起、`name` 为空）执行 `herdr agent rename w2K:pT mmw-probe-coord` 成功，`herdr agent get mmw-probe-coord` 按名解析到同一 pane；`--clear` 清回空。命名不必发生在启动时 |
| pane 标签 | `herdr pane rename <pane_id> <label>` | 未提 | **实测**：设 `issue-61 worker` 后 `pane get` 的 `label` 字段生效。`~/.config/herdr/config.toml:10` 的 `show_agent_labels_on_pane_borders = true` 让它显示在 pane 边框 |
| tab 标签与 tab 级环境变量 | `herdr tab create [--workspace ID] [--cwd PATH] [--label TEXT] [--env K=V] [--focus\|--no-focus]`、`herdr tab rename <tab_id> <label>` | 未提 tab 组 | **实测**：`tab create --label "#61 落地1/15 测试台" --env MMW_TICKET=61 --no-focus` 返回 `.result.tab.tab_id` 与 `.result.root_pane.pane_id`（可直接交给 `agent start`）；label 支持中文与 `#`；未设 label 的 tab 显示序号 `1`/`2`/`3` |
| pane 结构化元数据 | `herdr pane report-metadata <pane_id> --source ID [--title TEXT\|--clear-title] [--display-agent TEXT] [--state-label STATUS=TEXT] [--token NAME=VALUE] [--clear-token NAME] [--ttl-ms N]` | 未提 | **实测**：写入 `--token TICKET=61 --token PHASE=implement --state-label working=写码中 --title "issue-61 worker" --ttl-ms 120000` 后 `pane get` 全部读回。schema：每个 `source` 最多 16 个 token，键名须匹配 `^[A-Za-z0-9_-]{1,32}$`，值为字符串（null 即删除），`ttl_ms` 上限 86 400 000（24 小时）。读出侧 `PaneInfo.tokens` 上限 32 |
| workspace 结构化元数据 | `herdr workspace report-metadata <workspace_id> --source ID --token NAME=VALUE [--ttl-ms N]` | 未提 | 本机 `user.space-status` 插件正在用它写 `stb/stw/std/sti/stx`（`~/.pi/packages/integrations/herdr/space-status/sync_status.py`）。同样 16 token/source |
| 给 pane 注入环境变量 | `herdr pane split … --env KEY=VALUE`、`tab create --env`、`workspace create --env` | 未提 | **实测**：`pane split --env MMW_TICKET=61` 后在该 pane 里 `echo $MMW_TICKET` 写文件，得到 `MMWCHECK:61`。该变量对 pane 里启动的 agent 进程及其 hook 同样可见 |
| 布局导出与套用 | socket `layout.export` / `layout.apply`（CLI 未暴露） | 未提 | **实测** `layout.export`：返回 `root` 为 `{"type":"pane"\|"split"}` 的树。`layout.apply` 的参数 `root` 里，`pane` 节点可带 `command`（数组）、`cwd`、`env`、`label`，`split` 节点带 `direction` 与 `ratio`——一次调用即可铺开一整个 tab 的多 pane 布局并各自启动命令 |
| 事件推送的全貌 | socket `events.subscribe`（27 种订阅）、`events.wait` | §7 只测了 `pane.agent_status_changed` | **实测**：同时订 `pane.updated`、`pane.agent_status_changed`、`workspace.metadata_updated`，另一个连接写 token，订阅端在 3 秒内收到 80 条推送，其中 `pane.updated` 载荷是完整 `PaneInfo`（含 `tokens`），`workspace_metadata_updated` 载荷含 workspace 的 `tokens`。即 **token 一写就广播**。`pane.updated` 不接受 pane 过滤参数，要在消费端筛。`events.wait` 是阻塞式单事件等待，但**目前只支持 pane agent status 匹配**（实测传 `tab_created` 返回 `unsupported_event_wait_match`） |
| 插件 | `herdr-plugin.toml` + socket `plugin.link/list/enable/…`；manifest 里 `[[startup]]` 与 `[[events]] on = "<订阅名>" command = [...]` | 未提 | 本机已装三个（`herdr api` 的 `plugin.list` 实测）：`user.agent-display-names`（上报 `$ws`/`$session`）、`user.space-status`（把 pane 的 `state_labels` 汇总成 workspace token）、`user.ws-agents-filter`（用 `agent.view.set` 让 Agents 面板只显示当前 workspace）。herdr 在事件到来时 **spawn 一个进程**执行 manifest 里的命令，进程通过 `HERDR_SOCKET_PATH` 回调 socket，环境里有 `HERDR_PLUGIN_ID` |
| 侧栏由 token 驱动 | `~/.config/herdr/config.toml` 的 `[ui.sidebar.agents]`（24 行起）、`[ui.sidebar.agents.rows_by_agent]`（48 行起）、`[ui.sidebar.spaces]`（76 行起） | 未提 | 每一行是一组 token 或内置字段；`state_text`（35、58 行）显示的就是 pane 的 `state_labels`。加一个 token 就等于给侧栏加一行 |

另有两项与本文相关但不建议动的：`agent.view.set`（Agents 面板的过滤与排序，字段可用自定义 token）是**全局单例**，已被 `user.ws-agents-filter` 占用；`pane.report_agent`（自报生命周期状态）会与 herdr 自己的 agent 检测抢 authority（另有 `pane.clear_agent_authority`），本次未测。

## 2. pane、tab、workspace 怎么排

### 2.1 一张票在 Herdr 里最多两个可见 agent

按 #60 第 9 节与 `12-decisions.md` P0：一张票的 worker 是一个 cursor / grok 会话；它在收尾第 3 步经 Herdr 起一个 Claude Code 的 reviewer 会话（`issue-<n>-review`）；verifier 是 worker 的子代理，**对 Herdr 不可见**（`09` §1.1 末行：Claude 的 SessionStart hook 在 `agent_id` 存在时直接退出）。所以 Herdr 里一张票只会出现 worker 与 reviewer 两个 agent，且 reviewer 只在收尾阶段活着，与 worker 同一个分支、同一个 worktree。

### 2.2 一张票一个 tab

tab 是三层里唯一「聚合一组 pane 的状态、又不绑定仓库」的层：`herdr tab list` 每行有 `label`、`pane_count`、`agent_status`（**实测**输出）。把一张票的 worker 与 reviewer 放进同一个 tab，得到的是：tab 的 `agent_status` = 这张票整体在跑还是停；tab 的 label = 票号与标题；tab 数量 = 今晚在跑的票数。

`dispatch.sh <n> worker` 的第一步因此不是 `pane split`，而是：

```
herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$REPO_ROOT" \
  --label "#<n> <票标题前 20 字>" --env MMW_TICKET=<n> --no-focus
```

从返回里取 `.result.root_pane.pane_id` 直接交给 `agent start`（**实测**返回含此字段），省掉 `09` §1.1 表里「先 split 再 start」的一步。

### 2.3 分屏方向按实际宽度算，不写死

worker 起 reviewer 时在**同一个 tab** 里分屏。方向由 `herdr pane layout --pane <id>` 的 `.result.layout.area` 决定：**实测**本机当前 area 为 `width 210 / height 48`，宽 pane 应向右分（`SKILL.md:100`「Split a wide pane to the right and a narrow or tall pane down」），分完两个 pane 各 105 列。窗口尺寸会变，所以脚本读一次 area、`width >= 160` 走 `--direction right`，否则 `--direction down`，比写死一个方向可靠，代价是一次只读调用。

### 2.4 不给夜里的票另开 workspace

本机现在四个 workspace（**实测** `api snapshot`），每个对应一个仓库或 worktree，`$ws` 与 `$br` token 由 `user.agent-display-names` 上报，Spaces 面板一行一个。夜里若每张票开一个 workspace，Spaces 面板会被票挤满，`$br` 的「一个工作台一个分支」也不再成立（worker 的 worktree 是宿主自己开的，见 `12-decisions.md` E1，herdr workspace 并不跟着切）。

给整批票开一个共用 workspace（label `mmw-night`）也不做：它唯一的额外好处是 Spaces 面板分组与 `user.ws-agents-filter` 的侧栏过滤，而这两处的读者只有侧栏。归组已经由「一张票一个 tab」加 `ticket` token 完成——任何监控端从 `herdr api snapshot` 按 `tokens.ticket` 筛就够，workspace 不多给一个机器可读的字段。worker 的 pane 就开在主 agent 所在的 workspace 里。

### 2.5 什么时候不开 pane

一句话的规则：**一个 pane 服务一个需要被单独观察或单独输入的长活进程；同一张票的这种进程放同一个 tab；其余一律不开 pane。**

| 东西 | 开不开 pane | 理由 |
| --- | --- | --- |
| worker | 开，tab 的根 pane | 要被 prompt、要被观察 |
| reviewer 会话 | 开，同 tab 分屏 | 与 worker 生命周期重叠、同一分支，要能对照 |
| verifier | 不开 | 子代理，跑在 worker 的进程里（`09` §1.1） |
| `verify-ticket.py` / `visual-parity.py` / 测试 | 不开 | worker 自己的 Bash 调用，退出码就是结果 |
| coordinator 自己 | 单独一个 tab | 全夜常驻，不属于任何票 |
| 监控与唤醒（`15-monitor-tab-and-wakeup-loop.md`） | 开，单独一个 tab | 人要看它，它也要被 agent 读 |

要单独细看某个 worker 时用 `herdr pane zoom <pane_id> --on`，不必调整布局。

## 3. 命名：四个位置各管一件事

`12-decisions.md` E1 只定了 Herdr agent 名（`issue-<n>` / `issue-<n>-review`）。实际上有四个可命名的位置，各服务一个读者：

| 位置 | 命令 | 取值 | 读者与用途 |
| --- | --- | --- | --- |
| agent name | `agent start <name>` / `agent rename <target> <name>` | `issue-<n>`、`issue-<n>-review` | **CLI 的定位句柄**。须匹配 `[a-z][a-z0-9_-]{0,31}` 且在活着的 agent 里唯一（`SKILL.md:56`），所以不能只写票号 |
| pane label | `pane rename <pane_id> <label>` | `#<n> worker`、`#<n> reviewer` | 人眼。显示在 pane 边框（config.toml:10） |
| tab label | `tab create --label` / `tab rename` | `#<n> <标题前 20 字>` | 人眼。tab 条与 `tab list` |
| token（source `mmw`） | `pane report-metadata --token` | `ticket`、`role`、`phase`、`ac`、`verdict` | **机读**。coordinator 与监控端的台账 |

命名方案的关键不在名字取得多好，而在**名字可预测**：coordinator 要对 #61 的 worker 做任何事，直接写 `herdr agent prompt issue-61 …`，不必先 `agent list` 找 pane id，也不必记住任何映射。这一条已经由 E1 满足，本文只补两点：

- **`agent rename` 让命名不再依赖启动那一刻**。`agent start` 在启动期被挡时返回 `agent_not_ready`（`SKILL.md:120`），名字仍保留；即使某个宿主的就绪检测失败导致没命名成功，`dispatch.sh` 也可以在确认 pane 里跑起来之后补一条 `agent rename`。
- **模型写进 token，不写进 `display_agent`**。E1 记下「cursor / grok 只有 Herdr 一侧有名」。`pane report-metadata --display-agent` 能覆盖侧栏显示的 agent 种类字段，但它的读者只有侧栏；`--token model=grok-4.6-xhigh` 同样能让监控端说出这张票用的哪个模型，且是机读的。

coordinator 要的不是记忆，是一张表。`herdr api snapshot` 的 `agents[]` 每行已含 `name`、`pane_id`、`tab_id`、`workspace_id`、`agent_status`、`tokens`、`cwd`——加上 §4 的 phase token，一条命令就是全局台账，无需逐个 `agent get`。

## 4. 状态互知与「真的做完了」

### 4.1 三层通道，各管一件事

`09` §3.1 的结论「Herdr 没有完成信号」就 Herdr 自己的生命周期而言是对的，但不等于没有完成信号可用——**worker 可以自己发一个**。三层：

| 层 | 载体 | 寿命 | 回答什么 |
| --- | --- | --- | --- |
| 此刻在哪一步 | pane token（`ttl_ms` 上限 24 小时） | 会话内 | `phase=implement` / `verify` / `closed` |
| 发生了什么 | 票上的评论 | 永久、跨机器 | EVIDENCE、VERDICT、收尾评论 |
| 有变化了 | 事件订阅（`pane.updated` 一写即广播，**实测**） | 推送 | 不必轮询 |

关键的一条推论：**`agent_status` 与 phase token 合看，「idle 但没收尾」不再是猜的**。

| Herdr 状态 | phase token | 含义 |
| --- | --- | --- |
| `working` | 任意 | 在跑 |
| `idle` / `done` | `closed` / `handoff` | 真做完了 |
| `idle` / `done` | 其它值 | **半路停了**——正是 #60 Out of Scope 留下的那种情况 |
| `blocked` | 任意 | 停在审批或提问界面 |
| `unknown` | 任意 | 会话没了或无法分类（`SKILL.md:58`） |

### 4.2 phase token 由 `verify-ticket.py` 写，不靠 worker 自觉

谁来写这条 token？不能写进技能正文让 worker 照做——`10-previous-attempt-postmortem.md` §5 的教训与 `12-decisions.md` G0 的原则都指向同一处：固定操作交给脚本。而 `verify-ticket.py`（#62、#63）恰好在每个阶段边界都会被调用一次，**每个子命令首尾各加两行即可**，worker 无感、技能正文一字不改：

| 子命令 | 写什么 |
| --- | --- |
| `--preflight` 成功后 | `ticket=<n> role=worker phase=implement` |
| 默认（自跑） | 开始 `phase=selfcheck`，结束 `ac=<met>/<total>` |
| `--reverify` | `phase=verify` |
| `--closeout` 成功 | `phase=closed` 或 `phase=handoff`，并 `--clear-token` 掉 `ac` |
| `--closeout --check-only` 被拒 | `phase=closeout-rejected` |

写入形如：

```
herdr pane report-metadata "$HERDR_PANE_ID" --source mmw \
  --token ticket=<n> --token role=worker --token phase=<阶段> --ttl-ms 86400000
```

不写 `--state-label`：它的唯一读者是侧栏的 `state_text`（config.toml:35、58）。

脚本里做三件保护：`HERDR_ENV` 不为 1 时整段跳过（脚本在 Herdr 外也要能跑）；`HERDR_PANE_ID` 为空时跳过；socket 调用失败不影响退出码（照抄 `~/.claude/hooks/herdr-task-state.sh` 的写法，它对每个前提都 `exit 0`）。

`hook.py stop`（#64）被顶回时同样写一次 `phase=stalled`，于是「它想结束但被顶回了」也变成可见状态。

### 4.3 `dispatch.sh wait` 不必每 30 秒问一次 GitHub

#60 第 2 节定的 `dispatch.sh wait <n> <首行前缀> [秒]` 是「每 30 秒 `gh issue view` 看最后一条评论首行」。worker 等 reviewer 用它、coordinator 等 worker 也用它。更短的路径是让 Herdr 先挡住等待，`gh` 只在状态变化后确认一次：

```
herdr agent wait issue-<n>-review --timeout <ms>   # 阻塞到第一个 idle/done/blocked
gh issue view <n> --json comments                  # 确认评论到了；没到就再 wait 一次
```

`agent wait` 不带 `--until` 时等的是第一个稳定态（`SKILL.md:138`），且**它跟踪的是生命周期而不是某一个回合**（`SKILL.md:130`），所以单靠它不能判完成——这正是要接一次 `gh` 确认的原因。收益是把「30 秒粒度 + N 次 API 调用」降成「事件驱动 + 一次 API 调用」。这是 `dispatch.sh` 内部的实现，技能正文与调用形（`dispatch.sh wait <n> <前缀>`）不变。

### 4.4 blocked 是谁的 blocked

`09` §6 第 5 条记了一个真问题：verifier 是子代理，它的审批弹窗会表现为 **worker pane 的 blocked**，从外面分不清是 worker 自己卡住还是 verifier 卡住。`phase` token 已经回答了这个问题：`blocked` 且 `phase=verify` 就是 verifier 卡住的那段时间。不必再加一个字段。

### 4.5 不采：读屏找完成标记

`pane.output_matched` 订阅与 `herdr pane wait-output --match` 能在输出里出现某行时触发，看上去可以让 worker 打印一行 `MMW-DONE #61` 当完成信号。不采：`09` §1.5 与 §7 已实测 grok / codex / claude 默认跑在 alternate screen 上，滚出的行不进 scrollback，读屏不可靠。token 走的是 socket，与渲染层无关。

同样不采「worker 用 `agent prompt` 通知 coordinator」：`agent prompt` 会打断对方当前回合，且对方在 working 时可能返回 `agent_prompt_stalled`（`SKILL.md:130`）。反向通道用 token 加票评论。唯一值得保留 `agent prompt` 的反向用途是「必须让 coordinator 立刻做一件只有它能做的事」，而这属于 #60 Out of Scope 的夜间主循环。

## 5. coordinator 之外的用法

### 5.1 worker

除了 §4.2 的 token（由脚本代劳）与已定的「起 reviewer 会话」，worker 在 Herdr 这一侧不需要多做别的。`herdr notification show` 的桌面通知只在人守着屏幕时有用，本仓的用户在 GitHub 网页上看票，不看 Herdr 的侧栏与通知，所以不安排。

### 5.2 唤醒闭环与监控 tab

「下级停在半路 → 上级被通知、去查为什么、重新 prompt 它继续」这条闭环，以及一个人和 agent 都能读的监控界面，是另一份调查的题目：`15-monitor-tab-and-wakeup-loop.md`。本文只留下它需要的两个输入：§4.2 的 phase token（判断「停了没收尾」）、§3 的可预测 agent 名（`issue-<n>`，唤醒方不查表就能 prompt 到人）。

### 5.3 不动 `agent.view`

`agent.view.set` 能让 Agents 面板按 token 过滤和排序。它是全局单例（`apply_view.py` 一个 `source` 一个 `label`），已被 `user.ws-agents-filter` 占用，且读者是侧栏。不动。

### 5.4 不给侧栏加行

`[ui.sidebar.agents]`（config.toml:24 起）能用一个 token 换一行。不安排：侧栏已有四行（会话标题、`$ws`、`state_text`、`$task`），宽 38 列（config.toml:13），而这套流程的读者在 GitHub 网页与监控 tab 上。§4.2 的 token 写进 herdr 是给机器读的，不是为了显示。
## 6. 落点

| 改法 | 落在哪张票 | 具体位置 |
| --- | --- | --- |
| `dispatch.sh <n> worker` 先 `tab create --label "#<n> …" --env MMW_TICKET=<n> --no-focus`，用返回的 `root_pane.pane_id` 起 agent | #67 | `dispatch.sh` 第一步；#60 第 2 节 `dispatch.sh` 一段 |
| 起完 agent 后 `pane rename` 成 `#<n> worker`；模型写进 `--token model=` | #67 | 同上 |
| reviewer 在同 tab 分屏，方向按 `pane layout` 的 `area.width` 判断（≥160 向右，否则向下） | #67 | `dispatch.sh <n> reviewer` |
| `dispatch.sh wait` 内部改成 `agent wait` + 一次 `gh` 确认，调用形不变 | #67 | #60 第 2 节 `dispatch.sh wait` 一句、第 9 节第 3 步 |
| `models.md` 第三列里的 `<n>` 由 `dispatch.sh` 替换（现在没写明谁替换） | #66、#67 | #60 第 4 节 `models.md` 三列表的说明 |
| `verify-ticket.py` 五个子命令首尾写 `ticket/role/phase/ac/model` token，`HERDR_ENV` 不为 1 时整段跳过 | #62、#63 | #60 第 2 节 `verify-ticket.py` 各子命令 |
| `hook.py` 的票号优先取 `$MMW_TICKET`，取不到再按分支名 `issue-<n>` 匹配 | #64 | #60 第 2 节 `hook.py` 自定位一段 |
| `hook.py stop` 顶回时写 `phase=stalled` | #64 | 同上 |

不落地的：夜里另开 workspace（§2.4）、`--state-label` 与侧栏行（§4.2、§5.4）、`--display-agent`（§3）、`notification show`（§5.1）、动 `agent.view`（§5.3）——它们的读者都只有 Herdr 的侧栏，而这套流程的读者在 GitHub 网页与监控 tab 上。监控 tab 与唤醒闭环见 `15-monitor-tab-and-wakeup-loop.md`。

## 7. 与现有记载冲突或要修正的地方

1. **`09-herdr-dispatch-model.md` §1.2**「名字跟着 pane 里当前的占用者走」没错，但缺了 `agent rename`：命名不必发生在 `agent start` 那一刻，事后可改可清（**实测**）。
2. **`09` §3.1「Herdr 没有完成信号」要加一句限定**：Herdr 自己不产生完成信号，但 pane token 让 worker 能自己发一个，且一写即广播（**实测**）。「做完」的判据仍是票状态（`08-failure-vocabulary.md`），token 解决的是「票没变时，它是在跑还是死了」。
3. **`09` §1.5 的三种读输出方式**之外还有第四种：token。它不经渲染层，不受 alternate screen 影响。
4. **#60 第 2 节 `dispatch.sh` 的第一步**现在写的是 `herdr pane split`。若采 §2.2，第一步是 `tab create`；`pane split` 只用于 reviewer。
5. **#60 第 4 节 `models.md`** 的第三列写着 `issue-<n>`，但没规定谁把 `<n>` 换成真实票号。`dispatch.sh` 是唯一的读者，替换应写在它那一节。

## 8. 未测、未确定

- `layout.apply` 未实测（`layout.export` 已测）。若要一条调用铺开整批票的布局，需要先验 `pane` 节点的 `command` 数组在真实 agent 启动命令上的表现，以及它与 `agent start` 就绪检测的关系。
- `pane.report_agent`（自报生命周期状态）未测，它涉及 agent 检测的 authority（另有 `pane.clear_agent_authority`），有覆盖 herdr 自身检测的风险。
- token 在宿主会话崩溃后是否随 pane 一起消失、`ttl_ms` 到期后 `pane.updated` 是否推送一次「已过期」，未测。
- cursor / grok / codex 的会话在 `agent start` 之外被 `agent rename` 后，是否影响它们自己的 SessionStart hook 上报（`09` §1.1 表），未测。
- 插件的 `[[events]]` 是否支持 `pane.updated`（本机三个插件只用了 `pane.agent_status_changed`、`pane.closed`、`workspace.updated`），未测。

# dispatch

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：`night.md` 已经有不少真正起作用的判断句（开头的 "Every decision is yours"，收尾阶段的 "Not a question of size: the constraint is concurrency"、"Counting files is not counting effort"、"The default is to fix it"，挂起的判据），这些都保留。这个技能的主要问题是主 agent 手上还有大量脚本能做的工作：看门狗消息对照表、bounce 后手动再跑 `advance`、逐票翻找未路由的发现、手写 Memory 收口 JSON。这些交给脚本后，`night.md` 会明显变短。缺的"为什么"有五处，都是主 agent 在清单外最容易判错的地方（第五处 I7 由 advisor 提出）。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md`，"Choose the moment that matches your role." 之后 | Where you are is what the ticket's events say, not what this session remembers. | 一条命令失败得不清不楚、或会话被压缩后重新进入时：没有它，agent 按记忆判断"做过了"；有了它，先看票上的事件。"票是唯一状态"已写在 `verify-ticket` `SKILL.md` 第 10 行，按 advisor 意见只留重新进入这一句。 |
| I2 | `references/night.md` 第一段之后 | The night is read in the morning by the user, cold, from `NIGHT SUMMARY`, `NIGHT RETRO` and the tracker, with none of this session's context. So each decision you make leaves its reason where that reader will look: on the child, the ticket or the spec, in a comment that stands on its own. A reason that lives only in this session is lost when it ends. | 主 agent 跳过一张票、改一条 criterion、把问题交给用户时：没有它，理由只留在会话里；有了它，写进票上能独立读懂的评论。这正是你全局 CLAUDE.md 第 2 条"夜里的工作第二天早上冷读"的要求。 |
| I3 | `references/night.md` `## 3`，表之后、contract 权威段之前 | While a worker holds a ticket, its code is the worker's: you change what the worker works from (the spec, the ticket body, a criterion, a baseline, under the authority order below) and tell it through `resume`, never its worktree or branch. Your own fixes wait for the closing pass, on `origin/<into>`. | 一张票卡住、主 agent 看得出怎么修时：没有它，会直接进 worker 的 worktree 改代码，与 worker 的提交冲突，并把实现责任拆给两个会话（ADR 0027 否决"主 agent 在 merge worktree 里解决冲突"用的是同一理由）。 |
| I4 | `references/night.md` `## 3` 表中 `child.opened` of kind `fault` 那一行，替换 "Do" 列 | Read `python3 <events.py> fold <n>`. A `fault` in this repository's environment (a credential, a service, `.mmw/target.json`) you fix, then `<dispatch> resume <n> "… continue"`. A `fault` in the pipeline's own scripts you do not patch while they run the night: tell the user what failed, and suspend when the rest of the batch would hit it too. | 原文对两种性质相反的 fault 给的是同一个动作。流水线脚本来自冻结的安装工作树，夜里修补它等于让这一夜跑在两个版本上；本仓 `AGENTS.md` 的 `## Self-hosting boundary` 明文禁止这件事，`## Suspending the night` 也已有对应的判据，只是 fault 行没有指过去。 |
| I5 | `references/night.md` `## 4` Memory 收口，A9 精简后留下部分的开头 | These records are what this spec's workers left for the workers after them: each carries the `mmw-experience` label, so later workers in this repository see it in their start prompt and act on it before reading any code. A record that was true mid-night can be wrong once the batch has landed. Judge each against what landed: keep what still holds, deprecate or supersede what the batch made untrue, and propose to the retro what should change how the pipeline works. | 没有它，四选一会被当成填表，默认全填 `retain`；有了它，会拿每条记录去对照落地后的代码。调查员原稿写"an index of them goes into every later worker's start prompt"不准确：记录是经 `mmw-experience` 标签的检索进入后来 worker 的 Related experience（`dispatch.sh` 约第 1698 行），不是整份索引。已按代码改正。 |
| I6 | `references/night.md` `## 4` 修复提交规则第 2 条，改为右栏 | It touches only what the finding's cause requires, and the tests that prove it; anything more is a ticket after all. | 原文 "only the files that finding names" 照字面执行时，会漏改测试或调用方，或把一个一文件的修复升级成票。 |
| I7 | `references/night.md` 第一段 "Every decision is yours…" 之后（advisor 提出） | The night's output is a batch the user can accept in the morning, not a count of closed tickets. A ticket handed back with its reason on it is a good result; a criterion loosened, or a worker resumed again and again with `continue`, to make one close is a defect that lands under a green mark. | 收尾前一张票卡住，而主 agent 手里有改 criterion、反复 resume worker 的权限时：没有它，主 agent 会为了"关票"去放宽标准；有了它，把票连同原因交回。worker 那一侧由 `implement` I1 承担，主 agent 这一侧原来没有。第 220 行 "valid outcomes" 只说了结果可以不全绿，没点出放宽标准这个诱惑。 |

### 删除或交给脚本

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `references/night.md` `## 3` 表中七行 `watchdog:` 映射，以及 `### Exit codes of resume` 末段那条固定催促消息 | `watchdog.py` 在每条发现文本末尾写上下一步命令（它知道 repo、ticket、session）；催促文本搬进 `idle` 发现。表里只留一行需要判断的："`watchdog: #<n> silent since …`: when `python3 <events.py> fold <n>` lists an open `contract` child, the worker is waiting on you; settle that child first." | 固定映射；真实触发过的五类（`~/.mmw/state/*/watchdog.json`）都能由脚本带出下一步。 |
| D2 | `## 3` 编号第 5 步前半 "When the summary of the `advance` you just ran has `bounced`, run `advance` once more…" 与表中 bounce 行的前半 | `advance` 记下 bounce、结束第一轮后，自己再做一轮 frontier 计算并启动刚回到队列的票。ADR 0027 要求的两次状态转换仍分开。表中 bounce 行只留 "after the second bounce the ticket stays in `needs-triage`"。 | 这是陷阱：没有唤醒会来，忘了就一张票整夜不动。 |
| D3 | `### Exit codes of resume` 前三句（"`resume` prints the next step of every exit on stderr; act on it. Exit 2 sent nothing: read `status` and do not send again. Exit 4 is…"） | 删，只留调查员 A4 列出的两句（exit 3 后重发的措辞；替换 worker 后要重发指示） | 对 exit 2 的说法与 `resume_one` 的 stderr 矛盾（脚本说先 `retract` 再 `advance`）。 |
| D4 | `## 4` "**Read every ticket of the batch, not the ones you heard about.** …run the `fold` above on each one, one ticket at a time." | 新增 `<dispatch> findings <spec>`（复用 `status.py` 已有的收集逻辑），只列未路由的 finding；这一段换成 "List the open findings with `<dispatch> findings <spec>` and route exactly those." | 确定性查询；`summary` 本来就会因 open 不为 0 而拒绝。 |
| D5 | `## 4` 从 "Once every finding has a route, close this spec's Memory records…" 到 "…or is an `unchecked` object with its reason."（约 330 词，含算 Space id 的 shell 与两种 JSON 形状） | 新增 `<dispatch> memory-list <spec>`：自己算 Space、拉完整列表、写出决策文件骨架（`total`/`returned` 预填，读不到或被截断时直接写 `unchecked`）。正文只留 I5、四种决定各自的含义、`propose` 的 evidence 必须是事件评论或 commit 的 URL 及其原因（retro 只在它等于问题来源时才计入）。 | Space 的算法与 `dispatch.sh` 自己的重复；其余格式规则 `close_spec_memories` 逐条校验。 |
| D6 | `## 1b` "It starts nothing and runs no product. It reads every ticket of the batch and prints one finding per line; a `WARN`…" | 删 | 与 `verify-ticket` 的 lint 输出和它的说明重复。 |
| D7 | `## 3` 表 "The ticket needs the other worker grade" 行括号 "(none starts it as `junior-worker`; both, or a grade `models.json` has no row for, is refused)" | 删 | 三处脚本拒绝都会说明。 |
| D8 | `## 3` 第二段 "On `MMW turn guard:`, run the named `watchdog.py arm` command. Exit 0 means it runs; on exit 1, …" | 把 "exit 1 时开 `fault` child" 并进 `turn-guard.py` 的阻断文本，然后删这段 | 阻断文本已给出命令。 |
| D9 | contract 权威段 "…procedure in `## 4. The closing pass` — never the design package, which is written only by the `design-pages` skill's `references/pull.md`." 破折号后半句 | 删 | 表中 "naming a Claude Design page" 那一行已经说了。 |
| D10 | `## 6` "`finish` checks its own preconditions and names on stderr any that is missing. It merges `origin/<base branch>` into `origin/<project branch>`, records `spec.merged`, and deletes the base branch wherever that is safe." | 删。"stderr gives the commands that remove it…" 与最后一句（发布归用户）保留 | 复述 `finish_spec`。 |
| D11 | `## Suspending the night` 第二段 "It stops every session still holding a ticket of the batch, commits and pushes…" | 缩成："A suspended night wakes nobody: its watch is closed, and its workspaces, branches and pushed commits stay for `open` and `advance` to take up." | 复述脚本；只留主 agent 需要知道的后果。 |
| D12 | `SKILL.md` `## The arguments you supply` 整节 | 删 | usage 与每个子命令的拒绝都已说明。 |
| D13 | `references/editing-models.md` 开头 "The saved configuration is `MMW_HOME/models.json`; …" 与两处 "The command scans … and refuses…" | 删；"Change it only through the commands below." 保留 | agent 不直接碰这个路径；拒绝信息自带原因。 |
| D14 | `references/one-ticket.md` 第 3 步末 "A `watchdog:` or `MMW turn guard:` line is not acked." 与 `night.md` `## 3` 第一句 "A `watchdog:` line is not a queued wake: it is not acked." | 两处删，在 `SKILL.md` `## On waking` 第 3 步末写一次 | 两个 moment 都读 `## On waking`。 |
| D15 | `references/inside-a-ticket.md` `## Exit codes` 中 adopt 那一段（约 130 词） | 缩成："Run it from the ticket's worktree on branch `issue-<n>`, before claiming; outside a night add `--into <base branch>`. Exit 2 adopted nothing; its stderr names what to fix." | 复述 `adopt_ticket` 的实现与拒绝。"Without it no event names your session…" 那句理由保留。 |

### 修复：`~/.mmw/models.json` 里 reviewer 和 advisor 两行解析不出来

**现象**（2026-09-28 本机实测）：`python3 mmw-v2/skills/dispatch/scripts/models.py row reviewer` 输出 `cannot resolve the reviewer row: 'opus[1m]' matches nothing in the catalog`；`row advisor` 对 `fable[1m]` 同样失败；`junior-worker`（grok 4.7）和 `senior-worker`（gpt 6 sol）正常。这一轮找 advisor 时 `dispatch.sh advise` 就是因此启动失败的。从代码路径推出：下一夜启动 reviewer 也会在同一处失败，也就是每张票做完都等不到审查（未实际跑夜验证）。

**原因**：`models.py` 用 Claude Code 自己的 `/model` 选单当作可选模型的目录（`fetch_cli_offerings("claude")` → `_parse_claude_model_list`）。这台机器的 Claude Code 升到 2.1.283 后，选单里不再列出带 `[1m]`（100 万 token 上下文）的条目，只剩 `opus`、`claude-fable-5-1`（折叠成 `fable`）、`sonnet`、haiku 和几个旧版本。而命令行本身仍接受 `--model opus[1m]`（解析为 `claude-opus-5-5[1m]`）和 `--model fable[1m]`（解析为 `claude-fable-5-1`，不带 `[1m]` 标记）。你在配置里选的是对的，是目录的来源变了。

**修法（工程决定）**：`match_offering` 对 claude 这一行，名字带方括号后缀时（`opus[1m]`），用去掉后缀的名字（`opus`）在目录里匹配、校验 effort，返回的 id 保留原样，交给命令行。约十行，加一个测试夹具：选单里只有 `opus`，配置写 `opus[1m]`，应解析成功并原样传出。
- 不采用"把配置改成 `opus`、`fable`"：那会改掉你选的 100 万上下文，是替你改配置。
- 已知的剩余风险：目录里已看不出一个模型支不支持 `[1m]`，写错的后缀要到启动那一刻才报错；`fable[1m]` 解析出来没带 `[1m]`，Fable 实际是否按 100 万上下文运行，我没有验证。

### 不采纳

- 调查员 A2（`one-ticket.md` 的三条唤醒处理改为引用 `night.md` 的表）：`one-ticket.md` 是那个 agent 在那一刻读的文件；让它去读一张带着 bounce、收尾阶段等夜间专有行的表，再做替换，比现在的三行更容易出错。
- 1b 恢复稿（"Answer every finding now…" 与 "A clean lint still proves only the text…"）：`ERROR` 本来就必须当场修；第二句没有对应的动作。
- 换级判据草稿（"Move a ticket to `senior-worker` when…"）：判据是调查员推出来的，"a second bounce's integration" 与同表 "after the second the ticket stays in `needs-triage`" 矛盾，也没有换级的历史数据支持。不为填空而编一条判据；D7 只删括号。
- `SKILL.md` 开头的完整三句草稿：后两句已在别处，只采纳第一句（I1）。

## 结论

`mmw-v2/skills/dispatch/` 的技能正文（`SKILL.md` 加三个 reference）共 5,578 词，其中 `references/night.md` 占 4,029 词；脚本 12 个文件共 11,750 行，`scripts/dispatch.sh` 一个就有 4,613 行。正文的主要问题不是空话，而是**把本该由脚本说出的下一步写进了 night.md**：watchdog 每种发现的处理、`resume` 的退出码、bounce 之后再跑一次 `advance`、收尾时逐票 `fold` 找 finding、Memory 收口 JSON 的格式与 Space id 的算法，这几块都是确定性工作，脚本已经知道答案或只差一个命令。改成脚本输出之后，估计能删约 1,150 词，补约 300 词思想性内容，净减约 900 词（约 16%），功能不丢。脚本方面，大部分防御都有真实事故或实测依据（注释里写着事故票号和日期，relay/watchdog 日志也能对上），真正的死代码、重复检查和重复工具函数约 170–200 行，不到 2%；更大的体量来自 `dispatch.sh` 里 26 处 `python3 -c` 和 9 段内嵌 Python heredoc，那是结构选择，不算过度防御。"灵魂"基本完整：night.md 开头、收尾分流的四步理由、contract 的权威顺序都在；缺的是三件事：主 agent 做的这一夜最后交给谁读（早上的用户）、夜里哪些事不该由主 agent 亲手做（ticket 的代码、正在跑的流水线本身）、Memory 收口为什么要做。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `references/inside-a-ticket.md` `## Exit codes`："**`adopt <n> [--into <branch>]`**, for a session that picked ticket `<n>` up itself…"（第 9 行，约 130 词） | 1 | 整段复述 `dispatch.sh` 的 `adopt_ticket`（第 930–1019 行）：`into` 的三级来源、`worker.started` 记录的 10 个字段、再次 adopt 不重写、exit 2 的 9 种原因。每个 exit 2 分支的 `refuse` 文本都已写明下一步（例如第 950 行"adopt it from a worktree on issue-$number"，第 331 行"pass --into <base branch>"，第 991 行"retract that start once its session is gone"） | `adopt_ticket` 的拒绝信息。剩余风险：无 | 保留一句："Run it from the ticket's worktree on branch `issue-<n>`, before claiming; outside a night add `--into <base branch>`. Exit 2 adopted nothing; its stderr names what to fix." |
| A2 | `references/one-ticket.md` 第 3 步的三条子弹："`#<n> worker.lost`: the worker's session stopped…"、"`#<n> ticket.refused`…"、"`#<n> child.opened`: a `fault` stopped the worker…" | 6 | 与 `references/night.md` `## 3. Each time something wakes you` 表里 `worker.lost`、`ticket.refused`、`child.opened of kind fault/decision` 四行意思相同；第四条子弹本来就指回 night.md 的表 | night.md 第 3 步的表。剩余风险：one-ticket 的 agent 可能照搬夜里才有的行（bounce 重试）；用一句替换规则挡住 | 改成一句："Handle each wake by the table under **3. Each time something wakes you** in night.md, reading `advance` there as `<dispatch> start <n> worker`; a bounce outside a night goes straight to `needs-triage`, and `land` replaces the closing pass and `summary`." |
| A3 | `references/night.md` `## 1b`："It starts nothing and runs no product. It reads every ticket of the batch and prints one finding per line; a `WARN`…" | 1、6 | 与 verify-ticket 的 `references/linting.md` `## Exit codes` 及第 43 行"The batch is ready when `ERROR` is at zero…"重复 | linting.md 与 lint 自己的输出。剩余风险：无 | 删这两句。"except one saying the tracker could not answer (tagged `[parent-unreadable]`…)"这条例外目前还需要保留，见"与其他技能的重复"第 1 条：让 lint 给"tracker 没回答"单独的退出码之后，这条例外也能删 |
| A4 | `references/night.md` `### Exit codes of resume`："`resume` prints the next step of every exit on stderr; act on it. Exit 2 sent nothing: read `status` and do not send again. Exit 4 is…" | 6 | 第一句自己就承认 stderr 已给出下一步；而且对 exit 2 的说法和脚本**矛盾**：`dispatch.sh` `resume_one` 第 2209 行对"runner 上没有这个 session"说的是"run retract $number, then advance…"，`ended_worker_hold`（第 2220–2273 行）对每种结束事件给出不同下一步，night.md 却统一说"do not send again" | `resume_one` 与 `ended_worker_hold` 的 stderr。剩余风险：无，反而消除一处冲突 | 只留脚本说不出的两句："When you run `resume` again after exit 3, word it so a worker that receives both messages reads them as one instruction. A worker that `start <n> worker` puts in place of the old one has none of the instructions given only inside the old session; send them again with `resume`." |
| A5 | `references/night.md` `## 3` 表里七行 `watchdog:` 开头的行（`relay down`、`relay not reading`、`liveness unknown`、`is held with no session to ask`、`cannot read the tracker`、`events unreadable`、`silent since … with nothing to wait on`），以及 `### Exit codes of resume` 末段"For `watchdog: #<n> silent since <time>`… run `<dispatch> resume <n> "You ended your turn with no result…"`"（合计约 230 词） | 1、6 | 这些是"看到 X 就执行 Y"的固定映射。watchdog 的发现文本是主 agent 收到时正在读的那份，`watchdog.py` 已经这样做了一半：`NEXT` 常量（第 347 行）给 `relay not reading` 带了下一步，`relay down` 带了 `status` 命令。`~/.mmw/state/*/watchdog.json` 的 `reported` 记录显示真实触发过的是 `relay down`、`relay not reading`、`unheld`、`idle`、`read` 五类 | `watchdog.py` 的 `Watchdog.round`（第 627–686 行）和 `Watchdog._silent`（第 698–763 行）在每条发现文本末尾加上下一步命令（它知道 repo、ticket、session；spec 可从 watch 取）。剩余风险：同一次改动里必须改 watchdog 文本和测试 `mmw-v2/tests/liveness/`；单条消息变长，但本来就是一行 | 表里只留一条需要判断的："`watchdog: #<n> silent since …`: when `python3 <events.py> fold <n>` lists an open `contract` child, the worker is waiting on you; settle that child first." 固定的催促文本搬进 watchdog 的 `idle` 发现 |
| A6 | `references/night.md` `## 3` 编号第 5 步前半："When the summary of the `advance` you just ran has `bounced`, run `advance` once more…"，以及表中行"The `advance` summary has `bounced` \| Step 5 runs `advance` once more…" | 1、4 | 这是确定性规则，而且是陷阱："no wake will come for it"，忘了就一张票整夜不动。根源是 `advance` 第 3194 行跳过 `bounced_this_advance`。ADR `docs/adr/0027-a-bounce-returns-once.md` 要求的是"记录 bounce 的那次 frontier 计算不重启"，即两次状态转换分开，并不要求由 agent 手动触发第二次 | `dispatch.sh` `advance`：在写完 bounce 事件、第一轮结束后，再读一次 `status.py --advance-plan`，启动刚回到队列的票（或整个 `advance` 自调一次）。两次转换仍然分开，ADR 0027 的条件满足。剩余风险：`advance` 的汇总行要能说清哪次启动来自重试 | 删这两处，表里 bounce 行只留"after the second bounce the ticket stays in `needs-triage`" |
| A7 | `references/night.md` `## 3` 表中行"The ticket needs the other worker grade"的括号："(none starts it as `junior-worker`; both, or a grade `models.json` has no row for, is refused)" | 1 | `start_one` 第 1871–1877 行、`check_machine` 第 2453–2462 行、verify-ticket lint 的 `[worker-label]` 都会拒绝并说明 | 那三处拒绝。剩余风险：无 | 删括号，换成 B 部分"何时换级"的草稿 |
| A8 | `references/night.md` `## 4. The closing pass`："**Read every ticket of the batch, not the ones you heard about.** … Take the ticket list from `<dispatch> status <spec>` … run the `fold` above on each one, one ticket at a time." | 1 | 逐票找"kind 为 finding、还没有 child.closed 的 child"是确定性查询。`status.py` 的 `print_summary`（第 806–834 行）已经把每张票的 child、kind、resolution 全部读出，`routed_counts` 算出 open 数，`summary` 还会因 open 不为 0 而拒绝（`summary_spec` 第 3981–3992 行） | 新增 `status.py --findings <spec>`（经 `dispatch.sh findings <spec>` 暴露），每行打印 `<ticket> <child> <title>`，只列未路由的 finding。约 20 行，复用 `print_summary` 的收集逻辑。剩余风险：无 | 文本改成："List the open findings with `<dispatch> findings <spec>` and route exactly those. A finding wakes nobody, so the ones you were woken about are no measure of what exists." |
| A9 | `references/night.md` `## 4` 从 "Once every finding has a route, close this spec's Memory records before leaving the pass." 到 "…or is an `unchecked` object with its reason."（约 330 词，含一段算 Space id 的 shell 和两种 JSON 形状） | 1、6、4 | ① 那段 `gh repo view … \| tr … \| sed 's\|/\|__\|'` 与 `dispatch.sh` 第 1906 行、第 3667 行自己的算法相同，agent 手工重复一件脚本已做的事；② `total` 等于 `returned`、id 集合无重复且与新列表一致、`unchecked` 两种写法等规则，`close_spec_memories`（第 3771–3856 行）逐条校验，文本是在复述校验器；③ `nmem --json memories list` 实测返回 `memories`、`returned`、`total` 三个键，截断判断完全可以由脚本做 | 新增 `dispatch.sh memory-list <spec>`：自己算 Space、拉完整列表、写出决策文件骨架（每个 id 一条，`total`/`returned` 预填；列表读不到或被截断时直接写好 `unchecked` 对象）。agent 只填 `decision`、`reason`、`evidence`、`replacement_id`。剩余风险：新增约 40 行脚本和对应测试 | 文本只留：四种决定各自的含义；`propose` 的 evidence 必须是事件评论 URL 或 commit URL，以及原因（retro 只在它等于问题来源时才计入，见 `mmw-v2/skills/retro/SKILL.md` 第 106–107 行）；加上 B 部分关于"为什么要收口"的草稿 |
| A10 | `references/night.md` `## 6. Merge the accepted night`："`finish` checks its own preconditions and names on stderr any that is missing. It merges `origin/<base branch>` into `origin/<project branch>`, records `spec.merged`, and deletes the base branch wherever that is safe." | 1 | 复述 `finish_spec`（第 4194–4280 行）与 `finish_preflight`（第 4039–4098 行） | `finish` 的 stderr。剩余风险：无 | 删这两句。保留"stderr gives the commands that remove it, for the user to run once this session is done"和最后一句 release 决定归用户 |
| A11 | `references/night.md` `## Suspending the night` 第二段："It stops every session still holding a ticket of the batch, commits and pushes each stopped ticket branch…" | 1 | 复述 `suspend_night` 头注释（第 3348–3366 行）与其实现 | 脚本和它的汇总行。剩余风险：agent 可能不知道挂起之后不会再有唤醒 | 缩成一句："A suspended night wakes nobody: its watch is closed, and its workspaces, branches and pushed commits stay for `open` and `advance` to take up." |
| A12 | `references/night.md` `## 3` 第二段："On `MMW turn guard:`, run the named `watchdog.py arm` command. Exit 0 means it runs; on exit 1, fix stderr's reason or open a `fault` child…" | 6 | `turn-guard.py` `guard` 第 305–310 行的阻断文本已写"Run `python3 … arm --repo …`, act on what it prints, then end your turn" | 把"exit 1 时开 `fault` child"这半句并进 turn-guard 的文本。剩余风险：无 | 删这段 |
| A13 | `references/night.md` `## 3` 表下 contract 权威段："…through the normal `origin/<into>` commit and push procedure in `## 4. The closing pass` — never the design package, which is written only by the `design-pages` skill's `references/pull.md`." | 6 | 同一文件表里"`child.opened` of kind `contract` naming a Claude Design page"那一行已经说了一遍 | 表中那一行。剩余风险：无 | 删破折号后的半句 |
| A14 | `SKILL.md` `## The arguments you supply` 整节："`<n>`, `<spec>` and `<child>` are digits only, no `#`. `start`'s third argument is `worker` or `reviewer`. The base commit is computed…" | 1 | `dispatch.sh` 入口 `usage`（第 368–395 行）和每个子命令的"must be digits only"拒绝（第 4503–4580 行）；`ack` 本身接受带 `#` 的号码（第 4533 行） | usage 与拒绝信息。剩余风险：agent 带 `#` 时多一次被拒重试 | 删整节 |
| A15 | `references/editing-models.md` 开头："The saved configuration is `MMW_HOME/models.json`; when `MMW_HOME` is unset, that means `~/.mmw/models.json`." 以及 `## Change one role`、`## Change the runner` 里"The command scans … and refuses…"两句 | 2、1 | agent 从不直接碰这个路径（`config show` 会打印内容）；拒绝行为由 `models.py` 的 `_validate_local_config`（第 903–951 行）给出具体原因 | `models.py` 的输出与拒绝。剩余风险：无 | 保留"Change it only through the commands below."（这是禁止手改），删其余 |
| A16 | `references/one-ticket.md` 第 3 步末尾"A `watchdog:` or `MMW turn guard:` line is not acked." 与 `references/night.md` `## 3` 第一句"A `watchdog:` line is not a queued wake: it is not acked." | 6 | 同一规则写了两遍；而且对不在队列里的唤醒执行 `ack`，`relay.py` `cmd_ack`（第 1721–1729 行）会拒绝并说明原因 | 在 `SKILL.md` `## On waking` 第 3 步末尾写一次（两个 moment 都读这一节）。剩余风险：无 | 两处删，`SKILL.md` 写一次 |

没有第 3 类（历史记录、日期、issue 号）：在正文里 grep "no longer"、"now"、"2026-"、"#<三位数>"，只命中 `deprecate` 的定义"is no longer valid"，那是定义本身，不是历史。

## B. 灵魂

### 保留，勿删

- `references/night.md` 开头："You are the main agent. A spec's tickets will be worked while you are not watching each one. … Every decision is yours: whether a worker continues, whether a failure is yours to fix…"：告诉 agent 脚本只做机械活，判断都是它的；没有这段，agent 会把 night.md 当成跑命令的清单。
- `references/night.md` 开头第三段："Between the steps below you end your turn. … nothing else does, and no agent polls another."：规定了整个流水线的工作方式（靠事件唤醒，不轮询）；删掉之后 agent 会开始 sleep 加轮询。
- `references/night.md` `## 3` 第 3 步："Take every row the table matches, not only the ticket named by the wake."：唤醒只是指针，`status` 才是事实；这句防止 agent 只处理被点名的那张票。
- `references/night.md` contract 权威段，从 "For a `contract` child, use this authority order exactly…" 到 "…do not rewrite its delivery while the authority is unresolved."：规定主 agent 能改什么、什么时候必须把决定留给用户，是判断的依据，不是步骤。
- `references/night.md` `## 4` 分流四步里的理由句："Not a question of size: the constraint is concurrency. …"、"Counting files is not counting effort; it is asking whether the change has a cross-file shape…"、"**A name echoed through prose is not a coupling**…"、"**The default is to fix it, not to open a ticket.**"：每句都给出判断的理由，碰到清单外的情况 agent 可以照理由推。
- `references/night.md` `## 4`："A ticket you write here is dispatched in this night, and it has had none of the reading the published batch had. … Two shapes come back from a night's findings and neither is a criterion…"：说明夜里新开的票风险在哪，并点名两种已知的错误写法。
- `references/night.md` `## 5`："Tickets left for human acceptance, handed back to triage by their worker, or behind an open blocker are valid outcomes; `summary` does not require every ticket to succeed."：防止 agent 为了"全绿"去硬推票。
- `references/night.md` `## 6`："Do not merge the project branch into the repository default branch here; that remains the user's release decision."：划出产品决定的边界。
- `references/night.md` `## Suspending the night` 第一句："A night is worth suspending when the fault is in the pipeline rather than in a ticket: workers left running against it spend their time producing failures that say nothing about the work."：给出挂起的判断标准。
- `references/one-ticket.md` 开头："A ticket outside a night belongs to no spec, so no `advance` will ever collect it: `land <n>` is its whole ending."
- `references/inside-a-ticket.md`："Without it no event names your session, so your reviewer's report would wake nobody…"，以及 `## After the closeout` 的 "Do not run `land` from this worker session: it stops every session the ticket's events name, including this one."：两句都在防真实的误用。
- `SKILL.md` `## Resolve <dispatch> once`："Resolve it from this file's own location; the path differs by machine and by host."：`SKILL-SET-REVIEW.md` `### Redundancy and bloat` 点名的那类必须保留的句子。
- `SKILL.md` `## On waking` 第 2 步："the wake carries nothing the tracker does not."
- `references/editing-models.md` 最后一段："One difference between runners outlives the command; tell the user of it when the runner changes. …"：这是用户能直接感受到的差别，agent 必须转告。

### 缺口与补充草稿

- **`SKILL.md` 开头（`# Dispatch` 之下、`Choose the moment…` 之前）**：缺少对整套机制的一句话交代。一个刚被 `start` 起来的 worker 或 adopt 的 session 只读 SKILL.md，不知道 tracker 是唯一事实来源，于是会信 session 里的记忆、等着别人回话，或者轮询。
  > Dispatch lets tickets be worked while nobody watches. Three facts hold in every moment below: the ticket's events on the tracker are the only record anyone trusts, so what you did is done only once its event is there; nobody polls, so you end your turn and a wake brings you back; and a wake only points at a ticket, so the news is always read on the ticket, never taken from the wake or from memory.

- **`references/night.md` 开头第一段之后**：缺"这一夜交给谁读"。最后读结果的是早上的用户，他手里只有 `NIGHT SUMMARY`、`NIGHT RETRO` 和 tracker，前一晚的上下文已经忘了。agent 不知道这一点时，会把判断留在自己的 session 里，例如在对话里解释为什么跳过某张票、在 child 上只写一行结论，早上的读者就无从复核。
  > The night is read in the morning by the user, cold, from `NIGHT SUMMARY`, `NIGHT RETRO` and the tracker, with none of this session's context. So every decision you make leaves its reason where that reader will look: on the child, the ticket or the spec, in a comment that stands on its own. A night that finished but whose reasons live only in this session has to be redone by hand.

- **`references/night.md` `## 3` 表下（contract 段之前）**：缺"主 agent 夜里不亲手做什么"。现在只有收尾阶段说了"fix it yourself"。夜里一张票卡住时，一个积极的主 agent 很可能直接进 ticket 的 worktree 改代码，这会和 worker 的提交冲突，并把实现责任拆给两个 session（ADR 0027 否决"由 main agent 在 merge worktree 里解决冲突"用的就是这个理由）。
  > While a worker holds a ticket, its code is the worker's: you change what the worker works from (the spec, the ticket body, a criterion, a baseline, under the authority order below) and tell it through `resume`, never its worktree or branch. Your own fixes wait for the closing pass, on `origin/<into>`.

- **`references/night.md` `## 3` 表中 `child.opened` of kind `fault` 行**：现在写的是"fix the child, then resume"，没有区分两种性质完全不同的 fault。一种是本仓环境的问题（凭据、`.mmw/target.json`、端口、服务没起），主 agent 可以修；另一种是正在运行的流水线本身坏了（`dispatch.sh`、`verify-ticket.py`、某个 judge），主 agent 不能在夜里修补正在运行的版本。后一种正是根 `AGENTS.md` `## Self-hosting boundary` 在本仓禁止的事，而 `## Suspending the night` 已经给了对应动作，只是 fault 行没有指过去。
  > A `fault` names either this repository's environment (a credential, a service, `.mmw/target.json`), which you fix and then resume the worker, or the pipeline's own scripts, which you do not patch while they run the night: record it for a later batch and suspend if the rest of the batch would hit it too.

- **`references/night.md` `## 3` 表中"The ticket needs the other worker grade"行**：A7 删掉括号后，这一行需要一句"什么时候该换级"。现在 agent 不知道换级的判据，要么从不换，要么一失败就换。
  > Move a ticket to `senior-worker` when what stopped it is a design question across files or a second bounce's integration, not when a junior worker simply ran out of rounds on one criterion; a label change reaches only the next `start`.

- **`references/night.md` `## 4` Memory 收口（A9 精简后留下的部分）的开头**：缺少目的。现在的文本只有格式，agent 会把它当成交表，按默认值填 `retain` 了事。
  > These records are what the workers of this spec wrote for the tickets after them, and an index of them goes into every later worker's start prompt. A record that was true mid-night can be wrong once the batch has landed, and a wrong one misleads the next worker on this code before it reads a line. Judge each against what landed: keep what still holds, deprecate or supersede what the batch made untrue, and propose to the retro what should change how the pipeline works.

- **`references/night.md` `## 1b`（A3 精简后）**：前几轮删掉了"lint 通过不等于合约完成"这段理由（原文见 `git show c55574d0:mmw-v2/skills/dispatch/references/night.md` 第 44–47 行："**A clean lint is not a finished contract.** It reads text, not a running product…"），还删掉了为什么要在开夜前一次性处理（原文："Answer the findings in one sitting rather than one per ticket per night…"，后面跟一个日期案例）。建议恢复这两层意思，去掉日期：
  > Answer every finding now, in one sitting: each one left in costs a whole ticket later in the night, one at a time. A clean lint still proves only the text: a page that renders nothing or a check that does not depend on the click shows up only when a worker runs it, and comes back as a finding.

与 `SKILL-SET-REVIEW.md` 的关系：上面的草稿每条都写到了具体动作（留理由在哪、不碰什么、什么时候换级），能通过 `### Redundancy and bloat` 对 "No-op: an attitude where an action would do" 的检验。1b 的恢复草稿去掉了原文的日期案例，避开了 Sediment 表里 "a dated measurement" 那一行。本技能没有发现两份文件相冲突的地方。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `references/night.md` `## 4` Memory 收口：手写 JSON 的完整形状，加上 `unchecked` 的两种变体 | 格式完全由校验器决定，agent 没有判断空间，只可能写错 | A9：脚本生成骨架，agent 只做四选一的判断，再加 B 部分的目的说明 |
| C2 | `references/night.md` `## 4` "run the `fold` above on each one, one ticket at a time" | 一个脚本一次查询就能完成的枚举，被写成逐票手工操作 | A8：`findings` 命令 |
| C3 | `references/night.md` `## 3` 编号第 5 步（bounce 后再跑 `advance`） | 顺序确实存在（ADR 0027 的两次状态转换），但这个顺序应该由脚本保证，不该靠 agent 记住 | A6：由 `advance` 自己做第二轮 |
| C4 | `references/night.md` `## 4` 修复提交的第 2 条："It touches only the files that finding names." | 一个修复往往要同时改测试或调用方，而 finding 正文不一定点名这些文件。按字面执行，agent 会漏改测试，或把一个一文件修复升级成票 | 改为 "It touches only what the finding's cause requires, and the tests that prove it; anything more is a ticket after all." 第 1、3 条保留：第 1 条让 summary 能对上号，第 3 条防止写"the tests pass"这类空话 |
| C5 | `references/night.md` `## 3` 表中七行 watchdog 映射 | if-then 表照搬了脚本的分支 | A5：下一步写进 watchdog 的发现文本，表里只留一条需要判断的 |

这些**需要保留**，因为它们依赖真实的顺序：`## On waking` 的"读完再 ack，ack 在长工作之前"（relay 重启后会重发未 ack 的唤醒）；`## 3` 的 ack → `status` → `advance`；`## 5` 的 `reverify` → `summary` → retro → `finish`（`summary` 要 reverify 回执，`finish` 要 `spec.retroed` 回执，见 `finish_preflight` 第 4043–4052 行）；`one-ticket.md` 的四步（`open-ticket` 必须先于 `start`，否则 `start` 拒绝，见 `start_one` 第 1863–1865 行）；contract 的权威顺序（这是排序，不是步骤）。

## 脚本

按"四问"判断。凡是注释里有事故票号或实测日期、日志里触发过的防御，都没有列进来；根 `AGENTS.md` `## Self-hosting boundary` 相关的防护也没有列。

**死代码与退役残留**

1. `scripts/dispatch.sh` 入口第 4463 行 `--json | --run) refuse "$1 is no longer a flag"`：这两个 flag 在 2026-09-06（commit `98032106`）退役，全仓除了专门测它的 `mmw-v2/tests/dispatch/test_dispatch.sh` 第 2862–2872 行，没有任何调用者。删掉之后，`start 61 worker --json` 会因位置参数数量不对走进 `usage`，同样 exit 2、同样什么都不调用。建议一并删除那段测试。
2. `scripts/models.py` 中生产代码不调用、只有测试调用的部分：`apply_permissions`（第 1056–1063 行，全仓无调用者）；`scan_cli_catalogs`（第 645–650 行，无调用者）；`WORKTREE_OWNING = {"lody"}`（第 34 行）以及 `pick_runner` 里对它的过滤（第 317–318 行），这里重复了两次：`runtime_from_environ` 只会给出 orca/herdr/tmux，而 `has_adapter("lody")` 本身就为假，因为没有 `runners/lody.sh`；`pick_runner` 的 `ticket=`、`env=` 参数（第 294–295 行），唯一的生产调用者 `runner_name`（第 1109 行）从不传这两个参数，只有 `mmw-v2/tests/dispatch/test_runner_pick.py` 在用；`create_agent_settings` 的 `permissions` 参数（第 1047–1049 行）只接受唯一值 `bypass`。合计约 30 行，测试需要同步删。
3. `scripts/models.py` `match_offering` 第 387–396 行：`if len(exact) == 1: hits = exact / elif len(exact) > 1: hits = exact` 两个分支完全相同，`ordinary` 的两个分支也一样。合并成 `if exact: hits = exact`。
4. `scripts/dispatch.sh` `suspend_night` 第 3371–3375 行：计算了 `git_dir`，函数里再也没用，还带着一条和上一行重复的"not inside a git repository"拒绝。删两行。
5. `scripts/dispatch.sh` `summary_spec` 第 3999–4002 行：`extra` 由 `printf` 生成，永远非空，`if [ -n "$extra" ]` 不可能为假。
6. `scripts/dispatch.sh` 中 `newest_field` 只返回 0/2/3/4，但 `ticket_into`（第 2737、2744、2753 行）、`newest_worker_field`（第 272 行）、`finish_preflight`（第 4049、4065、4079 行）都写了 `*)` 分支，永远到不了。属于低优先级清理。
7. `scripts/relay.py` `open_checked` 第 1527–1535 行：拒绝"`relay.json` 带 `watch` 字段的旧版单 watch relay"。单 watch relay 在 2026-09-11（commit `b7752abc`）退役，现在的 `cmd_run`（第 1485–1487 行）不写这个字段；两个仓库的 `relay.log` 里 "serves one watch" 出现 0 次。守的路径已不存在，可删。
8. `scripts/relay.py` 的 `add` 子命令、`ack --through`：生产代码（`dispatch.sh`）只用 `start`/`stop`/`watching`/`ack --ticket --event`，这两个只在 `mmw-v2/tests/relay/test_relay.sh`（第 222、252 行等）使用。它们是测试接口，不算防御；留不留是工程上的选择，这里只做记录。`queue` 可作为排障入口保留。

**过度防御（正常输入走不到）**

9. `scripts/dispatch.sh` `summary_spec` 第 3956–3964 行：对 `mmw-reverify-<spec>` 回执做了五道格式校验。这个文件只由同一脚本的 `reverify_spec` 第 3656 行用 `printf '%s %s %s\n'` 写出，正常输入不会出现坏格式。保留"文件存在、红数为 0、commit 等于当前 `origin/<into>`"三项就够了，其余一律归为"unreadable, run reverify again"一条。
10. `scripts/dispatch.sh` `delete_landed_ticket_branch` 第 2907–2908 行：函数自己用 `ticket_branch` 拼出 `issue-<n>`，随后又用正则检查它是不是 `issue-<n>`，并检查它不等于 `into`。第一项不可能失败；第二项要求 base 分支恰好叫 `issue-<n>`，正常用法到不了。
11. `scripts/dispatch.sh` `reviewer_rules_packet` 第 1779–1815 行：对 `nmem context read` 的输出做了 9 道形状检查，每一道失败的结果都一样，都是 `unavailable: …` 然后 reviewer 照常启动。可以用一个 try/except 包住渲染，任何形状意外都写成 "unavailable: nmem answered in an unexpected shape (<field>)"，约 30 行缩到 10 行，行为不变。
12. `scripts/dispatch.sh` `close_spec_memories` 的 `evolves_to` 第 3747 行：`value.get("relations", value.get("links", value.get("items", [])))` 在猜三种容器键。实测 `nmem --json memories link list <id> --type EVOLVES` 返回的是 `{"memory_id", "relations", "total"}`；`links`/`items` 这两个猜测可删。第 3750 行的四个 target 键名没能实测（本机没有 EVOLVES 关系），保留，并在"没查到的"里记下。

**重复逻辑**

13. 去掉 `CLICOLOR_FORCE`/`CLICOLOR` 的代码在 dispatch 技能里写了 7 份：`dispatch.sh` 的 `gh_`（第 113 行）加三段内嵌 Python（第 1087、1575、1761 行），`status.py` 的 `gh` 与 `_gh_run`（第 63–65、88–90 行），`ghlist.quiet_env`。`dispatch.sh` 在入口 `unset CLICOLOR_FORCE CLICOLOR` 一次，就覆盖它所有子进程，四份可删；`status.py` 改用 `ghlist.quiet_env()`。runner 适配器里的 `env -u` 要保留，因为 relay/watchdog 也会直接调用它们。
14. `scripts/watchdog.py` 与 `scripts/relay.py` 互抄：`ask_liveness`（watchdog 第 440–453 行对 relay 第 574–587 行）、`send_to`（第 456–472 行）对 `send_via_adapter`（第 551–571 行）、`now_utc`/`iso`/`parse_iso`、`positive_int`、`state_for`。watchdog 已经 `import relay as relay_mod`，差别只有 `MMW_RUNNERS_DIR` 覆盖。给 relay 的函数加这个覆盖后 watchdog 直接调用，约 50 行可删。
15. `scripts/dispatch.sh` `workspace_origin_ready`（第 1173–1196 行）与 `ensure_workspace` 前 20 行（第 1345–1362 行）逐字重复。"停掉旧 worker 前后各查一次"是有意为之（注释第 1170–1172 行），但代码可以抽成一个函数调用两次。
16. `scripts/dispatch.sh` `worker_memory_packet` 与 `reviewer_rules_packet` 各自带一份 `call()`/`reason()`（第 1574–1587 行、第 1760–1772 行）。
17. `scripts/dispatch.sh` 里用 `importlib.util.spec_from_file_location` 按路径加载兄弟模块的内嵌 Python 共 9 处（`newest_field`、`row_for_role`、`worker_roles`、`lease_worktree_for`、`acquire_merge_lock`、`repository_state_dir`、`sweep_orphan_merge_worktrees`、`run_merge_checks`、`read_ticket`），`python3 -c` 共 26 处。这是 bash 调 Python 结构的代价，不是过度防御；只作记录。
18. `scripts/dispatch.sh` 中 `archive_ticket_agents`（第 1455 行）与 `stop_live_ticket_agents`（第 1461 行）是 `stop_ticket_agents` 的一行别名，各只有一个调用点。

**误导性的拒绝文本**

19. `scripts/dispatch.sh` 有 5 条拒绝让 agent "pass --tools <the … skill's scripts directory>"（第 1327、2131、3503、3563、4487 行）。生产环境从不传 `--tools`，脚本会从自身位置自动找到兄弟技能，全仓只有测试在传。生产中真出现"找不到 lease.py/verify-ticket.py"，说明安装坏了，照这条提示做只会绕开问题。建议改为 "the <skill> skill is missing beside this one; run `install.sh --check`"。

**核查后确认不是死代码**

`scripts/watchdog.py` `relay_problem` 第 403–415 行的 `since_cycle is None` 分支，注释说它服务"an older relay"（`cycle_at` 字段加入前的版本）。但 `relay.py` 的 `_forget_last_poll`（第 713–721 行）在最后一个 watch 关闭时会把 `cycle_at` 置为 `None`；新 relay 启动后、第一轮结束前，这个分支正是用 start grace 判断健康的那条路径，所以代码要留，只是注释写错了原因，应改注释。

## 与其他技能的重复或交接问题

1. **verify-ticket 的 lint**：`references/night.md` `## 1b` 要 agent 从 `ERROR` 行里分辨"tracker 没回答"（`[parent-unreadable]`、`[sub-issues-unreadable]`、traceback），再决定是重跑还是修票。这是脚本能精确判断的区别，应由 verify-ticket 的 lint 给出单独的退出码。改了之后 night.md 的这条例外可删。该改的是 verify-ticket 的脚本，这里只做记录。
2. **implement 与 dispatch 的唤醒规则**：worker（moment 1）的唤醒动作写在 implement `## Closing steps` 里，通用的 ack 规则写在 dispatch `SKILL.md` `## On waking`。worker 只为解析 `<dispatch>` 才读 dispatch 的 SKILL.md，恰好能读到 `## On waking`，交接成立，但靠的是巧合。建议 implement 在第 3 步提到 ack 的地方点名 dispatch `SKILL.md` `## On waking`。该留 dispatch 这一份。
3. **tool-guard 与 implement**：`scripts/tool-guard.py` 的 `NO_QUESTION`（第 76–80 行）复述了 implement 的 "Put no question on the screen…"。两份都该留：技能文本在事前防止，钩子在 agent 真的去调用提问工具的那一刻拒绝，读者和时刻都不同。
4. **维护者文档三份**：`docs/contexts/night/how-it-works.md`、`scripts/relay.py` 的 229 行模块文档、`scripts/watchdog.py` 的 158 行模块文档，对 relay/watchdog 机制讲了三遍。它们都不是技能正文，agent 不加载；读者是改脚本的人。建议以脚本头为准（离代码最近），how-it-works.md 只留跨脚本的总图。只做记录。
5. **retro**：night.md `## 5` 调用 retro，retro 结尾（`mmw-v2/skills/retro/SKILL.md` 第 174 行）指回 night.md `## 5`，交接完整。A9 精简时必须保留 `propose` evidence 的规则，retro 第 106–107 行依赖它。

## 没查到的

- `SKILL.md` `## On waking` 第 1 步 "A wake can cut short a command you were running. Run that command again first."：这句来自 Paseo 时期（commit `415403c7`，原文说 ticket message "does interrupt"）。现在用的 Orca 送达方式是"program mid-turn reads it when the turn ends"（`runners/orca.sh` `send` 第 477 行），看起来不会打断命令。Paseo 下是否仍会打断，没有验证，所以没有列入 A。
- `scripts/status.py` `night_opened`（第 504–515 行）用"16 小时前"近似本夜的开始，决定 `Closed:` 和 `Sub-issues opened tonight:` 列哪些；而 `spec.opened` 事件里有准确时间。这是正确性问题，不在本任务的三个方向里，只做记录：跨夜超过 16 小时的 night，summary 会漏列。
- `scripts/models.py` 的 `parse_legacy_rows`/`parse_legacy_runner`（第 161–196 行）服务 `install.sh` 的一次性 Markdown 迁移。本机 `~/.mmw/` 已经没有旧文件，但用户在其他机器上是否都已迁移，我没法查，所以没有列为可删。
- `close_spec_memories` `evolves_to` 的四个 target 键名（第 3750 行），因本机没有 EVOLVES 关系，没能实测。
- runner 适配器 `runners/herdr.sh`、`runners/paseo.sh` 只读了头注释、函数表和入口，没有逐行读 `start`/`send` 的实现；`runners/orca.sh` 全部读完。`hosts.json`、`statedir.py`、`ghlist.py`、`tool-guard.py`、`turn-guard.py`、`status.py`、`relay.py`、`watchdog.py`、`models.py`、`dispatch.sh` 全部读完。
- tracker 上事件的使用频次靠 `gh search issues "<event>" in:comments` 估计。本仓的 spec 和票里常提到这些事件名，本仓的计数因此偏高，只在 `agentflow-hq/agentflow` 的计数上作了推断；`worker.retracted` 两仓都是 0，说明 `retract` 可能从未真实执行过，但它是用户可见的一条恢复路径，没有列为可删。

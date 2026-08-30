# 审计 04 · 派发、等待、夜间循环、Herdr

范围：`CONTEXT.md`、`mmw-v2/skills/dispatch/` 全目录、`docs/research/code-landing/17-night-loop.md`、`12-decisions.md`、`mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`.../code-review/SKILL.md`、`mmw-v2/install.sh`。旁证：`docs/research/code-landing/15-monitor-tab-and-wakeup-loop.md`、`14-herdr-utilization.md`、`11-target-pipeline.html`、`docs/agents/issue-tracker.md`、`~/.agents/skills/herdr/SKILL.md`。

## 发现 1：`mmw board: <case> #<n> — run board.py --once` 这条唤醒句，主 agent 照字面跑不出它要看的东西

- 类型：断点
- 后果：主 agent 半夜被叫醒，照句子敲 `board.py --once`：① 没有路径，`board.py` 不在 PATH 上；② 不带 spec，`collect(None)` 只列还活着的会话——而 `WAKEUP LIMIT` / `REDISPATCHED` 交回票时 pane 已经被关掉，`night over` 时所有 pane 都关了，于是句子点名的那张票（或整晚的票）根本不在表里。它读到一张空表，然后「回到 idle」。
- 证据：
  - `mmw-v2/skills/dispatch/scripts/board.py:499` 「`MAIN_LINE = "mmw board: {case} #{n} — run board.py --once"`」
  - `mmw-v2/skills/dispatch/scripts/board.py:877` 「`numbers = list(sub_issues(spec)) if spec else []`」（`once(spec)` 在 `883`，`spec` 为 `None` 时票号只来自活着的会话）
  - `mmw-v2/skills/dispatch/scripts/board.py:771-776`（`hand_back` 里 `herdr(["pane", "close", row["worker"]["pane_id"]])`）与 `board.py:823` 「`self.for_main.append(MAIN_LINE.format(case="night over", n=self.spec))`」
  - `mmw-v2/skills/dispatch/SKILL.md:100-101` 「both arrive as one line: `mmw board: <case> #<n> — run board.py --once`. Run that, read the table, and go back to being idle.」
  - `CONTEXT.md:448` 「The main agent answers it by running `board.py --once` and reading; it takes no other action.」
  - `mmw-v2/skills/dispatch/SKILL.md:11-18` 只解析了 `dispatch.sh` 的绝对路径（「`scripts/dispatch.sh`, next to this file. Resolve its absolute path once.」），`board.py` 的路径在 SKILL.md 里一次都没出现
- 建议正名：句子里带上 spec 与路径，例如 `mmw board: <case> #<n> — run <skill>/scripts/board.py --once <spec>`；`MAIN_LINE`、`SKILL.md`「When the board re-prompts you」一节、`CONTEXT.md:447` 三处同改。理由：这条句子的唯一读者是一个空上下文的会话，它只有这一行。

## 发现 2：frontier 三处定义不同，派发顺序两处不同

- 类型：分岔 + 重复定义
- 后果：读 `CONTEXT.md` 的人以为 frontier 的硬规则是 Owns 不相交；读 `docs/agents/issue-tracker.md` 的人得到一条不看 `ready-for-agent`、而且「first in map order wins」（一次一张）的查询；`board.py` 实际按五个条件筛、按票号从小到大补到 `PARALLEL`。`17-night-loop.md` 又说派发「按启动层级」——`启动层级` 是 `verify-ticket.py --lint` 打印的东西，`board.py` 从不读它。同一晚谁先被派，按哪份文档推都不一样。
- 证据：
  - `CONTEXT.md:97-98` 「**frontier**: The set of tickets that may be worked in parallel right now. The hard rule: no two tickets on one frontier may have overlapping `## Owns`.」
  - `docs/agents/issue-tracker.md:43` 「**Frontier query**: list the map's open children … drop any with an open blocker … or an assignee; first in map order wins.」
  - `docs/research/code-landing/17-night-loop.md:75` 「frontier = open ∧ `ready-for-agent` ∧ blockedBy 全 CLOSED ∧ 无 assignee ∧ 没有活着的 pane（`docs/agents/issue-tracker.md` 的定义加最后一项）」
  - `docs/research/code-landing/17-night-loop.md:51` 「3. 派发：frontier 上的票，**按启动层级**，补到 `PARALLEL`」
  - `mmw-v2/skills/dispatch/scripts/board.py:369` 「The tickets that may be started right now, **in ticket order**.」（票序来自 `build_rows` 的 `sorted(set(numbers))`，`board.py:296`）
- 建议正名：以 `board.py` 的五条件 + 票号序为准，把它写成 `CONTEXT.md` 的 frontier 词条正文（Owns 不相交是 `--lint` 保证的前置，写成一句「由 `--lint` 保证」而不是 frontier 的定义）；`17-night-loop.md:51` 的「按启动层级」删掉或改成「按票号」；`issue-tracker.md:43` 那条标明它服务 `/wayfinder`，不是夜间派发的定义。

## 发现 3：`17-night-loop.md` §11 说第 3 步待返工、第 4/5 步没做，代码和同名 HTML 说全做完了

- 类型：脚本与文档不符
- 后果：接手的人读 §11 会去做一遍已经做完的事：删「句表」（`board.py` 里没有句表）、把评论首行改成 `BLOCKED:`（已经是）、实现 `blocked`/重派/`NIGHT SUMMARY`/`dispatch.sh run`（全在仓库里）。
- 证据：
  - `docs/research/code-landing/17-night-loop.md:207` 「已落地 `b9f405cb`，**待返工**：删掉句表，只发派发词；评论首行改 `BLOCKED:`」，同表 `208`、`209` 两行的「状态」列是「—」
  - `mmw-v2/skills/dispatch/scripts/board.py:487` 「`DISPATCH_LINE = "implement #{n}"`」、`board.py:501` 「`BLOCKED = "BLOCKED: {form}"`」、`board.py:652-683`（`at_a_form`）、`board.py:703-719`（`redispatch`）、`board.py:818-843`（`write_summary`）、`mmw-v2/skills/dispatch/scripts/dispatch.sh:331-378`（`run_night`）
  - `docs/research/code-landing/17-night-loop.html:67` 「已落地：#87 六个 commit（`e1db5a46` … `df6e47dd`）」
  - `git log`：`50c5779c refactor(dispatch): #87 步 3 返工`、`8bd1e24c … 步 4`、`8d6f8e19 … 步 5`、`df6e47dd`
- 建议正名：`17-night-loop.md` 的「状态」列整列删掉（按 CLAUDE.md「文件描述它的主题，不描述它自己的历史」），落地进度只留在 `12-decisions.md` 块 J 与 commit 里。

## 发现 4：`board.py` 的两种输出，文档里的样子和程序打印的不是一回事（而且有三个版本）

- 类型：分岔
- 后果：`--once` 的表在 `17-night-loop.md` 里是中文列头、中文备注，`15-monitor-tab-and-wakeup-loop.md` 里是又一套列（多「停了多久」、少 `wake`），程序打印的是英文列头。照文档写监控 tab 的解析、或照文档核对输出的人，对不上。
- 证据：
  - `docs/research/code-landing/17-night-loop.md:133-140`「`mmw board · 02:14 · spec #60 · 5 张票 · PARALLEL 2/2`」「` 票    agent          agent_status  phase       ac     wake  备注`」「`#64   -   -   closed   6/6   -   ALL MET，pane 已关`」
  - `mmw-v2/skills/dispatch/scripts/board.py:384-385` 「`COLUMNS = (("ticket", 8), ("agent", 18), ("agent_status", 14), ("phase", 19), ("ac", 7), ("wake", 6), ("note", 0))`」、`board.py:402` 「`head.append(f"{len(rows)} tickets")`」、`board.py:357` 「`return (head[:60] + ", pane closed").strip(", ")`」
  - `mmw-v2/skills/dispatch/tests/test_board.py:236` 「`"mmw board · 02:14 · spec #60 · 2 tickets · PARALLEL 1/2"`」、`test_board.py:154` 「`self.assertEqual(row["note"], "ALL MET, pane closed")`」
  - `docs/research/code-landing/17-night-loop.md:147` 「`02:16:33  #62  读票       最后一条评论 self-run：AC3、AC5 未过`」（程序没有「读票」这个动作词，`report_changes` 只打状态词，`board.py:893-909`）、`17-night-loop.md:152` 「`02:31:04  #63  shift+x → idle → prompt implement #63（wake=1）`」（程序打两行：`say(…, key, "form dismissed")` 与 `say(…, "prompt", …)`，`board.py:681`、`board.py:744`）
  - `docs/research/code-landing/15-monitor-tab-and-wakeup-loop.md:90-95` 「` 票    agent            状态     phase       AC     停了多久  备注`」
- 建议正名：把 `17-night-loop.md` §7b 的两段样例换成 `board.py` 真打印的那份（英文列头、英文备注）；`15` §4.3 的表标明已被 `17` §7b 取代，或直接删。

## 发现 5：主 agent 在活文件里被叫 `orchestrator` / `coordinator`，两个词都在 `_Avoid_` 里

- 类型：幽灵词
- 后果：读 `models.md` 的人在词表里查不到 `orchestrator`；他不知道这句话说的就是 `main agent`／`mmw-main`，也就不知道「表里没有它」等于「`dispatch.sh run` 那条命令是它自己敲的」。
- 证据：
  - `CONTEXT.md:11-13` 「**main agent（主 agent）**: … _Avoid_: coordinator, 编排者, orchestrator, 出票的主 agent, 落地 agent」
  - `mmw-v2/skills/dispatch/models.md:3-5` 「Every agent this pipeline sends out is here except the **orchestrator**, which is the session you started yourself from the CLI.」
  - `docs/research/code-landing/15-monitor-tab-and-wakeup-loop.md:120` 「上级（**coordinator** 或 `board.py --watch`）」、同文件 `133` 「只在查表落到最后两行时才叫醒 **coordinator**」
- 建议正名：`models.md` 改成 `main agent`；`15` 那两处同改（或标明该文件的用词已被块 J 的 J11 取代）。

## 发现 6：`CONTEXT.md` 明令禁用的「没到终点就停了」「半路停了」「半途停下」仍在活的研究文件里当正名用

- 类型：幽灵词
- 后果：`17-night-loop.md` 反复叫读者回去读 `15` §5 和 `14`（「`15` §5 六行全部采用」），读者到那里拿到的是被否掉的那套叫法，再写出来就是第二套词。
- 证据：
  - `CONTEXT.md:415-417` 「**`idle` ∧ `phase` ∉ {`closed`, `handoff`}**: … _Avoid_: 半路停了, 半途停下, 没到终点就停了, 停在半路, 到终点, 终点, stalled」
  - `docs/research/code-landing/15-monitor-tab-and-wakeup-loop.md:92` 「`#62   issue-62         idle     selfcheck   3/5    6m        没到终点就停了`」、同文件 `126` 「**这就是「没到终点就停了」**」
  - `docs/research/code-landing/14-herdr-utilization.md:106` 「`| idle / done | 其它值 | **半路停了**——正是 #60 Out of Scope 留下的那种情况 |`」
  - `docs/research/code-landing/11-target-pipeline.html:1301` 「`半途停下：J（board.py）`」
- 建议正名：三处都换成判据本身「`idle` 而 `phase` 未到 `closed`/`handoff`」。

## 发现 7：`HOOKS-INSTALLED` 是个谁也不打印的字符串

- 类型：幽灵词 + 脚本与文档不符
- 后果：`dispatch.sh run` 开夜前要跑 `install.sh --check`；按 `CONTEXT.md` 与总蓝图，人会去输出里找 `HOOKS-INSTALLED` 来确认 hook 装上了，找不到，于是不知道该信哪一行。
- 证据：
  - `CONTEXT.md:369-371` 「**`HOOKS-INSTALLED`**: The marker the installer prints after its own check of the hooks it just wrote.」
  - `docs/research/code-landing/11-target-pipeline.html:1105` 「`install.sh` 把五宿主各写一条指向同一个 `hook.py` 的配置，`--check` 打印 `HOOKS-INSTALLED`。」（`1269` 行同一句）
  - `mmw-v2/install.sh:507` 「`print(f"hook  {path}  {event}")`」、`install.sh:517` 「`print(f"已装  {count} 处 hook -> 五个宿主")`」、`install.sh:529` 「`echo "齐了：${installed_dests} 处 × ${#wanted_names[@]} 个技能"`」——全文没有 `HOOKS-INSTALLED`
  - 全仓唯一出现处是验收标准的样例文本：`mmw-v2/skills/verify-ticket/tests/test_closeout.py:258` 「`print("HOOKS-INSTALLED")`」
- 建议正名：待用户拍板。选项 A：`install.sh --check` 在 hook 全齐时真打印 `HOOKS-INSTALLED`（词表与蓝图不动，`dispatch.sh run` 也多一个可核的字符串）。选项 B：删掉词条与蓝图那两句，`--check` 的判据只留退出码。

## 发现 8：「早上五条查询」没有读者了——人不看，`board.py` 也不跑

- 类型：断点
- 后果：词表里立着一个五条查询的概念，`12-decisions.md` H8 说它的读者从人换成 `board.py`，`15` §4.2 把五条写成 `board.py` 的数据源，而 `17-night-loop.md` §3 又说「数据源只有两个」，`board.py` 实际一条 `gh issue list` 都不跑。想按词表去核对早上的入口的人，追到哪一层都落空。
- 证据：
  - `CONTEXT.md:613-614` 「**早上五条查询（the five morning queries）**: The fixed set of issue-list queries used to survey the tickets from outside the pipeline…」
  - `docs/research/code-landing/12-decisions.md:526` 「那五条 `gh issue list` 查询不作废，**读者从人换成程序**：写进 `15-monitor-tab-and-wakeup-loop.md` §4.2 的数据源一节，`board.py` 与将来的唤醒闭环跑它们。」
  - `docs/research/code-landing/15-monitor-tab-and-wakeup-loop.md:72-76`（五条 `gh issue list …` 原文）
  - `docs/research/code-landing/17-night-loop.md:70` 「**数据源只有两个，不持有状态文件**（B8、G1）」，表里只有 `gh api …/sub_issues` 与 `gh issue view <n> --json …`
  - `mmw-v2/skills/dispatch/scripts/board.py:873-880`（`collect` 只调 `sub_issues` 与 `read_ticket`），全文无 `issue list`
  - `docs/research/code-landing/17-night-loop.md:21` 「早上入口 | spec 页 sub-issue 面板 + **两个书签** | H8」
- 建议正名：删 `CONTEXT.md` 的「早上五条查询」词条，改立一条「早上的入口 = spec issue 页 + 两个书签链接」（H8 的裁决）；`15` §4.2 标明数据源已被 `17` §3 取代。

## 发现 9：`TIME LIMIT:` 说的是「since dispatch」，`board.py` 数的是「从我第一次看见它起」

- 类型：脚本与文档不符
- 后果：早上读票的人看到「TIME LIMIT: 4 h since dispatch」，以为这张票占了会话四小时。实际计时器在 `board.py` 进程内存里：`dispatch.sh run` 用 `until … ; do sleep 5; done` 套着它，board 崩一次重起，四小时从头再算；board 启动前就在跑的会话，从 board 第一眼看见起算。
- 证据：
  - `mmw-v2/skills/dispatch/scripts/board.py:509-510` 「`TIME_LIMIT = ("TIME LIMIT: {hours} h since dispatch, still at phase={phase}. …")`」
  - `mmw-v2/skills/dispatch/scripts/board.py:642` 「`started = self.held_since.setdefault(number, time.monotonic())`」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:372-374` 「`# It keeps no state, so a crash costs nothing but the wait`」+ 「`herdr pane run "$pane" "until $watch; do sleep $BOARD_RESTART_SECONDS; done"`」
  - `CONTEXT.md:463-464` 「re-prompted `WAKE_LIMIT` times and it stopped again, or `MAX_HOURS` **passed since dispatch**」
  - `docs/research/code-landing/17-night-loop.md:184` 「`COOLDOWN_SECONDS` 与 `WAKE_BACKOFF` 的计时在 `board.py` 进程内存里，**重起归零**」（同一份文档只承认前两个常量会归零，没说 `MAX_HOURS` 也是）
- 建议正名：把措辞改成事实——`TIME LIMIT: {hours} h under this board`，`CONTEXT.md:464` 与 `17` §9 同改；或者把开工时间从票上读（`--preflight` 认领的时间戳），让「since dispatch」成真。待用户拍板。

## 发现 10：`models.md` 第五列，词表叫它「launch command」，表本身叫「launch arguments」，裁决说过里面不许出现程序名

- 类型：分岔
- 后果：按 `CONTEXT.md` 改表的人会往那一格里写整条命令（`cursor-agent -w issue-{n} …`）。`dispatch.sh` 把这一格整格塞进 `herdr agent start … -- "${args[@]}"`，于是 `cursor-agent` 变成传给 harness 的第一个参数，会话起不来。
- 证据：
  - `CONTEXT.md:391-393` 「**`models.md`**: The one table defining, for every agent, its host, model, thinking effort and **launch command**.」
  - `mmw-v2/skills/dispatch/models.md:22` 「`| agent | host | model | effort | launch arguments |`」
  - `docs/research/code-landing/12-decisions.md:342` 「**第五列不写 harness 的程序名**：`herdr agent start --kind` 按「宿主」列决定跑哪个程序，`--` 后面只收参数；写进去就是同一件事说两遍」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:222` 「`herdr agent start "$name" --kind "$host" --pane "$pane" -- "${args[@]}"`」
- 建议正名：`CONTEXT.md:392` 改成「launch arguments」，与表头、与 E2 的裁决一致。

## 发现 11：`junior-worker` 那一行的 effort 列是死数据，改它什么也不会发生

- 类型：冗余
- 后果：用户「换思考强度」时按词表和 `editing-models.md` 的说法去改 effort 列，`dispatch.sh` 只在启动参数里含 `{effort}` 时才用它——cursor 那行没有 `{effort}`，改了不生效，表却照常「说真话」的样子摆着。
- 证据：
  - `mmw-v2/skills/dispatch/models.md:24` 「`| junior-worker | cursor | \`cursor-grok-4.6-high\` | high | \`-w issue-{n} --worktree-base main --force --trust --model {model}\` |`」（启动参数里没有 `{effort}`）
  - `mmw-v2/skills/dispatch/references/editing-models.md:15` 「Cursor | `cursor-agent models` lists them. **The effort is burned into the slug**, so there is no bare `cursor-grok-4.6` — the high-effort build is its own name」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:159-165`（只在 `*'{effort}'*` 时校验 effort 列非空）
- 建议正名：cursor 的行 effort 列写 `—`（和 reviewer 行一样），并在 `models.md` 的说明里点明「effort 烧在模型名里的 harness，这一列写 `—`」。

## 发现 12：`issue-<n>-review` 被写成「分支名」，`MMW_TICKET` 被写成「派发时注入」——reviewer 两样都没有

- 类型：重复定义
- 后果：读词表的人以为 reviewer 有自己的分支和 `MMW_TICKET`。实际 reviewer 是在 worker 的 pane 上劈一刀、cwd 是 worker 的仓库根、名字只是 Claude Code 的会话名；关票 hook 因为没有 `MMW_TICKET` 对 reviewer 完全不生效。
- 证据：
  - `CONTEXT.md:395-396` 「**`issue-<n>` / `issue-<n>-review`**: The Herdr name **and branch name** of a worker and of its reviewer.」
  - `CONTEXT.md:399-400` 「**`MMW_TICKET`**: The ticket number injected into the session's environment **at dispatch**.」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:195-206`（reviewer 走 `herdr pane split --cwd "$root"`，没有 `--env`，也没有任何 worktree 参数）对比 `dispatch.sh:216-217`（worker 走 `herdr tab create … --env "MMW_TICKET=$number"`）
  - `mmw-v2/skills/dispatch/models.md:26` 「`| reviewer | claude | \`opus\` | — | \`--permission-mode bypassPermissions --model {model} -n issue-{n}-review\` |`」（`-n` 是 Claude Code 的会话名，不是分支）
  - `mmw-v2/skills/verify-ticket/scripts/hook.py:20` 「the dispatcher sets `MMW_TICKET` on the **worker's** pane. No variable, no gate.」
- 建议正名：`CONTEXT.md:396` 改成「worker 的 Herdr 名同时是它的 worktree 分支名；reviewer 只有 Herdr 名，跑在 worker 的 worktree 里」；`CONTEXT.md:400` 改成「派 worker 时注入」。

## 发现 13：`dispatch.sh` 的退出 1 有两个原因，SKILL.md 只写了一个；`run --role` 的校验比 SKILL.md 承诺的松

- 类型：脚本与文档不符
- 后果：① 看到退出 1 的调用方（含 `board.py`）按 SKILL.md 判定「没起来」，实际也可能是起来了、prompt 被拒。② `dispatch.sh run --role reviewer`（或任何 subagent 行）通过开跑前校验、退出 0，之后每一轮 `dispatch.sh <n> reviewer` 都退出 2，票一张都派不出去，而「没有开着的 ready-for-agent 票」永远不成立，夜里空转到天亮。
- 证据：
  - `mmw-v2/skills/dispatch/SKILL.md:38` 「`1` | The session is up but **never became ready in time**, so it was **not** told anything」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:225-229`：两处 `give_up`——「`was not ready within …s`」与「`would not take the prompt`」
  - `mmw-v2/skills/dispatch/SKILL.md:87` 「`2` | Nothing was started. The reason is on stderr: not inside Herdr, **no such role**, or `install.sh --check` found something missing」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:349` 「`[ -n "$(row_for_role "$role")" ] || refuse "no role named $role in $MODELS"`」（只查行在不在，不查它是不是 worker 行）对比 `dispatch.sh:155-158`（真正的拒绝发生在每次派发时）
  - `mmw-v2/skills/dispatch/scripts/board.py:812-816` 「`lane = [r for r in rows if r["state"] == "OPEN" and "ready-for-agent" in r["labels"]] ; return not lane and not held(rows)`」
- 建议正名：SKILL.md 的退出 1 改成「up but was not told anything（没及时就绪，或拒收 prompt）」；`run_night` 的校验加一条「该行的启动参数不能是 `—`」，理由与 `dispatch()` 里那条一样，只是提前到人还在的时候。

## 发现 14：`WAKEUP LIMIT:` 那句话对着两种不同的事说同一句「it went idle again」

- 类型：命名撞车
- 后果：worker 是第三次弹出提问表单被交回的，票上却写着「它又 idle 了」。早上判这张票的人据此以为会话是自己停的，不会去想「它一直在问问题」。
- 证据：
  - `mmw-v2/skills/dispatch/scripts/board.py:507-508` 「`WAKEUP_LIMIT = ("WAKEUP LIMIT: re-prompted {k} times and it **went idle again** at phase={phase}. …")`」
  - `mmw-v2/skills/dispatch/scripts/board.py:668-670`（`at_a_form` 里 `blocked` 到上限时用的是同一条 `WAKEUP_LIMIT`）
  - `mmw-v2/skills/dispatch/tests/test_board.py:631-636` 「`def test_a_third_form_hands_the_ticket_back` … `self.assertTrue(comment[-1].startswith("WAKEUP LIMIT:"))`」
  - `docs/research/code-landing/17-night-loop.md:91`（`blocked` 行的上限列写「同 `wake` 上限」，没说首行文字复用）
- 建议正名：`at_a_form` 用自己的一句（如 `WAKEUP LIMIT: dismissed {k} forms and it asked again at phase={phase}.`），首行仍是 `WAKEUP LIMIT:`，早上的读者才知道是哪一种。

## 发现 15：SKILL.md 的唤醒表列了三个 case 字面串，漏了第四个 `night over`

- 类型：断点
- 后果：主 agent 收到 `mmw board: night over #76 — …`，在 SKILL.md 的表里逐字找 `night over` 找不到（表里那一行叫「The night ended」），只能靠猜。
- 证据：
  - `mmw-v2/skills/dispatch/SKILL.md:105` 「A limit was reached — `WAKEUP LIMIT`, `REDISPATCHED`, `TIME LIMIT`」，`SKILL.md:106` 「The night ended | `NIGHT SUMMARY` is the newest comment on the spec」
  - `mmw-v2/skills/dispatch/scripts/board.py:823` 「`MAIN_LINE.format(case="night over", n=self.spec)`」
  - `mmw-v2/skills/dispatch/tests/test_board.py:803` 「`"mmw board: night over #76 — run board.py --once"`」
- 建议正名：SKILL.md 第二行的 Case 列写成「`night over`」，说明列再写「`NIGHT SUMMARY` 是 spec 上最新的一条评论」。

## 发现 16：同一格东西有四个名字：`host` / harness / `--kind` / 宿主

- 类型：命名撞车
- 后果：要换 harness 的人在 `models.md` 找不到「harness」这一列，在 `editing-models.md` 找不到「host」这一节；词表里 `host` / 宿主 一个词条都没有，无从对齐。
- 证据：
  - `mmw-v2/skills/dispatch/models.md:22` 表头 「`| agent | host | model | effort | launch arguments |`」，`models.md:8-9` 「the **host** column says which **harness** that session is」
  - `mmw-v2/skills/dispatch/references/editing-models.md:13` 表头 「`| Harness | Ask it this |`」、`editing-models.md:21` 「## 2. Confirm a **harness**」、`editing-models.md:24` 「The **host cell** has to name an **agent kind** Herdr recognises.」
  - `mmw-v2/skills/dispatch/scripts/dispatch.sh:222` 「`--kind "$host"`」
  - `CONTEXT.md` 全文没有 `host` / 宿主 的词条（`grep -n '^\*\*.*host' CONTEXT.md` 为空）
- 建议正名：`CONTEXT.md` 加一条「**host（宿主）**：`models.md` 的第二列，取值是 `herdr agent` 认的 kind」，`editing-models.md` 全文用 host，不再用 harness。

## 发现 17：`CONTEXT.md` 把 `board` 列进 `_Avoid_`，`SKILL.md` 通篇管它叫 the board

- 类型：幽灵词
- 后果：写文档的人不知道该写 `board.py` 还是 the board；`board.py` 自己打的日志行第一列就是 `board`。
- 证据：
  - `CONTEXT.md:431-433` 「**`board.py`**: The one resident program of the night… _Avoid_: **board**, 常驻进程, 看板」
  - `mmw-v2/skills/dispatch/SKILL.md:73` 「**the board** dispatches the frontier」、`SKILL.md:81` 「Defaults to **the board's** own `PARALLEL`」、`SKILL.md:98` 「## When **the board** re-prompts you」
  - `mmw-v2/skills/dispatch/scripts/board.py:541` 「`say("board", "watch", …)`」、`board.py:727` 「`say("board", "refuse", …)`」
- 建议正名：待用户拍板。选项 A：`_Avoid_` 里删掉 `board`（英文散文里 the board 指代 `board.py` 是可读的，日志第一列也需要一个短词），只保留禁「看板」「常驻进程」。选项 B：`SKILL.md` 全改成 `board.py`，日志第一列也改。

## 发现 18：`implement` 让人去 dispatch 的 SKILL.md 查 reviewer 的参数，那里没写起点 commit 怎么来；两处的等待正则也不同

- 类型：断点
- 后果：worker 走到收尾第 3 步，被指去 `dispatch/SKILL.md` 找「怎么填参数」，那里只说 `[base-commit]` 是「the commit the code review starts from」，没说从哪算（上一次 `VERDICT` 的 commit？分支起点？`main`？），worker 只能自己拿主意——而这正是 code review 的 diff 范围。
- 证据：
  - `mmw-v2/upstream/skills/engineering/implement/SKILL.md:34` 「`bash ~/.agents/skills/dispatch/scripts/dispatch.sh <n> reviewer <base-commit>` starts the reviewer session — **the dispatch skill's SKILL.md says how to fill the arguments** — then `… dispatch.sh wait <n> "^REVIEW " 1800`」
  - `mmw-v2/skills/dispatch/SKILL.md:33` 「`[base-commit]` | Only the `reviewer` takes one. It is the commit the code review starts from」
  - `CONTEXT.md:525-526` 「**base-commit（起点 commit）**: The first argument of the review dispatch line: where the diff starts.」（同样没说怎么算）
  - 正则两种写法：`mmw-v2/skills/dispatch/SKILL.md:53` 「A worker waiting on its reviewer uses `^REVIEW`」 对 `implement/SKILL.md:34` 「`"^REVIEW "`」
- 建议正名：在 `dispatch/SKILL.md` 的参数表里把起点 commit 的算法写死一句（建议：worker 分支与 `main` 的 merge-base，和 `code-review` 的三点 diff 同源，`code-review/SKILL.md:14` 「`git diff <base-commit>...HEAD`」）；正则统一写 `^REVIEW`。

## 发现 19：`12-decisions.md` J11 那句裁决自相矛盾

- 类型：断点
- 后果：块 J 是这套词的裁决书。这一句同时说「就用判据本身当名字」和「这个判据是我自造的、用户当场否掉」，读它的人不知道到底该不该用 `idle` 而 `phase` 未到 `closed`/`handoff` 这个说法。
- 证据：
  - `docs/research/code-landing/12-decisions.md:636` 「这个状态不起名：写它的判据本身「`idle` 而 `phase` 未到 `closed`/`handoff`」（H1 第 3 条给的就是这两个 token；「`idle` 而 `phase` 未到 `closed`/`handoff`」**是我 2026-08-31 自造的，用户当场否掉**）」
  - `CONTEXT.md:415-417`（词表采纳的正是这个判据，`_Avoid_` 里是「半途停下」那一串）
- 建议正名：括号里被否掉的那个名字应当是「半途停下」一类的自造词，改回去。

## 旁证（不在仓库内，不计为发现）

- `~/.claude/skills/herdr -> ../../.agents/skills/herdr`，指向 `/Users/cheuklapchan/.agents/skills/herdr`——一个真实目录，只有一份 `SKILL.md`（2026-08-21），**不是** 本仓的软链，也不在 `mmw-v2/skills.txt` 里；`mmw-v2/skills/herdr` 不存在。本仓对 Herdr 技能正文没有控制权。
- 那份 `herdr/SKILL.md:128` 写着「It rejects an agent already waiting at an approval or question dialog with `agent_blocked` before sending any input. **Inspect the blocked UI and ask the user before answering it.**」——与本簇的纪律正相反：`mmw-v2/skills/dispatch/SKILL.md:93-96` 「you do not answer a question a worker put on screen — the board comments the form on the ticket, dismisses it, and sends the worker its dispatch line again, because the discipline is not to ask」。夜里同时加载两份技能的会话会拿到两条相反的指示。
- 同一份 `herdr/SKILL.md:120` 说 `agent start` 的默认超时是 30 秒，`dispatch.sh:19` 的 `IDLE_TIMEOUT_MS=120000` 是它之后再等的一段，两者不冲突，但 SKILL.md 的退出码表（「never became ready in time」）没说这 120 秒是第二段等待。

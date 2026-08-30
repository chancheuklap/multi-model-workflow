# 监控 tab 与唤醒闭环：agent 之间怎么交换信息，上级怎么把停下的下级捡回来

`14-herdr-utilization.md` 盘的是 Herdr 有哪些能力、一张票在里面怎么摆。本文回答另一个问题：这套东西自动跑起来时，**信息在 agent 之间怎么流动**，**下级 `idle` 而 `phase` 未到 `closed`/`handoff` 时上级做什么**，以及**这一切摆在哪个界面上给人和 agent 同时看**。本文只调查、只提议，不定案。

取证时间 2026-08-29。新增的取证来源：herdr 官方插件文档（`https://raw.githubusercontent.com/herdrdev/herdr/v0.8.2/docs/next/website/src/content/docs/plugins.mdx`）与市场文档（同目录 `marketplace.mdx`）、GitHub 上带 `herdr-plugin` 话题的仓库（`gh api search/repositories -f q='topic:herdr-plugin'`，2026-08-29 查得 882，这个数每天在涨）中六个同类项目的 README 与 manifest、本机 `herdr plugin` 命令组清单。

## 1. 「自动化 = 信息交换直到终点信息出现」成立，但要分开两种信息

命题本身成立：一条流水线跑完，等于「每一环把自己的产出交给下一环，直到出现代表终点的那条信息」。本仓的终点信息早已定义好——票上收尾评论的首行 `ALL MET`（关票）或 `HANDOFF REQUIRED`（换 `ready-for-human` 标签，不关票），见 `08-failure-vocabulary.md` §5.3 与 `12-decisions.md` 0.2「失败词汇」行。

要加的一句限定是：**交换的信息分账本与通知两种，它们不能放在同一处。**

| | 账本 | 通知 |
| --- | --- | --- |
| 内容 | 发生了什么：EVIDENCE、VERDICT、收尾评论、Outside Owns、sub-issue | 有变化了：某个 pane 从 working 变成 idle，某张票的 phase 变了 |
| 载体 | GitHub Issue | Herdr 的 pane token 与事件推送（`14` §4.1） |
| 寿命 | 永久、跨机器、用户在网页上直接看 | 会话内，pane 没了就没了 |
| 谁读 | 人、任何时候的任何 agent | 本机此刻醒着的监控端 |

同一个切分出现在 `husniadil/herdr-dispatch` 的 README 里，原话是「The board stays the ledger; this binary is only execution policy.」——board（它的任务板）是账本，dispatcher 只是执行策略。那是另一个人为同一类问题独立做的划分。

推论：**唤醒信号不该写进票**。票是用户唯一常看的界面，把「它 idle 了」「它又动了」这类心跳灌进去会淹掉真正要读的评论，而且读回来还得轮询。心跳留在 Herdr 里（一写即广播，`14` §1 表末行实测），票只承接结论。

## 2. 「未到终点就停下 → 上级唤醒、诊断、重新 prompt」也成立，且已有人做出来

同意，且它不是新发明——GitHub 上带 `herdr-plugin` 话题的八百多个仓库里，这条闭环的每一段都有现成实现。下表是六个同类项目，都在本次取证中读过 README 或 manifest。

| 项目 | 它做的事 | 对我们有用的部分 |
| --- | --- | --- |
| `andybarilla/herdr-scuttlebutt` | 给一个 Herdr 会话里的 agent 一间共享聊天室：agent 用 CLI 发帖，**守护进程用 `herdr agent prompt` 把新帖推给空闲的 agent**，另有一个 TUI pane 让人旁观并以 `human` 身份发言 | 「agent 之间交换信息」的完整实现范式；投递条件与失败处理（§3） |
| `rcosteira79/herdr-autocontinue` | 盯着 agent 撞用量墙，从 pane 里读出重置时间，窗口重开时**替你按下继续** | 「重新 prompt 一个停下的 agent」的安全规则（§3） |
| `husniadil/herdr-tasks` + `husniadil/herdr-dispatch` | 一块任务板（带租约的认领、以证据为准的复查、人的决策闸门）加一个派发器（每张 ready 的票一个 worker pane，交付目标、跟踪 worker、在复查处交棒） | 与本仓 #60 的结构几乎同构；「board 是账本、dispatcher 是执行策略」的说法 |
| `jirathip-dev/corral` | 守护进程读 Herdr socket 与 git，汇成一份实时快照，用 HTTP + SSE 供桌面看板和手机 app 使用，可远程 prompt / 打断 / 批准 / 读输出 / 停止 | 「被挡住的 agent 排在最前，并显示它正在等的那个问题」这条排序规则 |
| `DnzzL/herdr-automations` | 给 agent 排定时任务：一个提示词、一行 cron、每次一个新 worktree，另有一块实时板 | 定时派发的形态（本轮不需要） |
| `miiraheart/herdr-beads`、`KokiKono/herdr-kanban`、`ukwhatn/taskherd` | 把外部任务系统（beads、SQLite、Jira）画成 Herdr 里的板 | 板与外部账本的绑定方式 |

安装与发现的机制：仓库打上 GitHub 话题 `herdr-plugin`、默认分支里有一份能解析的 `herdr-plugin.toml`，就会进 `herdr.dev/plugins` 的索引；装一个是 `herdr plugin install <owner>/<repo>[/subdir]`（本机 `herdr plugin` 命令组实测存在，只是不在顶层 `--help` 里）。

## 3. 重新 prompt 别人之前必须满足什么：七条

前五条抄自上表两个项目在真实使用中付出的代价，后两条是 Herdr 自己的拒绝行为。任何「唤醒下级并让它继续」的实现都要满足这七条，否则它会打断正在工作的 agent、把字打进正在等审批的对话框、或者对着一个已经死掉的 pane 反复敲。

1. **只在对方 `idle` 或 `done`、且它的 pane 没有被聚焦时投递。**（scuttlebutt：「Delivery only happens while herdr reports an agent `idle` or `done` and its pane is not focused」）——工作中的 agent 与正在敲键盘的人都不会被打断。被聚焦的 pane 无限期推迟，焦点移开后整批投递。
2. **发送方的身份从 `$HERDR_PANE_ID` 解析，拒绝匿名。**（scuttlebutt 的 `post`）
3. **动手前重新确认一次状态。**（autocontinue：resume 触发前再查一遍这个 agent 仍然空闲、不是正在等你批准，而且它停下的那个原因还在）——中间隔了一段时间，状态可能已经变了。
4. **退避递增，并且有上限。**（autocontinue 五次后放弃并标 `⚠`；scuttlebutt 从约一分钟翻倍到半小时）——不能对着同一个 pane 无限重试。
5. **名字不等于身份。**（scuttlebutt：pane 重启后同名可能已是另一个会话，所以校验 `agent_session` 的 id）——`14` §3 的 `issue-<n>` 是定位句柄，认准某个具体会话要配上 `agent_session.value`。
6. **对方停在审批或提问对话框时，`herdr agent prompt` 一个字节都不发，直接返回 `agent_blocked`。**（`~/.claude/skills/herdr/SKILL.md:128`）——所以 `blocked` 状态下唤醒是无效动作，要先弄清它在问什么。
7. **prompt 发出后五秒内没有观察到生命周期变化，Herdr 返回 `agent_prompt_stalled`。**（`SKILL.md:130`）——这是「这个 pane 已经不接受输入了」的判据，不必自己造超时。

## 4. 监控 tab 该长什么样

### 4.1 硬约束：全屏 TUI 的内容 agent 读不到

备用屏（alternate screen）上滚出去的行不进 Herdr 的滚动缓冲，`herdr agent read --lines` 加大也读不回来（`09-herdr-dispatch-model.md` §1.5）。Claude Code 在备用屏上跑是 `09` §7 的实测；grok 与 codex 默认在备用屏是 `09` §3.2 从两家 `--help` 都有 `--no-alt-screen` 推断的，未实测。一个用备用屏画的全屏 TUI 面板（scuttlebutt 的聊天 pane、corral 的看板都是这种）对**人**很好，对**agent** 是黑的。

用户要的是「既能被 agent 看懂并利用，也能被人类看懂」。所以监控端不能只是一个 TUI。

### 4.2 一个程序，三种形态，同一份数据

```
board.py --once      打印一屏当前状态然后退出        agent 调用；上级醒来后的第一件事
board.py             常驻，每次事件到来追加一行      开在 tab 里给人看；不进备用屏，所以 herdr pane read 也读得到
board.py --watch     同上，并按 §5 的规则动手        唤醒闭环本体
```

三种形态读的是同一个数据源，没有第二份真相：`herdr api snapshot`（拿每个 pane 的 `agent_status` 与 `tokens.ticket/role/phase/ac`，`14` §4.2）加下面这五条 `gh` 查询。

这五条原本写在蓝图页步 13、`#60` 的 User Story 15 里，读者写的是「用户」——而本仓的用户在 GitHub 网页上看票，不敲命令（H0 第一条）。人的入口因此改成「打开 spec issue 那一页（原生 sub-issue 面板给出每张票的开关状态与完成度，worker 夜里用 `--parent <spec>` 开的 sub-issue 也在同一个面板里；票页面上的原生 Blocked by 区块给出还卡在谁身上）加两个书签链接（`label:ready-for-human` 要人处理的、`label:ready-for-agent` 加 `assignee:@me` 可能死掉的会话）」。查询本身不作废，**读者换成这个程序**：

```
gh issue list --state open --label ready-for-human                       # 要人处理的
gh issue list --state closed --search "closed:>=<昨天>"                  # 夜里做完的
gh issue list --state open --label ready-for-agent --assignee @me        # 认领了却没收尾评论
gh issue list --state open --label needs-triage --search "parent:<spec>" # 夜里新开的 sub-issue
gh issue list --state open --json number,title,blockedBy --jq '.[]|select(.blockedBy|length>0)'
```

出处 `08-failure-vocabulary.md` §5.4；第三条依赖 worker 开工时的 `--add-assignee @me`；「评论首行能否被 `--search` 稳定命中」未实测（`08` §8 末条），这条不确定性正是它不适合当人的入口的原因之一——程序可以退回逐条读评论，人不会。**不持有自己的状态文件**——与 `12-decisions.md` B8 给 `verify-ticket.py` 定的同一条纪律，理由也一样（`10-previous-attempt-postmortem.md` §3.a.3：镜像文件会漂移）。

常驻形态用追加输出而不是重绘，这一条同时解决三件事：人可以往回滚看历史；`herdr pane read --source recent-unwrapped` 读得到；不需要任何 TUI 库。

### 4.3 输出的样子

`--once` 是一张表，一行一张票，列固定：

```
mmw board · 02:14 · 5 张票在跑

 票    agent            状态     phase       AC     停了多久  备注
 #61   issue-61         working  implement   -      -
 #62   issue-62         idle     selfcheck   3/5    6m        idle 而 phase 未到 closed/handoff
 #63   issue-63         blocked  verify      5/5    2m        verifier 在等审批
 #64   -                -        closed      6/6    -         ALL MET，已关票
 #65   -                -        -           -      -         等 #62
```

常驻形态是一行一件事，时间戳打头：

```
02:14:31  #62  idle       phase=selfcheck ac=3/5    phase 未到 closed/handoff，去读票
02:14:33  #62  诊断        最后一条评论：self-run，AC3 失败：pytest exit 1
02:14:35  #62  prompt     第 1 次（上限 3）：继续修 AC3，修完跑 verify-ticket.py 62
02:14:38  #62  working
```

两种输出里出现的词全部是这套流程已有的词：`phase` 的取值（`14` §4.2 表）、Herdr 的状态词（`idle`/`working`/`blocked`/`done`/`unknown`）、`ALL MET` / `HANDOFF REQUIRED`（`08` §5.3）、`VERDICT` 五级（`12-decisions.md` B4）。没有为看板另造一套词，人和 agent 读到的是同一批名词。

### 4.4 这个 tab 怎么开

两条路，都不需要新基建：

- **最短**：`herdr tab create --label "mmw board" --cwd <仓库根> --no-focus`，拿返回的 `root_pane.pane_id`，`herdr pane run <id> "python3 <路径>/board.py"`。派发脚本 `dispatch.sh`（#67）本来就要做 `tab create`，多一个 tab 是同一套调用。
- **官方形态**：写成 Herdr 插件，manifest 里 `[[panes]] id = "board" / placement = "tab" / command = [...]` 加一个 `[[actions]]` 用来打开它，之后 `herdr plugin pane open --plugin <id> --entrypoint board --placement tab --focus`。scuttlebutt 的 `herdr-plugin.toml` 与 `scripts/open-chat-tab.sh` 是现成的两页模板。好处是能绑快捷键、能被 `herdr plugin log list` 收集日志、将来能分享出去；代价是多一个 manifest 与安装步骤。

先走第一条，等这套东西稳定了再包成插件——插件形态不改变 `board.py` 本身。

## 5. 唤醒闭环的最小形态

上级（main agent 或 `board.py --watch`）在每次 `pane.agent_status_changed` 推送后做一次判断，输入只有两样：Herdr 的状态与 phase token（`14` §4.1 的合看表）、票的最后一条评论。

| 观察到 | 上级做什么 |
| --- | --- |
| `working` | 不动 |
| `idle`/`done` 且 `phase` 是 `closed` 或 `handoff` | 到终点了，登记，不动 |
| `idle`/`done` 且 `phase` 是别的值 | **这就是 `idle` 而 `phase` 未到 `closed`/`handoff`**：读票的最后一条评论与 `herdr agent read` 最近的输出，判断它停在哪一步，按 §3 的七条重新 prompt 它继续 |
| `blocked` | 读它在问什么（`herdr agent read`）。§3 第 6 条：这时 prompt 无效。要么答，要么记成票上的一条评论交给人 |
| `unknown` 或 pane 消失 | 会话没了。票没关也没 HANDOFF，则这张票要重派或交人 |
| `agent_prompt_stalled` / 重试到上限 | 停手，在票上留一条评论说明，换 `needs-triage` |

「诊断」这一步要读什么，本仓已经有答案，不需要新东西：票上最后一条评论（`verify-ticket.py` 每次自跑都会贴一条，含每条 AC 的结果，#60 第 2 节）就是它停在哪的直接证据；读屏只是补充，且不可靠（§4.1）。

这套判断本身不需要模型——它是一张查表。**只有「重新 prompt 时说什么」需要模型**，而多数情况下那句话是固定的（「继续：上一步 `verify-ticket.py <n>` 有 N 条 AC 未过，修完再跑一次」）。所以 `board.py --watch` 能独立完成大部分捡回动作，只在查表落到最后两行时才叫醒 main agent。

## 6. 「需要人决策的地方应该小到能记进 issue」与现有定案的差距

用户的原则：任何需要人决策的地方都应该小到可以先记录在 issue 里、等人重新决策后再精确修改；夜里不该出现整条流水线停下来等人的情况。

现状（`08-failure-vocabulary.md` §5.3、`12-decisions.md` 0.2、B6）：一条验收标准做不下去时写 `ABANDON: AC<n> <failed|blocked|impossible|decision> <理由>`，**只要有一条 ABANDON，整张票就是 `HANDOFF REQUIRED`**——不关票、不关 PR、`ready-for-agent` 换成 `ready-for-human`。也就是说一条标准需要人拍板，整张票就停在那里等人。

差距在 `decision` 这个 kind 上：按用户的原则，它应该触发「**把这个决策点开成 spec 下的 sub-issue（`--parent <spec> --label needs-triage`），票的其余标准继续做完**」，而不是让整张票停住。这个通道本仓已经有了——`12-decisions.md` 0.1「写码中发现契约装不下」定的就是「继续做，在 spec 下开 sub-issue 记录」——只是没有接到 `ABANDON: decision` 上。

用户已裁决取甲（`12-decisions.md` H3）：`ABANDON: AC<n> decision <理由>` 触发「在 spec 下开 sub-issue（`--parent <spec> --label needs-triage`）+ 继续做完其余标准」，只在其余标准也没过时才整票 `HANDOFF REQUIRED`；`failed` / `blocked` / `impossible` 三个 kind 维持整票 HANDOFF。

另外两个 kind 的处境不同，不跟着改：`blocked`（等外部条件）与 `impossible`（做不到）本来就不是人一句话能解决的，整票交人是合理的；`failed`（跑了没过）在自动化下应该先走重试，到上限才算 ABANDON——上限定为同一条 AC 连续三轮（`16-stall-and-loop-risks.md` S11）。

带 `MANUAL:` 的标准是同一个问题的另一面：它必然 unmet，于是带人工项的票夜里必然 `HANDOFF REQUIRED`，首行分不清「出事了」和「一切正常只等你看一眼」。选项与状态见 `16-stall-and-loop-risks.md` §1.2 与 S3，待用户拍板。

## 7. 落点与待定

| 事项 | 状态 | 落在哪 |
| --- | --- | --- |
| `board.py` 三种形态、数据源、输出格式 | 待用户定形态后可落地 | `mmw-v2/skills/verify-ticket/scripts/`（与 `dispatch.sh`、`verify-ticket.py` 同处，#60 第 2 节） |
| 开 board tab 的命令 | 同上 | `dispatch.sh`（#67） |
| §3 的七条唤醒规则 | 调查结论，可直接引用 | 写唤醒实现时；#60 Out of Scope 的「夜间编排主循环」 |
| §5 的查表 | 待定 | 同上 |
| `ABANDON: decision` 改为开 sub-issue 后继续做完其余标准 | 已定（`12-decisions.md` H3） | #73（`implement` 收尾）、#60 第 9 节第 5–6 步、`08-failure-vocabulary.md` §5.3 |
| 带 `MANUAL:` 的票怎么收尾 | **要用户拍板** | `16-stall-and-loop-risks.md` S3 |
| 把这套东西包成 Herdr 插件 | 以后 | — |

`12-decisions.md` 的 P0 定的是「主 agent 派完 worker 只读票」，#60 的 Out of Scope 把夜间编排主循环整个留到以后。本文写的 §5 与 §3 是那件事的材料，不是它的定案；#62、#63、#64、#67 这几张票不应该为了迁就某一种唤醒方的形态而改形状——它们只需要产出 `phase` token 这一个输入。

## 8. 未读、未测

- 六个同类项目只读了 README 与 manifest，没有读实现，也没有安装运行。`herdr plugin install` 会执行仓库里的 `[[build]]` 命令（scuttlebutt 是 `cargo build --release`），装之前要看过那段脚本。
- 追加式输出在 Herdr 的滚动缓冲里能保留多少行，未测；`herdr pane read --lines` 的实际上限也未测。
- `board.py` 常驻进程与 Herdr 的 `events.subscribe` 断线重连行为未测（`user.space-status` 那类插件是「每次事件 spawn 一个短命进程」，不是长连接，没有这个问题）。
- `herdr agent read` 在 `blocked` 时能否稳定读到对方正在问的那句话，`09` §7 只在 Claude Code 上测过一次。

# R5 night 单元的逐项归置

本文按 `docs/research/workflow-compare/reports/R4-mmw-architecture-form.md`（下称 R4，引用写成「R4 D3.5 f」）逐项归置 night 单元，准绳是 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`（下称 L7）第 C 节。`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）是被审视的对象。

单元范围：`dispatch` 技能全部（`SKILL.md` 含 `## On waking`、`references/night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md`、`scripts/` 下 `dispatch.sh`、`relay.py`、`watchdog.py`、`status.py`、`models.py`、`runners/`、`statedir.py`、`ghlist.py`、`hosts.json`）；两个 hook（`tool-guard.py`、`turn-guard.py`）；`retro` 技能；夜的角色 orchestrator。

标注：「已核实」＝本轮回到原文或跑命令看到；「推断」＝由原文推出；做不出判断的在第 8 节。

---

## 0. 结论（先读这里）

1. **本单元没有要搬家的文件，技能与脚本层也不新建文件（唯一的新文件是修订 ADR 0020 的一份新 ADR，第 1 节 Q2）。** `night.md`、`one-ticket.md` 是 orchestrator 的角色操作文件（R4 D3.1），原位；`retro` 是能力技能，整份不动；四个 reference、全部脚本、两个 hook、`hosts.json` 的位置都不变。所有改动都是在原文件里修断点、去重复、接上角色指针。
2. **角色指针的对应表放进 `relay.py`，紧挨 `WAKES`，不另建模块。** `WAKES` 决定叫醒哪个角色，指针说这个角色去哪里，放在一起，以后加事件或角色只改一处。`watchdog.py` 本来就导入 `relay.py`；`dispatch.sh resume` 经新增的 `relay.py pointer` 子命令取指针。两个 hook 不导入它，理由见第 1 节 H1。
3. **指针必须接在同一行末尾，不能另起一行。** `watchdog.py` 第 813 行原文：「One line: a runner types what it is handed into a terminal, where a newline submits.」R4 D1.2 写的「末尾加一行」照字面做，会让 runner 把指针当第二条消息提交。本文改为同一行，用 ` · ` 隔开（已核实）。
4. **发现一处 R4 没列的断点：夜外 `adopt` 的 watch 和 `open-ticket` 的 watch 在 `watches.json` 里长得一样。** 两者都经 `open_relay --tickets <n>` 以调用会话为 MAIN 开 watch（`dispatch.sh` `open_relay` 第 629–642 行、`adopt_ticket` 第 65–70 行，已核实）。按 `to` 加 watch 类型生成指针，会把一个自拿票的 worker 送进 `one-ticket.md` 第 4 步去跑 `land`，而 `inside-a-ticket.md` `## After the closeout` 明文禁止它跑。修法：`open_relay` 记下开 watch 的命令（`by: open | open-ticket | adopt`），指针按它选文件；`inside-a-ticket.md` 补一句收到其他唤醒时怎么办。
5. **orchestrator 的 `RESUME:` 与 `night.md` 事实表合并成一份，而不是并存。** 事实表第 2、4、5、6 行是按 spec 上的事件算位置，这正是 `dispatch.sh` 的 `newest_field`（第 232–259 行）与 `finish` 的前置检查（第 4166–4177 行）已经在做的事。改由 `status.py --table` 首行印 `RESUME: <night.md 小节标题>`，事实表只留三行脚本算不出的（醒来的是什么、要不要挂起、用户说没说）和一行「其余：看 `RESUME:`」。V6（缺「retro 已记录、用户未验收」一行）随之成为脚本的一个状态。
6. **`MMW turn guard:` 不进 `## 3` 的表，改在事实表单列一行「照它做」。** 这条消息自带全部步骤并以「Then end your turn.」结尾（`turn-guard.py` 第 306–311 行），`## 3` 的五步（`status`、`advance`）对它不适用。这样修 V7，又不在技能文本里复述 hook 的文字。
7. **与 R4 的三处偏离，均为工程决定：** 指针在同一行（上面第 3 条）；`retro` 第 186 行的返回句不换成固定返回句（第 1 节 N5、第 5 节）；词条 **role pointer** 进 `docs/contexts/night/CONTEXT.md`，不进 toolbox（第 1 节 Q3）。
8. **本单元没有需要 owner 做的产品决定**，只有一处可选的范围问题（第 7 节）。

---

## 本轮读了什么、核实了什么

| 材料 | 读法 |
|---|---|
| R4 | 全文（任务附带） |
| L7 | 第 0 节、A.2、A.4–A.6、A.10、第 C 节全文、第 D 节 |
| N1 | 全文 |
| N7 | 第 1.1、2.1、3.1 节与 retro 相关的第 4、6、8 节行 |
| N8 | 第 2.5、2.6、4、8、9 节 |
| N10 | 第 3、4、5、9、10 节 |
| N11 | 全文 |
| `mmw-v2/skills/dispatch/SKILL.md`、`references/night.md`、`one-ticket.md`、`inside-a-ticket.md`、`editing-models.md` | 全文 |
| `mmw-v2/skills/retro/SKILL.md` | 全文 |
| `mmw-v2/upstream/skills/engineering/implement/SKILL.md` | 第 1–101 行（全文到 `## Closing steps` 末） |
| `code-review/references/session.md` | 标题列表与第 36–50 行 |
| SSR | 第 1–140 行 |
| `dispatch.sh` | 第 60–110、232–259、629–642 行，`adopt_ticket` 中与 relay 相关的行，第 1935–1975、2065–2078、2150–2290（`resume_one`、`ended_worker_hold`）、4105–4120、4166–4177、4705–4725 行 |
| `relay.py` | 第 1–60、158–185、280–300、355–395、1040–1075、1195–1210 行；import 段 |
| `watchdog.py` | 第 60–115、720–800、808–818 行；import 段 |
| `turn-guard.py` | 第 1–35、280–340 行 |
| `tool-guard.py` | 第 1–100 行、`no_kill`、`run_pretool` 开头 |
| `status.py` | 头注释、函数目录、`night_opened`、`table` |
| `verify-ticket.py` | `resume_at`（第 2148–2181 行） |
| 测试 | `tests/relay/test_relay.py` 第 365、433 行；`tests/dispatch/test_tool_guard.py` 第 63、440–450 行；`tests/liveness/test_liveness.py` 第 767 行；`tests/liveness/test_guard.sh` 第 117–123 行；grep 各套件对告警与拒绝文字的断言 |

**没读的**：`runners/*.sh` 的动词实现、`models.py`、`statedir.py`、`ghlist.py`、`hosts.json` 的正文、`retro.py`、`status.py` 的函数体、`dispatch.sh` 其余约 4000 行。这些部件在本方案里全部不动；对它们的描述取自 N1、N7，已在引用处注明。

**本轮核实并影响归置的新事实**（R4 第 1 节之外）：

| # | 事实 | 出处 |
|---|---|---|
| W1 | runner 把收到的文字敲进终端，换行等于提交，所以脚本送的消息必须是一行 | `watchdog.py` 第 813 行 |
| W2 | 夜外 `adopt` 以 adopt 的会话为 MAIN 开 `tickets` watch，与 `open-ticket` 在 `watches.json` 里无从区分（字段只有 `watch`、`runner`、`session`、`at`、`stopped_since`） | `dispatch.sh` `adopt_ticket` 第 65–70 行、`open_relay` 第 629–642 行；`relay.py` 头注释第 174–178 行 |
| W3 | `one-ticket.md` 第 3 步列出的唤醒里没有 `relay.recovered`，而 `relay.recovered` 发给每个 watch 的 orchestrator，含单票的 | `one-ticket.md` 第 3 步；`relay.py` 第 44–47、163–164 行 |
| W4 | `watchdog.py` idle 告警里给 worker 的 `resume` 原文写「If something outside your code stops you, open a fault sub-issue … then stop; if only a person can settle it, open a decision sub-issue, take the default and carry on」；`implement` 第 18 行把 `fault` 限于「the pipeline itself (the pipeline's own scripts, a hook, or `.mmw/target.json`)」，第 76 行把缺凭据、设备归为 `ABANDON … stuck`。两处对「外部原因卡住」给了不同出路 | `watchdog.py` 第 745–754 行；`implement/SKILL.md` 第 18、23、76 行 |
| W5 | `resume` 的退出码：0 送达且回合开始（无输出）；4 送达但看不到回合开始，stderr 说不要再发；3 对方在回合中，stderr 说结束回合、下次唤醒再发，连续两次则 `start <n> worker` 替换；2 由 `refuse` 给出去处（`retract`，或 `ended_worker_hold` 按结束事件给出的命令） | `dispatch.sh` 第 2190–2220、2222–2280 行 |
| W6 | `dispatch.sh status` 只调用 `status.py --table`；`status.py` 不读 spec 自己的夜事件；spec 的夜事件由 `dispatch.sh` 的 `newest_field` 读（`spec.opened`、`spec.suspended`、`spec.closed`、`spec.retroed`、`spec.merged`）；任务板不调用 `status.py` | `dispatch.sh` 第 4715–4719、232–259、4166–4177 行；grep `mmw-v2/board/` 无命中 |
| W7 | `NO_QUESTION` 有长度测试：`HOST_PREFIX + len(NO_QUESTION) <= REASON_LIMIT`（256，Grok 截断 deny reason 的实测值）；现文 242 字符；另一测试断言它含 `ABANDON: AC<n> decision` 与 `needs-triage` | `tests/dispatch/test_tool_guard.py` 第 440–450 行；`ui-acceptance/scripts/refusal.py` 第 21–28 行 |
| W8 | `relay.py` 在导入时加载 `statedir`、`ghlist` 与 `events.py`；`tool-guard.py` 每条 shell 命令前都被宿主调用 | `relay.py` import 段第 1–33 行（相对第 238 行）；`tool-guard.py` 头注释第 22–26 行 |
| W9 | `how-it-works.md` 第 81 行仍说沉默 worker 的消息在 `night.md` `Exit codes of resume` 下；实际在 `watchdog.py` | `docs/contexts/night/how-it-works.md` 第 81 行；`watchdog.py` 第 749 行 |
| W10 | reviewer 无法判定时的出路是报告里的「Could not tell」 | `code-review/references/session.md` 第 45 行 |

---

## 1. 归置表

动作只用：不动 / 移动 / 拆分 / 合并 / 回到上游原文 / 删除 / 新建 / 改写。收益只写用户要求 2 的六种之一。「批」指 R4 第 11 节的落地批次。

### 1.1 `dispatch/SKILL.md`（28 行，流水线角色入口，R4 D2.3）

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| A1 | frontmatter `description` | 原位（能力技能 `dispatch` 的触发） | 改写（批 2） | 删「Start a reviewer from inside a ticket,」 | 去掉经核实的真重复：`implement` description「Use when you were dispatched onto a ticket」与其第 3 步「Start the reviewer」已认领这一时刻（N10 B7、R7；本轮读 `implement` 第 3、84 行） | −7 词 | SSR `### Descriptions` 第 2 条（两份 description 争一件事）得到执行。worker 仍靠 `implement` 第 8 行「the `dispatch` skill's `dispatch.sh`」按名找到本技能，不靠这句 description |
| A2 | 第 8 行「Choose the moment … Where you are is what the ticket's events say, not what this session remembers. …」 | 原位 | 改写（批 3） | 句末加括注 `(the \`mmw\` skill's principle \`the-tracker-is-the-state\`)` | 让原则被两个以上调用方复用（R4 D4.4 把本句列为该原则的原句出处） | +1 括注 | — |
| A3 | 第 12 行 night 定义 | 原位 | 不动 | — | — | 0 | 与 `docs/contexts/night/CONTEXT.md` **night** 重复，但读者不同（agent / 维护者），N1 R1 |
| A4（已被 R12 K-47 改定） | `## Find your moment` 表第 1 行 | 原位 | 改写（批 1） | 「the worker a `start` put on a ticket, starting its reviewer or woken on its ticket → No file: the `implement` skill's `## Closing steps`」改为「the worker a `start` put on a ticket, woken on it → `## On waking` below, then the `implement` skill's `## Closing steps`」 | 消除已核实断点 B9：worker 读不到 `## On waking` 第 1 步「Run that command again first」（N10 B9，本轮重读 `implement` 全文无 `On waking`）；同时删去 B7 的第二处声称（「starting its reviewer」） | ±0 行 | `dispatch.sh` 第 79 行头注释「`## On waking`, which every moment shares」从此对 worker 也成立 |
| A5 | 表第 2–6 行 | 原位 | 不动 | — | — | 0 | 各行对应一个分支（SSR 事实 5），L7 C.1 第 7 问 |
| A6 | `## On waking` 四步 | 原位 | 改写（批 3），只加括注 | 第 1 步句末加 `(the \`mmw\` skill's principle \`rerun-dont-reroute\`)` | 原则复用（R4 D4.4 的引用处） | +1 括注 | 四步本身是天然整体（N1 第 8 节）：ack 必须在读之后、长工作之前 |

### 1.2 `references/night.md`（210 行，orchestrator 的角色操作文件）

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| B1 | 开头五段（第 3–11 行） | 原位 | 改写（批 3），只加括注 | 第 7 行（「The night's output is a batch …」）句末括注 `silence-is-never-a-pass`；第 11 行（「… no agent polls another.」）句末括注 `the-tracker-is-the-state` | 原则复用（R4 D4.4 表把 `night.md` 第 7 段列为理由出处、`night.md` 列为引用处） | +2 括注 | 第 5 行已说清夜留下什么、给谁读，功能等同 R4 D3.2 的 `**Leaves:**`，不再加这一行（见第 5 节） |
| B2 | 事实表（第 13–22 行，6 行） | 原位 | 改写（批 1） | 保留并改写为 4 行：(1)「A wake arrived: `#<n> <event>`、`relay.recovered since <time>`、a line of `watchdog:` alerts → `3. Each time something wakes you`」；(2)「An `MMW turn guard:` line → do what it says; it names every step and is not acked」；(3)「You are deciding to stop the night because the fault is in the pipeline → `Suspending the night`」；(4)「Anything else → `bash scripts/dispatch.sh status <spec>`; its first line `RESUME: <section>` names the section, read off the spec's night events and the frontier. `1. The user says the night starts` only once the user has said so; `6. Merge the accepted night` only once the user has accepted the result, and until then the last paragraph of `5. The night is over`.」 | 去掉经核实的真重复：原第 2、4、5、6 行按事件判位置，与 `dispatch.sh` `newest_field` 的「newest of spec.opened/suspended/closed」（第 320、2770、3615 行）和 `finish` 的「spec.retroed recorded after spec.closed」检查（第 4166–4177 行）是同一判定；消除已核实断点 V6（缺「retro 已记录、未验收」行，成为 `RESUME:` 的一个取值）与 V7 的前半（`MMW turn guard:` 被送到 `## 3`） | −2 行（最后一行变长），净约 ±0 | SSR `### Redundancy and bloat`「When a third thing exists to reconcile two copies … that is the reason to delete a copy」：这里删的是文本里那份事件判定，而不是加一个核对器。SSR `### Load and disclosure`「The table that finds the reader's moment sits before any step with side effects」仍然成立：表还在最前面，只是其中可算的部分交给脚本（SSR 事实 2） |
| B3 | `## 1.`、`## 1b.`、`## 2.` | 原位 | 不动 | — | — | 0 | 命令、退出码与判断（`[parent-unreadable]` 要重跑而不是改票）都只有这一个调用方（L7 C.2） |
| B4 | `## 3.` 五步（第 70–76 行） | 原位 | 不动 | 第 1 步「Do steps 1-3 of `## On waking`」保留 | — | 0 | 指针把被唤醒的 orchestrator 直接送到本节，第 1 步已包含 `## On waking`，所以指针不再先点 `## On waking`（与 R4 D1.2 的格式不同，见第 2 节） |
| B5 | `## 3.` 处理表（第 78–94 行） | 原位 | 改写（批 3），只加括注 | `child.opened` of kind `fault` 行的「you do not patch while they run the night」后括注 `rerun-dont-reroute` | 原则复用（R4 D4.4） | +1 括注 | 不加 `MMW turn guard:` 行（R4 D3.5 d 的写法），理由：B2 |
| B6 | 「While a worker holds a ticket …」与两段 contract 权威顺序（第 96–100 行） | 原位 | 不动 | — | — | 0 | 规则绑定具体机制、只有一个调用方（L7 C.2）；看起来像原则，见第 3 节 |
| B7 | `### Exit codes of \`resume\``（第 102–104 行，只剩两句） | 原位 | 改写（批 1） | 在现有两句前加一句：「Exit 0: the worker took the message; end your turn. Every other exit says on stderr what to do next.」 | 消除已核实断点 V8：`## 3` 表第 81 行、`watchdog.py` 第 735、780 行、`how-it-works.md` 第 81 行都指向本节，本节却没有退出码。exit 2、3、4 的去处 stderr 已写全（W5），所以只补 exit 0 | +1 行 | SSR `### Scripts and judgement` 第 1 条：只写脚本看不到的那一步（exit 0 没有输出），其余交给拒绝文字，不抄退出码表 |
| B8 | `## 4. The closing pass` 全节 | 原位 | 改写（批 3），只加括注 | 「A finding wakes nobody, so the ones you were woken about are no measure of what exists.」句末括注 `silence-is-never-a-pass` | 原则复用（R4 D4.4「`night.md` 收口」） | +1 括注 | Step 0 加四步判据、三条提交规则、开票规则、Memory 收口是天然整体（N1 第 8 节）；ADR 0012 要求程序本体在 `night.md`；L7 C.4 的「只有一个调用方」「机械部分已在脚本里（`findings`、`route`、`memory-list`）」都成立 |
| B9 | `## 5. The night is over` | 原位 | 不动 | 调用 `retro` 的段、「Then tell the user …」段 | — | 0 | `reverify → summary → retro → 告诉用户` 每步要上一步的收据（N1 第 8 节）。「Then tell the user」一段成为 B2 第 (4) 行「until then」的去处 |
| B10 | `## 6. Merge the accepted night` | 原位 | 不动 | — | — | 0 | — |
| B11 | `## Suspending the night` | 原位 | 不动 | — | — | 0 | — |

### 1.3 其余三个 reference

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| C1 | `one-ticket.md` 第 1、2、4 步与开头 | 原位（单票 orchestrator 的角色操作文件） | 不动 | — | — | 0 | 14 行，单一入口单一任务（L7 C.1 第 7 问） |
| C2 | `one-ticket.md` 第 3 步末条「`child.opened` of kind `contract`, a `watchdog:` line, or an `MMW turn guard:` line: act as night.md under **3. Each time something wakes you** says …」 | 原位 | 改写（批 1） | 拆成两句：「`child.opened` of kind `contract`, `relay.recovered since <time>`, or a `watchdog:` line: act as night.md under **3. Each time something wakes you** says for it, reading … `events.py fold <n>` where it says `status`.」与「An `MMW turn guard:` line: do what it says.」 | 消除两处已核实断点：V7 的后半（单票路径也把 turn guard 送进没有处理行的 `## 3`）；W3（单票 orchestrator 收到 `relay.recovered` 无处理行） | ±0 行 | SSR `### Hand-offs`「Each event gets one instruction」：`relay.recovered` 的唯一指令仍在 `night.md` `## 3` 表 |
| D1（已被 R12 K-46 改定） | `inside-a-ticket.md` 开头、`## Exit codes`、`## After the closeout` | 原位（worker 的分支 reference） | 改写（批 1），只加一句 | 在 `## After the closeout` 末尾加：「Every other wake this watch sends you is about your own ticket: read the event on it and tell the user; there is no orchestrator to act on it.」 | 消除已核实断点 W2：夜外 adopt 的会话是自己 watch 的 MAIN，`WAKES` 的 `ticket.refused`、`child.opened`、`worker.lost` 都会发给它，而本文件只写了 `ticket.passed`/`ticket.returned`。代码路径已核实；运行中是否发生过未查到（推断） | +1 行 | `implement` 第 22 行「the child wakes the orchestrator, which corrects the source」对夜外 adopt 不成立，这句给它一个去处，不改 `implement` |
| E1 | `editing-models.md` 全文 | 原位 | 不动 | — | — | 0 | 只在用户下令改模型或 runner 时读的分支（SSR 事实 5）；ADR 0024 |

### 1.4 脚本

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| H1 | `relay.py` `WAKES`（第 291–299 行）旁 | 原位（脚本） | 新建一张表（在现有文件里） | `POINTERS`：键为（收件角色、watch 的 `by`），值为指针文字的模板，只含技能名、技能内路径与小节标题。四行：worker →「the `dispatch` skill's `On waking`, then the `implement` skill's `Closing steps`」；`by=open` 的 MAIN →「the `dispatch` skill's `references/night.md` "3. Each time something wakes you"」；`by=open-ticket` 的 MAIN →「the `dispatch` skill's `references/one-ticket.md`」；`by=adopt` 的 MAIN →「the `dispatch` skill's `references/inside-a-ticket.md` "After the closeout"」。另加 `relay.py pointer --repo --ticket N --to worker\|main` 子命令给 `dispatch.sh` 用 | 让内容被两个以上调用方复用：三个发送方（`wake_text`、`watchdog.py` 告警、`dispatch.sh resume`）取同一张表；修改只动一处：加事件时 `WAKES` 与指针在同一屏 | +约 30 行 | R4 D1.2「放在 `dispatch/scripts/` 下」：放进已有的 `relay.py`，不新建模块。hook 不从这里取锚点：`relay.py` 导入时加载 `statedir`、`ghlist`、`events.py`（W8），`tool-guard.py` 在每条 shell 命令前运行，导入它会给每条命令加开销；hook 的锚点保留为各自文件里的常量，由接线 lint 第 1 类核对 |
| H2 | `relay.py` `wake_text`（第 385–389 行） | 原位 | 改写（批 1） | 返回 `#<n> <event> · <pointer>`，同一行；`relay.recovered` 行返回 `relay.recovered since <time> · <每个 watch 的指针>`，按收件地址在 `watches.json` 里的全部 watch 列出（spec watch 与 tickets watch 各一段） | 消除断点 B8、B9（被压缩的会话收到裸唤醒不知去哪；R4 第 2 节已核实）；R4 T12（一个地址同时持有多种 watch）由「全部列出」定下：`relay.recovered` 本来就是「one per session, however many watches it opened」（`relay.py` 第 163–164 行） | +约 10 行 | ADR 0020「nothing the tracker already says」：指针只是地址，不含 tracker 数据，原意保住；由新 ADR 修订一句（R4 第 9 节）。V4：`ack` 不解析文字，不受影响 |
| H3 | `relay.py` 的 watch 记录与 `dispatch.sh` `open_relay`（第 629–642 行） | 原位 | 改写（批 1） | `open_relay` 多传一个 `--by open\|open-ticket\|adopt`，`relay.py start/add` 把它存进 `watches.json` 的 watch 项 | 消除已核实断点 W2：否则 adopt 的 worker 会收到 one-ticket 的指针，照它跑 `land` 会停掉自己（`inside-a-ticket.md` `## After the closeout` 原文） | +约 8 行 | 状态文件多一个字段。发布只在没有 watch 打开时进行（AGENTS.md Self-hosting boundary；R4 C15 的 `--check` 报告），所以没有旧格式的项需要兼容（推断） |
| I1（已被 R12 K-46 改定） | `watchdog.py` 告警发送（第 808–818 行） | 原位 | 改写（批 1） | 每个 orchestrator 的一行告警末尾接一次指针（该地址全部 watch），同一行 | 消除断点 B8：被压缩的 orchestrator 收到 `watchdog:` 行也能回到操作文件 | +约 5 行 | — |
| I2（已被 R12 K-47 改定） | `watchdog.py` idle 告警里给 worker 的 `resume` 原文（第 745–754 行） | 原位 | 改写（批 1） | 缩成「You ended your turn with no result on the ticket.」，其余出路交给 `dispatch.sh resume` 自动接上的 worker 指针（→ `implement` `## Closing steps`，其第 74 行接 `RESUME:`） | 去掉一处经核实的真重复且已分歧（W4）：脚本拼的提示词复述 `implement` 第 18、23 行，而且对「外部原因卡住」给了与 `implement` 第 76 行不同的出路 | −4 行 | SSR `### Prompts written for other agents`「A rule stated both in a skill and in a prompt a script builds is duplication; the prompt keeps the data」 |
| I3 | `watchdog.py` 第 735、780 行「night.md's Exit codes of resume」 | 原位 | 改写（批 1） | 改为逐字引用小节标题的常量，由 lint 第 1 类核对 | 消除已核实断点 V8 的复发：锚点改名时 lint 失败 | ±0 | — |
| G1（已被 R12 K-47 改定） | `dispatch.sh` `resume_one`（第 2190–2220 行） | 原位 | 改写（批 1） | 发送前在同一行末接 `relay.py pointer --to worker` 的输出 | 消除断点 B9（worker 被 `resume` 时没有回到 `On waking` 的路）；复用 H1 | +3 行 | — |
| G2 | `dispatch.sh check_machine` | 原位 | 改写（批 3） | 消费仓库 `AGENTS.md` 没有指向 `mmw` 的行时打一行警告，只读 | 消除断点（`mmw` 的加载，R4 D1.4 第 2 条） | +约 10 行 | — |
| G3 | `dispatch.sh` 启动提示词（第 1949、1967、2072 行）、`AUTONOMOUS`、`PRODUCT_RULES`（第 108–109 行） | 原位 | 不动 | — | — | 0 | 测试钉着（R4 第 15 节）；`AUTONOMOUS` 是 reviewer 唯一读到「不在屏幕上提问」的地方（`code-review` 各文件无此句，本轮 grep），所以不删 |
| G4 | `dispatch.sh` 第 4115 行拒绝文字「as the closing pass of the dispatch skill's references/night.md says」 | 原位 | 不动 | 由 lint 第 1 类按「the `X` skill's references/y.md」的写法抽出核对 | — | 0 | 不为一处 bash 字面改成从 Python 模块取值 |
| G5 | `dispatch.sh` 其余子命令、头注释 | 原位 | 不动 | — | — | 0 | 头注释漂移（N10 B12）与 ADR 0012、0027 分歧另开普通票（R4 第 15 节） |
| J1（已被 R12 K-48 改定） | `status.py --table`（经 `dispatch.sh status`） | 原位 | 改写（批 1） | 首行印 `RESUME: <night.md 小节标题>`。取值：无 `spec.opened` →「1. The user says the night starts」；最新夜事件是 `spec.suspended` →「Suspending the night」；已开夜、frontier 非空或有活 agent →「3. Each time something wakes you」；已开夜、frontier 空且无活 agent、无 `spec.closed` →「4. The closing pass」；有 `spec.closed`、其后无 `result=recorded` 的 `spec.retroed` →「5. The night is over」；有 recorded 的 `spec.retroed`、无 `spec.merged` →「6. Merge the accepted night」；有 `spec.merged` →「none: the night is merged」。读 spec 评论与 fold 用 `events.py`，与 `newest_field` 同一套函数 | 去掉 B2 所述的真重复；消除已核实断点 V6 | +约 40 行 | R4 T9 由本轮阅读定下（W6）：所有按事件的取值都能算，「用户说开始」「用户已验收」算不出，留在事实表。status 之外不影响任务板（W6） |
| K1 | `models.py`、`hosts.json`、`runners/*.sh`、`statedir.py`、`ghlist.py` | 原位 | 不动 | — | — | 0 | 天然整体（N1 第 8 节：适配器 + `models.py` + `hosts.json`；relay + watchdog + turn guard + statedir）；与分层无关 |

### 1.5 两个 hook

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| L1 | `tool-guard.py` `NO_QUESTION`（第 76–80 行） | 原位（hook 的拒绝文字） | 改写（批 1） | 角色中立：「Nobody is at the screen. A worker: the `implement` skill, "Put no question on the screen". A reviewer: record it as Could not tell in your report (the `code-review` skill's `references/session.md`).」约 190 字符，在 256 以内（W7） | 消除已核实冲突 V9：现文让 worker 写 `ABANDON: AC<n> decision` 并开 needs-triage 子票，`implement` 第 23 行让它开 `--sub-issue decision` 后继续；reviewer 在同一工作树受拦却无承接处（N11 missing_edges 第 2 条；W10 给了 reviewer 的去处） | ±0 | SSR `### Hand-offs`「Each event gets one instruction」；ADR 0008「给唯一出路」由「按角色各一条出路」保住。同一次提交改 `test_tool_guard.py` 第 440–447 行的断言 |
| L2 | `tool-guard.py` `REFUSAL`、`no_kill()`、头注释、`governed_ticket` | 原位 | 不动 | — | — | 0 | 与 `implement` 第 99 行、`ui-acceptance` 五条规则是「事前文字 + 事发拒绝」，读者时刻不同（N8 第 9.3 节） |
| M1 | `turn-guard.py` 拦截文字（第 306–311 行）与头注释 | 原位 | 不动 | 不接指针 | — | 0 | 文字自带全部步骤并以「Then end your turn」结尾；下一次唤醒会带指针。它的处理由 B2 第 (2) 行、C2 指向「照它做」，不在技能文本里复述 |

### 1.6 `retro` 技能（210 行 `SKILL.md` + `scripts/retro.py`）

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| N1 | frontmatter `description` | 原位（能力技能） | 不动 | — | — | 0 | 只写触发，唯一入口时刻是 `spec.closed` 之后（N7 第 2.1 节）；自有技能，没有调用开关 |
| N2 | 第 8 行（从 `origin/<base branch>` 的 checkout 跑） | 原位 | 不动 | — | — | 0 | — |
| N3 | 引言三段（第 10–37 行） | 原位 | 不动 | — | — | 0 | 看起来像原则的两句见第 3 节 |
| N4 | `## Gather`、`## Analyze`、`## Decide`、`## Finalize` | 原位 | 不动 | — | — | 0 | 服务一个可命名交付物（Retro Memory 与 `spec.retroed`），L7 C.3；文字与 `retro.py` 的 `check_analysis()`、`qualifies()` 等是一份合同的两端（N7 第 8 节，已由 N7 核实，本轮未读 `retro.py`） |
| N5 | 第 186 行「Done when `finalize` has posted `spec.retroed` with `result=recorded`; then return to the dispatch skill's `references/night.md` `## 5. The night is over`, which tells the user.」 | 原位 | 不动（偏离 R4 D5.4） | — | 说不出收益：这句点名的是唯一的调用方，属 SSR `### Hand-offs`「the caller it returns to」，不是重述一段顺序。换成「return to the playbook that sent you; with none, the `mmw` skill routes」后，被压缩的 orchestrator 要多绕 `mmw` → `dispatch` → `night.md` → `status` 四跳才回来 | 0 | R4 D5.4 的原意（顺序只有一个家；单独斜杠进入不会断）在这里不受威胁：`retro` 只能在 `spec.closed` 之后跑，它之后的每一步都在 `night.md`，且 `status` 的 `RESUME:` 也会指回第 5 节 |
| N6 | `## Prevention destinations` | 原位 | 不动 | — | — | 0 | `mmw-skill` 一行「a cross-repository MMW workflow, in an MMW skill」已覆盖 `mmw` 目录里的 playbook 与原则；`repository-skill` 是 R4 D7.6 指定的仓库专有工作流去处 |
| O1 | `scripts/retro.py` | 原位 | 不动 | — | — | 0 | 未读（取 N7） |

### 1.7 角色与文档

| # | 部件 | 现在 → 新位置与层 | 动作 | 具体内容 | 收益与证据 | 体量 | 被取代的旧规则；原意怎样保住 |
|---|---|---|---|---|---|---|---|
| P1 | orchestrator 角色 | 人启动的会话；操作文件 `night.md`、`one-ticket.md`；`~/.mmw/models.json` 没有它的行 | 不动 | — | — | 0 | R4 第 12 节「角色」行；ADR 0020 要求它跑在 `self` 可读的 runner 会话里 |
| Q1 | `docs/contexts/night/how-it-works.md` 第 81 行 | 原位（维护者文档） | 改写（批 1） | 退出码仍指 `night.md` `Exit codes of resume`；沉默 worker 的消息改指 `watchdog.py` 的 idle 告警 | 消除已核实断点 W9（N1 第 9.1 节第 1 条） | ±0 | — |
| Q2 | 新 ADR（修订 ADR 0020 一句） | `docs/adr/` | 新建（批 1，R4 第 9 节） | 唤醒文字 = `#<n> <event>` 加同一行的角色指针；指针按收件角色与 watch 的 `by` 选取 | 消除已核实的规则冲突（ADR 0020「文字只带 `#<n> <event>`」与新做法） | +约 30 行 | ADR 0020 正文不改（ADR 记录决定，变化另写） |
| Q3 | 词条 **role pointer** | `docs/contexts/night/CONTEXT.md`，放在 **wake** 与 **alert** 旁（第 45、343 行） | 新建（批 1） | 一条词条，`_Home_` 指 `relay.py` 的 `POINTERS` | 给无处安放的内容一个家（新概念的定义）。放 night 语境而不放 toolbox（与 R4 第 9 节 `### Vocabulary` 行不同）：它是唤醒文字的一部分，**wake**、**ack**、**alert** 都在 night 语境 | +3 行 | — |
| R1 | 受影响的测试 | `tests/relay/test_relay.py`（`send.sent` 相等断言，V5）、`tests/dispatch/test_tool_guard.py` 第 440–447 行、`tests/dispatch/test_status.py`、`tests/dispatch/test_dispatch.sh` 的 `resume` 场景（第 3274–3395 行）与 `check` 场景、`tests/liveness/test_liveness.py`（idle 告警，第 767 行只断言前缀，不受影响） | 改写（与各自改动同一提交） | — | — | — | — |

---

## 2. playbook 草图

本单元不产生新的 playbook。它持有两份角色操作文件（R4 D3.1「角色的 playbook」），参与一份头部 playbook 的交接。下面按 R4 D3.2 的要素写出它们在新架构里的形态，只写「做什么、点名谁」。

### 2.1 Running a night（`dispatch` 的 `references/night.md`，原位）

- **入口**：
  - 人说「今晚跑 spec #N」：消费仓库 `AGENTS.md` 一行 → `mmw` `## Routes`「跑一夜 … → `dispatch` 技能」→ `dispatch` `## Find your moment` 第 3 行；或 `dispatch` 的 description；或 `/dispatch`。
  - 头部 playbook `mmw/playbooks/idea-to-tickets.md` 的 **Hand to the night** 交接到 `dispatch`。
  - 事件唤醒：relay 的 `#<n> <event> · <指针>`、`relay.recovered since <time> · <指针>`；watchdog 的 `watchdog: … · <指针>`；turn guard 的 `MMW turn guard: …`（无指针，自带步骤）。
- **所有权行**：现有第 3 行「You are the orchestrator. … Every decision is yours: …」即是，不另加。
- **Where you are**：事实表（B2 改写后 4 行），第 (4) 行交给 `bash scripts/dispatch.sh status <spec>` 首行的 `RESUME:`。
- **步骤**（现有小节标题即稳定名，不改名）：
  1. **1. The user says the night starts**：runs-script `dispatch.sh check`、`dispatch.sh open`；交出 board URL。
  2. **1b. Before the batch**：calls `verify-ticket` 的 `verify-ticket.py <spec> --lint`；UI 批次 calls `ui-acceptance` 的 `target_config.py --check`。（principle `silence-is-never-a-pass` 的情形：tracker 没回答时重跑，不当作零；本处不加括注，句子已带理由。）
  3. **2. First `advance`**：runs-script `dispatch.sh advance`。
  4. **3. Each time something wakes you**：`dispatch` `## On waking` 第 1–3 步（principle `rerun-dont-reroute`）→ `dispatch.sh status` → 处理表 → `dispatch.sh advance` 一次；`resume`、`retract`、`route` 按表行；reads-reference `to-spec` 的 `references/revising-a-spec.md`、`design-pages` 的 `references/pull.md`（contract 分支）。
  5. **4. The closing pass**：`dispatch.sh findings`、`route`、`memory-list`；开票时 reads `to-tickets` 的 `<issue-template>`，calls `verify-ticket.py <n> --lint`（principle `silence-is-never-a-pass`）。
  6. **5. The night is over**：`dispatch.sh reverify`、`summary`；calls `retro`；告诉用户。
  7. **6. Merge the accepted night**：用户验收后 `dispatch.sh finish`。
  - 分支：**Suspending the night**：`dispatch.sh suspend`。
- **重入**：事件唤醒里的角色指针直达 `3. Each time something wakes you`；其余情况 `status` 的 `RESUME:` 指出小节；事实表兜底非事件的三种情形。
- **Done when**：`finish` 退出 0；或 `suspend` 退出 0，或退出 1 且已把 stderr 每行告诉用户（`## Suspending the night` 现有句）。
- **交付物**（现有第 5 行已写，不另加 `**Leaves:**`）：`NIGHT SUMMARY`、`NIGHT RETRO`、child、票与 spec 上各决定的理由评论、合进 project branch 的一次 merge。

### 2.2 One ticket, outside a night（`references/one-ticket.md`，原位）

- **入口**：`mmw` `## Routes`「跑一张票 → `dispatch`」→ `## Find your moment` 第 4 行；事件唤醒带 `by=open-ticket` 的指针。
- **步骤**：`dispatch.sh open-ticket` → `dispatch.sh start <n> worker`（starts-with-prompt `Use the implement skill …`）→ 唤醒（`## On waking`；`contract`、`relay.recovered`、`watchdog:` 借 `night.md` `3.` 的表行；`MMW turn guard:` 照它做）→ `dispatch.sh land`。
- **Done when**：`land` 退出 0（现有句）。

### 2.3 参与的交接

- `idea-to-tickets` **Hand to the night** → `dispatch`（R4 D3.3 第 7 步）。本单元不改这条边的接收端：`## Find your moment` 第 3、4 行即是入口。
- `night.md` `5.` → `retro` → 返回 `night.md` `5.`（N5 保留点名的返回句）。

---

## 3. 原则候选

### 3.1 本单元引用 R4 的三条原则（本单元不新建原则）

| slug | 规则一句（R4 D4.4） | 理由出处 | 本单元里的引用位置 |
|---|---|---|---|
| `the-tracker-is-the-state` | 你在哪一步由票上的事件决定，不由会话记忆决定；要等别人就结束回合，由事件叫醒，不轮询 | ADR 0010、0019、0020；`dispatch/SKILL.md` 第 8 行原句 | `dispatch/SKILL.md` 第 8 行（A2）；`night.md` 第 11 行（B1） |
| `rerun-dont-reroute` | 被打断的命令原样重跑；被拒绝或撞上流水线自身的故障，就修拒绝点名的事或报 blocked，不绕路、不写重试循环、不换 host 或 runner | ADR 0010、0017、0018 | `dispatch/SKILL.md` `## On waking` 第 1 步（A6）；`night.md` `## 3` 表 `fault` 行（B5） |
| `silence-is-never-a-pass` | 一道检查、一次交付不能因为什么都没做而读起来像通过；检查要证明自己能失败；查不了就说查不了 | ADR 0008 | `night.md` 第 7 行（B1）；`night.md` `## 4` 「A finding wakes nobody …」（B8） |

每处都保留原句，原则名只作句末括注（R4 D4.2）。三条在本单元之外的引用处见 R4 D4.4，本单元满足门槛第 5 条（两处以上、不同机制）只是其中一部分。

### 3.2 看起来像原则、应留在原处的规则

| 规则 | 位置 | 留在原处的理由 |
|---|---|---|
| 「While a worker holds a ticket, its code is the worker's … never its worktree or branch」 | `night.md` 第 96 行 | 与 N9 PC12 `one-writer-per-file` 同源；R4 第 15 节已判不建该原则。这里绑定具体机制（`resume`、`origin/<into>`），只有 orchestrator 一个读者（L7 C.2） |
| contract 权威顺序「decision tickets and ADRs, then the spec, then …」 | `night.md` 第 98 行 | 只有一个调用方；是领域参数，不是跨任务的判断（L7 C.2） |
| 「A name echoed through prose is not a coupling」「Counting files is not counting effort」 | `night.md` `## 4` 第 3 步 | 是 closing pass 判据的内部理由，只适用这一步（L7 C.6 信号 7） |
| 「A `fault` in the pipeline's own scripts you do not patch while they run the night」 | `night.md` `## 3` 表 | 这是 `AGENTS.md` `## Self-hosting boundary` 在夜里的落地，家已在 `AGENTS.md`（D4.3 第 7 条）；它只加 `rerun-dont-reroute` 的括注 |
| 「each decision you make leaves its reason where that reader will look」 | `night.md` 第 5 行 | 与 `shared.md` 规则 2 末句、规则 10 同义，家在 `shared.md`（D4.3 第 7 条） |
| 「A problem exists only when a tracker event comment, commit, current repository file, or observed check proves it」 | `retro/SKILL.md` 第 16–20 行 | 与 N9 PC11 `clues-are-not-evidence` 同源。retro 已带完整理由（第 22–28 行「costs twice」），另一读者 `implement` 第 47–49 行（`## Shared experience while implementing`）也各带理由；新建原则文件而调用方原句都留下，不减少任何重复，也不改变决定（L7 C.6 信号 2、3；R4 第 15 节给出的进入条件未触发） |
| 「A missing source narrows the analysis; it never means that the corresponding problem did not happen」 | `retro/SKILL.md` 第 46–48 行 | 与 `silence-is-never-a-pass` 同义，但句子本身已带理由，retro 内每个情形都被覆盖；加括注不改变任何决定（L7 C.6 信号 2），所以不加 |
| 「Every prevention has a standing cost」「Choose the destination whose reader acts on the lesson」 | `retro/SKILL.md` 第 123 行、第 203 行 | 只有 retro 一个调用方；门槛由 `retro.py` `qualifies()` 执行（N7 第 2.1 节） |

---

## 4. 连线

边的两端用新架构的组件名。关系只用任务给定的十一种；lint 读锚点的边记为 `reads-reference`，括号里注明。

```edges
mmw -> dispatch : routes-to (## Routes「跑一夜、跑一张票、改 host/model/runner、开任务板」)
idea-to-tickets -> dispatch : hands-off-to (Hand to the night)
dispatch -> dispatch/references/night.md : routes-to (## Find your moment 第 3 行)
dispatch -> dispatch/references/one-ticket.md : routes-to (第 4 行)
dispatch -> dispatch/references/inside-a-ticket.md : routes-to (第 2 行)
dispatch -> dispatch/references/editing-models.md : routes-to (第 5 行)
dispatch -> dispatch.sh : runs-script (第 6 行 board)
dispatch -> implement : routes-to (第 1 行，经 ## On waking)
dispatch#On waking -> dispatch.sh : runs-script (ack)
dispatch#On waking -> rerun-dont-reroute : cites-principle
dispatch -> the-tracker-is-the-state : cites-principle (第 8 行)
orchestrator -> dispatch/references/night.md : re-enters-at (事实表；status 的 RESUME:)
orchestrator -> dispatch/references/night.md#3. Each time something wakes you : re-enters-at (唤醒指针，by=open)
orchestrator -> dispatch/references/one-ticket.md : re-enters-at (唤醒指针，by=open-ticket)
worker -> dispatch#On waking : re-enters-at (唤醒与 resume 的指针)
worker -> implement#Closing steps : re-enters-at (指针之后；RESUME: 步骤名)
worker -> dispatch/references/inside-a-ticket.md#After the closeout : re-enters-at (唤醒指针，by=adopt)
dispatch/references/night.md -> dispatch#On waking : reads-reference (## 3 第 1 步)
dispatch/references/night.md -> dispatch.sh : runs-script (check、open、advance、status、resume、retract、findings、route、memory-list、reverify、summary、finish、suspend)
dispatch/references/night.md -> verify-ticket : calls (--lint；events.py fold)
dispatch/references/night.md -> ui-acceptance : calls (target_config.py --check；lease.py release)
dispatch/references/night.md -> to-tickets : reads-reference (<issue-template> 与判据形状)
dispatch/references/night.md -> to-spec : reads-reference (references/revising-a-spec.md)
dispatch/references/night.md -> design-pages : reads-reference (references/pull.md)
dispatch/references/night.md -> retro : calls (5. The night is over)
dispatch/references/night.md -> the-tracker-is-the-state : cites-principle
dispatch/references/night.md -> rerun-dont-reroute : cites-principle
dispatch/references/night.md -> silence-is-never-a-pass : cites-principle
dispatch/references/one-ticket.md -> dispatch#On waking : reads-reference
dispatch/references/one-ticket.md -> dispatch/references/night.md#3. Each time something wakes you : reads-reference (contract、relay.recovered、watchdog:)
dispatch/references/one-ticket.md -> dispatch.sh : runs-script (open-ticket、start、resume、land、ack)
dispatch/references/inside-a-ticket.md -> dispatch.sh : runs-script (adopt、ack)
dispatch/references/editing-models.md -> models.py : runs-script (config set、config runner、config show)
implement -> dispatch/references/inside-a-ticket.md : reads-reference
implement -> dispatch.sh : runs-script (integrate、start reviewer、wait、ack)
retro -> retro.py : runs-script (gather、search、finalize)
retro -> writing-for-agents : calls (第 11 步)
retro -> dispatch/references/night.md#5. The night is over : hands-off-to (第 186 行返回句)
retro.py -> dispatch/references/night.md#6. Merge the accepted night : hands-off-to (spec.retroed recorded 是 finish 的前置；dispatch.sh 第 4166–4177 行)
dispatch.sh -> worker : starts-with-prompt (Use the implement skill …)
dispatch.sh -> reviewer : starts-with-prompt (Use the code-review skill …)
dispatch.sh -> advisor : starts-with-prompt (Use the advisor skill.)
dispatch.sh -> worker : wakes (resume，同一行接 worker 指针)
dispatch.sh -> relay.py : runs-script (start/add 带 --by、stop、watching、ack、pointer)
dispatch.sh -> status.py : runs-script (--table 首行 RESUME:、--advance-plan 等)
dispatch.sh -> models.py : runs-script
dispatch.sh -> runners/<runner>.sh : runs-script
dispatch.sh -> verify-ticket : runs-script (events.py、verify-ticket.py --reverify)
dispatch.sh -> ui-acceptance : runs-script (lease.py)
dispatch.sh -> ~/.mmw/models.json : configured-by
dispatch.sh -> hosts.json : configured-by
relay.py -> orchestrator : wakes (ticket.passed、ticket.returned、ticket.refused、child.opened、worker.lost、relay.recovered；同一行接指针)
relay.py -> worker : wakes (reviewer.reported、reviewer.lost、worker.queued；同一行接指针)
relay.py -> runners/<runner>.sh : runs-script (send、liveness)
relay.py -> watches.json : configured-by (watch、runner、session、by)
watchdog.py -> relay.py : runs-script (导入；取 POINTERS)
watchdog.py -> orchestrator : wakes (watchdog: 告警，同一行接指针)
watchdog.py -> dispatch/references/night.md#Exit codes of resume : reads-reference (告警文字点名)
watchdog.py -> runners/<runner>.sh : runs-script (liveness、send)
turn-guard.py -> watchdog.py : runs-script (arm；读心跳)
turn-guard.py -> orchestrator : wakes (MMW turn guard: 拦住回合)
orchestrator -> turn-guard.py : enforced-by-hook (回合结束)
worker -> tool-guard.py : enforced-by-hook (关票、改队列 label、提问、结束进程)
reviewer -> tool-guard.py : enforced-by-hook (同一工作树)
tool-guard.py -> implement : routes-to (NO_QUESTION 指向 "Put no question on the screen")
tool-guard.py -> code-review/references/session.md : routes-to (NO_QUESTION 指向 Could not tell)
tool-guard.py -> ui-acceptance : runs-script (refusal.py)
models.py -> hosts.json : configured-by
models.py -> ~/.mmw/models.json : configured-by
status.py -> verify-ticket : runs-script (events.py、issue_tree.py 按路径加载)
check_wiring.py -> relay.py : reads-reference (lint 第 1 类：POINTERS 的每个锚点)
check_wiring.py -> tool-guard.py : reads-reference (lint 第 1 类：NO_QUESTION 的锚点)
check_wiring.py -> watchdog.py : reads-reference (lint 第 1 类：Exit codes of resume)
check_wiring.py -> status.py : reads-reference (lint 第 1 类：RESUME: 的小节标题)
check_wiring.py -> dispatch.sh : reads-reference (lint 第 1 类：第 4115 行 references/night.md)
check_wiring.py -> dispatch/references/night.md : reads-reference (lint 第 2 类：MAIN 事件在 ## 3 表各有一行)
check_wiring.py -> dispatch/references/one-ticket.md : reads-reference (lint 第 2 类)
check_wiring.py -> dispatch/references/inside-a-ticket.md : reads-reference (lint 第 2 类)
```

lint 第 2 类的范围按本单元的发现扩大：R4 D3.6 写的是「MAIN 的看 `night.md` `## 3`，WORKER 的看 `implement`」；因为 MAIN 按 watch 的 `by` 分三种，第 2 类要按指针表逐行核对：每个（角色，`by`）对应的操作文件对每个会发给它的事件（含 `worker.queued`、`relay.recovered`）恰好有一个处理行。

---

## 5. 不动清单

| 部件 | 理由 |
|---|---|
| `dispatch/SKILL.md` 的位置、名字、`## On waking` 四步正文、表第 2–6 行、第 12 行定义 | 流水线的角色入口（R4 D2.3）；`## On waking` 四步是天然整体（N1 第 8 节），脚本按名点它（`dispatch.sh` 第 79 行，R4 V2） |
| `references/` 目录名与四个文件名 | 脚本与测试按路径点名（R4 V2、第 15 节）；改名说不出收益 |
| `night.md` `## 1`、`## 1b`、`## 2`、`## 3` 五步与除括注外的处理表、contract 两段、`## 4` 全部判据与规则、`## 5`、`## 6`、`## Suspending the night` | 单入口单任务的操作文件（L7 C.1 第 7 问）；长内容只有一个调用方、机械部分已在脚本里（L7 C.4）；ADR 0012 要求 closing pass 的程序本体在这里 |
| `night.md` 不加 `**Leaves:**` 行 | 第 5 行已写夜留下什么、给谁读；再加一行是重复（L7 C.6 信号 3） |
| `night.md` 各步不补 `Done when` 行（N1 第 9.2 节第 2 条） | 每步都以退出码行收尾（「Exit 0: …」），已经是完成判据；再写一行 `Done when` 只是换个格式重述（L7 C.6 信号 2）。SSR `### Rules and completion criteria` 要防的是「不知道一步何时算完」，退出码行已防住 |
| `night.md` `## 3` 第 1 步「Do steps 1-3 of `## On waking`」这处编号引用 | 同一技能内、`SKILL.md` 与 reference 一起发布一起改；指针的锚点是小节标题，不经这个编号。改写说不出收益 |
| `one-ticket.md` 除第 3 步末条之外的全部；不给它的步骤加粗体名 | 14 行，指针指向整个文件已足够；加步骤名不改变任何决定 |
| `inside-a-ticket.md` 除新增一句之外的全部；`editing-models.md` 全部 | 各是一个分支（SSR 事实 5）；只有一个调用方 |
| `dispatch.sh` 启动提示词、`AUTONOMOUS`、`PRODUCT_RULES`、「角色 → 技能」的 `case` 分支、其余子命令 | 测试钉着；`PRODUCT_RULES` 已是指针；`AUTONOMOUS` 是 reviewer 唯一读到的「不提问」 |
| `dispatch.sh` 头注释漂移（N10 B12）、ADR 0012 与 0027 与实现的分歧、`CODING_STANDARDS.md` 对 bounce 的描述（N1 第 9.1 节） | 真问题，但不属于分层；按 R4 第 15 节另开普通票 |
| `relay.py`、`watchdog.py` 的判定逻辑与状态文件（除 `by` 字段）；`statedir.py`、`ghlist.py` | 已跑通；只改它们发出的文字 |
| `turn-guard.py` 全部 | 拦截文字自带步骤；判定逻辑与五宿主实测记录都在脚本头（N8 第 2.6 节） |
| `tool-guard.py` 除 `NO_QUESTION` 外的全部 | 事前文字（`implement`、`ui-acceptance`）与事发拒绝，读者时刻不同（N8 第 9.3 节） |
| `models.py`、`hosts.json`、`runners/*.sh` | host × runner 的交叉参数与适配器是天然整体（N1 第 8 节，ADR 0018、0024） |
| `status.py` 除首行 `RESUME:` 外的全部 | 计划行只有 `dispatch.sh` 读，与 `events.py` fold 共用一套判定（N1 第 8 节） |
| `retro/SKILL.md` 全部，包括第 186 行的返回句 | 能力技能，内部步骤服务一个交付物（L7 C.3）；与 `retro.py` 是合同两端（N7 第 8 节）；返回句点名唯一调用方，换成固定返回句说不出收益（第 1 节 N5） |
| `retro.py` | 未读；文字不改，合同不变 |
| orchestrator 不建角色文件、不加 `models.json` 行 | R4 第 12 节；ADR 0015 |

---

## 6. 形式拆散自查（L7 C.6 十一个信号）

1. **没有先确认已有组件不是合适的归宿。** 未触发。指针表放进已有的 `relay.py`，不新建模块；adopt 的处理放进已有的 `inside-a-ticket.md` `## After the closeout`；`RESUME:` 放进已有的 `status.py --table`。
2. **新增内容不改变决定。** 未触发，有一处待实测。每项修补都改变一个具体动作：B2 让被压缩的 orchestrator 不再手工拆 spec 上的事件；B7 给 exit 0 一个去处；C2、D1、H3 让单票与 adopt 的会话在三种唤醒上有指令；I2、L1 让同一情形只有一种出路。六处原则括注是否改变决定待 R4 T13。
3. **重复已有的、位置得当的指引。** 未触发，而且反过来去掉三处：`night.md` 事实表的事件判定（交给脚本）、`watchdog.py` idle 文字对 `implement` 的复述、`NO_QUESTION` 与 `implement` 第 23 行的分歧。指针与 `## Find your moment` 第 1 行都写「worker 去 `On waking` 再去 `implement`」：前者是消息里的地址，后者是文件里的表，读者到达的路径不同；两者的锚点由 lint 第 1 类核对。
4. **本可由机制强制的规则写成了文字。** 未触发。事件位置交给 `status.py`；指针的锚点、hook 的锚点、`WAKES` 与处理行交给 lint；「消息必须一行」由指针生成函数执行，不写进技能文本。
5. **playbook 只调一个技能。** 未触发，不建 playbook。
6. **reference 每次都读、只有一个调用方。** 未触发，不建 reference。
7. **原则说不出改变哪个决定，或只适用一步。** 未触发，本单元不新建原则；第 3.2 节列出只适用一步的规则留在原处。
8. **拆完需要按步骤编号引用。** 未触发。指针与 `RESUME:` 都按小节标题引用；`night.md` 的小节标题本身带编号（如「3. Each time something wakes you」），lint 核对的是整行字面，不按位置找。
9. **拆出的内容没有第二个调用方、也不减少重复。** 未触发，没有拆出任何内容；唯一的「新集中」（`POINTERS`）有三个调用方。
10. **把单入口的固定流程拆成三层。** 未触发。`night.md`、`one-ticket.md` 保持一个操作文件。
11. **把只在流程之间复用的内容做成能力技能。** 未触发，没有新技能；`retro` 原本就是能力技能，保持。

---

## 7. 待用户决定

本单元的改动都不改变客户或用户看到的东西，也不改变怎么用这套工具，只有一处可选的范围问题：

| # | 决定 | 背景 | 工程上的建议 |
|---|---|---|---|
| U-N1 | 夜外 `adopt`（自己拿一张票、没有夜也没有 `open-ticket`）是否继续支持 | 这条路径下，接手的会话同时是自己 watch 的 orchestrator，`ticket.refused`、`child.opened`、`worker.lost` 都会叫醒它自己（W2），今天的文字只处理了关票后的两种。本方案给它补一句「读事件并告诉用户」（D1）。另一种做法是让 `adopt` 只在夜内可用，夜外一律走 `open-ticket`，这会改变你单独接一张票时的用法 | 保留并补一句；它不改变任何可见行为。只有当你本来就不用夜外 `adopt` 时，收窄才更省事 |

---

## 8. 未确定

| # | 问题 | 需要什么实测或阅读才能定 |
|---|---|---|
| X1 | 指针接在同一行后，三种 runner 的 `send` 能否整行送达（长度、特殊字符 `·` 与引号） | 读 `runners/{paseo,orca,herdr}.sh` 的 `send` 实现；在 `tests/relay` 的假 runner 与一次真实 Orca 会话各投一条带指针的唤醒 |
| X2 | 被压缩的 orchestrator 只凭「唤醒 + 指针」与 `RESUME:` 能否回到对的小节；worker 会不会把指针当成新指令 | R4 T2、T3 |
| X3 | 夜外 `adopt` 的 `child.opened`、`ticket.refused` 是否真的发生过；adopt 的会话是否总有人在场（D1 的「tell the user」依赖这一点，推断成立：它是自己拿票的会话） | 查 `gh search` 两仓含 `adopted` 的 `worker.started`；读一次 adopt 会话的记录 |
| X4 | `status.py` 读 spec 自己的评论后，`status` 多一次 `gh` 请求的耗时是否可接受；`test_status.py` 与 `test_dispatch.sh` 对表格首行的断言有多少 | 实现时量一次；grep 两份测试的首行断言 |
| X5 | worker 被指针送进 `## On waking` 后，`On waking` 第 3 步的 ack 与 `implement` 第 1、3 步的 ack 是两处同义指令（N10 R6）。是否删 `implement` 里的两处，属于 implement 单元 | 交给 implement 单元的归置判断 |
| X6 | orchestrator 在 retro 中途被压缩，`RESUME:` 送它回 `5.` 重跑 retro；`retro.py finalize` 重跑是否不重复开 issue、不重复写 Memory | 读 `retro.py` `finalize`（N7 说它复用同证据的 issue，固定 id 写 Memory，本轮未读） |
| X7 | `RESUME:` 的「3. Each time something wakes you」在没有唤醒时被读到（例如用户在夜中途问进度），orchestrator 会跑一次 `advance`。按 `advance` 的计划行这是无害的（推断），未实测 | `tests/dispatch` 加一个场景：夜中途无事件时跑一次 `status` 与 `advance` |
| X8 | 与 R4 的三处偏离（指针同一行、`retro` 返回句保留、词条放 night 语境）需要 R4 作者或下一轮归置确认是否与其他单元一致 | 汇总各单元报告时对照 |

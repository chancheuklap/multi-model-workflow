# 夜间 playbook 范本注解：`exemplars/mmw/playbooks/work-a-ticket.md`

这份范本是 R18 §3.3 P15 **Work a ticket**（角色 `worker` 与 `adopting-worker`）按 R20 5.3「角色操作文件式 playbook」写成的样子。名字 **Work a ticket** · `work-a-ticket` 按 R19 §4.2 保留；入口 **Picked up yourself** 按 R19 §4.2 改为 **Adopted ticket**，规则簇 `#### After the closeout, picked up yourself` 改为 `#### After the closeout of an adopted ticket`。没有用户定的名字。

缩写：`implement` = `mmw-v2/upstream/skills/engineering/implement/SKILL.md`（现行版，101 行，含 MMW 改动；R18 §4.2：它回上游原文且不再安装，正文全部进本 playbook）；`inside-a-ticket.md` = `mmw-v2/skills/dispatch/references/inside-a-ticket.md`；`sub-issues.md` = `mmw-v2/skills/verify-ticket/references/sub-issues.md`（R19 §4.5 改名 `child-issues.md`）；`tdd` = `mmw-v2/upstream/skills/engineering/tdd/SKILL.md`。

## 结构决定：步骤只留动作、闸门与 `Done when`

mode `## Playbooks` 要求把 `#### Steps` 下的步骤原样抄进待办（PS mode L117）。步骤越长，待办里「首句是能勾掉的动作、`Done when` 在眼前」的作用越弱，所以结构在范本里定下，不留给写票的人（用户本轮要求 1）：

- 每步只留要做的动作、它的闸门（退出码、停下的条件）、决定这一步结果的理由，以及 `Done when`；成段的规则移进按标题点名的规则簇。
- 移动以整句为单位，规则和紧跟它的理由句一起移（R20 T4），不拆句；步骤标题不动，`where` 与唤醒指针的锚点不变（S-O1）。
- 为此新增三个规则簇：`#### Reading yourself in`（原第 2 步后半）、`#### Integrating`（原第 4 步的合并出口）、`#### The review round`（原第 6 步的修复轮）；原第 3 步的第 2、3 段并进 `#### While writing code`。
- 规则簇按步骤第一次点名它的顺序排（R20 5.3 表「规则簇」行）。

结果：`#### Steps` 下 1272 词（原来约 1750 词）；第 2、3、10 步在 161–174 词之间，仍略超 S-G9「约 150 词」的参照。第 2 步的首句是一整句枚举（`implement` L16），第 3 步是决定整张票结果的红测试规则（W-G13），第 10 步的每个分句都是草稿要填的一项，再拆就要拆句（T3），所以停在这里。全文 3353 词，是 pstack 最长 playbook（913 词）的 3.6 倍；步数由 R18 §7.7 的 `where` 表固定（X15），不合并。

## 全文通用的机械改名（R19，T2 第 5 种或 R18 §7.6 的整句 `replace`）

| 原文 | 范本 | 依据 |
|---|---|---|
| `verify-ticket.py <n> --preflight` | `ticket_state.py <n> --claim` | R18 §7.6 拆分（整句 `replace`）；R19 §4.6 `ticket.py` → `ticket_state.py`；R19 §4.8 `--preflight` → `--claim` |
| `verify-ticket.py <n>`（一次判据运行） | `ticket_state.py <n> --run-and-record-criteria` | R18 §3.3 P15 第 4 步 `ticket.py <n> --check`；R19 §4.8 |
| `verify-ticket.py <n> --sub-issue <kind> <file>` | `ticket_state.py <n> --open-child <kind> <file>` | R18 §4.1 verify-ticket 行；R19 §4.8 |
| `verify-ticket.py <n> --decisions`、`--touched`、`--closeout`、`--reverify --actor worker` | `ticket_state.py <n> …` 同名开关 | R18 §4.1 |
| `verify-ticket.py <n> --draft` | `ticket_state.py <n> --closing-draft` | R19 §4.8 |
| `dispatch.sh wait <n> reviewer` | `dispatch.sh result <n> reviewer` | R19 §4.7；R19 第 7 节的 `renames.tsv` 行，kind `text` |
| `references/writing-interface-code.md`（`implement` 的） | the `ui-acceptance` skill's `references/writing-ui-code.md` | R19 §4.5 path 行；R18 §4.4 |
| 技能 `shared-experience` | `memory-records` | R19 §4.1 |
| `references/writing-code.md` | `references/code-writing-rules.md` | R19 §4.5 |
| 原则 `the-tracker-is-the-state`、`woken-not-polled`、`route-faults-dont-bypass` | `resume-from-durable-state`、`agents-are-woken-not-polled`、`report-faults-through-the-pipeline` | R19 §4.3 |
| 指子票的 `sub-issue`（「a `fault` sub-issue」「the sub-issue that records them」「its sub-issue is already open」） | `child` | W-G6 一词一义：全文的命令（`--open-child`）、规则簇（`#### Opening a child`）与其余句子都叫 child；R19 §4.5 把 `sub-issues.md` 改名 `child-issues.md`。这是换词，不在 R19 的逐行改名表里，所以按 T3 逐句写成 `replace`（见改写清单第 17 条） |

## 逐段来源

| 段 | 来源 | 结构依据（pstack） | 写法依据（mattpocock） |
|---|---|---|---|
| `### Work a ticket` | R18 §3.1、R19 §4.2 | S-P1 | 无 |
| 所有权行 | 搬运：R18 §3.3 P15「所有权」项的英文原句；出处 `implement` L99「the orchestrator lands the ticket once it is closed」 | R20 5.3 所有权行（`PS:skills/poteto-mode/playbooks/orchestrate.md` L3：拥有什么、从不拥有什么） | W-O2 |
| 首段第 1 句（谁在看这个会话） | 新写。出处：R18 §2.3 worker 启动提示词「unattended: mmw work-a-ticket#Claim」（派出的 worker 无人看守）；`inside-a-ticket.md` L3、L13（自己拿起的票没有 `start`，收尾后要告诉用户）与本文件 `**Reply:**` 的「With the user present」（adopt 会话可能有人在场）；判定条件的家是 mode `## Autonomy` `**Unattended.**`（R18 §2.2），这里只点名它。这一句代替原先的「Nobody watches this session.」：那一句对 **Adopted ticket.** 入口不成立 | R20 5.3 首段（`orchestrate.md` L5 至 L11） | W-G1；W-G9 |
| 首段第 2 句（读者是冷读） | 新写。出处：`mmw-v2/skills/dispatch/references/night.md` L5「read in the morning by the user, cold, … with none of this session's context」；`implement` L23「for the reviewer, who judges it, and for the user, who reads it in the morning without your context」 | R20 5.3 首段（`orchestrate.md` L5–11） | W-G1 |
| 首段第 3 句（诱惑） | 新写。出处：`implement` L22「never by bending the baseline, the harness or the test」；`night.md` L7「a criterion loosened … to make one close」 | 同上 | W-G3、W-P1 |
| 首段第 4 句「Green is what a recorded run of the ticket's criteria says, never the tests you wrote.」 | 新写：第 3 句第二个诱惑（自己写的测试绿了就算一轮完成）的替代动作。出处：`implement` L80「Done when `verify-ticket.py <n>` has recorded a run of your own after the integration」（一轮以记录下来的判据运行为准）；`implement` L30 末句「the review reads tests without running them」；`verify-ticket` 范本目标段「Your reading of the output never stands in for either」 | 同上 | W-G3（诱惑与替代动作同段） |
| 首段第 5 句（替代与代价） | 改写自 `night.md` L7 第 2 句（见改写清单）：原句属于 orchestrator，这里换成 worker 的情形 | 同上 | W-G1 的代价 |
| 「Commands of … are named bare below.」（L7） | 搬运：`implement` L8，两个命令的出处与写法改写（见改写清单第 2 条）；按 `README.md` `## 范本共用的约定` 第 1 条，这句声明写出解释器与路径，之后全文用短名 | N9 | 无 |
| `**Entry.**` **Started by `start`.** 第 1 句 | 新写：R18 §2.3 启动提示词「unattended: mmw work-a-ticket#Claim」 | R18 §3.2「MMW 多出」 | 无 |
| **Started by `start`.** 第 2 句 | 新写：R18 §2.3 表第 1 行「数据文件在 `~/.mmw/state/<repo>/prompts/<n>-<role>.md`：已安装 checkout 里这份 playbook 与 `dispatch.sh`、`ticket.py` 的绝对路径、Memory 索引、reviewer Rules 包」。启动提示词只有一行（R20 5.7 形式三），索引不在提示词里，worker 要先打开 `Data:` 指向的文件 | 同上 | W-G9 的精神：指出 agent 找不到就会跳过的那一步 |
| **Adopted ticket.** 第 1 句 | 搬运：`inside-a-ticket.md` L3，「ticket `<n>`」改为「the ticket」（见改写清单） | 同上 | 无 |
| 第 2、3 句 | 搬运：`inside-a-ticket.md` L5，逐字 | 同上 | W-G2（第 3 句是理由） |
| 第 4、5 句 | 搬运：`inside-a-ticket.md` L9，句首大写（见改写清单） | 同上 | W-O1 |
| **Woken.**、**Compacted, or unsure.** | 新写，英译 R18 §3.3 P15 Entry「被唤醒（指针）或被压缩（`where`）」 | 同上 | 无 |
| `**Where you are.**` | 新写：R20 5.3 骨架原句「Run `<where command>` and go to the step it prints.」，命令取 R18 §3.3 P15 | R20 5.3 | W-O1（只点名脚本，不复述输出） |
| 十一步标题 | 搬运：R18 §3.3 P15 的步骤标题（R18 注明「标题一一对应 `implement` 原文」，由 R18 起草；源 `implement` 的编号步骤没有标题）。R19 §4.2 列 **Claim**、**Get reviewed**、**Close out** 为被程序点名的标识符（N10） | X17；S-O1 | 无 |
| 第 1 步正文 | 搬运：`implement` L12 第 1、2 句（命令改名），L14 两句逐字 | S-P3 | W-G2（L12 第 2 句冒号后是理由） |
| 第 1 步 `Done when` | 新写：`--preflight` 的退出码 0「the ticket is now yours」（`verify-ticket.py` L4080–4082） | X10 | W-O1 |
| 第 2 步首句 | 搬运：`implement` L16 第 1 句；句首「Then read yourself in」去掉「Then」（改写清单第 15 条）；查子票的 `gh api` 查询换成 `issue_tree.py`（改写清单第 18 条）；「sub-issues」改「children」 | S-P3 | W-G7（「until you know …」是穷尽判据） |
| 第 2 步末句「`#### Reading yourself in` says how to read a baseline among them, then the spec, the glossary and the Memory records.」 | 新写：SSR L30，指针放在用到它的那一步。先点名「how to read a baseline」：那一簇第 1 段是 baseline 的定义与「a contract, not a reference」的立场，读 **Read first** 各项时就要用到；在源 `implement` L16 里它紧跟在枚举句之后（W-G3：立场放在诱惑出现的那一步），只写「the spec, the glossary and the Memory records」会让 agent 把这一簇当成关于 spec 的选读 | 同上 | W-G3 |
| 第 2 步 `Done when` | 新写：把 `implement` L16 开头的「until you know what this ticket delivers, what it must not contradict, and the words the repository uses for them」改成可核对的判据 | X10 | W-G7 |
| 第 3 步第 1 句 | 搬运：`implement` L30 第 1 句，逐字 | S-P3 | 无 |
| 第 3 步第 2 句 | 搬运：`tdd` L22 的 MMW 加句「Working from a ticket, the seams under test are the ones its `## Seam` section names.」，逐字（R18 §4.2 `tdd` 行：第 22 行票语句 → P15） | 同上 | 无 |
| 第 3 步第 3–5 句 | 搬运：`implement` L30 其余句，逐字。第 5 句「No later step does this for you: …」说明这一步为什么决定结果 | 同上 | W-G13（决定结果的那一步写明原因）；W-G2 |
| 第 3 步第 6 句（三个规则簇何时生效） | 新写：SSR L30 | 同上 | 无 |
| 第 3 步末句「Once done, commit your work to the current branch.」 | 搬运：`implement` L72 前半（见改写清单第 3 条） | 同上 | W-G4 |
| 第 3 步 `Done when` | 新写：取 `implement` L30 的红测试条件与 L34「implement every behavior the ticket asks for, completely」 | X10 | W-G7 |
| 第 4 步第 1 句 | 搬运：`implement` L78 第 1 句，逐字，句号照原文 | S-P3 | 无 |
| 第 4 步第 2 句「`#### Integrating` says what each exit asks of you, 0 included.」 | 新写的指针（SSR L30），单独成句，不接在搬来的句子上（T3：改标点、合并两句都不是机械改写）。「0 included」：干净合并退出 0，而 `#### Integrating` 第 1、2 句正是退出 0 之后要做的事，只写「exit other than 0」会让干净合并的 worker 不打开这一簇 | S-P3 | W-G9 |
| 第 4 步其余句 | 搬运：`implement` L78 从「Then run every criterion」起到段末，命令改名；「which step 7 puts」改为按标题引用（X9）；「A criterion passes only when …」一句不搬（见删去的句子）；末句「The kinds of `ABANDON` line are in `#### ABANDON kinds`.」新写（SSR L30） | 同上 | W-G2（「the closeout counts no rounds, so that line is the whole record of the trying」是理由） |
| 第 4 步 `Done when` | 搬运：`implement` L80，命令改名 | X10 | W-O1 |
| 第 5 步正文 | 搬运：`implement` L81，命令改名 | S-P3 | W-G2（「so the review judges every line of it」） |
| 第 5 步 `Done when` | 搬运：`implement` L83，逐字 | X10 | W-O1 |
| 第 6 步正文 | 搬运：`implement` L84 从开头到「start another.」，四处改写（命令改名；「as above」改为指向规则簇；见改写清单）；句末插两个原则点名（T2 附加项）；末句「Then work its findings as `#### The review round` says.」新写的指针 | S-P3；R18 §7.1（`reviewer.reported`、`reviewer.lost` 由本步处理，唤醒只有这一个处理处） | W-P2（**principle-agents-are-woken-not-polled** 的本地形式就是「then end your turn」） |
| 第 6 步 `Done when` | 搬运：`implement` L86，逐字 | X10 | W-G7 |
| 第 7 步 | 搬运：`implement` L87、L89，命令改名；第 3 句按改写清单第 16 条改写 | S-P3 | W-G7 |
| 第 8 步正文 | 搬运：`implement` L90，去掉句首「Audit: 」（它成了步骤标题）；第 2 句末插 **principle-prove-it-works**。这一句本身就是本地限定（「holds in the product, not only in a test」） | S-P3 | W-P2 |
| 第 8 步的 `(judgement)` | 新写的标记：这一步的工作是判断，点名的原则只是括注（R20 5.2 表编号步骤行「每步点名一个组件或标 `(judgement)`」；R20 S-P7；R21 §4.2 `step-names-component`）。判断标准就是正文第 2 句「holds in the product, not only in a test」与「followed where it applies」。标记放在粗体标题之后。按 R21 §3.3 的切分，标题单元之后的第一句是「(judgement) Read the ticket once more …」，标记是这一句的一部分，所以它写在改写清单第 6 条的新句里 | S-P3 | W-G5 |
| 第 8 步 `Done when` | 搬运：`implement` L92，逐字 | X10 | W-G7 |
| 第 9 步 | 搬运：`implement` L93、L95，命令改名 | S-P3 | 无 |
| 第 10 步 | 搬运：`implement` L96、L98，命令与开关改名 | S-P3 | W-G9（「the default if nobody answers」） |
| 第 11 步 | 搬运：`implement` L99、L101，命令改名 | S-P3 | X3（「Never close the ticket … : a hook blocks the command」禁令带理由） |
| `#### Reading yourself in` 第 1 段 | 搬运：`implement` L16 第 2、3 句，逐字 | R20 5.3 规则簇 | W-G6（baseline 的定义） |
| 第 2 段 | 搬运：`implement` L16 第 4–6 句；第 4 句句首「Then follow」改为「Follow」（改写清单第 19 条） | 同上 | W-G1（「choose what serves the person the Problem Statement names」） |
| 第 3 段 | 搬运：`implement` L16 末句，reference 路径改写（上表）；第 2 句新写，指向 Memory 簇（SSR L30） | 同上 | 无 |
| `#### Memory while working` 第 1 段 | 搬运：`implement` L38–40 前两句（原文的折行合并，T2 第 1 种），第 1 句主语「Your first prompt carries」改为「The start prompt's `Data:` file carries」（改写清单第 20 条）；第 3 句新写，原则点名加本地限定，出处 `implement` L47–49「Verify every Memory against current repository evidence before acting on it」 | R20 5.3 规则簇；簇名取 R18 §3.3 P15 | W-P2 |
| 第 2 段第 1 句 | 搬运：`implement` L51–54 第 1 句，逐字 | 同上 | W-G3（诱惑：先试绕过；替代：先搜） |
| 第 2 段第 2 句 | 新写：按名点名 `memory-records`（R18 §4.1：打开、搜索、保存、更正的做法归该技能） | 同上 | W-G12 |
| `#### While writing code` 第 1 条 | 搬运：`implement` L22，命令改名；两处句末插原则点名。「a false `ALL MET` lands broken behaviour …」一句是 **principle-silence-is-never-a-pass** 的本地后果（R18 §3.3 P15、R20 W-P2 的实例） | 同上；簇名取 R18 §3.3 P15 | W-P2、W-G2 |
| 第 2 条 | 新写：N7「写明打开它的条件与用法」；R18 §4.4：`implement` L24–25 搬进这份 reference | 同上 | 无 |
| 第 3 条 | 搬运：`implement` L32，逐字（原在第 3 步第 2 段） | 同上 | 无 |
| 第 4 条 | 搬运：`implement` L34，逐字（原在第 3 步第 3 段）。第 3 句「This is about extras only: …」限定前一句，两句一起移（T4） | 同上 | W-G4 |
| 第 5、6 条 | 搬运：`implement` L26、L27，逐字 | 同上 | 无 |
| 第 7 条 | 搬运：`implement` L28，命令改名，句末插 **principle-separate-before-serializing-shared-state**；「because one file has one writer at a time and the cut missed an edge」是本地后果（R18 §5.4 第 1 条的例子） | 同上 | W-P2 |
| 第 8 条第 1 句 | 搬运：`mmw-v2/skills/design-pages/SKILL.md` L21 后半句「a dispatched worker never runs it」，代词换成技能名（见改写清单） | 同上 | W-O2（角色不做的事写成边界句） |
| 第 8 条第 2 句 | 新写的正面目标（X3）。出处：`night.md` L84「`child.opened` of kind `contract` naming a Claude Design page … needs a session whose host has the Claude Design MCP tools」 | 同上 | X3、W-G8 |
| `#### While the product runs` 第 1 句 | 新写的指针：mode `## Non-negotiables` 触发行 3 已把「启动、连上、停掉产品」送到 `ui-acceptance` 的 `## Five rules while the product is running`，并搬运了 `PRODUCT_RULES` 第 1 句「Several tickets run on this machine at once.」。源里这一句只有一处，只能搬一次（R21 §3.3 按多重集合计数），每个 worker 都读 mode，所以这里点名 mode 那一行，不复述（K37）。`PRODUCT_RULES` 两句的去处见删去的句子 | 同上 | W-G12 |
| 第 2 句 | 新写，英译 R18 §3.3 P15「产品起不来就开 `fault` 子票后停」；出处 `ui-acceptance` L38「Reporting blocked, in rules 3 to 5, goes through an event … A worker opens a `fault` child, as the `implement` skill says, and stops.」（见改写清单第 10 条）。三种情况按内容写出（人工步骤、够不到产品、流水线自身故障），不按 `ui-acceptance` 的规则编号（X9、N4；R20 K22）：它们对应该节 **Never complete a human step by hand.**、**When the product cannot be reached, report the ticket blocked and stop.**、**A fault in the pipeline itself is reported blocked the same way.** 三条 | 同上 | W-G9 |
| `#### Unattended outlets` 第 1 段第 1 句 | 新写：本角色的决定写到哪里。出处 R18 §2.2 `## Autonomy` worker 那一条「写进 closeout 的 `Decisions I made on my own`」。「屏幕上不放问题、取最可能的选项、写一行、继续」只在 mode `**Unattended.**` 写一次（`README.md` `## 范本共用的约定` 第 3 条） | R20 5.3 `#### Unattended outlets`（R18 §3.3 P15 把这一簇叫 `#### Decisions I made on my own`，说明它「也是本角色的无人出路」） | W-G9 |
| 第 1 段第 2、3 句 | 搬运：`implement` L23 第 3、4 句，命令改名；「instead」保留，意思与原文相同：会改变交付内容的问题开 `decision` 子票，代替只写一行 | 同上 | W-G9；W-G1（读者是 reviewer 与早上的用户） |
| 第 2 段第 1 句 | 新写，英译 R18 §6 表 worker 行「每行 `skip: <步骤标题>: <reason>`」与同节「`--closeout` 的步骤核对」。`skip:` 行本身的格式在 mode `## Playbooks` 定一次（PS mode L117），这里只写 worker 独有的两点：写到收尾评论的哪里，以及为什么要带步骤标题。closeout 的步骤核对是 R18 §6 的设计（B2 只报告、B3 起拒绝），`ticket_state.py` 还不存在（推断） | 同上 | W-G2 |
| 第 2 段第 2 句 | 新写，英译 R18 §6 表 worker 行「原则名写进决定行」 | 同上 | W-G9 |
| `#### Integrating` 第 1 句「Exit 0 is a clean merge, or nothing to merge; a clean merge prints its incoming tickets.」 | 新写。出处：`mmw-v2/skills/dispatch/scripts/dispatch.sh` `integrate_ticket` L2544 至 L2562（本轮读）：已是最新时打印「issue-<n> is already current with origin/<into>」并返回 0；干净合并打印「integrated origin/<into> into issue-<n>; incoming tickets: #…」（或 `none`）并返回 0 | R20 5.3 规则簇；簇名是新增的（见上文「结构决定」） | W-G9（每种结果都有出路，0 也在内） |
| 第 2 句 | 搬运：`mmw-v2/upstream/skills/engineering/resolving-merge-conflicts/SKILL.md` L8 的 MMW 加句「After a clean merge of `origin/<base branch>`, … before changing the combined behavior.」，逐字（R18 §4.2：第 2 步票语句 → P15）。放在退出 0 之后、退出 3 之前：它管的正是干净合并；`resolving-merge-conflicts` 回上游原文（R18 §4.2），这份 playbook 是这句规则唯一的家 | 同上 | W-G13（干净合并时最容易跳过读来票） |
| `#### Integrating` 其余句 | 搬运：`implement` L78 第 2 至 5 句与第 7、8 句（从「Exit 3 leaves a conflicted merge」到「Never rebase, abort or push from this integration command.」），命令改名；「a `fault` sub-issue」改「a `fault` child」。第 6 句「A clean merge that makes repository checks red uses the `resolving-merge-conflicts` skill too.」不搬（见删去的句子） | 同上 | W-G2（「so a resolution that drops their behaviour reopens their ticket hours later」是理由，与规则同段） |
| `#### ABANDON kinds` | 搬运：`implement` L76，「rounds in step 1」改为按标题引用（X9）；两处「sub-issue」改「child」；「rules 3 and 4 of the `ui-acceptance` skill's **Five rules while the product is running** route it」改为指向本文件 `#### While the product runs`（改写清单第 22 条）；「a UI difference never goes here」后加去处「: it is a `contract` child」（改写清单第 21 条） | 簇名取 R18 §3.3 P15 | W-G6（三个 kind 各有定义）；X3（禁令带去处） |
| `#### Opening a child` 第 1 句 | 搬运：`sub-issues.md` L9，把主语「`--sub-issue`」换成完整命令（见改写清单） | 新簇，理由见「偏离」 | 无 |
| 第 2 句 | 改写自 `implement` L18 第 1 句（见改写清单） | 同上 | W-G12 |
| 第 3 句 | 改写自 `sub-issues.md` L11 末句（见改写清单）；R18 §3.3 P15 来源列「`sub-issues.md` 第 11 行里属于 worker 的部分」 | 同上 | W-G1（读者是谁，所以正文要自足） |
| 第 2 段 | 搬运：`implement` L18 第 2 句，命令改名，句末插原则点名 | 同上 | W-P2 |
| `#### The review round` | 搬运：`implement` L84 从「The in-ticket round is first」到段末，命令改名，「re-run step 1」改为按标题引用；新写一句「This round is the `tdd` skill's refactoring pass: restructure here, not under the next red.」，出处 `tdd` L38 MMW 加句「Working from a ticket, that pass is the round of fixes that follows its review」（R18 §3.3 P15 第 6 步「这一轮修复就是 `tdd` 的 refactor 轮」） | 新簇（见上文「结构决定」） | W-G3（诱惑：拿周边代码的真事实当反驳；替代：写出推翻这条主张的东西） |
| `#### When the orchestrator resumes you` | 新写，英译 R18 §3.3 P15「照 `resume` 送来的那句话做，再跑 `where`，从它印出的步骤继续」与 R18 §7.1「`dispatch.sh resume` 把 orchestrator 的那句话原样送进去」 | R20 5.3 唤醒处理簇；簇名是 `roles.json` 登记的标识符（R19 §4.2 保留，S-O1） | 无 |
| `#### After the closeout of an adopted ticket` | 搬运：`inside-a-ticket.md` L13，逐字 | 同上；簇名按 R19 §4.2 | X3（「Do not run `land` …: it stops every session …」带理由） |
| `**Reply:**` | 新写，英译 R18 §3.3 P15「交付物：`--closeout` 退出 0 的收尾评论，它就是 worker 的回复」；在场时补的三项出处 `implement` L96 的 `ABANDON: … decision` 行与 R18 §2.2 `## Writing the reply` | R20 5.3 `**Reply:**` | 只写本 playbook 独有的内容 |

## 必须改写、做不到逐字搬运的地方

1. 全文的命令、开关、文件、技能、原则改名（上表「全文通用的机械改名」）。其中 `verify-ticket.py` → `ticket_state.py` 不是改名表里的 token 替换，而是 R18 §7.6 的脚本拆分，要按 R19 §7 注意事项第 4 条写成整句 `replace`。逐句如下（原句都在 `implement`；新句逐字取范本；句中别的改动在后面各条另记，这里的新句已含它们）：
   - L12 第 1 句「First claim the ticket: `verify-ticket.py <n> --preflight`.」→「First claim the ticket: `ticket_state.py <n> --claim`.」
   - L18 第 2 句「A fault in the pipeline itself (the pipeline's own scripts, a hook, or `.mmw/target.json`): `verify-ticket.py <n> --sub-issue fault <file>`, whose body is the command you ran and the output you saw, then stop.」→「A fault in the pipeline itself (the pipeline's own scripts, a hook, or `.mmw/target.json`): `ticket_state.py <n> --open-child fault <file>`, whose body is the command you ran and the output you saw, then stop (**principle-report-faults-through-the-pipeline**).」
   - L22 第 5 句「When something this ticket was told to follow does not hold, …, keep going and run `verify-ticket.py <n> --sub-issue contract <file>`.」→ 同一句，命令换成「`ticket_state.py <n> --open-child contract <file>`」，其余逐字。
   - L23 第 3 句「A question whose answer would change what the ticket delivers gets `verify-ticket.py <n> --sub-issue decision <file>` instead, and the rest of the work carries on.」→「A question whose answer would change what the ticket delivers gets `ticket_state.py <n> --open-child decision <file>` instead, and the rest of the work carries on.」
   - L28 第 1 句「…; when the change is merely convenient, leave it and run `verify-ticket.py <n> --sub-issue deferred <file>`.」→ 同一句，命令换成「`ticket_state.py <n> --open-child deferred <file>`」。
   - L28 第 2 句「… whatever needs it: run `verify-ticket.py <n> --sub-issue contract <file>`, because one file has one writer at a time and the cut missed an edge.」→ 同一句，命令换成「`ticket_state.py <n> --open-child contract <file>`」，句末插「(**principle-separate-before-serializing-shared-state**)」。
   - L78 第 5 句「Where theirs and yours cannot both hold, the cut missed an edge: keep what landed and run `verify-ticket.py <n> --sub-issue contract <file>` naming both tickets.」→「… keep what landed and run `ticket_state.py <n> --open-child contract <file>` naming both tickets.」
   - L78「Then run every criterion: `verify-ticket.py <n>`.」→「Then run every criterion: `ticket_state.py <n> --run-and-record-criteria`.」
   - L80「Done when `verify-ticket.py <n>` has recorded a run of your own after the integration.」→「Done when `ticket_state.py <n> --run-and-record-criteria` has recorded a run of your own after the integration.」
   - L81 第 1 句「Post the decisions comment, once: `verify-ticket.py <n> --decisions <file>`.」→「Post the decisions comment, once: `ticket_state.py <n> --decisions <file>`.」
   - L84 末句「Then, for each out-of-ticket review finding whose body the in-ticket round has not made untrue, run `verify-ticket.py <n> --sub-issue finding <file>`.」→「…, run `ticket_state.py <n> --open-child finding <file>`.」
   - L87 第 1 句「Run every criterion one final time: `verify-ticket.py <n> --reverify --actor worker`.」→「Run every criterion one final time: `ticket_state.py <n> --run-and-record-criteria --reverify --actor worker`.」
   - L93「Tell the tickets whose files you changed: `verify-ticket.py <n> --touched`.」→「Tell the tickets whose files you changed: `ticket_state.py <n> --touched`.」
   - L96 第 2 句「A criterion that waits only on one sentence from a person: write `ABANDON: AC<n> decision <question, options, and the default if nobody answers>` **and** run `verify-ticket.py <n> --sub-issue decision <file>`, then keep working the rest; the ticket does not stop.」→ 同一句，命令换成「`ticket_state.py <n> --open-child decision <file>`」。
   - L96 第 3 句「Then `verify-ticket.py <n> --draft`, which prints the path it wrote as `DRAFT: wrote <path>`; give that run no path of your own.」→「Then `ticket_state.py <n> --closing-draft`, which prints the path it wrote as `DRAFT: wrote <path>`; give that run no path of your own.」
   - L99 第 1 句「Close the ticket: `verify-ticket.py <n> --closeout <draft>`.」→「Close the ticket: `ticket_state.py <n> --closeout <draft>`.」
2. `implement` L8「Commands of the `verify-ticket` skill's `verify-ticket.py` and the `dispatch` skill's `dispatch.sh` are named bare below.」→「Commands of this skill's `bash scripts/dispatch.sh` and `python3 scripts/ticket_state.py` are named bare below.」：两个脚本都搬进了 mode 的 `scripts/`（R18 §1.1），第一次点名写出解释器与路径。
3. `implement` L72「Once done, commit your work to the current branch and work through the closing steps below.」→ 只留前半句：`## Closing steps` 这个节不再存在，后面的步骤就在同一个 `#### Steps` 里。
4. `implement` L78「which step 7 puts in the closing-comment draft」→「which **Draft the closing comment** puts …」；`implement` L76「rounds in step 1」→「rounds in **Integrate and run every criterion**」；`implement` L84「re-run step 1」→「run **Integrate and run every criterion** again」。X9：按标题引用，编号一重排就指错。
5. `implement` L84「open the `fault` child as above, then stop」→「… as `#### Opening a child` says, then stop」：「as above」原指 L18，那一句现在在规则簇里。
6. `implement` L90 第 1 句「Audit: read the ticket once more against the branch, the way the user will read your closing comment.」→「(judgement) Read the ticket once more against the branch, the way the user will read your closing comment.」：「Audit」成了步骤标题 **Audit against the ticket**，正文去掉前缀并把句首改为大写；`(judgement)` 标记按 R21 §3.3 的切分属于这一句（R20 S-P7），所以写进新句。
7. `inside-a-ticket.md` L3「You picked ticket `<n>` up yourself」→「You picked the ticket up yourself」；L9「**`adopt <n> [--into <branch>]`**: run it from …」→「Run it from …」（原文是退出码表的一行，放进入口要去掉命令标签并大写句首）。
8. `design-pages` L21「a dispatched worker never runs it」→「A dispatched worker never runs the `design-pages` skill.」：代词在新位置没有所指。
9. （已并入删去的句子：`PRODUCT_RULES` 第 2 句不再搬进本文件，由 mode 触发行 3 与 `#### While the product runs` 第 1 句的指针承接。）
10. `ui-acceptance` L38「A worker opens a `fault` child, as the `implement` skill says, and stops.」→ `#### While the product runs` 第 2 句「When those rules have you report the ticket blocked (a human step, an unreachable product, a fault in the pipeline itself), open a `fault` child as `#### Opening a child` says, and stop.」：`implement` 回上游原文后不再说这件事，开子票的写法在本文件的 `#### Opening a child`；原句同段的「in rules 3 to 5」换成三种情况本身，不跨文件按编号引用（X9）。`ui-acceptance` L38 原句留在原处（copy）。
11. `sub-issues.md` L9「`--sub-issue` takes a kind and a file …」→「`ticket_state.py <n> --open-child <kind> <file>` takes a kind and a file …」。
12. `implement` L18 第 1 句「Every `--sub-issue` run below is in the `verify-ticket` skill's `references/sub-issues.md`.」→「Which kind it is: the `verify-ticket` skill's `references/child-issues.md`.」：命令搬到了 `ticket_state.py`，`verify-ticket` 只留 kind 的判别问题（R18 §4.1 verify-ticket 行），文件按 R19 §4.5 改名。
13. `sub-issues.md` L11 末句「None of these readers has seen your session, so the body stands on its own.」→「The child's readers have not seen your session, so the body stands on its own.」：「these readers」指的是同一段里被删去的四类读者（见删去的句子）。
14. `night.md` L7 第 2 句「A ticket handed back with its reason on it is a good result; a criterion loosened, or a worker resumed again and again with `continue`, to make one close is a defect that lands under a green mark.」→ 首段第 4 句「A ticket handed back with its reason on it is a good result; a ticket closed on a bent check is a defect that lands under a green mark.」：原句后半说的是 orchestrator 的行为（`continue` 反复续跑），worker 没有这个动作。
15. `implement` L16 句首「Then read yourself in, …」→「Read yourself in, …」：「Then」承接的是 L12–14 的认领，那部分现在是另一个步骤。
16. `implement` L87 第 3 句「If anything still fails, write `ABANDON: AC<n> failed` for each failure and close out `HANDOFF REQUIRED`; this final run gets no fix round.」→「If anything still fails, write `ABANDON: AC<n> failed` for each failure; the closeout will be `HANDOFF REQUIRED`, and you carry on with **Audit against the ticket**. This final run gets no fix round.」：「close out `HANDOFF REQUIRED`」能读成立刻跳到 **Close out**，跳过 **Audit against the ticket** 到 **Draft the closing comment** 三步；R18 §6 的步骤核对要求这三步都有痕迹。
17. 「sub-issue」→「child」逐句 `replace`：`#### Integrating`「a pipeline failure becomes a `fault` sub-issue」→「… a `fault` child」；`#### ABANDON kinds`「points at the sub-issue that records them」→「points at the child that records them」、「its sub-issue is already open」→「its child is already open」；第 2 步「its own open sub-issues」→「its own open children」。
18. `implement` L16 的子票查询「(`gh api --paginate repos/{owner}/{repo}/issues/<n>/sub_issues?per_page=100 --jq '.[] | select(.state=="open")'`)」→「(the `verify-ticket` skill's `python3 scripts/issue_tree.py <n> --root ticket` prints each child with its state)」。理由：同一件事在全套只留一条路（`verify-ticket` 范本 `## Read the tree under an issue`），技能文本不点工具名（S-G8，与 `verify-ticket` 注解改写清单第 5 条的处理一致），而且 `issue_tree.py` 在列表短于 tracker 给的数目时拒绝回答，手写的分页查询没有这道检查。本轮核实：`issue_tree.py` docstring L30–31「Every issue comes back as its number, title and state」，`--root` 取 `map|spec|ticket`（L4），文件没有执行位，所以写出 `python3`。它会列出所有子票，开着的要由 worker 按 state 挑出来；是否加一个只列开着的开关，由拆分票决定。
19. `implement` L16「Then follow **Parent** to the spec: …」→ `#### Reading yourself in` 第 2 段「Follow **Parent** to the spec: …」：「Then」承接的是留在第 2 步的枚举句，那一句不在同一处了。
20. `implement` L38「Your first prompt carries two Memory indexes, …」→「The start prompt's `Data:` file carries two Memory indexes, …」：R18 §2.3 把启动提示词定为一行，Memory 索引在它的 `Data:` 文件里。
21. `implement` L76「a UI difference never goes here」→「a UI difference never goes here: it is a `contract` child」。原文只禁不指（X3）。去处是推断：`sub-issues.md` 判别问题第 2 条「a baseline … lacks a state, field or case, or contradicts another such source」→ `contract`，界面的 baseline 是设计包与 screen contract（`implement` L16「A design package is copied exactly」）。本轮在 git 历史里找到这半句首次出现在提交 `d541e10e`，提交里没有写理由。写 spec 的人要核实后再把这一句写进票；核实不了就改成 `drop` 半句的登记。
22. `implement` L76「A human step or an unreachable product while the product runs is not `stuck`: rules 3 and 4 of the `ui-acceptance` skill's **Five rules while the product is running** route it.」→「A human step or an unreachable product while the product runs is not `stuck`: `#### While the product runs` routes it.」：原句按编号跨文件引用另一个技能的规则（X9、N4），编号一重排就指错；同一件事本文件 `#### While the product runs` 已按内容写出去处，按簇名点名它。
23. `inside-a-ticket.md` L11 标题 `## After the closeout` → `#### After the closeout of an adopted ticket`：R19 §4.2 的簇名（它是 `roles.json` 登记的唤醒处理处，N10）。标题只与标题比（R21 §3.3），写成 `replace`。

## 删去的句子（写成 `drop` 行时用）

- `implement` 的三个节名与一行引导句：L10 `## Claim, read in, write the code`、L36 `## Shared experience while implementing`、L70 `## Closing steps`，以及 L20「While writing code:」。它们组织的是 `implement` 里认领、读入、写码，Memory，收尾这几组段落。删后由本 playbook 的结构组织：认领、读入、写码与收尾各成 `#### Steps` 下的编号步骤，Memory 的做法在 `#### Memory while working`，写码时的规则在 `#### While writing code`（R21 §3.3：标题只与标题比，这些节名在目标里没有同名标题，要逐个写 `drop`）。
- `inside-a-ticket.md` L1 `# A ticket you picked up yourself` 与 L7 `## Exit codes`：前者是整份 reference 的标题，删后由 `**Entry.**` 的粗体标签 **Adopted ticket.** 组织；后者只装 `adopt` 一行，那一行的句子进了同一个入口（改写清单第 7 条）。`inside-a-ticket.md` L11 `## After the closeout` 不删，改名为 `#### After the closeout of an adopted ticket`，写成标题的 `replace`（R19 §4.2）。
- `implement` L6「Implement the work described by the user in the spec or tickets.」：它指导「没有票时按 spec 做」。本 playbook 只在票上跑，删后由所有权行与 **Read yourself in** 指导。
- `implement` L12 第 3 句「If you picked the ticket up yourself, with no `start` behind you, do what the `dispatch` skill's `references/inside-a-ticket.md` says before that claim.」：它指导自己拿起的票。删后由 `**Entry.**` 的 **Adopted ticket.** 指导（R20 T9 的示例句就是这一种）。
- `implement` L74「A ticket you are prompted back into: claim it again first, `verify-ticket.py <n> --preflight`, and carry on at the step its `RESUME:` line names.」：它指导被叫回的 worker。删后由 `**Where you are.**` 与 R18 §7.7 表的「`ticket.returned` 或 `ticket.bounced` 之后 → `AT` **Claim**，然后从 **Integrate and run every criterion** 起」指导。
- `implement` L78「A criterion passes only when its `CHECK` exits 0 and its output matches `EXPECT`.」：它指导「怎样算通过」。删后由 `verify-ticket` 技能的目标段指导（本轮能力技能范本把这一句移到了那里，S-P5）；worker 读的是运行结果，不自己判定通过。
- `implement` L24、L25：移到 `references/code-writing-rules.md`（R18 §4.4），由 `#### While writing code` 第 2 条指向。
- `implement` L38–41 第 3 句（`truncated:` 行）、L43–45、L47–49、L54 第 2 句至 L64、L66–68：方法部分移到 `memory-records`（R18 §4.1）；L47–49 的立场由 **principle-clues-are-not-evidence** 指导，本文件留一句本地限定。
- `implement` L23 第 1、2 句（「Put no question on the screen. Take the option … and keep going.」）：它们指导无人会话遇到问题时怎么办。它们进了 mode `**Unattended.**`（`exemplars/mmw/SKILL.notes.md` 逐段来源），本文件不复述；删后由 mode `## Autonomy` 与本文件 `#### Unattended outlets` 第 1 句的去处指导。
- `implement` L78 第 6 句「A clean merge that makes repository checks red uses the `resolving-merge-conflicts` skill too.」：它指导「干净合并后仓库检查变红」。检查真正运行是在 **Close out**（`--closeout` 跑仓库的 `checks`），第 11 步的「When the repository's own checks fail and the failing check covers code an incoming ticket of your integration changed, the failure is the merge's: use the `resolving-merge-conflicts` skill.」（`implement` L99）在那个时刻说同一件事，mode 触发行「A merge conflicts, or a clean merge turns the repository checks red」也点名它。删后由这两处指导；留在 `#### Integrating` 会让 worker 以为合并一结束就要查检查。
- `dispatch.sh` L109 `PRODUCT_RULES` 两句不进本文件：第 1 句「Several tickets run on this machine at once.」搬进 mode 触发行 3（源里只有一处，只能搬一次）；第 2 句「Before you start, reach or stop the product, read 'Five rules while the product is running' in the ui-acceptance skill.」指导「worker 碰产品之前读五条规则」，删后由 mode 触发行 3 的第 1 句（同一条件、同一去处）与 `#### While the product runs` 第 1 句的指针指导。常量本身随 R18 §2.2 删去。
- `sub-issues.md` L11 前两句（每种 kind 由谁、何时读）：R18 §4.1 定「谁在何时读」→ 各角色的唤醒行。worker 需要的只有「读者没看过你的会话」这一点，已留下。
- `tdd` L22 其余 MMW 加句（「The agreement is something written down, never a remark in conversation.」「With no ticket in hand, write the seams down and confirm them with the user.」）：R18 §4.2 `tdd` 行说它们随 `tdd` 回原文一并撤回；票上的 `## Seam` 就是书面约定，由第 3 步第 2 句指导。

## 与 R18 的偏离

- **第 10、11 步的内容分界**。R18 §3.3 P15 把「只有人能答的判据写 `ABANDON: AC<n> decision …` 并开 `decision` 子票」放在第 11 步 **Close out**。`implement` L96 里这件事在写草稿之前做，草稿要把 `ABANDON:` 行放到对应判据下；放到 **Close out** 就晚于草稿。R18 同时说「标题一一对应 `implement` 原文」，`implement` 第 7 步正是草稿步，所以范本照 `implement` 原文放在第 10 步。
- **`#### Unattended outlets` 代替 R18 的 `#### Decisions I made on my own`**：R20 5.3 骨架要求这个固定簇名；内容相同。
- **新增 `#### Opening a child`**：R18 §3.3 P15 的来源列有 `implement` L18 与 `sub-issues.md` L11，但没有给它们指定规则簇。步骤里多次用到 `--open-child`，放一个家比每次重复强（SSR L17 事实 7 的一个意思一个家）。
- **新增 `#### Reading yourself in`、`#### Integrating`、`#### The review round`**：见上文「结构决定」。R18 §3.3 P15 没有这三个簇。
- **R18 §5.3 给 **Audit against the ticket** 的本地一句**「在票里，真物就是判据在 `HEAD` 上的运行」没有采用：`implement` L90 原文说的是「holds in the product, not only in a test」，与那句方向相反。范本保留原文，只加原则点名。
- **规则簇的位置**：`orchestrate.md` 把规则簇放在 `#### Steps` 前后都有；R20 5.3 表定 MMW 统一放在 `#### Steps` 之后，按步骤第一次点名的顺序排。R20 5.3 的骨架原先把 `#### Unattended outlets` 画在最后，与同一节的表不一致；范本照表排，R20 已按范本补 S-O3 并改了骨架的注释：先是步骤点名的簇，按第一次点名的顺序，然后是 `roles.json` 登记的唤醒处理簇。

## 没有核对的

- `ticket_state.py` 还不存在，`--claim`、`--run-and-record-criteria`、`--open-child`、`--closing-draft` 的退出码沿用 `verify-ticket.py` 今天的行为（L4072–4100），是推断。
- `dispatch.sh where <n>` 还不存在（R18 §7.7 设计，B0 加入）；**Where you are.** 按它的设计写。
- `dispatch.sh integrate <n>` 的退出码本轮读 `integrate_ticket`（`dispatch.sh` L2529 至 L2570）核对：0 是已是最新或干净合并（后者打印来票），3 是留下冲突的合并，2 是 `refuse` 或 git 合并失败。`dispatch.sh` 的 usage（L377）没有写退出码。
- 自己拿起的票（**Adopted ticket.**）没有启动提示词，也就没有 `Data:` 文件；它的 Memory 索引从哪里来，R18 没有说。今天 `implement` L38 的「Your first prompt carries two Memory indexes」对 adopt 会话同样不成立（推断）。写 B2 票的人要定：`adopt` 是否也写一份数据文件。
- 这份 playbook 对 agent 行为的作用没有实测（R20 第 8 节）。

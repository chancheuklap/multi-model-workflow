# 白天 playbook 范本注解：`exemplars/mmw/playbooks/write-a-spec-and-tickets.md`

这份范本是 R18 §3.3 P1（原名 **Define a change**）按 R20 写成的样子，名字按 R19 §4.2 改为 **Write a spec and tickets** · `write-a-spec-and-tickets`（R19 结论「改」，不是用户定项）。给写 B1 这份 playbook 的票当基准。

缩写：`ask-matt` = `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md`（残留，不安装，R18 §4.2 最后一行：主流程 → P1）；`to-spec`、`to-tickets`、`triage`、`grilling`、`grill-with-docs` 均指 `mmw-v2/upstream/skills/` 下现行文件；`several-specs.md` = `mmw-v2/upstream/skills/engineering/to-spec/references/several-specs.md`。这份文件有两种安排：R18 §3.3 P1 第 6 步与 §9.4（「循环 → P1 …；判断一句留 to-spec | 拆」）让它整份并入本 playbook 的 `#### Several specs from one reference`，`to-spec` 只留判断划分的一句；R19 §4.5 第 189 行与 §7 的 `path`、`token` 两行（第 375、383 行）却把它留作 `to-spec` 的 reference 并改名 `spec-division.md`。范本照 R18：文件解散，内容全部进规则簇，`to-spec` 留 L14 的判断与 L16 的指针（指针的去处改由 `to-spec` 分叉票定）。两份计划不能同时进票：同一份内容既 `move` 走、又对空文件 `rename path`，词表 **spec division** 的 `_Home_`（`docs/contexts/tickets/CONTEXT.md` L73）就会指向不再承载这条规则的文件。R19 那三行与词表 `_Home_` 要随之改，见 `README.md` `## 已知的必须改写处` 第 3 组。

## 用的是哪种骨架

R20 5.2 的「长形态」（`### <Name>` → 所有权行 → 首段 → `**Entry.**` → `#### Steps` → 规则簇 → `**Reply:**`），加 R20 S-P6 的事实表式 `**Where you are.**`。理由：R20 5.2 长形态默认没有 `**Where you are.**`，S-P6 为跨会话、又没有 `where` 命令的白天 playbook 留了这一行，它正是按本范本补写的；R18 §3.3 P1 明写本 playbook 有「九行事实表」式的 Where you are（R12 K-33），而且它确实跨会话：**Ask the one who knows** 结束回合、`#### Several specs from one reference` 要用户下次再跑，下一个会话必须从 tracker 与仓库的事实找回位置。这属于 R20 5.3 引言所说的第一类「会跨会话的」。没有套 5.3 的全部骨架：本 playbook 只在人在场时跑，R18 §2.2 `## Autonomy` 没有给它无人出路，所以没有 `#### Unattended outlets`，而是在 `**Entry.**` 用一行 **Unattended.** 把这件事写进 agent 读的正文（R20 W-P3：问人的步骤写出无人出路或点名 mode `## Autonomy`）；`roles.json` 不给它登记唤醒，所以没有唤醒处理簇；也没有脚本能算出它的位置（R18 §7.7 的表只有角色行），所以 **Where you are.** 是一张事实表，不是一条命令。

## 逐段来源

| 段 | 来源 | 结构依据（pstack） | 写法依据（mattpocock） |
|---|---|---|---|
| `### Write a spec and tickets` | R19 §4.2 | S-P1（`PS:skills/poteto-mode/playbooks/bug-fix.md` L1） | 无 |
| 所有权行 | 搬运：R18 §3.3 P1「所有权」项给出的英文原句；出处 `to-spec` L6「A call on what the user sees, what happens to money, or what is in scope … is not yours」 | S-P1、R20 5.2 所有权行（`bug-fix.md` L3） | 说清谁决定什么（R20 5.2 表） |
| 首段第 1 句（目的与下游） | 新写。出处：`to-spec` L6「A spec is the last text a person checks before agents build from it unattended」、`to-tickets` L10「Each ticket is read by agents who were not in this conversation and cannot ask it anything」 | R20a P2 第 3 项的可选纪律段（`bug-fix.md` L5） | W-G1 |
| 首段第 2 句（下游怎样用） | 新写。出处：`implement` L16「then only the Implementation Decisions sections the ticket names」「Where the ticket is silent, choose what serves the person the Problem Statement names」 | 同上 | W-G1 |
| 首段第 3 句（决定结果的那一步与代价） | 新写。出处：`grilling` L6、L8 的 **design tree**、**frontier**；`to-tickets` L10「a choice left open is made at night by a worker who cannot ask」。按 S-P5 不复述 `to-tickets` 原句，改从整条链的角度写 | 同上 | W-G13（标出决定结果的那一步）；W-G1 的代价 |
| 首段第 4 句（诱惑与替代动作） | 新写。出处：`grilling` L46「The session is done when the frontier is empty」；诱惑是推断（本范本没有观察到的运行支持，按 T5「情况是推断的在句中说明」，句子只点名了情况，未声称观察过） | 同上 | W-G3、W-P1 |
| `**Entry.**` 前三行 | 新写，英译 R18 §3.1 P1 行「入口」列与 R18 §3.3 P1 **Entry**：P3、P4、P6 交过来的进 **Write the spec**；P7 **Triage an issue** 交来的 issue 进 **Split into several specs when it is several**，与 **Where you are.** 第 4 行对同一事实（「an issue triaged `ready-for-agent`」）给的步骤相同（见「偏离」）；名字按 R19。写成每个入口一行、粗体标签的列表，与 `work-a-ticket` 同一种形式（R20 S-P8） | R18 §3.2「MMW 多出」；R20 S-P8 | 无 |
| `**Entry.**` **Unattended.** 一行 | 新写。出处：R18 §2.2 `## Autonomy` 只给 worker、reviewer、advisor 等脚本起的角色无人出路，本 playbook 由人起；R20 W-P3 要求问人的步骤写出无人出路或点名 mode `## Autonomy`。第 1、3、4、5 步都把决定交给用户，所以无人会话能做的只有把产品问题写到它的角色记录决定的地方，然后停下；「records the product question where its role records a decision」按名点名 mode `**Where each role records a decision.**`，不复述各角色的去处 | R18 §3.2「MMW 多出」 | W-G9、W-P3 |
| `**Where you are.**` 首句 | 新写：R12 K-33 的「第一个成立者胜」与 K-41 的本地一句「事实只取 tracker、仓库与用户本条消息，不取会话记忆」；原则按 R19 §4.3 `the-tracker-is-the-state` → `resume-from-durable-state` | R18 §3.2「MMW 多出」 | W-P2（原则旁写本地限定） |
| 九行事实表 | 新写，英译 `docs/research/workflow-compare/reports/R12-mmw-master-placement.md` L138 的九行；步骤名换成 R18 §3.3 P1 的标题与 R19 的新名；第 3、4 行指向 **Split into several specs when it is several**（R12 写「Spec」，见下文「偏离」）；第 6 行照 R12 写 `pull-report.md` 已提交；`mmw-v2/skills/design-pages/references/pull.md` L16「Commit the design package and `pull-report.md` together.」证实它与设计包一起提交 | 同上 | W-O1 的精神：事实取可观察的记录 |
| `#### Steps` | R20 5.2 长形态 | S-O2 | 无 |
| 第 1 步 **Interview.** 正文第 1 句 | 新写，英译 R18 §3.3 P1 第 1 步「`grilling` 与 `domain-modeling`（用户输入 `/grill-with-docs` 的会话就处在这一步）」 | S-P3；R18 §3.2「每步点名一个组件」 | W-G12（点名不复述） |
| 第 1 步第 2 句「What is written down is all that a session resuming this playbook, and every worker of the night, will know of it.」 | 新写：第 1 句「write each term and hard decision down」的理由。出处：`ask-matt` L18「it's stateful, retaining what it learns in `CONTEXT.md` and ADRs … `grill-with-docs` is the one that leaves a paper trail」；本文件 `#### Session boundaries` 第 5 段（新会话从 `CONTEXT.md` 与 ADR 读回 **Interview** 的决定）与 **Where you are.**（只读持久的事实）都依赖这份记录；首段「a worker … settles alone」说明夜里的 worker 只拿到写下来的东西。只写规则不写理由时，agent 容易只记词、不记决定（R20 §7.5 第 2 条，推断） | 同上 | W-G2（理由在规则旁） |
| 第 2 句（research） | 新写，同上「仓库外的一手事实用 `research`」 | 同上 | 无 |
| 第 3 句（attack-the-premise） | 新写。R18 §3.3 P1 第 1 步点名 **principle-attack-the-premise**，但它的适用情境是「两次共用一个前提的修复都失败」（`principle-attack-the-premise` description），一次访谈不总是这种情况；按 W-P2 写成本地限定：只在想法本身是一次修复时适用。出处 `grilling` L44「When two or more attempts that share one premise have failed, suspect the premise, not the attempts.」 | 同上；N2 | W-P2 |
| 第 4 句（指向规则簇） | 新写：SSR L30，指针放在需要它的那一步 | R20 5.3 规则簇排序 | 无 |
| 第 1 步 `Done when` | 新写：按名引用 `grilling` L46 的完成判据，不复述 | X10 | W-G7 |
| 第 2 步第 1 句 | 搬运：`ask-matt` L19 第 2 句前半，结尾「detour through **the `prototype` skill**」改为「run **Prototype**」（见改写清单） | S-P3 | 无 |
| 第 2 步第 2 句 | 搬运：`ask-matt` L19 第 3 句，逐字 | 同上 | W-G2（冒号后是理由） |
| 第 2 步第 3 句「When it does not fit, follow `#### Session boundaries`.」 | 新写的指针（SSR L30）。被删的 `ask-matt` L19 末句原本管「原型放不进 smart zone 时换不换会话」（见删去的句子），删后由这个指针把 agent 送到 `#### Session boundaries` 第 2 段的做法；smart zone 的定义也在那一段 | S-P3 | K30（agent 必须选、文本沉默的地方） |
| 第 2 步第 4 句 | 搬运：`ask-matt` L21 第 1 句，逐字（含粗体） | 同上 | W-G6（leading word） |
| 第 2 步第 5 句 | 新写，英译 R18 §3.3 P1 第 2 步「它的 UI 结论经 **Design an interface** 回到 **Write the spec**」；名字按 R19 | 同上 | 无 |
| 第 2 步 `Done when` | 新写。出处：R18 §3.3 P4 第 5 步「答案写进叶目录 `README.md`（`prototype` 规则 6）」 | X10 | W-G7 |
| 第 3 步 | 新写。条件取 `to-questionnaire` description「a decision or a grilling round is blocked on knowledge that lives in someone else's head」；「结束回合」取 R18 §3.3 P1 第 3 步；回到 **Interview** 取 R12 L138 第 8 行 | S-P3 | W-G12 |
| 第 3 步 `Done when` | 新写 | X10 | W-G7 |
| 第 4 步的 `(judgement)` | 新写的标记：这一步的工作是判断，点名的 **Make a small change** 只是 No 分支的去处（R20 5.2 表编号步骤行；R20 S-P7；R21 §4.2 `step-names-component`）。判断标准写在第 3 句「small enough that the user will check it directly」。标记放在粗体标题之后；按 R21 §3.3 的切分它属于标题之后的第一句，所以写进改写清单第 2 条的新句 | S-P3 | W-G5 |
| 第 4 步第 1 句 | 改写：`ask-matt` L22「**Branch: is this a multi-session build?**」→「Decide whether this is a multi-session build.」（见改写清单第 2 条） | S-P3（首句是能勾掉的动作，因为步骤会原样抄进待办） | W-G5（是非判断） |
| 第 4 步第 2 句 | 改写：`ask-matt` L26 第 1 句，「the branch」→「the answer」（见改写清单第 2 条） | 同上 | W-G2（这一句就是理由） |
| 第 4 步第 3 句 | 搬运：`ask-matt` L26 第 2 句，逐字 | 同上 | 无 |
| 第 4 步第 4 句 | 新写，英译 R18 §3.3 P1 第 4 步「小到用户直接检查 → **Direct change**，本 playbook 结束」；名字按 R19 | 同上 | 无 |
| 第 4 步 `Done when` | 新写 | X10 | W-G7；W-G9（这是用户能听到的决定） |
| 第 5 步 | 新写。第 1 句取 R18 §4.1 `to-spec` 行「`to-spec` 留下「怎样判断划分」一句」（即 `to-spec` L14，在 `## Process` 第 1 步的第 2 段；`to-spec` 的编号步骤没有标题，所以指针只能落到节名，N8）；第 2 句仿 `to-spec` L16「Several, or a reference that already carries a **spec division** …: read [references/several-specs.md]…」，指向本文件的规则簇；「a **spec division**」逐字取 L16，是词表 `docs/contexts/tickets/CONTEXT.md` 的术语 **spec division**（W-G6：定义过的术语不换成「a division」） | S-P3；S-G9（这一步的材料超过 150 词，放进规则簇） | W-G12 |
| 第 5 步 `Done when` | 新写 | X10 | W-G7 |
| 第 6 步第 1 句 | 新写：点名 `to-spec`；「with a division …」是新写的衔接 | S-P3 | 无 |
| 第 6 步第 2 句 | 改写：`triage` L82 从「write a spec with the `to-spec` skill」到「a comment linking that spec」，含写新 spec 与扩写已发布 spec 两条路（见改写清单第 7 条）；R12 K-15 与 ADR 0001 L20 定：关 issue 这件事属于发布 spec 的会话 | 同上 | 无 |
| 第 6 步 `Done when` | 新写；两条路各有判据：新 spec 取 `to-spec` L36「Done when `--publish` exits 0」，扩写取 `mmw-v2/upstream/skills/engineering/to-spec/references/revising-a-spec.md` L11 的 Done when（按名引用，不复述） | X10 | W-G7（每条路都能满足、都能失败） |
| 第 7 步 | 第 1 句新写，点名 `to-tickets`；第 2 句新写，英译 R18 §3.3 P1 第 7 步「歧义扫描交给没写这批票的子代理（**principle-a-second-reader-judges**）」；第 3 句新写的本地后果，出处 `code-review` L8「the first reading by anyone who did not write it」（推断：同一会话读自己的假设会当成已定） | S-P3；N2 | W-P2 |
| 第 7 步 `Done when` | 新写；措辞取 `to-tickets` L151「every approved ticket is published as a sub-issue of the spec, with its labels and its blocking edges」 | X10 | W-G7 |
| 第 8 步第 1 句 | 新写，英译 R18 §3.3 P1 第 8 步；命令按 N8、N9 与 `README.md` `## 范本共用的约定` 第 1 条写出解释器与路径 | S-P3；N9 | 无 |
| 第 8 步第 2 句 | 新写的本地后果。出处 ADR 0008 L22「批次检查读错了批次，于是……什么都没打印」；每票一行 `LINT` 取 `mmw-v2/skills/verify-ticket/scripts/verify-ticket.py` L3689–3694 | 同上 | W-P2；W-G3 |
| 第 8 步 `Done when` | 新写；「every `WARN` has been looked at and either fixed or kept on purpose」搬运 `mmw-v2/skills/verify-ticket/references/linting.md` L11 的半句；退出码取 `verify-ticket.py` L4083–4087 `--lint` 的 0。`--lint` 的三个退出码各自之后做什么，写在 `verify-ticket` 范本 `## Output` 的 `--lint` 项 | X10 | W-G7（穷尽措辞「every」） |
| 第 9 步第 1 句 | 搬运：`to-tickets` L160 第 2 句，把「hand over to the `dispatch` skill: opening the night on this spec is one of its rows」改为点名两份 playbook（见改写清单） | S-P3 转交步骤（`bug-fix.md` L13「Run **Opening a PR**.」） | 无 |
| 第 9 步第 2 句 | 新写，英译 R18 §3.3 P1 第 9 步「什么时候开夜由用户定」 | 同上 | W-G9 |
| 第 9 步 `Done when` | 新写。按 R20 5.2 转交步骤：写下一份 playbook 入口读的可观察状态。**Run a night** 的入口读「用户说开夜、spec 上没有 `spec.opened`」（`night.md` L17），所以判据是「用户拿到了 spec 号与 playbook 名，本会话没写 `spec.opened`」 | X10 | W-G7 |
| `#### Session boundaries` 第 1 段 | 搬运：`ask-matt` L32，「steps 1–3」「the `to-tickets` skill」「the `implement` skill」三处改写（见改写清单） | R20 5.3 规则簇（`PS:skills/poteto-mode/playbooks/orchestrate.md` 的 `####` 簇）；簇名取 R18 §3.3 P1 | W-G2 |
| 第 2 段 | 搬运：`ask-matt` L34，「the `to-tickets` skill」与「(see Phase boundaries)」两处改写 | 同上 | W-G6（**smart zone** 是 leading word，带链接定义） |
| 第 3 段 | 搬运：`ask-matt` L65，逐字。SSR L120 要求点名会话命令的文件带这一句一次 | 同上 | S-G8 |
| 第 4 段第 1 句 | 新写，英译 R12 K-49「宿主在阶段中间自动压缩了，就先把摘要里带着、`CONTEXT.md` 与 ADR 里没有的决定逐条与用户确认，再调 `to-spec`」 | 同上 | W-G3（诱惑：信任摘要；替代动作：逐条确认） |
| 第 4 段第 2 句 | 搬运：`mmw-v2/upstream/skills/engineering/ask-matt/PHASE-BOUNDARIES.md` L5 末句「Compacting mid-phase makes the agent lose the thread.」，整句逐字、句号照原文，句号前插原则点名（T2 附加项；R18 §5.2 表：这条原则的出处就是 `PHASE-BOUNDARIES.md`，R12 K-49 也点名了这一句） | 同上 | W-P2 |
| 第 4 段第 3 句「A spec written from that summary states a decision the summary flattened as settled.」 | 新写的本地后果（W-P2），单独成句，不接在搬来的句子上（T3：改标点、合并两句都不是机械改写）；短语「a decision the summary flattened」逐字取 `PHASE-BOUNDARIES.md` L42 末句 | 同上 | W-P2、W-G2 |
| 第 5 段 | 新写。它回答第 3 步「end your turn」与本簇第 1 段「one unbroken context window」之间 agent 必须选、文本沉默的地方（K30）：同一会话收回问卷就没有断；换了新会话，就从 **Where you are.** 第 8 行找位置，从 `CONTEXT.md` 与 ADR 读回 **Interview** 记下的决定（第 1 步「write each term and hard decision down as the `domain-modeling` skill says」），其余逐条与用户确认，做法同第 4 段。出处：R12 K-49 的同一逻辑；`ask-matt` L86「What comes back is material for the `grill-with-docs` or `to-spec` skills」。换会话时丢掉的正是没写下来的决定，这是推断，没有观察到的运行 | 同上 | W-G9；W-G3 |
| `#### Several specs from one reference` 簇名 | 搬运：`several-specs.md` L1 的 H1，逐字 | 同上 | 无 |
| 簇第 1、2 段 | 搬运：`several-specs.md` L3、L5，五处改写（见改写清单第 5、6、11 条） | 同上 | W-G9：交给用户的判断写明了 |
| 簇末句「Stopping ends …」 | 新写：消除「stop」与 **Cut the tickets** 的歧义。出处：`to-spec` L125–127 `## Next`「The `to-tickets` skill.」说明上游在写完一份 spec 后仍去切票 | 同上 | K30「agent 必须选择而文本沉默的地方」 |
| `**Reply:**` | 新写，英译 R18 §3.3 P1 **Reply** 项，去掉其中「`skip:` 的步骤」一项（见「偏离」）；末句写 **Decide who checks** 走 **No** 时的回复，出处 R18 §3.3 P1 第 4 步「本 playbook 结束」：那条路没有 spec 与票，前四项都不存在 | S-P1 末行（`bug-fix.md` L15） | 只写本 playbook 独有的内容（R20 5.2 表） |

## 必须改写、做不到逐字搬运的地方

1. `ask-matt` L19：「detour through **the `prototype` skill**」→「run **Prototype**」。R18 §3.3 P1 第 2 步把去处定为 **Prototype** playbook，不是 `prototype` 技能。
2. `ask-matt` L22：「**Branch: is this a multi-session build?**」→「(judgement) Decide whether this is a multi-session build.」（`(judgement)` 标记按 R21 §3.3 的切分属于这一句，R20 S-P7）。原文是编号列表里的粗体分支名；放进步骤正文，首句要是能勾掉的动作（S-P3），所以问句改成祈使句，并去掉「Branch:」与粗体（T3）。同一处 `ask-matt` L26 第 1 句「In this repository the branch also decides who checks the work」→「In this repository the answer also decides who checks the work」：去掉「**Branch:**」标签后，「the branch」在 git 语境里会被读成 git 分支，改成指前一句问题的答案。两句都写成 `replace`。
3. `ask-matt` L32：「Keep steps 1–3 in …」→「Keep **Interview** through **Cut the tickets** in …」（X9：按标题引用；原文还含 U+2013）；「until after the `to-tickets` skill has run」→「until after **Cut the tickets** has run」；「Each run of the `implement` skill then starts fresh, working from the ticket.」→「Each worker of the night then starts fresh, working from its ticket.」（`implement` 回上游原文且不再安装，R18 §4.2）。
   同一处 `ask-matt` L30 的节名 `### Context hygiene` → `#### Session boundaries`（R18 §3.3 P1 的簇名）：标题只与标题比（R21 §3.3），写成 `replace`。
4. `ask-matt` L34：「before the `to-tickets` skill」→「before **Cut the tickets**」；「(see Phase boundaries)」→「(**principle-decide-at-phase-boundaries**)」（`## Phase boundaries` 随残留 `ask-matt` 不再安装，R18 §4.2 最后一行指向这条原则）。
5. `several-specs.md` L3：「this is the one judgement in this skill」的改写见第 11 条；「tell the user to run this skill against the map again」→「tell the user to run **Write a spec and tickets** against the map again」。
6. `several-specs.md` L5：「tell the user to run this skill next time」→「tell the user to run **Write a spec and tickets** next time」；「[revising-a-spec.md](revising-a-spec.md)」→「the `to-spec` skill's `references/revising-a-spec.md`」（同一个文件，写法按 N8；属 T2 第 4 种，但多了技能名，保守起见列为改写）。
7. `triage` L82：「write a spec with the `to-spec` skill, or extend a published one through that skill's `references/revising-a-spec.md`, citing this issue as a source; close this issue with a comment linking that spec」→「When the source is a triaged issue, write a spec, or extend a published one through the `to-spec` skill's `references/revising-a-spec.md`, citing the issue as a source; close the issue with a comment linking that spec.」加条件从句；「with the `to-spec` skill」删去（同一步第 1 句已点名它）；「that skill's」写成 N8 的全称；「this issue」变成「the issue」。扩写已发布 spec 这条路必须保留：`Done when` 两条路各有判据。
8. `to-tickets` L160：「When the batch is a spec's night run, hand over to the `dispatch` skill: opening the night on this spec is one of its rows.」→「When the batch is a spec's night run, hand over to **Run a night**; one ticket outside a night goes to **Land one ticket**.」（`dispatch` 解散，R18 §4.1 最后一行）。
9. `linting.md` L11 半句进第 8 步 `Done when`：原句主语是「The batch is ready when」，要改成 `Done when` 句式。
10. R18 §3.3 P1、R12 L138 的步骤说明、事实表、K-49 都是中文，只能英译（新写）。
11. `several-specs.md` L3「this is the one judgement in this skill you hand to the user」→「this is a judgement you hand to the user」。原句在 `to-spec` 里成立（那个技能里只有这一个判断交给用户）；搬进 playbook 后，所有权行「The user owns every product call」、第 4 步「the user has heard」、第 9 步「When the night opens is the user's call」都是交给用户的，「the one」与它们矛盾，会让 agent 以为别的产品决定不必交给用户。

## 删去的句子（写成 `drop` 行时用）

- `grill-with-docs` L7 末句「When the session settles a change to build, name the `to-spec` skill as the next step, in this same session.」：它指导「访谈结束后接着写 spec、不换会话」。删后由步骤顺序（**Interview** 在 **Write the spec** 之前）与 `#### Session boundaries` 第 1 段指导。`grill-with-docs` 回上游原文时这一句本来就不在（R18 §4.2 `grill-with-docs` 行）。
- `to-tickets` L20「A plan or a conversation with no published spec goes through the `to-spec` skill first; this skill cuts tickets from the spec's issue number.」：它指导「没有 spec 就切票」的情形。删后由步骤顺序（**Write the spec** 在 **Cut the tickets** 之前）与 **Where you are.** 第 1 行指导。
- `to-spec` L125–127 `## Next`「The `to-tickets` skill.」：同上，由步骤顺序指导（R18 §4.1 `to-spec` 行「`## Next` → 删」）。
- `ask-matt` L19 第 1 句「**Branch: can you settle every question in conversation?**」：它指导何时绕去原型；删后由第 2 步第 1 句的条件指导。
- `ask-matt` L19 末句「Hand off only for a reason on `PHASE-BOUNDARIES.md`'s question 3, such as a host with the Claude Design tools for step 2's interface branch.」：它指导原型阶段要不要换会话；删后由第 2 步第 3 句指向的 `#### Session boundaries` 与 **principle-decide-at-phase-boundaries** 指导，Claude Design 那一支归 **Design a UI**（R18 §3.3 P3 第 1 步）。
- `ask-matt` L21 第 2 句起（Claude Design、`write-screen-contract` 的先后）：它指导 UI 答案的去处；删后由 **Design a UI** 指导（R18 §3.3 P3）。
- `ask-matt` L23–24（Yes → `to-spec`、`to-tickets`、`dispatch`；No → `tdd`）：它指导两条路各自怎么走；删后 Yes 由第 5–9 步、No 由 **Make a small change** 指导。
- `ask-matt` L86「What comes back is material for the `grill-with-docs` or `to-spec` skills.」：它指导问卷回来后去哪；删后由第 3 步末句与 **Where you are.** 第 8 行指导。
- `improve-codebase-architecture` `### 4. Hand the decision on`（L75）的交接半句：R18 §4.2 定它去路由行与本 playbook 的入口；范本的路由行在 mode（「the decision it settles goes to **Write a spec and tickets**」），本文件的 **Where you are.** 最后一行「Anything else → **Interview**」接住它，没有单列。写票的人若要单列，可加一行事实「The user brings a decision `/improve-codebase-architecture` settled → **Decide who checks**」。

## 与 R18 的偏离

- **第 5、6 步的顺序与 R18 相反**。R18 §3.3 P1 是 5 **Write the spec**、6 **Split into several specs when it is several**。`several-specs.md` L3 要求用户先确认划分，然后才写第一份 spec；按 R18 的顺序，第 5 步写完 spec 后才轮到划分，第 6 步的「Then write the first spec only」就与已经写好的 spec 冲突。范本把划分放在前面。R18 的入口「P2、P3、P4、P6、P7 交过来的进 **Write the spec**」只对 P3、P4、P6 保留：它们交来的是单个 UI 设计、结论或修复，直接进 **Write the spec**。P7 **Triage an issue** 交来的 issue 改进 **Split into several specs when it is several**：**Where you are.** 第 4 行对「an issue triaged `ready-for-agent`」已经送到这一步，一份 issue 是一份还是几份 spec 与它怎样到达无关；是一份时这一步的 `Done when` 立刻成立，代价只有一次判断。P2 的地图经路由从头进入，由 **Where you are.** 送到划分那一步。
- **`**Reply:**` 不列 `skip:` 行**：R18 §3.3 P1 的 Reply 项有「`skip:` 的步骤」。`skip:` 行怎样交出是 mode 的通用规则（`## Playbooks`：留在待办里；没有待办工具时列在回复开头），`**Reply:**` 只写本 playbook 独有的内容（R20 5.2 表）；`work-a-ticket` 的 `**Reply:**` 也不列。
- **R12 事实表第 3、4 行原来指向「Spec」**，范本指向 **Split into several specs when it is several**，原因同上。

## 长度与审查提示

- 9 步，全文 1738 词（`wc -w`，含规则簇），超过 S-G9 的约 800 词，已按长形态放进两个规则簇。
- 每一步都在 150 词以内（最长的第 1 步约 120 词）；`#### Several specs from one reference` 约 300 词，是从第 5 步移出的材料（S-G9）。

## 没有核对的

- `to-tickets` 的 ambiguity scan 是否已由它自己派子代理（`to-tickets` L113–119）：R18 §4.1 说那一段移到 mode `## Subagents`，那么 `to-tickets` 分叉后是否还写「派子代理」，决定第 7 步是点名还是指挥。范本按「`to-tickets` 仍持有扫描，本步只加原则」写。
- 这份 playbook 对 agent 行为的作用没有实测（R20 第 8 节）。

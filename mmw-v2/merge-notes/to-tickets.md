# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 我们改的：补上「什么时候用我」——spec 或已批准的计划要变成 agent 一张一张做的那一批票时，以及那一批要 read-back 并报为已发布时。这一行本来就没有引号，值里也没有冒号加空格，保持不带引号。上游改这一行 → 收上游对产出物的措辞，「什么时候用我」保留 |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓要求这个 skill 模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用它。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块同增同删 |
| 第 2 步 `### 2. Explore the codebase` | 我们改的：标题不带 `(optional)`，正文写明只有 spec 的 `## Implementation Decisions` 已点名每张 ticket 写哪个模块或目录时才可省。理由：`## Owns` 要求写 ticket 的一方知道目录布局，而一次目录级 `ls` 很便宜。上游改这一步 → 收上游措辞，这个条件保留 |
| 第 3 步 `### 3. Draft vertical slices` 与第 4 步 `### 4. Write each acceptance criterion` | 我们分的两步：vertical slice 的规则与 wide refactor 在第 3 步，acceptance criterion 的全部规则在第 4 步，其后各步顺延一号。理由：加上四行形态、`CHECK:` / `EXPECT:` 的推导与三条 `CHECK:` 规则之后，一个标题下装两个概念，读的人在 vertical slice 与 acceptance criterion 之间来回跳。上游改这两段的措辞 → 收上游，仍分两步，acceptance criterion 那一步永远排在 vertical slice 之后、blocking link 之前 |
| 第 4 步的 `A criterion is decided by a command, or it is not a criterion.` 与 the five questions | 我们写的：一句判定规则加 the five questions，顺次问、停在第一个 yes——判定是一次比对且材料机器够得着 → 写成 acceptance criterion；判定是一次评价且材料够得着 → 归 code review 的一个 axis（`Standards` 怎么写、`Spec` 是不是要的那件事、`Tests` 某条 `CHECK:` 点名的用例值不值得信），它在另一个 session 里跑，而那句判断经 `to-spec` 的「Revising a published spec」一步写进 spec 对应的 `## Implementation Decisions` 小节——reviewer 的 `Spec` axis 读那一节，且「ticket 点名的 spec 小节里的决定」按 code-review 的判据算 in-ticket；不写进去 reviewer 按票和 spec 找不到就不会判；被判的性质是一个人的反应 → 单开一张 `reaction` 类的 ticket；机器判得了但够不着（设备、凭证、真实环境）→ 单开一张 `reach` 类的 ticket，并写明补上什么之后它就不需要；不是在验而是在取舍 → 进第 6 步的 quiz 问 user（列选项与自己会选的那个），答案写进那张 ticket 的 `## What to build`——出票在白天、user 在场，该问他；写进票 worker 才知道这是票的决定不是自己拿的主意；取舍全部在白天定完，夜里没有出票人留下的取舍，这条路对有没有 wayfinder map 都走得通。理由：`## Acceptance criteria` 里每条都由机器跑、再由 worker 最终全量运行重跑，「过了」才是事实而不是写代码那一个的看法；一条只有自己判得了的 criterion 留在这里，正好废掉这一节存在的理由。上游自己加了 acceptance criterion 的写法 → 收上游措辞，the five questions 保留 |
| 第 4 问的两支、`CHECK:` 自带前置状态那一段、第 8 步的 read-back、`<issue-template>` 的 `## Seam` | 我们写的一组，针对同一个洞：landing pipeline 容易把「测试够不够得着这个状态」当成要么不问、要么永远不行。第 4 问分两支：够得着是可以造出来的，那仍是 acceptance criterion，但到达它的东西必须在 spec `## Testing Decisions` 的 `How a test arrives at a state` 里有名字、并落在某张 ticket 的 `## Owns` 里，两样缺一就出一张 `reach` ticket，retiring line 点名还没名字的机制或该 Owns 它的 ticket——这个状态由此有了终点：到达机制的缺口进 `ready-for-human` queue 等一个 owner，与缺设备、缺凭证同形；真的够不着（设备、凭证、人眼）同样是 `reach` ticket。`CHECK:` 那一段讲两类状态——landing pipeline 自己的（branch、ticket、working tree）与系统的——并指回第 4 问，它是这条脉的入口。第 8 步有一行核对每个到达机制都在某张 ticket 的 `## Owns` 里，并写明 `--lint` 验不了、只能人判。`## Seam` 两半都写：在哪验，与 `How a test arrives at a state`。上游改这几段措辞 → 收上游，两支、入口那句、read-back 那一行与 `## Seam` 的两半保留 |
| 第 4 步 the five questions 之后的五段（四行形态、`CHECK:` / `EXPECT:` 从哪来、不许自己找对象、自带前置状态、fenced block） | 我们加的整块。四行形态：`- [ ] AC<n>:` / `CHECK:` / `EXPECT:` / `EVIDENCE: pending`，编号 publish 时编、不重排——ledger 按编号引用，行号不稳定。`CHECK:` 从 `## Testing Decisions` 的 test layer、目录、precedent 推出，`EXPECT:` 把 precedent 跑一次抄成功那一行（success-only marker）——不这么写就会写出永远不可能匹配的期望。`CHECK:` 不许搜索它验的对象（对象要么是这张 ticket 自己，从 `$MMW_TICKET` 或 branch 名 `issue-<n>` 来，要么在 ticket 上按编号指名）——「搜出来取第一个」验错过东西，也造过一条不可能失败的检查。`CHECK:` 自带前置状态并还原——每条一个独立 shell、cwd 固定在 repository root，而 branch、ticket、working tree 是共享的，reverify 还会把每条再跑一遍。多行命令写进 fenced block，没有 fence 的续行是解析错误——它遇到空行会静默丢掉后面的行。上游自己加了 `CHECK:` / `EXPECT:` 的写法 → 收上游，这五段并进去 |
| 第 6 步 `### 6. Quiz the user` 每张 ticket 的 `Worker` 一行（`junior` / `senior` 加一句理由与选它的判据）与「Is each worker grade right」一问，及 `ready-for-human` ticket 也列出（kind 与看什么）那一段 | 我们加的：worker grade 决定夜里用哪个 model，而机器只查 label 在不在、是不是恰好一个，查不了选得对不对，quiz 是它唯一经过 user 眼睛的地方。怎么选那一档的判据（错了会静默地错——钱要到终态、崩溃后的恢复、装机量已经在读的 contract、安全默认值；`## Seam` 已点名 precedent 的仍走 `junior-worker`）就写在这一行里：删的是票身上那份副本，不是这条指导，判据没有别处可去就会让 grade 变成没有依据的一个词。`ready-for-human` ticket 是同一 batch 的一部分，不列出来 user 看不到早上要看什么。上游改 quiz 那一步 → 收上游的问题清单，`Worker` 一行、这一问与 `ready-for-human` 那一段保留 |
| 第 6 步 `### 6. Quiz the user` 的 `Choices` 一行与「For each choice listed: which option?」一问，及 `<issue-template>` `## What to build` 里「A choice the user settled in the quiz … is a point of its own」那一句 | 我们加的：the five questions 第 5 问送来的取舍在 quiz 里逐张列出问 user，答案在 publish 前写进 `## What to build`。理由见上一行第 5 问。上游改 quiz 那一步 → 收上游的问题清单，`Choices` 一行与这一问保留 |
| 第 7 步的 label 那一句 | 我们改的：两个落点——agent 做的 ticket 打 `ready-for-agent`，并排打第 6 步那张已批准清单给它的 `junior-worker` 或 `senior-worker`；要人判的那张单独的 ticket 打 `ready-for-human`，不带 worker label。要人判的是另一张形态不同的 ticket（没有 `## Seam`、`## Owns` 与 `## Acceptance criteria`），不是这张 ticket 换个 label。上游改这句 → 收上游措辞，两个落点与 worker label 保留 |
| 第 7 步的 sub-issue 那一句 | 我们加的：在 GitHub 上每张 ticket 都建成 spec 的原生 sub-issue（`gh issue create --parent <spec>`，或建完用 `sub_issues` API 挂上去）。理由：上游那一句讲的是 blocking link，ticket 与 spec 的父子关系没有任何一步去建；而 `verify-ticket` 技能 `--lint` 的 ticket graph 与 `status.py --advance-plan` 都只从 spec 的 sub-issue 关系取这一 batch 的 ticket（`issue_tree.py` 一次 GraphQL 读整棵树），脚本还把 ticket 的**直接** parent 当成它的 spec——不挂上去，白天 lint 打一行 `no sub-issues` 就 return 0，night 里一张也 dispatch 不出来。同一句后面我们又加了分类 label：每张 ticket 打 `mmw:ticket`（仓库没有就先 `gh label create`，颜色 `0e8a16`），第 8 步 read-back 顺带核它。理由：mmw #315 第 6 节——board 靠分类 label 知道这一层是 ticket，不数嵌套深度；label 决定 board 怎么读这一层，父链决定脚本怎么找它的 spec，两件事分开。上游改这一步 → 收上游措辞，sub-issue 与 `mmw:ticket` 两句保留 |
| 第 7 步的 `Work the **frontier**` 那一句 | 我们改的：frontier 的条件按 `status.py` 算的那一组写全——open、带 `ready-for-agent`、blocker 全部**合入**（不只是关闭）、无 assignee、无活着的 worker。理由：同一个词在 `status.py`、`## Owns` 的不相交判据与 `dispatch.sh advance` 三处指同一组 ticket，写 ticket 的一方与 `status.py` 不能各有一套读法；「合入」而不是「关闭」是 mmw #315 第 10 节：被阻塞的票从主干切工作树，blocker 只关了、分支没合，切出来的树里没有它的代码。上游改这一句 → 收上游措辞，五个条件保留 |
| `### 5. Give each ticket its blocking edges` 独立成一步 | 我们把它从 vertical slice 那一步摘出来单独成步，那一句正文取上游原文，其后各步顺延。技能正文是 agent 顺序执行的：连 blocking link 这件事留在 vertical slice 那一步、排在 acceptance criterion 之前时，它手上只有 slice 的标题，只能凭印象连；独立成步且排在 acceptance criterion 之后时，每张 ticket 的 acceptance criteria 都已写完。上游改这一段的措辞 → 收上游，仍独立成步、仍排在 acceptance criterion 之后 |
| 第 4 步开头的三条规则 | 我们加的：外部可观察行为、精确值从 spec 或 prototype 的 chosen artifact 抄、一条一断言。上游自己加了 acceptance criterion 的写法规则 → 收上游，三条里它没有的并进去 |
| 第 8 步 `### 8. Read every ticket back` | 我们加的整步：publish 完逐张 read-back，核对标题与 `## What to build` 同一片、spec 的 sub-issue 数等于这一 batch 的 ticket 数、`## Read first` 与 `## Seam` 非空且指向 handoff package 时注明它是 contract、`## Owns` 非空且同一 frontier 两两不重叠、带 acceptance criteria 的每张跑 `verify-ticket` 技能的 `--lint`（参数是这张 ticket 的 issue 号；脚本路径由那份技能自己解析，这里不写。这一步只留 read-back 的义务——ERROR 改到没有、WARN 逐条看过；那次 run 读什么、报什么、退什么码写在那份技能的 `references/linting.md`，这里不复述），`ready-for-human` 的那张核 the five things（`## Parent`、是哪一类、看什么、什么算对、`## Blocked by`）；末尾把 main agent 交给 dispatch 技能，开 night 那一行在它的表里。理由：一次真实 publish 把 8 张 ticket 的标题错位了一格，没有 read-back 就没人发现；后来又出过整批的 `EXPECT:` 全都不可能匹配，脚本静态就查得出。`--lint` 的收敛判据分两级——`ERROR` 改到没有，`WARN` 逐条看过后决定改还是留；没有 `CHECK:` 的 acceptance criterion 报的是 `ERROR`，它是一条归错了档的 criterion。read-back 不是给内容打分，是对 publish 这个动作自检，所以给人判的那张不被豁免，只是核对的东西不同；它核 the five things 而不是三样，因为漏掉的 `## Parent` 与 `## Blocked by` 里，后者正是那种 ticket 上最要紧的一条 blocking link——连错了，人早上会被指去看一个还不存在的东西。上游改了步骤编号 → 顺延，这一步永远在 publish 之后 |
| `<issue-template>` | 我们加的四节：`## Parent`（写到 `## Implementation Decisions` 的小节号）、`## Read first`（本 ticket 小节引用的出处，无则 `None`）、`## Seam`（从 spec `## Testing Decisions` 抄的 test layer 与目录）、`## Owns`（本 ticket 可写的仓库相对路径，一行一条，`## Seam` 的测试目录或测试文件必含，新建的标 `(new)`，禁绝对路径、`..`、裸 `**`）。blocking edge 只记在 tracker 的原生 blocking link 上，模板里没有对应的一节。`## Owns` 排在 `## Seam` 之后，因为两节是一对：`## Seam` 说在哪验，`## Owns` 说在哪写。粒度跟着分工走——独占目录写 directory glob，几张 ticket 分工同一目录写到文件级；硬判据只有「同一 frontier 两张不得相交」，切不开的共用文件加一条 `## Blocked by`。`## Read first` 另写明凡记录已拍板结论的条目（prototype 的 chosen artifact、Claude Design 的 handoff package、ADR 标题行之后那一段决定、decision ticket 的 resolution）是 baseline——contract 不是参考，逐行标明；精确值与逐字文案从 handoff package 的 `README.md` 抄。`## What to build` 要求分点写：人在网页上扫标题找那一件，agent 没有写 ticket 那一方的上下文照着做，两边都读不动一大段连排文字。`## Acceptance criteria` 是四行形态，两条示例都带命令，并写明判断归 code review、只有人看得了的另开一张 ticket；第二条示例带可选的第五行 `TIMEOUT: <seconds>`，是 `verify-ticket.py` 读的每条 `CHECK:` 的时限，worker 自跑与最终全量运行读同一个数，只能抬高不能压低——不写在 ticket 上，慢检查就会在最终全量运行时超时变成失败。`implement` 靠 `## Read first`、`## Seam`、`## Owns` 三个节名读 ticket，改名要同步改 `implement`。上游改模板 → 收上游结构，这几节接回去 |
| `<issue-template>` 的 `## Owns` 一节，既有三条约束之后的新段 | 我们加的。见 `## 删除或改名的票收进引用处`。 |
| 第 4 步 `CHECK:` 自带前置状态那一段之后的「同批次后面的 ticket」一段 | 我们加的。见 `## 一条判据不被同批次后面的 ticket 弄红`。 |
| 第 5 步 `### 5. Give each ticket its blocking edges` 里 `(new)` 路径的三步推导与其后的两支、`<issue-template>` `## Owns` 第一段里「必须改才能让它投入使用的文件也归本票」那一句、第 8 步 `## Owns` 那条末尾的一句 | 我们加的一组。见 `## 让新文件跑起来的那几处改动归本票`。 |
| `<issue-template>` 没有 `## Worker` 节 | 我们删的：这张 ticket 交给哪一档 worker，答案只有一处，就是票上的 `junior-worker` / `senior-worker` label——`dispatch.sh` 读 label，别的一概不读。票身上再写一节等于同一件事记两份账，两份账要对就得有第三样东西去核，`--lint` 里那条核对两份账的 WARN 也一并退场。怎么选那一档写在第 6 步 quiz 那一行，模型写在本机 `MMW_HOME/models.json`，那是模型唯一写下来的地方。上游加了同类的一节 → 不收：落点是 label |
| `<issue-template>` 的 `## Seam` 段 | 我们改的：要抄的那个测试叫 `the precedent to copy`，与第 4 步的 `the precedent it names`、spec 的 `## Testing Decisions` 用同一个词——同一样东西两个名字，读的人要自己认出它们是一件事。这一段不写「只有人验得了时点名设备与步骤」：只有人判得了的事已经是另一张 ticket，这张上不会只剩人工验证。上游改这段 → 收上游，`precedent` 一词保留，那一句仍然不写 |
| `**Work only a person can do**` 那一段 | 挪到 `references/person-ticket.md`，`SKILL.md` 第 4 问的第 3、4 支和 `triage/SKILL.md` 都指向它；只有 criterion 停在问题 3 或 4 的那次 run 才读到这段。我们改的：分两类，且要求 ticket 上用一个词点明是哪一类——`reaction`（被判的性质就是一个人的反应，人是量具，消不掉）与 `reach`（机器判得了但够不着，补上一个测试账号、一台备用机、一个 runner、一个还没人 Owns 的到达机制、或 consuming repository 一条不给测试出口的可测试性规则就能消掉——后两样是第 4 问「It is.」一支缺名字或缺 Owns 时的落点，与缺设备、缺凭证同形）。上游给的四个理由（判断、只有人有的访问权、设计决定、手工测试）在这条 landing pipeline 里是混的：判断大半归了 code review，设计决定是 the five questions 的第 5 问，两样都不该进这个盒子。同时列明 the five things：`## Parent`、是哪一类、看什么（一个点开就能看的链接，不是一条要跑的命令）、什么算对、`## Blocked by`。理由：这是全 landing pipeline 唯一一个不向机器交代理由的出口，一行散文防不住，写不出自己是哪一类就说明它归错了档；而它的读者是早上、在手机上、没有上下文的人，缺「什么算对」他只能回答「我说不上来」。上游改这一段 → 收上游措辞，两类与 the five things 保留 |
| 模板之后的路径规则那一句 | 我们改的：收窄成 `no implementation file paths`，并明写两个例外——`## Seam` 的测试目录或测试文件，`## Owns` 的路径。理由：禁令反对的是散在描述里、一改名就错的实现路径；`## Owns` 写的不是「代码在哪」而是「你可以写哪」，文件在它里面怎么挪都不影响真值，而且它过期是可见失效（glob 匹配不到任何现存路径），不是静默误导。上游改这一句 → 收上游措辞，两个例外保留 |
| 第 7 步的 Local files 分支与 `<local-ticket-template>` | 删掉，publish 的地方只有 issue tracker；`description`、read-back 那一步与模板后那一句都不提本地形态，`description` 写的是每张 ticket 一个 issue、带 blocking link。理由：本仓的 ticket 必须有 issue 号才走得动——`dispatch.sh` 按 `issue-<n>` 开 branch、`verify-ticket.py <n>` 按 ticket number 跑 acceptance criteria 并把结论评论回去、`status.py` 从 spec 的 `sub_issues` 取当晚的 frontier，三样都只认 issue tracker 上的号；本地文件形态出的 ticket 一步都走不了，留着只是给写 ticket 的一方一个走不通的选项，而且它那套粗体行加 `**Status:**` 与 `<issue-template>` 的固定节名不同形，`--lint` 也只认 `<issue-template>` 那一种。上游再改那一段 → 不收 |
| 第 3 步 contract ticket 段与 acceptance ticket 段、第 4 步界面判据与「A layer with no precedent yet」、第 5 步 prefactor 里 contract ticket 那一句、模板 `## Read first` 的界面部分 | 我们加的。见 `## 界面 ticket 的规则 cutting-interface-tickets.md`。 |
| `<vertical-slice-rules>` | 删掉 `Each slice is sized to fit in a single fresh context window` 这一条。我们的 spec 通常很大，这条把 vertical slice 推得过细；粒度由 `### 6. Quiz the user` 那一步问 user 来定。上游改这条措辞 → 仍然删。上游把它换成别的尺寸规则 → 也删，保持 vertical slice 尺寸不设机械上限。其余段落我们没改，全取上游 |
| 开头「issue tracker 与 triage label 词汇没给你就去装」那一句、第 4 步两处「回到 to-spec」、第 7 步 publish 那一句里「那个 tracker 是谁配置的」 | host 中立：四处点技能名的地方一律写成散文形式，开头那句与 `triage`、`wayfinder` 同一个说法。共同理由与三种替换写法见 [README.md](README.md#host-中立) |
| 第 4 问「It is.」一支删掉「a screen composed against fixtures instead of the live client」那个例子；第 8 步 `## Owns` 一条加「跨仓库的工具改动不开票、当场改」；界面票 `## Read first` 由行的 `source` 推导（baseline 类出处按文档去重，spec 小节与 story 经 Parent 到达） | 我们改的，来自 mmw #115，#216 第 8 节未推翻的部分。fixtures 例子与「这正是本流水线要抓的失败」直接矛盾，删；推导 Read first 在 `cutting-interface-tickets.md`，含 `scenes.json`，target trees 一条已删。上游改 `SKILL.md` 这几处 → 收上游对第 4 问与 Owns 的措辞；界面 Read first 仍在新文件且不含 target trees |
| 开头两门表与 `references/ambiguity-scan.md` | 我们加的。见 `## 找漏 reference`。 |
| 第 6 步开头的找漏 subagent 与 `Choices` 行 | 我们加的：quiz 前列切分之前跑一轮找漏。理由：#415 第 14 节。上游改 quiz 那一步 → 收上游的问题清单，找漏那段与 `Choices` 的并入保留 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

## 找漏 reference `ambiguity-scan.md`

`references/ambiguity-scan.md` 是新文件。理由：#415 第 14 节。姿态一句取自 Factory Missions 抓包提示词（assertions 换成 decisions）。扫描分类清单照抄 spec-kit `templates/commands/clarify.md`（commit `d848fb4e`）第 73–123 行，每类标 Clear / Partial / Missing。约束照抄第 134、136、137、138 行，其中「会改变什么」收窄为「某张票交付什么或它的标准查什么」；最多 5 条（`Maximum of 5`），超出按 Impact × Uncertainty 取前 5。每条一句完整问句、一句 Why it matters、引用 spec 原句、2–5 个互斥选项、`Recommended: Option X — <1–2 句理由>`。只读 spec 与票草稿，不读代码，只跑一轮。没有值得问的原样返回 `No critical ambiguities detected worth formal clarification.`

上游给 to-tickets 加同类找漏步骤 → 收上游对调用句式的措辞，这份 reference 的分类、上限、形状与只读一轮保留。上游把 clarify.md 改了 → 分类清单跟那一版，收窄、上限、形状与只读一轮仍按上一段。

## 删除或改名的票收进引用处

`<issue-template>` 的 `## Owns` 一节，既有三条约束（无绝对路径与 `..`、同一 frontier 两张不重叠、拆不开就加 `## Blocked by`）后面加一段：一张删除或改名文件、脚本、合同字段或判据词的票，用 `grep` 找出每个引用处并收进自己的 `## Owns`。本批次两张票都要改同一文件时，走上一句已有的 `## Blocked by` 边；引用处只是另一张票已拥有的过期指向时，不塞进本票，开一张 `Blocked by` 那张已拥有引用处的票。

理由：#216 那一夜 #230、#231、#232、#241、#242、#243、#249、#250、#251、#252 十张子票全是同一类——某张票删了 `wiring-check.py` 或改了合同格式，别处还指着它，而那些地方不在该票的 `## Owns` 里。

上游改 `## Owns` 一节 → 收上游对既有三条约束的措辞，这一段保留。

## 让新文件跑起来的那几处改动归本票

第 5 步在上游那一句之后加一整块，`<issue-template>` 的 `## Owns` 第一段与第 8 步 read-back 的 `## Owns` 那一条各加一句。三处说的是同一件事：一张票新建的文件，要有另一处既有文件点它的名，它才会被渲染出来、才会被自己的判据看见；那几处既有文件也归这张票的 `## Owns`。

- 第 5 步：对每条标了 `(new)` 的路径做三步推导——找同类里最近的那一个（批次从零起步时，就是本批次另一张票落下的第一个）；对它 `grep` 两次（那个同类还没造出来时，读落它那张票的 `## Owns`）：文件名答出清单/manifest、路由、include 或 import 它的父模板、导出它的 index、给它摆场景的 story adapter；它对外声明的那一个标识（根 class 名、导出的符号、路由路径）答出样式表、打包入口或表——这一处**光按文件名 grep 到不了**，`agentflow` 那批里 `work_monitor.css` 与局部模板之间只有 class 名（`pt-rail`、`wm-day-rule`）这一条联系，而它正是冲突文件之一。把答出来的每个文件收进本票 `## Owns`。随后按重叠程度分两支：两张重叠走 `## Owns` 已有的 `## Blocked by` 边；三张及以上共用同一组文件，改切一张 prefactor ticket 排在它们前面，由它一次落下全部登记、路由、include 与导出（各指一个占位），并把「只是一串互不相干条目」的那种共用文件（样式表、登记表、打包入口）拆成一票一份、由共用的那份 include 一次，其余票只被它一张阻塞、于是能并行。「spec 有 screen contract 时这张票就是 contract ticket」那一句在 `references/cutting-interface-tickets.md`：它登记合同里每个设计页的场景与路由，而不只是当先例的那一页。共用文件本身是一整段逻辑（几张票各往同一个路由模块加 handler）时既不预落也不拆——写进去的内容就是各票自己的活——那几张票仍然串行。这一条是为了不误伤 #753 那种形状：它与 #745、#746 共用 `src/gateway/routes/org_work_monitor.py`，走的就是串行，而且它本来就把这个文件写进了自己的 `## Owns` 并连了 `## Blocked by` 边。
- `<issue-template>` 的 `## Owns`：明写「本票必须改才能让它新建的东西投入使用的文件也写在这里，哪怕是别的票建的」。不另开一节记「我要改但不拥有的文件」——同一件事记两份账，而 `## Owns` 本来就是「你可以写哪」不是「你的代码在哪」。
- 第 8 步 read-back 的 `## Owns` 那一条：末尾加一句，每条 `(new)` 路径在同一张票上要有那个让它投入使用的既有文件。没有这一句，推导被跳过时 read-back 查不出来——票与票的 `## Owns` 恰恰因为漏了那几个文件而不重叠，重叠那条检查照样过。

理由来自 mmw #408 的对照实验：`agentflow-hq/agentflow` 一夜同层并发四张界面票（#748 #750 #751 #752），四张的 `## Owns` 互不重叠、各拥有自己的一个局部模板加自己的测试，但真正冲突的四个文件（`.mmw/stories/adapter.py`、`src/gateway/routes/org_work_monitor.py`、`src/gateway/static/org/work_monitor.css`、`src/gateway/templates/org/work_monitor.html`）一张票的 `## Owns` 里都没有——要让一个新局部模板渲染出来并被 story 判官判到，四处都得加东西。第一张合进去，其余三张 `ticket.bounced`（#751 那条事件列的就是上面四个文件）。后来把四张用 blocked-by 串成直线、一次派一张，代码一行没改全部一次过。所以病根不是 `## Owns` 划重了，而是划得不足以让票做完自己的事；补法是让 `## Owns` 写全，`## Owns` 已有的不重叠规则随即自己生效。

取名不用「scaffolding ticket」：`scaffolding` 在 `docs/contexts/ui-acceptance/CONTEXT.md` 的 `prototype` 条目里已经指原型的挂载点与软链，是 `prototype/UI.md` 第 6 步要拆掉的东西。用 `prefactor`，因为它是本技能第 2 步与 `<vertical-slice-rules>` 已有的词（`Any prefactoring should be done first`），而 `contract ticket` 条目的 `_Avoid_` 明写 `prefactor ticket (for this one)`——那一行正说明 prefactor ticket 是另一样合法的东西。

上游改第 5 步、`## Owns` 一节或 read-back → 收上游措辞，三步推导、两支、`## Owns` 那一句与 read-back 那一句保留；第 5 步永远排在 acceptance criterion 之后（推导要先知道每条判据得看见什么），在 quiz 之前（prefactor ticket 是批次里多出来的一张，得让 user 在 quiz 上看见）。

## 界面 ticket 的规则 `cutting-interface-tickets.md`

`references/cutting-interface-tickets.md` 是新文件。理由：#447 第 1 节、方案 K5。

| 段落 | 我们的意图 |
| --- | --- |
| `SKILL.md` 第 3 步 contract ticket 段与 acceptance ticket 段、第 4 步「A layer with no precedent yet」与两条 story criterion、第 5 步 prefactor 里 contract ticket 那一句、模板 `## Read first` 的界面部分、第 8 步 `built_by` 一句 | 前几段移进新文件。`SKILL.md` 两处指向它：第 3 步一行，模板 `## Read first` 一行（`dispatch` 的 `night.md` 关票时只读模板）。规则不写回 `SKILL.md`。`built_by` 删除（合同里没有这个键），到达机制仍须在某张 ticket 的 **Owns** 里。上游把规则写回 `SKILL.md` → 不收进正文，接到新文件 |
| `references/cutting-interface-tickets.md` | 新文件，装有 screen contract 时怎么切界面 ticket。上游给 to-tickets 加同类 reference → 收上游对调用句式的措辞，这份文件的五种 ticket、共用 helper、reaction 与行变更的规则保留 |
| 五种 ticket | **design-system ticket**（handoff package 带 `_ds/<folder>/` 下的 design system、且其变量或部件样式表产品代码里还没有时就切；否则各界面票按设计页自己写样式；排在 contract ticket 之前并挡住它，没有 contract ticket 的批次改挡全部 component page ticket 与 app page ticket，criterion 不依赖 `.mmw/`）；**contract ticket**（已有产品只补 `target_config.py --check` 报缺的，没有要补的就不切；新产品落地整套 `.mmw/`，挡住 design-system ticket 以外的所有 ticket）；**interface ticket**（按 `Component · ` 页，一条 element parity 的 story criterion，每个 `calls` 不为 `none` 或 `next` 不是 `stay` 的行一条 boundary criterion）；**app page ticket**（认领 `App · ` 页，一条 story criterion，每条 cross-component row 一条 boundary criterion，被引用的 `Component · ` 页的 interface ticket 挡住它）；**acceptance ticket**（Testing Decisions 的关键流程每条一张，criterion 带 break，默认取该流程合同行里最后一个写操作，红了 `HANDOFF REQUIRED`）。每种 criterion 的形状只点名 `ui-acceptance` 的 `references/story-parity.md`、`boundary-check.md`、`journey.md` 各自的 **The criterion** 一节。上游改其中一种 → 收上游措辞接到新文件，五种与「点名、不另写命令形状」保留 |
| 共用 journey helper | 一批里有两张以上 journey ticket 需要同样的产品访问时，由 contract ticket（有的话）或这批第一张 journey ticket 在 `.mmw/harness/` 下建一个共用 helper 并列进自己的 **Owns**；之后的 journey ticket import 它，**Owns** 除 `.mmw/journeys/<flow>/` 外包括向这个 helper 添加、不包括产品代码。理由：#443，#447 第 5 节。写权限只由 **Owns** 说，**Seam** 不承担它（见下面 `## 界面 ticket 接回模板的 Seam、Owns 与五问`）。上游加同类共用 helper → 收上游措辞，落点 `.mmw/harness/` 与 Owns 规则保留 |

## 合同票的 Read first 点名 story 页面那一节

这句话在 `references/cutting-interface-tickets.md` 的 contract ticket 段：它的
**Read first** 点名 `ui-acceptance` 技能 `references/story-parity.md` 的
**The story page the product serves**，以及 `references/journey.md` 与 `references/product-answers.md`。

理由是那一节的内容原先散在三份写给别人的文件里——`[data-story-root]` 在 `ui-parity.md`
的 `Two sides`（收信人是写判据的人和读 `DIFF` 的人）与 `code-review` 的
`references/spec-reviewer.md`（reviewer 读的），地址形状在 `targets/README.md` 第 4 条，
adapter 读 `scenes.json` 的 `data` 在 `to-spec` 一句。这一段里的 `ui-parity.md` 与
`targets/README.md` 两个名字**不改**，尽管两份文件都已改名（`story-parity.md`、
`product-answers.md`）：这一句描述的是集中**之前**东西散在哪儿，那时候它们真叫这两个名字，
换成今天的名字这条理由本身就变成假的。后来 `rg` 老名字的人最容易在这里「顺手修好」，别修。造 story 页面的那个 worker 一份都不会
打开，`target_config.py --check` 给 `stories` 字段的整句说明也只有「brings up the
story page service and prints its origin」。它只能先造错，再被
`no visible [data-story-root] at <url>` 退回来。

把要求集中到 `story-parity.md` 之后，还要有人把 worker 带过去，而带它的只能是票的
**Read first**——这一句就是那个动作。同一句一并点名 `references/journey.md`：合同票也交付
旅程骨架，而每条旅程会在产品停掉之后被再跑一遍，什么都不断言的脚本会被报出来而不是放过
（mmw #297 决策 7）。#447 第 2 节再点名 `references/product-answers.md`。上游改写合同票那一段 → 收上游措辞接到 `cutting-interface-tickets.md`，点名这三节保留。

## 一条判据不被同批次后面的 ticket 弄红

第 4 步 `CHECK:` 自带前置状态那一段之后加一段：整批 ticket 落在同一条 base branch 上，收尾那一趟在那里把全批判据重跑一遍，所以一条点名了后面的 ticket 可能改动之物的判据，是由那张 ticket 的工作在判，不是由它自己的。两种形态——全仓库扫一遍（查某个名字是不是已经没了、在整棵树上数一个数），后面任何一张 ticket 都能在 note、文档或注释里把它写回来；以及按名字点名某个测试用例、函数或符号，后面的 ticket 可能改名。这样的判据放到这一批的最后一张 ticket 上，或者让那个名字只有一个主人：装着它的文件在整批里只落在一张 ticket 的 `## Owns` 里，而不只是同一 frontier 内不重叠。

理由：连着两晚同一类。spec #445 的 #472 AC4 是全仓库查旧名（`git grep -l -e 'claude-design-blocks' … | wc -l`），同批次后面的 ticket 又写了旧名，收尾 reverify 把已落地的 #472 判红；spec #446 的 #491 AC5 点名测试用例 `test_finds_ui_acceptance_without_tools`，同批次后面的 #493 把它改名为 `test_the_lint_runs_without_tools`，判据选不中任何用例，#491 被重开。两次都由 main agent 在收尾那一趟手工修因、手工重跑、手工关票。

上游给第 4 步加同类的批次内相互影响的规则 → 收上游措辞，两种形态与「最后一张 ticket 或唯一 Owns」这个二选一保留。

## 一个概念一个名字：component page ticket、Critical flows、pull

三处措辞，都是同一个毛病——一个概念两个名字，下游 agent 认不出是同一样东西。

`references/cutting-interface-tickets.md` 的 `## interface ticket` 一节改名 **`## component page ticket`**，与已有的 **app page ticket** 对称。理由：`interface ticket` 同时是广义和窄义。广义是 `verify-ticket.py --lint` 打印的那个——`## Read first` 带 `screen-contract.yaml rows:` 行的任何一张票，app page 与 acceptance 都算；窄义只认领 `Component · ` 页。切票的 agent 读 `linting.md` 会以为 app page ticket 不算 interface ticket，于是不写 `rows:` 行，发布时 `--lint` 报 ERROR。窄义改名后，`interface ticket` 只剩脚本打印的那一个意思，文件开头加一句写明这层包含关系。凡与 **app page ticket** 并列的地方（app page 的阻塞句、acceptance 的阻塞句、reaction 的阻塞句）都改成窄名；`docs/contexts/tickets/CONTEXT.md` 两条词条同步。

acceptance ticket 那一段原来写 `Testing Decisions names the key flows`。spec 里的小节叫 **Critical flows**（关键流程），`verify-ticket.py` 的 `CRITICAL_FLOWS_RE` 也只认这两种拼法；写成第三个名字，切票的 agent 在 spec 里搜不到这一节，一张 acceptance ticket 都不会切，而且下游没有任何检查发现它们缺席。同句的 `the login gate` 统一为 `sign-in`，与 `to-spec` 和两份 `CONTEXT.md` 一致。

`SKILL.md` 模板 `## Read first` 的 `a handoff package downloaded from Claude Design` 改成 `pulled into the repository`。ADR 0029 定下 pull 是这个包的唯一写入者；`downloaded` 会让 worker 去找 MCP 工具或 `edit-pages.md` 明令禁用的 "Handoff to Claude Code" 导出，而不是读 `## Read first` 已经点名的那个已提交目录。同一句里的 `journey skeleton` 改成 `first journey script, as the precedent`，因为 `skeleton` 在合同侧已经是 `extract_skeleton.py` 产出的控件清单。

上游改这三处 → 收上游措辞，`component page ticket`、`Critical flows` / `sign-in`、`pulled` 三个名字保留。

acceptance ticket 的阻塞句原来只写 **component page ticket** 与 **app page ticket**。journey 要启动真实产品、什么都不 mock，而这两种票交付的 boundary test 恰恰是把产品对外调用那一层换掉的；五种界面票没有一种负责建后端接口。于是批次里最贵的那一张（`senior-worker`、最后一张、在合并后的基线上跑）会在后端还不存在时被派出去，journey 过不了第一个写操作，变成 `HANDOFF REQUIRED` 等早上人工处理。现在改成从流程的行推导：它走过的页面的两种票，加上建出这些行 `calls` 所点名接口的那些票。上游改这一句 → 收上游措辞，「阻塞边从行推导、不按 ticket 种类枚举」这一点保留。

## 界面 ticket 接回模板的 Seam、Owns 与五问

`references/cutting-interface-tickets.md` 里五种界面 ticket 原先只复用了被脚本读取的机制（`## Read first` 的 `rows:` 行、criterion 形状），而只活在散文里的模板小节与五问被绕过了。四处接回，理由：#539。

| 段落 | 我们的意图 |
| --- | --- |
| 新增 `## Seam and Owns on these tickets` 一节 | 模板要求每张 agent ticket 的 **Seam** 非空（第 8 步），`implement` 要求 worker 动手前说出 seam，`tdd` 不许在未确认的 seam 上写测试；而五种界面票原先一处都没规定 **Seam** 填什么，worker 每夜现推一次。这一节按 criterion 形状给出观察层与「是什么把产品摆进那个状态」：story criterion 看无后端的 story 页、由 story adapter 读 scene data 摆进去；boundary criterion 看被替换的 outbound call module、由 interaction helper 按 `data-ui` id 摆进去；journey criterion 看经 `.mmw/target.json` 的 `start` 起来的真实产品；design-system 与 harness-guard 判据看仓库文件树。同一节说 **Owns**：design page 是 **Read first** 下的基线，永远不进 **Owns**，经合同 `pages.<page>.component` 译成产品目录。上游改模板的 **Seam** / **Owns** 定义 → 收上游措辞，这一节的「按 criterion 形状给观察层」与「design page 不进 Owns」保留 |
| acceptance ticket 的 **Owns** 句删去「**Seam** may forbid edits to product code」 | 那一句把 **Seam** 用成写权限，而写权限是模板 **Owns** 的职责（「Everything outside these paths is read-only」）。改成「product code is not in it」，由 **Owns** 自己说。上游再加让 **Seam** 管写权限的句子 → 不收 |
| component page ticket 与 app page ticket 的开头 | 原先写「Owns by design page」「Owns an `App · ` page」，照字面读是把一个基线路径填进唯一授予写权限的小节，而 `--lint` 只查 **Owns** 条目是不是仓库相对路径，拦不住。改成「Cut by / Takes」说认领哪些页，另起一句写 **Owns**：component page ticket 是合同为各页声明的 `component` 目录加它新增的测试文件；app page ticket 是把各组件拼成整页的那个 story 页加测试文件（`App · ` 页在合同里不声明 `component`）。design-system ticket 与 contract ticket 各补一句 **Owns**。上游改这几句 → 收上游措辞，「design page 说认领哪些行、不说能写哪里」保留 |
| 形状清单后加一句五问；contract ticket 的交付清单后加一段五问 | 原先只有 design-system ticket 一处走了五问。形状清单后一句：三种 criterion 形状都是第一问。contract ticket 是全批交付物里没有一项是产品行为的那一张，最容易把判断塞进 `## Acceptance criteria`；这一段写明第一问只到 smoke journey 与静态守卫，story service、第一个 story adapter、interaction helper、element parity 先例与 break switch 都是先例、没有自己的判据，由照抄它的第一张 component page ticket / acceptance ticket 用命令首次判定，建得好不好是第二问。上游改 contract ticket 的交付段 → 收上游措辞，这一段的五问归类保留 |
| design-system ticket 声明为纵切的第二个例外 | 它只落一层（样式）、没有自己的行为，对着 `SKILL.md` 第 3 步「vertical, NOT a horizontal slice」。照第 3 步 wide refactor 那一句的句式声明例外并附理由。上游改 wide refactor 那一句 → 收上游措辞，这一处例外保留 |
| harness-guard 判据从 contract ticket 移到这一批最后一张 ticket | `harness-guard.py .` 扫整棵树，而第 4 步「A criterion is also exposed to the rest of its own batch」把全仓库扫一遍的判据放到批次最后一张。留在 contract ticket 上，后面任一张票漏一个验收名字，收尾 reverify 就把批次第一张票判红、重开进 `needs-triage`，而能修它的 worker 已经走了。放到最后一张：有 acceptance ticket 就是最后一张 acceptance ticket，否则是最后一张 app page / component page ticket，并由它被本批其余每张 agent ticket 阻塞来保证它真是最后一张。contract ticket 仍交付 harness guard 本身。`ui-acceptance` 的 `references/harness-guard.md` 与 `docs/contexts/ui-acceptance/CONTEXT.md` 同步改掉「contract ticket carries this criterion」。上游改第 4 步那条规则 → 收上游措辞，这一处归属随之保留 |
| reaction ticket 收窄 | 原先覆盖「没带 `data-ui` id 的装饰、整体观感」，与 `code-review` 试点 UI axis 的 `undecorated` / `overall-look` 两类同词；五问停在第一个 yes，第二问（机器能到达的判断 → 代码审查）先于第三问（人的感受）。现在 reaction ticket 只管 story 渲染看不见的：在运行中的真实产品上用起来的感受、整个界面读起来像不像一个产品；story 渲染看得见的归 UI axis。`code-review` 的 `references/ui-reviewer.md` **What is not yours** 加对称的一句。UI axis 试点若结束被去掉，story 渲染看得见的那一类外观要重新找归属（回到这一行，或回到 reaction ticket），别让它静默失去主人。上游改 reaction ticket 那一段 → 收上游措辞，这条分界保留 |

## contract ticket 已有产品一支的条件

| 段落 | 我们的意图 |
| --- | --- |
| `references/cutting-interface-tickets.md` contract ticket 段第一句 | 原先写「An existing product whose `.mmw/` is already complete」，与后一句「A new product」组成两支；`.mmw/` 只完成了一部分的已有产品两支都对不上，离它最近的是「整套落地」，正是本段要停掉的重搭。现在只写「An existing product」，由 `target_config.py --check` 报缺什么就补什么，没缺的就不切。理由：#540。上游改这一句 → 收上游措辞，「已有产品只补报缺的、不按 `.mmw/` 完整与否分支」保留 |

## contract ticket 的「缺什么」不只看 `target_config.py --check`

`references/cutting-interface-tickets.md` contract ticket 段：`--check` 只看每项答案在不在，看不出它是为哪一代交接包建的。读旧交接包或旧 scene 形状的 story service 与 story adapter、不按 `data-ui` id 找控件的 interaction helper、没有 break switch 的 `start`，都算缺，由 spec 的 **How a test arrives at a state** 写明。理由：任务板试点 #541，`--check` 报「complete」而这四样都是上一代的，照原文会一张 contract ticket 都不切。design-system ticket 的切票条件见 `## 走真实流程补的四处缺口`。上游改这一段 → 收上游措辞，这一条保留。

## 任务板试点 #541 出 #555 那批票时补的规则

理由都来自同一次真实出票：任务板试点 #541 为 spec #555 切九张票，一路撞到下面这些文字与脚本对不上的地方。

| 段落 | 我们的意图 |
| --- | --- |
| `SKILL.md` 第 7 步开头「Lint the batch before anything is live」一段、第 8 步 `--lint` 那一条 | 我们加的：发布前先对本地草稿跑 `verify-ticket` 技能的 `--lint --drafts <dir>`（草稿形状：`TITLE:`、`LABELS:`、`BLOCKED BY:` 头，一行 `---`，然后是正文；草稿名代替还没有的 issue 号），ERROR 在还没上线时改掉；发布后第 8 步再对 spec 号跑一遍，因为只有 tracker 才有的东西（sub-issue 关系、tracker 上的 label 与 blocking link）草稿跑不到，`--drafts` 自己在输出末尾列出这几项。理由：`--lint` 原先只读 tracker，#555 那一批只能先发布再修，run 为此自己写了一个包装脚本把草稿塞进去。上游改第 7、8 步 → 收上游措辞，发布前一次、发布后一次这两遍保留 |
| `SKILL.md` 第 5 步末尾「Every branch above keeps one rule」一段 | 我们加的：一条规则，两张能同时跑的票（谁也不阻塞谁，直接或经一条链）不写同一个文件。共用文件（例如共用样式表）归一张票，其余需要它的票被它阻塞；worker 那一侧由 `verify-ticket` 的 `references/sub-issues.md` 第 5 问与 `implement` 的 Owns 外文件一条执行：能与本票同时跑的票拥有的文件不改，开 `contract` child。理由：第 5 问原先允许为过 criterion 改任何 Owns 外文件，与本步「同一 frontier 的 Owns 不重叠」相冲，两张并行票改同一个共用样式表正是 Owns 不重叠要防的 merge conflict。另一个选项（凡 Owns 外改动一律记成 `contract` child）没选：被阻塞的票在 owner 落地之后改那个文件不与谁并发，`--touched` 本来就为这种情况通知 owner。上游改第 5 步 → 收上游措辞，这一条规则与它在 `sub-issues.md`、`implement` 两处的对应保留 |
| `SKILL.md` 第 6 步「When the host offers no such restriction」一段 | 我们加的：host 不提供按次限制 subagent 权限时，prompt 加第二句「只许读」，并由出票一方在 subagent 前后各跑一次 `git status --porcelain` 比对，有差异就是 scan 写了东西，先撤回再往下走。理由：#555 那次的 host 没有按次限制工具的开关，原文只写了「能限制就限制」，没说不能时怎么办。上游改第 6 步 → 收上游措辞，这一段保留 |
| `<issue-template>` 的 `## Parent` 一节「When a contract row this ticket owns cites a section of an earlier spec」 | 我们加的：合同行的 `source` 引了更早一份 spec 的小节时，那份 spec 与小节写在本票 parent spec 之后、同样的措辞，永远不写在最前（`#535, Implementation Decisions sections 5 and 7; #318 Implementation Decisions section 4`）。理由：`verify-ticket.py` 的 `parent_spec` 把 `## Parent` 里第一个 issue 号读成本票的 spec（tracker 没有 parent link 时、`--drafts` 时、查另一批的 blocker 时都靠它），而 `source_findings` 又要求 `## Parent` 点名那份更早的 spec；模板原先只说写 parent issue，两边对不上。`--lint` 在知道本票 spec 时把第一个号不是它报成 `[parent-order]` ERROR。上游改模板 `## Parent` → 收上游措辞，「更早的 spec 写在后面」保留 |
| `SKILL.md` 第 8 步 `ready-for-human` 的「What to look at」一条、`references/person-ticket.md` 的 **What to look at** 之下一段 | 我们加的：消费自己 landing pipeline 的仓库（其 `AGENTS.md` 有 **Self-hosting boundary**）里，机器上常驻的是冻结的已安装版本，不是这一批在改的版本，链接给出去看到的是旧产品；那里票上给一条命令，从本票 worktree（切在 blocker 落地的 base branch 上）经 `ui-acceptance` 的 lease 用测试数据起产品、打开页面并打印地址，链接就是它打印的地址。理由：#555 的 reaction ticket 要「一个点开就能看的链接」，而任务板这个仓库本身就是自托管的。上游改 person-ticket 那一段 → 收上游措辞，这一段保留 |
| `references/cutting-interface-tickets.md` contract ticket 段：静态守卫的判据挪到这一批最后一张票 | 我们改的：静态守卫（产品模块不读 scene data、一次渲染里 `mount` 唯一、`data-ui` id 只在列表重复部分重复）仍由 contract ticket 交付，判据与 harness guard 一样放到最后一张票。理由：它们扫整棵树，后面每张页面票都会加组件，留在 contract ticket 上要等最后一张页面票落地才可能绿，收尾 reverify 会把批次第一张票判红重开；`SKILL.md` 第 4 步本来就把全树扫描放最后一张，这一段原先只挪了 harness guard。`ui-acceptance` 的 `references/product-answers.md` 同步写明判据的位置。上游改这一段 → 收上游措辞，静态守卫与 harness guard 同放最后一张保留 |
| `references/cutting-interface-tickets.md` contract ticket 段：element parity precedent 那一项与其后一段 | 我们加的：contract ticket 把设计页的 `data-ui` id 写进当先例的那个已有组件、根元素加 `[data-story-root]`、为那一页建第一个 story adapter，并把这些组件文件列进自己的 **Owns**；拿那一页的 component page ticket 被它阻塞，带着那一页的 story criterion 与 boundary criteria，是第一批判这些 id 与 adapter 的命令，同一组件目录也在它的 **Owns** 里，由 **Blocked by** 排先后。理由：#555 出票时原文没说 contract ticket 写不写这些 id、由谁的判据先判，run 自己定了这个分法。上游改这一段 → 收上游措辞，这个分法保留 |
| `references/cutting-interface-tickets.md` component page ticket 段：`next` 是另一页 scene 的行 | 我们加的：组件单独渲染时另一页不在场，这种行的 boundary test 照常断言 `calls`、`shows`、`on_failure`，`next` 一列断言本组件交出去的东西（发出的事件、路由变化或状态，带着目标 scene 需要的值，例如要打开的票号）；另一页进入那个 scene 由合同里重复这一行为的 `App · ` cross-component row、在拥有它的 app page ticket 上断言一次。理由：#555 的 `topbar.needs-you-jump` → `Component · 详情.ticket-returned`，原文没说组件页票的测试该断言到哪。上游改这一段 → 收上游措辞，这条分界保留 |

## 走真实流程补的四处缺口

理由都来自同一件事：按真实工作流程（从零做新产品、从已有产品建 design system 再重做界面）逐步走一遍 `references/cutting-interface-tickets.md`，下面四处的文字在其中一种情形下读不通。

| 段落 | 我们的意图 |
| --- | --- |
| `## contract ticket` 交付清单的 element parity precedent 一项，与其后「The element parity precedent is written here」一段末尾 | 我们加的：新产品还没有任何组件时，「one existing component made comparable」无从做起；先例是第一张 **component page ticket** 建出的那个组件。contract ticket 这时交付那张票要用的 story service、story adapter 的形状与 interaction helper，**Owns** 不列组件文件；那张票的 story criterion 是第一条判它们的命令，与「先例由照抄它的票上的命令首次判定」一致。上游改这一段 → 收上游措辞，这一支保留 |
| `## design-system ticket` 第一段、**Owns** 一句与判据一句 | 我们改的：design system 只装外观——变量（颜色、字号阶、间距、圆角、阴影）、字体、以类名加样式表表达的可复用部件，没有组件源码、没有打包产物（`design-pages` 技能 `references/design-system.md`）。所以这张票从交接包的 `_ds/<folder>/` 抄变量、字体与部件样式表进产品，保留类名；判据是一条 shell 命令，证明这些变量与样式表在产品代码里存在。切票条件由「只有新产品、且 design system 不是从产品自己的样式表建的」改为「交接包带的 design system 有产品代码里还没有的变量或部件样式表就切」：从已有产品代码建的 design system 会把不一致的值合并成一套（每处合并记在它 `readme.md` 的 `Unifications` 表），抄回去会改变产品，原条件把这种情形判成「什么也不变」而不切。排在 contract ticket 之前并挡住它的逻辑不变；已有产品没有 contract ticket 时，改挡全部 component page ticket 与 app page ticket。`docs/contexts/tickets/CONTEXT.md` 的 **design-system ticket** 条目仍是旧说法，需同步。上游改这一段 → 收上游措辞，外观三样、切票条件与阻塞关系保留 |
| `## acceptance ticket` 第一句 | 我们改的：不切 acceptance ticket 的条件由「`.mmw/target.json` cannot start the whole product」改为「产品永远不能整体启动（一个库、一个没有运行中产品的组件）」；`.mmw/target.json` 还不存在的产品照切，它的 contract ticket 落地 `start`。理由：新产品出票时还没有 `.mmw/target.json`，照字面读一张 acceptance ticket 都不切。`to-spec` 的 **Critical flows** 用同一条件。上游改这一句 → 收上游措辞，条件保留 |
| `## app page ticket` 的 **Owns** | 我们改的：**Owns** 包括产品自己的 composition module（运行中的产品里把各区域接在一起的那段代码），story 页挂载这个 module、自己不接线，另加测试文件。理由：原文让 story 页自己把组件拼成整页，产品漏接 A 区到 B 区时 story 页照样接上，element parity 与 boundary test 全绿。`ui-acceptance` 的 `references/product-answers.md` 同步写明 `App · ` 页挂载 composition module。上游改这一段 → 收上游措辞，composition module 进 **Owns** 保留 |

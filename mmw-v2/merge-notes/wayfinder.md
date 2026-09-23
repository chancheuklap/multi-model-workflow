# wayfinder

源目录：`mmw-v2/upstream/skills/engineering/wayfinder/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| `### Chart the map` 第 4 步末尾那一句，与新文件 `references/interface-and-remake.md` | 我们加的：第 4 步保留上游原文，末尾只接一句「A destination with an interface, or one that remakes an existing product, adds tickets」并指向 `references/interface-and-remake.md`；界面与重做两支（alignment ticket、design ticket、挑选清单、并存切换那张票）原样放在那份 reference 的两个标题下，文件末尾一行 `Done when`。理由：只有有界面或重做的目的地读这两支，`### Work through the map` 的每次 run 都用不上它们，放在上游的第 4 步里每次都要读；连接写在上游正文之外。上游改第 4 步 → 收上游措辞，末尾那一句接回去 |
| `references/interface-and-remake.md` `## A destination with an interface` 里 alignment ticket 那几句，与 `### Work through the map` 第 6 步「On a map with an alignment ticket…」那一句 | 我们加的：destination 含界面时，地图多一张 **alignment ticket**（grilling 类型，被全部决定票和产出 design package 的票阻塞），用 `write-screen-contract` 技能写出 **screen contract**；地图「清」的判据加上这张票已关。alignment ticket 的正文开头一行（在 `## Question` 之上，模板的标题照旧）也钉死：「用 write-screen-contract 解决：design package 与后端决定逐行对齐，每行 gap 都 aligned 后关票」——它是 `grilling` 类型，而 `## Ticket Types` 对 grilling 写的是 Always 读 `grilling` 与 `domain-modeling`，不钉这一行，接手的 agent 会拿它去跑一轮访谈。正文只写「It is the last ticket to close」与这一行本身，不附这两条理由（「界面与决定在这里并排」、「不钉会被拿去跑访谈」）。理由：design package 与决定各自完整、无处汇合，变色龙的界面因此接了空。上游改 `### Work through the map` 第 6 步 → 收上游措辞，那一句接回去 |
| `references/interface-and-remake.md` `## A destination with an interface` 里的 **design ticket** | 我们加的：有界面的目的地除 alignment ticket 外再开一张 **design ticket**，即「the ticket that produces the design package」：`prototype` 类型、HITL；被 `prototype` decision ticket 与会改变页面状态的 decision ticket 挡住；像点名 `write-screen-contract` 那样点名 `design-pages`；ticket 正文开头一行（在 `## Question` 之上）写「用 design-pages 解决：须在能调用 Claude Design MCP 工具的会话里做；按 design-pages 技能的 references/edit-pages.md 建 Claude Design 项目，用户在 Claude Design 里设计，你说定稿后按 references/pull.md 拉回」（只有宿主接了 Claude Design MCP 工具的会话能建项目和拉回，写在开头，接手的人不必做到一半才发现；设计由用户在 Claude Design 里做；design system 是可选入口，拉回与验收都不读它，所以这一行不点名它，任务板试点 #541）；它的 leaf `README.md` 放整个界面唯一的一份 state list，汇总每张 UI prototype 票的 winner（`prototype` 的 `UI.md` 第 6 步）。理由：一张 map 常把「长什么样」拆成几张 prototype 票，而 `design-pages` 与 pull 只认一份 state list（任务板试点 #541）。「Ticket Types」的 `prototype` 一条不改。挡住关系用原有阻塞链接。 |
| `references/interface-and-remake.md` `## A destination that remakes an existing product` | 我们加的：目的地是重做一个已有产品时，先开「挑选清单」：用户逐项定旧产品里哪些保留，每项写来源路径与进入口；可复用组件与样式是 prototype 的积木，建 design system 时也是它的来源；后端接口是写合同时的后端决定（正文不附「已上线产品通常保留后端、只重做界面」这句旁白）；旧 design package、screen contract、boundary test、journey 一律不保留（正文写成「are never kept」，删除清单用「those four」回指，不把四样再列一遍）；同一张挑选清单还要逐项、带路径列出重做要删掉的旧产物（这四样，以及 `.mmw/target.json` 里指向它们的字段），重做的 effort 名与旧 effort 不同（正文写成指令「Give the remake an effort name other than the old effort's」），新的 screen contract 与 spec 不落在旧路径上（按「重做已有产品」走真实流程时发现：只写「不搬」，旧产物留在原处、新合同写到同一个 `docs/specs/<effort>/` 上，没有人负责删）。已上线、有付费客户的产品再开一张，定新旧界面怎么并存、怎么切换、旧代码何时删。重做时外观取自 winning variant；沿用旧视觉不算重做。 |
| `### The map body` 模板 `## Notes` 那一行末尾的「the effort's directory name under `prototypes/` and `docs/specs/`」 | 我们加的：map 在 Notes 里写下这次工作的目录名（小写 ASCII 单词用 `-` 连），`prototype` 的叶目录 `prototypes/<effort>/`、pull 写的 design package `prototypes/<effort>/claude-design/` 与 screen contract 所在的 `docs/specs/<effort>/` 都用它。理由：map 标题常是中文、带空格和冒号，按标题起目录名每个 session 各起各的（任务板试点 #541）。上游改这行模板 → 收上游措辞，把这一项接回去 |
| `## The map` 第一句、`### Chart the map` 第 3 步里 map 的 label | 我们加的：map 除了 `wayfinder:map` 还打分类 label `mmw:map`（仓库没有就按 `docs/agents/issue-tracker.md` `## Three label sets` 建，颜色与说明只写在那一处）。`wayfinder:map` 是本技能找 map 用的，`mmw:map` 是 MMW 四层分类（map / spec / ticket / child）的顶层，board 靠它读层级、不数嵌套深度（mmw #315 第 6 节）。三套 label 的分工在 `docs/agents/issue-tracker.md` 的 **Three label sets**。正文只写打这两个 label，不写两者各管什么——那是给维护者的理由，跑技能的 agent 在第 3 步照做就够。上游改这两处 → 收上游措辞，`mmw:map` 保留 |
| `### Work through the map` 的第 6 步 | 我们加的整步：frontier 与 Not yet specified 都空时 map 已清，停下来把下一步交给 user——新会话里对这张 map 跑 `to-spec`（传完整引用），再 `to-tickets`；map 不关。上游给这一节加了新的收尾步 → 把我们这一步接在它后面并重编号；上游自己写了 map 走完之后往哪去 → 只留上游那一句，删掉我们这一步（`to-spec` 那侧的分卷判断不依赖这句话）。其余段落我们没改，全取上游 |
| `## Ticket Types` 的 Research、Prototype、Grilling 三条，`### Chart the map` 第 1 步与第 5 步，`### Work through the map` 第 3 步，以及 `## Plan, don't do` 里「issue tracker 没给你」那一句 | host 中立：要词汇的写成读那份技能的 `SKILL.md`（Prototype 与 Grilling 两类票用户在场，开子会话会把用户挡在外面），要另一个上下文的写成问本机 host 要它自己的 general-purpose subagent（Research 票与第 5 步，两处句子自己写着 subagent），指路那一句写成点 `setup-matt-pocock-skills` 技能的名。共同理由见 [README.md](README.md#host-中立)，写法见 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Paths, tokens and host neutrality` 与 `### Hand-offs` |
| frontmatter 的 `description` | 末尾那两句「什么时候用我」（`Use when the way from here to the destination is not visible yet …` 与 `Not for a well-scoped feature …`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；判据取自 `ask-matt/SKILL.md` 讲 wayfinder 那一条（`so save it for exactly that, never a well-scoped feature`）。上游改这一行 → 收上游对前半句的措辞，末尾这两句保留 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

# wayfinder

源目录：`mmw-v2/upstream/skills/engineering/wayfinder/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| `### Chart the map` 第 4 步 alignment ticket 那两句，与 `### Work through the map` 第 6 步「On a map with an alignment ticket…」那一句 | 我们加的：destination 含界面时，地图多一张 **alignment ticket**（grilling 类型，被全部决定票和产出 handoff package 的票阻塞），用 `write-screen-contract` 技能写出 **screen contract**；地图「清」的判据加上这张票已关。alignment ticket 的正文开头一行（在 `## Question` 之上，模板的标题照旧）也钉死：「用 write-screen-contract 解决：交接包与后端决定逐行对齐，每行 gap 都 aligned 后关票」——它是 `grilling` 类型，而 `## Ticket Types` 对 grilling 写的是 Always 读 `grilling` 与 `domain-modeling`，不钉这一行，接手的 agent 会拿它去跑一轮访谈。handoff ticket 与重做票写在同一步后面，所以这两句不在第 4 步末尾。理由：交接包与决定各自完整、无处汇合，变色龙的界面因此接了空。上游改这两步 → 收上游措辞，这两句接回去 |
| `### Chart the map` 第 4 步的 **handoff ticket** | 我们加的：有界面的目的地除 alignment ticket 外再开一张 **handoff ticket**，即「the ticket that produces the handoff package」：`prototype` 类型、HITL；被 `prototype` decision ticket 与会改变页面状态的 decision ticket 挡住；像点名 `write-screen-contract` 那样点名 `design-pages`；ticket 正文开头一行（在 `## Question` 之上）写「用 design-pages 解决：design system 入口先建设计系统，edit pages 入口做设计，你说定稿后走 pull 入口」（三个入口都点名：只点 edit pages 与 pull 时，两边的 session 都不建 design system，写页就在没绑定设计系统的项目里开工）；它的 leaf `README.md` 放整个界面唯一的一份 state list，汇总每张 UI prototype 票的 winner（`prototype` 的 `UI.md` 第 6 步）。理由：一张 map 常把「长什么样」拆成几张 prototype 票，而 `design-pages` 与 pull 只认一份 state list（任务板试点 #541）。「Ticket Types」的 `prototype` 一条不改。挡住关系用原有阻塞链接。上游改第 4 步 → 收上游措辞，这一段接回去 |
| `### Chart the map` 第 4 步重做已有产品的两张 decision ticket | 我们加的：目的地是重做一个已有产品时，先开「挑选清单」：用户逐项定旧产品里哪些保留，每项写来源路径与进入口；可复用组件与样式是 prototype 的积木与 design system 的来源；后端接口是写合同时的后端决定；旧 handoff package、screen contract、boundary test、journey 一律不搬。已上线、有付费客户的产品再开一张，定新旧界面怎么并存、怎么切换、旧代码何时删。重做时 design system 从 winning variant 建；沿用旧视觉不算重做。上游改第 4 步 → 收上游措辞，这一段接回去 |
| `### The map body` 模板 `## Notes` 那一行末尾的「the effort's directory name under `prototypes/`」 | 我们加的：map 在 Notes 里写下这次工作的目录名（小写 ASCII 单词用 `-` 连），`prototype` 的叶目录 `prototypes/<task>/` 与 pull 写的 handoff package `prototypes/<task>/claude-design/` 都用它。理由：map 标题常是中文、带空格和冒号，按标题起目录名每个 session 各起各的（任务板试点 #541）。上游改这行模板 → 收上游措辞，把这一项接回去 |
| `## The map` 第一句、`### Chart the map` 第 3 步里 map 的 label | 我们加的：map 除了 `wayfinder:map` 还打分类 label `mmw:map`（仓库没有就先 `gh label create`，颜色 `5319e7`）。`wayfinder:map` 是本技能找 map 用的，`mmw:map` 是 MMW 四层分类（map / spec / ticket / child）的顶层，board 靠它读层级、不数嵌套深度（mmw #315 第 6 节）。三套 label 的分工在 `docs/agents/issue-tracker.md` 的 **Three label sets**。上游改这两处 → 收上游措辞，`mmw:map` 保留 |
| `### Work through the map` 的第 6 步 | 我们加的整步：frontier 与 Not yet specified 都空时 map 已清，停下来把下一步交给 user——新会话里对这张 map 跑 `to-spec`（传完整引用），再 `to-tickets`；map 不关。上游给这一节加了新的收尾步 → 把我们这一步接在它后面并重编号；上游自己写了 map 走完之后往哪去 → 只留上游那一句，删掉我们这一步（`to-spec` 那侧的分卷判断不依赖这句话）。其余段落我们没改，全取上游 |
| `## Ticket Types` 的 Research、Prototype、Grilling 三条，`### Chart the map` 第 1 步与第 5 步，`### Work through the map` 第 3 步，以及 `## Plan, don't do` 里「issue tracker 没给你」那一句 | host 中立：要词汇的写成读那份技能的 `SKILL.md`（Prototype 与 Grilling 两类票用户在场，开子会话会把用户挡在外面），要另一个上下文的写成问本机 host 要它自己的 general-purpose subagent（Research 票与第 5 步，两处句子自己写着 subagent），指路那一句写成点 `setup-matt-pocock-skills` 技能的名。共同理由与三种替换写法见 [README.md](README.md#host-中立) |
| frontmatter 的 `description` | 末尾那两句「什么时候用我」（`Use when the way from here to the destination is not visible yet …` 与 `Not for a well-scoped feature …`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；判据取自 `ask-matt/SKILL.md` 讲 wayfinder 那一条（`so save it for exactly that, never a well-scoped feature`）。上游改这一行 → 收上游对前半句的措辞，末尾这两句保留 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

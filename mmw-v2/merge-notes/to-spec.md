# to-spec

源目录：`mmw-v2/upstream/skills/engineering/to-spec/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 我们没改，**引号也不能去**。值里 `tracker: no` 是一个冒号加空格，YAML 会把不带引号的这一行读成一个嵌套 mapping 的 key，`yaml.safe_load` 对整块 frontmatter 抛 `ScannerError: mapping values are not allowed here`——坏的不是这一个 key，是整份 frontmatter。而 `description` 恰好是每个 host 启动时唯一扫进技能列表的那一行，所以症状不是一声响的失败，是这份技能整个安静地消失；再加上改这一行要重开会话才生效，改动和症状之间还隔着一段距离。理由写在这里，是因为 `description` 的值里装不下注释。别人要求「把 description 统一成不带引号」时 → 这一份是例外，值里含冒号加空格的都是 |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓要求这个 skill 模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用它。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块同增同删 |
| 第 3 步的 seam 由 agent 定、不问 user 那一段，与 `<spec-template>` 里 `## Testing Decisions` 的 `How a test arrives at a state` 那一项 | 我们加的整块。seam 只回答测试在哪**观察**；测试怎么**到达**要测的状态，上游没有问处。判据是「声明的 seam 的写入面够不着」：真数据库的 seam 里测试直接改行就到了，不用写；有 screen contract 时，story 页由 adapter 读该 scene 的值进入场景，测不到只有真实请求才产生的产品状态，four-column boundary test 断言 `calls` / `shows` / `next` / `on_failure`、仍写不进这次点击本应写入的数据库，这两种够不着就必须在这里点名将来靠什么到达、以及那条通路存在于哪些构建。两例加「With a screen contract」门，用登记名 **four-column boundary test**。形态按 consuming repository 自己的可测试性规则给，规则没出口时是那个 repository 要补、不是 spec 去裁定——MMW v2 不该知道某个 repository 的测试规矩写了第几条；spec 只「say so」，后面接一句由 `to-tickets` 出 `reach` ticket，这样这个状态有终点，不在两份技能之间来回。第 3 步明写 seam 由 agent 自己定、不让 user 确认——user 看不懂 seam，问他等于把自己该做的判断推给读不懂的人，也跟开头「只交还一个判断」自相矛盾；user 看到的只是 `## Testing Decisions` 首句那句大白话。上游自己给 `## Testing Decisions` 加了要求 → 收上游措辞，这一项保留；上游加回「问 user 确认 seam」→ 不收；上游把够不着的例子改回 debugging port 或去掉 screen-contract 门 → 不收，story 页与 four-column boundary test 两例保留 |
| 第 4 步 publish 那一句的 label 规则 | 我们改的：spec 只打一个 label，分类 label `mmw:spec`（仓库没有就先 `gh label create`，颜色 `1d76db`），不打任何队列 label。spec 是它底下那批 ticket 的容器，不是一件待办。不打 `ready-for-agent` 的 spec 三道关全都过不去：进不了 `is:open label:ready-for-agent` 这条 agent queue，过不了 `preflight` 的第四项（`NOT_READY: … has no ready-for-agent label`），也过不了 `dispatch.sh` 派活前的查票（`REFUSE ticket #… is not labelled ready-for-agent`）。分类 label 不进任何队列，它回答的是「这张票是哪一层」，board 靠它把 spec 和 ticket 分开，不必数嵌套深度——所以原来那句「Leave it unlabelled」的理由只反对队列 label，不反对分类 label（mmw #315 第 6 节，用户确认）。三套 label 的分工写在 `docs/agents/issue-tracker.md` 的 **Three label sets**。上游改这句措辞 → 仍然不打队列 label，`mmw:spec` 保留 |
| 第 4 步 publish 之后的一句 | 我们加的：spec 由带 agent brief 的 issue 长出来时，把那张 issue 关掉并挂到 spec 底下。理由：这是 `docs/adr/0001-tracker-repo-authority.md` 的一条 Consequence，而整条 landing pipeline 只有这一步在 spec 刚 publish 时手上同时有两个号；agent brief 只存在于 issue tracker 上，仓库里没有对应文件，取代它的 spec 要能一路走回去。上游改 publish 那一步 → 收上游措辞，这一句接在真正 publish 的那一句之后 |
| 第 4 步 publish 的 native parent 三段 | 我们加的整块，接在 agent-brief 那一句之后，是 map child spec 的 prompt contract，不得缩成「记得设 parent」。wayfinder map 且 tracker 是 GitHub 时：每份 spec 都用 `gh issue create --parent <map>` 建成 map 的 native sub-issue，读回 `parent.number` 必须等于 map 号，缺了或不同就是 failed publish，交给下一手之前改掉；`## Sources`、`## Further Notes`、spec title、semantic similarity 都不能替代 native parent。引用不是 wayfinder map 时：do not invent a map parent，conversation / file / standalone issue / 其它非 map 来源在 map 层保持 parentless，除非来源自己已经带 native parent。GitHub 之外的 tracker 继续用它自己的 native sub-issue relationship，不增加自定义 Parent 字段或第二套 task-root metadata。第 1 步的 one-spec/several-spec 判断和 `## Specs` 写回顺序不动；后一份从同一 map 发布的 spec 走同一段，不只第一份。上游改第 4 步 → 收上游措辞，这三段仍接在 publish 与 agent-brief 之后 |
| `## Process` 的第 1 步 | 我们加的整步，上游原来的三步在它后面顺延：user 传了引用就先读全，是 wayfinder `map` 时按 `Decisions so far` 逐张读 resolution comment、读到 prototype 与 research file 的结论、`Out of scope` 原样进 spec；然后判一份还是几份 spec（同一个 seam 归一份，能不分就不分；分层交付里后一份依赖前一份是允许的，只要依赖单向不成环、顺序写进 `## Specs`——上游那条「实现票不依赖别的部分」的判据下没有任何分层产品能切成多份，而 `--lint` 把 cross-batch 的 blocker 记 `WARN`，正是为它留的口子），几份时问 user 确认并把划分写回 `map` 的 `## Specs`，只写第一份，publish 后回填链接再停。引用不是 map（issue、URL、文件、对话）时没有 map 可写回，划分写进第一份 spec 的 `## Further Notes`（每份一行：叫什么、覆盖什么、顺序、发布后的链接），下次对同一来源跑本技能时从那里接着写、经第 5 步回填链接，全部有链接时直接告诉 user 已写完——`<spec-template>` 的 `## Further Notes` 说明里也写了这个形状。上游改了 `## Process` 的编号或在前面插步 → 收上游的顺序，我们这一步永远排第一（它决定这次到底写几份 spec）|
| `## Process` 的第 5 步「Revising a published spec」，与第 1 步里指向它的那一句 | 我们加的整步：引用是已发布的 spec issue、要改其中一节时，读全正文、直接干净地改那一节、`gh issue edit --body-file` 写回，正文不留改动痕迹，改了什么、为什么写成一条评论，已出的 ticket 对着新文本核一遍。理由：重开一份 spec 编号会变、ticket 的 `## Parent` 指错；正文有历史则 user 读 spec 时在读历史。`triage` 技能第 5 步 `ready-for-agent` 一条的「extend a spec」指的就是这一步。上游自己加了修订已发布 spec 的步骤 → 收上游措辞，「正文干净、理由进评论」保留 |
| 开头 `Do NOT interview the user for facts` 那一句 | 我们改的：只禁问事实，并指向第 1 步那个唯一交还给 user 的判断，免得跟分卷确认自相矛盾。上游重写这句 → 收上游措辞，把这个例外重新挂上去 |
| 模板里 `## Implementation Decisions` 的说明 | 我们改的：小节编号（`### 1.`），每条决定句末标出处（decision ticket 的 ticket number、ADR、research file 路径），没有出处的明写 `this spec's decision`；路径规则收窄成 `no implementation file paths`，出处路径、测试目录、共享 contract 的位置必须写。理由：`to-tickets` 的 ticket 要用「第 N 节」指回，`## Read first` 要从小节里抄出处。上游重写这一节 → 收上游措辞，把编号、出处、路径三条接回去 |
| 模板里 `## Testing Decisions` 的说明 | 我们改的：首句是一句大白话，写测试从浏览器页面、HTTP 接口还是函数调用看结果——这是 user 唯一看得懂的那一层，seam 由 agent 定之后 user 只从这句知道定的是什么；第二句写第 3 步定下的 seam 与允许打桩的 external seams；之后按 test layer 列目录与 precedent，那个要抄的东西叫 `the precedent to copy`；末尾列提交前要跑的命令。理由：ticket 的 `## Seam` 从这里抄，而 `to-tickets` 第 4 步写的是 `the precedent it names`、`CONTEXT.md` 登记的正名是 `precedent`——同一样东西不给两个名字，否则写 ticket 的一方在 spec 里搜 `precedent` 搜不到。上游改这一节 → 收上游，大白话首句、seam 那一句、分层落点、`precedent` 一词四条保留 |
| 模板里 `## Testing Decisions` 的 **Critical flows**（关键流程） | 我们改的：原 **Cross-ticket flows** 收窄为关键流程——钱、登录、提交链，没有就不写；每条写流程名与涉及的 Implementation Decisions 节号。`to-tickets` 仍按行切 acceptance ticket。原句「Omit the bullet when the repository's `.mmw/target.json` cannot start the whole product.」保留。理由：#447 第 6 节（#415 第 16 节的范围收窄）。上游改 `## Testing Decisions` → 收上游措辞，这一项保留，名字保持 **Critical flows** / 关键流程，不能起整栈那一句仍在 |
| 第 5 步末尾「A published spec, a ticket body and its acceptance criteria are edited only by the main agent or the user.」 | 我们加的。理由：#415 第 5 节。上游改第 5 步 → 收上游措辞，这一句接在修订步骤之后 |
| 模板里 `## Further Notes` 之前的 `## Sources` 节 | 我们加的：一手来源固定十一类（wayfinder `map`、decision ticket、上游 spec、ADR、research file、prototype 目录、handoff package、screen contract、Domain docs、实测证据、测试规则），每类无则填 `none`。`implement` 技能靠这个节名往回读，改名要同步改 `implement`；`to-tickets` 的 `## Read first` 从这里按 ticket 挑。上游自己加了同类的来源节 → 用上游的名字，同步改 `implement` 与 `to-tickets`，十一类保留 |
| 开头「issue tracker 与 triage label 词汇没给你就去装」那一句 | host 中立：技能名写成散文形式，与 `triage`、`wayfinder` 的同一句同一个说法。共同理由与三种替换写法见 [README.md](README.md#host-中立) |
| 第 2 步的第二段（screen contract）、`## Implementation Decisions` 说明里的 **API contract** 小节、`## Sources` 的 Handoff package 与 Screen contract 两类 | 我们加的：有界面的效果有两个各管一域的基线——交接包管外观与逐字文案，`docs/specs/<effort>/screen-contract.yaml`（`write-screen-contract` 技能写出：有 map 时从 alignment ticket，没有 map 时与 to-spec 同一 session）管调用、显示值、流转、失败与计时。spec 读全合同；有 `gap` 未 `aligned` 就停、不出 spec：有 map 退回 alignment ticket，没有 map 留在同一 session、退回 `write-screen-contract` 的 **Reverse sweep**，再由用户在 **Write the gap list and stop for the person** 里裁决。没有 map 就没有 alignment ticket。`calls`/`shows` 两列生成 **API contract** 小节，新项目的 OpenAPI 从这里起。理由：交接包和后端决定各自完整、无处汇合，变色龙的界面因此接了空；没有 map 时没有 alignment ticket 可退（#446 第 4 节、#447 第 6 节）。上游改这几节 → 收上游措辞，这三处与两条退回路径接回去；Sources 若改名同步改 `implement`、`to-tickets`、`write-screen-contract` |
| 第 2 步「读全合同」加 `pages` 与 `scenes`；`## Implementation Decisions` 说明加「story 的定论折进实现它的小节」一段并把「user-story number」从出处清单拿掉 | 我们改的，来自 mmw #216 第 8 节（取代 #115 的 mechanism registry 与「只引 pages/scenes」的 visual acceptance；后两项的现行写法见下面 visual acceptance 与 How a test arrives 两行）。上游改这几处 → 收上游措辞，pages / scenes 与 story 定论折进实现小节保留 |
| `## Implementation Decisions` 说明里 **API contract** 之后的 **`App · ` 页组合** 小节 | 我们加的：有 screen contract 时的固定小节；每条 **cross-component row** 对应的请求字段与另一区域的状态，按 row id 引用。理由：#447 第 6 节。上游改 Implementation Decisions 说明 → 收上游措辞，这一小节保留 |
| `## Implementation Decisions` 说明里的 **visual acceptance** 一段 | 我们改的：外观由 `ui-acceptance` 的 story judge 按 `data-ui` id 做 **element parity**，引用合同的 `pages`，`App · ` 页包含在内；仍不写命令形状。取代 #216「`App · ` pages excluded」与「只引 pages 与 story 判官」。理由：#447 第 6 节。上游改这一段 → 收上游措辞，element parity、pages、`App · ` 页包含、不写命令形状保留 |
| 模板里 `## Testing Decisions` 的 **How a test arrives at a state** 末句与 **Test surfaces** | 我们改的：**How a test arrives at a state** 按该产品 contract ticket 现场定下的做法填写，不在 to-spec 里写死 adapter / 交互助手 / `.mmw/target.json`（不设 mechanism registry，#216 取代 #115）。**Test surfaces** 指向 `ui-acceptance` 技能的 `references/product-answers.md`，个数以该技能的 `target_config.py --check` 为准，不在这里列一份——旧的七项枚举把可选的 `instance` 算进去、漏了必填的 `harness_markers`。理由：#447 第 6 节（工作监控与变色龙各按自己的形态定过做法）。上游改这两项 → 收上游措辞，现场填写、指向 `product-answers.md`、以 `--check` 为个数保留 |
| `</spec-template>` 之后的 `## Next` | 我们加的：末节点名下一步 `to-tickets`。有 map 时 wayfinder **Work through the map** 第 6 步已经指路，没有 map 时由这里接上。理由：#447 第 6 节、方案 K7。上游在 SKILL.md 末尾加了下一步 → 收上游措辞，`to-tickets` 保留 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

## 一个概念一个名字：product answers / acceptance runtime

`## Testing Decisions` 的 **Test surfaces** 那一条原来写 `the answers that make the repository a runnable environment`。同一样东西在工具箱里有过四个名字——`automatable acceptance runtime`、`product answers`、`runnable environment`、`drivable`——而写 spec 的 agent 被这一句送去 `ui-acceptance` 的 `references/product-answers.md`，打开却是第四个说法，分不清是不是同一个文件。定名：**内容**叫 `product answers`（它是那个 reference 的文件名，也是 ADR 0028 的用词），**状态**叫 `acceptance runtime`；两个都登记在 `docs/contexts/ui-acceptance/CONTEXT.md`。这一条因此写成 `the **product answers** that make the repository an acceptance runtime`。

上游改 **Test surfaces** → 收上游措辞，`product answers` 与 `acceptance runtime` 两个名字保留，不收回 `runnable environment`。

## 有 screen contract 时，How a test arrives at a state 仍点名机制与主人

`## Testing Decisions` 的 **How a test arrives at a state** 那一条，原先有 screen contract 时的结尾是「从这个产品 contract ticket 在现场定下的做法来填……Do not write a second copy of those mechanisms here」。这一句把同一条自己的用途关掉了：同一条前面写着切票的人读这一节来判断一条判据写不写得出来、并由其中一张票负责建这里点名的每个机制；`to-tickets` 第 4 问要求把系统摆进某个状态的东西在这一节被点名、并落在某张票的 **Owns** 里，缺一样就切 `reach` ticket，第 8 步还回读核对。这一节对界面批次一留空，整批界面判据就都判第四问失败，或者切票的 agent 索性不问第四问。新产品更糟：它的 contract ticket 正是从这份 spec 切出来的，写 spec 时还什么都没「在现场定下」。

现在改成点名：有 screen contract 时，这一节写三个机制各自归哪张票建——从 scene data 把 story 页摆进一个 scene 的 story adapter、按 `data-ui` id 把控件摆上屏给 four-column boundary test 用的 interaction helper、给 journey 起产品的 `.mmw/target.json` 的 `start`。新产品三个都归 contract ticket；`.mmw/` 已经能回答的产品，写出建 `target_config.py --check` 报缺之物的那张票，或写明什么都不缺。「不写第二份」原本想说的是**形状**：每个机制怎么搭写在 `ui-acceptance` 技能的 reference 里，这里只点名、不复述。理由：#539。

上游改 **How a test arrives at a state** → 收上游措辞，「有 screen contract 时点名三个机制与主人、形状不复述」保留，不收回「不写第二份」那种留空的写法。

## 谁建 story adapter；scene input；旧 spec 算上游 spec

**How a test arrives at a state**：新产品上 contract ticket 建 story service 与第一个 story adapter、interaction helper、`start`，之后每张 component page ticket 加本页的 adapter，与 `ui-acceptance` 的 `story-parity.md` 和词表一致（原文写「三个都归 contract ticket」，两边冲突）；已有 `.mmw/` 的产品，缺的除了 `--check` 报的，还有为别一代交接包、scene 形状或控件查找方式建的答案。story adapter 一句加「或合同的 scene input」。`## Sources` 的上游 spec 一类写明包括决定票引为依据的旧 spec。理由：任务板试点 #541。上游改这几句 → 收上游措辞，这几处保留。

## 没有合同行的决定；外观验收那一段放哪

第 2 步加一句：没有合同行、交接包也没画成控件的决定（例如一段文字的行为），写进它所属的小节并注明来源，算本 spec 的决定。模板的 visual acceptance 一段写明放在自己的编号小节或带 `data-ui` id 的那一节。理由：任务板试点 #541 起草 spec 时两处都要猜。上游改这两处 → 收上游措辞，这两句保留。

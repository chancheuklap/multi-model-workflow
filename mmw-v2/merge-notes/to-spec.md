# to-spec

源目录：`mmw-v2/upstream/skills/engineering/to-spec/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓要求这个 skill 模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用它。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块同增同删 |
| 第 3 步的 seam 由 agent 定、不问 user 那一段，与 `<spec-template>` 里 `## Testing Decisions` 的 `How a test arrives at a state` 那一项 | 我们加的整块。seam 只回答测试在哪**观察**；测试怎么**到达**要测的状态，上游没有问处。判据是「声明的 seam 的写入面够不着」：真数据库的 seam 里测试直接改行就到了，不用写；而经 debugging port 比对界面只读渲染结果、写不进应用状态，就必须在这里点名将来靠什么到达、以及那条通路存在于哪些构建。形态按 consuming repository 自己的可测试性规则给，规则没出口时是那个 repository 要补、不是 spec 去裁定——MMW v2 不该知道某个 repository 的测试规矩写了第几条；spec 只「say so」，后面接一句由 `to-tickets` 出 `reach` ticket，这样这个状态有终点，不在两份技能之间来回。第 3 步明写 seam 由 agent 自己定、不让 user 确认——user 看不懂 seam，问他等于把自己该做的判断推给读不懂的人，也跟开头「只交还一个判断」自相矛盾；user 看到的只是 `## Testing Decisions` 首句那句大白话。上游自己给 `## Testing Decisions` 加了要求 → 收上游措辞，这一项保留；上游加回「问 user 确认 seam」→ 不收 |
| 第 4 步的 `Leave it unlabelled` | 我们改的：spec 不打 label。spec 是它底下那批 ticket 的容器，不是一件待办。不打 `ready-for-agent` 的 spec 三道关全都过不去：进不了 `is:open label:ready-for-agent` 这条 agent queue，过不了 `preflight` 的第四项（`NOT_READY: … has no ready-for-agent label`），也过不了 `dispatch.sh` 派活前的查票（`REFUSE ticket #… is not labelled ready-for-agent`）。上游改这句措辞 → 仍然不打 label |
| 第 4 步 publish 之后的一句 | 我们加的：spec 由带 agent brief 的 issue 长出来时，把那张 issue 关掉并挂到 spec 底下。理由：这是 `docs/adr/0001-tracker-repo-authority.md` 的一条 Consequence，而整条 landing pipeline 只有这一步在 spec 刚 publish 时手上同时有两个号；agent brief 只存在于 issue tracker 上，仓库里没有对应文件，取代它的 spec 要能一路走回去。上游改 publish 那一步 → 收上游措辞，这一句接在真正 publish 的那一句之后 |
| `## Process` 的第 1 步 | 我们加的整步，上游原来的三步在它后面顺延：user 传了引用就先读全，是 wayfinder `map` 时按 `Decisions so far` 逐张读 resolution comment、读到 prototype 与 research file 的结论、`Out of scope` 原样进 spec；然后判一份还是几份 spec（同一个 seam 归一份，能不分就不分；分层交付里后一份依赖前一份是允许的，只要依赖单向不成环、顺序写进 `## Specs`——上游那条「实现票不依赖别的部分」的判据下没有任何分层产品能切成多份，而 `--lint` 把 cross-batch 的 blocker 记 `WARN`，正是为它留的口子），几份时问 user 确认并把划分写回 `map` 的 `## Specs`，只写第一份，publish 后回填链接再停。引用不是 map（issue、URL、文件、对话）时没有 map 可写回，划分写进第一份 spec 的 `## Further Notes`（每份一行：叫什么、覆盖什么、顺序、发布后的链接），下次对同一来源跑本技能时从那里接着写、经第 5 步回填链接，全部有链接时直接告诉 user 已写完——`<spec-template>` 的 `## Further Notes` 说明里也写了这个形状。上游改了 `## Process` 的编号或在前面插步 → 收上游的顺序，我们这一步永远排第一（它决定这次到底写几份 spec）|
| `## Process` 的第 5 步「Revising a published spec」，与第 1 步里指向它的那一句 | 我们加的整步：引用是已发布的 spec issue、要改其中一节时，读全正文、直接干净地改那一节、`gh issue edit --body-file` 写回，正文不留改动痕迹，改了什么、为什么写成一条评论，已出的 ticket 对着新文本核一遍。理由：重开一份 spec 编号会变、ticket 的 `## Parent` 指错；正文有历史则 user 读 spec 时在读历史。`triage` 技能第 5 步 `ready-for-agent` 一条的「extend a spec」指的就是这一步。上游自己加了修订已发布 spec 的步骤 → 收上游措辞，「正文干净、理由进评论」保留 |
| 开头 `Do NOT interview the user for facts` 那一句 | 我们改的：只禁问事实，并指向第 1 步那个唯一交还给 user 的判断，免得跟分卷确认自相矛盾。上游重写这句 → 收上游措辞，把这个例外重新挂上去 |
| 模板里 `## Implementation Decisions` 的说明 | 我们改的：小节编号（`### 1.`），每条决定句末标出处（decision ticket 的 ticket number、ADR、research file 路径），没有出处的明写 `this spec's decision`；路径规则收窄成 `no implementation file paths`，出处路径、测试目录、共享 contract 的位置必须写。理由：`to-tickets` 的 ticket 要用「第 N 节」指回，`## Read first` 要从小节里抄出处。上游重写这一节 → 收上游措辞，把编号、出处、路径三条接回去 |
| 模板里 `## Testing Decisions` 的说明 | 我们改的：首句是一句大白话，写测试从浏览器页面、HTTP 接口还是函数调用看结果——这是 user 唯一看得懂的那一层，seam 由 agent 定之后 user 只从这句知道定的是什么；第二句写第 3 步定下的 seam 与允许打桩的 external seams；之后按 test layer 列目录与 precedent，那个要抄的东西叫 `the precedent to copy`；末尾列提交前要跑的命令。理由：ticket 的 `## Seam` 从这里抄，而 `to-tickets` 第 4 步写的是 `the precedent it names`、`CONTEXT.md` 登记的正名是 `precedent`——同一样东西不给两个名字，否则写 ticket 的一方在 spec 里搜 `precedent` 搜不到。上游改这一节 → 收上游，大白话首句、seam 那一句、分层落点、`precedent` 一词四条保留 |
| 模板里 `## Further Notes` 之前的 `## Sources` 节 | 我们加的：一手来源固定九类（wayfinder `map`、decision ticket、上游 spec、ADR、research file、prototype 目录、Domain docs、实测证据、测试规则），每类无则填 `none`。`implement` 技能靠这个节名往回读，改名要同步改 `implement`；`to-tickets` 的 `## Read first` 从这里按 ticket 挑。上游自己加了同类的来源节 → 用上游的名字，同步改 `implement` 与 `to-tickets`，九类保留 |

| 第 2 步的第二段（screen contract）、`## Implementation Decisions` 说明里的 **API contract** 小节、`## Testing Decisions` 里 **How a test arrives at a state** 末尾的 **mechanism registry** 一句、`## Sources` 的 Handoff package 与 Screen contract 两类 | 我们加的：有界面的效果有两个各管一域的基线——交接包管外观与逐字文案，`docs/specs/<effort>/screen-contract.yaml`（`align-screens` 技能从 alignment ticket 写出）管调用、显示值、流转、失败与计时。spec 读全合同；有 `gap` 未 `aligned` 就退回 alignment ticket，不出 spec。`calls`/`shows` 两列生成 **API contract** 小节，新项目的 OpenAPI 从这里起；机制登记项统一 `seed:`/`stub:`/`dev:` 三种前缀，`reach` 只引用这里。理由：交接包和后端决定各自完整、无处汇合，变色龙的界面因此接了空。上游改这几节 → 收上游措辞，这四处接回去；Sources 若改名同步改 `implement`、`to-tickets`、`align-screens` |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

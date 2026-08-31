# to-spec

源目录：`mmw-v2/upstream/skills/engineering/to-spec/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 第 4 步「Apply the `ready-for-agent` triage label」 | 改成「不打标签」。spec 是它底下那批票的容器，不是一件待办。不打 `ready-for-agent` 的 spec 三道关全都过不去：进不了 `is:open label:ready-for-agent` 这条 agent 队列，过不了开工守卫 `--preflight` 的第四项（`NOT_READY: … has no ready-for-agent label`），也过不了 `dispatch.sh` 派活前的查票（`REFUSE ticket #… is not labelled ready-for-agent`）。上游改这句措辞 → 仍然不打标签 |
| 第 4 步发布之后的一句 | 我们加的：spec 由带 agent brief 的 issue 长出来时，把那张 issue 关掉并挂到 spec 底下。理由：这是 `docs/adr/0001-tracker-repo-authority.md` 的一条 Consequence，而全流水线只有这一步在 spec 刚发布时手上同时有两个号；agent brief 只存在于 tracker 上，仓库里没有对应文件，取代它的 spec 要能一路走回去。上游改发布那一步 → 收上游措辞，这一句接在真正发布的那一句之后 |
| 开始写文档的那一句 | 追加一句：用 `readable-docs` 技能写，落盘/发布前跑它的 claim check。上游改这句的措辞或位置 → 收上游，把我们这一句接回新位置。上游把写文档这一步拆成多句 → 接在真正落笔的那一句后面。其余段落我们没改，全取上游 |
| `## Process` 的第 1 步 | 我们加的整步，把上游原来的 1/2/3 顺延为 2/3/4：用户传了引用就先读全，是 wayfinder 地图时按 Decisions so far 逐张读 resolution comment、读到 prototype 与 research 的结论、Out of scope 原样进 spec；然后判一份还是几份 spec（同一个 seam 归一份，能不分就不分；分层交付里后一份依赖前一份是允许的，只要依赖单向不成环、顺序写进 `## Specs`——上游原本要求「实现票不依赖别的部分」，那条判据下没有任何分层产品能切成多份，而 `--lint` 现在把跨批次依赖当 `WARN` 正是为它留的口子），几份时问用户确认并把划分写回地图的 `## Specs`，只写第一份，发布后回填链接再停。上游改了 `## Process` 的编号或在前面插步 → 收上游的顺序，我们这一步永远排第一（它决定这次到底写几份 spec）|
| 开头「Do NOT interview the user」那一句 | 改成「Do NOT interview the user **for facts**」并指向第 1 步那个唯一交还给用户的判断，免得跟分卷确认自相矛盾。上游重写这句 → 收上游措辞，把这个例外重新挂上去 |
| 模板里 `## Implementation Decisions` 的说明 | 我们改的：小节编号（`### 1.`），每条决定句末标出处（决定票号 / ADR / research 路径），没有出处的明写「this spec's decision」；路径禁令收窄成「不写实现文件路径」，出处路径、测试目录、共享合同位置必须写。理由：`to-tickets` 的票要用「第 N 节」指回，`## Read first` 要从小节里抄出处。上游重写这一节 → 收上游措辞，把编号、出处、路径三条接回去 |
| 模板里 `## Testing Decisions` 的说明 | 我们改的：首句固定写第 3 步确认过的 seam 与允许打桩的外部 seam；之后按测试层次列目录与先例，那个要抄的东西叫 `the precedent to copy`；末尾列提交前要跑的命令。理由：票的 `## Seam` 从这里抄，而 `to-tickets` 第 4 步写的是 `the precedent it names`、`CONTEXT.md` 登记的是「先例」——同一样东西不给两个名字，否则出票人在 spec 里搜 `precedent` 搜不到。上游改这一节 → 收上游，seam 首句、分层落点、`precedent` 一词三条保留 |
| 模板里 `## Further Notes` 之前的 `## Sources` 节 | 我们加的：一手来源固定九类（map、决定票、上游 spec、ADR、research、prototype、领域文档、实测证据、测试规则），每类无则填「none」。`implement` 技能靠这个节名往回读，改名要同步改 `implement`；`to-tickets` 的 `## Read first` 从这里按票挑。上游自己加了同类的来源节 → 用上游的名字，同步改 `implement` 与 `to-tickets`，九类保留 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

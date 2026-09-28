# advisor

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能已经有灵魂："the value is a session that has not spent the last hour convincing itself"、"Your framing is the thing under review"、"A second opinion you steered is your own opinion in a stronger model's voice"。这几句都保留。缺的有三样：一是 advisor 这一侧对"这次回答有多要紧"的交代；二是发起咨询的一方拿到回答后该怎么对待；三是"值不值得问"的判据。另有一处矛盾要你决定。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `references/advising.md` 开头第一句，改为右栏（只补上漏掉的触发条件） | You are the advisor: a second opinion on a stronger model, consulted before a commitment is made, after a problem has resisted two attempts, or before a disputed reading of the task is treated as fact. You receive the packet the caller composed, not its session or its tool trace. | 补上"试了两次"这个触发条件后，advisor 知道这类 packet 要的是"对方对问题的模型哪里错了"，而不是在几个方案里挑一个；I4 依赖这一点。调查员原稿与我初稿里的 "consulted at the moment that decides whether the next hour of work is wasted" 按 advisor 意见删去：它只是宣告重要性，读透文件已由第 1 条 "Look before you opine" 要求。 |
| I2 | `references/consulting.md` `## Start it` 之后，新起一节 `## The answer` | The answer is advice, not a ruling: you still own the decision. Take it, or set it aside with a reason you can state. When it would change something the user decides (what the customer sees, scope, anything hard to undo), it goes to the user like any other such decision, with the advisor's reasoning attached. | 没有它，agent 会把更强模型的话当成裁决照做，甚至越过用户已定的产品决定；或者读完既不采纳也不说明。与你全局 CLAUDE.md 第 1 条的分工一致。 |
| I3 | `consulting.md` `## When it is worth a session` 第一句之后 | The test is the cost of being wrong: a choice that is expensive to undo once work is built on it, or a problem whose repeated failure says your model of it is off. A choice you could reverse in minutes is not worth a session. | 三条正面触发只在 description 里，reference 里只有反面。遇到清单外的情况（一个配置选择、一次中等规模的改名），有了这个判据，agent 能自己判断值不值。 |
| I4 | `consulting.md` `## The packet` 列表之后 | The test for the packet: a stranger with only this and the repository can reconstruct the decision. For a problem that resisted two attempts, each attempt and what it produced is the core of the evidence. | 五项是为"提交前选方案"写的，"试了两次"那种情况最要紧的证据（试了什么、得到什么报错）不在里面。五项本身不动：`dispatch.sh` 的拒绝信息引用了 "the five parts"。 |
| I5 | `consulting.md` "One decision gets one consultation" 改为右栏 | Do not ask again to get a different answer. A second consultation is for a new decision, or for the evidence the advisor said would change its answer. | 原规则防的是反复问到满意为止，但也禁掉了正当的第二次：advisor 按 `advising.md` 第 4 条说"缺 X 会改变答案"，caller 查到 X 以后再问一次是合理的。 |
| I6 | `advising.md` `## What you never do` 第二条 "Review diffs or whether work was executed." 改为右栏 | Judge the quality of a diff or whether work was done: that is the reviewer's. Reading uncommitted changes to see where the work stands is part of looking. | 原句字面上禁止看 diff，而 ADR 0014 让 advisor 跑在 caller 的工作树里，正是为了看见没提交的改动。**推断**：没观察到 advisor 因此不看 `git diff`。 |

### 删除

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `consulting.md` "To change which host or model the advisor uses, read the dispatch skill's `references/editing-models.md`." | 删 | 咨询那一刻不是改配置的时刻；`dispatch` 的 description 已负责触发。 |
| D2 | `consulting.md` "Exit 0 prints the session id. Exit 2 starts nothing; the reason is on stderr, read it verbatim." | 改为 "It prints the advisor's session id; a refusal says what to fix." | 复述脚本。 |
| D3 | `advising.md` "Agree without checking. If you'd genuinely push back, push back." | 并进 `## How to answer` 第 3 条："A sound reading gets a short answer, and only after you have checked it." | 与第 1、3 条正反同义。 |
| D4 | `dispatch.sh` `advise_one` 第 2061 行缺 advisor 行时的拒绝 | 删 | 永远走不到：`models.py` 先以 exit 2 拒绝；测试通过掩盖了这一点。 |

### 已定（2026-09-28）：读法 A

`consulting.md` 里有两句互相矛盾。"Read the answer where the selected runner shows the session" 让发起方自己去读回答；"Done when `advise` exits 0 and you have told the user its session id" 却把启动成功、交出会话 id 当作完成。你在 9 月 23 日定过"advisor 的回答怎么读，不修"，下面两种写法取决于那条裁定的原意：

- **读法 A：由发起方读回答，并据此行动。** Done when 改为 "Done when you have the answer and have acted on it as **The answer** says, and the user has the session id."。I2 随之生效。
- **读法 B：回答由你自己去 runner 里读。** 删掉 "Read the answer where the selected runner shows the session"，Done when 不动；I2 改成写给你看的说明，放在交出会话 id 的那一句旁边。

采用读法 A：咨询的意义是让发起方在做决定前拿到第二意见，只交出一个会话 id 就结束，第二意见到不了做决定的人手里。读法 B 不再考虑。

## 结论

`mmw-v2/skills/advisor/` 共 952 词（`SKILL.md` 156、`references/consulting.md` 360、`references/advising.md` 436），自身没有脚本；启动靠 dispatch 技能的 `dispatch.sh advise`（`mmw-v2/skills/dispatch/scripts/dispatch.sh` 的 `advise_one`，第 2046–2078 行，约 30 行）。这个技能已经很轻，没有编号流程压着判断，也没有明显的过度设计；真正的"废话"只有两三句，合计约 35 词可删。它的"灵魂"主体完整：`## The question stays open` 和 `## The packet tells you what the caller knows` 两侧互相对应，守的是 ADR 0014 记录过的真实问题（caller 替 advisor 划定调查范围）。缺的是三样：前几轮减重删掉的"为什么是这个时刻"（stakes）那句；caller 拿到回答以后怎么对待它（它是建议，不是裁决；越到产品决定要交给用户）；以及 packet 五项里没有"已经试过什么、结果如何"，而"一个问题试了两次都没解决"恰恰是三个触发条件之一。补充约 110 词，净增约 75 词。脚本侧有一条死代码（缺 advisor 行的拒绝永远走不到）。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `references/consulting.md` `## Start it`，"To change which host or model the advisor uses, read the dispatch skill's `references/editing-models.md`." | 2 | 在咨询的那一刻，caller 要做的是写 packet、启动 advisor；改模型是用户对机器配置的操作，不是这一刻的动作。dispatch 技能的 description 已写 "change the host, model, reasoning effort or runner"，`editing-models.md` 第 17 行已把 `advisor` 列为允许的角色 | dispatch 技能的 description 负责触发；models.json 缺行或模型不可用时，`models.py` / `dispatch.sh` 的拒绝信息指路。剩余风险：无 | 删这一句（约 20 词） |
| A2 | `references/consulting.md` `## Start it`，"Exit 0 prints the session id. Exit 2 starts nothing; the reason is on stderr, read it verbatim." | 1 | 复述 `dispatch.sh` 第 2046–2049 行注释和 `refuse` 的行为；`advise_one` 每一个拒绝都自带下一步（第 2053、2054、2067、2069、2075 行）。"read it verbatim" 是 agent 默认就会做的事 | 脚本的拒绝信息。agent 仍需知道成功时输出的是 session id（它要把 id 交给用户），这一半保留 | 改成 "It prints the advisor's session id; a refusal says what to fix."（省约 12 词） |
| A3 | `references/advising.md` `## What you never do`，"Agree without checking. If you'd genuinely push back, push back." | 6 | 与同文件 `## How to answer` 第 1 条 "Look before you opine" 和第 3 条 "Do not manufacture objections" 是同一对意思的正反两面 | 第 1、3 条已覆盖。剩余风险：极小；这一句把"迎合"点名为禁止项，语气更重。可留可删，优先级最低 | 可选：删掉，或并进第 3 条："A sound reading gets a short answer, and only after you have checked it." |

没有列入 A 的（看过，判断为该留）：

- `consulting.md` `## Resolve <dispatch> once`：看似和 dispatch 技能 `SKILL.md` `## Resolve <dispatch> once` 重复，但 caller 此刻没有加载 dispatch 技能；这句防的是"把本机路径写死"这一已知误用，属于 `SKILL-SET-REVIEW.md` `### Redundancy and bloat` 里"These stay"的第一类。保留。
- `consulting.md` `## The question stays open` 与 `advising.md` `## The packet tells you what the caller knows` 表达同一条禁令，但这是有意的两份：ADR 0014（`docs/adr/0014-advisor-has-one-door.md` `## 要修的是什么`）写明禁令必须同时落在 caller 看得见的地方和 advisor 自己的正文里，两边读者不同、各自只读一份。不要合并。
- `consulting.md` `## The packet` 的五项列表：`dispatch.sh` 第 2054 行的拒绝信息写着 "write the five parts consulting.md lists"，脚本引用了它；改动见 C1。

## B. 灵魂

### 保留，勿删

- `references/consulting.md` 开头，"started as its own session that holds none of your context and reads the code itself; writing nothing is a rule it keeps, not a limit its session enforces. It is slow and expensive next to the worker models."：告诉 caller 为什么 packet 必须自足、为什么不是每个决定都值得一次咨询。
- `references/consulting.md` `## When it is worth a session`，"the value is a session that has not spent the last hour convincing itself."：整份技能存在的理由，一句话说清第二意见的价值来自"没被自己说服过"。
- `references/consulting.md` `## The packet`，"The advisor sees the packet and nothing else: not your session, not your tool trace, not the file you have open."：让 caller 从读者的位置写 packet。
- `references/consulting.md` `## The question stays open` 全段，尤其 "Your framing is the thing under review" 和 "A second opinion you steered is your own opinion in a stronger model's voice."：守的是 ADR 0014 记录的真实失败（"派 advisor 的 main agent 经常替它划定调查范围"），不是设想出来的。
- `references/advising.md` `## The packet tells you what the caller knows` 全段，"The caller is the party whose judgement is in question"：advisor 这一侧对同一条禁令的执行；三条 bullet 各对应一种真实的引导方式。
- `references/advising.md` `## How to answer` 五条：第 1 条 "The packet is a claim about the world, not evidence of it"、第 2 条 "Weighing the options at length is doing the caller's job instead of yours"、第 3 条 "Do not manufacture objections to justify being consulted"、第 5 条 "Write for a model mid-task, not for a report" 都是思考方式，不是步骤。
- `references/advising.md` `## What you never do` 第一条的后半句 "Your session runs with permissions granted and no tool list stops you, so this is a rule you keep, not one that keeps you."：ADR 0014 `## Consequences` 第一条确认只读只能靠这句文字实现，删了就没有任何东西拦 advisor 写 caller 正在改的文件。
- `references/advising.md` `## What you never do` 最后一条 "The decision you were given is your scope and the whole of it: name an adjacent concern in one line and go no further."：给出了范围外问题的处理方式，而不只是禁止。

### 缺口与补充草稿

- `references/advising.md` 开头段："consulted before a commitment is made or a disputed reading of the task is treated as fact" 只剩定义，没有分量。提交 e74e0140 和 e9b0866d 删掉了原文 "consulted at exactly the moment that decides whether the next hour of work is wasted" 和 "You're here to be right when it matters, not to help type."。这两句告诉 advisor 为什么值得花时间把文件读透、为什么要给结论而不是综述；没有它们，一个中等 effort 的会话（本机 `~/.mmw/models.json` 的 advisor 行是 `effort: medium`）更容易只读 packet 就作答。开头也漏了三个触发条件中的"一个问题试了两次"，而这种 packet 要的是原因判断，不是方案选择。建议把开头段改为：
  > You are the advisor: a second opinion on a stronger model, consulted at the moment that decides whether the next hour of work is wasted — before a commitment is made, after a problem has resisted two attempts, or before a disputed reading of the task is treated as fact. You are here to be right when it matters. You receive the packet the caller composed, not its session or its tool trace.

- `references/consulting.md` `## Start it` 之后（原 `## What comes back` 的位置）：caller 读到回答以后怎么对待它，技能没说。提交 4e4ee6a5 删掉 `## What comes back` 时，删的是"回答长什么样"，那部分确实与 `advising.md` 重复；但"怎么用这个回答"从来没写过。缺了它，agent 会有两种偏差：把更强模型的话当裁决直接照做，包括越过用户已定的产品决定；或者读完不采纳也不说明。按用户全局规则第 1 条，产品决定（客户看到什么、钱、范围、不可撤回的事）属于用户。建议加一段：
  > The answer is advice, not a ruling: you still own the decision. Take it, or set it aside with a reason you can state. When it would change something the user decides — what the customer sees, scope, anything hard to undo — it goes to the user like any other such decision, with the advisor's reasoning attached.

- `references/consulting.md` `## When it is worth a session`：三条正面触发只在 frontmatter `description` 里，reference 里只剩反面（"What you can settle by reading the code..."），没有判断标准。遇到清单外的情况（一个配置选择、一个中等规模的改名）agent 无从判断值不值。提交 e9b0866d 删了三条 bullet，因为与 description 重复，这个删法本身对；缺的是背后的标准，一句即可：
  > The test is the cost of being wrong: a choice that is expensive to undo once work is built on it, or a problem whose repeated failure says your model of it is off. A choice you could reverse in minutes is not worth a session.

- `references/advising.md` `## What you never do` 第二条 "Review diffs or whether work was executed."：ADR 0014 `## Consequences` 第二条说 advisor 跑在 caller 的 worktree 里，正是为了看见未提交的改动（"正在被决定的那份工作往往还没提交，看不见就答不了"）。现在这句字面上禁止看 diff，可能让 advisor 不去看 `git status` / `git diff`，而那恰恰是理解现状的地方。这是推断，没有观察到实际发生。建议改为：
  > Judge a diff's quality or whether work was done; that is the reviewer's job. Reading uncommitted changes to see where the work stands is part of looking: you run in the caller's own worktree, and the work under decision is often not committed yet.

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| C1 | `references/consulting.md` `## The packet`，"All five parts:" 及 1–5 | 五项是为"提交前的方案选择"写的：options、leaning、constraints。对"一个问题试了两次"这个触发条件，最关键的证据是试了什么、各自得到什么结果（报错、输出），五项里没有。"All five parts" 让 agent 照格填写，而不是问自己"一个陌生人要重建这个决定，还缺什么" | 保留五项（`dispatch.sh` 第 2054 行引用了"the five parts"），在列表后加一句目标和一个分支："The test for the packet: a stranger with only this and the repository can reconstruct the decision. For a problem that resisted two attempts, each attempt and what it produced is the core of the evidence." 如果改成六项，第 2054 行的拒绝信息要同步改 |
| C2 | `references/consulting.md` `## When it is worth a session`，"One decision gets one consultation" | 硬规则没有说明它防的是什么。它防的是重复问同一个决定，直到得到想要的答案（opinion shopping）；但它也禁止了正当的第二次：advisor 按 `advising.md` 第 4 条指出"缺 X 会改变答案"，caller 查到 X 以后，再问一次是合理的 | 改成判断点："Do not ask again to get a different answer. A second consultation is for a new decision, or for the evidence the advisor said would change its answer." |
| C3 | `references/consulting.md` `## Start it`，"Done when `advise` exits 0 and you have told the user its session id." | 完成标准停在"启动成功"，而前一句要求 "Read the answer"。一个咨询真正完成，是 caller 拿到回答并做了取舍。注意：调用方怎么读到回答（runner 没有读取会话输出的动词），用户在 2026-09-23 复审时已裁定不修（`docs/reviews/2026-09-23-skill-set/汇总.md` 第 17、118 行）；tracker 里也没有夜间 worker 调用过 advisor 的记录。这里不重提那个机制 | 只把标准和前一句对齐，不加机制："Done when you have the answer and have acted on it as below, and the user has the session id." 与 B 中"怎么对待回答"那段配合。如果用户对 2026-09-23 那条裁定的原意是"回答由用户自己在 runner 里读"，那就删掉 "Read the answer where the selected runner shows the session"，保留现在的 Done when。两种读法只能取一种，现在两句并存、互相矛盾 |

`advising.md` `## How to answer` 虽然编了号，但除第 1 条（先看再说）有先后以外，其余是并列的原则，不限制判断，不必改。

## 脚本

advisor 没有自己的脚本。它依赖的 `mmw-v2/skills/dispatch/scripts/dispatch.sh` `advise_one`（第 2046–2078 行）：

- **死代码**：第 2061 行 `[ -n "$row" ] || refuse "the advisor row is missing from $MODELS_JSON; add it as the dispatch skill's references/editing-models.md says, then advise again"` 走不到。`row_for_role`（第 1024 行）只有在 `models.py` 抛出以 "no row " 开头的错误时才会返回空；但 `models.py` `session_rows()`（第 238 行）先调用 `_validate_config_shape`，缺 advisor 行时抛出 `InvalidConfig`（"rows: four role rows are required; missing advisor"），于是 `row_for_role` 以 exit 2 返回，第 2060 行 `|| exit 2` 直接退出；而 advisor 在 `ALLOWED_AGENTS` 里，`resolve_session` 的 "no row for" 分支（第 1087 行）永远不会触发。测试 `mmw-v2/tests/dispatch/test_dispatch.sh` `scenario_advise`（第 3225–3242 行）只 grep "missing advisor"，这段文字来自 `models.py`，所以测试通过掩盖了第 2061 行从未执行。删掉后由 `models.py` 的 `InvalidConfig` 承担，剩余风险：用户看到的信息不指向 `editing-models.md`。同一个空返回分支在 `row_for_role` 的另外两个调用处（第 970、1882 行）也走不到，归 dispatch 的审查者判断。
- **轻度过度防御**：第 2068–2069 行 `body="$(cat -- "$packet")" || refuse "could not read the packet file ..."`。前面第 2053 行已确认文件存在，且 packet 是 caller 自己刚写的文件，"存在但不可读"在正常输入下走不到，tracker 和日志里没有触发记录（`advise` 不写事件，这一点无法从 tracker 验证，属于推断）。删掉后如果真发生，advisor 会拿到只有 "Use the advisor skill." 的 prompt，会话会说没有 packet。收益只有两行，优先级很低。
- 第 2054 行对空文件的拒绝保留：这是 caller 用 heredoc 写文件失败时可能真实遇到的情况，代价只有一行，拒绝信息把 agent 指回五项清单。

## 与其他技能的重复或交接问题

- **启动处（与 dispatch 的交接）**：`consulting.md` 用 `<dispatch> advise <file>`，`dispatch.sh` 的 usage、头注释、`case` 分派都有 `advise`（`bash dispatch.sh` 的输出包含 "dispatch.sh advise <packet file>"，已运行确认），两边一致。dispatch 技能的 `SKILL.md` 表格不提 advise，这是对的：caller 从 advisor 技能进入，不需要经过 dispatch 的"moment"表。
- **回答的去向**：runner 边界只有 `start/send/liveness/stop/self`（三个适配器头注释），没有读取会话输出的动词；advisor 会话结束后也没有任何东西去 `stop` 它，Orca 下会留着一个 terminal。前者用户已裁定不修（见 C3），后者是同一裁定的延伸，这里只记录。
- **tool-guard 的交叉影响**：worker 在 `issue-<n>` worktree 里启动的 advisor，其 worktree 名同样是 `issue-<n>`，所以 `tool-guard.py` 会把它当作受管会话：它的提问工具会被拒绝，拒绝信息教的是 "`ABANDON: AC<n> decision` with a sub-issue"，这对 advisor 是错的指引。实际影响很小，因为 `advising.md` `## How to answer` 第 4 条已让 advisor 把缺的信息写进回答而不是提问。只记录，不建议改。
- **术语表**：`docs/contexts/ticket-run/CONTEXT.md` 的 advisor / packet / recommendation 三个词条与 `docs/contexts/night/CONTEXT.md` 的 advise 词条和技能一致，没有冲突。
- **与 `SKILL-SET-REVIEW.md` 的冲突**：前几轮按 `### Redundancy and bloat` 的"去掉后 agent 行为是否改变"删掉了 advising.md 的 stakes 句和 SKILL.md 的 "The two sides are asymmetric on purpose..."。后者的意思两份 reference 各自保留了，不必恢复；前者属于本任务书说的"灵魂"，按 B 恢复。`SKILL-SET-REVIEW.md` 的"These stay"只保护"a reason the agent needs to decide an edge case"，没有覆盖"让 agent 知道这件事有多重要、因此该投入多深"这一类，这是它与本任务书的冲突点。

## 没查到的

- 没有找到任何一次 `dispatch.sh advise` 的真实使用记录：`advise` 不写 ticket 事件，`~/.mmw/logs` 里没有 advisor 字样，当前 Orca terminal 里没有 advisor 会话，tracker 评论里提到 advisor 的都是建设它的票。Nowledge Mem 里有 `dispatch.sh advise` 出现之前通过 Paseo `create_agent` 使用 advisor 的决定记录（例如"此决策由 advisor 确认、主会话采纳"）。所以 B、C 中关于 agent 会怎么做错的判断都是推断，不是观察。
- Nowledge Mem 线程 `claude-code-1f93e920-…`（"Advisor 审核 mmw 流水线规划"）读取超时，没看到当时 advisor 回答是怎么被读取和采纳的。
- 没有运行 `advise` 场景测试，也没有真的启动 advisor 会话（按任务书，只读）。

# manage-agents-md

## 定稿（主 agent 复核）

以下是逐条复核后要落地的改动，取代下文调查员的建议。

**判断**：这个技能的流程太重，而最该有的那句话没有：`AGENTS.md` 会被这个仓库里每个宿主、每个会话整份加载，每一行都被当作事实执行。有了这句，"什么该写、什么不该写"就有了共同的判据。开头那句写好以后，好几处机械的记账和自检可以删掉。有三处改动会推翻你 2026-08-23 在 spec 里定的格式，列在最后请你决定；其余是工程改动。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md`，`# Manage AGENTS.md` 下、"Two situations share one flow" 之前 | An `AGENTS.md` is loaded into every session of every agent that works in this repository, on every host, and each line is obeyed as fact: a wrong or stale line misleads every agent after you, and a line the code already says only thins attention. So the file holds what an agent working here cannot find out by itself before it does damage: what this project is and what is at stake, what must not be touched, what must happen in order, what looks wrong but is deliberate, and where the documents are. | 遇到清单外的事实时（ERP 的"这是一个多仓库文件夹"、agentflow 的机器分工），有了它，agent 能按"会不会在自己发现之前造成损害"来决定写不写。整套 `### What NOT to Add` 也有了共同的依据。 |
| I2 | 调查模板，替换 "Cross-reference with the actual codebase: run the documented commands, …" 中 "run the documented commands" 的部分；`### Checks` 第 347 行 "run each one a file names" 同样改 | Run a command only when running it changes nothing outside a temporary directory: `--help`, a test, a lint, a local build. A command that deploys, publishes, migrates, sends messages or writes to a shared service is verified by reading the script it invokes, never by running it. | 消费仓库是有付费客户的产品，README 里常写着部署、迁移、发布命令。照字面执行的调查 subagent 会把它们真的跑起来。**推断**：没找到发生过的记录；但后果不可撤回，写一句的代价很小。 |
| I3 | `SKILL.md` `## Find your situation` 表后 | The survey and the questions exist to find what the user has not told you. When the user has already said what the file must say, survey only what verifies those facts and ask only what is still missing; the format, `check.sh` and the report stay the same. | 这个技能唯一一次真实使用（2026-09-28，`~/ERP`）里，用户已经说了要写什么，agent 只好自己决定跳过调查和固定问题。有了这句，这条路是技能给的，不是 agent 违规走的。 |
| I4 | `#### 1. Foundational context stays bare, domain guidance gets wrapped` 标题下（恢复 `66089d06`、`e74e0140` 删掉的判据，合并为一段） | Not everything goes in an `<important if>` block. What every task needs (identity, package manager, commands, external references, key conventions, gotchas) stays as plain markdown; wrap only what some tasks reach. | 这个标题现在只有前半句没有正文，agent 不知道包不包的判据，容易全包或全不包。 |
| I5 | 根模板身份占位 `<identity: …>` 末尾 | An agent decides what kind of task it is on, and how careful to be, from these lines. | 写身份行时知道它们的用途。xiaohuangya 提交 `190522b` 的说明记着真实后果：身份过时后，"一个 agent 读完会以为任务是完善那个客户端"。 |

### 删除或简化

| # | 位置与原文 | 处理 | 依据 |
| --- | --- | --- | --- |
| D1 | `SKILL.md` `## The scratch directory` 整节，与两个 `## Set up` 里填 `inputs.md` 的句子 | 删；别家工具的指令文件直接写进 documents 组的 assignment；命令与 `@` 行的去向交给 `destinations.md`；`### Writing rules` 与 `### Steps` 第 4 步里引用 `inputs.md` 的地方改指 `destinations.md` | 同一条命令会落在三份中间文件里；create 情况下三个标题里有两个恒为 `none`。 |
| D2 | `### Collect` 的 Done 句（`fact:`/`evidence:` 逐行配对） | 缩成 "Done when every group has reported ('nothing found' counts) and the entries are merged and sorted by place." | 纯格式配对；每条事实有证据，已由调查模板的格式保证。 |
| D3 | `### Self-check` 整节 | 删；Currency、Actionability 两项并进 `## Prune` 的 Done 句："… no line states an outdated version or count, and no template placeholder or TODO is left." | 六行里四行是别处规则的复述或不可能判"否"的空判据。 |
| D4 | `## Prune` Done 句后半 "and every rule is phrased as the behaviour to perform…" | 删 | 与 `### Writing rules` 第 286 行重复。 |
| D5 | `references/rewrite.md` `### How to apply` 第 2、4、5 步 | 并成一句："A line that matters to one kind of work only gets a `when` value, chosen as `SKILL.md` `### Domain sections` says." | 复述 `### Domain sections` 与根模板。 |
| D6 | `rewrite.md` `### What happens to each old file on disk` 第 2、3、4 行与表后那句 | 删，留第 1、5、6 行 | 由 `### Steps` 第 4、5 步承担；第 2 行是 agentflow 已删光的旧写法。 |
| D7 | `rewrite.md` `inventory.md` 与按行数对账（空行、标题、分隔线也各记一行，`wc -l` 相等） | 改为按规则和命令记账："Done when every rule and every command of every old file has a destination in `destinations.md`." 目标句 "No line is lost without a reason written down." 保留 | 为执行一条规则加了一套程序；`inventory.md` 说是报告的基线，报告却不打印行数。旧文件都在 git 里可以对照。 |
| D8 | `### Writing rules` "List exact external files for setup, architecture…" 与 "Put commands in tables when there is more than one." | 删 | 根模板已画出。 |
| D9 | `### Format` 的五行模板 | 缩成 "Ask the whole set in one message, each question numbered with your recommended answer under it, then wait for the answers." | 与 `grilling` 逐字相同；这里不整份加载 `grilling` 有理由（它是一问接一问），一句话足够。 |
| D10 | `### Nested purpose, one question per directory` 标题 | 改为 "Nested purpose, one table" | 标题与正文矛盾。 |
| D11 | `### Groups` "Topic groups, always these four"、"Directory groups: one per top-level directory…" | 保留四个主题与按目录切分，作为默认切法；目标写成 "every part of the repository is read by someone whose share fits one session"；小仓库可以合并分组；frozen 目录的抽样规则照留 | 三个目录的小仓库也要开七个 subagent；切分的本意（份额装得进一个会话）正文没写。 |
| D12 | `references/create.md` `## Set up` 第 1 步 "If this is not a git repository, stop and tell the user…" | 改为："Work from the repository root (`git rev-parse --show-toplevel`). A folder that is not a git repository still gets its files: its root is the folder the user named, and the history group is left out." | ERP 是非 git 的多仓库文件夹，agent 没有停，照样写出了通过 `check.sh` 的文件；`rewrite.md` 也没有这条停止规则。 |
| D13 | `### What NOT to Add` 的位置 | 移到 `## Write` 开头作为写作标准；`## Prune` 缩成一次通读："read each file as the agent who loads it at the start of every session; cut every line that would not change what that agent does." | 写作标准排在写完之后才读，写一遍、删一遍。真正依赖的顺序（survey → ask → write → `check.sh`）不动。 |

### 已定（2026-09-28）：三处格式改动都采纳，取代 2026-08-23 spec 里的对应格式

1. **嵌套文件的门槛。** 现在的规则是：一个目录只要有一条规则，就建一对嵌套文件。你在 agentflow（`812e39309`）和 xiaohuangya（`190522b`）里都手工删光过，理由是"跟着代码漂移、无人复核"。提议改为：
   > A nested file is one more file that drifts as the code under it changes, and nothing reminds anyone to update it. A directory earns one when an agent working there would break something it would not notice; a rule the agent would learn from the first error or the first file it opens stays out, and a rule for one kind of work can be a domain section in the root instead.
2. **段落标题固定用英文。** 现在的规则是标题随仓库语言翻译。`code-checkers` 和 `setup-matt-pocock-skills` 按 `## Commands`、`## External References`、`## Key Conventions` 往文件里加行。标题一旦翻译，`setup-matt-pocock-skills` 就会再建一个英文的 `## External References`，文件里出现两节。提议：
   > Other skills add rows under `## Commands`, `## External References` and `## Key Conventions` by those headings, so the headings stay in English as written; the lines under them are in the repository's language.
3. **放开两处固定格式。**
   - 根文件允许在固定几节之外，为"每个任务都需要、模板里又没有位置"的一类事实加一节。三个真实文件都需要这样的一节：ERP 的仓库表、agentflow 的机器分工、xiaohuangya 的"这个仓库现在是什么"。点名禁止的几样（目录图、环境变量、技能清单等）保留。
   - 11 个固定问题改为一张覆盖清单：调查已有证据答实的问题，改成确认一行；一个回答引出文件需要的新事实时，允许追问一句。"一轮问完、每题带推荐答案"的形式保留。

### 不采纳

- `## Write` 那句的理由补句（"a line without evidence is a guess that every later agent will obey as fact"）：I1 已经说了"每一行都被当作事实执行"。

## 结论

体量：`mmw-v2/skills/manage-agents-md/SKILL.md` 3,932 词、`references/rewrite.md` 944 词、`references/create.md` 215 词，合计 5,091 词；脚本只有 `scripts/check.sh` 110 行。主要问题有三个。第一，流程过重：四个固定主题组加每个顶层目录一组的调查、12 个固定问题、改写时逐行记账（空行、标题也要记），外加 `inputs.md`、`inventory.md`、`destinations.md`、`survey-list.md` 四份中间文件，其中有几份互相重复。第二，真实使用证据显示这套流程几乎没被完整跑过。唯一一次真实加载（2026-09-28，`~/ERP`）里，agent 明说"没有照搬完整流程……只用了它的文件格式和检查脚本"。两个主要消费仓库（agentflow、xiaohuangya）是用户手工把嵌套文件全删、并成根文件一份的，而技能的规定正好相反：一个目录只要有一条规则就建一对嵌套文件。第三，"灵魂"不完整：技能开头只有分流，没有说明 `AGENTS.md` 每个会话都会整份加载、错一行就误导所有 agent；调查模板要求 "run the documented commands"，却没有交代哪些命令不能跑。估计能删约 650–750 词（约 13–15%）而不丢功能，同时要补约 250 词的思想性文字。脚本本身很精简，没有实质性的过度防御。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
|---|---|---|---|---|---|
| A1 | `SKILL.md` `## The scratch directory`（第 27–40 行，"`inputs.md` in the scratch directory has three headings"），以及 `references/create.md` `## Set up` 第 3 步、`references/rewrite.md` `## Set up` 第 3 步 | 4、6 | create 情况下三个标题里有两个恒为 `none`（create.md 第 9 行 "The other two headings say `none` in this situation"）。rewrite 情况下，命令和 `@` 行先记进 `inputs.md`，到 `## Migrate` 又要逐行记进 `destinations.md`，其中保留的再追加进 `survey-list.md`：同一条命令落在三份文件里。`inputs.md` 第一个标题只有一个用处，就是把别家工具的指令文件列给 documents 组 | 别家工具的文件（`.cursor/rules/` 等）直接写进 documents 组的 assignment。命令和 `@` 行的去向交给 `destinations.md`：根 `CLAUDE.md` 的 `@` 行记作 `CLAUDE.md`，"可从 `--help` 看出含义"的命令记作 `removed: discoverable`。剩余风险：无，报告里 "dropped as discoverable (<count>)" 改从 `destinations.md` 计数 | 删掉 `## The scratch directory` 整节和两个 Set up 里填 `inputs.md` 的句子；`### Writing rules` 第 282 行 "stays in `inputs.md`" 和 `### Steps` 第 4 步里引用 `inputs.md` 的地方改指 `destinations.md` |
| A2 | `SKILL.md` `### Collect` 的 Done 句（第 98 行，"every `- fact:` line in `survey-list.md` is followed by its own `  evidence:` line … read the file top to bottom and name every line on either side that has no partner"） | 1、4 | 这是纯机械的格式配对检查，而文件是同一个 agent 刚刚合并出来的。它守的真正规则是"每条事实都有证据"，这条已经由调查模板的报告格式（第 81–82 行）和 `## Write` 的 "Each line you write comes from one entry" 承担 | 调查模板里 `evidence:` 是必填字段；写手只从条目写。剩余风险：一条缺证据的条目被写进文件，`## Prune` 读文件时会看到 | Done 句缩成 "Done when every group has reported ('nothing found' counts) and the entries are merged and sorted by place." |
| A3 | `SKILL.md` `### Self-check` 整节（第 318–329 行，"Answer each for the file in front of you"） | 4、6 | 六行里有四行是在复述已有规则："Commands" 行复述 `### Writing rules` 的命令规则，"Single source" 行复述 `### What NOT to Add` 第 12 条和 `### Nested template` 第 241 行 "A nested file says only what differs from the root"；"Orientation"（"let an agent find where things live?"）和 "Non-obvious patterns"（"Are gotchas and quirks documented?"）写得太宽，几乎不可能判"否"，按 `SKILL-SET-REVIEW.md` `### Scripts and judgement` "A check … that cannot fail proves nothing"，这两行应删 | 其余规则在 `### Writing rules` 和 `### What NOT to Add` 里，只剩 "Currency"（版本、计数不过时）和 "Actionability"（不留模板占位、不留 TODO）没有别处承担 | 删掉整张表和它的引导段；把 Currency、Actionability 并进 `## Prune` 的 Done 句："… no line states an outdated version or count, and no template placeholder or TODO is left." |
| A4 | `SKILL.md` `## Prune` 的 Done 句后半（第 331 行，"and every rule is phrased as the behaviour to perform or, where a prohibition had to stay, sits next to its positive target"） | 6 | 与 `### Writing rules` 第 286 行 "State each rule as the behaviour to perform…" 几乎逐字重复 | `### Writing rules` 保留的那一份 | 删后半句 |
| A5 | `references/rewrite.md` `### How to apply` 第 2、4、5 步（"Extract the package manager…"、"Break apart rules — split any list of rules into individual `<important if>` blocks…"、"Wrap domain sections — releasing, deploying…"） | 6、2 | 第 4、5 步复述的是 `SKILL.md` `### Domain sections` 的 §1、§2（何时包、条件要窄，连 Bad/Good 的意思都一样）；第 2 步 "condense to one or two lines" 在根模板 `## Package Manager` 占位里已经写了 | `SKILL.md` `### Domain sections`；migrate 时只需给行分配 `when` 值 | 三步并成一句："A line that matters to one kind of work only gets a `when` value, chosen as `SKILL.md` `### Domain sections` says." |
| A6 | `references/rewrite.md` `### What happens to each old file on disk` 第 2、3、4 行，以及表后那句 "A nested file survives only on entries whose place is that directory." | 6、5 | 第 3 行（嵌套 `CLAUDE.md` 改成 `@AGENTS.md`）已由 `SKILL.md` `### Steps` 第 5 步 "The `CLAUDE.md` beside it holds the one line `@AGENTS.md`, replacing whatever was there" 承担；第 4 行（根 `CLAUDE.md` 保留所有 import）已由第 4 步承担；表后那句已由第 5 步 "from the entries whose place is that directory" 承担。第 2 行（"Nested `AGENTS.md` whose only content says 'read the override'"）是 agentflow 特有的写法：agentflow 已在 2026-08-26 用提交 `812e39309` 删光全部 override，xiaohuangya 已在 2026-09-07 用提交 `190522b` 删光 40 份。触发过吗？没有找到记录。正常输入能走到吗？只有照抄 agentflow 旧写法的仓库才会 | 第 1 行（override 迁移后删除）照留，它就能覆盖第 2 行：那个嵌套文件的唯一一行按 "removed" 处理，再从 survey list 重写 | 删第 2、3、4 行和表后那句，留第 1、5、6 行 |
| A7 | `references/rewrite.md` `## Set up` 第 2 步（`inventory.md`，"piped through `xargs wc -l` … This is the migration's input and the final report's baseline"），`### Two lists for the report` 之前的 `destinations.md` 记账规则里的 "`blank` for an empty line; a heading, a table rule, or a code fence is `removed: markup`"，以及文件末尾 Done 句（"`wc -l` of the old file equals the number of `destinations.md` lines that start with its path"） | 4、1 | "No line is lost without a reason written down" 这个目标，被落实成了行数相等的机械对账。为了让行数对上，空行、标题、表格分隔线也各记一行。`inventory.md` 说是 "the final report's baseline"，但 `SKILL.md` `### Report` 的 rewrite 模板根本不打印行数，所以这个"基线"没有任何读者 | 目标保留，改成按规则和命令记账："every rule and every command of every old file has a destination"。旧文件都在 git 里，`git show HEAD:<file>` 就能对照。剩余风险：一条既不是规则也不是命令的散文行被默默丢掉；这类行多数本来就在 `### What NOT to Add` 第 10、11 条的删除范围内。如果仍想保留机械对账，就写成一个 20 行的脚本，文本里不再描述 | 删 `inventory.md`；Done 句改成 "Done when every rule and every command in each old file has a line in `destinations.md`, and every line with a section destination is an entry in `survey-list.md`." |
| A8 | `SKILL.md` `### Writing rules` 第 281 行 "List exact external files for setup, architecture…" 和第 283 行 "Put commands in tables when there is more than one." | 6 | 根模板已经把两者画出来了：`## External References` 占位写着 "<setup, architecture, API, security, release, policy>"，`## Commands` 本身就是表格。documents 组的 assignment 也已点名同一串文档类别 | 根模板 | 删这两条 |
| A9 | `SKILL.md` `### Format`（第 106–116 行，"Ask the whole set in one message… ❓ **Q1** …"） | 6 | 与 `mmw-v2/upstream/skills/productivity/grilling/SKILL.md` 第 13–15 行逐字相同。之所以保留副本，是因为原 spec 决定"不引用任何外部技能"：整份加载 grilling 会带进它"一问接一问"的行为，和本技能"一轮问完"冲突。所以副本本身说得通，但五行的模板写成一句就够了 | 一句文字 | 缩成 "Ask the whole set in one message, each question numbered with your recommended answer under it, then wait for the answers." |
| A10 | `SKILL.md` `### Nested purpose, one question per directory`（第 137 行标题） | 其他（标题与正文矛盾） | 标题说 "one question per directory"，正文却是 "Ask about every directory that earns a pair in one question: a table with one row per directory" | — | 标题改成 "Nested purpose, one table" |

以上合计约 650–750 词。A1、A7 两项最大，各约 150 词。

## B. 灵魂

### 保留，勿删

- `SKILL.md` `## Survey` 第 44 行（"You are collecting the facts the `AGENTS.md` files will be written from. Everything that ends up in a file traces back to an entry…"）：告诉 agent，调查的产出就是整个写作的依据。
- `SKILL.md` `## Ask the user` 第 102 行（"The survey list holds what the repository shows. Four things it cannot show…"）：说明为什么必须问人、问的是什么、为什么附推荐答案（"so the user confirms or corrects instead of composing"）。这是整个提问环节的理由。
- 调查模板第 70 行（"You report facts with evidence; you do not write the AGENTS.md and you do not judge style."）和第 91 行（"When two parts of the repository do the same thing differently, report both … the user decides."）：给调查 subagent 划了分工，事实去查，决定交给人。
- 调查模板第 89 行里对 defect 的定义（"a defect is reported, never written into an AGENTS.md"）：把"发现坏东西"和"写成规则"分开，防止把仓库里的缺陷固化成指令。
- `SKILL.md` `### Root template` 第 203 行（convention 与 gotcha 的对照例子）：这是 agent 最容易分错的地方，给了一对对照例子。
- `SKILL.md` 第 205 行（"Hosts that load nested files on their own lose nothing by the last line; hosts that stop at the working directory depend on it."）：一句话说明那句子目录提示为什么不能省。
- `SKILL.md` `### Code and test rules` 第 211 行里的理由（"The reviewer's Standards and Tests axes read those two files, and a worker gets the rules it needs through the spec and the ticket."）：没有这句，agent 会觉得把代码规则挪出 `AGENTS.md` 是多此一举，按 `SKILL-SET-REVIEW.md` 属于 "a reason … to keep a design choice it would otherwise simplify away"。
- `SKILL.md` 第 241 行（"the nested file is already scoped, so it carries no domain sections … keep narrower files shorter than root files"）。
- `SKILL.md` `### Domain sections` §2 的 Bad/Good 对照。
- `SKILL.md` `### Writing rules` 第 285 行（"The one rationale that does is the reason behind a deliberate unconventional choice: it stops the next agent from 'fixing' it."）。
- `SKILL.md` `### Pointers` 第 290 行（"their wording, not the file behind them, decides whether an agent reaches the file"）。
- `SKILL.md` `### What NOT to Add` 第 2 条（"LLMs are in-context learners — if your codebase consistently uses a pattern, the agent will follow it after a few searches."）：这是整套删减标准的根据。
- `references/rewrite.md` `## Migrate` 第 17 行（"No line is lost without a reason written down."）：这是改写的目标本身。A7 只减轻落实它的记账方式，这句要留。
- `references/create.md` 第 8 行 "Survey reports and the user's answers go there, never into the repository."

### 缺口与补充草稿

- **`SKILL.md` 开头（`# Manage AGENTS.md` 下、"Two situations share one flow" 之前）：缺少这件事的意义。** 现在第一句就是分流。agent 不知道这份文件会被每个宿主的每个会话整份加载，也不知道一行错误会被之后所有 agent 当成事实执行，于是只能照清单填空。遇到清单外的事实（ERP 的"这是多仓库文件夹"、agentflow 的 "Machines"），它就不知道该不该写、写在哪。
  > An `AGENTS.md` is loaded into every session of every agent that works in this repository, on every host. Each line is paid for in every task and obeyed as fact: a wrong or stale line misleads every agent after you, and a line the code already says only thins attention. The file is for what an agent working here cannot find out by itself before it does damage: what this project is and what is at stake, what must not be touched, what must happen in order, what looks wrong but is deliberate, and where the documents are. The survey finds what the repository shows; the questions get what only the user knows; everything else stays out.

- **调查模板第 77 行（"run the documented commands"）和 `### Checks` 第 347 行（"run each one a file names"）：缺少"哪些命令不能跑"的判断。** MMW 的消费仓库是有付费客户的商用产品，README 里常写着部署、迁移、发布命令（agentflow 有 cloud-ops 技能和迁移流程）。一个照字面执行的调查 subagent 可能真的把它们跑起来。这一点是推断，我没有找到发生过的记录。
  > Run a command only when running it changes nothing outside a temporary directory: `--help`, a test, a lint, a local build. A command that deploys, publishes, migrates, sends messages or writes to a shared service is verified by reading the script it invokes, never by running it.

- **`SKILL.md` `## Find your situation` 表后：缺少"用户已经定了内容"时怎么办。** 2026-09-28 的 ERP 会话里，用户说"在 agents.md 里写清楚这个文件夹是一个多仓库文件夹……不要去规定死工作流程"。agent 只好自己判断跳过调查和 12 问，技能本身没给它这条路。
  > The survey and the questions exist to find what the user has not told you. When the user has already said what the file must say, survey only what verifies those facts and ask only what is still missing; the format, `check.sh` and the report stay the same.

- **`SKILL.md` `#### 1. Foundational context stays bare, domain guidance gets wrapped`：标题的前半句现在没有正文。** 2026-09-23 提交 `66089d06` 删掉了 "Not everything should be in an `<important if>` block…" 那一段；更早，2026-09-22 提交 `e74e0140` 删掉了 "This is onboarding context the agent always needs." 和 "The rule: inline what every task needs, and wrap what only some tasks reach."。结果是 agent 不知道包块的判断标准，容易把整个文件都包起来，或者一个都不包。建议恢复（原文稍作合并）：
  > Not everything goes in an `<important if>` block. What every task needs (identity, package manager, commands, external references, key conventions, gotchas) stays as plain markdown: it is onboarding context the agent always needs. The rule: inline what every task needs, and wrap what only some tasks reach.

- **`SKILL.md` `## Write` 第 149 行（"an idea with no entry is not written"）：只给了规则，没给理由。** 缺了理由，agent 容易把"条目可追溯"当成官僚手续，顺手补一句"显然正确"的话进去。
  > … an idea with no entry is not written: a line without evidence is a guess that every later agent will obey as fact.

- **根模板身份占位（第 170 行 `<identity: …>`）：没说身份行为什么重要。** xiaohuangya 提交 `190522b` 的说明写得很清楚：身份过时后，"一个 agent 读完会以为任务是完善那个客户端"。
  > (附在占位说明末尾) An agent decides what kind of task it is on, and how careful to be, from these lines.

- **`### Nested purpose` 或 `### Steps` 第 1 步：缺少"嵌套文件的代价"。** 技能门槛是有一条 command、convention 或 gotcha 就建一对（第 139 行）。但用户在两个消费仓库里都手工撤掉了嵌套文件，理由是"嵌套治理文档太细碎，跟着代码漂移"（agentflow `812e39309`）、"跟着代码漂移……已经无人守、无人复核"（xiaohuangya `190522b`）。技能对这种代价一字未提，照现在的门槛在大仓库里会重新造出几十对嵌套文件。草稿（**改变 2026-08-23 spec 里用户定的"哪怕只有一条就建"，需用户确认**）：
  > A nested file is one more file that drifts as the code under it changes, and nothing reminds anyone to update it. A directory earns one when an agent working there would break something it would not notice; a rule the agent would learn from the first error or the first file it opens stays out, and a rule for one kind of work can be a domain section in the root instead.

- **`### Language`（第 153 行 "Translate the section headings of the templates"）：没说谁还会写这些文件。** `code-checkers` `SKILL.md` 第 8 步按 `## Commands`、`## Key Conventions` 找位置；`setup-matt-pocock-skills` `SKILL.md` 第 74 行按 `## External References` 加行，"creating the file or the section when it does not exist"。标题一旦翻译（ERP 的 `## 参考文件`、xiaohuangya 的 `## 外部参考`），setup 就会再建一个英文的 `## External References`，文件里出现两节。草稿（**改变 spec 里"段名随之翻译"的决定，需用户确认**）：
  > Other skills add rows under `## Commands`, `## External References` and `## Key Conventions` by those headings, so the headings stay in English as written; the lines under them are in the repository's language.

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
|---|---|---|---|
| C1 | `SKILL.md` `### Groups`（"Topic groups, always these four"；"Directory groups: one per top-level directory holding code…"） | 不管仓库大小，至少开 4 个加 N 个 subagent。一个三个目录的小库也要开七个。分组方式的本意是让每个调查员的份额装得进它的上下文（原 spec 用户故事 13），这个目的正文没写 | 保留四个主题和目录切分，作为默认切法；目标写成 "every part of the repository is read by someone whose share fits one session"。小仓库可以合并分组，frozen 目录的抽样规则照留 |
| C2 | `SKILL.md` `## Ask the user` 第 104 行（"This is one round: the questions are fixed, there is no follow-up tree, and nothing else is asked here."） | 调查已有确证的问题照样要问。回答里冒出文件必需的新事实也不许追问（比如用户说"有两台机器"，却不能问两台各跑什么）。ERP 会话的 agent 把这称为"再问你 11 个固定问题"，并绕开了。**这是 2026-08-23 spec 第四节里用户定的"问题集固定，不做设计树"** | 把 11 问当作覆盖清单：调查已用证据答实的问题，改成"确认"一行；一个回答引出文件需要的事实，就追问一句，但不展开设计讨论。"一轮问完、带推荐答案"的形式保留 |
| C3 | `references/rewrite.md` 逐行记账（见 A7） | 为了守"不丢一行"，每一个空行、每一条分隔线都要记一行，再用 `wc -l` 对账，属于"为执行一条规则又加一套程序" | 按规则和命令记账（A7）。目标句 "No line is lost without a reason written down" 保留 |
| C4 | `references/create.md` `## Set up` 第 1 步（"If this is not a git repository, stop and tell the user…"） | git 只在两处用到：解析根目录和 history 组。2026-09-28 的 ERP（非 git 的多仓库文件夹）就是这种情况，agent 没有停，照样写出了通过 `check.sh` 的文件。另外，`rewrite.md` 没有这条停止规则，两个情况的做法不一致 | "Work from the repository root (`git rev-parse --show-toplevel`). A folder that is not a git repository still gets its files: its root is the folder the user named, and the history group is left out." |
| C5 | `SKILL.md` 第 207 行（"A root file carries only the sections above"） | 三个真实文件都需要模板外的一节：ERP 加了 `## 仓库`（多仓库表），agentflow 有 `## Machines`、`## Products and code names`，xiaohuangya 有 `## 这个仓库现在是什么`、`## 机器`。封闭的段落集合，逼着 agent 要么硬塞进 Key Conventions，要么违反模板 | 把点名禁止的几样（目录图、环境变量、已装技能清单、提交署名、元数据头、嵌套文件索引）留下，因为它们各有理由；另加 "A class of facts every task needs that no section above holds gets one section of its own." **这会松动 description 里的 "one fixed format"，需用户确认** |
| C6 | `## Write` 与 `## Prune` 的"先写后删"两遍 | `### What NOT to Add` 是写作标准，却排在写完之后才读；rewrite 的 Migrate 第 7 步又要提前引用它。写一遍删一遍，比带着标准写一遍多做一轮 | 把 `### What NOT to Add` 移到 `## Write` 开头作为写作标准；`## Prune` 缩成一次通读："read each file as the agent who loads it at the start of every session; cut every line that would not change what that agent does." 真正依赖顺序的只有 survey → ask → write → check.sh，这个顺序要留 |

## 脚本

`scripts/check.sh`（110 行）总体精简，六项检查都有测试覆盖（`mmw-v2/tests/manage-agents-md/test_check.sh`，17 个用例），没有死代码，也没有为想象中的并发或文件损坏写的恢复逻辑。具体几点：

- **注释编号是历史残留（类别 3）**：第 44、59、63、68、87、92 行的 `# 6.`、`# 1.`、`# 5.`、`# 2.`、`# 4.`、`# 3.` 乱序。原因是原来有一行注释 "(Checks are numbered as in the skill's references/verify.md, not in file order.)"，`verify.md` 在 `66089d06` 里并进 `SKILL.md` 时这行注释被删了，编号现在不对应任何东西。去掉编号即可。
- **没有 `--help`**：`bash check.sh --help` 会把 `--help` 当成目录去 `cd`，直接报错。用法只写在头部注释里（第 8–10 行）。技能文本已经给出三条完整命令，影响很小；修不修都行。
- **路径检查有真实的误报，但这不属于过度防御**：在本仓库只读运行 `check.sh .`，报出三条：`docs/research/code-landing-refs/ponytail/CLAUDE.md: missing`、`…/swarm-forge/CLAUDE.md: missing`（第三方快照目录，本仓 `AGENTS.md` 说明它们只读），以及 ``path `str/includes?` does not exist``（一个带斜杠的函数名，不是路径）。`SKILL.md` `### Checks` 第 345 行 "A failure this repository cannot satisfy is a pass; write its cause down" 覆盖了这些情况，这句话有真实用处，要留。
- `[ -n "$f" ] &&`、`[ -n "$agents" ] || continue`、`[ -n "$tok" ] || continue` 这三处空行保护按理走不到，但每处只有一行、没有成本，不建议为此改动。

## 与其他技能的重复或交接问题

- **段名翻译会打断两个下游写入方**（详见 B 的最后一条）：`mmw-v2/skills/code-checkers/SKILL.md` 第 8 步和 `mmw-v2/upstream/skills/engineering/setup-matt-pocock-skills/SKILL.md` 第 74 行都按英文段名 `## Commands`、`## External References` 写入。应该留在 manage-agents-md 这一边改：段名保持英文。下游两个技能不用改。
- **`CLAUDE.md` 只放 `@` 行的规则写了两份**：`SKILL.md` `### Steps` 第 4、5 步，以及 `setup-matt-pocock-skills/SKILL.md` 第 76 行。后者是本仓对上游的改写，`mmw-v2/merge-notes/setup-matt-pocock-skills.md` 第 22 行登记了理由。两边的 agent 各在自己动手的那一刻需要这条规则，两份都该留。
- **问题格式与 `grilling` 重复**（A9）：留本技能的一句话版本，不引用 grilling。
- **`retro` 的 `repository-agents` 去向**（`mmw-v2/skills/retro/SKILL.md` 第 184 行）会往消费仓库的 `AGENTS.md` 加行，但没提这套格式（哪一节、要不要包 `<important if>`）。这里只作记录；该补的在 retro 那边，写一句 "in the section its type belongs to, as the `manage-agents-md` skill's format has it" 即可。
- `docs/contexts/toolbox/CONTEXT.md` 第 81–82 行的词条与技能一致，没有问题。

## 没查到的

- 没有读原 spec 引用的四份外部参考（humanlayer、sentry、anthropic、mattpocock）的当前版本。`### What NOT to Add`、`### Domain sections`、`references/rewrite.md` `### How to apply` 是从它们抄来的，我只凭 spec（`git show 3a418c08:docs/specs/manage-agents-md/spec.md`，现已不在 HEAD）的来源表判断出处。
- "技能从未在消费仓库完整跑过"是根据以下材料推断的，没有证明：`~/.claude/projects` 里所有含 `survey-list.md` 或 `manage-agents-md` 的会话（真实加载只有 ERP 2026-09-28 一次，而且没走完整流程；agentflow 2026-09-11 那次只跑了 `check.sh`）；`~/.codex/sessions` 里命中的几个会话（都是在读 MMW，不是在跑这个技能）；tracker 里 20 张相关 issue（全是维护技能文本的票）。`~/.grok/sessions` 的两处命中没有打开，`~/.pi` 没有命中。
- "调查 subagent 可能执行部署或迁移命令"是推断，没有找到发生过的记录。
- `test_check.sh` 只读了，没有运行（任务书说不需要）。

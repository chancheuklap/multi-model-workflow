# R20a pstack 的文本结构：按组件类型的可执行规则

这份文件把 pstack 的文本结构风格写成一组可以逐条照做、逐条检查的规则，供 MMW 架构升级时重排技能文本用。读者是两类：写 `R20-writing-style-guide.md` 与范本的 agent，和之后按票搬文字、写新文字的 worker 与 reviewer。它只管「结构」：一份文件有哪些节、按什么顺序、每节装什么、标题用几级、句子是什么形状、怎样引用别的组件。句子里要装多少理由、讲到多深，是 mattpocock 写作规则一侧的事（`mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `## What skill text is for` 第 1、4 条），本文遇到两者冲突时在第 10 节列出，不在这里裁决。

**出处与标注约定。**

- pstack 快照在 `docs/research/code-landing-refs/pstack/`（cursor/plugins b0b9c7a0，`.cursor-plugin/plugin.json` `"version": "0.15.4"`）。下文不带前缀的路径都相对 `docs/research/code-landing-refs/pstack/skills/`；「mode」指 `poteto-mode/SKILL.md`，「playbook」指 `poteto-mode/playbooks/<file>.md`。
- 行号是本轮用 `cat -n` 读原文得到的。
- 「原文」：pstack 文件里写明的规则或可见的写法。「统计」：本轮用 `grep`、`wc` 在快照里数出来的数。「推断」：原文没有直说，由写法归纳出的判断。「建议」：给 MMW 的工程决定，附理由。
- L7 指 `docs/research/workflow-compare/reports/L7-pstack-component-contract.md`；本文第 1–8 节细化它的第 A 节，第 9 节补充它的第 E 节。

**本轮读了什么。** 全文读过：mode；playbook `bug-fix`、`feature`、`investigation`、`refactoring`、`authoring-a-skill`、`orchestrate`、`opening-a-pr`、`babysit`、`pause-safely`、`worktree-cleanup`，`multi-phase-plan` 前 40 行；能力技能 `how`、`arena`、`tdd`、`bro`、`blast-radius`、`unslop`、`show-me-your-work`、`figure-it-out`、`teach`、`interrogate`、`reflect`、`no-comments`，`why`、`swarm`、`architect`、`typescript-best-practices`、`recall` 的开头与小节表；原则 `attack-the-premise`、`prove-it-works`、`guard-the-context-window`、`encode-lessons-in-structure`、`build-the-lever`、`laziness-protocol`、`never-block-on-the-human`、`model-the-domain`，其余 15 条只用 `grep` 统计了标签、行数和 description 开头；reference `how/references/explorer-prompt.md`、`explainer-prompt.md`、`interrogate/references/reviewer-prompt.md`、`architect/references/runner-prompt.md`、`why/references/sources/slack.md`，其余 reference 只读了开头 5 行；`agents/poteto-agent.md`、`agents/comment-sicko.md` 全文；脚本 `check-plan.mjs`、`worktree-audit.sh`、`log.sh` 的头部。没读的 playbook（`autopilot-full`、`autopilot-stack`、`shipping`、`eval`、`hillclimb`、`perf-issue`、`prototype`、`runtime-forensics`、`trace-forensics`、`session-pickup`、`visual-parity`、`autonomous-run`）只参与了第 3 节的骨架统计。

---

## 0. 结论（先读这里）

1. pstack 的结构统一靠四件事：每类组件有固定的起始标题层级（mode H1+H2、playbook H3+H4、能力技能 H1+H2、原则 H1 加粗体段首标签）；每类组件有固定的首行与末行（playbook 首行 `### <Name>`、次行所有权句、末行 `**Reply:**`）；句子是一句一事的短陈述句或祈使句；引用别的组件只点名，不复述。第 1 节是跨类型的通用规则，第 2–8 节按类型写。
2. 统一程度最高的是 playbook 与原则：23 份 playbook 里 22 份有同样的首行、所有权行和 Reply 行（统计，第 3 节）；23 条原则的 frontmatter 完全同构，description 全部以 "Apply" 开头（统计，第 5 节）。统一程度最低的是能力技能的小节命名（步骤标题有四种标点、收尾小节有七种名字）和 reference 的提示模板（三种形状）。MMW 照搬时，按 pstack 的高频形态定一种写法，不照搬它的变体（第 9 节）。
3. pstack 至少有五处结构写法与 MMW 现行规则冲突，照搬前要按 MMW 规则改写：frontmatter 只许 `name` 与 `description`；description 只写触发；跨组件按标题引用、不按步骤编号；技能文本不点宿主、工具和模型名；每个步骤要有完成判据（第 10 节）。
4. 第 11 节列出其中能由结构 lint 机械检查的规则，供 `R21-text-integrity-checks.md` 取用。

---

## 1. 通用规则（所有组件都适用）

### G1 标题层级按组件类型固定，不按内容长短变化

| 组件 | 起始标题 | 下一级 | 再下一级 |
|---|---|---|---|
| mode | `# <Name> mode` | `## <Section>` | 小节内用粗体段首标签，不再加标题 |
| playbook | `### <Name>`（文件里没有 H1、H2） | `#### <Cluster>`（只在长 playbook） | 无 |
| 能力技能 | `# <Name>` | `## <Step/Phase/Section>` | `### <Sub>`（少用） |
| 原则 | `# <Name>` | 无；小节用 `**Label:**` 粗体段首标签 | 无 |
| reference | `# <Name>` | `## <Section>` | `### <Output section>`（提示模板的输出格式） |

实例：
- mode 第 11 行 `# Poteto mode`，第 13、37、79、89、97、111、115 行七个 `##`，`## Principles` 里的分组用粗体 `**Core**`（第 41 行）而不是 `###`。
- `bug-fix.md` 第 1 行 `### Bug fix`、`orchestrate.md` 第 1 行 `### Orchestrate`，后者的规则簇是 `#### Roles and placement`（第 13 行）、`#### Steps`（第 58 行）。统计：23 份 playbook 首行都是 `### `，只有 `orchestrate.md` 有 `####`（9 个）。
- 原则：`principle-attack-the-premise/SKILL.md` 第 7 行 `# Attack the Premise`，小节是第 11 行 `**Why:**`、第 13 行 `**Pattern:**`、第 19 行 `**Stop:**`；统计：23 条原则只有 `principle-prove-it-works` 用了 `##`（第 18 行 `## Script the check when you can`）。
- reference：`how/references/explorer-prompt.md` 第 1 行 `# Explorer Prompt Template`、第 11 行 `## Question`、第 36 行 `### Components Found`。

推断：playbook 用 H3，是因为它原本是 mode `## Playbooks` 下的小节（L7 A.2、F.3）。MMW 的 playbook 同样由 mode 路由、抄进 todo，保留 H3 能让「playbook 是 mode 的一部分」在层级上可见（建议）。

### G2 一句一事，句号结尾，短陈述句或第二人称祈使句

规则原文：mode 第 101 行 "**Short declarative sentences.** One thought per sentence, ended with a period."；`unslop/SKILL.md` 第 62 行规则 28 "One idea per sentence."

实例：
- `bug-fix.md` 第 5 行 "Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship."
- `pause-safely.md` 第 5 行 "Stop at a safe boundary. Finish the current atomic step or back out of it. Start nothing new, and cancel any nested subagents."
- `arena/SKILL.md` 第 9 行 "Fan out N parallel attempts at the same task. Read every candidate end to end. Pick the strongest as the base."

### G3 禁令、定义与区分用固定句式

三种句式反复出现，承担「划界」：

- **「X is not Y」定义句**，用来否定一个常见的错误等同。实例：`worktree-cleanup.md` 第 6 行 "The bucket is advice, not permission."；`orchestrate.md` 第 89 行 "CI green is an input to a verdict, not a verdict."；`refactoring.md` 第 7 行 "Type check and lint are not a pin."；`babysit.md` 第 23 行 "Owner approval is a wait, not a blocker to fix."
- **Never / Only / No 开头的禁令**，一句只禁一件事。实例：`babysit.md` 第 10 行 "No base retarget, rebase, stack-wide submit, or force-push from inside a babysit."；`orchestrate.md` 第 70 行 "Never deep-review inline." 与 "Never review a diff inside a drain."；`refactoring.md` 第 11 行 "No compatibility shims, no parallel old-and-new paths."
- **「Distinct from X, which …」区分句**，说明与相邻组件的分界，放在所有权行、首段或文件末尾。实例：`refactoring.md` 第 3 行 "Distinct from Feature, which adds behavior, and Bug fix, which corrects it."；mode 第 124 行 Hillclimb 行 "Distinct from Perf issue, which is a one-off fix."；`principle-attack-the-premise/SKILL.md` 第 23 行 "This principle is distinct from [Redesign from First Principles](...), which rebuilds a design around a new requirement."

### G4 规则的理由紧跟在规则后面，同一句或下一句

实例：
- `reflect/SKILL.md` 第 31 行 "agent mode (`readonly: false`). Reviewers need MCP access ... Readonly strips MCPs."
- `worktree-cleanup.md` 第 8 行 "Show the diff and get a decision first, since removing a clean worktree is recoverable from its branch but uncommitted work is gone."
- `refactoring.md` 第 11 行 "Spot-check every rename against the actual files. Renames silently miss usages in strings, prose, and back-references."
- `orchestrate.md` 第 63 行 "Spawn a rolling window of workers ... Blocking batches pay the slowest child of every batch."

理由不另开一节，也不放在文件末尾。注意：pstack 自己对「写不写理由」的政策与 MMW 不同（第 10 节 C6）。

### G5 粗体段首标签以句号结束，后面接新内容

规则原文：`unslop/SKILL.md` 第 39 行规则 16 "A bold lead-in that ends in a period, names the item, and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one file.") is fine"；mode 第 102 行 "a bold section header as its own sentence ("**Verification.** End to end via CDP")"。

实例：
- `opening-a-pr.md` 第 5、7、9、11、13 行 `**Worktree.**`、`**Commits.**`、`**PRs.**`、`**Titles.**`、`**Descriptions.**`。
- mode 第 81、83、87 行 `**Just do it.**`、`**Always pause** for …`、`**No is an acceptable answer.**`。
- `multi-phase-plan.md` 第 13、15 行 `**Verification.**`、`**Control skill.**`。
- 长 playbook 的步骤首句加粗，同样以句号结束：`babysit.md` 第 7 行 "1. **Declare the mode and resolve the forge before any poll.**"，`orchestrate.md` 第 60 行 "1. **Frame.**"。

例外：原则的小节标签以冒号结束（`**Why:**`、`**Pattern:**`），见第 5 节。

### G6 不用长破折号，不用句中冒号；冒号只放在列表或示例之前

规则原文：mode 第 102 行 "**No long-dash character anywhere.**"、第 103 行 "**A colon as a mid-sentence connector is also out** (unslop rule 14). A colon before a list is fine."；`unslop/SKILL.md` 第 36 行规则 13、第 37 行规则 14。

合规实例：mode 第 17 行 "Remaining triggers:" 后接列表；`interrogate/SKILL.md` 第 15 行 "Identify what to review from context:" 后接列表。pstack 自己的违反见第 9 节 P9。

### G7 引用别的组件：点名，不复述

规则原文：`authoring-a-skill.md` 第 10 行 "Delegate to other skills by path. Don't restate."；`show-me-your-work/SKILL.md` 第 81 行 "Reference it by name and let it own the format. Don't restate the columns."；`no-comments/SKILL.md` 第 19 行 "Pass the scope. Do not restate its rules."

各类目标的点名写法（统计口径：playbook 与 mode 里的出现次数）：

| 被引用的 | pstack 的高频写法 | 实例 | 建议 MMW 统一成 |
|---|---|---|---|
| 能力技能 | `the **<name>** skill`（31 次）；另有反引号名 `` `how` ``（13 次）、斜杠 `` `/deslop` ``（28 次） | `investigation.md` 第 7 行 "Route through the **how** skill."；`bug-fix.md` 第 8 行 "the **why** skill for regression history" | MMW 规则已定：`` the `<name>` skill ``，斜杠只在让人输入时用（`SKILL-SET-RULES.md` `### Paths and host neutrality` 第 116、118 行） |
| 原则 | `the **<slug>** principle skill`（21 次）；另有 `**principle-<slug>**`、括注 `(principle-<slug>)` 等，共五种（L7 E.1 第 1 条） | `feature.md` 第 10 行 "(the **separate-before-serializing-shared-state** principle skill)"；`refactoring.md` 第 10 行 "(**principle-subtract-before-you-add**)" | 建议：句末括注 `(**principle-<slug>**)`，放在它改变的那个决定所在的句子末尾。理由：MMW 的原则是 `mmw/principles/principle-<slug>.md` 文件、不是技能（R18 第 1.1 节），"principle skill" 一词不再成立；slug 与文件名相同，lint 能核对它存在 |
| playbook | 粗体显示名，首次出现带相对路径 | mode 第 20 行 "the Prototype playbook (`playbooks/prototype.md`)"；`bug-fix.md` 第 13 行 "Run **Opening a PR**."；`multi-phase-plan.md` 第 6 行 "Run `playbooks/prototype.md` for each." | 建议：`Run **<Display name>** (`playbooks/<file>.md`).`，显示名与路径都写，前者给人读、后者给 lint 核对 |
| reference | 相对路径，从 playbook 引用时带 `../` | mode 第 33 行 "per `references/bugbot-triage.md`"；`babysit.md` 第 22 行 "per `../references/bugbot-triage.md`"；`how/SKILL.md` 第 28 行 "`references/explorer-prompt.md`" | 相对所在技能根目录写 `references/<file>.md`，并写打开它的条件（MMW `### Load and disclosure` 第 25 行） |
| 脚本 | 反引号里的路径加参数占位 | `show-me-your-work/SKILL.md` 第 38 行 "`scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>`"；`worktree-cleanup.md` 第 5 行 "run `scripts/worktree-audit.sh`" | 见第 7 节 |
| 另一组件的某一步 | 按编号：mode 第 25 行 "(Feature step 3)"、`blast-radius/SKILL.md` 第 33 行 "Use `why` step 2" | 无 | 不照搬，改为按标题引用（第 9 节 P2、第 10 节 C3） |

---

## 2. mode

范本：`poteto-mode/SKILL.md`（143 行）。全插件只有这一份 mode。

### M1 frontmatter

原文第 1–9 行：`name`、`description`（两句，第二句以 "Use for" 起头）、`disable-model-invocation: true`、`mode: true`、`icon`、`color`、`reminder`。后四个键是 Cursor 专有机制（L7 E.2），MMW 不照搬（第 10 节 C1）。

### M2 固定的节与顺序

`# <Name> mode` → `## Non-negotiables` → `## Principles` → `## Autonomy` → `## Subagents` → `## Writing the reply` → `## Comments` → `## Playbooks`（原文第 11–115 行）。

每节装什么、不装什么：

| 节 | 装 | 不装 | 实例 |
|---|---|---|---|
| `## Non-negotiables` | 一段总规则（引用原则时要说出它改变了哪个决定），然后 "Remaining triggers:" 下的触发行 | 某个 playbook 的步骤；多分支的决策程序 | 第 15 行总规则；第 19–35 行 17 条触发 |
| `## Principles` | 一句读法说明，然后按组列出每条原则的一行索引 | 原则全文 | 第 39 行 "Read the leaf skill in full for any principle you apply. Each entry names when it applies."；第 43–77 行 |
| `## Autonomy` | 哪些事直接做、哪些必须停、会话级覆盖、敢于说不 | 具体动作的步骤 | 第 81–87 行四个粗体段首标签 |
| `## Subagents` | 派子代理的默认参数、谁对子代理的产出负责 | 某个能力技能自己的子代理参数（它们「set their own」） | 第 91、93、95 行 |
| `## Writing the reply` | 所有 playbook 共用的回复写法 | 某个 playbook 独有的回复内容 | 第 99–109 行；第 109 行 "The per-playbook lines below name only the content unique to that playbook." |
| `## Comments` | 代码注释规则 | 无 | 第 113 行 |
| `## Playbooks` | 执行协议、升级路由、路由表 | playbook 的步骤 | 第 117、119、121–143 行 |

### M3 句式

- **触发行**：`- <可观察的条件> → the **<skill>** skill.`，后面至多一两句限定。实例：第 19 行 "Nontrivial change, architecture decision, or "are we sure?" → the **how** skill."；第 22 行 "Code crossing a function boundary → the **architect** skill, parallel design exploration before implementing."；第 29 行 "Before review → the **no-comments** skill (`/no-comments`)."
- **原则索引行**：`- **<Display Name>** (**principle-<slug>**). <何时适用>. <一句要点>.` 实例：第 43 行 Laziness Protocol、第 65 行 "**Prove It Works** (**principle-prove-it-works**). After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles"."
- **路由行**：`- **<Name>.** <任务类型定义>. [用户原话]. [Distinct from …]. [交付物限定]. `playbooks/<file>.md`.` 实例：第 122 行 "**Bug fix.** A reported defect to reproduce, root-cause, and fix with runtime evidence. `playbooks/bug-fix.md`."；第 125 行 Runtime forensics 行的交付物限定 "The deliverable is a diagnosis, not a fix."；第 136 行 Orchestrate 行的用户原话与 "Distinct from Autonomous run"。
- **执行协议**：一段祈使句，说明怎样把 playbook 变成 todo。实例：第 117 行 "Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`."

### M4 长度

原文 143 行：17 条触发、23 条原则索引各一行、23 条路由各一行。推断：mode 的每一行都会在每个任务开始时被读到（mode 第 39 行、`agents/poteto-agent.md` 第 9 行 "Read the `poteto-mode` skill's `SKILL.md` in full before doing any work"），所以它只装索引与跨 playbook 的规则，单条触发行超过三句就是装错了地方（L7 A.1 把第 20 行列为反例）。

### M5 引用写法

mode 向下引用：技能用 `the **x** skill`，原则用 `**principle-x**`，playbook 用路由行末的相对路径 `playbooks/x.md`，reference 用 `references/x.md`（第 33 行）。mode 不引用任何 playbook 的步骤编号；pstack 在第 25、30 行违反了这条（第 9 节 P2）。

---

## 3. playbook

范本：短的看 `bug-fix.md`（15 行，351 词），长的看 `orchestrate.md`（111 行，2636 词）。

### P1 没有 frontmatter，放在 mode 目录的 `playbooks/` 下

原文：23 份 playbook 都没有 frontmatter，都在 `poteto-mode/playbooks/`（统计）。它们只经 mode 路由表与其他 playbook 引用（L7 A.2）。

### P2 固定骨架（短 playbook）

1. `### <Name>`，名字是任务类型，与 mode 路由行的粗体名一致。实例：`bug-fix.md` 第 1 行 `### Bug fix` 对 mode 第 122 行 `**Bug fix.**`；`investigation.md` 第 1 行对 mode 第 121 行。
2. 空一行后的**所有权行**：`**You own <对象>. <动词>, <动词>.**`，可再跟一句委派立场或区分句。实例：`bug-fix.md` 第 3 行 "**You own this task. Plan, review, verify.** Delegate investigation and the fix to subagents, stay in the lead."；`investigation.md` 第 3 行 "**You own the answer. Plan, route, write.**"；`pause-safely.md` 第 3 行 "**You own a clean stop. Leave a checkpoint a cold-start agent can resume from.**"
3. 可选的**纪律段**：本类任务的总要求、与相邻 playbook 的分界、何时改走别处。实例：`bug-fix.md` 第 5 行 "Be scientific. …"；`investigation.md` 第 5 行 "Investigation requests are read-only."；`refactoring.md` 第 5 行 "Large or cross-cutting structural work belongs to the **figure-it-out** skill."
4. **编号步骤**。见 P3。
5. 可选的**尾段**：边界与转交。实例：`investigation.md` 第 12 行 "No PR, no babysit, no `architect` unless the investigation precedes a code change."；`feature.md` 第 19 行 "Code-coupled work … goes to a single owner with the checkpoint inline."；`worktree-cleanup.md` 第 12 行 "This is the one playbook that deletes user state with no code review to catch a slip, so the gates above are the review."
6. 末行 `**Reply:** <本 playbook 独有的回复内容>`。实例：`bug-fix.md` 第 15 行 "**Reply:** what was broken, root cause, fix, how you verified. Paste failing-then-passing repro output verbatim."；`pause-safely.md` 第 10 行 "… This is a pause, not a final report."

统计：23 份里 22 份第 3 行以 `**You own` 开头、有且只有一个 `**Reply:**` 行；唯一的例外是 `opening-a-pr.md`（第 9 节 P4）。

### P3 步骤的写法

- **每步首句是一个能勾掉的祈使动作**，后面接门槛、例外或理由。原因写在 mode 第 117 行：步骤会被原样抄进 todo（"copied in verbatim"）。实例：`bug-fix.md` 第 7 行 "1. Reproduce it yourself on the matching surface via the control skill …"；`refactoring.md` 第 7 行 "1. Pin the behavior contract first."；`pause-safely.md` 第 7 行 "3. Make the work durable."
- **长步骤的首句加粗并以句号结束**，粗体句本身就是 todo 项。统计：`autopilot-full`、`autopilot-stack`、`babysit`、`eval`、`orchestrate`、`shipping` 六份每一步都用这种写法，其余 16 份都不用。实例：`babysit.md` 第 8 行 "2. **Work the merge frontier and nothing above it.**"；`orchestrate.md` 第 61 行 "2. **Install the runtime.**"。建议：MMW 一份 playbook 里只要有一步超过三句，就全部步骤首句加粗，否则全不加（一份文件内一致）。
- **步数**：统计 4 到 9 步（`authoring-a-skill`、`investigation`、`pause-safely` 4 步，`babysit`、`shipping` 9 步）。
- **一步里的子项**用缩进列表，每项仍是粗体段首标签加句号。实例：`feature.md` 第 8–11 行 throughput checkpoint 的四项 `**Blocking first steps.**` 等。
- **不做的步骤留在列表里写理由**：mode 第 117 行 "`skip: <reason>`"；`feature.md` 第 7 行 "keeps its item with `n/a: <reason>` rather than being dropped"；`investigation.md` 第 8 行 "`throughput checkpoint: n/a, read-only investigation`"。
- **原则在它改变的那个决定的句末括注点名**，不展开原则内容。实例：`refactoring.md` 第 9–13 行每步各一处；`worktree-cleanup.md` 第 5–7 行 "(principle-build-the-lever)"、"(principle-prove-it-works)"、"(principle-guard-the-context-window, transcripts are bulk)"。
- **最后一步转交下一份 playbook**，一句话。实例：`bug-fix.md` 第 13 行、`feature.md` 第 18 行、`authoring-a-skill.md` 第 8 行 "Run **Opening a PR**."

### P4 长 playbook 的变体

一份 playbook 的规则多到放不进步骤时，pstack 的做法是：所有权行 → 纪律段（可含「Three rules carry the rest.」这样的总纲列表）→ 若干 `####` 规则簇 → `#### Steps` → 更多 `####` 规则簇 → `**Reply:**`。只有 `#### Steps` 抄进 todo，其余规则簇在步骤里按名引用。

实例：`orchestrate.md` 第 7–11 行三条总纲；第 13、21、34 行三个规则簇在 `#### Steps`（第 58 行）之前，第 68、77、85、93、103 行五个在之后；步骤里按名引用规则簇，如第 65 行 "Run the queue discipline below at every drain point."、第 66 行 "Stack safety governs."。

pstack 另有六份长 playbook（`babysit` 1291 词、`autopilot-full` 1436 词等，L7 A.0）没有用这种变体，而是把几百词塞进一步（第 9 节 P6）。建议：MMW 的一份 playbook 超过约 800 词，或任何一步超过约 150 词时，改用 `####` 规则簇变体。数字是推断的阈值，依据是 pstack 用了规则簇的 `orchestrate.md` 七步在 11–128 词之间（统计），而没用的 `babysit.md` 第 6 步连同三个续段约 460 词（统计，第 12–20 行）。

### P5 装什么、不装什么

- 装：一类用户任务里各能力的先后、门槛、谁拥有什么、何时停、回复里交什么（L7 A.2）。只属于这一类任务的做法可以写在步骤里（`shipping.md` 第 3 步的 patch-id 规则，L7 A.2）。
- 不装：能力技能的做法（点名技能）；原则的内容（括注点名）；被多处引用的概念定义（`feature.md` 第 3 步定义了 throughput checkpoint、mode 第 25 行和 `investigation.md` 第 8 行引用它，是反例）；别的技能的输出格式（`investigation.md` 第 9 行重写了 `how` 的五节，是反例，违反 `authoring-a-skill.md` 第 10 行 "Don't restate."）；与流程无关的技术目录（`perf-issue.md` 第 2 步的策略族，L7 E.1 第 5 条）。
- `**Reply:**` 只写本 playbook 独有的内容；通用写法在 mode `## Writing the reply`（mode 第 109 行）。

### P6 长度

统计：10–33 行（`orchestrate.md` 111 行、`multi-phase-plan.md` 156 行除外），127–913 词。行数不能反映长度，按词数看（L7 A.0）。

---

## 4. 能力技能

范本：子代理编排型看 `how/SKILL.md`（56 行）加两份 references；阶段型看 `arena/SKILL.md`（71 行）；编号步骤型看 `tdd/SKILL.md`（42 行）或 `blast-radius/SKILL.md`（50 行）。

### C1 frontmatter

- `name` 等于目录名。实例：`how/SKILL.md` 第 2 行 `name: how`；`arena/SKILL.md` 第 2 行 `name: arena`。例外 `make-bot-ui` 的 `name: Make Bot UI`（L7 E.1 第 26 条）。
- `description` 的高频形态是「动作句，然后 `Use for …` 触发」。实例：`arena` "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', …"；`architect` "Sketch types, signatures, and module structure before code, … Use for /architect, 'architect this', …"；`swarm` "Fan out N parallel workers, drain them, and return one report. Use for /swarm, …"。另两种形态（只写触发、只写动作）见 L7 A.3。MMW 的 description 规则不同（第 10 节 C2）。
- `disable-model-invocation: true`（46/47 个 `SKILL.md`，L7 A.3）。MMW 不照搬（第 10 节 C1）。

### C2 正文的固定顺序

1. `# <Name>`（与 `name` 同词，首字母大写）。
2. **目标段**：一到三句说明这项能力做什么、交出什么；或一句粗体的第二人称目标。实例：`how/SKILL.md` 第 9 行 "Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer …"；`teach/SKILL.md` 第 9 行 "**You explain what a thing is, how it works, and why it's built that way, …**"；`recall/SKILL.md` 第 9 行同样是一句粗体。
3. 可选的**分工句**：与兄弟技能的分界。实例：`blast-radius/SKILL.md` 第 11 行 "Companion to `how` and `why`. `how` tells you what the code does. `why` tells you why it's shaped that way. Blast radius tells you what it breaks somewhere else."；`why/SKILL.md` 第 11 行 "Companion to the `how` skill. …"。
4. 可选的**立场节**：这项工作特有的诱惑和该怎么做。实例：`blast-radius/SKILL.md` 第 15 行 `## Don't trust your own writeup`；`why/SKILL.md` 第 13 行 `## Operating Posture`；`interrogate/SKILL.md` 第 11 行 "The deliverable is a synthesized verdict. Do NOT auto-apply changes."（未单列成节）。
5. **做法**：按形态分，见 C3。
6. **收尾节**：交回什么。即使细节在 reference 里，也在这里列出节名。实例：`how/SKILL.md` 第 54–56 行 `## Output Format` 列出 "Overview, Key Concepts, How It Works, Where Things Live, Gotchas"；`why/SKILL.md` 第 140 行 `## Output Format` 列出八个节名；`arena/SKILL.md` 第 69–71 行 `## Outputs`；`blast-radius/SKILL.md` 第 40 行 `## What to hand back`。
7. 可选的末行 `**Reply:** …`。实例：`blast-radius/SKILL.md` 第 50 行、`figure-it-out/SKILL.md` 第 53 行、`teach/SKILL.md` 第 21 行、`recall/SKILL.md` 第 35 行。
8. 可选的**供别人组合的说明**或 reference 索引。实例：`show-me-your-work/SKILL.md` 第 79 行 `## Composing this skill`；`why/SKILL.md` 第 150 行 `## Reference Files`，每项一句「是什么，谁读」。

### C3 做法部分按形态选一种标题写法

| 形态 | 标题写法 | 实例（至少两处） |
|---|---|---|
| 阶段型 | `## Start`（开 todo，每阶段一项，编号列出），然后 `## Phase A: <Verb phrase>` … | `arena/SKILL.md` 第 11–20 行 `## Start` 与六项，第 22 行 `## Phase A: Frame`；`swarm/SKILL.md` 第 11–18 行；`architect/SKILL.md` 第 11、21 行；`figure-it-out/SKILL.md` 第 11、15 行 |
| 子代理编排型 | `## Step N. <Title>`，分支用 `2a`、`2b`，每步写子代理参数块 | `how/SKILL.md` 第 11、20、30、40、50 行；`why/SKILL.md` 第 17、23、56、121、136 行 |
| 编号步骤型 | 一个 `## Steps`（或 `## Workflow`），下面编号列表 | `blast-radius/SKILL.md` 第 31 行；`no-comments/SKILL.md` 第 17 行；`tdd/SKILL.md` 第 13 行 `## Workflow` |
| 规则目录型 | `## Process`（两三步）加按类分组的规则，规则编号是稳定 id | `unslop/SKILL.md` 第 11、16 行，第 18 行 "Rule numbers are stable ids that other skills cite. A removed rule leaves a gap."；`technical-writing/SKILL.md` 第 21–106 行每个 H2 是一条祈使句（"Pick the mode first (Diátaxis)"） |
| 格式持有型 | 按「格式 → 怎样写一行 → 放哪 → 规则 → 审计 → 供组合」分 H2 | `show-me-your-work/SKILL.md` 第 11、34、42、48、53、79 行 |
| 单条指令型 | 没有标题，frontmatter 后一段 | `bro/SKILL.md` 第 7 行 |

同一形态内部，pstack 的标题标点不一致（第 9 节 P11）；建议 MMW 每种形态只用上表第一处实例的写法。

### C4 子代理参数块

每个派子代理的步骤写成一个列表或表，列出参数，参数后紧跟一句理由（G4）。

实例：
- `how/SKILL.md` 第 24–26 行三项 "`subagent_type`: `generalPurpose`"、"`model`: your configured how-explorer model (default …)"、"`readonly`: `true`"，接着第 28 行 "Each explorer gets the prompt in `references/explorer-prompt.md` with its angle filled in."
- `why/SKILL.md` 第 125–127 行同样的三项，第三项带理由 "The synthesizer's quality check spot-verifies citations, which can require MCP access. Readonly/Ask mode strips MCPs and defeats that."
- `reflect/SKILL.md` 第 33–37 行用表：`Lens | model | Prompt template`。

参数名与宿主绑定（`subagent_type`、`readonly` 都是 Cursor `Task` 的参数），MMW 按角色写（第 10 节 C4）。

### C5 自带人工闸门，写在它生效的那一步里

实例：`interrogate/SKILL.md` 第 32 行 "If you're unsure about the intent, ask the user before proceeding."；`reflect/SKILL.md` 第 51 行 "present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval."；`no-comments/SKILL.md` 第 23 行 "Wait for interactive approval. Unattended and eval require caller pre-approval." 最后一例同时写了无人运行时的出路，这是 MMW 应当照学的形态（R18 `## 审查记录` 第 40 条也要求能力技能的人工闸门写明无人会话的出路）。

### C6 长度

统计：7–156 行，多数 35–115 行（`bro` 7、`teach` 21、`why` 156）。推断：超过 115 行的只有 `why`，它把每类来源的检索法放进了 `references/sources/`，正文仍有 156 行，其中 `### Discovery`、`### Investigator roster` 两节（第 60–120 行）是可以按分支拆出去的候选。

### C7 引用写法

- 引用兄弟技能：按名，不引用它的步骤编号。反例：`blast-radius/SKILL.md` 第 33 行 "Use `why` step 2"；`eval.md` 的 "per the **arena** skill's Phase B"（L7 A.3）。
- 引用自己的 reference：`references/<file>.md`，写在用到它的那一步，写明怎样用（整份转交、填占位、只读某节）。实例：`how/SKILL.md` 第 38 行 "Build its prompt from `references/explainer-prompt.md` without the explorer-findings section."；`reflect/SKILL.md` 第 39 行 "Pass each template verbatim, substituting the transcript path or digest where marked."；`interrogate/SKILL.md` 第 51–55 行列出要填进模板的四样东西。
- 能力技能不引用 playbook（L7 A.3，唯一例外 `recall` 的往外分流）。

---

## 5. 原则

范本：`principle-attack-the-premise/SKILL.md`（23 行，结构最完整）。

### R1 frontmatter

`name: principle-<slug>`；`description: "Apply <when/to/after/before> <情境>. <祈使句的规则摘要>."`；`disable-model-invocation: true`。统计：23 条全部如此，description 全部以 "Apply" 开头。

实例：`principle-attack-the-premise` "Apply when two or more fixes that share one premise have failed the same gate. Take a census …"；`principle-prove-it-works` "Apply after completing a task, before declaring done. Verify against the real artifact …"；`principle-guard-the-context-window` "Apply when context is filling up: …"。

MMW 的原则是 `mmw/principles/principle-<slug>.md`，不是技能（R18 第 1.1 节）。建议保留 description 这一行（写成文件首段或 frontmatter 由 R18 的导入接口定），因为 mode 的原则索引行就是从它来的（mode 第 43–77 行与各原则 description 的「情境 + 要点」一一对应）。

### R2 正文的固定顺序

1. `# <Name>`。
2. **规则**：一到三句，陈述句或祈使句。实例：`principle-attack-the-premise` 第 9 行 "When two or more fixes that share one premise have failed the same gate, suspect the premise, not the fixes."；`principle-build-the-lever` 第 8 行 "When the work isn't trivial, build the tool that does it instead of doing it by hand."
3. `**Why:**` 一到三句后果或成本。统计：23 条里 16 条有。实例：`principle-attack-the-premise` 第 11 行 "**Why:** Each failure under a shared premise is evidence about the premise."；`principle-never-block-on-the-human` 第 11 行。
4. `**Pattern:**` 3 到 8 条做法，每条是粗体段首标签加句号，再接一两句。实例：`principle-attack-the-premise` 第 14–17 行 "**Write the premise down.**"、"**Take a census before the next fix.**"；`principle-guard-the-context-window` 第 14–16 行 "**Isolate large payloads.**" 等。做法可以是编号的短程序：`principle-encode-lessons-in-structure` 第 15–17 行。
5. 可选的**判别节**：`**The test:**`、`**Stop:**`、`**Boundaries:**`、`**Balance:**`。实例：`principle-attack-the-premise` 第 19–21 行 `**Stop:**`；`principle-never-block-on-the-human` 第 17–20 行 `**Boundaries:**`；`principle-laziness-protocol` 第 18 行 `**The test:**`；`principle-build-the-lever` 第 21 行 `**Balance:**`。
6. 可选的**区分句**，放最后：`Distinct from [<Name>](../principle-<slug>/SKILL.md), which …`。实例：`principle-attack-the-premise` 第 23 行；`principle-build-the-lever` 第 23 行。

### R3 句式

- 小节用粗体段首标签，以冒号结束，不用 `##`（G1）。
- 做法条目用祈使句，省略主语。实例见 R2 第 4 项。
- 反面信号用一句「你跳过了它的迹象是……」。实例：`principle-model-the-domain` 第 26 行 "The sign that you skipped this is a new feature that grows an existing if/else chain by one more branch …"；`principle-build-the-lever` 第 18 行 "If you cited it and there is no codemod, script, generator, or delegate skill in the diff, you didn't apply it."

### R4 装什么、不装什么

- 装：可观察的触发情境、一条能改变具体决定的规则、它的理由、判别方法（L7 A.4 的四条门槛）。
- 不装：命令、参数、输出格式、某种语言或工具的细节（L7 A.4 把 `test-behavior-not-implementation` 的 Jest 断言名、`type-system-discipline` 的多语言惯用法列为写错）；只适用于某个流程一步的规则。

### R5 长度

统计：16–34 行（合计 513 行）；最长 `principle-boundary-discipline` 34 行。

### R6 引用写法

- 原则之间用相对 Markdown 链接，括注或 `per` 引导。实例：`principle-attack-the-premise` 第 15 行 "per [Build the Lever](../principle-build-the-lever/SKILL.md)"、第 16 行 "per [Fix Root Causes](../principle-fix-root-causes/SKILL.md)"；`principle-build-the-lever` 第 21 行 "Per the [Laziness Protocol](../principle-laziness-protocol/SKILL.md)"。统计：只有 3 个文件用了这种链接（`attack-the-premise` 4 处、`build-the-lever` 3 处、`minimize-reader-load` 1 处）。
- 原则只向下引用两个能力技能（`prove-it-works` → `show-me-your-work`，第 22 行；`type-system-discipline` → `typescript-best-practices`），不引用 playbook、脚本、子代理（L7 A.4）。

---

## 6. reference

reference 没有 frontmatter，放在所属技能的 `references/` 下，由正文点名（L7 A.5）。按用途分四种形状。

### F1 提示模板（整份或填占位后交给子代理）

高频形状（统计：`how` 两份、`interrogate/references/reviewer-prompt.md`、`why/references/investigator-prompt.md`、`synthesizer-prompt.md`，共 5 份）：

1. `# <Role> Prompt Template`。
2. 一句给编排者的说明："Build … prompt from this template. Fill in the placeholders."
3. `---` 分隔线。线下是给子代理的第二人称正文。
4. 一段角色与处境（你是谁、别人在做什么、你的产出给谁）。
5. `## Question` / `## Intent` 等输入节，用 `{UPPER_SNAKE}` 占位。
6. `## … Instructions` 做法节。
7. `## Output` 或 `## Output Format`，下面 `###` 列出固定的输出小节，并明说「没有发现也要说」。

实例：
- `how/references/explorer-prompt.md` 第 1、3、5 行是 1–3 项；第 7–9 行角色与处境 "A separate agent will write the human-facing explanation from your findings, so favor thoroughness and accuracy over prose."；第 13 行 `{QUESTION}`；第 32–52 行六个输出小节，最后一节 `### Open Questions` "Be honest about gaps."
- `interrogate/references/reviewer-prompt.md` 第 1、3、5 行；第 13、19、23、27 行四个占位；第 55–57 行 "If you have zero findings, say so. An empty review is a valid outcome."

另两种形状是变体（第 9 节 P10）：`architect/references/runner-prompt.md` 没有 `---`，给编排者的说明写成第 3 行一整段；`reflect/references/*.md` 四份没有标题，直接从 "You are a reviewer applying …" 开始，占位写成 `<ABSOLUTE_PATH>`。建议 MMW 只用高频形状。

### F2 检索或操作指南（按外部来源替换的变体）

固定小节：`## What this source contains` → `## How to search it` → `## What good evidence looks like here` → `## Common pitfalls` → `## What to return`。实例：`why/references/sources/slack.md` 第 3、14、30、38、46 行；L7 A.5 记录 `why/references/sources/*.md` 全部用这五节。由一份索引 reference 列表指向（`why/references/source-playbook.md` 第 5 行起的表）。

### F3 判断框架或清单（只在某个条件下查）

`# <Name>` → 一句「何时用、怎样用」→ 每一项一个 `##`。实例：`architect/references/design-red-flags.md` 第 1–5 行 "Screen every candidate before synthesis. A red flag is a reason to revise or reject the shape." 然后 `## Shallow module`；`interrogate/references/rubric.md` 第 3 行 "Review through whichever lenses are relevant. Not every lens applies to every change." 然后 `## Correctness`。

### F4 产物模板、样例与会增长的目录

- 产物模板：`# <Name> template` → 一句用法 → 产物的各节。实例：`architect/references/rationale-template.md` 第 3 行 "The prose that ships alongside the type sketch. One page. Sentence-case headings, no boilerplate."；`show-me-your-work/references/decision-log-template.tsv`（只有表头行）。
- 会增长的目录：开头一句说明谁在什么时候读，末尾有追加区。实例：`poteto-mode/references/bugbot-triage.md` 第 3 行 "Use this reference when the Babysit playbook (`../playbooks/babysit.md`) handles Bugbot …"；L7 A.5 引它的追加区原文 "Append new candidate learnings here during or after babysitting"。

### F5 所有 reference 共用的规则

- **H1 下第一句说明谁在什么时候读它、怎样用**。实例：F1–F4 各例的第 3 行；`typescript-best-practices/references/patterns.md` 第 3 行 "Code examples for each rule in `SKILL.md`."
- **正文列出节名，reference 装节的内容**：技能正文的收尾节即使把格式交给 reference，也写出节名（C2 第 6 项的 `how`、`why` 实例）。
- **长度**：统计 17–144 行（排除 1 行的 `.tsv` 与 313 行的 `patterns.md`）。
- **什么进 reference**：给子代理的提示模板（即使每次都用）；只在某个分支才查的清单；随环境替换的变体；产物模板；会增长的目录（L7 A.5 表）。步骤顺序、分支条件、子代理参数留在正文。

---

## 7. 脚本调用写法

### S1 技能文本里怎样写一次脚本调用

一句里给出：反引号里的调用（路径相对技能根目录，参数用 `<name>` 占位）；它做什么（一句）；拿到输出后做什么。只写这一步用到的开关，完整参数表留在脚本头部。

实例：
- `show-me-your-work/SKILL.md` 第 38 行 "Use the helper `scripts/log.sh <logfile> <phase> <decision> <why> <evidence> <result>`. It stamps `ts`, writes the header on first use, strips stray tabs/newlines, …"
- `multi-phase-plan.md` 第 10 行 "6. Run `node pstack/skills/poteto-mode/scripts/check-plan.mjs <plan.md>` and fix every line it prints (the **encode-lessons-in-structure** principle skill)."
- `babysit.md` 第 12 行 "status comes from `scripts/watch-pr/watch-pr`. Run it directly. It emits JSON by default and accepts `--pretty` for humans. In `check` mode pass `--status-only`."
- `worktree-cleanup.md` 第 5 行 "then run `scripts/worktree-audit.sh` (principle-build-the-lever). … It classifies each worktree …, then suggests a bucket. The transcript scan is slow, so background it."

### S2 脚本的结论是建议时，下一步写明判断归谁

实例：`worktree-cleanup.md` 第 6 行 "The bucket is advice, not permission. … the pinned set wins."；`orchestrate.md` 第 15 行 "The CLI never spawns, waits, or wakes anything."（说明脚本不做的事，免得 agent 等它做）。

### S3 多次调用同一脚本时，先给一次全名再定简称

实例：`orchestrate.md` 第 23 行 "Use `bun scripts/orch/orch.ts` for bookkeeping, written below as `orch`"，之后第 61、70、73 行都写 `orch init`、`orch inbox push …`、`orch unit add`。

### S4 脚本头部（给写脚本的人，不在技能文本里）

头部注释写：做什么、保证不做什么、`Usage:` 一行；用法错误写 stderr 并以非 0 退出。实例：`worktree-audit.sh` 第 2–7 行 "Read-only worktree prune audit. … Never deletes anything; deletion stays a human-gated step in the playbook. # Usage: worktree-audit.sh [repo-path]"；`log.sh` 第 2–3 行与第 6–9 行 `printf 'usage: …' >&2; exit 1`。输出与退出码约定见 L7 A.6。

### S5 字面检查器持有它所检查的原文

`check-plan.mjs` 第 5–6 行常量 `RULE` 就是 `multi-phase-plan.md` 第 13 行 `**Verification.**` 规定的那句话；`SUB_BLOCKS`（第 8–18 行）是模板要求的粗体段首标签。这意味着改那句话要两处同改（L7 A.6）。

---

## 8. agent 定义

范本：`agents/poteto-agent.md`（9 行）与 `agents/comment-sicko.md`（32 行）。

- **frontmatter**：`name`（就是派它时的类型名，可以带空格）、`description`、可选 `is_background: true`。实例：`poteto-agent.md` 第 2–4 行；`comment-sicko.md` 第 2–3 行 `name: Comment Sicko`。
- **正文尽量薄，两种形态**：
  - 指路型：一句「先读哪份文件全文」。`poteto-agent.md` 第 9 行 "Read the `poteto-mode` skill's `SKILL.md` in full before doing any work … Navigate to a leaf `principle-*` skill whenever you apply that principle."
  - 角色型：第一人称的角色、输入、保留清单、判定规则、越权边界、输出。`comment-sicko.md` 第 12 行输入、第 14–20 行保留清单、第 30 行 "I never write application code."、第 32 行 "Report only. Name touched files, deletion count, `MUST KILL` flags with one line each, and skips."
- **调用方不复述它的规则**：`no-comments/SKILL.md` 第 19 行 "Pass the scope. Do not restate its rules."
- **不把政策写进 description**：`poteto-agent.md` 第 3 行把续跑政策写进了 description，与 mode 第 95 行冲突（第 9 节 P16）。

---

## 9. pstack 自己不一致或写得不好、MMW 不照搬的地方

L7 第 E.1 节已列 31 条。下面只列与文本结构有关的，并补本轮新发现的（标「本轮」）。每条写 MMW 的做法。

| # | 问题 | 出处 | MMW 的做法 |
|---|---|---|---|
| P1 | 原则引用至少五种写法 | L7 E.1 第 1 条；本文 G7 表 | 一种：句末 `(**principle-<slug>**)` |
| P2 | 按步骤或阶段编号引用别的组件 | mode 第 25 行 "(Feature step 3)"、第 30 行 "Bug fix step 1"；`blast-radius/SKILL.md` 第 33 行 "`why` step 2"；L7 E.1 第 2 条 | 按标题或粗体步骤首句引用；编号一重排就指错 |
| P3 | "Invoked at the end of every other playbook." 与实际不符（23 份里只有 7 份以它收尾） | mode 第 143 行、`opening-a-pr.md` 第 3 行；L7 E.1 第 3 条 | 路由行只写真实的调用关系；「每份都收尾于 X」这类全称句由连线检查核对 |
| P4 | `opening-a-pr.md` 名为 playbook，没有所有权行、编号步骤、Reply 行，实质是标准 | `opening-a-pr.md` 全文 | 没有步骤的约定不进 `playbooks/`；是规则就进 mode 或 reference |
| P5 | 被多处引用的概念定义在某个 playbook 的一步里 | `feature.md` 第 7–11 行 throughput checkpoint；mode 第 25 行、`investigation.md` 第 8 行引用它 | 共享概念放 mode 或一份 reference，各处按名引用 |
| P6 | 一步几百词，步骤首句被淹没 | `babysit.md` 第 12–20 行（第 6 步，含三个续段）；L7 A.2 列的 `autopilot-full.md` 第 2、6 步 | 改用第 3 节 P4 的 `####` 规则簇变体 |
| P7 | playbook 复述技能的输出格式 | `investigation.md` 第 9 行重写 `how` 的五节 | 写「按 `how` 的输出格式」，不列节名 |
| P8 | 箭头简写：mode 触发行与原则用 `→`、`->`，而 `unslop` 规则 33 要求把箭头写成完整句 | mode 第 19–35 行；`principle-encode-lessons-in-structure` 第 25 行 "One-off -> brain note."；`unslop/SKILL.md` 第 67 行 "spell out arrows and abbreviations"（本轮） | 触发行保留一种箭头（它是索引格式，lint 按它解析）并在 mode 首次使用处说明读法；正文段落不用箭头 |
| P9 | 句中冒号与长破折号违反 mode 自己的规则 | `orchestrate.md` 第 17 行 "needs this machine: `control-ui`"；`opening-a-pr.md` 第 5 行；`bugbot-triage.md` 第 98、107 行；`create-verification-skill` description 的 em dash；L7 E.1 第 9、10 条 | 结构 lint 查长破折号；句中冒号用启发式检查 |
| P10 | 提示模板三种形状，占位符两种写法（`{X}` 与 `<X>`） | F1 节；`reflect/references/judgment-reviewer.md` 第 1 行无标题、用 `<ABSOLUTE_PATH>`（本轮） | 只用 F1 的高频形状与 `{UPPER_SNAKE}` |
| P11 | 同一形态的步骤标题四种标点 | `how/SKILL.md` 第 11 行 "Step 1. Assess Complexity"；`interrogate/SKILL.md` 第 13 行 "Step 1, Determine Scope"；`reflect/SKILL.md` 第 17 行 "### 1. Locate the active transcript"；`create-verification-skill` "## 1. Interview the repo, not the user"（本轮） | 每种形态一种写法（C3 表第一处实例） |
| P12 | 收尾节七种名字 | `## Output Format`（how、why、interrogate）、`## Outputs`（arena、architect）、`## Final Response`（tdd）、`## Output contract`（recall）、`## What to hand back`（blast-radius）、`## Outcomes`、单行 `**Reply:**`；L7 A.3 | 建议两种：交给人或调用方的产物结构用 `## Output`，回复要点用末行 `**Reply:**`；两者都有时 `**Reply:**` 只写 `## Output` 之外的内容 |
| P13 | 标题大小写不一：`unslop` 规则 17 要求 sentence case，但 22/23 条原则的 H1 是 Title Case，`how`、`interrogate`、`why`、`tdd` 的 H2 也是 | `unslop/SKILL.md` 第 40 行；`principle-sequence-verifiable-units` 是唯一的 sentence case H1（本轮统计） | 标题一律 sentence case；原则的显示名（专有名）在 mode 索引里保留大写的由写作规范定 |
| P14 | 同一原则的显示名在两处不同 | mode 第 45 行 "Redesign from First Principles" 与原则 H1 "Redesign From First Principles"；mode 第 67 行 "Sequence Work into Verifiable Units" 与 H1 "Sequence work into verifiable units"（本轮） | 显示名只有一个出处（原则文件的 H1），mode 索引与之逐字相同，由 lint 核对 |
| P15 | 原则小节标签七种写法，`**Why:**` 只有 16/23 条有 | 本轮统计：`**Pattern:**` 7、`**The pattern:**` 4、`**The test:**` 3、`**The tests:**` 2，另有 `**Rule:**`、`**Core rule:**`、`**Applications:**` 等各 1；L7 E.1 第 15 条 | 固定四个标签：`**Why:**`（必有）、`**Pattern:**`（必有）、`**The test:**` 或 `**Stop:**`（可选，二选一）、区分句（可选） |
| P16 | agent 定义的 description 里写政策，与 mode 冲突 | `agents/poteto-agent.md` 第 3 行 "Resume an existing `poteto-agent` … rather than spawning a sibling."；mode 第 95 行 "fire a fresh subagent with consolidated scope"；L7 E.1 第 29 条 | description 只写它是谁、何时派；政策只在 mode 一处 |
| P17 | 每次调用都读的 reference 与 `guard-the-context-window` 的规则相反 | 该原则第 15 行 "Templates and references used on every invocation belong in the skill file"；`how` 的 `explainer-prompt.md` 两条路径都读；L7 E.1 第 28 条 | 提示模板例外（它整份交给另一个代理）写明为规则；其他每次都读的内容回正文 |
| P18 | 正文写死模型名与宿主工具 | `bug-fix.md` 第 9 行 "(default `grok-4.7-xhigh-fast`)"；`how/SKILL.md` 第 25 行；mode 第 26、28、30 行点名 Cursor 内置技能与 `cursor-team-kit`；L7 E.2 | 写角色名，模型由 `~/.mmw/models.json` 决定；宿主差异写成能力（第 10 节 C4） |
| P19 | description 写 "Must always apply." 却关闭自动触发 | `unslop/SKILL.md` 第 3–4 行；L7 E.1 第 11 条 | description 不写与调用开关矛盾的话 |
| P20 | playbook 里装了与流程无关的技术目录 | `perf-issue.md` 第 2 步；L7 E.1 第 5 条 | 目录进 reference，步骤写「按 `references/x.md` 选」 |

---

## 10. 照搬结构时与 MMW 现行写作规则的冲突

MMW 的规则在 `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md`（下称 SSR）与 `AGENTS.md`。下表每行的「做法」一列是按 MMW 规则改写 pstack 结构的建议，理由写在同一格里。

| # | pstack 的结构写法 | MMW 规则 | 做法 |
|---|---|---|---|
| C1 | frontmatter 带 `disable-model-invocation`、`mode`、`reminder`、`icon`、`color`、`paths`（M1、C1、R1） | `AGENTS.md` `## Commands` 表：`check_own_skill_frontmatter.py` 在「one of this repository's skills carries a key other than `name` and `description`」时失败 | MMW 自写组件只写 `name`、`description`；调用开关由 `mmw-v2/skills.txt` 的 `+model` 标记表达（R18 第 1.1 节）。导入的 pstack 原文不改，开关在安装副本里去掉（R18 审查记录第 16 条） |
| C2 | description 是「动作句 + Use for 触发」（C1） | SSR `### Descriptions` 第 67 行 "A description carries the trigger and nothing else" | MMW 自写技能的 description 只写「是什么」加触发分支；动作、流程、输出进正文。原则的 "Apply when … . <要点>." 是 mode 索引行的来源，属于 mode 内部数据，不受此条约束（推断，需写作规范确认） |
| C3 | 按步骤编号跨组件引用（P2） | SSR `### Vocabulary` 第 81 行 "cited by producer and reader as the same literal, by title rather than by number" | 按粗体步骤首句或 `####` 标题引用。这也是建议长步骤首句加粗（P3）的另一个理由：它给了每一步一个可引用的字面名 |
| C4 | 子代理参数写 `subagent_type`、`readonly`、`model` 默认值，点名 Cursor、`Task`、`/loop`（C4、P18） | SSR `### Paths and host neutrality` 第 118、120 行：不点宿主、工具、runner 名 | 参数块改写为「角色（`models.json` 的行名）+ 只读或可写 + 理由」；宿主差异写成能力 |
| C5 | playbook 步骤没有完成判据，完成由所有权行与 `**Reply:**` 隐含（P2） | SSR `### Rules and completion criteria` 第 124 行 "a step without a completion criterion is a finding … on a line beginning `Done when`" | 建议：playbook 在编号步骤之后、`**Reply:**` 之前加一行 `Done when <可检查的条件>.`；步骤首句本身能勾掉的，不再逐步加。这是结构上新增的一行，由写作规范最终定 |
| C6 | 「写不写理由」：pstack `authoring-a-skill.md` 第 10 行 "Tell it to do the thing and skip the reason. Explain only when the rule is confusing without one." | SSR `## What skill text is for` 第 1 条 "next to a rule, the reason for it: a model given the reason carries it into cases no rule names" | 结构上照 pstack：理由紧跟规则（G4），不另开节。写多少理由按 mattpocock 一侧，这是用户说的「决定技能对 agent 思考深度与广度的影响」的那部分，本文不裁决 |
| C7 | 所有权行只写「你拥有什么」，没有「这项工作为谁、错了谁付代价」 | SSR `## What skill text is for` 第 1 条的开篇段测试 | 推断：所有权行后的可选纪律段（P2 第 3 项）就是放这类句子的位置，不必新增节 |
| C8 | pstack 文本是英文 | SSR `### Vocabulary` 第 78 行 "Skill text is English." | 一致，照搬 |

---

## 11. 能由结构 lint 机械检查的规则

供 `R21-text-integrity-checks.md` 取用。只列判定能写成确定规则的；「首句是否能勾掉」「理由是否紧跟」这类要判断的不列。

| 组件 | 检查 | 依据 |
|---|---|---|
| playbook | 第 1 行匹配 `^### `；文件里没有 `^# `、`^## ` | G1、P1 |
| playbook | 第一个非空正文行以 `**You own ` 开头 | P2 第 2 项 |
| playbook | 最后一个非空行以 `**Reply:** ` 开头；全文恰好一个 | P2 第 6 项 |
| playbook | 编号步骤数在 3–9 之间；有 `####` 时恰好一个 `#### Steps` | P3、P4 |
| playbook | 一份文件里的编号步骤，要么全部以 `**…**` 开头，要么全不 | P3 |
| playbook | `### ` 名与 mode 路由行的 `**<Name>.**` 逐字相同，路由行末的路径存在 | P2 第 1 项、M3 |
| mode | `##` 节的名字与顺序等于固定列表 | M2 |
| mode | 每条原则索引行匹配 `^- \*\*.+\*\* \(\*\*principle-[a-z-]+\*\*\)\. `，slug 对应的文件存在，显示名与该文件 H1 逐字相同 | M3、P14 |
| 原则 | 有 `^# `；没有 `^## `；有 `**Why:**` 与 `**Pattern:**`；小节标签只在固定集合里 | R2、P15 |
| 能力技能 | frontmatter 只有 `name`、`description`；`name` 等于目录名 | C1、第 10 节 C1 |
| 能力技能 | 收尾节名只能是 `## Output` 或末行 `**Reply:**` | P12 |
| reference（提示模板） | 第 1 行 `^# .+ prompt template`（大小写不敏感）；有 `^---$`；占位只用 `\{[A-Z_]+\}` | F1、P10 |
| 全部 | 没有 U+2014、U+2013 | G6、P9 |
| 全部 | 没有 `step \d+`、`Step \d+`、`Phase [A-Z]` 出现在指向别的文件的句子里（启发式：同一句里还有另一个组件名） | P2、第 10 节 C3 |
| 全部 | 原则引用只用 `(**principle-<slug>**)` 一种写法，且 slug 存在 | G7、P1 |
| 全部 | 不出现宿主、工具、runner 名（SSR 第 120 行已有的 grep） | 第 10 节 C4 |

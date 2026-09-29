# L7 pstack 组件规范：组件类型、写法、连线与归类判据

这份规范用于下一轮把 MMW 的每个部件归入 pstack 的分层架构，归类时以它为准。它由六份读者报告合成：

- `docs/research/workflow-compare/reports/L1-pstack-mode-and-short-playbooks.md`
- `L2-pstack-long-playbooks-and-scripts.md`
- `L3-pstack-capability-skills-a.md`
- `L4-pstack-capability-skills-b.md`
- `L5-pstack-principles.md`
- `L6-pstack-machinery-and-guide.md`

以下简称 L1 到 L6。pstack 快照在 `docs/research/code-landing-refs/pstack/`（cursor/plugins b0b9c7a0，`.cursor-plugin/plugin.json` `"version": "0.15.4"`）。下文不带前缀的路径都相对这个目录。

**合成时做的核对：**

- 用 `wc -l` 重新量了全部组件的行数；playbook 另用 `wc -w` 量了词数。第 A 节的「实测行数」「词数」都出自这次测量。
- 用 grep 在快照里逐条核对了第 C 节依赖的原文引语，全部命中。
- 把六份报告末尾的 `edges` 块机器合并，第 B.3 节的统计出自这次合并。
- 审查者的 49 条修正逐条回到快照核对（见文末「审查记录」）。
- 没有把 pstack 全文再读一遍。凡是只依据某一份报告的结论，都注明报告编号；报告本身标「推断」或「未确定」的，这里照样保留。

**标注约定：**

- 「原文」：pstack 文件里写明的内容，附路径和标题或标识符。
- 「推断」：报告作者或我根据写法得出的判断，原文没有直接说。
- 读不到或拿不准的，放进第 F 节。

---

## 0. 这份规范的核心结论（先读这里）

1. **pstack 按「谁决定顺序、给谁复用」分层，不按「有没有步骤」分层。**
   - playbook 规定一类任务里各种能力的先后，入口是 mode 的路由表。
   - 能力技能是一项产出可命名交付物、能脱离 mode 被直接调用（斜杠命令、自动化、agent 定义、其他技能）的能力。它内部的 Phase 或 Step 留在技能里，不论它内部调用了多少其他技能。
   - 只在 playbook 之间复用的任务流程，pstack 留作 playbook，按文件名或名字引用（babysit、shipping、opening-a-pr、prototype 都是这样）。
   - 这条判据是推断，四份报告独立得出了相近结论（L1 4.2、L3 4.1、L4 4.1、L6 4.2），审查时又按复用发生的位置收窄过（见 A.2、C.3）。
   - 旁证原文：`skills/automate-me/SKILL.md` "This skill orchestrates three others ... It sequences them. It doesn't replace them."；`skills/poteto-mode/playbooks/authoring-a-skill.md` "A workflow you keep hitting but isn't captured → propose a new skill."；benny 只复用技能和原则，不引用任何 playbook（`automations/` 下 grep "playbook" 结果为 0）。
2. **原则是「情境触发 + 一条规则 + 理由」的短文件，只被按名字点名，不被调用。** 原则可以带一个短的顺序程序或闸门（见 A.4）。
   - 够不够格成为原则，不看它是否已经被按名复用。干净的例子是 `principle-attack-the-premise`：按名引用为 0，内容也没有在别处复用。`experience-first`、`test-behavior-not-implementation` 按名引用同样为 0，但内容被 `interrogate/references/rubric.md`、mode、`tdd` 不点名地使用了（B.3）。
   - 实际门槛是四条：能用一个短名字说出口；有可观察的触发情境；能改变一个具体决定；跨任务通用（L5 第 7 节，推断）。
3. **pstack 大量「该拆没拆」，而且多数有理由。**
   - 长内容留在 playbook 里，理由有几条：只有一个调用方；它本身就是交付物；降级时要求自足；机械部分已拆成脚本（第 C.4 节）。
   - 领域专属规则留在调用方正文里。调用方点名原则，同时限定这条原则在本处的范围（第 C.2 节）。
   - 这些「不拆」是本规范最需要照搬的部分。`reflect/references/synthesizer.md` 给出了防止「为套分层硬拆、硬塞」的原文规则（Existing-skill-first、Decision-changing、Already-covered、Structural-mechanism check，见 C.1、C.6）。
4. **pstack 自身有不少不一致**（第 E 节）。例如原则引用至少有五种写法；playbook 之间按步骤编号互相引用；「Invoked at the end of every other playbook」与实际不符（23 个 playbook 里只有 7 个以 Opening a PR 收尾）；agent 定义的续跑政策与 mode 冲突。归置 MMW 时不应当把这些不一致当成规范复制过去。
5. **许多机制是 Cursor 专有的**（第 E.2 节）：`mode: true`、`reminder`、`disable-model-invocation`、`paths`、`alwaysApply` 的 `.mdc` 规则、`subagent_type` 注册、`/loop`、`/goal`、cloud agent、内置 `create-skill`。换宿主时，这些机制要逐项找替代，不能照抄。另有一种连线方式与 MMW 的规则正面冲突：运行中从 trunk 重读组件本身（B.1），它与本仓库 `AGENTS.md` 的 Self-hosting boundary 相反。

---

## A. 组件类型总表

### A.0 类型一览与实测行数

| 类型 | pstack 里的位置 | 文件数 | 实测行数 | 典型范围 |
|---|---|---|---|---|
| mode | `skills/poteto-mode/SKILL.md` | 1 | 143 | — |
| playbook | `skills/poteto-mode/playbooks/*.md` | 23 | 10–156 行；合计 15314 词 | 行数不能反映长度，因为一步常常是一整段。按词数，长 playbook 有 `orchestrate.md` 2636、`multi-phase-plan.md` 2186、`autopilot-full.md` 1436（13 行）、`babysit.md` 1291、`shipping.md` 913、`autopilot-stack.md` 823、`opening-a-pr.md` 818；其余在 641 词以下 |
| 能力技能 | `skills/<name>/SKILL.md`（principle 与 poteto-mode 之外） | 23 | 7–156 | 多数在 35–115；`bro` 7，`teach` 21，`why` 156 |
| 原则 | `skills/principle-*/SKILL.md` | 23 | 16–34 | 合计 513；最长 `principle-boundary-discipline` 34 |
| reference | `skills/*/references/**` | 31 | 1–313 | 多数在 33–144；`decision-log-template.tsv` 1，`typescript-best-practices/references/patterns.md` 313 |
| 脚本 | `skills/poteto-mode/scripts/**`、`skills/show-me-your-work/scripts/log.sh` | 见 A.6 | 42–1607 | — |
| agent 定义 | `agents/*.md` | 2 | 9、32 | — |
| 配置 / 规则文件 | `.cursor-plugin/plugin.json`；运行时生成的 `~/.cursor/rules/pstack-models.mdc` | 1 + 1 | 31；mdc 有 17 行角色 | — |
| 文档（guide） | `README.md`、`docs/guide/*.md` | 1 + 11 | README 261；guide 30–98 | — |
| automation pack | `automations/benny/**` | 12 | 23–310 | 3 个操作文件在 240–310 |
| 生成到目标仓库的项目私有组件 | 目标仓库的 `.cursor/skills/verify-<app>/`、用户的 `<handle>-mode`、benny 的 feature map 与 routing map | 由生成方决定 | — | 见 A.11 |

### A.1 mode

- **用途（原文）**
  - `README.md` 第 34 行："it reads your request, picks from a set of playbooks, and runs the other skills as the steps need them."
  - `README.md` 第 91 行："once entered it stays on across turns, applying itself when a playbook matches or the task needs rigor and staying out of the way otherwise."
- **判据**
  - 属于 mode 的内容：
    - 跨所有 playbook 的触发器（"遇到 X 用 Y"）；
    - 原则索引；
    - 自主权边界；
    - 子代理默认值；
    - 回复写法；
    - 代码注释规则；
    - playbook 执行协议与路由表。
  - 不属于 mode 的内容：
    - 具体任务的步骤，这些在 playbook；
    - 能力的做法，这些在技能；
    - 原则全文，这些在 leaf。
  - 原文："The per-playbook lines below name only the content unique to that playbook."（`skills/poteto-mode/SKILL.md` 第 109 行）。这句把通用回复写法留在 mode，各 playbook 的 `**Reply:**` 行只写它独有的内容。
  - mode 的路由目标不只有 playbook。原文第 119 行："A large or cross-cutting effort ... routes to the **figure-it-out** skill even when a narrower playbook like Feature fits"。
- **frontmatter 与布局（原文，L1 2.1）**
  - `name: Poteto Mode`，显示名，与目录名不同；
  - `description`，两句，第二句以 "Use for ..." 开头；
  - `disable-model-invocation: true`；
  - `mode: true`；
  - `icon: crown`、`color: yellow`；
  - `reminder: New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't.`
  - 全插件只有这一个文件带 `mode`、`reminder`、`icon`、`color` 四个键。
  - 目录下挂 `playbooks/`、`references/`、`scripts/` 三个子目录。
- **正文模板（原文，L1 2.1）**
  - 章节顺序：`# Poteto mode` → `## Non-negotiables` → `## Principles` → `## Autonomy` → `## Subagents` → `## Writing the reply` → `## Comments` → `## Playbooks`。
  - `## Non-negotiables`：一段总规则，接着是 "Remaining triggers:" 下的 17 条「条件 → 技能名或 playbook 名」（第 19–35 行）。
  - `## Principles`：分 Core、Architecture、Verification、Delegation、Meta 五组，每条写成 `**显示名** (**principle-slug**). 适用时机. 一句要点.`
  - `## Playbooks`：
    - 先写执行协议（第 117 行，见 D.1）；
    - 再写升级路由（第 119 行，大任务转 figure-it-out，常驻项目转 Orchestrate）；
    - 最后是 23 行路由表。每行写成 `- **<名字>.** <任务类型定义>. [用户原话]. [Distinct from ...]. [交付物限定]. \`playbooks/<file>.md\`.`
  - 范例路径：`skills/poteto-mode/SKILL.md`。
- **语气**：短祈使句，一句一事。正文遵守它自己在 `## Writing the reply` 里的要求（L1）。
- **调用关系**
  - 谁调用 mode：
    - 用户用 `/poteto-mode`；
    - 宿主注入 `reminder`（推断）；
    - `agents/poteto-agent.md` 要求先读 mode 全文；
    - `figure-it-out` 的 todo 第一项是读 mode 的 Principles 一节；
    - `automate-me` 只把它当颗粒度样例读；
    - `setup-pstack` 第 5 步按 mode 的角色标签写配置（"using the same labels poteto-mode uses"）。
  - mode 调用谁：路由到 playbook 和 `figure-it-out`，按名触发技能，索引原则，派 `poteto-agent`。
- **怎样算写错（以 pstack 自身的例外为反例）**
  - 把某个 playbook 的步骤编号写进 mode。原文第 25 行 "(Feature step 3)"、第 30 行 "the narrow Bug fix step 1 exception"：步骤一重排，这些引用就会指错（L1 5.2）。
  - 在触发器列表里塞进多分支的决策程序。第 20 行的 `AskQuestion` 那条先分类、再走 prototype 或 investigation、再看全自主授权（L1 5.2）。

### A.2 playbook

- **用途（原文）**
  - `README.md` 第 85 行："matches your task to a playbook and opens a todo list whose first items are its steps, copied in verbatim."
  - `docs/guide/05-build-and-clean.md`："the playbook supplies the steps you didn't type: reproduce before fixing, name the data shape before implementing, pin behavior before restructuring, profile before optimizing."
  - `docs/guide/02-poteto-mode.md` Pitfall："The playbook already sequences them, and a hand-written sequence usually reorders or drops steps the playbook would have kept."
- **判据**
  - 属于 playbook 的内容：
    - 一类用户任务（按任务类型命名）；
    - 在多个能力和原则之间的先后顺序与门槛；
    - 谁拥有什么；
    - 何时停；
    - 交什么回复。
  - 可以装做法，条件是这些做法只属于这一类任务或这一组 playbook。
    - patch-id 规则单一出处在 `shipping.md` 第 3 步，`autopilot-full.md`、`autopilot-stack.md`、`multi-phase-plan.md` 按文件名引用。
    - forge 选择规则（`gh` 默认、`command -v origin` 探测、不依赖 Graphite）没有单一出处，在 `autopilot-full.md` 第 2 步、`autopilot-stack.md` 第 1 步、`shipping.md` 第 1 步、`babysit.md` 第 1 步、`opening-a-pr.md` `**Forge.**`、`multi-phase-plan.md` 模板 `### PR mechanics` 共 6 个 playbook 里各写一份（L2 4.1、5.1）。
  - 被其他 playbook 复用，不会让一个流程变成技能。原文实例：
    - `babysit.md` 被 `autopilot-full.md` 第 2 步（"the babysit loop to green (`playbooks/babysit.md`)"）、`autopilot-stack.md`、`orchestrate.md` 使用；
    - `opening-a-pr.md` 被 7 个 playbook 在最后一步使用；
    - `prototype.md` 被 mode 第 20 行的触发器和 `multi-phase-plan.md` 第 2 步（"Run `playbooks/prototype.md` for each"）调用。
  - 不属于 playbook 的内容：
    - 要被 mode 之外的入口（用户斜杠命令、自动化、agent 定义、其他技能）复用的能力，应当做成技能；
    - 跨任务的判断，应当做成原则；
    - 按需才查、会增长的目录，应当做成 reference（例如 bugbot-triage）。
- **frontmatter 与布局（原文）**
  - 没有 frontmatter，不注册为技能，不能用斜杠命令调用。
  - 放在 `skills/poteto-mode/playbooks/`，以 `### <名字>` 三级标题开头，文件里没有 H1。
  - 推断：它们原本是 mode 里 `## Playbooks` 下的小节，为按需加载才拆成文件（L1、L2）。
- **正文模板（原文，L1 2.3，L2 第 0 节）**
  1. `### <名字>`
  2. 粗体所有权行 `**You own <对象>. <动词>, <动词>.**`，有时再跟一句委派立场，如 "Delegate ... Stay in the lead."
  3. 可选首段：本类任务的纪律、与相邻 playbook 的界线、与某条原则的关系。
  4. 编号步骤 4 到 9 步，每步首句是一个可以勾掉的祈使动作，后接门槛、例外或理由。
  5. 可选尾段：边界与转交。
  6. 末行 `**Reply:** <本 playbook 独有的回复内容>`。
  - 典型范例：`skills/poteto-mode/playbooks/bug-fix.md`（15 行）。
  - 长 playbook 的范例：`skills/poteto-mode/playbooks/orchestrate.md`（111 行，2636 词）。它的 `#### Steps` 只有 7 行，其余是若干 `####` 规则簇：Roles、Store layout、The brief、Queue and drain、Stack safety、Verification、Liveness and failure、Escalation。只有 `#### Steps` 抄进 todo（L2 2.4、第 7 节）。
- **语气**：第二人称祈使句，大量 "Never / Only / X is not Y" 式的禁令和定义句。理由紧跟在规则后面。原则用括注点名，不展开（L2 第 0 节）。
- **调用关系**
  - 调用方只有两类：mode 的路由表（相对路径），以及其他 playbook（名字、路径或步骤编号）（L1 3.2）。
  - 唯一的例外是能力技能 `recall` 第 1 步把「恢复某个旧聊天」转给 `session-pickup`。这是往外分流，不是调用（L3 3.4）。
  - playbook 调用技能、点名原则、派 `poteto-agent`、跑脚本、读 reference，并把工作交接给其他 playbook。
- **怎样算写错**
  - 格式偏离骨架：`opening-a-pr.md` 没有编号步骤、没有所有权行、没有 Reply 行，实质是一份 PR 约定标准（L1 5.2）。
  - 在一步里塞进多条做法：`feature.md` 第 4 步（L1 5.2）；更严重的是 `autopilot-full.md` 第 2 步和第 6 步、`babysit.md` 第 6 步和第 8 步，各自是几百词的一段。
  - 把被多处引用的概念定义在某个 playbook 内部：throughput checkpoint 定义在 `feature.md` 第 3 步，mode 和另外三个 playbook 都引用它（L1 5.2）。
  - 复述技能的输出格式：`investigation.md` 第 3 步重写了 how 的五节结构（L3 5.2），违反 `authoring-a-skill.md` "Don't restate."

### A.3 能力技能

- **用途（原文）**
  - `README.md` 第 97 行："`/poteto-mode` runs most of these for you when a step needs them ... the table below is for when you want one directly"。
  - `docs/guide/04-design.md`："`/arena` is the general tool underneath"。
- **判据（推断，L3 4.1、L4 4.1，审查时收窄）**
  - 属于能力技能的内容：
    - 一项可以命名的能力，或一个可以命名的交付物；
    - 要能脱离 mode 被直接调用（用户斜杠命令、自动化、agent 定义），或被其他技能复用；
    - 自带的 references、scripts 需要一个目录来放。
  - 编排其他技能并不会让它变成 playbook（`automate-me` 原文见第 0 节）。`figure-it-out` 还是 mode 的路由目标，照样是技能。
  - 不属于能力技能的内容：
    - 按任务类型排的多能力顺序，而且只在 mode 和 playbook 之间复用，应当放在 playbook；
    - 跨任务的判断，应当抽成原则（但见 C.2）。
- **能力技能的形态**（L3、L4 归纳，审查时补充）

  | 形态 | 例子 | 结构特征 |
  |---|---|---|
  | 子代理编排型 | `how`、`why`、`interrogate`、`reflect`、`recall` | `## Step N` 或编号步骤，每步写子代理参数（`subagent_type`、`model`、`readonly`），提示模板放在 references |
  | 阶段型 | `architect`、`arena`、`swarm`、`figure-it-out` | `## Start` 开 todo，然后 `## Phase A..F`。前三个写 "Open a todolist with one entry per phase"；`figure-it-out` 写 "Open a todolist whose first item is to read the Principles section of the **poteto-mode** skill. Then add the phases below as todos." |
  | 编号步骤型 | `tdd`、`teach`、`blast-radius`、`no-comments` | 一个代理自己按编号步骤做，可以调用其他技能（`teach` 跑 how 和 why，`blast-radius` 用 why 和 arena） |
  | 规则目录型 | `unslop`、`technical-writing`、`typescript-best-practices` | 没有步骤或步骤很短，正文是规则。`unslop` 的规则编号是稳定 id："Rule numbers are stable ids that other skills cite. A removed rule leaves a gap." |
  | 格式持有型 | `show-me-your-work`（带 `scripts/log.sh`） | 持有一份被多处共享的产物格式。原文 `## Composing this skill`："Other skills route their audit trail here instead of inventing one. Reference it by name and let it own the format. Don't restate the columns." |
  | 生成器或维护型 | `create-verification-skill`、`maintain-verification-skill`、`automate-me`、`setup-pstack` | 编号步骤，产出另一个技能或配置文件（产物见 A.11） |
  | 平台操作手册型 | `make-bot-ui` | 按平台操作顺序分 H2（`## Create the webhook routine` 到 `## Handle the webhook wake`） |
  | 单条指令型 | `bro`（7 行） | frontmatter 加一段三句话 |

- **frontmatter 与布局（原文）**
  - 键：`name`（等于目录 slug；例外是 `make-bot-ui` 的 `name: Make Bot UI`）、`description`、`disable-model-invocation: true`。
  - 47 个 `SKILL.md` 里只有 `skills/setup-pstack/SKILL.md` 没有 `disable-model-invocation`（L1、L4 的 grep）。
  - 只有 `typescript-best-practices` 带 `paths: ["**/*.ts", "**/*.tsx"]`，它同时带 `disable-model-invocation: true`。
  - `description` 有三种写法：
    1. 动作，加 "Use for/when ..." 触发（多数）；
    2. 只写触发（`tdd`、`make-bot-ui`）；
    3. 只写动作（`no-comments`、`bro`、`unslop`）。
  - 推断：第 3 种都是只靠斜杠命令或按名调用的技能（L4 2.0）。
  - 目录布局：`SKILL.md` 加可选的 `references/`、可选的 `scripts/`。
- **正文模板**
  - 目标段（普通陈述，或一句粗体）。
  - 可选的与兄弟技能分工句，如 blast-radius："`how` tells you what the code does. `why` tells you why it's shaped that way. Blast radius tells you what it breaks somewhere else."
  - Step 或 Phase。
  - 收尾格式有多种写法，没有统一：`## Output Format`（how、why、interrogate）、`## Outputs`、单行 `**Reply:**`（teach 等）、`## Final Response`（tdd）、`## Output contract`（recall）、`## What to hand back`（blast-radius）、`## Outcomes`（maintain-verification-skill）。
  - 范例：阶段型看 `skills/arena/SKILL.md`（71 行）；子代理编排型看 `skills/how/SKILL.md`（56 行）加两份 references。
- **语气**：祈使句、第二人称、短句。子代理参数后面紧跟一句理由，如 reflect 的 "Readonly strips MCPs."
- **调用关系**
  - 谁调用能力技能：mode 的触发器和路由、playbook 的步骤、其他能力技能、agent 定义（`Comment Sicko` 跑 `/how`、`/why`）、用户的斜杠命令、原则（`principle-prove-it-works` 指向 `show-me-your-work`）、benny 的操作文件。
  - 能力技能一般不知道是谁在调用它（L3 3.4）。
  - 能力技能不引用 playbook。唯一例外是 `recall` 的往外分流（L3、L4）。
- **自带人工闸门（原文，很普遍，不算写错）**：能力技能或它的 reference 常常声明自己的人工闸门：
  - `interrogate` Step 2 "If you're unsure about the intent, ask the user before proceeding."；
  - `maintain-verification-skill` 第 0 步 "Several candidates → ask which one"；
  - `architect` Phase C 的可选检查点（"Opt in to a checkpoint when the invoker explicitly asks"）；
  - `setup-pstack` 第 3 步 (c) 请用户确认角色；
  - `make-bot-ui` "If `update_state` shows a confirm card, wait for the user to confirm."；
  - `poteto-mode/references/bugbot-triage.md` "When in doubt, ask."
  - 推断：能力技能可以脱离 mode 单独调用，所以需要自带闸门。
- **怎样算写错**
  - 伸进别的技能内部，引用它的步骤编号：`blast-radius` 写 "Use `why` step 2"；`eval.md` 写 "per the **arena** skill's Phase B"（L3 5.2）。
  - 截断被调用技能的阶段顺序：`no-comments` 第 3 步 "run `/architect` once ... Stop at the sketch. Architect shapes. Step 4 implements."，而 `architect` Phase C 的默认是 "Default: proceed directly to implementation with the synthesized design."
  - 绕过技能本体，直接复用它的内部零件：`recall` 直接用 `why` 的 source investigators（L3 5.2）。
  - 本地闸门或审批政策与 mode 的 `## Autonomy` 或调用它的 playbook 的授权冲突，又没有说明优先级。实例：`bugbot-triage.md` 写 "When in doubt, ask."，而 `autonomous-run.md` 第 4 步写 "Do not park reversible work for the human or use `AskQuestion`."，`autopilot-full.md` 和 `autopilot-stack.md` 在全自主运行里又引用 `bugbot-triage.md`（E.1 第 18 条）。

### A.4 原则

- **用途（原文）**
  - `README.md` 第 196 行："twenty-three short skills, one principle each. `poteto-mode` indexes them inline and reads that index at task start. the standalone files are there so other skills can reference a principle by name, and so the index can point at the full rule for each."
  - `docs/guide/08-principles.md`："You don't invoke principles. You use their names to steer."
- **判据**
  - 原文里唯一明写的分层规则：`principle-encode-lessons-in-structure` "Route to the right layer. One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle."
  - 实际门槛是推断（L5 第 7 节）：
    - 能用短名字说出口；
    - 有可观察的触发情境；
    - 能改变一个具体决定；
    - 跨任务；
    - 作者希望它在每个任务开始时都被看到。
  - 「被按名复用」不是前提。干净的实例只有 `principle-attack-the-premise`：按名引用为 0，内容也没有被别处复用。`experience-first` 和 `test-behavior-not-implementation` 按名引用同样为 0，但内容经 `interrogate/references/rubric.md`、mode 第 105 行、`tdd` 不点名地使用（B.3）。
  - 不属于原则的内容：绑定具体工具、流程或领域参数的规则（见 C.2）；只适用于某一个流程的一步。
- **frontmatter 与布局（原文，L5 2.1）**
  - 23 个文件完全同构：`name: principle-<slug>`、`description: "Apply <when/to/after/before/during> <情境>. <祈使规则摘要>."`、`disable-model-invocation: true`。
  - 没有 references，没有 scripts。
- **正文模板（高频形态，推断归纳，L5 2.2）**
  - `# <Title>`
  - 一到三句规则。
  - `**Why:**` 一到三句后果或成本（23 条里有 16 条）。
  - `**Pattern:**` 类做法 3 到 8 条。标签有七种写法。
  - 可选的判别小节：`**The test:**`、`**Stop:**`、`**Boundaries:**`、`**When it applies:**` 等。
  - 可选的一句区别句，如 "Distinct from ..."。
  - 原则可以带一个短的顺序程序或硬闸门，前提是它跨任务、有触发情境。实例：`principle-encode-lessons-in-structure` 的 `**Pattern:**` 是编号三步（"1. Ask: can this be a lint rule ... 2. If yes, encode it. Delete the instruction 3. If no (requires judgment) ..."）；`principle-attack-the-premise` 的 `**Stop:**` "Do not start the next fix before the premise is written down and the census exists."；`principle-make-operations-idempotent` 的 `**The test:**` 也是编号的。
  - 小节用粗体段首标签，不用 `##`。唯一例外是 `principle-prove-it-works` 的 `## Script the check when you can`。
  - 范例：`skills/principle-attack-the-premise/SKILL.md`（23 行，结构最完整）。
- **语气**：陈述句加祈使句，省略主语；判别问句加引号。多数不含命令、参数、输出格式。
- **调用关系**
  - 原则被这些地方读到（原文）：
    - mode 的索引，任务开始时读；
    - 应用某条原则时读它的 leaf 全文（"Read the leaf skill in full for any principle you apply."）；
    - playbook、技能、reference、其他原则用括注或 `per` 点名；
    - 人在对话里说出原则名。
  - 原则只指向其他原则（13 条边），或往下指向能力技能（2 条：`prove-it-works` → `show-me-your-work`，`type-system-discipline` → `typescript-best-practices`）。它不调用 playbook、脚本或子代理（L5 3.1）。
- **怎样算写错**
  - 引用原则却说不出它改变了哪个决定。原文要求："name each principle that shaped a decision and the specific choice it changed. Cite only principles whose leaf SKILL.md you read this session."（mode `## Non-negotiables`）
  - 原则写进语言或工具细节：`test-behavior-not-implementation` 列 Jest 断言名，`type-system-discipline` 列多语言惯用法。
  - 原则之间内容重叠却不划界：`foundational-thinking` 与 4 条专门原则重叠（L5 5.3）。

### A.5 reference

- **用途**：pstack 没有给 reference 下定义。下表的用法都是从实际写法归纳的，每种都附了实例（L1 4.5、L3 4.5、L4 4.3、L6 4.4）。
- **判据（推断）**

  | 进 reference 的内容 | 实例 |
  |---|---|
  | 原样或填占位后转交给子代理的提示模板，即使每次调用都用 | `how/references/explorer-prompt.md`（开头 "Build ... prompt from this template. Fill in the placeholders."）、`how/references/explainer-prompt.md`（Step 2b 和 Step 3 两条路径都用）、`reflect/references/*.md`（每次调用都读）、`interrogate/references/reviewer-prompt.md`（Step 3 每次都读）、`architect/references/runner-prompt.md` |
  | 只在某个条件下才查的长清单或判断框架 | `interrogate/references/rubric.md`、`lead-judgment.md`、`why/references/epistemics.md`、`architect/references/design-red-flags.md` |
  | 会随使用增长的目录，带追加区 | `poteto-mode/references/bugbot-triage.md`（"Append new candidate learnings here during or after babysitting"） |
  | 产物模板、生成物样例、代码示例 | `architect/references/rationale-template.md`、`create-verification-skill/references/feature-map-example/`、`typescript-best-practices/references/patterns.md` |
  | 随外部环境替换的变体 | `why/references/sources/*.md`，由 `source-playbook.md` 索引 |
  | 适配器契约（调用方点名角色，由配置绑定到具体技能） | `automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md` |

  - 不进 reference、留在正文的内容：步骤顺序、子代理参数、分支条件、何时跳过、输出结构的章节名。即使细节放在 reference 里，正文也要列出章节名（how 和 why 的 `## Output Format`）。
  - 原文判据（`principle-guard-the-context-window`）："Keep frequently used content inline. Templates and references used on every invocation belong in the skill file, not in separate files that cost a read each time."
    - pstack 自己的做法有一个固定例外：要原样或填占位后交给子代理的提示模板，即使每次都用，也放在 reference（上表第一行）。推断：读者是另一个代理，模板要整份转交。原则与做法的这处不一致记在 E.1 第 28 条。
  - `principle-subtract-before-you-add` "When a reference has no novel content, delete it rather than leaving a stub" 是否指技能的 `references/` 文件，原文没有说清：该原则 description 把 "stub references" 与 dead code、redundant validators 并列，`refactoring.md` 第 4 步的 "orphan references" 指代码里的引用。把它当 reference 文件的判据是推断。
- **frontmatter 与布局**：没有 frontmatter，放在所属技能的 `references/` 下，由正文用相对路径 `references/<file>` 点名。
- **正文模板**：
  - 提示模板：先写一段给编排者的说明，`---` 之后是给子代理的第二人称正文，用 `{PLACEHOLDER}` 或 `<PLACEHOLDER>` 占位。
  - 检索指南：固定小节 `What this source contains / How to search it / What good evidence looks like here / Common pitfalls / What to return`（`why/references/sources/*.md`）。
- **调用关系**：通常只被所属技能读。有三种例外：
  - 跨技能共享：`bugbot-triage.md` 被 babysit、autopilot-full、autopilot-stack、multi-phase-plan 引用；
  - 被别的技能借用：`recall` 借 `why` 的 sources；
  - 全文嵌进另一份模板：`reviewer-prompt.md` 用 `{RUBRIC_CONTENTS}` 嵌入 `rubric.md`。
- **怎样算写错**
  - reference 里装完整的子流程：benny 的 `verify-existing-fix.md`（L6 5.2）。
  - 提示模板与实际用法不符：`how` Step 2b 要求去掉 findings 一节再用 `explainer-prompt.md`，但模板开头那句仍假定有多个 explorer（L3 5.2）。

### A.6 脚本

- **术语注意（原文）**：pstack 的 "lever" 不等于脚本。`principle-build-the-lever` description："(codemod, script, generator, or a skill your subagents follow)"；`**Pattern:**` "When you fan work out to subagents, write the lever as a skill they all read"。所以不能用 lever 一词指代脚本这一层。
- **用途（原文）**
  - `principle-encode-lessons-in-structure`："Encode the rule as a lint, metadata flag, runtime check, or script instead of more text."
  - `principle-prove-it-works`："The strongest proof is a deterministic script that re-runs the same comparison, not a one-time eyeball."
- **全部实例**（L2 第 3 节，L4 2.2）

  | 脚本 | 行数 | 调用方 | 性质 |
  |---|---|---|---|
  | `scripts/orch/orch.ts` + `store.ts` | 578 + 1607 | `orchestrate.md` | 只管状态与格式校验，不分类、不派子代理、不唤醒（原文 "The CLI never spawns, waits, or wakes anything."） |
  | `scripts/watch-pr/*` | 入口 6 行，其余 169–832 | `babysit.md` 第 6 步、`shipping.md` 第 8 步 | 只读 GitHub，做合并就绪判定和阻塞优先级 |
  | `scripts/check-plan.mjs` | 186 | `multi-phase-plan.md` 第 6 步 | 只查计划文件的结构与文风 |
  | `scripts/worktree-audit.sh` | 86 | `worktree-cleanup.md` 第 1 步 | 只读收集，给出建议分桶 |
  | `scripts/bootstrap.ts` | 62 | 被 orch 和 watch-pr 导入 | 依赖自举 |
  | `skills/show-me-your-work/scripts/log.sh` | 42 | `show-me-your-work` 正文 | 追加一行格式正确的日志 |

  前五行的路径都相对于 `skills/poteto-mode/`。
- **判据**
  - 组件层面「一条规则要不要做成随插件发布的脚本」，原文依据是：
    - `principle-encode-lessons-in-structure`：触发条件是重复，"When you catch yourself writing the same instruction a second time: 1. Ask: can this be a lint rule, a metadata flag, a runtime check, or a script?"；
    - `reflect/references/synthesizer.md` Structural-mechanism check："route to Backlog when a lint rule, script, metadata flag, or runtime check already enforces the rule or could enforce it cheaply. Skill prose is for things mechanisms cannot enforce."
  - `principle-build-the-lever` 的 `**Balance:**` "The bar is triviality, not repetition." 只管「执行手头这件工作时要不要先写工具」。原文把两者分开："Distinct from Encode Lessons in Structure, which makes a recurring instruction a durable guardrail. This is throughput and reviewability on the work in front of you."
  - 脚本实际出现在四种情形（推断，L2 4.4）：
    1. 多个写者共享、需要跨会话存活的状态（orch，锁加原子写）；
    2. 轮询外部系统并对结果做一致分类（watch-pr）；
    3. 对产物格式做机器检查（check-plan.mjs）；
    4. 批量只读的数据收集（worktree-audit.sh）。
    - 另有一种小情形：手写容易出错、出错后又难发现的机械细节（log.sh 处理表头、制表符、公式注入）。
  - 需要判断、后果不可逆的部分留在文字里。原文 `worktree-cleanup.md` 第 2 步："The bucket is advice, not permission."
  - 已知例外：确定性的机械内容仍留在文字里（原文可见）：
    - forge 选择（`command -v origin` 探测）在 6 个 playbook 里用文字重复；
    - `shipping.md` 第 3 步的 patch-id 比对规程是文字；
    - `reflect` 第 1 步的 transcript 定位是正文里的 bash 片段；
    - `babysit.md` 第 6 步明令不为 Origin 写 watcher 实现："The public watcher remains GitHub-specific, so do not pretend it covers Origin or add an Origin implementation just to run this playbook."
- **布局与接口**：
  - 放在所属技能的 `scripts/` 下。poteto-mode 的脚本共用一个 `scripts/package.json`，由 `bootstrap.ts` 首次运行时自举依赖。
  - 接口约定（原文可见）：默认输出紧凑文本或 JSON，`--json` 或 `--pretty` 切换；错误信息写 stderr；退出码有类型化的含义（orch 0/1/2，watch-pr 0/2–7/64，check-plan 0/1/2）。
  - 调用方式要写在正文里。`create-verification-skill` 对生成物的要求："any script the skill ships is executable and its invocation is shown in the skill body."
- **测试**：orch 和 watch-pr 有 bun 测试（watch-pr 另有编译期类型测试）。check-plan、worktree-audit、log.sh、bootstrap 没有测试（L2）。
- **字面检查器必须持有被匹配的原文**：`check-plan.mjs` 的常量 `RULE` 是 `multi-phase-plan.md` `**Verification.**` 规定的原文（"That sentence is the verification rule. Every verification block opens with it."），第 134 行 `if (b && !b.rest.startsWith(RULE))` 做字面匹配。这是字面检查必然的做法；代价是改这句话时 playbook 与脚本两处要同步改。
- **怎样算写错**
  - 脚本写死本应来自配置的值：`check-plan.mjs` 的常量 `LANES` 把 `Ten lanes on grok-4.7-xhigh-fast` 写死，绕开了模型角色配置（L2 5.1，D.4）。
  - 脚本路径写法不统一：`node pstack/skills/poteto-mode/scripts/check-plan.mjs` 相对仓库根，其他地方的 `scripts/...` 相对技能目录（L2 5.2）。

### A.7 agent 定义

- **用途（原文）**
  - `README.md`："`/poteto-mode` and `subagent_type: "poteto-agent"` route through the same wrapper."
  - `docs/guide/05-build-and-clean.md`（关于 Comment Sicko）："Comments need their own pass, and not from the agent that wrote them."
- **判据（L6 4.6）**。只有两种情况做成 agent 定义：
  1. 需要一个不是作者本人的全新上下文（Comment Sicko）；
  2. 需要保证子代理开工前先加载某个 mode（poteto-agent）。原文 description："Substituting `generalPurpose` skips that read and drifts."
- **frontmatter 与布局（原文）**
  - `agents/<name>.md`，由 `plugin.json` 的 `"agents": "./agents/"` 注册。
  - 键：`name`（即 `subagent_type` 的值，可以带空格，如 `Comment Sicko`）、`description`、可选 `is_background: true`。
- **正文**：尽量薄。
  - `poteto-agent.md` 全文 9 行，正文只指路："Read the `poteto-mode` skill's `SKILL.md` in full before doing any work ... Navigate to a leaf `principle-*` skill whenever you apply that principle."
  - 但它的 description 里带了一条续跑政策："Resume an existing `poteto-agent` for the conversation rather than spawning a sibling." 这与 mode 和 orchestrate 的规则冲突（E.1 第 29 条，D.2）。
  - `comment-sicko.md` 32 行，只装保留清单、判定规则、越权边界、输出格式，执行和修复交给调用它的 `no-comments`。`no-comments` 原文："Pass the scope. Do not restate its rules."
- **调用关系**：由 `Task` 的 `subagent_type` 派生。agent 定义自己也可以调用技能（Comment Sicko 跑 `/how`、`/why`）。
- **怎样算写错**：把规则复制进 agent 文件。这样 agent 文件和 mode 会各有一份规则，逐渐漂移（推断，L6 2.2）。poteto-agent 的续跑政策就是一个实例。

### A.8 配置 / 规则文件

- **`.cursor-plugin/plugin.json`（原文）**
  - 只声明 `"skills": "./skills/"` 和 `"agents": "./agents/"` 两个交付面。
  - `automations/`、`docs/` 不在清单里。
- **`~/.cursor/rules/pstack-models.mdc`（原文，`skills/setup-pstack/SKILL.md` `### 5. Write the rule`）**
  - 由 `setup-pstack` 整文件覆盖写入："Overwrite the whole file so re-runs stay idempotent."
  - frontmatter：`description: pstack per-role model choices (overrides skill defaults)` 和 `alwaysApply: true`。
  - 正文是 `#` 注释行，加上每个角色一行 `<角色标签>: <值>`，共 17 行。标签与 mode 一致（"using the same labels poteto-mode uses"）。格式细节见 D.4。
- **判据（推断）**：配置放在插件目录之外、由技能在运行时写入，这样用户数据不会被插件更新覆盖。benny 用同一思路把用户配置放在 `.cursor/benny/` 或 `~/.config/benny/`（L6 7.4）。项目私有的生成物同理，见 A.11。

### A.9 文档（guide）

- **用途**：给人读，不是 agent 读取的组件。`plugin.json` 不含 `docs/`（L5、L6）。
- **正文的高频形态（原文，L6 2.5；不是固定模板）**
  - H1。
  - 一段引子。句式不统一：`01-setup.md`、`02-poteto-mode.md` 用 "In this page you ..."；`05`、`06`、`09` 用 "This page shows / covers ..."；`03`、`04`、`07`、`08`、`10` 两种都不用（如 `03-understand.md` 第 3 行 "Editing code you don't understand is how subtle regressions ship."）。
  - 配图（快照缺图）。
  - 若干 H2，每个 H2 是一个 `text` 代码块的示例提示词，加一段解释为什么有效。
  - `**Pitfall:**`。
  - `Next:`。
- **语气**：第二人称，Google developer style。写用户怎么说、背后发生什么，不写 agent 的执行步骤。
- **怎样算写错**：guide 复述 playbook 的行为细节。例如 06 写了 Babysit 的顺序 "conflicts, then review threads, then CI"；行为一改，guide 就要跟着改（L6 5.1）。

### A.10 automation pack（benny）

- **用途（原文）**：`README.md` 第 255 行："pstack also ships a dormant benny automation pack ... its files are not registered as slash skills."
- **判据（推断，L6 4.7）**
  - benny 不是一个单一入口。原文 `FOR_AGENTS.md`："i want two cursor automations that work together in one slack issue channel"。两个自动化（triage、reproduce-and-fix）靠 thread 里的标记串接（"then wait for the trusted triage marker in the original thread"），另有一个配置向导 setup-benny。
  - 每个触发式自动化各自一个操作文件，单一入口、单一任务类型，不需要 mode 路由，也不需要 playbook 选择。所以操作文件同时承担 playbook（编号步骤顺序）和技能（每步的做法）两层。
- **布局（原文）**
  - `FOR_AGENTS.md`：前半是第一人称的用户意图，后半 "## for the agent" 是 7 步 bootstrap。
  - `skills/<name>/SKILL.md`：带技能 frontmatter 和 `disable-model-invocation: true`，但不注册，按仓库相对路径读取。
  - `references/`：契约、分支子流程、配置样例。
  - `templates/`：`configuration.example.yaml`（`schema_version: 1`）和两个 automation 提示词模板。
- **操作文件的正文模板**
  - 两个运行时操作文件 `triage-issue-reports`（240 行）和 `reproduce-and-fix-issues`（310 行）：
    - H1 → 两段定位（做什么、不做什么）→ `## Hard safety rules`（分别 14 条和 18 条，最后几条点名原则）→ `## 1.` 到 `## N.` 编号步骤；
    - description 以 "Use only from the configured Benny ... automation" 结尾。
    - 范例：`automations/benny/skills/triage-issue-reports/SKILL.md`。
  - 配置向导 `setup-benny`（266 行）单列：没有 `## Hard safety rules`，H2 从 `## 1. Copy the pack and enable shared pstack skills` 开始；description 以 "Use when installing Benny or changing its ... settings." 触发。
- **如何复用 pstack（原文，L6 7.4）**
  - 共享技能靠目标仓库 `.cursor/settings.json` 的 `"plugins": {"pstack": {"enabled": true}}` 在项目范围内解析，范围原文是 "only for shared dependencies such as `how`, `why`, `tdd`, `unslop`, and the required principle skills"。
  - 对声明为共享依赖的技能按名调用，如 "Use pstack's `how` skill"；原则按名点名，如 "Apply pstack's `principle-…`"。这两类不复述内容。
  - 其他能力仍在操作文件里复述：`reproduce-and-fix-issues` 第 13 步自己写 "smoke the blast radius around the changed behavior. Cover nearby states, inputs, permissions, platforms, and failure paths"，全文不点名 `blast-radius` 技能。
  - 不引用任何 playbook。它的 reproduce 流程与 Bug fix playbook 重叠，也是自己重写的。
  - 控制技能用角色槽位绑定（B.1）：`references/control-adapter.md` "The user must configure one control skill or adapter that implements this contract ... Set its skill name in `control.skill_name`."
- **怎样算写错**：同一条安全规则写在六处。例如 Slack 写禁令，禁止的动作名单在四处逐字重复（L6 5.1）。

### A.11 生成到目标仓库的项目私有组件

pstack 有一类组件不随插件发布，而是由某个技能生成到目标仓库或用户目录，之后由配对技能维护。它们的位置在插件目录之外，与 A.8 的配置同一思路。

| 组件 | 生成方 | 维护方 | 位置 | 出处 |
|---|---|---|---|---|
| 项目私有 verify 技能（含 `features/` 功能地图） | `create-verification-skill` 第 3 步："Create `.cursor/skills/verify-<app>/features/README.md` plus one file per user-facing feature" | `maintain-verification-skill`："This skill is the upkeep loop for a skill generated by `/create-verification-skill`" | 目标仓库 `.cursor/skills/verify-<app>/` | 两个技能的 SKILL.md |
| 个人 mode `<handle>-mode` | `automate-me` | 原文没有写 | 用户的技能目录（推断） | `skills/automate-me/SKILL.md` |
| benny 的配置、feature map、routing map | `setup-benny` | 用户 | pack 目录之外（"i keep user-owned configuration, feature maps, routing maps, and secrets outside `.cursor/automations/benny/`"） | `automations/benny/FOR_AGENTS.md` |
| 模型角色规则 | `setup-pstack` | 重跑 `setup-pstack` | `~/.cursor/rules/pstack-models.mdc` | A.8 |

---

## B. 连线规则

### B.1 连线方式（原文可见）

| 方式 | 写法 | 用在 | 出处 |
|---|---|---|---|
| 相对路径 | `` `playbooks/<file>.md` ``、`` `references/<file>` ``、`` `scripts/<file>` ``、`` `../references/bugbot-triage.md` `` | mode 到 playbook；技能到自己的 reference 和 script；playbook 到 reference 和 script | mode `## Playbooks`；`babysit.md` 第 8 步 |
| 按名字（粗体） | "the **how** skill"；"Run **Opening a PR**."；"the **x** principle skill" | 调用技能；playbook 之间交接；点名原则 | L1 2.3 |
| 斜杠形式 | `/how`、`/create-verification-skill` | 技能正文互相指代；用户调用 | `no-comments`、`setup-pstack` 第 7 步 |
| `subagent_type` | `subagent_type: "poteto-agent"`、`"Comment Sicko"`、`generalPurpose` | 派子代理 | mode `## Subagents` 第 91 行；`no-comments` 第 1 步 |
| 脚本命令 | `bun scripts/orch/orch.ts ...`（文中简写为 `orch`）、`` `scripts/watch-pr/watch-pr` --status-only ``、`node pstack/skills/poteto-mode/scripts/check-plan.mjs <plan.md>` | playbook 到脚本 | L2 第 3 节 |
| 按步骤或阶段编号 | "(Feature step 3)"、"per Autopilot-full step 6"、"the **arena** skill's Phase B"、"Use `why` step 2" | 跨组件引用内部步骤 | L1 5.2、L2 5.2、L3 5.2 |
| 按小节名 | "(see Autonomy)"、"per **Comments**"、"via the control skill (Non-negotiables)" | playbook 引用 mode 的某一节 | L1 2.3 |
| 角色槽位 / 适配器契约 | "the matching control skill"；"via the control skill (Non-negotiables)"；`multi-phase-plan.md` `**Control skill.**` "Pick it by surface"；benny 的 `control.skill_name` | 调用方只点名角色，由宿主、配置或按场景解析到具体技能（cursor-team-kit 的 `control-ui` / `control-cli`，或项目私有的 `verify-*`）。benny 把契约写在 reference 里，缺失时 fail closed | `bug-fix.md` 第 1 步；`automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md` |
| 注入 | `alwaysApply: true` 的规则；`paths:` 触发；`reminder` | 配置进入每个会话；按文件类型加载；mode 保持常驻 | L4 3.1、7.2 |
| 全文嵌入 | `{RUBRIC_CONTENTS}` | 把一份 reference 粘进另一份提示模板 | `interrogate/references/reviewer-prompt.md` |
| 运行中从 trunk 重读组件 | `autopilot-full.md` 第 6 步 "re-read this playbook from trunk with `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-full.md`"；`multi-phase-plan.md` 模板 "Read these from trunk at program start. Re-read them at every tick." | 正在运行的长流程每个 tick 读到仓库里最新发布的 playbook、swarm、opening-a-pr 等 | autopilot-full、autopilot-stack、multi-phase-plan 生成的计划 |

**不能照搬到 MMW 的一种**：「运行中从 trunk 重读组件」与本仓库 `AGENTS.md` 的 Self-hosting boundary 正好相反。MMW 在一次 watch 期间冻结 `~/.mmw/installed-root` 记录的已安装版本，不让运行中的流程读到正在被改的版本。

### B.2 允许的方向

下表把 pstack 里实际出现过的方向，按「常规 / 少见但存在 / 未出现」归纳。归纳是推断，每条都有实例支撑。

| 从 \ 到 | mode | playbook | 能力技能 | 原则 | reference | 脚本 | agent | 角色槽位 |
|---|---|---|---|---|---|---|---|---|
| mode | — | 常规：路由（相对路径） | 常规：触发（按名）；路由到 `figure-it-out` | 常规：索引 | 少见：`bugbot-triage.md` | 未出现 | 常规：`poteto-agent` | 常规：control skill |
| playbook | 少见：引用小节名 | 常规：交接、按文件名或步骤编号引用 | 常规 | 常规：括注 | 常规 | 常规 | 常规：`subagent_type` | 常规："the matching control skill" |
| 能力技能 | 少见：`figure-it-out` 读 Principles 一节；`automate-me` 把 mode 当样例读；`setup-pstack` 按 mode 的角色标签写配置 | 仅往外分流（`recall`） | 常规：横向调用 | 常规 | 常规：只读自己的 | 少见：`show-me-your-work` | 少见：`no-comments` → `Comment Sicko` | 未核实 |
| 原则 | 未出现 | 未出现 | 少见：2 条 | 常规：13 条 | 未出现 | 未出现 | 未出现 | 未出现 |
| reference | 未出现 | 少见：`bugbot-triage.md` 声明它服务于 babysit | 少见：`runner-prompt.md` 让 runner 读 architect | 常规 | 少见：索引、嵌入 | 未出现 | 未出现 | 少见：benny `control-adapter.md` 定义槽位契约 |
| agent | 常规：读 mode | 未出现 | 少见：Comment Sicko 调 how、why | 常规：读 leaf | 未出现 | 未出现 | — | 未出现 |
| 脚本 | 未出现 | 只有 `check-plan.mjs` 检查计划格式（enforces） | 未出现 | 未出现 | 未出现 | 导入、测试 | 未出现 | 未出现 |

**方向上的硬规律**：

1. 原则只指向原则，或往下指向能力技能。
2. 脚本不往上调用任何东西。
3. 能力技能不依赖 playbook。
   - 推断：这是为了能力技能能脱离 mode 使用（L4 3.3）。
   - 旁证：`automate-me` 第 6 步自己写了一句怎么开 PR，而不是引用 `opening-a-pr.md`；benny 完全不引用 playbook。

### B.3 全 pstack 边统计（六份报告的 edges 块合并）

**合并方法**：

- 抽出 L1 到 L6 的 `edges` 块，共 715 行。
- 统一节点名，例如 `playbook:feature`、`poteto-mode/playbooks/feature.md` 都记为 `playbooks/feature.md`；benny 的三个技能都加 `automations/benny/` 前缀。
- 按（源, 目标, 关系）去重后得 550 条；只按（源, 目标）去重得 498 对。

**注意**：各报告的关系词不统一。同一条连线可能在一份里记为 `calls`、在另一份里记为 `routes-to`。所以下面的数字只能看量级和排序，不能当精确值。统计只算按名引用，不点名的内容复用不在其中（见本节末）。

**按关系计数**（去重后）：

| 关系 | 条数 |
|---|---|
| `calls` | 138 |
| `cites-principle` | 118 |
| `routes-to` | 68 |
| `reads-reference` | 52 |
| `spawns-subagent` | 34 |
| `hands-off-to` | 30 |
| `configured-by` | 29 |
| `imports` / `tests` / `runs-script` | 8 / 6 / 7 |
| `requires-installed`（benny） | 6 |
| 引用内部步骤或阶段：`refers-to-step`、`calls-step`、`calls-phase`、`defers-rule-to` | 3 + 1 + 1 + 4 |
| `scopes-principle`（调用方限定原则范围） | 4 |
| `restates-principle` | 1 |
| 其余 22 种 | 各 1 到 5 |

**按组件类型对计数**（去重后，前 12 项）：

| 源 → 目标 | 条数 |
|---|---|
| playbook → 能力技能 | 47 |
| mode → 原则 | 47（23 条索引，加报告间的重复记法） |
| playbook → 原则 | 44 |
| playbook → playbook | 39 |
| playbook → 宿主或外部（`/loop`、`/goal`、cloud agent、`gh`、`gt`、cursor-team-kit） | 36 |
| mode → playbook | 26 |
| 能力技能 → 原则 | 25 |
| 能力技能 → 能力技能 | 23 |
| mode → 能力技能 | 22 |
| 能力技能 → reference | 21 |
| 原则 → 原则 | 13 |
| 能力技能 → 配置 | 13 |

**被按名引用最多的原则**（不同来源数，不计 mode 索引、README、guide；与 L5 3.3 的「功能性引用」逐项吻合）：

| 原则 | 来源数 | 原则 | 来源数 |
|---|---|---|---|
| `principle-prove-it-works` | 12 | `principle-foundational-thinking` | 4 |
| `principle-encode-lessons-in-structure` | 10 | `principle-build-the-lever` | 4 |
| `principle-sequence-verifiable-units` | 10 | `principle-minimize-reader-load` | 4 |
| `principle-laziness-protocol` | 9 | `principle-exhaust-the-design-space`、`subtract-before-you-add`、`never-block-on-the-human`、`model-the-domain`、`type-system-discipline` | 各 2 |
| `principle-separate-before-serializing-shared-state` | 9 | `principle-outcome-oriented-execution`、`make-operations-idempotent`、`migrate-callers-then-delete-legacy-apis` | 各 1 |
| `principle-guard-the-context-window` | 9 | `principle-attack-the-premise`、`experience-first`、`test-behavior-not-implementation` | 0 |
| `principle-boundary-discipline` | 6 | | |
| `principle-redesign-from-first-principles`、`principle-fix-root-causes` | 各 5 | | |

- 引用原则最密集的单个文件是 `playbooks/refactoring.md`，点名了 9 条（L5）。
- **不点名的内容复用**（原文，不在上表）：
  - `principle-experience-first`（"Every feature, control, and option must be justified"；"The engineer who maintains the code next is a user too"）的内容出现在 `interrogate/references/rubric.md` `## Complexity Budget` "Every feature, control, and option should earn its place." 和 mode 第 105 行 "Frame impact for the consumer and the maintainer"。
  - `principle-test-behavior-not-implementation` 的内容出现在 `rubric.md` `## Verification` "Do they test behavior or implementation details?" 和 `tdd` 第 3 步 "The test should encode intended behavior, not mirror the current implementation."
  - `rubric.md` 全文复述了十余条原则的要点，一条都不点名（C.2）。

**被引用最多的能力技能和 agent**（不同调用方数）：

| 组件 | 调用方数 |
|---|---|
| `how` | 15 |
| `unslop` | 13 |
| `why` | 11 |
| `show-me-your-work` | 10 |
| `architect` | 9 |
| `poteto-agent`（agent） | 9 |
| `arena`、`interrogate`、`no-comments` | 各 6 |
| 外部的 `deslop`、`control-ui`、`control-cli` | 各 5 |
| `create-skill`（Cursor 内置） | 4 |

- `recall`、`teach`、`blast-radius`、`bro`、`make-bot-ui` 在 pstack 内没有调用方，只由人用斜杠命令调用（L3、L4）。

**被引用最多的 playbook**：

- `opening-a-pr.md`：7 个 playbook 在最后一步交接给它（visual-parity、authoring-a-skill、bug-fix、refactoring、feature、hillclimb、perf-issue），另有 mode 路由和 `multi-phase-plan.md` 读取。
- `babysit.md`：mode、`autopilot-full.md`、`autopilot-stack.md`、`orchestrate.md`、`shipping.md`（"This is the half after `playbooks/babysit.md`."）。
- `shipping.md`：babysit 交接；autopilot-full、autopilot-stack、multi-phase-plan 引用它的 patch-id 规则。
- `prototype.md`：mode 第 20 行的触发器、`multi-phase-plan.md` 第 2 步。
- 其余 playbook 多数只有 mode 一个调用方。

---

## C. 归类判定流程

### C.1 判定顺序

给定 MMW 里的一段内容，按下面的顺序问，第一个回答「是」的就是它的归属。每一问后面附 pstack 的依据。

1. **它是需要判断、后果不可逆，或需要人拍板的一步吗？**
   - 是，就留在文字里（playbook 步骤或技能正文），不做成脚本。
   - 依据：`worktree-cleanup.md` "The bucket is advice, not permission."；L2 4.4。
2. **它是可以确定性执行或检查、每次结果都一样的机械部分吗？** 包括格式检查、共享状态读写、外部系统的一致分类、批量只读收集、容易写错的字节细节。
   - 是，就可以做成脚本，并且在调用方正文里写出调用命令。
   - pstack 实际的前提：这条规则跨会话共享状态、要轮询外部系统，或是已有机器检查的产物格式，并且有一个稳定的实现对象。否则允许留在文字里（已知例外见 A.6：forge 选择、patch-id 规程、reflect 的 transcript 定位、babysit 拒绝为 Origin 写 watcher）。
   - 组件层面的门槛依据：`principle-encode-lessons-in-structure`（规则反复出现，"the same instruction a second time"，且机制能够强制）；`reflect/references/synthesizer.md` Structural-mechanism check "Skill prose is for things mechanisms cannot enforce."
   - `principle-build-the-lever` 的 "The bar is triviality, not repetition." 只用于「执行某件工作时要不要先写工具」，不用于这一问。
3. **它是一类用户任务从头到尾的顺序，决定了多个能力和原则的先后与门槛，并且有自己的交付物形状吗？**
   - 是，而且只由 mode 路由或只在 playbook 之间复用，就是 playbook（前提是存在一个路由多种任务的入口，见第 7 问）。被多个 playbook 复用不改变这个结论，按文件名引用即可（babysit、shipping、opening-a-pr、prototype）。
4. **它是一项产出可命名交付物、要被 mode 之外的入口（用户斜杠命令、自动化、agent 定义、其他技能）复用的能力吗？** 即使内部有多步、有阶段、还编排其他技能，也算。
   - 是，就是能力技能，内部的步骤留在技能里。
5. **它是跨任务、用短名字就能说出口、有可观察的触发情境、能改变一个具体决定的工程判断吗？**
   - 是，就是原则。但先查第 C.2 节，确认它不应该留在调用方。
6. **它只在某个分支或条件下才需要，或写给另一个读者（子代理、生成物），或会随使用增长，或是模板、样例、适配器契约吗？**
   - 是，就是所属技能的 reference。
   - 每次调用都要用、读者又是本代理的内容，留在正文：`principle-guard-the-context-window` "Keep frequently used content inline."
   - 例外：要原样或填占位后交给子代理的提示模板，即使每次都用，也放在 reference（how、interrogate、reflect 的实际做法，见 A.5）。
7. **它所在的流程是单一入口、单一任务类型吗？**（例如一个定时或触发式的自动化）
   - 是，就不必拆成 mode 加 playbook 加技能。每个触发式自动化各自一个操作文件，按名字引用共享技能和原则；多个自动化之间用外部状态（如 thread 里的标记）串接，不引入 mode 或 playbook 路由（benny，L6 4.7，推断）。
8. **以上都不是，或者拆出去后没有第二个调用方、也不减少重复，就留在原处。** 往已有组件加内容时，按 `reflect/references/synthesizer.md` 的原文规则检查：
   - Existing-skill-first："propose `new skill via create-skill:` only when no existing skill is a real home, the pattern recurs, and the topic deserves its own skill."
   - Decision-changing："a future agent does something different because of the edit, not just reads more text."
   - Already-covered："If the proposal duplicates clear, well-placed existing guidance, reject as `already-covered`."
   - Structural-mechanism check：能由机制低成本强制的，转去 Backlog，不写成技能文字。

### C.2 「不拆」的条件：规则留在调用方正文里

pstack 里有大量规则与某条原则同义，却仍写在调用方里、只点名或完全不点名原则。归纳出几个理由（推断，每条附实例）：

| 理由 | 实例 | 出处 |
|---|---|---|
| **规则绑定了具体机制或领域参数**，不是领域无关的立场。原则写方向，调用方写它在本领域的具体化 | forge 选择与 "Never require Graphite (`gt`)"；patch-id 规则；rebase 时机；「只以副作用计进度」 | L2 4.2 |
| 同上 | benny 的 "No confirmed repro means no authored fix."、"The exact discriminating symptom must appear twice through real UI interaction." | L6 4.3 |
| 同上 | `refactoring.md` 第 1 步 "Type check and lint are not a pin."；`hillclimb.md` 的停机谓词规则 | L1 4.4 |
| **规则的读者读不到原则**，比如跑在别的模型上的子代理。只给指针会失效，所以复述全文 | `interrogate/references/rubric.md` 复述了十余条原则的要点，一条都不点名（可对上 make-operations-idempotent、separate-before-serializing、fix-root-causes、encode-lessons-in-structure、boundary-discipline、foundational-thinking、redesign-from-first-principles、migrate-callers、test-behavior、prove-it-works、outcome-oriented-execution、experience-first 等），它的全文经 `{RUBRIC_CONTENTS}` 粘进 reviewer 提示 | L3 4.4，L5 4.3，审查核对 |
| 同上，折中写法：先复述要点，再点名原则 | `architect/references/runner-prompt.md` "Idempotent state transitions where applicable, per the **make-operations-idempotent** principle skill." | L5 5.4 |
| **只有一个调用方**，抽出去没有复用价值 | `prototype.md` "No decision means no prototype."；`eval.md` 的盲测七条 | L1 4.4 |
| **规则带着具体清单或会话级授权**，比原则细 | mode `## Autonomy` "**Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages."，以及 "Session overrides" | L1 4.4，L5 4.3 |

**mode `## Autonomy` 与 `principle-never-block-on-the-human` 是冲突，不只是重叠（原文）**：

- 原则 `**Boundaries:**`："Irreversible actions (force-push, delete production data, send external messages) still require confirmation."
- mode 第 81 行："Reversible work and external actions (team chat, ticket updates, kicking off evals) proceed without asking."；只对 "customer messages" 暂停。
- mode 的清单比原则更细，而且放宽了原则的规定；pstack 没有写明哪一层优先。归置 MMW 时要显式写出优先级。

**调用方可以限定原则的范围，因此不必为每个例外改写原则（原文）**：

- `skills/no-comments/SKILL.md` 第 22 行："The **principle-fix-root-causes** and **principle-redesign-from-first-principles** skills guide intent only. Neither authorizes widening the fence nor fixing instances outside it."
- `playbooks/prototype.md`："The one playbook where the Laziness Protocol's 'smallest change' and the verification bar invert."
- `playbooks/feature.md` 第 4 步："Mandatory: no skip-with-reason escape, and Laziness Protocol does not override it"。

**不为凑数造原则**：

- 原文里唯一的分层规则是 "One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle."（`principle-encode-lessons-in-structure`）。
- pstack 没有为 transcript 隐私边界、prompt 注入防护、「引用而不内联」这类反复出现的操作规则建原则，而是让它们留在各自的技能里重复写（L4 4.2）。「might help 就回退」也是这样（C.5）。

### C.3 「不拆」的条件：多步内容留在能力技能内部

| 技能 | 内部流程 | 不拆的理由 |
|---|---|---|
| `architect` | Phase A–E，依次调用 how、arena、（可选）interrogate | 这是「一次设计比较」的做法，与任务是 bug 还是 feature 无关；被 bug-fix、perf-issue、feature、refactoring、prototype、figure-it-out、no-comments 复用（L3 4.1） |
| `arena` | Phase A–F | 被 architect、blast-radius、figure-it-out、eval、feature、orchestrate 调用 |
| `how` | Step 1、2a、2b、3、4 | 步骤内容是怎么派子代理、用什么提示、怎么合并结果，不是任务先后（L3 4.1 第 4 条） |
| `why`、`interrogate` | Step 1–5 | 同上 |
| `reflect`、`create-verification-skill`、`tdd`、`no-comments` | 1–6 步 | 流程服务于一个可以命名的交付物，拆开后单独的一步没有用处（L4 4.1 第 1 条）。`no-comments` 串 Comment Sicko、how/why、architect |
| `teach` | 1–5 步，串 how 和 why | 交付物是一份解释；用户直接调用 |
| `automate-me` | 0–6 步，编排三个其他技能 | 原文 "It sequences them. It doesn't replace them."；它是用户能直接调用的独立任务，不是 mode 下的一类工作 |
| `figure-it-out` | Phase A–E | 它的内容是「写一份 playbook 的方法」，对任何任务类型都适用。原文 "When the task matches no playbook, design one."（L3 4.2）。它同时是 mode 按任务规模路由到的目标（mode 第 119 行） |

**共同判据（推断，审查时改写）**：流程产出一个可以命名的交付物，并且这项能力能脱离 mode 被用户斜杠命令或多个调用方直接调用，就留在技能里，不论它内部调用了多少其他技能。步骤是否跨越多项能力、是否由任务类型触发，都不是判据：architect、automate-me、teach、no-comments 的步骤都跨越多项能力，figure-it-out 还由 mode 按任务规模路由。

**形式上的对应（原文）**：阶段型技能的 `## Start` 待办清单，和 mode 的 "Open a todolist whose first items are the matched playbook's steps" 是同一种做法。所以「它有 todo 和阶段」不能作为把它拆成 playbook 的理由。

### C.4 「不拆」的条件：长内容留在 playbook 里

按词数，长 playbook 有 `orchestrate.md`（2636 词）、`multi-phase-plan.md`（2186 词，其中模板 138 行）、`autopilot-full.md`（1436 词，只有 13 行）、`babysit.md`（1291 词）、`shipping.md`（913 词）。其中 orchestrate 的 brief 模板、store 布局、drain 协议、恢复规程，multi-phase-plan 的计划模板，autopilot-full 和 babysit 的长步骤，都没有拆成技能或 reference。理由如下：

| 理由 | 依据 |
|---|---|
| 只有一个调用方，拆出去不减少重复 | L2 第 7 节第 1 条（推断） |
| 它就是这个 playbook 的产物 | 原文 `orchestrate.md` "The brief is the product."；`multi-phase-plan.md` "The plan is the deliverable. Do not implement." |
| 执行中要被从 trunk 重读 | 原文：`autopilot-full.md` 第 6 步每个 tick 用 `git show origin/main:...` 重读自己；`multi-phase-plan.md` 生成的计划要求每个 tick 从 trunk 重读执行 playbook、swarm 等。`orchestrate.md` 每次 spawn 和 resume 原样粘贴的是 standing orders（`preferences.md`），不是 playbook 本身（"Every spawn and every resume carries the standing orders verbatim."）。orchestrate 与 multi-phase-plan 自身是否被整份重读，原文没有写；「拆散会增加每次 tick 要读的文件数」是推断 |
| 降级路径要求自足 | 原文 `orchestrate.md` 第 60 行："Collapsing must not depend on another document being present." |
| 作者试过、并且明确放弃了固定结构 | 原文 `orchestrate.md` 第 19 行："Hard-coded swarm trees were tried and parked as too rigid."，以及 "Author the track decomposition per project" |
| 机械部分已经拆出去，留下的是判断 | 文件格式、锁、原子写、verdict 枚举进了 `scripts/orch/`；何时排空、如何分类、何时升级留在文字里（L2 第 7 节第 4 条） |
| 模板有机器检查，拆出去不增加任何保障 | `check-plan.mjs` 直接检查计划文件（L2 4.3） |
| 规模必须随任务伸缩，不能固定成仪式 | 原文 `orchestrate.md` 第 5 行："Ceremony must scale with the program. On cheap near-identical units, collapse it as each section directs." |

**这也说明**：playbook 长，不等于要拆。长度来自「多个代理 + 跨会话 + 共享状态」这三个条件，每多一个条件就多出一类内容：角色、存储与单一写者、恢复、升级边界（L2 第 7 节，推断）。

### C.5 「不拆」的条件：可以接受的重复

pstack 有两种单一出处的写法，与逐字复制并存（L2 5.1）：

- 单一出处加引用：patch-id 规则放在 `shipping.md` 第 3 步，其他文件按文件名引用；`autopilot-stack.md` 按步骤编号引用 autopilot-full。
- 逐字复制：
  - forge 选择规则在 6 个 playbook 里近乎逐字出现（A.2）；
  - owner 生命周期在 autopilot-full 和 autopilot-stack 里大段相同；
  - 「might help 就回退」在 4 个 playbook 里各自重写：`bug-fix.md` 第 5 行 "Belt-and-suspenders that 'might help' is a hypothesis, not a fix."、`autonomous-run.md` 第 3 步 "Belt-and-suspenders that \"might help\" gets reverted, not left to ride."、`refactoring.md` 第 4 步 "A speculative cleanup that \"might help\" gets reverted."、`hillclimb.md` 第 5 步 "A tweak that \"might help\" is not kept."。一条规则在多个 playbook 里重复，也可以不抽成原则。

**读者是只读一份文件的独立代理时，接受复制（推断，只适用于部分实例）**：

- autopilot 的 owner 是云代理，只看自己的 brief（L2 5.1）；
- why 的每份 `sources/*.md` 单独交给一个 investigator，所以 "Instrumented != caused" 这类告诫写了两遍（`datadog.md` 第 89 行、`databricks.md` 第 54 行）；
- reflect 的三份 reviewer 提示（`judgment-reviewer.md`、`tooling-reviewer.md`、`divergent-reviewer.md`）里 prompt 注入防护逐字相同，`synthesizer.md` 的是同义改写，针对 reviewer outputs（L4 2.1）。

这条推断解释不了 forge 规则的复制：babysit、shipping、opening-a-pr 由同一个主代理在同一上下文里先后读取（`shipping.md` "This is the half after `playbooks/babysit.md`."）。forge 规则为什么复制而不引用，原因未确定（F.4）。

**写作时必须一直生效的规则：点名持有者，同时复述最关键的几条（原文）**：

- mode `## Writing the reply` 第 99 行："Write the reply clean as you draft it. A cleanup pass after drafting does not remove these patterns." 随后复述 unslop 的规则并注明出处，如第 103 行 "**A colon as a mid-sentence connector is also out** (unslop rule 14)."，同时 mode 第 26 行仍触发 unslop。
- `technical-writing` "Replace an em dash with a new sentence."，同时 "Apply the **unslop** skill to every doc this skill touches."
- `multi-phase-plan.md` 第 5 步 "No long dashes. No mid-sentence colons."，同时要求 "then `/unslop`"。
- 写法要点：复述时点名规则的持有者（mode 的 "(unslop rule 14)" 写法），不改写规则本身。

**其他情况要求引用，不要复述（原文）**：`authoring-a-skill.md` "Delegate to other skills by path. Don't restate."；`show-me-your-work` "Reference it by name and let it own the format. Don't restate the columns."；`no-comments` 对 Comment Sicko "Pass the scope. Do not restate its rules." 这不是「同一上下文就一律只引用」的硬规则，上面两类例外都存在。

### C.6 形式拆散的信号（用来检查下一轮的归置方案）

有原文依据的信号（`reflect/references/synthesizer.md`）：

1. 新建组件前没有先确认已有组件不是合适的归宿，或者模式并不反复出现（Existing-skill-first）。
2. 新增内容不会让未来的代理做出不同的事，只是让它多读文字（Decision-changing）。
3. 新增内容重复了已有的、位置得当的指引（Already-covered）。
4. 本可以由脚本、lint、元数据或运行时检查强制的规则，被写成了技能文字（Structural-mechanism check）。

推断出的信号（由前文依据反推）：

5. 拆出的 playbook 只调用一个技能，没有自己的门槛、所有权或交付物。pstack 的每个 playbook 都有所有权行和 `**Reply:**`，只有 `opening-a-pr.md` 例外。
6. 拆出的 reference 每次调用都要读，只有一个调用方，而且读者是本代理自己。要整份转交给子代理的提示模板不算（A.5 的例外）。
7. 新建的原则说不出它会改变哪个决定，或者只适用于某一个流程的一步。原则带顺序步骤本身不是问题（A.4）。
8. 拆完后，调用方需要按步骤编号引用被拆出的部分。pstack 自己这样做过，而且这正是它最脆弱的连线（第 E 节）。
9. 拆出的内容没有第二个调用方，也没有减少任何重复。
10. 为了套分层，把一个单入口的固定流程拆成 mode 加 playbook 加技能三层。benny 的做法恰恰相反（L6 4.7）。
11. 为了套分层，把只在任务流程之间复用的内容做成能力技能。pstack 把 babysit、shipping、opening-a-pr、prototype 都留作 playbook。

---

## D. 状态、重入与配置

### D.1 todo 抄写与 skip

- **协议（原文，`skills/poteto-mode/SKILL.md` 第 117 行）**："Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`."
- **理由（原文）**
  - `docs/guide/01-setup.md`："so you can see what it chose not to do"。
  - `docs/guide/02-poteto-mode.md` Pitfall：手写的顺序 "reorders or drops steps"。
- **变体（原文）**
  - `feature.md` 第 3 步定义 throughput checkpoint 的四项，不适用的保留为 `n/a: <reason>`。
  - investigation、runtime-forensics、trace-forensics 把 throughput checkpoint 写成一条固定的 `n/a` 行。
  - `feature.md` 第 4 步的 arena 委派："Mandatory: no skip-with-reason escape"，即禁止跳过。
- **能力技能内的 todo（原文）**
  - architect、arena、swarm 在 `## Start` 里写 "Open a todolist with one entry per phase"。
  - figure-it-out 的 `## Start` 不同："Open a todolist whose first item is to read the Principles section of the **poteto-mode** skill. Then add the phases below as todos." 它还把自己设计出的步骤插进 Phase C 之后、Phase D 之前。
  - 能力技能没有自己的 skip 写法。推断：沿用 mode 的规则（L3 第 6 节）。
- **什么进 todo（推断，L2 第 0 节）**：只有编号步骤进 todo。步骤之外的规则簇（orchestrate 的 `####` 小节）和模板（multi-phase-plan）是执行时查阅的常设规则或输出格式，不进 todo。
- **重新匹配（原文）**：用户说 "new task" 才重新匹配（`docs/guide/02-poteto-mode.md`）；`reminder` 的开头就是 "New task?"。

### D.2 Session pickup 与 Pause safely（原文，L2 2.7、2.8）

**`playbooks/session-pickup.md`**（11 行）是重入的入口：

1. 定位旧记录，只看本工作区的 `agent-transcripts/`。明令不跨 `~/.cursor/projects/*/` 读，理由是会读到无关项目的私聊。长记录交给子代理解析，并点名 `principle-guard-the-context-window`。
2. 重建状态。原文 "The prior trail is authoritative input."，不重做已经做过的事。
3. 对比已做与待做。
4. 路由到匹配的 playbook，并选定结论类型：继续执行、交付、批准或推翻、事后分析。原文 "The pickup playbook ends here. The routed playbook owns the rest."
5. 在真实产物上验证继承来的结论，点名 `principle-prove-it-works`。

**`playbooks/pause-safely.md`**（10 行）是暂停的出口，原文 "This is explicit only."：

- 在安全边界停下，取消嵌套的子代理；
- 不做不可逆动作；第 2 步 "No PR and no push unless you already had one out."；
- 把未提交改动提交成一个 `wip:` commit；
- 把恢复笔记写到上下文之外。压缩触发时写 `/tmp/<slug>-resume.md`；已经有 show-me-your-work 记录的，就指向它，不复制。

**`skills/recall/SKILL.md`**：跨会话重建上下文的轻量工具。第 1 步把「恢复某一个具体的旧会话」分流给 session-pickup。

**被中断后续跑的子代理：pstack 在这一点上不一致（原文）**：

- mode 第 95 行："Interrupt-chained resumes silently drop directives, so fire a fresh subagent with consolidated scope rather than trusting a 'done' summary."
- `orchestrate.md`："Never resume-chain a brief. Respawn fresh with consolidated scope."
- 相反：`agents/poteto-agent.md` description "Resume an existing `poteto-agent` for the conversation rather than spawning a sibling."
- 两边说的场景不完全相同（前者是被中断后续跑，后者是同一对话里要不要再开一个），但原文没有划界，也没有写谁优先（E.1 第 29 条）。

### D.3 orchestrate 的存储（原文，L2 2.4、3.1）

- **位置与写者**：`orchestrate/<project-slug>/`，建在当前 agent 的 store 里。原文 "Every file has exactly one writer."
- **文件**：
  - 由 orch 管理：`units.tsv`、`ledger.tsv`（以 PR 加 SHA 为键，同键覆盖）、`inbox/*.tsv`、`gates.md`、`preferences.md`（编号行）、`frontier.json`（每次 set 代数加 1）、`status.md`（由 `status` 生成）。
  - 不由 orch 创建，但 playbook 要求有：`overview.md`、`decisions.tsv`。
- **写入机制**：临时文件加 `rename` 原子写；`.orch.lock` 里写 pid，持锁进程已死则自动替换，否则报错，除非加 `--force`；`init` 幂等。
- **协议**：原文 "State reads and writes go through scripts/orch/orch.ts at drain points, one command in and one line out." 排空回合以 `orch status` 的三行结束。
- **恢复**：Cursor 重启后，按以下顺序恢复：
  1. 重读 standing orders 与 `units.tsv`；
  2. 重算 frontier；
  3. 按 PR 和分支（而不是 agent id）重新挂接云端工作；
  4. 按存储的 brief 加当前状态，重派每个 track 的子协调者。
- **收尾**：原文 "Leave the store intact. It is the postmortem."
- **已知缺口（推断，L2 3.1）**：playbook 要求 "write a stop line at the top of the standing orders"，但 `orch standing add` 只能追加到末尾，而 `readStanding` 要求编号连续。

**其他持久状态**：

| 位置 | 内容 | 出处 |
|---|---|---|
| `show-me-your-work` 的 `decisions.tsv` 或 `.audit/<task-slug>.tsv` | 六列 `ts phase decision why evidence result`，只追加（"A wrong call gets a new row that supersedes it."），默认不提交 | L4 2.2 |
| `hillclimb.md` 的 `decision.tsv` | 另一套列，gitignored，每次尝试前读回 | L1 第 6 节 |
| autopilot | `/goal` 跨回合延续，每个 tick 从 trunk 重读 playbook（B.1） | L2 第 6 节 |
| benny | 冻结坐标、按 permalink 去重、补偿动作、有界的跟进窗口；两个自动化靠 thread 里的 triage marker 串接 | L6 第 6 节 |

### D.4 模型角色配置如何被读取（原文，L4 7.2、L3 3.3）

- **写入**：`setup-pstack` 第 5 步整文件覆盖 `~/.cursor/rules/pstack-models.mdc`，frontmatter 带 `alwaysApply: true`，角色标签与 mode 一致。
- **格式**：
  - `#` 注释行说明两件事：删掉某行就回到技能默认值；`inherit-parent` 或 `auto` 表示省略 Task 的 `model` 字段。
  - 另有一行预算记录，如 `# budget: unlimited (max)`。
  - 每个角色一行 `<角色标签>: <值>`。几个角色共用一个值时写在同一个标签里，如 `feature, refactoring:`。
  - 面板角色只有三个：`arena runners`、`architect runners`、`interrogate reviewers`。它们的值是列表，列表长度就是扇出的子代理数（`setup-pstack` `### 3. Budget, map, and confirm` (c)："For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry ... so the list length sets the count."）。
  - `arena cross-judge pool` 也是列表，但它是候选池："Arena selects one value from it whose model family differs from the parent's when possible."；`arena` `## Phase C: Cross-judge` "choose one model from the `arena cross-judge pool`"。
- **读取有三种写法，彼此不统一**：
  1. 点名文件和角色行：arena "Use `arena runners` from `~/.cursor/rules/pstack-models.mdc` when present"；swarm；interrogate。
  2. 只写 "your configured <角色> model (default `<slug>`)"：how、why、architect、reflect，以及 bug-fix、perf-issue、hillclimb、feature、refactoring 五个 playbook。推断：这依赖 `alwaysApply` 把规则注入每个会话。
  3. 只描述档次：recall 写 "on a fast, cheap model"，没有对应的角色行。
- **优先级（原文，mode `## Subagents`）**："Per-role lines in the `/setup-pstack` rule override these defaults and the model choices in the routed skills"。
- **缺省回退**：每个消费方都在自己的正文里写默认 slug。默认值因此分散在 `setup-pstack` 第 5 步、各技能正文、mode `## Subagents` 三类地方（L4 5.1）。
- **没有任何脚本解析这个文件**，标签的对应全靠模型自己理解：技能写 `how-explorer`，规则写 `how explorer:`（L3 3.3，L4 5.2 第 8 条）。
- **绕过配置的地方**：`multi-phase-plan.md` 和 `check-plan.mjs` 的 `LANES` 把 live lane 的模型写死为 `grok-4.7-xhigh-fast`，填其他值时 check-plan 会报错（L2 5.2 第 8 条）。
- **生效时机（原文，`docs/guide/01-setup.md`）**："The model rule applies to new sessions."

---

## E. pstack 自身的不一致与例外，以及 Cursor 专有机制

### E.1 不一致与例外（逐条出处）

1. **原则引用至少有五种写法**（L1 2.3、L5 3.2，审查补充）：
   - 粗体名加 "principle skill"，如 "the **prove-it-works** principle skill"；
   - 带前缀的粗体 slug，如 `**principle-model-the-domain**`；
   - 带前缀的粗体 slug 加 "skill" 放在括号里，如 `trace-forensics.md` "(the **principle-guard-the-context-window** skill)"、`session-pickup.md` "(the **principle-prove-it-works** skill)"；
   - 不加粗、带前缀的 slug 放在括号里，如 `worktree-cleanup.md` "(principle-build-the-lever)"、`orchestrate.md` "(principle-separate-before-serializing-shared-state)"；
   - 相对 Markdown 链接，只在原则之间和 guide 里用；
   - 纯文本名，如 `arena` 的 "per the Laziness Protocol"。
2. **按步骤或阶段编号的跨组件引用，没有任何检查**（L1 5.2、L2 5.2、L3 5.2）：
   - mode → "Feature step 3"、"Bug fix step 1"；
   - `autopilot-stack.md` → "Autopilot-full step 2/4/6"；
   - `eval.md` → arena 的 "Phase B/C"；
   - `blast-radius` → "`why` step 2"。
3. **"Invoked at the end of every other playbook." 与实际不符**（mode 第 143 行、`opening-a-pr.md` 第 3 行）：22 个其他 playbook 中只有 7 个以 Opening a PR 收尾（visual-parity、authoring-a-skill、bug-fix、refactoring、feature、hillclimb、perf-issue）。其余 15 个不运行它：investigation（"No PR"）、runtime-forensics、trace-forensics、prototype、eval、session-pickup、pause-safely（"No PR and no push unless you already had one out."）、autonomous-run、babysit、shipping、autopilot-full、autopilot-stack、orchestrate、multi-phase-plan（"The plan is the deliverable. Do not implement."）、worktree-cleanup。
4. **`opening-a-pr.md` 名为 playbook，实质是标准**：没有编号步骤、所有权行、Reply 行（L1 5.2）。
5. **playbook 里装了与流程无关的技术目录**：`perf-issue.md` 第 2 步的八个策略族（L1 5.2）。
6. **跨 playbook 复用的概念定义在一个 playbook 的某一步里**：throughput checkpoint 定义在 `feature.md` 第 3 步（L1 5.2）。
7. **orchestrate 依赖 Graphite，其他 PR 类 playbook 禁止依赖**：`orchestrate.md` `#### Stack safety` 要求 `gt`，`orch frontier set` 也只能经 `gt` 取得 stack。babysit、shipping、autopilot-full、autopilot-stack 写 "Never require Graphite (`gt`)"，multi-phase-plan 写 "Never require `gt`"，opening-a-pr 写 "Do not require Graphite (`gt`)"（L2 5.2 第 7 条）。
8. **`show-me-your-work` 声明自己持有日志格式，但 `hillclimb.md` 第 3 步自定了列**，文件名也不同（`decision.tsv` 与 `decisions.tsv`）（L4 5.2）。
9. **mid-sentence colon 规则覆盖所有 prose，多个 playbook 正文违反（已核实）**：
   - mode 第 26 行 "Any prose surface → the **unslop** skill. ... Agent-facing prose also follows the **create-skill** skill"；`unslop` description "Cut AI tells from any writing."，规则 14 "Not as mid-sentence connectors."；`multi-phase-plan.md` 第 5 步对计划文件也要求 "No mid-sentence colons."，`check-plan.mjs` 执行这条。
   - 违反实例：`orchestrate.md` 第 17 行 "needs this machine: `control-ui`"；`opening-a-pr.md` 第 5 行 "Dirty branch with unrelated work: patch out, fresh worktree, apply."（L2 5.2 第 9 条）。
10. **违反 `unslop` 的其他规则**：
    - 规则 17（标题用 sentence case）：`tdd` 用 Title Case 标题；
    - 规则 13（"Avoid em dashes entirely"）：`create-verification-skill`、`maintain-verification-skill`、`setup-pstack` 用了 em dash（L4 5.2）；
    - `poteto-mode/references/bugbot-triage.md` 追加区第 98、107 行的 em dash 同样违反规则 13（经 mode 第 26 行适用于所有 prose）。
11. **`unslop` 的 description 写 "Must always apply."，frontmatter 却是 `disable-model-invocation: true`**。实际靠 mode 的触发行和其他技能按名引用来保证（L4 5.2）。
12. **原则层反向指向能力技能**：`principle-prove-it-works` → `show-me-your-work`（L4 5.2、L5）。
13. **原则之间内容重叠，多数没有划界**：`foundational-thinking` 与 separate-before-serializing、subtract-before-you-add、sequence-verifiable-units、test-behavior 重叠（L5 5.3）。
14. **原则的一句话摘要在四处重复**：description、mode 索引、README 表格、`08-principles.md`，措辞不一（L5 5.1）。
15. **原则格式不统一**：`**Why:**` 只有 16/23 有；做法小节的标签有七种写法（L5 第 7 节）。
16. **"brain note" 没有定义**：`principle-encode-lessons-in-structure` 用了它，全 pstack 找不到定义（L5 5.5）。
17. **没有脚本检查「引用了原则就必须改变一个决定」**。这与 `principle-encode-lessons-in-structure` 自己的主张不一致（L5 4.4）。
18. **能力技能的本地闸门或审批政策与上层授权冲突，没有写明优先级**：
    - `bugbot-triage.md` "When in doubt, ask." 与 `autonomous-run.md` 第 4 步 "Do not park reversible work for the human or use `AskQuestion`." 冲突，而 `autopilot-full.md`、`autopilot-stack.md` 在全自主运行里引用 `bugbot-triage.md`；
    - `no-comments` 第 5 步、`reflect` 第 5 步、`show-me-your-work` 的 Attention 小节，与 mode `## Autonomy` 各自维护、彼此不引用（L4 5.2）。能力技能自带闸门本身不算错（A.3）。
19. **调用方改写被调用方的默认策略**：`teach` 要求 "Keep `why` narrow by default"，但 why 允许跳过某类来源的两条理由里并没有「调用方要求收窄」这一条（L3 5.2 第 4 条）。
20. **实现归属不清**：
    - architect Phase D "Implement against the sketch" 与 `feature.md` 第 4 步的委派实现，都在描述实现，没有写清由谁负责（L3 5.2 第 5 条）；
    - `no-comments` 第 3 步要求 architect "Stop at the sketch. Architect shapes. Step 4 implements."，截断了 architect Phase C 的默认 "proceed directly to implementation"。
21. **"playbook" 一词两义**：`why/references/source-playbook.md` 和 `recall` 的 "per-source playbooks" 指按来源的检索指南，不是 mode 的 playbook（L3 5.2 第 9 条）。
22. **三套裁决词汇并存**：
    - swarm：`PASS` / `ISSUES` / `BLOCKED`；
    - figure-it-out：`VERIFIED` / `NOT VERIFIED` / `INCONCLUSIVE`；
    - interrogate：Act on / Consider / Noted / Dismissed；
    - orch ledger：另有五个 verdict 值（L3 5.2 第 8 条，L2）。
23. **冗余的防御性指令**：`shipping.md` 第 8 步的 "ignoring `READY`" 在 queued-stack 模式下是冗余的。`watch-pr/types.ts` 的 `Terminal<"READY", 0, "single" | "stack">` 保证 queued 模式不会发出 `READY`，`babysit.md` 第 6 步也写明 "Queued mode never emits `READY`."。不算不一致（L2 5.2 第 10 条）。
24. **一条教训留在文字里，没进脚本**：`worktree-cleanup.md` 第 2 步记下 "The lever has marked safe a worktree the user had pinned"，但 `worktree-audit.sh` 不知道 pin 状态。推断：pin 信息在 Cursor 侧边栏，脚本读不到（L2 5.2 第 11 条）。
25. **benny 的操作文件把 playbook 和技能压成一层**，reference 里装了完整子流程（`verify-existing-fix.md`），用文字描述本可以脚本化的机械步骤（L6 5.2）。
26. **`name` 与目录名不一致**：`poteto-mode`（`Poteto Mode`）、`make-bot-ui`（`Make Bot UI`）（L1、L4）。
27. **外部插件依赖没有安装检查**：`deslop`、`control-cli`、`control-ui` 来自 `cursor-team-kit`，只在 README `## not shipped here` 里列出（L1 5.2、L6 2.4）。
28. **`principle-guard-the-context-window` 与 how、interrogate、reflect 的实际做法不一致**：原则写 "Templates and references used on every invocation belong in the skill file"，而 `how` 的 `explainer-prompt.md`（Step 2b 和 Step 3 都用）、`interrogate` Step 3 的 `reviewer-prompt.md`、`rubric.md`、`code-quality-review.md`、`lead-judgment.md`、`reflect` 的四份 reference 都是每次调用都读、只有一个调用方的 reference。
29. **agent 定义的续跑规则与 mode、orchestrate 冲突**：`agents/poteto-agent.md` description "Resume an existing `poteto-agent` for the conversation rather than spawning a sibling."；mode 第 95 行 "fire a fresh subagent with consolidated scope rather than trusting a 'done' summary"；`orchestrate.md` "Never resume-chain a brief. Respawn fresh with consolidated scope."（D.2）。
30. **mode `## Autonomy` 放宽了 `principle-never-block-on-the-human`**：原则要求 "send external messages" 前确认，mode 第 81 行让团队聊天等外部动作直接执行（C.2）。
31. **README 与 guide 对 `typescript-best-practices` 的说法不一致**：`README.md` 第 128 行把 `/typescript-best-practices` 列成斜杠命令；`docs/guide/05-build-and-clean.md` 第 47 行 "has no slash command in your workflow. It loads whenever the agent touches a `.ts` or `.tsx` file"。

### E.2 Cursor 专有机制（换宿主时需要替换）

| 机制 | 在 pstack 里的作用 | 出处 | 换宿主要解决的问题 |
|---|---|---|---|
| `mode: true` | 把 mode 技能标成常驻 | mode frontmatter | 原文没有定义语义（推断为常驻）。其他宿主需要一个每轮都在上下文里的等价物 |
| `reminder:` | 每轮用一句话判断是否重新应用 mode（推断） | mode frontmatter | 需要宿主的每轮注入机制，例如 hook 或常驻规则 |
| `disable-model-invocation: true` | 不让模型按 description 自动触发，调用权集中在 mode 和 playbook | 46/47 个 SKILL.md | 部分证据：`automate-me` 第 73 行 "Frontmatter `disable-model-invocation: true` by default. Opt out only if the user explicitly wants their mode to apply on every turn."，即关闭它等于允许每轮自动应用。其他宿主的技能发现机制不同，要确认「按名读取」在关闭自动触发后仍然可用 |
| `description` | 决定技能能否被触发 | `reflect/SKILL.md` "`tune description: <skill path>` (the skill exists but didn't trigger when it should have)"；`create-verification-skill` "without frontmatter the skill never registers" | 各宿主的触发匹配方式不同 |
| `paths:` | 按文件类型自动加载 | `typescript-best-practices`；`reflect/references/synthesizer.md` "path-shaped triggers belong in `paths:`, not description prose" | 部分证据：`typescript-best-practices` 同时带 `disable-model-invocation: true`，`docs/guide/05-build-and-clean.md` 第 47 行称它 "loads whenever the agent touches a `.ts` or `.tsx` file"，即两者同时存在时 `paths` 仍按文件类型加载（guide 原文声称，未在宿主上验证） |
| `.mdc` 规则加 `alwaysApply: true` | 模型角色配置注入每个会话 | `setup-pstack` 第 5 步 | 隐式读取依赖注入。换宿主后，要么注入，要么让每个消费方显式读文件 |
| `.cursor-plugin/plugin.json` 的 `skills` 和 `agents` | 插件交付面 | `plugin.json` | 各宿主的安装方式不同 |
| `agents/*.md` 加 `subagent_type` 加 `is_background` | 派自定义子代理 | `agents/` | 需要宿主支持具名子代理类型。`is_background` 的语义未确定 |
| `Task` 工具参数：`run_in_background`、`readonly`（会去掉 MCP）、`model`、`environment: "cloud"`、`cloud_base_branch` | 子代理调度 | mode `## Subagents`、swarm、why | 参数名和能力逐项找替代。「readonly strips MCP」是 Cursor 的行为 |
| `/loop`、`/goal` | 事件或心跳唤醒；跨回合目标 | autonomous-run、autopilot-*、babysit | 需要宿主的循环和唤醒机制 |
| Cursor cloud agent、cloud-sleeper wake chain、monitored-shell sleep 加 sentinel | 云端 owner 与唤醒链 | autopilot-*、shipping、orchestrate | 未在快照中核实 |
| 运行中 `git show origin/main:` 重读组件 | 长流程每个 tick 读最新发布的 playbook | autopilot-full 第 6 步、multi-phase-plan 模板 | 与 MMW 的 Self-hosting boundary 冲突，不照搬（B.1） |
| 内置 `create-skill`、`automate`、`babysit`、`AskQuestion` | 写技能、建 automation、问卷 | reflect、automate-me、authoring-a-skill、setup-benny、mode | pstack 只引用、不自带 |
| `~/.cursor/projects/<slug>/agent-transcripts/` | transcript 位置 | reflect、session-pickup、worktree-audit.sh | 路径和格式都是宿主专有 |
| `cursor-team-kit`：`deslop`、`control-cli`、`control-ui` | 外部插件技能 | mode、opening-a-pr | 需要找等价技能；控制技能按角色槽位解析（B.1） |
| Bugbot、Grok Bot routine、`update_state`、`SendToUser` | 评审自动化；平台工具 | bugbot-triage、make-bot-ui | 平台专有 |
| 模型 slug，如 `grok-4.7-xhigh-fast`、`claude-opus-5-5-max` | 默认值与写死值 | setup-pstack、multi-phase-plan、check-plan.mjs | 按宿主可用的模型重写 |

与宿主无关、可以直接借鉴的外部工具有：`gh`、`git`、Origin CLI（可选）、Graphite `gt`（只有 orchestrate 用）、`bun`、`jq`、`rg`。其中 `worktree-audit.sh` 用了 BSD 形式的 `stat` 和 `date`（推断：只在 macOS 上按预期工作，L2 3.4）。

---

## F. 未确定事项

1. **几个 frontmatter 键在 Cursor 里的确切语义**（部分证据见 E.2）：
   - `disable-model-invocation: true`：已知关闭它等于允许每轮自动应用（`automate-me` 第 73 行）；它是否影响按名读取，未确定；
   - `mode: true`、`reminder`：何时注入，如何保持常驻；
   - `paths` 与 `disable-model-invocation` 同时存在时：guide 05 声称仍按文件类型加载，但宿主层面的规则没有写；
   - `is_background: true` 的含义。
2. **`setup-pstack` 为什么是唯一不带 `disable-model-invocation` 的技能**：原文没有说明。L4 7.1 的四条都是推断。
3. **playbook 为什么没有 frontmatter、为什么用 H3 标题**：「原本是 mode 里的小节」这个说法是推断，快照不含 git 历史。
4. **逐字复制与单一出处两种写法并存的原因**：原文没有说明（L2 5.1）。forge 选择规则在同一上下文里被先后读取的 babysit、shipping、opening-a-pr 中各写一份，「读者是独立代理」的推断解释不了它。
5. **两处角色冲突**：architect 调用 arena 时，runner 用 `architect runners` 还是 `arena runners`；recall 的 "fast, cheap model" 对应哪个角色（L3 未确定）。
6. **两处分工不清**：architect Phase D 与 Feature 第 4 步谁负责实现；teach 的收窄请求与 why 的跳过门槛如何协调（L3）。
7. **`shipping.md` 第 3 步要求记录的 verdict head SHA、base SHA、patch-id 存在哪里**：原文没有写（L2）。
8. **用 `automate-me` 生成的 `<handle>-mode` 能带什么**：是否应该带 `mode: true` 和 `reminder`，能否复用 `poteto-mode/playbooks/`，谁维护，原文没有说（L4 7.3）。
9. **项目私有 verify 技能默认不带 `disable-model-invocation` 是否有意**：`create-verification-skill` 生成的 `verify-<app>` 只规定了 `name` 和 `description`（L4 7.4）。
10. **测试是否通过**：各报告都没有运行脚本和测试，现在能否通过未知。`orch/` 不在 `typecheck` 命令的范围内（L2）。
11. **第 B.3 节的边统计只是量级**：它依赖六份报告的边块，而这些报告只读了各自范围内的文件，范围外的调用方大多来自 grep。用意译方式引用原则的地方（例如 "design it twice" 对应 exhaust-the-design-space，rubric.md 对十余条原则的复述）没有计入（L5）。
12. **"brain note" 的含义**：pstack 内没有定义。
13. **guide 引用的图片与 `assets/logo.png` 不在快照里**。
14. **poteto-agent 的续跑政策与 mode「重开新子代理」规则的适用场景是否不同**：原文没有划界（D.2）。

---

## 审查记录

审查者提出 49 条修正。逐条回到快照核对，结果如下。编号按修正清单的顺序；内容重复的条目合并说明。

| # | 修正要点 | 结果 | 核对与处理 |
|---|---|---|---|
| 1 | bug-fix 的 "might help" 不是「只有一个调用方」的实例 | 采纳 | grep 命中 bug-fix 第 5 行、autonomous-run 第 3 步、refactoring 第 4 步、hillclimb 第 5 步。已从 C.2 移到 C.5「逐字复制」，作为跨 playbook 重复的实例 |
| 2 | A.2 forge 规则是复制不是引用 | 采纳 | 6 个 playbook 各写一份（autopilot-full、autopilot-stack、shipping、babysit、opening-a-pr、multi-phase-plan）；patch-id 单一出处。A.2 已改 |
| 3 | D.4 面板角色不含 cross-judge pool | 采纳 | `setup-pstack` (c) 原文只列三个面板角色，cross-judge pool 单列为候选池。D.4 已改 |
| 4 | C.5「读者是否独立」推断过度，forge 计数应为 6 | 采纳 | babysit、shipping、opening-a-pr 由同一主代理先后读取。推断降为只适用于三例，forge 复制原因并入 F.4，计数改为 6 |
| 5 | "Instrumented != caused" 只写两遍 | 采纳 | 只在 datadog.md 第 89 行、databricks.md 第 54 行 |
| 6 | reflect 只有三份 reviewer 提示 | 采纳 | 三份逐字相同，synthesizer.md 第 3 行是针对 reviewer outputs 的同义改写 |
| 7、32 | 三条原则「没有被复用」说过头 | 采纳 | rubric.md "Every feature, control, and option should earn its place."、"Do they test behavior or implementation details?"，mode 第 105 行，tdd 第 3 步均核实。第 0 节、A.4、B.3 已改，干净实例只留 attack-the-premise |
| 8 | rubric.md 复述的原则远多于 6 条 | 采纳 | 通读 rubric.md 各节后改为「十余条」并列出可对上的原则 |
| 9、40 | Non-negotiables 是 17 条 | 采纳 | mode 第 19–35 行共 17 个 `→` 条目 |
| 10 | 原则行数最大值应为 31 | 驳回 | `wc -l skills/principle-*/SKILL.md`：最长是 `principle-boundary-discipline` 34 行，`principle-type-system-discipline` 31 行排第二。原值 16–34 正确，表中补注最长文件名 |
| 11 | figure-it-out 的 Start 写法不同 | 采纳 | 原文 "Open a todolist whose first item is to read the Principles section ..."。A.3、D.1 已单独注明 |
| 12 | how 没有 Step 5 | 采纳 | how 为 Step 1、2a、2b、3、4。C.3 已拆行 |
| 13 | guide 引子句式不统一 | 采纳 | 01、02 用 "In this page you"；05、06、09 用 "This page ..."；03、04、07、08、10 都不用。A.9 改为高频形态 |
| 14 | setup-benny 不符合操作文件模板 | 采纳 | setup-benny 无 `## Hard safety rules`，description 以 "Use when" 触发；另两个分别 14、18 条。A.10 已分开写 |
| 15、34 | 句中冒号规则覆盖 playbook 正文 | 采纳 | mode 第 26 行、unslop description 与规则 14、multi-phase-plan 第 5 步均核实；违反实例 orchestrate 第 17 行、opening-a-pr 第 5 行。E.1 第 9 条改为已核实，原 F.8 删除 |
| 16 | bugbot-triage 的 em dash 不能用「只针对回复」开脱 | 采纳 | 第 98、107 行含 em dash；unslop 规则 13 "Avoid em dashes entirely"。E.1 第 10 条已改 |
| 17、39 | 只有 7 个 playbook 以 Opening a PR 收尾 | 采纳 | grep 只命中 7 个；其余 15 个已在 E.1 第 3 条逐个列出 |
| 18 | shipping 的 "ignoring READY" 是冗余不是不一致 | 采纳 | `types.ts` 第 351 行 `Terminal<"READY", 0, "single" | "stack">`；babysit "Queued mode never emits `READY`."。E.1 第 23 条改为冗余 |
| 19 | C.4「整份重读」依据不支撑 orchestrate、multi-phase-plan | 采纳 | orchestrate 原样粘贴的是 standing orders；multi-phase-plan 模板要求重读执行 playbook。C.4 该行已改写并标推断 |
| 20 | check-plan 的 RULE 不算写错 | 采纳 | 模板规定 "Every verification block opens with it."，第 134 行做字面匹配。A.6 改为「字面检查器必须持有原文」，写错只留 LANES |
| 21 | "Never require gt" 措辞不一且漏了 opening-a-pr | 采纳 | multi-phase-plan 第 57 行 "Never require `gt`."，opening-a-pr 第 25 行 "Do not require Graphite (`gt`)."。E.1 第 7 条已改 |
| 22 | C.3 共同判据被自己的例子推翻 | 采纳 | architect Phase A/B 调 how、arena，automate-me "orchestrates three others"，teach 串 how/why，mode 第 119 行路由到 figure-it-out。C.3 判据改写，A.1 注明 mode 路由目标包括 figure-it-out；新判据仍标推断 |
| 23 | 被多处复用的流程仍可以是 playbook | 采纳 | babysit、opening-a-pr、prototype、shipping 的复用均核实；`automations/` 下 grep "playbook" 为 0；FOR_AGENTS 共享依赖原文核实。A.2、A.3、C.1 第 3、4 问、第 0 节已收窄 |
| 24 | 脚本门槛引错了原则 | 采纳 | build-the-lever 原文 "Distinct from Encode Lessons in Structure ... This is throughput and reviewability on the work in front of you."。A.6、C.1 第 2 问改引 encode-lessons-in-structure 和 synthesizer Structural-mechanism check |
| 25 | lever 不等于脚本 | 采纳 | build-the-lever description "(codemod, script, generator, or a skill your subagents follow)"。A.6 改名「脚本」并加术语注意 |
| 26 | 确定性内容不一定做成脚本 | 采纳 | babysit 第 6 步原文拒绝写 Origin watcher；forge、patch-id、reflect transcript 定位均为文字。C.1 第 2 问改为「可以」并加前提，A.6 列已知例外 |
| 27 | 每次都用的提示模板仍放 reference | 采纳 | how Step 2b、Step 3 都读 explainer-prompt.md；interrogate Step 3 读 reviewer-prompt、rubric、code-quality-review；reflect 每次读 reference。C.1 第 6 问、C.6 信号 6、A.5 加例外，E.1 新增第 28 条 |
| 28 | 同一上下文里也有复述 | 部分采纳 | mode 第 99、103 行，technical-writing "Replace an em dash with a new sentence."，multi-phase-plan 第 5 步 "No long dashes. No mid-sentence colons." 均核实，C.5 已补这一类。审查者列的 teach 实例不属实：`skills/teach/SKILL.md` 全文没有 "No em dashes" 或 sentence case，只写 "Write every response through the **unslop** skill"，未采用 |
| 29 | poteto-agent 的续跑政策 | 采纳 | description 原文核实。A.7、D.2、E.1 第 29 条、F.14 已补 |
| 30 | 能力技能自带闸门很普遍 | 采纳 | interrogate Step 2、maintain-verification 第 0 步、setup-pstack 第 3 步、make-bot-ui、bugbot-triage 均核实；architect Phase C 的闸门是可选的（"Opt in to a checkpoint when the invoker explicitly asks"），已如实写。A.3 收窄，E.1 第 18 条补 bugbot-triage 与 autonomous-run、autopilot 的冲突 |
| 31 | Autonomy 与 never-block-on-the-human 是冲突 | 采纳 | 原则 `**Boundaries:**` 与 mode 第 81 行核实。C.2 改写，E.1 新增第 30 条 |
| 33 | F.1 有部分原文证据 | 采纳 | automate-me 第 73 行、guide 05 第 47 行、synthesizer 的 `paths:` 句、reflect 的 tune description、create-verification-skill 的 frontmatter 句均核实。E.2、F.1 已补；README 第 128 行与 guide 05 的不一致记为 E.1 第 31 条。`paths` 与 disable-model-invocation 同时生效只标为「guide 原文声称」 |
| 35 | 漏了角色槽位连线 | 采纳 | bug-fix 第 1 步、multi-phase-plan `**Control skill.**`、benny `control-adapter.md` 的 `control.skill_name` 均核实。B.1 加一行，B.2 加一列，A.5 加一类 reference |
| 36 | 漏了从 trunk 重读组件 | 采纳 | autopilot-full 第 6 步、multi-phase-plan 模板第 36 行核实。B.1 加一行并注明与 MMW 的 Self-hosting boundary 冲突，E.2 加一行，第 0 节第 5 条提及 |
| 37 | synthesizer 的原文规则应作锚点 | 采纳 | Existing-skill-first、Decision-changing、Already-covered、Structural-mechanism check 四句核实。C.1 第 8 问、C.6 前四条改为有原文依据 |
| 38 | 行数不能反映 playbook 长度 | 采纳 | `wc -w` 结果与审查一致（另有 autopilot-stack 823、opening-a-pr 818）。A.0 加词数，C.4 扩大长 playbook 范围，A.2 补 autopilot-full 第 2、6 步和 babysit 第 6、8 步 |
| 41 | no-comments 截断 architect | 采纳 | no-comments 第 3 步与 architect Phase C 原文核实。A.3、E.1 第 20 条已补 |
| 42 | 能力技能形态和收尾格式不全 | 采纳 | show-me-your-work `## Composing this skill`、tdd `## Final Response`、recall `## Output contract`、blast-radius `## What to hand back`、maintain-verification `## Outcomes` 均核实。形态表增加格式持有型、平台操作手册型、编号步骤型，recall 归子代理编排型 |
| 43 | 漏了生成到目标仓库的组件 | 采纳 | create-verification-skill 第 3 步、maintain-verification-skill、FOR_AGENTS 原文核实。新增 A.11 和 A.0 一行 |
| 44 | 原则引用不止四种写法 | 采纳 | worktree-cleanup、orchestrate 的括注 slug 核实；审查者举的 session-pickup 实例里括注的是 prove-it-works，guard-the-context-window 的这种写法出现在 trace-forensics.md 第 7 行，已按实际出处写。E.1 第 1 条改为至少五种 |
| 45 | setup-pstack → mode | 采纳 | 第 5 步 "using the same labels poteto-mode uses" 核实。A.1、B.2、A.8 已补 |
| 46 | 原则可以带步骤和闸门 | 采纳 | encode-lessons Pattern 三步、attack-the-premise Stop、make-operations-idempotent The test 核实。A.4 模板和 C.6 信号 7 已改 |
| 47 | benny 只复用部分能力 | 采纳 | reproduce-and-fix-issues 第 13 步自写 blast radius smoke，全文不点名 `blast-radius` 技能。A.10 已改 |
| 48 | subtract-before-you-add 的 reference 含义不清 | 采纳 | description "stub references" 与 dead code 并列；refactoring 第 4 步 "orphan references" 指代码引用。A.5 改标推断 |
| 49 | benny 不是单一入口 | 采纳 | FOR_AGENTS "two cursor automations"、"wait for the trusted triage marker" 核实。A.10、C.1 第 7 问已改 |

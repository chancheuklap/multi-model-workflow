# L1：pstack 的 mode 技能、bugbot-triage reference 与 13 个短 playbook

来源快照：`docs/research/code-landing-refs/pstack/`（cursor/plugins b0b9c7a0）。下文路径都相对这个目录。行号取自快照文件。

负责并完整读过的文件（行数）：

| 文件 | 行数 |
| --- | --- |
| `skills/poteto-mode/SKILL.md` | 143 |
| `skills/poteto-mode/references/bugbot-triage.md` | 142 |
| `skills/poteto-mode/playbooks/investigation.md` | 14 |
| `skills/poteto-mode/playbooks/bug-fix.md` | 15 |
| `skills/poteto-mode/playbooks/perf-issue.md` | 24 |
| `skills/poteto-mode/playbooks/hillclimb.md` | 21 |
| `skills/poteto-mode/playbooks/runtime-forensics.md` | 11 |
| `skills/poteto-mode/playbooks/trace-forensics.md` | 14 |
| `skills/poteto-mode/playbooks/feature.md` | 21 |
| `skills/poteto-mode/playbooks/refactoring.md` | 16 |
| `skills/poteto-mode/playbooks/prototype.md` | 14 |
| `skills/poteto-mode/playbooks/visual-parity.md` | 11 |
| `skills/poteto-mode/playbooks/authoring-a-skill.md` | 12 |
| `skills/poteto-mode/playbooks/eval.md` | 25 |
| `skills/poteto-mode/playbooks/opening-a-pr.md` | 33 |

为确认连线，另外只查了一个事实就停的文件（没有通读，结论涉及它们的地方已标明）：`agents/poteto-agent.md`（全文 9 行，已读完）、`.cursor-plugin/plugin.json`（已读完）、`docs/guide/02-poteto-mode.md`、`docs/guide/08-principles.md`、`docs/guide/09-make-it-yours.md`（这三篇已读完）、`skills/setup-pstack/SKILL.md`（只看了角色名那几行）、`skills/principle-prove-it-works/SKILL.md`（读了前 22 行）、`skills/tdd/SKILL.md`（读了前 20 行）、以及 `architect`、`arena`、`swarm`、`how`、`figure-it-out`、`show-me-your-work` 各自 `SKILL.md` 的章节标题（只 grep 了标题）。全仓库还 grep 了 frontmatter 键和对 `poteto-mode`、`playbooks/`、`bugbot-triage` 的引用。

---

## 1. 组件清单

| 文件 | 组件类型 | 管什么 |
| --- | --- | --- |
| `skills/poteto-mode/SKILL.md` | mode（带 `mode: true` 的技能） | 整个工作风格的入口：非谈判触发规则、23 条原则索引、自主权边界、子代理默认值、回复写法、注释规则，以及把任务路由到 23 个 playbook 的路由表 |
| `references/bugbot-triage.md` | reference | Babysit 处理 Bugbot / 安全审查评论时的分类判据（fix / dismiss / ask）加一份持续追加的「已学到的模式」目录 |
| `playbooks/investigation.md` | playbook | 只读问题：产出带引用的解释或建议，不改代码 |
| `playbooks/bug-fix.md` | playbook | 复现、二分定位、修复、同表面验证一个缺陷 |
| `playbooks/perf-issue.md` | playbook | 以基线 trace 为准的一次性性能修复 |
| `playbooks/hillclimb.md` | playbook | 对一个指标持续做「一次改动、一次测量、留或回退」的循环 |
| `playbooks/runtime-forensics.md` | playbook | 对活进程取证，交付诊断而不是修复 |
| `playbooks/trace-forensics.md` | playbook | 对已抓好的 profiling 产物取证，交付诊断 |
| `playbooks/feature.md` | playbook | 新增或改变行为：设计、吞吐检查点、委派实现、验证 |
| `playbooks/refactoring.md` | playbook | 保持行为不变的结构调整 |
| `playbooks/prototype.md` | playbook | 用一次性草图做设计或经验性决定 |
| `playbooks/visual-parity.md` | playbook | 像素级 UI 等价迁移 |
| `playbooks/authoring-a-skill.md` | playbook | 写或改一个 SKILL.md |
| `playbooks/eval.md` | playbook | 盲测一个技能 / 结构 / 提示改动对 agent 行为的影响 |
| `playbooks/opening-a-pr.md` | playbook（形式上）；内容上是一份 PR 约定标准 | worktree、提交、PR 标题与正文、forge 选择、栈、就绪、与 Babysit 的界线 |

补充事实（原文写明）：

- 整个插件只有 `poteto-mode/SKILL.md` 带 `mode:` 和 `reminder:` 两个键（全仓库 grep `^mode:\|^reminder:` 只命中这一个文件）。
- 47 个 `SKILL.md` 中 46 个写了 `disable-model-invocation: true`，唯一例外是 `skills/setup-pstack/SKILL.md`（grep 结果）。
- playbook 没有 frontmatter，不是独立技能：`.cursor-plugin/plugin.json` 只声明 `"skills": "./skills/"` 和 `"agents": "./agents/"`，playbook 文件在 `skills/poteto-mode/playbooks/` 下，没有自己的 `SKILL.md`。推断：宿主不会把 playbook 当技能列出，它只能经由 mode 或其他 playbook 的相对路径被读到。
- 路由表 23 行，对应 `playbooks/` 目录下 23 个文件；`docs/guide/02-poteto-mode.md` 原文 "it matches one of twenty-three playbooks"。

---

## 2. 解剖

### 2.1 `skills/poteto-mode/SKILL.md`（143 行）

**Frontmatter（第 1-9 行）逐键：**

| 键 | 值 | 说明 |
| --- | --- | --- |
| `name` | `Poteto Mode` | 注意是带空格、首字母大写的显示名，不是目录名 `poteto-mode`。其他技能都用 slug（如 `name: principle-prove-it-works`、`name: how`）。别处一律用 `poteto-mode` / `/poteto-mode` 指它（`agents/poteto-agent.md`、`README.md`） |
| `description` | "poteto's agent style for concise, detailed responses, deliberate subagents, unslopped prose, simple code, and verified work. Use for poteto, /poteto-mode, or requests to work in this style." | 两句：第一句说是什么（风格的五个特征），第二句 "Use for ..." 列触发词，含斜杠命令本身 |
| `disable-model-invocation` | `true` | 与 46 个兄弟技能一致。推断：模型不会凭 description 自动加载它，只能由用户斜杠命令、`reminder` 提示、或 `poteto-agent` 的指令读入 |
| `mode` | `true` | 全插件独有。原文没有解释语义；推断：Cursor 插件用它把该技能标成「模式」（持续生效、可切换），`docs/guide/02-poteto-mode.md` 原文 "Short works because the mode is sticky" 支持这一推断 |
| `icon` | `crown` | 展示用 |
| `color` | `yellow` | 展示用 |
| `reminder` | "New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't." | 一行两条件：何时套用、何时不套用，用 `->` 连接（不是 `→`）。推断：宿主在每轮或新任务时把这行注入上下文，让「disable-model-invocation」的技能仍有被重新想起的机会；语义未在快照中写明 |

**正文结构与顺序：**

| 章节 | 行 | 装的内容类型 | 句式 |
| --- | --- | --- | --- |
| `# Poteto mode` | 11 | 标题 | — |
| `## Non-negotiables` | 13-35 | 首段是一条总规则（回复里点名原则及其改变的决定，只引本会话读过的 leaf SKILL.md）；然后 "Remaining triggers:" 下 16 条「条件 → 技能 / playbook」的触发规则 | 条件在前，`→` 后是技能名（粗体）或 playbook 名加路径，再加一两句理由或例外 |
| `## Principles` | 37-77 | 23 条原则的索引，分 Core(10) / Architecture(6) / Verification(4) / Delegation(2) / Meta(1) 五组 | 每条统一为 `**显示名** (**principle-slug**). 适用时机. 一句要点.` |
| `## Autonomy` | 79-87 | 四段粗体开头的段落：Just do it / Always pause / Session overrides / No is an acceptable answer | 判断与边界，祈使句 |
| `## Subagents` | 89-95 | `subagent_type` 规定、每次 `Task` 调用的默认参数、模型按角色分配与 `/setup-pstack` 覆盖、对子代理产出的责任 | 命令与参数 + 理由 |
| `## Writing the reply` | 97-109 | 7 条回复写法 + 一段说明每个 playbook 以这种回复收尾、PR 链接格式 | 输出格式 |
| `## Comments` | 111-113 | 代码注释只留非显然的 why；验证脚本不写阶段叙述注释 | 做法 |
| `## Playbooks` | 115-143 | 首段：待办清单协议；次段：升级路由（figure-it-out / Orchestrate）；然后 23 行路由表 | 步骤顺序 + 触发条件 |

**各节职责（额外问题的回答）：**

- **Non-negotiables**：横切所有 playbook 的触发器表。它不讲怎么做，只讲「遇到 X 就去用 Y」。首段把 Principles 定为所有触发的依据，并立下「引用原则必须读过其 leaf SKILL.md」的门槛（第 15 行 "Cite only principles whose leaf SKILL.md you read this session."）。16 条里：6 条指向能力技能（how、architect、swarm/arena、interrogate、unslop+create-skill、technical-writing），3 条指向外部插件技能（deslop、control-cli/control-ui），1 条指向原则（principle-model-the-domain），4 条指向 playbook 或 reference（prototype、babysit、shipping、bugbot-triage），另有「提问前先分类」「坏掉的技能单开 PR 修」「长任务留 decision trail」这类横切规则。
- **Principles**：原则的目录和触发条件，不是原则正文。第 39 行 "Read the leaf skill in full for any principle you apply. Each entry names when it applies." 每条自带一句要点，但要点只够判断是否适用，应用时要读 leaf。
- **Autonomy**：定义什么可以不问就做、什么必须停（第 83 行 "**Always pause** for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages."）、用户用哪些话把会话切到全自主、以及允许说「不」。
- **Subagents**：规定所有 playbook 步骤里派出的子代理用 `subagent_type: "poteto-agent"`，但被路由的工作流技能（how、why、interrogate、reflect、swarm）自带 `subagent_type` 时不得覆盖；给出 `Task` 默认参数（`run_in_background: true`、agent 模式、传文件指针不内联、每个角色指定模型）；模型默认值和 `/setup-pstack` 的覆盖关系；主代理对子代理产出负责（第 95 行 "You own every subagent's work."）。
- **Writing the reply**：所有 playbook 共用的回复格式。第 109 行 "Every playbook ends with a reply written this way ... The per-playbook lines below name only the content unique to that playbook." 这句规定了分工：通用写法在 mode，每个 playbook 的 `**Reply:**` 行只写该 playbook 独有的内容。
- **Comments**：代码注释规则，明确延伸到子代理的 diff（第 113 行 "This applies to every file you produce, including the delegate's diff."）。
- **Playbooks**：执行协议 + 路由表。协议是第 117 行 "Open a todolist whose first items are the matched playbook's steps, copied in verbatim, before any task-specific todos. A step you choose not to do stays in the list with a one-line `skip: <reason>`."

**路由表每一行的写法（第 121-143 行）：**

统一格式 `- **<Playbook 名>.** <触发描述>. \`playbooks/<file>.md\`.`。触发描述的写法有四种成分，按需组合：

1. 任务类型的一句定义（全部行都有），如 Bug fix "A reported defect to reproduce, root-cause, and fix with runtime evidence."
2. 用户原话式的触发措辞放进括号和引号，如 Prototype `("prototype", "mock it up", "try this layout", "sketch it to decide")`、Autonomous run `("run until done", "/loop until X")`。我负责的 13 个里只有 Prototype 这样写；其余带引号措辞的行是 Orchestrate、Autopilot-full、Autopilot-stack、Worktree cleanup、Autonomous run。
3. 与相邻 playbook 的区分句 "Distinct from ..."，如 Hillclimb "Distinct from Perf issue, which is a one-off fix."；Runtime / Trace forensics 都写 "The deliverable is a diagnosis, not a fix."
4. 交付物限定，如 forensics 两行。

特殊行：Pause safely 写 "Full steps: `playbooks/pause-safely.md`"；Opening a PR 不写触发条件，写 "Invoked at the end of every other playbook."。

路由表之前的升级规则（第 119 行）优先于表内匹配："A large or cross-cutting effort ... routes to the **figure-it-out** skill even when a narrower playbook like Feature fits. Use **figure-it-out** whenever no bundled playbook fits." 以及 Orchestrate 与 figure-it-out 的分工 "figure-it-out designs one bespoke run, orchestrate runs the program."

**语气**：短祈使句、每句一个意思、句号结尾；自身遵守它在 Writing the reply 里要求的「不用长破折号」「不用句中冒号」（mode 正文没有 `—`）。

### 2.2 `references/bugbot-triage.md`（142 行）

无 frontmatter。结构：

| 章节 | 行 | 内容类型 |
| --- | --- | --- |
| `# Bugbot triage` + 首段 | 1-3 | 触发条件（"Use this reference when the Babysit playbook (`../playbooks/babysit.md`) handles Bugbot or review-automation comments."）和目标 |
| `## Decision rubric` | 5-13 | 判断：三分类 `fix` / `dismiss` / `ask`，每类一句判据和一句动作；"When in doubt, ask." |
| `## Learned pattern format` | 15-29 | 输出格式：一个 markdown 模板（`Confidence` / `Skip when` / `Do not skip when` / `Example signal` / `Source`）和三档置信度的定义 |
| `## Recurring skip candidates` | 31-73 | 数据：6 条已学模式 |
| `## Ask by default` | 75-84 | 判断：永不自动跳过的类别 |
| `## Candidate learnings from recent babysits` | 86-142 | 数据 + 追加规则："Append new candidate learnings here during or after babysitting ... Prefer promoting recurring candidates into the section above once several PRs confirm the pattern." 4 条 |

语气：前半是规则，后半是案例库。后 4 条条目用硬换行、用了 `—`（第 98、107 行）和分号，与前面条目的排版不同。推断：后半是 agent 在不同 babysit 会话里追加的，未统一改写。

### 2.3 Playbook 的统一格式

13 个文件共同遵守的骨架（原文可见）：

1. **标题**：`### <Playbook 名>`，三级标题，文件里没有一级标题。推断：playbook 原本是 mode SKILL.md 里的小节，后来拆成文件；mode 第 109 行 "The per-playbook lines below" 的 "below" 也指向这个历史布局。这是推断，快照里没有写明。
2. **所有权行**：粗体，`**You own <对象>. <动词>, <动词>, <动词>.**`，例如 bug-fix "**You own this task. Plan, review, verify.**"、investigation "**You own the answer. Plan, route, write.**"、visual-parity "**You own pixel-exact equivalence. The baseline is the spec. You do not touch it.**"。有的后面紧跟一句委派立场（bug-fix / feature "Delegate ... Stay in the lead."）。
3. **首段（可选）**：讲这一类任务的纪律、与相邻 playbook 的区别、或与某原则的关系。例：bug-fix "Be scientific. Every shipped line traces to runtime evidence."；hillclimb "Core discipline: one change, one measurement, keep or revert."；prototype "The one playbook where the Laziness Protocol's 'smallest change' and the verification bar invert."
4. **编号步骤**：4 到 8 步。每步首句是祈使动作，后面是门槛、例外或理由。
5. **尾段（可选）**：边界和转交，如 investigation "No PR, no babysit, no `architect` unless the investigation precedes a code change."；perf-issue 指向 Hillclimb；feature 的单一 owner 与父级 fan-out 规则。
6. **`**Reply:**` 行**：最后一行，只列该 playbook 回复里独有的内容。

**步骤里点名其他组件的写法（原文实例，写法并不统一）：**

| 被点名的 | 写法实例 |
| --- | --- |
| 能力技能 | "Route through the **how** skill"（investigation 1）；"`how` over the affected subsystem"（feature 1）；"`architect` first"（bug-fix 3）；"the **arena** skill's Phase B"（eval 4）；"See the **tdd** skill"（bug-fix 5） |
| 原则 | 至少三种写法并存："the **sequence-verifiable-units** principle skill"（bug-fix 5、perf 3、hillclimb 5、feature 6、refactoring 8，省略 `principle-` 前缀）；"per **principle-model-the-domain**"（feature 4、refactoring 2，完整 slug）；"(the **principle-guard-the-context-window** skill)"（trace-forensics 1）；括号里的完整 slug "(**principle-prove-it-works**)"（refactoring 6）；显示名 "Laziness Protocol"（feature 4、prototype 首段） |
| 其他 playbook | "Run **Opening a PR**."（粗体名字，无路径）；"the Hillclimb playbook (`playbooks/hillclimb.md`)"（名字 + 路径）；"Hand the chosen direction to **Feature**"；"Route to Bug fix or Perf issue"（纯文字） |
| mode 的小节 | "via the control skill (Non-negotiables)"（bug-fix 1）；"Comments per **Comments**"（feature 4）；"(see Autonomy)"（investigation Reply） |
| 外部插件 / 宿主功能 | "Cursor's `/loop` command"（bug-fix 2）；"the **create-skill** skill (Cursor's built-in ...)"（authoring 1）；"Run `/deslop` from `cursor-team-kit`"（opening-a-pr） |
| 模型配置 | "using your configured bug-fix model (default `grok-4.7-xhigh-fast`)"（bug-fix 3，perf / hillclimb / feature / refactoring 同式）；这些角色名与 `skills/setup-pstack/SKILL.md` 写入 `~/.cursor/rules/pstack-models.mdc` 的行一一对应（`bug-fix:`、`perf-issue:`、`hillclimb:`、`feature, refactoring:`） |

### 2.4 逐个 playbook 的解剖

以下「内容类型」用题目给的六类：步骤顺序 / 做法 / 理由与判断 / 命令与参数 / 输出格式 / 触发条件。

**investigation.md（14 行）**。所有权行 + 首段（只读，交付引用解释或建议）+ 4 步 + 尾段 + Reply。步骤 1 路由到 how（动机问题加 why）；步骤 2 是一条固定输出 `throughput checkpoint: n/a, read-only investigation`；步骤 3 是输出格式（how 的 Overview / Key Concepts / How It Works / Where Things Live / Gotchas，或带 tradeoffs 表的建议）；步骤 4 unslop。尾段是转交规则："If it does, hand back to the user and re-route to Bug fix or Feature." Reply 行包含一条判断："Push back if the premise is wrong (see Autonomy)."

**bug-fix.md（15 行）**。所有权 + 委派立场 + 首段（「每行代码可追溯到运行时证据」「证据推翻假设就回退它引出的改动」，理由与判断）+ 6 步 + Reply。步骤 1 复现（含何时才可以请用户复现的窄例外，mode 第 30 行以 "the narrow Bug fix step 1 exception" 反向引用它）；步骤 2 二分假设，含做法（加日志、`/loop`）；步骤 3 计划与委派；步骤 4 同表面验证；步骤 5 提交顺序（失败复现先入历史）并点名 tdd 和原则；步骤 6 Opening a PR。Reply 要求 "Paste failing-then-passing repro output verbatim."

**perf-issue.md（24 行）**。所有权 + 6 步 + 尾段（指向 Hillclimb）+ Reply。步骤 2 内嵌一份 8 条「策略族」清单（Elimination / Divide and conquer / Caching / Indirection / Batching / Redundancy / Lazy evaluation / Scheduling），每条是一段做法说明，并有使用规则 "Use them as hypothesis generators, not a checklist. A family earns an attempt only when the trace shows the signal it names."。这是本组 playbook 里体量最大的做法内容。步骤 4 含命令性做法 "Parse and compare the artifacts (JSON to sqlite, diff)."

**hillclimb.md（21 行）**。所有权 + 首段（核心纪律）+ 8 步 + Reply。步骤 1 定工作负载、指标、方向和停机谓词（给出谓词形状示例 "at least 50% better than baseline and at least 10 iterations"）；步骤 2 建测量 harness、证明灵敏度后冻结；步骤 3 开 `decision.tsv`，给出列定义（id, hypothesis, change, before, after, delta, tests, verdict, note），"Keep it out of the tree (gitignored)."（输出格式 + 持久状态）；步骤 5 是带子弹的循环体，含命令 `git add <files>`, never `-A`；步骤 6-7 停机判断；步骤 8 Opening a PR。本组点名原则最多的 playbook：prove-it-works、build-the-lever、guard-the-context-window、separate-before-serializing-shared-state、sequence-verifiable-units、laziness-protocol，外加 show-me-your-work 技能。

**runtime-forensics.md（11 行）**。所有权行把交付物写死（"The deliverable is a cited diagnosis, not a fix."）+ 5 步 + Reply。第 5 步是固定行 `throughput checkpoint: n/a, read-only forensics`。Reply 行里夹了转交规则 "Hand back to Bug fix or Perf once the cause is known."。不跑 Opening a PR。

**trace-forensics.md（14 行）**。所有权 + 首段（与 Runtime forensics 的区分，工具保持通用以便可移植）+ 6 步 + Reply。步骤 2 是做法 "Dump the trace or heap snapshot into sqlite, one row per sample, frame, or node."；步骤 5 是判断（没有配对抓取就标为 "the strongest hypothesis the artifact supports"）；步骤 6 转交 + 固定 throughput 行。不跑 Opening a PR。

**feature.md（21 行）**。所有权 + 8 步 + 尾段 + Reply。步骤 3 定义「吞吐检查点」（throughput checkpoint）为四个待办项：Blocking first steps / Independent workstreams / Shared mutable state / Smallest safe decomposition，不适用的保留为 `n/a: <reason>`。这是 mode（第 25 行 "write the throughput checkpoint (Feature step 3)"）和 investigation / forensics 的 "n/a" 行所引用的定义源。步骤 4 是一整段（本组最长的一步），混合了：委派范围要写什么、何时改用 arena、"Mandatory: no skip-with-reason escape, and Laziness Protocol does not override it"、禁止 "standing by" 回复、注释规则、手术式编辑、共享原语改进要移植到所有使用方、多提交。尾段是扇出规则："Code-coupled work ... goes to a single owner ... Parent-level fan-out is for slices that produce independent artifacts ... Spawn a fresh owner rather than chaining interrupts."

**refactoring.md（16 行）**。所有权 + 首段（与 Feature / Bug fix 的区分，拆出发现的 bug 或缺失功能，大改走 figure-it-out）+ 8 步 + Reply。几乎每一步都挂一条原则：步骤 2 model-the-domain；步骤 3 foundational-thinking + redesign-from-first-principles；步骤 4 subtract-before-you-add + laziness-protocol；步骤 5 migrate-callers-then-delete-legacy-apis；步骤 6 prove-it-works；步骤 7 minimize-reader-load；步骤 8 sequence-verifiable-units。步骤 1 有一条判据 "Type check and lint are not a pin."；步骤 7 把原则变成保留或回退的判据 "If the diff does not lower reader load somewhere, revert it."

**prototype.md（14 行）**。所有权 + 首段（明写本 playbook 翻转 Laziness Protocol 与验证门槛）+ 6 步 + Reply。步骤 1 有进入门槛 "No decision means no prototype. Route to Feature."；步骤 3 给做法（隔离 scratch 目录、vanilla HTML/CSS/JS、CDN）；步骤 4 "This is the **exhaust-the-design-space** principle skill made cheap."；步骤 6 转交 Feature / architect。不跑 Opening a PR。Reply "Say plainly that the prototype is throwaway."

**visual-parity.md（11 行）**。所有权 + 5 步 + Reply。步骤 2 是一组防走捷径条款（"no harness modifications, no baseline tampering, no component restructuring to make a diff pass"），属于判断规则而不是动作；步骤 4 "`/loop` per component until the diff is zero"；步骤 5 按组件或安全批次开 PR。

**authoring-a-skill.md（12 行）**。所有权行只有一句 "**You own the skill's voice.**" + 4 步 + 尾段 + Reply。步骤 1 交给宿主内置 create-skill；步骤 2 是一份验证清单（frontmatter 有 `name` 和 `description`、引用文件存在、跨技能链接可解析）。尾段是写作做法："When in doubt, delete. Keep only prose that changes a decision. Tell it to do the thing and skip the reason. ... Delegate to other skills by path. Don't restate. A workflow you keep hitting but isn't captured → propose a new skill."

**eval.md（25 行）**。格式偏离统一骨架：所有权行后是 "**Non-negotiables for blinding:**" 七条规则，再是 "**Steps:**" 标签和七个带粗体小标题的步骤（**Frame.** / **Set up sanitized environments.** / ...）。步骤 4、5 直接引用 arena 技能的内部阶段 "per the **arena** skill's Phase B" / "Phase C"。步骤 6 是带安全边界的做法："Do not glob across `~/.cursor/projects/*/`. That crosses workspace boundaries and reads private chats from unrelated projects." 不跑 Opening a PR。

**opening-a-pr.md（33 行）**。格式偏离最大：没有编号步骤，没有 Reply 行，没有所有权行；首句 "Invoked at the end of every other playbook." 之后是九段粗体开头的段落：**Worktree.** / **Commits.** / **PRs.** / **Titles.** / **Descriptions.** / **Forge.** / **Size and stacks.** / **Readiness.** / **Babysit.**，最后一段写子代理开 PR 的规则。内容几乎全是做法、命令与参数、输出格式：Conventional Commits 标题格式（`type(scope): subject`，列出允许的 type）、PR 正文五节 `## Why` / `## Scope` / `## Tradeoffs` / `## Blast Radius` / `## Verification` 及禁写项、forge 选择（`gh` 默认，`command -v origin` 成功则用 `origin pr ...`，"Do not require Graphite (`gt`)"）、栈的分支和 `--base` 命令、就绪（"Open every PR ready, never as a draft"）。

---

## 3. 调用与连线

### 3.1 谁调用 mode

| 调用者 | 方式 | 出处 |
| --- | --- | --- |
| 用户 | 斜杠命令 `/poteto-mode` | `README.md` 第 26、34 行；`docs/guide/02-poteto-mode.md` |
| 宿主的 reminder 机制 | frontmatter `reminder` 行（推断：宿主注入） | `SKILL.md` 第 8 行 |
| `agents/poteto-agent.md` | agent 定义（frontmatter `name: poteto-agent`、`is_background: true`），正文唯一的指令是 "Read the `poteto-mode` skill's `SKILL.md` in full before doing any work, including its inline Principles index." description 写明 "Substituting `generalPurpose` skips that read and drifts." | `agents/poteto-agent.md` 第 1-9 行 |
| mode 自己的子代理 | `subagent_type: "poteto-agent"`，因此每个子代理也会读 mode | `SKILL.md` 第 91 行 |
| `figure-it-out` 技能 | "Open a todolist whose first item is to read the Principles section of the **poteto-mode** skill." | `skills/figure-it-out/SKILL.md` 第 13 行 |
| `automate-me` 技能 | 只把它当形状样例读："Read it for granularity. Don't copy its content." | `skills/automate-me/SKILL.md` 第 63 行 |
| `setup-pstack` 技能 | 反向依赖：写 `~/.cursor/rules/pstack-models.mdc` 时 "using the same labels poteto-mode uses" | `skills/setup-pstack/SKILL.md` 第 39 行 |

### 3.2 谁调用 playbook

- 只有 mode 的路由表（相对路径 `playbooks/<file>.md`）和其他 playbook（按名字或相对路径）。原文协议：mode 第 117 行 "Match the task to a playbook below, open its file, and copy its steps in verbatim."
- playbook 之间：Opening a PR 被 bug-fix(6)、perf-issue(6)、hillclimb(8)、feature(8)、refactoring(8)、visual-parity(5)、authoring-a-skill(4) 以 "Run **Opening a PR**" 调用。
- `multi-phase-plan.md`（不在我的范围）以 `playbooks/prototype.md` 调用 Prototype，并在计划骨架里 `git show origin/main:pstack/skills/poteto-mode/playbooks/opening-a-pr.md`（grep 结果）。
- `hillclimb.md` 步骤 5 只借 Autonomous run 的唤醒机制："borrow only the wake mechanism from the Autonomous run playbook (`playbooks/autonomous-run.md`), not its stop rule."

### 3.3 谁调用 bugbot-triage

mode 第 33 行 "Triage fix / dismiss / ask per `references/bugbot-triage.md`."；`playbooks/babysit.md` 第 22 行 "per `../references/bugbot-triage.md`"；`playbooks/multi-phase-plan.md` 第 61 行（grep 结果）。reference 自己声明的调用方只有 Babysit（第 3 行）。

### 3.4 Opening a PR 如何被「所有 playbook」调用

原文声称 "Invoked at the end of every other playbook."（`opening-a-pr.md` 第 3 行，mode 第 143 行）。实际写法是每个要产出代码的 playbook 在最后一步写 "Run **Opening a PR**."，按名字点名，不给路径；mode 路由表给出路径。不产出代码的 playbook 不调用它：investigation 明写 "No PR"；runtime-forensics、trace-forensics、prototype、eval 都没有这一步。所以「every other playbook」在原文层面不准确，见第 5 节。

Opening a PR 本身再往下连：`/deslop`、`/no-comments`、`/technical-writing`、`/unslop`；子代理开 PR 时还要跑 `interrogate`；并明确切断与 Babysit 的自动连接（"Opening a PR does not start a babysit."）。

### 3.5 连线表

关系词：沿用题目给的八个；另自拟五个：`cites-section`（playbook 按小节名引用 mode 的某一节，如 "(Non-negotiables)"、"per **Comments**"）、`reads-skill`（agent 或技能读取另一个技能的正文作为自身指令）、`refers-to-step`（按编号引用另一组件内部某一步）、`borrows-from`（只借用另一 playbook 的一部分机制）、`distinguishes-from`（原文专门写一句与某组件划界，不产生调用）。`control-skill` 指 cursor-team-kit 的 `control-cli` / `control-ui`，原文在 playbook 里只写 "the control skill"。

```edges
user -> poteto-mode : calls
poteto-agent -> poteto-mode : reads-skill
figure-it-out -> poteto-mode : reads-skill (Principles section only)
automate-me -> poteto-mode : reads-skill (shape example, content not copied)
setup-pstack -> poteto-mode : configured-by (inverse: pstack-models.mdc uses poteto-mode role labels)
poteto-mode -> setup-pstack : configured-by
poteto-mode -> poteto-agent : spawns-subagent
poteto-mode -> how : calls
poteto-mode -> architect : calls
poteto-mode -> swarm : calls
poteto-mode -> arena : calls
poteto-mode -> interrogate : calls
poteto-mode -> unslop : calls
poteto-mode -> create-skill (Cursor built-in) : calls
poteto-mode -> technical-writing : calls
poteto-mode -> deslop (cursor-team-kit) : calls
poteto-mode -> no-comments : calls
poteto-mode -> control-cli (cursor-team-kit) : calls
poteto-mode -> control-ui (cursor-team-kit) : calls
poteto-mode -> show-me-your-work : calls
poteto-mode -> figure-it-out : routes-to
poteto-mode -> references/bugbot-triage.md : reads-reference
poteto-mode -> playbooks/feature.md : refers-to-step (Feature step 3, throughput checkpoint)
poteto-mode -> playbooks/bug-fix.md : refers-to-step (Bug fix step 1 exception)
poteto-mode -> Cursor built-in babysit : distinguishes-from
poteto-mode -> playbooks/investigation.md : routes-to
poteto-mode -> playbooks/bug-fix.md : routes-to
poteto-mode -> playbooks/perf-issue.md : routes-to
poteto-mode -> playbooks/hillclimb.md : routes-to
poteto-mode -> playbooks/runtime-forensics.md : routes-to
poteto-mode -> playbooks/trace-forensics.md : routes-to
poteto-mode -> playbooks/feature.md : routes-to
poteto-mode -> playbooks/refactoring.md : routes-to
poteto-mode -> playbooks/prototype.md : routes-to
poteto-mode -> playbooks/visual-parity.md : routes-to
poteto-mode -> playbooks/authoring-a-skill.md : routes-to
poteto-mode -> playbooks/eval.md : routes-to
poteto-mode -> playbooks/babysit.md : routes-to
poteto-mode -> playbooks/shipping.md : routes-to
poteto-mode -> playbooks/autonomous-run.md : routes-to
poteto-mode -> playbooks/orchestrate.md : routes-to
poteto-mode -> playbooks/autopilot-full.md : routes-to
poteto-mode -> playbooks/autopilot-stack.md : routes-to
poteto-mode -> playbooks/session-pickup.md : routes-to
poteto-mode -> playbooks/pause-safely.md : routes-to
poteto-mode -> playbooks/multi-phase-plan.md : routes-to
poteto-mode -> playbooks/worktree-cleanup.md : routes-to
poteto-mode -> playbooks/opening-a-pr.md : routes-to
poteto-mode -> principle-laziness-protocol : cites-principle
poteto-mode -> principle-foundational-thinking : cites-principle
poteto-mode -> principle-redesign-from-first-principles : cites-principle
poteto-mode -> principle-attack-the-premise : cites-principle
poteto-mode -> principle-subtract-before-you-add : cites-principle
poteto-mode -> principle-minimize-reader-load : cites-principle
poteto-mode -> principle-outcome-oriented-execution : cites-principle
poteto-mode -> principle-experience-first : cites-principle
poteto-mode -> principle-exhaust-the-design-space : cites-principle
poteto-mode -> principle-build-the-lever : cites-principle
poteto-mode -> principle-model-the-domain : cites-principle
poteto-mode -> principle-boundary-discipline : cites-principle
poteto-mode -> principle-type-system-discipline : cites-principle
poteto-mode -> principle-make-operations-idempotent : cites-principle
poteto-mode -> principle-migrate-callers-then-delete-legacy-apis : cites-principle
poteto-mode -> principle-separate-before-serializing-shared-state : cites-principle
poteto-mode -> principle-prove-it-works : cites-principle
poteto-mode -> principle-fix-root-causes : cites-principle
poteto-mode -> principle-sequence-verifiable-units : cites-principle
poteto-mode -> principle-test-behavior-not-implementation : cites-principle
poteto-mode -> principle-guard-the-context-window : cites-principle
poteto-mode -> principle-never-block-on-the-human : cites-principle
poteto-mode -> principle-encode-lessons-in-structure : cites-principle
playbooks/investigation.md -> how : calls
playbooks/investigation.md -> why : calls
playbooks/investigation.md -> unslop : calls
playbooks/investigation.md -> playbooks/bug-fix.md : hands-off-to
playbooks/investigation.md -> playbooks/feature.md : hands-off-to
playbooks/bug-fix.md -> control-skill : calls
playbooks/bug-fix.md -> how : calls
playbooks/bug-fix.md -> why : calls
playbooks/bug-fix.md -> Cursor /loop : calls
playbooks/bug-fix.md -> architect : calls
playbooks/bug-fix.md -> interrogate : calls (named only in step 2 as "step-3 architect/interrogate fan-out")
playbooks/bug-fix.md -> poteto-agent : spawns-subagent (bug-fix model)
playbooks/bug-fix.md -> setup-pstack : configured-by (bug-fix role)
playbooks/bug-fix.md -> tdd : calls
playbooks/bug-fix.md -> principle-sequence-verifiable-units : cites-principle
playbooks/bug-fix.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/perf-issue.md -> control-skill : calls
playbooks/perf-issue.md -> how : calls
playbooks/perf-issue.md -> architect : calls
playbooks/perf-issue.md -> poteto-agent : spawns-subagent (perf-issue model)
playbooks/perf-issue.md -> setup-pstack : configured-by (perf-issue role)
playbooks/perf-issue.md -> principle-sequence-verifiable-units : cites-principle
playbooks/perf-issue.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/perf-issue.md -> playbooks/hillclimb.md : routes-to
playbooks/hillclimb.md -> how : calls
playbooks/hillclimb.md -> show-me-your-work : calls
playbooks/hillclimb.md -> poteto-agent : spawns-subagent (hillclimb model)
playbooks/hillclimb.md -> setup-pstack : configured-by (hillclimb role)
playbooks/hillclimb.md -> principle-prove-it-works : cites-principle
playbooks/hillclimb.md -> principle-build-the-lever : cites-principle
playbooks/hillclimb.md -> principle-guard-the-context-window : cites-principle
playbooks/hillclimb.md -> principle-separate-before-serializing-shared-state : cites-principle
playbooks/hillclimb.md -> principle-sequence-verifiable-units : cites-principle
playbooks/hillclimb.md -> principle-laziness-protocol : cites-principle
playbooks/hillclimb.md -> playbooks/autonomous-run.md : borrows-from (wake mechanism only)
playbooks/hillclimb.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/hillclimb.md -> playbooks/perf-issue.md : distinguishes-from
playbooks/runtime-forensics.md -> control-skill : calls
playbooks/runtime-forensics.md -> principle-guard-the-context-window : cites-principle
playbooks/runtime-forensics.md -> poteto-agent : spawns-subagent (artifact parsing)
playbooks/runtime-forensics.md -> playbooks/bug-fix.md : hands-off-to
playbooks/runtime-forensics.md -> playbooks/perf-issue.md : hands-off-to
playbooks/trace-forensics.md -> principle-guard-the-context-window : cites-principle
playbooks/trace-forensics.md -> poteto-agent : spawns-subagent (artifact parsing)
playbooks/trace-forensics.md -> playbooks/runtime-forensics.md : distinguishes-from
playbooks/trace-forensics.md -> playbooks/bug-fix.md : hands-off-to
playbooks/trace-forensics.md -> playbooks/perf-issue.md : hands-off-to
playbooks/feature.md -> how : calls
playbooks/feature.md -> architect : calls
playbooks/feature.md -> arena : calls
playbooks/feature.md -> interrogate : calls
playbooks/feature.md -> poteto-agent : spawns-subagent (feature model)
playbooks/feature.md -> setup-pstack : configured-by (feature role)
playbooks/feature.md -> principle-separate-before-serializing-shared-state : cites-principle
playbooks/feature.md -> principle-model-the-domain : cites-principle
playbooks/feature.md -> principle-laziness-protocol : cites-principle (to say it does not override step 4)
playbooks/feature.md -> principle-sequence-verifiable-units : cites-principle
playbooks/feature.md -> poteto-mode#Comments : cites-section
playbooks/bug-fix.md -> poteto-mode#Non-negotiables : cites-section
playbooks/investigation.md -> poteto-mode#Autonomy : cites-section
playbooks/feature.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/refactoring.md -> how : calls
playbooks/refactoring.md -> architect : calls
playbooks/refactoring.md -> control-skill : calls
playbooks/refactoring.md -> poteto-agent : spawns-subagent (refactoring model)
playbooks/refactoring.md -> setup-pstack : configured-by (refactoring role)
playbooks/refactoring.md -> principle-model-the-domain : cites-principle
playbooks/refactoring.md -> principle-foundational-thinking : cites-principle
playbooks/refactoring.md -> principle-redesign-from-first-principles : cites-principle
playbooks/refactoring.md -> principle-subtract-before-you-add : cites-principle
playbooks/refactoring.md -> principle-laziness-protocol : cites-principle
playbooks/refactoring.md -> principle-migrate-callers-then-delete-legacy-apis : cites-principle
playbooks/refactoring.md -> principle-prove-it-works : cites-principle
playbooks/refactoring.md -> principle-minimize-reader-load : cites-principle
playbooks/refactoring.md -> principle-sequence-verifiable-units : cites-principle
playbooks/refactoring.md -> figure-it-out : routes-to
playbooks/refactoring.md -> playbooks/feature.md : routes-to
playbooks/refactoring.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/prototype.md -> principle-laziness-protocol : cites-principle (inverted here)
playbooks/prototype.md -> principle-exhaust-the-design-space : cites-principle
playbooks/prototype.md -> control-skill : calls
playbooks/prototype.md -> playbooks/feature.md : hands-off-to
playbooks/prototype.md -> architect : hands-off-to
playbooks/visual-parity.md -> principle-separate-before-serializing-shared-state : cites-principle
playbooks/visual-parity.md -> control-skill : calls
playbooks/visual-parity.md -> Cursor /loop : calls
playbooks/visual-parity.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/authoring-a-skill.md -> create-skill (Cursor built-in) : calls
playbooks/authoring-a-skill.md -> principle-encode-lessons-in-structure : cites-principle
playbooks/authoring-a-skill.md -> playbooks/opening-a-pr.md : hands-off-to
playbooks/eval.md -> arena : refers-to-step (Phase B, Phase C)
playbooks/eval.md -> arena : spawns-subagent (candidates and judge per arena)
playbooks/opening-a-pr.md -> deslop (cursor-team-kit) : calls
playbooks/opening-a-pr.md -> no-comments : calls
playbooks/opening-a-pr.md -> technical-writing : calls
playbooks/opening-a-pr.md -> unslop : calls
playbooks/opening-a-pr.md -> interrogate : calls (subagent that opens a PR)
playbooks/opening-a-pr.md -> gh / origin CLI : runs-script (external CLI, resolved per repository)
playbooks/opening-a-pr.md -> playbooks/babysit.md : distinguishes-from (does not start a babysit)
playbooks/babysit.md -> references/bugbot-triage.md : reads-reference
playbooks/multi-phase-plan.md -> references/bugbot-triage.md : reads-reference
```

---

## 4. 边界判据

以下每条先写原文依据，再写推断。

### 4.1 什么让一段内容成为 playbook 而不是技能

原文依据：

- playbook 的入口是「任务类型」：路由表每行定义一类用户请求（"A reported defect to ..."、"Read-only question: ..."），mode 按请求匹配（第 117 行 "Match the task to a playbook below"）。
- playbook 的主体是「按顺序用哪些技能和原则」：investigation 的 4 步里 3 步是「路由到 how / why」「unslop」；feature 的 8 步里 1、2、4、7、8 是 how、architect、arena、interrogate、Opening a PR。
- playbook 的步骤要能被逐字抄进待办清单（第 117 行），跳过也要留痕。所以每步开头是一个可勾掉的动作。
- playbook 有 `**Reply:**` 行，定义这一类任务交付给人的内容。
- playbook 没有 frontmatter、不在插件的技能列表里，不能单独被调用。

推断：

- 判据是「谁来决定顺序」。playbook 决定一类任务里各能力的先后与取舍；技能提供一种能力，在多个 playbook 里被复用（how 被 investigation、bug-fix、perf-issue、hillclimb、feature、refactoring 六个调用）。
- 「交付物形状」是另一条判据：每个 playbook 对应一种交付（诊断 / PR / 决定 + 草图 / 评测结论），Reply 行把它写死；技能的输出格式（例如 how 的 Overview / Key Concepts ...）是能力本身的形状，被 playbook 借用（investigation 步骤 3）。

### 4.2 能力技能内部自带多步流程，为什么没被拆成 playbook

原文依据（只看了标题）：`architect/SKILL.md` 有 `## Phase A: Ground the problem` 到 `## Phase E`；`arena` 有 Phase A-F；`swarm` Phase A-D；`how` 有 `## Step 1. Assess Complexity` 到 `## Step 4. Present`；`tdd` 有 `## Workflow` 1-6 步；`figure-it-out` Phase A-E。eval playbook 直接引用 arena 的 "Phase B"、"Phase C"，而不是复制它们。

推断：

- 这些内部阶段是「一种能力怎么完成」，与任务类型无关，被多个 playbook 复用。拆成 playbook 会让它失去被多处按名字调用的能力，并且会和 mode 的路由表冲突（它们不是用户请求的一种类型）。
- 内部阶段只调度自己的子代理（arena 的 fan-out、cross-judge），不在多个技能之间选择先后；playbook 则在多个技能、原则之间排先后。
- 技能要能脱离 mode 使用：它们有 frontmatter 和斜杠命令（README 第 143 行 "the other skills fire as the steps need them. a few i reach for directly."）。playbook 只在 mode 里存在。
- 例外是 `figure-it-out`：它是技能，但职责是「为没有合适 playbook 的任务现场设计一个 playbook」（其 description "Design an auditable playbook when no narrower one fits"）。它放成技能而不是 playbook，推断是因为它的产物是一个新的流程，而不是执行一个固定流程。

### 4.3 原则为什么单独成技能，而不写在调用方里

原文依据：

- `docs/guide/08-principles.md` 第 5 行 "You don't invoke principles. You use their names to steer. Each name points at a complete rule the agent has already read, so one phrase redirects the work more precisely than a paragraph of instructions."
- mode 第 15 行要求在回复里点名原则和它改变的决定，且只能引用读过的 leaf；第 27 行 guide 原文 "A principle citation with no decision behind it is the tell that it name-dropped instead of applying."
- 原则技能的 description 以 "Apply ..." 开头写适用条件（`principle-prove-it-works` "Apply after completing a task, before declaring done."；`principle-guard-the-context-window` "Apply when context is filling up ..."），与能力技能 "Use for ..." 的写法不同。
- 原则正文装的是一条规则 + `**Why:**` 理由 + 若干做法（`principle-prove-it-works` 第 9-22 行）。

推断：

- 原则被多个 playbook 共用，单独成技能就只写一次。我负责的 13 个 playbook 里，sequence-verifiable-units 被 5 个引用，prove-it-works、guard-the-context-window、separate-before-serializing-shared-state、laziness-protocol、model-the-domain 各被 2-4 个引用。
- 原则单独成技能还带来一个「名字」。名字让用户能用一个短语纠偏，让 agent 在回复里被检查是否真的用了（引用即要写改变了哪个决定）。
- 原则跨任务类型（调试、重构、功能都适用），不属于任何一个 playbook；它的触发是「情境」（"Context fills up"、"Two or more fixes that share one premise have failed"），不是「任务类型」。

### 4.4 仍写在调用方正文里、没有抽成原则的规则

原文可见、只在一处出现的规则（推断：因为只有一个调用方，抽出来没有复用价值）：

| 规则 | 出处 |
| --- | --- |
| "Belt-and-suspenders that 'might help' is a hypothesis, not a fix. It does not ship. When evidence refutes a hypothesis, revert what it motivated." | `bug-fix.md` 首段 |
| 请用户复现的窄例外 | `bug-fix.md` 步骤 1 |
| "one change, one measurement, keep or revert. Never stack untested changes" | `hillclimb.md` 首段 |
| 停机谓词要把目标和尝试次数下限配对；"Don't relax the predicate to meet it" | `hillclimb.md` 步骤 1、7 |
| "Type check and lint are not a pin." | `refactoring.md` 步骤 1 |
| "The reshape must delete branches or invalid states, not add indirection." | `refactoring.md` 步骤 2 |
| 防走捷径条款 | `visual-parity.md` 步骤 2 |
| 盲测七条 | `eval.md` "Non-negotiables for blinding" |
| "No decision means no prototype." | `prototype.md` 步骤 1 |
| 没有配对抓取就只算最强假设 | `trace-forensics.md` 步骤 5 |
| "Inconclusive or wrong-surface is not a pass. Flag it." | bug-fix 4、perf-issue 4、feature 5（三处重复，却没有抽成原则；它与 principle-prove-it-works 内容相近） |
| mode 自己的规则：先分类再 `AskQuestion`、坏技能单开 PR 修、Always pause 列表、"No is an acceptable answer" | `SKILL.md` Non-negotiables 第 20、34 行，Autonomy |

最后一行值得注意：mode 的「先分类再提问」和 Autonomy 的 "Just do it" 与 `principle-never-block-on-the-human` 的索引要点（"Tempted to ask 'should I do X?' on reversible work. Proceed, present the result"）重叠，但 mode 仍把更细的版本写在自己正文里。推断：mode 里的是 poteto 个人的操作细则（何时 prototype 代替提问、全自主授权下怎么报告默认值），原则只是通用判断。

### 4.5 什么让内容成为 reference 而不是正文

原文依据（`bugbot-triage.md`）：

- 只在一个子步骤里需要：第 3 行 "Use this reference when the Babysit playbook ... handles Bugbot or review-automation comments."
- 体量远大于 playbook：142 行，而 13 个 playbook 在 11-33 行之间。
- 它是一份会增长的数据：有追加模板（`## Learned pattern format`）、置信度升级规则（candidate → recurring → strong）和追加区（`## Candidate learnings from recent babysits`，"Append new candidate learnings here during or after babysitting"）。

推断：reference 的判据是「按需加载 + 体量大 + 会随使用持续追加的案例或判据」。如果把它写进 babysit 正文，每次读 babysit 都要付这 142 行的上下文代价，而且追加学习会不断改动流程文件。

### 4.6 什么成为脚本而不是文字

我负责的文件里没有直接运行 pstack 自带脚本的步骤。相关原文：

- mode 的 Meta 原则索引（第 77 行）"You catch yourself writing the same instruction a second time. Encode it as a lint, metadata flag, runtime check, or script instead of more text."
- `authoring-a-skill.md` 尾段 "Point at structural sources (types, READMEs, config) per the **encode-lessons-in-structure** principle skill."
- 脚本属于任务产物的情形：hillclimb 步骤 2 的测量 harness（"one repeatable command emits the metric"，挂 build-the-lever）；refactoring 步骤 6 的等价检查 "a script that diffs old-vs-new outputs"。这些是 agent 为当前任务造的 lever，不是插件自带脚本。
- 插件自带脚本的例子不在我的文件里：`playbooks/multi-phase-plan.md` 第 10 行运行 `scripts/check-plan.mjs` 并挂 encode-lessons-in-structure（grep 结果）；`check-plan.mjs` 开头把计划文件必须出现的小节名写成常量（`SUB_BLOCKS`、`PROGRAM_H3` 等，只读了前 30 行）。

推断：pstack 的判据是「同一条要求第二次写成文字仍被违反时，就改成可执行的检查」，以及「证明工作需要能被评审者重跑」。

---

## 5. 重复与例外

### 5.1 同一规则或步骤的多处重复

| 重复内容 | 出处 |
| --- | --- |
| deslop → no-comments → technical-writing → unslop 这组提交前 / 评审前处理 | mode Non-negotiables 第 26-29 行；`opening-a-pr.md` **PRs.** 段 |
| 开 PR 不触发 Babysit | mode 第 31 行 "Never triggered by merely opening a PR."；`opening-a-pr.md` **Babysit.** 段 |
| Bugbot 要怀疑地逐条分类 | mode 第 33 行；`bugbot-triage.md` 全文；`babysit.md` 步骤 8（grep 所见） |
| "Inconclusive or wrong-surface is not a pass. Flag it." | bug-fix 4、perf-issue 4、feature 5 |
| 跨函数边界先 architect | mode 第 22 行；bug-fix 3、perf-issue 3（原文同一句 "If it crosses a function boundary, `architect` first."）；refactoring 3 |
| 委派给「你配置的某角色模型（默认 `grok-4.7-xhigh-fast`）」 | mode Subagents 第 93 行；bug-fix 3、perf-issue 3、hillclimb 5、feature 4、refactoring 5 |
| 先命名数据形状，按 model-the-domain 选结构 | mode 第 21 行；feature 4；refactoring 2 |
| 大产物交子代理解析（guard-the-context-window） | runtime-forensics 2；trace-forensics 1 |
| `throughput checkpoint: n/a, ...` 固定行 | investigation 2；runtime-forensics 5；trace-forensics 6 |
| rebase 成小而有序的提交 | feature 6；refactoring 8；`opening-a-pr.md` **Commits.** |
| 在同表面复现 / 验证（control skill） | mode 第 30 行；bug-fix 1、4；perf-issue 1；runtime-forensics 1；refactoring 6；prototype 5；visual-parity 4 |
| 不因「可能有用」保留改动 | bug-fix 首段；hillclimb 步骤 5 "A tweak that 'might help' is not kept."；refactoring 步骤 4 "A speculative cleanup that 'might help' gets reverted." |
| 原则要点在 mode 索引里再写一遍 | mode Principles 每行的要点句与各 `principle-*` 的 description 基本同义（例：索引 "Verify against the real artifact, not a proxy or 'it compiles'." 与 `principle-prove-it-works` description） |
| 同一原则的多种称呼 | 见 2.3 节表格：`**sequence-verifiable-units** principle skill`、`**principle-model-the-domain**`、`the **principle-guard-the-context-window** skill`、显示名 `Laziness Protocol` 并存 |

### 5.2 pstack 自身违反「分层」的地方

| 现象 | 出处 | 说明 |
| --- | --- | --- |
| playbook 里写了大段做法 | `perf-issue.md` 步骤 2 的八个策略族 | 这是一份性能优化的技术目录，与「按顺序用哪些能力」无关。推断：按 4.5 的判据它更像 reference 或技能 |
| playbook 整体是标准而不是流程 | `opening-a-pr.md` | 没有编号步骤、没有所有权行、没有 Reply 行，内容是 PR 约定、命令与格式。形式上叫 playbook，实质是一份被所有交付型 playbook 共用的规范 |
| playbook 内一步塞入多条做法与规则 | `feature.md` 步骤 4 | arena 强制条款、注释、手术式编辑、共享原语移植、多提交都在一步里 |
| playbook 尾段是写作做法 | `authoring-a-skill.md` 尾段 | "When in doubt, delete ... Delegate to other skills by path. Don't restate." |
| playbook 规定输出 schema | `hillclimb.md` 步骤 3 的 `decision.tsv` 列定义 | 格式定义放在流程步骤里；同时它依赖 show-me-your-work 技能 |
| playbook 定义跨组件概念 | `feature.md` 步骤 3 定义 throughput checkpoint | mode 第 25 行和另外三个 playbook 都引用它，定义却放在一个具体 playbook 的第 3 步里 |
| mode 按编号引用 playbook 内部步骤 | mode 第 25 行 "(Feature step 3)"、第 30 行 "the narrow Bug fix step 1 exception" | mode 与具体 playbook 的步骤编号耦合，改动 feature 或 bug-fix 的步骤顺序会让 mode 的引用失效 |
| mode 写了流程顺序和决策程序 | mode 第 20 行 `AskQuestion` 那条（分类 → prototype 或 investigation → 全自主授权下的处理）；第 117 行待办清单协议 | 前者是一段多分支的决策程序，放在触发器列表里 |
| playbook 引用技能内部阶段 | `eval.md` 步骤 4、5 "per the **arena** skill's Phase B / Phase C" | 与 arena 的阶段编号耦合 |
| playbook 宣称自身是原则的范例 | `bug-fix.md` 步骤 5 "This is the canonical **sequence-verifiable-units** principle skill" | playbook 在给原则下定义 |
| 原则里有做法段 | `principle-prove-it-works` 的 `## Script the check when you can`（只读了前 22 行） | 原则也装做法，不只装判断 |
| 声称与实际不符 | `opening-a-pr.md` 第 3 行、mode 第 143 行 "Invoked at the end of every other playbook." | investigation 明写不开 PR；runtime-forensics、trace-forensics、prototype、eval 没有这一步 |
| mode 调用的技能不在本插件 | mode 第 26 行 create-skill（Cursor 内置）、第 28 行 deslop 与第 30 行 control-cli / control-ui（`cursor-team-kit` 插件） | 插件对外部插件有硬依赖，快照内没有安装检查（推断：由用户自行安装 cursor-team-kit） |
| frontmatter `name` 与目录名不一致 | mode `name: Poteto Mode` | 其他 46 个技能 `name` 都等于目录 slug |
| 通用写法规则与 reference 自身排版冲突 | mode 第 102 行禁用长破折号（针对回复）；`bugbot-triage.md` 第 98、107 行用了 `—` | 规则明写只针对回复，所以不算违规，只是风格不统一 |
| Bug fix 引用了一个它自己的步骤 3 里没有的动作 | `bug-fix.md` 步骤 2 "before the step-3 architect/interrogate fan-out"，但步骤 3 只写 architect，没有 interrogate | 行文漂移 |

---

## 6. 状态与重入

原文写明的机制：

- **待办清单是 playbook 进度的唯一载体**：mode 第 117 行，匹配后把 playbook 步骤逐字抄入待办清单，放在任务特有待办之前；不做的步骤保留并写 `skip: <reason>`。`docs/guide/02-poteto-mode.md` 第 38 行 "A skipped step stays visible with `skip: <reason>`."
- **重新匹配**：`docs/guide/02-poteto-mode.md` 第 64 行，用户说 "new task" 才重新匹配，否则 "a mode mid-Feature tends to treat your question as the next feature step"。frontmatter `reminder` 的第一个词就是 "New task?"。
- **不信任中断续跑**：mode 第 95 行 "Interrupt-chained resumes silently drop directives, so fire a fresh subagent with consolidated scope rather than trusting a 'done' summary."；`feature.md` 尾段 "Rewrite the checkpoint at phase boundaries. Spawn a fresh owner rather than chaining interrupts."
- **持久决策记录**：mode 第 35 行，长 / 自主 / 多阶段 / 用户离开的任务用 show-me-your-work 留 decision trail，"Commit it when stakes need an auditable record. Keep it local otherwise."；`hillclimb.md` 步骤 3 的 `decision.tsv`，"Read it before each attempt. Keep it out of the tree (gitignored)."——这是本组唯一在每次循环开头读回的持久状态。
- **跳步的规则性限制**：`feature.md` 步骤 3 的四项检查点不适用时保留为 `n/a: <reason>`；步骤 4 的 arena 委派 "Mandatory: no skip-with-reason escape"。investigation / forensics 把检查点写成固定的 `n/a` 行。
- **跨会话学习状态**：`bugbot-triage.md` 的追加区与置信度升级规则，是 reference 层面的持久知识。
- **暂停与接手**：mode 路由表里的 Pause safely 与 Session pickup 两个 playbook 负责（不在我的范围，未读）。

推断：

- playbook 本身无状态文件；进度靠宿主的待办工具，中断后能否续上取决于宿主是否保留待办清单，以及 Pause safely / Session pickup 的做法。
- 幂等与重试由 `principle-make-operations-idempotent` 在原则层表达，13 个 playbook 里没有一个直接引用它。

---

## 未确定

- `mode: true`、`reminder`、`icon`、`color` 在 Cursor 宿主里的确切行为（何时注入 reminder、mode 如何持续生效）。快照里没有定义，本报告只做了推断。
- `disable-model-invocation: true` 在 Cursor 里的确切含义（是否完全阻止模型按 description 自动加载）。推断为「只能显式调用」，未在快照中核实。
- playbook 用 `###` 三级标题、mode 写 "The per-playbook lines below" 是否说明 playbook 曾内联在 SKILL.md 中。只是推断，没有看 git 历史（快照不含历史）。
- 「control skill」在不同表面（CLI / UI）之间怎么选，原文只在 mode 第 30 行给出两者分工，playbook 内一律只写 "the control skill"。
- `bugbot-triage.md` 后半条目是否由 agent 在 babysit 中自动追加，原文只写了「应该追加」，没有写由谁追加。
- 能力技能（architect、arena、swarm、how、tdd、figure-it-out、show-me-your-work）的正文我只看了章节标题，4.2 节关于其内部流程的结论只依据标题和 eval 对 arena Phase B / C 的引用。

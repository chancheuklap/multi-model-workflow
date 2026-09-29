# L3-pstack-capability-skills-a：pstack 能力技能（how、why、recall、teach、blast-radius、architect、arena、swarm、interrogate、figure-it-out）的组件解剖

范围：`docs/research/code-landing-refs/pstack/skills/` 下 10 个技能目录的全部文件（共 29 个文件，全部逐行读完）。下文 `skills/` 即指 `docs/research/code-landing-refs/pstack/skills/`，`agents/`、`README.md`、`docs/guide/` 指 `docs/research/code-landing-refs/pstack/` 下同名路径。

为回答"谁调用它"和"模型角色名"，另外读了这些范围外的片段，只作连线证据：`skills/poteto-mode/SKILL.md` 第 1 到 140 行（frontmatter、`## Non-negotiables`、`## Principles`、`## Subagents`、`## Playbooks`）；`skills/setup-pstack/SKILL.md` 第 36 到 74 行（`### 5. Write the rule` 到 `### 7.`）；`skills/poteto-mode/playbooks/investigation.md`、`authoring-a-skill.md` 全文；`feature.md` 第 3 到 12 行；`skills/principle-exhaust-the-design-space/SKILL.md` 前 20 行；`agents/poteto-agent.md` 前 10 行；README 技能表（第 90 到 135 行）；另外用 grep 取了其他 playbook、`skills/no-comments/SKILL.md`、`agents/comment-sicko.md` 里点名这 10 个技能的那几行。这些文件的其余部分没有读，涉及它们的结论只到"该行这样写"为止。

标注约定：没有标注的结论都是"原文写明"，并给出处；标"推断"的是我根据写法得出、原文没有直说的判断。

---

## 1. 组件清单

| 文件 | 行数 | 组件类型 | 管什么 |
|---|---|---|---|
| `skills/how/SKILL.md` | 56 | 能力技能 | 回答"X 怎么工作"：按复杂度派 1 个 explainer 或 2 到 4 个 explorer 加 1 个 explainer，产出架构讲解 |
| `skills/how/references/explorer-prompt.md` | 52 | reference（subagent 提示模板） | explorer subagent 的完整提示，含探索顺序和返回结构 |
| `skills/how/references/explainer-prompt.md` | 55 | reference（subagent 提示模板 + 输出格式） | explainer subagent 的提示，定义 Overview / Key Concepts / How It Works / Where Things Live / Gotchas |
| `skills/why/SKILL.md` | 156 | 能力技能 | 回答"为什么这样写"：建代码锚点，按可用 MCP 每类证据派一个 investigator，再派 synthesizer |
| `skills/why/references/investigator-prompt.md` | 103 | reference（subagent 提示模板） | investigator 的提示：只收证据、不下结论、只在本来源内追链接 |
| `skills/why/references/synthesizer-prompt.md` | 135 | reference（subagent 提示模板 + 输出格式 + 自检清单） | synthesizer 的提示与最终输出结构 |
| `skills/why/references/epistemics.md` | 144 | reference（判断框架） | 五级置信度（Direct / Supported / Inferred / Speculative / Unknown）和措辞规则 |
| `skills/why/references/source-playbook.md` | 17 | reference（索引） | 证据类别到来源文件的对照表 |
| `skills/why/references/sources/*.md`（8 个） | 15 到 100 | reference（按来源的检索指南） | 每类 MCP 各一份：装什么、怎么搜、好证据长什么样、常见坑、返回什么；`incident-postmortem.md` 是跨来源角度 |
| `skills/recall/SKILL.md` | 35 | 能力技能 | 从自己的聊天记录和共享记录重建近期工作上下文，交回简报 |
| `skills/teach/SKILL.md` | 21 | 能力技能（组合型，调用 how 与 why） | 把 how 与 why 的发现编成一份让人真正理解的讲解 |
| `skills/blast-radius/SKILL.md` | 50 | 能力技能 | 找出改动在别处可能弄坏什么，并用运行真代码证明"它安全所依赖的那一个事实" |
| `skills/architect/SKILL.md` | 83 | 能力技能（带 A 到 E 五阶段，调用 how、why、arena） | 先写类型与签名草图，多模型比较后按草图实现，草图错了就推倒 |
| `skills/architect/references/design-red-flags.md` | 33 | reference（筛查清单） | 四类设计红旗：Shallow module、Information leakage、Temporal decomposition、Pass-through method |
| `skills/architect/references/rationale-template.md` | 35 | reference（产物模板） | 设计说明的七个固定章节 |
| `skills/architect/references/runner-prompt.md` | 20 | reference（subagent 提示） | 每个并行设计 runner 的提示，列出设计纪律并点名原则 |
| `skills/arena/SKILL.md` | 71 | 能力技能（带 A 到 F 六阶段） | N 个候选做同一件事，交叉评审，选底稿，嫁接其余候选的长处，再验证 |
| `skills/swarm/SKILL.md` | 46 | 能力技能（带 A 到 D 四阶段） | N 个并行 worker 分片或竞速，汇总成一份报告 |
| `skills/interrogate/SKILL.md` | 110 | 能力技能 | 每个配置模型各派一名对抗式 reviewer，主 agent 汇总并分四档裁决 |
| `skills/interrogate/references/reviewer-prompt.md` | 70 | reference（subagent 提示模板 + 输出格式） | reviewer 提示，含 severity 分级与发现格式 |
| `skills/interrogate/references/rubric.md` | 77 | reference（评审清单） | Correctness、Root Causes vs. Symptoms、Structural Integrity、Verification、Complexity Budget、Security 六个视角 |
| `skills/interrogate/references/code-quality-review.md` | 47 | reference（评审清单） | 代码质量视角：0 到 7 八条维度、Approval Bar、Review Tone |
| `skills/interrogate/references/lead-judgment.md` | 58 | reference（判断框架） | 主 reviewer 过滤发现的原则（Nitpick Gravity 等）与裁决校准 |
| `skills/figure-it-out/SKILL.md` | 53 | 能力技能，但内容是"设计一份 playbook"的元流程 | 没有现成 playbook 匹配时，先设计本次任务的阶段列表，再按假设循环执行并留审计记录 |

这 10 个目录里没有 `scripts/`、没有 agent 定义、没有配置文件。它们用到的模型配置在别处：`skills/setup-pstack/SKILL.md` 写出的 `~/.cursor/rules/pstack-models.mdc`（`### 5. Write the rule`）。

---

## 2. 解剖

### 2.1 frontmatter（10 个 SKILL.md 共同）

- 10 个 SKILL.md 的 frontmatter 都只有三个键：`name`、`description`、`disable-model-invocation: true`。没有一个带 `mode`、`reminder`、`icon`、`color`、`paths`。`mode: true` 与 `reminder:` 只出现在 `skills/poteto-mode/SKILL.md` 的 frontmatter（`mode: true`，`reminder: New task? Playbook match or rigor needed -> apply /poteto-mode. ...`）。
- `disable-model-invocation: true` 在 pstack 里几乎全员都有：`skills/` 下只有 `setup-pstack/SKILL.md` 没带它（grep 结果），原则技能 `principle-*` 也全部带。README 的解释是这些技能由 `/poteto-mode` "runs most of these for you when a step needs them"，技能表"is for when you want one directly"（`README.md`，`## skills`）。推断：`disable-model-invocation: true` 让技能不按描述被自动加载，只在用户打斜杠命令或上层技能/playbook 点名时读取；pstack 用 poteto-mode 的路由表取代了"按 description 自动触发"。原文没有一句话解释这个键的效果，此项仍属推断。
- `description` 的写法有两种句式：
  - "Use for ..." 开头，先列触发短语，再说做什么，最后指向兄弟技能：`how`（"Use for \"how does X work\" ... Use why for motivation."）、`why`（"... Use how for runtime behavior."）、`interrogate`（"Use for \"interrogate\", \"adversarial review\" ..."）。
  - 先一句说做什么，再"Use for /<name>, '<短语>', or <情形>"：`recall`、`teach`、`blast-radius`、`architect`、`arena`、`swarm`、`figure-it-out`。
  - 共同点：都把斜杠名或口语触发短语原样放进引号；`how` 与 `why` 在描述末尾互相指路。

### 2.2 正文结构，逐个技能

**how**（`skills/how/SKILL.md`，56 行）
- 顺序：一段目标（"at the level of a senior engineer onboarding onto a subsystem"）→ `## Step 1. Assess Complexity`（判定 Simple / Complex，"When in doubt, take the simple path."）→ `## Step 2a. Explore` → `## Step 2b. Direct Explain` → `## Step 3. Synthesize` → `## Step 4. Present` → `## Output Format`。
- 内容类型：Step 1 是触发条件与分支；Step 2a/2b/3 是 subagent 参数（`subagent_type`、`model`、`readonly` 三个键的列表）加"用哪个 reference 做提示"；Step 4 是一句呈现规则（"Do not substantially rewrite it."）；Output Format 只指向 reference。
- 语气：祈使句，第二人称，短句。理由几乎没有，只有步骤和参数。
- references：两个都是完整的 subagent 提示，以"Build ... prompt from this template. Fill in the placeholders."开头，`---` 之后是给 subagent 的正文，用 `{QUESTION}`、`{EXPLORATION_ANGLE}`、`{EXPLORER_FINDINGS_ALL}` 占位。`explorer-prompt.md` 内含一个 5 步探索顺序（"Find the entry point" → "Trace the flow" → "Map the key abstractions" → "Find the boundaries" → "Look for the non-obvious"）和 6 节返回结构。`explainer-prompt.md` 内含最终输出的 5 节结构和 `## Communication Style`。

**why**（`skills/why/SKILL.md`，156 行，10 个技能里最长）
- 顺序：一句目标 → 与 how 的分工 → `## Operating Posture`（指向 `references/epistemics.md`）→ `## Step 1. Understand the Target and the Question` → `## Step 2. Establish the Code Anchor`（内嵌两段 bash 命令：`git blame -L`、`git log --follow -p`、`gh pr view <number> --json ...`）→ `## Step 3. Spawn Parallel Investigators (default posture)`（`### Discovery`、`### Investigator roster`、`### When to skip an investigator`）→ `## Step 4. Synthesize` → `## Step 5. Present` → `## Output Format` → `## Common Failure Modes to Avoid`（只有 Recency bias 一条）→ `## Reference Files`（索引）。
- 内容类型：Step 2 是命令与参数；Step 3 是 7 类证据分类法、每类的"最擅长找出什么"、跳过的两条合法理由（"No MCP is available"、"provably irrelevant"）；Step 4 是 synthesizer 的参数与 5 项输入；Output Format 指向 synthesizer 模板并追加一条："if the user's `why` question is a precursor to actually changing this code, convert the lineage findings into a Preserve / Change / Avoid / Risk constraint set"。
- 独有做法：`readonly: false` 并写明理由（"**Do not use readonly/Ask mode.** It strips MCP access"）。
- references 的分层：`epistemics.md` 是判断框架（五级置信度、措辞表、"The Sycophancy Trap"、"Calibration Check Before Finalizing"）；`investigator-prompt.md` 与 `synthesizer-prompt.md` 是 subagent 提示；`source-playbook.md` 是 17 行索引表；`sources/*.md` 每份按同一套小节写：`## What this source contains` → `## How to search it`（含具体 MCP 工具名或 SQL/bash）→ `## What good evidence looks like here` → `## Common pitfalls` → `## What to return`。`incident-postmortem.md` 例外，它不是一个来源，而是"a **cross-cutting angle**"，按来源逐条列要搜什么。

**recall**（`skills/recall/SKILL.md`，35 行）
- 顺序：粗体一句目标（"**Before you start or resume work, you rebuild ...**"）→ 两段背景（两份记录；transcript 的磁盘路径规则）→ 编号步骤 1 到 6 → `## Output contract` → `**Reply:**` 行。
- 步骤 1 是路由（"One specific prior chat to resume is the `session-pickup` playbook, not this. Turning habits into a durable skill is `automate-me`."）；步骤 2 锁范围（默认 7 天、默认当前 workspace）；步骤 3 派并行 subagent 读聊天记录，写明每个 subagent 的检索做法与返回 schema；步骤 4 把 why 的 source investigator 拿来用；步骤 5 用 `git`、`gh` 核对；步骤 6 按合同写简报。
- 输出合同：Capsule（至多 5 条）、Threads（每行一个状态标签，六选一：`[merged #N]`、`[open PR #N]`、`[in flight <branch>]`、`[verified, uncommitted]`、`[reverted #N]`、`[planned, not started]`）、Problems（至多 5 条）、Next move。
- 没有 references，没有独立小节标题的步骤，步骤写成长段落。

**teach**（`skills/teach/SKILL.md`，21 行，行数最少但单行极长）
- 顺序：粗体一句目标 → 一段定位（"Teach sits on top of `how` and `why`"）→ 编号 1 到 5（决定要讲清哪几点 → 让 how 和 why 干活 → 先给通用定义再落到本例 → 保持对话 → 一图一图地搭）→ 一段写作风格 → `**Reply:**` 行。
- 内容主要是做法与写作规范，不是流程顺序；第 5 条非常具体（"to teach a flow from A to B to C, draw it three times"；空间性内容用图像生成工具，"marker-on-whiteboard style"）。
- 风格段落大量是 unslop 类规则（"No em dashes. Prefer periods over commas. Keep each sentence to one or two commas."）以及禁用词表（"the key insight", "TL;DR" 等）。

**blast-radius**（`skills/blast-radius/SKILL.md`，50 行）
- 顺序：目标 → 与 how、why 的分工（"`how` tells you what the code does. `why` tells you why it's shaped that way. Blast radius tells you what it breaks somewhere else."）→ "Listing the callers is not the job." → `## Don't trust your own writeup`（内含 `### How sure are you`，五级证据阶梯：You said so → You pointed at the line → You showed the bad case can't happen → You ran it → You reproduced it in the running app）→ `## Steps`（1 到 6）→ `## What to hand back`（五项）→ 一句写作要求 → `**Reply:**` 行。
- 内容：理由与判断（为何不信自己写的结论）排在步骤之前；步骤里第 3 步是做法清单（"Look where grep stops"：库源码、固定版本、微任务、teardown、wire format、feature flag）。

**architect**（`skills/architect/SKILL.md`，83 行）
- 顺序：目标段 → `## Start`（"Open a todolist with one entry per phase before starting."，列 Ground / Sketch / Agree / Implement / Scrap）→ `## Phase A: Ground the problem` → `## Phase B: Sketch` → `## Phase C: Agree (opt-in)` → `## Phase D: Implement against the sketch` → `## Phase E: Scrap when the architecture is wrong`（六条"Tells"列表 + 推倒后的四步）→ `## Outputs`。
- 内容：几乎每个阶段都点名一个下游技能或原则（见第 3 节）。Phase B 是做法与筛选标准（"Design it twice. Require at least two structurally distinct candidates"；"Compare viable candidates on interface depth"）；Phase C 是人工检查点的触发条件（默认不停，"Opt in ... when the invoker explicitly asks"）；Phase E 是判断标准（"The signal is a *pattern*, not single instances."）。
- references：`runner-prompt.md` 第一段是给编排者的说明（"The orchestrator passes this file through to every parallel candidate runner"），第二段起是给 runner 的正文，开头要求"Read the **architect** skill in full first. That's the workflow you're inside."；`rationale-template.md` 是产物模板，章节为 Problem / Usage (caller's view) / Shape / Synthesis decision / Tradeoffs accepted / Alternatives considered / Open questions and risks / Next implementation step，每节用斜体写"该填什么"；`design-red-flags.md` 是四个红旗的定义与识别信号。

**arena**（`skills/arena/SKILL.md`，71 行）
- 顺序：目标段 → `## Start`（todolist，六项 Frame / Fan out / Cross-judge / Pick / Graft / Verify）→ `## Phase A: Frame`（四步：定产物、推 3 到 6 条 rubric、选 runner、分配输出路径）→ `## Phase B: Fan out` → `## Phase C: Cross-judge` → `## Phase D: Pick a base` → `## Phase E: Graft` → `## Phase F: Verify` → `## Outputs`。
- 内容：步骤顺序和判断标准混写。关键判断句："Pick the base on which candidate a future maintainer can extend most easily without breaking invariants."；"When N candidates wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence."
- 没有 references。

**swarm**（`skills/swarm/SKILL.md`，46 行）
- 顺序：目标段 → `## Start`（todolist，四项 Frame / Fan out / Aggregate / Report）→ `## Phase A: Frame`（五步：完成判据、形态 partition/race/mix 与选择规则 `first pass` / `rank all` / `best-of`、N、worker 模型、每个 worker 独立输出与 SHA/测量方法）→ `## Phase B: Fan out`（参数：`subagent_type: generalPurpose`、`environment: "cloud"`、`run_in_background: true`、`cloud_base_branch`；报告词汇 `PASS` / `ISSUES` / `BLOCKED`）→ `## Phase C: Aggregate`（缺 SHA 与方法的结果丢弃并重跑一次，"After a second miss, record a gap. A gap does not count as a pass."）→ `## Phase D: Report`。
- 没有 references。

**interrogate**（`skills/interrogate/SKILL.md`，110 行）
- 顺序：目标段（"The adversarial signal comes from model diversity, not assigned personas."；"Do NOT auto-apply changes."）→ `## Step 1, Determine Scope`（含 `git diff main...HEAD`）→ `## Step 2, State the Intent` → `## Step 3, Spawn Reviewers`（模型表 Reviewer A/B/C、三个 subagent 参数、模型 slug 失效时的回退规则、如何拼装模板的四项输入）→ `## Step 4, Synthesize`（五项）→ `## Step 5, Lead Judgment`（四档 Act on / Consider / Noted / Dismissed）→ `## Output Format`（Intent / Reviewers / Act On / Consider / Noted / Dismissed / Agreement Map）。
- references 分工：`reviewer-prompt.md` 是 subagent 提示模板，占位 `{INTENT}`、`{DIFF_OR_FILES}`、`{RUBRIC_CONTENTS}`、`{CODE_QUALITY_CONTENTS}`，也就是说 `rubric.md` 和 `code-quality-review.md` 的全文会被粘进每个 reviewer 的提示；`lead-judgment.md` 只给主 agent 自己读（Step 5 "Read `references/lead-judgment.md` for the full framework."）。

**figure-it-out**（`skills/figure-it-out/SKILL.md`，53 行）
- 顺序：目标段（"When the task matches no playbook, design one. The deliverable before any code is the workflow itself"）→ `## Start`（todolist 第一项是"read the Principles section of the **poteto-mode** skill"）→ `## Phase A: Frame`（可证伪的完成判据、量化范围、偏高的 rigor 等级）→ `## Phase B: Design the workflow`（拆成可独立落地的单元、风险最大的先做、先建验证工具、一次性决策才调 architect、决定并行边界、把阶段列表写下来）→ `## Phase C: Run the loop`（每个单元是一次实验；裁决三值 VERIFIED / NOT VERIFIED / INCONCLUSIVE）→ `## Phase D: Keep the audit trail`（经 show-me-your-work）→ `## Phase E: Verify and hand back` → `**Reply:**` 行。
- 几乎每一小句后面都挂一个原则名（见第 3 节）。

### 2.3 全体共同的写法

- 语气一律是祈使句加第二人称，短句，以句号结束；没有长破折号（10 个 SKILL.md 与全部 references 中都没有看到 em dash）。
- 收尾格式有三种：`## Output Format`（how、why、interrogate）、`## Outputs`（architect、arena）、`**Reply:** ...` 单行（recall、teach、blast-radius、figure-it-out）。`**Reply:**` 行与 poteto-mode playbook 的收尾格式相同（例：`skills/poteto-mode/playbooks/investigation.md` 末行"**Reply:** the investigation output."）。swarm 用 `## Phase D: Report` 充当输出段。
- 阶段命名有两种：`Step N`（how、why、interrogate，带 subagent 参数表）与 `Phase A..F` 加 `## Start` 待办清单（architect、arena、swarm、figure-it-out）。
- 开头目标句有两种：普通陈述（how、why、architect、arena、swarm、interrogate、figure-it-out）与粗体一句（recall、teach）。粗体一句的写法与 poteto-mode playbook 开头的粗体"所有权句"同形（`investigation.md`："**You own the answer. Plan, route, write.**"）。

---

## 3. 调用与连线

### 3.1 谁调用它们（入边）

证据来自 grep 命中行，我只读了命中的那一行或所在段落。

- **poteto-mode 的触发表**（`skills/poteto-mode/SKILL.md`，`## Non-negotiables`）按情形点名：`how`（"Nontrivial change, architecture decision, or \"are we sure?\" → the **how** skill."）、`architect`（"Code crossing a function boundary → the **architect** skill"）、`swarm` 与 `arena`（"Parallel fan-out → the **swarm** skill ... Use **arena** for design or code bakeoffs"）、`interrogate`（"Contested design → the **interrogate** skill"）。
- **poteto-mode 的 playbook 路由**（`## Playbooks`）把 `figure-it-out` 当作 playbook 的替补："routes to the **figure-it-out** skill even when a narrower playbook like Feature fits. Use **figure-it-out** whenever no bundled playbook fits. It designs a bespoke, rigorous playbook for the task."
- **playbook 按技能名调用**（`skills/poteto-mode/playbooks/`）：`investigation.md` 第 1 步 how 与 why；`feature.md` 第 1、2、7 步 how、architect、interrogate；`bug-fix.md` 第 2、3 步 how、why、architect；`perf-issue.md` 第 2、3 步 how、architect；`refactoring.md` how、architect，大型结构工作转 figure-it-out；`hillclimb.md` 第 1 步 how；`prototype.md` 第 6 步 architect；`eval.md` 第 4、5 步"per the **arena** skill's Phase B / Phase C"；`multi-phase-plan.md` 用路径 `pstack/skills/swarm/SKILL.md`、`pstack/skills/how/SKILL.md`、`pstack/skills/interrogate/SKILL.md`；`opening-a-pr.md` "A subagent that opens a PR runs `interrogate`"；`autopilot-full.md` 第 4 步"per the **swarm** skill"。
- **其他技能与 agent**：`skills/no-comments/SKILL.md` 第 2 步"run `/how` or `/why` on their symbol"，第 3 步"run `/architect` once"；`agents/comment-sicko.md`"I run `/how`, `/why`, or both"。
- **人直接用斜杠命令**：README 技能表列了全部 10 个（`README.md`，`## skills`）；`recall`、`teach`、`blast-radius` 在 pstack 内部没有任何技能或 playbook 调用它们，只出现在 README 与 `docs/guide/03-understand.md`、`06-verify-and-ship.md`。在本快照里，这三个技能的调用方只有人（打斜杠命令）。
- **模型配置**：`skills/setup-pstack/SKILL.md`（`### 5. Write the rule`）写出的角色行里，与本组相关的是 `how explorer`、`how explainer`、`why investigators`、`why synthesizer`、`arena runners`、`arena cross-judge pool`、`swarm workers`、`architect runners`、`interrogate reviewers`。`recall`、`teach`、`blast-radius`、`figure-it-out` 没有角色行。

### 3.2 它们调用谁（出边）与调用方式

| 调用方 | 被调用 | 方式（原文） |
|---|---|---|
| how | explorer / explainer subagent | `subagent_type: generalPurpose`，`readonly: true`，提示取自 `references/explorer-prompt.md`、`references/explainer-prompt.md` |
| why | investigator / synthesizer subagent | `subagent_type: generalPurpose`，`readonly: false`；investigator 提示 = `investigator-prompt.md` + 一份 `sources/<source>.md` +（防御性代码时）`incident-postmortem.md` + 代码锚点 + 原问题 |
| recall | why 的 source investigators 与 per-source playbooks | "Hand it to the **why** skill's source investigators ... Reuse its per-source playbooks"；另派 subagent "on a fast, cheap model" 读聊天记录；输出经 unslop |
| teach | how、why、unslop | "Those are real skill invocations that do their own digging."；"Run them in parallel"；"Write every response through the **unslop** skill" |
| blast-radius | why 的 Step 2、arena、unslop | "Use `why` step 2 to pull the PR and commits."；"For a big or wide change, run it as an `arena`."；"Write it through `unslop`" |
| architect | how、why、arena、interrogate（可选） | Phase A "Run the **how** skill"，必要时"also run the **why** skill"；Phase B "Run the **arena** skill ... Pass `references/runner-prompt.md` as each runner's prompt"；Phase C "run the **interrogate** skill on the synthesized sketch"；Phase E 第 1、4 步再跑 how 与 arena |
| arena | runner subagent、judge subagent | "Spawn all N subagents in one message with `run_in_background: true`"；judge "readonly"，模型"Prefer a different model family from the parent's" |
| swarm | worker subagent | `subagent_type: generalPurpose`、`environment: "cloud"`、`run_in_background: true` |
| interrogate | reviewer subagent | Task 工具，`subagent_type: generalPurpose`、`readonly: true`，同一份已填模板发给所有 reviewer |
| figure-it-out | poteto-mode 的 Principles 段、architect、show-me-your-work | todolist 第一项读 poteto-mode Principles；Phase B "run the **architect** skill (it runs **arena**)"；Phase D "Log the run via the **show-me-your-work** skill" |

原则引用（全部按名字加"principle skill"，不给路径）：
- architect：exhaust-the-design-space（"This is the **exhaust-the-design-space** principle skill made concrete."）、foundational-thinking、outcome-oriented-execution、redesign-from-first-principles、fix-root-causes、subtract-before-you-add。
- architect/references/runner-prompt.md：separate-before-serializing-shared-state、encode-lessons-in-structure、boundary-discipline、make-operations-idempotent、laziness-protocol、minimize-reader-load。
- arena：separate-before-serializing-shared-state、redesign-from-first-principles、prove-it-works，另有一处"per the Laziness Protocol"（没有粗体、没有"principle skill"字样）。
- figure-it-out：prove-it-works、never-block-on-the-human、foundational-thinking、laziness-protocol、separate-before-serializing-shared-state、sequence-verifiable-units、encode-lessons-in-structure。
- how、why、recall、teach、blast-radius、swarm、interrogate：一个原则都没点名。

### 3.3 模型角色的指定方式

有三种写法，彼此不统一：
1. 只说"your configured <角色> model"加默认值，不提配置文件：how（"your configured how-explorer model (default `grok-4.7-xhigh-fast`)"）、why（"your configured why-investigators model"）、architect（"Use your configured architect runners"）。
2. 点名配置文件和角色行，再给默认值：arena（"Use `arena runners` from `~/.cursor/rules/pstack-models.mdc` when present"）、swarm（"`swarm workers` in `~/.cursor/rules/pstack-models.mdc`"）、interrogate（"`interrogate reviewers` list from `~/.cursor/rules/pstack-models.mdc`"）。
3. 不给角色，只描述档次：recall（"on a fast, cheap model"）。

推断：第 1 种能成立，是因为 `pstack-models.mdc` 带 `alwaysApply: true`（`skills/setup-pstack/SKILL.md`，`### 5. Write the rule`），这份规则在每个会话都已在上下文里，技能不必去读文件。角色名拼写也不一致：技能里写 `how-explorer`、`why-investigators`（连字符），setup-pstack 写 `how explorer:`、`why investigators:`（空格）。

interrogate 额外写了模型失效时的做法："pick the closest equivalent ... spawn with the valid slug, and open a separate PR to update the configured value or default table. Do not block the review on the slug issue."，以及 `inherit-parent` / `auto` 表示省略 `model`。

poteto-mode 对这些技能的 subagent 类型有一条总则："Routed workflow skills (`how`, `why`, `interrogate`, `reflect`, `swarm`) set their own `subagent_type` for diverse-model review. Respect what the skill prescribes, don't override to `poteto-agent`."（`skills/poteto-mode/SKILL.md`，`## Subagents`）。同一节的"Defaults for every `Task` call"说"agent mode (readonly strips MCP)"，而 how 与 interrogate 自己规定 `readonly: true`；按上一句"Respect what the skill prescribes"，技能的规定优先。

### 3.4 能力技能是否知道谁在调用它

- 大多数不知道。how、why、arena、swarm、interrogate、blast-radius、teach 的正文里没有出现 poteto-mode 或任何 playbook 的名字。
- 例外一：figure-it-out 知道自己属于 poteto-mode 体系，todolist 第一项就是读 poteto-mode 的 Principles 段，描述里也说"when no narrower playbook applies"。
- 例外二：recall 在第 1 步点名 `session-pickup` playbook 与 `automate-me` 技能，但只是为了把不属于自己的请求送走，不是在说谁调用它。
- 例外三（向下知道）：architect 的 `runner-prompt.md` 让 runner "Read the **architect** skill in full first. That's the workflow you're inside."；`rationale-template.md` 的 Synthesis decision 节写"Filled in by [arena](../../arena/SKILL.md)"。也就是 subagent 知道自己在哪个技能里，但技能不知道上面是哪个 playbook。
- 反方向的耦合存在：playbook 与技能会伸进别的技能内部的阶段编号，例如 `eval.md` 的"per the **arena** skill's Phase B"、blast-radius 的"Use `why` step 2"。

---

## 4. 边界判据

### 4.1 为什么这些多步流程写在技能里，没有拆成 playbook

原文没有一句话直接回答这个问题。下面是根据写法得出的判断，全部为**推断**，每条附依据：

1. **playbook 以"整件任务的类型"来选，技能以"任务中的一个动作"来选。** poteto-mode 的 playbook 列表按任务类型划分（Investigation、Bug fix、Feature、Refactoring 等，`## Playbooks`），而技能在 `## Non-negotiables` 里按"遇到某个情形"触发（"Code crossing a function boundary → the **architect** skill"）。architect 的五个阶段、arena 的六个阶段讲的都是"怎样完成一次设计比较"或"怎样做一次多候选比武"这个动作本身，与任务是 bug 还是 feature 无关。
2. **同一个技能被多个 playbook 和技能复用。** arena 被 architect、blast-radius、figure-it-out、`eval.md` 调用；how 被 7 个 playbook 调用。拆成 playbook 就没法在别的 playbook 的某一步里调用。
3. **技能要能被人直接打斜杠命令单独用。** README："the table below is for when you want one directly"。
4. **技能的内部步骤大部分是"怎么派 subagent、用什么提示、怎么合并"的机械做法，不是"先做什么任务再做什么任务"。** how 的 Step 2a/2b/3 全是 subagent 参数；interrogate 的 Step 3 到 5 是派发、合并、裁决。

所以 architect、arena、swarm、figure-it-out 各自的 `## Start` 待办清单加 Phase 列表，从形式上等于一个内嵌 playbook（它们与 poteto-mode "Open a todolist whose first items are the matched playbook's steps" 的做法同形），但内容是单一技术动作的操作规程。

`authoring-a-skill.md` 给了一条相关的写作规则："Delegate to other skills by path. Don't restate. A workflow you keep hitting but isn't captured → propose a new skill."（`skills/poteto-mode/playbooks/authoring-a-skill.md`）。它说的是"反复出现的工作流"会被提成新**技能**，而不是新 playbook，与上面的推断一致。

### 4.2 figure-it-out：一个处在 playbook 与技能之间的组件

- 它的描述第一句是"Design an auditable playbook when no narrower one fits"，正文第一句"When the task matches no playbook, design one."，产物是"the workflow itself: a sequence of phases"。
- 它被 poteto-mode 当作 playbook 的替补路由（`## Playbooks` 段），但文件放在 `skills/figure-it-out/`，不在 `skills/poteto-mode/playbooks/`，并且有自己的斜杠命令。
- 它自己的 Phase A 到 E 是"如何设计并运行一份 playbook"的元流程；Phase B 设计出的步骤要"Add its steps to the todolist as concrete items, after the Phase C entry and before Phase D"，即生成的 playbook 被插进元流程中间执行。
- 推断：它之所以是技能而不是 playbook，是因为它的内容是"写 playbook 的方法"，适用于任何任务类型；这正符合 4.1 第 1 条的判据。

### 4.3 为什么原则单独成技能，而不是写在调用方里

- poteto-mode 的原文："Read the leaf skill in full for any principle you apply. Each entry names when it applies."，以及"Cite only principles whose leaf SKILL.md you read this session."（`skills/poteto-mode/SKILL.md`，`## Principles` 与 `## Non-negotiables`）。每个原则技能有自己的"When it applies / When it doesn't"（例：`skills/principle-exhaust-the-design-space/SKILL.md`）。
- 本组的实际写法：调用方只写一句"per the **X** principle skill"，把原则的名字作为"这个决定的理由"挂在做法后面，原则的全文不复述。例：arena Phase A 第 4 步"Each candidate writes to its own location ... per the **separate-before-serializing-shared-state** principle skill."
- 推断：原则单独成技能，是因为同一条原则被很多调用方引用（separate-before-serializing-shared-state 在 arena、architect runner-prompt、figure-it-out、`feature.md` 都出现），写在调用方里就会重复；并且原则回答的是"为什么这样做、何时适用"，调用方的正文只管"做什么"。
- architect 的"Design it twice"与原则 exhaust-the-design-space 的关系给了一个清晰样本：原则说"build 2-3 competing prototypes"（`principle-exhaust-the-design-space/SKILL.md`，`**The rule.**`），architect 说"This is the **exhaust-the-design-space** principle skill made concrete."——技能是原则在某个动作上的具体执行。

### 4.4 哪些规则仍写在调用方正文里，没有抽成原则

| 规则 | 所在位置 | 与哪个原则或技能重叠 |
|---|---|---|
| 五级证据阶梯（You said so → ... → reproduced it in the running app） | `blast-radius/SKILL.md`，`### How sure are you` | 与 prove-it-works 同一主题，但没有引用它 |
| "Verify by inspecting the artifact, never a self-report." | `figure-it-out/SKILL.md`，`## Phase C` | 同上；`interrogate/references/rubric.md` `## Verification` 也有"does the code verify actual output artifacts, or does it trust self-reports" |
| 幂等、并发、根因与症状、边界验证、遗留双路径、"structure over instructions" | `interrogate/references/rubric.md`，`## Correctness`、`## Root Causes vs. Symptoms`、`## Structural Integrity` | 分别与 make-operations-idempotent、separate-before-serializing-shared-state、fix-root-causes、boundary-discipline、migrate-callers-then-delete-legacy-apis、encode-lessons-in-structure 重叠，全部以明文复述，没有点名原则 |
| 浅模块、信息泄漏、时序分解、透传方法 | `architect/references/design-red-flags.md` | pstack 没有对应原则技能；只有 minimize-reader-load 部分重叠 |
| 写作规则（无长破折号、句号优先、每句至多一两个逗号、禁用收尾套话） | `teach/SKILL.md` 最后一段 | 与 unslop 技能重叠，teach 同时写了"Write every response through the **unslop** skill" |
| 置信度与措辞规则 | `why/references/epistemics.md` | 没有对应原则；只在 why 家族内部用，recall 与 teach 通过"inherit its posture"与"Keep `why`'s confidence language intact"间接继承 |

推断：rubric 与 code-quality-review 选择明文复述而不是点名原则，是因为它们的全文会被粘进 reviewer 的提示（`reviewer-prompt.md` 的 `{RUBRIC_CONTENTS}`），而 reviewer 跑在别的模型上、未必能读到 pstack 的原则技能；architect 的 `runner-prompt.md` 采取折中写法，每条先写一句要点再点名原则。

### 4.5 什么内容进 references，什么留在正文

从本组的实际分布看（这是对写法的归纳，属于**推断**，但每类都有实例）：
- **进 references 的**：
  1. subagent 的完整提示模板（how 两份、why 两份、interrogate 一份、architect 一份）。开头统一是"Build ... prompt from this template. Fill in the placeholders."。
  2. 只在某一步才需要的长清单或判断框架（interrogate 的 `rubric.md`、`code-quality-review.md`、`lead-judgment.md`；why 的 `epistemics.md`；architect 的 `design-red-flags.md`）。
  3. 产物模板（architect 的 `rationale-template.md`）。
  4. 按外部环境变化的可替换例子（why 的 `sources/*.md`，每份写"adapt for ..."，由 `source-playbook.md` 索引）。
- **留在正文的**：步骤顺序、subagent 参数、分支条件、何时跳过、最终呈现规则、输出结构的章节名（即使细节在 reference 里，正文也列出章节名，例如 how 的 `## Output Format` 与 why 的 `## Output Format`）。
- 没有 references 的技能（recall、teach、blast-radius、arena、swarm、figure-it-out）都不派"需要长提示的专职 subagent"，或者它们的 subagent 提示由调用方给（architect 把 `runner-prompt.md` 交给 arena）。

### 4.6 什么内容成为脚本

本组 10 个目录没有任何脚本文件。命令以内联代码块写在正文或 reference 里：why Step 2 的 `git blame`、`git log`、`gh pr view`；`sources/code-archaeology.md` 的 `git log -S`、`rg`；`sources/databricks.md` 的 SQL；interrogate Step 1 的 `git diff main...HEAD`。本组只在两处要求运行时**产出**脚本：blast-radius 第 5 步"Write a script or test that runs the real code, run it, and paste what happened."，figure-it-out Phase E"Encode any recurring correction as a gate, a lint rule, a check, or a script"。推断：在 pstack 里，检索命令是"给 agent 抄用的例子"，留在文字里；"证明某件事"的脚本是每次任务的产物，不随技能分发。

---

## 5. 重复与例外

### 5.1 同一内容在多处重复

1. **置信度规则在 why 家族重复四次。** `epistemics.md` 全文；`synthesizer-prompt.md` `## Epistemics Framework` 再列 6 条"key rules"；`synthesizer-prompt.md` `## Quality Check Before Returning` 7 条与 `epistemics.md` `## Calibration Check Before Finalizing` 4 条大部分重合；`investigator-prompt.md` `## Epistemic Discipline` 又写一遍"Don't confuse mechanics with motivation"。why Step 4 同时把 `epistemics.md` 作为输入第 4 项交给 synthesizer，所以 synthesizer 会读到两遍。
2. **git/gh 命令重复。** why `## Step 2` 与 `sources/code-archaeology.md` `## How to search it` 都有 `git blame -L`、`git log --follow`、`gh pr view --json ...`，字段列表略有不同（后者多 `files`）。
3. **how 的输出结构重复三处。** `how/SKILL.md` `## Output Format`、`how/references/explainer-prompt.md` `## Output Format`、以及范围外的 `skills/poteto-mode/playbooks/investigation.md` 第 3 步"Produce the `how`-shaped output (Overview / Key Concepts / How It Works / Where Things Live / Gotchas)"。
4. **"每个候选独立输出位置"重复。** arena Phase A 第 4 步（"a git worktree where possible, otherwise `/tmp/arena-<slug>/candidate-<n>/`"）与 architect `runner-prompt.md` 第一段（"a git worktree when available, otherwise a per-runner subdirectory under the sketch dir"），兜底路径写法不同。
5. **掉队处理重复。** arena Phase B "proceed with N-1 and note the dropout"，swarm Phase B "If a worker drops out, proceed with N-1 and note it."
6. **"不要把代码当作意图的证据"重复。** `epistemics.md` Calibration 第 3 条、`synthesizer-prompt.md` 第 4 条与 Quality Check 第 6 条、`investigator-prompt.md` `## What You're Not Doing` 末条、`sources/code-archaeology.md` Common pitfalls 末条。
7. **"Treat Seer / 相关性 不等于 因果"类告诫**在 `sources/datadog.md`、`sources/databricks.md`、`sources/sentry.md` 各写一遍（"Instrumented != caused" 在前两者字面相同）。推断：这是有意的，每份来源指南要单独交给一个 investigator，必须自足。
8. **写作规则**在 teach 最后一段与 unslop 重叠（见 4.4）；recall、blast-radius、teach 都各自写"through the **unslop** skill"。

### 5.2 违反分层的地方

1. **playbook 伸进技能内部的阶段编号，技能伸进别的技能的步骤编号。** `eval.md` "per the **arena** skill's Phase B / Phase C"；blast-radius 第 1 步"Use `why` step 2"。改动被引用技能的步骤编号会打断调用方，而被引用方不知道有人依赖它（why 正文没有提到 blast-radius）。
2. **playbook 复述技能的输出格式。** `investigation.md` 第 3 步重写 how 的五节结构（见 5.1 第 3 条）。这与 `authoring-a-skill.md` 自己的规则"Delegate to other skills by path. Don't restate."相抵。
3. **技能直接复用另一技能的内部零件，不经过该技能。** recall 第 4 步使用 why 的"source investigators"与"per-source playbooks"，但不走 why 的 synthesizer，并改写了它们的问题（"steer their question from \"why was this built this way\" to \"what's the current state ...\""）。这等于把 why 的 references 当作公共库用。
4. **调用方改写被调用方的默认策略。** why 写"**Default to the full parallel investigation.**"，跳过某类来源只允许两种理由（`### When to skip an investigator`）；teach 第 2 步写"Keep `why` narrow by default since its full sweep is slow. Put the narrowing in the ask itself (a scoped question, git plus a source or two) so `why` records the skipped categories per its own contract"。teach 靠"把问题问窄"来绕开 why 的默认值，而 why 的两条合法跳过理由里并没有"调用方要求变窄"。推断：两者存在张力，按 why 原文执行时 teach 的收窄可能不成立。
5. **一个技能的正文里写了整套任务流程（等于内嵌 playbook）。** architect（A 到 E，含实现阶段 Phase D）、figure-it-out（A 到 E）。architect 的 Phase D"Implement against the sketch"已经是在做 feature 的实现，而 `feature.md` 自己也有实现步骤（第 4 步"Delegate code-writing to a subagent"）。推断：Feature playbook 走到第 2 步调用 architect 时，architect 的 Phase D 与 Feature 第 4 步都在描述"实现"，谁负责实现没有写清。
6. **原则的引用写法不统一。** 本组写"the **exhaust-the-design-space** principle skill"（不带 `principle-` 前缀），poteto-mode 与 playbook 写"**principle-model-the-domain**"（技能的真实 `name`，例：`skills/principle-exhaust-the-design-space/SKILL.md` frontmatter `name: principle-exhaust-the-design-space`）；arena Phase D 写"per the Laziness Protocol"，既不是技能名也没标为原则。
7. **提示模板与使用方式不符。** how Step 2b 要求简单路径"Build its prompt from `references/explainer-prompt.md` without the explorer-findings section"，但该模板第一段就写"Multiple explorer agents have traced different slices of the codebase in parallel ... Synthesize their findings"，去掉 findings 一节后开头这句仍然在，模板只为复杂路径写过。
8. **裁决词汇三套并存。** swarm `PASS` / `ISSUES` / `BLOCKED`；figure-it-out `VERIFIED` / `NOT VERIFIED` / `INCONCLUSIVE`；interrogate 发现级别 `critical` / `warning` / `nit` 与裁决四档 Act on / Consider / Noted / Dismissed。各自服务不同动作，但"不通过不算通过"的语义（swarm "A gap does not count as a pass."，figure-it-out "Inconclusive is not a pass."）写了两遍。
9. **"playbook"一词两义。** poteto-mode 的 playbook 指任务类型流程；why 的 `source-playbook.md` 与 `sources/*.md` 称按来源的检索指南为"playbook"（"The playbooks are concrete examples for common MCPs."），recall 也沿用"per-source playbooks"。
10. **与原则的潜在冲突。** interrogate Step 2："If you're unsure about the intent, ask the user before proceeding."；原则 never-block-on-the-human 在 poteto-mode 的摘要是"Tempted to ask \"should I do X?\" on reversible work. Proceed"。推断：interrogate 的提问是问"意图"不是问"要不要做"，两者未必冲突，但原文没有调和。

---

## 6. 状态与重入

- **待办清单作为进度状态。** architect、arena、swarm、figure-it-out 都在 `## Start` 要求"Open a todolist with one entry per phase"。figure-it-out 进一步要求把设计出的步骤插入待办清单中间（Phase B 末段）。poteto-mode 对 playbook 的对应规则是"A step you choose not to do stays in the list with a one-line `skip: <reason>`"（`## Playbooks`）；本组技能没有自己的跳步写法，推断是沿用 poteto-mode 的规则。
- **显式回退（阶段内重入）。** architect："If the human pushes back on the shape ... treat that as Phase A evidence. Re-ground and re-run Phase B"；Phase E 推倒后"Return to Phase B and re-run arena"。arena Phase F："either Phase A was wrong (re-frame and re-run) or one candidate caught it and you missed the graft (go back to Phase E)"；Phase E："When N candidates wildly diverge ... Reframe and re-run"。figure-it-out Phase C："keep it if it advanced, revert it if it didn't"。
- **失败重试上限。** swarm Phase C：缺 SHA 与方法的结果"rerun that worker once. After a second miss, record a gap."；arena 与 swarm 都允许 N-1 继续。
- **持久记录。** arena：synthesis note"alongside the base artifact"（Phase D、Phase E、`## Outputs`）；architect：rationale 文件"ships alongside"草图（`## Outputs`）；figure-it-out：经 show-me-your-work 的决策记录，"usually ambitious enough to commit the trail"（Phase D）。how、why、interrogate、swarm、teach、blast-radius 只产出对话内的回复，没有持久文件；blast-radius 写的验证脚本是唯一可能留下的文件。
- **中断后继续。** 本组没有一个技能写"被中断后如何恢复"。recall 本身是"开始或恢复工作前重建上下文"的工具，但它把"恢复某一个具体旧会话"明确交给 `session-pickup` playbook（第 1 步）；暂停的对应物是 poteto-mode 的 `pause-safely` playbook（`## Playbooks` 列表，未读全文）。推断：pstack 把"中断与恢复"放在 playbook 层统一处理，能力技能不自带恢复逻辑。
- **人工检查点。** architect Phase C 默认不停，只有调用者明说才停；figure-it-out Phase A："a multi-hour run earns one checkpoint"；interrogate Step 2 意图不清时问人；其余技能不停。

---

## 未确定

1. `disable-model-invocation: true` 在 Cursor 中的确切效果（是否阻止模型在未点名时自动加载、点名"the **how** skill"时 agent 以何种机制读取），pstack 原文没有解释，本报告按推断处理。
2. architect 调 arena 时，runner 模型用 `architect runners` 还是 `arena runners`：architect Phase B 写"Use your configured architect runners"，arena Phase A 第 3 步写"Use `arena runners`"，两者冲突时谁优先，原文未说明。
3. Feature playbook 调用 architect 之后，architect 的 Phase D（实现）与 Feature 第 4 步（委派实现）如何分工，原文未说明（只读了 `feature.md` 第 3 到 12 行）。
4. teach 要求"Keep `why` narrow"与 why 的跳过门槛如何调和，原文未说明。
5. recall 派"fast, cheap model"的 subagent 用哪个角色配置：setup-pstack 没有 recall 角色行。
6. `pause-safely.md`、`session-pickup.md` 与本组技能的状态交接，本轮没有读这两份 playbook。

---

```edges
poteto-mode -> how : routes-to
poteto-mode -> architect : routes-to
poteto-mode -> swarm : routes-to
poteto-mode -> arena : routes-to
poteto-mode -> interrogate : routes-to
poteto-mode -> figure-it-out : routes-to
playbook:investigation -> how : calls
playbook:investigation -> why : calls
playbook:feature -> how : calls
playbook:feature -> architect : calls
playbook:feature -> interrogate : calls
playbook:bug-fix -> how : calls
playbook:bug-fix -> why : calls
playbook:bug-fix -> architect : calls
playbook:perf-issue -> how : calls
playbook:perf-issue -> architect : calls
playbook:refactoring -> how : calls
playbook:refactoring -> architect : calls
playbook:refactoring -> figure-it-out : routes-to
playbook:hillclimb -> how : calls
playbook:prototype -> architect : hands-off-to
playbook:eval -> arena : calls-phase (伸入 arena 的 Phase B 与 Phase C)
playbook:multi-phase-plan -> swarm : calls
playbook:multi-phase-plan -> how : calls
playbook:multi-phase-plan -> interrogate : calls
playbook:opening-a-pr -> interrogate : calls
playbook:autopilot-full -> swarm : calls
no-comments -> how : calls
no-comments -> why : calls
no-comments -> architect : calls
agent:comment-sicko -> how : calls
agent:comment-sicko -> why : calls
how -> setup-pstack : configured-by
why -> setup-pstack : configured-by
arena -> setup-pstack : configured-by
swarm -> setup-pstack : configured-by
architect -> setup-pstack : configured-by
interrogate -> setup-pstack : configured-by
how -> how/references/explorer-prompt.md : reads-reference
how -> how/references/explainer-prompt.md : reads-reference
how -> subagent:how-explorer : spawns-subagent
how -> subagent:how-explainer : spawns-subagent
why -> why/references/epistemics.md : reads-reference
why -> why/references/investigator-prompt.md : reads-reference
why -> why/references/synthesizer-prompt.md : reads-reference
why -> why/references/source-playbook.md : reads-reference
why -> why/references/sources/*.md : reads-reference
why -> subagent:why-investigator : spawns-subagent
why -> subagent:why-synthesizer : spawns-subagent
why/references/source-playbook.md -> why/references/sources/*.md : indexes
why/references/synthesizer-prompt.md -> why/references/epistemics.md : reads-reference
why/references/investigator-prompt.md -> why/references/sources/*.md : appends (模板末尾追加一份来源指南)
recall -> why : reuses-internals (借用 why 的 source investigators 与 per-source playbooks，不走 synthesizer)
recall -> subagent:chat-history-miner : spawns-subagent
recall -> unslop : calls
recall -> playbook:session-pickup : routes-to (把不属于自己的请求送走)
recall -> automate-me : routes-to (同上)
teach -> how : calls
teach -> why : calls
teach -> unslop : calls
blast-radius -> why : calls-step (伸入 why 的 Step 2)
blast-radius -> arena : calls
blast-radius -> unslop : calls
architect -> how : calls
architect -> why : calls
architect -> arena : calls
architect -> interrogate : calls (可选，Phase C)
architect -> architect/references/runner-prompt.md : reads-reference
architect -> architect/references/rationale-template.md : reads-reference
architect -> architect/references/design-red-flags.md : reads-reference
architect -> principle-exhaust-the-design-space : cites-principle
architect -> principle-foundational-thinking : cites-principle
architect -> principle-outcome-oriented-execution : cites-principle
architect -> principle-redesign-from-first-principles : cites-principle
architect -> principle-fix-root-causes : cites-principle
architect -> principle-subtract-before-you-add : cites-principle
architect/references/runner-prompt.md -> architect : reads-reference (runner 先读 architect 全文)
architect/references/runner-prompt.md -> principle-separate-before-serializing-shared-state : cites-principle
architect/references/runner-prompt.md -> principle-encode-lessons-in-structure : cites-principle
architect/references/runner-prompt.md -> principle-boundary-discipline : cites-principle
architect/references/runner-prompt.md -> principle-make-operations-idempotent : cites-principle
architect/references/runner-prompt.md -> principle-laziness-protocol : cites-principle
architect/references/runner-prompt.md -> principle-minimize-reader-load : cites-principle
architect/references/rationale-template.md -> arena : filled-by (Synthesis decision 节由 arena 填写)
arena -> subagent:arena-runner : spawns-subagent
arena -> subagent:arena-cross-judge : spawns-subagent
arena -> principle-separate-before-serializing-shared-state : cites-principle
arena -> principle-redesign-from-first-principles : cites-principle
arena -> principle-prove-it-works : cites-principle
arena -> principle-laziness-protocol : cites-principle (原文写 "the Laziness Protocol"，未加粗未标原则)
swarm -> subagent:swarm-worker : spawns-subagent
interrogate -> interrogate/references/reviewer-prompt.md : reads-reference
interrogate -> interrogate/references/rubric.md : reads-reference
interrogate -> interrogate/references/code-quality-review.md : reads-reference
interrogate -> interrogate/references/lead-judgment.md : reads-reference
interrogate -> subagent:interrogate-reviewer : spawns-subagent
interrogate/references/reviewer-prompt.md -> interrogate/references/rubric.md : embeds (全文粘入 {RUBRIC_CONTENTS})
interrogate/references/reviewer-prompt.md -> interrogate/references/code-quality-review.md : embeds (全文粘入 {CODE_QUALITY_CONTENTS})
figure-it-out -> poteto-mode : reads-reference (todolist 第一项读其 Principles 段)
figure-it-out -> architect : calls
figure-it-out -> show-me-your-work : calls
figure-it-out -> principle-prove-it-works : cites-principle
figure-it-out -> principle-never-block-on-the-human : cites-principle
figure-it-out -> principle-foundational-thinking : cites-principle
figure-it-out -> principle-laziness-protocol : cites-principle
figure-it-out -> principle-separate-before-serializing-shared-state : cites-principle
figure-it-out -> principle-sequence-verifiable-units : cites-principle
figure-it-out -> principle-encode-lessons-in-structure : cites-principle
```

自拟关系说明：`calls-phase` / `calls-step` 表示调用方点名被调用技能内部的某个阶段或步骤编号；`reuses-internals` 表示绕过技能本体、直接使用它的 references 与 subagent 角色；`indexes` 表示索引文件指向被索引文件；`appends` 表示模板要求在末尾追加另一份文件；`embeds` 表示一份文件的全文被粘进另一份模板的占位符；`filled-by` 表示模板中某节由另一个技能的产出填写；`configured-by` 的方向是"被配置的技能 -> 写配置的技能"。

# Findings and placement plan for #1165

Source: the owner's words under the ticket's `## Problem`. Line numbers are on `origin/dev` at 6c33cab84.

## Findings

1. A candidate is sent with two different working files from two skills: `--follow "the brief"` and `--follow "the architect skill's references/runner-prompt.md"`, both on `mmw-v4/skills/arena/SKILL.md:23`. Every other brief role's `--follow` names one skill: researcher is sent from `how/SKILL.md:21`, `why/SKILL.md:44` and `mmw-mode/playbooks/investigation.md:7`, all into the research skill; advisor, reviewer and retro-analyst have one sender each.
2. A UI candidate never receives the per-variant rules: they are written to the main agent in `mmw-v4/skills/prototype/UI.md:56` to `:68` (`### 2. Generate radically different variants`), and its start prompt follows only `the brief`.
3. The code-shape branch is the only prototype branch that is not a prototype file: `mmw-v4/skills/prototype/SKILL.md:19` sends it to the architect skill. On 2026-10-19 a Codex session in agentflow ran `cat ~/.agents/skills/prototype/SKILL.md; cat ~/.agents/skills/prototype/SKETCH.md` and got `No such file or directory` (`~/.codex/sessions/2026/10/19/rollout-2026-10-19T13-39-12-01a152ab-c9a9-7323-bf1d-4733a597c5a4.jsonl`).
4. Three gates decide when a sketch is drawn: `prototype/SKILL.md:19` (reaches beyond one ticket), `architect/SKILL.md:22` (a shape later work builds on), and `mmw-mode/references/owning-a-task.md:13` (any code crossing a function boundary). The third sends nearly every change to architect and contradicts the first.
5. The callee carries its callers' special cases: `arena/SKILL.md:8` (the UI branch), `:19` (the prototype leaf `SKETCH/`), `:23` (the architect skill's runner prompt).
6. `blast-radius/SKILL.md:37` runs an arena to ask more than one model; arena runs every candidate on one model, and `writing-for-agents/DESIGN-INTENTS.md:127` (Departures, P19) records cross-model review as not taken.
7. `runner` names the program that starts sessions (`dispatch/scripts/models.py runner`), and also the candidate in `architect/references/runner-prompt.md:1` and `:20` and `architect/references/rationale-template.md:27` (SKILL-SET-RULES.md `### Vocabulary`).
8. The brief footer defines `## Known` as "what the session that sent you already has, so start from it and do not redo it" (`dispatch/scripts/dispatch.sh:1530`), so the files that shape a candidate's artifact belong in `## Task`.
9. Sentences duplicated across the files each reader loads are listed per file under **Sentence by sentence** below, each with the file and heading that keeps the meaning.

Second opinion: `advisor.md` beside this file (advisor brief 20261019-063512-190e). Its four corrections are applied below; its one question for the owner was answered on 2026-10-19: a shape inside one ticket gets no sketch.

## Readers, entries and exits per file

| File | Kind | Readers | When | Entry | Exit | Writes |
|---|---|---|---|---|---|---|
| `prototype/SKILL.md` | 改 | 主 agent | 每次进 prototype，整份读 | feature.md 第 4 步、bug-fix.md 6. Plan the fix、perf-issue.md 4. Plan the change、refactoring.md 4. Name the target shape、grill-with-docs.md 2. Route each fork…、wayfinder.md Ticket Types: Prototype、owning-a-task.md 的 Prototype 路由行、principle-redesign-from-first-principles 第 4 步、codebase-design Going deeper、no-comments 第 3 步 | ## Pick a branch 选一份：LOGIC.md / UI.md / EXP.md / SKETCH.md | — |
| `prototype/SKETCH.md` | 新（architect/SKILL.md 搬入） | 主 agent | prototype/SKILL.md 选中 What shape should this code take? 时 | prototype/SKILL.md ## Pick a branch | arena（每次都进）；最后把草图和 README.md 交回调用方 | 主 agent 写 leaf 目录 SKETCH/ 和其中的 README.md |
| `arena/SKILL.md` | 改 | 主 agent | SKETCH.md 或 UI.md 点名时；或你直接点名 arena | prototype/SKETCH.md；prototype/UI.md ### 2.；你点名 | 唯一一处派 candidate → 被 brief <batch> done 唤醒 → Phase C 到 F → 交回调用方 | 主 agent 写 brief 和综合说明 |
| `arena/references/candidate.md` | 新 | candidate（每一个） | 启动句：then follow the arena skill's references/candidate.md | arena ## Phase B 的唯一发送行 | 答案文件 → dispatch.sh report | candidate 写自己的输出目录和答案文件 |
| `prototype/references/sketch-candidate.md` | 搬入并改名（原 architect/references/runner-prompt.md） | candidate（由 arena 为草图派出） | brief 的 ## Task 点名，开工前读 | SKETCH.md 写进 brief ## Task | — | — |
| `prototype/references/rationale-template.md` | 搬入（原 architect/references/） | 主 agent + candidate（由 arena 为草图派出） | 主 agent 写最终 README.md 时；candidate 写答案时 | SKETCH.md ## Outputs；sketch-candidate.md | — | — |
| `prototype/references/design-red-flags.md` | 搬入（原 architect/references/） | 主 agent + candidate（由 arena 为草图派出） | 主 agent 综合前筛查；candidate 交答案前自查 | SKETCH.md ## Phase B；sketch-candidate.md | — | — |
| `prototype/UI.md` | 改 | 主 agent | prototype/SKILL.md 选中 What should this look like? 时 | prototype/SKILL.md；feature.md 第 4 步；one-ticket.md 3. Each wake 的 contract 子票 | arena（方向未定时）；design freeze 后交回 winner 路径和 feature file | 主 agent 写 brief、winner/、feature file |
| `prototype/references/ui-variant.md` | 新 | 主 agent + candidate（由 arena 为界面派出） | 主 agent：UI.md 第 2 步，每次；candidate：brief 的 ## Task 点名 | UI.md ### 2.；brief ## Task | — | — |
| `blast-radius/SKILL.md` | 改 | 主 agent | 你点名时 | 你点名 | — | — |
| `mmw-mode/references/owning-a-task.md` | 改 | 主 agent | 负责任务的会话开局整份读 | mmw-mode | — | — |
| `mmw-mode/playbooks/*.md` | 改 | 主 agent | 走到那一步时 | — | prototype/SKILL.md | — |
| `其余点名 architect 的技能文本` | 改 | — | — | — | — | — |
| `维护记录与给你看的文档` | 改 | 你 / 维护者 | — | — | — | — |

## Words each reader loads (estimates, English words)

| Reader | Before | Words | After | Words | Note |
|---|---|---|---|---|---|
| 主 agent，代码结构，从 feature / bug-fix 等直接进 | architect 673 + arena 684 + red-flags 458 + template 470 + codebase-design 916 | 3201 | prototype/SKILL.md 900 + SKETCH.md 530 + arena 640 + 458 + 470 + 916 | 3914 | 多出 prototype/SKILL.md；但只在结构会被后续依赖时才进 |
| 主 agent，代码结构，从 prototype 进 | prototype/SKILL.md 1014 + 上一行 3201 | 4215 | 同上 | 3914 |  |
| candidate（为草图派出），每个 | mmw-mode 2161 + runner-prompt 472 + template 470 + red-flags 458 + codebase-design 916 | 4477 | mmw-mode 2161 + candidate.md 150 + sketch-candidate 250 + 470 + 458 + 916 | 4405 | 一次派 3 到 4 个 |
| 主 agent，界面 | prototype/SKILL.md 1014 + UI.md 2215 + arena 684 | 3913 | prototype/SKILL.md 900 + UI.md 1880 + ui-variant 270 + arena 640 | 3690 |  |
| candidate（为界面派出），每个 | mmw-mode 2161，界面规则一条也拿不到 | 2161 | mmw-mode 2161 + candidate.md 150 + ui-variant 270 | 2581 | 多出来的就是原来传不到的规则 |

## Sentence by sentence

### `prototype/SKILL.md` (改)

- **改写**: `→ the **architect** skill, which writes its sketch and rationale into the leaf directory `SKETCH/`; the rationale is the leaf `README.md`.`
  - to: → [SKETCH.md](SKETCH.md).　放在哪的半句移到 SKETCH.md ## Outputs
  - why: 四支对等。2026-10-19 agentflow 的一个 Codex 会话执行 cat …/prototype/SKETCH.md，得到 No such file or directory
- **合并**: `Run it only when both hold: no prototype, ADR, or earlier spec has already settled this shape, and the shape reaches beyond one ticket.`
  - to: 保留 the shape reaches beyond one ticket，后面补它的判定：an interface that code outside this change calls, a data shape that is stored or passes between subsystems, or a change spanning more than one subsystem
  - why: 两道门槛说的是同一件事，只留这一处；措辞保住 DESIGN-INTENTS.md 第 25 条 a code shape that reaches beyond one ticket
- **删除**: `A UI prototype follows `UI.md` for its API fake and state, and records its conclusion in the feature file's account of what the product can do, not a leaf `README.md`.`
  - why: Duplication：UI.md ### 6. Capture the answer at design freeze 末段已有
- **删除**: `A UI prototype that needs its own route obeys whatever routing convention the project already uses; don't invent a new top-level structure.`
  - why: Duplication：UI.md ### Sub-shape B 已有
- **删除**: `A UI prototype starts with the product's own launch command plus one environment variable, including Electron.`
  - why: Duplication：UI.md ### 3. Wire them together 已有同一句
- **移动**: `A sketch type-checks with one command.`
  - to: SKETCH.md 开头段
  - why: 只有结构分支用到
- **删除**: `A sketch touches no data at all.`
  - why: No-op：草图函数体都是 not implemented，本来就碰不到数据
- **删除**: `A sketch has no implementation: its bodies are `not implemented`.`
  - why: Duplication：SKETCH.md 开头 with `not implemented` bodies
- **删除**: `; every experiment run writes its evidence page`
  - why: Duplication：EXP.md ### 4. Run it, write the evidence page, record what you see
- **删除**: `A sketch has no state to show.`
  - why: No-op
- **删除**: `For UI, follow `UI.md`'s design freeze and put the conclusion in the feature file's account of what the product can do. Keep the winner as the ticket's baseline, with its exact path under **Read first**.`
  - why: Duplication：UI.md ### 6. 和 feature.md 第 5 步已有

### `prototype/SKETCH.md` (新（architect/SKILL.md 搬入）)

- **删除**: `name: architect / description: Run only when the user, mmw-mode or another skill names it…`
  - why: 不再是独立技能
- **改写**: `# Architect`
  - to: # Sketch Prototype
  - why: 照 UI.md 的 # UI Prototype、LOGIC.md 的 # Logic Prototype
- **移动**: `Several candidates are for a shape later work builds on: an interface that code outside this change calls, a data shape that is stored or passes between subsystems, or a change spanning more than one subsystem.`
  - to: prototype/SKILL.md 门槛
  - why: 进分支的条件只写在入口
- **删除**: `Any other change, such as passing one more value along calls the change edits itself, takes the Phase A sketch as its design, finished as `## Outputs` says and screened against `references/design-red-flags.md`, with no arena.`
  - why: 行为变更，owner 2026-10-19 同意：一张票内部的形状不再画草图，由 worker 按票里点名的数据形状自己定，reviewer 把关。ticket 和 commit message 写明这一决定
- **改写**: `Otherwise, run the **arena** skill with the design-sketch task, …`
  - to: 去掉 Otherwise,
  - why: 进到这里就一定开 arena
- **改写**: `Each candidate reads `references/runner-prompt.md` itself, since arena's send has it follow that file, and produces a design package shaped per `references/rationale-template.md`.`
  - to: Its ## Task names references/sketch-candidate.md, references/rationale-template.md, references/design-red-flags.md and the codebase-design skill as the shape of the artifact.
  - why: 发送只在 arena 一处；这里只说 candidate 照哪些文件交付
- **合并**: `The synthesized sketch goes where the caller says; under the **prototype** skill that is the leaf `SKETCH/` directory, with the rationale as its `README.md`.`
  - to: 并入 ## Outputs
- **删除**: `Design it twice. Require at least two structurally distinct candidates before synthesis, even when the first looks sufficient. This is the **exhaust-the-design-space** principle skill made concrete. Whole-shape alternatives, not point fixes inside one shape.`
  - to: 原则名挂到 Run three 那句
  - why: No-op：下一段固定跑三到四个角度，至少两个永远成立。whole-shape 一句重复 arena ## Phase A: Frame 第 3 条
- **删除**: `The caller's usage is written first and the type sketch derived from it.`
  - why: Duplication：rationale-template.md ## Usage (caller's view)
- **改写**: `The rationale ships alongside, shaped per `references/rationale-template.md`, including the usage sketch and the synthesis decision.`
  - to: The sketch and its rationale go in the leaf directory SKETCH/, the rationale as its README.md, shaped per references/rationale-template.md.
  - why: including… 重复模板的章节名

### `arena/SKILL.md` (改)

- **删除**: `When the **prototype** skill's UI branch calls this skill, follow its `UI.md` for scoring, selection, and what to keep, including the exception to "Then remove `candidates/`" under `## Outputs`.`
  - to: 换成下面三处通用说法：rubric 由调用方给、谁挑底版由调用方定、candidates/ 留不留由调用方定
  - why: 被调用方不再记住某个调用方
- **删除**: `(under the **prototype** skill, the leaf `SKETCH/`)`
  - why: 放哪由调用方说
- **移动**: ``## Task` the task and this candidate's angle, with the artifact and a short rationale to produce, the rationale naming the alternatives it considered and what it rejected; the artifact stays in its output directory, and the one file it reports is the `README.md` there, which carries the rationale;`
  - to: arena/references/candidate.md；这里留 ## Task the task and this candidate's angle
  - why: 这是 candidate 干活的规矩，每次派都一样，不必每份 brief 重写
- **改写**: ``## Task` the task and this candidate's angle, …`
  - to: ## Task the task, this candidate's angle, and the artifact shaped per the files the caller names; ## Known the path to the shared grounding and its output directory
  - why: dispatch.sh 的 brief 末尾把 ## Known 说成发送方已有、不必重做的东西，candidate 会略读那里的文件；交付形状属于要做什么
- **改写**: `Send them all with one `dispatch.sh send candidate --follow "the brief" <brief>...` of the **dispatch** skill, or, when the **architect** skill sent you here, with `dispatch.sh send candidate --follow "the architect skill's references/runner-prompt.md" <brief>...``
  - to: Send them all with one dispatch.sh send candidate --follow "the arena skill's references/candidate.md" <brief>... of the dispatch skill
  - why: 全套技能只有这一行派 candidate，启动句永远相同
- **删除**: `and end your turn. Woken by `brief <batch> done`, follow the dispatch skill's `## On waking`.`
  - why: Duplication：owning-a-task.md ## Subagents 已写
- **改写**: `## Phase D: Pick 的 Pick the base a future maintainer can extend most easily…`
  - to: 前面加：When the caller hands the pick to the owner, show the owner every candidate and take the owner's pick and combination as the base.
  - why: 界面分支由你挑，原来靠第 8 行特例
- **改写**: `## Outputs 的 Then remove `candidates/`: what was taken and what was rejected lives in the note.`
  - to: …Then remove candidates/, unless the caller keeps them as reference.
  - why: 界面分支要保留落选版
- **新增**: `## Phase A: Frame 第 2 条 Candidates only see the task. ／ ## Phase B The rubric stays out of every brief.`
  - to: 补一句：The rubric that ranks candidates stays out of the brief; a Done criterion every candidate must meet is part of the task.
  - why: 界面分支的评分就是 ui-variant.md 的 Done，candidate 必须读到，否则两条规则字面上打架

### `arena/references/candidate.md` (新)

- **新增**: `（开头，新写）`
  - to: You produce one of N candidates at the same task, from the angle your brief's ## Task gives. Read every file your brief names before you start, and write only in your output directory.
  - why: 所有 candidate 共同的规矩只写这一处
- **原文搬入**: `arena ## Phase B 的 with the artifact and a short rationale to produce, … the one file it reports is the README.md there, which carries the rationale`
- **原文搬入**: `sketch-candidate.md 末段 You are one of the parallel runners, each on a different constraint. Produce the best design your constraint allows. Don't hedge against the others. …`
  - to: runners 改为 candidates，constraint 改为 angle
  - why: 这是所有 candidate 的立场，不只是草图

### `prototype/references/sketch-candidate.md` (搬入并改名（原 architect/references/runner-prompt.md）)

- **改名**: `文件名 runner-prompt.md`
  - to: sketch-candidate.md
  - why: Vocabulary：MMW 里 runner 指启动会话的程序（models.py runner），一词两义
- **改写**: `You are producing one candidate design in architect's parallel exploration.`
  - to: …in the prototype skill's sketch branch.
- **改写**: `The package covers the interface (types, methods, params, plus invariants, ordering, error modes), how callers use it, what the implementation hides behind the seam, the dependency strategy and adapters, and the trade-offs: where leverage is high, where it's thin.`
  - to: 只留模板没有的：invariants, ordering and error modes, and the dependency strategy and adapters
  - why: 其余重复 rationale-template.md 的 ## Usage、## Shape、## Tradeoffs accepted
- **删除**: `The orchestrator compares candidates on these axes to pick a base.`
  - why: 不是事实：主 agent 按 SKETCH.md 给的 rubric 打分；也等于向 candidate 透露评分（arena ## Phase A 第 2 条 Candidates only see the task）
- **删除**: `- Caller's usage first. Write the README-style usage and two or three real call sites before the types, … reconcile the sketch to the usage, not the reverse.`
  - why: Duplication：rationale-template.md ## Usage (caller's view)
- **删除**: `Do not put transport or wire types on the public API. Parse into domain types behind the interface.`
  - why: Duplication：design-red-flags.md ## Information leakage
- **删除**: `- Shared state: if two actors might both write, ask "what happens?" …`
  - why: Duplication：design-red-flags.md ## Split ownership
- **删除**: `- Single source of truth per invariant. Derive instead of sync.`
  - why: Duplication：design-red-flags.md ## Hand-synced list
- **移动**: `You are one of the parallel runners, each on a different constraint. Produce the best design your constraint allows. Don't hedge against the others. …`
  - to: arena/references/candidate.md
  - why: 所有 candidate 共用

### `prototype/references/rationale-template.md` (搬入（原 architect/references/）)

- **改写**: `[Phase A](../SKILL.md#phase-a-ground-the-problem)`
  - to: ../SKETCH.md#phase-a-ground-the-problem
  - why: 文件搬家后链接跟着改
- **改写**: `## Alternatives considered 末句 … not other runner candidates.`
  - to: …not other candidates.
  - why: Vocabulary：runner 在 MMW 指启动会话的程序；pstack 原文，一词之改写进 commit message

### `prototype/references/design-red-flags.md` (搬入（原 architect/references/）)

No sentence changes.

### `prototype/UI.md` (改)

- **新增**: `（### 2. Generate radically different variants 开头新增一句）`
  - to: Write every variant, yours or a candidate's, as references/ui-variant.md says.
  - why: 主 agent 自己画几版、第 5 步一对一迭代时也要守这些规则
- **移动**: `Use the product's existing components and production-style frontend code. Each variant follows the page's purpose, available data, and styling system, with a clear exported component name. Variants differ in layout, information hierarchy, or primary action, rather than just colour or copy.`
  - to: ui-variant.md
  - why: candidate 也要读
- **改写**: `For competing directions, use the **arena** skill and the **dispatch** skill's `dispatch.sh send candidate`. Each candidate writes one direction into `candidates/<n>/` within this checkout's leaf directory.`
  - to: For competing directions, run the arena skill: each candidate writes one variant into candidates/<n>/ within this checkout's leaf directory; its ## Task names references/ui-variant.md; the rubric is that file's Done criterion; the owner chooses the base, not the score, and you fuse the selected parts into winner/; keep candidates/<n>/.
  - why: 界面也只经 arena 派 candidate；原来写在 arena 第 8 行的界面特例，改由调用方在这里交代
- **删除**: `The arena scoring only filters candidates by these three criteria: it runs, every state is reachable, and buttons have interfaces. Use no other scoring criteria, and keep the criteria out of the candidate briefs.`
  - why: 并入上一句：rubric 就是 ui-variant.md 的 Done；这三条 candidate 必须知道，藏起来没有道理
- **移动**: `Use an **API fake** only for interfaces that do not exist yet. …（整段）`
  - to: ui-variant.md
  - why: candidate 也要读
- **移动**: `When the product has accounts, use the real login flow and test accounts … （整段）`
  - to: ui-variant.md
  - why: candidate 也要读
- **移动**: `Give every actionable element a role and an accessible name, so e2e can find it by those names.`
  - to: ui-variant.md
  - why: candidate 也要读
- **移动**: `Done when the variants run, expose every state, and connect each button to a real interface or the API fake.`
  - to: ui-variant.md 作为每一版的 Done；这里改为 Done when every variant meets references/ui-variant.md's Done criterion.
- **删除**: `- **Variants that differ only in colour or copy.** That's a tweak, not a prototype. Real variants disagree about structure.`
  - why: Duplication：第 2 步第一段 rather than just colour or copy
- **移动**: `- **Sharing too much code between variants.** …`
  - to: ui-variant.md
  - why: candidate 也要读
- **删除**: `- **Replacing existing interfaces with stubs.** …`
  - why: Duplication：API fake 段

### `prototype/references/ui-variant.md` (新)

- **新增**: `（开头一句，新写）`
  - to: How one variant of a UI prototype is written, by the session running UI.md or by a candidate arena sends.
- **原文搬入**: `UI.md ### 2. 的四段、Anti-patterns 的 Sharing too much code、第 2 步的 Done`
  - to: 逐字不改

### `blast-radius/SKILL.md` (改)

- **删除**: `6. For a big or wide change, run it as an `arena`. Ask more than one model the same question and merge the answers. Different models catch different real bugs.`
  - to: upstream-keep.tsv 记一行理由
  - why: DESIGN-INTENTS.md ## Departures 的 P19 行：cross-model adversarial review 不采用；arena 只用一个模型，而且是设计擂台

### `mmw-mode/references/owning-a-task.md` (改)

- **删除**: `- Code crossing a function boundary → the **architect** skill, parallel design exploration before implementing. Prototype code under the **prototype** skill's logic, UI and experiment branches is the exception: speed over polish, no planning.`
  - why: 几乎所有改动都跨函数边界，和 prototype/SKILL.md 门槛（超出一张票才画草图）冲突；代码结构问题由各流程那一步送进 prototype

### `mmw-mode/playbooks/*.md` (改)

- **改写**: `feature.md 第 4 步：Run `architect` for the code shape, which decides how many candidates it needs. Its sketch goes in `efforts/<effort>/prototypes/<n>/SKETCH/`, named as the **prototype** skill's rule 1 names them, committed on `fix-<n>`.`
  - to: For the code shape, run the prototype skill, whose Pick a branch decides whether a sketch is drawn; commit what it writes on fix-<n>.
  - why: 放哪一句重复 prototype/SKILL.md 规则 1
- **改写**: `feature.md 第 5 步：When `architect` produced a sketch`
  - to: When the prototype skill's sketch branch produced a sketch
- **改写**: `bug-fix.md 6. Plan the fix：If it crosses a function boundary, the **architect** skill first.`
  - to: A question of code shape goes to the prototype skill's Pick a branch first.
  - why: 门槛只写在 prototype/SKILL.md 一处
- **改写**: `bug-fix.md 7. Write the ticket：an `architect` sketch is a baseline`
  - to: a sketch from the prototype skill is a baseline
- **改写**: `perf-issue.md 4. Plan the change：If it crosses a function boundary, `architect` first.`
  - to: 同 bug-fix.md 第 6 步
- **改写**: `refactoring.md 4. Name the target shape：If the target crosses a function boundary, run the **architect** skill for parallel design exploration of the shape before the move, and commit its sketch on `fix-<n>`.`
  - to: Run the prototype skill on the target shape before the move; its Pick a branch decides whether a sketch is drawn, committed on fix-<n>.
- **改写**: `refactoring.md 5. Write the ticket：the `architect` sketch when there is one`
  - to: the sketch when there is one
- **改写**: `investigation.md：No PR, no `architect` unless the investigation precedes a code change.`
  - to: No PR and no sketch. When the investigation precedes a code change, hand back…

### `其余点名 architect 的技能文本` (改)

- **改写**: `mmw-mode/SKILL.md ## Principles：code written against an architect sketch`
  - to: code written against a sketch
- **改写**: `principle-redesign-from-first-principles：When the code written against an **architect** sketch … ／ 4. Re-run the **architect** skill.`
  - to: a sketch from the prototype skill ／ Re-run the prototype skill's sketch branch.
- **改写**: `codebase-design ## Going deeper：see the **architect** skill`
  - to: see the prototype skill's sketch branch
  - why: 这一行是 MMW 加的，不是上游原文
- **改写**: `no-comments 第 3 步：run `/architect` once for the accepted set and surrounding code. Stop at the sketch. Architect shapes.`
  - to: run the prototype skill's sketch branch once … The sketch shapes.
  - why: 上游 pstack 原文；架构技能已不存在，不改会让 agent 找不到技能
- **改写**: `mmw-help/SKILL.md 第 38、57、95、102 行；references/recipes.md 第 25 行`
  - to: architect 行删去，prototype 行写上代码结构

### `维护记录与给你看的文档` (改)

- **改写**: `writing-for-agents/DESIGN-INTENTS.md 第 25 条 Home：the `architect` and `arena` skills`
  - to: the prototype skill's SKETCH.md; the arena skill
- **改写**: `writing-for-agents/UPSTREAM.md 第 92 行（P19 行）两次写 `architect``
  - to: 改为 prototype 的 SKETCH.md
- **改写**: `writing-for-agents/scripts/upstream-map.tsv 的 architect 四行`
  - to: 改指向 prototype/SKETCH.md 和 prototype/references/
- **移动**: `architect/ 目录`
  - to: docs/retired-skills/architect/
  - why: AGENTS.md：不再用的技能移走，不删
- **改写**: `README.md、docs/guide/04-design.md、05、10、README.md、02`
  - to: architect 的说明改成 prototype 的 sketch branch
  - why: 只给你看，不进 agent 上下文

## Seen, not changed by this ticket

- candidate（由 UI.md 派出）怎样在页面上跑出自己那一版：UI.md ### 3. Wire them together 才接挂载点，而派 candidate 在第 2 步。没有找到出错的运行记录，按 SKILL-SET-RULES.md ## Editing 不加规则。
- principle-redesign-from-first-principles 的 When code keeps fighting its sketch 让读者重画草图；夜里按草图写代码的 worker，feature.md 第 5 步要它开 contract 子票。同一情况两种指示，没有出错记录。
- candidate 一词还被 eval.md、retro、mmw-mode/references/bugbot-triage.md、improve-the-architecture.md 用在别的意思上（SKILL-SET-RULES.md ### Vocabulary）。

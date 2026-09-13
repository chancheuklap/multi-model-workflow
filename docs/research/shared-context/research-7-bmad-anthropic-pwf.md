# 调研 7：BMAD-METHOD v6、Anthropic 工程文章、planning-with-files 三者对 MMW 的可借鉴机制（2026-09-13）

## 0. 范围、方法、可信度

- **BMAD-METHOD**：浅克隆到 scratchpad 下的 `mktemp -d` 目录，HEAD `94b6727b00c8316557828c8a8ff2a48ff60d60cc`（2026-09-11），与 research-3 第 9 节同一提交。未运行任何脚本。
  链接前缀 `B=https://github.com/bmad-code-org/BMAD-METHOD/blob/94b6727b00c8316557828c8a8ff2a48ff60d60cc/`
  全文读过：`skills/bmad-build/{SKILL.md, workflow.md, step-01-clarify-and-route.md, step-02-plan.md, step-03-implement.md, step-04-review.md, step-05-present.md, spec-template.md, sync-sprint-status.md, compile-epic-context.md, customize.toml, references/claims-check.md, references/deletion-check.md}`；`skills/bmad-build-auto/workflow.md`（全文）、`step-04-review.md` 第 84–118 行与 grep 结果、`spec-template.md` 前 30 行、`customize.toml` 第 108–140 行；`skills/bmad-correct-course/{SKILL.md, customize.toml}` 全文、`checklist.md` 前 150 行；`skills/bmad-retrospective/{SKILL.md, workflow.md, references/*.md}` 全文，`scripts/sprint_status.py` 只 grep 了函数名与 `action_items` 相关行；`skills/bmad-project-context/{SKILL.md, references/best-practices.md, references/template.md}` 全文；`skills/bmad/scripts/memlog.py` 前 80 行（文档串）；`skills/bmad-sprint-planning/SKILL.md` 前 20 行、`scripts/sprint_plan.py` grep；`skills/bmad-build/review-prompts/verification-gap.md` 前 60 行；`skills/bmad/scripts/resolve_customization.py` 前 40 行。
- **planning-with-files（PWF）**：HEAD `1ec8f4eb5c683e31644856d98f9abde0d5a53448`（2026-09-10），与 research-3 第 16 节同一提交。
  链接前缀 `P=https://github.com/OthmanAdi/planning-with-files/blob/1ec8f4eb5c683e31644856d98f9abde0d5a53448/`
  全文读过：`skills/planning-with-files/SKILL.md`（500 行）、`scripts/gate-stop.sh`；`scripts/ledger-append.sh` 第 1–140 行与第 180–346 行的 grep；`scripts/check-complete.sh` 第 185–282 行；`scripts/ledger-summary.sh` 第 1–40 行；`scripts/inject-plan.sh` 第 1–60 行与 attestation/nonce 相关 grep；`hooks/hooks.json` 前 60 行。
- **planning-with-teams（PWT）**：HEAD `024def2fda6cdf465d2e6c10b5ae13256fabea35`（2026-08-03）。
  链接前缀 `T=https://github.com/OthmanAdi/planning-with-teams/blob/024def2fda6cdf465d2e6c10b5ae13256fabea35/`
  读过：`skills/planning-with-teams/SKILL.md` 全文、`scripts/check-team-complete.sh` 前 60 行。
- **Anthropic**：用 curl 抓 HTML 转纯文本后全文读：harness-design-long-running-apps（2026-03-24）、effective-harnesses-for-long-running-agents（2025-11-26）、building-c-compiler（2026-02-05）；multi-agent-research-system（2025-06-13）按关键词读相关段落；另找到 2026 年三篇相关文章并读了相关段落：demystifying-evals-for-ai-agents（2026-01-09）、claude.com/blog/building-effective-human-agent-teams（2026-06-24）、claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle（2026-07-21）。anthropic.com/engineering 索引页上 2026-04-23 之后没有新的工程文章条目（索引页只列到 april-23-postmortem；how-we-contain-claude 发布于 2026-05-25，内容是权限隔离，未深读）。
- **MMW**：只读，工作树 HEAD `0f438594`。读过：`mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`code-review/SKILL.md`、`code-review/references/session.md`、`code-review/references/spec-reviewer.md`、`to-tickets/SKILL.md`、`triage/SKILL.md`（均全文）；`mmw-v2/skills/verdict/SKILL.md`、`verify-ticket/references/{sub-issues.md, closeout.md, claiming.md}` 全文；`docs/adr/README.md`、`docs/adr/0012-review-finding-routing.md` 全文；`mmw-v2/skills/dispatch/references/{how-it-works.md, night.md}` 按关键词读；`mmw-v2/skills/dispatch/scripts/turn-guard.py` 头注释；`relay.py` 的 `overlap()`（第 449–470 行）。
- 标注：**推断** = 从读到的文本推出、未见直接陈述或未实测；**未找到** = 查了没有。

---

## 1. BMAD-METHOD v6：实现怎样忠于人批准的意图

### 1.1 bmad-build 五步的骨架

- 一次只加载一个 step 文件："**NEVER** load multiple step files simultaneously"（B/skills/bmad-build/workflow.md#L76）。
- **Step 1**（`step-01-clarify-and-route.md`）：解析状态、检查工作树干净（dirty 或分支不对就 HALT，#L79）、多目标检查——一个 intent 含两个以上可独立交付的目标就让人选 Split（把其余目标追加进 `deferred-work.md`）或 Keep（#L80-L92）。同一 epic 的上一张 `done` 故事，读它的 Code Map、Design Notes、Spec Change Log 与任务表作为连续性上下文（#L66）。
- **Step 2**（`step-02-plan.md`）：先调查代码，调查期间不问人："Do not ask the human during investigation"（#L13）。调查结果写进 spec 的 `## Code Map`，实现时不再复述。人才能定的事写成 `## Open Questions`，**"Never write an intent gap into the frozen block as an assumption"**（#L24）。人回答后把答案作为决定写进冻结区块并删掉问题条目（#L35）。批准前重读磁盘上的 spec，采纳人手工改动（#L59）；批准后 status 置 `ready-for-dev`，"everything inside `<frozen-after-approval>` is then locked and only the human can change it"（#L59）。
- **Step 3**（`step-03-implement.md`）：先把 `baseline_commit` 写进 frontmatter，续跑时不覆盖（#L20）。实现交给一个无上下文 subagent，派发提示只有一句 "the spec is the sole source of truth"（B/skills/bmad-build/customize.toml#L79-L85），并禁止在派发里追加目标复述、文件列表、验收标准（step-03#L32）。实现回来后编排者自己写 diff 文件并读："Judge against the diff, not against the implementation subagent's report"（#L40）。矩阵测试审计："A covering test that exists but did not run — unregistered, filtered out, skipped, or disabled — counts as missing"；"never edit the expectation to match the code"（#L46）。
- **Step 4**（`step-04-review.md`）：三层并行评审（blind-hunter、edge-case-hunter、verification-gap），均为 context-free subagent，只拿 diff 路径（#L14-L24）。然后编排者对每条 finding **先核实再定级**，再分流（见 1.3）。
- **Step 5**（`step-05-present.md`）：status 置 `done`，本地提交，"NEVER auto-push"（#L8）。

### 1.2 冻结区块与三个只追加的节

spec 模板（B/skills/bmad-build/spec-template.md）：

- `<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">`（#L16）包住三节：`## Intent`（Problem/Approach 各一两句）、`## Boundaries & Constraints`（Always/Never）、`## I/O & Edge-Case Matrix`（#L18-L45）。
- 冻结区块之外由 agent 维护：`## Code Map`、`## Tasks & Acceptance`（Given/When/Then）、`## Design Notes`、`## Verification`。
- 三个只追加的节（#L68-L86）：
  - `## Implementation Notes`："Agent-owned. Append-only during implementation: decisions made, files touched, surprises encountered."
  - `## Spec Change Log`："Populated by step-04 during review loops … what finding triggered the change, what was amended, what known-bad state the amendment avoids, and any KEEP instructions (what worked well and must survive re-derivation)."
  - `## Review Triage Log`："Populated by step-04 on EVERY review pass, including loopbacks and blocked exits … one row per reviewer finding: verdict, route, and evidence."
- 篇幅标准："A specification should target a **single user-facing goal** within **900–1600 tokens**"，"above 1600 risks context-rot in implementation agents"，"Neither limit is a gate"（workflow.md#L23-L29）。
- 无人值守版 `bmad-build-auto` 把冻结区块改名为 `<intent-contract>`（B/skills/bmad-build-auto/spec-template.md#L20-L49），并在 Ready-for-Development 标准里加了一条 "**Surface-anchored**: ACs observe the outermost surface the intent references — never a more internal proxy for it"（B/skills/bmad-build-auto/workflow.md#L66）。

### 1.3 评审分流：先核实，再四路分流，回环上限 5

来源 B/skills/bmad-build/step-04-review.md#L28-L80：

1. **每条 finding 先定一个核实结论**，评审 subagent 给的严重度一律忽略："Disregard any severity a reviewing subagent assigned — they lack the context to grade"（#L30）。结论只有五种：`high` / `medium` / `low`（坏结果真实存在）、`false`（查过，不发生，要写出反驳）、`maybe-false`（查不清，要写出还需查什么）（#L38-L40）。"Every finding gets one row in the `## Review Triage Log` … never drop, merge, or silently skip one"（#L42）。
2. 已记过的同一 finding（同位置同论断、代码未变）沿用旧结论，前面加 `carried`，不再重复 patch 或 defer（#L32）——防止回环里反复处理同一条。
3. 拒绝规则：`false` 按反驳拒绝；`low` 且日常碰不到、修法要加分支或参数的拒绝（#L44-L46）。**"Reject any finding whose fix is to edit this build's spec"**（#L50）。越界判断只看 intent，不看 spec 的范围节："If only those would exclude it, keep the finding: the spec or plan drew the line somewhere the intent did not, so it routes to intent_gap or bad_spec, never to patch or defer"（#L48）。
4. 按根因分组，再分到四类之一（#L55-L59）：
   - `intent_gap`：由本次改动造成，但冻结区块里的意图不完整，spec 无法裁决；"Do not infer intent unless there is exactly one possible reading."
   - `bad_spec`：由本次改动造成，spec 本应写清却没写清，含直接偏离 spec；"When in doubt between bad_spec and patch, prefer bad_spec — a spec-level fix is more likely to produce coherent code."
   - `patch`：修法很小、不加公共接口、不守未经证明的状态。
   - `defer`：不是本故事造成的既有问题；或全部 `maybe-false` 且若为真属 medium/high；或修法要改 CLAUDE.md/AGENTS.md 这类 agent 上下文文件。
5. **级联处理**（#L61-L79）：只要有 `intent_gap` 或 `bad_spec` 就回环，低类别作废（代码会重生成）。每次回环前 `review_loop_iteration` +1，**超过 5 就 HALT 交人**。
   - `intent_gap`：根因在冻结区块内。回滚代码，交人补意图，再从 step 2 重跑。
   - `bad_spec`：根因在冻结区块外。**回滚前先抽出 KEEP 指令**（哪些做对了、重生成时必须保留），回滚代码，读 Spec Change Log 并遵守其中全部已记约束，修改 spec 非冻结部分，追加一条变更记录（触发 finding、改了什么、避免的已知坏状态、KEEP），再从 step 3 重新实现。
   - `patch`：发回**同一个**实现 subagent（"a fresh launch is not re-engagement"），只跑受影响测试，编排者再跑完整验证。
   - `defer`：追加进 `deferred-work.md`，不改旧条目、不查重。
- 无人值守版的差别（B/skills/bmad-build-auto/step-04-review.md#L69-L71）：`intent_gap` 不回环，**把尝试过的改动存成 patch 文件**、回滚、HALT `blocked`，附未决问题与 patch 路径；`bad_spec` 回环上限到 5 后 HALT `review repair loop exceeded 5 iterations (non-convergence)`。
- 无人值守版多一层评审 **Intent Alignment Auditor**（B/skills/bmad-build-auto/customize.toml#L114-L131）：拿"verbatim intent"和 diff，"Your task is strictly descriptive — do not prescribe additional work. Report: (1) the defensible readings of the intent, enumerated; (2) which reading this diff implements; (3) where the readings and the diff diverge — specifically, which surface the intent's expectations live at versus which surface the diff's changes and its tests exercise."
- edge-case 层的 **claims check**：spec 是"testimony, not evidence"，在路径追踪做完之后才读，逐条尝试证伪（B/skills/bmad-build/references/claims-check.md#L3-L5）。
- blind-hunter 层要求"find at least N issues"，N 由 diff 大小算出，"If you have zero findings, re-check and keep thinking; do not stop with an empty list"（customize.toml#L102-L105）。

### 1.4 "spec 本身错了"之外的三种纠偏

- **bmad-correct-course**（B/skills/bmad-correct-course/SKILL.md）：交互式。读 PRD、epics、架构、UX、spec 与 AGENTS.md 的 `bmad:context` 区块；按 checklist 逐项评估（触发故事、问题归类如 "Misunderstanding of original requirements"、epic 影响、产物冲突、三条路径 Direct Adjustment / Potential Rollback / MVP Review）；每项改动写成 OLD→NEW 并附理由（#L136-L155）；产出 Sprint Change Proposal，按 Minor/Moderate/Major 分派（#L220-L227），人批准才算数。**没有脚本，也没有自动回写**。
- **bmad-retrospective**（B/skills/bmad-retrospective/workflow.md）：
  - 原则："Every finding you report carries a source reference (file, line, commit, or log). A claim you cannot point at … is not a finding. Drop it."（#L5）
  - Phase 1 证据清点，"A reader of the final retro must always be able to tell **"checked and clean"** from **"never checked."**"（references/evidence-gathering.md#L24）。
  - Phase 2 **aggregate views**：单个会话看不到的缺陷——架构变化、重复实现地图、文件在整个 epic 上累积变大、偏离既有约定、spec 与实现对账。"Nine sessions each added three hundred lines and none ever saw the 3,000-line class they collectively built."（references/aggregate-views.md#L3）；另对整个 epic 的 diff 跑评审，"weighting the boundaries between stories, where no single session ever saw both sides"（workflow.md#L88）；有运行时变化就端到端跑，"Passing tests do not substitute for running the system"（#L89）。
  - Phase 4 每条 finding 两个独立处置："What to do about this instance — fix now, defer, or accept as-is"与"What would prevent the next one — the upstream lesson: spec wording, story sizing, a missing convention or gate, or nothing"（references/acceptance-verdict.md#L9-L10）。子 agent 的 finding 是"unverified reports"，写成行动项前回原始来源复核（#L12）。修复与 spec 对账**只提议不执行**："an uncertain interpretation is never written into the spec automatically"（#L19）。
  - **上一轮 retro 的跟进**：逐条读上一轮行动项，按证据判断是否落地，"An item you cannot point at is "no evidence found", not "not done""（#L26）；只在人确认后才改状态（references/retro-document.md#L62-L80）。
  - 验收结论：`accepted` / `accepted-with-open-items` / `rejected`，有未完成故事时机器结论强制 `rejected`（acceptance-verdict.md#L35-L53）。
  - **回写方式**：行动项经 `sprint_status.py update --add-action` 以稳定 id（`epic-<N>-retro-item-<n>-<slug>`）追加进 `sprint-status.yaml` 的 `action_items`，状态 `open`（retro-document.md#L54）；`bmad-sprint-planning` 的状态视图把未完成行动项列入"下一步建议"（B/skills/bmad-sprint-planning/references/status-view.md#L10）。**retro 不改技能、不改 AGENTS.md、不改 spec**。
- **bmad-project-context 的 `record`**（B/skills/bmad-project-context/SKILL.md#L101-L105）："Capture one observed agent mistake as it happens — the only admissible source for a pitfall … One occurrence is noted; a recurring or costly mistake earns a line now … If it is mechanically preventable, propose the hook, lint rule, or CI check instead." 准入规则："A repo yields hundreds of trap-looking facts and none of them predict real mistakes; only observed behavior does"（references/best-practices.md#L16）；退役规则："nothing failing lately is not evidence — a working rule erases its own evidence"（#L39）。

### 1.5 上下文预算与状态写入

- `compile-epic-context.md`：把 PRD/架构/UX 中与本 epic 相关的部分提炼成一份文件，"Target 800–1500 tokens total"，"Describe by purpose, not by source"，"Nothing derivable from the codebase"（B/skills/bmad-build/compile-epic-context.md#L50-L55）；缓存有效条件是规划目录里没有比它新的文件（step-01#L56）。
- `sprint_plan.py`：唯一写入者；临时文件 + fsync + `os.replace`，写后校验失败恢复原字节；重算状态时"never downgrade"（B/skills/bmad-sprint-planning/scripts/sprint_plan.py#L241、#L325）。退一步看：状态同时存在 spec frontmatter 与 sprint-status 两处，一致性靠流程约定（**推断**，research-3 已记）。
- `memlog.py`：只追加、写时不读、没有生命周期状态，"Whether the work is done, blocked, or paused is itself a fact that happened, so it is recorded as an entry"（B/skills/bmad/scripts/memlog.py#L20-L32）。
- `customize.toml` 三层合并：默认 → `_bmad/custom/<skill>.toml`（团队）→ `<skill>.user.toml`（个人）；"Strings replace the default. Lists append … Arrays of tables merge by `id`"（B/skills/bmad-build/customize.toml#L7-L11）。实现 handoff 与每个评审层都是可替换的一段 instruction，"an override may run anything (e.g. an external reviewer via bash)"（#L87-L91）。

---

## 2. Anthropic 工程文章

### 2.1 planner / generator / evaluator 与 sprint contract（harness-design-long-running-apps，2026-03-24）

URL：https://www.anthropic.com/engineering/harness-design-long-running-apps

- 为什么要分开评估者："agents tend to respond by confidently praising the work"；"tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"。
- **Planner** 只写产品层 spec："if the planner tried to specify granular technical details upfront and got something wrong, the errors in the spec would cascade into the downstream implementation. It seemed smarter to constrain the agents on the deliverables to be produced and let them figure out the path as they worked."
- **Sprint contract（开工前协商完成的定义）**："Before each sprint, the generator and evaluator negotiated a sprint contract: agreeing on what "done" looked like for that chunk of work before any code was written. This existed because the product spec was intentionally high-level … The generator proposed what it would build and how success would be verified, and the evaluator reviewed that proposal to make sure the generator was building the right thing. The two iterated until they agreed." 契约粒度："Sprint 3 alone had 27 criteria covering the level editor"。
- **通信方式**："Communication was handled via files: one agent would write a file, another agent would read it and respond either within that file or with a new file."
- **Evaluator 的输入与输出**：输入是契约里的测试条目与运行中的应用（Playwright MCP，"click through the running application the way a user would, testing UI features, API endpoints, and database states"）；输出是逐条 PASS/FAIL 加定位到代码行的发现，外加四个评分维度（product depth、functionality、visual design、code quality），"Each criterion had a hard threshold, and if any one fell below it, the sprint failed"。
- **怎样把 evaluator 调成怀疑者**："Out of the box, Claude is a poor QA agent. In early runs, I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway. It also tended to test superficially … The tuning loop was to read the evaluator's logs, find examples where its judgment diverged from mine, and update the QAs prompt." 设计领域还用 "few-shot examples with detailed score breakdowns" 校准。
- **何时去掉脚手架**："every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing"；一次砍太多后无法判断哪部分承重，改为"removing one component at a time"。Opus 4.6 下去掉 sprint 结构、evaluator 改成末尾一次；"the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo." 但 QA 仍抓到"several core DAW features are display-only"，"The generator was still liable to miss details or stub features when left to its own devices"。
- 成本数据：solo 20 分钟 9 美元；完整 harness 6 小时 200 美元；V2 harness 3 小时 50 分 124.70 美元。

### 2.2 progress 文件、JSON 功能清单、clean state（effective-harnesses-for-long-running-agents，2025-11-26）

URL：https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

- 两个失败模式："try to do too much at once"，以及"a later agent instance would look around, see that progress had been made, and declare the job done"。
- 功能清单 200 多条，初始全部 `"passes": false`；"We prompt coding agents to edit this file only by changing the status of a passes field … "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality." … the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files."
- clean state："the kind of code that would be appropriate for merging to a main branch: there are no major bugs, the code is orderly and well-documented"；做法是每次提交 git 并写 progress 文件。
- 自称完成："Claude's tendency to mark a feature as complete without proper testing … would fail recognize that the feature didn't work end-to-end"；解法是明确要求用浏览器自动化"as a human user would"。
- **会话开头先验证基础功能再做新功能**："ask the initializer agent to write an init.sh script that can run the development server, and then run through a basic end-to-end test before implementing a new feature … If the agent had instead started implementing a new feature, it would likely make the problem worse."
- 这篇**没有** evaluator 与 generator 分离，脚注说两个 agent 只是初始提示不同。

### 2.3 并行 Claude 的锁、测试预言机、日志（building-c-compiler，2026-02-05）

URL：https://www.anthropic.com/engineering/building-c-compiler

- 锁："Claude takes a "lock" on a task by writing a text file to current_tasks/ … If two agents try to claim the same task, git's synchronization forces the second agent to pick a different one." "I don't use an orchestration agent."
- 测试质量是核心："it's important that the task verifier is nearly perfect, otherwise Claude will solve the wrong problem"；后期新功能频繁破坏旧功能，"I built a continuous integration pipeline and implemented stricter enforcement that allowed Claude to better test its work so that new commits can't break existing code."
- 让 agent 自知进展："include instructions to maintain extensive READMEs and progress files that should be updated frequently with the current status."
- 日志设计："The test harness should not print thousands of useless bytes … if there are errors, Claude should write ERROR and put the reason on the same line so grep will find it. It helps to pre-compute aggregate summary statistics"；"time blindness"对策是 `--fast` 抽样，"deterministic per-agent but random across VMs"。
- 并行失败："compiling the Linux kernel is one giant task. Every agent would hit the same bug, fix that bug, and then overwrite each other's changes"；解法是用 GCC 作为"online known-good compiler oracle"，把问题切到不同文件上。
- 专职角色：去重、性能、文档、从 Rust 开发者角度批评设计。
- 作者的保留意见："it is easy to see tests pass and assume the job is done, when this is rarely the case."

### 2.4 多 agent 研究系统（2025-06-13）

URL：https://www.anthropic.com/engineering/multi-agent-research-system

- 委派："Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."
- 适用边界："most coding tasks involve fewer truly parallelizable tasks than research."
- 评估："focusing on end-state evaluation rather than turn-by-turn analysis"；LLM-as-judge 单次调用输出 0.0–1.0 与 pass/fail "was the most consistent and aligned with human judgements"。
- 自我改进："When given a prompt and a failure mode, they are able to diagnose why the agent is failing and suggest improvements"，工具描述改写后"40% decrease in task completion time"。
- 部署："we use rainbow deployments to avoid disrupting running agents"。
- 产物落文件："Subagents call tools to store their work in external systems, then pass lightweight references back to the coordinator."

### 2.5 2026 年其他相关文章

- **Demystifying evals for AI agents**（2026-01-09，https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents）："A good task is one where two domain experts would independently reach the same pass/fail verdict"；"a 0% pass rate across many trials … is most often a signal of a broken task, not an incapable agent"；"it's often better to grade what the agent produced, not the path it took"；给模型评分者留出口，"return "Unknown" when it doesn't have enough information"，并"grade each dimension with an isolated LLM-as-judge"；"You won't know if your graders are working well unless you read the transcripts."
- **Lessons from Anthropic on building effective human-agent teams**（2026-06-24，https://claude.com/blog/building-effective-human-agent-teams）："the best long-running agents have many different ways to verify their work before a human looks at it … it often helps to give one agent the job of doing the task and another agent the job of checking the first agent's work. This is often called the "Doer-Verifier" agent harness."；建立信任的做法包括"Building reflection into the cycle and asking agents to review their own misses"与"Tracking which kinds of tasks each agent has earned autonomy on and expanding scope per task type after repeated successes"；一个团队每周让 agent 写包含"lessons & missteps"的周报；教 agent "batch questions to be answered in a single pass"。
- **How Anthropic secures its AI-native software development lifecycle**（2026-07-21，https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle）：
  - 发现需带证明："The share of PRs that get substantive review comments has grown from 16 to 54% as we've gained confidence in the findings by requiring the agents to write a proof that their finding is valid."
  - 多个窄评审："Each review agent is designed and scoped to a specific, narrow focus … They do not share biases and blindspots."
  - 治理退化点："If a skill goes stale, a discovered bug class never makes it back into CLAUDE.md, or an agent's decisions go unsampled, the whole structure degrades."；"Shadow mode for all new AI reviewers"；"Sampling a percentage of all automated approvals."
  - 权限边界："draw the boundary around access and actions, not around a model's instructions"。
- 未找到：Anthropic 2026 年关于"generator 与 evaluator 协商完成定义"的后续工程文章（除 2.1 外）。

### 2.6 小结：Anthropic 怎样减少"自称完成"

按文章出现顺序归纳（归纳本身是**推断**，每条来源见上）：
1. 完成的定义在代码之前写下，且写成可检查的条目（功能清单 `passes`、sprint contract）。
2. 判定者与实现者分开，判定者运行应用而不是读代码或读报告。
3. 判定者本身要调：读它的日志，找它放水的例子，改提示。
4. 进度记录只允许改受限字段（JSON 的 `passes`）。
5. 会话开头先验证已有功能没坏，再做新的。
6. 评审发现要附证明，否则噪声会淹没真问题。

---

## 3. planning-with-files 与 planning-with-teams

### 3.1 orchestrator 独占计划，worker 各写 ledger

- 规则："The orchestrator owns `task_plan.md` and shared summaries. Workers report through their own ledgers or assigned files; they do not independently rewrite the shared planning files."（P/skills/planning-with-files/SKILL.md#L85）；"A worker joining an existing task uses its assigned plan; it must not create or overwrite a competing root plan"（#L46）。
- ledger 实现（P/scripts/ledger-append.sh）：每个 agent 一个 `ledger-<agent>.jsonl`；事件词表固定六个 `progress phase_complete error gate_block attest note`（#L40）；summary 截到 200 字符并清理不完整的 UTF-8（#L18-L20、#L99）；"tick = 1 + max tick across ALL ledger-*.jsonl in the plan dir, so concurrent agents share a monotonic counter"（#L31-L33）；有 `flock` 时"Compute tick AND write while holding the lock so concurrent appenders do not pick the same tick number"（#L331-L335），没有时靠单次 `printf` 追加。显式选择器解析失败就拒绝写，不回退到当前目录："a legacy cwd fallback after a rejected selector files another plan's run history"（#L56-L61）。
- 对照 PWT（同作者早期作品）：**所有队友写同一组共享文件**，"All teammates read from and write to the SAME files"（T/skills/planning-with-teams/SKILL.md#L162），并行写靠"Assign file ownership to avoid conflicts"的提示约束。PWF 在 v3.10 写明其后果："Two sessions sharing one plan directory can both write `task_plan.md` from the same read. The later write silently discards the earlier one's work, and nothing notices"（P/skills/planning-with-files/SKILL.md#L387），parallel-write guard 只是事后比较已完成项数量是否下降的提示，"not a lock or merge mechanism… Keep a single writer for shared summaries and separate files for workers"（#L389-L391）。**同一作者从"大家写一个文件"退到"一个写者 + 各自追加日志"**，这是本调研里最直接的反例证据。

### 3.2 注入节奏与防注入

- 节奏（#L369-L377）：旧模式轮次开始注入计划头 50 行 + `progress.md` 尾部，每次工具调用前再注入计划头 30 行；autonomous/gated 模式**去掉每次工具调用的注入**（"strong models drift less"），轮次开始的注入保留。可选 `PWF_INJECT=smart` 只注入 Goal/Next Step/当前阶段与最近 3 条决定（#L383）。
- 结构化摘要代替自由文本：`ledger-summary.sh` 输出固定形状（条目数、阶段完成数、当前 in_progress 标题、每个 agent 最后一个事件类型），"NO free text from disk reaches the model context, and there are NO timestamps, so the injected block is KV-cache stable by construction"（P/scripts/ledger-summary.sh#L5-L7）。理由："`progress.md` is not covered by attestation, so any instruction-like text written there … used to flow into context every turn"（SKILL.md#L476）。
- attestation：计划的 SHA-256 存在 `.attestation`，每次注入重算，不一致就拒绝注入 `[PLAN TAMPERED]`；v3 模式下没有 attestation 直接拒绝注入正文（P/scripts/inject-plan.sh#L1145、#L1169）。作者自己写明局限："a process that can replace both the plan and the attestation can make new content pass"（SKILL.md#L464）。
- nonce 分隔符：注入内容包在 `===BEGIN-PLAN-DATA-<nonce>===` 里；同样写明 nonce 与计划在同一目录，"Nonce framing is not an access-control boundary"（#L474）。
- 规则："Write web/search results to `findings.md` only"，因为 `task_plan.md` 每轮被注入，"untrusted content there amplifies on every tool call"（#L482）。

### 3.3 防提前结束：gated Stop hook

- 只有同时满足五条才阻止结束（SKILL.md#L397-L403；P/scripts/check-complete.sh#L185-L282）：`.mode` 含 `gate`；存在 `in_progress` 阶段（"Merely complete<total is a normal state and must NOT block (issue #178 lesson)"）；`stop_hook_active` 为假；阻止次数低于上限（默认 20，存在 `.stop_blocks`，init 时清零）；上次阻止后 ledger 行数增加了（"no progress since last gate block — allowing stop"）。
- 阻止理由是固定模板 + 阶段名，不带计划正文；"Outside gated mode the wording is always advisory, never imperative (PR #180 lesson: imperative text in a `reason` field becomes a continuation command)"（#L405）。
- "it judges the plan artifact on disk, not the conversation transcript"（#L379）。
- 宿主分三级（#L411-L417）：Claude Code/Codex 能硬阻止；Cursor/Pi 等只能发 follow-up；Gemini CLI 只能提示。

---

## 4. MMW 现有做法（与本调研相关的部分）

- **意图与冻结**：票正文发布后不改（brief）；`## Read first` 里记录已定结论的条目是 baseline，"a contract, not a reference"（`mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 172 行 `## Read first` 模板段）；worker 不得悄悄改 baseline，不合时开 `contract` 子票并继续做（`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 24 行）。spec 正文可原地改，改动理由写一条评论（`mmw-v2/upstream/skills/engineering/to-spec/SKILL.md` 第 32 行，步骤 5 "Revising a published spec"）。人批准的环节：`to-spec` 只在拆成多份 spec 时问人（第 16 行）；`to-tickets` 第 6 步 "Quiz the user" 迭代到用户批准切分（第 106–126 行）。
- **完成的定义在代码之前**：每条验收标准是 `CHECK:` 命令 + 只在成功时打印的 `EXPECT:` 行（`to-tickets/SKILL.md` 第 4 步，第 50–85 行）；判断类的要求不进验收标准而交给 code review（第 53 行）；发布后 `--lint`。
- **独立验证**：verifier 在同一 commit、同一 worktree 重跑全部标准，只写一行结论，"Fix nothing, however small and however obvious the fix"（`mmw-v2/skills/verdict/SKILL.md` 第 52–57 行）；closeout 要求 reverify 事件覆盖的标准指纹与票上当前标准一致，并以 #162 为例（`mmw-v2/skills/verify-ticket/references/closeout.md` "The criteria that run covered"）；`VERDICT` 的 commit 必须等于 `HEAD`。
- **评审**：reviewer 会话起三个 axis subagent（Standards/Spec/Tests），按六条规则把 finding 分成 in-ticket / out-of-ticket；"You report. You do not decide whether a review finding is worth fixing"（`mmw-v2/upstream/skills/engineering/code-review/references/session.md` 第 35–43、80–82 行）。Spec axis 每条 finding 必须引用票/spec/baseline 原句，"A review finding with no quoted line is your opinion"（`references/spec-reviewer.md` 第 53 行）。worker 对 in-ticket finding 修一轮，不再复审（`implement/SKILL.md` 步骤 2，第 60 行）。out-of-ticket 的 `finding` 子票在收口轮由 main agent 按 ADR 0012 四步门槛路由，第 0 步先核对 finding 的条件在当前 `HEAD` 是否仍成立（`mmw-v2/skills/dispatch/references/night.md` 第 136–139 行；`docs/adr/0012-review-finding-routing.md`）。
- **回环上限**：一轮 in-ticket 修复、一个 verifier，`verifier.failed` 后不再起第二个，直接 `HANDOFF REQUIRED`（`implement/SKILL.md` 步骤 4，第 65 行）。
- **spec 错了怎么办**：`contract` 子票"back to whoever wrote the spec or the baseline; never changed quietly and worked on"（`mmw-v2/skills/verify-ticket/references/sub-issues.md` 第 20 行）。**`contract` 子票不唤醒任何人**："A `finding`, a `contract` or a `deferred` child is written on its ticket and wakes nobody, by design"（`mmw-v2/skills/dispatch/references/how-it-works.md` 第 35 行）。只有 `fault` 与 `decision` 唤醒 main agent。
- **状态与通信**：票状态是事件块的 fold，事件只由脚本写（ADR 0019）；唤醒只携带 `#<n> <event>`，"the wake carries nothing the board does not"（`mmw-v2/skills/dispatch/SKILL.md` 第 40 行）。
- **防提前结束**：`turn-guard.py` 只守 main agent 的回合结束，只在 watchdog 不健康且有票被持有时阻止（`mmw-v2/skills/dispatch/scripts/turn-guard.py` 头注释 "The predicate"）；worker 沉默由 watchdog 发现，"a worker has been alive and silent for an hour with nothing to wait on" 时通知 main agent 用 `resume`（`how-it-works.md` 第 43、87 行）。
- **并行冲突**：同 spec 内 `## Owns` 不重叠检查在 `to-tickets` 读回与 `--lint`；relay 的 `overlap()` 只比较**票号**是否被两个 watch 同时持有（`mmw-v2/skills/dispatch/scripts/relay.py` 第 449–470 行），未找到跨 watch 的 `## Owns` 路径重叠检查（grep `dispatch/scripts/` 中 `owns` 只命中 `dispatch.sh` 里关于 `Outside Owns:` 的注释；未逐行读 `dispatch.sh`，结论为部分核实）。
- **一夜之后**：`reverify` → `summary`（`NIGHT SUMMARY` 六行计数）；早上 `triage` 读 `ticket.returned`/`ticket.bounced` 的事件轨迹（`triage/SKILL.md` 第 69–73 行）；triage 表里"A toolbox problem found in a consuming repository → `gh issue transfer`"（第 93 行）。未找到跨夜 retro。

---

## 5. 机制 × MMW 对照表

"值得度"：高 / 中 / 低 / 不引入。

| # | 机制 | 来源 | 解决的问题 | MMW 现有对应物 | 差距 | 是否值得引入、如何以 MMW 的方式引入 | 前提与失效场景 |
|---|---|---|---|---|---|---|---|
| 1 | **spec 错误触发的回环**：bad_spec 回滚→改 spec 非冻结部分→记 Spec Change Log（含 KEEP）→重实现；intent_gap 回滚交人；上限 5 | BMAD step-04-review.md#L61-L79；build-auto 版存 patch 后 HALT | 按错 spec 写出的代码被修修补补而不是按改对的 spec 重写；同一 spec 错误再犯 | `contract` 子票（sub-issues.md 第 20 行），worker 继续做；`HANDOFF REQUIRED`→早间 triage | `contract` 子票**不唤醒 main agent**（how-it-works.md 第 35 行），同一 spec 小节下尚未开工的兄弟票当夜照常派出，会基于同一个错误写代码（**推断**：没有看到任何机制在 `contract` 打开后暂停同小节的票）。没有"改 spec 前先记下哪些做对了"的字段 | **高**。不照搬回滚重生成（夜里没有人批准 spec 改动，而 spec 是产品决定）。MMW 方式：① `contract` 加入唤醒 main agent 的种类；② main agent 的动作只有一个：对 `## Parent` 点名同一 Implementation Decisions 小节、且尚未 `worker.started` 的票暂不派出（`NIGHT SUMMARY` 的 `Not dispatched` 行里写明原因是哪张 `contract`），已开工的继续；③ `contract` 子票正文模板增加一节 "What held"（BMAD 的 KEEP），早上改 spec 时照着保留。实现落点：`how-it-works.md` 唤醒表、`night.md` 唤醒处理表、`status.py`/`advance` 的派出判断 | 前提：票的 `## Parent` 写了小节号（`to-tickets` 模板要求）。失效：worker 把本该是 `decision` 或实现 bug 的问题误开成 `contract`，会冻住一组票一整夜；缓解是只冻结同小节、未开工的票，并在 summary 里可见 |
| 2 | **每条评审发现先核实再处置**，结论 high/medium/low/false/maybe-false，`false` 必须写反驳，全部入 Triage Log，已记的 `carried` | BMAD step-04-review.md#L30-L50；Anthropic SDLC 文："requiring the agents to write a proof that their finding is valid"（16%→54%） | 假发现消耗修复轮，甚至把正确代码改错；真发现被悄悄忽略 | Spec axis 要求引用原句；reviewer 会话只报告不裁决（session.md 第 80–82 行）；worker 修一轮；out-of-ticket 在收口轮有第 0 步核对 | in-ticket finding 的处置**没有逐条记录**：closeout 只对"screen-contract 行的 Missing"强制写明处置（closeout.md 最后几条），其余 in-ticket finding 修没修、为什么不修，票上无法逐条对账 | **高**。保持 reviewer 只报告（MMW 的分工正确：reviewer 与 worker 不同会话、可不同模型）。把核实放在 worker 的修复轮：closing comment 增加 `Review findings:` 一节，每条 in-ticket finding 一行 `fixed <commit>` 或 `refuted: <在 file:line 实际发生什么>`；`--closeout` 像检查 screen-contract Missing 一样检查每条都有一行。反驳由收口轮 main agent 或早间 triage 抽样读 | 前提：review comment 的 `## In-ticket` 列表格式可被脚本解析（session.md 第 66 行已规定每条带 axis 与 file:line）。失效：worker 用空洞反驳糊弄；缓解是要求反驳引用代码位置，且 Spec axis 的 `should not` 不允许 `refuted` |
| 3 | **跨故事 retro**：finding 必须有来源；aggregate views（重复实现、文件累积膨胀、偏离约定、spec 与实现对账）；每条两个处置（本例怎么办 / 怎样防下一次）；行动项稳定 id；下一轮先核上一轮行动项是否落地；只提议不执行 | BMAD bmad-retrospective workflow.md、references/*；Anthropic 人-agent 团队文的"lessons & missteps"周报与"review their own misses"；SDLC 文"a discovered bug class never makes it back into CLAUDE.md … the whole structure degrades" | 单张票各自合格，整批合起来有重复实现、架构退化；同类错误每夜重犯；技能不从结果改进 | `NIGHT SUMMARY` 只有计数；`reverify` 查回归；triage 逐票处理；未找到 retro | 缺口 A 与"没有跨夜 retro"（brief）都落在这里。MMW 的事件轨迹已经是 BMAD 缺的"证据"：`ticket.checked`、`reviewer.reported`、`verifier.*`（含 verifier 写的"What you repaired"）、`child.opened`、`ticket.bounced` 的 `files` | **高**。MMW 方式：新增 `retro` 动作，在 `summary` 之后、`finish` 之前由 main agent 跑（或早上用户点名跑），输入只取票事件 + `git log <spec.opened 的 base>..origin/<base branch>`，产出一条 spec 评论（首行固定，事件由脚本写）：① 每条 finding 带事件或 commit 来源；② 处置二分：本例（开票/接受）与预防（改哪个技能的哪一节、改 consuming repo 的 AGENTS.md 哪一条、加哪个 lint）；③ 预防项里属于工具箱的，按 triage 表第 93 行转成 multi-model-workflow 仓库的 issue，属于 consuming repo 运行知识的交给 `manage-agents-md` 的增量更新；④ 下一次 retro 先读上一次的行动项，按证据写"landed / no evidence found"。全部只提议，人决定 | 前提：事件轨迹完整可读（ADR 0019 已保证）。失效：finding 无来源变成空泛感想——照 BMAD 规则"无来源即丢弃"；retro 产出太多行动项无人处理——每次只提名数量有限的预防项，并跟进上一次的落地率 |
| 4 | **观察到的错误才准入**：一次记下，重犯或代价高才成为一条指令；能机械阻止就提议 hook/lint 而不是加一行；退役需要理由 | BMAD bmad-project-context SKILL.md#L101-L105、best-practices.md#L16、#L39 | 运行知识（怎么起产品、哪个测试不稳）无处沉淀；AGENTS.md 被猜测性条目撑大 | `manage-agents-md` 技能；本仓 AGENTS.md 的 Gotchas；verifier 一行结论里的"What you repaired"（verdict/SKILL.md 第 44 行） | worker 与 verifier 修环境的经验写在票上，但不回流到 consuming repo 的 AGENTS.md（缺口 A） | **中高**，作为第 3 条 retro 的一个产出，而不是新增共享笔记文件。准入门槛照 BMAD：同一修复在两张票以上出现，或一次就让票 `stuck`，才提议写入 | 前提：verifier 真的把修复写进结论行。失效：写入内容来自不可信工具输出——必须经人批准再进 AGENTS.md（见第 13 条 PWF 的注入教训） |
| 5 | **Intent Alignment Auditor**：拿用户原话与 diff，列出意图的多种合理读法、diff 实现了哪一种、意图期望的"表面"与测试实际观察的表面是否一致；"Surface-anchored" AC 标准 | BMAD build-auto customize.toml#L114-L131、workflow.md#L66 | 代码忠于票、票忠于 spec，但 spec/票已偏离用户最初想要的东西；验收标准测的是内部代理而不是用户看到的表面 | Spec axis 只读票、Parent 点名小节、Testing Decisions、Out of Scope、baseline（spec-reviewer.md 第 22–27 行），刻意不读 spec 其余部分以免误报越界；`to-tickets` 规则 1"Observable external behaviour, from the spec's seam or a user-visible UI" | 没有任何一层把最终产物与 spec 的 Problem Statement / User Stories / map 的 Destination 对照 | **中高**。不放进每票评审（会破坏 Spec axis 刻意的读取边界）。MMW 方式：放在 spec 级，作为 retro 的"spec 与实现对账"一节，或收口轮 `reverify` 之后的一次只读会话：输入 spec 的 Problem Statement、User Stories、Out of Scope 与整批 diff 范围，输出只描述不提议（照 BMAD 原文 "strictly descriptive"）。另把 "Surface-anchored" 写进 `--lint` 的 WARN 候选（**推断**可行性：lint 读文本，只能对明显内部路径的 CHECK 发 WARN） | 前提：spec 的 User Stories 写得具体。失效：审计者自己脑补读法——要求每种读法引用原句；与 retro 合并时防止篇幅失控 |
| 6 | **开工前协商完成的定义**（sprint contract：generator 提议构建内容与验证方式，evaluator 审到双方同意） | Anthropic harness-design | 高层 spec 与可测实现之间的缺口；实现者自定标准 | `to-tickets` 在发布前写好可执行 `CHECK:`/`EXPECT:`，用户在第 6 步批准切分，`--lint` 检查；closeout 指纹防改标准 | MMW 已做得更彻底：定义可执行、人批准、事后不可改。剩下的缺口是：**没人在写代码之前确认每条 CHECK 在基线上是红的** | 协商本身**不引入**（Anthropic 需要它是因为 spec 故意写得粗；MMW 的 spec 细到 Testing Decisions）。取其可机械化的一半：见第 7 条 | — |
| 7 | **写代码前先跑一遍**：会话开始先验证已有功能没坏；测试要先失败 | Anthropic effective-harnesses（"run through a basic end-to-end test before implementing a new feature"）；BMAD 矩阵审计"A covering test that exists but did not run … counts as missing" | 基线已坏时在坏基础上加功能；一条 CHECK 在没写代码时就已通过，说明它测不到这张票的行为或工作早已完成 | `--preflight` 只查分支、脏树、状态、标签、blocker、assignee（claiming.md）；负对照只存在于 `boundary-check.py`、journey、story-parity 三个判官；收口轮第 2 步把"已绿但东西坏了"的 CHECK 开成 senior 票（night.md 第 139 行） | 普通测试类 CHECK 没有"先红"证据；这类问题只能在事后被 review 撞见 | **中**。MMW 方式：`--preflight` 认领成功后，在 `worker.started.base` 上把全部标准跑一遍，写一条 `ticket.checked` run `baseline`；closeout 读它：某条标准在 baseline 就 `met` 的，draft 必须对它写一行说明（已被别的票做掉 → `ABANDON … decision` 或走 stale；或 CHECK 测不到 → `contract`）。不阻止开工 | 前提：跑一遍的成本可接受（带 `TIMEOUT:` 的长标准会拖慢开工，**推断**需要允许跳过长标准）。失效：测试文件还不存在时 CHECK 必然"红"，这种红不证明任何事——只对"baseline 已绿"这一种情况下结论 |
| 8 | **Evaluator 调成怀疑者**：读 evaluator 日志，找它发现问题后又自我说服放行、测得太浅的例子，改提示；单维度独立评分；给"Unknown"出口 | Anthropic harness-design；demystifying-evals | 评审放水、浅测 | 验收由命令决定，verifier 不做判断（verdict/SKILL.md "The one line"），这一层 LLM 放水不可能发生——MMW 更好。判断类要求在 code review 三个 axis，各自独立、不跨 axis 合并（session.md 第 68 行） | 三个 axis 的提示没有"读日志 → 改提示"的闭环；`ticket.bounced`/`ticket.regressed` 的票回头看 reviewer 是否漏报，目前没人做 | **中**，并入第 3 条 retro：每次 retro 对 `bounced`/`regressed`/`returned` 的票回读 `reviewer.reported`，记下"评审本应发现而未发现"的条目，作为改 axis 提示的证据 | 前提：有足够多的失败票形成模式。失效：单个案例驱动过度修改提示——照 Anthropic "removing one component at a time"，一次只改一处并在下一轮 retro 核效果 |
| 9 | **并行 agent 撞同一问题互相覆盖** → 把问题切到互不相交的单元（GCC oracle） | Anthropic building-c-compiler | 多 agent 修同一文件、互相覆盖 | 同 spec 内 `## Owns` 不重叠 + Blocked by；`advance` 在 origin 上合并，冲突变 `ticket.bounced` | relay `overlap()` 只比较票号，未找到跨 watch（跨并行 spec）的 `## Owns` 重叠检查；用户记忆中同文件票并行导致 bounce（#748、#750、#751，brief） | **高**，但不是本轮新发现（brief 已列）。MMW 方式：`advance` 派出前，把候选票的 `## Owns` 与同仓库其他 watch 下所有 `worker.started` 且未 `ticket.landed` 的票的 `## Owns` 求交；有交集就不派，summary 的 `Not dispatched` 行写明是哪张票挡住 | 前提：relay 已持有同仓库全部 watch（ADR 0022）。失效：glob 过宽（目录级）造成大量误挡——报告被挡数量，让 `to-tickets` 收紧 glob |
| 10 | **日志为 agent 而写**：少输出；错误写 `ERROR` 与原因在同一行；预先算好汇总；确定性抽样 | Anthropic building-c-compiler | 上下文被日志淹没；agent 不知道自己进展 | 每道闸口拒绝三段式（ADR 0008、`refusal.py`）；`EXPECT` 成功标记；`DIFF` 一行；`--closeout` 首行计数问题并给 `--check-only` 命令 | 无实质差距 | **不引入**，MMW 已做到。 | — |
| 11 | **JSON 清单只允许改 `passes` 字段** | Anthropic effective-harnesses | agent 删改测试项 | 票正文发布后不改；`EVIDENCE` 由脚本写；closeout 比对 reverify 指纹与当前标准（#162） | MMW 在闸口处机械检查，比"强硬措辞 + JSON 格式"强 | **不引入**，MMW 更好 | — |
| 12 | **一个写者 + 各自追加日志**；共享 tick 用 flock | PWF SKILL.md#L85、ledger-append.sh；反例 PWT SKILL.md#L162 | 共享计划被并发覆盖 | 票是唯一的板，每个会话只经脚本写自己的事件；fold 按评论顺序；tracker 为权威（ADR 0001、0019） | MMW 天然避免共享可变文件；PWF 需要锁与事后提示 | **不引入**。它是反对"新增一个所有 agent 都能写的共享笔记文件"来解决缺口 A 的证据：同作者的 PWT 这样做过，PWF 退回到单写者 | — |
| 13 | **注入只放结构化摘要、不放磁盘上的自由文本**；attestation + nonce；外部内容只进 findings | PWF SKILL.md#L461-L487、ledger-summary.sh#L5-L7 | 被注入的上下文里夹带指令（间接 prompt injection），且每轮放大 | 唤醒只带 `#<n> <event>`，不带正文（dispatch/SKILL.md 第 40 行）；MMW 不做周期注入 | 目前无差距。若将来按第 3、4 条把"经验"自动喂给 worker，就会出现同样风险 | **作为约束引入**：任何回流给 worker 的经验必须是人批准后写入仓库的文件（AGENTS.md），不直接把票评论或 verifier 输出拼进 worker 提示 | 失效：绕过人批准直接注入 |
| 14 | **gated Stop hook**：有进行中阶段才阻止；上限 20；上次阻止后无进展就放行；理由固定模板、不带命令式文本 | PWF SKILL.md#L395-L426、check-complete.sh | agent 在任务未完时结束回合 | `turn-guard.py` 只守 main agent；worker 回合结束无结果时靠 watchdog，"alive and silent for an hour with nothing to wait on"后由 main agent `resume`（how-it-works.md 第 43、87 行） | worker 过早结束回合时，最长约一小时后才被发现（**推断**：取决于 watchdog 的阈值实现，只读了文档） | **中**。MMW 方式：扩展 turn guard 的"谁的回合"判断到 worker：该会话持有一张票、票上没有等待中的 `reviewer.started`/`verifier.started`/`worker.queued`、也没有 `ticket.passed`/`ticket.returned`/`fault` 时，阻止一次；照 PWF 的教训加上限与"自上次阻止后票上无新事件就放行"，理由用固定句子（照 `how-it-works.md` 第 87 行 `resume` 那句） | 前提：各宿主回合结束能力表已实测（turn-guard.py 头注释）。失效：Cursor 等只能 follow-up 的宿主上可能形成循环——必须有上限与停滞放行 |
| 15 | **上下文预算**：spec 900–1600 token；epic 上下文 800–1500 token；按"用途"而非"出处"写；可推导的不写 | BMAD workflow.md#L23-L29、compile-epic-context.md#L50-L55 | 实现 agent 上下文腐烂 | worker 只读票、Read first、Parent 点名小节（implement/SKILL.md 第 14 行）——读取范围已按票裁剪 | 票与 spec 没有篇幅上限；未测 | **低**。先在第 3 条 retro 里统计 `returned` 票的正文长度与失败是否相关，有证据再加 `--lint` WARN | 失效：token 上限变成切票理由而非意图理由 |
| 16 | **上一张同 epic 故事的连续性**：读其 Code Map、Spec Change Log、Implementation Notes | BMAD step-01#L66 | 后一个会话不知道前一个做了什么决定 | Spec axis 读已并入 base branch 的票的 closeout（spec-reviewer.md 第 31–42 行）；`integrate` 冲突时 stderr 列出合入的票；worker 自己不读兄弟票（brief 缺口 A） | worker 写代码前看不到 blocker 票的 `DECISIONS` 与 `Outside Owns` | **中**。MMW 方式：`implement` 的读入步骤加一项：本票 `Blocked by` 的已落地票的 `DECISIONS` 评论（只此一条，篇幅可控）。不扩大到全部兄弟票 | 失效：依赖链长时累积过多——只读直接 blocker |
| 17 | **correct-course**：交互式影响分析 + OLD→NEW 改动提案 + 按规模分派 | BMAD bmad-correct-course | 执行中发现方向错 | `wayfinder` map、`to-spec` 步骤 5、`triage` 的 grill | 功能上重合；MMW 没有"一份提案列出受影响的全部 spec/票"的固定格式 | **低**。第 1 条 `contract` 唤醒后早上的处理可借用 OLD→NEW 格式写 spec 修订评论 | — |
| 18 | **blind hunter 下限 N 条发现**，"do not stop with an empty list" | BMAD customize.toml#L102-L105 | 评审偷懒报零 | 三 axis 独立；ADR 0012 记录每票约 3 张子票三代不变 | 强制凑数会放大 ADR 0012 记录的"循环不会自己停" | **不引入**，与 MMW 数据相冲突 | — |
| 19 | **customize.toml 三层合并** | BMAD customize.toml#L7-L11 | 团队/个人覆盖默认流程 | 技能一份文本对所有宿主；`models.json` 管模型 | 个人工具箱，无团队层需求 | **不引入** | — |
| 20 | **状态只由脚本写、原子写、不降级**；memlog 只追加、无生命周期状态 | BMAD sprint_plan.py#L241、#L325；memlog.py#L20-L32 | 手改 YAML 损坏、状态回退 | 事件由脚本写到 tracker、fold 派生状态（ADR 0019）；`reverify` 红票写 `ticket.regressed` | BMAD 状态存两处（**推断**）；MMW 单一来源 | **不引入**，MMW 更好 | — |
| 21 | **按任务类型累计自主权**：重复成功后扩大该类任务的自主范围 | Anthropic 人-agent 团队文 | 一刀切的信任 | `junior-worker`/`senior-worker` 由 `to-tickets` 按"错了是否无声"定级（to-tickets/SKILL.md 第 113 行） | 没有按结果回调定级的数据 | **低**，并入 retro：统计各级别 `returned`/`bounced` 比例，给出定级规则是否需要调整的证据 | — |

---

## 6. MMW 已经做得更好的地方

1. **"完成"由命令判定，独立 verifier 在同一 commit 重跑，闸口核指纹**（verdict/SKILL.md、closeout.md）。Anthropic 的 evaluator 仍是 LLM，文章承认它会"talk itself into deciding they weren't a big deal"；BMAD 的 step-03 由编排者自己对照 diff 勾任务。MMW 的验收层没有给 LLM 放水留位置。
2. **状态是 tracker 上脚本写的事件的 fold**（ADR 0019），单一来源；BMAD 在 spec frontmatter 与 sprint-status 两处存状态，PWF 靠 attestation 与事后提示对付并发改写，PWT 让所有队友写同一文件。
3. **回环有硬上限且更短**：一轮修复、一个 verifier、失败即交回（implement/SKILL.md 步骤 4 解释了"一个 verifier 重复同一问题是这一步永远结束不了的唯一方式"）。BMAD 上限 5，PWF Stop 上限 20。
4. **评审者与实现者是不同会话、可以是不同宿主与模型**，axis 之间不合并不排序；BMAD 要求"All review subagents must run at the same model capability as the current session"（step-04#L5），且 blind hunter 强制下限条数。
5. **负对照已进判官**（`boundary-check.py` 的 `GREEN WITHOUT INTERACTION`、journey 在产品停掉时再跑一次、story-parity 的 `NEGATIVE CONTROL FAILED`），比 BMAD 的"测试没跑也算缺失"更进一步。
6. **唤醒不带自由文本**、agent 之间不轮询、合并在 origin 上先合再查再推——三个参考对象都没有对应的机制。
7. **ADR 0012 有实测数据**支撑"默认自己修、四步门槛开票"，而 BMAD 的 defer 只是追加进一个不查重的文件。

---

## 7. 最值得采纳的 5 条

按对"返工更少、忠于设计初衷、夜间回路更可靠"的直接作用排序。

### 第 1 条：`contract` 子票唤醒 main agent，并暂停同一 spec 小节下未开工的票（表第 1 行）

- **来源**：BMAD bad_spec / intent_gap 分流。
- **现在的效果**：worker 发现 baseline 不成立后开 `contract` 子票、继续做；按设计谁也不唤醒；同一 Implementation Decisions 小节下的其他票当夜照常派出（**推断**，未见阻止机制），第二天早上一组票要按改后的 spec 返工。
- **改后的效果**：发现错误的那一刻起，只有已开工的票继续；未开工的等早上改 spec。返工限于已开工的票。
- **取舍**：一个误开的 `contract` 会让同小节的票停一夜。只冻结同小节、未开工的票，summary 可见，影响有上限。
- **需要你定的事**：夜里因 spec 疑点主动少派票，是否符合你的产品节奏（这改变的是一夜能交付多少）。

### 第 2 条：每条 in-ticket 评审发现在 closing comment 里有一行处置，closeout 机械核对（表第 2 行）

- **来源**：BMAD Review Triage Log；Anthropic 2026-07 SDLC 文"要求写出发现有效的证明"后实质性评论占比从 16% 到 54%。
- **效果**：reviewer 报的问题修没修、为什么不修，在票上逐条可查；假发现不再被默默照改，真发现不再被默默略过。改动集中在 `--closeout` 的检查项与 `--draft` 骨架，属工程决定。

### 第 3 条：一夜结束后的 retro，只用票事件与 git 作证据，产出"本例处置 + 预防措施"并跟进上一次的落地（表第 3、4、8、21 行）

- **来源**：BMAD bmad-retrospective 与 bmad-project-context `record`；Anthropic "lessons & missteps" 与"a discovered bug class never makes it back into CLAUDE.md … the whole structure degrades"。
- **效果**：补上 brief 里的缺口 A 与"没有跨夜 retro"。单张票看不到的重复实现、文件膨胀、同类失败会出现在一份有出处的清单里；工具箱改进项以 issue 形式进入 multi-model-workflow 仓库，运行知识以提议形式进入 consuming repo 的 AGENTS.md。
- **约束**（来自 PWF 的教训与 BMAD 原文）：无来源的条目丢弃；只提议不执行；回流给 worker 的内容必须先经人批准写进仓库文件。
- **需要你定的事**：retro 每夜自动跑还是你点名跑；它产出的工具箱 issue 是否直接进 `ready-for-agent`。

### 第 4 条：spec 级意图对账（表第 5 行）

- **来源**：BMAD Intent Alignment Auditor 与 "Surface-anchored" 标准。
- **效果**：把"整批交付的东西"与 spec 的 Problem Statement / User Stories / Out of Scope 对一次，描述性输出：用户原话有哪几种读法、这批实现了哪种、用户期望的表面与测试观察的表面是否一致。这是目前唯一回答"是否符合设计初衷"而不只是"是否符合票"的一层。放在 spec 级而不是每票，是为了不破坏 Spec axis 刻意的读取边界（spec-reviewer.md 第 27 行）。可作为第 3 条 retro 的一节实现。

### 第 5 条：认领后在基线 commit 上先跑一遍全部标准（表第 7 行）

- **来源**：Anthropic effective-harnesses"新功能前先跑基础端到端测试"；BMAD 矩阵审计"测试没跑等于没覆盖"。
- **效果**：写代码之前就知道哪条 CHECK 在没有任何改动时已经通过——它要么测不到这张票的行为，要么工作已被别的票做完。今天这类问题只能在收口轮第 2 步或 review 中事后撞见，然后开成 senior 票返工。
- **取舍**：开工变慢（长标准要跑两次）。只对"基线已绿"下结论，不阻止开工。

### 未进前五但证据充分的

- **跨并行 spec 的 `## Owns` 重叠检查**（表第 9 行）：值得度高，有 bounce 实例，C 编译器文章给出同一失败模式；未列入前五只因 brief 已识别，不是本轮新机制。
- **worker 的回合结束守卫**（表第 14 行）：缩短 worker 过早结束到被发现的间隔，PWF 的上限、停滞放行、固定理由三条教训可直接照用。

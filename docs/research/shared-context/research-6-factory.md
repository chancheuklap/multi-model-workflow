# Factory Missions 深度调研，与 MMW 逐环节对照

调研日期 2026-09-13。MMW 仓库只读，未改任何文件。

## 0. 来源与可信度

四类来源，可信度从高到低：

| 标记 | 含义 | 代表来源 |
| --- | --- | --- |
| 官方 | Factory 博客、官方文档、官方 changelog、Factory 员工在 AI Engineer 的演讲 | factory.ai/news/*，docs.factory.ai/missions/*.md，docs.factory.ai/changelog/release-notes.md，YouTube `ow1we5PzK-o` |
| 非官方·抓包 | V1ki 用 mitmweb 抓到的 orchestrator 系统提示词（Droid factory-cli 0.84.0，2026-03-25 抓取） | gist 356b121038722ebf32b5aac85482c113 |
| 非官方·实物 | 用户仓库里提交的真实 mission 产物（`.factory/validation/**`、`.factory/skills/**`、validator droid 定义）和两份用户对本机 `~/.factory/missions/` 的取证 | skchaudr/gddp-runtime、AaronAbuUsama/agentic-whatsapp、weklund/mlx-stack、CorrectRoadH/OpenTickly、jellydn/my-ai-tools 等 |
| 推断 | 我根据上面材料得出、没有直接证据的结论 | 文中标"推断" |

版本漂移提醒：抓包是 2026-03 的 0.84.0，gddp 取证是 2026-08 的 0.189.0。两者之间字段有差异，例如抓包提示词要求 `features.json` 有 `verificationSteps`，AaronAbuUsama 在三个本地 mission 里核对后写 "**Not present** in any of the three local missions. Drifted or wrong"。下文凡是字段级细节，都注明出自哪份。

没拿到的：`mission-planning`、`define-mission-skills`、`mission-worker-base`、`scrutiny-validator`、`user-testing-validator` 这五个内置技能的原文（GitHub 代码搜索只找到它们的名字和产物，没有正文）。抓包 gist 只含 orchestrator 的 mission 段、worker 通用系统提示和工具 schema。validator 的子代理提示（`scrutiny-feature-reviewer`、`user-testing-flow-validator`）有用户从 `~/.factory/droids` 拷进 dotfiles 的副本，下文引用，但无法确认它们与当前版本一致。

---

## 1. Mission 全生命周期

### 1.1 总览（每步的产物、写者、读者、格式）

| # | 阶段 | 产物 | 写者 | 读者 | 格式 |
| --- | --- | --- | --- | --- | --- |
| 1 | 需求澄清 | 对话；`AskUser` 问卷 | orchestrator | 用户 | 1–4 题多选（抓包 `AskUser` schema） |
| 2 | 研究 | `.factory/research/`（原始）、`.factory/library/`（提炼） | orchestrator 派出的调研子代理 | orchestrator；worker 读 library | Markdown |
| 3 | 提案 | `mission.md` | `ProposeMission` 工具，用户批准后自动落盘 | 所有角色 | Markdown，五节：Plan Overview / Expected Functionality / Environment Setup / Infrastructure / Non-functional Requirements |
| 4 | 验收契约 | `validation-contract.md` | orchestrator 派子代理起草，≥2 轮顺序对抗评审 | user-testing validator、orchestrator | Markdown，`### VAL-<AREA>-<NNN>: 标题` + 行为描述 + `Tool:` + `Evidence:` |
| 5 | 契约状态 | `validation-state.json` | orchestrator 初始化为 pending；user-testing validator 更新 | orchestrator（修复计划、终局闸） | JSON |
| 6 | 拆解 | `features.json` | orchestrator | runner（按数组顺序派发）、worker、validator | JSON |
| 7 | 工人设计 | `.factory/skills/<worker-type>/SKILL.md` | orchestrator（`define-mission-skills`） | worker | SKILL.md |
| 8 | 运行面 | `AGENTS.md`（mission 目录内）、`.factory/services.yaml`、`.factory/init.sh`、`.factory/library/*.md` | orchestrator；之后 worker、validator 按权限追加 | worker、validator | Markdown / YAML / bash |
| 9 | 执行 | 每 feature 一个 commit；`handoffs/<ts>__<feature>__<session>.json`；`progress_log.jsonl`；`worker-transcripts.jsonl` | worker（commit、handoff 内容）；runtime（日志、骨架） | orchestrator、scrutiny 复审子代理 | JSON / JSONL |
| 10 | 里程碑验证 | `.factory/validation/<milestone>/scrutiny/{synthesis.json,reviews/*.json}`；`.../user-testing/{synthesis.json,flows/*.json}`；`evidence/**` | 系统自动注入的两个 validator feature 及其子代理 | orchestrator | JSON |
| 11 | 修复 | 新的 fix feature 插到 `features.json` 顶部 | orchestrator | runner | JSON |
| 12 | 完成 | README 更新；`validation-state.json` 全部 passed | orchestrator | 用户 | — |

### 1.2 关键原文与模板

**orchestrator 的身份**（抓包）："You are the architect and manager of a multi-agent mission." / "You don't build - you design systems that build, and steer them to success." / "You NEVER write implementation code or do hands-on work yourself."

**对 worker 的假设**（抓包）："Implementation workers are skilled and efficient and execute well-specified features well, but struggle with ambiguity and can be lazy."

**四个阶段**（抓包）："1. **Mission Planning** … 2. **Worker Design** … 3. **Creating Mission Artifacts** … 4. **Managing Execution**"；并要求"Invoke `mission-planning` and `define-mission-skills` skills simultaneously at the start."

**产物创建顺序**（抓包）："1. `validation-contract.md` — must be created first … Run at least 2 sequential review passes with subagents before finalizing. This is mission-level TDD — features.json cannot exist without it. 2. `validation-state.json` … 3. `features.json` — Every `fulfills` ID must reference an assertion from the finalized contract. If the contract doesn't exist yet, stop — go back to step 1."

**两个目录不可混**（抓包）：missionDir 放 `validation-contract.md`、`validation-state.json`、`features.json`、`AGENTS.md`；repo root 的 `.factory/` 放 skills、services.yaml、init.sh、library，且 "The `.factory/` folder MUST be committed to the repository."（2026-04-22 changelog："Files related to Missions now live together under `~/.factory`"，mission 目录现在在 `~/.factory/missions/<uuid>/`，gddp 取证里 skills、library、services.yaml 也出现在 mission 目录内。推断：repo 与 mission 目录的分工在 4 月后调整过，提示词里"commit 到仓库"的规则是否仍成立未验证。）

**features.json 单条**（抓包模板，节选）：

```json
{
  "id": "checkout-reserve-inventory-endpoint",
  "description": "POST /api/checkout/reserve - Atomically reserve inventory ...",
  "skillName": "backend-worker",
  "milestone": "checkout",
  "preconditions": ["Cart service returns user's current cart items with quantities", "..."],
  "expectedBehavior": ["Returns 409 with { code: 'INSUFFICIENT_STOCK', ... }", "..."],
  "verificationSteps": ["npm test -- --grep 'reserve inventory' (expect 8+ test cases)", "..."],
  "fulfills": ["VAL-CHECKOUT-001", "VAL-CHECKOUT-002", "VAL-CHECKOUT-003"],
  "status": "pending"
}
```

实物 schema（gddp 取证，0.189.0，从二进制 byte 62,914,074 读出）：`{id, description, status: pending|in_progress|completed|cancelled, skillName, preconditions[], expectedBehavior[], fulfills?[], milestone?, workerSessionIds?[], currentWorkerSessionId?, completedWorkerSessionId?}`。没有 `verificationSteps`。validator 本身也是 features.json 里的条目，`skillName` 为 `scrutiny-validator` / `user-testing-validator`，无 `fulfills`，描述写 "Always returns to orchestrator."

**state.json 状态机**（gddp 取证）："MissionState: planning, awaiting_input, initializing, running, paused, orchestrator_turn, completed"；"SuccessState: success, partial, failure"。

**progress_log.jsonl 事件词表**（gddp 取证）：`mission_accepted`、`mission_paused`、`mission_resumed`、`mission_run_started`、`worker_started`、`worker_selected_feature`、`worker_completed`、`worker_failed`、`worker_paused`、`handoff_items_dismissed`、`milestone_validation_triggered`。AaronAbuUsama 的一个真实 mission：27 features、47 runs、238 条事件、11 次 pause / 9 次 resume，他写 "The mission was stopped and restarted constantly and did not care, because state is on disk."

**执行循环**（抓包）："**start_mission_run is a blocking call.** … The runner spawns workers sequentially, each executing one feature." 返回条件三选一："A worker's handoff contains actionable items (discoveredIssues, unfinished work, or returnToOrchestrator=true) / The user pauses the mission / All features complete"。

**worker 启动**（抓包）："1. The system pre-assigns a feature to the worker (the first pending feature in features.json). 2. The worker invokes `mission-worker-base` skill for setup (read mission.md, AGENTS.md, run init, baseline tests). 3. The worker invokes the specific skill you specified for that feature to complete the work. 4. Commits the work and returns a structured handoff."

**失败重跑**（抓包）："When a worker returns with `successState: "failure"` or `"partial"`, the system resets the feature to `pending`. Calling `start_mission_run` will execute that same feature again first." 官方 troubleshooting 提到 "A feature retry limit warning appears"，上限数值未找到。

**终局闸**（抓包）："Before declaring mission complete, check `validation-state.json`. ALL assertions must be `"passed"`." 另加一条 README 闸（changelog 2026-02-24："Missions now require README updates before completion"）。

**成本粗估**（官方 planning.md）："`total runs ≈ #features + 2 * #milestones`"，"In practice, this is a floor rather than a ceiling."

---

## 2. 验收契约（validation contract）

### 2.1 断言怎么写

抓包的字段要求："**Stable ID** with area prefix … **Title** … **Behavioral description**: semantic but unambiguous, with a clear pass/fail condition … **Evidence requirements**: what evidence must be collected (screenshots, console-errors, network calls, terminal output)"。官方博客的样例多一行 `Tool: agent-browser`。

AaronAbuUsama 在真实 mission（96 条断言，54KB 契约）里看到的写法，比提示词多一条显式失败条件：

```markdown
### VAL-FOUND-003: Provider bootstraps only from publishable key
The web provider initializes ... The assertion fails if provider setup requires Convex URL, Openfort config, ...
Tool: shell
Evidence: provider source citation and forbidden-pattern scan for `convexUrl`, ...
```

他的判断（非官方）："**Failure condition** — an explicit _"The assertion fails if …"_. This is what stops a validator rationalising a pass. Every assertion has one." 契约前言写："It is black-box and behavior-based: validators must test user-visible behavior, build/runtime boundaries, and external integration boundaries, not implementation preferences."

### 2.2 怎么保证可测、完整

- **先契约后拆解**（官方博客）："When creating the validation contract, the orchestrator draws from its understanding of requirements. If it had created the features first, the contract would be influenced by the implementation it had already planned."
- **按用户视角枚举**（抓包）："Spawn a subagent for each feature to investigate and enumerate all possible user interactions: What can a user DO with this feature?" 并要求跨区流程："Include first-visit flow, reachability via actual navigation (not just direct URL), and any flows that span multiple features."
- **对抗评审**（抓包）："run **at least 2 sequential review passes** … one reviewer per area plus one for cross-area … It is very likely that important assertions are missing, even if the contract looks good on the surface. Ensure that the agent is skeptical, adversarial, and actively tries to find gaps." 真实 mission 目录里有 `contract-work/review-pass-1-*.md`、`review-pass-2-*.md`（AaronAbuUsama）。
- **计划期实测**（非官方·实物）：`mission.md` 有一节 "Already verified during planning"，记录规划时实际跑过的事实和会过期的事实（"Workers must re-check npm at dependency-update time"）。changelog 2026-02-26 "Dry-run validation - New dry-run validation approach during Missions planning"；gddp 取证在二进制里看到 `InspectMissionReadiness` / `daemon.inspect_mission_readiness`。推断：规划期有一步"验证环境能跑验收"的就绪检查，细节未找到。

### 2.3 与 `fulfills` 一一对应

抓包原文："**`fulfills` semantics ("completes", not "contributes to")**: Only the leaf feature that makes an assertion fully testable claims it. Infrastructure/foundational features have empty or no `fulfills`. Each assertion ID should appear in exactly one feature's `fulfills` across the entire features.json. **Coverage check (REQUIRED before starting mission):** Every assertion ID in `validation-contract.md` must be claimed by exactly one feature. Unclaimed assertions = planning gap."

实物核对（AaronAbuUsama）："**The coverage gate is real and it held.** In this mission: 96 assertions in the contract, 96 referenced across `fulfills`, zero uncovered, zero dangling references."

user-testing validator 用 `fulfills` 决定本里程碑测哪些断言（抓包："Determines testable assertions from features' `fulfills` field"），所以 `fulfills` 同时是覆盖检查的依据和验证调度的依据。

### 2.4 何时修订、如何传播

触发点是用户中途改需求，或者执行中发现的新事实。抓包里的"Handling Mid-Mission User Requests"九步：

1. Pause execution；2. 澄清与调研交替；3. 提出变更方案；4. 等用户确认；
5. **先改指导性共享文件**："every file that states the old truth must be updated to state the new truth before workers resume." 要检查的文件：`mission.md`（列了七个小节名）、`AGENTS.md`、`.factory/library/`、`.factory/skills/`；
6. **契约修订交给子代理**："The orchestrator should not open or edit `validation-contract.md` or `validation-state.json` itself during mid-mission updates." 语义：新增断言写入并在 state 里置 pending；删除断言"removed entirely"；修改断言"If the change invalidates a previous `"passed"` result … reset the status to `"pending"`"；子代理必须返回"assertions added … removed (with orphaned `fulfills` references) … modified (with which were reset to `"pending"`)"；
7. 重新满足覆盖不变量（无孤儿、无重复）；
8. **一致性复核**："No file should contradict another. For large changes, delegate a review pass to a subagent";
9. 所有产物改动作为 "a single atomic commit"，然后恢复运行。

两条收尾规则：
- 契约不留历史："The validation contract is a living specification of current requirements, not a history log — git history provides the audit trail. Features use `"cancelled"` status because they serve as execution history; assertions don't need this because they represent what's true *now*."
- 太大的变更开新 mission："If the scope change would fundamentally restructure the mission … Tell the user to start a new mission in this case."

**传播失败的真实案例**（gddp 取证，非官方·实物）：一个 feature 的描述要求把 wrapper 精简成"worktree-only"，与契约 VAL-WRAPPER-001..009 和 `architecture.md` 描述的旧设计矛盾。worker 按 feature 描述做了，scrutiny 通过，user-testing validator 判 7 条断言 failed，理由是 "The minimal wrapper pipes raw packet JSON and has no contract-required build_prompt interface." scrutiny synthesis 给出的建议是 "Reconcile wrapper descriptions and assertions with the approved minimal worktree-only executor contract."，`isSystemic: true`。也就是说：变更只写进了 feature 描述，没有走第 5、6 步，于是契约仍陈述旧事实，验证循环把"正确的新实现"判成失败。这正是那条规则要防的事，也说明规则只写在提示词里、没有机器检查时会漏。

---

## 3. Validator

### 3.1 种类与时机

官方博客："Scrutiny validators review each worker's implementation and trajectory for quality and correctness, and encode relevant knowledge updates into shared state. User-testing validators exercise the system as a black box - using it the way a real user would - and verify behavior against the validation contract."

抓包："When all implementation features in a milestone complete, the system automatically injects two sequential validation features … **You do NOT create these yourself**"。可在设置里关：`missionModelSettings.skipScrutiny`、`skipUserTesting`（官方 reference.md）。

演讲（Luke Alvoeiro，AI Engineer，2026-05-06 上传）："Critically neither validator has seen the code before. They're not invested in the implementation and so validation is adversarial by design."

### 3.2 Scrutiny validator

- **硬闸**（抓包）："Runs test suite, typecheck, lint as hard gate"。
- **每个 feature 一个复审子代理**，重跑时只复审 fix feature 并与原 feature 一起看（抓包）。
- **复审子代理的输入**（`scrutiny-feature-reviewer.md`，非官方副本）：`features.json` 里该条目；handoff（按 workerSessionId 找）；`git show <commitId>`；**worker 轨迹骨架** `worker-transcripts.jsonl`；该 worker 的 SKILL.md；`AGENTS.md`、`services.yaml`、`library/architecture.md`。明确"You do NOT re-run validators"、"Do not fix code"、"Do not launch services, browsers, or other heavy processes."
- **复审子代理还要找共享状态缺口**："**Convention gaps** … **Skill gaps**: Compare the worker's skill file against the transcript skeleton and `handoff.skillFeedback` … **Services/commands gaps** … **Knowledge gaps**"，写进 `sharedStateObservations`。
- **单 feature 报告**（副本）：`{featureId, reviewedAt, commitId, transcriptSkeletonReviewed, diffReviewed, status: pass|fail, codeReview:{summary, issues:[{file,line,severity: blocking|non_blocking,description}]}, sharedStateObservations:[{area, observation, evidence}], addressesFailureFrom, summary}`。
- **里程碑综合报告** `scrutiny/synthesis.json`（实物，weklund/mlx-stack 与 gddp 两处一致）：`{milestone, round, status, validatorsRun:{test,typecheck,lint:{passed,command,exitCode}}, reviewsSummary:{total,passed,failed,failedFeatures}, blockingIssues:[{featureId,severity,description}], appliedUpdates:[{target,description,sourceFeature}], suggestedGuidanceUpdates:[{target,suggestion,evidence,isSystemic}], rejectedObservations:[{observation,reason}], previousRound}`。
- **写权限分层**（抓包）："The scrutiny validator directly applies factual, low-risk updates to `services.yaml` and `.factory/library/`. These are already committed." 而对 `AGENTS.md` 和 worker skill 只能提 `suggestedGuidanceUpdates`，由 orchestrator 判断："If it's systemic (same issue across multiple features/workers), strongly consider acting on it"。

### 3.3 User-testing validator

- **流程**（抓包）："Reads `.factory/library/user-testing.md`, `services.yaml` … Determines testable assertions from features' `fulfills` field … Sets up environment (starts services, seeds data) … Plans isolation strategy (assertion grouping, state partitioning, isolation resources) … Spawns flow validator subagents … Synthesizes results, updates `validation-state.json`"。
- **flow 子代理**（`user-testing-flow-validator.md`，非官方副本）：只拿到分给它的断言 ID 和隔离资源（账号、URL、端口、数据目录）；"**Stay within your isolation boundary.**"；环境坏了只许做不影响他人的修复，否则把断言标 `blocked`："Do NOT restart services or modify shared infrastructure — other subagents may be using them."；证据硬要求："Screenshots: mandatory for any UI flow / Console errors check: mandatory for any UI flow / Terminal snapshots: mandatory for CLI flows / Network calls: mandatory when the assertion involves API requests"；资源纪律："Use a single tool session … Close your tool session before writing the report."
- **flow 报告**：每条断言 `status: pass|fail|blocked|skipped`、`steps:[{action,expected,observed}]`、`evidence`、`issues`；另有 `frictions:[{description,resolved,resolution,affectedAssertions}]`（验证时遇到的、`user-testing.md` 没写的坑）和 `blockers`。
- **状态文件**（实物）：`validation-state.json` 每条 `{status: pending|passed|failed|blocked, validatedAtMilestone?, issues?}`，AaronAbuUsama 看到的版本还有 `validatedBy`、`evidence[]`。
- **知识回写**（抓包）："The user testing validator updates `.factory/library/user-testing.md` with runtime findings (isolation approach used, new constraints from this milestone's implementation, gotchas) and may update `.factory/services.yaml`." 并允许整轮只修环境："The validator may spend its session resolving setup issues (creating fixtures, fixing services) without testing any assertions. If so, just re-run — no fix features needed."

### 3.4 输入是 diff 还是轨迹

两种都有：scrutiny 复审子代理读 diff（`git show <commitId>`）和轨迹骨架；user-testing 子代理只读契约与运行中的产品，不读代码。官方博客对 scrutiny 写的就是 "implementation and trajectory"。

### 3.5 发现问题后的路由

官方博客："Validators … don't implement fixes - they surface issues to the orchestrator, which creates fix features that future workers implement."

抓包"Handling Validation Failures"：validator 失败 → 回 orchestrator → orchestrator 派子代理分析根因 → "Create fix features at the top of features.json" → 同一个 validator feature 仍是 pending，自动重跑 → "On re-run, the validator reads its previous report and only re-validates what failed" → 需要给重跑的 validator 传话，就在其 description 末尾追加 "Orchestrator note after round 2: ..."。

**封存里程碑**（抓包）："Once a milestone's validators pass, that milestone is **sealed**. Never add features to a completed milestone." 之后发现的工作进 `<name>-followup` 或 `misc-*` 里程碑（每个最多 5 个 feature，放在当前工作之后 2–3 个里程碑）。"This ensures every change gets a validation pass. No exceptions for "small" or "internal" changes."

**覆盖失败须留痕**（抓包）："Overrides must never be silent — always leave an auditable trail." user-testing override 要求把未通过的断言 ID 移出已封存里程碑的 feature，挪到未封存里程碑的 feature 上并重置为 pending。

**收敛数据**（官方博客，Slack clone）："Round 1 0/6 … Round 2 1/6 … Round 3 2/6 … Round 4 6/6 milestones passed"；"Every milestone converged in 2-4 validation rounds"；"validators surfaced 81 issues, and the orchestrator generated 21 targeted fix features (34.4% of implementation work)"。演讲："Notice how validation never succeeds on the first go."

---

## 4. Worker 的上下文

### 4.1 拿到什么、不拿什么

- **拿到**：注入的 feature JSON（gddp 取证的 worker 骨架第一段就是 "## Your Assigned Feature" + 整条 feature JSON）；环境快照（pwd、ls、git status、git log -5、工具版本）；仓库 AGENTS.md；`mission-worker-base` 让它读 `mission.md`、mission `AGENTS.md`、跑 `init.sh`、跑基线测试；它的 worker SKILL.md 规定读哪些 library 文件（例如 OpenTickly 的 `tracking-backend-worker`："Read mission `mission.md`, mission `AGENTS.md`, `.factory/services.yaml`, `.factory/library/architecture.md`, and `.factory/library/documentation-traceability.md`."）。
- **不拿**：前一个 worker 的对话；orchestrator 的上下文；validation contract 全文不在强制读取列表里（推断：抓包没有要求 worker 读契约，feature 的 `expectedBehavior` 是它的直接验收）。
- **工具被裁**（抓包）："Workers **cannot** spawn sub-agents, ask the user questions, or propose missions."（worker 13 个工具，无 `AskUser`、无 mission 工具；工具列表里仍有 `Task`，与这句话矛盾，gist 原文如此，未核实）。changelog 2026-04-20："Missions worker permission requests are now auto-denied"。
- **worker 系统提示**是通用 Exec 模式提示："You cannot ask the user for help or clarification. If the task is unclear or ambiguous, you must research and review alternatives until you figure out their intent."

### 4.2 library 的读写

- 结构（抓包）："the library has a **flat structure** (no nested folders). Organize by topic, not by milestone." 初始文件 `environment.md`、`architecture.md`、`user-testing.md`、`[topic].md`，每个文件头写清"What belongs here / What does NOT belong here"。
- 原始调研与提炼分开（抓包）："Distilled, worker-facing knowledge goes in `.factory/library/`; raw research stays in `.factory/research/`."
- 写入者：orchestrator 初始化；"Workers will add knowledge during execution."；scrutiny 直接落"factual, low-risk updates"；user-testing validator 写 `user-testing.md`。实物（gddp 取证表）：`library/environment.md` 的最后写者是 "scrutiny validator applied update"，`library/user-testing.md` 的最后写者是 "user-testing validator"。
- 已知与 mission 无关的老问题写进 mission `AGENTS.md` 的固定小节（抓包）："## Known Pre-Existing Issues (Do Not Fix) … so future workers/validators don't waste time on the same issues"，且 "Don't create fix features"。

### 4.3 services.yaml 作为命令唯一来源

抓包原文："The **single source of truth** for all commands and services. Workers read this - they don't guess." 分 `commands`（install/typecheck/build/test/lint）与 `services`（`start`/`stop`/`healthcheck`/`port`/`depends_on`）。"**CRITICAL: If the service runs on a port, the port must be hardcoded in ALL commands**"。测试并行度按机器资源设（"`max(1, floor(cpus / 2))` for conservative"）。坏了怎么办："If a worker finds that a command or service in the manifest is broken … they will return control to you. You must then either fix the broken entry …, create a feature to fix it …, or **return control to the user** if the issue is an external dependency you cannot restore". 边界与命令分开："Boundaries define what's allowed; the manifest defines how to do it."

它解决的问题：每个 fresh worker 不再各自摸索怎么起服务、用哪个端口，避免端口冲突和"猜命令"。

### 4.4 Handoff 字段

实物 schema（gddp 取证，7 份 handoff 全部核对过）：顶层 `{timestamp, workerSessionId, featureId, milestone?, commitId?, repoPath?, successState: success|partial|failure, returnToOrchestrator: boolean, handoff}`；`handoff` 内 `salientSummary`、`whatWasImplemented`、`whatWasLeftUndone`、`verification:{commandsRun:[{command,exitCode,observation}], interactiveChecks:[{action,observed}]}`、`tests:{added,updated,coverage}`、`discoveredIssues[]`、可选 `skillFeedback:{followedProcedure, deviations:[{step,whatIDidInstead,why}], suggestedChanges[]}`。文件名 `<UTC>__<featureId>__<workerSessionId>.json`，写入器"returns without rewriting if the path exists"（只写一次）。

OpenTickly 的 worker SKILL 里，`tests.added[].cases[].verifies` 直接写断言 ID（`"verifies": "VAL-TIMER-001"`），把测试用例和契约断言连起来。

演讲对 handoff 的定位："It fills out a structured handoff detailing what was completed, what was left undone, what commands were run throughout that that agent loop and what were the the exit codes of those commands. What issues were discovered and did it abide by the procedures that the orchestrator defined for that worker? That's how we catch issues and how the system self-heals."

**handoff 里的事项不许静默丢弃**（抓包 `DismissHandoffItems`）："To continue the mission run, you need to take one of these actions before calling start_mission_run again."；justification "Minimum 20 characters"；"\"Low priority\" or \"non-blocking\" is not a sufficient reason to dismiss."；"Skipped work (e.g., skipped manual QA, incomplete verification) is tech debt, and must be tracked." 被丢弃项的类型枚举：`discovered_issue`、`critical_context`、`incomplete_work`。演讲："the only deterministic logic is very thin … Stuff like running validation and ensuring that progress is blocked when there are some handoff issues that are not addressed."

**handoff 的可靠性限制**（gddp 取证）："only 2/7 handoffs carry commits; a handoff does not reliably declare the feature's exact base"；"there is no explicit `attempt`, `retryOf`, or duplicate-completion discriminator"。handoff 是 worker 自述，没有机器核对它和 git 是否一致。

### 4.5 returnToOrchestrator 条件

- 越界（抓包 AGENTS.md 模板）："Workers: If you cannot complete your work within these boundaries, return to orchestrator. Never violate boundaries."
- services.yaml 里的命令或服务坏了（见 4.3）。
- worker SKILL 自定义条件，例如 OpenTickly："The required behavior depends on a source doc outside the closed set in mission `AGENTS.md` / The backend rule cannot be implemented truthfully without changing mission boundaries or external dependencies / The feature would require inventing undocumented semantics rather than applying the approved mission contract"。
- runtime 层面：handoff 带 `discoveredIssues` 或 `whatWasLeftUndone` 非空，`start_mission_run` 也会返回（抓包）。validator feature 一律 "Always returns to orchestrator."

orchestrator 何时再回用户（抓包"When to Return to User"）：需要人做的动作；需要人判断的安全/架构/商业决定；无法恢复的外部依赖（"Do not create retry features for infrastructure you can't fix."）；需求歧义；范围明显超过约定；需要改边界。

---

## 5. Orchestrator 的"研究先行"与规划

抓包里规划期做的事，按降低返工的作用归类：

| 做法 | 原文 | 防的返工 |
| --- | --- | --- |
| 需求全记录并回显 | "Every requirement the user mentions - even casually, even once - must be captured and tracked." / "Before proposing, echo back every requirement you've captured at least once" | 漏需求导致后期补 feature |
| 通过子代理探索代码，自己只看结构 | "**You handle:** README, AGENTS.md, package.json, directory listings, infrastructure checks (ports, services)" / "**Subagents handle:** Code reading, flow tracing, module analysis, operational discovery" | orchestrator 上下文被细节占满后判断变差 |
| 先弄清怎么跑 | "always find out how to run things correctly - build commands, test commands, dev servers, database setup, required services, environment variables" | worker/validator 各自猜命令 |
| 按技术新旧决定是否上网查 | "Research is NOT needed for: Foundational, slowly-evolving technologies … Research IS needed for: … Smaller or newer ecosystems (Convex, Drizzle, Hono, etc.) / SDK-heavy integrations" | 用过时 API 设计架构 |
| 拆解时发现知识缺口就暂停补查 | "If you discover knowledge gaps during decomposition, pause and spawn research subagents to fill those gaps before proceeding." | 拆出不可实现的 feature |
| 每阶段要用户确认 | "Each phase requires user confirmation before proceeding." 里程碑数 "get explicit user agreement" | 方向性返工 |
| 先契约、对抗评审两轮、覆盖闸 | 见第 2 节 | 漏断言、feature 与断言脱节 |
| 设计 worker 技能与 handoff 要求 | "Designing handoff requirements that surface shortcuts and gaps" | worker 偷工不暴露 |
| 定边界（端口段、禁区） | "## Mission Boundaries (NEVER VIOLATE) … Port Range: 3100-3199" | 多进程抢端口、误碰他人资源 |
| 资源感知 | "Before finalizing the manifest, check machine resources." | 并发测试压垮本机 |

官方文档对规划价值的判断（planning.md）："The biggest value we have found in Missions is in the planning phase." 演讲："argue with the orchestrator about the scope, approve the plan, and then go do something else."

2026-08-27 研究文章（官方，"What it Takes for Coding Agents to Complete Large Software Tasks"）把这一点推进了一步，给出目前最强的数据：同一模型，单 agent 在 gdal 重写上达到 36% 行为一致性，"It did not run out of time or budget. It stopped because, by its own assessment, it was done."；三角色系统（validator 先造"instrument"，再持续度量）达到 90%。24 个任务三个模型的中位数：Fable 5 从 56.7 到 89.3，Kimi K3 从 45.1 到 75.4，GPT-5.6-sol 从 48.6 到 66.2（每格单次运行，无方差；非算力对齐，gdal 系统版 14 倍 credits、13 倍墙钟）。结论原文："The single agent didn't lack skill. It lacked a standard of completion." 并声明："We are building this structure into the next generation of Missions."

这篇文章新增了一条 Missions 当前版本没有的约束，叫"the wall"："the implementer never authors it, runs it, or sees its cases or raw output: once a sparse sample becomes visible, it becomes the target, and passing it establishes those cases, not the space they were meant to represent." validator 只把按根因聚类后的发现交给 orchestrator，orchestrator 转成功能层面的指令给实现者。validator 也不许削弱标准："cannot weaken or revise it to accommodate what the candidate happens to contain."

---

## 6. 并行与冲突

- **顶层串行**（演讲）："we tried that and it doesn't really work for tasks in the like software dev domain because agents conflict. They step on each other's changes. They duplicate work. They make inconsistent architectural decisions. … The difference with missions is that we run features serially. So there's only one worker or validator running at any given point in time. Within a feature, we allow for parallelization on read-only operations … Within validators, we also parallelize read-only operations such as code review." 声称"the error rate drops dramatically"，未给数据。
- **官方文档的表述**（Introducing Missions）："Serial execution with targeted parallelization has worked better than broad parallelism." 同时列为开放问题："Is parallelization necessary?"。Factory 2.0 博文（2026-06-15）又写 Missions "decomposing work into parallel tracks"，与演讲不一致，未找到解释。
- **实物印证**（gddp 取证）："Top-level timeline has no overlap: every next `worker_started` follows the previous `worker_completed`"；validator 的子代理有并发（三个 scrutiny 子记录同一时刻创建）。
- **排序**（抓包）："Features are executed in array order - first pending feature runs next." / "Place foundational features first (database schema before API endpoints)" / "When adding urgent/blocking features, insert them at the TOP of the array"。没有显式依赖边，依赖只靠数组顺序和 `preconditions` 文字。
- **文件冲突怎么避免**：靠串行本身，加上每个 worker 在上一个 worker 的 commit 上开始（演讲："commits by Git allowing the next worker to inherit a clean slate and a working code base"）。gddp 取证："mission output was committed in-place/on main rather than isolated onto a per-feature branch."，spawn 调用里 "no mandatory per-feature worktree parameter is visible"。
- **user-testing 的并行隔离**：由 validator 规划"assertion grouping, state partitioning, isolation resources"，每个 flow 子代理分到自己的账号/端口/数据目录（副本提示词）。
- **多个 mission 并发**：changelog 2026-02-26 "Warns on Missions entry and confirms concurrent Missions runs"——只警告，不做冲突检测。

---

## 7. 失败模式、批评、成本

### 7.1 官方自承的问题

- Introducing Missions："Milestone validation catches most, but the orchestrator still scopes too broadly sometimes, and workers get stuck on edge cases a human would navigate easily."；"Worker scope. Narrow scope keeps workers focused but increases overall cost and introduces more coordination overhead."；"Recursive management depth … Three starts to feel like a bureaucracy."
- 官方 troubleshooting 列出的症状：mission 冻结、单 worker 卡住（建议 "Mark it as complete and move to the next feature"）、卡在里程碑、feature 重试上限警告、"Validation keeps failing or QA cannot run"。
- 前提要求（overview.md）："your repository should be at Agent Readiness **Level 4 (Optimized) or above** … Without it, the mission cannot reliably verify its own work."
- 2026 年修过的可靠性 bug（changelog）："Missions after sleep - A mission now moves a stuck worker onto a fresh one after your machine sleeps instead of hanging"（08-17）；"Mission milestones now run their validation steps even after a session is interrupted, paused, or resumed"（08-29）；"Validation contracts now update correctly when Mission requirements change"（02-27）；"Missions artifacts are now schema-validated on create, edit, and apply-patch"（04-23）；"Mission skills are now validated when starting a mission run"（04-29）。

### 7.2 实物里看到的失败

| 失败 | 证据（非官方·实物） |
| --- | --- |
| 契约没跟着设计变更更新，validator 把新实现判失败 | gddp 取证：VAL-WRAPPER 7 条 failed，synthesis 建议 "Reconcile wrapper descriptions and assertions" |
| worker 技能名配置了但运行时找不到，跨两个里程碑的 synthesis 都在报 | weklund/mlx-stack：ops round1 `"Skill \"cli-feature\" not found"`，lifecycle round2 "Multiple lifecycle fix reviews still show transcript-level mismatch"，均标 `isSystemic: true`。说明 `suggestedGuidanceUpdates` 靠 orchestrator 自觉，不会自动生效 |
| 技能文本与仓库事实不符 | 同上："skill guidance references `cli/__init__.py`, but command registration in this repo is done in `cli/main.py`" |
| 验收脚本本身假通过 | jonathanprocter/clinical-hud 最终报告："Both blocking issues were e2e judge false-passes"（scrutiny 第一轮查出） |
| 重跑覆盖上一轮报告，历史丢失 | clinical-hud："round 2 overwrote that file **in place** … the round-1 counts appear nowhere in it" |
| handoff 与 git 边界不对应 | gddp 取证：commit 缺失 5/7；"`result^..result` is the exact boundary of a commit object, **not necessarily the feature boundary**" |
| init.sh 不可执行导致 worker 首轮失败 | gddp：`discovered_issue` "init.sh not executable (permission denied on direct invocation)" |

### 7.3 社区批评

公开讨论很少。HN 发布帖（item 47182879）3 分、1 条评论，无批评内容。Reddit 未找到相关讨论。Developers Digest 评测（2026-06-10，无署名，无亲测）："Missions require Extra Usage to be enabled"；"if you have strict cost requirements and are on a Pro or Plus plan, it is possible to exhaust quota mid-Mission."。AaronAbuUsama 对"可推广到非代码任务"的质疑："the claim is made in marketing and unsupported in mechanism"，理由是 `services.yaml` 是 shell 命令、user-testing 驱动浏览器、Level 4 前提假设可运行的应用。

### 7.4 成本数据（全部官方）

- Slack clone：16.5 小时（编排 2.3%、实现 60.5%、验证 37.2%）；185 次 agent 运行（1 orchestrator + 12 子代理，63 workers，27 validators + 82 子代理）；778.5M tokens，其中 cache read 744.9M；38.8k 行，52.5% 是测试，语句覆盖 89.25%；实现轨迹中位 51 轮（p90 123），验证中位 30 轮（p90 37）。
- 分布：mission 中位时长约 2 小时，65% 超过 1 小时，37% 超过 4 小时，14% 超过 24 小时，最长 16 天；中位 token 用量是普通会话的 12 倍；速率约 45K tokens/分钟（Introducing Missions）。
- 路由文章（2026-08-24）："The median mission spans 423 turns over ten sessions and about twelve hours. Routing saves 37.8% of the complete mission cost against pricing every call at the frontier model's rate."；"our default validator comes from a different model family than our default implementer."
- gdal 研究：系统版 3.00B credits 对单 agent 216M（14 倍），196.9h 对 15.0h；花费分布 impl 97% / val 2% / orch 1%。

---

## 8. 与 MMW 的逐项对照表

MMW 侧的依据文件（均为 `/Users/cheuklapchan/multi-model-workflow/.worktrees/rainbowfish` 下相对路径）：`mmw-v2/upstream/skills/engineering/to-spec/SKILL.md`、`to-tickets/SKILL.md`、`implement/SKILL.md`、`code-review/references/session.md`、`code-review/references/spec-reviewer.md`、`mmw-v2/skills/verdict/SKILL.md`、`mmw-v2/skills/verify-ticket/references/{closeout,linting}.md`、`mmw-v2/skills/dispatch/references/{how-it-works,night}.md`、`mmw-v2/skills/dispatch/hosts.json`、`mmw-v2/skills/drive-target/references/runtime-environment.md`、`docs/contexts/tickets/CONTEXT.md`。

| # | Factory 机制 | 解决的问题 | MMW 现有对应物 | 差距 | 是否值得引入，怎样引入才符合 MMW 的设计意图 | 风险 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | orchestrator 不写代码，只维护共享状态 | 编排者上下文被实现细节占满 | 夜里 main agent 只跑 `advance`/`route`；但收口轮默认"fix it yourself"（`dispatch/references/night.md` `## 4. The closing pass` 第 4 步 "The default is to fix it, not to open a ticket."；ADR 0012） | MMW 有意让 main agent 修小 finding，这是省成本的取舍 | 不引入。MMW 的收口轮只在 frontier 空后才修，此时不再编排，上下文污染的代价低。保留现状 | — |
| 2 | 契约先于拆解（mission-level TDD） | 验收标准被已想好的实现带偏 | spec 的 `## User Stories`、`## Implementation Decisions`（to-spec）先于票；但可执行的 `CHECK:` 是 `to-tickets` 第 4 步在切票时逐票写的 | 没有 spec 层的"可执行断言清单"；断言与切票同一步产生，Factory 文章指出的"标准被拆解收窄"风险存在 | **值得**（见第 10 节第 1 条）：在 spec 与切票之间加"断言清单"而不是新文件格式，写进 spec 的 `## Testing Decisions` 下的编号断言，或 spec 评论；票的 AC 声明它完成哪条 | spec 变长；断言与 AC 双写可能漂移，需要 lint 核对 |
| 3 | `fulfills` 覆盖闸（每条断言恰被一个 feature 声明） | 漏做、重复做 | `to-tickets` 第 8 步读回检查；`verify-ticket --lint` 查 AC 形状、worker 标签、图可启动（`verify-ticket/references/linting.md` `## --lint on a batch`）。**没有**"spec 每条决定/故事被某张票覆盖"的机器检查（to-spec、to-tickets、linting.md 中搜 coverage/traceab 无结果） | 覆盖靠写票 agent 自觉与用户 quiz | **值得**，最高优先级。`--lint <spec>` 增加覆盖检查：每条断言 ID 恰被一张票的 AC 声明，或显式标注去向（review 轴 / reaction / reach 票），否则 ERROR | 判断型需求（to-tickets 第 4 步问题 2）无法变成命令，必须允许"去向=code review"，否则逼出假 CHECK |
| 4 | 契约对抗评审 ≥2 轮（按区域并行子代理 + 跨区域一个） | 断言清单表面完整实则漏项 | `to-tickets` 第 6 步 quiz 用户（粒度、依赖、grade）；`--lint` 查形状 | 没有独立会话专门找"漏掉的断言" | **值得**，与第 3 条合并：发布前起一个 fresh 会话（可用 `advisor` 或 reviewer 行的模型）只读 spec 与草拟断言，输出缺口；写票 agent 合并后再发布。不需要两轮硬性要求，按 spec 规模 | 增加白天成本；评审者可能灌水制造"缺口"，需要"引用 spec 原句"规则（与 `spec-reviewer.md` "A review finding with no quoted line is your opinion" 同一纪律） |
| 5 | 断言带显式失败条件与证据要求 | validator 为通过找理由 | 每条 AC 是 `CHECK:` + `EXPECT:`（成功专用行）+ `EVIDENCE:`（to-tickets 第 4 步）；判定由命令，不由模型 | MMW 更强：失败条件就是命令退出与 EXPECT 不匹配 | 不需要引入 | — |
| 6 | 每 feature 全新上下文 worker | 上下文稀释 | 每票一个独立会话 `dispatch.sh start`，worktree `.worktrees/issue-<n>`，只读票、Read first、Parent 指名的 spec 小节、CONTEXT.md（`implement/SKILL.md` 第 14 行） | 对等，且 MMW 的读取范围更收敛（只读 Parent 指名小节） | 不需要 | — |
| 7 | scrutiny：每 feature 独立复审，读 diff + **轨迹骨架** + 技能遵从 | 实现者自评偏差；技能与现实不符 | `code-review` 三轴（Standards/Spec/Tests），每票合并前一次，fresh 会话（`code-review/references/session.md`）；Spec 轴读已合入的兄弟票做组合审查（`spec-reviewer.md` "Read tickets already integrated into the base branch"） | MMW 不读 worker 轨迹；不检查"worker 是否按技能流程做"；没有"共享状态缺口"观察项 | **部分值得**：不读轨迹（成本高、轨迹格式因 host 而异，违背"技能对所有 host 同一文本"）；但给 review 加一类输出"toolbox observations"（技能文字与仓库事实不符、缺命令、缺已知坑），见第 10 节第 4 条 | 评审 prompt 变长；观察项噪声 |
| 8 | scrutiny 在里程碑末做（批量） | 省成本 | MMW 每票合并前审 | MMW 更早发现问题，不会在同一里程碑内把错误传给后续 feature | 不引入批量审；保留 | — |
| 9 | user-testing validator：里程碑末黑盒跑契约断言，含跨区流程 | 单 feature 各自绿、整体流程不通 | `verdict` 重跑本票 CHECK（`verdict/SKILL.md`）；夜后 `reverify` 在 `origin/<into>` 上重跑所有已落地票的 CHECK（`how-it-works.md` `## Reverify and summary`）；`journey.py` 整机旅程只在 contract 票和 owner 点名的票上（`to-tickets/SKILL.md` 第 38 行 "Journeys appear only on this ticket and on tickets the owner named."） | **没有批次级的跨票黑盒流程验证**。reverify 只重跑各票自己的断言，不测"票 A 的产物 + 票 B 的产物组成的用户流程" | **值得**（第 10 节第 2 条）：spec 声明跨票流程断言（Factory 的 VAL-CROSS），由一张"收口验证票"持有，blocked by 该流程涉及的所有票；在 frontier 最后由 fresh worker 用 journeys 跑；失败走现有 finding / ticket 路由 | 需要 `.mmw/target.json` 能起整机；无 UI 仓库无意义；旅程脚本本身不稳会制造假红（journey 负对照可缓解） |
| 10 | 验证不通过 → orchestrator 建 fix feature 置顶 → 同一 validator 重跑只验失败项 | 修复闭环 | worker 内：review in-ticket 一轮修（`implement/SKILL.md` 步骤 2）；verifier 失败无第二轮，`HANDOFF REQUIRED`（步骤 4 "One round is the cap"）；夜后 reverify 红 → `ticket.regressed` 进 triage | MMW 把失败交回人（早上 triage）而非夜里自动修到收敛；Factory 自动循环 2–4 轮 | **不整体引入**。MMW 的"一轮上限"是有意防无限循环（implement 步骤 4 原文）；Factory 的数据也显示 34% 的实现量是修复，成本高。可考虑：收口验证票（第 9 条）失败时允许 main agent 按 ADR 0012 四步规则开修复票并再跑一次收口验证，上限一轮 | 放开轮数会让夜里烧钱且可能不收敛 |
| 11 | 封存里程碑：验证通过后新改动必须进新里程碑再验证 | 验证后的"小改动"绕过验证 | 收口轮 main agent 自修的 finding 直接推 `origin/<into>`，只跑受影响测试，无 reviewer/verifier（`night.md` 收口轮 "The ones you fix" 三条规则）；之后 `reverify` 重跑各票 CHECK | 自修提交不经独立验证，靠 `git log` 早上审计 | **小幅值得**：在 `summary` 前强制 `reverify`（现在是"A reverify run in this checkout adds `Reverify:`"，可选），使每个自修提交至少被一次独立重跑覆盖 | 夜更长；reverify 覆盖的只是 CHECK，不覆盖 finding 本身 |
| 12 | 共享知识库 `.factory/library/`（扁平、按主题），worker 追加，validator 落事实性更新 | 每个 fresh worker 重新踩同样的坑 | **没有**。brief 缺口 A；`to-tickets/SKILL.md` 第 146 行只说工具技能"is improved in use, the change is made there at once" | 夜内学到的环境事实（怎么起、哪个测试不稳、verifier 修环境的办法）无处沉淀，兄弟票和并行 spec 读不到 | **值得**（第 10 节第 5 条）：单一写者整合，不让并行 worker 同写一个文件 | 知识过期；常驻注入膨胀（Factory 自己给 AGENTS.md 设 80,000 字符上限，`harness/agents-md.md`） |
| 13 | `services.yaml` 命令唯一来源，端口硬编码 | worker 猜命令、端口冲突 | `.mmw/target.json`：`start`/`stop`/`discover`/`checks`/`instance`，端口由 `lease.py` 分配（`drive-target/references/runtime-environment.md`） | **MMW 更强**：租约分端口，`stop` 语义有检查，身份校验 `instance_check`；Factory 端口硬编码只能串行跑 | 不引入 | — |
| 14 | `init.sh` 幂等、每个 worker 启动时跑 | 环境漂移 | `start` 幂等（runtime-environment.md "idempotent in both directions"） | 对等 | — | — |
| 15 | Mission Boundaries（端口段、禁区），越界就 return | worker 碰他人资源 | `## Owns`（允许写的文件）+ closeout 记录 `Outside Owns:`；`leaves_machine`；lease | MMW 在文件层更细；在"外部资源禁区"层靠 `leaves_machine` 声明 | 基本对等 | — |
| 16 | 结构化 handoff：`whatWasLeftUndone`、`verification.commandsRun`、`discoveredIssues`、`skillFeedback` | fresh 会话之间只靠文件传承 | 结束评论：`ALL MET`/`HANDOFF REQUIRED` 首行、`ABANDON:` 三类、`Counts:`、每条 AC 的 `EVIDENCE:`、`Decisions I made on my own`、`Outside Owns`、`skipped: [X], add when [Y]`、`Sub-issues opened:`；由 `--closeout` 逐条机器核对（`verify-ticket/references/closeout.md` "What `--closeout` reads the draft against"） | MMW 在"做了什么、证据"上远强于 Factory（机器核对、绑定 commit）；缺 `skillFeedback`（是否按技能流程、哪里偏离、建议怎么改）和"学到的环境事实" | **值得补两个字段**（第 10 节第 4 条） | 自述字段容易被填成套话 "followedProcedure: true" |
| 17 | handoff 事项不处理就不能继续（`DismissHandoffItems`，理由 ≥20 字、"low priority" 不算理由） | 发现的问题被静默丢弃 | `discoveredIssues` 的对应物是 `--sub-issue finding/deferred/contract/decision/fault`，每个都是 tracker 上的 issue；`summary` 在有未路由 finding 时拒绝（`how-it-works.md` "`summary` refuses, with nothing posted …"） | 对等，MMW 更硬（issue 实体 + 事件计数）。但只有 `finding` 被 summary 强制路由，`deferred`、`contract` 留给早上 triage | 不需要引入 | — |
| 18 | 需求变更传播："every file that states the old truth must be updated … before workers resume"，契约由子代理改，最后原子提交 | 共享文件互相矛盾 | spec 可原地修订，原因写一条评论，"Tickets already cut from the section are checked against the new text and corrected where they no longer match."（`to-spec/SKILL.md` 第 32 行）；但 `docs/contexts/tickets/CONTEXT.md` 第 74 行："Its **ticket body** is the sections, not edited once the batch has been reported to the user as published" | **两份文件有张力**：spec 改了，已发布的票体按 CONTEXT 不能改，按 to-spec 要改；夜里改 spec 时，正在跑的 worker 不会被告知（relay 只把票事件变成唤醒，`how-it-works.md` "Results, watches and wakes"） | **值得**，中优先级：定义 `spec.revised` 事件（由脚本写，含改动的小节号）；relay 唤醒 Parent 指向这些小节的活 worker；`advance` 暂不派发受影响且未重新 lint 的票。票体不改的规则保留，改为"开新票 + 旧票 retract"或"在票上发一条带事件的更正"，二者择一需要 owner 定 | 夜里改 spec 本就少见，机制可能很少触发；定错规则会让票体与 spec 长期不一致 |
| 19 | 已知的无关老问题写进 AGENTS.md "Known Pre-Existing Issues (Do Not Fix)" | 后续 worker/validator 重复排查 | 无对应；worker 遇到只能开 `fault`（流水线坏）或 `deferred`（票外改动） | 不稳定测试、无关红测没有"已知，不修"的共享登记 | **值得**，并入第 12 条的知识库作为一个主题文件 | 被滥用成"把红测标已知来绕过"；需要登记者不是受益者（由 verifier/reviewer 登记而非 worker） |
| 20 | 顶层串行，只并行只读操作 | 并行 agent 互相覆盖、重复、架构不一致 | `advance` "starts every frontier ticket"（`how-it-works.md` `## How advance processes a batch` 末段）；冲突由 `## Owns` 不重叠 + `Blocked by` 预防，合并冲突 → `ticket.bounced`；`--lint` 的 linting.md 未列 Owns 重叠检查，verify-ticket.py 里无 overlap 逻辑（grep 结果为空）；跨并行 spec 无检查（brief 已识别）；用户记忆里 #748/#750/#751 同文件并行导致 bounce | MMW 选择并行换吞吐，冲突预防靠写票 agent 自觉 | **值得**（第 10 节第 3 条）：把 Owns 重叠变成机器检查，覆盖同一仓库所有已 open 的 night；重叠即自动串行（等价于加 blocked-by 边或 advance 不同时派发） | 过度保守会让夜里退化成串行；glob 与"(new)"路径的重叠判断有误报 |
| 21 | 验证与实现用不同模型家族 | 同源模型共享盲点 | `hosts.json` 默认：junior-worker grok、senior-worker codex gpt 5.6 sol、reviewer claude opus 5、verifier claude sonnet 5 | 对等，已经做到 | 不需要 | — |
| 22 | validator 不看代码（user-testing），"the wall"：实现者看不到验收用例 | 实现者针对可见样本过拟合 | worker 自己跑全部 CHECK（`implement/SKILL.md` 步骤 1），verifier 重跑同一批 CHECK | MMW 的 CHECK 对 worker 完全可见 | **暂不引入到票层**：MMW 票的 CHECK 是精确的规格，不是对行为空间的稀疏抽样，可见是设计意图（ADR 0008 要求闸口点名事实）。可在第 9 条的收口验证票上试"持有者不是实现者"：流程断言由 spec 写、只由收口验证 worker 跑 | 若在票层隐藏 CHECK，worker 无法自测，返工反而增多 |
| 23 | Mission Control：进度、预算、每个 worker 的输出 | owner 远程掌握 | 本地 task board（`mmw-v2/board/`）；`status`；`NIGHT SUMMARY` | 对等（未深入比较 board 功能） | — | — |
| 24 | 状态全在磁盘，随时暂停/恢复 | 长任务中断 | 票状态是评论事件的 fold（ADR 0019），worker 丢失由 watchdog 写 `worker.lost`，`start` 在原 worktree 接续并提交 `wip(#<n>)` | **MMW 更强**：事件由脚本写、带 commit，Factory 的 `features.json`/`state.json` 是可变快照，handoff 无 attempt id（gddp 取证） | 不需要 | — |
| 25 | 每个 worker 在 main 上顺序提交 | 串行下无需合并 | 每票独立分支，`advance` 在 `.worktrees/merge-<into>` 里 fetch→merge→checks→ff push，冲突或红检查 → `ticket.bounced`（ADR 0023） | **MMW 更强**：合并前跑仓库检查，base branch 不会被坏提交污染 | 不需要 | — |
| 26 | 计划期实测事实，并标注哪些会过期（"Already verified during planning"） | worker 基于过期假设实现 | wayfinder 决策票、research 文件作为 Read first 的 baseline | MMW 没有"会过期"的标注，baseline 被当作合同 | **小幅值得**：to-spec 的 `## Sources` 条目可加"验证日期/会过期"标记；低成本 | 标注本身过期无人更新 |
| 27 | 按 feature 选 worker 技能（orchestrator 为每个 mission 写专用 worker SKILL） | 通用 worker 不懂本任务流程 | 技能跨项目共用（`implement` 等），票上只有 junior/senior 两个 grade | MMW 不为每批生成专用技能 | **不引入**。MMW 的 AGENTS.md 规定技能是交付物、对所有 host 同一文本；每批生成技能会让技能不可复用、不可审计。weklund 的实物也显示 mission 专用技能会与仓库事实脱节 | — |
| 28 | 按角色估算成本 `#features + 2·#milestones` | 事前知道花多少 | 未找到 MMW 的成本估算 | 缺 | 可选：`NIGHT SUMMARY` 加各角色 token/时长（需要 runner 能报用量，未核实各 runner 是否支持） | 数据不全时误导 |

---

## 9. MMW 已经做得更好的地方

1. **判定由命令而不由模型**。MMW 每条 AC 是 `CHECK:`/`EXPECT:`，`--closeout` 逐条核对证据、计数、verdict 覆盖的 commit 必须等于 `HEAD`（`verify-ticket/references/closeout.md`）。Factory 的 user-testing 结论是 LLM 读截图和网络记录给出的 pass/fail，实物里出现过验收脚本假通过（clinical-hud "judge false-passes"）。
2. **状态可审计**。MMW 票状态是脚本写的事件 fold（ADR 0019），模型手打的 `VERDICT` 不算。Factory 的 handoff 是 worker 自述 JSON，gddp 取证 7 份里 5 份没有 commit，无 base SHA，无 attempt 标识。
3. **合并在分支上做，先检查后推送**（ADR 0023）。Factory 顶层串行在同一分支上直接提交，没有合并前闸口。
4. **每票合并前独立 review 和 verify**。Factory 的 scrutiny/user-testing 在里程碑末才跑，里程碑内的错误会被后续 feature 继承；它自己的数据是首轮验证 0/6 通过。
5. **运行时隔离**。`lease.py` 分端口和数据目录，`stop` 有"端口不再应答"的检查，产品实例有身份校验（`runtime-environment.md`）。Factory 的 services.yaml 要求端口硬编码，这是它只能串行跑验证的原因之一。
6. **不许轮询、watchdog 判活**（ADR 0010、0021）。Factory 到 2026-08 还在修"睡眠后 worker 卡死"。
7. **失败有上限、交回人**。verifier 一轮上限（`implement/SKILL.md` 步骤 4），避免 Factory 那种 34% 实现量用于修复、轮数不封顶的成本曲线。
8. **验证者默认异族模型**已经配置（`hosts.json`），Factory 在路由文章里才把这写成默认。
9. **finding 路由有规则**（ADR 0012 四步），Factory 的 `DismissHandoffItems` 只要求理由不少于 20 字符。

---

## 10. 最值得 MMW 采纳的 5 条

### 第 1 条：spec 层断言清单 + 覆盖闸 + 发布前独立找漏

**做法**：`to-spec` 在 `## Testing Decisions` 下写编号的行为断言（ID 稳定、每条带"何时算失败"）；`to-tickets` 写 AC 时标注它完成哪条断言（Factory `fulfills` 的"completes, not contributes to"语义）；判断型、反应型、触达型需求在清单里标注去向（code review 的哪个轴 / reaction 票 / reach 票），与 `to-tickets` 第 4 步的五问一一对应。`verify-ticket --lint <spec>` 增加检查：每条断言恰被一个去向认领，无孤儿、无重复，否则 ERROR。发布前起一个 fresh 会话只读 spec 与断言清单，按"引用 spec 原句"的纪律列出缺口。

**解决的问题**：Factory gdal 实验里单 agent 在 36% 处"自认完成"停下；MMW 当前靠写票 agent 与用户 quiz 保证覆盖，spec 里的一条决定没有任何票的 AC 对应时，夜里所有闸口都会是绿的（ADR 0008 说的"靠什么都不做通过"在批次层成立）。

**前提**：spec 的 Implementation Decisions 与断言编号在发布后稳定（to-spec 原地修订规则已保证编号不变）；lint 能从票体解析出"完成哪条断言"的字段。

**失效场景**：spec 主要是判断型要求（架构重构、文档类），断言大多去向 review，覆盖闸退化成形式检查；写票 agent 为了通过闸口把一条断言硬塞给一张不真正完成它的票（Factory 用"leaf feature that makes an assertion fully testable"防这一点，MMW 需要 review 的 Spec 轴读到该声明并判断）。

### 第 2 条：批次级跨票黑盒验证（收口验证票）

**做法**：spec 的断言清单里区分"单票断言"和"跨票流程断言"（Factory 的 VAL-CROSS：首访流程、经真实导航可达、跨功能状态保持）。`to-tickets` 为跨票流程断言切一张验证票，`Blocked by` 流程涉及的所有票，`## Owns` 只含 `.mmw/journeys/<flow>/` 与其测试目录，AC 是 `journey.py run <flow>`。它自然在 frontier 最后被派发，由 fresh worker 在已合并的 base branch 上跑。失败时 worker 按现有规则 `ABANDON`/开 finding，收口轮按 ADR 0012 路由。

**解决的问题**：MMW 的 `reverify` 只重跑各票自己的 CHECK，`spec-reviewer.md` 的组合审查是读代码不是跑产品；"每张票绿、流程不通"目前只能早上由人发现。Factory 的数据显示 user-testing 是发现问题最多的环节（Slack clone 验证占 37.2% 时长）。

**前提**：仓库的 `.mmw/target.json` 通过 `screen_driver.py target --check`，能在 lease 下起整机并登录；journeys 带负对照（`drive-target/references/journey.md` 已要求）。

**失效场景**：无可运行界面的仓库（MMW 自身就是一例：脚本与技能文本）；旅程脚本不稳导致假红，占用早上 triage；流程涉及的票有一张被 bounce，验证票永远不被派发（需要在 `NIGHT SUMMARY` 的 "Not dispatched, a blocker stayed open" 里看到它）。

### 第 3 条：`## Owns` 重叠的机器检查，覆盖同仓库所有已 open 的夜，重叠即串行

**做法**：`verify-ticket --lint` 在 batch 图检查里加 Owns 重叠检查（同一 frontier 上两张票的 glob 相交即 ERROR，提示加 `Blocked by`）。`dispatch.sh advance` 派发前读同仓库其他已 open watch 的活票 Owns（relay 已有 `overlap()` 用来检查 watch 之间是否共享票，`mmw-v2/skills/dispatch/scripts/relay.py` 第 449 行，可参考），与待派发票相交时本轮不派发，并在 stderr 点名占用它的票（沿用 `how-it-works.md` "When no ticket can start … stderr names each condition" 的格式）。

**解决的问题**：用户记忆里 #748、#750、#751 同文件并行导致 bounce；Factory 演讲给出的理由是并行 agent "step on each other's changes"，它的解法是全串行。MMW 保留并行，但把"同文件"这一类冲突变成确定性的串行，而不是依赖写票 agent 读回时肉眼检查（`to-tickets/SKILL.md` 第 146 行）。

**前提**：票的 `## Owns` 足够准确（implement 已要求 worker 开工前核对 Owns，closeout 记录 Outside Owns）。

**失效场景**：Owns 写得过宽（整目录 glob），检查把本可并行的票串起来，夜变慢；冲突发生在 Owns 之外（worker 写了 Outside Owns 的文件），检查看不到——这类冲突仍由 `advance` 合并时 bounce 兜底。

### 第 4 条：结束评论补 `skillFeedback` 与"环境事实"两个字段，review 补"toolbox observations"，收口轮汇总

**做法**：`--draft` 生成的骨架加两节：`Procedure deviations`（按技能哪一步没做、做了什么、为什么，对应 Factory `skillFeedback.deviations`）和 `What I learned about this repository`（起产品、测试、环境的事实）。`code-review` 的会话报告加 `## Toolbox observations`（技能文字与仓库事实不符、worker 用了没有登记的命令）。`summary` 把本夜所有票的这两类条目汇成一条 spec 评论，作为跨夜 retro 的输入。

**解决的问题**：brief 指出的"没有跨夜 retro 从结果改进技能"。weklund 的实物说明，这类反馈如果只写在报告里、不强制处理，会在多个里程碑重复出现而无人修；所以汇总要落到一个会被人看的地方（NIGHT SUMMARY 或 triage 队列），而不是只留在票上。

**前提**：closeout 只检查两节存在（允许写 `None`），不检查内容，避免逼出套话；汇总由脚本做，不靠 main agent 记忆。

**失效场景**：worker 一律写 `None`（Factory 实物里也有 `followedProcedure` 与转录不符需要 scrutiny 去核对的情况）；汇总条目太多，owner 不读。缓解：只汇总被两张以上票重复报告的条目（Factory 的 `isSystemic` 判据）。

### 第 5 条：仓库级运行知识库，单一写者整合

**做法**：在 `.mmw/` 下加一个扁平、按主题的知识目录（例如 `environment.md`、`flaky-and-known-failures.md`），每个文件头写"放什么、不放什么"（Factory library 的做法）。写入分两层，沿用 Factory 的权限分层但换成 MMW 的并行模型：worker/verifier/reviewer 不直接改文件，只在各自事件或结束评论的"环境事实"节里提交条目（第 4 条）；收口轮由 main agent（夜里唯一串行的角色）去重合并，作为一个普通提交走 `origin/<into>`，受第 11 行"reverify 前置"约束。`implement` 的读入清单加上这个目录；verifier 修环境的办法（`verdict/SKILL.md` "The environment is yours"）首先写进这里。"已知不修的失败"只能由 verifier 或 reviewer 提交，不能由受益的 worker 提交。

**解决的问题**：brief 缺口 A（夜内学到的操作性知识无处沉淀，兄弟票、并行 spec 读不到）；Factory 的 `library/user-testing.md` 与 "Known Pre-Existing Issues" 正是为此。

**前提**：先查 ADR 0001（tracker 与仓库文件的权威归属）是否允许运行知识放仓库文件——运行知识描述的是仓库本身的事实，推断属于仓库权威，但我未读 ADR 0001 正文，未验证；知识条目带发现日期与来源票号，便于判断过期。

**失效场景**：同一夜内并行的票读不到本夜新知识（只有下一夜或收口轮后才生效）——若要夜内生效，需要 relay 广播，这会触碰"agent 之间只靠票事件唤醒"的边界，建议不做；知识过期无人删，变成误导；目录被当成堆放区，读入成本上涨（Factory 给 AGENTS.md 设 80,000 字符上限，MMW 需要类似的上限并由 lint 检查）。

**第 6 名（未进前五）**：spec 夜间修订的传播（表第 18 行）。价值真实，但触发频率低，且需要 owner 先裁定"票体不改"与"票按新 spec 更正"两条规则如何并存，这是产品规则层面的决定。

---

## 11. 未找到 / 未验证

- `mission-planning`、`define-mission-skills`、`mission-worker-base`、`scrutiny-validator`、`user-testing-validator` 五个内置技能正文：未找到。
- feature 重试上限的具体数值：未找到。
- 契约评审"至少两轮"在当前版本是否仍是硬要求：只有 3 月抓包与 AaronAbuUsama 看到的 `contract-work/review-pass-{1,2}-*.md` 目录，未核实当前版本。
- Factory 2.0 博文"parallel tracks"与演讲"serial"的矛盾：未找到解释。
- `droid exec --mission` 是否需要 `--auto high`：`autonomy-and-safety/specification-mode.md` 示例写 `droid exec --mission --auto high`，reference.md 示例未带，未验证是否必需。
- `InspectMissionReadiness` 的具体行为：只见名字。
- Factory 的长时任务完成率、返工率的统计口径：除 Slack clone 单例和 ProgramBench 24 任务外，未找到。
- MMW 侧：ADR 0001 正文、ADR 0012 正文、`task-board` 功能、各 runner 是否能报 token 用量，均未读，未核实。

## 12. 读过的来源

官方：
- https://factory.ai/news/missions-architecture （Theo Luan，2026-04-10，全文）
- https://factory.ai/news/missions （页面日期显示 2025-02-26，但文中引用 Opus 4.6 且 CLI changelog 2026-02-26 同日出现 Missions 条目，推断实际为 2026-02-26）
- https://factory.ai/news/what-it-takes-for-coding-agents-to-complete-large-software-tasks （2026-08-27）
- https://factory.ai/news/model-routing-belongs-in-the-harness （2026-08-24）
- https://factory.ai/news/software-factory （2026-06-15）
- https://docs.factory.ai/llms.txt
- https://docs.factory.ai/missions/overview.md 、planning.md 、running-cli.md 、running-app.md 、reference.md
- https://docs.factory.ai/autonomy-and-safety/specification-mode.md
- https://docs.factory.ai/harness/agents-md.md 、hooks.md 、skills.md 、subagents.md
- https://docs.factory.ai/droid-exec/overview.md
- https://docs.factory.ai/software-factory/droid-control.md
- https://docs.factory.ai/changelog/release-notes.md （按 mission 关键词检索）
- https://www.youtube.com/watch?v=ow1we5PzK-o （Luke Alvoeiro，AI Engineer，上传 2026-05-06，自动字幕全文）

非官方：
- https://gist.github.com/V1ki/356b121038722ebf32b5aac85482c113 （全文精读）
- https://github.com/skchaudr/gddp-runtime/blob/HEAD/docs/archive/mission-mode-research/02-factory-forensics.md 、06-post-mission-code-review.md ，及 `probe2-raw/A/mission-dir-immediate-snapshot/` 下 `library/user-testing.md`、`worker-transcripts.jsonl`
- https://github.com/AaronAbuUsama/agentic-whatsapp/blob/HEAD/docs/research/missions.md
- https://github.com/jellydn/my-ai-tools/blob/HEAD/configs/factory/droids/scrutiny-feature-reviewer.md 、user-testing-flow-validator.md
- https://github.com/weklund/mlx-stack/tree/HEAD/.factory/validation （ops round1 synthesis、lifecycle synthesis、一份 review）
- https://github.com/CorrectRoadH/OpenTickly/blob/HEAD/.factory/skills/tracking-backend-worker/SKILL.md
- https://github.com/howardwu1/whodo/blob/HEAD/.missions/security-hardening/AGENTS.md
- https://github.com/jonathanprocter/clinical-hud/blob/HEAD/docs/final-mission-report.md （检索片段）
- https://github.com/repr0bated/operation-dbus-proto/blob/HEAD/.mission-planning/HANDOFF.md
- https://github.com/prikotov/task-orchestrator/blob/main/docs/research/framework-comparisons/missions-framework-comparison.md （结构扫读）
- https://news.ycombinator.com/item?id=47182879
- https://www.developersdigest.tech/blog/factory-droid-review-setup-2026

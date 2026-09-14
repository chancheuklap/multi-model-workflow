# 知识的采集、审阅、提升、检索与防陈旧：monomind project-context、Devin、Augment 深挖，及对 MMW 与 Nowledge Mem 的映射（2026-09-13）

## 0. 范围、方法、可信度

- 对象：monomind-ai-lab/project-context（含上轮没发现的姊妹仓库 monomind-ai-lab/project-hub）、Devin（Cognition）、Augment Code。关注点是知识如何被采集、审阅、提升、检索、防陈旧、跨会话与跨仓库复用，以及这些机制能否放进 Nowledge Mem。
- 方法：
  - monomind 两个仓库克隆到 `scratchpad/r8mono.iu7f/`，只读源码与设计文档，未运行脚本（第 1 节，本人亲读）。
  - Devin 与 Augment 各派一个只读调研子 agent 抓官方文档与博客，完整笔记在 `notes/devin-notes.md`（408 行）与 `notes/augment-notes.md`（363 行）。第 2、3 节是从中挑出的、对 MMW 有用的部分。我抽查了 8 条关键引语，用 curl 取原页核对，全部与原文一致（Augment `cosmos/experts-memory.md` 的 "flags discrepancies" 与 "Noisy memory"，`experts-code-review-memory.md` 的 "Explicit human feedback carries more weight"；Devin `session-insights.md` 的 "Misleading Knowledge"；Cognition `multi-agents-working` 的四句；Augment 指南的 "undiscoverable" "same mistake twice"）。子 agent 标注的一处方法限制：augmentcode.com 的 guides/blog 页经 WebFetch 转述，只保留短句引语。
  - Nowledge Mem 能力取自本机 `nmem --help` 与各子命令 help 的输出（`scratchpad/nm/help1.txt`、`help2.txt`，本会话前一轮采集，我读过）、一份 context bundle 样本（`scratchpad/nm/ctx.txt`）和 `scratchpad/nm/openapi.json` 里的 `MemoryCreateRequest` schema。没有写入任何 memory。
  - MMW 只读：`docs/adr/README.md`、`CONTEXT-MAP.md`、`docs/contexts/{tickets,ticket-run,night,toolbox}/CONTEXT.md` 的相关词条、`mmw-v2/upstream/skills/engineering/implement/SKILL.md`、`code-review/SKILL.md`、`to-tickets/SKILL.md` L95-110 与 L146、`mmw-v2/skills/manage-agents-md/references/incremental.md`、`mmw-v2/skills/dispatch/scripts/relay.py` 的 `overlap`（L449 起）、`mmw-v2/install.sh` 里 nowledge-mem 相关段（L1619-1698）。未改任何文件。
- 标注约定：每条事实带 URL 或固定链接与英文短引语；"推断"是我从已读内容推出的；"未找到"是查过没有。

## 0.1 一句话结论

三家给出的共同答案是：**采集要便宜且带出处，提升要经人且去处固定，检索按"要改的文件/范围"取而非全量加载，陈旧靠"加载时核对"而非过期删除**。MMW 在"事件、闸口、独立验证、评审与编码分离"上已经比三家都严格；它缺的正好是这四件事中的前三件半——一夜里学到的东西没有采集点、没有提升通道、没有按文件取回的检索、没有出处锚。Nowledge Mem 适合承担"采集箱 + 检索 + 人审队列"，不适合承担任何状态或闸口；提升后的规则仍应落在仓库文件里，经票进入。

## 1. monomind-ai-lab/project-context 与 project-hub（源码级，已读）

### 1.0 读了什么、版本、可信度

- 克隆到 `mktemp -d` 目录 `scratchpad/r8mono.iu7f/`，未运行任何脚本。
- `project-context` 提交 `72a0a22640f4577eddd615c6bd3a4dad2a6473b9`（2026-09-10），GitHub 上 3 stars（`gh api` 读到）。链接前缀 `M=https://github.com/monomind-ai-lab/project-context/blob/72a0a22640f4577eddd615c6bd3a4dad2a6473b9/`。
- 上轮没发现的第二个仓库 `monomind-ai-lab/project-hub`，提交 `5b2d92cb42215d19fa72dc96a5e897c45efe5bbd`（2026-09-05），1 star。Hub 的 push/pull 实现在这里，不在 project-context 里。链接前缀 `H=https://github.com/monomind-ai-lab/project-hub/blob/5b2d92cb42215d19fa72dc96a5e897c45efe5bbd/`。
- 全文读过：`planning/project-context-design.md`（1039 行）、`planning/record-model-v1.md`、`planning/project-context-handoff-2026-09-03.md`、`docs/archive/context-hub-architecture.md`、`skills/project-context/SKILL.md`、`scripts/context_packet.py`、`context_capture.py`、`context_review.py`、`context_triggers.py`；`context_doctor.py` 读了 `verify_anchors`（L444-537）并按 issue code 列表浏览全文；`src/project_context_cli/__init__.py`（只是转发到 init 脚本的 48 行壳）；记录模板（decisions/questions/inbox/LEARNINGS/DECISIONS）；project-hub 的 `skills/project-hub/SKILL.md`、`docs/CLI.md`、`guides/authored-and-pushed.md`、`.project-hub.json`、`global/skills/README.md`、`templates/global/SKILL.md`；`project_hub.py`（1736 行）只按关键字定位，未通读。未读：`project_context_init.py`（1741 行，安装器）、`web/`、tests。
- 成熟度：3 stars / 1 star，作者自用，设计文档是 2026-09-02~03 两天内由 Claude 会话写成，多处"v2 再做"。它的价值在"设计理由写得清楚、代码与设计一致"，不在"被大量用户验证过"。

### 1.1 记录模型

- 目录：`project-context/` 下 `NOW.md`、`PLAN.md`、`DECISIONS.md`+`decisions/`、`LEARNINGS.md`、`QUESTIONS.md`+`questions/`、`tasks/`、`inbox/`、`indexes/`（派生）；Hub 推下来的 `global/`、`blueprint/` 只读；`sessions/` 永不进 git。(M/planning/record-model-v1.md §5)
- 明细记录 frontmatter 只有 6 个必填键："`id` … `kind` … `status` … `title` … `created` … `asserted_by`"，"Six, not eight. Eight is the ceiling, not the target"。可选键：`approved_by, supersedes, superseded_by, evidence, files, valid_at, invalid_at, session, harness, model`。(M/planning/record-model-v1.md §2 L28-55)
- 每种 kind 一套状态词，doctor 按 kind 校验，不接受别的 kind 的词："a question is not an assertion and a task is not a claim, so forcing all three through one set of words was the error"。decision/learning/capsule：`proposed → accepted → superseded | rejected`；question：`open → answered → superseded`；task：`proposed → active → done | dropped`。(同上 §3 L63-81)
- 引用语法（按形状校验，不解析）：`session:<harness>:<id>`、`commit:<binding>:<sha>`、`pr:<binding>#<number>`、`review:<binding>#<pr>/<comment-id>`、`ticket:<tracker>:<key>`、`doc:<binding>:<path>@<commit>`、`url:…`、`capsule:<id>`、`hub:<hub-id>@<commit>`。(同上 §4)
- 证据锚：正文里写 `path/to/file@<commit>`，doctor 用 `git diff --quiet <commit> HEAD -- <path>` 判断文件自引用后是否变过，变了报 `evidence-drift`（warning），文件没了也报，commit 不在本地（浅克隆）报 `evidence-unverifiable`。原话："A link that still resolves proves the cited file exists, not that it still says what it said when it was cited. Pinning the commit makes the citation falsifiable"。(M/skills/project-context/scripts/context_doctor.py L456-537)
- 处理漂移的规定动作："Re-read the evidence, then either re-anchor the entry to the current commit or supersede it."(M/skills/project-context/SKILL.md L118-122)
- `asserted_by` / `approved_by` 用 `person:<name>` 或 `agent:<name>`；doctor 有 `agent-self-approval` 错误："`approved_by` may not equal `asserted_by` for an agent actor"。(M/planning/project-context-design.md L688-690；context_doctor.py L765)
- 冲突解决只能"取代"不能"改写"："Supersede it, never rewrite its meaning"；"Never edit the old statement into agreement with the new one — what it said, and why, is the evidence for the reversal."(SKILL.md L55-56, L79-82)

### 1.2 触发条件、ack 与 commit 绑定

- 核心原则："Update a document when its trigger fires — not when someone asks for an update."(SKILL.md L43)
- 三类触发写成可判断的条件清单：NOW.md 是"the state a next contributor would act on changed"；DECISIONS.md 是"a choice now constrains future work"（含 "a rule that would have prevented a review finding" 归 LEARNINGS）；LEARNINGS.md 是"evidence changed what is believed, and it will recur … Evidence is required, and it must apply beyond this one task."(SKILL.md L47-62)
- 脚本只判"窗口"不判"内容"：`context_triggers.py` 看 `git log <最后一次改 project-context/ 的 commit>..HEAD`（排除 `project-context/` 自身）与未提交路径，有就说窗口开着；"Deciding which documents actually fire is the agent's job"。(context_triggers.py L1-8, L147-155)
- `ack` 绑定当时的 HEAD 和当时见过的脏路径集合："It stays valid only while that claim is still about the same work. A new commit moves HEAD and reopens the window; uncommitted work the ack never saw reopens it too."(context_triggers.py L185-199)
- Stop 钩子每个会话最多拦一次，"blocks at most once per session so it can never loop"；找不到仓库时明确说"this is a wiring problem, not a clean bill of health"。(context_triggers.py L12-13, L353-361, L433-434)
- 钩子只装进 Claude Code 的 `.claude/settings.json`（`--install-hooks`），其他宿主靠 AGENTS.md 受管区块里一句"先跑命令"。(M/skills/project-context-init/SKILL.md L191-193；design L625-628)
- 状态文件放 `.git/` 下而不是工作树，理由："every honest `ack` a tracked file change — the exact noise the trigger check exists to keep out"。(context_triggers.py L227-236)

### 1.3 capture → inbox → promote

- 采集要便宜："Capture has to be cheap enough to happen *during* the work, or it does not happen at all."；判断推迟："The judgement — is this a decision, a learning, or nothing — is deferred to promotion, where it is cheap."(M/skills/project-context/scripts/context_capture.py L4-10)
- capsule：≤200 词（超了拒绝，"Anything longer is the record it should become"）；`--kind decision|learning|question|assumption|constraint|proposal`；自动带 `commit:<binding>:<HEAD>` 作证据；`--actor agent:<name> --session --harness --model`；id 是 `C-<日期>-<正文 sha256 前 6 位>`，同一天同一段文字只写一次，"a `Stop` hook that fires twice should not leave two identical capsules"。(context_capture.py L42-47, L89-119, L158-164)
- 未知字段不写 "unknown"："a field carrying the string "unknown" is a claim that reads like a value"。(L93-95)
- 提升没有脚本，是手工动作：写对应 registry 条目，把 capsule 的 `status` 改成 `accepted` 并链接去处，或 `rejected`；"Leaving it `proposed` is the only outcome that is not a resolution."(SKILL.md L220-223)
- 积压靠 `context_review.py` 按"年龄"排序报告：`unpromoted-capsule`、`proposed-record`、超过 14 天的 `open-question`、`unconfirmed-assumption`、`evidence-drift`、`stale-current-state`、90 天未刷新的 `stale-snapshot`。永不以非零退出："a backlog is not a build failure, and CI that breaks on one teaches people to stop filing questions."(M/skills/project-context/scripts/context_review.py L1-31, L59-76)

### 1.4 检索（context packet）

- 故意笨："a path-prefix comparison and a token overlap … There are no embeddings and no index to keep warm, because the signal that actually decides relevance is already written down — a decision cites the files it constrains, and the task names the files it touches."(M/skills/project-context/scripts/context_packet.py L4-9)
- 顺序：global 的 SUMMARY/IDENTITY/GUARDRAILS → blueprint 的 EPIC（plan/review 模式加 ARCHITECTURE）→ NOW → PLAN 活跃项 → 与 `--files` 共享路径前缀的已接受记录（得分 +10）→ 仅词汇重叠的记录 → 匹配的 global skills/shared。(L52-61, L309-388)
- 只加载 `accepted/answered/done/active`，`proposed` 只列链接；预算 4000 token（字符数/4 估算）；超预算的不丢弃，列成链接："the packet never implies that what it left out does not exist"。(L11-16, L70-73, L390-404)
- `--mode review --diff` 用工作树改动路径当 `--files`。(L239-261)
- 设计文档里的"Verified" 定义："only `accepted` / `approved` records are included by default"。(design L621-623)

### 1.5 决策冲突检测

- 两种信号：两条已接受决策的路径锚共享前缀（强信号，直接报）；词汇重叠需 ≥5 个共享词且占较小一方词汇 ≥25%（弱信号）。已由 supersede 链接关联的对不报。最多 25 对，其余计数不丢。(context_review.py L91-125, L331-360, L400-438)
- 明确承认只能给候选："It cannot tell that two decisions contradict — that is a semantic judgement and it stays with the person or agent reading them."(L16-22)
- 写新决策前的闸口 `--new-decision "<一句>" --new-decision-files <paths>`，结果只有两条出路：取代旧的，或在新决策里写明两者为何并存（"the boundary between them, or the condition that selects one over the other"）。(SKILL.md L64-91)
- 闸口没跑成时不许读起来像"无冲突"："so "no candidates" and "the check never ran" must not read the same. A silent all-clear from a broken install is worse than no check at all."(context_review.py L498-501, L553-560) —— 这与 MMW ADR 0008 同一原则。

### 1.6 跨仓库：Project Hub

- 两个产品一个记录模型：Project Context 在各项目仓库，Project Hub 是组织 owner 私有仓库，builder 对 Hub 连读权限都没有。"Every movement between them is initiated from the side that holds the right, and that side is almost always the Hub"。(design L229-244)
- `push`（Hub→仓库）走白名单：`.project-hub.json` 的 `push.global_include` 默认 `SUMMARY.md, GUARDRAILS.md, WORKFLOWS.md, skills/, shared/`；`IDENTITY.md` 在任何配置下都不推；`README.md` 与带 `<!-- project-hub:unfilled -->` 的种子文件跳过，"An empty guardrail in front of every agent is worse than none"。(H/.project-hub.json；H/docs/CLI.md L148-162)
- push 的闸：目标树必须干净；Hub 待发送部分有未提交改动则拒绝（"the stamp would name a commit that does not contain those bytes"）；超字数预算拒绝并点名文件（global 单文件 400 词、合计 2000、EPIC 600、ARCHITECTURE 1200）；在长寿 `hub-sync` 分支上提交，带 `Source-Commit:` `Project-Id:` trailer，推分支、开/更新 PR，"Merging stays a human act"。(H/docs/CLI.md L164-222；H/skills/project-hub/SKILL.md L62-73)
- 只读副本防篡改：推下去的每个文件 sha256 记在仓库 marker 的 `pushed` 里；仓库 doctor 发现 hash 不符报 `pushed-file-modified` 错误并点名 Hub；下一次 push 遇到被改过的副本整体拒绝："A copy that was edited where it landed is a conflict, not an overwrite."(M/planning/record-model-v1.md §6；H/skills/project-hub/SKILL.md L76-78)
- `pull`（仓库→Hub）只读仓库：用 `git ls-tree`/`git show` 读默认分支对象库，不碰工作树；白名单 authored set；写 `pulled/STAMP.json`（仓库、分支、commit、时间、每文件 sha256）。(H/docs/CLI.md L93-125)
- 反馈通道没有写回路径："They file a question or a `proposal` capsule in their own repo, and it reaches the owner at the next `/hub-pull` … Its one weak point is latency — nothing moves until the owner pulls"。(design L579-587；H/guides/authored-and-pushed.md)
- 两个高度的计划：`blueprint/EPIC.md`（owner）与 `PLAN.md`（builder），每个 PLAN 里程碑必须有 `- Serves: E-00N`，无 Serves 是 error，EPIC 项无人服务只是 warning。(record-model-v1 §7)
- 跨项目检索只在 Hub 侧："A builder's packet sees only this project and the global snapshot, which is the correct blast radius"。(design L614-619)
- 技能演进作为全局记录：`global/skills/<name>.md` 带 `Version`、`Learned from: capsule:<id>, doc:…@<commit>`；"An agent may propose a change to a skill; it may never approve, activate, or retire its own."(H/global/skills/README.md；H/templates/global/SKILL.md) 只有模板和规则，没有代码实现（`grep` 未找到相关逻辑）。
- 被放弃的上一代（Context Hub）：存原始会话 transcript 被判为错误，"Git cannot purge committed history, so the current default makes an honest purge impossible"；改为"sessions local, capsules only"(D1)。(design L150-155, L993-995)

### 1.7 对 MMW 的判断（推断）

- monomind 的强项全在"一个仓库里、单一时间线上的人+agent 连续性"；它没有并发多 agent、没有事件、没有消息，跨仓库也是 owner 手动 push/pull。MMW 的票事件 fold、relay、闸口远比它的"协作"部分成熟。
- 真正可借的是四个小机制：证据锚 `path@commit` + 漂移检测；capture 与 promote 分两步且 capture 带自动 provenance；按"窗口"而非"内容"触发、ack 绑定 HEAD；写决策前的冲突候选闸（只给候选，出路二选一）。

---

## 2. Devin（Cognition）：对 MMW 有用的部分

完整笔记与 URL 清单：`notes/devin-notes.md`。

### 2.1 Knowledge：触发检索 + pin，但没有版本、过期、写入时冲突检测

- 检索方式："Devin retrieves Knowledge when relevant, not all at once or all at the beginning."；pin 到某仓库则"always used whenever Devin is working in that specific repo" — https://docs.devin.ai/product-guides/knowledge
- 条目字段（v3 API）：`name`、`body`、`trigger` 必填，另有 `folder_id`、`is_enabled`、`pinned_repo`；响应没有版本号、过期时间、来源字段 — https://docs.devin.ai/api-reference/v3/notes/post-organizations-knowledge-notes 。版本历史：未找到（playbook 有，knowledge 没有）。
- 使用可审计："Devin will tell you in a session what Knowledge it used; you can see this under "Accessed Knowledge"" — https://docs.devin.ai/onboard-devin/knowledge-onboarding
- 建议来源是聊天反馈，人编辑后保存或丢弃，也会建议更新已有条目："Devin can also suggest updates to existing knowledge items in addition to suggesting new knowledge items." — https://docs.devin.ai/product-guides/knowledge 。2025-11-07 起 Devin 可在会话中直接写入知识库（"contribute knowledge base entries within the folder hierarchy during sessions"，https://docs.devin.ai/release-notes/2025 ），它与"建议—审批"的边界：未找到。
- 自动导入仓库规则文件（`.rules`、`.mdc`、`.cursorrules`、`CLAUDE.md`、`AGENTS.md`），同步时机：未找到。
- Organization → Enterprise 提升："Promotion requires enterprise knowledge management permissions, and is only available for user-created knowledge items" — https://docs.devin.ai/product-guides/knowledge
- 陈旧只能事后发现：Session Insights 的 "Misleading Knowledge" "lists knowledge items that led Devin astray or contained outdated or incorrect information"，原因之一 "Knowledge conflicts with other knowledge items"；API 字段 `note_usage.good_usages / bad_usages` — https://docs.devin.ai/product-guides/session-insights 。文档对后果的定性："a single outdated knowledge item can degrade session quality across your entire team."
- 维护是排出来的例行会话，顺序固定："Start with deduplication to reduce noise / Then resolve conflicts to ensure consistency / Finally, fill gaps" — https://docs.devin.ai/work-with-devin/advanced-capabilities

### 2.2 Session Insights：事后分析只出建议，不自动回写

- 触发："For large sessions (L or XL), a full analysis is also generated automatically at teardown"；L/XL "are flagged as unhealthy" — https://docs.devin.ai/product-guides/session-insights
- 输出：Issue Timeline（带影响等级）、Improved Prompt、Action Items，类型枚举 `machine_setup`、`repo_config`、`knowledge`、`prompt_improvement`、`external`、`other` — https://docs.devin.ai/api-reference/v3/sessions/get-organizations-session-insights
- 自动回写知识或 playbook：按文档是否，全部是"建议 + 跳转让人改"（笔记 §3）。

### 2.3 Playbooks：版本化，按成败对比改进

- "Each time you edit and save a playbook, a new version is created. You can view previous versions and revert" — https://docs.devin.ai/product-guides/creating-playbooks （2026-03-19 上线，同时显示每个 playbook 的会话数与 merged PR 数）
- 改进方式："Reference the playbook and share sessions where it fell short. Devin compares successes and failures to propose targeted improvements." — https://docs.devin.ai/work-with-devin/advanced-capabilities 。由用户发起，不是后台自动流程。
- Skills（2026-02 上线）会在会话中建议"创建或更新 skill"并给 "Create PR" 按钮写回仓库；"When it figures out a setup step the hard way, Devin can suggest saving that knowledge as a testing skill in the repo" — https://docs.devin.ai/product-guides/skills ；https://cognition.ai/blog/testing-development

### 2.4 "怎么起项目"放在 blueprint，不放在 Knowledge

- blueprint 的 `knowledge` 段 "Not executed. Loaded into Devin's context at session start."；分工："For architecture docs, conventions, and team workflows, use the standalone Knowledge feature instead." — https://docs.devin.ai/onboard-devin/environment/blueprints
- `post-build` "A non-zero exit code fails the build, so no snapshot ships without passing your checks"；约每 24 小时重建，可 pin 某次构建 — https://docs.devin.ai/onboard-devin/environment/blueprint-reference

### 2.5 Managed Devins：子会话不共享可写状态，Cognition 自列三条缺陷

- 每个 managed Devin 独立 VM；代码交接走 git 分支："It cannot see the orchestrating session's files, so code handoffs go through git branches" — https://docs.devin.ai/work-with-devin/dynamic-workflows
- 派发前人批准分组，分组准则是不冲突："Group them into independent work packages that won't conflict"，有依赖的串行 — https://docs.devin.ai/use-cases/gallery/parallelize-migration
- 子会话继承哪些 Knowledge：文档未写（推断：同组织会话照常适用）。
- 已知缺陷原文（2026-04-22）："Agents assume they share state with their children when they don't. Cross-agent communication, a sub-agent writing messages back to its manager to be passed to other agents in the agent team, doesn't happen by default" — https://cognition.ai/blog/multi-agents-working
- 立场演变：2025-06 "Don't Build Multi-Agents"（https://cognition.ai/blog/dont-build-multi-agents ）收窄为 "a narrower class works, where agents contribute intelligence while writes stay single-threaded"；"The open problems are all communication problems." — https://cognition.ai/blog/multi-agents-working
- 父子共享可写笔记的特例：auto-triage "The parent monitor and all child sub-devins share a persistent scratchpad ... The parent is primarily responsible for maintaining it" — https://docs.devin.ai/product-guides/auto-triage
- 模型自写笔记的局限（2025-09-29）："When we relied on the model's own notes without our compacting and summarization systems, we saw performance degradation ... the model didn't know what it didn't know" — https://cognition.ai/blog/devin-sonnet-4-5-lessons-and-challenges

### 2.6 Devin Review 与编码会话：刻意不共享上下文，由编码方过滤发现

- 读取仓库指令文件（`**/REVIEW.md`、`**/AGENTS.md`、`**/CLAUDE.md` 等，子目录作用域）— https://docs.devin.ai/work-with-devin/devin-review 。是否读 Knowledge 库：未找到（子 agent 对该页全文 grep 无结果）。评审反馈是否变成知识：未找到。
- "we found this technique to work best when the coding and review agents do not share any context beforehand"；过滤责任在编码方："does Devin properly use its broader context of user instructions, decisions, etc. to filter the bugs that come back from Devin Review? This is key to preventing looping, disobeying the user, doing work that is out of scope" — https://cognition.ai/blog/multi-agents-working
- 防循环：每 PR 评审花费上限、diff 未变不重评、新提交取消进行中的评审（release notes 2026，笔记 §6）。

---

## 3. Augment Code：对 MMW 有用的部分

完整笔记与 URL 清单：`notes/augment-notes.md`。先交代：2026 年 Augment 主力是 Cosmos（团队 agent 平台）与 Intent（桌面多 agent 工作区）；Remote Agents 已移除，原文 "Remote Agent has been removed from IDE extensions; this field is retained for historical data."（https://docs.augmentcode.com/llms-full.txt 的 analytics-api 段）。

### 3.1 两代 memory，写入规则相反

- 第一代（IDE，2025-09）：先审后存。"X Pending Memory" 按钮，Approve / Edit / Discard — https://www.augmentcode.com/changelog/memory-review ；指南原文 "Nothing gets stored without the developer's sign-off"，范围 "Per-developer, cross-session, reviewable" — https://www.augmentcode.com/guides/agent-memory-vs-context-engineering 。陈旧与去重：未找到。
- 第二代（Cosmos Expert Memory，2026）：存进共享虚拟文件系统（VFS）的 Markdown，按仓库/频道/项目/用户划范围；先存后告知："it tells you when it remembers something so you can correct or veto it." — https://docs.augmentcode.com/cosmos/experts-memory
- 加载时核对，不做过期："At the start of relevant work, the Expert loads memory for the current scope. It applies matching guidance and flags discrepancies when current evidence conflicts with a remembered rule."（同页）
- 两种写入模型："Simple memory … writes explicit, high-quality human feedback directly to a curated knowledge file"；"Noisy memory uses an evidence log plus a curated knowledge file. It combines weaker signals over time and promotes a learning only after the evidence is strong enough."（同页）
- 范围准则："Use the narrowest stable scope that matches the workflow"；"Save information only when it could change a future decision or area of focus."（同页）
- VFS 的版本与归属："every version is attributed to the agent that wrote it, and deletions are recorded as tombstones rather than erasures"；"Sync happens automatically at turn boundaries" — https://docs.augmentcode.com/cosmos/understanding-files

### 3.2 Code Review Memory：在合并时从评审结果学习

- 收集："records useful human comments, reactions to agent findings, addressed change requests, and the outcome of the change. Routine acknowledgments, bot updates, and process-only comments are filtered out." — https://docs.augmentcode.com/cosmos/experts-code-review-memory
- 信号分级："Explicit human feedback carries more weight than reactions or an inferred outcome, so strong feedback can become useful memory immediately while weaker signals must recur."（同页，已 curl 核对）
- 按路径加载："load relevant guidance for the repository and changed paths on their next run. They use it to avoid known false positives and recognize team-specific anti-patterns."（同页）
- 证据与结论分存："A raw breadcrumb log preserves the evidence collected from reviews, while a curated knowledge file contains the concise guidance"（同页）。是否需人批准：未找到批准步骤。

### 3.3 指南《Agent Memory vs. Context Engineering》原文要点（2026-04-17，更新 2026-06-18）

URL：https://www.augmentcode.com/guides/agent-memory-vs-context-engineering （下列四句我已从原 HTML 核对）

- 区分："agent memory determines what information survives between sessions, while context engineering determines what information is loaded into the next session's finite context window."
- 进 AGENTS.md 的准入："it is undiscoverable (the agent cannot infer it from reading the codebase) and it is universal (it applies to virtually every task in the project)"。
- 晋升触发（引 OpenAI Codex 文档）："when the agent makes the same mistake twice, conduct a retrospective and update AGENTS.md with the resulting guidance."
- 三层：context files（全队、进版本库）/ agent memory（自动捕获、人治理、每人一份）/ living spec（按 feature、随工作更新）。
- 四问判定（转述）：代码里读得出 → 不存；每个任务都适用 → context file；数周到数月稳定 → memory（全队适用再晋升为 rule）；feature 专属且在变 → living spec。
- 反模式："Spec rot: the file says one thing, the code does another, and agents read the stale version"；团队约定只存在个人 memory 会让"teammate's agent suggests the wrong library because the memory isn't shared"。
- 同系列 AGENTS.md 指南："Rules should respond to observed failure, not be generated speculatively."；"Measure whether the file changed anything before adding to it." — https://www.augmentcode.com/guides/how-to-build-agents-md （WebFetch 短句）

### 3.4 Intent 与 Cosmos 的多 agent 协作面

- Intent：Coordinator / Implementor / Verifier；spec 是 workspace 里的一份 note，"Agents read the Spec before starting work."；任务块属性 `dependsOn=`、`conflictsWith=`；每个 workspace 一个 git worktree；"The Coordinator reconciles file overlap at the merge step rather than during execution." — https://www.intentapp.dev/docs ；https://www.augmentcode.com/guides/intent-walkthrough-prompt-to-merge
- 验收的边界："A property absent from the spec stays absent from the Verifier's checks."（walkthrough）
- Cosmos Verifier："it reports what it observed, what could not be observed, and what evidence supports the finding." — https://docs.augmentcode.com/cosmos/experts-verifier.md
- Expert 之间以工件为媒介："No Expert launches another; the pull request is the medium." — https://docs.augmentcode.com/cosmos/workers-subagents
- Ticket Dispatcher 的背压："respects a maximum number of dispatcher-owned open changes so automation does not flood the review queue"，并 "records concise skip reasons" — https://docs.augmentcode.com/cosmos/experts-ticket-dispatcher.md
- Context Engine：每用户实时索引；Context Lineage 把当前分支近期 commit 用 LLM 压成几句摘要 — https://www.augmentcode.com/blog/announcing-context-lineage ；跨仓库评审靠在 AGENTS.md 里列外部仓库并调用 `augment_code_search` — https://docs.augmentcode.com/codereview/cross-repo-context

---

## 4. Nowledge Mem：可用作映射目标的机制（本机 `nmem` help 所见）

来源：`nmem --help` 与子命令 help（`scratchpad/nm/help1.txt`、`help2.txt`）、`nmem context read` 输出样本（`scratchpad/nm/ctx.txt`）、`scratchpad/nm/openapi.json`。只读了说明，没有写入测试，下表"能做什么"是 help 文本的字面意思，行为未实测。

| 机制 | help 原文 / 字段 | 可以承担的角色 |
| --- | --- | --- |
| Space | `spaces create … --rules … --share-with <SHARED_SPACE_IDS> … --retrieval-mode strict\|shared\|all` | 每个消费仓库一个 space（隔离不同客户的项目）；一个 MMW 工具箱 space 用 `--share-with` 共享给各仓库 |
| Agent identity | `agents enroll <ID> --role --default-space --rules --tag`，"Named agent identities consumed by Context Bundle" | worker / reviewer / verifier / main agent 四个身份，各带角色规则与默认 space |
| Rules | `rules upsert --scope global\|agent\|space --status draft\|active\|archived --priority`；`rules review` "Ask Mem to look for draft rule suggestions"；bundle 注明 "Rules are compiled from owner settings and review-approved evidence" | 提升后的"总是加载"的短规则；draft 状态天然是待人批准 |
| Memory 字段 | `memories add --title --importance --label --unit-type --agent-id --source-app --source-thread --event-start --space`；API `MemoryCreateRequest` 另有 `metadata`、`confidence`；`memories search --label --metadata key=value --unit-type fact/preference/decision/plan/procedure/learning/context/event --include-history` | capsule 与已接受条目；`metadata` 放 repo、ticket、commit、paths，`label` 放种类与状态。CLI 的 `add` 未见 `--metadata`（推断：需走 API 或 MCP 写） |
| 取代与作废 | `memories supersede <OLD> <NEW> --reason`；`deprecate --reason --replacement`；`graph evolves` "Show EVOLVES version chain" | 与 monomind 的 supersede、Augment 的 tombstone 同义；默认检索不含历史版本 |
| 人审队列 | `feed reviews` "List one page of unresolved Memory reviews"；`feed resolve` "through the server's audited action executor" | 早间提升队列的现成界面（推断：其审阅项由 Mem 自己的健康检查生成，能否由外部脚本塞入自定义审阅项未找到） |
| Working Memory | `working-memory read/edit/patch --space`，"daily focus surface" | 每个 space 一份当日简报；只适合放"非状态"的提示 |
| Context Bundle | `context read --agent-id --space --source-app`，"Owner/agent/space/rules context bundle (session-start surface)" | 会话开始时一次取出身份、规则、Working Memory |
| 线程 | `threads save/capture/distill/triage` | 会话原文存档与蒸馏（与 monomind 的 D1"transcript 不进共享库"相冲突的地方见 §8） |

与 MMW 的现状：`mmw-v2/install.sh` L1619-1698 只为 Cursor 写 `~/.cursor/mcp.json` 的 `nowledge-mem` 条目，流水线脚本与技能正文里没有任何对 Nowledge Mem 的读写（区分大小写搜索 `Nowledge|nowledge-mem|nmem`，`mmw-v2/` 与 `docs/` 下除 `install.sh` 外只有 `docs/contexts/toolbox/CONTEXT.md` L174 描述 install.sh 的那一条）。


---

## 5. 机制 × MMW 对照表

缩写：**NM** = Nowledge Mem；**tracker** = GitHub issue 与 `<!-- mmw {...} -->` 事件；**仓库文件** = 消费仓库或 MMW 仓库里进版本库的文件。"MMW 现有对应物"只写我读到的，未读到的写"未找到"。

| # | 机制 | 来源 | 解决的问题 | MMW 现有对应物 | 差距 | 是否值得引入、如何以 MMW 的方式引入（载体） | 前提与失效场景 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 采集与提升分两步：工作中只写一条 ≤200 词的 capsule 进 inbox，判断推迟到提升时 | monomind `context_capture.py` L4-10；Augment noisy memory 的 evidence log；Devin 聊天反馈生成 Knowledge 建议 | 中途停下写正式条目太贵，于是不写；一夜学到的操作性知识丢失 | 无。worker 的 `Decisions I made on my own` 与 `skipped:` 行只记本票决定；verifier 修环境的办法、不稳定的测试、起产品的坑没有落点（brief 缺口 A） | 没有采集点，没有 kind 分类 | **值得（前 5 第 1 条）**。由 verify-ticket 或 dispatch 技能的脚本提供一个采集子命令（事件由脚本写的原则，ADR 0019），capsule 写入 NM 该仓库的 space：`unit_type` learning/procedure/fact，`label` 为 `mmw:capsule` + 种类（`env`、`flaky`、`gotcha`、`decision`、`assumption`），`metadata` 为 repo、ticket、run、commit、files。票上只留一行指向 | NM 服务在跑且本机可达；云端或别的机器上的 runner 取不到时要明说"没采集"。风险：capsule 泛滥无人提升（monomind 用按年龄排序的 review 报出积压） |
| 2 | capture 自动附出处：actor、session、harness、model、`commit:<binding>:<HEAD>`；未知字段不写 "unknown" | monomind `context_capture.py` L89-109；Augment VFS "every version is attributed to the agent that wrote it"；NM `--agent-id --source-app --source-thread` | 事后无法判断一条知识是谁在什么代码状态下得出的，也无法复查 | tracker 事件已带 commit、run、模型（`ticket.checked`、`verifier.passed` 的 payload） | 知识条目本身没有出处，因为没有知识条目 | **值得，随第 1 条一起做**。脚本从票事件与 `git rev-parse HEAD` 取值，不让模型填 | 模型若绕过脚本直接 `nmem m add`，出处缺失；按 ADR 0019 的精神，检索时只信带 `metadata.run` 的条目 |
| 3 | 触发"窗口"由脚本判，内容是否值得记由 agent 判；"没触发"也要显式 ack，ack 绑定当时 HEAD 与脏路径 | monomind `context_triggers.py` L185-199，SKILL.md L93-107 | "什么都没记"与"评估过、无可记"读起来一样；ack 变成永久跳过 | ADR 0008 已是同一原则；`manage-agents-md` 的 incremental 用"最后一次改 AGENTS.md 的 commit..HEAD"算变更集（`references/incremental.md` L15-18），思路相同 | 收尾评论没有"学到了什么"的固定行 | **值得，小改动**。收尾评论加一个固定行（例如 `Learnings: <capsule ids>` 或 `Learnings: none — <评估了什么>`），`--closeout` 缺行即拒绝。它天然绑定该票 commit，无需另存 ack | 形式化后 agent 可能一律写 `none`。缓解：晨间 retro 对 returned/bounced/lost 的票抽查 `none` 是否属实 |
| 4 | 按路径锚取回：记录写明它约束的文件（证据锚或 `Files:`），开工时用 `--files` 做路径前缀匹配，路径命中权重高于词汇命中 | monomind `context_packet.py` L4-9、L336-352；Augment Code Review Memory "load relevant guidance for the repository and changed paths"；Devin pin 到仓库必加载、未 pin 按触发 | 启动时要么全量塞入、要么什么都不读；worker 看不到兄弟票和前几夜在同一批文件上踩过的坑 | `## Read first` 由 `to-tickets` 从 spec 的 Sources 挑，是写票时静态决定的；`worker.touched` 只在事后通知同一 spec 的票（`docs/contexts/ticket-run/CONTEXT.md` `worker.touched` 词条） | 没有按 `## Owns` 取回历史知识的步骤；没有跨 spec 的"谁也在改这些文件" | **值得（前 5 第 2 条）**。implement 读票步骤加一条命令：以票的 `## Owns` 为 `--files`，从 NM 取该仓库 space 中已接受（非 capsule）的条目，在脚本里做路径前缀匹配（NM 无原生前缀查询，推断），再从 tracker 查"其他开着的 spec 里 Owns 重叠的活票"。reviewer 用 `git diff --name-only` 做同样的事 | NM 的语义检索是非确定的，只能用作补充；确定性部分靠 `metadata.files` 与脚本匹配。条目不写路径就永远匹配不到——提升时必须补路径 |
| 5 | 只加载已接受条目，proposed 只列标题链接；超预算的列成链接而不丢弃 | monomind `context_packet.py` L11-16、L359-404 | 未审内容混进上下文；截断后 agent 以为没有更多 | `Read first` 读到结论为止的规定（implement SKILL.md 读票段） | 无检索包，所以无此规则 | **值得，随第 4 条**。包的末尾固定有 "Not loaded" 一节 | 预算估算不准时仍可能超；按字符数/4 估算即可 |
| 6 | 证据锚 `path@commit`，doctor 用 git 判断引用后文件是否变过（evidence-drift），规定动作是重读后重锚或取代 | monomind `context_doctor.py` L456-537，SKILL.md L118-122 | 链接还能打开不代表内容还成立；陈旧知识被当事实执行 | ADR 与 CONTEXT.md 词条靠 `_Home_` 指向源文件，但不带 commit；票正文发布后不改 | 没有"这条依据的文件后来变了"的检测 | **值得（前 5 第 4 条）**。提升后的条目在 `metadata` 里存 `anchors: [path@sha]`；检索脚本对每条跑 `git diff --quiet <sha> HEAD -- <path>`，变了就在包里标"依据已变，先核对"，不自动删 | 浅克隆或 squash 后 commit 不在本地，只能报"无法核对"（monomind 的 `evidence-unverifiable`）；跨仓库条目无法在本仓库核对 |
| 7 | 加载时核对，冲突就报出来，而不是过期删除 | Augment experts-memory "flags discrepancies when current evidence conflicts with a remembered rule"；Devin Session Insights "Misleading Knowledge" | 过期规则被照做；删除又会丢失理由 | ADR 0008 要求每道闸口说出事实 | worker 没有被要求报告"取回的知识与现状不符" | **值得，随第 4、6 条**。收尾评论或 `worker.decided` 加一处"取回条目与现状不符：<id> <事实>"，晨间据此 supersede | 依赖 agent 真去核对；只能提高发现率，不能保证 |
| 8 | 取代不改写：新条目 `supersedes` 旧条目，旧条目标 superseded 并保留原文 | monomind SKILL.md L79-82；NM `memories supersede --reason`、`deprecate`；Augment tombstone | 改写后丢失"为什么曾经这么做" | ADR 的 `amends` 与"被哪几份改写"列；票正文不改、spec 改动写评论（brief 不变量） | 已具备，知识条目沿用即可 | **已有，映射到 NM 的 supersede** | NM 的 EVOLVES 关系可能由其后台自动推断（help 有 `graph evolves`，生成方式未实测）；以脚本显式调用 `supersede` 为准 |
| 9 | 写新决策前查冲突候选：路径重叠直接列，词汇重叠需 ≥5 词且 ≥25%；出路只有两个——取代旧的，或写明两者为何并存；检查没跑成不许读作"无冲突" | monomind `context_review.py` L331-360、L494-513，SKILL.md L64-91 | 第三十条决策开始和前面的悄悄矛盾 | `worker.decided` 由 Spec 轴逐条判断（`docs/contexts/ticket-run/CONTEXT.md` `worker.decided` 词条），但比对对象是本 spec；ADR 有编号与 amends | worker 的临时决定不与 ADR、其他 spec 的已接受决定比对 | **值得，排在前 5 之后**。`--decisions` 前由脚本把每条决定的文件与 NM 中 `unit_type=decision` 的已接受条目、`docs/adr/` 的标题做路径/词汇候选匹配，把候选写进 DECISIONS 评论供 Spec 轴读 | 词汇匹配噪声大，monomind 自己也承认"cannot tell that two decisions contradict"；只当提示，不当闸 |
| 10 | agent 不得批准自己提出的条目 | monomind doctor `agent-self-approval`（design L688-690）；Augment Pair Reviewer "posts comments or a verdict only after human authorization"；NM rules 的 `draft` 状态 | agent 自说自话把猜测升格为规则 | worker 不能手工关票（hook 拦截）；`decision` 子票交人；早间 triage 由人 | 知识提升无此约束（因为没有提升） | **值得（前 5 第 3 条的一部分）**。capsule 由 agent 身份写入，只有用户在早间把它变为已接受；写 NM rules 一律 `--status draft`，由用户改 active | 用户不看队列时知识一直是 proposed，检索包不加载——这是正确的失败方向 |
| 11 | 晋升阈值："同一个错误出现两次"就做 retro 并更新 AGENTS.md；AGENTS.md 准入要"读代码推不出"且"每个任务都适用" | Augment 指南（引 Codex 文档）；https://www.augmentcode.com/guides/how-to-build-agents-md "Rules should respond to observed failure" | 规则文件被猜测性内容撑大；真正反复出现的错误不进规则 | `manage-agents-md` 的 incremental 由代码变更驱动，不由失败驱动；用户自己拥有的行（evidence `user`）不自动改（`references/incremental.md` L7） | 没有"失败重复次数"这个信号 | **值得（前 5 第 3 条）**。晨间脚本按 `label`+`files` 聚合 capsule，同一类出现 ≥2 次（跨票或跨夜）自动提名；去处固定为：仓库 `AGENTS.md` Gotchas、`CONTEXT.md` 词条、技能 `references/`、ADR，全部经票落地；只对"所有 agent 每次都要知道"的一两句短规则才写 NM rules | 聚合依赖 label 一致；NM 已有 `label-backfill` 技能处理同义标签。阈值 2 是 Codex 文档的经验说法，未见测量 |
| 12 | 两种写入模型：人明确说的直接写入；弱信号先进证据日志，重复到阈值才晋升 | Augment experts-memory、experts-code-review-memory | 逐条人审太累，全自动又被噪声淹没 | 无 | 无 | **值得，用于第 13 条**。用户在 triage 中明说的规则→直接成为已接受条目；reviewer/verifier 的结果与 agent 观察→capsule，靠第 11 条聚合 | 分级规则写错时，弱信号永远升不上来或升得太快 |
| 13 | 从评审结果学习：合并时收集发现被采纳/驳回、人工评论、改动结果，按仓库与路径加载，用来压低已知误报和识别团队反模式 | Augment Code Review Memory（原文已核对） | reviewer 每夜重复同样误报、漏掉本仓库特有的缺陷 | 评审发现的去向已是结构化事件：`dispatch.sh route … fixed\|stale\|became-ticket` 写 `child.closed`（`docs/contexts/night/CONTEXT.md` `route` 词条）；in-ticket 修复后重跑；`verifier.failed` 的 `failed` 字段；`ticket.bounced` 的原因 | 这些结构化结果没有被汇总回 reviewer 与 worker | **值得（前 5 第 5 条）**。`summary` 之后跑一个脚本：把本夜 `child.closed stale`（误报信号）、`fixed`/`became-ticket`（真缺陷信号）、`verifier.failed` 的准则、bounced 原因，按 finding 引用的文件写成 capsule（弱信号）；reviewer 的 Standards/Tests 轴启动时按 diff 路径取回已接受的"本仓库评审指南" | `stale` 不全是误报（也可能是被别的票修掉了），需区分；只有 finding 带文件路径时才可按路径加载 |
| 14 | 知识使用可审计：会话记录用了哪些条目；事后标 Useful / Misleading | Devin "Accessed Knowledge"、Session Insights `note_usage.good_usages / bad_usages` | 不知道哪条知识在帮忙、哪条在误导 | 无 | 无 | **值得，低成本**。检索包输出条目 id 列表，worker 的自跑事件或收尾评论带上这些 id；配合第 7 条的"与现状不符"报告即得"misleading" | 只有 id 被写上事件才可追踪；agent 读了但没用无法区分 |
| 15 | 事后会话分析：只对大/失败会话自动跑，输出分类 action item（machine_setup / repo_config / knowledge / prompt_improvement），不自动改 | Devin Session Insights | 失败原因散落在各会话里，没人归类，也没人回头改流程 | `NIGHT SUMMARY` 只有计数与列表（`docs/contexts/ticket-run/CONTEXT.md` 词条）；早间 `triage` 看 returned/bounced/regressed 票 | 没有跨票归类，没有对技能文本的改进建议（brief：没有跨夜 retro） | **值得，但放在前 5 之后**。晨间 retro 只读 `HANDOFF REQUIRED`、`ticket.bounced`、`worker.lost` 的票与其事件，输出分类建议；技能改动走 MMW 仓库的票（技能是交付物） | 需要会话原文才能深挖；MMW 目前靠票事件与评论，已足够做第一层归类 |
| 16 | playbook 版本化，按成功与失败会话对比来改 | Devin playbooks、advanced-capabilities | 凭印象改 prompt，改完不知道好坏 | MMW 技能在 git 里，天然有版本；ADR 记录为什么 | 没有"用哪个版本的技能跑出了什么结果"的关联 | **暂不**。先让第 15 条的 retro 产出证据；NM 的 `skills eval/outcome/sharpen` 面向 NM 自己管理的技能，MMW 技能是仓库交付物，不应搬进 NM | 样本太少时成败对比无统计意义 |
| 17 | "怎么起项目"放在可执行、可版本化的环境定义里，构建后检查失败就不产出快照；知识只放命令引用 | Devin blueprint `post-build`、`knowledge` 段 | 每个 worker 各自摸索环境 | `.mmw/target.json` 的启动/停止命令、`drive-target` 的 lease 与端口分配；verifier "The environment is yours; the repository is not"（`docs/contexts/ticket-run/CONTEXT.md`） | 环境修复的办法不回流到 `target.json` 或 Gotchas | **MMW 已有主体**。只补采集：verifier 修过环境就写 `env` capsule，重复两次提名改 `target.json` 或 `AGENTS.md` Gotchas | — |
| 18 | 派发前按"不改同一文件"分组、有依赖的串行；任务声明 `conflictsWith` | Devin gallery parallelize-migration；Intent `dependsOn=`/`conflictsWith=` | 并行 worker 改同一文件导致 bounce | `to-tickets` 在一个批次内：同一 frontier 上 Owns 重叠须加 Blocked by，三张以上先切 prefactor 票（`to-tickets/SKILL.md` L99-105、L146）；`relay.py` `overlap`（L449）只查同一张票被两个 watch 看 | 未找到跨并行 spec 的文件级重叠检查（brief 与用户记忆中 #748/#750/#751 的代价） | **值得，但载体是 tracker 与 lint，不是 NM**。`open <spec>` 时读其他开着的 spec 的活票 `## Owns`，重叠就拒绝或要求 Blocked by 跨 spec 链接 | 需要读多个 spec 的票，GitHub API 调用增加；Owns 写得不全时检不出 |
| 19 | 一个维护者 + 多个读者的共享笔记（scratchpad / Organization scope / notes） | Devin auto-triage scratchpad；Augment VFS；Intent notes | 跨会话去重、路由表这类"非状态"信息没有落点 | spec 评论、`NIGHT SUMMARY` | 夜内非状态提示（"今晚 lease 端口 X 不稳"）无处放 | **低优先**。若做，由 main agent 单写 NM 该仓库 space 的 Working Memory 一个小节（`working-memory patch`）；严禁放票状态 | NM 的 Working Memory 也会被 Mem 自己按天重写（样本里是自动生成的简报），可能覆盖或改述；Cognition 自己也说模型自写笔记"didn't know what it didn't know" |
| 20 | 跨仓库分发走白名单，推下去的副本记 sha256，被就地改过就拒绝下一次推送；反馈只能以 question/proposal 回流 | monomind project-hub `docs/CLI.md` L148-222、`skills/project-hub/SKILL.md` L62-78 | 全局规则在各仓库被悄悄改掉；私密内容被推到不该去的仓库 | MMW 技能以 symlink 从一个 checkout 供给全机（`AGENTS.md` Key Conventions），改一处全机生效；downstream-note 记录影响消费仓库的改动 | 跨仓库"学到的东西"没有通道；也没有"什么不许跨仓库"的规则 | **部分值得**：借"白名单"这一点。NM 里只有 MMW 工具箱 space 用 `--share-with` 共享给各仓库 space；各消费仓库 space 设 `--retrieval-mode strict`，默认不互相可见 | 不同消费仓库可能属于不同付费客户——跨 space 默认共享会泄露。这是产品决定（见 §8） |
| 21 | 评审与编码不共享上下文，由编码方按用户指令过滤评审发现 | Cognition 2026-04-22 | reviewer 被编码方的错误前提带偏；编码方盲从评审而越界、打转 | reviewer 是独立会话，读 `git diff <base>...HEAD` 与票；发现分 in-ticket / out-of-ticket，in-ticket 只修一轮，out-of-ticket 开 finding 子票，ADR 0012 四步门槛 | 无 | **MMW 已做得更好**（见 §6） | 检索包若把 worker 的临时笔记也给 reviewer，会破坏这一点——reviewer 只取"已接受的评审指南"，不取 worker capsule |
| 22 | 定期知识维护：先去重、再解冲突、再补缺，产出待批变更 | Devin advanced-capabilities；NM `memory-health`、`label-backfill` 技能 | 知识只增不减导致冲突 | 无 | 无 | **值得，频率低**。每周一次，用 NM 已有的健康检查与标签合并，结果进 `feed reviews` 由用户处理 | 维护本身若自动合并条目，会破坏出处；只提议不执行 |
| 23 | verdict 必须说出"没能观察到什么" | Augment Cosmos Verifier | "无法验证"被读成"通过" | ADR 0008；`verifier.failed` 在 `could not start` 时 `ran` 为 false（`docs/contexts/ticket-run/CONTEXT.md` 词条） | 基本无差距 | **MMW 已有** | — |

---

## 6. MMW 已经做得更好的地方

1. **状态只由脚本写，且是事件折叠。** 票状态是 `<!-- mmw {...} -->` 事件按评论顺序的折叠，模型打字不算（ADR 0019）。monomind 的状态是人或 agent 手改 Markdown 里的 `Status:` 行；Devin Knowledge 没有版本号（v3 响应无该字段）；Augment 第二代 memory 是"先存后告知"。MMW 的做法可审计性最强，引入知识系统时应沿用：知识条目也由脚本写入，出处字段由脚本填。
2. **"沉默不是通过"是全流水线的规则，不是个别脚本的习惯。** ADR 0008 覆盖每一道闸口。monomind 只在 `context_review.py --new-decision` 和 `context_triggers.py` 两处做到（"A silent all-clear from a broken install is worse than no check at all"）；Devin 与 Augment 文档里没有对应的通用原则（未找到）。
3. **评审与编码的上下文隔离，比 Cognition 描述的更结构化。** Cognition 2026-04 的结论是"coding and review agents do not share any context beforehand"，并把"编码方如何过滤评审发现"列为关键开放问题。MMW 已经把过滤写成规则：in-ticket 一轮修复、out-of-ticket 变 finding 子票、收口轮用 ADR 0012 四步门槛 `route`。
4. **独立验证绑定 commit。** verifier 在同一 commit 上独立重跑全部验收，`--closeout` 要求 verdict 覆盖将被合并的 commit。Augment `cosmos approve` 的 "Current-head review" 是同一思路，但只是可选策略；Devin Review 文档里没有等价的"绑定 commit 的独立复跑"（未找到）。
5. **唤醒不轮询，靠事件与 ack。** relay 把结果事件变成唤醒并要求 ack，watchdog 查沉默会话（ADR 0010、0020-0022）。Devin coordinator 需要 "Schedule messages to itself — set reminders to check back"；Intent 的 daemon 唤醒与之相当，另有去抖与批处理（第 5 节未列入，因为与知识无关）。
6. **"只有人能定的事"有固定出口。** question gate 拒绝提问工具，`decision` 子票带默认值继续工作。monomind 的 `assumption` capsule 与 `QUESTIONS.md` 需要人主动去看；Devin playbook 的 "Required from User" 只是一段文字。
7. **环境与产品启动已经可执行化。** `.mmw/target.json` 与 `drive-target` 的 lease 相当于 Devin blueprint 的执行部分，而且带端口隔离；缺的只是"修过环境"这件事的采集（表第 17 行）。
8. **跨机器、跨仓库的工具箱分发是实时的。** 技能 symlink 到一个 checkout，改一处全机下一次调用即生效；monomind Hub 要 owner 手动 `push --all`、每仓库一个 PR 再人工合并，作者自己也写明代价 "a repo whose owner has not pushed lately is quietly stale"（design L505-508）。

---

## 7. 最值得采纳的 5 条

排序依据：对 brief 缺口 A（一夜学到的知识无处沉淀、兄弟票读不到）的直接程度 × 与 MMW 不变量的兼容度 ÷ 改动面。每条都遵守两条边界：**NM 里的东西永远不是票的状态，也不当任何闸口的通过条件**（ADR 0001、0019）；**NM 不可达时，读写它的步骤要明说"没做"，而不是静默跳过**（ADR 0008）。

### 第 1 条：票内采集 capsule，带脚本填写的出处；收尾评论加 `Learnings:` 固定行

- 做什么：worker、reviewer、verifier 在工作中遇到"值得下一个人知道、但不是本票决定"的事（环境修法、不稳定测试、工具行为与文档不符、起产品的坑、做下去所依据的假设），调用一个脚本子命令写一条 ≤200 词的 capsule。收尾评论新增固定行 `Learnings:`，写 capsule id 列表，或 `none — <评估了什么>`；`--closeout` 缺此行即拒绝。
- 为什么这样：monomind 的论证——"Capture has to be cheap enough to happen *during* the work, or it does not happen at all"（`context_capture.py` L4）；判断推迟到提升时。固定行是 ADR 0008 在知识上的应用，与 monomind 的 `ack` 同义，但直接绑定在票的 commit 上，不需要另存状态文件。
- 载体：capsule 进 **NM**，该消费仓库一个 space；`unit_type` 取 learning/procedure/fact，`label` 取 `mmw:capsule` 与种类，`metadata` 由脚本填 `repo`、`ticket`、`run`（worker/reviewer/verifier）、`commit`、`files`；`--agent-id` 用角色身份（`nmem agents enroll worker --role worker --default-space <repo space>`）；id 由"日期+正文哈希"派生，重复写入无副作用。`Learnings:` 行在 **tracker**。
- 放弃的替代方案：写进仓库 `project-context/inbox/`（monomind 做法）——会在 ticket 分支上产生与 `## Owns` 无关的文件改动，触发 `Outside Owns:`，并与并行票冲突；写成票评论——跨票、跨 spec、跨夜检索困难。
- 前提：`nmem` 在 worker 所在机器可达；各 host 能跑 shell 命令（MMW 的脚本全靠这个，已满足）。
- 失效场景：云端 runner 或别的机器没有 NM → 子命令必须打印一行"未采集：NM 不可达"，`Learnings:` 行写 `unavailable`，closeout 接受但晨间汇总列出；agent 一律写 `none` → 靠第 3 条的 retro 抽查。

### 第 2 条：认领后与评审前各取一次"按文件取回"的检索包

- 做什么：implement 读票步骤（`implement/SKILL.md` "Then read yourself in"）之后加一条命令，以票的 `## Owns` 为文件集；reviewer 以 `git diff --name-only <base>...HEAD` 为文件集。脚本输出一个有预算的包，顺序：(a) 其他开着的 spec 里 `## Owns` 与本票重叠的活票（号、标题、状态、worker）——从 **tracker** 查；(b) NM 中该仓库 space 与工具箱 space 里已接受条目中 `metadata.files` 与文件集路径前缀重叠的；(c) 仅词汇重叠的；(d) 超预算与 proposed 条目只列标题。reviewer 只取 `mmw:review-guide` 类已接受条目，不取任何 worker capsule（保持表第 21 行的隔离）。包的 id 列表写进 worker 自跑事件或收尾评论（表第 14 行）。
- 为什么这样：monomind 的判断——"the signal that actually decides relevance is already written down — a decision cites the files it constrains, and the task names the files it touches"（`context_packet.py` L6-8）；Augment 评审记忆按 "changed paths" 加载；MMW 的票天然有 `## Owns`，比 monomind 的 `--files` 更可靠。
- 载体：检索与匹配在 MMW 脚本里做（确定性）；NM 只作存储与候选召回（`nmem --json m search --space … --label … --metadata repo=…`），路径前缀匹配在脚本中完成（推断 NM 没有原生前缀查询）。
- 放弃的替代方案：用 NM 的 context bundle 或语义检索直接灌给 agent——不可复现，reviewer 隔离也保不住；把知识写进 `## Read first`——票正文发布后不改，且写票时还不知道当夜会学到什么。
- 前提：提升后的条目必须带 `files`（第 3 条负责）；工具箱 space 与仓库 space 的共享关系已设定（§8 的产品决定）。
- 失效场景：条目没写路径 → 永远匹配不到，只能靠词汇召回；NM 不可达 → 包里写"知识库未查询"，(a) 的 tracker 部分照常输出。

### 第 3 条：早间提升队列——agent 不自批，"同类出现两次"自动提名，去处固定

- 做什么：`summary` 之后或早间 triage 之前，脚本列出该仓库 space 中未处理的 capsule，按年龄从老到新（monomind："latency is the one weak point of a system where nothing moves until a person looks"，`context_review.py` L11-14），并按 `label`+`files` 聚合，出现 ≥2 次（跨票或跨夜）的标"建议提升"。用户对每组选：接受（成为已接受条目，必须补 `files` 与第 4 条的锚）、驳回、或"开票改规则"。去处：
  - 所有 agent 每次都必须知道、代码里读不出的一两句 → 消费仓库 `AGENTS.md` Gotchas（经票，`manage-agents-md`）或 NM `rules --scope space --status draft` 由用户改 active；
  - 某个领域词或约定 → `CONTEXT.md`（经 `domain-modeling`）；
  - MMW 流程本身的缺陷 → MMW 仓库的票，改技能正文或 `references/`；
  - 只对部分文件有效的操作性知识 → 留在 NM 作为已接受条目，由第 2 条按路径取回。
- 为什么这样：Augment 指南的准入两条（undiscoverable 且 universal）与晋升触发 "when the agent makes the same mistake twice"；monomind 的 `agent-self-approval` 与 "Leaving it `proposed` is the only outcome that is not a resolution"；Devin 建议可编辑、可丢弃、可指向已有条目做更新。
- 载体：队列展示可复用 **NM** `feed reviews` 界面（能否由外部脚本塞入自定义审阅项未找到，若不能则由 MMW 脚本在终端或任务板列出）；决定写回 NM 条目状态；规则改动走 **tracker 票 → 仓库文件**。
- 放弃的替代方案：让 NM 的 `rules review` 自动产出并直接生效——违背 ADR 0019"事件由脚本写"与 agent 不自批；全部写进 AGENTS.md——Augment 与 monomind 都指出规则文件膨胀会降低遵循度。
- 前提：用户愿意每天花几分钟看队列。这改变用户每天要处理的事，是产品决定（§8）。
- 失效场景：用户不看 → capsule 一直是 proposed，检索包不加载，知识不起作用但也不误导；标签不一致导致聚合失败 → 用 NM 的 `label-backfill` 定期合并同义标签。

### 第 4 条：已接受条目带 `path@commit` 锚，取回时检测漂移并要求报告"与现状不符"，只取代不改写

- 做什么：提升时脚本把条目依据的文件与当时 commit 存入 `metadata.anchors`。第 2 条的检索脚本对每条执行 `git diff --quiet <sha> HEAD -- <path>`：文件变了就在包里标"依据已变，先核对"；commit 不在本地就标"无法核对"。worker 或 reviewer 发现条目与现状不符，写进 `worker.decided` 评论或收尾评论的一行；晨间据此 `nmem m supersede <old> <new> --reason` 或 `deprecate`。
- 为什么这样：monomind 的论证——"A link that still resolves proves the cited file exists, not that it still says what it said when it was cited. Pinning the commit makes the citation falsifiable"（`context_doctor.py` L459-463）；Augment 选择"加载时核对并报出"而非过期删除；Devin 只能事后在 Session Insights 里发现 Misleading Knowledge，陈旧成本已付。
- 载体：锚与状态在 **NM** 条目的 metadata 与 supersede 关系里；核对在 MMW 脚本里用本仓库 git 做；"不符"报告在 **tracker** 评论。
- 前提：锚引用的 commit 在 base branch 历史上可达（MMW 用 fast-forward 推送，ADR 0023，满足）。
- 失效场景：跨仓库条目（工具箱 space）无法在消费仓库核对 → 只能标"无法核对"；文件改名 → 报 drift，需人重锚。

### 第 5 条：把评审与验收的结构化结果变成"本仓库评审指南"，按路径喂回 reviewer

- 做什么：夜的收口轮与 `summary` 之后，脚本读本夜事件，按 finding 或准则关联的文件写 capsule（弱信号）：`child.closed` 为 `stale` 的 finding（可能是误报）、`fixed` 与 `became-ticket`（真缺陷）、in-ticket 发现修复后通过、`verifier.failed` 的 `failed` 准则、`ticket.bounced` 的原因。第 3 条聚合后，"同一路径同类发现两次被判 stale" 提名为"已知误报"指南，"同类缺陷两次成立"提名为"本仓库反模式"指南，或提名为代码检查器规则（`code-checkers` 技能）或 `code-review` 轴文件的改动票。reviewer 的三个轴按 diff 路径取回已接受指南（第 2 条）。
- 为什么这样：Augment Code Review Memory 的做法与信号分级（"Explicit human feedback carries more weight than reactions or an inferred outcome"）；monomind 把 "a rule that would have prevented a review finding" 列为 LEARNINGS 触发条件（SKILL.md L58-62）。MMW 已有的 `route` 结果比 Augment 需要从 PR 评论与表情里推断的信号更干净。
- 载体：原始信号来自 **tracker** 事件（只读）；capsule 与指南在 **NM**；规则落地为检查器或技能文本走 **仓库文件**。
- 前提：finding 子票正文带文件路径（`code-review` 的 finding 格式要求引用需求行，是否总带文件路径我未核实）。
- 失效场景：`stale` 实为"被别的票顺手修掉"→ 需要 `route` 时区分"误报"与"已被修复"两种 stale（现有 `route` 只有 `fixed|stale|became-ticket` 三值，推断需要细分或加一个 reason 字段）；样本少时误把真缺陷压成"已知误报"→ 已知误报指南只让 reviewer 降级标注，不让它不报。

### 不在前 5 但同等重要、载体不是知识系统的一条

- **跨并行 spec 的 `## Owns` 重叠检查**（表第 18 行）。用户记忆里 #748、#750、#751 三次 bounce 的代价就是它；`to-tickets` 只在一个批次内检查，`relay.py` 的 `overlap`（L449）只查同一张票被两个 watch 看。它应做在 `open <spec>` 或 `advance` 派发前，读 tracker，不需要 NM。第 2 条检索包里的 (a) 部分是给 worker 看的提示，不能替代这个闸口。

---

## 8. 需要用户决定的事与风险

这些改变客户能看到的东西、跨客户的数据流、或每天的人工工作量，属于用户的决定。上面 5 条中不依赖它们的部分（采集脚本、检索脚本、锚与漂移检测、事件汇总）可以先做；依赖它们的部分标在括号里。

1. **不同消费仓库之间是否共享知识。** 各仓库若属于不同付费客户，一个仓库的 capsule（可能含内部路径、业务规则、客户数据形状）被另一个仓库的 worker 取回，就是跨客户泄露，且写入 NM 后的外泄无法撤回。建议默认每仓库一个 `--retrieval-mode strict` 的 space，只有 MMW 工具箱 space 共享给所有仓库，写入工具箱 space 须经用户在第 3 条队列中手动"移到工具箱"（`nmem m move`）。（影响第 2、3 条）
2. **每天是否愿意处理提升队列。** 不处理，知识永远不生效；处理，每天多一件事。可以把门槛调高（只列"出现两次"的组）来减少条数。（影响第 3、5 条）
3. **会话原文是否进入 NM。** NM 有 `threads save/capture/distill`。monomind 明确不把 transcript 放共享存储（D1："capsules only, sessions local"，理由之一是无法真正删除）；Cognition 的经验是分析失败会话需要完整轨迹。折中：原文只在本机 NM、不进工具箱 space，且不自动蒸馏为已接受条目。（影响表第 15 行的 retro 深度）

工程上的风险（我的判断，无需用户决定，但需知道）：

- **NM 的后台处理是模型驱动的**（自动标签、实体抽取、社区、Working Memory 简报、EVOLVES 关系），结果不可复现。MMW 只把显式写入的 `metadata` 与脚本调用的 `supersede` 当依据，其余当辅助。
- **取回的知识是不可信输入。** 条目正文可能源自票内容或外部文本，agent 应把它当资料而不是指令；技能正文需要写明这一点。
- **单机依赖。** NM 服务在本机；MMW 的 runner 若将来在云端或他机，采集与检索会变成"未做"。按 ADR 0008 显式报告即可，不应让任何闸口依赖它。
- **Working Memory 会复述票状态。** 本机样本（`scratchpad/nm/ctx.txt`）里 Working Memory 已在总结 ADR 0023 与具体票号；若 worker 在会话开始读到它，可能把过时的票状态当事实。建议 worker、reviewer、verifier 的 context bundle 调用加 `--no-working-memory`，只有 main agent 与用户读 Working Memory。

---

## 9. 来源清单

monomind（源码，固定到提交）：

- https://github.com/monomind-ai-lab/project-context/tree/72a0a22640f4577eddd615c6bd3a4dad2a6473b9 ：`planning/project-context-design.md`、`planning/record-model-v1.md`、`planning/project-context-handoff-2026-09-03.md`、`docs/archive/context-hub-architecture.md`、`skills/project-context/SKILL.md`、`skills/project-context/scripts/{context_packet,context_capture,context_review,context_triggers}.py`（全文）、`context_doctor.py`（L444-537 全文，其余按 issue code 浏览）、`src/project_context_cli/__init__.py`、`skills/project-context-init/assets/project-context/{DECISIONS.md,LEARNINGS.md,decisions/TEMPLATE.md,questions/TEMPLATE.md,inbox/README.md}`、`skills/project-context-init/SKILL.md`（hook 段）
- https://github.com/monomind-ai-lab/project-hub/tree/5b2d92cb42215d19fa72dc96a5e897c45efe5bbd ：`skills/project-hub/SKILL.md`、`docs/CLI.md`、`guides/authored-and-pushed.md`、`.project-hub.json`、`global/skills/README.md`、`templates/global/SKILL.md`；`skills/project-hub/scripts/project_hub.py` 只按关键字定位
- 未读：`skills/project-context-init/scripts/project_context_init.py`、两仓库 `tests/`、`web/`

Devin 与 Augment：URL 全表见 `notes/devin-notes.md` 末节（docs.devin.ai 35 页、cognition.ai 16 篇）与 `notes/augment-notes.md` 末节（docs.augmentcode.com 与 augmentcode.com 约 40 页、intentapp.dev/docs）。本报告正文引用的均在其中；我亲自 curl 核对的是：https://docs.augmentcode.com/cosmos/experts-memory.md 、https://docs.augmentcode.com/cosmos/experts-code-review-memory.md 、https://docs.devin.ai/product-guides/session-insights.md 、https://cognition.ai/blog/multi-agents-working 、https://www.augmentcode.com/guides/agent-memory-vs-context-engineering 。

Nowledge Mem：本机 `nmem` 各子命令 help（`scratchpad/nm/help1.txt`、`help2.txt`）、`scratchpad/nm/ctx.txt`、`scratchpad/nm/openapi.json` 的 `MemoryCreateRequest`。

MMW（只读）：见 §0。

# Devin（Cognition）调研笔记：Knowledge、Playbooks、Session Insights、DeepWiki、Managed Devins、Devin Review

调研日期 2026-09-13。来源只取 docs.devin.ai（通过 `https://docs.devin.ai/<path>.md` 取原始 Markdown）与 cognition.ai 博客原页，另有两处第三方搜索结果单独标出。每条事实附 URL 与英文原文短引语；"推断"表示文档没有直说、由我从已读内容推出；"未找到"表示在已读页面和搜索中都没有官方说法。

---

## 1. Knowledge

### 1.1 条目字段

- UI 字段：Trigger Description（必填）、Content、可选 macro、按用户启用/停用、文件夹、pin 的仓库范围。
  - https://docs.devin.ai/product-guides/knowledge ："all Knowledge requires a trigger description." ／"**Content** should be a handful of sentences with relevant information."
  - macro："a short identifier starting with `!` (e.g., `!deploy-checklist`) ... must be unique within your organization."
  - 启用/停用是按用户的："Each knowledge item can be individually **enabled or disabled** per user. Disabling a knowledge item prevents Devin from retrieving it in your sessions, without deleting it from the organization."
  - 文件夹："Nested hierarchy"、"Bulk enable/disable"、"Auto-organize — Select multiple knowledge items and let Devin automatically sort them into logical folders."
- API v3 字段（`POST /v3/organizations/{org_id}/knowledge/notes`）：请求体 `name`、`body`、`trigger`（这三个必填）、`folder_id`、`is_enabled`、`pinned_repo`；响应另有 `note_id`、`folder_path`、`access_type`（enum `enterprise`/`org`）、`macro`、`created_at`、`updated_at`、`org_id`。
  - https://docs.devin.ai/api-reference/v3/notes/post-organizations-knowledge-notes （OpenAPI 片段 `KnowledgeNoteCreateRequest` / `KnowledgeNoteResponse`）
  - 权限："Requires a service user with the `ManageOrgKnowledge` permission"
- API v1 字段（`POST /v1/knowledge`）：`name`、`body`、`trigger_description`（必填）、`parent_folder_id`、`pinned_repo`；响应带创建者 `full_name`。
  - https://docs.devin.ai/api-reference/v1/knowledge/create-knowledge
- 响应里没有版本号、过期时间、来源（手写/建议/导入）字段。**未找到** knowledge 的版本历史（对比：playbook 有版本历史，见 2.3）。

### 1.2 检索机制：按触发，外加 pin 的强制注入

- 按相关性检索，不是一次全部加载："Devin retrieves Knowledge when relevant, not all at once or all at the beginning. Be sure to make your retrieval trigger highly relevant to the contents." — https://docs.devin.ai/product-guides/knowledge
- 命中后读全文："Devin will read the entire Knowledge contents, so keep it all relevant and up-to-date!"
- pin 三档改变检索规则（同页）：
  - "Pinning to **no repo**: The Knowledge is only retrieved when Devin decides it's relevant to your current context."
  - "Pinning to **a specific repo**: The Knowledge is always used whenever Devin is working in that specific repo."
  - "Pinning to **all repos**: The Knowledge automatically applies to every repo that Devin is working on in any session."
- 会话内可见用了哪些条目："Devin will tell you in a session what Knowledge it used; you can see this under "Accessed Knowledge" in the session chat." — https://docs.devin.ai/onboard-devin/knowledge-onboarding
- API 建会话时可限定知识集合：v1 `knowledge_ids` "List of knowledge IDs to use. If None, use all knowledge. If empty list, use no knowledge." — https://docs.devin.ai/v1-openapi.yaml （`CreateSessionParams`）；v3 `SessionCreateRequest` 也有 `knowledge_ids`（无描述）— https://docs.devin.ai/v3-openapi.yaml
- 检索的具体算法（嵌入检索、LLM 判断还是关键词）：**未找到**。
- 与 blueprint 里的 `knowledge` 段是两套东西：blueprint 的 `knowledge` "Not executed. Loaded into Devin's context at session start."，且 "**Knowledge is per-repository.** If you have 5 repositories configured, Devin only sees the knowledge entries for the one it's working on." — https://docs.devin.ai/onboard-devin/environment/blueprints ；文档明确分工："The `knowledge` section in your blueprint is for short command references tied to the environment. For architecture docs, conventions, and team workflows, use the standalone Knowledge feature instead."

### 1.3 数量与长度限制

- 企业级 knowledge 条目上限 300："The maximum number of enterprise knowledge items has been increased from 200 to 300."（2026-06-17）— https://docs.devin.ai/release-notes/2026
- 组织级条目数上限、单条字符上限：**未找到**。文档只给写作建议："a handful of sentences"。
- 相邻限制（DeepWiki 的 `repo_notes`，不是 Knowledge）："Maximum 10,000 characters per note"— https://docs.devin.ai/work-with-devin/deepwiki

### 1.4 建议知识：何时产生、如何审批

- 触发来源是聊天中的用户反馈："Devin will automatically suggest Knowledge to remember based on your feedback in chat. Edit the suggested Knowledge before saving, or dismiss the Knowledge if it's not helpful." — https://docs.devin.ai/product-guides/knowledge
- 可以让 Devin 按反馈重写建议，也会建议改已有条目："You can also request Devin to regenerate a Knowledge Suggestion based on your feedback ... Devin can also suggest updates to existing knowledge items in addition to suggesting new knowledge items."
- UI 位置：会话 worklog 中的独立事件（2026-06-17）："When Devin suggests a knowledge item during a session, it now appears as a standalone event in the worklog for easier visibility and review." — https://docs.devin.ai/release-notes/2026 ；企业非主组织还有 **Suggestions** 标签页："AI-generated knowledge suggestions based on your session interactions (shown for non-primary organizations)." — https://docs.devin.ai/product-guides/knowledge
- API/MCP 可审建议：`devin_knowledge_manage` "Also manage knowledge suggestions — list, view, and dismiss pending suggestions." — https://docs.devin.ai/work-with-devin/devin-mcp 。MCP 表述里只有 list/view/dismiss，没有写 accept（**推断**：接受走 UI 或直接 create note）。
- 会话中 Devin 直接写入知识库（不经建议）：2025-11-07 "Improved agentic knowledge management, allowing Devin to contribute knowledge base entries within the folder hierarchy during sessions." — https://docs.devin.ai/release-notes/2025 。它与"建议-审批"之间的边界（是否仍需人批准）：**未找到**。
- 自动生成仓库知识："Devin will automatically generate repo knowledge based on the existing READMEs, file structure and contents of the connected repositories." — https://docs.devin.ai/onboard-devin/knowledge-onboarding ；建议人工复核："Review any auto-generated Knowledge and verify for (a) completeness and (b) accuracy."
- 另有 "skills 建议"（写回仓库而不是知识库），见 7.2。

### 1.5 陈旧、删除、冲突

- 有删除（UI 与 API v1/v3 DELETE）、有停用（按用户、按文件夹）。
- 过期/TTL：**未找到**。
- 自动冲突检测：**未找到**产品内置的写入时冲突检测。存在两条事后机制：
  1. Session Insights 的 **Misleading Knowledge**："lists knowledge items that led Devin astray or contained outdated or incorrect information. Each entry explains why the knowledge was harmful" — https://docs.devin.ai/product-guides/session-insights ；原因之一列为 "Knowledge conflicts with other knowledge items"。API 字段 `note_usage.good_usages` / `bad_usages`，每项含 `note_id`、`reason`、`message` — https://docs.devin.ai/api-reference/v3/sessions/get-organizations-session-insights
  2. 用 Advanced Capabilities 让 Devin 整理："Find and merge duplicate knowledge entries"、"Resolve conflicting guidance"；推荐顺序 "Start with deduplication to reduce noise / Then resolve conflicts to ensure consistency / Finally, fill gaps by creating knowledge from codebase analysis"；并建议排定时任务 "runs every Monday at 8 AM to review pending knowledge suggestions, deduplicate entries, and resolve conflicting guidance." — https://docs.devin.ai/work-with-devin/advanced-capabilities
- 文档对陈旧的定性："a single outdated knowledge item can degrade session quality across your entire team." — https://docs.devin.ai/product-guides/session-insights

### 1.6 规则文件自动导入与同步

- "Devin will automatically pull and update Knowledge based on specialized files in your codebase including `.rules`, `.mdc`, `.cursorrules`, `.windsurf`, `CLAUDE.md`, and `AGENTS.md`. Note that Devin won't automatically pull in more general file types like `.md`." — https://docs.devin.ai/onboard-devin/knowledge-onboarding
- AGENTS.md："Devin will look for the file before it starts coding." — https://docs.devin.ai/onboard-devin/agents-md
- 同步时机（按提交、按索引刷新还是按会话 clone）：**未找到**。**推断**：文档用 "pull and update"，且仓库索引按分支进行（https://docs.devin.ai/onboard-devin/index-repo："index the branches your team actively develops on"），导入可能随索引刷新；未验证。
- 相邻机制写得清楚的是 skills 的双源发现（索引 + 会话内磁盘扫描，磁盘优先），见 7.2。

### 1.7 Organization → Enterprise 提升

- 三个标签页：Organization Knowledge（默认作用域）、Suggestions、Enterprise Knowledge — https://docs.devin.ai/product-guides/knowledge
- 提升流程："Open the item, then click **Promote to Enterprise** in the Details tab. The item is moved from organization scope to enterprise scope"；条件："Promotion requires enterprise knowledge management permissions, and is only available for user-created knowledge items in organizations that belong to an enterprise."（**推断**：自动生成/导入的条目不能提升。）
- 共享默认值：2025-10-10 "Knowledge entries now default to being shared within your organization."；2025-09-12 API v2 `shared_in_org` "true applies knowledge to the entire organization, false applies only to the creator of the knowledge." — https://docs.devin.ai/release-notes/2025
- 相关 2025-11-07："Added the ability to provide enterprise-wide knowledge for the synchronous repository setup agent" — https://docs.devin.ai/release-notes/2025

### 1.8 API 端点

| 版本 | 端点 | 来源 |
| --- | --- | --- |
| v1 | `GET/POST /v1/knowledge`，更新、删除（List all knowledge "entries and folders"） | https://docs.devin.ai/api-reference/v1/knowledge/list-knowledge 、create-knowledge |
| v2 | 企业 knowledge 共享字段 `shared_in_org`（release note 提及）；v2 的独立 knowledge 端点在 API 索引中**未找到** | https://docs.devin.ai/release-notes/2025 、https://docs.devin.ai/_llms/en/api.md |
| v3 org | `/v3/organizations/{org_id}/knowledge/notes`（list 支持 `search`、`folder_path`、`pinned_repo`、分页 `after`/`first`）、`/notes/{note_id}`（GET/PUT/DELETE）、`/knowledge/folders`（"full folder tree with per-folder note counts"） | https://docs.devin.ai/v3-openapi.yaml |
| v3 enterprise | `/v3/enterprise/knowledge/notes`、`/notes/{note_id}`、`/knowledge/folders` | 同上 |
| MCP | `devin_knowledge_manage` | https://docs.devin.ai/work-with-devin/devin-mcp |

- v3 API 中知识建议（suggestions）的端点：**未找到**（只在 MCP 中出现）。

---

## 2. Playbooks

### 2.1 结构

- 定位："A playbook is like a custom system prompt for a repeated task." — https://docs.devin.ai/product-guides/creating-playbooks
- 可选段落：Procedure / Specifications（"Describe postconditions - what should be true after Devin is done?"）/ Advice（"Include tips to correct Devin's priors"）/ Forbidden Actions / Required from User。
- Procedure 写法："one step per line, each line written imperatively"、"Include at least one step for setup, the actual task, and delivery"、"Aim to make the steps Mutually Exclusive and Collectively Exhaustive"。
- 迭代建议："Run 2+ Devins in parallel with the same playbook to quickly identify possible errors."；"If Devin needs help, chat with it to help it along. Then add to your playbook so Devin succeeds without intervention next time."
- 文件形式：`.devin.md` 拖入会话；附加成功时出现 blue pill 与内联编辑器。
- API v3 字段 `title`、`body`（必填）、`macro`、`structured_output_schema`（"JSON Schema (Draft 7) that sessions using this playbook will produce as structured output. Max 64KB."）— https://docs.devin.ai/api-reference/v3/playbooks/post-organizations-playbooks
- 2026-06-05 "Playbooks can now specify a Devin mode (e.g., Fast or Normal)."；2026-06-17 "Playbooks now support a structured output schema" — https://docs.devin.ai/release-notes/2026

### 2.2 宏

- "a short identifier starting with `!` (e.g., `!data-tutorial`). Macros let you quickly attach a playbook to a session by typing its macro name" — https://docs.devin.ai/product-guides/creating-playbooks
- 2026-07-24 悬停宏可预览内容；2026-08-12 Slack 消息中的 playbook 提及会被解析 — https://docs.devin.ai/release-notes/2026
- 自动化可引用宏："Attach automation macros to playbooks for trigger-based workflows." — https://docs.devin.ai/work-with-devin/advanced-capabilities

### 2.3 版本

- "Each time you edit and save a playbook, a new version is created. You can view previous versions and revert to an earlier version" — https://docs.devin.ai/product-guides/creating-playbooks
- 2026-03-19 上线，同时 playbook 页显示 "session count, unique users, and merged PRs per playbook, with a weekly activity chart." — https://docs.devin.ai/release-notes/2026 。2025-11-07 "Added analytics for when playbooks are retrieved during sessions." — https://docs.devin.ai/release-notes/2025

### 2.4 从会话生成、"改进 playbook"

- 从会话生成："Share one or more session links and describe the playbook you want. Devin analyzes the sessions and produces a structured playbook with procedures, specifications, and advice." — https://docs.devin.ai/work-with-devin/advanced-capabilities
- 改进：成败对比："Reference the playbook and share sessions where it fell short. Devin compares successes and failures to propose targeted improvements."；示例 prompt："Our !db-migration playbook keeps failing on foreign key constraints. Here are 4 recent sessions — analyze the failures, compare them to the successes, and update the playbook"。
- 这是由用户在会话里发起的能力（需 `UseDevinExpert` 权限），不是后台自动流程。自动定期改进：**未找到**（可用 schedule 手工排，见 7.3）。
- 相反方向：Skills 有自动建议（7.2），playbooks 没有："Auto-suggestion ... Playbooks: Created manually by team members" — https://docs.devin.ai/product-guides/skills

### 2.5 Community / Enterprise playbooks

- Community："select one from your Team or the Community library"；Community Gallery 位于 https://app.devin.ai/settings/playbooks — https://docs.devin.ai/product-guides/using-playbooks 。社区库的投稿/审核机制：**未找到**。
- Enterprise："Enterprise playbooks are shared across all organizations in your enterprise" — https://docs.devin.ai/product-guides/creating-playbooks ；2025-10-10 上线（release-notes/2025）；2026-07-15 "Admins can now promote a playbook from a single organization to the entire enterprise" — https://docs.devin.ai/release-notes/2026
- API：v1 `/v1/playbooks`，v2 企业 playbooks，v3 `/v3/organizations/{org_id}/playbooks` 与 `/v3/enterprise/playbooks` — https://docs.devin.ai/_llms/en/api.md

### 2.6 Skills 与 Playbooks 的分工（2026 年新增的第三层）

- "If your instructions are tied to a specific repo — how to run it, test it, or deploy it — use a skill. If your instructions are general-purpose prompts that apply across repos or teams, use a playbook." — https://docs.devin.ai/product-guides/skills
- "Devin can only have one skill active at a time. Invoking a new skill replaces the previous one."（同页 Limitations 与正文）

---

## 3. Session Insights

- 产生时机："When a session ends, Devin automatically generates a lightweight classification (category, languages, and tools). For large sessions (L or XL), a full analysis is also generated automatically at teardown. For smaller sessions, you can trigger a full analysis manually" — https://docs.devin.ai/product-guides/session-insights 。2026-03-13 改为按需生成、L/XL 仍自动 — https://docs.devin.ai/release-notes/2026
- 规模分级：XS–XL，按 ACU 与用户消息数取较大者；"Sessions classified as **L** or **XL** are flagged as unhealthy"。
- 输出三个标签页：
  1. **Issue Timeline**：Issues（label、impact high/medium/low、description）+ 按颜色的时间线（红=高影响问题，绿="Value provided"）。
  2. **Actionable Feedback**：Improved Prompt（带 "Changes Made" 列表，按钮 "Start new session"）+ Action Items（Machine setup / Repo config，按钮 "Go to machine"）。API 的 action item `type` 枚举：`machine_setup`、`repo_config`、`knowledge`、`prompt_improvement`、`external`、`other` — https://docs.devin.ai/api-reference/v3/sessions/get-organizations-session-insights
  3. **Knowledge Usage**：Useful Knowledge / Misleading Knowledge，"Click on any knowledge item to navigate directly to it and make edits."
- 是否自动回写知识或 playbook：**否（按文档）**。文档全部是"建议 + 跳转让人改"："Update or delete the flagged knowledge items."、"Add key learnings as Knowledge so your teammates can benefit from them."、"Save your best prompts as Playbooks"。自动回写：**未找到**。
- 深挖入口："The **Investigate with Devin** button ... opens a new Devin session pre-configured to analyze the original session in depth."
- API：`/v3/organizations/{org_id}/sessions/insights`（列表）、`/sessions/{devin_id}/insights`、`/insights/generate`；企业同构。响应还带 `parent_session_id`、`child_session_ids`、`playbook_id`、`structured_output`。

---

## 4. DeepWiki 与 Ask Devin

### 4.1 索引与刷新

- 索引按分支：选择分支索引，"To index additional branches later, click **Manage** ... **Add branch**." — https://docs.devin.ai/onboard-devin/index-repo
- 刷新频率：官方文档**未找到**。第三方文章称按计划而非每次提交刷新（非官方，未核实）：https://fast.io/resources/devin-deepwiki-guide/ 、https://codersera.com/blog/deepwiki-complete-guide-2026/ 。Cognition 年度回顾把它称为 "comprehensive, always-updating documentation"（2025-11-14，https://cognition.ai/blog/devin-annual-performance-review-2025），但没有给频率。
- 环境快照的刷新是有明确数字的（别混淆）："Builds run automatically when your blueprint changes and periodically (every ~24 hours)." — https://docs.devin.ai/onboard-devin/environment/blueprint-reference
- 生成成本分级：Low（免费，默认）/ Medium ~5-10 ACUs / High ~20-40 ACUs；"Enterprise orgs always run at low effort" — https://docs.devin.ai/work-with-devin/deepwiki

### 4.2 `.devin/wiki.json`

- 位于仓库根，字段 `repo_notes`（必填，可为空数组；每条 `content` ≤10,000 字符、`author` 可选）与 `pages`（必填，至少 1 页；`title` 唯一、`purpose`、`parent`、`page_notes`）。
- 语义是"完全替代自动规划"："When a config file is present, we bypass the default cluster-based planning and create exactly the pages you specify — so list every page you want."
- 限制："Maximum 30 pages (80 for enterprise)"、"Maximum 100 total notes"。
- 生效方式："Commit the file and regenerate your wiki" — https://docs.devin.ai/work-with-devin/deepwiki

### 4.3 Ask Devin → 会话

- 两种用途：Ask（带引用的代码问答）与 Plan："Devin generates a context-rich prompt based on what it learns, ready to hand off to an Agent session." — https://docs.devin.ai/work-with-devin/ask-devin
- 从对话起会话后状态回显："the **session status is displayed directly in the Ask Devin conversation**"；截图说明 "Devin writes a context-rich prompt from your session"。
- Ask Devin 使用 Wiki："Ask Devin will use information in the Wiki to better understand and find the relevant context" — https://docs.devin.ai/work-with-devin/deepwiki
- 内部实践（2026-02-27）："Devin starts with clear context from our exploration, and the prompt is automatically tailored to our task." — https://cognition.ai/blog/how-cognition-uses-devin-to-build-devin
- 会话中也能用：2025 release note "At any point during a session, ask a question, and Devin will provide a DeepWiki-like answer, complete with code citations." — https://docs.devin.ai/release-notes/2025 ；多 agent 文章把它称为只读子 agent："Devin can call out to a Deepwiki subagent to acquire codebase context." — https://cognition.ai/blog/multi-agents-working

### 4.4 跨仓库检索

- MCP `ask_question`："Ask any question about one or more repositories (up to 10)" — https://docs.devin.ai/work-with-devin/devin-mcp
- Ask Devin 网页端的跨仓库范围：**未找到**明确说法；gallery 示例是单仓库问题。

---

## 5. Managed Devins（coordinator 派子会话）

### 5.1 能力清单

- 发布日期 2026-03-19："Each managed Devin is a full Devin, running in its own isolated virtual machine with its own terminal, browser, and development environment ... Each has its own session link, so you can inspect its work or message it directly." — https://cognition.ai/blog/devin-can-now-manage-devins
- coordinator 能做："Spin up managed Devins — launch child sessions with specific prompts, playbooks, tags, and ACU limits"、"Message child sessions"、"Monitor ACU consumption"、"Put child sessions to sleep or terminate them"、"Schedule messages to itself — set reminders to check back on long-running child sessions" — https://docs.devin.ai/work-with-devin/advanced-capabilities
- 启动前人批准："Devin analyzes your request and proposes the sessions for your approval before launching them."（同页）
- 设计理由："when one agent tries to handle too many things in a single session, context accumulates, focus degrades ... Each managed Devin gets a clean slate, a narrow focus, its own shell, and its own test runner." — 博客同上
- 内部通道："A manager Devin can break a larger task into pieces, spawn child Devins to work on them, and coordinate their progress through an internal MCP." — https://cognition.ai/blog/multi-agents-working （2026-04-22）。对外同类工具：`devin_session_create`、`devin_session_interact`、`devin_session_events`、`devin_session_gather`（"Wait for multiple sessions to reach a settled state ... instead of polling in a loop"）— https://docs.devin.ai/work-with-devin/devin-mcp

### 5.2 子会话继承什么

- 显式传入：prompt、playbook、tags、ACU limit（见上）。API 另有 `child_playbook_id`、`session_links`、`knowledge_ids`、`structured_output_schema` — https://docs.devin.ai/v3-openapi.yaml
- 平台位置继承："When omitted (or set to 'inherit'), a session created by a parent Devin inherits the parent's placement — both its platform and its outpost pool" — 同上 `SessionCreateRequest.platform`
- 知识：**推断**子会话是同组织的普通会话，因此组织 Knowledge、pin 规则、环境快照与 skills 都照常适用；文档没有专门写"子会话继承知识"。
- 会话历史：**不继承**（**推断**，依据：各自独立 VM、"clean slate"；Devin CLI 子 agent 明文 "does not inherit the parent's conversation history" — https://docs.devin.ai/cli/subagents ，但那是本地 CLI，不是云端 managed Devins）。
- 结构化返回：2026-04-03 "Child sessions can return structured JSON via schema for automated workflows." — https://docs.devin.ai/release-notes/2026

### 5.3 父子消息与结果汇总

- 父→子：message child sessions；子→父：父读取子的完整轨迹 "Devin can also read the full trajectories of its managed Devins to understand what worked, what didn't, and where they got stuck, and use that to improve how it breaks down the next task." — https://cognition.ai/blog/devin-can-now-manage-devins
- 已知缺陷（2026-04-22）："Managers trained on small-scoped delegation default to being overly prescriptive, which backfires when the manager lacks deep codebase context. Agents assume they share state with their children when they don't. Cross-agent communication, a sub-agent writing messages back to its manager to be passed to other agents in the agent team, doesn't happen by default" — https://cognition.ai/blog/multi-agents-working
- UI：2026-03-27 "Agents" 标签页 "showing their status, todos, and PRs in one place"；2026-03-19 父子会话在侧栏分组；2026-09-09 "Archiving a session now also closes the open pull requests of the child sessions" — https://docs.devin.ai/release-notes/2026

### 5.4 共享可写状态与冲突

- 默认不共享：Dynamic Workflows 文档："A full child Devin session with its own machine ... It cannot see the orchestrating session's files, so code handoffs go through git branches: each agent pushes a branch and reports the branch name" — https://docs.devin.ai/work-with-devin/dynamic-workflows
- 可选共享 VM："shares its working tree, including uncommitted changes ... Because they share one working tree with no isolation, parallel writers must be given strictly non-overlapping files or directories."（同页）
- 冲突预防靠拆分：示例 prompt "Group them into independent work packages that won't conflict"、"no two groups should modify the same file or share mutable state"；有依赖的组串行："Will launch Auth first, then Admin after Auth's PR merges." — https://docs.devin.ai/use-cases/gallery/parallelize-migration
- 冲突发生后：coordinator "resolves conflicts"（advanced-capabilities 原文 "scoping work, monitoring progress, resolving conflicts, and compiling results"），具体机制**未找到**；gallery 另一例写的是人来解："If two sessions touched a shared test helper, resolve the conflict manually or ask Devin to fix it." — https://docs.devin.ai/use-cases/gallery/batch-test-coverage
- 共享可写"记忆"的特例：Auto-triage 父子共享 scratchpad："The parent monitor and all child sub-devins share a persistent scratchpad ... The parent is primarily responsible for maintaining it, but children can read it for context and update it" — https://docs.devin.ai/product-guides/auto-triage

### 5.5 Dynamic Workflows（managed Devins 的脚本化形态）

- "A dynamic workflow is a **deterministic Python script that orchestrates a team of Devin agents**" — https://docs.devin.ai/work-with-devin/dynamic-workflows
- 原语：`register_workflow`、`agent(prompt, phase, schema)`、`pipeline(items, stage1, ...)`（"no barrier between stages"）、`parallel([...])`、`log`。
- 可恢复："each agent call is keyed by a hash of its prompt, schema, and execution settings. Everything that already completed replays from its recorded result"；因此 "Workflow logic and prompts must not depend on the current time or date, randomness, generated IDs, environment variables, filesystem state, or network responses."
- 失败处理由脚本决定："skip the item, substitute a default, retry, or fail the run. A resumed run retries failed agents with new sessions."；运行预算上限 7 天。
- 何时不用："The work is tightly coupled through shared state, or is small and sequential."
- 可存为 skill："committed to your repo as a skill: a `workflow.py` next to a `SKILL.md`"。

---

## 6. Devin Review 与编码会话的上下文关系

- 读取的上下文：仓库指令文件 `**/REVIEW.md`、`**/AGENTS.md`、`**/CLAUDE.md`、`**/CONTRIBUTING.md`、`.cursorrules`、`.windsurfrules`、`.cursor/rules`、`*.rules`、`*.mdc`、`.coderabbit.yaml`、`greptile.json`；子目录作用域："`src/.agents/REVIEW.md` applies to files under `src/`"；可在 Settings > Review 加自定义 glob（例 `docs/**/*.md`）— https://docs.devin.ai/work-with-devin/devin-review 。安全扫描读 SECURITY.md（2026-06-17 release note）。
- **是否读取 Knowledge 库**：Devin Review 文档全文未提 Knowledge（我对该页 479 行全文 grep "knowledge" 无结果）→ **未找到**。**推断**：评审上下文来自仓库文件而非知识库。
- Review → 编码会话：
  - 评审内对话可改代码："Ask the chat agent to make code edits ... apply them as a commit to the PR branch"。
  - Auto-Fix：开启后 Devin 会话处理 Devin Review 的评论；"Devin Review's **No Issues Found** summary comments are always ignored. Only comments with actual findings trigger Auto-Fix."（同页）
  - PR 评论 `/devin review` 触发评审；"Other `/devin` comments (for example `/devin fix the failing test`) start a regular Devin session on the PR instead of a review."
  - 博客（2026-02-10）："Devin can now be configured to autofix incoming review comments from Devin Review and other review bots." — https://cognition.ai/blog/closing-the-agent-loop-devin-autofixes-review-comments
- 评审与编码**刻意不共享上下文**（2026-04-22）："we found this technique to work best when the coding and review agents do not share any context beforehand."；理由："it is forced to reason backward from the implementation without the spec"、"The dedicated review agent gets to skip this extraneous context, only look at the diff"；过滤责任在编码方："does Devin properly use its broader context of user instructions, decisions, etc. to filter the bugs that come back from Devin Review? This is key to preventing looping, disobeying the user, doing work that is out of scope"。数据："Devin Review catches an average of 2 bugs per PR, of which roughly 58% are severe" — https://cognition.ai/blog/multi-agents-working
- 从评审反馈产生知识：**未找到**。只有通用的"聊天反馈 → 知识建议"（1.4）；是否覆盖评审评论不明。
- 成本与防循环：每 PR 自动评审花费上限，"Once a PR's total review spend ... reaches the limit, auto-review is turned off for that PR"；"Devin Review now skips re-reviewing a PR when its diff against the base branch is unchanged"（2026 release note）；"When new commits are pushed to a PR, any in-progress Devin reviews are now automatically canceled."（2026-06 release note）。
- 发现分级：Bugs（Severe / Non-severe）、Flags（Investigate / Informational）、Security（Critical / Warning，带 CWE）；可标记 resolved。规则来源标注：Lifeguard 从规则文件标出的 bug 显示 "Repo rule" 徽章（2026 release note）。

---

## 7. Environment / 快照、Skills、Schedules、Memory/notes

### 7.1 Environment 与 blueprint（"怎么起项目"的沉淀处）

- 快照："a frozen, bootable image that every session starts from"；"Each organization has exactly one active snapshot."；"Session changes don't persist back to the snapshot." — https://docs.devin.ai/onboard-devin/environment
- 让 Devin 生成："Devin proposes a blueprint as suggestion cards in the timeline. Review the proposed setup and approve the cards you want to use."（同页）
- blueprint 段落：`initialize`（构建时运行）、`maintenance`（构建时运行；会话开始时 "surfaced to the agent as context — **not auto-executed**"）、`knowledge`（不执行，lint/test/build 命令；"By convention, `lint`, `test`, and `build` are the standard names. Devin references these when verifying its work."）、`post-build`（"A non-zero exit code fails the build, so no snapshot ships without passing your checks"）、`clone` — https://docs.devin.ai/onboard-devin/environment/blueprints 、https://docs.devin.ai/onboard-devin/environment/blueprint-reference
- 层级：enterprise → organization → repository 叠加（"Blueprints are **additive**"）；git 化：`.devin/blueprint.yaml`。
- 构建触发："Saving a blueprint"、"Adding or removing a repository"、"Periodic refresh — Automatic, roughly every 24 hours"、"Devin suggestion — Devin proposes a blueprint change during a session"；可 pin 某次构建（"must be `success` or `partial`, less than 7 days old"）。
- 旧形态 Machine Snapshots（2024-06-05）："Machine Snapshots are 'save' states for Devin." — https://cognition.ai/blog/june-24-product-update
- 云端休眠恢复（2026-04-23）："snapshotting full machine state at the hypervisor level — memory, process trees, and filesystem. Compute shuts down while the agent is idle, and the session resumes exactly where it left off when a CI result or review comment arrives." — https://cognition.ai/blog/what-we-learned-building-cloud-agents

### 7.2 Skills（2026-02-13 上线）

- 位置 `.agents/skills/<name>/SKILL.md`（另 5 个路径）；遵循 Agent Skills 标准 — https://docs.devin.ai/product-guides/skills
- 发现："Indexed repos — ... available immediately when a session starts, before any repos are cloned"；"Disk-scanned skills update or override any matching indexed skill from the same repo, ensuring Devin always uses the latest version on the branch being worked on."；"When a repo clone completes mid-session, Devin automatically re-scans that repo"。
- 自动建议并以 PR 写回："After Devin tests your application or learns something new about your setup during a session, it will suggest creating or updating a skill ... A **"Create PR"** button to commit the skill to your repo"。博客佐证（2026-05-29）："When it figures out a setup step the hard way, Devin can suggest saving that knowledge as a testing skill in the repo and propose the fix back to the user as a one-click PR." — https://cognition.ai/blog/testing-development
- `triggers: ["user"]` 禁止模型自动调用；`allowed-tools` 限制工具。
- 已知限制："skills live inside repositories. For org-wide skills, you can create a dedicated "skills" repo as a workaround."（2026-07-17 起可经 Plugins 集中分发 — release-notes/2026）

### 7.3 Schedules / Automations

- Scheduled Sessions 仍可用，但 "**Automations are now the recommended way to run Devin on a schedule.**" — https://docs.devin.ai/product-guides/scheduled-sessions
- 配置项：Recurring（cron）/ One-time、Agent（Devin / Data Analyst / Advanced）、可选 playbook、repositories、通知（默认 "On failure only"）、Run as；状态 Active / Paused / Error（"consecutive failures"）；Past Sessions 标签页。
- Automations：Trigger / Conditions / Action；Action 含 "Message session — Sends a message to an existing, long-running Devin session — useful for feeding events into a session that maintains state"；限额 "ACU limit" 与 "Invocation limit ... "at most 10 invocations per hour"" — https://docs.devin.ai/product-guides/automations

### 7.4 Memory / notes

- 定时 Devin 的跨运行笔记（2026-03-20）："Devin carries state between runs. It reads and writes its own notes across sessions, which means each run builds on the context of the one before it"；例："it won't re-summarize the PRs it already covered last week, because Devin knows where it left off" — https://cognition.ai/blog/devin-can-now-schedule-devins 。docs 的 Scheduled Sessions 页没有写这个笔记机制（**未找到**其存储位置、可见性、如何清除）。
- Auto-triage scratchpad：见 5.4，"The scratchpad is the automation's long-term memory."
- Cognition 对模型自写笔记的评估（2025-09-29）："When we relied on the model's own notes without our compacting and summarization systems, we saw performance degradation and gaps in specific knowledge: the model didn't know what it didn't know" — https://cognition.ai/blog/devin-sonnet-4-5-lessons-and-challenges
- 通用、用户可浏览的 "Memory" 产品：**未找到**（Knowledge 承担此角色）。

---

## 8. Cognition 博客论点（按日期）

| 日期 | 文章 | 论点与原文 |
| --- | --- | --- |
| 2024-06-05 | [June '24 Product Update](https://cognition.ai/blog/june-24-product-update) | Knowledge 与 Playbook 分工："Create Playbooks for common, recurring tasks ... Add Knowledge to teach Devin general context about your organization that is relevant for all runs, with and without Playbooks." |
| 2025-06-12 | [Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)（Walden Yan） | 两条原则："Share context, and share full agent traces, not just individual messages"；"Actions carry implicit decisions, and conflicting decisions carry bad results"。"The simplest way to follow the principles is to just use a single-threaded linear agent"。长任务用压缩模型："a new LLM model whose key purpose is to compress a history of actions & conversation into key details, events, and decisions"。"running multiple agents in collaboration only results in fragile systems." |
| 2025-09-29 | [Rebuilding Devin for Claude Sonnet 4.5](https://cognition.ai/blog/devin-sonnet-4-5-lessons-and-challenges) | "context anxiety"："the model taking shortcuts or leaving tasks incomplete when it believed it was near the end of its window"；模型自写笔记不足以替代系统记忆（见 7.4）；"you have to be very careful about when to use subagents because the context and state management gets complex quickly." |
| 2025-11-14 | [Devin's 2025 Performance Review](https://cognition.ai/blog/devin-annual-performance-review-2025) | "Devin excels at tasks with clear, upfront requirements and verifiable outcomes"；"PR review ... Human review is still necessary, because code quality is not straightforwardly verifiable." |
| 2026-01-21 | [Devin Review: AI to Stop Slop](https://cognition.ai/blog/devin-review) | "code review—not code generation—is now the bottleneck"；"Lazy LGTM problem"。 |
| 2026-02-10 | [Closing the Agent Loop](https://cognition.ai/blog/closing-the-agent-loop-devin-autofixes-review-comments) | "One agent writes, the other pressure-tests, and this continues in a loop."；"The human's job narrows to the decisions that require judgment"。 |
| 2026-02-27 | [How Cognition Uses Devin to Build Devin](https://cognition.ai/blog/how-cognition-uses-devin-to-build-devin) | 内部流程：Ask Devin 探索后起会话；"!triage-bug playbook"；"An AI software engineer with clear context, working autonomously on well-scoped tasks, is a force multiplier." |
| 2026-03-19 | [Devin can now Manage Devins](https://cognition.ai/blog/devin-can-now-manage-devins) | 见 5.1；"Over time, each managed Devin makes the next one more effective." |
| 2026-03-20 | [Devin can now Schedule Devins](https://cognition.ai/blog/devin-can-now-schedule-devins) | 跨运行笔记，见 7.4。 |
| 2026-04-22 | [Multi-Agents: What's Actually Working](https://cognition.ai/blog/multi-agents-working)（Walden Yan） | 修正版立场："a narrower class of patterns that do: setups where multiple agents contribute intelligence to a task while writes stay single-threaded"；评审循环 clean context（见 6）；"Smart Friend" 大模型顾问："a reasonable 80/20 solution is to just share a fork of the full context of the primary model with the smart model"；反馈方向："the right answer from the smart model is not to make up some theories ... but to specifically instruct the primary model to investigate this file and ask again later"；群体架构："unstructured-swarm approach ... is mostly a distraction. The practical shape is map-reduce-and-manage"；"The open problems are all communication problems." |
| 2026-04-23 | [What We Learned Building Cloud Agents](https://cognition.ai/blog/what-we-learned-building-cloud-agents) | async 间隙需保存完整机器状态（见 7.1）；"Review and quality standards: The volume of code that needs review increases dramatically" |
| 2026-05-29 | [Verifying Agentic Development at Scale](https://cognition.ai/blog/testing-development)（Ido Pesok） | "For the first time, more Devin sessions are triggered asynchronously than interactively."；测试计划必须基于源码："This plan must be grounded in source, not assumptions."；先写预期再动作："Devin will lie less about its findings if it annotates its expected behavior right before performing an action"；重复步骤抽成确定性脚本放进 testing skill；失败模式 "cheating ... executing JavaScript in the browser to trigger states programmatically instead of clicking through the UI"。 |

---

## 9. 对 spec → 票 → 夜间多 worker → reviewer/verifier → 合并 流水线可借鉴的机制

每条写：机制（Devin 出处）→ 解决的问题 → 前提。

1. **知识条目 = 触发描述 + 正文 + 作用域 pin**（1.1、1.2）
   - 解决：worker 启动时把所有规则一次塞进上下文，既浪费又淹没重点；pin 到仓库保证硬规则必到，未 pin 的按任务相关性取。
   - 前提：触发描述写得具体（文件、仓库、任务类型）；有一个"本次会话读了哪些条目"的可见记录（Devin 的 "Accessed Knowledge"），否则无法审计。

2. **反馈 → 知识建议 → 人审批（可编辑、可重生成、可更新旧条目）**（1.4）
   - 解决：夜里 worker 被纠正过的事，第二夜又犯；同时避免 agent 未经审核直接写入长期规则。
   - 前提：有一个晨间审批队列；建议要能指向已有条目做"更新"而不是只新增，否则会重复堆积。

3. **事后会话分析把知识标为 Useful / Misleading，并给出带类型的 action item**（3）
   - 解决：陈旧或互相冲突的规则不会自己暴露；按 `machine_setup` / `repo_config` / `knowledge` / `prompt_improvement` 分类后，晨间处理可以直接分派。
   - 前提：保存完整会话轨迹；分析只做建议，不自动改规则（Devin 也是这样做的）；只对大/失败会话自动跑以控制成本（Devin 以 L/XL 为阈值）。

4. **定期的"知识维护"会话：先去重、再解冲突、再补缺**（1.5）
   - 解决：知识库只增不减导致冲突；把维护变成排好的例行任务而非靠人想起来。
   - 前提：知识以可枚举、可 diff 的形式存放；维护会话产出的是待批准的变更，不是直接覆盖。

5. **成败会话对比来改进 playbook，playbook 有版本和使用统计**（2.3、2.4）
   - 解决：同一类票反复失败时，按"失败轨迹 vs 成功轨迹"定位缺失步骤，而不是凭印象改 prompt；版本可回退。
   - 前提：每个会话记录它用了哪个 playbook 版本；有成功判定（Devin 用 merged PRs 计数）。

6. **coordinator 先提出分组方案，人批准后才派发；分组准则是"不改同一文件、不共享可变状态"，有依赖的组串行**（5.1、5.4）
   - 解决：并行 worker 在合并时互相冲突；把冲突风险前移到派发前的一次人工确认。
   - 前提：能在派发前算出文件/依赖图（Devin 用 Ask Devin/DeepWiki）；票之间的 blocking 边是显式的。

7. **子 worker 各自独立机器，交接只走 git 分支 + 结构化输出（JSON Schema）**（5.4、5.5）
   - 解决：worker 误以为共享状态（Cognition 明确列为已知缺陷 "Agents assume they share state with their children when they don't"）；结构化结果让下一阶段不用解析自然语言。
   - 前提：每个 worker 的结果有固定 schema（分支名、摘要、状态）；合并步骤单线程。

8. **可恢复的编排：每次 agent 调用以 (prompt, schema, 设置) 的哈希为键记录结果，重跑时已完成的直接回放**（5.5）
   - 解决：夜里中断后从头重跑浪费算力，或手工判断"哪些做过了"。
   - 前提：编排逻辑确定性——不依赖当前时间、随机数、环境变量、文件系统或网络；凡需要读外部世界的都放进被记录的 agent 调用里。

9. **reviewer 与 coder 不共享上下文，但由 coder 按自己掌握的用户指令过滤评审发现**（6）
   - 解决：reviewer 被 coder 的长上下文和错误前提带偏；同时防止 coder 盲从评审导致越界、打转、违背用户指令。
   - 前提：reviewer 只拿 diff + 仓库指令文件（REVIEW.md 等）；有防循环手段——每 PR 花费上限、diff 未变不重评、新提交取消进行中的评审。

10. **验证者先写基于源码的测试计划，动作前先写预期，重复性前置步骤抽成确定性脚本**（8，2026-05-29）
    - 解决：验证 agent 跑偏、把意外结果合理化成 pass、在登录等重复步骤上耗时且不稳定。
    - 前提：验证产物是可复查的证据（带标注的截图/录像、逐条 pass/fail/untested）；脚本放进版本库并可被一键 PR 更新。

11. **"怎么起项目"放进可版本化的 blueprint：构建时执行、会话开始时只作为上下文呈现依赖命令、post-build 检查失败则不产出快照、可 pin 某次构建**（7.1）
    - 解决：每个 worker 各自摸索环境；环境回归影响整夜所有票。
    - 前提：环境定义与知识分开存放（Devin 明确区分 blueprint `knowledge` 与 Knowledge 产品）；周期性重建（Devin 约 24 小时）加回滚能力。

12. **长期运行的监控者与子 worker 共享一个 scratchpad，父负责维护、子可读可补充**（5.4、7.4）
    - 解决：跨夜去重（已处理的事件、重复报告）与路由表（代码区域 → 负责人）没有落脚处。
    - 前提：单一维护者（父）以避免并发写冲突；scratchpad 不承载票据状态本身。Cognition 自己的评估提醒：模型自写笔记不能替代系统级的状态记录。

13. **可复用程序写回仓库（SKILL.md），会话开始用索引版本、clone 后以分支上的磁盘版本覆盖**（7.2）
    - 解决：worker 读到的是旧版本流程；中途改了流程要重启。
    - 前提：程序文件与代码同分支版本化；同一时刻只激活一个程序（Devin 的限制），或明确组合规则。

---

## 读过的 URL

docs.devin.ai（均以 `.md` 形式获取原文）：
- https://docs.devin.ai/llms.txt
- https://docs.devin.ai/_llms/en/api.md
- https://docs.devin.ai/product-guides/knowledge
- https://docs.devin.ai/onboard-devin/knowledge-onboarding
- https://docs.devin.ai/onboard-devin/agents-md
- https://docs.devin.ai/product-guides/creating-playbooks
- https://docs.devin.ai/product-guides/using-playbooks
- https://docs.devin.ai/product-guides/skills
- https://docs.devin.ai/product-guides/session-insights
- https://docs.devin.ai/work-with-devin/advanced-capabilities
- https://docs.devin.ai/work-with-devin/dynamic-workflows
- https://docs.devin.ai/work-with-devin/devin-review
- https://docs.devin.ai/work-with-devin/ask-devin
- https://docs.devin.ai/work-with-devin/deepwiki
- https://docs.devin.ai/onboard-devin/index-repo
- https://docs.devin.ai/onboard-devin/environment
- https://docs.devin.ai/onboard-devin/environment/blueprints
- https://docs.devin.ai/onboard-devin/environment/blueprint-reference
- https://docs.devin.ai/product-guides/scheduled-sessions
- https://docs.devin.ai/product-guides/automations
- https://docs.devin.ai/product-guides/auto-triage
- https://docs.devin.ai/work-with-devin/devin-mcp
- https://docs.devin.ai/cli/subagents
- https://docs.devin.ai/use-cases/gallery/parallelize-migration
- https://docs.devin.ai/use-cases/gallery/batch-test-coverage
- https://docs.devin.ai/release-notes/2026
- https://docs.devin.ai/release-notes/2025
- https://docs.devin.ai/api-reference/v3/notes/post-organizations-knowledge-notes
- https://docs.devin.ai/api-reference/v1/knowledge/create-knowledge
- https://docs.devin.ai/api-reference/v1/knowledge/list-knowledge
- https://docs.devin.ai/api-reference/v3/playbooks/post-organizations-playbooks
- https://docs.devin.ai/api-reference/v3/sessions/get-organizations-session-insights
- https://docs.devin.ai/v1-openapi.yaml （只查 `CreateSessionParams`）
- https://docs.devin.ai/v3-openapi.yaml （只查 knowledge/playbook/insights 路径与 `SessionCreateRequest`）
- 已下载但只做关键词检索、未通读：work-with-devin/devin-handoff、work-with-devin/stacked-prs、product-guides/plugins、enterprise/environment-management/overview

cognition.ai 博客：
- https://cognition.ai/blog （索引页，列出文章 slug）
- https://cognition.ai/blog/dont-build-multi-agents
- https://cognition.ai/blog/multi-agents-working
- https://cognition.ai/blog/devin-can-now-manage-devins
- https://cognition.ai/blog/devin-can-now-schedule-devins
- https://cognition.ai/blog/devin-review
- https://cognition.ai/blog/closing-the-agent-loop-devin-autofixes-review-comments
- https://cognition.ai/blog/testing-development
- https://cognition.ai/blog/what-we-learned-building-cloud-agents
- https://cognition.ai/blog/how-cognition-uses-devin-to-build-devin
- https://cognition.ai/blog/devin-annual-performance-review-2025
- https://cognition.ai/blog/devin-sonnet-4-5-lessons-and-challenges
- https://cognition.ai/blog/introducing-devin-2-2
- https://cognition.ai/blog/deepwiki
- https://cognition.ai/blog/june-24-product-update
- 已下载但正文未取到有效内容：coding-agents-101-the-art-of-actually-getting-things-done（页面文本仅约 700 字节）、devin-2

第三方（仅用于 DeepWiki 刷新频率，非官方、未核实）：
- https://fast.io/resources/devin-deepwiki-guide/
- https://codersera.com/blog/deepwiki-complete-guide-2026/

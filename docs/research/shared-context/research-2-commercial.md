# 商业产品中"跨 agent / 跨会话 / 长期项目共享上下文"的设计调研

调研日期：2026-09-13。来源以官方文档为主；非官方来源（逆向工程、社区文章）在引用处单独标明"非官方"。"推断"标注的是我根据文档内容推出、文档没有直接写出的结论。每条引语后给出 URL。

阅读顺序建议：每节先看"要点"一行，再看细节；末尾有横向对比表和"对本流水线的可借鉴点"。

---

## 1. Claude Code（Anthropic）及 Anthropic API

要点：人写的 CLAUDE.md（层级拼接、启动时注入）+ Claude 自写的 auto memory（`MEMORY.md` 索引 + 按主题分文件，只注入前 200 行）+ agent teams 的共享任务表（文件锁认领）与每个 agent 一个 JSON 邮箱文件。API 侧有客户端执行的 memory tool；Managed Agents 有带版本、带乐观并发控制的 memory store。

### 1.1 CLAUDE.md 层级与 @import

- 文档类型与位置：managed policy（`/Library/Application Support/ClaudeCode/CLAUDE.md` 等）、用户级 `~/.claude/CLAUDE.md`、项目级 `./CLAUDE.md` 或 `./.claude/CLAUDE.md`、本地 `./CLAUDE.local.md`。"The table below lists them in load order, from broadest scope to most specific" — https://code.claude.com/docs/en/memory
- 合并方式是拼接而不是覆盖："All discovered files are concatenated into context rather than overriding each other." 子目录中的 CLAUDE.md 按需加载："they are included when Claude reads files in those subdirectories." — 同上
- 注入机制是一条 user message，不是系统提示："CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself." — 同上
- @import："CLAUDE.md files can import additional files using `@path/to/import` syntax." "Imported files can recursively import other files, with a maximum depth of four hops." 与 AGENTS.md 共存的官方写法是在 CLAUDE.md 第一行写 `@AGENTS.md`。— 同上
- 路径作用域规则 `.claude/rules/*.md`，frontmatter 例：
  ```markdown
  ---
  paths:
    - "src/api/**/*.ts"
  ---
  ```
  "Path-scoped rules trigger when Claude reads files matching the pattern, not on every tool use." — 同上
- 防膨胀：`"target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."`；HTML 注释在注入前剥掉："Block-level HTML comments (`<!-- maintainer notes -->`) in CLAUDE.md files are stripped before the content is injected"；`/doctor` 会建议删掉"content Claude can derive from the codebase"。— 同上
- 压缩后的存活："Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session." — 同上
- 冲突：文档只提示人工排查，没有机制："if two rules contradict each other, Claude may pick one arbitrarily." — 同上

### 1.2 Auto memory 与 `/memory`

- 写者是 Claude，读者是之后的每个会话："Auto memory: notes Claude writes itself based on your corrections and preferences" — https://code.claude.com/docs/en/memory
- 结构：`~/.claude/projects/<project>/memory/` 下一个 `MEMORY.md` 索引 + 每条记忆一个主题文件；frontmatter 带 `type` 字段，取值 `user` / `feedback` / `project` / `reference`。"`MEMORY.md` # Index, one line per memory, loaded into every session" — 同上
- 作用范围："all worktrees and subdirectories within the same repo share one auto memory directory"；"Auto memory is machine-local." — 同上
- 注入量上限与防膨胀："The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation." 写入后客户端检查长度："If the file is near a limit, Claude Code reminds Claude to shorten it: keep one line per entry, move detail into topic files, and merge or drop stale entries." 主题文件不在启动时加载，按需用文件工具读。— 同上
- 写什么、不写什么："Claude skips anything it can derive from the codebase, such as architecture, file paths, or debugging fixes. It also skips anything your CLAUDE.md files already say." — 同上
- 陈旧度：写入时自动加时间戳："Claude Code records the write time in a `modified` frontmatter field as an ISO 8601 timestamp." — 同上
- 人工审计：`/memory` 列出所有记忆文件并可打开编辑、开关 auto memory。— 同上

### 1.3 Subagents

- 上下文隔离："Each subagent starts with a fresh, isolated context window. It doesn't see your conversation history" — https://code.claude.com/docs/en/sub-agents
- 子 agent 初始上下文包含：自身系统提示、主 agent 写的 task message、全部 CLAUDE.md 层级、git status 快照、预加载 skills、"Sibling roster ... each a valid `to` value for `SendMessage`"。不包含主会话的 auto memory。— 同上
- 子 agent 自有持久记忆：frontmatter `memory: user|project|local`，目录分别为 `~/.claude/agent-memory/<name>/`、`.claude/agent-memory/<name>/`、`.claude/agent-memory-local/<name>/`；"`project` is the recommended default scope. It makes subagent knowledge shareable via version control." 启用时"The subagent's system prompt also includes the first 200 lines or 25KB of `MEMORY.md`"。— 同上
- 结果回传：只回一段总结；"Claude Code scans each subagent's final report before Claude reads it." 嵌套深度默认 3 层。— 同上

### 1.4 Agent teams（实验功能）

- 组件："Team lead / Teammates / Task list / Mailbox" — https://code.claude.com/docs/en/agent-teams
- 邮箱是文件："Each agent's mailbox is a JSON file at `~/.claude/teams/{team-name}/inboxes/{agent-name}.json`." 送达确认以写文件成功为准："Claude Code reports a message as sent only when the write to the recipient's mailbox file succeeds" — 同上
- 任务表：`~/.claude/tasks/{team-name}/`；三态 "pending, in progress, and completed"；依赖："a pending task with unresolved dependencies cannot be claimed until those dependencies are completed."；并发认领："Task claiming uses file locking to prevent race conditions" — 同上
- 团队成员名册：`config.json` 的 `members` 数组，"Teammates can read this file to discover other team members." 但"don't edit it by hand or pre-author it"。— 同上
- 每个 teammate 读什么："a teammate loads the same project context as a regular session: CLAUDE.md, MCP servers, and skills. It also receives the spawn prompt from the lead. The lead's conversation history does not carry over." — 同上
- 流转方式："Automatic message delivery ... The lead doesn't need to poll for updates."；"Idle notifications: when a teammate finishes and stops, it automatically notifies the lead and includes its final answer" — 同上
- 质量门禁 hook：`TeammateIdle`、`TaskCreated`、`TaskCompleted`，"Exit with code 2 to prevent completion and send feedback." — 同上
- 信任边界："a teammate can't approve a permission prompt or supply consent on your behalf" — 同上
- 已知缺陷（与陈旧有关）："Task status can lag: teammates sometimes fail to mark tasks as completed, which blocks dependent tasks." 冲突靠分工避免："Two teammates editing the same file leads to overwrites. Break the work so each teammate owns a different set of files." — 同上

### 1.5 Anthropic API：memory tool

- 客户端执行："The memory tool operates client-side: Claude requests file operations, and your application executes them." 命令：view / create / str_replace / insert / delete / rename，限制在 `/memories` 前缀下。— https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- 系统提示自动注入："IMPORTANT: ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE." 以及 "ASSUME INTERRUPTION: Your context window might be reset at any moment" — 同上
- 防膨胀/陈旧交给实现方："Track memory file sizes and cap how large a file can grow."；"Periodically delete memory files that haven't been accessed in a long time." — 同上
- 多会话软件开发模式：initializer session 建 progress log + feature checklist；每个会话开头读、结尾更新；"Mark a feature complete only after end-to-end verification confirms it works, not when the code is written." — 同上

### 1.6 Claude Managed Agents：memory stores

- 形态："A **memory store** is a workspace-scoped collection of text documents optimized for Claude. When you attach a store to a session, it is mounted as a directory inside the session's sandbox." 挂载在 `/mnt/memory/<slug>/`；"a note describing each mount is automatically added to the system prompt" — https://platform.claude.com/docs/en/managed-agents/memory
- 读写权限：`access` 为 `read_write`（默认）或 `read_only`，"`access` is enforced at the filesystem level"。一个会话最多 8 个 store，典型用法是"one read-only store attached to many sessions (standards, conventions, domain knowledge), kept separate from each session's own read-write store." — 同上
- 跨会话同步："Writes under the mount path are persisted back to the store and stay in sync across sessions that share it" — 同上
- 冲突：API 写入可带乐观并发前置条件："pass a `content_sha256` precondition. The update only applies if the stored content hash still matches the one you read" — 同上
- 审计：每次修改生成不可变版本 "memory version"，"attributed to the session"；版本保留 30 天；可 redact。— 同上
- 上限与防膨胀："Individual memories within the store are capped at 100 kB (~25k tokens). A store holds a maximum of 10,000 memories. Structure memory as many small focused files, not a few large ones." 另有"dreaming session"把碎片合并到新的输出 store："consolidates fragmented content into a separate new output store rather than modifying the original." — 同上（注：部分第三方文章写 2,000 条，官方页当前写 10,000 条，以官方为准）
- 安全警告："a successful prompt injection could write malicious content into the store. Later sessions then read that content as trusted memory." — 同上
- 只能在创建会话时挂载："memory stores can only be attached at session creation time" — 同上

---

## 2. OpenAI Codex（CLI / cloud）

要点：AGENTS.md 由人写、按目录层级拼接、有 32 KiB 总上限；Codex memories 是后台生成的本地记忆，官方明确"规则放 AGENTS.md，记忆只是回忆层"。harness engineering 文章把 repo 当 system of record：AGENTS.md 只做 ~100 行目录，知识放 `docs/`，执行计划带进度与决策日志入库，靠 linter/CI 和"doc-gardening" agent 防陈旧。

### 2.1 AGENTS.md 发现与合并

- 全局："In your Codex home directory (defaults to `~/.codex`, unless you set `CODEX_HOME`), Codex reads `AGENTS.override.md`"（无则读 `AGENTS.md`）— https://learn.chatgpt.com/docs/agent-configuration/agents-md（原 https://developers.openai.com/codex/guides/agents-md 308 重定向至此）
- 项目："Starting at the project root (typically the Git root), Codex walks down to your current working directory." 每个目录"checks for `AGENTS.override.md`, then `AGENTS.md`, then any fallback names in `project_doc_fallback_filenames`" — 同上
- 拼接与优先级："Codex concatenates files from the root down, joining them with blank lines." "Files closer to your current directory override earlier guidance because they appear later in the combined prompt." — 同上
- 防膨胀："stops adding files once the combined size reaches the limit defined by `project_doc_max_bytes` (32 KiB by default)." — 同上

### 2.2 Codex Memories

- "Memories let ChatGPT and Codex carry useful context from earlier work into future work." 位置："The main memory files live under `~/.codex/memories/`" — https://learn.chatgpt.com/docs/customization/memories?surface=app
- 何时生成："Codex skips active or short-lived sessions"；"updates memories in the background instead of immediately at the end of every chat"；"Codex waits until a chat has been idle long enough to avoid summarizing work" — 同上
- 两段式模型：`memories.extract_model`（"per-chat memory extraction"）与 `memories.consolidation_model`（"global memory consolidation"）。推断：先逐会话抽取、再全局合并，这是它防膨胀/去重的机制，文档未写合并细节。— 同上
- 注入开关：`memories.use_memories`（"controls whether Codex injects existing memories into future sessions"）；防污染：`memories.disable_on_external_context`（用过 MCP/web search 的会话不进记忆）。— 同上
- 与 AGENTS.md 的分工："Keep required team guidance in `AGENTS.md` or checked-in documentation." "Treat memories as a helpful recall layer, not as the only source for rules" — 同上
- 线程级控制："use `/memories` to control memory behavior for the current chat" — 同上

### 2.3 Harness engineering 文章（repo 作为 system of record）

原文 https://openai.com/index/harness-engineering/ 对 WebFetch 与 curl 均返回 403 / JS 验证页，未能直接读取；以下引语取自该文全文镜像 https://jaytaylor.com/notes/node/1770842156000.html（非官方镜像，内容为原文转载）。

- 核心前提："anything it can't access in-context while running effectively doesn't exist"
- AGENTS.md 定位："give Codex a map, not a 1,000-page instruction manual"；"we treat it as **the table of contents**"；"serves primarily as a map, with pointers to deeper sources of truth elsewhere"。约 100 行的数字出自多篇转述（如 https://medium.com/@AdithyaGiridharan/openais-harness-engineering-post-is-a-blueprint-for-the-agent-first-era-d9932851dcee），镜像提取未直接给出，记为未在原文核实。
- 知识库："The repository's knowledge base lives in a structured `docs/` directory treated as the system of record"
- 目录结构（原文）：
  ```
  AGENTS.md
  ARCHITECTURE.md
  docs/
  ├── design-docs/ (index.md, core-beliefs.md, ...)
  ├── exec-plans/
  │   ├── active/
  │   ├── completed/
  │   └── tech-debt-tracker.md
  ├── generated/ (db-schema.md)
  ├── product-specs/ (index.md, new-user-onboarding.md, ...)
  ├── references/ (design-system-reference-llms.txt, nixpacks-llms.txt, uv-llms.txt, ...)
  ├── DESIGN.md  FRONTEND.md  PLANS.md  PRODUCT_SENSE.md
  └── QUALITY_SCORE.md  RELIABILITY.md  SECURITY.md
  ```
- 计划："Plans are treated as first-class artifacts"；复杂工作"captured in execution plans with progress and decision logs...checked into the repository"
- 防陈旧（机械化）："Dedicated linters and CI jobs validate that the knowledge base is up to date, cross-linked"；"A recurring "doc-gardening" agent scans for stale or obsolete documentation"
- 防熵增："we started encoding what we call "golden principles" directly into the repository"；"This functions like garbage collection"
- agent 间流转："we've pushed almost all review effort towards being handled agent-to-agent"（流转载体是 PR 与 repo 文件，推断）

---

## 3. Devin（Cognition）

要点：Knowledge 是带"触发描述"的检索式条目，可 pin 到仓库；Devin 从聊天反馈中建议新条目，人编辑后保存或丢弃；自动拉取仓库里的 `.rules`/`CLAUDE.md`/`AGENTS.md` 等。Playbook 是重复任务的"系统提示"。DeepWiki 是自动生成的代码库 wiki。协调者 Devin 派 managed Devins（独立 VM），靠提示、playbook、消息、读子会话事件流来流转。

- Knowledge 定位与检索："Your **Trigger Description** will help Devin recall relevant Knowledge at the right times."；"Devin retrieves Knowledge when relevant, not all at once or all at the beginning." — https://docs.devin.ai/product-guides/knowledge
- Pin 三种作用范围："Pinning to **no repo**: The Knowledge is only retrieved when Devin decides it's relevant"；"Pinning to **a specific repo**: The Knowledge is always used whenever Devin is working in that specific repo."；"Pinning to **all repos**" — 同上
- 谁建议、谁批准："Devin will automatically suggest Knowledge to remember based on your feedback in chat."；"Edit the suggested Knowledge before saving, or dismiss the Knowledge if it's not helpful." — 同上
- 组织：文件夹、"Bulk enable/disable — Toggle an entire folder on or off."、Organization vs Enterprise Knowledge，"Promotion requires enterprise knowledge management permissions" — 同上
- 自动从仓库导入："Devin will automatically pull and update Knowledge based on specialized files in your codebase including `.rules`, `.mdc`, `.cursorrules`, `.windsurf`, `CLAUDE.md`, and `AGENTS.md`"；"Devin won't automatically pull in more general file types like `.md`."；自动生成的 repo knowledge 要人核对："Review any auto-generated Knowledge and verify for (a) completeness and (b) accuracy" — https://docs.devin.ai/onboard-devin/knowledge-onboarding
- Playbooks："A playbook is like a custom system prompt for a repeated task." 章节：Procedure（"Include at least one step for setup, the actual task, and delivery"）、Specifications（"describe the postconditions of the playbook"）、Advice、Forbidden Actions、Required from User；宏 "`!data-tutorial`"；文件扩展名 `.devin.md`；与 Knowledge 分工："Most best practices, style guides, or other project-specific instructions should be shared with Devin by using Knowledge" — https://docs.devin.ai/product-guides/creating-playbooks
- DeepWiki："Devin now automatically indexes your repos and produces wikis with architecture diagrams, links to sources, and summaries"；可用 `.devin/wiki.json` 的 `repo_notes` 和 `pages` 引导，"Maximum 30 pages (80 for enterprise)"；"Ask Devin will use information in the Wiki" — https://docs.devin.ai/work-with-devin/deepwiki 。重新生成频率：未找到（文档只写手动 regenerate）。
- 多 Devin 协调："launch child sessions with specific prompts, playbooks, tags, and ACU limits"；"Message child sessions — send follow-up instructions or clarifications to running sessions"；"Inspect any session's full event timeline"；"Schedule messages to itself — set reminders to check back on long-running child sessions"；"wait for all of them to finish in a single call instead of polling individually"；协调者职责"scoping work, monitoring progress, resolving conflicts, and compiling results" — https://docs.devin.ai/work-with-devin/advanced-capabilities
- 从会话提炼知识："Devin analyzes the sessions and produces a structured playbook with procedures, specifications, and advice"；"Devin compares successes and failures to propose targeted improvements" — 同上
- 子会话之间是否共享可写上下文：未找到。推断：子会话之间不共享工作记忆，只通过协调者消息和共享的 Knowledge/仓库间接共享。
- Devin for Terminal 的规则文件：AGENTS.md 等为 always-on，子目录文件懒加载（来源 https://docs.devin.ai/cli/extensibility/rules ，本次只读到搜索摘要，未打开原页，记为未核实）。

---

## 4. Factory（Droids / Missions）

要点：Missions 是 orchestrator（不写代码）+ 每个 feature 一个全新上下文的 worker + 独立 validator 的结构，协调完全靠共享状态文件（验证契约、feature 列表、AGENTS.md、知识库 library），而不是在 agent 之间传完整上下文。Spec Mode 把计划存为 `.factory/docs/YYYY-MM-DD-slug.md`。

- 架构原则（官方博客）："The full state is distributed across shared artifacts: the validation contract, the feature list, research notes, operational guidelines, and an evolving knowledge base."；"No single agent needs to hold the complete picture in its context at once."；"Each agent reads what's relevant to its current job." — https://factory.ai/news/missions-architecture
- 写者分工（官方博客）：orchestrator "writes the validation contract - a finite checklist of testable behavioral assertions"，"decomposes the work into features"，"creates shared state files - boundaries and procedures for its workers"；worker "starts with a fresh context, receives its feature spec, writes tests first, then implements"；"Scrutiny validators review each worker's implementation and trajectory for quality and correctness" 并 "encode relevant knowledge updates into shared state"；library 是"a library that will accumulate knowledge over the mission's duration"。博客中列出的文件名：`validation-contract.md`、`features.json`、`services.yaml`、`AGENTS.md`。— 同上
- 为何独立验证："An agent that implemented something is worse at objectively evaluating its own work than a fresh, unbiased reviewer." — 同上
- 继承配置（官方文档）："**AGENTS.md**: Workers follow your project conventions and coding standards."；无头运行 `droid exec --mission -f mission.md`，可分别设 `--worker-model` / `--validator-model`。— https://docs.factory.ai/missions/reference.md
- 验证节奏（官方文档）："Validation workers run at the end of each milestone, verifying its work."；估算 "`total runs ≈ #features + 2 * #milestones`" — https://docs.factory.ai/missions/planning.md
- 共享状态文件的细则（非官方：mitmweb 抓包逆向出的 orchestrator 提示词，https://gist.github.com/V1ki/356b121038722ebf32b5aac85482c113 ）：
  - "Mission objectives belong in `mission.md` (the mission proposal) and `validation-contract.md`, NOT AGENTS.md."
  - `validation-contract.md`："a living specification of current requirements, not a history log"
  - `features.json`："Each assertion ID should appear in exactly one feature's `fulfills` across the entire features.json."
  - `AGENTS.md`："Operational guidance for workers (constraints, conventions, boundaries)."；"If you cannot complete your work within these boundaries, return to orchestrator."
  - `.factory/library/`："the library has a **flat structure** (no nested folders). Organize by topic, not by milestone."；"Workers will add knowledge during execution."
  - `services.yaml`："The **single source of truth** for all commands and services. Workers read this - they don't guess."
  - 交接："`workerHandoffs` - an array of worker handoff **summaries**"，字段含 "discoveredIssues, unfinished work, or returnToOrchestrator=true"
  - 变更传播："every file that states the old truth must be updated to state the new truth before workers resume."
- Spec Mode（官方文档）："By default, plans are saved to `.factory/docs` inside the nearest project-level `.factory` directory."；"Files are named `YYYY-MM-DD-slug.md`"；只读规划后 "calls `ExitSpecMode` to ask for approval" — https://docs.factory.ai/cli/user-guides/specification-mode
- AGENTS.md 规范（官方文档）：初始加载预算 "80,000 characters"，按读取路径动态发现 "40,000 characters"；"Do not use `AGENTS.md` as a dumping ground."；不要放"temporary task notes that belong in an issue, PR, or spec." — https://docs.factory.ai/harness/agents-md.md（原 memory-management 页现 301 到此页）
- org / project memory：旧文档中的 `~/.factory/memories.md` 手工记忆方案页面已下线（重定向到 AGENTS.md 页），当前官方文档中未找到独立的 org memory 功能说明。

---

## 5. GitHub Copilot（coding agent / Memory / Spaces / Agent HQ）

要点：指令文件按类型组合（repo 级、路径级 `applyTo`、AGENTS.md 最近者优先），可用 `excludeAgent` 指定哪个 agent 不读。Copilot Memory 是最有特色的防陈旧设计：每条记忆带代码引用（citation），使用前对当前分支校验，28 天未用自动删除，且 coding agent、code review、CLI 之间共享。

- 指令文件："**Repository-wide** instructions (using the `.github/copilot-instructions.md` file)."；"**Path-specific** instructions (using `.github/instructions/**/*.instructions.md` files)."；"**Agent** instructions (using `AGENTS.md`, `CLAUDE.md` or `GEMINI.md` files)."；另有 "**Organization** instructions." — https://docs.github.com/en/copilot/reference/custom-instructions-support
- frontmatter 例：
  ```markdown
  ---
  applyTo: "**"
  excludeAgent: "code-review"
  ---
  ```
  "When Copilot is working, the nearest `AGENTS.md` file in the directory tree will take precedence."；"Personal instructions take the highest priority. Repository instructions come next, and then organization instructions are prioritized last. However, all sets of relevant instructions are provided to Copilot." — https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- Copilot Memory：
  - 引用校验："Repository-level facts are stored with citations pointing to the code that supports them."；"it checks those citations against the current branch to confirm the information is still accurate" — https://docs.github.com/en/copilot/concepts/agents/copilot-memory
  - TTL："any stored fact or preference that goes unused is automatically deleted after 28 days"；"The 28-day timer may reset whenever Copilot successfully validates and uses an entry." — 同上
  - 写入权限："Copilot only creates repository-level facts in response to actions by users with write access to the repository" — 同上
  - 跨 agent 共享："Facts and preferences captured by one Copilot feature can be used by another."；"Copilot Memory is currently used by Copilot cloud agent, Copilot code review, and Copilot CLI." — 同上
  - 人工管理："Repository owners can review and manually delete the repository-level facts stored for their repository." — 同上
  - 写入机制（官方工程博客）：记忆创建是 agent 可调用的工具，引用校验在使用时实时做。— https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/（本次只读到搜索摘要，未打开原文，记为未核实）
- Copilot Spaces："Spaces can include repositories, code, pull requests, issues, free-text content like transcripts or notes, images, and file uploads."；"GitHub files and other GitHub-based sources added to a space are automatically updated as they change"；IDE 里经 GitHub MCP server 读取。— https://docs.github.com/en/copilot/concepts/context/spaces 。coding agent 是否直接读取 Space：该页未找到。
- Agent HQ / mission control："assign tasks to Copilot across repos, pick a custom agent, watch real‑time session logs, steer mid-run (pause, refine, or restart), and jump straight into the resulting pull requests" — https://github.blog/changelog/2025-10-28-a-mission-control-to-assign-steer-and-track-copilot-coding-agent-tasks/（搜索摘要，未打开原文）。agent 间流转的载体是 issue / PR / 会话日志（推断），未找到 agent 之间直接传消息的机制。

---

## 6. Google：Jules、Gemini CLI Conductor、Antigravity

要点：Conductor 是"上下文作为 repo 内受管产物"最完整的文件化方案：`conductor/` 下项目级文档 + `tracks/<id>/spec.md, plan.md, metadata.json`，agent 边做边勾选 plan.md。Jules 读 AGENTS.md，有按仓库的 Memory。Antigravity 用 Artifacts（任务表、实现计划、walkthrough）作为人与 agent 的交接面，Knowledge Items 由知识子 agent 从对话中提炼。

### 6.1 Jules

- "Jules now automatically looks for a file named AGENTS.md in the root of your repository."；"Keep AGENTS.md up to date." — https://jules.google/docs/
- 计划审批："Once you submit a task, Jules will generate a plan. You can review and approve it before any code changes are made." — 同上
- Memory："During a task, Jules will save your preferences, nudges, and corrections."；"You can toggle memory on or off for the repo in the repo settings page under "Knowledge"" — https://jules.google/docs/changelog/2025-09-30/ 。存储格式、防膨胀机制：未找到。

### 6.2 Gemini CLI Conductor 扩展

- 理念："By treating context as a managed artifact alongside your code, you transform your repository into a single source of truth"；"These Markdown files persist in your repository, enabling you to pause and resume work and move between machines." — https://developers.googleblog.com/conductor-introducing-context-driven-development-for-gemini-cli/
- 文件：`conductor/product.md`、`conductor/product-guidelines.md`、`conductor/tech-stack.md`、`conductor/workflow.md`、`conductor/code_styleguides/`、`conductor/tracks.md`；每个 track：`conductor/tracks/<track_id>/spec.md`、`plan.md`、`metadata.json` — https://github.com/gemini-cli-extensions/conductor
- track 定义："This initializes a _track_—our term for a high-level unit of work." — Google 博客（同上）
- 命令与更新："Starts a new feature or bug track. Generates `spec.md` and `plan.md`."；implement 的 "Updated Artifacts" 为 `conductor/tracks.md (Status updates)` 与 `conductor/tracks/<id>/plan.md (Status updates)`；任务状态用复选框，revert "resets the task state back to pending `[ ]`"；review 修正会 "append a `Review Fixes` tracking phase to `plan.md`"；revert 按 track/phase/task 理解 git 历史。— GitHub README（同上）
- 更新："Your coding agent then works through the `plan.md` file, checking off tasks as it completes them."；"the ability to edit the plan mid-flight" — Google 博客
- 团队共享："You can set these preferences once, and they become a shared foundation for every feature your team builds." — Google 博客
- 多 agent：未找到。Conductor 是单 agent 顺序执行，跨会话靠文件。

### 6.3 Antigravity

- Artifacts："As the agent works, it produces Artifacts, tangible deliverables in formats that are easier for users to validate"，包括"task lists, implementation plans, walkthroughs, screenshots, and browser recordings" — https://antigravity.google/blog/introducing-google-antigravity
- 反馈回流："Google-doc-style comments on text Artifacts or select-and-comment feedback on screenshots"；"This feedback will be automatically incorporated into the agent's execution" — 同上
- 审批："the agent will pause at intermediate milestones and request review"；"Artifacts are primarily generated during the agent's **Planning Mode**" — https://antigravity.google/docs/artifacts/
- 知识库："Antigravity treats learning as a core primitive, with agent actions both retrieving from and contributing to a knowledge base" — 博客
- 多 agent 界面："mission control for spawning, orchestrating, and observing multiple agents across multiple workspaces in parallel" — 博客
- Knowledge Items 细节：官方文档页 `https://antigravity.google/docs/knowledge` 返回 404，未找到官方说明。非官方来源（https://iceberglakehouse.com/posts/2026-03-context-google-antigravity/ 等）称"a separate Knowledge Subagent analyzes the conversation"、每个 KI 有 `metadata.json` 与 artifacts 目录、存于 `~/.gemini/antigravity/`；Google 论坛有用户报告 KI 不自动生成（https://discuss.ai.google.dev/t/knowledge-items/126774 ）。均未经官方核实。
- Artifacts 在 agent 之间如何共享：未找到。

---

## 7. Kiro（AWS）

要点：steering（常驻/按文件匹配/手动/自动四种注入模式）+ spec 三件套（requirements.md / design.md / tasks.md，任务表带实时状态与依赖波次并行）+ hooks（文件保存、任务前后等事件触发 agent 提示或 shell 命令，用来让文档跟随代码更新）。

- steering 位置："Workspace steering (`.kiro/steering/`)"、"Global steering (`~/.kiro/steering/`)"；默认文件 `product.md`、`tech.md`、`structure.md` — https://kiro.dev/docs/steering/
- 注入模式 frontmatter：`inclusion: always`；`inclusion: fileMatch` + `fileMatchPattern: "components/**/*.tsx"`；`inclusion: manual`（聊天里输入 `#troubleshooting-guide` 引入）；`inclusion: auto` + `name` + `description`。文件引用语法 "`#[[file:<relative_file_name>]]`" — 同上
- AGENTS.md："AGENTS.md files do not support inclusion modes and are always included." 冲突："Kiro will prioritize the workspace steering instructions" — 同上
- specs："**requirements.md** (or **bugfix.md**) - Captures user stories, acceptance criteria, or bug analysis in structured notation"；"**design.md** - Documents technical architecture, sequence diagrams, and implementation considerations"；"**tasks.md** - Provides a detailed implementation plan with discrete, trackable tasks"；"All specs follow a three-phase workflow" — https://kiro.dev/docs/specs/
- 任务状态与并行："Tasks are updated as in-progress or completed"；"Kiro builds a **dependency graph** of the tasks in your `tasks.md` and groups independent tasks into **waves**"；"Waves execute sequentially; tasks within a wave execute concurrently" — 同上
- spec 目录 `.kiro/specs/<name>/`、EARS 记法：本页未找到原文（子页未读）。
- hooks："Each hook file is a standalone JSON file at `.kiro/hooks/<id>.json`."；触发器含 Prompt Submit、Agent Stop、Session Start、Pre/Post Tool Use、File Create/Save/Delete、"Before a spec task starts"、"After a spec task completes"；动作 "`"command"` (shell command) or `"agent"` (inject prompt)"；"File triggers respond only to changes made by the agent."；用例"auto-create tests, docs, or translations when new source files appear" — https://kiro.dev/docs/hooks/

---

## 8. 其他

### 8.1 Augment Code

- Memory Review："you'll see an "X Pending Memory" button in the turn summary"；"Approve, edit, or discard as needed"；此前"the only way to audit them was by periodically opening the memories file" — https://www.augmentcode.com/changelog/memory-review
- 记忆 vs 规则的判定（官方指南，搜索摘要，未打开原页）：能从代码读出的不存；对每个任务都适用的放 AGENTS.md / workspace rules；工作中学到且需审核的放 memory — https://www.augmentcode.com/guides/agent-memory-vs-context-engineering
- Remote agents 之间互相通信：未找到官方说明（The New Stack 报道称"they don't yet interact with each other"，https://thenewstack.io/augment-codes-remote-agents-code-in-the-cloud/ ，非官方）。

### 8.2 Amp（Sourcegraph）

- 线程引用："You can now reference threads in your messages, and Amp will fetch and extract the relevant context"；"Amp pulls in only what's needed using a new `read_thread` tool"，"which first fetches the thread as Markdown and then uses another model to extract the relevant context" — https://ampcode.com/news/read-threads
- Handoff 取代 compaction："Instead of summarizing a thread, you're extracting from it what matters for your next task."；"Amp then analyzes the current thread and generates a prompt to start the new thread, along with a list of relevant files."；"The generated prompt will then appear as a draft in the new thread so you can still review and edit it." — https://ampcode.com/news/handoff

### 8.3 Windsurf（Cascade，文档已并入 docs.devin.ai）

- 自动记忆："stored locally in `~/.codeium/windsurf/memories/`"；"Memories generated in one workspace are not available in another"；"Cascade retrieves them when it believes they're relevant." — https://docs.devin.ai/desktop/cascade/memories（原 https://docs.windsurf.com/windsurf/cascade/memories 307 重定向）
- 规则：".devin/rules/*.md (preferred) or .windsurf/rules/*.md (fallback)"；`trigger` 取值 `always_on` / `model_decision`（"Only the `description` is shown in the system prompt."）/ `glob` / `manual`（"typing `@rule-name`"）；上限 "Workspace rule files are limited to 12,000 characters each."、"The global rules file is limited to 6,000 characters."；AGENTS.md "root-level = always-on, subdirectory = auto-glob for that directory" — 同上
- 官方转向："for durable knowledge, prefer Rules or AGENTS.md"；"Memories apply to the legacy Cascade agent only." — 同上

### 8.4 Replit Agent

- "Agent first creates a `replit.md` file in your project's root directory using proven best practices."；"Agent can also update your `replit.md` file as it learns more about your project and makes changes to your application."；"`replit.md` must be located in your project's root directory to work properly." — https://docs.replit.com/replitai/replit-dot-md

### 8.5 Warp

- "Warp uses `AGENTS.md` as the default project rules file."；"When relevant, Agents automatically pull in applicable rules"；"Rules used in an interaction will appear in the conversation under **References**"；"the most specific, project-relevant rules take priority over broader ones" — https://docs.warp.dev/agent-platform/capabilities/rules/
- Warp Drive 作为团队共享上下文："Workflows, Notebooks, Environment Variables, Rules, and MCP Servers"，被使用时 "displayed in the conversation as a citation under "References" or "Derived from"" — https://docs.warp.dev/knowledge-and-collaboration/warp-drive/warp-drive-as-agent-mode-context

### 8.6 Linear

- "Agent guidance lets you provide instructions that agents will automatically receive"；"Workspace guidance applies across the entire organization"；"team guidance takes priority" — https://linear.app/docs/agents-in-linear
- 委派模型："Assigning an issue to an agent delegates the issue to that agent"；"The human assignee remains responsible for the issue, even after delegation" — 同上
- 流转载体是 issue 本身（agent session 活动写在 issue 上，推断自"Agent user pages show issue activity and contributions"）。

### 8.7 背景：Cursor Projects（非本次调研对象，仅核对）

- 官方 changelog https://cursor.com/changelog/projects 未打开；搜索摘要称 Projects 于 2026-09-10 以 beta 发布，coordinator "doesn't write code itself"。未核实原文。

---

## 横向对比表

| 产品 | 文档类型 | 写者 | 读取机制 | 更新触发 | 防膨胀/冲突 | 跨 agent 流转 |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code | CLAUDE.md 层级 + `.claude/rules/`（`paths`）；auto memory `MEMORY.md`+主题文件；子 agent `agent-memory/<name>/` | 人（CLAUDE.md）；Claude（auto memory）；子 agent（自有 memory） | 启动时作为 user message 注入；子目录/path 规则读文件时懒加载；MEMORY.md 注入前 200 行/25KB，主题文件按需读 | 人纠正时 Claude 自决写入；`/memory` 人工编辑；compaction 后重读根 CLAUDE.md | 200 行建议；写入后客户端提醒缩短；`modified` 时间戳；HTML 注释剥离；冲突无机制 | agent teams：共享任务表（文件锁认领、依赖自动解锁）+ 每 agent JSON 邮箱；idle 通知带最终答案；TaskCompleted 等 hook 可拒绝 |
| Anthropic API memory tool | `/memories` 下任意文件 | agent | 系统提示强制"先 view 记忆目录"；工具调用 | agent 边做边写（"ASSUME INTERRUPTION"） | 由实现方限大小、删久未访问文件 | 未提供；多会话靠同一存储 |
| Claude Managed Agents | memory store（路径寻址的文本文档） | agent（read_write 挂载）；人/程序经 API | 挂载为 `/mnt/memory/<slug>/`，系统提示自动加挂载说明 | agent 写文件即持久化；API 种子/修订 | 单条 100kB、每 store 1 万条；`content_sha256` 乐观并发；不可变版本+审计+redact；dreaming 合并到新 store；read_only 分层 | 多会话挂同一 store，写入跨会话同步 |
| OpenAI Codex | AGENTS.md（全局/项目层级/override）；`~/.codex/memories/` | 人（AGENTS.md）；后台模型（memories） | AGENTS.md 根到 cwd 拼接进提示；memories 开关注入 | memories 在会话空闲后后台抽取+全局合并 | AGENTS.md 总量 32 KiB；近目录后出现即优先；用过外部上下文的会话可不进记忆 | 未找到内建 agent 间机制 |
| OpenAI harness engineering（实践文章） | AGENTS.md 目录 + `docs/`（design-docs、exec-plans/active|completed、tech-debt-tracker、product-specs、references、generated） | agent（人设计环境） | AGENTS.md 指路，渐进式读取 | 执行计划带进度与决策日志随工作入库 | linter + CI 校验新鲜度与交叉链接；定期 doc-gardening agent 开 PR；golden principles 当垃圾回收 | agent 对 agent 审查；载体是 repo 与 PR（推断） |
| Devin | Knowledge（触发描述、pin、文件夹、org/enterprise）；Playbook `.devin.md`；DeepWiki；自动导入 `.rules`/`AGENTS.md` 等 | 人；Devin 建议→人编辑保存或丢弃；从会话生成 playbook | 按触发描述检索；pin 到仓库则常驻 | 聊天反馈触发建议；仓库规则文件变化自动拉取 | 人工审批建议；按文件夹整体开关；小而专的条目 | 协调者派 managed Devins（独立 VM），附 prompt/playbook/ACU 限额；发消息、读子会话事件、定时提醒自己、一次性等待全部完成 |
| Factory Missions | 验证契约、`features.json`、`mission.md`、AGENTS.md、`.factory/library/`、`services.yaml`（后几项细则为非官方逆向）；Spec Mode 计划 `.factory/docs/` | orchestrator 写契约/feature/边界；worker 写代码与 library；validator 写知识更新 | 每个 worker 全新上下文，只读与当前 feature 相关的共享文件 | 每 milestone 末跑验证；需求变化时先改共享状态再继续 | 契约是"当前需求"不是历史；每个断言只归一个 feature；library 扁平按主题；AGENTS.md 预算 80k 字符 | 结构化交接摘要（discoveredIssues、未完成项、returnToOrchestrator）；validator 发现问题→orchestrator 建修复 feature |
| GitHub Copilot | `copilot-instructions.md`、`*.instructions.md`（`applyTo`、`excludeAgent`）、AGENTS.md；Copilot Memory；Spaces | 人（指令）；agent 经工具创建记忆（限有写权限用户触发） | 指令全部下发，路径匹配才含；记忆使用前按引用对当前分支校验 | agent 发现可行动事实时写记忆 | 引用校验不通过则不用；28 天未用自动删除，用了续期；仓库级隔离；owner 可删 | 记忆在 cloud agent / code review / CLI 间共享；mission control 管多个 agent 会话；载体 issue/PR |
| Gemini CLI Conductor | `conductor/` 下 product、guidelines、tech-stack、workflow、styleguides、`tracks.md`；`tracks/<id>/spec.md, plan.md, metadata.json` | agent 生成，人审阅编辑 | 命令（setup/newTrack/implement/status/review/revert）读取对应文件 | implement 时勾选 plan.md、更新 tracks.md；review 追加修复阶段 | 按 track 分目录；git 感知的按任务回滚 | 单 agent；跨会话/跨机器靠入库文件 |
| Jules | AGENTS.md；按仓库 Memory | 人；Jules（偏好、纠正） | 自动读根 AGENTS.md | 任务中记录人的纠正 | 仓库设置可关；其余未找到 | 未找到 |
| Antigravity | Artifacts（任务表、实现计划、walkthrough、截图、录屏）；知识库 | agent；人以评论反馈 | 人评论自动并入执行 | Planning Mode 生成，里程碑处暂停待审 | 人审批；KI 细节官方未找到 | Agent Manager 并行多 agent；artifact 间共享未找到 |
| Kiro | steering（always/fileMatch/manual/auto）；spec 三件套；hooks JSON | 人 + agent（spec 由 agent 生成、人逐阶段确认） | steering 按模式注入；`#[[file:]]` 引用 | hooks：文件保存、任务前后、agent 停止等 | 按文件匹配/按描述自动注入以控量；工作区优先于全局 | tasks.md 依赖图分波次并行执行 |
| Augment | memories 文件；rules/AGENTS.md | agent 提议，人审批 | 未找到细节 | 工作中产生"Pending Memory" | 每条新记忆人工批准/编辑/丢弃 | remote agents 间无交互（非官方） |
| Amp | 线程本身 | 人/agent | `read_thread`：另一模型按当前问题抽取相关部分 | 人引用线程或 handoff | 不做摘要式 compaction，按下一任务目标抽取 | handoff 生成新线程草稿提示+相关文件，人可编辑 |
| Windsurf | 自动 memories（本机、按工作区）；rules（4 种 trigger）；AGENTS.md | Cascade；人 | always_on 全文进系统提示；model_decision 只放描述；glob 读文件时 | Cascade 自决或人要求 | 规则 12k/6k 字符上限；官方建议持久知识改写成 Rules/AGENTS.md | 未找到 |
| Replit | `replit.md` | Agent 创建并随学习更新；人可编辑 | 根目录文件 | agent 学到新东西时 | 未找到 | 未找到 |
| Warp | AGENTS.md/WARP.md；Warp Drive（规则、笔记本、工作流） | 人/团队 | 相关时自动拉取，回复中标注引用来源 | 人维护 | 子目录优先 | 团队同步 Drive 对象 |
| Linear | workspace / team agent guidance | 人（有权限者） | agent 工作于 issue 时自动收到 | 人改设置 | team 优先于 workspace | issue 委派：人仍是负责人，agent 是 delegate |

---

## 对本流水线（spec → 票 → 夜间 worker → reviewer/verifier → 合并关票）的可借鉴点

以下是从上面事实推出的判断，属于推断。

1. 共享状态按"谁有权写"拆文件，而不是一个大 notes：Factory 的 orchestrator 独写契约与 feature 列表、worker 只往 library 追加、validator 写知识更新；Managed Agents 用 read_only 与 read_write 两类 store 分层。与 Cursor 的 coordinator 独写 notes.md 同一思路。
2. 验证契约先于实现、每条断言只归属一个工作单元（Factory `features.json` 的 `fulfills`），对应票的 `CHECK:` 行；验证由不同的全新 agent 做（Factory、Claude Code 的 TaskCompleted hook）。
3. 防陈旧最强的两个机制是"带引用、使用前校验 + 未使用 TTL"（Copilot Memory）和"CI/linter 校验文档 + 定期 gardening agent"（OpenAI harness）；其次是时间戳（Claude Code `modified`）和人工审批建议（Devin、Augment）。
4. 常驻注入必须有硬上限并分层：Codex 32 KiB、Claude Code MEMORY.md 200 行、Windsurf 12k 字符、Factory 80k 字符；超出部分改成按触发/按路径/按需检索（Devin trigger、Kiro fileMatch/auto、Windsurf model_decision）。
5. 规则与记忆分开：Codex、Windsurf、Augment 官方都要求必须遵守的规则进入入库文件（AGENTS.md/rules），自动记忆只作回忆层。
6. 交接用结构化摘要而不是整段上下文：Factory 的 `workerHandoffs`（discoveredIssues / 未完成 / returnToOrchestrator）、Amp handoff（目标+相关文件+可编辑草稿）、Claude Code idle 通知附最终答案。
7. 并发写冲突的现成做法：Claude Code 任务认领用文件锁；Managed Agents 用 `content_sha256` 前置条件；Claude Code 文档对同文件并发编辑只给"按文件划分所有权"的建议。

---

## 读过的 URL 清单

官方文档 / 官方博客（已打开）：
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/sub-agents
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- https://platform.claude.com/docs/en/managed-agents/memory
- https://learn.chatgpt.com/docs/agent-configuration/agents-md（由 developers.openai.com/codex/guides/agents-md 重定向）
- https://learn.chatgpt.com/docs/customization/memories?surface=app（由 developers.openai.com/codex/memories 重定向）
- https://openai.com/index/harness-engineering/（403，未能读取）
- https://docs.devin.ai/product-guides/knowledge
- https://docs.devin.ai/onboard-devin/knowledge-onboarding
- https://docs.devin.ai/product-guides/creating-playbooks
- https://docs.devin.ai/work-with-devin/deepwiki
- https://docs.devin.ai/work-with-devin/advanced-capabilities
- https://factory.ai/news/missions-architecture
- https://docs.factory.ai/missions/overview
- https://docs.factory.ai/missions/reference.md
- https://docs.factory.ai/missions/planning.md
- https://docs.factory.ai/missions/running-cli.md
- https://docs.factory.ai/droid-computers/overview.md
- https://docs.factory.ai/cli/user-guides/specification-mode
- https://docs.factory.ai/guides/power-user/memory-management（现重定向到 https://docs.factory.ai/harness/agents-md.md）
- https://docs.factory.ai/llms.txt
- https://docs.github.com/en/copilot/concepts/agents/copilot-memory
- https://docs.github.com/en/copilot/concepts/context/spaces
- https://docs.github.com/en/copilot/reference/custom-instructions-support
- https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- https://jules.google/docs/
- https://jules.google/docs/changelog/2025-09-30/
- https://github.com/gemini-cli-extensions/conductor
- https://developers.googleblog.com/conductor-introducing-context-driven-development-for-gemini-cli/
- https://antigravity.google/blog/introducing-google-antigravity
- https://antigravity.google/docs/artifacts/
- https://antigravity.google/docs/knowledge（404）
- https://kiro.dev/docs/steering/
- https://kiro.dev/docs/specs/
- https://kiro.dev/docs/hooks/
- https://www.augmentcode.com/changelog/memory-review
- https://ampcode.com/news/handoff
- https://ampcode.com/news/read-threads
- https://docs.devin.ai/desktop/cascade/memories（由 docs.windsurf.com/windsurf/cascade/memories 重定向）
- https://docs.replit.com/replitai/replit-dot-md
- https://docs.warp.dev/agent-platform/capabilities/rules/
- https://docs.warp.dev/knowledge-and-collaboration/warp-drive/warp-drive-as-agent-mode-context
- https://linear.app/docs/agents-in-linear

非官方（已打开，引用处已标注）：
- https://jaytaylor.com/notes/node/1770842156000.html（harness engineering 全文镜像）
- https://gist.github.com/V1ki/356b121038722ebf32b5aac85482c113（Factory Missions 提示词逆向）

仅见搜索摘要、未打开原页（结论标为未核实）：
- https://docs.devin.ai/cli/extensibility/rules
- https://github.blog/ai-and-ml/github-copilot/building-an-agentic-memory-system-for-github-copilot/
- https://github.blog/changelog/2025-10-28-a-mission-control-to-assign-steer-and-track-copilot-coding-agent-tasks/
- https://www.augmentcode.com/guides/agent-memory-vs-context-engineering
- https://thenewstack.io/augment-codes-remote-agents-code-in-the-cloud/
- https://iceberglakehouse.com/posts/2026-03-context-google-antigravity/
- https://discuss.ai.google.dev/t/knowledge-items/126774
- https://medium.com/@AdithyaGiridharan/openais-harness-engineering-post-is-a-blueprint-for-the-agent-first-era-d9932851dcee
- https://cursor.com/changelog/projects

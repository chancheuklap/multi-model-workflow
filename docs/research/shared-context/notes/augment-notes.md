# Augment Code 调研笔记（R8）：memory、rules、Context Engine、多 agent、Code Review

调研日期 2026-09-13。只读网络调研。英文引语照原文保留。"推断"表示没有原文直接支持；"未找到"表示查过但没有找到。

## 0. 先交代：2026 年 Augment 的产品版图变了

- 2026 年 Augment 的主力产品是 **Cosmos**（团队级 agent 平台，SiliconANGLE 报道 2026-06-05 发布；Tessl 报道 2026-05-05 预览）和 **Intent**（桌面端多 agent 工作区，博客 2026-02-10）。IDE 扩展和 Auggie CLI 仍在，但文档首页只把 Cosmos 和 Auggie CLI 作为入口，IDE 放在一句 "Looking for Augment for your favorite IDE?" 里。来源：https://docs.augmentcode.com/introduction （llms-full.txt 内）。
- **Remote Agents 已经移除**。官方 Analytics API 文档字段说明原文："Remote Agent has been removed from IDE extensions; this field is retained for historical data."（https://docs.augmentcode.com/llms-full.txt 中 analytics-api 段）；分析看板里写作 "Messages from remote agent sessions (deprecated feature)"。它的继任者是 Cosmos 的 Environments + Experts + Workers（推断：官方没有写"继任"二字，但功能对应，且 remote-agents 产品页现在讲的是 Cosmos：https://www.augmentcode.com/product/remote-agents ，"Cosmos is the platform for building an always-on software delivery system"）。
- **IDE 的 Memories 功能在当前官方文档里没有专页**：在 llms-full.txt 全文里 grep "memor"，除 Cosmos 的两页外没有 IDE/CLI memories 文档（未找到）。Memory Review 只在 changelog 和 blog 里有记录（见 §1.1）。
- IDE 扩展是否整体下线：第三方 Kilo 博客称用户收到"sunsetting its IDE extensions"邮件（https://blog.kilo.ai/p/is-augment-sunsetting-its-ide-extensions ，没有原邮件引文）；但官方 changelog 在 2026-08-10 仍发布 "VSCode Extension 0.893.1 Release Notes"（https://www.augmentcode.com/changelog ）。结论：未核实，不以此为事实。

---

## 1. Memories

Augment 有两代 memory，机制差别很大，分开记。

### 1.1 第一代：IDE agent 的 Memories + Memory Review（2025）

| 问题 | 发现 | 来源 |
| --- | --- | --- |
| 存在哪里 | 一个"memories file"，用户过去只能打开原始文件审计："periodically opening the memories file" | https://www.augmentcode.com/changelog/memory-review |
| 作用范围 | 批准后进入 "workspace long-term memory"（按 workspace）。指南又说它是 "Per-developer, cross-session"（每个开发者本人，跨会话）。两者合起来：每个开发者、每个 workspace 一份，不在团队间共享（推断：两句原文拼合） | https://www.augmentcode.com/blog/how-we-built-memory-review ；https://www.augmentcode.com/guides/agent-memory-vs-context-engineering |
| 如何自动产生 | agent "when it sees something worth persisting across sessions" 时建立。触发例子："A long-term project goal mentioned in chat."、"A decision made during debugging or planning."、"A relevant piece of code or system detail."；以及开发者纠正 agent 输出 | how-we-built-memory-review；搜索摘要 |
| 来源字段 | 每条带 Source：Agent（agent 提议）或 Correction（开发者纠正触发）。此说法来自 agent-memory-vs-context-engineering 指南；changelog 页本身没有写 | 指南 |
| 审阅流程 | turn summary 出现 "X Pending Memory" 按钮 → 聊天面板内 modal → "Approve"（加入长期记忆）/"Edit"（"curate before saving"）/"Discard"（"reject entirely"）→ "the agent loop continues with curated memory context"。指南的四步版："Nothing gets stored without the developer's sign-off." | how-we-built-memory-review；指南 |
| 发布 | 2025-09-08，"VS Code v0.542.0+ and JetBrains v0.280.0+" | changelog/memory-review |
| 为什么做 | 旧问题：自动生成、看不见存了什么、只能翻原始文件，"unnecessary or low-quality memories piling up"。设计目标：把审阅做成 "the natural chat loop, instead of a separate audit process" | how-we-built-memory-review |
| 如何注入 | 未找到原文细节（推断：批准后的 memories 在后续会话开头随上下文加载；指南的 persistence matrix 对"decision logs"写的是 session 开始时注入） | — |
| 编辑、删除（事后） | 事后编辑：只有"打开 memories 文件"一途（changelog 反向证明）；没有专门的删除 UI 说明（未找到） | — |
| 陈旧处理、去重 | 未找到（blog 明确没有讨论） | — |

### 1.2 第二代：Cosmos Expert Memory（2026）

来源：https://docs.augmentcode.com/cosmos/experts-memory 、https://docs.augmentcode.com/cosmos/understanding-files 、https://docs.augmentcode.com/cosmos/experts-code-review-memory

- **存在哪里**：共享虚拟文件系统 VFS。"It stores scoped knowledge in the shared virtual filesystem (VFS)"；"The Expert writes the information as readable Markdown under its own VFS directory."
- **VFS 本身**："the storage layer Experts use between Sessions"。两个持久 scope：User（"private to you"）和 Organization（"shared with everyone in your organization. The right place for team knowledge and outputs an Expert wants to hand off to another Expert."）。同步时机："Sync happens automatically at turn boundaries — once an Expert finishes a turn, every file change it made is uploaded and visible to the next Session." 版本化："every version is attributed to the agent that wrote it, and deletions are recorded as tombstones rather than erasures"；保留 "at least one version per week retained beyond 30 days"。上限：1 MB/文件、10,000 文件、100 MB/文件系统，超限 "are rejected at sync time"。
- **作用范围**："Repository-based Experts typically use one scope per repository, while other Experts can use a global, channel, project, or user-specific scope. Memory can be shared with an organization or kept within a user's VFS, depending on the Expert's visibility." 归属："An Expert's memory belongs to its team"；"Each Expert team owns and maintains its memory rather than modifying another team's curated knowledge."
- **默认开启**："Memory is enabled for all Template Experts." Advisor 建自定义 Expert 时 "wires in lightweight memory by default"。
- **写路径（Capture）**："A memory-enabled Expert identifies durable information that could change a future decision. In interactive sessions, it tells you when it remembers something so you can correct or veto it."（注意：从"先审后存"变成"存了告诉你、你可否决"。）
- **读路径（Load）**："At the start of relevant work, the Expert loads memory for the current scope. It applies matching guidance and flags discrepancies when current evidence conflicts with a remembered rule."
- **两种模型**：
  - Simple memory（默认）："writes explicit, high-quality human feedback directly to a curated knowledge file."
  - Noisy memory："uses an evidence log plus a curated knowledge file. It combines weaker signals over time and promotes a learning only after the evidence is strong enough."
  - "Both models expose the same curated knowledge view to readers."
- **陈旧处理**：没有过期机制；靠加载时对照现状："Treat memory as evolving context, not an unquestionable rule. Experts should surface contradictions rather than ignore current evidence."
- **最佳实践原文**："Use the narrowest stable scope that matches the workflow"；"Save information only when it could change a future decision or area of focus."；"Use skills or Expert instructions for explicit workflows; use memory for context learned through ongoing work."
- **其它 Expert 的 memory 实例**：Ticket Manager "remembers durable guidance within the relevant Linear project, Jira Epic, or GitHub repository"；Feedback Triager "remembers explicit standing guidance for classification, routing, deduplication, and when to stay silent within each configured channel."（https://docs.augmentcode.com/llms-full.txt 中 experts-ticket-manager、experts-feedback-triager 段）
- **自定义 Expert 的 prompt checklist 把 memory 列为一项**："Memory: where reusable team learnings should be read or written, if the workflow improves over time"（https://docs.augmentcode.com/cosmos/experts-configure-custom ）
- **营销层面的"学习飞轮"**：Milo 例子——先把所有测试规范塞进初始指令，"broke down quickly under real workloads"；后改为窄范围 + 持续学习："when Milo stumbled, an engineer on Slack would jump in to help, and Milo distilled the important information from those conversations and stored it."（https://www.augmentcode.com/guides/cosmos-experts ）。该指南还把 memory 分为 episodic / domain-specific isolation / procedural 三层，属于指南作者的概念框架，文档里没有对应实现（推断）。

---

## 2. 指南 "Agent Memory vs. Context Engineering"

URL：https://www.augmentcode.com/guides/agent-memory-vs-context-engineering 。作者 Paula Hingel，发布 2026-04-17，更新 2026-06-18。WebFetch 工具对长段落拒绝逐字复述，下列引语均为短句原文，表格为逐行转述。

### 2.1 核心论点
- "The key distinction between agent memory and context engineering is the scope of persistence: agent memory determines what information survives between sessions, while context engineering determines what information is loaded into the next session's finite context window."
- 缺一的后果：agents "forget critical decisions, resuggest rejected patterns and erode developer trust within days."
- 比喻（原文）："Memory is the library. Context engineering is the librarian who decides which books to put on the desk for this session."
- 故障症状 → 缺哪层：反复重推已做过的决定 = 缺 memory 治理；队友之间约定不一致 = 缺共享 context file；做到一半丢了 feature 状态 = 缺 living spec。

### 2.2 对比表（转述，引号内为原文）
| 维度 | Agent memory | Context engineering |
| --- | --- | --- |
| 目标 | "Retain decisions across sessions" | "Load the right subset into the next prompt" |
| 失败方式 | "Stale or bloated recall" | "Wrong information loaded, right information excluded" |
| 持续时间 | "Days to months" | "Per-turn, ephemeral selection" |
| 人的角色 | 治理存什么 | 设计加载什么 |
| 成本 | 存储/检索延迟 | token 预算 |

### 2.3 三层持久化（"Three persistence layers"）
- Context files（AGENTS.md、rules）：静态、全队、进版本库。
- Agent memory：自动捕获、人工治理、每个开发者一份。
- Living specs（Intent）：自动更新、按 feature 划范围。
- Persistence matrix：chat history、tool outputs 不持久（"Only within active session"）；decision logs（session 开始时注入）、AGENTS.md/rules（"Auto-discovered by directory traversal"）、living specs（相关任务自动注入）、vector embeddings（语义检索）持久。

### 2.4 Context file 的准入标准
- 两条同时成立："undiscoverable (the agent cannot infer it from reading the codebase)" 且 "universal (it applies to virtually every task in the project)".
- 引 Anthropic：长文件 "consume more context and reduce adherence"。层级：monorepo 嵌套 AGENTS.md，"the closest one takes precedence"。
- 样例 AGENTS.md 含命令区与 "Always / Ask First / Never" 三档权限。

### 2.5 Agent memory
- 核心张力："automatic memory capture reduces developer burden, but uncurated memory degrades agent performance."
- 建议在会话末尾批量审阅，"when context is freshest"。
- 晋升管线（promotion pipeline）：Memories = "Per-developer, cross-session"，"Per-memory human approval" → Rules = 全队，"Committed to version control"。原文目标："individual developers learn from their sessions, curate what matters, and promote patterns the entire team should follow."
- 引 OpenAI Codex 的晋升触发：更新 AGENTS.md "when the agent makes the same mistake twice."

### 2.6 Living specs
- 静态文件和 memory 都做不了 feature 级追踪，因为缺 "bidirectional updates and structured task tracking."
- "the spec auto-updates as agents complete work"，需求变更传播到并行 agent。
- 样例 spec：JWT 认证 feature，Architecture 段（auth-service、api-gateway、RS256）+ Tasks 勾选清单（已完成 / "[in progress]" / 未开始）。

### 2.7 判定流程（四问，按序）
1. agent 读代码能发现吗？能 → 不存。
2. 适用于每个任务吗？是 → context file。
3. 数周到数月稳定吗？是 → agent memory（全队适用则晋升为 rule）。
4. feature 专属且在变吗？是 → living spec。

示例映射（转述）：build 命令、命名约定 → context file；Redis vs Memcached 的决定 → 先 memory 再晋升；未决的产品问题 → living spec；任务完成状态 → living spec；"不要重构某段代码"的警告 → context file。

### 2.8 反模式表（转述，引号内为原文）
| 反模式 | 后果 |
| --- | --- |
| 把 feature 决定写进 AGENTS.md | 文件膨胀，"adherence drops" |
| 团队约定只存在个人 memory | 队友的 agent 行为不一致 |
| 把演进中的意图写进静态文件 | "Spec rot: the file says one thing, the code does another" |
| 把完整聊天记录当 memory | "Mostly noise" |
| 没有任何持久层 | agent "resurface already-rejected approaches" |

另：即使 Context Engine 深度索引（"400,000+ files"）也推不出 "undocumented team decisions, operational procedures, or evolving feature intent."

### 2.9 结论
先找代价最高的持久化故障，再定位到层：普遍问题进 "AGENTS.md or the workspace rules"；工作中学到、需要审阅的留在 "the agent's memory"；随 feature 演进的放进 "a living spec so every active agent stays aligned."

### 2.10 同系列相关 guides
- **How to Build Your AGENTS.md**（https://www.augmentcode.com/guides/how-to-build-agents-md ，2026-03-31，更新 2026-09-04）：引 ETH Zurich/LogicStar.ai 论文，只写 agent 发现不了的内容，"repository overviews, although popular and recommended by model providers, are not helpful"；六个常见段落（精确版本的 stack、带完整 flag 的命令、约定、测试规则、"Don't Touch" 边界、非标准工具）；目标 "under 200 lines"；层级 "files closer to your current directory override earlier guidance because they appear later in the combined prompt"；Codex 32 KiB 上限下 "a deep tree can lose its leaf instructions without saying so"；陈旧："A directory listing goes stale faster than anything else in the file and returns the least while it lasts."；"Rules are rarely removed"；更新时机 "Rules should respond to observed failure, not be generated speculatively."；"Measure whether the file changed anything before adding to it."
- **Context Engineering: Enhancing Agentic Swarm Coding through Intent, Environment, and System Memory**（https://www.augmentcode.com/guides/context-engineering-enhancing-agentic-swarm-coding-through-intent-environment-and-system-memory ，2025-09-24，更新 2026-06-18）：四层——Intent（"task specifications, architectural constraints, and project invariants"）、Environment（"file structures, dependency graphs, test results, and service relationships"）、System memory（"discovered patterns, architectural decisions, and validated conventions"）、Shared agent state（跟踪 "which files have been modified, which tests have been run, and which decisions have been validated"）。交接失真："a sub-agent receiving a task mid-pipeline has no access to the file contents, test outputs, or architectural reasoning accumulated by the orchestrator." 严格度三级："spec-first... spec-anchored... and spec-as-source."
- **Spec-Driven AI Code Generation With Multi-Agent Systems**（https://www.augmentcode.com/guides/spec-driven-ai-code-generation-with-multi-agent-systems ）：spec 是 "define requirements, acceptance criteria, data models, and API contracts in a single document that agents reference continuously"；Verifier "checks each implementation against the living spec"，使 "outdated specs produce flagged discrepancies during development, not during production incident response"；第三方 agent 经 MCP 访问 Context Engine "with more limited context"。
- **How to Define Custom Specialist Agents in Intent**（https://www.augmentcode.com/guides/how-to-define-custom-specialist-agents-in-intent ，2026-04-24）：见 §6.2。
- **Intent Walkthrough: From Prompt to Merged PR**（https://www.augmentcode.com/guides/intent-walkthrough-prompt-to-merge ）：见 §6.2。
- **Cosmos Experts: AI Agents That Learn From Feedback**（https://www.augmentcode.com/guides/cosmos-experts ）：见 §1.2、§6.1。
- 搜索中出现但未打开的：Harness Engineering for AI Coding Agents、AI Agent Loop Token Costs（摘要称 AGENTS.md 类文件可让每会话推理成本增加 20% 以上，未核实）、Agentic Infrastructure stack、CI/CD for AI Agents、Mastering Context Engineering。

---

## 3. Rules / Guidelines / AGENTS.md

来源：https://docs.augmentcode.com/setup-augment/guidelines 、https://docs.augmentcode.com/cli/rules

| 项 | 内容 |
| --- | --- |
| 用户级 rules | `~/.augment/rules/`；"User rules... are always treated as 'Always' type and are automatically included in every prompt regardless of any frontmatter configuration." |
| 工作区 rules | `<workspace_root>/.augment/rules/`（CLI 递归找 `.md`）；"Files in `.augment/rules/` are only loaded from the workspace root." |
| 旧版工作区 guidelines | 仓库根 `.augment-guidelines`，进版本库，"everyone working on the codebase has the same guidelines" |
| IDE 用户 guidelines | VS Code `~/.augment/user-guidelines.md`；本地存储，"will not propagate to JetBrains IDEs and vice versa" |
| 类型（IDE） | Always："contents will be included in every user prompt"；Manual："needs to be tagged through @ attaching the Rules file manually"；Auto："Agent will automatically detect and attach rules based on a description field" |
| 类型（CLI） | frontmatter `always_apply` / `agent_requested`；"Manual rules are IDE-only and are skipped by the CLI" |
| 层级 | 只有 `AGENTS.md` 与 `CLAUDE.md` 支持目录层级：从当前文件所在目录向上找，"stops at the workspace root (since workspace root rules are already loaded separately)"；"cached per conversation session to avoid duplicate inclusion" |
| CLI 加载顺序 | `--rules` 指定文件 → CLAUDE.md → AGENTS.md → `.augment-guidelines` → `.augment/rules/` → `~/.augment/rules/`；`--rules` "will append the specified rules to any workspace guidelines" |
| 字数上限（IDE） | User Guidelines "24,576 characters"；Workspace Guidelines + Rules 合计 "49,512 characters"，超出时按优先级取：manual rules → always + auto rules → `.augment-guidelines` |
| CLI 上限 | 未找到数值 |
| 子 agent 定义 | `~/.augment/agents/`（用户）或 `./.augment/agents/`（共享、进版本库），Markdown + YAML frontmatter（name/description/model/color，另有 `tools`/`disabled_tools`，"`disabled_tools` takes precedence"）（https://docs.augmentcode.com/cli/subagents ；Intent 专家指南） |
| Cosmos skills | `cosmos/files/organization/.augment/skills/<name>/<name>.md`，遵循 agentskills.io，frontmatter `name`（1–64）+ `description`（1–1024）；VFS 中 "discovered and loaded automatically by Experts"（https://docs.augmentcode.com/cosmos/config-skills ） |
| Intent | 自动扫描 "AGENTS.md, CLAUDE.md, and files under a skills/ directory"；另有 "Global instructions — Personal rules applied across all workspaces (Settings → Agent Behavior)"（https://www.intentapp.dev/docs ） |
| Code Review | 自动读取 AGENTS.md/CLAUDE.md，另有 `.augment/code_review_guidelines.yaml`（见 §7） |

User vs workspace 的区别（归纳）：用户级 = 本机、个人偏好、总是加载、不进仓库；工作区级 = 仓库内、全队共享、可按 always/manual/auto 选择加载。

---

## 4. Context Engine

| 问题 | 发现 | 来源 |
| --- | --- | --- |
| 实时性、按人 | "Therefore we maintain a real-time index of your codebase, for each user."；动机 "professional developers tend to switch branches fairly often"；"our indexing system is capable of processing many thousands of files per second"；对手 "updating the context every 10 minutes, which is also not sufficient" | https://www.augmentcode.com/blog/a-real-time-index-for-your-codebase-secure-personal-scalable |
| 权限 | "the IDE must prove to the backend it knows a file's content by sending a cryptographic hash"（proof of possession：客户端必须证明持有文件内容才能检索到它）；"predictions are strictly limited to the data the user is authorized to access" | 同上 |
| 分支 | 本地索引跟随工作目录（切分支即重建受影响文件）；远程 MCP 只索引 "Selected repos' default branches"，"Automatically when commits are pushed to the default branch" | 同上；https://docs.augmentcode.com/context-services/mcp/overview |
| commit history | Context Lineage："Indexes recent commits on the current branch, including message, author, timestamp, and changed files."；"Summarizes diffs with a lightweight LLM step"（"Gemini 2.0 Flash to condense each commit into a few sentences"）；"New commits are detected in near real time" | https://www.augmentcode.com/blog/announcing-context-lineage （2025-07-29） |
| 当作上下文的东西 | "Indexes commit history, codebase patterns, external sources (docs, tickets), and tribal knowledge." | MCP overview |
| 对外 MCP | 本地 server（Auggie CLI stdio）暴露 `codebase-retrieval`，"Real-time indexing of your working directory"；远程 server 需 GitHub App，适合 "Cross-repo context" 与 "CI/server environments without a local working tree"；价格 "roughly $0.03–$0.06 per query" | MCP overview |
| Context Connectors | 开源式管线：Source（"GitHub, GitLab, BitBucket, or website"）→ Indexer（遵守 .gitignore，哈希比对，增量）→ Store（本地或 S3，"for incremental updates"）→ Context Engine → Client（"CLI, MCP server, or your own application"）；读全文件时 MCP "from the original source (filesystem or Git API)" 取，不从索引取 | https://docs.augmentcode.com/context-services/context-connectors/how-it-works |
| SDK | 可 "Explicitly index files from any source (APIs, databases, memory, disk)" 并保存/加载状态 | https://docs.augmentcode.com/context-services/sdk/overview （llms-full 内） |
| 跨仓库（Code Review） | 在 `<repo-root>/AGENTS.md` 写 External Repositories 段，列 repo + description，并指示 "call `augment_code_search` tool with repo_owner, repo_name, and a natural language query"；需在 Code Review MCP 设置加 `https://api.augmentcode.com/mcp` | https://docs.augmentcode.com/codereview/cross-repo-context |
| 规模 | 营销口径 "400,000+ files"（多处） | 多个 guide |

---

## 5. Remote Agents（已移除）及其在 Cosmos 中的对应物

- 状态：已从 IDE 扩展移除（§0）。旧 docs 页 https://docs.augmentcode.com/using-augment/remote-agent-environment 现在返回的是普通 Agent 页内容（WebFetch 结果），没有 remote agent 内容。
- 旧机制（仅搜索摘要，未核实原页）：每个 remote agent 跑在云 VM，需选 environment，bash 初始化脚本可自动生成并提交进仓库共享；memories 对同步与异步 agent 都适用。
- **Cosmos 对应机制（有原文）**：
  - Environment："The compute environment where your agents access filesystem, repositories, execute code, and run tools." 云环境 "Persistence between sessions: New each sessions"，"Concurrency: Unlimited"；自托管 daemon "Disk and other state persists"，并发 "Bounded by the number of daemons you've connected"（https://docs.augmentcode.com/cosmos/environments/overview ）。
  - Session 生命周期：对话永久保存；环境 "runs for up to 24 hours at a time"，长期暂停后 "may restart from a clean state and lose uncommitted changes"（https://docs.augmentcode.com/cosmos/sessions-overview ）。
  - **是否共享上下文**：不共享上下文窗口——"each delegated agent has its own context window, its own system prompt, can define its own model, and runs in parallel with the manager, reporting progress back."（https://docs.augmentcode.com/cosmos/workers-subagents ）。共享的是 VFS 文件（Organization scope 用于 "outputs an Expert wants to hand off to another Expert"）和 memory。
  - **三种委派**：
    - Worker："a manager Expert launches another Expert as a separate session with its own VM, Environment, integrations, and permissions."，协调面 "Manager ↔ worker messages"。必须显式要求："Cosmos does not launch one implicitly."
    - Subagent："A subagent is just an agent"，同会话内，"scoped to a repo"。
    - Expert-to-Expert：经共享集成间接协作。原文例子："PR Author creates a pull request. Deep Reviewer is triggered by the pull-request-created event, analyzes the change, and posts review comments. PR Author subscribes to events on that pull request, including newly posted comments, and responds to the review feedback." "No Expert launches another; the pull request is the medium." 好处："people can inspect the interaction between agents — for example, by reading the pull request comments — and intervene whenever they want."
  - 官方警告："Worker orchestration can get complicated for the same reasons multi-threading is: coordination, complex interleavings, data races, deadlocks, and unclear ownership. Prefer a single Expert when the whole workflow fits in one context window."
  - Space 继承："a worker launched by a manager agent inherits the manager's Space, so an entire worker subtree stays together."（https://docs.augmentcode.com/cosmos/spaces/managing ）
  - 事件驱动（https://docs.augmentcode.com/cosmos/automations ）：trigger "opens a new session from the Expert"；subscription "delivers the event into the existing session"，由 agent 运行时用 `subscribe-event` 创建，"when the session ends, its subscriptions expire"。事件 payload 作为会话第一条消息；过滤器 JSONLogic 在建会话前执行，"events you don't care about cost nothing"；有 events log 与 run history。
  - 幂等：自定义 Expert 的 prompt 应含 "idempotency checks for event-driven Experts so repeated triggers do not create duplicate comments, tickets, or sessions"（experts-configure-custom）。Ticket Manager 的 GitHub 版 "removes the label after claiming an automated run so later updates do not create duplicate sessions"。

---

## 6. 2026 年多 agent / spec / context 产品

### 6.1 Cosmos 的"软件工厂"循环与 Template Experts

- 定位原文："The work keeps one memory, even when it moves. Files, knowledge, and Experts, shared and versioned across the org."；"Agents write what they learn back to shared knowledge."；"Nothing merges without a human at the checkpoint."（https://www.augmentcode.com/product/cosmos ）
- 核心循环图（https://docs.augmentcode.com/cosmos/guides/software-factory-core-loops ）：
  - 入口循环：Spec Driven Development（Project Builder，产出 PRD/Tech spec/Architecture 存 Cosmos Files，再进 Jira/Linear）；Ticket and Dispatch（Feedback Triager、Backlog Dispatcher）；Incident Response。汇合到 "Ready for implementation"。
  - 产码循环：PR Author → PR Risk Analyzer → Deep Code Reviewer → PR Fixer → E2E Verifier（"intake → detect → checkout → install → start web server → serve pages → verify → verdict → report"）→ Pair Reviewer（与人）→ Memory Manager（"captures learnings"）。回路："Verification or review findings return to PR Author for another pass"。
  - 页面有 "v1.0 (pilot day #1)" 视图，把 Ticket/Dispatch、Incident、E2E Verifier 标为 "not yet built"（文档页的状态，可能已过时）。
- **Project Builder**："launching a PR Author worker per unit of work in dependency waves"；"It never merges implementation changes and never writes feature code itself"。spec 存在哪里：该页未写（未找到），核心循环图显示为 Cosmos Files。
- **Ticket Manager**：一张票一个 owner；"keeps one canonical status comment up to date as work moves through four milestones: started, workers dispatched, pull requests or merge requests opened, and terminal."；实现前核对 "concrete problem, desired outcome, implementation scope, and target repositories"；"A delegation trigger requests triage; it does not bypass this readiness check."；意图未定时 "writes a specification, links the session from the ticket for human review, and waits"；"closes the ticket only after all expected changes are merged or otherwise terminal."
- **Ticket Dispatcher**：定时扫描，"applies a readiness rubric"，"respects a maximum number of dispatcher-owned open changes so automation does not flood the review queue"，"records concise skip reasons for tickets that need more human input."
- **PR Author**："creates the branch, implements the change, opens the review, and stays with it through CI, merge conflicts, and review comments."
- **Verifier**："acquires or uses a test environment, serves the change, provisions the identities or flags needed to exercise it, runs an end-to-end verification pass, and reports findings with linked evidence."；"it reports what it observed, what could not be observed, and what evidence supports the finding."；证据形态 "screenshots, logs, traces, and captured outputs"。
- **Template Expert 的 prompt 结构**："the system prompt is a single include statement that references a prompt managed by Augment. Your customizations ... are appended below that include."
- Cosmos Experts 指南：检查点模型 "Eight human interruptions in a typical SDLC loop become three checkpoints"（优先级、spec/intent 审阅、代码演进）。

### 6.2 Intent（桌面端，spec 驱动多 agent）

来源：https://www.augmentcode.com/blog/intent-a-workspace-for-agent-orchestration （2026-02-10，作者 Amelia Wattenberger）；https://www.intentapp.dev/docs ；https://www.augmentcode.com/guides/intent-walkthrough-prompt-to-merge ；https://www.augmentcode.com/guides/how-to-define-custom-specialist-agents-in-intent

- **角色**：Coordinator / Implementor / Verifier 为默认团队；docs 列六个内置 specialist：Coordinator、Developer（"Plans, implements, and verifies by itself"，新 workspace 默认单个 Developer）、Implementor（"Called by the Coordinator"）、Verifier（"Reviews work against acceptance criteria"）、UI Designer、PR Reviewer。自定义 specialist 在 Settings → Specialists，含 behavior prompt、provider、model。
- **Living spec 怎么共享**：
  - "As code changes, agents read from and update the spec so every human and agent stays aligned."（blog）
  - Spec 是 workspace 的一个 note："the source of truth for what the workspace is trying to accomplish"，推荐四段 Goal / Tasks / Acceptance Criteria / Non-goals；"Agents read the Spec before starting work."（docs）
  - Notes："anything you write, agents can read, and vice versa"；"Notes as shared memory: Specs, task notes, and notes persist across agents and sessions, so an agent reads a short note instead of re-deriving context or re-reading a long transcript."（docs）
  - Context tab = "the Spec, your notes, connected MCP servers, and any detected agents and skills files"。
  - spec 编辑实时传播："edits propagate to all active agents mid-session, which is what prevents spec rot."（walkthrough）
- **任务结构**：`@@@task` 块保存后转为 Task Note，属性 `key=`、`dependsOn=`、`conflictsWith=`、`effort=`；状态 "in progress, blocked, waiting, review required"。Coordinator "decomposes the spec into a dependency-ordered directed acyclic graph (DAG)"，按 "waves" 并行派发（专家指南）。
- **隔离**："Intent is organized around isolated workspaces, each backed by its own git worktree."；"Each Implementor commits to its own branch off the Space's base."；"The Coordinator reconciles file overlap at the merge step rather than during execution."（walkthrough）
- **三个人工检查点**：spec 审阅（"Stop the Coordinator and edit before approving"，建议加爆炸半径限制如 "Do not modify exported signatures of `src/lib/redis.ts`; extend only."）、task 审阅（找 "tasks with overlapping file targets"，删除 acceptance criteria 追溯不到 spec 的任务）、diff 审阅。
- **验证**：Verifier 对照 spec 的声明检查；范围限制 "Runtime behavior and security analysis sit outside its scope."；发现缺口时 "Implementors get another pass before final review, and the living spec updates to reflect what was actually built."；关键限制 "A property absent from the spec stays absent from the Verifier's checks."（walkthrough）。"the Verifier and Implementers have opposing goals"；建议 Verifier 必须 "identify at least one specific problem before an approval is valid"（专家指南）。视觉证据："Agents embed before-and-after screenshots — saved as ordinary workspace files — directly in the Spec"（docs）。
- **工具权限强制**："An agent bound only to `view` and `codebase-retrieval` cannot modify files regardless of what its prompt says."（专家指南）
- **唤醒与成本**（docs "Token Savings"）："Hooks and PR monitors — The daemon does the checking and wakes an agent only on a meaningful change, instead of polling inside a turn."；"Debounced PR wakes — A stream of comments and checks collapses into one wake."；"Batched reports and events — Report-to-parent debounce and batched event subscriptions combine several child reports or events into a single wake."；"Idle reaping and agent caps — Forgotten or runaway agents are stopped before they burn more turns."；"Slim conversation reads — When one agent reads another's transcript, large tool inputs, outputs, and images are truncated to previews"；按角色分模型："implementors and verifiers can run a cheaper, lower-effort model while the Coordinator uses a stronger one."；"Agent coordination provides better results but uses more tokens, because agents have to communicate."
- **BYOA**：providers "Augment Auggie, Anthropic Claude Code, Grok Build, OpenAI Codex, OpenCode, Pi, and Unsloth"；非 Augment agent 建议装 Context Engine MCP。
- **合并**：GitHub PR，或 "The Merge drawer merges the workspace branch back to trunk without a PR."
- Intent 里有没有 Memory Review 式的自动 memory：未找到（docs 只把 notes/spec 称为 shared memory）。

---

## 7. Augment Code Review 与上下文、记忆

| 问题 | 发现 | 来源 |
| --- | --- | --- |
| 用什么上下文 | 完整 diff；"Augment's Context Engine" 访问 "your full codebase"；PR 标题与描述（"more detailed PR descriptions help"） | https://docs.augmentcode.com/codereview/overview |
| 是否读 rules | 读：`<repo-root>/.augment/code_review_guidelines.yaml`（每条 id、description、severity high/medium/low，支持 glob 范围、`file_paths_to_ignore`，"per-guideline analytics"）；并 "If your repository already contains `AGENTS.md` or `CLAUDE.md` files, Augment Code Review automatically discovers and applies them."，官方称 "the recommended way" | https://docs.augmentcode.com/codereview/review-guidelines |
| 焦点 | "high signal-to-noise ratio"；"the agent avoids low-value style nags and focuses on objective issues" | overview |
| 外部上下文 | MCP（本地/远程）；加 MCP 后要 "Add a review guideline telling Augment Code Review when to use the MCP server"；跨仓库见 §4 | https://docs.augmentcode.com/codereview/mcp-context |
| 反馈 | 对行内评论点 👍/👎 | https://docs.augmentcode.com/codereview/providing-feedback |
| 独立 Code Review 产品是否从反馈学习 | 未找到（反馈页只说是 "in product feedback"，没说会改变后续评审） | — |
| Cosmos 评审是否从反馈学习 | 是，Code Review Memory Manager（noisy memory）："records useful human comments, reactions to agent findings, addressed change requests, and the outcome of the change. Routine acknowledgments, bot updates, and process-only comments are filtered out."；"Explicit human feedback carries more weight than reactions or an inferred outcome, so strong feedback can become useful memory immediately while weaker signals must recur."；"Risk Analyzer, Deep Reviewer, and Pair Reviewer load relevant guidance for the repository and changed paths on their next run. They use it to avoid known false positives and recognize team-specific anti-patterns."；"A raw breadcrumb log preserves the evidence ... while a curated knowledge file contains the concise guidance"；在合并时运行。Memory Manager 还吸收 "Pair Reviewer sessions" | https://docs.augmentcode.com/cosmos/experts-code-review-memory ；https://docs.augmentcode.com/cosmos/experts-code-review |
| 学习到的 memory 是否要人批准 | 未找到批准步骤；按文档是自动更新 curated view（"updates that curated view after each completed change"） | 同上 |
| 评审分工 | Risk Analyzer 分流并按策略自动批准低风险；Deep Reviewer 无交互逐行、对照 AGENTS.md/CLAUDE.md；Pair Reviewer 与人交互，"posts comments or a verdict only after human authorization"；Verifier 运行时证据；PR Dashboard Manager "an observer and entry point, not a controller of the other Experts" | experts-code-review |
| `cosmos approve` 策略 | 可要求：Ownership（请求者是作者且是每个改动文件的 CODEOWNER）；"Current-head review"（无未解决 Deep Reviewer 发现、Pair Reviewer blocker、未处理的人工评论）；"Runtime evidence"（Verifier 对当前 commit 无未处理缺陷）。"An approval never merges the change. A human always owns and performs the final merge." | 同上 |
| 仪表数据 | 营销页示例 "Deep Reviewer · findings accepted / 94% / +9% since v11"（按 Expert 版本追踪评审发现的采纳率） | https://www.augmentcode.com/product/cosmos |

---

## 8. 对一条 spec → 票 → 夜间多 worker → reviewer/verifier → 合并 的流水线可借鉴的机制

每条写：解决的问题 / 前提。

1. **memory 分两种写入模型（simple vs noisy）**：人明确说的规则直接写入 curated 文件；弱信号（反应、结果推断、agent 自己的观察）先进 evidence log，重复出现到阈值才晋升。
   解决：自动记忆被低质量内容淹没，同时不必让人逐条批准每个弱信号。前提：能给信号分级（显式人工反馈 > 反应 > 结果推断），并有一个定期或在合并时运行的整理步骤。

2. **加载时对照现状，冲突就报出来，而不是过期删除**（"flags discrepancies when current evidence conflicts with a remembered rule"）。
   解决：记忆陈旧后被当成事实执行。前提：记忆条目写成可核对的断言（带适用路径或范围），加载它的 agent 被指示去核对并在输出中报告冲突。

3. **在合并事件上从评审结果学习（Code Review Memory）**：票关闭或合并时，收集 reviewer 发现被采纳/驳回、人工评论、修复与否，蒸馏成按仓库、按改动路径加载的评审指南，用来压低已知误报。
   解决：reviewer 每晚重复同样的误报或漏掉团队特有的反模式。前提：评审发现和其处置有结构化记录（例如带事件块的评论），且能按路径过滤加载。

4. **memory → rule 的晋升管线，触发条件"同一错误出现两次"**。
   解决：个人或单次运行学到的约定不传播到其它 worker，或 AGENTS.md 被猜测性规则塞满。前提：晋升进入版本库文件要经过人（或 review），且规则文件有字数预算。

5. **context file 准入两条："undiscoverable" 且 "universal"；feature 专属、会变的东西放 living spec，不放 AGENTS.md**。
   解决：AGENTS.md 膨胀、adherence 下降、"spec rot"。前提：存在一个每票或每 spec 的可写文档位置，并且 worker 被要求读它。

6. **Living spec 双向更新 + 三个人工检查点（spec、tasks、diff）**；Verifier 发现缺口后 spec 更新为"实际建成了什么"。
   解决：夜里多个 worker 各自对着过期 prompt 工作；早上的人读不到"做了什么、偏离了什么"。前提：spec 有并发写入规则（谁能写哪一段），否则多 worker 写同一文件会冲突；Intent 的做法是 task 拆成独立 Task Note，状态分别更新。

7. **任务依赖显式声明（`dependsOn=`、`conflictsWith=`）+ 按 wave 派发 + 审 task 时查"overlapping file targets"**。
   解决：并行 worker 改同一文件导致合并冲突或逻辑冲突。前提：拆票时能预测每票触及的文件或模块；冲突仍会在合并步发生，需有 bounce/重排机制（Intent 的做法是 "reconciles file overlap at the merge step"）。

8. **"A property absent from the spec stays absent from the Verifier's checks."**：verifier 只核对 spec 写出的性质，所以验收标准必须在 spec/票里写全；另外 Verifier 报告必须区分 "what it observed, what could not be observed"。
   解决：verifier 通过但行为缺失；"无法验证"被读成"通过"。前提：票的验收标准可执行；verdict 格式有"未能观察"一栏。

9. **Verifier 与 Implementer 目标对立 + 拒绝橡皮图章**（建议要求 verifier "identify at least one specific problem before an approval is valid"）。
   解决：同模型自评时倾向放行。前提：可接受更多来回轮次；此条是 Augment 指南的建议，不是经过测量的结论（未见数据）。

10. **Expert-to-Expert 以工件为协调面**（PR/票评论是媒介，"No Expert launches another"），而不是 manager 直接消息。
    解决：agent 之间的交互人看不到、无法中途介入；manager 上下文被 worker 汇报塞满。前提：有事件订阅机制（trigger 开新会话、subscription 投递到现有会话、会话结束订阅失效）。

11. **事件唤醒去抖与批处理**（"Debounced PR wakes"、"Batched reports and events"、daemon 检查后 "wakes an agent only on a meaningful change"），加 **idle reaping 与 agent 上限**。
    解决：一串评论和 CI 状态引发多次唤醒，每次唤醒重发整个上下文，token 成本线性增长；忘记关的 agent 空转。前提：唤醒层能判断"有意义的变化"并能合并窗口内事件；有每个 agent 的存活和轮次计量。

12. **Dispatcher 的 backpressure 与 skip reason**（"maximum number of dispatcher-owned open changes"；"records concise skip reasons"）。
    解决：夜间自动化产出的 PR 淹没早上的评审队列；未派发的票原因不明。前提：能数出由流水线打开且未关闭的变更数；票上有写入跳过原因的位置。

13. **一张票一个 owner、一条规范状态评论、四个里程碑，readiness gate 不被委派触发绕过**（Ticket Manager）；关闭前要求所有预期变更 "merged or otherwise terminal"。
    解决：票状态分散在多条评论难以折叠；触发标签被当成"已就绪"。前提：票状态可由脚本维护单一评论或事件折叠；readiness 标准成文。

14. **幂等领取**：自动运行领取后移除触发标签，防止后续更新重复开会话；自定义 Expert prompt 必含幂等检查。
    解决：同一事件或标签重复触发导致重复会话、重复评论。前提：领取动作是原子的（或有锁），且可检测"已有运行"。

15. **审批不等于合并**（`cosmos approve` 只评估策略：ownership、current-head 无未决发现、Verifier 对当前 commit 无未处理缺陷；"A human always owns and performs the final merge"）。
    解决：自动批准被误当成自动合并；在旧 commit 上的验证结论被沿用到新 commit。前提：发现与验证结论绑定到具体 commit SHA。

16. **Verifier 分两层**：spec 对照（Intent Verifier，明确不管运行时与安全）与运行时 E2E（Cosmos Verifier：拿环境、serve、准备身份与 flag、跑、附证据）；官方建议运行时 Verifier 最后上线，因为 "needs a working test environment"。
    解决：把"读代码觉得对"和"跑起来看到对"混为一谈。前提：可重复启动的测试环境与端口/身份隔离。

17. **按角色分模型与 effort**（Coordinator 强模型，Implementor/Verifier 便宜低 effort）与**工具白名单强制**（只给 `view` + `codebase-retrieval` 的 agent 无论 prompt 怎么写都改不了文件）。
    解决：成本；reviewer/verifier 越权改代码。前提：运行器支持按角色配置模型和工具白名单（在 host 层强制，而非只写在 prompt）。

18. **共享文件层的版本化与归属**（VFS：每个版本标注写入的 agent，删除留 tombstone，turn 边界同步）。
    解决：某个出错的 agent 静默覆盖共享状态且无法追查。前提：共享状态走一个带版本的存储；同步点定义清楚（turn 边界），并接受 turn 内其它 agent 看不到中间状态。

19. **Template prompt = 一行 include + 本地追加定制**。
    解决：上游改进 prompt 时覆盖掉本地定制，或本地 fork 后收不到上游改进。前提：prompt 由可组合的片段拼成，定制只追加不修改上游片段。

---

## 读过的 URL 清单

直接打开（WebFetch 或 curl）：
- https://docs.augmentcode.com/llms.txt
- https://docs.augmentcode.com/llms-full.txt （下载后按段读取：experts-memory、experts-code-review-memory、experts-configure-custom、experts-pr-author、experts-pr-fixer、experts-project-builder、experts-risk-analyzer、experts-templates、experts-ticket-dispatcher、experts-ticket-manager、experts-verifier、experts-deep-reviewer、experts-pair-reviewer、experts-feedback-triager、experts-incident-investigator、experts-code-review、experts、environments/overview、sessions-overview、spaces/overview、spaces/managing、workers-subagents、codereview/cross-repo-context、codereview/mcp-context、cosmos/config-skills、cli/subagents、analytics-api 字段说明）
- https://docs.augmentcode.com/cosmos/experts-memory.md
- https://docs.augmentcode.com/cosmos/experts-code-review-memory.md
- https://docs.augmentcode.com/setup-augment/guidelines.md
- https://docs.augmentcode.com/cli/rules.md
- https://docs.augmentcode.com/cosmos/workers-subagents.md
- https://docs.augmentcode.com/cosmos/understanding-files.md
- https://docs.augmentcode.com/cosmos/guides/software-factory-core-loops.md
- https://docs.augmentcode.com/cosmos/experts-verifier.md
- https://docs.augmentcode.com/cosmos/experts-ticket-dispatcher.md
- https://docs.augmentcode.com/cosmos/experts-code-review.md
- https://docs.augmentcode.com/cosmos/experts-pr-author.md
- https://docs.augmentcode.com/cosmos/experts-triggers-subscriptions-integrations.md
- https://docs.augmentcode.com/cosmos/experts-project-builder.md
- https://docs.augmentcode.com/cosmos/experts-deep-reviewer.md
- https://docs.augmentcode.com/cosmos/experts-pair-reviewer.md
- https://docs.augmentcode.com/cosmos/automations.md
- https://docs.augmentcode.com/context-services/mcp/overview.md
- https://docs.augmentcode.com/context-services/context-connectors/how-it-works.md
- https://docs.augmentcode.com/codereview/overview.md
- https://docs.augmentcode.com/codereview/review-guidelines.md
- https://docs.augmentcode.com/codereview/providing-feedback.md
- https://docs.augmentcode.com/using-augment/remote-agent-environment （现返回普通 Agent 页内容）
- https://www.augmentcode.com/guides/agent-memory-vs-context-engineering （打开两次）
- https://www.augmentcode.com/guides/how-to-build-agents-md
- https://www.augmentcode.com/guides/context-engineering-enhancing-agentic-swarm-coding-through-intent-environment-and-system-memory
- https://www.augmentcode.com/guides/spec-driven-ai-code-generation-with-multi-agent-systems
- https://www.augmentcode.com/guides/intent-walkthrough-prompt-to-merge
- https://www.augmentcode.com/guides/how-to-define-custom-specialist-agents-in-intent
- https://www.augmentcode.com/guides/cosmos-experts
- https://www.augmentcode.com/guides/remote-agents-guide-deploy-autonomous-development-workers
- https://www.augmentcode.com/blog/intent-a-workspace-for-agent-orchestration
- https://www.augmentcode.com/blog/how-we-built-memory-review
- https://www.augmentcode.com/blog/announcing-context-lineage
- https://www.augmentcode.com/blog/a-real-time-index-for-your-codebase-secure-personal-scalable
- https://www.augmentcode.com/changelog/memory-review
- https://www.augmentcode.com/changelog
- https://www.augmentcode.com/product/cosmos
- https://www.augmentcode.com/product/remote-agents
- https://www.intentapp.dev/docs （curl 下载后读取 Specialists、Context、Notes、Rules & Skills、Token Savings 段）
- https://tessl.io/blog/with-cosmos-augment-code-wants-to-give-ai-coding-teams-a-shared-memory-and-context （第三方）
- https://blog.kilo.ai/p/is-augment-sunsetting-its-ide-extensions （第三方）

只见搜索摘要、未打开：SiliconANGLE Cosmos 发布报道（https://siliconangle.com/2026/06/05/augment-code-launches-cosmos-bring-agentic-ai-software-development-teams/ ）、Cosmos Week 33 Release Notes、Intent 0.3.4 / 0.2.6 release notes、Harness Engineering guide、AI Agent Loop Token Costs guide、loop engineering blog、The New Stack remote agents 报道。

## 方法局限
- WebFetch 经一个小模型转述页面，长段逐字复述会被拒；凡是 llms-full.txt 或 curl 下载能直接读到的，引语取自原文；augmentcode.com 的 guides/blog 引语来自 WebFetch 返回的短句，未与原 HTML 逐字比对。
- 未登录 Cosmos 或 Intent，未实际运行任何产品；所有机制描述来自文档与博客，不是实测。

# 调研 5：Nowledge Mem 能否作为 MMW 的共享上下文载体

调研日期 2026-09-13。本机 `nmem` CLI 与 server 均为 v0.10.78（`nmem status`），官网 changelog 最新为 0.10.81（2026-09-12）。全程只做只读操作：`--help`、`status`、`stats`、`doctor`、`context`、`memories search/list/show`、`threads list/search`、`fs ls/stat/recall/capabilities`、`spaces`/`agents`/`rules`/`skills`/`tasks`/`schedules` 的列出、`feed reviews`（读）、`config ... show`、`resources get`、一次 `ask --ephemeral`（不写 Timeline）、对 `http://127.0.0.1:14242` 的 GET。原始命令输出存于 `scratchpad/nm/`（`help1.txt`、`help2.txt`、`ro1.txt`、`ctx.json`、`openapi.json`）。

证据标注：【命令】本机命令输出；【文件】本机文件路径；【URL】网页原文；【推断】未直接验证。

---

## 0. 结论先行

1. **它能做"跨任务、跨仓库"的模糊回忆层，做不了"同一夜跨 agent、跨 spec"的确定性协调层。** 语义检索（0.5 s）、按 label / unit type / 时间 / metadata 过滤、自动把每个 worker、reviewer 会话存成 thread 并蒸馏成 memory，这些都已经在本机跑着——MMW 夜里的 worker 会话今天已经被自动采集（见 §2.4）。但自动蒸馏排队几十分钟、结果由模型决定、label 不可靠、没有"只给我这个 spec 的"强过滤，所以不能承担同一夜内必须送达的信息。
2. **"读"要做到完整、自动，Nowledge Mem 自带的机制只到 Context Bundle 为止**：身份、space、rules、Working Memory 四块，**不含任何按当前任务检索出的 memory**。按 agent 身份区分内容靠 `NMEM_AGENT_ID` + agent 级 rules；按仓库区分靠 `NMEM_SPACE`；插件**明确不按 cwd / git 推断 space**。按任务关键词自动检索没有现成机制，需要 MMW 自己在派发时算好查询、把结果放进 prompt。
3. **本机现状离可用还差三步**：spaces 处于 disabled；51 条 rules 全是 `draft`，Context Bundle 里 rules 为空；只有一个 `default` agent 身份。Working Memory 把 MMW 与客户产品的内容混在一起，现在会被注入到任何仓库、任何 host 的每个会话。
4. **不同 host 差异真实存在**：Claude Code、Codex、Pi、Cursor（IDE 插件）会在会话开始时自动注入 Context Bundle；Grok Build 的 SessionStart 输出被丢弃，只能靠技能在"第一个相关回合"读；Claude Code 用户级没有 Nowledge MCP，只能走 CLI。
5. **与 ADR 0001（tracker 是事实权威）的边界**：Nowledge Mem 只能作为"提示与经验"的第三份副本，永远不作为行动依据；票状态、依赖、Owns、验收结论、事件都留在 tracker 与仓库。

---

## 1. 数据模型

| 对象 | 是什么 | 谁生成 | 如何关联 | 证据 |
| --- | --- | --- | --- | --- |
| memory | 一条原子知识：`title`、`content`、`unit_type`（fact/preference/decision/plan/procedure/learning/context/event）、`importance`、`labels`、`space_id`、`metadata`、`claim_status`、`source_grounding`、`trust_warnings`、`is_latest`、`lifecycle_state` | agent 用 `nmem m add` / MCP `memory_add` 显式写；或后台蒸馏 thread 生成（`source: agent`，`metadata.distillation_type: simple_llm`） | `source_thread` 指回来源 thread；EVOLVES 边连新旧版本；label；entity | 【命令】`curl /memories/d5ca323a…` 输出含 `source_thread`、`claim_status 'planned'`、`source_grounding`、`trust_warnings []`；label-backfill 技能称"87% of this store arrives through that distillation path"【文件】`~/ai-now/skills-active/label-backfill-a5fd56b8/SKILL.md` 第 100 行 |
| thread | 一段完整会话记录，带 `source`（claude-code/codex/grok…）、`project`、`workspace`、`metadata`（`session_id`、`cwd`、`git.commit_hash`、`git.branch`） | host 插件的 Stop/SessionEnd/PreCompact 钩子调 `nmem t capture`；Pi 扩展直接 POST `/threads` | 蒸馏出 memory | 【命令】`/threads/codex-01a0974d…` 输出 `workspace '/Users/cheuklapchan/agentflow/.worktrees/issue-900'`、`git.branch 'issue-900'`；最近 200 条 thread 来源 `claude-code 141, codex 41, grok 18` |
| label | 字符串标签，用于过滤 | 保存时由模型一次性给出，之后无后台复查 | memory 多对多 | 【文件】label-backfill SKILL.md 第 6 行："asks a model for a memory's labels once, while saving it, and never asks again"；【命令】`/labels/health`：3354 个 label，`singleton_rate_pct 70.7` |
| entity / graph | 知识图谱实体（6755 个），由 KG 抽取生成；无自定义 ontology | 后台 `KG Extraction` | memory ↔ entity；`nmem graph expand` | 【命令】`nmem stats`；`nmem ontology show`："No ontology configured" |
| community / wiki | 图上的主题聚类；wiki 把实体、crystal、topic 渲染成 markdown | 后台 Community Detection（每 6 天）、Crystallization | `nmem wiki page topic <id>` | 【命令】`nmem wiki topics`：2 个 topic，其中一个 2806 members（聚类过粗） |
| crystal | 把多条相关 memory 合成一篇引用来源的参考文 | 后台自动 | memory 集合 | 【URL】advanced-features："Crystals appear when the system has enough material to say something useful. You don't request them." |
| library / source | 导入的文件、网页、笔记，解析、分块、可搜索 | 用户或 agent `nmem library add` | 可 `extract` 出 memory | 【命令】`nmem library --help`；本机 0 sources |
| space | 存储隔离边界，含 `instructions`、`sharedSpaceIds`、`defaultRetrievalMode`（strict/shared/all）、独立 Working Memory | 用户 `nmem spaces create` | memory/thread/source 各属一个 space | 【命令】`nmem spaces`："Memory Spaces (disabled)"，只有 Default |
| agent identity | 命名的 AI 身份：`role`、`default_space`、`instructions`（agent 专属 rules）、`tags`；"Identity is provenance, not auth" | 用户 `nmem agents enroll` | 进程用 `NMEM_AGENT_ID` 选中；写入时记为 `agent_id` | 【命令】`nmem agents`：仅 `default`；【命令】openapi `MemoryCreateRequest.agent_id`："Portable AI Identity attribution. Identity is provenance, not auth." |
| rules | 常驻指导，scope 为 global / agent / space，status 为 draft / active / archived，priority 0–100 | 用户 `rules upsert`；后台 `guidance_rule_review` 每 7 天从证据里提 draft | 编译进 Context Bundle 的 `rule_stack` | 【命令】`nmem rules list --all`：51 条，全部 `draft`；bundle `rule_stack.status 'empty'`，notes："Rules are compiled from owner settings and review-approved evidence. They are not memory unit types and not Skills." |
| Working Memory | 每个 space 一份每日简报（Focus Areas / Briefing / Explore Next），默认 space 同步到 `~/ai-now/memory.md` | 后台每日 5:00 生成 + 刷新；人或 agent 可 `wm edit/patch` | 注入 Context Bundle | 【命令】`nmem config settings show`：`Briefing Hour 5:00`；bundle `working_memory.path '/Users/cheuklapchan/ai-now/memory.md'` |
| skills（managed） | Mem 从用户经验编译出的 SKILL.md，生命周期 candidate→promotable→draft→active，带 eval 与 outcome 回报 | 后台 `skill suggestions`/`skill curator`；`nmem skills create/import` | `skills connect` 软链进各 host 技能目录 | 【命令】`nmem skills list --stage all`：2 active（memory-health、label-backfill），10 candidate/promotable；`nmem skills hosts`：Codex/Claude Code/Cursor/Zed connected，Pi 仅 detected |
| feed | 不可变 Timeline 事件；其中 review 家族（`flag_contradiction`、`memory_cleanup_review`）需要人明确批准 | 后台检测 | `related_memory_ids`；`nmem feed resolve` 写 EVOLVES 边 | 【命令】`nmem --json feed reviews -n 1`：`total 5`，类型 `flag_contradiction`；【文件】memory-health SKILL.md 第 6 行："One judgement it will not make alone is that two memories contradict each other." |
| schedules / tasks | schedules 是用户建的定时 AI Now 任务（草稿需 confirm）；tasks 是在跑/排队工作的只读视图 | 用户 / 后台 | — | 【命令】`nmem schedules list`："No recurring tasks yet."；`nmem tasks`：多条 `Thread distillation` 在 Queued，最早"47m ago" |
| ontology | 图谱类型词表，可起草、提案、接受 | 用户 / curator | 只管 KG 类型，不管 label | 【文件】label-backfill SKILL.md 第 100 行："the configurable ontology governs knowledge-graph object and link types rather than labels" |
| team | 连接 Nowledge Cloud 团队工作区时，key 以谁的身份行事 | Cloud | `memories add --contribute` 单向复制到团队 | 【命令】`nmem team whoami`："Team mode is off."；`/capabilities` `"team": false` |
| Nowledge FS | 把以上对象投影成只读为主的路径树：`/memories/by-id|by-date|by-label|by-type|crystals`、`/context/bundle.md`、`/working-memory/today.md`、`/feed`、`/skills`、`/threads`、`/sources`、`/wiki`、`/at`、`/of`；可写仅 `/memories/by-id/` 与 `/working-memory/today.md` | server | `nowledgemem://` 与 FS 路径互通 | 【命令】`nmem fs capabilities`：`version "0.9-preview"`，`write: write, rm, delete`；openapi `POST /fs/write` 描述 |

---

## 2. 读取路径

### 2.1 Context Bundle

`nmem --json context`（REST `GET /context/bundle`，参数 `agent_id`、`source_app`、`host_agent_id`、`space_id`、`include_working_memory`）返回【命令，`ctx.json`】：

- `owner_profile`（名字、首选语言）
- `agent_profile`（本机为 `derived:default`）
- `active_space`（`retrieval_mode 'strict'`、`search_space_ids ['default']`）
- `rule_stack`（global/owner/space/agent 四层、`shadowed`、`conflicts`；本机 `active_rule_count 0`）
- `working_memory`（全文，本机约 2 KB）
- `kfs_roots`（下一步可读的路径）
- `rendered_markdown`（钩子注入的就是这一段，本机 4.6 KB）、`compiled_hash`

**它不含任何检索结果。** 渲染文本末尾只有 "Explore Next" 三条路径提示。本机读一次 0.02 s。

### 2.2 各 host 接入方式（本机实测配置）

| host | 注入 Context Bundle | 会话采集 | 检索工具 | 证据 |
| --- | --- | --- | --- | --- |
| Claude Code | 插件 `nowledge-mem@nowledge-community` 0.7.24：`SessionStart`（startup/resume/clear/compact）跑 `nmem-hook-read.sh` → `nmem --json context --source-app claude-code [--agent-id $NMEM_AGENT_ID] [--space $NMEM_SPACE]`，失败退回 `wm read`，再退回 `~/ai-now/memory.md`；`SubagentStart` 仅对 `Plan,code-reviewer,architect,researcher` 注入完整 bundle（截断到 4 KB），`Explore` 什么都不给，其他类型只给检索提示；`UserPromptSubmit` 每回合注入一行"Search proactively…"提示 | `Stop`/`SubagentStop`/`SessionEnd` 后台排队 `nmem t capture`，`PreCompact` 同步保存 | 仅 CLI（用户级 `~/.claude.json` 的 `mcpServers` 只有 `claude-design`） | 【文件】`~/.claude/plugins/cache/nowledge-community/nowledge-mem/0.7.24/hooks/hooks.json`、`scripts/nmem-hook-read.sh`、`scripts/nmem-hook-subagent.py` 第 17–19、130–148 行 |
| Codex | 插件 0.1.32：`SessionStart`/`SubagentStart` 跑 `nmem-context.py` 注入 bundle；子 agent 默认名单 `planner,code-reviewer,architect,researcher`，`worker`/`default` 角色只给检索提示 | `Stop` → `nmem t capture --from codex` | 插件自带 MCP `http://127.0.0.1:14242/mcp`（`APP: Codex`） | 【文件】`~/.codex/plugins/cache/nowledge-community/nowledge-mem/0.1.32/hooks/hooks.json`、`hooks/nmem-context.py` 第 29–31、92–103 行、`.mcp.json`；`~/.codex/config.toml` 第 631–641 行的 trusted_hash |
| Cursor | 本地插件 `~/.cursor/plugins/local/nowledge-mem-cursor`：`sessionStart` 跑 `session-start.mjs` 读 bundle；**cursor-agent CLI（MMW worker 用的形态）是否加载本地插件钩子：未验证** | `stop` 钩子 | MMW `install.sh` 写入的 `~/.cursor/mcp.json` `nowledge-mem`，headers 只有 `APP`、`X-Nmem-Tool-Set: external-agent`、`X-Nowledge-Tool-Schema-Profile: slim`，**没有** `X-Nmem-Agent-Id` / `X-Nmem-Space-Id` | 【文件】`hooks/hooks.json`、`hooks/session-start.mjs`；README 第 130 行："MCP tool calls use their normal backend lane unless Cursor/runtime support forwards an explicit `space_id`." |
| Grok Build | **不自动注入**：`nmem-hook-read.sh` 检测到 Grok 直接 `exit 0`，注释 "Grok Build treats SessionStart and SubagentStart as passive hooks and discards stdout. Context is loaded through the plugin skill instead." | 全局钩子 `~/.grok/hooks/nowledge-mem-capture.json`（PreCompact/Stop/SubagentStop/SessionEnd） | CLI；`nmem config mcp show --host grok` 报 "Unsupported MCP client type" | 【文件】`nmem-hook-read.sh` 第 41–48 行；`~/.grok/config.toml` 第 49 行 `enabled = ["nowledge-mem"]` |
| Pi | npm 包 `nowledge-mem-pi` 0.8.6：`before_agent_start` 注入 "## Nowledge Mem Context Bundle"，读失败时注入一行 "startup context unavailable: …"（不静默） | `agent_end` 等事件直接 POST `/threads`、`/threads/{id}/append` | CLI | 【文件】`~/.pi/agent/npm/node_modules/nowledge-mem-pi/extensions/nowledge-mem.ts` 第 459–482、774–810 行；`~/.pi/agent/settings.json` 第 16 行 |

`nmem doctor`【命令】：Claude Code、Codex、Cursor "registered"；OpenCode 未注册；未列 Grok 与 Pi。

### 2.3 检索维度

| 入口 | 过滤维度 | 延迟（本机实测） | 证据 |
| --- | --- | --- | --- |
| `nmem m search` / `POST /memories/search` | `--label`（可重复）、`--metadata key=value`（可重复，同 key 为 OR）、`--time`、`--event-from/to`、`--recorded-from/to`、`--unit-type`、`--importance-min`、`--space`、`--include-history`、`--mode normal|deep`、`--explain` | normal 0.52 s，deep 1.23 s | 【命令】`help2.txt`；`--metadata distillation_type=simple_llm` 过滤生效（3 条），`--metadata source_thread_id=…` 返回 0（原因未查明） |
| `nmem t search` / `GET /threads/search` | `--source`、`--space`；**不能按 workspace / project / git 分支过滤** | 0.07 s | 【命令】openapi `/threads/search` 参数只有 `query, mode, limit, source, space_id` |
| `nmem fs recall` | `--in <root>`、`--unit-type`；返回路径，可接 `fs cat` | 未单测 | 【命令】`nmem fs recall … --paths` 返回 `/memories/by-id/<id>.memory.md` |
| `nmem fs find/grep` | find：`--type --unit-type --label --since --until --mentions`；grep：精确 / 正则 | — | 【命令】`help2.txt` |
| `nmem resources get nowledgemem://…` | 解析交接文本里的稳定引用（memory、context bundle 等）；Working Memory 里已经内嵌 `nowledgemem://memory/<uuid>` 链接 | — | 【命令】`nmem resources get nowledgemem://context/bundle` 返回 bundle；openapi `/resources/resolve`："This endpoint never fetches HTTP(S) or file URLs." |
| `nmem ask` | 跨 memory、thread、library、graph 的有引用问答；默认把问答写进 Timeline，`--ephemeral` 不写 | **129.6 s** | 【命令】返回键 `answer, answer_status, citations, coverage, retrieved, thread_id, timeline_event_id` |

**搜索没有 agent_id / source_app 过滤维度**（openapi `MemorySearchRequest` 字段中无此项）。

### 2.4 自动注入能做到多细

- 按 space：可以，但只认显式 `NMEM_SPACE`。【文件】`nmem-hook-save.py` 第 342–358 行注释："We deliberately do NOT derive a space from the repo / cwd. The old git-basename derivation tagged every captured thread with a repo-named space the user never created."
- 按 agent：可以，`NMEM_AGENT_ID` 选身份，身份决定 agent 级 rules 与默认 space。【URL】raft 集成页："The identity is used only where you set `NMEM_AGENT_ID=cindy` or explicitly pass `agent_id="cindy"`."
- 按当前仓库 / 工作目录：插件不做；需要启动方（MMW `dispatch.sh`）给子进程设 `NMEM_SPACE`。
- 按任务关键词：**没有**。bundle 不含检索结果；各插件只注入"主动去搜"的提示语。自动检索必须由 MMW 在派发时自己做。
- MMW 夜里的会话**已经**被采集：【文件】`~/.codex/plugins/data/nowledge-mem-nowledge-community/nowledge-mem-stop-hook.log` 末尾：`nmem --json t capture --from codex --session-id 01a0974d… --project /Users/cheuklapchan/agentflow/.worktrees/issue-900` → "durable capture accepted"；`nmem t search issue-900` 同时找到 codex worker 线程与两条 claude-code 评审线程（"审查 ticket #900：AC2 未证明策略共享"）。按同一 hooks.json 推断这些会话开始时也注入了 bundle【推断】。

---

## 3. 写入路径

| 路径 | 谁 | 带来源吗 | 证据 |
| --- | --- | --- | --- |
| `nmem m add` / `POST /memories` | 任何 agent（CLI、MCP `memory_add`、REST） | 可带 `--source`、`--source-app`、`--agent-id`、`--source-thread`、`--source-range`、`--event-start`、`--when`；REST 另有自由 `metadata`（**CLI `m add` 没有 `--metadata` 旗标**）。"We never infer provenance, so absence is honest rather than a guess." | 【命令】openapi `POST /memories` 描述 |
| 自动会话采集 → 蒸馏 | host 钩子入队；后台 `thread_distillation` 用远程 LLM 抽取 | memory 记 `source_thread`、`source_grounding`、`claim_status` | 【命令】`nmem tasks`；`config settings show`：`Thread Summaries on`，`models status`：`Local LLM not_installed` |
| `nmem t create` / `t append` | agent 写"交接 thread" | `append` 支持 `--idempotency-key`、`--expected-message-count` | 【命令】`help2.txt` |
| `nmem wm patch --heading` | agent 改某一节 Working Memory | 无版本字段；`fs write /working-memory/today.md --record-version` 有乐观版本 | 【命令】`help2.txt`；openapi `FSWriteRequest.record_version` |
| `nmem rules upsert` / `agents enroll` / `spaces create` | 人或脚本 | — | 【命令】`help2.txt` |

**审阅队列**：只有"两条 memory 互相矛盾"会进 Feed 等人批准（`flag_contradiction`，本机待处理 5 条），动作只写 EVOLVES 边、不改正文，到期 `expired_no_change`【文件】memory-health SKILL.md 第 6、32–35、54–63 行。rules 由 `guidance_rule_review` 生成 draft，需人转 active 才进 bundle【命令】`rules list --all` 全 draft。skills 同理从 candidate 到 active 需人 `activate`。**普通 memory 写入没有审阅**，写完即可被检索。

**去重 / 冲突 / 过期 / 版本**：
- 去重：`m add --id` 同 id 为 upsert；不带 id 每次新建。后台 `Memory Compaction`、`autoLabelConsolidation` 合并【命令】`/agent/knowledge-processing/status`。
- 冲突：EVOLVES 检测分 Replaces / Enriches / Confirms / Challenges【URL】advanced-features；矛盾交人。
- 过期：`deprecate`、`supersede`、`archive`、`forget`；`Decay Score Refresh` 每日；`autoHideLowRiskMemories: true`；`autoArchiveStaleMemories: false`。
- 版本：EVOLVES 链（`nmem graph evolves`）；**`memories update` 不保留正文历史**【文件】memory-health SKILL.md 第 105 行："keeps no content version history and the previous text survives nowhere in the store."
- 重要度上限：`agentMemoryImportanceCap: 0.8`【命令】status 端点。

**label 与 entity 如何形成**：label 由保存时模型一次性给出，之后不再复查；本机过滤 `--label mmw` 搜"verifier 修环境"只返回 2 条，印证 label 召回不全。label-backfill 技能称"there is no label vocabulary setting … `/memories/distill` takes no vocabulary"【文件】第 100 行。entity 由 KG 抽取（置信阈值 0.7）。

---

## 4. spaces、agents、远程与团队

- **retrieval mode**【文件】`~/.claude/plugins/marketplaces/nowledge-community/shared/behavioral-guidance.md` §4："`strict` means "search only here"; `shared` means "search here, then the listed shared spaces"; `all` means "search across everything"; `instructions` means "adjust how this lane searches and explains," not "store somewhere else"." 并且 "Shared or cross-space recall should be explicit, not automatic."
- **space 边界**：CLI `--space` "follows that Space's normal strict/shared/all retrieval policy, and it does not bypass Space boundaries"【URL】docs/cli（经搜索摘要）。每个 space 有自己的 Working Memory 与 Feed 视图（0.10.76："Feed, Tree, and Files now keep reads tied to the Space you selected."）。
- **agent identity 让不同 agent 读到不同内容的方式**：只有两处不同——agent 级 rules 和默认 space。memory 检索本身不按 agent 过滤。行为指南："if every child gets the same value, all agents will collapse into one profile"；需要变体时"fork it into a new slug"【文件】behavioral-guidance.md §1。
- **编排器用法**（与 MMW 同构）："For orchestration tools that spawn another AI CLI, keep `--source-app` as the child runtime … `NMEM_AGENT_ID` selects a Nowledge AI Identity directly. Add `NMEM_SPACE` only when the whole child process should override that identity's default space."【文件】behavioral-guidance.md §1。
- **Access Anywhere**：hub 模式，"one Nowledge Mem instance is the single source of truth"；不支持 "offline-first multi-master sync between separate databases"【URL】docs/sync。"API key is required for every remote request"；"Access Anywhere management APIs are local-only"；远程模式下会话采集仍在客户端机器上解析："remote mode does **not** mean the Mem server reads those agent session files remotely."【URL】docs/remote-access。**没找到只读 key 或按 space 限权的 key**。本机 `config access show`：LAN 关闭，仅 127.0.0.1。
- **Team workspace**：Nowledge Cloud 托管，"signed, attributed, with audit"【URL】mem.nowledge.co 首页摘要；`--contribute` 把个人 memory 单向复制进团队；本机 team 关闭。按 space 的成员权限模型：未找到。

---

## 5. 可编程性

- REST：`GET http://127.0.0.1:14242/openapi.json` 返回 286 条路径，API 版本 `0.9.15`【命令】。关键端点：`POST /memories`、`POST /memories/search`、`GET /context/bundle`、`GET /resources/resolve`、`GET /fs/*`、`POST /threads`、`POST /threads/{id}/append`、`GET /agent/feed/events`、`GET /events/stream`（SSE："Emits data-change, progress, and stage events as they occur."）、`GET /agent/trigger/{task_type}/context-plan`。
- MCP：`http://127.0.0.1:14242/mcp`，工具名（社区仓库出现频次最高的）：`memory_search`、`memory_add`、`memory_update`、`thread_search`、`read_working_memory`、`read_context_bundle`、`mem_fs`、`find_skills`、`report_skill_outcome`【命令】对 `~/.claude/plugins/marketplaces/nowledge-community` 的 grep。`X-Nmem-Agent-Id`、`X-Nmem-Space-Id` 头可带身份与 space【命令】`nmem config mcp show --host claude-code`。
- CLI：全局 `--json`；错误走 stderr。离线时 `nmem` 立即报 "Connection refused"【命令】`NMEM_API_URL=http://127.0.0.1:9 nmem --json memories search x`；插件钩子都以 `|| true` 吞掉失败。
- **MMW 的 python 脚本可以直接用标准库 `urllib` 调 REST**（本机无鉴权；远程加 API key）。
- 并发写：`m add --id` 为最后写入者胜；`fs write --record-version` 与 `t append --idempotency-key/--expected-message-count` 提供乐观并发与幂等；`memories update` 无版本检查。server 内部如何串行化：**未找到**（server 闭源，`gh api repos/nowledge-co/nowledge-mem/contents` 只有 `README.md`、`refs`）。

---

## 6. 官方文档与源码

读过的：
- https://mem.nowledge.co/docs （目录）
- https://mem.nowledge.co/docs/sync
- https://mem.nowledge.co/docs/remote-access
- https://mem.nowledge.co/docs/integrations/raft （多命名 agent）
- https://mem.nowledge.co/docs/advanced-features
- https://mem.nowledge.co/docs/api
- https://mem.nowledge.co/changelog
- GitHub：`nowledge-co/community`（172 stars，2026-09-11 推送，本机克隆于 `~/.claude/plugins/marketplaces/nowledge-community`，commit `f04bc1b9`）；`nowledge-co/nowledge-mem`（276 stars，仅 README，server 非开源）。
- 本机读过的实现文件：Claude Code 插件 `nmem-hook-read.sh`、`nmem-hook-subagent.py`、`nmem-hook-save.py`（全文）；Codex 插件 `nmem-context.py`（全文）；Cursor 插件 `session-start.mjs`（前 80 行）、README 相关段；Pi 扩展 `nowledge-mem.ts`（grep 定位，未全文读）；`shared/behavioral-guidance.md`（全文）；`label-backfill`、`memory-health` 两个 SKILL.md（全文）。

注意：`label-backfill` 与 `memory-health` **不在 MMW 仓库里**，是 Nowledge Mem 编译的 managed skill，位于 `~/ai-now/skills-active/`，经软链进入 `~/.claude/skills`、`~/.agents/skills`。MMW 仓库对 Nowledge Mem 的唯一接触点是 `mmw-v2/install.sh` 第 1619–1698 行写 `~/.cursor/mcp.json`；仓库里没有任何 `NMEM_AGENT_ID` / `NMEM_SPACE`（grep `NMEM_` 只命中 install.sh 自己的变量 `MMW_NMEM_MCP`）。

---

## 7. 局限与风险

| 风险 | 事实 | 对 MMW 的后果 |
| --- | --- | --- |
| 本机单点 | 默认 `127.0.0.1:14242`，hub 模式无多主同步 | 云端或其他机器的 worker 要读，必须开 Access Anywhere + 分发全权 API key；关机或 app 退出时全部 agent 失去记忆 |
| 失败静默 | 各插件钩子失败时 `|| true` 或 fail open；只有 Pi 会注入一行 "unavailable" | 违反 ADR 0008 精神："读不到"与"没有相关经验"看起来一样。MMW 若依赖它，必须自己判断并明说 |
| 蒸馏延迟与不确定 | `nmem tasks`：蒸馏任务排队"47m ago"仍在 Queued；抽取内容由模型决定 | 同一夜内 worker A 学到的东西，worker B 靠自动蒸馏读不到；必须显式写 |
| 检索召回不稳 | label 召回差（`--label mmw` 只 2 条）；社区聚类一个 topic 占 2806 条；`ask` 130 s | 自动注入只能用"语义搜索 + 少量硬过滤"，结果是提示，不能保证完整 |
| 隐私与串味 | 单一 Default space；Working Memory 同时含 MMW 与客户产品（监控产品）的决策 | 任何仓库的任何 worker 开局都会读到别的产品的上下文；若 worker 跑在第三方模型 host 上，这些内容也随 prompt 发出去 |
| 提示注入 | memory 从会话记录蒸馏，而会话记录包含 issue 正文、网页、工具输出；普通写入无审阅 | 一条被污染的 memory 会被注入后续所有 agent；有 `trust_warnings`、`claim_status`、`source_grounding` 字段可用于过滤，但注入钩子不看这些字段 |
| 过期知识 | Working Memory 每日 5:00 才重生成；`update` 不留历史；矛盾要人批 | 夜里注入的是昨天的简报；一条被修正前的旧结论可能仍在检索前列 |
| host 差异 | Grok 不自动注入；Claude Code 无 MCP；Cursor 的 MCP 不带身份头；子 agent 默认名单 Claude 与 Codex 不同 | MMW "技能对所有 host 同一份文本"要求能力对等；只能用"脚本在派发时拼进 prompt"这种不依赖 host 钩子的方式补齐 |
| 与 ADR 0001 冲突 | memory 会复述票状态、决策结论（本机 rules 草稿里已有"关票门只认派发注入标记"一类条目） | 若 agent 把 memory 当依据，就有第三份无人维护的副本；票正文不改而 memory 可能被 EVOLVES 合并改写 |
| 与 ADR 0019 / 0017 | memory 由模型打字；后台有定时任务 | 不能承载事件与唤醒；只能在 agent 被事件唤醒后作为读物 |
| 版本漂移 | 本机 0.10.78，线上 0.10.81；插件 0.7.24 / 0.1.32 各自升级 | 路径、字段、行为可能变；MMW 脚本应只依赖 openapi 中稳定端点并在 `install.sh --check` 里探测 |

---

## 8. Nowledge Mem 能力 × MMW 四层 context 映射表

先定两个前提（都是需要用户拍板的产品决定，见 §10）：

- **P1 身份**：`install.sh` 登记四个身份 `mmw-main`、`mmw-worker`、`mmw-reviewer`、`mmw-verifier`，各自带 agent 级 active rules；`dispatch.sh start` 与起 reviewer/verifier 的命令给子进程设 `NMEM_AGENT_ID`。这一步与 host 无关，环境变量对五个 host 都成立（Claude Code/Codex/Cursor 钩子与 MCP 头都读它；Grok/Pi 的 CLI 读它）。
- **P2 space**：启用 spaces；每个消费仓库一个 space（名字取 `statedir.py` 已有的 `<owner>__<name>`），另建一个 `mmw-toolbox` space 放流水线本身的经验，仓库 space 设 `shared` 并链到 `mmw-toolbox`；`dispatch.sh` 给子进程设 `NMEM_SPACE`。用户自己的日常会话仍落 Default。

| 层 | 要传什么 | 谁写 | 谁读 | 何时读 | 用 Nowledge Mem 哪个机制 | MMW 这边要加什么 | 风险 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 跨 agent（同一夜，worker / reviewer / verifier / main） | 操作性知识：怎么起产品、哪个测试不稳、环境坑与修法、verifier 修环境的办法 | 当事 agent 在关键节点显式写（不是等蒸馏）；最好由脚本在 `--decisions`、`--closeout`、`verdict` 这些已有步骤里提示并代为提交 | 同 spec 与同仓库后续起跑的 worker、reviewer、verifier | 被事件唤醒之后、开工前一次（`--preflight`、reviewer 启动、verifier 启动）；不轮询 | `POST /memories`：`unit_type procedure/learning`、`space_id` 仓库 space、`metadata {repo, spec, ticket, commit, night}`、`agent_id`；读用 `POST /memories/search` 带 `metadata_filters repo=` + `recorded_date_from` | 一个小脚本（放在 dispatch 或 verify-ticket 的 `scripts/`）：写入固定 metadata；`--preflight` 时按"票标题 + Owns 文件名"查询，取前 N 条拼进 worker prompt，读不到时在 prompt 里明说"经验库不可达"；`install.sh --check` 探测 server | 召回不全；延迟 0.5 s 可接受；错误经验会扩散到整夜，需带 `commit` 让读者判断是否过期；普通写入无审阅 |
| 跨 spec（并行开夜） | "别的 spec 正在碰哪些区域"的风险提示；某 spec 当夜发现的全仓库级环境坑 | 同上 | 另一 spec 的 main agent 与 worker | `open <spec>` 时、worker `--preflight` 时 | 同仓库 space 内按 `metadata.night` 检索 | 同上；**Owns 重叠检查本身不放这里**（见 §9） | 语义检索无法保证"两个 spec 改同一文件"被发现；只能是补充提示 |
| 跨任务（跨夜、跨 map） | bounce / regressed 的原因模式、triage 结论、反复出现的评审发现、技能被证明不好用的地方 | 自动：会话采集 + 蒸馏（已在跑）；显式：main agent 在 `summary` 后、triage 后写一条 `event`/`learning` | 下一夜的 main agent（`open` 前）、`to-tickets` / `to-spec` 的作者、改进技能的人 | 开夜前、写 spec 与切票时 | Working Memory 每日简报（5:00 生成，可按 space）；`memories search --time week --unit-type learning`；Feed 矛盾审阅；`guidance_rule_review` 与 skill curator 产出的 draft rules / candidate skills | `night.md` 的开夜步骤加一步"读仓库 space 的 Working Memory 与近 7 天 learning"；把 draft rules 转 active 设为用户审阅环节，而不是自动 | 蒸馏质量由模型决定；草稿规则可能固化错误结论；与"技能是交付物"的仓库规则冲突——改技能必须仍走票 |
| 跨仓库（多个消费仓库与 MMW 自身） | 流水线级经验（runner、host、hook、安装坑）与产品无关的工程经验 | MMW 自身仓库的会话；各仓库会话中标为流水线问题的 fault / finding | 所有仓库的 main agent 与 worker | 同上 | `mmw-toolbox` space + 仓库 space 的 `shared` 检索模式；space `instructions` 说明检索口径 | `install.sh` 建 space 与身份（需用户同意）；`dispatch.sh` 按仓库设 `NMEM_SPACE` | 启用 spaces 后 Default 里 1847 条旧 memory 不会自动迁移，`strict` 下仓库 space 起初是空的；`shared` 若链到 Default 就把客户产品上下文重新混进来 |

补一条读取侧的完整性做法：因为 Context Bundle 不含检索结果，而 Grok 不注入、Cursor CLI 钩子未验证，**"读"要做到完整且对所有 host 一致，唯一可靠的位置是 MMW 自己拼 prompt 的地方**（`dispatch.sh start` 与起 reviewer/verifier 的命令）：脚本调 `GET /context/bundle?agent_id=…&space_id=…&include_working_memory=false` + 一次 `POST /memories/search`，把结果与"来源、commit、记录日期、trust_warnings"一起写进 prompt 的固定小节，失败时写明失败。host 钩子注入的那份作为重复的补充，可以关掉（`NMEM_SUBAGENT_CONTEXT_TYPES=` 等）以免 Working Memory 串味。

---

## 9. 它不该承担什么

| 内容 | 留在哪里 | 理由 |
| --- | --- | --- |
| 票状态、认领、frontier、依赖、blocking link、父子关系 | GitHub tracker 与 `<!-- mmw -->` 事件块 | ADR 0001、0019：只有脚本写的事件算数；memory 由模型打字、可被后台合并改写，无法 fold |
| 唤醒与 agent 间通知 | relay | ADR 0010、0020–0022：靠事件唤醒、要求 ack；Nowledge Mem 没有送达保证，SSE 流不是 ack 语义 |
| `## Owns` 重叠检查（含跨 spec） | 发布与 `open` 时的脚本检查 | 需要确定性的集合运算；语义检索会漏，漏了就是 bounce（#748、#750、#751） |
| 验收标准、`CHECK:`、VERDICT、NIGHT SUMMARY | 票正文与评论 | ADR 0008：闸口必须点名事实；记忆检索结果不能当证据 |
| spec、ADR、CONTEXT.md、screen contract、技能文本 | 仓库文件 | 有版本、有 diff、有评审；memory `update` 不留历史；技能改动必须走票 |
| 决策结论（decision 子票的结论） | 结论评论 | ADR 0001 Consequences：决策只存在于结论评论；memory 可做索引，但检索到后要回到评论核对 |
| 凭证、客户数据 | 不进任何共享层 | 全权 API key、无 space 级权限；Working Memory 会注入所有会话 |

Nowledge Mem 适合承担的是这些权威来源**之外**的东西：没人会写进票、但下一个 agent 很需要的"怎么做、踩过什么坑、上次为什么失败"。它对 MMW 的正确定位是"团队里口口相传的经验"，而不是"团队的账本"。

---

## 10. 需要用户决定的事（调研不替用户做）

1. 是否启用 spaces。这会改变用户个人记忆的组织方式：Feed、Working Memory、Tree 都按 space 分开，已有 memory 不自动迁移（`spaces enable` 与 `memories move` 都是写操作，本次未执行）。
2. 是否把 51 条 draft rules 中与 MMW 相关的转为 agent 级 active rules，交给哪个身份。
3. 是否接受 worker 会话继续自动写入个人记忆库（现状已经在写），还是给夜里的子进程关掉采集、只保留脚本显式写入。
4. 云端或其他机器上的 worker 是否允许持有全权 API key。

## Sources

- [Nowledge Mem Docs](https://mem.nowledge.co/docs)
- [Sync Across Devices](https://mem.nowledge.co/docs/sync)
- [Access Mem Anywhere](https://mem.nowledge.co/docs/remote-access)
- [Raft × Nowledge Mem](https://mem.nowledge.co/docs/integrations/raft)
- [Advanced Features](https://mem.nowledge.co/docs/advanced-features)
- [API Reference](https://mem.nowledge.co/docs/api)
- [Changelog](https://mem.nowledge.co/changelog)
- [Nowledge Mem CLI](https://mem.nowledge.co/docs/cli)
- [nowledge-co/community](https://github.com/nowledge-co/community)
- [nowledge-co/nowledge-mem](https://github.com/nowledge-co/nowledge-mem)

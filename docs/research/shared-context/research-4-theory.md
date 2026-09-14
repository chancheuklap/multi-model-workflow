# 跨 agent 共享上下文：原则、失败模式与"谁写谁读"建议（调研 4：理论与一线经验）

调研日期：2026-09-13。对象：多 agent 落地流水线（spec → 票 → 夜间派 worker → reviewer/verifier → 合并关票）想借鉴 Cursor Projects 的 shared Project Context。
所有引语为英文原文短摘，出处 URL 在同一行。"推断"字样标出不是原文直接陈述、由本调研推出的内容。

---

## 0. 先校正一个前提：Cursor 官方到底说了什么

用户背景里写的"coordinator 独写 notes.md"不是 Cursor 官方说法，是一位用户（arslan.io）自己的做法。

- Cursor 官方博客（2026-09-10）只说 agent 们都往共享文件里加东西："Agents add research and artifacts, along with what they learn about the codebase and how you prefer work to be done. If one agent figures out how to test a service, for example, every future agent can use those instructions." — https://cursor.com/blog/projects
- 官方博客没有写 notes.md 这个文件名，没有写谁有写权限、怎么解决冲突、怎么淘汰陈旧条目。Cursor 文档页 `cursor.com/docs/projects` 抓取只得到空壳，`cursor.com/docs/agent/projects` 返回 404：**Projects 的官方文档未找到**。
- "只让 coordinator 写 notes.md"出自 arslan.io 的个人实践："A notes.md file. This is your README.md of your Project. But it's dynamic. You can edit it as well if you like, but I let only the coordinator write to it." — https://arslan.io/2026/09/11/how-i-manage-my-agents/
  同文还写：User Context 里的 preferences.md "is like AGENTS.md, but it's not passed down to agents. The coordinator reads it at the start of every turn, and agents do not get it."；多个 coordinator 之间不能互读 Context，改用 git 仓库里的 inbox 文件，"Every file there starts with four lines: From, To, Date, and Why"，"Projects do not write into each other's files, they ask the Hub"。
- 同一公司更早的研究（2026-01-14）恰好记录了"平等 agent 共写一个协调文件"的失败，见 B.4。

所以"单写者"是一个值得采用的设计，但它的依据应当来自下文 Cognition 与 Cursor 研究文章，而不是 Cursor Projects 产品本身。

---

## A. 原则清单

格式：原则｜解决的问题｜前提假设｜失效场景｜来源 URL + 引语

### A1. 状态写外部文件，不靠上下文窗口或摘要延续
- **解决的问题**：每个新会话（或 context reset 后）没有记忆；compaction 摘要会丢关键细节。
- **前提**：agent 能被提示在开始时读、结束时写；文件内容本身是准确的。
- **失效场景**：agent 在上下文用尽时写到一半，下一个会话"猜"发生了什么；进度文件写"完成"但功能没端到端验证过（见 A9）。
- **来源**：
  - Anthropic, Effective harnesses for long-running agents（2025-11-26）："each new session begins with no memory of what came before. Imagine a software project staffed by engineers working in shifts" ；"The key insight here was finding a way for agents to quickly understand the state of work when starting with a fresh context window, which is accomplished with the claude-progress.txt file alongside the git history." — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - 同文："This happens even with compaction, which doesn't always pass perfectly clear instructions to the next agent."
  - Anthropic, Effective context engineering（2025-09-29）："Structured note-taking, or agentic memory, is a technique where the agent regularly writes notes persisted to memory outside of the context window." — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - Anthropic memory tool 文档（系统提示自动注入）："ASSUME INTERRUPTION: Your context window might be reset at any moment, so you risk losing any progress that is not recorded in your memory directory." — https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool

### A2. 仓库（版本化文件）是唯一事实来源；agent 看不到的等于不存在
- **解决的问题**：知识散落在聊天、Slack、人脑里，冷启动的 agent 拿不到。
- **前提**：知识能写成文字并放进仓库；有人（或 agent）持续维护它。
- **失效场景**：文件没人维护就陈旧（A4）；把所有东西塞进一个大文件（A3）。
- **来源**：OpenAI, Harness engineering（2026-02-11，Ryan Lopopolo）："From the agent's point of view, anything it can't access in-context while running effectively doesn't exist. Knowledge that lives in Google Docs, chat threads, or people's heads are not accessible to the system."；"That Slack discussion that aligned the team on an architectural pattern? If it isn't discoverable to the agent, it's illegible in the same way it would be unknown to a new hire joining three months later." — https://openai.com/index/harness-engineering/ （openai.com 对抓取返回 403；全文经镜像 https://jaytaylor.com/notes/node/1770842156000.html 读取，与搜索引擎给出的原文摘录一致）

### A3. 入口文件是目录，不是百科；按需逐层加载（progressive disclosure）
- **解决的问题**：大指令文件挤占任务上下文；"全都重要"等于没有重点。
- **前提**：入口文件里的指针准确；agent 会顺着指针去读。
- **失效场景**：入口文件膨胀回百科；指针指向已删除/改名的文件。
- **来源**：
  - OpenAI Harness engineering："We tried the 'one big AGENTS.md' approach. It failed in predictable ways"；"Too much guidance becomes non-guidance. When everything is 'important,' nothing is."；"instead of treating AGENTS.md as the encyclopedia, we treat it as the table of contents."；"A short AGENTS.md (roughly 100 lines) is injected into context and serves primarily as a map, with pointers to deeper sources of truth elsewhere."
  - Anthropic context engineering："maintain lightweight identifiers (file paths, stored queries, web links, etc.) and use these references to dynamically load data into context at runtime"；"good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome."
  - 实证支撑见 A11（AGENTS.md 论文）。

### A4. 共享知识必须有机械校验和定期清理（gardening）
- **解决的问题**：文档陈旧后 agent 分不清哪条还成立。
- **前提**：能写出校验规则（链接、覆盖、新鲜度、归属），或有 agent 定期对照代码核查。
- **失效场景**：没有校验时 "drift is inevitable"；清理 agent 自身判断错（推断：需要人抽查其 PR）。
- **来源**：
  - OpenAI："It rots instantly. A monolithic manual turns into a graveyard of stale rules. Agents can't tell what's still true, humans stop maintaining it, and the file quietly becomes an attractive nuisance."；"It's hard to verify. A single blob doesn't lend itself to mechanical checks (coverage, freshness, ownership, cross-links), so drift is inevitable."；"Dedicated linters and CI jobs validate that the knowledge base is up to date, cross-linked, and structured correctly. A recurring 'doc-gardening' agent scans for stale or obsolete documentation that does not reflect the real code behavior and opens fix-up pull requests."
  - OpenAI 同文，把规则升级为代码："When documentation falls short, we promote the rule into code"；custom lint "we write the error messages to inject remediation instructions into agent context."
  - Cursor Projects："adds a lint rule whenever it sees the same mistake twice." — https://cursor.com/blog/projects
  - Anthropic memory tool 文档："Memory expiration: Periodically delete memory files that haven't been accessed in a long time."

### A5. 写操作单线程（一个写者），其他 agent 贡献"智能"而非"动作"
- **解决的问题**：并行写者各自做出隐含决策（风格、边界情况、代码模式），决策互相冲突。
- **前提**：可以把工作划成"只读分析/评审"与"写"两类；写者有足够上下文来吸收其他 agent 的意见。
- **失效场景**：写者吸收不了评审结果（循环、越权、超范围）；子任务确实需要并行写时（需按文件/任务隔离，见 A6）。
- **来源**：
  - Cognition, Don't Build Multi-Agents（2025-06-12，Walden Yan）："Principle 1: Share context, and share full agent traces, not just individual messages"；"Principle 2: Actions carry implicit decisions, and conflicting decisions carry bad results" — https://cognition.ai/blog/dont-build-multi-agents
  - Cognition, Multi-Agents: What's Actually Working（2026-04-22）："Our original observations still hold today for parallel-writer swarms"；"multi-agent systems work best today when writes stay single-threaded and the additional agents contribute intelligence rather than actions." — https://cognition.ai/blog/multi-agents-working
  - LangChain, How and when to build multi-agent systems（2025-06-16）："read actions are inherently more parallelizable than write actions."；"The actual writing—synthesizing findings into a coherent report—is deliberately handled by a single main agent in one unified call." — https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems
  - Anthropic 多 agent 研究系统（2025-06-13）："some domains that require all agents to share the same context or involve many dependencies between agents are not a good fit for multi-agent systems today. For instance, most coding tasks involve fewer truly parallelizable tasks than research" — https://www.anthropic.com/engineering/multi-agent-research-system

### A6. 并行写者按所有权切分（文件/任务），并用确定性机制认领
- **解决的问题**：两个 agent 改同一处互相覆盖；重复劳动。
- **前提**：任务能切成相互独立的块；有外部仲裁（git push 冲突、锁文件、乐观并发）。
- **失效场景**：任务本质上是一个大块（所有 agent 撞同一个 bug）；锁由 LLM 自觉维护时会忘记释放。
- **来源**：
  - Claude Code agent teams 文档："Two teammates editing the same file leads to overwrites. Break the work so each teammate owns a different set of files." — https://code.claude.com/docs/en/agent-teams
  - Anthropic, Building a C compiler with a team of parallel Claudes（2026-02-05，Nicholas Carlini）："Claude takes a 'lock' on a task by writing a text file to current_tasks/ ... If two agents try to claim the same task, git's synchronization forces the second agent to pick a different one."；失败："compiling the Linux kernel is one giant task. Every agent would hit the same bug, fix that bug, and then overwrite each other's changes." — https://www.anthropic.com/engineering/building-c-compiler
  - Cursor, Scaling long-running autonomous coding（2026-01-14）：乐观并发 "was simpler and more robust" 但 "there were still deeper problems"（见 B.4）。 — https://cursor.com/blog/scaling-agents

### A7. 角色分层：planner 建任务、worker 只做自己的任务、judge 决定是否继续；每轮重新开始
- **解决的问题**：扁平结构下 agent 风险规避、无人对困难任务负责；长期运行漂移。
- **前提**：planner 有足够全局视野；worker 的任务描述足够完整。
- **失效场景**：结构过多变脆；集成者角色成为瓶颈。
- **来源**：Cursor scaling-agents："Workers pick up tasks and focus entirely on completing them. They don't coordinate with other workers or worry about the big picture."；"At the end of each cycle, a judge agent determined whether to continue, then the next iteration would start fresh."；"We initially built an integrator role for quality control and conflict resolution, but found it created more bottlenecks than it solved."；"The right amount of structure is somewhere in the middle. Too little structure and agents conflict, duplicate work, and drift. Too much structure creates fragility."；"We still need periodic fresh starts to combat drift and tunnel vision."

### A8. 交接内容要显式、结构化；worker 冷启动时需要 objective、输出格式、边界
- **解决的问题**：简短委派让子 agent 误解任务、重复工作；自然语言多跳传递像传话游戏一样失真。
- **前提**：委派者知道接收者缺什么信息。
- **失效场景**：委派者以为双方共享状态（其实没有）；manager 缺代码库细节却过度规定实现。
- **来源**：
  - Anthropic 研究系统："Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries. Without detailed task descriptions, agents duplicate work, leave gaps, or fail to find necessary information."
  - MetaGPT（ICLR 2024）："in the telephone game ... after several rounds of communication, the original information may be quite distorted."；"agents in MetaGPT communicate through documents and diagrams (structured outputs) rather than dialogue." — https://arxiv.org/abs/2308.00352
  - Cognition 2026："Managers trained on small-scoped delegation default to being overly prescriptive, which backfires when the manager lacks deep codebase context. Agents assume they share state with their children when they don't. Cross-agent communication ... doesn't happen by default"
  - Claude Code agent teams："Teammates load project context automatically, including CLAUDE.md, MCP servers, and skills, but they don't inherit the lead's conversation history."
  - Anthropic planner/generator/evaluator（2026-03-24）：planner 只写产品层 spec，"if the planner tried to specify granular technical details upfront and got something wrong, the errors in the spec would cascade into the downstream implementation." — https://www.anthropic.com/engineering/harness-design-long-running-apps

### A9. 大产物走文件系统，只回传引用（避免 coordinator 转述）
- **解决的问题**：经 coordinator 中转会丢信息、耗 token。
- **前提**：产物有稳定路径；接收方有权限读。
- **失效场景**：引用失效（文件被覆盖/移动）；接收方不去读。
- **来源**：Anthropic 研究系统附录："Subagent output to a filesystem to minimize the 'game of telephone.'"；"Subagents call tools to store their work in external systems, then pass lightweight references back to the coordinator. This prevents information loss during multi-stage processing"；Anthropic harness-design："Communication was handled via files: one agent would write a file, another agent would read it and respond either within that file or with a new file"

### A10. 压缩要可恢复；不可逆的摘要有风险
- **解决的问题**：无法预知哪条观察在十步后变关键。
- **前提**：原始数据保存在可按路径/URL/事件序号取回的地方。
- **失效场景**：只存摘要不存原件。
- **来源**：
  - Manus（2025-07-18，Yichao 'Peak' Ji）："you can't reliably predict which observation might become critical ten steps later. From a logical standpoint, any irreversible compression carries risk."；"Our compression strategies are always designed to be restorable." — https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
  - Anthropic Managed Agents（2026-04-08）："irreversible decisions to selectively retain or discard context can lead to failures. It is difficult to know which tokens the future turns will need."；session log 作为 "a context object that lives outside Claude's context window" — https://www.anthropic.com/engineering/managed-agents
  - Anthropic context engineering："overly aggressive compaction can result in the loss of subtle but critical context whose importance only becomes apparent later."

### A11. 共享的规则文件只写"最少必要要求"和代码里查不到的东西
- **解决的问题**：冗余/泛泛的上下文文件让任务更难、更贵。
- **前提**：能分辨"仓库里已能发现的信息"和"只有人知道的信息"。
- **失效场景**：LLM 自动生成的上下文文件（大量 overview、目录列举）；仓库本身文档很少时，自动生成反而有用。
- **来源**：
  - Gloaguen et al., Evaluating AGENTS.md（arXiv 2602.11988，2026-02-12，ETH Zurich / LogicStar）："context files tend to reduce task success rates compared to providing no repository context, while also increasing inference cost by over 20%"；"unnecessary requirements from context files make tasks harder, and human-written context files should describe only minimal requirements."；"LLM-generated context files cause performance drops in 5 out of 8 settings"；"developer-provided context files outperform the LLM-generated ones for all four agents ... and improve the performance compared to no context files for all agents but Claude Code"；"context files, even developer-provided ones, are not effective at providing a repository overview"；"agents generally follow instructions present in the context files"（所以没提升不是因为不遵守）；"stronger models do not necessarily generate superior context files." — https://arxiv.org/abs/2602.11988
  - 同文，删除仓库全部文档后 "LLM-generated context files not only consistently improve performance by 2.7% on average, but also outperform developer-written documentation." —— 说明价值在于提供仓库里没有的信息。
  - Lulla et al., On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents（arXiv 2601.20404，v2 2026-03-30，ICSE JAWs 2026）：10 个仓库 124 个 PR，"the presence of AGENTS.md is associated with a lower median runtime (Δ28.64%) and reduced output token consumption (Δ16.58%), while maintaining a comparable task completion behavior." — https://arxiv.org/abs/2601.20404 （只读了摘要）
  - 两篇结论方向不同（一篇成本升 20%+，一篇运行时间降 28.6%）。**推断**：差别可能来自文件内容（人写 vs LLM 生成）、任务来源和测量指标不同；两篇都不支持"文件越全越好"。

### A12. 增量追加条目，不做整体重写（防 context collapse / brevity bias）
- **解决的问题**：让 LLM 反复整体重写共享笔记，会把积累的细节压成空话。
- **前提**：知识能拆成独立条目（带 id、有用/有害计数）；合并由确定性代码完成。
- **失效场景**：没有可靠反馈信号时，条目被错误信号污染；Reflector 太弱时笔记变噪声。
- **来源**：ACE, Agentic Context Engineering（arXiv 2510.04618 v3，2026-03-29）："brevity bias, which drops domain insights for concise summaries, and from context collapse, where iterative rewriting erodes details over time."；实测："at step 60 the context contained 18,282 tokens and achieved an accuracy of 66.7, but at the very next step it collapsed to just 122 tokens, with accuracy dropping to 57.1—worse than the baseline accuracy of 63.7"；做法："represent context as a collection of structured, itemized bullets"，"merged deterministically into the existing context by lightweight, non-LLM logic. Because updates are itemized and localized, multiple deltas can be merged in parallel"；局限："in the absence of reliable feedback signals (e.g., ground-truth labels or execution outcomes), both ACE and other adaptive methods such as Dynamic Cheatsheet may degrade" — https://arxiv.org/abs/2510.04618
  - Dynamic Cheatsheet（arXiv 2504.07952）："DC's memory is self-curated, focusing on concise, transferable snippets rather than entire transcript." — https://arxiv.org/abs/2504.07952 （只读了摘要）

### A13. 按角色订阅，而不是全员广播
- **解决的问题**：共享池里什么都给每个 agent，造成信息过载。
- **前提**：角色的信息需求可预先定义。
- **失效场景**：订阅规则漏掉了某角色真正需要的信息（对应 MAST FM-2.4）。
- **来源**：MetaGPT："Sharing all information with every agent can lead to information overload."；"agents utilize role-specific interests to extract relevant information ... an agent activates its action only after receiving all its prerequisite dependencies." 黑板系统 LbMAS 用 "a public space and private spaces" 区分 — https://arxiv.org/abs/2507.01701

### A14. 验证者用干净上下文；执行者（worker）继承上下文
- **解决的问题**：评审者被执行者的推理锚定；长上下文让评审变笨（context rot）。
- **前提**：评审材料（diff、验收标准）能独立成包。
- **失效场景**：执行者不会用自己更完整的上下文过滤评审意见，导致循环或违背用户指令。
- **来源**：
  - Cognition 2026："we found this technique to work best when the coding and review agents do not share any context beforehand."；"The dedicated review agent gets to skip this extraneous context, only look at the diff, and re-discover any context it needs"；"does Devin properly use its broader context of user instructions, decisions, etc. to filter the bugs that come back from Devin Review? This is key to preventing looping, disobeying the user, doing work that is out of scope"
  - LangChain, Organizing Context in a Multi-Agent Harness（2026-09-08）："A verifier reviews another agent's work ... inheriting the supervisor's reasoning can be counterproductive. The verifier should evaluate the work itself rather than being anchored by the supervisor's diagnosis or expectations."；worker 用 fork："Starting the worker in isolation would force it to rediscover its evidence." — https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness
  - 同文的 memory agent 做法：fork 完整对话、但写权限用路径规则限制（示例中 write 对 `/**` deny，read 只允许 `/AGENTS.md` 与 `/docs/**`）。**注意**：示例代码本身写权限全部拒绝，文章没说明允许写到哪里；这是它的示例，不是完整方案。
  - Anthropic harness-design："tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"

### A15. 用中间结果"复述目标"对抗长程漂移
- **解决的问题**：长循环里忘了原目标（lost-in-the-middle）。
- **前提**：计划文件被频繁改写到上下文末尾。
- **失效场景**：计划文件本身被写错（context poisoning，见 B）。
- **来源**：Manus："By constantly rewriting the todo list, Manus is reciting its objectives into the end of the context."；LangChain Deep Agents："Claude Code uses a Todo list tool. Funnily enough - this doesn't do anything! It's basically a no-op." — https://blog.langchain.com/deep-agents/

### A16. 保留失败记录
- **解决的问题**：清掉错误后模型重复同样的错。
- **前提**：失败记录是真实的执行结果，不是幻觉。
- **失效场景**（推断）：跨 agent 共享时，一个 agent 的错误结论被当作事实传给别人（B.7）。
- **来源**：Manus："Erasing failure removes evidence. And without evidence, the model can't adapt."；C 编译器文章："When stuck on a bug, Claude will often maintain a running doc of failed approaches and remaining tasks."

### A17. 每个脚手架组件都是对模型能力的假设，要随模型更新复查
- **解决的问题**：为旧模型加的机制（context reset、sprint）在新模型上变成负担。
- **前提**：有评估集能单独拆掉一个组件对比。
- **失效场景**：一次拆太多，分不清哪个组件真在起作用。
- **来源**：Anthropic harness-design："every component in a harness encodes an assumption about what the model can't do on its own, and those assumptions are worth stress testing"；"Opus 4.5 largely removed that behavior on its own, so I was able to drop context resets from this harness entirely."；Managed Agents："The resets had become dead weight."

---

## B. 常见失败模式

| # | 失败模式 | 表现 | 来源 |
|---|---|---|---|
| B.1 | Context rot（上下文变长能力下降） | 输入越长，召回与推理越不可靠，且下降不均匀 | Chroma（18 个模型）："performance grows increasingly unreliable as input length grows" — https://research.trychroma.com/context-rot ；Anthropic："as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases." ；Cognition 2026 解释评审需干净上下文的原因也是它 |
| B.2 | 摘要/压缩丢信息 | 交接文件或 compaction 漏掉后来才重要的细节；下一会话猜测前情 | Anthropic harnesses："leaving the next session to start with a feature half-implemented and undocumented. The agent would then have to guess at what had happened"；Manus "any irreversible compression carries risk"；Cognition 2025 需"fine-tuning a smaller model"做摘要："This is hard to get right." |
| B.3 | Context collapse / brevity bias | LLM 整体重写共享笔记，18,282 token 一步塌到 122 token，准确率跌破无笔记基线 | ACE（见 A12） |
| B.4 | 写冲突与锁失效 | 锁不释放、重复获取、不拿锁直接改协调文件；20 个 agent 吞吐量降到 2–3 个；同文件互相覆盖 | Cursor scaling-agents："Agents would hold locks for too long, or forget to release them entirely. Even when locking worked correctly, it became a bottleneck. Twenty agents would slow down to the effective throughput of two or three"；"update the coordination file without acquiring the lock at all."；Claude Code agent teams "leads to overwrites"；CodeCRDT 用 CRDT 实现零合并失败，但仍有 "semantic conflict rates (5-10%)"，且 "up to 39.4% slowdown on others" — https://arxiv.org/abs/2510.18893 |
| B.5 | 平等协作下的责任稀释 | 无层级时 agent 挑简单任务，工作长期空转 | Cursor："With no hierarchy, agents became risk-averse. They avoided difficult tasks and made small, safe changes instead. No agent took responsibility for hard problems" |
| B.6 | 陈旧（staleness） | 规则文件成为"stale rules"坟场；agent 分不清哪条还成立 | OpenAI（见 A4）。**推断**：共享 notes 里"测试怎么跑"这类知识在代码改动后最容易过期，而且没有测试会发现它过期 |
| B.7 | Context poisoning / 错误传播 | 一次幻觉写进目标或摘要，被反复引用，长时间才能纠正；共享后污染所有读者 | Drew Breunig（2025-06-22）引 Gemini 2.5 报告："many parts of the context (goals, summary) are 'poisoned' with misinformation about the game state, which can often take a very long time to undo." — https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html ；ACE：无可靠反馈时 "the constructed context can be polluted by spurious or misleading signals"；Anthropic 研究系统："minor changes cascade into large behavioral changes" |
| B.8 | Context clash（上下文自相矛盾） | 多来源信息互相冲突；多轮拆分信息后平均下降 39% | Breunig："Context Clash is when you accrue new information and tools in your context that conflicts with other information"；引 Microsoft/Salesforce："The sharded prompts yielded dramatically worse results, with an average drop of 39%." |
| B.9 | 膨胀（bloat） | 共享文件越写越大，挤占任务上下文；成本升 20%+，推理 token 升 14–22% | OpenAI "A giant instruction file crowds out the task"；AGENTS.md 论文（A11）；Anthropic memory tool 文档建议限制文件大小："Track memory file sizes and cap how large a file can grow." |
| B.10 | 过度模仿（few-shot 化） | 上下文里重复的模式被机械照搬；仓库里的次优写法被复制 | Manus："The more uniform your context, the more brittle your agent becomes."；OpenAI："Codex replicates patterns that already exist in the repository—even uneven or suboptimal ones. Over time, this inevitably leads to drift." |
| B.11 | 信息扣留 / 忽视他人输入 / 丢失历史（MAST） | FM-2.4 "Failure to share or communicate important data or insights that an agent possess"；FM-2.5 "Disregarding or failing to adequately consider input ... provided by other agents"；FM-1.4 "Loss of conversation history"；FM-2.1 "Conversation reset"；FM-2.4 等 "appear almost exclusively in failed runs" | Cemri et al., Why Do Multi-Agent LLM Systems Fail?（arXiv 2503.13657 v3，1600+ 条 trace、7 个框架）— https://arxiv.org/abs/2503.13657 ；原因分析："the collapse of 'theory of mind', where agents fail to accurately model other agents' informational needs."；"many MAS failures arise from the challenges in organizational design and agent coordination rather than the limitations of individual agents." |
| B.12 | 验证缺失或错误，错误状态被写进共享进度 | 未端到端测试就标"完成"；后续 agent 看到有进度就宣布整个项目完成；评审发现问题后自己说服自己放行 | Anthropic harnesses："a later agent instance would look around, see that progress had been made, and declare the job done."；"Claude's tendency to mark a feature as complete without proper testing"；harness-design："I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway."；MAST FM-3.2/3.3 在成功运行中也常见 |
| B.13 | 提示注入沿共享通道传播 | 恶意指令在 agent 之间自我复制；通过普通查询把恶意记录写进记忆库 | Prompt Infection（arXiv 2410.07283）："malicious prompts self-replicate across interconnected agents, behaving much like a computer virus"，"even when agents do not publicly share all communications" — https://arxiv.org/abs/2410.07283 ；MINJA（arXiv 2503.03704）："The attacker injects malicious records into the memory bank by only interacting with the agent via queries and output observations." — https://arxiv.org/abs/2503.03704 ；Managed Agents："a prompt injection only had to convince Claude to read its own environment"；memory tool 文档要求路径穿越防护 "/memories/../../secrets.env" |
| B.14 | 共享状态的错觉 | 管理者以为子 agent 知道自己知道的东西 | Cognition 2026 "Agents assume they share state with their children when they don't."；Anthropic context engineering 把 "falsely assumes shared context" 列为提示词失败的一端 |
| B.15 | 结构化文件被随意改写 | Markdown 进度/清单被 agent 删改测试项 | Anthropic harnesses："we landed on using JSON for this, as the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files."；只允许改 `passes` 字段 |
| B.16 | 痕迹无人能解读 | 环境痕迹若没有解读它的认知结构就无效 | Emergent Collective Memory（arXiv 2512.10166，网格仿真，非 LLM 编码任务）："environmental traces without memory fail completely. This demonstrates that memory functions independently but traces require cognitive infrastructure for interpretation." — https://arxiv.org/abs/2512.10166 。**推断**：对应到流水线，写进共享文件的条目需要读者知道它的格式和适用范围 |

关于 stigmergy（通过修改环境间接协调）：SwarmWorld（arXiv 2608.26081，2026-08-26）发现 "most reuse beginning through physical observation rather than communication"，共享社会的产物组合比 best-of-N 独立搜索"broader, more resilient"，但 "isolated search remains competitive for the strongest artifact" — https://arxiv.org/abs/2608.26081 （只读摘要；实验环境是模拟世界，不是代码库）。黑板系统两篇（2507.01701 数学/推理题；2510.01285 数据湖检索，报告较 master–slave 基线相对提升 13%–57%）都不是编码流水线，结论迁移到本场景属**推断**。

---

## C. 结论性建议：谁写、谁读、何时写、写什么

总体取向（综合 A5/A7/A11/A12/A14）：**共享文件只放"代码与票里查不到、且被多个未来会话需要"的信息；写入口单一或按条目增量合并；读者按角色拿子集；验证者不读执行者的推理。**

### C.1 共享事实型知识（测试怎么跑、服务在哪配置、环境坑）
- **谁写**：worker 可以**提出**条目（发现即记录，否则知识随会话消失，A1）；**合并**由单一写者完成——coordinator 或一个确定性脚本（A5、A12；Cursor 研究里平等共写协调文件失败，B.4）。条目格式固定（id、内容、证据来源如命令与退出码、日期、验证状态），合并用代码追加/去重，不让 LLM 整体重写（ACE）。
- **谁读**：每个 worker 冷启动时读；reviewer/verifier 只读与"如何运行/验证"相关的部分，不读 worker 的推理（A14）。
- **何时写**：worker 结束时（与进度一起提交）；coordinator 在合并/关票时审核后并入。
- **写什么**：只写仓库里 grep 不到、或需要试错才知道的东西（A11 论文：冗余 overview 无效且增本）。能变成脚本或 lint 的，升级成脚本或 lint，笔记里只留一行指针（OpenAI "promote the rule into code"；Cursor "adds a lint rule whenever it sees the same mistake twice"）。
- **防陈旧**：每条带"最后验证日期 + 验证命令"；定期由 gardening 任务重跑验证命令、删除或标记失效条目（A4）。**推断**：对流水线而言，最便宜的新鲜度校验是把"测试怎么跑"写成可执行命令，由验收脚本真正执行一次。

### C.2 决策记录（为什么这样做、放弃了什么）
- **谁写**：做决策的那一方——spec/planner 阶段由 coordinator 或人写；实现中 worker 做出的影响他人的隐含决策（Cognition Principle 2）必须显式写出，否则并行 worker 会冲突。
- **谁读**：所有后续 worker（避免重复决策或反向决策）；reviewer 读"决策结论"以判断是否越界，但不读得出结论的推理过程（A14）。
- **何时写**：决策发生时，而不是会话末尾补写（**推断**：末尾补写容易被上下文耗尽截断，B.2）。
- **写什么**：结论、约束、被否决的备选与理由。只增不改；被推翻时追加新记录指向旧记录（**推断**，与 ACE 增量更新和 OpenAI 执行计划的 "decision logs" 一致）。
- **不宜放进**冷启动必读集合的全文：决策库按主题索引，入口只放目录（A3）。

### C.3 进度状态（哪张票做到哪、哪些通过）
- **谁写**：**由脚本写，不由模型自由书写**。状态从可验证事件派生（测试结果、合并、关票），模型只能改受限字段（Anthropic 用 JSON + 只改 `passes`，B.15）。
- **谁读**：coordinator 读全局；worker 只读自己票的状态和阻塞依赖（MetaGPT 订阅，A13）。
- **何时写**：状态变化的那一刻，由触发它的动作写入。
- **写什么**：状态、证据引用（日志路径、提交号），不写解释性长文。"完成"只能由验证者的端到端结果置位（B.12：自评不可信、看到进度就宣布完成）。

### C.4 交接（worker → reviewer/verifier，会话 → 下一会话）
- **谁写**：交出方写交接包；内容要让一个没有任何前情的读者能开工（A8："objective, an output format ... clear task boundaries"）。
- **谁读**：
  - 下一个执行者（继续同一工作）：给完整交接包 + 必要时可取回原始日志（fork 式，A14；可恢复压缩，A10）。
  - 验证者：只给任务定义、验收标准、diff/产物引用，**不给执行者的推理和自评**（Cognition 2026、LangChain isolated 模式）。
- **何时写**：会话结束前，与 git 提交一起；长任务在阶段边界写（Anthropic "summarize completed work phases and store essential information in external memory before proceeding"）。
- **写什么**：已完成、未完成、已知失败的尝试（A16）、环境是否处于干净状态（Anthropic "clean state"），以及大产物的路径引用而非全文（A9）。
- **执行者对评审意见的回应**：执行者负责用自己的上下文过滤评审意见（是否超范围、是否违背用户指令），过滤结果写回票里（Cognition "communication bridge"）。

### C.5 偏好 / 规则（用户喜欢的 PR 结构、命名、禁忌）
- **谁写**：用户本人，或 coordinator 根据用户明确反馈写入，需经用户确认后才进入规则层。**推断**：由 worker 从一次反馈中泛化出"用户偏好"风险最高——一次性意见被固化为全局规则，属于 B.7 的一种。
- **谁读**：arslan.io 的做法是 coordinator 每轮读 preferences.md、不下发给 worker，由 coordinator 在派活时转成具体要求。这与 A8（交接要显式）和 A11（给 worker 的上下文只放最少必要要求）一致；缺点是 coordinator 转述时可能漏掉（B.2）。**推断**：适合流水线的折中是——跟产出物形态直接相关的规则（PR 结构、提交信息格式）写成 worker 必读的短文件或由 lint/验收脚本强制；其余偏好留在 coordinator 层。
- **何时写**：用户给出反馈时；重复出现两次以上再从笔记升级为脚本/lint（Cursor gardening 做法）。
- **写什么**：可检查的规则，而不是形容词。

### C.6 安全边界（适用于全部共享文件）
- 共享文件是提示注入的传播通道（B.13）。worker 读到的外部内容（issue 正文、网页、第三方评论）不得原样写进共享知识；写入前标注来源（Prompt Infection 论文的防御叫 "LLM Tagging"）。
- 共享目录不放凭据（Managed Agents：让 token "never reachable from the sandbox"）。
- 写入路径做白名单校验（memory tool 文档的路径穿越防护）。

### C.7 何时共享上下文有效、何时失效（汇总）
- **有效**：任务可切成独立块（不同文件、不同失败测试）；知识是事实型且可验证；有可靠反馈信号（测试、执行结果）来判断笔记条目对错；读者冷启动、代码库文档少。
- **失效**：任务本质是一个大块（所有 agent 撞同一个问题，C 编译器编 Linux 内核的阶段）；多写者无仲裁；知识无法验证（ACE 无反馈时退化）；文件膨胀或冗余（AGENTS.md 论文）；验证者读到执行者推理后被锚定；共享文件混入未过滤的外部内容。

---

## D. 读过的 URL 清单

状态：✔ 全文读取（或读了与主题相关的全部章节）｜△ 部分读取（摘要或部分章节）｜✘ 抓取失败

| # | 资料 | URL | 状态 |
|---|---|---|---|
| 1 | Anthropic, How we built our multi-agent research system（2025-06-13） | https://www.anthropic.com/engineering/multi-agent-research-system | ✔ |
| 2 | Anthropic, Effective context engineering for AI agents（2025-09-29） | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | ✔ |
| 3 | Anthropic, Effective harnesses for long-running agents（2025-11-26） | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | ✔ |
| 4 | Anthropic, Harness design for long-running application development（2026-03-24） | https://www.anthropic.com/engineering/harness-design-long-running-apps | ✔（附录的示例 spec 只读开头） |
| 5 | Anthropic, Building a C compiler with a team of parallel Claudes（2026-02-05） | https://www.anthropic.com/engineering/building-c-compiler | ✔ |
| 6 | Anthropic, Scaling Managed Agents: Decoupling the brain from the hands（2026-04-08） | https://www.anthropic.com/engineering/managed-agents | ✔ |
| 7 | Claude memory tool 文档 | https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool | △（读了行为说明、协议、安全、多会话模式；SDK 代码示例略过） |
| 8 | Claude Code agent teams 文档 | https://code.claude.com/docs/en/agent-teams | △（读了上下文、任务列表、邮箱、最佳实践；UI 操作部分略过） |
| 9 | Anthropic 关于 agent teams 的专门工程文章 | — | 未找到（仅找到 #5 与 #8） |
| 10 | Cognition, Don't Build Multi-Agents（2025-06-12） | https://cognition.ai/blog/dont-build-multi-agents | ✔ |
| 11 | Cognition, Multi-Agents: What's Actually Working（2026-04-22） | https://cognition.ai/blog/multi-agents-working | ✔ |
| 12 | Manus, Context Engineering for AI Agents（2025-07-18） | https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus | ✔ |
| 13 | LangChain, Context Engineering（write/select/compress/isolate，2025-07-02） | https://blog.langchain.com/context-engineering-for-agents/ | ✔ |
| 14 | LangChain, How and when to build multi-agent systems（2025-06-16） | https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems | ✔ |
| 15 | LangChain, Deep Agents（2025-07-30） | https://blog.langchain.com/deep-agents/ | ✔ |
| 16 | LangChain, Organizing Context in a Multi-Agent Harness（2026-09-08） | https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness | ✔ |
| 17 | OpenAI, Harness engineering（2026-02-11） | https://openai.com/index/harness-engineering/ | ✘ 直连 403；✔ 经镜像全文读取 https://jaytaylor.com/notes/node/1770842156000.html |
| 18 | OpenAI Agents SDK, Handoffs | https://openai.github.io/openai-agents-python/handoffs/ | △（读 input_filter 与历史传递部分）。要点："When a handoff occurs, it's as though the new agent takes over the conversation, and gets to see the entire previous conversation history. If you want to change this, you can set an input_filter." |
| 19 | Cursor, Introducing Projects（2026-09-10） | https://cursor.com/blog/projects | ✔ |
| 20 | Cursor Projects 官方文档 | https://cursor.com/docs/projects ；https://cursor.com/docs/agent/projects | ✘（前者只得空壳，后者 404） |
| 21 | Cursor, Scaling long-running autonomous coding（2026-01-14） | https://cursor.com/blog/scaling-agents | ✔ |
| 22 | Cursor, Speeding up GPU kernels by 38% with a multi-agent system（2026-04-14） | https://cursor.com/blog/multi-agent-kernels | ✔（与共享上下文相关的只有一句："The entire coordination protocol lived in a single markdown file that specified the output format, rules, and tests."） |
| 23 | Fatih Arslan, How I manage my agents（2026-09-11） | https://arslan.io/2026/09/11/how-i-manage-my-agents/ | △（按关键词读了 Projects/Context/inbox 相关段落） |
| 24 | Han & Zhang, Exploring Advanced LLM MAS Based on Blackboard Architecture（arXiv 2507.01701） | https://arxiv.org/abs/2507.01701 | △（摘要、架构、结论、局限） |
| 25 | Salemi et al., LLM-Based Multi-Agent Blackboard System for Information Discovery（arXiv 2510.01285） | https://arxiv.org/abs/2510.01285 | △（摘要、结论） |
| 26 | MetaGPT（arXiv 2308.00352 v7，ICLR 2024） | https://arxiv.org/abs/2308.00352 | △（PDF 第 3 节通信协议与相关段落） |
| 27 | ACE, Agentic Context Engineering（arXiv 2510.04618 v3） | https://arxiv.org/abs/2510.04618 | △（摘要、第 2–3 节、结果中反馈依赖与局限、鲁棒性段落） |
| 28 | Dynamic Cheatsheet（arXiv 2504.07952） | https://arxiv.org/abs/2504.07952 | △（仅摘要） |
| 29 | Cemri et al., Why Do Multi-Agent LLM Systems Fail?（MAST，arXiv 2503.13657 v3） | https://arxiv.org/abs/2503.13657 | △（摘要、失败模式定义附录、成功/失败分布、组织设计讨论） |
| 30 | Gloaguen et al., Evaluating AGENTS.md（arXiv 2602.11988） | https://arxiv.org/abs/2602.11988 | ✔（正文结果、轨迹分析、消融、结论；附录略过） |
| 31 | Lulla et al., On the Impact of AGENTS.md Files on the Efficiency of AI Coding Agents（arXiv 2601.20404 v2） | https://arxiv.org/abs/2601.20404 | △（仅摘要） |
| 32 | CodeCRDT（arXiv 2510.18893） | https://arxiv.org/abs/2510.18893 | △（仅摘要） |
| 33 | SwarmWorld（arXiv 2608.26081） | https://arxiv.org/abs/2608.26081 | △（仅摘要） |
| 34 | Emergent Collective Memory in Decentralized MAS（arXiv 2512.10166） | https://arxiv.org/abs/2512.10166 | △（仅摘要） |
| 35 | Prompt Infection（arXiv 2410.07283） | https://arxiv.org/abs/2410.07283 | △（仅摘要） |
| 36 | MINJA, Memory Injection Attacks（arXiv 2503.03704） | https://arxiv.org/abs/2503.03704 | △（仅摘要） |
| 37 | Chroma, Context Rot（2025） | https://research.trychroma.com/context-rot | △（引言与结论段） |
| 38 | Drew Breunig, How Contexts Fail and How to Fix Them（2025-06-22） | https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html | △（四类失败定义与例子） |
| 39 | InfoQ 关于 OpenAI harness engineering 的报道 | https://www.infoq.com/news/2026/02/openai-harness-engineering-codex | △（只含转述，未用作引语来源） |
| 40 | arXiv 2604.02547 Beyond Resolution Rates | https://arxiv.org/html/2604.02547v1 | △（读标题与目录后判定与本题无关，未使用） |

未找到：Cursor Projects 中 notes.md 的官方写权限/冲突/淘汰规则；Anthropic 关于 Claude Code agent teams 的独立工程文章（除 C 编译器案例外）；Cognition 2026 后在"共享笔记文件"具体格式上的公开说明。

# research

## 定稿（主 agent 复核）

**判断**：技能正文与上游逐字相同，灵魂完整，不改。三处交接问题都在调用方，已写进对应技能的定稿：

- `wayfinder` 派出的 research subagent 会再派一层，结果存放在一条临时分支上，后面的环节读不到：见 `wayfinder` 定稿 I6。
- `implement` 让 worker 读 research 文件的"最后一节"，而实际报告的最后一节多是来源清单：见 `implement` 定稿 I14。
- research 文件算不算 baseline，三处说法不一致：只记录，留给 `to-tickets` 与词表处理。

## 结论

`mmw-v2/upstream/skills/engineering/research/SKILL.md` 共 131 词（去掉 frontmatter 后正文 87 词），没有 reference，没有脚本；另有 `agents/openai.yaml`（3 行，Codex 读的展示名）。它与最近一次上游 squash 提交 `5b1a4c51` 的 `skills/engineering/research/` 逐字相同（`git diff 5b1a4c51:skills/engineering/research HEAD:mmw-v2/upstream/skills/engineering/research` 输出为空），也与 GitHub 上 mattpocock/skills 今天的 `main` 相同（上游最后一次改它是 `32165827`，2026-08-19，去 em-dash）。本仓曾在 `30bf4b1e`（2026-08-22）加过一句「用 `readable-docs` 写」，又在 `9766d7f7`（2026-09-02）删掉，所以现在没有 merge-note 是对的。

技能本身没有可删的内容，也没有死板流程；它的灵魂（为什么放到后台、为什么只认一手来源、产出是一份带出处的文件、放在仓库惯例的位置）在 87 词里是完整的。真正的问题都在交接上，而且都不在 research 的正文里：wayfinder 把它派给 subagent 的那一句（`wayfinder/SKILL.md` `### Chart the map` 第 5 步）没说清楚 subagent 该不该再派、文件落在哪、谁关票；下游 `implement` 从 research file 里读结论的位置写错了。估计可删 0 词。

## A. 删除或改成脚本

无。

逐条核过：正文三条 `Its job` 各自对应一个行为（一手来源、带出处写成一份文件、按仓库惯例放置），没有复述脚本（没有脚本）、没有维护者理由、没有历史记录、没有防御条款。description 除触发条件外还有前半句「Investigate a question … as a Markdown file in the repo」，按用户「description 只写触发条件」的裁定属于非触发内容，但这是上游原文，删它只为减字数，按任务书边界不提。

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第一句 "Spin up a **background agent** to do the research, so you keep working while it reads."：说明这个技能存在的理由是保护调用者的上下文和进度，不是"读文档"本身。没有这半句，agent 会在自己的会话里读完再回来。
- `Its job` 第 1 条 "not a secondary write-up of them. Follow every claim back to the source that owns it."：这是整个技能的判断标准，告诉 agent 什么样的来源算数、查到哪一步才算到底。agentflow 的实际使用（见下文"与其他技能的重复或交接问题"第 2 条）里，subagent 先读 SDK 源码再对照阿里云官方文档，正是按这句做的。
- `Its job` 第 2 条 "citing each claim's source"：下游 `to-spec` 的 `## Sources` 与 `to-tickets` 的 `## Read first` 都把 research file 当作可追溯的来源；每条带出处是它能被当作来源的前提。
- `Its job` 第 3 条 "match the existing convention, and if there is none, put it somewhere sensible and say where."：把落点交给 agent 判断，并要求它报告落点。本仓的惯例是 `docs/research/`（根 `AGENTS.md` 第 4 行："The rest of `docs/research/` holds research notes, which a spec may cite as sources"），这句让 agent 自己找到它，不需要写死路径。

### 缺口与补充草稿

research 正文没有需要补的灵魂缺口。候选的三处我都查了，结论是不补：

- 何时停止读、怎样才算查完：上游文档页 `docs/engineering/research.md`（squash 树里）承认 "There is no stopping criterion in the skill"。在 MMW 里，问题的范围来自调用方：wayfinder 路径下是票的 `## Question`，直接调用时是用户那段话。补在调用方给 subagent 的那段交代里更合适，草稿并入下文"交接问题"第 1 条的 wayfinder 草稿，不改上游正文。
- 区分"没找到"和"不存在"：本仓已有的 research file 都自带这一节（例如 `docs/research/mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/README.md` `## 没查清楚的部分`，`docs/research/workflow-compare/reports/M1-mmw-front.md` `## 9. 未读到或不确定`），用户级 prompt 的规则 4 也要求标明推断与未核实。没有做错的证据，不补。
- 记下所查对象的版本与日期（research file 会过时，而 `docs/contexts/tickets/CONTEXT.md` 的 **baseline** 条目把 "a research file's conclusion" 列为 worker 必须照做的 baseline）：agentflow #592 的报告自己写了 SDK 版本 1.2.5 和 `uv.lock` 行号，本仓 #20 的答案写了拿不到完整 SHA 的原因。agent 没有这句也做对了，不补。

## C. 死板的流程

无。`Its job` 的三条是三个目标，不是步骤，每条都留了判断空间（"somewhere sensible"）。

## 脚本

无。

## 与其他技能的重复或交接问题

1. **wayfinder 派 research subagent 的那一句没交代清楚，会导致嵌套派发（上游原文在 MMW 工作流里会让 agent 做错）。**
   - 位置：`mmw-v2/upstream/skills/engineering/wayfinder/SKILL.md` `### Chart the map` 第 5 步 "Fire the research subagents. … spin up your host's own general-purpose subagent and have it use the `research` skill…"，以及 `## Ticket Types` 的 Research 条 "Resolved by your host's own general-purpose subagent using the `research` skill"。
   - 问题：被派出的 subagent 加载 research，读到的第一句是 "Spin up a **background agent**"，于是按字面再派一个。上游 issue mattpocock/skills#530（仍是 OPEN）报告的就是这个：一次调研在后台跑出两到三个重叠的 agent；上游文档页说 Codex 上也复现。Claude Code 的 general-purpose subagent 带有派 agent 的工具（本会话的工具清单里 general-purpose 是 "Tools: All tools"）。
   - MMW 内的真实证据：我只找到一次 wayfinder 真的派了 research subagent，是 agentflow 仓库 map #578 的 research 票 #592（2026-09-02，会话记录 `~/.claude/projects/-Users-cheuklapchan-agentflow--claude-worktrees-hedgehog-boss-console/0c222014-…/subagents/agent-afe82d9840bd9bd11.jsonl`）。那次没有嵌套，因为发起派发的 agent 自己写了 7 步交代：认领、调研、写到 `docs/research/work-monitor/592/report.md`、在 `research/oss-delete-and-ram` 分支上提交并切回、在票上评论结论、关票、在 map 的 `## Decisions so far` 追加一行，并说明要回报什么。也就是说，wayfinder 第 5 步没写的交接，全靠那个 agent 自己补上了。本仓自己的 research 票只有三张：#19、#20 属于上一代 MMW（`archive/`），v2 的 #550 在试点 #541 里"这次没有派 subagent，事实已经在生产代码里"。
   - 该留哪边：research 正文不动。按 `SKILL-SET-REVIEW.md` `### Upstream skills` "Connect outside the upstream text first … in the line a caller reads"，改 wayfinder 第 5 步（本仓已经为 host 中立改过这一步，`mmw-v2/merge-notes/wayfinder.md` 有对应条目），并按 `### Prompts written for other agents` "A subagent's brief states what it returns and its length" 补上回报内容。草稿（接在第 5 步末尾）：
     > The subagent is the background agent the `research` skill asks for: it reads and writes itself and starts no agent of its own. Give it the ticket's question as its whole scope. It saves the file where the repository keeps research notes, posts the answer as the ticket's resolution comment with the file's path, and closes the ticket; it returns the path and the answer in three sentences, and you append each context pointer to the map's Decisions-so-far yourself, one edit at a time, so parallel subagents never rewrite the map body at once.
   - 剩余风险：用户直接说"research 一下 X"时不经过 wayfinder，主 agent 派出的后台 agent 仍可能因为 description 匹配而再加载 research、再派一次。这条路径只能靠改 research 正文（上游那种一句话补丁："if you are already a subagent, do the work yourself"）来堵，要改就得新建 `mmw-v2/merge-notes/research.md`。本仓没有观察到这种情况，我不建议现在改上游。

2. **wayfinder 的 "throwaway `research/<name>` branch" 与 MMW 下游读 research file 的方式冲突。**
   - 位置：同上第 5 步 "capturing its findings on a throwaway `research/<name>` branch with a context pointer from the ticket"；research `Its job` 第 3 条 "Save it where the repo already keeps such notes"。
   - 问题：在 MMW 里，research file 不是用完即扔的。`to-spec` 的 `## Sources` 有一行 "Research files"，每条决定句末要写 "a research or prototype path"；`to-tickets` 第 173 行把 research files 放进 `## Read first`；`implement` 第 20 行要 worker 把它读到结论。worker 的票 worktree 是从 base branch 切出来的，如果文件只在一条没合并的分支上，worker 打不开 spec 引用的路径。上游文档页自己也写了这个坑（"deleting the branch later breaks the context pointers the tickets hold"），另有 mattpocock/skills#576（subagent 从这种分支开了 draft PR）。
   - 真实证据：agentflow #592 的结论评论写的是"分支 `research/oss-delete-and-ram`，未 push"，即 context pointer 指向一条只在本机的分支。那份报告后来出现在 agentflow 的 `dev` 与 `main` 上，是经什么路径合进去的我没有追。agentflow 里还有 5 条 `research/*` 分支被推到了 `origin`，与"throwaway"的说法不符。多个 subagent 在同一个 checkout 里并行 `git checkout -b` 会互相切走对方的工作树，这一点是推断，#592 那次只有一个 subagent，没有经过检验。
   - 该留哪边：留 research 第 3 条（仓库惯例目录），改 wayfinder 第 5 步，去掉 throwaway 分支的说法，与第 1 条的草稿合并成一句（草稿里的 "saves the file where the repository keeps research notes" 已经覆盖）。改动要在 `mmw-v2/merge-notes/wayfinder.md` 登记：上游这一处在 MMW 里会让 spec 引用的路径失效。

3. **`implement` 读 research file 结论的位置写错了。**
   - 位置：`mmw-v2/upstream/skills/engineering/implement/SKILL.md` 第 20 行 "each through to its conclusion: the last section of a research file"；`mmw-v2/merge-notes/implement.md` 第 14 行（"research 的末节"）也是这样写的。
   - 证据：research 技能从没要求把结论放在最后一节。本仓 `docs/research/` 下约 30 份报告，最后一个 `##` 几乎都是来源清单或未核实事项，例如 `shared-context/research-5-nowledge-mem.md` 的 `## Sources`、`workflow-compare/reports/M2-mmw-night.md` 的 `## 9. 未读到或不确定`、`mmw-artifact-wiring/issue-20/aidlc-v2-artifact-wiring/report.md` 的 `## 12. CI 与测试覆盖`。agentflow #592 的报告把结论放在开头的 `## 结论摘要`，最后一节是 `### 4. 开发桶与生产桶`。worker 照字面去读"最后一节"，会把来源清单或一个细节小节当成结论，而这份结论在 MMW 里是 baseline（照做，不是参考）。
   - 该留哪边：research 不动。改 `implement` 与它的 merge-note，写成 "the part of a research file that answers its question"，和 `docs/contexts/tickets/CONTEXT.md` **baseline** 条目的 "a research file's conclusion" 用同一个说法。这一条归 `implement` 的复审者处理。

4. **research file 算不算 baseline，三处说法不一致（只记录）。** `docs/contexts/tickets/CONTEXT.md` **baseline** 条目列了 "a research file's conclusion"；`to-tickets/SKILL.md` 第 173 行列举 baseline 时（"the chosen artifact of a prototype, a design package …, the decision an ADR states …, the resolution of a decision ticket"）没有 research file；`implement` 第 20 行说 Read first 里"anything there that records a settled conclusion"都是 baseline。research 查到的是事实，不是决定；wayfinder 路径下，这个事实会经过 decision ticket 的 resolution 进入 baseline，所以 `to-tickets` 不把它单列可能是有意的。该以哪处为准由 `to-tickets` 或 domain-modeling 的复审者判断。

5. **`ask-matt/SKILL.md` 第 84 行对 research 的概述**（"delegate reading legwork to a background agent … leaves a cited Markdown file in the repo"）与 research 的 description 意思重叠。这是路由器给出的选择依据，两边都是上游原文，都留着。

## 没查到的

- 没有在 Codex、Grok、Pi、Cursor 上核实"general-purpose subagent 能否再派 agent"。说 Codex 会嵌套，依据只是上游文档页的转述。
- agentflow #592 的报告从 `research/oss-delete-and-ram` 进入 `dev` / `main` 的路径没有追；agentflow 另外 5 条 `research/*` 分支是不是 wayfinder 派出来的，也没有查。
- Claude 会话记录只按 `engineering/research/SKILL.md` 与 `"skill":"research"` 两种字符串搜过，Codex 会话只按路径搜过（命中的是 2026-09-05 的若干 rollout，我没有打开，推测是复审时读文件）。直接调用（不经 wayfinder）时是否发生过嵌套，没有找到证据，也不能排除。
- 上游 `docs/engineering/research.md` 是 squash 树里的文档页，不会被 host 加载。这里引用它只是作为上游对已知问题的说明。

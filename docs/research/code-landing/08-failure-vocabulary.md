# 失败词汇：票收尾时「失败 / 验不了 / 放弃 / 要人定」怎么说，票在 GitHub 上怎么落

问题：一张票由 agent 无人看守地做到收尾，结果不是全过时，用哪套固定词写在票上；票本身开还是关、贴什么标签；用户早上 `gh issue list` 看什么就知道哪些票要自己处理。

路径约定：参考快照的路径都相对 `docs/research/code-landing-refs/`；本仓自己的文件相对仓库根。`file:12-15` 指该文件第 12 到 15 行。

## 1. 一句话结论

四家里只有 unlazy 把「一条验收标准的终态」和「一张票的终态」分成两层并各给了固定词（`gates.md:126-128`、`orchestration.md:7-15`），pstack 只给了「谁验、验到什么等级」的裁决词（`orchestrate.md:91`）和「要人定」的停车位（`orchestrate.md:107`），grok 只有「整个单元失败 → 下游全跳过」的批处理词（`execute-plan/SKILL.md:786-797`），swarm-forge 只有「问操作员」一条通道（`handoff-protocol.md:193-198`）。建议：标准层沿用 unlazy 的 `met / unmet / abandoned` 加 `ABANDON: <id> <kind> <reason>`，把 `<kind>` 固定为 `decision / failed / stuck` 三个词区分三种情况（`12-decisions.md` I4）；票层沿用 unlazy 的评论首行 `ALL MET` / `HANDOFF REQUIRED`；GitHub 上只动两样东西：`ALL MET` 摘掉 `ready-for-agent` 并关票（`gh issue close --reason completed`），`HANDOFF REQUIRED` 不关票、把 `ready-for-agent` 换成 `needs-triage`——卡住的那一刻还没有人判定过它要人做、要补信息还是换个 agent，而 `needs-triage` 是唯一一道有技能主动去取的队列（`12-decisions.md` I3）。下游被 block 的票什么都不做：本仓的 frontier 定义已经是「blocker 全关才解锁」（`docs/agents/issue-tracker.md:42`、`mmw-v2/upstream/skills/engineering/implement/SKILL.md:8`），这正是 unlazy「abandonment 不能提升父级」的语义，不需要 grok 的 Cascade-Skip 再标一遍。

## 2. 各家的终态词表与精确定义

### 2.1 unlazy

标准层（一条 gate）。`stop-hook.mjs:122-127` 里 `gateState` 的取值就是全部：

| 词 | 定义 | 出处 |
| --- | --- | --- |
| met | runnable gate：进程 exit 0 **且** `EXPECT:` 匹配合并输出；manual gate：勾了且 `EVIDENCE:` 非 `pending`。 | `gates.md:50-53`、`:57`；`unlazy/SKILL.md:30` |
| unmet | 没勾；或勾了但 `EVIDENCE:` 缺失或仍是 `pending`（hook 里叫 `unmet-no-evidence`）。exit 非零即使输出含期望 token 也算 unmet；超时、shell 起不来、命令不存在、输出超限都算 unmet。 | `gates.md:55`、`:57`；`stop-hook.mjs:125` |
| abandoned | 文件里有一行列首的 `ABANDON: <id> <非空理由>` 指向这条 gate。原 gate 原文保留，不删不改。 | `gates.md:40-41`、`:128` |

三个额外规定决定了这套词怎么用：

- `ABANDON:` 的准入条件是「required outcome is genuinely impossible within the authorized task」，用词是「only」（`gates.md:128`）；hook 的阻止消息里重复了同一句（`stop-hook.mjs:172`）。
- abandoned 是终态但不是完成：`gate-check` 打印 `HANDOFF REQUIRED` 并 exit 1，即使其余 gate 全 met（`gates.md:128`）。
- 环境不一致不是证据：「Treat an environment mismatch as a failed verification, not as evidence」（`unlazy/SKILL.md:71`）；父级重验时「If the environment differs, record and resolve the mismatch instead of accepting old evidence」（`orchestration.md:84`）。也就是说「验不了」在 unlazy 里先落到 unmet，不落到 abandoned。

票层（一个 leaf）。`orchestration.md:7-13` 只允许五个状态：

| 词 | 定义 |
| --- | --- |
| `WAITING` | `Needs` 里有 id 还不是 `VERIFIED` |
| `READY` | 依赖全 verified 且 `OWNS:` 路径可申领 |
| `IN-FLIGHT` | 已派发，未经父级独立重验 |
| `VERIFIED` | 父级 `--reverify` 通过，manual gate 也审过 |
| `ABANDONED` | 至少一条必需 gate 有记录在案的 handoff；「never treat this as full completion」 |

branch 只有 `OPEN / VERIFIED / ABANDONED`（`orchestration.md:15`）。派发层还有一个 `dispatch-check abandon --wave --reason`，整个 wave 放弃，`status` exit 1，hook 同样发 `HANDOFF REQUIRED`（`dispatch.md:70-76`）。

Stop hook 什么状态放行、什么状态阻止（`stop-hook.mjs`，只读）：

- 没有任何 ledger、没有阻塞或放弃的 wave → 静默放行（`:84-87`）。
- 有 unmet 或解析失败的 ledger → 返回 `decision: "block"`，理由是「N gate/ledger/dispatch item(s) need work: <前 5 个 id>」，并附「Use ABANDON: <id> <non-blank reason> only when a gate is genuinely impossible」（`:168-173`）。连续 6 次 block 而 gate 状态没变就放行，消息改为「releasing after 6 blocks without gate progress; N item(s) remain」（`:12`、`:161-165`）。
- 全部 met 或 abandoned、无 unmet → 放行；有 abandoned 时附 `systemMessage`：「HANDOFF REQUIRED: N abandoned item(s): <限定 id，最多 5 个>」，不带自由文本理由（`:92-97`、`:130-135`）。

这是关键机制：unmet 让 agent 停不下来，abandoned 让它能停但必须留下 handoff。放弃是唯一诚实的退出。

最终报告（`unlazy/SKILL.md:80-82`「Audit the final report」）：报告前重读原请求、重测每个数字，用限定 id（`leaf-1.2.1:G3`），报出实测的 met / unmet / abandoned 三个计数并列出每一条 abandonment；「Do not compose a done report while any required gate is unmet, abandoned, deferred, or awaiting an owner decision」。注意 `orchestration.md:44` 把「deferment, and owner decisions」也列为 non-completion，但状态词表里没有对应的词——「要人定」在 unlazy 里只能写成 `ABANDON:`，`gates.md:28` 的示例正是这样：`ABANDON: G3 decision owner unavailable; handoff recorded in issue 123`。

### 2.2 pstack

裁决层（一个 PR head SHA 一行，`orchestrate.md:91`）：

| 词 | 定义 |
| --- | --- |
| `live-ui-verified` | 在跑起来的 app 里验过 |
| `unit-test-verified` | 单测验过；「Behavioral work needs better than `type-check-only`」 |
| `type-check-only` | 只过了类型检查 |
| `verifier-blocked` | 「is not a pass; respawn when the environment heals」 |
| `verifier-failed` | 「gets a fix unit, not a re-verify」 |

规则：「A worker may self-report; a verifier overrides it on the same key. A new head SHA voids the row」；「CI green is an input to a verdict, not a verdict」（同行）。

单元层（`orchestrate.md`）：

- 收件箱分类五个词：`landed, needs-verify, failed, zombie, noise`（`:75`）。
- 收尾时每个 spawn 过的 agent 要归到终行：`done, abandoned, zombie-reconciled`（`:68`）。
- 重试按失败模式分类，「Two retries, then abandon the unit and replan around it」（`:99`）。
- 悄悄死掉的 agent 得到一行合成 postmortem：「unit, failure mode, last evidence, options」（`:98`）。
- `TIMEBOX` 到期「return partial findings and stop rather than run on」（`:47`）；`REPORT` 固定字段「status, branch, head SHA, PRs, verdict, what you actually ran, deviations, suggested follow-ups」（`:49-50`）。
- 自己的基础设施连续出错时「write a terminal handoff to durable state (what is done, where it lives, the exact command to resume) and end the run」（`:102`）。

要人定（`orchestrate.md:107-109`「Escalation」）：能到人的只有四类：不可逆操作、实验解决不了的产品/偏好判断、常驻规则与现实矛盾、replan 后仍存在的程序级死路；每一项「Park each as a `gates.md` entry before asking, and route work around it」，`gates.md` 条目是「question, options, default on no answer」（`:32`）；到人的方式是「batched into the status page rather than per item」。明确不到人的包括「"should I keep going"」（`:109`）。

维护 verification skill 的三种结局（`maintain-verification-skill/SKILL.md:15-17`）：`clean`（无需改）、`changed`（一个 PR）、`blocked`（「Say exactly what blocked it」）。另有一个 feature 级的词 `verified-unreachable`，只有带「the concrete prerequisite (auth, entitlement, OS, external state) and the route attempted」才能用（`:33`）；app 本身坏了是「product gap; record it for the user, keep it out of this PR」（`:35`）。

暂停与接手：`pause-safely.md:5-8` 要求在安全边界停、不越过不可逆线、`wip:` 提交、写 resume note（意图、进度、已验证的、下一步）；`session-pickup.md:11` 接手时「A passing prior self-report is not the proof」。

### 2.3 grok-bundled

`implement/SKILL.md` 没有失败终态：「The **only** exit condition is **all reviewers** reporting **0 issues** of any severity in the same round. There is no iteration cap」（`:760`）。它有的词：

| 词 | 定义 | 出处 |
| --- | --- | --- |
| `Status: open / fixed / wontfix` | 一条评审发现的状态；`wontfix` 由实现者写并附技术理由 | `:660-669` |
| stalemate | 上一轮实现者标 `wontfix`、本轮 reviewer 又标回 `open` 的同一条发现 | `:620-624` |
| Step 3a Escalate to User | 检出 stalemate 就问用户，列双方立场和可选项；用户答复是 final，实现者按答复把该条标 `fixed` | `:636-643` |
| 子代理崩溃 | 「report the error to the user and stop」；只有 specialist reviewer 失败可继续 | `:1000` |

`execute-plan/SKILL.md` 才有批处理终态：

| 词 | 定义 | 出处 |
| --- | --- | --- |
| `failed` | 子代理返回失败、实现超过 15 分钟被 kill、cherry-pick 无法解决、push 重试仍失败 | `:454-458`、`:573-577`、`:904`、`:960` |
| `skipped` | 状态为 `pending` 或 `branch_created`、且传递依赖里有 `failed` 的 PR；error 写成 `Skipped: dependency <id> failed` | `:786-795` |
| Cascade-Skip | 标 failed 后把上面这些依赖者全部标 skipped，从 ready_queue 移除，「Do not abort the entire run -- independent PRs continue executing」 | `:784-797` |
| Resumption | `--resume`：`failed` 清干净重来；`skipped` 若依赖现已 `completed` 则回到 `pending`，否则保持 `skipped`；`implementing`/`reviewing` 视为崩溃、重来 | `:821-826` |

grok 的「需要人决定」只有 stalemate 一种，且是阻塞式的（问了就等）。

### 2.4 swarm-forge

只有两种消息：`git_handoff` 和 `note`（`handoff-protocol.md:127-217`）。被歧义、矛盾、测试与规格冲突卡住时，「ask the operator with `pack_dashboard_request.sh clarify ./tmp/question.txt` instead of asking in the pane or sending a `note` handoff」（`:195-198`）。人看的是仪表盘 **Attention** 面板：「human gates: spec approvals and agent clarification requests」（`README.md:125`）；回答被注入该 agent 的 pane，卡片留在原 agent 手里（`README.md:136-138`）。没有「失败」「放弃」的词；`AUDIT_REQUIRED` 是交接前的自审门，不是终态（`:248-262`）。

## 3. 四种情况各家用哪个词、谁标、标了以后怎么走

| 情况 | unlazy | pstack | grok | swarm-forge |
| --- | --- | --- | --- | --- |
| **验失败**（命令跑了，结果不对） | 词：unmet。谁标：checker 机器判（`gates.md:50-55`）。之后：hook 阻止退出，继续修；修不了才 `ABANDON:`。 | 词：`verifier-failed`。谁标：verifier，覆盖 worker 自报（`orchestrate.md:91`）。之后：开一个 fix unit，不是重验。 | 词：评审 `Status: open`（`implement:660`）；批处理层 `failed`（`execute-plan:573-577`）。谁标：reviewer / orchestrator。之后：无上限修审循环；批处理层 Cascade-Skip。 | 无专门词；`git_handoff` 只在自审通过后发（`:257`）。 |
| **验不了**（环境、缺依赖、命令起不来） | 词：unmet（超时、命令不存在都算，`gates.md:55`；环境不一致是 failed verification 不是证据，`SKILL.md:71`）。谁标：checker。之后：「record and resolve the mismatch」（`orchestration.md:84`）；任务内确实解决不了才 `ABANDON:`。 | 词：`verifier-blocked`（`orchestrate.md:91`）；维护流程叫 `blocked` / `verified-unreachable`（`maintain-verification-skill:17`、`:33`）。谁标：verifier。之后：「respawn when the environment heals」；`verified-unreachable` 必须写前提和试过的路径。 | 无区分；超时 15 分钟就是 `failed`（`execute-plan:454-458`）。 | 无。 |
| **放弃**（任务内做不到） | 词：`ABANDON: <id> <reason>` → gate abandoned → leaf `ABANDONED`（`gates.md:128`；`orchestration.md:13`）。谁标：做这个 leaf 的人自己写，但准入是「genuinely impossible within the authorized task」。之后：`HANDOFF REQUIRED` exit 1；hook 放行；父级永不因此 `ALL MET`；报告必须列出。 | 词：`abandon the unit and replan around it`（`orchestrate.md:99`）。谁标：coordinator，在两次重试之后。之后：终行 `abandoned`（`:68`），回复里「what was abandoned and why」（`:113`）。 | 词：`failed` + 依赖者 `skipped`（`execute-plan:786-795`）。谁标：orchestrator。之后：独立 PR 继续；最终报告列 failed 和 skipped，给 `--resume` 命令（`:1189-1190`）。 | 无。 |
| **需要人决定** | 无专门词。写成 `ABANDON: <id> decision owner unavailable; handoff recorded in issue 123`（`gates.md:28`）；`orchestration.md:44` 把「owner decisions」列为 non-completion。之后：同放弃。 | 词：`gates.md` 条目「question, options, default on no answer」（`orchestrate.md:32`、`:107`）。谁标：coordinator。之后：「route work around it」，批量进 status page，人回来再看。 | 词：stalemate → Step 3a（`implement:620-643`）。谁标：orchestrator 检出，用户裁决。之后：阻塞等答复；答复 final。 | 词：`clarify` 请求 → Attention 面板（`handoff-protocol:195-198`；`README:125`、`:138`）。谁标：卡住的 agent。之后：卡片留在该 agent，人答了注入 pane。 |

两点值得单拎出来：

- 只有 pstack 把「验不了」和「验失败」用两个词分开，且明确两者的后续动作不同（重派 vs 开修复单元）。unlazy 两者都先是 unmet，靠 `ABANDON:` 的自由文本理由区分。
- 只有 pstack 和 swarm-forge 让「要人定」不阻塞其余工作（停车位 / Attention 面板）；grok 的 stalemate 是阻塞的，unlazy 把它并进放弃。无人看守场景要的是前者。

## 4. 已定规则落到哪种终态

`00-synthesis.md:46-55`「第一轮之后已定的事」里三条与终态有关：

| 已定规则 | 对应终态 | 理由 |
| --- | --- | --- |
| 写码中发现契约装不下 → 继续做，在 spec 下开 sub-issue 记录（`00-synthesis.md:54`） | **不是终态**。原票照常走 met / unmet；新开的 sub-issue 是一张普通新票。 | 「继续做」意味着原票的验收标准不受影响；unlazy 里对应「Do not invent a dependency during dispatch. Add it to `PLAN.md`」（`orchestration.md:75`），pstack 里对应「Everything else parks in follow-ups」（`orchestrate.md:111`）。只有当装不下的那部分让某条验收标准做不到时，那条标准才 `ABANDON: <id> impossible <reason> → sub-issue #N`。 |
| code-review 两轮，第二轮仍有票内发现 → 不关票（`00-synthesis.md:55`） | **HANDOFF REQUIRED，kind = failed**。 | 「票内发现」= 与票的验收标准或 spec 决策相关的发现，两轮没修完就是「验失败且修不了」。这是本仓记忆 `456d6f5e`（reviewer 只能对票的验收门判定，超范围只记录不阻塞）对 grok 无上限循环的替代：grok 靠 stalemate 问人（`implement:636-643`），我们靠轮数上限落 handoff。票外发现走 sub-issue，不影响终态。 |
| verifier 覆盖 worker 自报（`03` 候选 B；`orchestrate.md:91`） | `verifier-failed` → **HANDOFF REQUIRED，kind = failed**；`verifier-blocked` → **HANDOFF REQUIRED，kind = blocked**；三个 pass 等级 → 该条 met。 | `03` §6 D 已说明：若采 B，D 只保留 `ABANDON:` 语义（worker 主动放弃），verifier 的两种非 pass 归 B。这里把两者接起来：verifier 的非 pass 裁决就是 `ABANDON:` 的 `failed` / `blocked` 两个 kind 的来源。谁写那行 `ABANDON:` 见 §6.3。 |

## 5. 映射到 GitHub Issues

### 5.1 `gh` 能表达什么（gh 2.96.0，本机实测）

| 能力 | 命令 |
| --- | --- |
| 开/关票，关票带原因 | `gh issue close <n> --reason {completed\|"not planned"\|duplicate}`；JSON 字段 `stateReason`、`closedByPullRequestsReferences` |
| 标签 | `gh issue edit <n> --add-label / --remove-label`（`docs/agents/issue-tracker.md:11`） |
| sub-issue | `gh issue create --parent <n>`；`gh issue edit <n> --parent / --add-sub-issue / --remove-sub-issue`；JSON 字段 `parent`、`subIssues`、`subIssuesSummary` |
| blocked-by | `gh issue create --blocked-by 200,201 --blocking 300`；`gh issue edit --add-blocked-by / --remove-blocked-by`；JSON 字段 `blockedBy`、`blocking`。比 `docs/agents/issue-tracker.md:42` 写的 `gh api ... /dependencies/blocked_by` 那条路直接 |
| 认领 | `gh issue edit <n> --add-assignee @me`（`docs/agents/issue-tracker.md:44`） |
| 评论 | `gh issue comment <n> --body`；评论无结构，「首行」只是约定 |

没有的：per-criterion 状态、评论级标签。所以标准层的词只能活在评论正文里，票层的词才能用开关和标签表达。

### 5.2 与 triage 状态机的关系

`mmw-v2/upstream/skills/engineering/triage/SKILL.md:30-36` 的五个状态角色、`:44` 的转移：未标 → `needs-triage` → `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix`；`needs-info` 回 `needs-triage`；「The maintainer can override at any time; flag transitions that look unusual」。`to-tickets/SKILL.md:68` 出票即 `ready-for-agent`。`triage-labels.md:9-10`：`ready-for-agent` = 「Fully specified, ready for an AFK agent」，`ready-for-human` = 「Requires human implementation」。

implement 收尾要做的状态变化只有一种：`ready-for-agent → ready-for-human`（HANDOFF）。这条转移状态机没有列，但落在「maintainer can override」之内，且语义吻合：票已经到了只有人能推进的地步。反向 `ready-for-human → ready-for-agent` 只由人做（人答完问题、修好环境、或决定放弃），agent 不做。`wontfix` 仍归 triage，implement 不碰。`needs-info` 不用：`triage-labels.md:8` 定义它是「Waiting on reporter」，reporter 是外人，不是用户自己。

### 5.3 最小词表

评论首行（票层，二选一，全大写方便 `--search`）：

| 首行 | 票 | 标签 |
| --- | --- | --- |
| `ALL MET` | `gh issue close <n> --reason completed` | 不动 |
| `HANDOFF REQUIRED: <n> abandoned (<kinds>), <m> unmet, <k> met of <total>` | 不关 | `--remove-label ready-for-agent --add-label ready-for-human` |

标准层（评论正文，每条验收标准一块）：

| 状态 | 写法 |
| --- | --- |
| met | `- [x] AC<n>: <原文>` + `CHECK:` / `EXPECT:` / `EVIDENCE:`（`03` 候选 A） |
| unmet | `- [ ] AC<n>: <原文>` + `EVIDENCE:` 写失败事实；**没有** `ABANDON:` 行。只出现在会话被 timebox 或中断时（pstack 的「partial findings」）。 |
| abandoned | `- [ ] AC<n>: <原文>` 保留原文 + 列首 `ABANDON: AC<n> <kind> <reason>` |

`<kind>` 三选一，固定拼写。三个词各对应一种机器行为——一个词要留下，得有人据它做不同的事（`12-decisions.md` I4）：

| kind | 情况 | 准入 | `--closeout` 据它做什么 |
| --- | --- | --- | --- |
| `decision` | 要人定 | 两个选项都合法、票和 spec 都没说。理由写成「问题 + 选项 + 无人答复时的默认」（pstack `orchestrate.md:32`）。UI 截图 diff 非零**不**走这里 | 不挡 `ALL MET`：它已开成一张 `needs-triage` 的 sub-issue，票继续做完其余标准（`12-decisions.md` H3） |
| `failed` | 跑了，没过 | 同一条标准自跑修满三轮仍不过；或 code-review 票内发现修一轮后仍不过；或 verifier 裁决 `verifier-failed` | 挡 `ALL MET`；并要求票上数得出三条该标准未过的 `self-run` 评论（`12-decisions.md` I5） |
| `stuck` | 跑不起来，或任务内做不到 | `CHECK:` 起不来、缺凭据、缺设备、verifier 裁决 `verifier-blocked` 修环境后仍起不来，或任务内做不到。理由必须含试过的路径（`maintain-verification-skill:33` 对 `verified-unreachable` 的要求）或指向记录它的 sub-issue | 挡 `ALL MET`；不看轮次——它第一轮就该允许放弃 |

verifier 行（若采 `03` 候选 B）：`VERIFIER (<模型家族>, <sha>): <裁决> for AC…`，裁决词沿用 `live-ui-verified / unit-test-verified / type-check-only / verifier-blocked / verifier-failed`。

末尾计数一行：`Counts: <k> met, <m> unmet, <n> abandoned of <total>`，与首行数字相同；两处都写是为了 `--search "HANDOFF REQUIRED"` 命中首行、人眼读末尾（`unlazy/SKILL.md:82`「remeasure every reported count」）。

### 5.4 早上看什么

```
gh issue list --state open --label ready-for-human            # 要你处理的：每张打开读最后一条评论的 ABANDON: 行
gh issue list --state closed --search "closed:>=<昨天>"        # 夜里做完的
gh issue list --state open --label ready-for-agent --assignee @me   # 认领了却没收尾评论 = 会话死了（pstack zombie）
gh issue list --state open --label needs-triage --search "is:issue parent:<spec 号>"  # 夜里新开的 sub-issue
gh issue list --state open --json number,title,blockedBy --jq '.[]|select(.blockedBy|length>0)'  # 还被卡着的
```

第三条依赖 implement 开工时 `--add-assignee @me` 认领；现行 `implement/SKILL.md` 没有这一步，`docs/agents/issue-tracker.md:44` 只给 wayfinder 定了。见 §7。

## 6. 夜间批量：一张票 HANDOFF，下游怎么办

grok Cascade-Skip 把下游显式标 `skipped`，理由写「Skipped: dependency <id> failed」，`--resume` 时依赖完成了再回 `pending`（`execute-plan:786-795`、`:824`）。unlazy 不标下游：abandoned 的 leaf 永远不是 `VERIFIED`，依赖它的 leaf 就一直 `WAITING`（`orchestration.md:9`、`:13`），「Never promote an abandoned child through a parent `ALL MET` oracle」（`gates.md:128`）。

本仓已经是 unlazy 那种：`docs/agents/issue-tracker.md:42`「A ticket is unblocked when every blocker is closed」，`implement/SKILL.md:8` 开工前查「every ticket under **Blocked by** is closed. If either fails, stop and report」。HANDOFF 票不关，下游就自然拿不到。所以：

1. 下游票不加评论、不改标签。改了反而要在人处理完上游后再改回来，多一处状态。
2. 独立的票继续做（grok `execute-plan:797`、unlazy rolling dispatch `orchestration.md:58-73` 一致）。
3. 派发者的夜间总结（不是票上）列出「因 #N HANDOFF 而未派的票」，`gh issue list --json number,blockedBy` 能算出来。
4. 人处理完上游：要么关掉上游（下游自动解锁），要么把上游改回 `ready-for-agent` 让 agent 再来一次。

grok 的 Cascade-Skip 唯一多出来的价值是 `skipped` 这个可查询的显式状态；用 `blockedBy` 字段查得到同样的信息，不必再写。

## 7. 建议

### 7.1 implement 收尾评论的固定格式

```
<ALL MET | HANDOFF REQUIRED: n abandoned (kinds), m unmet, k met of total>
Branch: <branch>  Commit: <sha>  PR: #<n>

- [x] AC1: <验收标准原文>
  CHECK: <命令>
  EXPECT: <期望子串或 /regex/>
  EVIDENCE: exit <code>; matched "<...>"; <sha>
- [ ] AC2: <验收标准原文>
  EVIDENCE: <失败事实：exit code、不匹配的输出片段，或 manual 时看的制品>
ABANDON: AC2 <decision|failed|stuck> <理由；decision 时写 问题/选项/默认；failed 写三轮各做了什么；stuck 写试过哪些路>

VERIFIER (<模型家族>, <sha>): <裁决> for AC…
Sub-issues opened: #<n> (<一句话>), …
Counts: met k / unmet m / abandoned n
```

规则：未过的标准保留原文，不改写、不删；`ABANDON:` 列首、一条标准最多一行；`unmet` 而无 `ABANDON:` 只在会话被截断时合法，正常收尾时每条标准要么 met 要么 abandoned（unlazy `SKILL.md:82`）；`Counts:` 在写完后重数一遍再填。

### 7.2 票的开关规则

| 情况 | 动作 |
| --- | --- |
| 首行 `ALL MET` | `gh issue close <n> --reason completed`（`implement/SKILL.md:24` 现有三步之三） |
| 首行 `HANDOFF REQUIRED` | 不关；不关 PR |
| spec / parent 票 | 永不由 implement 关（`to-tickets/SKILL.md:72`） |
| 夜里开的 sub-issue | `gh issue create --parent <spec 号> --label needs-triage`；不给 `ready-for-agent`，因为 `to-tickets/SKILL.md:61` 的用户批准这一步没走过 |
| sub-issue 后来发现多余 | 人关，`--reason "not planned"` |

### 7.3 标签规则

| 转移 | 谁 | 何时 |
| --- | --- | --- |
| `ready-for-agent → ready-for-human` | implement | 首行写 `HANDOFF REQUIRED` 的同一步 |
| `ready-for-human → ready-for-agent` | 人 | 答了 decision、修好 blocked、或改了票之后 |
| `ready-for-human → wontfix` | 人（走 triage） | 决定不做 |
| 认领 | implement | 开工第一步 `--add-assignee @me`；收尾不摘，留给早上第三条查询 |

`ABANDON:` 行由谁写：worker 写 `decision`（只有它知道拿不准）与 `stuck` 里「任务内做不到」那一半；`failed` 与 `stuck` 里「跑不起来」那一半由收尾者根据自跑轮数、code-review 轮数或 verifier 裁决写——单会话里这仍是同一个 agent，但它抄的是 verifier 那一行，不是自己的判断。verifier 本身不改票的勾、不写 `ABANDON:`，只留 `VERIFIER` 行（pstack「a verifier overrides it on the same key」在票上的形态就是这一行盖过上面的勾）。

### 7.4 完整示例

票 #42「登录页支持 magic link」，四条验收标准，夜间无人看守，UI 截图 diff 非零，code-review 第二轮剩一条票内发现：

```
HANDOFF REQUIRED: 2 abandoned (failed, decision), 0 unmet, 2 met of 4
Branch: feat/42-magic-link  Commit: 3f9c2e1a  PR: #57

- [x] AC1: POST /api/login 收到已注册邮箱返回 202 且 body 为 {"sent":true}
  CHECK: npm test -- src/auth/magic-link.spec.ts
  EXPECT: 4 passed
  EVIDENCE: exit 0; matched "4 passed"; 3f9c2e1a
- [x] AC2: 未注册邮箱返回 202 且不发信（防枚举）
  CHECK: npm test -- src/auth/magic-link.spec.ts -t "unknown email"
  EXPECT: 1 passed
  EVIDENCE: exit 0; matched "1 passed"; 3f9c2e1a
- [ ] AC3: 链接 15 分钟后失效，页面显示「链接已过期，重新发送」
  CHECK: npm test -- src/auth/magic-link-expiry.spec.ts
  EXPECT: 2 passed
  EVIDENCE: exit 1; output "1 passed, 1 failed: expected 'link expired' got 'invalid token'"
ABANDON: AC3 failed code-review 第二轮仍报「过期与无效走同一分支」（Spec 轴，引 spec §Implementation Decisions 4）；两轮上限已到
- [ ] AC4: /login 在 375px 与 1280px 两个宽度下与 prototypes/login/42/UI/ 胜出 variant「inline-form」一致
  EVIDENCE: manual; 两个宽度各截图，1280px diff 非零（按钮下沿 6px），基线/实现/diff 三图见上一条评论
ABANDON: AC4 decision 1280px diff 6px 是否接受？选项：A 接受并关闭；B 按基线改。无人答复默认 A（Seam: 人眼，设备见票 Seam 段）

VERIFIER (claude-haiku, 3f9c2e1a): unit-test-verified for AC1, AC2; verifier-failed for AC3; AC4 manual, not run
Sub-issues opened: #58 (契约装不下：spec 没说重发按钮的冷却时间，实现暂用 60s), #59 (code-review 票外发现：login.tsx 里旧的密码登录分支未删)
Counts: met 2 / unmet 0 / abandoned 2
```

随后执行：`gh issue edit 42 --remove-label ready-for-agent --add-label ready-for-human`；票 #42 与 PR #57 保持打开；被 #42 block 的 #43、#44 不动。早上 `gh issue list --state open --label ready-for-human` 列出 #42，读最后一条评论的两行 `ABANDON:` 就知道要做两件事：决定 AC4 的 6px，看 AC3 为什么两轮没修好。

## 8. 未读 / 未确定

- 未读：`unlazy/references/parallel.md`、`method.md`、`token-economy.md`、`templates/`、`scripts/lib/gates.mjs`（`gateState` 的具体实现，`stop-hook.mjs:9` 引用；本文对 `unmet-no-evidence` 的解释来自 `stop-hook.mjs:125` 的用法而非定义处）。
- 未读：`pstack/skills/poteto-mode/playbooks/autonomous-run.md`、`babysit.md`（`orchestrate.md:83` 说 babysitter「report conflicts to the stacker rather than restacking」，可能有别的失败词）；`scripts/orch/orch.ts` 不在快照里，`orch inbox push <status>` 的合法 status 集合未核实。
- 未读：`grok-bundled/shared/personas/implementer.md`、`reviewer.md`（`wontfix` 的书写要求可能在那里）。
- 未读：swarm-forge 各角色 prompt 和 `handoffs.prompt`、`workflow.prompt`；`README.md:137` 的 Reject 之后 specifier 怎么写才算重新提交没看到。
- 未确定：verifier 裁决 `verifier-failed` / `verifier-blocked` 之后，worker 是否再得一轮修复再验，还是直接 HANDOFF。pstack 是「fix unit, not a re-verify」（`orchestrate.md:91`），即修完要重新裁决；本文示例按「code-review 两轮」的同一上限写成直接 HANDOFF，两者取一要定。
- 未确定：`decision` 类 HANDOFF 用 `ready-for-human` 还是 `needs-info`。本文取前者，理由是 `triage-labels.md:8` 把 `needs-info` 定义为等 reporter；若用户觉得「等我回答」和「要我动手」该分开看，需要第六个标签或改 `needs-info` 的含义。
- 未确定：UI 票在无人看守下按 `00-synthesis.md:53` 的规则（diff 非零贴图给人看）几乎必然以 `decision` HANDOFF 收尾；这是规则的直接后果，不是缺陷，但意味着夜间跑 UI 票的「完成率」天然不为 100%，报告时要按 kind 分开数。
- 未确定：`implement` 开工认领（`--add-assignee @me`）不在现行 `implement/SKILL.md` 里；§5.4 第三条查询依赖它。加不加属于 `implement` 改动，与本文其他建议一起决定。
- 未确定：评论首行的两个大写词能否被 `gh issue list --search` 稳定命中（GitHub 搜索对评论正文的索引有延迟）；没有实测。

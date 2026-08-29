# 关票前的独立只读 verifier

问题：`00-synthesis.md` §「三份报告共同推荐、无分岔的改法」表中「谁来判」一行取自 pstack：收尾前插一个只读 verifier，重跑 `CHECK:`，按 commit SHA 写一行裁决，覆盖 worker 自报。本文把这个机制研究透，让用户能回答三件事：要不要加 verifier；加了它做什么、不做什么；宿主不支持时怎么办。

路径约定：参考快照的路径都相对 `docs/research/code-landing-refs/`；本仓自己的文件相对仓库根。`file:12-15` 指该文件第 12 到 15 行。`CHECK:` / `EXPECT:` / `EVIDENCE:` 是 `03-post-landing-evidence-review.md` §6 候选 A 采自 unlazy 的验收标准写法，本文假定它已进票。

## 1. 一句话结论

值得加，但只在两种票上派：有 `manual` 验收条目或 `## Seam` 指向跑起来的界面的票，以及无人看守跑的票；其余票由 worker 自己重跑 `CHECK:` 并把裁决行标成 `self-reported`。verifier 只做一件事：在最终 commit SHA 上重跑票上每条 `CHECK:`，按 pstack `orchestrate.md:91` 的五个裁决词写一行到票评论，键是 SHA；它不评代码，不提新标准，不修东西。它和 `code-review` 互补不重叠：`code-review` 的两个 sub-agent 读 diff 和 spec 文本、不执行代码（`mmw-v2/upstream/skills/engineering/code-review/SKILL.md:60-70`；技能本身只跑 `git diff` / `git log` / `git rev-parse`，`:21-23`），verifier 跑命令、不读 diff 的好坏。顺序是先 `code-review`、再 commit 最终 SHA、再 verifier，因为裁决绑 SHA，任何后续修改都作废它。

## 2. pstack 的 verifier 到底做什么

pstack 有三处写 verifier，对象不同但机制一致：`orchestrate.md` 的 program 级 verifier unit、`shipping.md` 的每 PR 独立验证、`autopilot-full.md` 第 4 步的 swarm 验证。

### 2.1 输入

| 输入 | 出处 | 内容 |
| --- | --- | --- |
| brief 全文 | `pstack/skills/poteto-mode/playbooks/orchestrate.md:41-52` | `GOAL / SCOPE / CONTEXT / ACCEPTANCE / VERIFY / TIMEBOX / FORBIDDEN / REPORT / STANDING` 九个字段；「a field you cannot fill is a unit you have not scoped yet」（`:38`）。verifier 是 worker 的一种（`:19` 把两者写成同一角色「Worker / verifier」），拿的是同一模板 |
| `VERIFY` 字段 | `orchestrate.md:46` | 「exact commands or the control-skill path, plus known gotchas」。命令或驱动 app 的 control skill 路径，二选一 |
| PR head SHA | `orchestrate.md:91`；`autopilot-full.md:8` | 裁决的键。autopilot 写「At the owner's merge-ready head SHA, fan out parallel independent verifiers」 |
| control skill | `orchestrate.md:19`；`autopilot-full.md:8` | `control-ui` / `control-cli`，来自 `cursor-team-kit`，不在快照里。需要本机时 verifier 才跑 local，否则 cloud（`orchestrate.md:19`） |
| 上游报告 | `orchestrate.md:43-44` | `CONTEXT` 要求「upstream reports pasted in full when this unit depends on them, because workers cannot see siblings」 |

### 2.2 动作

`autopilot-full.md:8` 把 verifier 的动作写成三条 lane，是三处里最具体的：

1. 「re-run the gates at that SHA」——在 SHA 上重跑门禁。
2. 「prove the load-bearing behavior live on the real surface the change touches」——在改动触及的真实界面上活验承重行为。「The live lane is the floor, and a verdict without it is not clean」。
3. 「audit the receipts and the diff, distrusting the PR body」——审收据和 diff，不信 PR 正文。

`shipping.md:7` 的版本：「each exercising the real surface (`control-ui` or `control-cli` from `cursor-team-kit` as the change demands) against parent versus head」——拿 parent 和 head 各跑一遍对比。

verifier 不做的事，pstack 写在角色定义里：worker「never rebase and never run `gt`」（`orchestrate.md:83`）；`FORBIDDEN` 字段固定含「no fixes outside scope」（`:48`）；`verifier-failed` 「gets a fix unit, not a re-verify」（`:91`），修复是另一个 unit，不是 verifier 顺手做。

### 2.3 输出

`orchestrate.md:91`：`ledger.tsv`「one row per verdict, keyed by PR number plus head SHA」，值域五个词。pstack 只给了词和三条使用规则，没有逐词定义；下表的定义列是本文按 `orchestrate.md:91`、`autopilot-full.md:8`、`docs/guide/06-verify-and-ship.md:17-23` 推出的，用户采纳时要把它当成本仓自己的定义写进技能。

| 裁决词 | pstack 原文给的约束 | 本文推出的定义 |
| --- | --- | --- |
| `live-ui-verified` | 是「Behavioral work needs better than `type-check-only`」能满足的最高档；autopilot 说 live lane 是 floor | 在跑起来的 app 里走过改动的流程（`06-verify-and-ship.md:20`「A UI change walks the changed flow in the running app」），且所有 `CHECK:` 通过 |
| `unit-test-verified` | 同上，中间档 | 所有 `CHECK:` 通过，但没有在跑起来的界面上走流程。本文自定：`## Seam` 不在界面层的票（`06-verify-and-ship.md:19`、`:21`、`:23` 列的 CLI、解析器、存储那类改动，它们的「真制品」是命令、输入回放、读回的值）拿这一档算过；这与 `autopilot-full.md:8`「The live lane is the floor」不同，那句针对的是必须过 UI 的 PR |
| `type-check-only` | 「Behavioral work needs better than `type-check-only`」 | 只有类型检查或构建通过；有行为改动的票拿这一档不算过 |
| `verifier-blocked` | 「is not a pass; respawn when the environment heals」 | 至少一条 `CHECK:` 跑不起来（依赖、端口、凭证、control skill 缺），不是代码错。结局是环境好了重派，不是修代码 |
| `verifier-failed` | 「gets a fix unit, not a re-verify」 | 跑起来了，至少一条 exit 非零或 `EXPECT:` 不匹配。结局是修复，修完是新 SHA，新 SHA 再验 |

`shipping.md:7` 用的是另一套三值 `PASS / PASS+NOTES / FAIL`，「posts that verdict on its own PR so the record outlives the chat」；`swarm/SKILL.md:34` 的 worker 报告用 `PASS / ISSUES / BLOCKED`。三套词并存说明 pstack 没有统一，`orchestrate.md:91` 那套最细，本文取它。

### 2.4 覆盖规则

`orchestrate.md:91` 三句：

- 「A worker may self-report; a verifier overrides it on the same key.」worker 可以自报同一 SHA 的裁决，verifier 的行覆盖它。
- 「A new head SHA voids the row, so re-verify after restack.」换 SHA 作废。`shipping.md:9` 补了一个例外：比较 `git patch-id`，patch 内容没变才可沿用旧裁决；「Twenty-one verdicts went stale this way in one run with no signal at all」是它踩过的坑。
- 「CI green is an input to a verdict, not a verdict.」`shipping.md:7` 同义：「CI green is not a verdict, and an approving bot review is not a verdict」。

`orchestrate.md:93` 还要求裁决落地即外化：「a verifier writes its ledger row, receipts land in the store. Work that exists only on one VM when that VM dies was never done.」

## 3. 「不同模型家族」的理由与证据

### 3.1 pstack 怎么说

- `orchestrate.md:19`：「Run a unit's verifier on a different model family from its worker.」一句话，没有理由。
- `show-me-your-work/SKILL.md:67`：「you must spawn a subagent on a different model family from the one that did the work. Self-review is not a substitute; the point is fresh eyes you cannot bring yourself.」理由是「你自己带不来的新眼睛」。
- `blast-radius/SKILL.md:38`：「Ask several models the same question and merge the answers. Different models catch different real bugs.」
- `setup-pstack/SKILL.md:22`：`arena cross-judge pool` 「selects one value from it whose model family differs from the parent's when possible」——「when possible」说明 pstack 自己也把它当尽力而为，不是硬门。
- `docs/guide/06-verify-and-ship.md:85`：「the agent that judges a change is never the one that wrote it」——这句强调的是「不是写码那个 agent」，不是家族。

### 3.2 有没有数据

没有。§3.1 列的五处 pstack 原文关于家族的话都是断言。pstack 给出的实测数字有两个，都不是家族的收益：`shipping.md:9` 的「Twenty-one verdicts went stale」说的是换 SHA 作废；`orchestrate.md:3` 说的是 ceremony 的代价，方向相反：「measured head-to-head, this playbook's ceremony turned a half-hour 12-unit job into 1 landed unit while a plain agent landed all 12」——是 ceremony 的代价，不是 verifier 的收益。所以「不同家族」在本仓只能当偏好，不能当理由；能站住的最低要求是 `06-verify-and-ship.md:85` 那句：判的不是写的那个。

### 3.3 我们的宿主各能否指定不同模型的子代理

`mmw-v2/agents/assemble.py:8-13` 定义了五个宿主的 subagent 文件格式，每个都带 `model` 字段；`mmw-v2/install.sh:222-228` 列出六个安装点（五个宿主的 agent 目录加 `~/.grok/roles`），其后的循环把成品软链过去。任务问的是三个宿主，下表按 assemble.py 的五个列全，前三个是问的。

| 宿主 | 能否指定子代理模型 | 能否指定不同家族 | 只读怎么做 | 出处 |
| --- | --- | --- | --- | --- |
| Claude Code | 能。Agent 工具有 `model` 参数，值域 `sonnet / opus / haiku / fable`；agent 定义文件 frontmatter 有 `model` | 不能。四个值全是 Anthropic 模型 | 定义文件 `tools` 列表（`assemble.py:59`），现有三个 agent 都是 `Read, Grep, Glob, Bash` 或只 `Read`（`mmw-v2/agents/*/agent.json`） | 本会话 Agent 工具说明；`assemble.py:53-60` |
| Grok Build | 未确定。对照课写本机 `16-subagents.md`「还允许设 `model` / `reasoning_effort` / `default_isolation`」，但它把这三个字段放在 persona 文件 `~/.grok/personas/reviewer.toml` 上，没写 `~/.grok/agents/` 的定义文件也能设；`assemble.py:80-85` 的 `grok.md` frontmatter 带 `model`，是否生效没有实测 | 未确定。`~/.grok/config.toml` 的 `[model.my-model]` 能接任意端点，但对照课没写子代理能否指到它 | roles 文件 `default_capability_mode = "read-only"`（`assemble.py:88`）；内置 `explore` 类型只读，但两份官方文档对它有没有 shell 说法打架 | `docs/research/grok-build-vs-claude-code.html:729-733`、`:1240-1243`、`:1270-1274` |
| Codex | 定义文件带 `model` 与 `model_reasoning_effort`（`assemble.py:70-78`），现有 agent 写 `gpt-5.6-sol` | 未确定。本仓没有 Codex 子代理文档快照；只能从我们自己的定义格式推断它接受 `model` 字段 | `sandbox_mode = "read-only"`（`assemble.py:76`） | `assemble.py:70-78`；`mmw-v2/agents/*/agent.json` |
| Cursor | 定义文件 `model: <slug>[effort=…]`；pstack 自己就在 Cursor 上跑，`setup-pstack/SKILL.md:39-56` 列了 Claude、GPT、Grok 三家 slug | 能。Cursor 一个宿主里就有三家模型 | `readonly: true`（`assemble.py:67`） | `assemble.py:62-68`；`setup-pstack/SKILL.md:14`、`:39-56` |
| pi | 定义文件 `model: <provider>/<id>`，现有 agent 写 `openai-codex/gpt-5.6-sol` | 能。pi 按 provider 前缀切家族；`docs/research/cursor-pi-cli/subscription-into-pi/report.md:79-81` 说 `/model` 里可挑 `cursor/<id>` | `tools` 列表（`assemble.py:98`） | `assemble.py:92-99`；上述 report |

结论：Claude Code、Cursor、pi 能给子代理指定模型，Grok Build 和 Codex 未确定；「不同家族」只有 Cursor 和 pi 天然做得到，Claude Code 做不到。所以技能正文不能写「不同模型家族」，只能写「能选模型时选一个和自己不同的」。现有 agent 也只做到这一步：`mmw-v2/agents/claim-checker/agent.json:5-21` 在 Claude 上用 `opus`、Cursor 上用 `cursor-grok-4.6`、Codex 上用 `gpt-5.6-sol`、Grok 上用 `grok-4.6`——除 Cursor 外都是该宿主自家家族里的另一个具体模型，不跨家族。

## 4. verifier 与 `code-review` 的分工

### 4.1 「code-review 读、verifier 跑」是否成立

成立，限定在两个 sub-agent 上；技能本身在 `code-review/SKILL.md:21-23` 跑的只有 `git diff` / `git log` / `git rev-parse`，不跑被审的代码。`:66-70` 的 Spec sub-agent brief 只给「The diff command and commit list」和「The path or fetched contents of the spec」，任务是「Report: (a) requirements ... missing or partial; (b) ... scope creep; (c) requirements that look implemented but where the implementation looks wrong」——三项全是读出来的判断，没有一条要求执行。Standards sub-agent 同样只拿 diff、标准文件和粘贴进去的 smell baseline（`:60-64`）。`03-post-landing-evidence-review.md` §2「不信自报的机制」行已指出这点：「Spec sub-agent 只读 diff 与 spec 文本，不跑任何东西」。

verifier 反过来：输入是票上的 `CHECK:` / `EXPECT:` 和 SHA，动作是执行，输出是每条的 exit 与匹配结果加一行裁决。它不看 diff 好不好、不看有没有 scope creep、不看 smell——那些是 `code-review` 两轴的事。

两者唯一的重叠是 Spec 轴的 (c)「看似实现但错」：`code-review` 靠读推测「looks wrong」，verifier 靠跑证明「is wrong」。重叠是好事：读能抓到没写 `CHECK:` 的需求，跑能抓到读不出来的运行时错。

### 4.2 与本仓记忆的关系

Nowledge Mem 记忆 `456d6f5e-4eae-4512-a0f4-acffcc5edd86`「Reviewer must not self-set pass criteria in agent-in-the-loop workflows」：reviewer 只能对票的验收门和 spec 业务对齐判定，范围外的发现只记录不阻塞。verifier 的设计天然满足这条：它的判定依据全部来自票上事先写好的 `CHECK:` / `EXPECT:`，没有自设标准的空间；它发现的任何「票外」问题都不进裁决行。grok 的 reviewer 循环（`grok-bundled/implement/SKILL.md:758-762`「The only exit condition is all reviewers reporting 0 issues ... There is no iteration cap」）正是记忆里被否决的形态，本文不取。

### 4.3 顺序

先 `code-review`，再 commit 最终 SHA，再 verifier。理由只有一个：裁决绑 SHA（`orchestrate.md:91`「A new head SHA voids the row」）。`00-synthesis.md` §「第一轮之后已定的事」已定 `code-review` 「最多两轮」，且第一轮发现会引起修改；verifier 若跑在前面，修改一次就白跑一次。反过来 verifier 之后再改代码，就必须重派 verifier。

verifier 失败后的回路要有界，和 `code-review` 的两轮一样：`verifier-failed` → 修 → 新 SHA → 再派一次；第二次仍 `verifier-failed` 或任何一次 `verifier-blocked`，票不关，评论首行 `HANDOFF REQUIRED`（`03` §6 候选 D）。grok 自己也把无界循环兜成「Escalate, don't spin — if the implementer and a reviewer cannot reach consensus on an issue after two rounds, escalate to the user」（`grok-bundled/implement/SKILL.md:1005`）。

## 5. ceremony 代价：什么规模的票才值得派

### 5.1 pstack 的界线

- `orchestrate.md:89`：「When VERIFY is a single cheap command, the worker runs it and reports the output, and the coordinator spot-checks receipts; a dedicated verifier agent ... is for units whose verification is expensive, judgment-laden, or high-blast-radius. A verifier agent whose entire product would be rerunning one command is ceremony, not verification.」
- `orchestrate.md:64`：「The dedicated pilot pipeline (separate verifier agent, audit gate) is for expensive or novel unit shapes, not for clone-units」。
- `orchestrate.md:3`：ceremony 的实测代价见 §3.2。
- `orchestrate.md:72`：「a completion that needs review becomes a verifier unit」——不是每个 completion 都需要。
- unlazy 同样的话：「use it for attention isolation, not ceremony」（`unlazy/references/orchestration.md:99`）。

pstack 的三个触发词是 expensive、judgment-laden、high-blast-radius。对应到我们的票，能机器判的只有前两个的代理指标；第三个要看 `Owns:`。

### 5.2 判定规则（提议）

票满足任一条就派 verifier；一条都不满足，worker 自己在最终 SHA 上重跑全部 `CHECK:`，裁决行标 `self-reported`：

1. 验收标准里有 `manual` 条目（写不出 `CHECK:` 的），或 `## Seam` 指向跑起来的界面——这是 judgment-laden。
2. 票是无人看守跑的（没有人在会话里看输出）——没有人抽查收据，`orchestrate.md:89` 的「coordinator spot-checks receipts」这一层缺失，只能用 verifier 补。
3. `Owns:` 触及迁移、鉴权、对外接口或多张票共用的路径——这是 high-blast-radius。
4. `CHECK:` 合计要跑起 app、起数据库或超过一条命令能跑完——这是 expensive。

第 2 条是我们和 pstack 最大的差异：pstack 的 coordinator 是活的会话，`00-synthesis.md` §「三份报告一致指出的根因」末行说我们的症状正是「无法无人看守」。无人看守的票，verifier 不是 ceremony，是唯一的第二双眼。

一条命令、一个人看着跑的票，不派。

## 6. 宿主不支持时的降级

三层，按能力判断，不按宿主名：

| 宿主能做到的 | 做法 | 裁决行的 `by` 字段 |
| --- | --- | --- |
| 能派一个不能改文件的子代理，且能给它指定模型 | 派 verifier，模型选一个和自己不同的 | `<model>`，例如 `by opus` |
| 能派不能改文件的子代理，不能指定模型 | 派 verifier，同模型也派——新上下文、没有写码记忆，仍满足 `06-verify-and-ship.md:85`「the agent that judges a change is never the one that wrote it」 | `<model>`（和自己相同也如实写） |
| 不能派子代理 | worker 自己在最终 commit 之后从干净 shell 重跑每条 `CHECK:`，逐条记 `EVIDENCE:`；裁决行的档位照实写，`by` 写 `self-reported` | `self-reported` |

`self-reported` 的票能不能关：只在所有验收条目都是可跑的 `CHECK:`、且全部通过时关；有 `manual` 条目又没有独立 verifier 的，票不关，首行 `HANDOFF REQUIRED`，因为 `manual` 条目的判断本来就是 verifier 存在的理由（§5.2 第 1 条）。

技能正文的措辞样例（一份，不分宿主）：

> 收尾前，在最终 commit 上重验票的每条 `CHECK:`。如果你能派一个不能编辑文件的子代理，派它去做，能选模型就选一个和你自己不同的，把下面的 brief 原样给它；如果不能派子代理，自己从新的 shell 里逐条重跑，裁决行的 `by` 写 `self-reported`。

「只读」的含义要说清：现有三个 agent 的只读靠两类机制——Claude 和 pi 是 `tools` 列表（`assemble.py:59`、`:98`），Cursor、Codex、Grok 是 `readonly` / `sandbox_mode` / `default_capability_mode` 开关（`:67`、`:76`、`:88`）。但 verifier 必须有 shell 才能跑 `CHECK:`，而 shell 能写文件，Codex 的 `sandbox_mode = "read-only"` 之外的宿主开关拦不拦 shell 写文件本仓没有核对。这三处后来由 `agent.json` 顶层键 `sandbox` 决定，缺省仍是只读（`12-decisions.md` G7）。所以 verifier 的只读是两层：定义文件上不给编辑工具或开只读开关；body 里 `FORBIDDEN` 写明不改文件、不 commit、不修，并要求它在开始和结束各跑一次 `git status --porcelain` 贴进报告，两次都为空才算干净。

## 7. 裁决写到哪、什么格式

### 7.1 位置

票评论。理由是 `shipping.md:7`「posts that verdict on its own PR so the record outlives the chat」和 `orchestrate.md:91`「The ledger answers "was this verified", not memory and not the transcript」——本仓没有 `ledger.tsv`，票在 GitHub Issues 上、全部操作走 `gh`（`AGENTS.md` §「Issue tracker」），任何宿主的任何会话都读得到。`implement/SKILL.md:22` 已经要求在票上评论证据，裁决行放进同一条评论。PR 引用票（`:23`），不必再抄一遍。

### 7.2 格式（提议）

一行，键是 commit SHA，放在收尾评论的第一行（有 `HANDOFF REQUIRED` 时放第二行）：

```
VERDICT <full-sha> <level> by <model|self-reported> — <一句话：什么跑了、什么没跑>
```

`<level>` 取 §2.3 的五个词。例：

```
VERDICT 3a9f1c2e… unit-test-verified by opus — 6/6 CHECK 通过；Seam 是 API 层，未起 UI
VERDICT 7c21e0a4… verifier-blocked by fable — CHECK 3 需要 POSTGRES_URL，环境里没有
```

后面跟每条验收标准的 `EVIDENCE:`（`03` §6 候选 A），由 verifier 写；worker 先前自报的勾按 verifier 的结果改，这就是 `orchestrate.md:91`「a verifier overrides it on the same key」在票上的形态。

同一张票上出现多行 `VERDICT`，SHA 不同的旧行自然作废；SHA 相同的以最后一行为准。

### 7.3 与已定规则的衔接

- `code-review` 最多两轮（`00-synthesis.md` §「第一轮之后已定的事」末行）：两轮跑完、修完、commit 之后才派 verifier。第二轮仍有票内发现 → 票已经不关，verifier 可以跳过（省一次派发），评论首行 `HANDOFF REQUIRED`。
- `HANDOFF REQUIRED`（`03` §6 候选 D）：`verifier-blocked`、第二次 `verifier-failed`、`self-reported` 遇到 `manual` 条目——三种情况都进这条通道。候选 D 的 `ABANDON:` 是 worker 主动放弃某条标准；verifier 不写 `ABANDON:`，它只写自己的档位。评论末尾的 met / unmet / abandoned 计数由 worker 按 verifier 结果填。

## 8. 建议：收尾几步、brief 长什么样

### 8.1 收尾步数

`implement/SKILL.md:18-24` 现在是 `/code-review`（`:18`）→ commit（`:20`）→ 三步（评论、push+PR、关票，`:22-24`）。提议改成五步，第 2 步是新的：

1. `/code-review`，最多两轮，修完 commit；记下最终 SHA。
2. 在最终 SHA 上重验：按 §6 的能力判断派 verifier 或自己重跑，拿到 `VERDICT` 行和每条 `EVIDENCE:`。
3. 在票上评论：`VERDICT` 行、分支、SHA、每条验收标准的 `EVIDENCE:`，只勾 verifier 判过的。
4. push 分支，开引用票的 PR。
5. 裁决是 `live-ui-verified` 或 `unit-test-verified`、没有 `ABANDON:`、没有 `manual` 条目落在 `self-reported` 上 → 关票；否则票不关，评论首行 `HANDOFF REQUIRED`。

`verifier-failed` 回到第 1 步之后的修改，再走第 2 步，只走一次。

### 8.2 verifier 的 brief（最小字段）

对照 `orchestrate.md:41-52` 的九个字段，去掉我们没有的（`STANDING` 常驻规则、`TIMEBOX` 是 `00-synthesis.md` §「这轮明确不动的」列的无人看守议题），并按 `orchestrate.md:54`「Size the brief to the unit」压成一段：

```
TICKET      <issue URL>；以下验收标准原文粘贴，不要自己去读票
SHA         <full-sha>，分支 <name>，worktree <绝对路径>
ACCEPTANCE  每条验收标准 + 它的 CHECK: / EXPECT:（或 manual + 看什么制品），原样粘贴
SEAM        票的 ## Seam 原文；需要起 app 时，spec Testing Decisions 里的启动命令
FORBIDDEN   不改文件、不 commit、不修、不加新标准；开头和结尾各跑一次 git status --porcelain
REPORT      第一行 VERDICT <sha> <level> by <你的模型>；然后每条标准一行：id、exit、EXPECT 匹配与否、输出前 200 字；最后两次 git status 的输出
```

要点：

- `ACCEPTANCE` 粘贴原文而不是让它读票，对应 `orchestrate.md:43-44`「workers cannot see siblings」和现有 `ui-evaluator/agent.json:3`「Your prompt must carry everything it judges」的做法。
- 不给 diff、不给 spec、不给 prototype——给了它就会去评代码，那是 `code-review` 的事（§4.1）。
- `by <你的模型>` 要它自报，对应 `show-me-your-work/SKILL.md:74`「Lead with the reviewer's model on its own line (`reviewed by <model>`)」。

### 8.3 落成一个 subagent

按 `mmw-v2/agents/` 现有的样子加第四个目录 `verifier/`：`agent.json` 五个宿主的 `model` 各选一个和该宿主写码常用模型不同的；Claude 和 pi 的 `tools` 给 `Read, Grep, Glob, Bash` 与 `read, grep, find, ls, bash`（shell 是跑 `CHECK:` 必需的），Cursor、Codex、Grok 没有 `tools` 字段，它们的开关由 `agent.json` 顶层键 `sandbox` 决定（`12-decisions.md` G7）；`body.md` 写 §2.2 的动作、§2.3 的五个词定义、§6 末段的两次 `git status` 要求、§8.2 的 REPORT 格式。`implement/SKILL.md` 第 2 步只写「派 verifier subagent」和降级句，不重复 body 内容。这样宿主差异全部落在 `agent.json`，技能正文对所有宿主是同一份。

## 9. 未读或未确定

- 已核实（2026-08-29，落地 #69 时各真派一次）：Codex 与 Grok Build 的子代理**都**按定义文件里的 `model` 字段切模型——Codex 的会话记录里 `turn_context.model` 是 `agent.json` 写的 `gpt-5.6-terra`，Grok 的子代理跑的是 `grok-4.5`。另记：Codex 的父会话自己在 `workspace-write` 下起不了子代理（`failed to initialize in-process app-server client`），要 `danger-full-access`。（`12-decisions.md` G7）
- 未确定：Grok Build 的 `[model.my-model]` 自定义端点（`grok-build-vs-claude-code.html:1270-1274`）能否被子代理定义引用；能的话 Grok 也可以做到不同家族。
- 未读：`pstack/skills/poteto-mode/playbooks/babysit.md`、`opening-a-pr.md` 全文；`pstack/skills/create-verification-skill/` 与 `maintain-verification-skill/` 全文——live lane 的具体驱动方法在那里。
- 未读：`cursor-team-kit` 的 `control-ui` / `control-cli` 不在快照里（`03` §8 已列）；我们的 live 验证要靠 `playwright-cli` 技能，其能力仍未核对（`00-synthesis.md` §「先于一切要定的前提」第 3 条）。
- 未确定：`shipping.md:9` 的 `git patch-id` 例外（patch 不变则旧裁决可沿用）要不要采。我们的票是单分支不 restack，SHA 只在修改后才变，暂时不需要；若将来在 PR 上 rebase 再决定。
- 未确定：五个裁决词的定义（§2.3 表第三列）是本文推的，pstack 没写；采纳时按本仓的 `## Seam` 层次校一遍。

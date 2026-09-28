# to-questionnaire

## 定稿（主 agent 复核）

**判断**：正文与上游一致，灵魂完整。本仓把它改成模型可触发，却没补触发句，这一处必须修。另有一句上游文档页写了、技能正文没写的判断，写进正文。

### 增加与修正

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | frontmatter `description` | Turn a decision the user can't settle alone into a questionnaire for the one person who holds what is missing. Use when a decision or a grilling round is blocked on knowledge that lives in someone else's head (a client, a domain expert, a colleague), not in the user's or the codebase. | 现在的模型可触发技能里只有它没有 "Use when" 句，宿主判断不了何时加载；原句中的 "you" 还可能被读成 agent 自己。改完要开新会话才生效；merge-note 加对应一行。 |
| I2 | `SKILL.md` 正文，写问题那一步之后（本仓加，merge-note 记一条） | The user's open questions are rarely the ones to send. Recast each into something the recipient can answer from their own position and in their own words, and keep the link back to the decision it serves. | 没有它，问卷会把你自己的问题原样发出去，对方从自己的位置答不了。上游文档页写了这条，但 agent 读不到文档页。没有使用记录，属推断。 |

### 不采纳

- "第 1、2 步在对话已回答时仍要问"的修改：改上游原文，且没有使用记录。

## 结论

技能只有一个文件 `mmw-v2/upstream/skills/productivity/to-questionnaire/SKILL.md`，正文 468 词（`wc -w`），另有 3 行的 `agents/openai.yaml`，没有 reference、没有脚本。与最新上游 squash 提交 `5b1a4c51` 比，本仓只删了两处开关（`SKILL.md` frontmatter 的 `disable-model-invocation: true` 与 `agents/openai.yaml` 的 `policy` 整块，由提交 `5181acc2` 做，`mmw-v2/merge-notes/to-questionnaire.md` 登记），正文一个字没改。A 类没有可删的内容：没有复述脚本、没有历史注记、没有过度防御，模板内联是 `SKILL-SET-REVIEW.md` `## Upstream examples` 表里点名的正例，估计可删 0 词。"灵魂"基本完整："Grill the send, not the subject" 一段和每一步附带的理由都在。唯一实质问题出在本仓自己的改动上：开关删了，技能变成模型可触发，但 `description` 没补 "Use when" 触发句，它是本仓全部已安装、模型可触发的技能里唯一没有触发句的一个。

## A. 删除或改成脚本

无。逐段读过，理由如下，免得下一轮把"没发现"当成"没查"：

- 没有脚本可替代的内容：唯一的确定性动作是把文件写到 `to-questionnaire-<slug>.md` 并报告路径（`SKILL.md` 第 3 步），一句话，不值得脚本化。
- 没有 agent 不需要的内容、没有历史碎碎念（无日期、issue 号、"no longer/now"）。
- `## Document structure` 的 "Order questions most-important-first ... group them under `##` headings by theme" 与模板里 "One `##` section per theme. Under each, its questions, most-important-first." 意思重复一次。这是上游原文，在 MMW 里不会让 agent 做错，按任务书"为减字数删上游原文，不提"，不列为发现。

## B. 灵魂

### 保留，勿删

- 开头段 "Turn something the user can't answer alone into a **questionnaire** ... the questionnaire pulls it out of them."：交代了这件事的前提（知识在收件人手里，不在用户手里），决定了整份问卷为谁而写。
- "**Grill the send, not the subject.**" 整段：技能的核心动作。没有它，agent 会按 `grilling` 的习惯去追问用户主题本身，而那恰恰是用户答不了的（上游 `docs/productivity/to-questionnaire.md` `## It's working if` 第一条就把"问主题"判为跑偏）。
- 第 1 步 "This fixes the questionnaire's tone and how much context it must carry."：告诉 agent 为什么要问收件人是谁，问的结果怎么用；没有它，第 1 步就成了填表。
- 第 2 步与第 3 步的 "Done when ..." 两句（"a concrete list of what the user must walk away able to do or decide"；"every item the user named in step 2 is covered by a question"）：完成标准，而且是可核对的。
- `## Document structure` 的 "since async means you may only get one pass"：排序规则带着理由，agent 在清单外的情况也能据此判断。
- 模板 `## How to answer` 的 "Partial answers and "I don't know" are useful: flag anything you're unsure of rather than skipping it." 与 "a one-line _why this matters_ only where the question could be misread or invite a throwaway answer"：前者保护回收答案的质量，后者约束篇幅且说明了何时该加。
- `<question-example>`：示例问题问的是收件人能答的事实（launch 时的负载），而不是用户自己的决定（要不要现在为突发流量预留）。它是下面第二个缺口唯一的现有载体。

### 缺口与补充草稿

- `SKILL.md` frontmatter 的 `description`（**本仓改动造成的缺口，建议补**）：现在是 "Turn a decision you can't fully answer into a questionnaire for someone else to fill in."，只说"我是什么"，没有触发句。本仓给其他翻成模型可触发的技能都补了 "Use when"，理由写在 `mmw-v2/merge-notes/wayfinder.md`、`triage.md`、`ask-matt.md` 的 `description` 行："host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它"。逐个核对 `mmw-v2/upstream/skills/*/*/SKILL.md` 中不带 `disable-model-invocation` 的技能，只有这一个没有触发句。后果（推断，无使用记录可证）：它最常见的使用时机是 `grilling` 一轮卡在"这得问客户/问某位专家"上（上游 `docs/productivity/to-questionnaire.md` `## When to reach for it` 称之为 "The common case"），而 `mmw-v2/upstream/skills/productivity/grilling/SKILL.md` 没有指向它的句子，只能靠 description 被扫到；另外 "a decision you can't fully answer" 里的 "you" 在模型读来是 agent 自己，容易被读成"agent 自己答不了的决定就写问卷"，而正文说的是 "the user can't answer alone"。建议改成（放 `SKILL.md` 第 3 行，同时在 `mmw-v2/merge-notes/to-questionnaire.md` 加一行 `description`，写法照 `wayfinder.md` 那行："上游改这一行 → 收上游对前半句的措辞，末句保留"）：
  > description: Turn a decision the user can't settle alone into a questionnaire for the one person who holds what is missing. Use when a decision or a grilling round is blocked on knowledge that lives in someone else's head (a client, a domain expert, a colleague), not in the user's or the codebase.

- `SKILL.md` 第 3 步或 "Grill the send" 段末（**上游原文，可选**）：正文说问题要 "target the **gap**"，但没说出最容易做浅的那一步：用户手里的开放问题通常不能原样发出去，要改写成收件人站在自己的位置、用自己的词汇能回答的问题。在 MMW 里这个风险偏高：技能多半在一次 `grilling` 之后被调用，对话里堆着的是工程术语写成的 frontier 问题，而收件人往往不是工程师。上游在 `docs/productivity/to-questionnaire.md` `## It's working if` 第三条写了这个标准（"The questions read as aimed at what the *recipient* knows, not as your own open questions copied down verbatim."），但那份文档不会被 agent 加载。草稿：
  > The user's open questions are rarely the ones to send. Recast each into something the recipient can answer from their own position and in their own words, and keep the link back to the decision it serves: the example below asks for launch load, not for a provisioning decision.

  这是改上游正文，要在 merge-note 加一行意图；如果坚持"上游原文尽量不改"，这一条可以不做，示例问题已经隐含了这个做法，损失是 agent 只有在注意到示例时才会这样做。

## C. 死板的流程

| # | 位置 | 为什么死板 | 换成什么 |
| --- | --- | --- | --- |
| 1 | `SKILL.md` 第 1、2 步 "Ask, in one exchange, ..."（上游原文，可选） | 无条件要求问两轮。技能被模型在对话中途触发时（本仓翻成模型可触发后，这是主要路径），收件人和要什么往往已经在对话里说过了，照做就是把已知答案再问一遍；用户的既定偏好（Nowledge Mem 记忆 `feedback-ask-only-real-tradeoffs`「只问有真实取舍的问题」）正是反对这种提问。三步的先后顺序本身是真依赖（不知道收件人和需求就没法写），保留。 | 在第 2 步后加一句判断点："If the conversation has already answered either question, say what you took from it and ask only what is still missing." 同样是改上游正文，需要 merge-note 一行；不改的剩余风险是偶尔多问一轮，代价小。 |

模板 `<questionnaire-template>` 是固定格式，但不算死板：它是交给非技术收件人的成品形态，技能的价值之一就是这个形态（上游文档 `## Common questions` 最后一问："the document comes out in a shape a non-technical recipient can actually fill in"），保留。

## 脚本

无。

## 与其他技能的重复或交接问题

- `mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` `## Standalone` 的 to-questionnaire 条目复述了"inverse of grill-me / interviews you about the send"。这是路由器的本职（帮人选技能），to-questionnaire 自己那份用于执行，两边都留。
- 答案回来之后交给谁（再进一轮 `grilling`，或进 `grill-with-docs` / `to-spec`）只写在 `ask-matt` 那一条里，to-questionnaire 正文没写。写问卷的 agent 不需要这条信息就能把问卷写对，所以不建议补进 to-questionnaire，留在 `ask-matt`。
- 上游 `mmw-v2/upstream/docs/productivity/to-questionnaire.md` 写着 "You invoke this by typing `/to-questionnaire`; the agent won't reach for it on its own."，与本仓的模型可触发矛盾。这份文档不被任何 host 加载、也不被本仓技能引用（`grep` 只在上游自己的 README/CHANGELOG/docs 里命中），且属上游原样保留的文件，只记录，不改。
- `mmw-v2/upstream/skills/productivity/grilling/SKILL.md` 没有指向 to-questionnaire 的句子；不建议改 `grilling`（上游），由上面 B 的 description 修正承担发现路径。

## 没查到的

- 没有真实使用证据：`find ~ -maxdepth 5 -name "to-questionnaire-*.md"` 无结果，`nmem --json m search "to-questionnaire"` 无相关记忆，`nmem t search` 命中的一个会话（`claude-code-82475683-…`）没能读出内容（`nmem t show` 输出不是 JSON）。所以 B 与 C 里关于"会让 agent 做错"的判断都是推理，不是观察。
- 夜里的 worker 会不会因为 description 被模型触发而在无人会话里写问卷：没查到发生过；按 `implement` 等技能把问题路由到别处的做法，推断可能性低，上面建议的 description 把触发限定在"用户"答不了的决定上，也收窄了这条路。
- 问卷语言：模板标题是英文（`**Purpose:**`、`## How to answer` 等），给中文收件人时 agent 可能照抄英文标题。没有使用记录可证，未列为发现。

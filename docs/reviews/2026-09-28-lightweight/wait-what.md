# wait-what

## 定稿（主 agent 复核）

**判断**：上游那一句不动。本仓写的 `VISUAL.md` 在两轮改写里丢了一句判断：页面上的名字要用 `CONTEXT.md` 的正式词汇，恢复它。另一处（在自带页面规则的渲染面上两套规则打架）没有观察到实际发生，不加。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `VISUAL.md` 开头 | Every label on the page uses the ubiquitous language of `CONTEXT.md`, because the user carries those names into the next message. | 没有它，页面上会出现 agent 自己起的名字，你带着这些名字回到对话里，又要再对一次词。**推断**：没观察到实际失败；这句在 `d69e75c0`、`8a8db1de` 两轮改写里丢了。 |

### 不采纳

- 渲染面自带页面规则时让位的那句：没有观察到冲突。

## 结论
- **体量**：`mmw-v2/upstream/skills/productivity/wait-what/SKILL.md` 83 词。其中上游原文一句；本仓加了 frontmatter `argument-hint` 和末句 `Tagged \`visual\`: …`。`VISUAL.md` 242 词，全部是本仓写的。`agents/openai.yaml` 17 词。没有脚本。
- **比对结果**：对照上游 squash `5b1a4c51` 和 2026-09-28 取到的上游 `main`，上游那句重讲指令一字未改。
- **可删的**：本仓加的文字里没有可删的。每句要么是这个分支的入口，要么是防误用，要么是思想性内容，估计可删 0 词。
- **成本**：真正的开销在别处。`visual` 分支要求 agent 读 `diagram-design` 的 `SKILL.md`（5,905 词），外加一份类型 reference。这是已做出的设计决定，不重开，只记下成本。
- **灵魂**：大体完整。有两个缺口，都是推断，没有观察到实际失败：
  - `d69e75c0` 与 `8a8db1de` 两轮改写丢了“页面上的名字用 `CONTEXT.md` 的词”这一句；
  - 在自带页面规则的渲染面（例如 Claude Code 的 Artifact）上，页面规则会和 `diagram-design` 的规则打架。

## A. 删除或改成脚本
无。逐段核对 `VISUAL.md`：
- 首句 `The \`visual\` branch of …` 只有几个词，用来给这个分支定位；
- `## Put the page where the user is looking` 下的两条 bullet 是一个真实的判断点：有能渲染 HTML 的工具就用，没有就写临时文件、打开它、给出路径；
- `## Draw the page` 的三句各管一件不同的事：页面的样子交给 `diagram-design`；不画图时也照样交一页；跳过 §3 的确认暂停。

以上都不是 agent 默认就会做的事，也没有复述任何脚本。

## B. 灵魂
### 保留，勿删
- `SKILL.md` 上游那句 `Re-pitch that: give me a little bit of context, talk in ASD-STE100 Simplified Technical English, and use the ubiquitous language …`：三个抓手（补上下文、用简化英语、用统一词汇），就是这个技能的全部方法。
- `VISUAL.md` `Same job as the prose re-pitch (make the thing that did not land land)`：把成功定义为“用户懂了”，而不是“页面做得漂亮”。
- `VISUAL.md` `Explain what was already said. The material is the message the user just stopped you on, not a fresh investigation.`：防止 agent 借机重新调查、扩大范围；也是跳过 §3 确认的理由所在。`e74e0140` 删掉了 §3 那句后面的 `the material is already fixed`，理由现在只留在这里，所以这句更不能删。
- `VISUAL.md` 标题 `## Put the page where the user is looking`：标题本身就是目标，下面两条 bullet 只是例子。新 host 出现时，agent 按这个目标去判断。
- `VISUAL.md` `Where it judges that a table or a sentence does the job better than a picture, put that table or sentence on the page instead.`：`b898a009` 冷跑时发现了缺口后补的，保证这一分支无论如何都交出一页。
- `VISUAL.md` `Skip its §3 "Confirm before drawing" pause and draw straight away.`：没有这句，agent 会按 `diagram-design` `### Confirm before drawing` 先停一轮，让一个已经没看懂的用户再读一条计划。
- `VISUAL.md` `The reader knows nothing about this topic. …` 整段：规定了读者是谁，以及图和字怎么分工。这是这一分支的核心思想。

### 缺口与补充草稿
- `VISUAL.md` 第一段，即 `Same job as the prose re-pitch …` 那句。
  - **缺什么**：`SKILL.md` 里“用 `CONTEXT.md` 的统一词汇”写在散文重讲那一句里，而入口句说 `re-pitch it as one HTML page instead of prose`，agent 可能把 `instead of prose` 读成连那一整句要求也一起替换掉了。
  - **怎么丢的**：旧版 `VISUAL.md` 的 `## Build the page to stand alone` 有 `**Real labels, real data.** Use the names from the conversation and from \`CONTEXT.md\`.`，在 `d69e75c0`（2026-08-23，照抄 show-me）被删；随后 show-me 的 `### guidance` 也在 `8a8db1de` 换成 `diagram-design` 时一起删了。`diagram-design` 的 `SKILL.md` 里没有提到 `CONTEXT.md`（grep 为空）。
  - **后果（推断）**：页面上的标签用 agent 自己起的名字，用户拿不到可以带进下一句话、可以搜索的正式名称。
  > Same job as the prose re-pitch (make the thing that did not land land), with one HTML page carrying the explanation. Only the medium changes: the page still supplies the missing context, and every label uses the ubiquitous language of `CONTEXT.md`, because the user carries those names into the next message.
- `VISUAL.md` `## Put the page where the user is looking` 两条 bullet 之后。可选，优先级低。
  - **冲突在哪**：`diagram-design` `## 12. Output` 规定页面自带 CSS、只允许 Google Fonts；它的文件里没有任何深色模式（grep `prefers-color-scheme` 为空）。而本会话里 Claude Code 的 Artifact 工具说明要求，写任何页面之前必须先加载 `artifact-design`，并且必须定义深色模式的 token。`VISUAL.md` 说 `diagram-design` “sets the page's look”，两条“必须”同时成立。
  - **现状**：还没观察到实际失败，agent 多半能自己调和。加一句能让它的调和方式固定下来。
  > When that surface imposes its own page rules (theme, allowed resources), they govern the page; `diagram-design` still draws what goes on it.

## C. 死板的流程
本仓写的文字里没有死板的流程。死板之处全部是 `diagram-design` 带进来的：§0 选风格指南这道关、§3 先选语义模式再选类型、§9 `Pre-Output Checklist (Taste Gate)`。对“把一条没讲清的消息重讲一遍”来说，这套流程偏重。但“所有向用户解释的 HTML 用同一套设计系统”是已经做出的决定（`mmw-v2/merge-notes/wait-what.md` `### VISUAL.md` 表的第二行，提交 `8a8db1de`），属于口味与产品层面的取舍，这里只记下剩余成本：每次用 `visual` 大约多读 6 千词，不重开这个决定。`VISUAL.md` 已经免掉了其中唯一会卡住用户的一步（§3 的确认暂停），这是对的。

## 脚本
无。

## 与其他技能的重复或交接问题
- `The reader knows nothing about this topic. …` 这一段逐字出现在三处：`VISUAL.md` `## Draw the page`、`mmw-v2/upstream/skills/productivity/teach/SKILL.md` `## Lessons`、`mmw-v2/upstream/skills/engineering/improve-codebase-architecture/HTML-REPORT.md` `## Candidate card`。三处各自位于执行那一刻 agent 会加载的文件里，三份都该留。同步规则已写在三份 merge-note 里（“改一处，三处一起改”）。
- `VISUAL.md` 和 `improve-codebase-architecture` 都把画图交给 `diagram-design`，并且各自免掉 §3。`mmw-v2/merge-notes/diagram-design.md` 已经记下这两个调用方依赖 `diagram-design` 的哪几节，交接关系清楚。

## 上游原文（单独列出，不建议改）
- `SKILL.md` 的 `talk in ASD-STE100 Simplified Technical English`：ASD-STE100 是一种受控的英语写法。用户经常用中文对话，在中文会话里调用时，agent 可能改用英文重讲。这只是推断，没有找到实际发生过的记录；用户的 `~/.claude/CLAUDE.md` 第 6 条只要求中英文都用标准词汇，没有规定回复语言。在观察到问题之前，按“上游原文尽量不改”不动。

## 没查到的
- 没有找到 `wait-what` 被实际调用的会话记录，两个缺口都是从文本和提交历史推断出来的。
- `mmw-v2/merge-notes/wait-what.md` 说 Claude Code 会把 `ARGUMENTS: visual` 追加到技能末尾，这一点没有实测。
- `diagram-design` 的 `SKILL.md` 只读了第 1–137 行（§0 到 §3）和 `## 12. Output` 的开头，其余各节只看了标题。

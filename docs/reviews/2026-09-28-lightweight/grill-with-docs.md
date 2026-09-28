# grill-with-docs

## 定稿（主 agent 复核）

**判断**：技能正文只有一句，思路全部借自 `grilling` 和 `domain-modeling`。它缺两样：一是说明它和普通 grilling 的区别，也就是边谈边把结论写进文档，而且这些写入不属于 `grilling` 所说的"用户确认前不动手"；二是谈完以后交给谁。你 5 次直接点名它时都没经过 `ask-matt`，所以 `ask-matt` 里"同一会话接着做 `to-spec`"那条规则在这时根本没被加载。

### 增加

| # | 位置 | 最终文字 | 它改变的选择 |
| --- | --- | --- | --- |
| I1 | `SKILL.md` 正文那一句之后（本仓加，merge-note 记一条） | Write each resolved term into `CONTEXT.md` as it resolves, and offer an ADR as the `domain-modeling` skill describes: these writes are part of the session, not the acting on it that `grilling` holds back. When the session settles a change to build, name the `to-spec` skill as the next step, in this same session. | 没有它，agent 可能把 `CONTEXT.md` 的写入也推迟到"用户确认之后"，访谈很好却什么都没留下（上游文档列为已知毛病）；谈完也不知道交给谁。 |

### 删除

- `mmw-v2/merge-notes/grill-with-docs.md` 里重复 README 的七个"只能由用户点名触发"技能名单：只减维护量，不影响 agent。

## 结论

`mmw-v2/upstream/skills/engineering/grill-with-docs/SKILL.md` 全文 40 词，正文只有第 7 行一句（14 词）；`agents/openai.yaml` 16 词；没有 reference、模板和脚本。本仓对上游只改了一处：第 7 行把上游的 `Call the Skill tool twice, for "grilling" and "domain-modeling".` 换成 `Read the `grilling` and `domain-modeling` skills' `SKILL.md` and run this session as both describe.`（host 中立），其余三处（`description`、`disable-model-invocation: true`、`policy.allow_implicit_invocation: false`）与上游 `5b1a4c51` 一字不差，merge-note `mmw-v2/merge-notes/grill-with-docs.md` 的三条记录与现状一致。技能本身没有可删的词，没有死板流程，也没有脚本。它的"灵魂"全部借自 `grilling` 和 `domain-modeling`，自己一句也没有：一个刚加载它的 agent 不知道它和 `grill-me` 的区别就在"留下文字记录"，也不知道结束后下一步是 `to-spec`。建议在第 7 行后补两句（约 60 词，草稿见 B），这是本报告唯一有分量的建议；证据是上游自己的文档记录的两个已知问题，加上用户真实的调用方式（直接点名，不经过 `ask-matt`），但这两个问题在本仓是否真的发生过，我没能验证。

## A. 删除或改成脚本

技能文本（`SKILL.md`、`agents/openai.yaml`）：**没有可删的内容。** 正文只有一句交接，删了技能就不工作。

只有一条落在维护者文件上，不影响 agent，列出供参考：

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| A1 | `mmw-v2/merge-notes/grill-with-docs.md` `### SKILL.md` 表第一行，"另外六个保留这一行的是 `setup-matt-pocock-skills`、`grill-me`、…" | 6 冗余重复 | 七个用户点名技能的名单在 `mmw-v2/merge-notes/README.md` `## disable-model-invocation`（"两行都留着的只有 …"）已有一份，同一节末尾还写着"下面每份说明只写它那个 skill 站在哪一边，不复述这条规则"；可同一名单又在 `grill-me.md`、`handoff.md`、`teach.md`、`improve-codebase-architecture.md` 和本文件各抄一遍。2026-09-23 的 `c9f4e5c7` 把三个技能改回用户点名时，这几份名单都得跟着改。我核对过，名单目前与实际一致（`grep -rl "disable-model-invocation: true"` 在已安装技能里正好命中这七个） | README 那一份承担。剩余风险：无，merge-note 不被任何 agent 在干活时加载 | 删掉"另外六个保留这一行的是 …"这一句，保留前面的理由和"规则见 README"。优先级低，只节省维护工作，不影响 agent |

## B. 灵魂

### 保留，勿删

- `SKILL.md` 第 7 行整句：它是这个技能存在的全部意义，即 grilling 的访谈加 domain-modeling 的记录，缺一个就退化成 `grill-me`。"both" 这个词让 agent 知道要读两份，不要只读一份。
- `SKILL.md` 第 4 行 `disable-model-invocation: true` 与 `agents/openai.yaml` 的 `policy` 块：merge-note 写明了理由，它与 `grilling` 抢同一个"grill"触发；模型如果自己选中了 `grilling`，就什么也写不进 `CONTEXT.md` 和 ADR。2026-09-23 汇总（`docs/reviews/2026-09-23-skill-set/汇总.md` 第 66 行）是按用户的决定恢复成这样的，不要再改回模型可触发。
- `mmw-v2/merge-notes/grill-with-docs.md` 第 11 行里的理由句"它与 `grilling` 抢同一个请求（「grill me」）…"：下一次拉上游或做修剪的人会靠这一句判断能不能删掉这个开关。

`git log -p --since=2026-09-01` 查了技能目录和 merge-note：2026-09-10 的 `793d4703` 加过一段 description 尾巴（"Use when a plan or design has to be sharpened inside a working directory … Not for a subject with no repository under it …"），2026-09-23 的 `c9f4e5c7` 按"用户点名的技能 description 只写摘要"的规则删掉了。这是用户的既定决定，**不建议恢复**。除此之外，没有被删掉的思想性段落。

### 缺口与补充草稿

- **`SKILL.md` 第 7 行之后：这个技能自己的目的，以及结束后交给谁。** 两份借来的技能各管一半，却都不说这次会话的意义。
  1. **两半都要，边谈边写。** 上游文档 `mmw-v2/upstream/docs/engineering/grill-with-docs.md` 第 52 行把"只加载了 `grilling`、没加载 `domain-modeling`，结果访谈很好却没留下任何记录"列为 "the most reported problem with this skill"。上游为此在 `.changeset/skill-tool-invocation-terminology.md` 把写法改成了显式调用工具，本仓出于 host 中立又改回了散文写法，所以上游修这个问题的那一手在本仓不存在（这是推断，本仓里没有观察到这种失败）。另外，`grilling/SKILL.md` 第 42 行说 "Do not act on it until the user confirms"；而按 `SKILL-SET-REVIEW.md` `### Hand-offs` 第 90 行的要求，把它放到 grill-with-docs 的场景里重读，一个 agent 可能把这句读成"会话结束前不要写 `CONTEXT.md`"，这就正好违背了 `domain-modeling` `### Update CONTEXT.md inline` 的"Don't batch these up"（同样是推断）。
  2. **下一步是 `to-spec`，而且在同一个会话里。** 上游文档第 61 行："The skill's closing message tends to be open-ended, which is a known rough edge"。`grilling` 只结束在 "until the user confirms"，`domain-modeling` 没有结尾。可是大部分决定既不是术语，也够不上 ADR 的三道门槛，只存在于这个会话里（上游文档 `## The paper trail` 第三行）。"留在同一个会话里"这条规则写在 `ask-matt/SKILL.md` `### Context hygiene`，而用户真实的用法是直接点名这个技能（`~/.claude/history.jsonl` 里 2026-08-20 到 09-02 共 5 次 `/grill-with-docs`，没有一次经过 `ask-matt`），这时 `ask-matt` 根本没被加载。如果用户在这一步清空或压缩了会话，这些决定就丢了，`to-spec` 只能凭 `CONTEXT.md` 去写。`SKILL-SET-REVIEW.md` 第 89 行 "Each skill ends by naming what comes next" 也要求补这一句。

  建议草稿（接在第 7 行后，同一段）：
  > What sets this session apart from a plain grilling is the paper trail it leaves: write each resolved term into `CONTEXT.md` as it resolves, and offer an ADR the moment a decision passes the three tests. Those writes are part of the session, not the "acting on it" that grilling holds back. Everything else the user decides exists only in this conversation, so when the session settled a change to build, name the `to-spec` skill as the next step, to run in this same session.

  这段草稿改变了 agent 的两个做法：术语在会话进行中就落到文件里，不等到最后；结束时明确把用户带到 `to-spec`，而不是开放式地收尾。草稿没有用"清空/压缩会话"的字眼，所以不用按 `### Paths, tokens and host neutrality` 再补那句 host 中立的固定句。按 `SKILL-SET-REVIEW.md` `### Upstream skills` 的规定，这是一处改变行为的改动，落地时要在 `mmw-v2/merge-notes/grill-with-docs.md` 的"正文那一句"条目里补上意图和理由。它加在本仓本来就已经改过的那一行后面，没有改动上游的其他文字。

## C. 死板的流程

无。技能本身没有步骤、模板或规则。它通过交接继承来的轮次格式和思考规程，属于 `grilling` 的审查范围（见下节）。

## 脚本

无。

## 与其他技能的重复或交接问题

- **与 `grill-me`**（`mmw-v2/upstream/skills/productivity/grill-me/SKILL.md`）：两者的结构是对称的，本仓对两者做了同样的 host 中立改写，没有重复，也没有矛盾。区别只在有没有 `domain-modeling`。B 的草稿只加在 grill-with-docs 里，不能加到 `grilling`，因为 `grilling` 同时被 `grill-me`（没有仓库）、`triage`、`wayfinder`、`improve-codebase-architecture` 使用，"下一步是 `to-spec`"对它们不成立。
- **与 `grilling`**：用户的真实调用在参数里反复补同一类要求。2026-08-24 "你在向我提问的时候，一定要记得向我提供相关的上下文"；08-27 "我看不懂你的问题，说清楚前因后果，直白一点"；09-02 "从业务意图和功能设计的角度去向我解释、提问和给出建议"（以上三条是 `/grill-with-docs`）；另有 09-02 的 `/grill-me`："注意修复方法明确或者你自己能找到最佳解法的不要问我"。这说明问题的格式和"哪些该问用户"是真实存在的摩擦。`grilling` 第 26 行 "The _decisions_ are the user's: put each to them" 没有区分工程决定和产品决定，而 Nowledge Mem 记录的决定（2026-09-16，"能自己定的写进➡️，只有用户必须拍板的才升成 frontier 问题"）在 `grilling` 现文里没有明说。这一条归 `grilling` 的审查，不归本技能，只记录；应该留在 `grilling` 里，因为五个入口共用它。这几次调用的时间有一部分早于 `grilling` 最近的改动，现文是否已经解决了这个问题，我没有验证。
- **与 `domain-modeling`**：本仓的 ADR 格式（`docs/adr/README.md` `## 一份 ADR 长什么样`，带 `date`/`amends` frontmatter，不写 `## Decision`，要手工补索引行）和 `domain-modeling/ADR-FORMAT.md` 不同。这个衔接已经做在上游文本之外：`docs/agents/domain.md` 第 61 行，以及根 `AGENTS.md` `## External References` 的 "ADR shape" 一行，在本仓干活的 agent 都会加载根 `AGENTS.md`。不需要改动。
- **与 `ask-matt`**：`docs/reviews/2026-09-28-lightweight/ask-matt.md` B 节的草稿说 "`grill-with-docs` is the exception: it is the `grilling` and `domain-modeling` skills run together, and you can read both"。如果 B 的补充落地，走这条例外路径的 agent 会绕过它；不过 `ask-matt` 主流程第 3 步和 `### Context hygiene` 已经覆盖了"下一步 `to-spec`、同一个会话"，所以不冲突，两边都留。
- **与 `SKILL-SET-REVIEW.md`**：没有冲突。第 15 行 "Skills are peers composed by name" 把本技能当作正面例子；B 的补充符合第 89 行 "Each skill ends by naming what comes next"。

## 没查到的

- 本仓里真实的 grill-with-docs 会话有没有出现过"只加载一半""等到最后才写 `CONTEXT.md`""结束后清空会话丢了决定"：没有找到会话记录或 tracker 证据。B 的两条依据的是上游文档的报告和推断，属于未验证。
- 第 7 行的散文写法在 Codex、Grok、Pi、Cursor 上能否可靠地让 agent 读到两份 `SKILL.md`：没有实际运行，未验证。
- `grilling` 和 `domain-modeling` 本身没有逐段审查，只读了与交接有关的部分（`grilling` 全文读过，`domain-modeling/SKILL.md` 全文读过，`ADR-FORMAT.md` 读了前 30 行）。

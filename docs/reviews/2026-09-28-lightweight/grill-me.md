# grill-me

## 定稿（主 agent 复核）

**判断**：正文只有一句，灵魂在 `grilling`，改动见 `grilling` 定稿。这里只删 `mmw-v2/merge-notes/grill-me.md` 里一条已经与上游相同的记录。

七个"只能由用户点名触发"技能的名单，在 `mmw-v2/merge-notes/README.md` 之外，又在五份 merge-note 里各抄了一遍（`handoff`、`wait-what`、`grill-with-docs`、`improve-codebase-architecture` 等报告都发现了）。统一只留 README 一处。

## 结论

`mmw-v2/upstream/skills/productivity/grill-me/SKILL.md` 正文只有一句（第 7 行 `Read the grilling skill's SKILL.md and run this session as it describes.`），全文 28 词，没有脚本，没有 reference；`agents/openai.yaml` 与上游相同。本仓对上游只改了这一句：把 `Call the Skill tool with "grilling".` 改成与 host 无关的写法，`mmw-v2/merge-notes/grill-me.md` 有对应记录，与现文一致。frontmatter 的 `disable-model-invocation: true` 和 description 都是上游原文。技能正文没有可删的，也没有死板的流程；它的"灵魂"全部在 `grilling` 里，由那份技能承担，缺口也在那边（见 `docs/reviews/2026-09-28-lightweight/grilling.md`）。唯一可删的是 merge-note 里一条已经与上游相同的记录。

## A. 删除或改成脚本

| # | 位置（文件 + 标题，引用原文开头几个词） | 类别（1–6） | 证据 | 删掉后由谁承担 / 剩余风险 | 建议修法 |
| --- | --- | --- | --- | --- | --- |
| 1 | `mmw-v2/merge-notes/grill-me.md` 表格第二行 "frontmatter 的 `description` \| 收上游原文：…不写「什么时候用我」" | 3、6 | `git diff 5b1a4c51:skills/productivity/grill-me HEAD:mmw-v2/upstream/skills/productivity/grill-me` 显示 description 与上游逐字相同。这一行记录的是 `c9f4e5c7`（2026-09-23）撤回本仓旧改动的经过；`mmw-v2/merge-notes/README.md` 开头规定"说明里没覆盖的段落：我们没改过，取上游"，没改过的段落不需要条目。它要防的事（再给 description 加"Use when…"）已由 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Descriptions`"A user-invoked skill … its description is a one-line summary for the person reading the command list"承担 | `SKILL-SET-REVIEW.md` `### Descriptions`；剩余风险：无，上游改 description 时照 README 默认"取上游"即可 | 删掉这一行。这是 merge-note，不是 agent 加载的技能文本，优先级低 |

第一行（`disable-model-invocation: true` 的理由）不删：它记录"为什么这个技能只能由用户点名"，下一次拉上游的人需要它。它和 `mmw-v2/merge-notes/README.md` `## disable-model-invocation` 以及另外四份 merge-note 重复列出"七个保留这一行的技能"，本批 `handoff.md` 报告已记录这处六份重复，这里不重复提。

`SKILL.md` 正文那一句不可删：它是这个技能唯一的动作。

## B. 灵魂

### 保留，勿删

- frontmatter `disable-model-invocation: true` 与 `agents/openai.yaml` 的 `policy.allow_implicit_invocation: false`：被审问的是用户自己的想法，开始的时机归用户（merge-note 第一行的理由）。两处要一起留（`mmw-v2/merge-notes/README.md` `## disable-model-invocation`）。
- 正文只加载 `grilling`、不加载 `domain-modeling`：这就是 `grill-me` 和 `grill-with-docs` 的区别，"stateless，什么也不写"（`mmw-v2/upstream/skills/engineering/ask-matt/SKILL.md` 第 80 行）。这种区别靠"不加载"实现，不需要写成一句禁令。

### 缺口与补充草稿

没有需要补在本技能里的。考虑过的两处：

- 用户在仓库里用了 `grill-me`，本该用 `grill-with-docs` 留下 `CONTEXT.md` 和 ADR：路由判断由 `ask-matt` 第 16、80 行承担，而且技能是用户点名启动的，用户已经选好了。在这里加一句"在仓库里请改用 grill-with-docs"会替用户重做一次选择，不加。
- 访谈该怎么想、怎么问：全部在 `grilling`。用户点名 `/grill-me` 时反复要求"直白、只问需要我拍板的"（`~/.claude/history.jsonl`，08-23、09-02、09-10 三次），这些缺口在 `grilling` 报告的 B 节处理，因为 `grill-with-docs`、`wayfinder`、`triage`、`improve-codebase-architecture` 走的是同一份文本，补在 `grilling` 一处，所有入口一起生效（这也是用户 2026-09-16 把思考写进 `grilling` 而不另开技能的理由，见 Nowledge Mem"思考规程并入同一份grilling SKILL.md，作为推荐答案检查"）。

## C. 死板的流程

无。

## 脚本

无。

## 与其他技能的重复或交接问题

- 交接成立：`grilling` 在 `mmw-v2/skills.txt` 第 30 行安装，本机 `~/.claude/skills/grilling` 与 `~/.agents/skills/grilling` 两个符号链接都指向已安装的 checkout，`grill-me` 正文点到的 `SKILL.md` 能找到。
- `grill-me` 与 `grill-with-docs` 的正文结构相同（都是一句"读某某技能并照做"），各留各的，没有重复问题。
- 谁把用户引到 `grill-me`：只有 `ask-matt`（第 16、80、81、85 行）。它是模型可触发的，而 `grill-me` 只能由用户点名；这个问题本批 `ask-matt.md` 报告 R1 已记录，归 `ask-matt` 那边改。

## 没查到的

- 没有在 Codex、Grok、Pi 上实测 `$grill-me` 或等价的点名方式能否加载；只核对了 `agents/openai.yaml` 的 `policy` 与上游一致、Claude 侧的符号链接存在。
- `~/.codex/history.jsonl` 里没有 `grill` 的点名记录；其他 host 的历史没查。

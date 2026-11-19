# grilling

源目录：`mmw-v2/upstream/skills/productivity/grilling/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 正文 `Finding _facts_ is your job` 段之后、`The session is done` 段之前新增的整段（`Put to the user only the decisions` 起，到 `redirect to the process behind them.` 止） | 我们加的，两部分。第一部分（`Put to the user only the decisions that are theirs.` 一段）：收窄上游 `The _decisions_ are the user's: put each to them and wait.`——只有用户自己的决定才问，用户既定规程留给 agent 的工程选择写进推荐答案、附理由，用户能否决但不用被问；每道问题给读者背景（起因、每个选项对产品的影响）。依据是用户 8 次点名启动这组访谈里有 5 次要求"给背景、说直白、能自己定的别问我"，与用户全局规则第 1 条（工程决定归 agent）一致，但第 26 行原文没有收窄，访谈现场只照眼前这份技能。这是本仓新写的文字，不是摘录。第二部分（`Think through the paragraphs below…` 起）：形成每道推荐答案时要跑的思考，恢复自 `adae02f2`（2026-09-16，2026-09-22 的 `e74e0140`、2026-09-23 的 `95e05b11` 两轮改写误当成"维护者理由"删掉或移进本说明的几句，现按用户 2026-09-16 的裁定"只做原文摘录的精确修剪、不做总结精简、'惯例不是理由' 一段保持不动"逐句恢复原文）：先质疑前提和需求，把约束分成物理/合同/实测与惯例，从剩下的 primitives 重建满足需求的最简解并删掉不该存在的步骤；失败、复发或修补方案才区分 symptom、proximate cause、root cause（用英文里的通用术语，读者查得到），几次共享同一前提的尝试都失败时怀疑前提，优先去掉促成条件而不是只补近因、让失败暴露而不是加守卫把它盖住。恢复的原文里 "none of these are REASONS" 前的破折号换成冒号，理由是 `mmw-v2/upstream/` 不写破折号，其余逐字照 `adae02f2`。"first principles is overkill" 那一句从原来的位置（判断放行条件的段落末尾）移到这一整块的开头第一句之后：按顺序读的 agent 会先跑完约束分类再读到放行条件，移到开头让路径已经清楚的问题可以直接给推荐答案；原位置末尾 `; first principles is for where the path is not already clear` 同时删去，避免说两遍。不写「workaround 要一大段注释来辩护就是错的」：那是审代码时的判断，不是访谈里形成推荐答案的判断。约束一句写 `not past practice alone`，不用 `precedent`：本仓 `docs/contexts/tickets/CONTEXT.md` 的 **precedent** 指 ticket 要抄的那个测试。措辞覆盖 plan、decision、idea（含无仓库的写作与 wayfinder 单张决策票），不绑死在代码或排错。不改 rounds、frontier、问法或结束条件。这几条的理由只记在这里，正文不写：问题问得再好，也可能是在帮着完善一个本不该存在的东西，所以先质疑前提；需求总有几分是错的，先减需求，否则可能给错的问题一个完美答案；人常忘了试着整个删掉一步，而最常见的错误是优化一个本不该存在的东西，所以删在优化之前；第一个找到的原因几乎从来不是真问题，所以先列 5–7 个来源。上游改前后段落 → 收上游措辞，这一整段原样保留；上游若自己写入形成推荐答案时的思考，且与这段重叠 → 收上游的机制，删掉我们这一段（第一部分——谁来决定——不属于这条，继续保留）。 |

## 上游再动这几段时

- 上游改 **design tree、rounds、frontier、问法格式、事实与决定的分工、结束条件** → **收上游**，第一部分（谁来决定）接在收上游之后的措辞不变。
- 上游若自己写入形成推荐答案时的思考，且与第二部分重叠 → **收上游的机制，删掉我们这一段**，避免两套写法并存。

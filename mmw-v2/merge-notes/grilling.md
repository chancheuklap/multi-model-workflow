# grilling

源目录：`mmw-v2/upstream/skills/productivity/grilling/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| 正文 `Finding _facts_ is your job` 段之后、`The session is done` 段之前新增的整段（`Think through the paragraphs below when forming each recommended answer.` 起，到 `redirect to the process behind them.` 止） | 我们加的。形成每道推荐答案时要跑的思考：先质疑前提和需求，把约束分成物理/合同/实测与惯例，从剩下的 primitives 重建满足需求的最简解并删掉不该存在的步骤；失败、复发或修补方案才区分 symptom、proximate cause、root cause（用英文里的通用术语，读者查得到），几次共享同一前提的尝试都失败时怀疑前提，优先去掉促成条件而不是只补近因、让失败暴露而不是加守卫把它盖住——这几句只在失败那一段写一次。不写「行业惯例」「一直这么做」这类说法的列举：约束分类那一段已经要求惯例拿出独立的支持。不写「workaround 要一大段注释来辩护就是错的」：那是审代码时的判断，不是访谈里形成推荐答案的判断。约束一句写 `not past practice alone`，不用 `precedent`：本仓 `docs/contexts/tickets/CONTEXT.md` 的 **precedent** 指 ticket 要抄的那个测试。措辞覆盖 plan、decision、idea（含无仓库的写作与 wayfinder 单张决策票），不绑死在代码或排错。不改 rounds、frontier、问法或结束条件。这几条的理由只记在这里，正文不写：问题问得再好，也可能是在帮着完善一个本不该存在的东西，所以先质疑前提；需求总有几分是错的，先减需求，否则可能给错的问题一个完美答案；人常忘了试着整个删掉一步，而最常见的错误是优化一个本不该存在的东西，所以删在优化之前；第一个找到的原因几乎从来不是真问题，所以先列 5–7 个来源。上游改前后段落 → 收上游措辞，这一整段原样保留。 |

## 上游再动这几段时

- 上游改 **design tree、rounds、frontier、问法格式、事实与决定的分工、结束条件** → **收上游**。
- 上游若自己写入形成推荐答案时的思考，且与这段重叠 → **收上游的机制，删掉我们这一段**，避免两套写法并存。

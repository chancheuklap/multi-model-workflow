# grill-with-docs

源目录：`mmw-v2/upstream/skills/engineering/grill-with-docs/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留，与上游一致；`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false` 一起保留。理由：它与 `grilling` 抢同一个请求（「grill me」），模型可触发时挑中 `grilling` 就什么也没写进 `CONTEXT.md` 与 ADR；由用户点名才开始。上游改这一行 → 收上游，两处一起跟。七个技能的名单与规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 收上游原文：user 点名才触发的技能，description 是给读命令列表的人看的一行摘要（`writing-for-agents` 技能的 `SKILL-MECHANICS.md` `## Invocation`），不写「什么时候用我」。上游改这一行 → 收上游 |
| 正文那一句（全文只有这一句） | host 中立：改成读 `grilling` 与 `domain-modeling` 两份技能的 `SKILL.md`，按它们说的跑这次会话。共同理由见 [README.md](README.md#host-中立)，写法见 `writing-for-agents` 技能的 `SKILL-SET-REVIEW.md` `### Paths and host neutrality` 与 `### Hand-offs` |
| 正文那一句之后新增两句（本仓写的） | 说明本技能与普通 grilling 的区别（边谈边把结论写进 `CONTEXT.md` 与 ADR，这些写入不属于 `grilling` "用户确认前不动手"的范围），以及谈完后交给 `to-spec`，在同一会话里。理由：上游文档把"只加载了一半、结果访谈很好却没留下记录"和"结束语开放、不知道下一步"列为最常见的两个毛病；本仓把 grilling 的问法改成散文写法后，上游修第一个问题的显式工具调用不在本仓生效。上游改上一行 → 收上游措辞，这两句接在后面不动 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 保留，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |

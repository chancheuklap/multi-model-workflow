# grill-with-docs

源目录：`mmw-v2/upstream/skills/engineering/grill-with-docs/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留，与上游一致；`agents/openai.yaml` 的 `policy.allow_implicit_invocation: false` 一起保留。理由：它与 `grilling` 抢同一个请求（「grill me」），模型可触发时挑中 `grilling` 就什么也没写进 `CONTEXT.md` 与 ADR；由用户点名才开始。另外六个保留这一行的是 `setup-matt-pocock-skills`、`grill-me`、`handoff`、`wait-what`、`teach`、`improve-codebase-architecture`。上游改这一行 → 收上游，两处一起跟。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 收上游原文：user 点名才触发的技能，description 是给读命令列表的人看的一行摘要（`writing-for-agents` 技能的 `SKILL-MECHANICS.md` `## Invocation`），不写「什么时候用我」。上游改这一行 → 收上游 |
| 正文那一句（全文只有这一句） | host 中立：改成读 `grilling` 与 `domain-modeling` 两份技能的 `SKILL.md`，按它们说的跑这次会话。共同理由与三种替换写法见 [README.md](README.md#host-中立) |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 保留，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |

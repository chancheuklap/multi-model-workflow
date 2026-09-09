# grill-me

源目录：`mmw-v2/upstream/skills/productivity/grill-me/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留。这是四个例外之一（另三个是 `setup-matt-pocock-skills`、`handoff`、`wait-what`）：被审问的是用户自己的想法，该由用户点名才开始。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 末尾那句「什么时候用我」（`Use when the subject is a plan, a design or a piece of writing with no repository under it, since this skill saves nothing locally.`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；判据是这份技能自己的 stateless 定位与 `ask-matt/SKILL.md` 讲 grill-me 那一条。「什么时候不要用我」那半段没加，判断权在写那一份技能的人。上游改这一行 → 收上游对前半句的措辞，「什么时候用我」这半段保留 |
| 正文那一句（全文只有这一句） | host 中立：改成读 `grilling` 技能的 `SKILL.md`，按它说的跑这次会话。共同理由与三种替换写法见 [README.md](README.md#host-中立) |

# handoff

源目录：`mmw-v2/upstream/skills/productivity/handoff/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留，是保留这一行的七个之一（另六个是 `setup-matt-pocock-skills`、`grill-me`、`wait-what`、`grill-with-docs`、`teach`、`improve-codebase-architecture`）：把会话压成一份交接文档是用户决定的时机，不该由模型自己认出来触发。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 收上游原文：user 点名才触发的技能，description 是给读命令列表的人看的一行摘要（`writing-for-agents` 技能的 `SKILL-MECHANICS.md` `## Invocation`），不写「什么时候用我」。上游改这一行 → 收上游 |
| `Include a "suggested skills" section …` 一句 | host 中立：删掉句尾的工具名，只让文档点出下一个 agent 该拿起哪几份技能。这一句不是让谁去调用什么，所以点名另一个技能的写法都不适用。共同理由见 [README.md](README.md#host-中立) |

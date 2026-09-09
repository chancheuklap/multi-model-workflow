# handoff

源目录：`mmw-v2/upstream/skills/productivity/handoff/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留。这是四个例外之一（另三个是 `setup-matt-pocock-skills`、`grill-me`、`wait-what`）：把会话压成一份交接文档是用户决定的时机，不该由模型自己认出来触发。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理。规则见 [README.md](README.md#disable-model-invocation) |
| frontmatter 的 `description` | 末尾那句「什么时候用我」（`Use when the work has to travel — to another host, another directory, or another person — or when a side task found mid-phase is forked off without derailing this one.`）是本仓补的：host 启动时只扫这一行，一份只说「我是什么」的技能在列表里挑不出该不该用它；四种场合逐字取自 `ask-matt/PHASE-BOUNDARIES.md` 第 3 问那张清单。「什么时候不要用我」那半段没加，判断权在写那一份技能的人。上游改这一行 → 收上游对前半句的措辞，「什么时候用我」这半段保留 |
| `Include a "suggested skills" section …` 一句 | host 中立：删掉句尾的工具名，只让文档点出下一个 agent 该拿起哪几份技能。这一句不是让谁去调用什么，所以三种替换写法都不适用。共同理由见 [README.md](README.md#host-中立) |

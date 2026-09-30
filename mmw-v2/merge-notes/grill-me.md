# grill-me

源目录：`mmw-v2/upstream/skills/productivity/grill-me/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 保留，是保留这一行的七个之一：被审问的是用户自己的想法，该由用户点名才开始。上游改这一行 → 收上游，跟 `agents/openai.yaml` 的 `policy` 块一起处理。七个技能的名单与规则见 [README.md](README.md#disable-model-invocation) |
| 正文那一句（全文只有这一句） | host 中立：改成读 `grilling` 技能的 `SKILL.md`，按它说的跑这次会话。共同理由见 [README.md](README.md#host-中立)，写法见 `mmw` 技能的 `references/skill-set-rules.md` `### Paths and host neutrality` 与 `### Hand-offs` |

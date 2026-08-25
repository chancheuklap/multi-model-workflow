# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求全部技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| `<vertical-slice-rules>` | 删掉「Each slice is sized to fit in a single fresh context window」这一条。我们的 spec 通常很大，这条把切片推得过细；粒度由第 4 步问用户来定。上游改这条措辞 → 仍然删。上游把它换成别的尺寸规则 → 也删，保持切片尺寸不设机械上限。其余段落我们没改，全取上游 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

# to-questionnaire

源目录：`mmw-v2/upstream/skills/productivity/to-questionnaire/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |

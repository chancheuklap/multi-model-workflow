# wayfinder

源目录：`mmw-v2/upstream/skills/engineering/wayfinder/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求这个技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| `### Work through the map` 的第 6 步 | 我们加的整步：frontier 与 Not yet specified 都空时地图已清，停下来把下一步交给用户——新会话里对这张地图跑 `to-spec`（传完整引用），再 `to-tickets`；地图不关。上游给这一节加了新的收尾步 → 把我们这一步接在它后面并重编号；上游自己写了地图走完之后往哪去 → 只留上游那一句，删掉我们这一步（`to-spec` 那侧的分卷判断不依赖这句话）。其余段落我们没改，全取上游 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

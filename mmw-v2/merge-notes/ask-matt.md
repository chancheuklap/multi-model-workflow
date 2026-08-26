# ask-matt

源目录：`mmw-v2/upstream/skills/engineering/ask-matt/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉。本仓库要求全部技能模型可触发——不留上游的人工触发限制，免得漏输入指令时 agent 没法自己认出该用这个技能。上游改这一行 → 仍然删，跟 `agents/openai.yaml` 的 `policy` 块一起处理 |
| 主流程第 2 步、技能清单里的 `/prototype` 条 | 跟上我们改造后的 prototype：三类问题（逻辑、UI、实现方式）；去掉 throwaway；处置是留在仓库 `prototypes/` 下当参考（完整路径规范归 prototype 技能，这里不复述），**没有** `prototype/<name>` 一次性分支。上游改措辞可跟，但这三点不能被上游的说法覆盖回去。改这里同时看 `merge-notes/prototype.md` |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉。跟 `SKILL.md` 的 `disable-model-invocation` 同步去掉，两处必须同增同删 |

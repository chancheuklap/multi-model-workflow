# writing-for-agents

源目录：`mmw-v2/upstream/skills/productivity/writing-for-agents/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 触发条件去掉「modifying AGENTS.md or CLAUDE.md」那一支，改成「writing any document an agent will consume」：这两份文件在本仓归 `manage-agents-md` 管，两个 skill 同时被触发会互相拆台。上游改这句的措辞 → 收上游，再把 `AGENTS.md` / `CLAUDE.md` 那一支去掉 |
| `## Context pointers`、`## Pruning`、`## Leading words` 三节 | 正文全取上游，一个字没改。但 `manage-agents-md` 技能的 `references/write.md` 与 `references/prune.md` 按节名指到这里读这三节的规则（`prune.md` 那一行里有两处指路）。`Negation` 不是节名，是 `## Leading words` 一节里的一个加粗词，所以按节名指过来的人指的是 `## Leading words`。上游改这三个节名、或把内容并进别的小节 → 收上游，再把那几处指路里的节名改成新的 |

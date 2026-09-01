# writing-for-agents

源目录：`mmw-v2/upstream/skills/productivity/writing-for-agents/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 触发条件去掉「modifying AGENTS.md or CLAUDE.md」那一支，改成「writing any document an agent will consume」：这两份文件在本仓归 `manage-agents-md` 管，两个 skill 同时被触发会互相拆台。上游改这句的措辞 → 收上游，再把 `AGENTS.md` / `CLAUDE.md` 那一支去掉 |
| `## Pointers`、`## Pruning`、`## Negation` 三节 | 正文全取上游，一个字没改。但 `mmw-v2/skills/manage-agents-md/prune.md` 的 `## Pruning` 与 `write.md` 的 `## Pointers` 按节名指到这里读这三节的规则。上游改这三个节名、或把内容并进别的小节 → 收上游，再把那两处指路行里的节名改成新的 |

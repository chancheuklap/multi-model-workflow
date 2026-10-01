# writing-for-agents

源目录：`mmw-v2/upstream/skills/productivity/writing-for-agents/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 触发条件「modifying AGENTS.md or CLAUDE.md」那一支放宽成「writing any document an agent will consume」：spec、ticket、写给 agent 的 prompt 与 `AGENTS.md` 都在里面。`AGENTS.md` 的格式归 `manage-agents-md` 技能管。上游改这句的措辞 → 收上游，再把那一支放宽成同一句 |

### 别处按标题引用这里

`mmw` 技能的 `references/skill-set-rules.md` 按节名引用这个目录的 `SKILL.md`（`## Pruning`、`## Context pointers`），并在 `## Upstream examples` 里按标题引用若干上游技能；`references/reviewing-a-skill-set.md` 按技能名引用这个目录的 `SKILL.md`。上游改这些标题 → 收上游，再改这两份文件里对应的引用。

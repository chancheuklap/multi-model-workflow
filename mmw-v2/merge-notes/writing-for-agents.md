# writing-for-agents

源目录：`mmw-v2/upstream/skills/productivity/writing-for-agents/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 触发条件去掉「modifying AGENTS.md or CLAUDE.md」那一支，改成「writing any document an agent will consume」：这两份文件在本仓归 `manage-agents-md` 管，两个 skill 同时被触发会互相拆台。上游改这句的措辞 → 收上游，再把 `AGENTS.md` / `CLAUDE.md` 那一支去掉 |
| 开头指向 `SKILL-MECHANICS.md` 的那一段 | 句末加一句指向本仓自己的 `SKILL-SET-REVIEW.md`，触发条件是「写、改、复审或精简一组互相交接的技能中的一个」。上游改这一段 → 收上游，再把这一句接回段末 |
| `## Context pointers`、`## Pruning`、`## Leading words` 三节 | 正文全取上游，一个字没改。但 `manage-agents-md` 技能的 `references/write.md` 与 `references/prune.md` 按节名指到这里读这三节的规则（`prune.md` 那一行里有两处指路）。`Negation` 不是节名，是 `## Leading words` 一节里的一个加粗词，所以按节名指过来的人指的是 `## Leading words`。上游改这三个节名、或把内容并进别的小节 → 收上游，再把那几处指路里的节名改成新的 |

### SKILL-SET-REVIEW.md

上游没有这份文件，整份是本仓写的：本仓技能文本规则的唯一归属（根 `AGENTS.md` 不再重复这些规则），外加复审一组技能的方法，来源是上游技能自身的写法、`SKILL.md` 的概念和本仓历次改写技能留下的规则。它按名字引用 `SKILL.md` 的 `## Context pointers`、`## Steps and completion criteria`、`## Pruning` 三节；末节 `## Upstream examples` 按路径与节名引用上游原版的若干文件作范例（`wizard`、`prototype` 及其 `LOGIC.md` / `UI.md`、`codebase-design` 的 `## Glossary` 与 `## Going deeper`、`to-questionnaire`、`improve-codebase-architecture/HTML-REPORT.md` 的 `## Tone`、`grilling`、`to-spec` / `to-tickets` / `triage` / `tdd` / `diagnosing-bugs`、`code-review` 第 4 步、in-progress `retro`、`triage/AGENT-BRIEF.md`）。上游改这些节名、移动这些文件或删掉被引用的写法 → 收上游，再改这份文件里对应的引用；上游自己加了同主题的文件 → 读它，重合的部分以上游为准，本仓独有的规则留在这里。

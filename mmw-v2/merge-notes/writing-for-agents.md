# writing-for-agents

源目录：`mmw-v2/upstream/skills/productivity/writing-for-agents/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `description` | 触发条件「modifying AGENTS.md or CLAUDE.md」那一支放宽成「writing any document an agent will consume」：spec、ticket、写给 agent 的 prompt 与 `AGENTS.md` 都在里面。`AGENTS.md` 的格式归 `manage-agents-md` 技能管，它的 `references/write.md` 与 `references/prune.md` 按节名读本技能的三节（见下面第三行），所以两个技能同时加载是设计如此。上游改这句的措辞 → 收上游，再把那一支放宽成同一句 |
| 开头指向 `SKILL-MECHANICS.md` 的那一段 | 句末加一句指向本仓自己的 `SKILL-SET-REVIEW.md`，触发条件是「写、改、复审或精简一组互相交接的技能中的一个」。上游改这一段 → 收上游，再把这一句接回段末 |
| `## Context pointers`、`## Pruning`、`## Leading words` 三节 | 正文全取上游，一个字没改。但 `manage-agents-md` 技能的 `references/write.md` 与 `references/prune.md` 按节名指到这里读这三节的规则（`prune.md` 那一行里有两处指路）。`Negation` 不是节名，是 `## Leading words` 一节里的一个加粗词，所以按节名指过来的人指的是 `## Leading words`。上游改这三个节名、或把内容并进别的小节 → 收上游，再把那几处指路里的节名改成新的 |

### SKILL-SET-REVIEW.md

上游没有这份文件，整份是本仓写的：本仓技能文本规则的唯一归属（根 `AGENTS.md` 不再重复这些规则），外加复审一组技能的方法，来源是上游技能自身的写法、`SKILL.md` 的概念和本仓历次改写技能留下的规则。它按名字引用 `SKILL.md` 的 `## Context pointers`、`## Steps and completion criteria`、`## Pruning` 三节与 `## Leading words` 一节里的加粗词 **Negation**；首节 `## What skill text is for` 与末节 `## Upstream examples` 按路径与节名引用上游原版的若干文件作范例（`implement`、`grill-with-docs`、`wizard`、`prototype` 及其 `LOGIC.md` / `UI.md`、`codebase-design` 的 `## Glossary` 与 `## Going deeper`、`to-questionnaire`、`improve-codebase-architecture/HTML-REPORT.md` 的 `## Tone`、`grilling`、`to-spec` / `to-tickets` / `triage` / `tdd` / `diagnosing-bugs`、`code-review` 第 1、3、4 步与 `## Why two axes`、in-progress `retro`、`triage/AGENT-BRIEF.md`）。上游改这些节名、移动这些文件或删掉被引用的写法 → 收上游，再改这份文件里对应的引用；上游自己加了同主题的文件 → 读它，重合的部分以上游为准，本仓独有的规则留在这里。

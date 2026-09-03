# improve-codebase-architecture

源目录：`mmw-v2/upstream/skills/engineering/improve-codebase-architecture/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `disable-model-invocation: true` | 删掉，这个 skill 在本仓是模型可触发的；`agents/openai.yaml` 的 `policy.allow_implicit_invocation` 一起删。上游改这一行 → 仍然删。规则见 [README.md](README.md#disable-model-invocation) |

### HTML-REPORT.md

| 段落 | 我们的意图 |
| --- | --- |
| Candidate card 末段（`The reader knows nothing about this topic.` 起） | 替掉上游的 `No paragraphs of explanation. If the diagram needs a paragraph to be understood, redraw the diagram.`。上游那句只限篇幅，读者仍默认懂代码；我们这段定读者（一无所知）和图、字的分工：图管是什么与怎么连，字只做图做不到的三件事（图答的是哪个问题、重点在哪、由此得出什么），字重复图就删字，图要一段话才看得懂就重画。上游那句的「重画」要求已含在最后一句里。上游改那句措辞 → 仍用我们的这段 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `policy` 整块（`allow_implicit_invocation: false`） | 删掉，跟 `SKILL.md` 的 `disable-model-invocation` 一起。规则见 [README.md](README.md#disable-model-invocation) |

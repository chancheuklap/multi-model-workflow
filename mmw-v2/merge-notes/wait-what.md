# wait-what

源目录：`mmw-v2/upstream/skills/productivity/wait-what/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `argument-hint` | 我们加的，上游没有。给 user 一个开关：不带参数走文字重讲，带 `visual` 走 `VISUAL.md`。值是自动补全里显示的参数占位符，说明写在方括号内。上游自己加 `argument-hint` → 取上游的，把 `visual` 这一支并进去 |
| 正文末尾 `Tagged \`visual\`:` 那一句 | 我们加的整句，是 `VISUAL.md` 的唯一入口。上游改了它上面那句重讲指令的措辞 → 收上游，这一句原样接在后面。上游把重讲拆成多句 → 接在最后 |
| 正文第一句（重讲指令） | 上游原文，没改，全取上游 |

正文靠自然语言认这个标签，**不用 `$ARGUMENTS`**。`$ARGUMENTS` 是 Claude Code 的替换机制，别的 host 不替换，这个字面串就原样留在正文里。不写它也不丢参数：Claude Code 会把 `ARGUMENTS: visual` 追加到技能末尾。

### VISUAL.md

`mattpocock/skills` 里没有这个文件，subtree pull 不会碰它。它是我们写的；最初取自 humanlayer 的 `show-me` 技能（<https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md>），现在已不含 `show-me` 的原文。

| 段落 | 我们的意图 |
| --- | --- |
| 开头到 `## Put the page where the user is looking` 那一节 | 接上 `wait-what` 的语境，并规定呈现面：有渲染 HTML 的工具就用它，纯 CLI 才落盘再打开。不点任何 host 的名字——`host neutrality` 不许按 host 名分支，写成按能力判断的自然语言，新 host 出现也不过时 |
| `## Draw the page` 第一段 | 页面的样子和页上每张图交给 `diagram-design` 技能，让本仓库所有向用户解释的 HTML 用同一套设计系统。`diagram-design` 判定表格或一句话比图更清楚时（它的 §2、§3 都这样说），那张表或那句话照样放在这一页上：这一分支无论如何都交一页，不能因为不画图就没有页。末句点名免掉 `diagram-design` §3 的「Confirm before drawing」：内容就是用户刚看不懂的那条消息，已经定了，再停一轮确认只是让用户多等一次 |
| `## Draw the page` 下 `The reader knows nothing about this topic.` 那段 | 定读者（对主题一无所知）和图、字的分工：图管是什么与怎么连，字只做图做不到的三件事（图答的是哪个问题、重点在哪、由此得出什么），字重复图就删字，图要一段话才看得懂就重画。四个用 HTML 做解释的技能放的是同一段 |

`show-me` 原来那七种视图（伪代码、调用树、组件树、文件树、Mermaid、四种 diff、整块代码）和它的 `### guidance` 不收：它们是给读代码的人看的表示法；同一份列表逐字出现在 mattpocock 的 `pr` 技能（`mmw-v2/upstream/skills/in-progress/pr/SKILL.md` 的 `### Summary`），那里的读者是审 PR 的人。`wait-what` 的读者不读代码。`show-me` 的 `Skip the preamble and keep prose brief.` 一句也不收，它与读者那段「字只做图做不到的三件事」说的是同一件事。`show-me` 更新 → 不跟。

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改过，为了让 Codex 上的 user 也看得见 `visual` 这个开关——那边不显示 `argument-hint`，这行是唯一的发现入口。上游改这行 → 收上游的措辞，把 `visual` 接回去 |
| `policy.allow_implicit_invocation: false` | 上游原文，没改；`SKILL.md` 的 `disable-model-invocation: true` 一起留着。规则见 [README.md](README.md#disable-model-invocation) |

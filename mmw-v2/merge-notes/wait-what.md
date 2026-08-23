# wait-what

源目录：`mmw-v2/upstream/skills/productivity/wait-what/`

## 逐段意图

### SKILL.md

| 段落 | 我们的意图 |
| --- | --- |
| frontmatter 的 `argument-hint` | 我们加的，上游没有。给用户一个开关：不带参数走原来的文字重讲，带 `visual` 走 `VISUAL.md`。上游自己加 `argument-hint` → 取上游的，把 `visual` 这一支并进去 |
| 正文末尾 `Tagged \`visual\`:` 那一句 | 我们加的整句，是 `VISUAL.md` 的唯一入口。上游改了它上面那句重讲指令的措辞 → 收上游，这一句原样接在后面。上游把重讲拆成多句 → 接在最后 |
| 正文第一句（重讲指令） | 上游原文，没改，全取上游 |

### VISUAL.md

`mattpocock/skills` 里没有这个文件，subtree pull 不会碰它。

正文是 humanlayer 的 `show-me` 技能，逐字照抄（<https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md>，2026-08 取）。那些示例块——伪代码、调用树、组件树、文件树、Mermaid、四种 diff、整块代码——是这份提示词的主体，一个字都不改写。

| 段落 | 我们的意图 |
| --- | --- |
| 开头到 `## Put the page where the user is looking` 那一节 | 我们写的。接上 `wait-what` 的语境，并规定呈现面：有渲染 HTML 的工具就用它，纯 CLI 才落盘再打开。不点任何宿主的名字——五宿主平权禁止按宿主名分支，写成能力语言，新宿主出现也不过时 |
| `## Views` 这个标题 | 替掉 show-me 的第一句 `Help the user understand the current topic of conversation visually.`——那句的职责已经由本文件第 3 行承担。同段后半句 `Skip the preamble...` 照抄，末尾加一句「每种视图都放在那一页上」 |
| 各视图条目与全部示例块 | show-me 原文逐字。上游 show-me 更新 → 重新逐字取，只把下面这一条的改动重做一遍 |
| 最末一条（原文的 `For a visual UI, ... write one focused HTML file` + `Bash(open ...)`） | 只有这一条改了表述。原文里写 HTML 是「太密的东西才走」的条件分支，还写死了 macOS 的 `open` 和工作目录里的文件名。我们无论如何都出一页 HTML，交付也已由上面那节处理，所以改成「承载这些的那一页本身就是可视化」。原文的实质要求全部留着：形态自选（图解／信息图／短幻灯）、配色排版跟产品走、真实标签与数据、桌面和手机都要支持 |
| `### guidance` | show-me 原文逐字 |

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改过，为了让 Codex 侧的用户也看得见 `visual` 这个开关——那边不显示 `argument-hint`，这行是唯一的发现入口。上游改这行 → 收上游的措辞，把 `visual` 接回去 |
| `policy.allow_implicit_invocation: false` | 上游原文，没改。它和 `SKILL.md` 的 `disable-model-invocation: true` 必须同设 |

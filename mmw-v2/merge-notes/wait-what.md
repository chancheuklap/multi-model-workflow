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

整份是我们写的，上游没有这个文件。上游更新不会碰它。

内容改写自 humanlayer/skills 的 `show-me` 技能（<https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md>，2026-08 取）。取它的**视图选择判断表**——什么内容配哪种视图。三处按本仓库的规矩改掉：

- 上游 show-me 把视图当聊天里的 code fence 发，只有 HTML 那一条例外。我们全部收敛成一页 HTML，于是「这个宿主渲不渲染 Mermaid」不再是问题——图在 HTML 里永远成立。
- 上游写死 `Bash(open ...)`，是 macOS 命令，也假定宿主只能靠文件系统交付。改成按呈现能力判断：有渲染 HTML 的工具就用它，纯 CLI 才落盘再打开。不点任何宿主的名字。
- 上游把文件写在工作目录里。改成工作目录之外的临时位置，别脏了用户的仓库。

### agents/openai.yaml

| 字段 | 我们的意图 |
| --- | --- |
| `interface.short_description` | 改过，为了让 Codex 侧的用户也看得见 `visual` 这个开关——那边不显示 `argument-hint`，这行是唯一的发现入口。上游改这行 → 收上游的措辞，把 `visual` 接回去 |
| `policy.allow_implicit_invocation: false` | 上游原文，没改。它和 `SKILL.md` 的 `disable-model-invocation: true` 必须同设 |

# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

这个目录里 squash 原文有的文件与 `5b1a4c51` 逐字节相同。它不装进任何 host。`skills.txt` 装的是 `self/to-tickets`，即分叉 `mmw-v2/skills/to-tickets/`。两者同名，`install.sh` 拒绝重名。拉 upstream 时这个目录照常取上游；上游的改进要不要进分叉，读上游的 diff 后在分叉里改。分叉的文字归 `mmw` 技能的 `references/skill-set-rules.md` 与结构 lint 管。

## 本仓的文字在哪里

| 本仓的文字 | 现在在哪里 |
| --- | --- |
| 开头一段、第 2–8 步、票模板、路径规则 | `mmw-v2/skills/to-tickets/SKILL.md` |
| `ambiguity-scan.md`、`person-ticket.md` | 分叉同名文件 `mmw-v2/skills/to-tickets/references/ambiguity-scan.md`、`mmw-v2/skills/to-tickets/references/person-ticket.md` |
| `cutting-interface-tickets.md` | `mmw-v2/skills/to-tickets/references/screen-contract-tickets.md` |
| 第 20 行 | P1 **Write a spec and tickets** 的步骤顺序与 **Where you are.** |
| 第 160 行第 2 句 | P1 **Write a spec and tickets** 的 **Hand to the night** |
| 派子代理的通用做法 | `mmw` 技能的 `## Subagents` |
| 开关 | 同 `to-spec`：分叉不带 `agents/openai.yaml`，frontmatter 只有 `name` 与 `description` |

各段当初为什么这样写，记在这份说明在 `1dc33ec5` 的版本里（`git show 1dc33ec5:mmw-v2/merge-notes/to-tickets.md`）。

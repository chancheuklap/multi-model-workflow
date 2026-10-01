# to-tickets

源目录：`mmw-v2/upstream/skills/engineering/to-tickets/`

这个目录里 squash 原文有的文件与 `5b1a4c51` 逐字节相同。装的是分叉 `mmw-v2/skills/to-tickets/`；分叉与拉 upstream 的规则见 [README](README.md) `## 上游目录只允许两类改动`。

## 本仓的文字在哪里

| 本仓的文字 | 现在在哪里 |
| --- | --- |
| 开头一段、第 2–8 步、票模板、路径规则 | `mmw-v2/skills/to-tickets/SKILL.md` |
| `ambiguity-scan.md`、`person-ticket.md` | 分叉同名文件 `mmw-v2/skills/to-tickets/references/ambiguity-scan.md`、`mmw-v2/skills/to-tickets/references/person-ticket.md` |
| `cutting-interface-tickets.md` | `mmw-v2/skills/to-tickets/references/screen-contract-tickets.md` |
| `1dc33ec5` 的 `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 20 行，句首「A plan or a conversation with no published spec」 | P1 **Write a spec and tickets** 的步骤顺序与 **Where you are.** |
| `1dc33ec5` 的 `mmw-v2/upstream/skills/engineering/to-tickets/SKILL.md` 第 160 行第 2 句，句首「When the batch is a spec's night run」 | P1 **Write a spec and tickets** 的 **Hand to the night** |
| 派子代理的通用做法 | `mmw` 技能的 `## Subagents` |
| 开关 | 同 `to-spec`：分叉不带 `agents/openai.yaml`，frontmatter 只有 `name` 与 `description` |

各段当初为什么这样写，记在这份说明在 `1dc33ec5` 的版本里（`git show 1dc33ec5:mmw-v2/merge-notes/to-tickets.md`）。

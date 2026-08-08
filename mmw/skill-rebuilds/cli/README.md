# CLI rebuild

`candidate/` 是 `mmw/cli/` 的完整副本，在 review 期间独立演进。现役 `mmw/cli/` 不动。

候选与现役的关系跟技能一样：这里改完、跟七个技能候选一起验过之后，再整体替换现役 `mmw/cli/`。

## 为什么 CLI 要一起 rebuild

这个 CLI 只有 agent 会跑。一个 agent 跑它的时候正带着大量上下文，没有余力去猜参数、去试错、去翻源码。所以每一条命令都要在帮助文本里把三件事说全：

1. 这条命令干什么，输出长什么样（几列、怎么分隔、每列是什么）。
2. 每个参数的值从哪来 —— 是 map 正文里读的、是上游技能交回的、还是自己起的名字。
3. 失败时该怎么办 —— 改哪个输入，还是换一张 ticket，而不是重试或绕开这条命令。

技能候选精简之后，一部分原本写在技能正文里的参数来源和约束应该落到 CLI 帮助文本里，由 CLI 自己说清楚。技能只负责说"在这一步跑这条命令"。

## 已落地的修改

全部集中在 `candidate/mmw` 的 `usage_*` 函数和 `candidate/seeds/CONTEXT-MAP-rules.md`。**命令行为一行没改**，只改帮助文本和注入文本。

| 位置 | 改了什么 |
| --- | --- |
| `usage_task` | 每条子命令单独成段。补上 `--from` 什么时候要给 map 分支、`state` 的四个取值、以及哪些子命令在哪个宿主上可用 |
| `usage_result` | 把 `verify` 和 `merge` 各自检查了什么写全。补一句三个参数都由交回结果的一方给出，SHA 对不上时不要重试、不要改用 `git merge` 绕过去 |
| `usage_issue` | 说明 `--body-file` 收的是文件路径不是正文；说明 `--label` 的取值由调用它的技能给；`frontier` 补上空输出的含义和退出码；`claim` 补上失败时改取下一张；末尾列出这五条之外要直接用的四条 `gh` 命令 |
| `usage_domain` | `path` 的三种形态各自写清"照它做什么"；`adr-next` 补上并行会话不要提前取号、先用 `draft-` 命名；`check` 补上退出码非 0 时这次修改不算完成 |
| `usage_path` | 参数取值来源逐条列出；安全路径段的字符规则写成实际规则（首字符字母或数字，其余只能字母、数字、点、下划线、连字符，不能含斜杠，不能是 `.` 或 `..`）；补一句不合规时改传入值、不要自己拼路径 |
| `seeds/CONTEXT-MAP-rules.md` | 注入 Context Map 顶部的 7 条规则压成一句。原来那 7 条在 `AGENTS.md` 的「领域上下文」和 `/mmw-domain-modeling` 里都已经有，注入块重复一遍只占上下文 |

## 未决

见 `mmw/skill-rebuilds/` 顶层讨论：

- `mmw path` 的六个 kind 要不要合并。取证已经并进 `/mmw-research`，实测台账写在 `mmw path research` 底下，所以 `evidence` 这个 kind 在七个技能候选里已经没有任何消费者。现役 `mmw/skills/mmw-prototype` 和 `mmw/skills/mmw-wayfinder` 还在用它，所以 `candidate/mmw` 里先原样留着，等其余技能也有 candidate 之后一起决定删不删。
- `mmw issue` 要不要补齐 comment / close / view / edit。现在候选里这四个动作直接用 `gh`。

两件都会改到命令行为，还没有做。

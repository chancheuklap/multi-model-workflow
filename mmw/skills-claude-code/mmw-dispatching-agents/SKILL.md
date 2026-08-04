---
name: mmw-dispatching-agents
description: 把一件任务派给隔离上下文的 subagent——派不派、派哪个角色、怎么收回。需要把任务派出去时用它。
---

把一件任务派给隔离上下文的 subagent。

本技能供 **Claude Code** 使用。派发由 `mmw dispatch` 执行：模型、档位、护栏、沙箱写在 adapter 与 `.mmw.json` 里，技能正文不出现型号。

## 派不派

**默认派。** 下面四种情况才自己做：

| 什么情况自己做 | 为什么 |
| --- | --- |
| 要跟用户一来一回 | subagent 问不到人 |
| 这条结论要你对用户负责 | 派出去的结论本身又要验证，没有尽头 |
| 中途要换判断方向，事先写不出 brief | 只能边看边定 |
| 一句话就做完 | 派发的往返比做本身还慢 |

第三条要收紧：**subagent 内部的试错照派**。探一块代码本来就是查了这里才知道要查那里，那种试错它自己就能做完整个来回，一份 brief 说得清要回答什么就够了。只有需要**你**换判断方向的才留下——比如追一个 bug 时，看到这次埋点的输出才知道下一个探针埋在哪。

同一件活反复做很多遍时，先看能不能只派其中机械的那一半：验证可以拆成取证和判定，取证派得出去，判定派不出去（`/mmw-verifying-agent-output`）。

**一个方向派一个人。** 要几个方向就派几个，每份 brief 只有方向那一栏不同。要并行就在一条消息里发多个 Bash 调用起多个 `mmw dispatch`；拿到 `mode: host-tool` 的回执后，再在一条消息里调用各自的宿主工具。

## 派哪个角色

角色有哪几个、参数怎么写，跑 `mmw dispatch` 不带参数看用法。这里只留它答不了的两条：哪一道审派哪两个角色，判据在 `/mmw-review`；`worker` 什么时候升 `worker-high-risk`，判据在 `/mmw-implement`。

派会写文件的角色之前，工作区必须干净，`mmw dispatch` 会先查——否则提交里会混进别人的改动。

## 怎么派

1. 按「组装与存盘」写好 brief 文件。
2. 用 Bash、`run_in_background: true` 起：
   ```bash
   mmw dispatch <角色> --brief <文件> [--cwd <目录>]
   ```
   可写角色 `--cwd` 必填。
3. 读回执第一行 `mode:`。

**`mode: executed`** —— CLI 已跑完。

```
mode: executed
report: <报告文件的绝对路径>
exit: 0
```

读 `report:` 即为交回报告。

**`mode: host-tool`** —— 要调会话内工具，CLI 只给参数。

```
mode: host-tool
tool: <Agent|Bash>
brief: <提示词文件的绝对路径>
skill-path: <方法论文件的绝对路径>     ← 可能没有
params: {"...": "..."}
```

调用时**原样**传递 `params:` 的 JSON。禁止按记忆重拼、禁止删键、禁止只挑熟悉字段。

| `tool:` | 输入 |
| --- | --- |
| `Agent` | `brief:` 文件全文作提示词；有 `skill-path:` 时要求 subagent 先读该路径；`params` 原样带上 |
| `Bash` | `command` 已带齐，直接调用（含 `run_in_background`） |

adapter 已写入后台标记。工具先交 run id，完成后再通知。收到 run id 后继续不依赖报告的工作；没有独立工作时把控制权交回宿主，完成后再读报告。

起 `mmw dispatch` 时一律使用 Bash 的 `run_in_background: true`。

## 方法论怎么到它手里

长的、改得勤的方法论（审查、计划、TDD）：GPT 侧靠 `install-agent-skills.sh` 软链进 Codex 技能目录；Claude 侧回执若有 `skill-path:`，要求 subagent 先读该绝对路径。装没装用 `mmw doctor` 看。

短的、不常改的**原文粘进 brief**，例如给 `worker` 的 `mmw-implement/worker-brief.md` 与 TDD 纪律（清单在 `/mmw-implement` 第 3 步）。

**插件内路径只在回执出现 `skill-path:` 时才写进提示词。** 被审仓库里的路径可以给。

同一个视角派给两个角色时用**同一份 brief 文本**，只有「你负责哪个视角」那一栏不同。

派发前自检：brief 里提到的每个仓库内路径真实存在，缺了当场报错。

## 组装与存盘

各技能组装 brief 时照这里做，各自不再复述：粘进 brief 的内容一律现从文件里读再粘，不凭记忆复述。提示词和完工报告落 worktree 根的 `.dispatch/`，写之前 `mkdir -p`。这个目录已在仓库根 `.gitignore` 里。审查那一道的落点不同，按 `/mmw-review` 落 `.reviews/`。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 派出去的都交回了报告 | **移交**：`/mmw-verifying-agent-output`，逐条验证过才能用，绝不原样转发 |
| 报告里说它自己停下了 | **自己继续**：读它的尝试记录，把你看到的连同原来那份 brief 写成一份新的 brief，重派一次。不要试图续接原来那个会话——护栏和模型档要重新固定，重派比续接干净 |
| 派发前自检发现 brief 里有不存在的仓库内路径 | **自己继续**：当场修掉路径再派 |
| `mmw doctor` 说方法论没装 | **自己继续**：按它那一行给的路径跑安装脚本，装好再派。不要改成把方法论粘进提示词 |
| 要派会写文件的角色，`mmw dispatch` 报工作区不干净 | **停**：报那个目录里有哪些未提交的改动 |
| `mmw dispatch` 报认不出宿主 | **停**：报这台机器上 CLI 认不出自己跑在哪个宿主里 |
| Codex 报 `model is not supported when using Codex with a ChatGPT account` | **停**：八成是这台机器的型号缓存旧了，不是 `.mmw.json` 写错。让用户在 Codex 里刷一次，再看 `~/.codex/models_cache.json` 的 `models[].slug` 里有没有这个型号。**没验证到缓存里确实没有之前不要改 `.mmw.json`**，更不要动用户的 `~/.codex/config.toml` |

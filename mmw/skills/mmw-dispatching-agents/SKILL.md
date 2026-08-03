---
name: mmw-dispatching-agents
description: 把一件任务派给隔离上下文的 subagent——派不派、派哪个角色、怎么收回。需要把任务派出去时用它。
---

把一件任务派给隔离上下文的 subagent。

派发这个动作由 `mmw dispatch` 执行。**模型、档位、护栏、沙箱、宿主差异全在它里面**，本技能正文和任何提示词里都不出现型号——换型号只改仓库根的 `.mmw.json`。

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

**一个方向派一个人。** 要几个方向就派几个，每份 brief 只有方向那一栏不同。要并行就在一条消息里发多个 Bash 调用起多个 `mmw dispatch`；拿到 `mode: host-tool` 的回执后，再在一条消息里调用各自的宿主工具。adapter 给每次调用都带了后台参数，所以同轮调用不会争抢前台。

## 派哪个角色

角色有哪几个、各做什么、参数怎么写，跑 `mmw dispatch` 就有。这里只留它答不了的两条：哪一道审派哪两个角色，判据在 `/mmw-review`；`worker` 什么时候升 `worker-high-risk`，判据在 `/mmw-implement`。

派会写文件的角色之前，它那棵 worktree 的工作区必须干净，`mmw dispatch` 会先查——否则它的提交里会混进别人的改动。

## 返回怎么读

`mmw dispatch` 有两种返回，第一行的 `mode:` 说明是哪一种。

**`mode: executed`** —— CLI 已经把这个 subagent 跑完了。

```
mode: executed
report: <报告文件的绝对路径>
exit: 0
```

读 `report:` 那个文件就是它交回来的报告。

**`mode: host-tool`** —— 这次派发要用宿主的会话内工具，CLI 跑不了，只给你参数。

```
mode: host-tool
tool: <工具名>
brief: <提示词文件的绝对路径>
skill-path: <方法论文件的绝对路径>     ← 可能没有这一行
params: {"...": "..."}
```

调用宿主工具时原样传递 `params:` 的 JSON。

| `tool:` | 输入 |
| --- | --- |
| `Agent`、`subagent` | 把 `brief:` 文件全文作为提示词；有 `skill-path:` 时，要求 subagent 先读该路径 |
| `Bash` | `command` 已带齐 brief 与执行参数，直接调用 |

adapter 已在 `params:` 中写入后台参数。宿主工具先交回 run id，完成后再发通知。收到 run id 后继续不依赖报告的工作；没有独立工作时把控制权交回宿主，收到完成通知后再读报告。

起 `mmw dispatch` 时一律使用 Bash 的 `run_in_background: true`。`mode: executed` 的 subagent 跑在该后台 Bash 里。`mode: host-tool` 的 Bash 只返回参数，adapter 负责把真正的 subagent 固定成后台执行。

## 方法论怎么到它手里

长的、改得勤的方法论（审查那一整套、写计划那一套、测试标准）**装进它自己的技能目录**，`mmw dispatch` 会按宿主把它送到位，你不用管送法。装没装用 `mmw doctor` 看。

短的、不常改的**原文粘进提示词**，比如给 `worker` 的 `mmw-implement/worker-brief.md` 和 TDD 纪律（要粘哪几个文件，清单在 `/mmw-implement` 第 3 步）。代价是提示词长，而且改了之后已经派出去的那批读的还是旧的。

**插件内路径只在返回里出现 `skill-path:` 那一行时才给。** 其余情况派出去的那个模型看不见我们的插件文件，给了它读不到。被审仓库里的路径可以给——它就在那个仓库里，读得到。

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

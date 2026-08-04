---
name: mmw-dispatching-agents
description: 把一件任务派给隔离上下文的 subagent——派不派、派哪个角色、怎么收回。需要把任务派出去时用它。
---

把一件任务派给隔离上下文的 subagent。

**型号、思考档、async、context、skill 不出现在技能正文，也不由主 agent 手填。**
它们写在各宿主原生 agent 的 frontmatter 里（`mmw agents materialize` 从 `.mmw.json` 生成），或由 Claude Code 的 `mmw dispatch` adapter 写入工具参数。

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

**一个方向派一个人。** 要几个方向就派几个，每份 brief 只有方向那一栏不同。

## 派哪个角色

| 角色 | 原生 agent 名 | 可写 |
| --- | --- | --- |
| `worker` | `mmw-worker` | 是 |
| `worker-high-risk` | `mmw-worker-high-risk` | 是 |
| `planner` | `mmw-planner` | 是 |
| `investigator` | `mmw-investigator` | 否 |
| `reviewer-gpt` | `mmw-reviewer-gpt` | 否 |
| `reviewer-claude` | `mmw-reviewer-claude` | 否 |

也可用 `mmw agents list` / `mmw agents resolve <角色>` 查询。表与 `mmw/agent-src/roles.json` 不一致时以 `roles.json` 为准。

哪一道审派哪两个角色，判据在 `/mmw-review`；`worker` 什么时候升 `worker-high-risk`，判据在 `/mmw-implement`。

## 怎么派（按宿主）

先认宿主：环境变量 `PI_CODING_AGENT` 有值是 Pi；`CLAUDECODE` 有值是 Claude Code；Cursor 走原生 subagent，与 Pi 同一套步骤。拿不准时看 `mmw doctor` 报的宿主行。

### A. 原生 subagent 宿主（Pi、Cursor）

**不要跑 `mmw dispatch`。** 策略已在原生 agent 文件里，再经 CLI 转发是绕路。

1. 按「组装与存盘」写好 brief 文件。
2. 可写角色先护栏：
   ```bash
   mmw agents guard <角色> --cwd <worktree绝对路径>
   ```
   不干净或缺 `--cwd` 会非零退出；只读角色可省略 guard，或只跑 `mmw agents resolve <角色>`。
3. 确认 agent 名（上表或 `mmw agents resolve <角色>` 的 `agent:` 行）。
4. 把 brief 文件**全文**读进内存，作为 `task`（禁止摘要）。
5. 调宿主原生工具，**只传**这些：
   - `agent`：上表名字（如 `mmw-planner`）
   - `task`：brief 全文
   - `cwd`：可写角色必给；只读可给仓库根或省略（Pi 上建议给明确路径）
6. **禁止**再传 `model`、`thinking`、`context`、`async`、`skill`。这些在 agent frontmatter 里；手传会覆盖默认值或漏字段。

Pi 工具名是 `subagent`。并行时在**同一条消息**里发多个 `subagent` 调用。

agent 文件由 `mmw agents materialize --host pi`（或 `cursor`）生成。改型号只改 `.mmw.json` 再物化，不要手改生成物里的 model 行。

### B. Claude Code

会话内 Claude 走 `Agent` 工具；GPT 走后台 `Bash`+Codex。主 agent **不要**手拼 Codex 命令或型号。

1. 按「组装与存盘」写好 brief 文件。
2. 用 Bash、`run_in_background: true` 起：
   ```bash
   mmw dispatch <角色> --brief <文件> [--cwd <目录>]
   ```
   可写角色 `--cwd` 必填；CLI 会查工作区是否干净。
3. 读回执第一行 `mode:`：

**`mode: executed`** —— CLI 已跑完（少见；内部二次 dispatch 后可能出现）。

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

并行：一条消息里多个后台 `mmw dispatch`；拿到 `host-tool` 回执后，再一条消息里调各自的 `Agent`/`Bash`。

## 方法论怎么到它手里

| 宿主 | 长方法论（审查、计划、TDD） |
| --- | --- |
| Pi / Cursor | 写在原生 agent 的 `skill` frontmatter 里，宿主注入 |
| Claude Code · GPT | `install-agent-skills.sh` 软链进 Codex 技能目录；`mmw doctor` 可查 |
| Claude Code · Claude | 回执若有 `skill-path:`，要求 subagent 先读该绝对路径 |

短的、不常改的**原文粘进 brief**，例如给 `worker` 的 `mmw-implement/worker-brief.md` 与 TDD 纪律（清单在 `/mmw-implement` 第 3 步）。

**插件内路径只在 Claude Code 回执出现 `skill-path:` 时才写进提示词。** 其余情况派出去的模型看不见插件文件。被审仓库里的路径可以给。

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
| `mmw agents guard` 报工作区不干净 | **停**：报那个目录里有哪些未提交的改动 |
| `mmw doctor` 说方法论没装（Claude Code / Codex） | **自己继续**：按它那一行给的路径跑安装脚本，装好再派。不要改成把方法论粘进提示词 |
| Claude Code 上 `mmw dispatch` 报认不出宿主 | **停**：报这台机器上 CLI 认不出自己跑在哪个宿主里 |
| Codex 报 `model is not supported when using Codex with a ChatGPT account` | **停**：八成是这台机器的型号缓存旧了，不是 `.mmw.json` 写错。让用户在 Codex 里刷一次，再看 `~/.codex/models_cache.json` 的 `models[].slug` 里有没有这个型号。**没验证到缓存里确实没有之前不要改 `.mmw.json`**，更不要动用户的 `~/.codex/config.toml` |

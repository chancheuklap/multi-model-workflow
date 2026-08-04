---
name: mmw-dispatching-agents
description: 把一件任务派给隔离上下文的 subagent——派不派、派哪个角色、怎么收回。需要把任务派出去时用它。
---

把一件任务派给隔离上下文的 subagent。

本技能供 **Pi / Cursor** 使用。主 agent **直调宿主原生 subagent**。
型号、思考档、async、context、skill 已写在原生 agent 的 frontmatter 里（`mmw agents materialize` 从 `.mmw.json` 生成），调用时不要手填、不要覆盖。

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

**一个方向派一个人。** 要几个方向就派几个，每份 brief 只有方向那一栏不同。并行时在同一条消息里发多个原生 subagent 调用。

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

## 怎么派

1. 按「组装与存盘」写好 brief 文件。
2. 可写角色先护栏：
   ```bash
   mmw agents guard <角色> --cwd <worktree绝对路径>
   ```
   不干净或缺 `--cwd` 会非零退出。只读角色可省略，或只跑 `mmw agents resolve <角色>`。
3. 确认 agent 名（上表或 `resolve` 的 `agent:` 行）。
4. 把 brief 文件**全文**读进内存作为 `task`（禁止摘要）。
5. 调宿主原生 subagent 工具，**只传**：
   - `agent`：上表名字（如 `mmw-planner`）
   - `task`：brief 全文
   - `cwd`：可写角色必给
6. **禁止**传 `model`、`thinking`、`context`、`async`、`skill`。

Pi 上工具名是 `subagent`。Cursor 上用该宿主注册的等价原生 agent 调用，字段同样只有 agent / task / cwd。

改型号只改 `.mmw.json` 再执行 `mmw agents materialize --host pi` 或 `--host cursor`，不要手改生成物里的 model 行。

## 方法论怎么到它手里

长方法论（审查、计划、TDD）写在原生 agent 的 `skill` frontmatter 里，由宿主注入。
短的、不常改的**原文粘进 brief**，例如给 `worker` 的 `mmw-implement/worker-brief.md` 与 TDD 纪律（清单在 `/mmw-implement` 第 3 步）。

被审仓库里的路径可以给。不要把插件内部路径写进 brief，除非该路径在 subagent 工作目录内可读。

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

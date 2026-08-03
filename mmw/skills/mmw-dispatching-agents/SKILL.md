---
name: mmw-dispatching-agents
description: 把一件任务派给隔离上下文的 subagent——Claude 会话内 subagent，或 Codex headless 进程。管选后端、固定模型档位、护栏、brief 自包含、怎么收回。需要把任务派出去时用它。
---

把一件任务派给隔离上下文的 subagent。

模型和档位一律从目标仓库的 `docs/agents/models.md` 取。**本技能正文和任何提示词里都不出现型号**——换型号只改 `docs/agents/models.md`。

## 派不派

**默认派。** 下面四种情况才自己做：

| 什么情况自己做 | 为什么 |
| --- | --- |
| 要跟用户一来一回 | subagent 问不到人 |
| 这条结论要你对用户负责 | 派出去的结论本身又要验证，没有尽头 |
| 中途要换判断方向，事先写不出 brief | 只能边看边定 |
| 一句话就做完 | 派发的往返比做本身还慢 |

第三条要收紧：**subagent 内部的试错照派**。探一块代码本来就是查了这里才知道要查那里，那种试错它自己就能闭环，一份 brief 说得清要回答什么就够了。只有需要**你**换判断方向的才留下——比如追一个 bug 时，看到这次埋点的输出才知道下一个探针埋在哪。

同一件活反复做很多遍时，先看能不能只派其中机械的那一半：验证可以拆成取证和判定，取证派得出去，判定派不出去（`/mmw-verifying-agent-output`）。

**一个方向派一个人。** 要几个方向就派几个，并行，每份 brief 只有方向那一栏不同。

## 两个后端

| 后端 | 怎么起 | 什么时候用 |
| --- | --- | --- |
| Claude | `Agent` 工具，`subagent_type: general-purpose` | 派 Claude |
| Codex | `codex exec` headless 进程，Bash 后台起 | 派 Codex |

派哪个模型由 `docs/agents/models.md` 的红线定：每一道审至少有一个视角的审查者与作者不是同一个模型。

### Codex headless 怎么起

```bash
codex exec -C . --sandbox read-only --color never \
  -m <模型> -c model_reasoning_effort="<档位>" \
  -o <报告文件> \
  - < <提示词文件>
```

- 用 Bash 的 `run_in_background: true` 跑。
- `-o` 把它最后一条消息写进报告文件。读那个文件就是报告，不用从事件流里取。
- 提示词走 stdin，所以先用 Write 把它写成文件。
- 派可写任务时换 `--sandbox workspace-write`。**首次派发前工作区必须干净。**
- **要它自己提交，还得单独放开 `.git`。** `workspace-write` 默认把 `.git` 锁成只读，工人写完代码会卡在 `.git/index.lock: Operation not permitted`。加这个覆盖：

  ```bash
  -c 'sandbox_workspace_write.writable_roots=["<worktree 绝对路径>/.git"]'
  ```

  派它的时候要说清：只许 `add` 加 `commit`，不许 `amend`、`rebase`、`reset` 或强推。
- 续接用 `codex exec ... resume <会话号> "<追问>"`。**resume 不继承原来的护栏和模型档，整套重新固定。** 会话号要用就加 `--json` 起，在事件流的 `thread_id` 里。
- **不用 `codex review`。**

## 方法论怎么到它手里

headless 那一侧看不见我们的插件文件。有两条路解决，按方法论的长短选：

| 怎么送 | 什么时候用 | 代价 |
| --- | --- | --- |
| **装进它自己的技能目录** | 长、改得勤的，比如审查那一整套 | 要装一次。派之前先确认装了没有，没装先装再派 |
| **原文粘进提示词** | 短、不常改的，比如给写码工人的 `mmw-implement/worker-brief.md` 和 TDD 纪律（要粘哪几个文件，清单在 `/mmw-implement` 第 3 步） | 提示词长；改了之后已经派出去的那批读的还是旧的 |

安装走软链不走拷贝。安装脚本是本文旁边的 `install-agent-skills.sh`，它装三份技能：`mmw-reviewer`（审查方法论）、`mmw-planner`（写计划方法论）、`mmw-tdd`（测试标准）。

**两条路都不把插件内路径给 headless 那个模型。** 被审仓库里的路径可以给——它 `-C .` 就在那个仓库里，读得到。会话内的 subagent 不受这条限制，它读得到插件里的原件，给绝对路径即可。

同一个视角派给两个模型时用**同一份 brief 文本**，只有「你负责哪个视角」和那句方法论路径不同。

派发前自检：brief 里提到的每个仓库内路径真实存在，缺了当场报错。

## 存盘

工人的提示词和完工报告落 worktree 根的 `.dispatch/`，写之前 `mkdir -p`。这个目录已在仓库根 `.gitignore` 里。

## 并行

一条消息里发多个 `Agent` 调用，它们并行跑。派给 Codex 的那些各自后台起，也并行。两边可以同时在跑。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 派出去的都交回了报告 | **移交**：`/mmw-verifying-agent-output`，逐条验证过才能用，绝不原样转发 |
| 报告里说它自己停下了 | **自己继续**：读它的尝试记录，把你看到的发回去，用 `resume` 续接同一个会话。**resume 不继承原来的护栏和模型档，整套重新固定** |
| 派发前自检发现 brief 里有不存在的仓库内路径 | **自己继续**：当场修掉路径再派 |
| 要派的活靠安装脚本送方法论，但 Codex 自己的技能目录里没有 | **自己继续**：先跑安装脚本装好再派，不要改成把方法论粘进提示词 |
| 要派可写任务，但工作区不干净 | **停**：报工作区里有哪些未提交的改动 |

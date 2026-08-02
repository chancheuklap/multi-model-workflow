---
name: mmw-dispatching-agents
description: 把一件任务派给隔离上下文的 subagent——Claude 会话内 subagent，或 Codex headless 进程。管选后端、固定模型档位、护栏、brief 自包含、怎么收回。需要把任务派出去时用它。
---

把一件任务派给隔离上下文的 subagent。

模型和档位一律从目标仓库的 `docs/agents/models.md` 取。**本技能正文和任何提示词里都不出现型号**——换型号只改 `docs/agents/models.md`。

## 两个后端

| 后端 | 怎么起 | 什么时候用 |
| --- | --- | --- |
| Claude | `Agent` 工具，`subagent_type: general-purpose` | 派 Claude |
| Codex | `codex exec` headless 进程，Bash 后台起 | 派 Codex |

派哪个模型由 `models.md` 的红线定：每一道审至少有一个视角的审查者与作者不是同一个模型。

### Codex headless 怎么起

```bash
codex exec -C . --sandbox read-only --color never \
  -m <模型> -c model_reasoning_effort="<档位>" \
  -o <报告文件> \
  - < <提示词文件>
```

- 用 Bash 的 `run_in_background: true` 起。审一轮、写一份计划，都常常超过前台超时上限。
- `-o` 把它最后一条消息写进报告文件。读那个文件就是报告，不用从事件流里取。
- 提示词走 stdin，所以先用 Write 把它写成文件。
- 派可写任务时换 `--sandbox workspace-write`。**首次派发前工作区必须干净**，否则验收读 diff 时分不清哪些改动是它的。
- **要它自己提交，还得单独放开 `.git`。** `workspace-write` 默认把 `.git` 锁成只读，工人写完代码会卡在 `.git/index.lock: Operation not permitted`。加这个覆盖：

  ```bash
  -c 'sandbox_workspace_write.writable_roots=["<worktree 绝对路径>/.git"]'
  ```

  放开之后它理论上也能改历史，所以派它的时候要说清：只许 `add` 加 `commit`，不许 `amend`、`rebase`、`reset` 或强推。
- 续接用 `codex exec ... resume <会话号> "<追问>"`。**resume 不继承原来的护栏和模型档，整套重新固定。** 会话号要用就加 `--json` 起，在事件流的 `thread_id` 里。
- **不用 `codex review`。** 它自带提示词，会绕过我们的审查方法。

## 方法论怎么到它手里

headless 那一侧看不见我们的插件文件。给它一个插件内路径，它读不到，然后自己编一个。有两条路解决，按方法论的长短选：

| 怎么送 | 什么时候用 | 代价 |
| --- | --- | --- |
| **装进它自己的技能目录** | 长、改得勤的，比如审查那一整套 | 要装一次。派之前先确认装了没有，没装先装再派 |
| **原文粘进提示词** | 短、不常改的，比如给写码工人的那几份纪律 | 提示词长；改了之后已经派出去的那批读的还是旧的 |

装载走软链不走拷贝，插件里改一次，下一轮读到的就是新的。装载脚本是本文旁边的 `install-agent-skills.sh`，它装审查方法论、写计划方法论和测试那一份。

**两条路都不把插件内路径给 headless 那个模型。** 被审仓库里的路径可以给——它 `-C .` 就在那个仓库里，读得到。会话内的 subagent 不受这条限制，它读得到插件里的原件，给绝对路径即可。

同一个视角派给两个模型时用**同一份 brief 文本**，只有「你负责哪个视角」和那句方法论路径不同。

派发前自检：brief 里提到的每个仓库内路径真实存在。缺了当场报错，不让它开工之后才发现。

## 存盘

工人的提示词和完工报告落 worktree 根的 `.dispatch/`，写之前 `mkdir -p`。这个目录随 worktree 一起死，已在仓库根 `.gitignore` 里，不进 git。

## 并行

一条消息里发多个 `Agent` 调用，它们并行跑。派给 Codex 的那些各自后台起，也并行。两边可以同时在跑。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 派出去的都交回了报告 | **移交**：`/mmw-verifying-agent-output`。报告是证据不是结论，逐条验证过才能用，绝不原样转发 |
| 报告里说它自己停下了 | **自己继续**：读它的尝试记录，把你看到的发回去，用 `resume` 续接同一个会话。**resume 不继承原来的护栏和模型档，整套重新固定** |
| 派发前自检发现 brief 里有不存在的仓库内路径 | **自己继续**：当场修掉路径再派，不要让它开工之后才发现 |
| 要派的活靠装载送方法论，但 Codex 自己的技能目录里没有 | **自己继续**：先跑装载脚本装好再派，不要改成把方法论粘进提示词 |
| 要派可写任务，但工作区不干净 | **停**：报工作区里有哪些未提交的改动。工作区不干净，验收读 diff 时分不清哪些改动是它的 |

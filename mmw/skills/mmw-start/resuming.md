# 回来接着做

用户不带内容叫 `/mmw-start`，或者当前 checkout 已绑定任务分支，问的都是同一件事：这个任务现在走到哪一步。

没有状态文件要读。每一步都有一件落在 git 或 GitHub 上的产物对应它，查产物在不在就够了。

## 有哪些任务在进行

运行 `git worktree list --porcelain`。已绑定分支的 linked worktree 是进行中的任务。**slug 是分支名最后一个 `/` 之后的部分**——slug 本身不含斜杠，所以有斜杠就一定是宿主的命名空间前缀（Codex App 是 `codex/`）。detached worktree 尚未绑定，不替用户猜 slug。只有一项就直接查；有多项就把分支名和进度报给用户选择。

## 一个任务走到哪一步

审查记录目录是 `.reviews/`。按顺序查，第一个查不到的地方就是它停下的地方。

| 想知道 | 怎么查 |
| --- | --- |
| 当初用户要的是什么 | 分支上第一个提交的正文，也就是那个空提交：`git log --reverse --format='%B' $(git merge-base HEAD <父分支>)..HEAD \| head -20`。`<父分支>` 是这条任务分支分叉出来的那条：普通任务是仓库默认分支，从 Wayfinder map 派生的是 map 分支（map 正文的 `## 分支` 一节记着它） |
| 是不是一个 `/mmw-wayfinder` 的 effort | 有没有一张打 `wayfinder:map` 标签的 issue 指向这个 slug |
| 这张 map 走到哪一步了 | `mmw issue children <map 编号>`：一行一张，带状态、认领人、被几张挡着 |
| 有几张 decision ticket 在同时推进 | 查从该任务分支派生的 worktree 与结果分支。**结果分支**是派出去的角色在自己那棵树上写代码用的分支，做完由主 agent 用 `mmw result verify` 收、`mmw result integrate` 合；每个结果分支只对应一张 decision ticket |
| spec 有没有写出来 | `docs/specs/<slug>/` 在不在，里面的文件有没有提交进分支 |
| spec 过没过用户那道关卡 | 先反查那张 spec issue：`gh issue list --search "docs/specs/<slug>/<slug>.md" --state all --json number,title,labels`。`/mmw-to-spec` 发布时把 spec 的精确路径写进了 issue 正文，所以搜得到。它在、而且带 `ready-for-agent`，才算过了这道关卡。**下面几行里的 `<spec issue 编号>` 就是它的编号** |
| ticket 有没有拆 | `mmw issue children <spec issue 编号>` 有没有输出 |
| plan 写了没有 | `docs/plans/<slug>/` 在不在，里面的份数跟 ticket 数对不对得上 |
| 合同锚点回填了没有 | spec 的 `## Cross-Plan Contract Anchors` 一节在不在、精确字段补实了没有 |
| plan 审过没过 | 逐张读取 open tracer bullet ticket；全部带 `ready-for-agent` 才算通过 |
| 做到第几张 ticket | `mmw issue children <spec issue 编号>`：closed 的是做完的，open 且有认领人的是正在做的 |
| 终审有没有跑 | `.reviews/<slug>-final.md` 在不在 |
| 有没有归档 | `mmw wiki ensure` 把 Wiki 克隆到本地并输出那个目录的路径，看该目录下 `Spec-<slug>.md` 在不在 |

审查记录目录随 worktree 存活，不进 Git。它是空的不代表没做过，只代表这台机器上这一轮没做过。以提交记录和 issue 状态为准。

spec 文件已经提交、issue 却还没发布，是个中间状态：用户可能刚点完头，也可能还没看过。这时按没过这道关卡处理，重新给他看一次。

有 open tracer bullet ticket 缺少 `ready-for-agent` 时，回 `/mmw-to-plan`。全部齐全后，才进入 `/mmw-implement`。

## 查完之后

用业务语言报三句：这个任务当初要做什么、现在完成了哪些、下一步归谁。然后调起下一步该走的那个技能接着走。

用户报的 slug 在任务分支和 worktree 清单中都找不到，按新任务处理，回 `SKILL.md` 第 1 步。

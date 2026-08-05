# 回来接着做

用户不带内容叫 `$mmw:mmw-start`，或者当前 checkout 已绑定任务分支，问的都是同一件事：这个任务现在走到哪一步。

没有状态文件要读。每一步都有一件落在 git 或 GitHub 上的产物对应它，查产物在不在就够了。

## 有哪些任务在进行

运行 `git worktree list --porcelain`。已绑定分支的 linked worktree 是进行中的任务；分支名按当前宿主的任务命名规则给出 slug。detached worktree 尚未绑定，不替用户猜 slug。只有一项就直接查；有多项就把分支名和进度报给用户选择。

## 一个任务走到哪一步

按顺序查，第一个查不到的地方就是它停下的地方。

| 想知道 | 怎么查 |
| --- | --- |
| 当初用户要的是什么 | 分支上第一个提交的正文，也就是那个空提交：`git log --reverse --format='%B' $(git merge-base HEAD <父分支>)..HEAD \| head -20` |
| 是不是一个 `$mmw:mmw-wayfinder` 的 effort | 有没有一张打 `wayfinder:map` 标签的 issue 指向这个 slug |
| 这张 map 走到哪一步了 | `mmw issue children <map 编号>`：一行一张，带状态、认领人、被几张挡着 |
| 有几条链在同时跑 | 查从该任务分支派生的 worktree 与结果分支；每个结果分支是一条链 |
| spec 有没有写出来 | `docs/specs/<slug>/` 在不在，里面的文件有没有提交进分支 |
| spec 是否已发布并可进入拆 ticket | 那张 spec issue 在不在、带没带 `ready-for-agent` 标签。这两样齐了才算发布步骤完成；用户批准本身仍以 `$mmw:mmw-to-spec` 的 spec 定稿人工审批关卡为准 |
| ticket 有没有拆 | `mmw issue children <spec issue 编号>` 有没有输出 |
| plan 写了没有 | `docs/plans/<slug>/` 在不在，里面的份数跟 ticket 数对不对得上 |
| 合同锚点回填了没有 | spec 的 `## Cross-Plan Contract Anchors` 一节在不在、精确字段补实了没有 |
| plan 审过没过 | `.reviews/` 里有没有 ② plan 审那一轮的审查记录。回填排在审之前，回填了不代表审过 |
| 做到第几张 ticket | `mmw issue children <spec issue 编号>`：closed 的是做完的，open 且有认领人的是正在做的 |
| 终审有没有跑 | `.reviews/` 里有没有终审报告 |
| 有没有归档 | `mmw wiki ensure` 取到副本，看 `Spec-<slug>.md` 在不在 |

`.reviews/` 随 worktree 存活，不进 git。它是空的不代表没做过，只代表这台机器上这一轮没做过——以提交记录和 issue 状态为准。

spec 文件已经提交、issue 却还没发布，是个中间状态：无法从持久产物判断用户是否已经批准。这时重新执行 `$mmw:mmw-to-spec` 的 spec 定稿人工审批关卡：批准对象是 spec 定稿、审查处置和 seam 清单，批准人是用户，通过凭据是用户明确批准这三项，通过后发布 spec issue。

## 查完之后

用业务语言报三句：这个任务当初要做什么、现在完成了哪些、下一步归谁。然后调起下一步该走的那个技能接着走。

用户报的 slug 在任务分支和 worktree 清单中都找不到，按新任务处理，回 `SKILL.md` 第 1 步。

# 回来接着做

用户不带内容叫 `/mmw-start`，或者会话已经在一个任务 worktree 里，问的都是同一件事：这个任务现在走到哪一步。

没有状态文件要读。每一步都有一件落在 git 或 GitHub 上的产物对应它，查产物在不在就够了。

## 有哪些任务在进行

```bash
git worktree list
```

`.worktrees/` 下的每一棵都是一个进行中的任务，目录名就是它的 slug。只有一棵就直接查它；有好几棵就把清单连同各自的进度报出来，让用户挑。

## 一个任务走到哪一步

按顺序查，第一个查不到的地方就是它停下的地方。

| 想知道 | 怎么查 |
| --- | --- |
| 当初用户要的是什么 | 分支上第一个提交的正文，也就是那个空提交：`git log --reverse --format='%B' $(git merge-base HEAD <父分支>)..HEAD \| head -20` |
| 是不是一个 `/mmw-wayfinder` 的 effort | 有没有一张打 `wayfinder:map` 标签的 issue 指向这个 slug |
| 这张 map 走到哪一步了 | 查 frontier：还剩几张没人认领，几张有 assignee 正在别的会话里解 |
| 有几条链在同时跑 | `.worktrees/` 下以这个 slug 开头、但不等于这个 slug 的目录，每一棵是一条链 |
| spec 有没有写出来 | `docs/specs/<slug>/` 在不在，里面的文件有没有提交进分支 |
| spec 过没过用户那道关卡 | 那张 spec issue 在不在、带没带 `ready-for-agent` 标签。这两样齐了才算过了这道关卡 |
| ticket 有没有拆 | 那张 spec issue 有没有子 issue（`docs/agents/issue-tracker.md`） |
| plan 写了没有 | `docs/plans/<slug>/` 在不在，里面的份数跟 ticket 数对不对得上 |
| 合同锚点回填了没有 | spec 的 `## Cross-Plan Contract Anchors` 一节在不在、精确字段补实了没有 |
| plan 审过没过 | `.reviews/` 里有没有 ② plan 审那一轮的审查记录。回填排在审之前，回填了不代表审过 |
| 做到第几张 ticket | 子 issue 里哪些已经关掉；还开着的里面谁有 assignee，那张就是正在做的 |
| 终审有没有跑 | `.reviews/` 里有没有终审报告 |
| 有没有归档 | Wiki 上 `Spec-<slug>.md` 在不在（`docs/agents/wiki.md`） |

`.reviews/` 和 `.dispatch/` 随 worktree 存活，不进 git。它们是空的不代表没做过，只代表这台机器上这一轮没做过——以提交记录和 issue 状态为准。

spec 文件已经提交、issue 却还没发布，是个中间状态：用户可能刚点完头，也可能还没看过。这时按没过这道关卡处理，重新给他看一次。

## 查完之后

用业务语言报三句：这个任务当初要做什么、现在完成了哪些、下一步归谁。然后调起下一步该走的那个技能接着走。

用户报的 slug 在 `.worktrees/` 下找不到，按新任务处理，回 `SKILL.md` 第 1 步。

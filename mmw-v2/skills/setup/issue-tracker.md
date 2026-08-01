# Issue tracker:GitHub Issues

本仓库 issue 全在 GitHub。所有操作走 `gh`，仓库从 `git remote -v` 自动推断（在 clone 内运行 `gh` 会自己认出来）。

## 基本操作

- **建**：`gh issue create --title "..." --body "..."`（多行 body 用 heredoc）
- **读**：`gh issue view <n> --comments`
- **列**：`gh issue list --state open --json number,title,body,labels --jq '[.[] | {number, title, body, labels: [.labels[].name]}]'`，按需加 `--label` / `--state`
- **评论**：`gh issue comment <n> --body "..."`
- **打 / 摘标签**：`gh issue edit <n> --add-label "..."` / `--remove-label "..."`
- **关**：`gh issue close <n> --comment "..."`

标签词汇见 `triage-labels.md`。

## issue 承载身份，文件承载内容

一条铁律，先讲清楚再讲层级：**issue 正文只放这件事是什么、现在什么状态、内容在哪**，真正要反复打磨的长文放任务分支上的文件里。

理由是 issue 正文没有逐行差异。设计要过审、要返工，在 issue 正文上改，你看不出改了哪几个字，也没法确认审查意见真被吸收了。文件在 git 里就都有。而 issue 那些好处——原生父子、原生阻塞、UI 里看得见谁被谁挡住、关掉即归档——一样不丢。

## 层级

常态两层。跑了 `wayfinder`（把一整块活画成一张决策地图，逐条把雾散掉的技能）就是三层，因为一张地图可能派生出好几份设计。

| 层 | 正文放什么 | 权威内容在哪 | 结局 |
| --- | --- | --- | --- |
| 地图（跑了 `wayfinder` 才有） | 目的地、已定决策的一行索引、范围外、还在雾里的部分 | 就在正文——它本来就是索引不是文档 | 关掉，不上 Wiki |
| 设计 | 一段摘要说清要解决什么问题 + 指向分支上设计文档的路径 + 切片清单 | 任务分支的 `docs/design/<slug>/` | 落地后转一页 Wiki（见 `wiki.md`） |
| 切片 | 一段摘要 + 指向分支上该切片计划的路径 + 阻塞关系 | 任务分支的 `docs/plans/<slug>/` | 并进设计那页 Wiki 的章节 |

- **子 issue**：GitHub 原生 sub-issue（`gh api` 的 sub-issues 端点）。未启用时退化：父 body 用任务清单列出，子 body 顶部写 `Part of #<父编号>`。
- **阻塞关系**：GitHub 原生 issue dependencies，UI 里看得见。加边：
  ```bash
  gh api --method POST repos/<owner>/<repo>/issues/<子>/dependencies/blocked_by -F issue_id=<阻塞方的 database id>
  ```
  `database id` 用 `gh api repos/<owner>/<repo>/issues/<n> --jq .id` 取——不是 `#编号`，也不是 `node_id`。不可用时退化成子 body 顶部一行 `Blocked by: #<n>, #<n>`。
- **下一个能开工的切片**：父 issue 的 open 子 issue 中，`issue_dependencies_summary.blocked_by == 0` 且无 assignee 的，按父 body 里的顺序取第一个。
- **认领**：`gh issue edit <n> --add-assignee @me`。这是开工前的第一个写动作。

## Wayfinding operations

`wayfinder` 会来查这一节。它问的是地图、决策票、阻塞、frontier 在本仓库怎么表达——答案就是上面那套，加上一条它专用的：

- **地图**：一张 GitHub issue，打 `wayfinder:map` 标签。这个标签既不是状态也不是类型，只是「这张 issue 是一张地图」的记号（见 `triage-labels.md`）。
- **决策票**：地图的子 issue，一张决策票对应一个待定的决策。
- **阻塞**：原生 issue dependencies，加边命令见上。
- **frontier 查询**：地图的 open 子 issue 中，`issue_dependencies_summary.blocked_by == 0` 且无 assignee 的全部——注意这里要的是全部，不是取第一个。`wayfinder` 允许你并行开几张决策票。
- **决策的答案**：作为结案评论贴在决策票上，关掉它，再往地图的「已定决策」追加一行指针。**难以回退、有真取舍的那些还要另写一份架构决策记录**，别只留在评论里——评论区是最难检索的地方（见本文件最后一节的分流表）。

`wayfinder` 找不到本节时会退化成拿本地 markdown 文件当 issue 追踪器。本仓库有 GitHub，不要走那条退路。

## 技能里的说法对应什么动作

- 「发布到 issue tracker」= 建一张 GitHub issue，长文另落文件、正文只留摘要和路径
- 「取相关 issue」= `gh issue view <n> --comments`

## 设计与计划文档的生命周期

三段，落地是分界点：

1. **任务期间**：落在任务 worktree 的 `docs/design/<slug>/` 与 `docs/plans/<slug>/`，提交进任务分支。打磨过程因此受 git 保护，改坏了能回退。
2. **代码落地后**：转成 GitHub Wiki，Wiki 从此是这份设计的唯一真相源。命名、页面结构、写入顺序和核验清单全在 `wiki.md`。
3. **合回上一层之前**：在任务分支上删掉本地那两个目录并提交，然后再合并。主线因此不留设计和计划文档，不会随项目演进变成过时残留。

第 3 步必须等 `wiki.md` 那三条核验全过才能做——本地文档一删就没有第二份了。

## `wayfinder` 的产物不上 Wiki，但也不能死

设计文档是地图的可读综合版——地图的目的地变成设计的问题陈述，每条已定决策变成设计的「已定实现决策」，范围外原样继承。正因为是综合版，两个都上 Wiki 就是两页内容重叠的东西摆在一起，读者不知道哪个权威。留综合版，不留原始日志。

但地图上那些决策不能随任务一起消失，它们的归宿是仓库：

| 产物 | 去哪 | 为什么 |
| --- | --- | --- |
| 难以回退、有真取舍的决策 | `docs/adr/` | 改代码时同一次 diff 就能看见相关决策，Wiki 看不见 |
| 考察过但决定不做的方向 | `.out-of-scope/`，一个概念一个文件 | 分诊时按概念相似度查它，防止同一个需求换个说法再提一遍 |
| 沉淀下来的术语 | `CONTEXT.md` | 见 `domain.md` |
| 其余可回退的决策 | 被设计文档的「已定实现决策」吸收 | 不值得单独归档 |
| 地图本身 | 关掉即止 | 它是按走过顺序记的过程日志，含死路，价值在过程中 |

这些都写在 `wayfinder` 自己那个 worktree 的分支上，随整块活一起合回主线，中途不提前合（见 `worktrees.md`）。

审查留痕和终审报告不走上面任何一条路：它们一次性写入、不打磨，落 **worktree 根的 `.reviews/`**，随 worktree 一起死，不进 git 也不进 Wiki。这个目录已在仓库根 `.gitignore` 里，写的时候 `mkdir -p` 即可，不需要另铺脚手架。搁置项里有长期价值的那部分已经开成 issue 了（见 `triage-labels.md`）。

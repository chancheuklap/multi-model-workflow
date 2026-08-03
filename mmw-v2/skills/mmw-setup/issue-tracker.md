# Issue tracker:GitHub Issues

本仓库 issue 全在 GitHub。所有操作走 `gh`，仓库从 `git remote -v` 自动推断。

## 基本操作

- **建**：`gh issue create --title "..." --body "..."`（多行 body 用 heredoc）
- **读**：`gh issue view <n> --comments`
- **列**：`gh issue list --state open --json number,title,body,labels --jq '[.[] | {number, title, body, labels: [.labels[].name]}]'`，按需加 `--label` / `--state`
- **评论**：`gh issue comment <n> --body "..."`
- **打 / 摘标签**：`gh issue edit <n> --add-label "..."` / `--remove-label "..."`
- **关**：`gh issue close <n> --comment "..."`

标签词汇见 `triage-labels.md`。

## issue 承载身份，文件承载内容

**issue 正文只放这件事是什么、现在什么状态、内容在哪**，真正要反复打磨的长文放任务分支上的文件里。

## 层级

常态两层。跑了 `/mmw-wayfinder` 就是三层。

| 层 | 正文放什么 | 权威内容在哪 | 结局 |
| --- | --- | --- | --- |
| map（跑了 `/mmw-wayfinder` 才有） | `Destination`、`Decisions so far` 的一行索引、`Out of scope`、`Not yet specified` | 就在正文 | 关掉，不上 Wiki |
| spec | 一段摘要说清要解决什么问题 + 指向分支上 spec 文件的路径 + ticket 清单 | 任务分支的 `docs/specs/<slug>/` | 落地后转一页 Wiki（见 `wiki.md`） |
| ticket | 一段摘要 + 指向分支上该 ticket 计划的路径 + 阻塞关系 | 任务分支的 `docs/plans/<slug>/` | 并进 spec 那页 Wiki 的章节 |

- **子 issue**：GitHub 原生 sub-issue（`gh api` 的 sub-issues 端点）。未启用时退化：父 body 用任务清单列出，子 body 顶部写 `Part of #<父编号>`。
- **阻塞关系**：GitHub 原生 issue dependencies，UI 里看得见。加边：
  ```bash
  gh api --method POST repos/<owner>/<repo>/issues/<子>/dependencies/blocked_by -F issue_id=<阻塞方的 database id>
  ```
  `database id` 用 `gh api repos/<owner>/<repo>/issues/<n> --jq .id` 取——不是 `#编号`，也不是 `node_id`。不可用时退化成子 body 顶部一行 `Blocked by: #<n>, #<n>`。
- **下一个能开工的 ticket**：父 issue 的 open 子 issue 中，`issue_dependencies_summary.blocked_by == 0` 且无 assignee 的，按父 body 里的顺序取第一个。
- **认领**：`gh issue edit <n> --add-assignee @me`。这是开工前的第一个写动作。

## Wayfinding operations

`/mmw-wayfinder` 会来查这一节。它问的是 map、decision ticket、阻塞、frontier 在本仓库怎么表达——答案就是本文「基本操作」与「层级」两节，另加下面这几条它专用的：

- **map**：一张 GitHub issue，打 `wayfinder:map` 标签。这个标签既不是状态也不是类型，只是「这张 issue 是一张 map」的记号（见 `triage-labels.md`）。
- **decision ticket**：map 的子 issue，一张对应一个待定的决定，带一个 `wayfinder:<类型>` 标签（见 `triage-labels.md`）。
- **阻塞**：原生 issue dependencies，加边命令见本文「层级」一节。
- **frontier 查询**：map 的 open 子 issue 中，`issue_dependencies_summary.blocked_by == 0` 且无 assignee 的全部——注意这里要的是全部，不是取第一个。`/mmw-wayfinder` 允许几个会话各认领一条 decision ticket 链同时跑。
- **决定的答案**：作为结案评论贴在 decision ticket 上，关掉它，再往 map 的 `Decisions so far` 追加一行指针。**难以回退、有真取舍的那些还要另写一份 ADR**，别只留在评论里（见本文「`/mmw-wayfinder` 的产物不上 Wiki，但也不能死」一节的产物去向表）。

`/mmw-wayfinder` 找不到本节时会退化成拿本地 markdown 文件当 issue 追踪器。本仓库有 GitHub，不要走那条退路。

## 技能里的说法对应什么动作

- 「发布到 issue tracker」= 建一张 GitHub issue，长文另落文件、正文只留摘要和路径
- 「取相关 issue」= `gh issue view <n> --comments`

## spec 与计划文档的生命周期

三段，落地是分界点：

1. **任务期间**：落在任务 worktree 的 `docs/specs/<slug>/` 与 `docs/plans/<slug>/`，提交进任务分支。
2. **代码落地后**：转成 GitHub Wiki，Wiki 从此是这份 spec 的唯一事实来源。命名、页面结构、写入顺序和验证清单全在 `wiki.md`。
3. **合回上一层之前**：在任务分支上删掉本地的 `docs/specs/<slug>/` 与 `docs/plans/<slug>/` 并提交，然后再合并。主线因此不留 spec 和计划文档。

第 3 步必须等 `wiki.md` 的验证清单全部通过才能做。

**原型产物和取证台账不走这三段。** `docs/prototypes/<slug>/` 与 `docs/evidence/<slug>/` 随任务分支合回上一层，留在仓库里，不转 Wiki 也不删。

## `/mmw-wayfinder` 的产物不上 Wiki，但也不能死

spec 是 map 的可读综合版——map 的 `Destination` 变成 spec 的问题陈述，`Decisions so far` 里的每一条变成 spec 的 `Implementation Decisions`，`Out of scope` 原样继承。Wiki 只留综合版，不留原始日志。

但 map 上那些决定不能随任务一起消失，它们的归宿是仓库：

| 产物 | 去哪 | 为什么 |
| --- | --- | --- |
| 难以回退、有真取舍的决定 | `docs/adr/` | 改代码时同一次 diff 就能看见相关决定，Wiki 看不见 |
| 考察过但决定不做的方向 | `.out-of-scope/`，一个概念一个文件 | 分诊时按概念相似度查它，防止同一个需求换个说法再提一遍 |
| 沉淀下来的术语 | `CONTEXT.md` | 见 `domain.md` |
| 用户走查过的原型产物 | `docs/prototypes/<slug>/` | 逻辑模块会被搬进正式代码，界面变体是视觉契约的出处 |
| 实测出来的外部事实与原始产物 | `docs/evidence/<slug>/` | 记的是外部世界的表现，spec 归档之后仍然成立。重测要花钱花时间 |
| 其余可回退的决定 | 被 spec 的 `Implementation Decisions` 吸收 | 不值得单独归档 |
| map 本身 | 关掉即止 | 它是按走过顺序记的过程日志，含死路，价值在过程中 |

这些都写在 wayfinder 那棵 worktree 的分支上，随 effort 一起合回主线，中途不提前合（见 `worktrees.md`）。

派出去的 subagent 那些进出材料不走上面任何一条路：它们一次性写入、不打磨，随 worktree 一起死，不进 git 也不进 Wiki。审查记录和终审报告落 **worktree 根的 `.reviews/`**，派给工人的提示词和它交回的报告落 **`.dispatch/`**。两个目录都已在仓库根 `.gitignore` 里，写的时候 `mkdir -p` 即可，不需要另铺脚手架。搁置项里有长期价值的那部分已经开成 issue 了（见 `triage-labels.md`）。

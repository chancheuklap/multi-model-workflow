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

## 一份设计的 issue 形状

父 issue 一张，承载设计意图与验收条件；实施切片挂成它的子 issue。

- **子 issue**：GitHub 原生 sub-issue（`gh api` 的 sub-issues 端点）。未启用时退化：父 body 用任务清单列出，子 body 顶部写 `Part of #<父编号>`。
- **阻塞关系**：GitHub 原生 issue dependencies，UI 里看得见。加边：
  ```bash
  gh api --method POST repos/<owner>/<repo>/issues/<子>/dependencies/blocked_by -F issue_id=<阻塞方的 database id>
  ```
  `database id` 用 `gh api repos/<owner>/<repo>/issues/<n> --jq .id` 取——不是 `#编号`，也不是 `node_id`。不可用时退化成子 body 顶部一行 `Blocked by: #<n>, #<n>`。
- **下一个能开工的切片**：父 issue 的 open 子 issue 中，`issue_dependencies_summary.blocked_by == 0` 且无 assignee 的，按父 body 里的顺序取第一个。
- **认领**：`gh issue edit <n> --add-assignee @me`。这是开工前的第一个写动作。

## 技能里的说法对应什么动作

- 「发布到 issue tracker」= 建一张 GitHub issue
- 「取相关 issue」= `gh issue view <n> --comments`

## 设计与计划文档的生命周期

三段，落地是分界点：

1. **任务期间**：落在任务 worktree 的 `docs/design/<slug>/` 与 `docs/plans/<slug>/`，提交进任务分支。打磨过程因此受 git 保护，改坏了能回退。
2. **代码落地后**：把定稿转成 GitHub Wiki 页，Wiki 从此是这份设计的唯一真相源。
3. **合并前**：在任务分支上删掉本地那两个目录并提交，然后再合并。主线因此不留设计和计划文档，不会随项目演进变成过时残留。

## 开工顺序

worktree 和分支名带父 issue 编号（见 `worktrees.md`），所以顺序只能是：先建父 issue 拿到编号，再建 worktree。不能反过来。

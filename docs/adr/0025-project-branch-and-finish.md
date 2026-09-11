---
date: 2026-09-11
amends: [0023]
---

# 开夜记住并推送 project branch；用户验收后 `finish` 把 base branch 合回并清理

一夜的 base branch 从哪个 project branch 切出，在 `open` 时按固定证据顺序确定并写进 `spec.opened.project`。`open` 先把 project branch 与 base branch fast-forward 推到 origin；用户在 `spec.closed` 之后验收，main agent 才用 `finish` 把 `origin/<base branch>` 合回 project branch、检查、推送、记录 `spec.merged`，然后删除已经包含的 base branch 与干净 worktree。project branch 合回默认分支不属于 MMW。

## 两个时间边界

- 开夜以前，reflog、`branch.<base branch>.vscode-merge-base`、origin 上最近且唯一的共同历史依次提供 project branch；旧 `spec.opened.project` 优先于重新推导。默认分支、推导平手和任何 local/origin 分叉都拒绝，避免把猜测或覆盖写入 GitHub。
- `summary` 只说明 agent batch 已收完；用户验收才授权 `finish`。`finish` 先确认 spec 已关、project 已记录、没有另一夜共用同一 base branch，并逐张确认用过该 base branch 的 spec 下没有开票。
- 合并复用落票时的 detached merge worktree、repository checks、`MMW_BASE_REF` 和 fast-forward push 规则。冲突或检查失败保留两条分支及工作区，让证据仍可检查。
- `spec.merged` 是推送成功的事实，也是重跑边界：有它以后只补做逐项清理，不再产生第二个 merge commit。

## Considered Options

- **让用户在开夜前手工推两条分支。** 否决。`open` 已经能查出每条分支与 origin 的 ancestry；在 fast-forward 条件内把同一事实落到 origin，不需要把机械步骤交回用户。
- **只记录 base branch，收夜时再猜 project branch。** 否决。reflog 和本机配置可能已经消失，历史也可能随着别的合并出现新的平手；开夜时的来源才是这夜实际从哪里切出的证据。
- **`summary` 后立即自动合回 project branch。** 否决。`spec.closed` 只证明批次执行结束，不是用户接受产品结果；合回 project branch 会改变用户接下来验收的基线。
- **合回默认分支或删除 instance 数据。** 否决。前者是用户的发布决定，后者会删除验收与诊断状态；两者都超出收夜的 branch 清理。

## Consequences

- 本机和云端开始工作前都能取得 project branch 与 base branch；`spec.opened` 留下两者的永久对应。
- 用户验收前，project branch 不含这一夜的合并；验收后，一条 `finish` 命令完成受检查的合回和可安全重复的清理。
- 删除只发生在 base branch 已包含于 `origin/<project branch>` 之后；脏 worktree 和无法核对的分支保留，并打印人工补做命令。
- ADR 0023 中「本机领先就拒绝并由用户推送」的开夜后果不再成立；分叉仍拒绝，push 仍只允许 fast-forward。

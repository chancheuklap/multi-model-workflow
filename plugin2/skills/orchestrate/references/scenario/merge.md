# Merge · 多分支/PR 合并(场景操作指南)

> 用户要合并多个并行 worktree 时,orchestrate 路由到这里。**不开新 worktree**——在主仓库做,读全队 manifest + 设计文档,按序合回。
>
> **理念(PDF)**:merge 的难点不是 git 文本冲突,是**业务意图 / 功能设计冲突**——两个任务各自改了同一块的设计、合起来语义打架。git 能自动合的不代表设计不冲突。

## 1. 看全队(一条命令)

```bash
mmw task team
```

逐个在管 worktree 一行:`slug / title / scenario / phase / status / branch / base_commit / design(设计文档路径) / open_items / subtasks`。据此排合并序、找冲突源。

## 2. 排序 + 查冲突(判断,留你)

- **只合 `status=ready-to-close`(或已 ④终审过)的**;没跑完的先别合。
- **合并序**:按 base_commit / 依赖排(被依赖的先合);拿不准问用户。
- **业务/设计冲突扫描**(merge 的命门,git 看不到):读各队员的设计文档(`design` 路径),找两份任务**碰同一功能/对象/合同却给了不同设计**的地方——例如都改了登录态模型、都动了同一张表的语义。这类冲突 **HITL 拍**(一次一个业务决策),不自己猜着合。

## 3. 逐个合(merge = 红线,要人批)

合回主分支是**唯一硬红线**(`guard-redline` PreToolUse 拦)。逐个:

1. 用户批准 → `mmw release-approve`(造一次性令牌)→ `git merge --no-ff <branch>`(**禁 `--squash`**,保留分支历史);令牌放行后即消费,下一个合并需重新批。
2. **git 文本冲突**:常规解。
3. **业务/设计冲突**(第 2 步扫出的):按 HITL 拍定的方向解,改的是让两份设计语义自洽,不是单纯选一边的文本。解完确保合并结果仍符合两份设计的意图(必要时跑相关测试)。
4. 合进主线后:`mmw task cleanup --slug <slug>` 删该 worktree + 分支 + 临时状态。

## 4. 收尾

全部合完 + 清理后,主分支上跑一遍相关测试确认没合坏。有跨任务的整体性疑问 → 可对合并结果起一次 ④final 级审(`mmw review start --stage final`)。

## 红线

- 不开新 worktree;在主仓库做。
- merge/push 要人批(red line);`--no-ff` 不 `--squash`。
- 业务/设计冲突交用户拍,不自己合掉语义分歧。

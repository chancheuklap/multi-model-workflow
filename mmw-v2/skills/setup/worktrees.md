# 任务隔离

正式任务在独立 git worktree 里做，**从你开口的那一刻就建**，不等 issue、不等 spec。这台机器上会有好几个 agent 同时干活，主线程和 Codex 工人不在同一棵树上，工人正在改的文件才不会在主线程读它时变形。

worktree 只是分支的载体，没有别的含义。它可以随便建、随便从别的 worktree 分叉，不是什么要小心对待的重资源。

## 粒度

默认**一份 spec 一个 worktree**：spec 拆出的几张 ticket 全在里面按顺序做完，整体合并一次、终审一次、Wiki 写一次。spec 是原子交付单元。

effort——比一份 spec 大、要好几份 spec 才做得完的那种——大到一次会话装不下、路还在雾里时，先跑 `wayfinder`（把 effort 画成一张决策 map，逐条把雾散掉的技能）。它有自己的 worktree，而且**一张 map 可能派生出好几份 spec**。这时的分叉关系是：

```
主线
 └── payments-overhaul          ← wayfinder 的 worktree
      ├── phone-login           ← 从 payments-overhaul 分支分叉
      └── refund-window         ← 同上
```

**问题没解决之前不合回主线。** spec worktree 从 `wayfinder` 分支分叉，做完合回 `wayfinder` 分支；effort 收尾时 `wayfinder` 分支才合回主线。`wayfinder` 期间写下的术语、ADR、拒掉的方向因此对所有兄弟 spec 都可见，不用提前往主线塞半成品。

确实能并行的 ticket 也照这个办法从当前 worktree 的分支分叉。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在 `.worktrees/` 下。

## 命名

名字叫 **slug**：一个 kebab 短语，说清这次做什么，例如 `phone-login`。不带 issue 编号、不带日期、不带前缀。

**一个 slug 贯穿四处**——worktree 目录名、分支名、`docs/specs/<slug>/`、Wiki 上的 `Spec-<slug>.md`。别的文件提到 `<slug>` 时指的都是它。

不带编号不丢任何东西：GitHub 把分支、PR 和 issue 串起来靠的是提交信息里的 `#42` 和 PR 正文的关键词，不靠分支名。带编号反而逼你先建 issue 才能开工，而 issue 是干着干着才建的。

日期在提交记录里，不用编进名字。同名冲突时加个区分词，别加序号。

## 落点与建法

仓库内 `.worktrees/`，已进 `.gitignore`。

```bash
# 从主线开一个新任务
git worktree add -b <name> .worktrees/<name> main

# 从父 worktree 的分支分叉（wayfinder 派生 spec、拆并行 ticket 都走这个）
git worktree add -b <name> .worktrees/<name> <父分支名>
```

然后 `EnterWorktree({ path: ".worktrees/<name>" })` 进去——只有这一步能切会话工作目录，脚本切不了。

**会话限制**：`EnterWorktree` 从主仓库按路径进没问题；但同一个会话里从一个 worktree 直接跳到另一个 worktree 时，它只认 `.claude/worktrees/` 下的目标。我们是一个任务一个会话，正常撞不上；真要跳先回主仓库。

## 目录用到才建

新 worktree 里不预先铺 `docs/specs/`、`docs/plans/`、`.reviews/`、`.dispatch/` 这些目录。真要写第一个文件时 `mkdir -p` 一下就够了。

空目录是噪音：它会让人以为该有内容却没有，也会让技能误判前一步是不是跑过。`.gitignore` 该挡的在 `/setup` 时已经一次挡掉，不需要每个 worktree 再铺一份脚手架。

## 清理

worktree 在使用期持久，可以跨天，中途别删。

合并进上一层（父分支或主线）后向用户报一句、等他点头，再删 worktree、删分支、清掉里面的临时文件。删目录不可逆，而且里面可能还有没提交的东西，所以不自动清。

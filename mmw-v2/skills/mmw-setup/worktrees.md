# 任务隔离

正式任务在独立 git worktree 里做，**从你开口的那一刻就建**，不等 issue、不等 spec。主 agent 和 Codex 工人不在同一棵树上。

worktree 只是分支的载体，没有别的含义。它可以随便建、随便从别的 worktree 分叉，不是什么要小心对待的重资源。

## 粒度

默认**一份 spec 一个 worktree**：spec 拆出的几张 ticket 全在里面按顺序做完，整体合并一次、终审一次、Wiki 写一次。spec 是原子交付单元。

effort——比一份 spec 大、要好几份 spec 才做得完的那种——哪几份 spec、按什么顺序都还罩着 fog of war 时，先跑 `/mmw-wayfinder`。它有自己的 worktree，而且**一张 map 可能派生出好几份 spec**。这时的分叉关系是：

```
主线
 └── payments-overhaul          ← wayfinder 的 worktree
      ├── phone-login           ← 从 payments-overhaul 分支分叉
      └── refund-window         ← 同上
```

**问题没解决之前不合回主线。** spec worktree 从 wayfinder 分支分叉，做完合回 wayfinder 分支；effort 收尾时 wayfinder 分支才合回主线。期间写下的术语、ADR、决定不做的方向对所有兄弟 spec 都可见。

确实能并行的 ticket 也照这个办法从当前 worktree 的分支分叉。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在 `.worktrees/` 下。

## 命名

名字叫 **slug**，形状是 `<类型>-<短语>`：类型取 Conventional Commits 那一套，短语用 kebab 说清这次做什么。例如 `feat-phone-login`、`fix-refund-rounding`、`refactor-order-state`。

| 类型 | 用在 |
| --- | --- |
| `feat` | 新增用户可见的能力 |
| `fix` | 修一个缺陷 |
| `refactor` | 改内部结构，外部行为不变 |
| `perf` | 改性能 |
| `docs` | 只改文档 |
| `test` | 只改测试 |
| `chore` | 依赖、配置、构建脚本 |

类型写在前面，同时约束范围：一个 `fix` 里混进新功能，说明当初的类型定错了，或者这次改动该拆成两个。

**一个 slug 贯穿五处**——worktree 目录名、分支名、`docs/specs/<slug>/`、这个目录里的主文件 `<slug>.md`、Wiki 上的 `Spec-<slug>.md`。别的文件提到 `<slug>` 时指的都是它。主文件与目录同名。类型前缀用连字符而不是斜杠，斜杠会在 `.worktrees/` 下建出子目录，破坏「目录不嵌套」。

不带 issue 编号、不带日期。同名冲突时加一个区分词，不加序号。

## 落点与建法

仓库内 `.worktrees/`，已进 `.gitignore`。

```bash
# 从主线开一个新任务
git worktree add -b <name> .worktrees/<name> main

# 从父 worktree 的分支分叉（wayfinder 派生 spec、拆并行 ticket 都走这个）
git worktree add -b <name> .worktrees/<name> <父分支名>
```

然后 `EnterWorktree({ path: ".worktrees/<name>" })` 进去——只有这一步能切会话工作目录，脚本切不了。

**会话限制**：`EnterWorktree` 从主仓库按路径进没问题；但同一个会话里从一个 worktree 直接跳到另一个 worktree 时，它只认 `.claude/worktrees/` 下的目标。一个任务一棵树，正常撞不上；真要跳先回主仓库。

## 开工的第一个提交

进去之后先打一个空提交：

```bash
git commit --allow-empty -m "<slug>" -m "<用户交代这件事时的原话>"
```

原话原样记，不要替他概括——这条提交是几天后回来时唯一还留着他当初怎么说的地方。

它同时是这个任务的起点标记：`git merge-base` 取分支点取的就是它前面那一条，终审要的固定点因此不用另外记。

任务走到第几步不用状态文件，看产物在不在就知道：`docs/specs/<slug>/` 在不在、子 issue 谁开着谁有 assignee、`.reviews/` 里有没有终审报告、Wiki 上有没有那一页。

## 目录用到才建

新 worktree 里不预先铺 `docs/specs/`、`docs/plans/`、`docs/prototypes/`、`.reviews/`、`.dispatch/` 这些目录。真要写第一个文件时 `mkdir -p` 一下就够了。

空目录是噪音：它会让人以为该有内容却没有，也会让技能误判前一步是不是跑过。`.gitignore` 该挡的在 `/mmw-setup` 时已经一次挡掉，不需要每个 worktree 再铺一份脚手架。

## 清理

worktree 在使用期持久，可以跨天，中途别删。

合并进上一层（父分支或主线）后向用户报一句、等他确认，再删 worktree、删分支、清掉里面的临时文件。删目录不可逆，而且里面可能还有没提交的东西，所以不自动清。

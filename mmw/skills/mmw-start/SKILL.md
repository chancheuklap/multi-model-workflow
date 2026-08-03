---
name: mmw-start
description: 多模型工作流的入口——判定这次的任务走哪条路，定 slug，建 worktree 并进去，把用户原话记进第一个提交，然后移交给对应技能。用户开始一件新任务、提一个新需求、报一个 issue 编号、说要接着做某张 map、说有东西坏了、或者只说要开工时用它；没有交代任何内容时，它报当前任务的进度。
argument-hint: "[bug|big] [要做的事，或者一张 map 的编号]"
---

本技能只做路由，这次任务本身一个字都不实现。

本次输入：`$ARGUMENTS`

这一栏为空、用户也没有在对话里交代要做什么，走 [resuming.md](resuming.md)。已经在一个任务 worktree 里的，同样走 [resuming.md](resuming.md)。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。有标签就直接用，不要再推断。

| 情况 | 下一步 |
| --- | --- |
| 一张 map 的编号或链接，或者他说要接着做某张 map | **移交**：`/mmw-wayfinder` |
| 一个 issue 编号，带着某个 `wayfinder:` 类型标签——那是一张 map 上的一条 decision ticket | **移交**：`/mmw-wayfinder` |
| 一个 issue 编号，挂在一张带 `wayfinder:map` 标签的 issue 底下、自己不带 `wayfinder:` 标签——那是收尾时切出来的一份 spec | **移交**：`/mmw-to-spec` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`/mmw-triage` |
| 一个 issue 编号，已是 `ready-for-agent`，brief 写明 `**Test seam:**`，而且只碰一处 | **移交**：`/mmw-implement` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`/mmw-diagnosing-bugs` |
| 一个 effort，还不知道要拆成哪几份 spec，或者挂了 `big` | **移交**：`/mmw-wayfinder` |
| 想先看看某个界面长什么样，或者不确定一套状态模型对不对 | **移交**：`/mmw-prototype` |
| 只要一条查得清的事实，比如某个库或某个外部接口的官方说法 | **移交**：`/mmw-research`，跳过第 2、3 步 |
| 一个新需求，或对已有需求的改进 | **移交**：`/mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`/mmw-improve-codebase-architecture`，跳过第 2、3 步 |
| 几条并行分支要合到一起，或者合并冲突要解 | **移交**：`/mmw-review` 的 ⑥ 合并集成审，跳过第 2、3 步 |

**先做原型还是先谈清楚**：他要的是先看见一个能跑的东西，走 `/mmw-prototype`；他要的是先把这件事说清楚，走 `/mmw-grilling`。分不出来时走 `/mmw-grilling`。

**effort 怎么认**：判据是这件事要拆成几份 spec。一份 spec 说得完、拆出的 ticket 都挂在这份 spec 底下，走 `/mmw-grilling`。要好几份 spec 才做得完，而且哪几份、按什么顺序都还没有答案，才是 `/mmw-wayfinder`。

带 issue 编号的，先 `gh issue view <编号> --comments` 把它读出来再判，不要只看编号。标签的含义见 `/mmw-triage`。

## 2. 定 slug

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

类型取自第 1 步的判定结果：走 `/mmw-diagnosing-bugs` 的用 `fix`，新需求和先做原型的用 `feat`。类型同时约束范围——一个 `fix` 里混进新功能，说明当初的类型定错了，或者这次改动该拆成两个。

**一个 slug 贯穿五处**：worktree 目录名、分支名、`docs/specs/<slug>/`、这个目录里的主文件 `<slug>.md`、Wiki 上的 `Spec-<slug>.md`。别的技能提到 `<slug>` 时指的都是它。

类型前缀用连字符不用斜杠——斜杠会在 worktree 落点下建出子目录，破坏「目录不嵌套」。不带 issue 编号、不带日期。同名冲突时加一个区分词，不加序号。

**下面四种情况跳过这一步**，第 3 步也一并跳过：

- 用户报的是一张已有 map 的编号或链接。slug 由 `/mmw-wayfinder` 定。
- 判定走 `/mmw-improve-codebase-architecture`。slug 由它定，类型固定用 `refactor`。
- 判定走 `/mmw-research`。
- 判定走 `/mmw-review` 的 ⑥ 合并集成审。

## 3. 建 worktree、进去、记原话

```bash
mmw task new <slug> "<用户交代这件事时的原话>"
```

它一次做完三件事：建分支、建 worktree、打那个记原话的空提交。原话原样传，不要替他概括。

然后用宿主的工作目录切换工具进到它输出的那个路径（Claude Code 是 `EnterWorktree`，pi 是 `enter_worktree`；这一步脚本做不了，只有宿主工具做得到）。

不给基点时它从当前 HEAD 分叉，从主线开的新任务正好要这个。**这次任务是从一张 `/mmw-wayfinder` 的 map 派生出来的（用户报的是那张 map 切出来的 spec），就要显式给基点**：

```bash
mmw task new <slug> "<用户交代这件事时的原话>" --from <map 的 slug>
```

这个会话此刻还在主仓库，当前 HEAD 是主线，不是 map 分支；`git checkout` 也切不到 map 分支，它正被 map 的 worktree 占着。不给 `--from` 就会把这次任务错分叉到主线，map 上已经做出的决定一条都拿不到。

**粒度是一份 spec 一棵树。** 这份 spec 拆出的几张 ticket 全在这棵树里按顺序做完，整体合并一次、终审一次、Wiki 写一次。确实能并行的 ticket 从当前这棵树的分支再分叉出去（判据在 `/mmw-implement`）。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在同一个落点下。

树在整个任务期间持久，可以跨天，中途别删。**新树里不预先铺目录**：`docs/specs/`、`docs/plans/`、`docs/prototypes/`、`.reviews/`、`.dispatch/` 都是真要写第一个文件时 `mkdir -p` 一下就够。

报一句你定的 slug 和你要走的路线，然后接着做，不用停下来等用户确认。

**第 2 步列出的那四条路线，这一步同样跳过**，留在主仓库直接移交。一个会话只能进一次 worktree，在这里替它们建了，它们就没法再进自己那棵。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起第 1 步判出的那个技能，把用户原话原样传过去 |
| 第 1 步那张表哪一行都对不上，或者同时对上互相冲突的两行 | **停**：把你认为可能的那两三条路线连同各自的判据摆给用户，让他点一条。不要挑一条最像的就往下走 |

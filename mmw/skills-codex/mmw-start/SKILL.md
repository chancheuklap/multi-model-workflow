---
name: mmw-start
description: MMW 日常工作的统一路由器。用于开始或恢复一项 MMW 任务，且用户没有直接指定下游技能。
argument-hint: "[bug|big] [要做的事，或者一张 map 的编号]"
---

本技能只做路由，这次任务本身一个字都不实现。

本次输入：`$ARGUMENTS`

这一栏为空、用户也没有在对话里交代要做什么，走 [resuming.md](resuming.md)。

有输入时先运行 `mmw task state`。只有输出以 `bound` 开头，才走 [resuming.md](resuming.md)。`detached` 表示宿主已经准备好 worktree，但 MMW 尚未绑定任务；这时继续判定路线和 slug。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。有标签就直接用，不要再推断。

| 情况 | 下一步 |
| --- | --- |
| 一张 map 的编号或链接，或者他说要接着做某张 map | **移交**：`$mmw:mmw-wayfinder` |
| 一个 issue 编号，带着某个 `wayfinder:` 类型标签——那是一张 map 上的一条 decision ticket | **移交**：`$mmw:mmw-wayfinder` |
| 一个 issue 编号，挂在一张带 `wayfinder:map` 标签的 issue 底下、自己不带 `wayfinder:` 标签——那是收尾时切出来的一份 spec | **移交**：`$mmw:mmw-to-spec` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`$mmw:mmw-triage` |
| 一个 issue 或 PR 编号，已是 `ready-for-agent`，但没有完整 agent brief | **移交**：`$mmw:mmw-triage`，补齐 `Acceptance criteria`、范围边界和 `Test seam` |
| 一个 issue 编号，已是 `ready-for-agent`，整项工作可以作为一张 ticket 独立验收，只有一个已确认的测试 seam，而且没有未决设计取舍 | **移交**：`$mmw:mmw-implement` |
| 一个 issue 或 PR 编号，已是 `ready-for-agent`，但需要拆成多张 ticket、需要多个测试 seam，或者还有设计取舍要谈 | **移交**：`$mmw:mmw-to-spec` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`$mmw:mmw-diagnosing-bugs` |
| 一个 effort 超出一次 agent session，而且从当前状态到 destination 的路线还看不清，或者挂了 `big` | **移交**：`$mmw:mmw-wayfinder` |
| 想先看看某个界面长什么样，或者不确定一套状态模型对不对 | **移交**：`$mmw:mmw-prototype` |
| 只要一条查得清的事实，比如某个库或某个外部接口的官方说法 | **移交**：`$mmw:mmw-research`，跳过第 2、3 步 |
| 一个新需求，或对已有需求的改进 | **移交**：`$mmw:mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`$mmw:mmw-improve-codebase-architecture`，跳过第 2、3 步 |
| 几条并行分支要集成到当前目标分支，某条分支要跟上已经推进的目标分支，或者手上有一个正在进行中的冲突 | **移交**：`$mmw:mmw-integrate`，跳过第 2、3 步 |

**先做原型还是先谈清楚**：他要的是先看见一个能跑的东西，走 `$mmw:mmw-prototype`；他要的是先把这件事说清楚，走 `$mmw:mmw-grilling`。分不出来时走 `$mmw:mmw-grilling`。

**effort 怎么认**：同时满足两个条件才走 `$mmw:mmw-wayfinder`。第一，这件事超出一次 agent session 能容纳的范围。第二，从当前状态到 destination 的路线还看不清。最终形成一份还是多份 spec 不是入口判据。范围大但路线已经清楚时，直接进入 `$mmw:mmw-to-spec` 或 `$mmw:mmw-to-tickets`；路线模糊但一次会话能谈清时，走 `$mmw:mmw-grilling`。

带 issue 编号的，先 `gh issue view <编号> --comments` 把它读出来再判，不要只看编号。标签的含义见 `$mmw:mmw-triage`。

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

类型取自第 1 步的判定结果：走 `$mmw:mmw-diagnosing-bugs` 的用 `fix`，新需求和先做原型的用 `feat`。类型同时约束范围——一个 `fix` 里混进新功能，说明当初的类型定错了，或者这次改动该拆成两个。

**一个 slug 贯穿四处**：任务分支名、`docs/specs/<slug>/`、这个目录里的主文件 `<slug>.md`、Wiki 上的 `Spec-<slug>.md`。worktree 的物理目录由宿主管理，不参与任务识别。

slug 的类型前缀用连字符。不带 issue 编号，不带日期。同名冲突时加一个区分词，不加序号。宿主可以在分支名前增加固定命名空间；该命名空间不属于 slug。

**下面四种情况跳过这一步**，第 3 步也一并跳过：

- 用户报的是一张已有 map 的编号或链接。slug 由 `$mmw:mmw-wayfinder` 定。
- 判定走 `$mmw:mmw-improve-codebase-architecture`。slug 由它定，类型固定用 `refactor`。
- 判定走 `$mmw:mmw-research`。
- 判定走 `$mmw:mmw-integrate`。它使用当前目标分支，不新建任务分支。

## 3. 建立任务 worktree

任务 worktree 必须从正确的父分支开始。普通任务使用当前目标分支；从 `$mmw:mmw-wayfinder` map 派生的任务使用 map 分支。父分支不包含任务所需决定时停下，不在错误基点上补提交。

Codex App 在任务创建时已经准备好 detached worktree。确认任务范围和父分支后，运行 `mmw task bind codex/<slug> "<用户原话>" --from <父分支或基点 SHA>`。命令必须返回任务分支名和起始提交；当前状态不是 detached、工作区不干净、分支已存在或父分支不正确时停下。

**粒度是一份 spec 一棵树。** 这份 spec 拆出的几张 ticket 全在这棵树里按顺序做完，整体合并一次、终审一次、Wiki 写一次。确实能并行的 ticket 从当前这棵树的分支再分叉出去（判据在 `$mmw:mmw-implement`）。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在同一个落点下。

任务 worktree 在整个任务期间持久，可以跨天，中途不要清理。**新 worktree 不预先创建目录**：`docs/specs/`、`docs/plans/`、`docs/prototypes/` 和 `.reviews/` 都在首次写入时创建。

报一句你定的 slug 和你要走的路线，然后接着做，不用停下来等用户确认。

**第 2 步列出的四条路线同样跳过本步**，直接移交。

下表准备移交下一技能时，先读 [phase-boundaries.md](phase-boundaries.md)，按顺序判断是否留在当前会话。因路由冲突停下不触发阶段边界判断。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起第 1 步判出的那个技能，把用户原话原样传过去 |
| 第 1 步那张表哪一行都对不上，或者同时对上互相冲突的两行 | **停**：把你认为可能的那两三条路线连同各自的判据摆给用户，让他点一条。不要挑一条最像的就往下走 |

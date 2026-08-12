---
name: mmw-start
description: MMW 的统一入口。用于开始或恢复任务，并把输入路由到正确技能。
argument-hint: "[wayfinder] [需求、bug、issue/PR/map 编号或链接；留空恢复当前任务]"
disable-model-invocation: true
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
| 一个 issue 编号，挂在 spec issue 下，正文 `## Plan` 指向已提交的 plan，并已是 `ready-for-agent`——那是一张通过 ② plan 审的 tracer bullet ticket | **移交**：`$mmw:mmw-implement`；tracer bullet ticket 不要求 agent brief |
| 一个 issue 编号，挂在 spec issue 下，但已提交的 plan 或 `ready-for-agent` 缺少任何一项 | **移交**：`$mmw:mmw-to-plan`；不送 `$mmw:mmw-triage` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`$mmw:mmw-triage` |
| 一个 issue 或 PR 编号，已是 `ready-for-agent`，但没有完整 agent brief | **移交**：`$mmw:mmw-triage`，补齐 `Acceptance criteria`、范围边界和 `Test seam` |
| 一个 issue 编号，已是 `ready-for-agent`，整项工作可以作为一张 ticket 独立验收，只有一个已确认的测试 seam，而且没有未决设计取舍 | **移交**：`$mmw:mmw-implement` |
| 一个 issue 或 PR 编号，已是 `ready-for-agent`，但需要拆成多张 ticket、需要多个测试 seam，或者还有设计取舍要谈 | **移交**：`$mmw:mmw-to-spec` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`$mmw:mmw-diagnosing-bugs` |
| 一个 effort 超出一次 agent session，而且从当前状态到 destination 的路线还看不清，或者用户在输入开头写了 `wayfinder` | **移交**：`$mmw:mmw-wayfinder` |
| 想先看看某个界面长什么样，或者不确定一套状态模型对不对 | **移交**：`$mmw:mmw-prototype` |
| 单个文件、符号、事实或一条命令能答完 | **自己继续**：主 agent 直接查询并回答，到这里完成，不进入第 2、3 步 |
| 要从多个独立角度调查跨模块实现、调用链、数据流或影响面，或者需要对照多份一手资料 | **移交**：`$mmw:mmw-research`，跳过第 2、3 步 |
| 一个新需求，或对已有需求的改进 | **移交**：`$mmw:mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`$mmw:mmw-improve-codebase-architecture`，跳过第 2、3 步 |
| 几条并行分支要集成到当前目标分支，某条分支要跟上已经推进的目标分支，或者手上有一个正在进行中的冲突 | **移交**：`$mmw:mmw-integrate`，跳过第 2、3 步 |

**先做原型还是先谈清楚**：他要的是先看见一个能跑的东西，走 `$mmw:mmw-prototype`；他要的是先把这件事说清楚，走 `$mmw:mmw-grilling`。分不出来时走 `$mmw:mmw-grilling`。

**effort 怎么认**：同时满足以下两个条件才走 `$mmw:mmw-wayfinder`：

1. 这件事超出一次 agent session 能容纳的范围。
2. 从当前状态到 destination 的路线还看不清。

最终形成一份还是多份 spec 不是入口判据。范围大但路线已经清楚时，直接进入 `$mmw:mmw-to-spec` 或 `$mmw:mmw-to-tickets`；路线模糊但一次会话能谈清时，走 `$mmw:mmw-grilling`。

带 issue 编号的，先 `gh issue view <编号> --comments` 把它读出来再判，不要只看编号。`wayfinder:` 这一族标签的含义见 `$mmw:mmw-wayfinder`，其余分诊标签见 `$mmw:mmw-triage`。

## 2. 定任务分支名

任务分支名使用 **slug**。形状是 `<类型>-<短语>`。类型取 Conventional Commits。短语用 kebab 说清这次做什么。例如 `feat-phone-login`、`fix-refund-rounding`、`refactor-order-state`。

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

任务分支名只标识任务分支。它不承担工作名。worktree 的物理目录由宿主管理，不参与任务识别。

slug 的类型前缀用连字符。不带 issue 编号，不带日期。同名冲突时加一个区分词，不加序号。宿主可以在分支名前增加固定命名空间；该命名空间不属于 slug。

**下面四种情况跳过这一步**，第 3 步也一并跳过：

- 用户报的是一张已有 map 的编号或链接。slug 由 `$mmw:mmw-wayfinder` 定。
- 判定走 `$mmw:mmw-improve-codebase-architecture`。slug 由它定，类型固定用 `refactor`。
- 判定走 `$mmw:mmw-research`。
- 判定走 `$mmw:mmw-integrate`。它使用当前目标分支，不新建任务分支。

## 3. 建立任务 worktree

任务 worktree 必须从正确的父分支开始。普通任务使用当前目标分支；从 `$mmw:mmw-wayfinder` map 派生的任务使用 map 分支。父分支不包含任务所需决定时停下，不在错误基点上补提交。

先跑 `mmw task state`。它输出一行，第一个词决定这棵树要不要你自己建：

| 第一个词 | 什么意思 | 你做什么 |
| --- | --- | --- |
| `bound` | 你已经在一棵绑好的任务 worktree 里 | 什么都不用建。运行 `mmw task name` 取工作名，记下它 |
| `detached` | 宿主把你放在一棵干净的树上了，还没绑分支 | 先单独确定工作名。绑定：`mmw task bind <任务分支名> "<用户原话>" --name <工作名> [--from <父分支或基点 SHA>]`。命令成功后重新运行 `mmw task state`。确认输出是 `bound`。再运行 `mmw task name` 取工作名 |
| `local` | 你在主检出里 | 先单独确定工作名。禁止 `mmw task new`。宿主已把你放在树上则运行 `mmw task bind <任务分支名> "<用户原话>" --name <工作名> [--from <父分支或基点 SHA>]`。还没有树时请用户用宿主建树，新会话已经在树上后再 bind。 重新运行 `mmw task state`。确认输出是 `bound`。再运行 `mmw task name` 取工作名 |
| `outside` | 你根本不在仓库里 | 向用户索取目标仓库路径。拿到路径后进入该仓库，再重新运行 `mmw task state`，按新输出重新选行 |

两条路都一样：工作区不干净、分支已经存在、或者父分支里没有这次任务需要的决定时，**停下来**——不要在错的基点上补提交。

**粒度是一份 spec 一棵树。** 这份 spec 拆出的几张 ticket 全在这棵树里按顺序做完，整体合并一次、终审一次、收尾一次。确实能并行的 ticket 从当前这棵树的分支再分叉出去（判据在 `$mmw:mmw-implement`）。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在同一个落点下。

任务 worktree 在整个任务期间持久，可以跨天，中途不要清理。**新 worktree 不预先创建产物目录**：spec、plan、prototype 和审查记录的目录都在首次写入时才创建。

报一句你定的 slug 和你要走的路线，然后接着做，不用停下来等用户确认。

**第 2 步列出的四条路线同样跳过本步**，直接移交。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起第 1 步判出的那个技能，把用户原话原样传过去 |
| 第 1 步判定是单个文件、符号、事实或一条命令能答完 | **停**：给出查询结果和出处 |
| 第 1 步那张表哪一行都对不上，或者同时对上互相冲突的两行 | **停**：把你认为可能的那两三条路线连同各自的判据摆给用户，让他点一条。不要挑一条最像的就往下走 |

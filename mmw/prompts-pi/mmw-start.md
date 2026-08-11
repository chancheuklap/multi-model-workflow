---
description: "MMW 的统一入口。用于开始或恢复任务，并把输入路由到正确技能。"
argument-hint: "[wayfinder] [需求、bug、issue/PR/map 编号或链接；留空恢复当前任务]"
---


本技能只做路由，这次任务本身一个字都不实现。

本次输入：`$@`

这一栏为空、用户也没有在对话里交代要做什么，走 下文的「resuming.md」。

有输入时先运行 `mmw task state`。只有输出以 `bound` 开头，才走 下文的「resuming.md」。`detached` 表示宿主已经准备好 worktree，但 MMW 尚未绑定任务；这时继续判定路线和 slug。

## 1. 判定路线

读用户说的内容，加上他在开头挂的标签。有标签就直接用，不要再推断。

| 情况 | 下一步 |
| --- | --- |
| 一张 map 的编号或链接，或者他说要接着做某张 map | **移交**：`/mmw-wayfinder` |
| 一个 issue 编号，带着某个 `wayfinder:` 类型标签——那是一张 map 上的一条 decision ticket | **移交**：`/mmw-wayfinder` |
| 一个 issue 编号，挂在一张带 `wayfinder:map` 标签的 issue 底下、自己不带 `wayfinder:` 标签——那是收尾时切出来的一份 spec | **移交**：`/mmw-to-spec` |
| 一个 issue 编号，挂在 spec issue 下，正文 `## Plan` 指向已提交的 plan，并已是 `ready-for-agent`——那是一张通过 ② plan 审的 tracer bullet ticket | **移交**：`/mmw-implement`；tracer bullet ticket 不要求 agent brief |
| 一个 issue 编号，挂在 spec issue 下，但已提交的 plan 或 `ready-for-agent` 缺少任何一项 | **移交**：`/mmw-to-plan`；不送 `/mmw-triage` |
| 一个 issue 或 PR 编号，上面还没有状态角色 | **移交**：`/mmw-triage` |
| 一个 issue 或 PR 编号，已是 `ready-for-agent`，但没有完整 agent brief | **移交**：`/mmw-triage`，补齐 `Acceptance criteria`、范围边界和 `Test seam` |
| 一个 issue 编号，已是 `ready-for-agent`，整项工作可以作为一张 ticket 独立验收，只有一个已确认的测试 seam，而且没有未决设计取舍 | **移交**：`/mmw-implement` |
| 一个 issue 或 PR 编号，已是 `ready-for-agent`，但需要拆成多张 ticket、需要多个测试 seam，或者还有设计取舍要谈 | **移交**：`/mmw-to-spec` |
| 有东西坏了、报错、跑不通、变慢了，或者挂了 `bug` | **移交**：`/mmw-diagnosing-bugs` |
| 一个 effort 超出一次 agent session，而且从当前状态到 destination 的路线还看不清，或者用户在输入开头写了 `wayfinder` | **移交**：`/mmw-wayfinder` |
| 想先看看某个界面长什么样，或者不确定一套状态模型对不对 | **移交**：`/mmw-prototype` |
| 单个文件、符号、事实或一条命令能答完 | **自己继续**：主 agent 直接查询并回答，到这里完成，不进入第 2、3 步 |
| 要从多个独立角度调查跨模块实现、调用链、数据流或影响面，或者需要对照多份一手资料 | **移交**：`/mmw-research`，跳过第 2、3 步 |
| 一个新需求，或对已有需求的改进 | **移交**：`/mmw-grilling` |
| 没有具体需求，只说想让代码库更好维护 | **移交**：`/mmw-improve-codebase-architecture`，跳过第 2、3 步 |
| 几条并行分支要集成到当前目标分支，某条分支要跟上已经推进的目标分支，或者手上有一个正在进行中的冲突 | **移交**：`/mmw-integrate`，跳过第 2、3 步 |

**先做原型还是先谈清楚**：他要的是先看见一个能跑的东西，走 `/mmw-prototype`；他要的是先把这件事说清楚，走 `/mmw-grilling`。分不出来时走 `/mmw-grilling`。

**effort 怎么认**：同时满足以下两个条件才走 `/mmw-wayfinder`：

1. 这件事超出一次 agent session 能容纳的范围。
2. 从当前状态到 destination 的路线还看不清。

最终形成一份还是多份 spec 不是入口判据。范围大但路线已经清楚时，直接进入 `/mmw-to-spec` 或 `/mmw-to-tickets`；路线模糊但一次会话能谈清时，走 `/mmw-grilling`。

带 issue 编号的，先 `gh issue view <编号> --comments` 把它读出来再判，不要只看编号。`wayfinder:` 这一族标签的含义见 `/mmw-wayfinder`，其余分诊标签见 `/mmw-triage`。

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

**一个 slug 贯穿四处**：任务分支名、`docs/specs/<slug>/`、这个目录里的主文件 `<slug>.md`、Wiki 上的 `Spec-<slug>.md`。worktree 的物理目录由宿主管理，不参与任务识别。

slug 的类型前缀用连字符。不带 issue 编号，不带日期。同名冲突时加一个区分词，不加序号。宿主可以在分支名前增加固定命名空间；该命名空间不属于 slug。

**下面四种情况跳过这一步**，第 3 步也一并跳过：

- 用户报的是一张已有 map 的编号或链接。slug 由 `/mmw-wayfinder` 定。
- 判定走 `/mmw-improve-codebase-architecture`。slug 由它定，类型固定用 `refactor`。
- 判定走 `/mmw-research`。
- 判定走 `/mmw-integrate`。它使用当前目标分支，不新建任务分支。

## 3. 建立任务 worktree

任务 worktree 必须从正确的父分支开始。普通任务使用当前目标分支；从 `/mmw-wayfinder` map 派生的任务使用 map 分支。父分支不包含任务所需决定时停下，不在错误基点上补提交。

先跑 `mmw task state`。它输出一行，第一个词决定这棵树要不要你自己建：

| 第一个词 | 什么意思 | 你做什么 |
| --- | --- | --- |
| `bound` | 你已经在一棵绑好的任务 worktree 里 | 什么都不用建。第二个词是任务分支名，第三个词是当前 HEAD，记下它们 |
| `detached` | 宿主把你放在一棵干净的树上了，还没绑分支 | 绑定：`mmw task bind <分支名> "<用户原话>"`。`<分支名>` 用这个任务的 slug；宿主对任务分支有固定命名空间（Codex App 是 `codex/`）时带上它。知道预期基点就加 `--from <父分支或基点 SHA>`，它只是一道校验，不确定就不加。命令必须返回任务分支名和起始提交 |
| `local` 或 `outside` | 你在主检出里，或者根本不在仓库里 | 这棵树要你自己建：`mmw task new <slug> "<用户原话>"`，从 map 分支派生时加 `--from <map 分支>`。命令返回绝对路径，用宿主切换工作目录的能力进去 |

两条路都一样：工作区不干净、分支已经存在、或者父分支里没有这次任务需要的决定时，**停下来**——不要在错的基点上补提交。

**粒度是一份 spec 一棵树。** 这份 spec 拆出的几张 ticket 全在这棵树里按顺序做完，整体合并一次、终审一次、Wiki 写一次。确实能并行的 ticket 从当前这棵树的分支再分叉出去（判据在 `/mmw-implement`）。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在同一个落点下。

任务 worktree 在整个任务期间持久，可以跨天，中途不要清理。**新 worktree 不预先创建产物目录**：spec、plan、prototype 和审查记录的目录都在首次写入时才创建。

报一句你定的 slug 和你要走的路线，然后接着做，不用停下来等用户确认。

**第 2 步列出的四条路线同样跳过本步**，直接移交。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| 第 1 步判出了路线 | **移交**：调起第 1 步判出的那个技能，把用户原话原样传过去 |
| 第 1 步判定是单个文件、符号、事实或一条命令能答完 | **停**：给出查询结果和出处 |
| 第 1 步那张表哪一行都对不上，或者同时对上互相冲突的两行 | **停**：把你认为可能的那两三条路线连同各自的判据摆给用户，让他点一条。不要挑一条最像的就往下走 |

## resuming.md

# 回来接着做

用户不带内容叫 `/mmw-start`，或者当前 checkout 已绑定任务分支，问的都是同一件事：这个任务现在走到哪一步。

没有状态文件要读。每一步都有一件落在 git 或 GitHub 上的产物对应它，查产物在不在就够了。

## 有哪些任务在进行

运行 `git worktree list --porcelain`。已绑定分支的 linked worktree 是进行中的任务。**slug 是分支名最后一个 `/` 之后的部分**——slug 本身不含斜杠，所以有斜杠就一定是宿主的命名空间前缀（Codex App 是 `codex/`）。detached worktree 尚未绑定，不替用户猜 slug。只有一项就直接查；有多项就把分支名和进度报给用户选择。

## 一个任务走到哪一步

审查记录目录是 `.reviews/`。按顺序查，第一个查不到的地方就是它停下的地方。

| 想知道 | 怎么查 |
| --- | --- |
| 当初用户要的是什么 | 分支上第一个提交的正文，也就是那个空提交：`git log --reverse --format='%B' $(git merge-base HEAD <父分支>)..HEAD \| head -20`。`<父分支>` 是这条任务分支分叉出来的那条：普通任务是仓库默认分支，从 Wayfinder map 派生的是 map 分支（map 正文的 `## 分支` 一节记着它） |
| 是不是一个 `/mmw-wayfinder` 的 effort | 有没有一张打 `wayfinder:map` 标签的 issue 指向这个 slug |
| 这张 map 走到哪一步了 | `mmw issue children <map 编号>`：一行一张，带状态、认领人、被几张挡着 |
| 有几张 decision ticket 在同时推进 | 查从该任务分支派生的 worktree 与结果分支。**结果分支**是派出去的角色在自己那棵树上写代码用的分支，做完由主 agent 用 `mmw result verify` 收、`mmw result integrate` 合；每个结果分支只对应一张 decision ticket |
| spec 有没有写出来 | `docs/specs/<slug>/` 在不在，里面的文件有没有提交进分支 |
| spec 过没过用户那道关卡 | 先反查那张 spec issue：`gh issue list --search "docs/specs/<slug>/<slug>.md" --state all --json number,title,labels`。`/mmw-to-spec` 发布时把 spec 的精确路径写进了 issue 正文，所以搜得到。它在、而且带 `ready-for-agent`，才算过了这道关卡。**下面几行里的 `<spec issue 编号>` 就是它的编号** |
| ticket 有没有拆 | `mmw issue children <spec issue 编号>` 有没有输出 |
| plan 写了没有 | `docs/plans/<slug>/` 在不在，里面的份数跟 ticket 数对不对得上 |
| 合同锚点回填了没有 | spec 的 `## Cross-Plan Contract Anchors` 一节在不在、精确字段补实了没有 |
| plan 审过没过 | 逐张读取 open tracer bullet ticket；全部带 `ready-for-agent` 才算通过 |
| 做到第几张 ticket | `mmw issue children <spec issue 编号>`：closed 的是做完的，open 且有认领人的是正在做的 |
| 终审有没有跑 | `.reviews/<slug>-final.md` 在不在 |
| 有没有归档 | `mmw wiki ensure` 把 Wiki 克隆到本地并输出那个目录的路径，看该目录下 `Spec-<slug>.md` 在不在 |

审查记录目录随 worktree 存活，不进 Git。它是空的不代表没做过，只代表这台机器上这一轮没做过。以提交记录和 issue 状态为准。

spec 文件已经提交、issue 却还没发布，是个中间状态：用户可能刚点完头，也可能还没看过。这时按没过这道关卡处理，重新给他看一次。

plan 按批次写，某张 ticket 缺 `ready-for-agent` 不一定是流程断了，可能只是批次没到。判据：存在「阻塞已全部关闭、还没有 `ready-for-agent`」的 open ticket 时，回 `/mmw-to-plan` 写它们的 plan；frontier 上有带标签的 ticket 时，进入 `/mmw-implement` 继续落地；两者都没有、但仍有 open ticket 时，报告各张的状态（被谁阻塞、被谁认领）等用户处理。

## 查完之后

用业务语言报三句：这个任务当初要做什么、现在完成了哪些、下一步归谁。然后调起下一步该走的那个技能接着走。

用户报的 slug 在任务分支和 worktree 清单中都找不到，按新任务处理，回 `SKILL.md` 第 1 步。

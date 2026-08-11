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

**粒度是一份 spec 一棵树。** 这份 spec 拆出的几张 ticket 全在这棵树里按顺序做完，整体合并一次、终审一次、收尾一次。确实能并行的 ticket 从当前这棵树的分支再分叉出去（判据在 `/mmw-implement`）。**分支可以嵌套，目录不嵌套**——所有 worktree 一律扁平挂在同一个落点下。

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

用户不带内容调用 `/mmw-start`，或者当前 checkout 已绑定任务分支，都是要恢复现有任务。

MMW 不保存流程状态文件。使用仓库产物、审查记录和 tracker 状态判断进度。

## 找到进行中的任务

运行 `git worktree list --porcelain`。已绑定分支的 linked worktree 是进行中的任务。detached worktree 尚未绑定，不替用户推断任务分支名或工作名。

进入候选 worktree 后运行 `mmw task state`。输出以 `bound` 开头时，第二个字段是任务分支名，第四个字段是工作名。

只有一项时直接检查。存在多项时，报告每项的任务分支名、工作名和当前进度，让用户选择。

## 判断一个任务的进度

按表中顺序检查。每次解析产物位置都运行表内的完整命令。不要自己拼路径。

| 想知道 | 怎么查 |
| --- | --- |
| 当初用户要什么 | 读取任务分支上的第一个空提交正文。父分支取任务实际分叉点 |
| 是否属于 Wayfinding effort | 查是否有一张带 `wayfinder:map` 标签的 issue 点名该工作名 |
| map 走到哪里 | 运行 `mmw issue children <map 编号>` |
| 共同理解记录是否仍在本机 | 运行 `mmw artifact path scratch --name <工作名> --sub understanding.md`，再检查输出路径 |
| spec 是否已经写入仓库 | 运行 `mmw artifact path spec --name <工作名>`。检查输出路径是否存在并已提交 |
| spec 是否通过人工审批关卡 | 用上一行的 spec 路径反查 spec issue。issue 存在且带 `ready-for-agent` 才算通过 |
| tracer bullet ticket 是否已经拆出 | 运行 `mmw issue children <spec issue 编号>` |
| 每份 plan 是否已经写入仓库 | 从每张 tracer bullet ticket 取得计划文件名。逐份运行 `mmw artifact path plan --name <工作名> --sub <计划文件>`，再检查输出路径 |
| 共同理解审是否跑过 | 运行 `mmw artifact path review --name <工作名> --sub understanding.md`，再检查输出路径 |
| spec 审是否跑过 | 运行 `mmw artifact path review --name <工作名> --sub spec.md`，再检查输出路径 |
| plan 审是否跑过 | 运行 `mmw artifact path review --name <工作名> --sub plan.md`，再检查输出路径 |
| 做到哪张 ticket | 运行 `mmw issue children <spec issue 编号>`。closed 表示完成；open 且有人认领表示正在处理 |
| final 终审是否跑过 | 运行 `mmw artifact path review --name <工作名> --sub final.md`，再检查输出路径 |
| 当前还有哪些过程材料 | 先运行 `mmw artifact path scratch --name <工作名> --sub evidence`，从输出取得 scratch 父目录。对每个实际条目再次运行对应的完整 `mmw artifact path scratch … --sub <类别内细分>` 命令 |
| 长期文档是否仍在仓库 | 再次运行 spec 与每份 plan 的落点命令。全部输出路径都必须存在并已提交 |

Wayfinding decision ticket 的 scratch 检查必须加入 `--issue <编号>`。命令形态是 `mmw artifact path scratch --name <工作名> --issue <编号> --sub <类别内细分>`。

审查记录和 scratch 随 worktree 存活，不进入 Git。它们缺失只说明本机没有对应过程材料。spec、plan、提交记录和 tracker 状态才是长期依据。

spec 已提交但 spec issue 未发布时，按尚未通过人工审批关卡处理。重新向用户展示 spec。

任何 open tracer bullet ticket 缺少 `ready-for-agent` 时，回 `/mmw-to-plan`。全部具备后才进入 `/mmw-implement`。

## 查完之后

用业务语言报告三项：任务目标、已完成内容、下一步归属。然后调起下一步技能。

用户给出的任务分支名和工作名都不在 worktree 清单中时，按新任务处理，回 `SKILL.md` 第 1 步。

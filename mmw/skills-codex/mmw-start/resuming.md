# 回来接着做

用户不带内容调用 `$mmw:mmw-start`，或者当前 checkout 已绑定任务分支，都是要恢复现有任务。

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

plan 按批次写，某张 ticket 缺 `ready-for-agent` 不一定是流程断了，可能只是批次没到。判据：存在「阻塞已全部关闭、还没有 `ready-for-agent`」的 open ticket 时，回 `$mmw:mmw-to-plan` 写它们的 plan；frontier 上有带标签的 ticket 时，进入 `$mmw:mmw-implement` 继续落地；两者都没有、但仍有 open ticket 时，报告各张的状态（被谁阻塞、被谁认领）等用户处理。

## 查完之后

用业务语言报告三项：任务目标、已完成内容、下一步归属。然后调起下一步技能。

用户给出的任务分支名和工作名都不在 worktree 清单中时，按新任务处理，回 `SKILL.md` 第 1 步。

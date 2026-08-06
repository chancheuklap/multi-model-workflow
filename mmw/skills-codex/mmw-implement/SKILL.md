---
name: mmw-implement
description: 把定好的需求实现成代码，一张 ticket 派一个 `worker`。用户说要开始实现、做下一张 ticket 时用它；别的技能判定某张 ticket 已是 ready-for-agent 时也用它。
---

把 spec 和它的 ticket 描述的需求实现出来。spec 已定稿，seam 已谈定；本技能执行那份计划，不重开它。

**你不写代码。** 每张 ticket 交给一个 `worker`。你的职责是写清派工 task、派发、验收、发起审查。

## 流程

### 1. 确认前置条件

先确认这次需求出自哪里。`docs/specs/<slug>/` 里已经有 spec，就走 spec 分支。没有 spec，就读取原 issue 上那份 `ready-for-agent` 的 agent brief；只有整项工作可以作为一张 ticket 独立验收、只有一个已确认测试 seam、没有未决设计取舍时，才走 agent brief 分支。

然后检查下面各项。标明来源分支的检查只在对应分支适用；适用项有一件不满足就按表中出口处理。

| 检查 | 怎么查 | 不满足怎么办 |
| --- | --- | --- |
| 你在已绑定的任务 worktree 里 | `mmw task state` 输出以 `bound` 开头 | 回 `$mmw:mmw-start` 建立或绑定任务 worktree |
| spec 分支写明了测试 seam | 读 spec `## Testing Decisions` 一节里的 seam 清单表 | 回 `$mmw:mmw-to-spec` 第 3 步补 |
| agent brief 分支的行为合同完整 | 原 issue 的 agent brief 有当前行为、目标行为、可独立验证的 `Acceptance criteria`、范围边界和且仅一个 `Test seam`；整项工作可以作为一张 ticket 独立验收，而且没有未决设计取舍 | 缺字段就回 `$mmw:mmw-triage` 补；需要多张 ticket、多个 seam 或设计取舍就转 `$mmw:mmw-to-spec` |
| ticket 存在 | spec 分支：`mmw issue children <spec issue 编号>` 有输出；agent brief 分支：带 agent brief 的原 issue 就是这张 ticket | spec 分支先跑 `$mmw:mmw-to-tickets`；agent brief 分支回 `$mmw:mmw-triage` 补齐或修正 issue |
| 这张 ticket 的 plan 写好了、过了 ② plan 审 | `docs/plans/<slug>/` 下有对应那一份 | 先跑 `$mmw:mmw-to-plan`。走 agent brief 那条路的需求没有 plan 这一层，这一行不适用 |

### 2. 取下一张 ticket

spec 分支运行：

```bash
mmw issue frontier <spec issue 编号> --label ready-for-agent
```

它给出阻塞全部关闭、没人认领、带这个标签的那些，按 `$mmw:mmw-to-tickets` 的发布顺序排。**取第一行那张。** agent brief 分支不查 frontier；带 agent brief 的原 issue 就是唯一一张 ticket。用 `gh issue view <编号> --json state,assignees,labels` 确认它仍然 open、无人认领并带 `ready-for-agent`。

开工前先 `mmw issue claim <编号>`。认领失败说明别的会话抢先了。spec 分支取下一行；agent brief 分支没有下一张，停止并报告这张 issue 已被谁认领。

一个 `worker` 的独立 worktree 一次只做一张 ticket。frontier 确实很宽、用户又明确要求并行推进时，每张 ticket 各派一个 `worker`，都从当前已提交的任务分支开始。

### 3. 写派工 task

| 上下文 | 何时读取 | 读取范围 | 不读取 | 向下传递 |
| --- | --- | --- | --- | --- |
| `worker-brief.md` | 始终 | 文件路径 | 正文副本 | 文件路径 |
| spec 或 agent brief | 始终 | 当前需求的精确位置 | 其它需求 | 精确位置 |
| ticket | 始终 | 当前 ticket 编号 | 其它 ticket | ticket 编号 |
| plan | spec 分支 | 当前 ticket 的 plan 路径 | 其它 plan | plan 路径 |
| `TESTING.md` | 文件存在时 | 仓库根文件 | 自拟测试命令 | 文件路径 |
| prototype | 当前 ticket 引用时 | 索引、选中产物和明确相关证据 | 整个产物目录和过程材料 | 精确路径 |
| research | 当前 ticket 引用时 | research 索引和精确文件 | research 的上级目录和 subagent 原始报告 | 精确路径 |

按 **四栏表**（目标 / 读 / 约束 / 验收）填写。issue 上的 **agent brief** 是 tracker 里的权威行为合同，进入「读」栏。

| 栏 | 本角色填写 |
| --- | --- |
| 目标 | 完成 ticket `#<编号>`（或 tracker 等价编号） |
| 读 | 按上方上下文清单逐行列出精确路径。没有 plan、prototype 或 research 时分别写「无 plan」「无 prototype 资产」「无 research」 |
| 约束 | 只改本 worktree 源码与测试；不改 `docs/`；不扩大 ticket 范围；所有上下文只读 task 点名的精确路径 |
| 验收 | spec 分支：见 ticket `#<编号>` 的验收标准，seam 见 spec `## Testing Decisions`；agent brief 分支：见原 issue 的 agent brief 中 `**Acceptance criteria:**` 与 `**Test seam:**`（在「读」里已给出定位，此处不抄正文） |

TDD 在 worker 的 `mmw-tdd` 技能里，不进 task 正文。

### 4. 派发

派发前确认当前任务分支已经提交且工作区干净。为这次工作确定唯一、完整的结果分支名，并记下 `git rev-parse HEAD` 作为基点。结果分支名和基点 SHA 都要写入 task。

启动：先用 `list_projects` 取得当前仓库的 projectId，再调用 `create_thread`。target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型使用 `gpt-5.6-terra`，思考档使用 `xhigh`。任务提示包含四栏 task、主 agent 已确定的完整结果分支名和派发前基点 SHA；结果分支名使用独立的 `codex/<slug>`。后台 agent 先运行 `mmw task bind <完整结果分支名> <目标栏原文> --from <基点 SHA>`，并在工作前完整读取 `$mmw:mmw-tdd`，然后完成工作并提交。后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 worktree 设置，取得 threadId 后再等待。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告；报告交回后只按 `$mmw:mmw-verifying-agent-output` 验证关键断言，不重做整个 task。

ticket 涉及计费、权限、数据迁移，或改错不可逆时：改用
启动：先用 `list_projects` 取得当前仓库的 projectId，再调用 `create_thread`。target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型使用 `gpt-5.6-sol`，思考档使用 `high`。任务提示包含四栏 task、主 agent 已确定的完整结果分支名和派发前基点 SHA；结果分支名使用独立的 `codex/<slug>`。后台 agent 先运行 `mmw task bind <完整结果分支名> <目标栏原文> --from <基点 SHA>`，并在工作前完整读取 `$mmw:mmw-tdd`，然后完成工作并提交。后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 worktree 设置，取得 threadId 后再等待。

派出 subagent 后，主 agent 不得执行与该 subagent task 重叠的 research、实现或审查。没有明确不重叠的协调工作时，立即等待 subagent 交回报告；报告交回后只按 `$mmw:mmw-verifying-agent-output` 验证关键断言，不重做整个 task。
升档由你决定，不由 worker 自报。

`worker` 完成后，先收取结果：

该角色完成后，运行 `mmw result verify <结果分支> <HEAD SHA> <基点 SHA>`。命令通过后，从输出取得结果 worktree 路径；在该路径读取报告与 diff，并运行本技能规定的验收。此动作不合入结果分支。

### 5. 验收：亲手验证三关

按 `$mmw:mmw-review` 的 **③ 逐份验收**，三关都过才允许合并回任务分支：做漏没有、测试达不达标、有没有偏离。三关各自的判据、三关不过时的返工升级策略，都在 `$mmw:mmw-review` 目录里的 `self-review.md`——**这一道不派审查者**，`$mmw:mmw-review` 正文其余各节跟它无关。报告按 `$mmw:mmw-verifying-agent-output` 采信，它交回的四档怎么读也在那里。

三关之外还要确认两件本阶段特有的事：commit 存在并引用这张 ticket；报告显示类型检查和当前测试文件在实现过程中交错运行，完整测试套件在结束时运行一次。具体命令由目标仓库 `TESTING.md` 决定；仓库缺少某一层入口时，报告必须写明不适用的证据。

ticket 涉及界面时，还要完成浏览器验收：

完整读取并遵守 `/browser:control-in-app-browser`。主 agent 在结果 worktree 启动界面，使用 Codex 内置浏览器走通黄金路径和本次相关边界状态。按视觉合同设置 viewport，逐个检查加载、空、错误、成功和部分完成中实际存在的状态。保存关键截图；交互异常时同时读取 DOM 和 console。保存最后一份证据后恢复默认 viewport。浏览器验收没有通过，或者浏览器不可用且没有等价证据时，不得集成结果分支。

三关都过后，集成结果：

本技能规定的验收全部通过后，运行 `mmw result integrate <结果分支> <HEAD SHA> <基点 SHA>`。命令成功后，结果提交才算进入当前任务分支。

结果提交已经进入当前任务分支，才关闭这张 ticket。spec 分支继续取下一张；agent brief 分支只有这一张，直接进入第 7 步。

### 6. spec 分支全部落地后验证合同

本节只适用于有 spec 的分支。agent brief 分支没有跨 plan 合同，跳到第 7 步。

每张 ticket 都关闭、改动都在任务分支上之后，按 `$mmw:mmw-review` 的 **④ 合同门**验证一次：spec 的 `## Cross-Plan Contract Anchors` 一节里每条跨 plan 合同，在合并后的代码里真兑现了。逐条要查什么、合同条数多时怎么把取证派出去，在 `$mmw:mmw-review` 目录里的 `self-review.md`——**这一道也不派审查者**。

**grep 不到行号就不算兑现**，回去补，不要留给终审。这是本阶段特有的一句：终审那一道审的是代码本身，不替你补合同。

### 7. 发起 ⑤ final 终审

spec 分支通过合同门，或者 agent brief 分支完成第 5 步后，按 `$mmw:mmw-review` 发起一轮 **⑤ final 终审**，固定点取分支点。整体审一次，不逐张审。

分支点用 `git merge-base HEAD <父分支>` 取。普通任务的父分支是创建任务时选择的目标分支；从 `$mmw:mmw-wayfinder` map 派生的任务以 map 分支为父分支。

采信的 findings 打包成一张修复 ticket 派给新 `worker`，带上 `file:line` 和要改成什么。然后按 `$mmw:mmw-review` 第 7 步复审。

下表准备移交下一技能时，先读 [`../mmw-start/phase-boundaries.md`](../mmw-start/phase-boundaries.md)，按顺序判断是否留在当前会话。自己继续和因 blocker 停下不触发阶段边界判断。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 分支第 5 步三关都过，frontier 上还有 ticket | **自己继续**：回第 2 步取下一张 |
| spec 分支的 ticket 全部关闭了 | **自己继续**：走第 6 步验证合同，过了再走第 7 步发起 ⑤ final 终审 |
| agent brief 分支第 5 步三关都过，原 issue 已关闭 | **自己继续**：跳过第 6 步，走第 7 步发起 ⑤ final 终审 |
| 第 6 步有合同 grep 不到行号 | **停**：报是哪条合同、提供方或消费方缺在哪 |
| 审出了采信的 findings | **自己继续**：打包成一张修复 ticket 派新 `worker`，然后按 `$mmw:mmw-review` 第 7 步复审 |
| 审完没有采信项，或者修复已经复审通过，而且这次改动碰了带出包配置的产品 | **移交**：`$mmw:mmw-release`，先把安装包出出来。仓库里有没有出包配置，跑 `grep -rl '"product"' --include='*.release-adapter.json' .` |
| 审完没有采信项，或者修复已经复审通过；这次不用出包，而且有 spec | **移交**：`$mmw:mmw-closing`，把 spec 与 plan 归档到 Wiki、删掉本地的 `docs/specs/<slug>/` 与 `docs/plans/<slug>/`，再交回用户合并 |
| 审完没有采信项，或者修复已经复审通过；这次不用出包，而且只有 agent brief | **停**：报告实现结果、验证证据和当前分支 HEAD。这项任务没有 spec，不走 `$mmw:mmw-closing`；分支已就绪，交回用户集成 |
| 第 1 步有一项前置不满足 | **停**：说清是哪一项，按第 1 步表中的出口回 `$mmw:mmw-triage`、`$mmw:mmw-to-spec`、`$mmw:mmw-to-tickets` 或 `$mmw:mmw-to-plan` |
| `worker` 卡在 ticket 与代码互相矛盾上 | **停**：把矛盾交给用户，不要换一个 `worker` 再派一遍 |
| `worker` 交回的不是「完成」，也不是因为矛盾 | **自己继续**：按 `$mmw:mmw-verifying-agent-output` 的四档读它交回的东西，再按返工升级策略接着走 |

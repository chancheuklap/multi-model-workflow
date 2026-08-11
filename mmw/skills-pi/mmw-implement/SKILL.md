---
name: mmw-implement
description: 派 `worker` 落地已准备好的工作。用于完整的 `ready-for-agent` agent brief，或全部 plans 已通过审查的 spec。
---

把 spec 和它的 ticket 描述的需求实现出来。spec 已定稿，seam 已谈定；本技能执行那份计划，不重开它。

**你不写代码。** 每张 ticket 交给一个 `worker`。你的职责是写清派工 task、派发、验收、发起审查。

## 流程

### 1. 确认前置条件

先确认这次需求出自哪里：

- 运行 `mmw artifact path spec`。输出路径有 spec 时，走 spec 分支。
- 没有 spec，就读取原 issue 上那份 `ready-for-agent` 的 agent brief。只有整项工作可以作为一张 ticket 独立验收、只有一个已确认测试 seam、没有未决设计取舍时，才走 agent brief 分支。

然后检查下面各项。标明来源分支的检查只在对应分支适用；适用项有一件不满足就按表中出口处理。

`<spec issue 编号>` 只用于 spec 分支，由调用方移交。spec 分支缺少这个编号时，停下并说明缺少这项输入。agent brief 分支不需要 spec issue 编号。

| 检查 | 怎么查 | 不满足怎么办 |
| --- | --- | --- |
| 你在已绑定的任务 worktree 里 | `mmw task state` 输出以 `bound` 开头 | **停**：说明当前没有已绑定的任务上下文，无法继续 |
| spec 分支写明了测试 seam | 读 spec `## Testing Decisions` 一节里的 seam 清单表 | 回 `/mmw-to-spec` 第 3 步补 |
| agent brief 分支的行为合同完整 | 原 issue 的 agent brief 有当前行为、目标行为、可独立验证的 `Acceptance criteria`、范围边界和且仅一个 `Test seam`；整项工作可以作为一张 ticket 独立验收，而且没有未决设计取舍 | 缺字段就回 `/mmw-triage` 补；需要多张 ticket、多个 seam 或设计取舍就转 `/mmw-to-spec` |
| ticket 存在 | spec 分支：`mmw issue children <spec issue 编号>` 有输出；agent brief 分支：带 agent brief 的原 issue 就是这张 ticket | spec 分支先跑 `/mmw-to-tickets`；agent brief 分支回 `/mmw-triage` 补齐或修正 issue |
| 这张 ticket 的 plan 已提交 | 路径写在这张 ticket 正文的 `## Plan` 一节里，照它跑 `git cat-file -e "HEAD:<那条路径>"` | 先跑 `/mmw-to-plan`。走 agent brief 那条路的需求没有 plan 这一层，这一行不适用 |

### 2. 取下一张 ticket

spec 分支先重新读取全部子 issue。任何 open tracer bullet ticket 缺少 `ready-for-agent` 时，回 `/mmw-to-plan`。全部齐全后运行：

```bash
mmw issue frontier <spec issue 编号> --label ready-for-agent
```

它给出阻塞全部关闭、没人认领、带这个标签的那些，按 `/mmw-to-tickets` 的发布顺序排。**取第一行那张。** 认领前，用 `gh issue view <编号> --json state,assignees,labels` 确认它仍然 open、无人认领并带 `ready-for-agent`。

agent brief 分支不查 frontier；带 agent brief 的原 issue 就是唯一一张 ticket。用 `gh issue view <编号> --json state,assignees,labels` 确认它仍然 open、无人认领并带 `ready-for-agent`。

开工前先 `mmw issue claim <编号>`。认领失败说明别的会话抢先了。spec 分支取下一行；agent brief 分支没有下一张，停止并报告这张 issue 已被谁认领。

一个 `worker` 的独立 worktree 一次只做一张 ticket。frontier 确实很宽、用户又明确要求并行推进时，每张 ticket 各派一个 `worker`，都从当前已提交的任务分支开始。

### 3. 写派工 task

| 上下文 | 何时读取 | 读取范围 | 不读取 | 向下传递 |
| --- | --- | --- | --- | --- |
| `worker-brief.md` | 始终 | 文件路径 | 正文副本 | 文件路径 |
| spec 或 agent brief | 始终 | 当前需求的精确位置 | 其他需求 | 精确位置 |
| ticket | 始终 | 当前 ticket 编号 | 其他 ticket | ticket 编号 |
| plan | spec 分支 | 当前 ticket 的 plan 路径 | 其他 plan | plan 路径 |
| 产物引用 | plan 有 `artifact_refs` 时 | 当前 ticket 的条目 | 其他 plan 的条目 | 同一行键值形态 |
| `TESTING.md` | 文件存在时 | 仓库根文件 | 自拟测试命令 | 文件路径 |
| prototype | 当前 ticket 引用时 | 索引、选中产物和明确相关证据 | 整个产物目录和过程材料 | 精确路径 |
| research | 当前 ticket 引用时 | research 索引和精确文件 | research 的上级目录和 subagent 原始报告 | 精确路径 |

按 **四栏表**（目标 / 读 / 约束 / 验收）填写。issue 上的 **agent brief** 是 tracker 里的权威行为合同，进入「读」栏。

从 plan 元数据块读取 `artifact_refs`。键缺失时停止，说明缺少 plan 声明。每条在 task 的「读」栏写成 `- category=<类别> name=<工作名>`。类别需要范围段或类别内细分时，在同一行追加 `issue=<编号>` 或 `sub=<类别内细分>`。`name` 必须显式出现。空列表时在「读」栏写 `无`。

| 栏 | 本角色填写 |
| --- | --- |
| 目标 | 完成 ticket `#<编号>`（或 tracker 等价编号） |
| 读 | 按本节的上下文表逐行列出精确路径。没有 plan、prototype 或 research 时分别写「无 plan」「无 prototype 资产」「无 research」 |
| 约束 | 只改本 worktree 源码与测试；不改 `docs/`；不扩大 ticket 范围；所有上下文只读 task 点名的精确路径 |
| 验收 | spec 分支：见 ticket `#<编号>` 的验收标准，seam 见 spec `## Testing Decisions`；agent brief 分支：见原 issue 的 agent brief 中 `**Acceptance criteria:**` 与 `**Test seam:**`（在「读」里已给出定位，此处不抄正文）。两条路都要交回结果分支上的 HEAD SHA |

TDD 在 worker 的 `mmw-tdd` 技能里，不进 task 正文。

### 4. 派发

派发前确认当前任务分支已经提交且工作区干净。为这次工作确定唯一、完整的结果分支名，并记下 `git rev-parse HEAD` 作为基点。结果分支名和基点 SHA 都要写入 task。

**验收栏里要求它交回结果分支上的 HEAD SHA。** 收结果时 `mmw result verify` 要这个值，它自己不算，只有做完的那一侧知道。

启动：先运行 `mmw task new <结果分支> "<目标栏原文>" --from <基点 SHA>`，使用命令返回的 worktree 绝对路径作为 cwd。然后调用原生 `subagent`，agent 设为 `mmw-worker`，task 传四栏表全文，cwd 设为该绝对路径。

ticket 涉及计费、权限、数据迁移，或改错不可逆时：改用
启动：先运行 `mmw task new <结果分支> "<目标栏原文>" --from <基点 SHA>`，使用命令返回的 worktree 绝对路径作为 cwd。然后调用原生 `subagent`，agent 设为 `mmw-worker-high-risk`，task 传四栏表全文，cwd 设为该绝对路径。
升档由你决定，不由 worker 自报。

`worker` 完成后，先收取结果：

该角色完成后，运行 `mmw result verify <结果分支> <HEAD SHA> <基点 SHA>`。命令通过后，从输出取得结果 worktree 路径；在该路径读取报告与 diff，并运行本技能规定的验收。这一步不合入结果分支。

### 5. 验收：亲手验证三关

按 `/mmw-review` 的 **③ 逐份验收**验证三关：做漏没有、测试达不达标、有没有偏离。三关各自的判据、三关不过时的返工升级策略，都在 `/mmw-review` 目录里的 `self-review.md`。

三关都过才允许合并回任务分支。**这一道不派审查者**，`/mmw-review` 正文其余各节跟它无关。报告按 `/mmw-verifying-agent-output` 采信，它交回的四档怎么读也在那里。

再验证两项本阶段合同：

- commit 存在并引用这张 ticket。
- 报告显示类型检查和当前测试文件在实现过程中交错运行，完整测试套件在结束时运行一次。具体命令由目标仓库 `TESTING.md` 决定；仓库缺少某一层入口时，报告必须写明不适用的证据。

ticket 涉及界面时，还要完成浏览器验收：

在结果 worktree 里把界面启动起来。用浏览器入口走通黄金路径和相关边界状态。viewport 和状态以选中的 UI 产物为准。没有 prototype 时，按 plan 的界面验收段执行。逐个检查实际存在的加载、空、错误、成功和部分完成状态。运行 `mmw artifact path scratch --sub evidence`。关键截图写进输出目录。一个状态一份。文件名说明页面和状态。交互异常时同时读 DOM 和 console，并一并写入。用户要求长期保存时，写到用户指定位置。改过 viewport 后，留下最后一份证据再恢复默认。宿主和项目都没有浏览器入口时，记录可重复执行的人工步骤。**验收没过，或者拿不出等价证据，就不许集成结果分支。**

三关都过后，集成结果：

本技能规定的验收全部通过后，运行 `mmw result integrate <结果分支> <HEAD SHA> <基点 SHA>`。命令成功后，结果提交才算进入当前任务分支。

结果提交已经进入当前任务分支，才关闭这张 ticket。spec 分支继续取下一张；agent brief 分支只有这一张，直接进入第 7 步。

### 6. spec 分支全部落地后验证合同

本节只适用于有 spec 的分支。agent brief 分支没有跨 plan 合同，跳到第 7 步。

每张 ticket 都关闭、改动都在任务分支上之后，按 `/mmw-review` 的 **④ 合同门**验证一次：spec 的 `## Cross-Plan Contract Anchors` 一节里每条跨 plan 合同，在合并后的代码里真兑现了。

逐条要查什么、合同条数多时怎么把取证派出去，见 `/mmw-review` 目录里的 `self-review.md`。**这一道也不派审查者**。

**grep 不到行号就不算兑现**，回去补，不要留给终审。这是本阶段特有的一句：终审那一道审的是代码本身，不替你补合同。

### 7. 发起 ⑤ final 终审

spec 分支通过合同门，或者 agent brief 分支完成第 5 步后，按 `/mmw-review` 发起一轮 **⑤ final 终审**，固定点取分支点。整体审一次，不逐张审。

分支点用 `git merge-base HEAD <父分支>` 取。普通任务的父分支是创建任务时选择的目标分支；从 `/mmw-wayfinder` map 派生的任务以 map 分支为父分支。

采信的 findings 打包成一张修复 ticket 派给新 `worker`，带上 `file:line` 和要改成什么。修复回来后逐条验证原问题已经消失，并运行修复涉及的验收命令。全部通过后按 `/mmw-review` 第 7 步在原审查记录登记 `修复提交` 和 `终审提交`；不再派审查者。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| spec 分支第 5 步三关都过，frontier 上还有 ticket | **自己继续**：回第 2 步取下一张 |
| spec 分支的 ticket 全部关闭了 | **自己继续**：走第 6 步验证合同，过了再走第 7 步发起 ⑤ final 终审 |
| agent brief 分支第 5 步三关都过，原 issue 已关闭 | **自己继续**：跳过第 6 步，走第 7 步发起 ⑤ final 终审 |
| 第 6 步有合同 grep 不到行号 | **停**：报是哪条合同、提供方或消费方缺在哪 |
| 审出了采信的 findings | **自己继续**：按第 7 步一次性修复并验证；有一条没修好就停，不再审 |
| 审完没有采信项，或者采信项已经修复并验证，而且这次改动碰了带出包配置的产品 | **移交**：`/mmw-release`，先把安装包出出来。同时告诉它这次是有 spec 还是只有 agent brief——它收尾要按这个分岔。仓库里有没有出包配置，跑 `grep -rl '"product"' --include='*.release-adapter.json' .` |
| 审完没有采信项，或者采信项已经修复并验证；这次不用出包，而且有 spec | **移交**：`/mmw-closing`，让 spec 与 plan 长期留在仓库，只清理当前任务的过程材料，再交回用户合并 |
| 审完没有采信项，或者采信项已经修复并验证；这次不用出包，而且只有 agent brief | **停**：报告实现结果、验证证据和当前分支 HEAD。这项任务没有 spec，不走 `/mmw-closing`；分支已就绪，交回用户集成 |
| 第 1 步有一项前置不满足 | **停**：说清是哪一项，按第 1 步表中的出口回 `/mmw-triage`、`/mmw-to-spec`、`/mmw-to-tickets` 或 `/mmw-to-plan` |
| `worker` 卡在 ticket 与代码互相矛盾上 | **停**：把矛盾交给用户，不要换一个 `worker` 再派一遍 |
| `worker` 交回的不是「完成」，也不是因为矛盾 | **自己继续**：按 `/mmw-verifying-agent-output` 的四档读它交回的东西，再按返工升级策略接着走 |

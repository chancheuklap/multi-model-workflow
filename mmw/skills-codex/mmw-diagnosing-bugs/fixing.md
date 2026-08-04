# Phase 5 到 6 —— 修复与收尾

根因已经定住了。这一段的修复动作派 `worker` 做。

## Phase 5 —— 修复 + 回归测试

**你不自己写这次修复。** 把前四个 Phase 拿到的东西交给 `worker`：red 的 loop、最小化的 repro、验证过的那条假设。

回归测试**写在修复之前**——前提是存在一个 **correct seam**。

correct seam 是指：测试在调用点上跑的是**真实的 bug 形态**。手上唯一能用的 seam 太浅（bug 要多个调用方才出现，测试却只有单个调用方；单元测试复现不了触发这个 bug 的那条链），放在那里的回归测试不算数。

**没有 correct seam，这件事本身就是发现。** 把它记下来，按本文「下一步」一节处置。

有 correct seam 的话，按顺序做三件事：

1. **先把工作区清干净。** grep `[DEBUG-` 前缀，删掉 Phase 4 埋点。在 worktree 根执行 `git status --porcelain`；有输出则先清理，再派发。
2. 按 **四栏表**（目标 / 读 / 约束 / 验收）填写后启动 `worker`：

   | 栏 | 本角色填写 |
   | --- | --- |
   | 目标 | 修根因并补回归测试 |
   | 读 | ① 复现命令与输出若已落盘则给路径，否则写命令本身一行；② 最小化 repro / 假设若已落盘给路径；③ seam 说明（一层、断言什么）；④ `worker-brief.md`（与 `$mmw:mmw-implement` 的 `SKILL.md` 同目录）；⑤ 仓库根 `TESTING.md`（无则「无」） |
   | 约束 | 先在 seam 上把 repro 变成失败测试再修；不扩大范围 |
   | 验收 | 新测试红后绿；Phase 1 原始 loop 不再复现 |

   派发前确认当前任务分支已经提交且工作区干净。为这次修复确定唯一、完整的结果分支名，并记下 `git rev-parse HEAD` 作为基点。结果分支名和基点 SHA 都要写入 task。

   启动：先用 `list_projects` 取得当前仓库的 projectId，再调用 `create_thread`。target 使用该 projectId，environment.type 设为 `worktree`，startingState.type 设为 `branch`，branchName 设为当前已提交的任务分支。模型使用 `gpt-5.6-terra`，思考档使用 `xhigh`。任务提示包含四栏 task、主 agent 已确定的完整结果分支名和派发前基点 SHA；结果分支名使用独立的 `codex/<slug>`。后台 agent 先运行 `mmw task bind <完整结果分支名> <目标栏原文> --from <基点 SHA>`，并在工作前完整读取 `$mmw:mmw-tdd`，然后完成工作并提交。后台 agent 交回结果分支名、HEAD SHA、基点 SHA 和验证结果。`create_thread` 返回 threadId 后用 `wait_threads` 等待；只返回 clientThreadId 时先等 App 完成 worktree 设置，取得 threadId 后再等待。

   `worker` 完成后，先收取结果：

   该角色完成后，运行 `mmw result verify <结果分支> <HEAD SHA> <基点 SHA>`。命令通过后，从输出取得结果 worktree 路径；在该路径读取报告与 diff，并运行本技能规定的验收。此动作不合入结果分支。

3. `worker` 要跑的循环是：在那个 seam 上把最小化 repro 变成一个失败的测试，看它红，写修复，看它绿。

它交回来之后按 `$mmw:mmw-verifying-agent-output` 验收：自己把那个测试跑一遍，读它的 diff，再拿 Phase 1 的 loop 对着**原始的、没最小化的**场景跑一次。

## Phase 6 —— 清理 + 复盘

宣布完成之前必须满足：

- [ ] 原始的复现不再复现（重跑 Phase 1 的 loop）
- [ ] 回归测试通过（或者没有 correct seam 这件事已经写下来）
- [ ] `[DEBUG-...]` 埋点全部不在了（grep 那个前缀确认）
- [ ] 一次性 harness 已删除（或者挪到一个明确标出来的调试位置）
- [ ] 结果证明成立的那条假设写进了 `worker` 那次提交的信息里，或者由你追加一条评论

五项全部通过后，集成结果：

本技能规定的验收全部通过后，运行 `mmw result integrate <结果分支> <HEAD SHA> <基点 SHA>`。命令成功后，结果提交才算进入当前任务分支。

**然后问：什么本来能防住这个 bug？** 这个建议在修复落地**之后**给，不在之前。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| `worker` 的修复验收通过、Phase 6 五条全过、结果已集成 | **停**：用业务语言报什么坏了、根因是什么、修成什么样、怎么证明它好了。结果 worktree 由宿主管理，不在这里另行清理 |
| 复盘的答案牵涉架构改动（没有好的测试 seam、调用方互相缠绕、藏着的耦合） | **移交**：`$mmw:mmw-improve-codebase-architecture`，把具体情况带过去当它的扫描方向 |
| 找不到 correct seam | **移交**：`$mmw:mmw-improve-codebase-architecture`，把「找不到 correct seam」这件事带过去当它的扫描方向 |
| `worker` 卡在 bug 与代码互相矛盾上 | **停**：把矛盾交给用户，不要换一个 `worker` 再派一遍 |
| 这次修复要审 | **移交**：`$mmw:mmw-review`，发起一轮 ⑤ final 终审，固定点取派 `worker` 之前那一条提交 |

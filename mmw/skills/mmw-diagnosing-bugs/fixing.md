# Phase 5 到 6 —— 修复与收尾

根因已经定住了。这一段的修复动作派 `worker` 做。

## Phase 5 —— 修复 + 回归测试

**你不自己写这次修复。** 把前四个 Phase 拿到的东西交给 `worker`：red 的 loop、最小化的 repro、验证过的那条假设。

回归测试**写在修复之前**——前提是存在一个 **correct seam**。

correct seam 是指：测试在调用点上跑的是**真实的 bug 形态**。手上唯一能用的 seam 太浅（bug 要多个调用方才出现，测试却只有单个调用方；单元测试复现不了触发这个 bug 的那条链），放在那里的回归测试不算数。

**没有 correct seam，这件事本身就是发现。** 把它记下来，按本文「下一步」一节处置。

有 correct seam 的话，按顺序做三件事：

1. **先把工作区清干净。** grep `[DEBUG-` 前缀，删掉 Phase 4 埋点。在 worktree 根执行 `git status --porcelain`；有输出则先清理，再派发。
2. 写 task（只写指令与路径），至少包含：

   | 项 | 内容 |
   | --- | --- |
   | 复现 | 命令 + 你跑过时的输出要点或输出文件路径 |
   | 最小化 repro | 场景，以及各项为何关键 |
   | 假设 | 已验证的那条，以及验证时的观测 |
   | seam | 测试放哪一层、断言什么（你定） |
   | 纪律 | `worker-brief.md` 绝对路径（与 `/mmw-implement` 的 `SKILL.md` 同目录）；仓库根 `TESTING.md`（有则路径，无则写「无」） |

   TDD 由 worker 的 `mmw-tdd` 技能提供，task 不粘贴 `mmw-tdd` 文件正文。

   打开并执行 `/mmw-dispatching-agents` 的「启动」四节，角色为 `worker`，`cwd` 为该 worktree 根绝对路径。

3. `worker` 要跑的循环是：在那个 seam 上把最小化 repro 变成一个失败的测试，看它红，写修复，看它绿。

它交回来之后按 `/mmw-verifying-agent-output` 验收：自己把那个测试跑一遍，读它的 diff，再拿 Phase 1 的 loop 对着**原始的、没最小化的**场景跑一次。

## Phase 6 —— 清理 + 复盘

宣布完成之前必须满足：

- [ ] 原始的复现不再复现（重跑 Phase 1 的 loop）
- [ ] 回归测试通过（或者没有 correct seam 这件事已经写下来）
- [ ] `[DEBUG-...]` 埋点全部不在了（grep 那个前缀确认）
- [ ] 一次性 harness 已删除（或者挪到一个明确标出来的调试位置）
- [ ] 结果证明成立的那条假设写进了 `worker` 那次提交的信息里，或者由你追加一条评论

**然后问：什么本来能防住这个 bug？** 这个建议在修复落地**之后**给，不在之前。

## 下一步

| 情况 | 下一步 |
| --- | --- |
| `worker` 交回的修复验收通过，Phase 6 五条全过 | **停**：用业务语言报什么坏了、根因是什么、修成什么样、怎么证明它好了。合并和清理 worktree 由用户批准，他批准后清理跑 `mmw task cleanup <slug>` |
| 复盘的答案牵涉架构改动（没有好的测试 seam、调用方互相缠绕、藏着的耦合） | **移交**：`/mmw-improve-codebase-architecture`，把具体情况带过去当它的扫描方向 |
| 找不到 correct seam | **移交**：`/mmw-improve-codebase-architecture`，把「找不到 correct seam」这件事带过去当它的扫描方向 |
| `worker` 卡在 bug 与代码互相矛盾上 | **停**：把矛盾交给用户，不要换一个 `worker` 再派一遍 |
| 这次修复要审 | **移交**：`/mmw-review`，发起一轮 ⑤ final 终审，固定点取派 `worker` 之前那一条提交 |

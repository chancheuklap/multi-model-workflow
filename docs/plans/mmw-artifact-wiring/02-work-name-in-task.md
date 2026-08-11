---
ticket: 40
artifact_refs: []
---

# Plan: 工作名贯穿任务分支

**Goal:** 每棵已绑定的任务 worktree 都保存并输出工作名。`mmw artifact path` 可以用这个工作名解析当前交付的产物。
**Source spec:** `docs/specs/mmw-artifact-wiring/mmw-artifact-wiring.md`
**Source ticket:** `#40`

## Constraints

- 本 plan 在 01 之后实施。01 先交付 `mmw artifact path`，并要求显式传 `--name`。（ticket `#40` 的 `Blocked by`；spec 第 4 节）
- 工作名与任务分支名是两个值。一次交付可以有多条任务分支，但只有一个工作名。（spec 第 5 节；ADR `0005-work-name-vs-branch-name.md`）
- 从普通检出新建任务 worktree 时必须给工作名。从已有任务 worktree 分叉时继承工作名。（spec 第 5 节；ticket `#40`）
- 工作名必须是一个安全路径段。机械校验只检查字符规则，不判断名字含义。（spec 第 1、5 节）
- `--name` 缺省时只读当前任务 worktree 的绑定信息。读不到工作名时必须非零退出。诊断必须写出当前任务分支和补写命令。（spec 第 4、5 节与 Failure Paths）
- 已绑定的任务 worktree 用 `mmw task bind <当前任务分支名> <目标原文> --name <工作名>` 补写工作名。该路径不建分支，也不动提交。（spec 第 5 节）
- 工作名不使用静默默认值，也不使用任务分支名替代。已有分支挂回 worktree 时必须重新写入显式工作名。（spec 第 5 节；`mmw/cli/lib/task.sh:144-145`）
- 本 plan 独占任务状态实现。它不修改 01 的产物落点数据，也不修改其他 plan 的技能源分区。（spec `Cross-Plan Contract Anchors`）
- CLI 主入口只改 `task` 的用法段和参数分发。本 plan 不增加 `artifact` 分发行，也不重排其他子命令。（spec `Cross-Plan Contract Anchors`）
- `guardrails.sh` 只改 task 测试分区。06 拥有 dispatch 测试分区，本 plan 不碰该分区。（spec `Cross-Plan Contract Anchors`）
- 本 ticket 没有 prototype 资产，也没有 research。（ticket `#40`）

## Current State

- `mmw_task_state` 用 Git 目录、symbolic ref 和 `HEAD` 推导状态。linked worktree 有任务分支时直接输出 `bound`，没有读取工作名。（`mmw/cli/lib/task.sh:14-32`）
- `mmw_task_bind` 只接受 detached linked worktree。它新建任务分支并打空提交，但没有保存工作名。（`mmw/cli/lib/task.sh:36-79`）
- `mmw_task_new` 遇到已存在的同名分支时直接挂回 worktree。它不新建分支，也不打空提交；原 worktree 的局部绑定信息已经随清理丢失。（`mmw/cli/lib/task.sh:144-145`、`mmw/cli/lib/task.sh:183-186`）
- `usage_task` 仍记录旧参数。`cmd_task` 只允许 Codex App 调用 `task bind`，因此其他宿主不能用该命令补写已有绑定。（`mmw/cli/mmw:97-113`、`mmw/cli/mmw:390-400`）
- `guardrails.sh` 已有独立的 `task new` 与 `task bind` 测试分区。现有 bind 用例明确拒绝已绑定分支，必须改成补写合同。根测试入口已经运行这份测试。（`mmw/cli/tests/guardrails.sh:238-301`、`mmw/test.sh:24`）
- 五个交付技能把 `mmw task state` 的 `bound` 输出作为前置条件。缺少迁移路径会让现有任务 worktree 停在这些前置条件。（`mmw/skills-src/mmw-integrate/SKILL.md:14`、`mmw/skills-src/mmw-release/SKILL.md:20`、`mmw/skills-src/mmw-closing/SKILL.md:20`、`mmw/skills-src/mmw-implement/SKILL.md:25`、`mmw/skills-src/mmw-to-plan/SKILL.md:18`；spec 第 5 节）
- 01 已把 `mmw/cli/lib/artifact.sh` 和 `mmw/cli/tests/test_artifact.sh` 标为 Create。当前 checkout 尚无这两个实现文件。（plan `01-artifact-path-command.md:36`；跨 plan 接口 01 → 02）

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/path.sh` | Modify | 提供一条共享的安全路径段校验，供工作名与产物路径复用 |
| `mmw/cli/lib/task.sh` | Modify | 接收、继承、补写、重建、保存和读取工作名；扩展任务状态输出与修复诊断 |
| `mmw/cli/mmw` | Modify | 更新 `usage_task`，并允许各宿主在已绑定的任务 worktree 运行补写路径 |
| `mmw/cli/tests/guardrails.sh` | Test | 只修改 task 测试分区，覆盖建立、绑定、继承、补写、重建、状态和拒绝路径 |
| `mmw/cli/lib/artifact.sh` | Modify（由 01 创建） | `--name` 缺省时读取任务状态的工作名字段 |
| `mmw/cli/tests/test_artifact.sh` | Test（由 01 创建） | 覆盖缺省工作名的成功、失败和无副作用行为 |

## Contracts and Seams

- **Test seam:** 使用真实一次性 Git 仓库调用 `mmw` CLI。验证标准输出、标准错误、退出码和 Git 状态。（spec Testing Decisions）
- **Consumes from 01:** 保留 `mmw artifact path <类别> [--name <工作名>] [--issue <编号>] [--sub <类别内细分>] [--absolute]`。显式 `--name` 的行为不变。本 plan 只增加缺省读取。（spec 第 4 节；跨 plan 接口 01 → 02）
- **Produces for 01, 06, 07:** `mmw task state` 的成功输出固定为以下四种形态。前三个既有字段保持原位置。

  ```text
  outside
  local <任务分支或 detached> <HEAD>
  detached <HEAD>
  bound <任务分支> <HEAD> <工作名>
  ```

  已绑定任务 worktree 缺少合法工作名时，命令写诊断到标准错误。命令非零退出，并且不输出状态行。诊断必须填入实际任务分支，并给出 `mmw task bind <实际任务分支> '<目标原文>' --name <工作名>`。
- **Task parameters:** `mmw task new <任务分支> [用户原话] [--name <工作名>] [--from <基点>]`。`mmw task bind <完整任务分支名> <用户原话或任务目标> [--name <工作名>] [--from <预期基点>]`。
- **Inheritance:** 当前任务 worktree 或 `--from` 指向的已绑定任务 worktree 提供父工作名。省略 `--name` 时继承该值。显式值与父工作名不同时拒绝。没有可读父工作名时必须显式给值。
- **Binding storage:** 工作名写入 linked worktree 自己的 Git 绑定信息。它不写进工作区文件，也不进入 Git 历史。状态读取、父任务继承、补写和重建共用同一读写合同。
- **Migration / Registry:** 已绑定但缺少合法工作名时，`task bind` 只接受实际当前任务分支和显式合法工作名。它只写绑定信息，不运行 `git switch`，不创建提交，也不改 `HEAD`、索引或工作区。detached worktree 的首次绑定仍只允许 Codex App，并保留建分支和空提交的既有行为。（spec 第 5 节；`mmw/cli/lib/task.sh:35-79`）
- **Host routing:** 每个宿主都能在已绑定的任务 worktree 运行 `task bind` 补写路径。detached worktree 的首次绑定仍只允许 Codex App。（spec 第 5 节；`mmw/cli/mmw:390-400`；跨 plan 文件归属）
- **Existing-branch reattach:** `task new` 挂回已有任务分支时要求显式 `--name`。命令先校验工作名，再添加 worktree，并把该值写入新 worktree 的绑定信息。它不从任务分支名推导工作名，也不使用已被清理的局部绑定信息。它继续不建分支、不打空提交，并继续忽略 `--from`。（spec 第 5 节；`mmw/cli/lib/task.sh:144-145`、`mmw/cli/lib/task.sh:183-186`）
- **Missing-name lookup:** `mmw artifact path` 收到显式 `--name` 时不读取任务状态。缺省时只接受四字段的 `bound` 输出，并取第四字段。其他状态、状态命令失败或第四字段缺失都必须报错，且不输出路径。

## Implementation

1. **任务 worktree 保存并输出工作名**
   - Change: 在 `path.sh` 提取安全路径段校验。规则是首字符为小写字母或数字，其余字符只能是小写字母、数字、点、下划线或连字符。
   - Change: 给 `task new` 与 `task bind` 增加 `--name`。在任何 Git 改动前完成参数校验和父工作名解析。
   - Change: 普通检出没有父工作名时要求显式值。已有任务 worktree 分叉时继承父值。
   - Change: 把工作名写进每棵 linked worktree 的 Git 绑定信息。写入失败时不得报告成功。
   - Change: 让 `task state` 在 `bound` 行第四字段输出合法工作名。绑定信息缺失或损坏时非零退出。诊断写出实际任务分支和补写命令，不输出状态行。
   - Change: 更新 `usage_task` 与 `cmd_task` 的 task 分发。允许每个宿主进入已绑定任务 worktree 的补写路径，并保留 detached 首次绑定的 Codex App 限制。
   - Files: `mmw/cli/lib/path.sh`、`mmw/cli/lib/task.sh`、`mmw/cli/mmw`、`mmw/cli/tests/guardrails.sh`
   - Verify: `bash mmw/cli/tests/guardrails.sh` → task 测试分区全部通过，且现有 task 护栏继续通过。

2. **补写旧绑定，并恢复已有分支的工作名**
   - Change: 给 `task bind` 增加已绑定任务 worktree 的补写路径。分支参数必须等于实际当前任务分支，且必须显式给合法工作名。
   - Change: 补写路径只写绑定信息。测试固定补写前后的任务分支、`HEAD`、提交数、索引和工作区内容，证明命令没有其他 Git 改动。
   - Change: 把现有「已绑定分支不允许 bind」测试改为补写成功。另测分支不匹配、工作名缺失和工作名非法的拒绝路径。
   - Change: `task new` 挂回已有任务分支时要求显式工作名。先校验，再添加 worktree，并在新 worktree 写入绑定信息。
   - Change: 缺少工作名时在 `worktree add` 前拒绝。不得把任务分支名写进工作名位。
   - Files: `mmw/cli/lib/task.sh`、`mmw/cli/mmw`、`mmw/cli/tests/guardrails.sh`
   - Verify: `bash mmw/cli/tests/guardrails.sh` → 旧绑定补写和已有分支重建用例通过，且分支与提交不变。

3. **产物路径缺省读取当前工作名**
   - Change: 在 01 的 `mmw artifact path` 实现中处理缺省 `--name`。读取并严格解析 `mmw task state` 的第四字段。
   - Change: 显式 `--name` 保持优先。它允许读取其他交付的产物，不读取当前任务状态。
   - Change: 对 `outside`、`local`、`detached`、状态失败和缺失字段分别拒绝。绑定信息缺失或损坏时保留当前分支和补写命令的诊断。失败时不输出路径，也不创建目录。
   - Files: `mmw/cli/lib/artifact.sh`、`mmw/cli/tests/test_artifact.sh`
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 显式与缺省工作名用例通过，全部失败用例无路径输出且无文件系统副作用。

4. **完成整仓回归**
   - Change: 不增加新的根测试入口。复用 01 加入的产物测试入口和现有 CLI 护栏入口。
   - Files: 无额外文件
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 新任务 worktree 能接收工作名；普通检出不得省略 | CLI 测试断言 `new`、`bind` 的成功与拒绝路径，并检查失败后没有新任务分支 | `bash mmw/cli/tests/guardrails.sh` → 对应用例通过 |
| 子任务分支继承已有任务 worktree 的工作名 | 在父任务 worktree 和 `--from <父任务分支>` 两种入口创建子任务，再比较状态第四字段 | `bash mmw/cli/tests/guardrails.sh` → 两种入口都输出父工作名 |
| 任务状态提供工作名字段 | 对 `outside`、`local`、`detached` 和 `bound` 断言完整输出；`bound` 的第四字段是工作名 | `bash mmw/cli/tests/guardrails.sh` → 状态合同用例通过 |
| 已绑定但缺少合法工作名时给出可执行的补写方向 | 构造旧绑定，断言 `task state` 非零退出、标准输出为空，标准错误包含实际任务分支和 `mmw task bind <实际任务分支> '<目标原文>' --name <工作名>` | `bash mmw/cli/tests/guardrails.sh` → 诊断合同用例通过 |
| 已存在的任务 worktree 可以原地补写工作名 | 分别以 Codex App 和 Pi 运行诊断给出的 `task bind` 形态，再断言状态输出工作名；补写前后任务分支、`HEAD`、提交数、索引和工作区内容不变 | `bash mmw/cli/tests/guardrails.sh` → 两类宿主都补写成功，且没有其他 Git 改动 |
| 已有任务分支挂回 worktree 后重新保存工作名 | 清理 worktree 但保留分支；不带 `--name` 时断言没有添加 worktree，带显式 `--name` 后断言状态第四字段正确、分支和提交数不变 | `bash mmw/cli/tests/guardrails.sh` → 重建与拒绝用例通过 |
| 当前任务的产物路径可以省略 `--name` | 在已绑定任务 worktree 比较显式与缺省命令的标准输出 | `bash mmw/cli/tests/test_artifact.sh` → 两次输出相同路径 |
| 当前上下文没有工作名时不回退 | 覆盖 `outside`、`local`、`detached` 与损坏绑定信息；断言非零退出、空标准输出、无新目录，并确认任务分支名没有进入工作名位 | `bash mmw/cli/tests/test_artifact.sh` → 全部拒绝用例通过 |
| 工作名遵守安全路径段规则 | 覆盖合法的点、下划线和连字符；拒绝大写、非法首字符与斜杠，并检查没有 Git 改动 | `bash mmw/cli/tests/guardrails.sh` → 字符规则用例通过 |
| 新增行为进入整仓回归 | 运行任务测试、产物测试和根测试入口 | `bash mmw/test.sh` → 退出码为 0 |

## Browser Acceptance

不适用。

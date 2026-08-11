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
- `--name` 缺省时只读当前任务 worktree 的绑定信息。读不到工作名时必须非零退出。（spec 第 4 节与 Failure Paths）
- 本 plan 独占任务状态实现。它不修改 01 的产物落点数据，也不修改其他 plan 的技能源分区。（spec `Cross-Plan Contract Anchors`）
- CLI 主入口只改 `usage_task`。本 plan 不增加 `artifact` 分发行，也不重排其他子命令。（spec `Cross-Plan Contract Anchors`；本 ticket 约束）
- `guardrails.sh` 只改 task 测试分区。06 拥有 dispatch 测试分区，本 plan 不碰该分区。（spec `Cross-Plan Contract Anchors`）
- 本 ticket 没有 prototype 资产，也没有 research。（ticket `#40`）

## Current State

- `mmw_task_state` 只输出状态、任务分支和 `HEAD`。已绑定状态没有工作名字段。（`mmw/cli/lib/task.sh:14`）
- `mmw_task_bind` 接收任务分支、任务目标和可选基点。它绑定分支后没有保存工作名。（`mmw/cli/lib/task.sh:36`）
- `mmw_task_new` 接收任务分支、任务目标和可选基点。它可以从当前 `HEAD` 或 `--from` 分叉。（`mmw/cli/lib/task.sh:137`）
- `usage_task` 仍记录旧参数。`cmd_task` 把参数原样交给 task 函数。（`mmw/cli/mmw:97`、`mmw/cli/mmw:390`）
- `guardrails.sh` 已有独立的 `task new` 与 `task bind` 测试分区。根测试入口已经运行这份测试。（`mmw/cli/tests/guardrails.sh:238`、`mmw/test.sh:24`）
- 01 已把 `mmw/cli/lib/artifact.sh` 和 `mmw/cli/tests/test_artifact.sh` 标为 Create。当前 checkout 尚无这两个实现文件。（plan `01-artifact-path-command.md:36`；跨 plan 接口 01 → 02）

## Change Map

| 路径 | 动作 | 职责 |
| --- | --- | --- |
| `mmw/cli/lib/path.sh` | Modify | 提供一条共享的安全路径段校验，供工作名与产物路径复用 |
| `mmw/cli/lib/task.sh` | Modify | 接收、继承、保存和读取工作名；扩展任务状态输出 |
| `mmw/cli/mmw` | Modify | 只更新 `usage_task` 的参数与输出说明 |
| `mmw/cli/tests/guardrails.sh` | Test | 只扩展 task 测试分区，覆盖建立、绑定、继承、状态和拒绝路径 |
| `mmw/cli/lib/artifact.sh` | Modify（由 01 创建） | `--name` 缺省时读取任务状态的工作名字段 |
| `mmw/cli/tests/test_artifact.sh` | Test（由 01 创建） | 覆盖缺省工作名的成功、失败和无副作用行为 |

## Contracts and Seams

- **Test seam:** 使用真实一次性 Git 仓库调用 `mmw` CLI。验证标准输出、标准错误、退出码和 Git 状态。（spec Testing Decisions）
- **Consumes from 01:** 保留 `mmw artifact path <类别> [--name <工作名>] [--issue <编号>] [--sub <类别内细分>] [--absolute]`。显式 `--name` 的行为不变。本 plan 只增加缺省读取。（spec 第 4 节；跨 plan 接口 01 → 02）
- **Produces for 01:** `mmw task state` 的成功输出固定为以下四种形态。前三个既有字段保持原位置。

  ```text
  outside
  local <任务分支或 detached> <HEAD>
  detached <HEAD>
  bound <任务分支> <HEAD> <工作名>
  ```

  已绑定任务 worktree 缺少合法工作名时，命令写诊断到标准错误。命令非零退出，并且不输出状态行。
- **Task parameters:** `mmw task new <任务分支> [用户原话] [--name <工作名>] [--from <基点>]`。`mmw task bind <完整任务分支名> <用户原话或任务目标> [--name <工作名>] [--from <预期基点>]`。
- **Inheritance:** 当前任务 worktree 或 `--from` 指向的已绑定任务 worktree 提供父工作名。省略 `--name` 时继承该值。显式值与父工作名不同时拒绝。没有可读父工作名时必须显式给值。
- **Binding storage:** 工作名写入 linked worktree 自己的 Git 绑定信息。它不写进工作区文件，也不进入 Git 历史。状态读取、父任务继承和重新绑定共用同一读写函数。
- **Missing-name lookup:** `mmw artifact path` 收到显式 `--name` 时不读取任务状态。缺省时只接受四字段的 `bound` 输出，并取第四字段。其他状态、状态命令失败或第四字段缺失都必须报错，且不输出路径。

## Implementation

1. **任务 worktree 保存并输出工作名**
   - Change: 在 `path.sh` 提取安全路径段校验。规则是首字符为小写字母或数字，其余字符只能是小写字母、数字、点、下划线或连字符。
   - Change: 给 `task new` 与 `task bind` 增加 `--name`。在任何 Git 改动前完成参数校验和父工作名解析。
   - Change: 普通检出没有父工作名时要求显式值。已有任务 worktree 分叉时继承父值。
   - Change: 把工作名写进每棵 linked worktree 的 Git 绑定信息。写入失败时不得报告成功。
   - Change: 让 `task state` 在 `bound` 行第四字段输出合法工作名。绑定信息缺失或损坏时非零退出。
   - Change: 只更新 `usage_task`。保留 task 分发行和其他用法段。
   - Files: `mmw/cli/lib/path.sh`、`mmw/cli/lib/task.sh`、`mmw/cli/mmw`、`mmw/cli/tests/guardrails.sh`
   - Verify: `bash mmw/cli/tests/guardrails.sh` → task 测试分区全部通过，且现有 task 护栏继续通过。

2. **产物路径缺省读取当前工作名**
   - Change: 在 01 的 `mmw artifact path` 实现中处理缺省 `--name`。读取并严格解析 `mmw task state` 的第四字段。
   - Change: 显式 `--name` 保持优先。它允许读取其他交付的产物，不读取当前任务状态。
   - Change: 对 `outside`、`local`、`detached`、状态失败和缺失字段分别拒绝。失败时不输出路径，也不创建目录。
   - Files: `mmw/cli/lib/artifact.sh`、`mmw/cli/tests/test_artifact.sh`
   - Verify: `bash mmw/cli/tests/test_artifact.sh` → 显式与缺省工作名用例通过，全部失败用例无路径输出且无文件系统副作用。

3. **完成整仓回归**
   - Change: 不增加新的根测试入口。复用 01 加入的产物测试入口和现有 CLI 护栏入口。
   - Files: 无额外文件
   - Verify: `bash mmw/test.sh` → 全部测试通过，退出码为 0。

## Acceptance

| Ticket 验收 | 证明方式 | 命令或人工结果 |
| --- | --- | --- |
| 新任务 worktree 能接收工作名；普通检出不得省略 | CLI 测试断言 `new`、`bind` 的成功与拒绝路径，并检查失败后没有新任务分支 | `bash mmw/cli/tests/guardrails.sh` → 对应用例通过 |
| 子任务分支继承已有任务 worktree 的工作名 | 在父任务 worktree 和 `--from <父任务分支>` 两种入口创建子任务，再比较状态第四字段 | `bash mmw/cli/tests/guardrails.sh` → 两种入口都输出父工作名 |
| 任务状态提供工作名字段 | 对 `outside`、`local`、`detached` 和 `bound` 断言完整输出；`bound` 的第四字段是工作名 | `bash mmw/cli/tests/guardrails.sh` → 状态合同用例通过 |
| 当前任务的产物路径可以省略 `--name` | 在已绑定任务 worktree 比较显式与缺省命令的标准输出 | `bash mmw/cli/tests/test_artifact.sh` → 两次输出相同路径 |
| 当前上下文没有工作名时不回退 | 覆盖 `outside`、`local`、`detached` 与损坏绑定信息；断言非零退出、空标准输出和无新目录 | `bash mmw/cli/tests/test_artifact.sh` → 全部拒绝用例通过 |
| 工作名遵守安全路径段规则 | 覆盖合法的点、下划线和连字符；拒绝大写、非法首字符与斜杠，并检查没有 Git 改动 | `bash mmw/cli/tests/guardrails.sh` → 字符规则用例通过 |
| 新增行为进入整仓回归 | 运行任务测试、产物测试和根测试入口 | `bash mmw/test.sh` → 退出码为 0 |

## Browser Acceptance

不适用。

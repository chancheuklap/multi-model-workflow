# Codex App Worktree 边界核验

## 范围

- 日期：2026-07-23。
- 本机 Codex CLI：`0.145.0`。
- 资料：当前 Codex 官方
  [Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees) 文档和当前
  Codex App 暴露的线程工具。
- 问题：MMW 能否中途用 `git worktree add` 创建主任务 worktree，再把当前 App
  task、UI 和 cwd 切进去。

## 当前能力

官方 Worktrees 文档确认：

1. 用户可以在新任务开始时选择 Worktree mode 和 starting branch。
2. App 创建的 worktree 默认是 detached HEAD。
3. App 的 Handoff 可以在 Local 与当前任务关联的 worktree 之间移动同一个任务。
4. App 提供 **Create branch here**，用于在当前 App worktree 上创建并识别 branch。
5. App 的 diff、terminal、Git controls 和 Open 操作都围绕当前任务关联的
   checkout。
6. App 管理 worktree 的恢复、snapshot、容量清理和 archive。

当前 task 工具没有提供：

- 把任意 shell-created worktree attach/register 到当前 task。
- 当前 task 自己调用 self-handoff。
- 在当前 turn 内把 cwd 迁移到一个 MMW 刚创建的 worktree。

`fork_thread` 或 `create_thread` 会创建新的用户可见 task，不能替代同一任务的
workspace 切换。

## 最短适配

MMW 不再与 App 竞争主 worktree/branch 的所有权：

1. 用户从 App Worktree mode 开始，或从 Local 使用 App Handoff。
2. 如果当前 App worktree 还是 detached，用户点击 **Create branch here**，创建
   `codex/<slug>`。
3. `mmw task new` 只采用当前 App 已打开的 worktree 和 App 已创建的 branch。
4. MMW 在当前 worktree 内写 docs scaffold 和
   `.codex/multi-model-workflow/task.json`。
5. 主线程全程自然使用当前 cwd。
6. plan/build 的短命 inner worktrees 仍由 MMW 创建；它们不是 App 导航对象。
7. closing 从 target branch 的 clean checkout 本地
   `git merge --no-ff <app-created-task-branch>`。
8. MMW cleanup 只清自己的 task state；App worktree/branch 由 App 管理。

## 为什么不使用其他机制

| 机制 | 结论 |
| --- | --- |
| MMW 创建 outer worktree | 不采用。当前 task 无法 attach，UI 与 cwd 会分裂。 |
| shell 创建 task branch | 不采用。用户已经说明 App 不能可靠识别；使用 App 自己的 Create branch here。 |
| 内部 `chdir` / `TASK_ROOT` | 不采用。脚本不能改变主线程 cwd，且 App 已提供正确 checkout。 |
| detached custom ref | 不采用。App 可以原生创建可见 branch，没有必要绕过。 |
| external task registry | 不采用。三份镜像的状态都在任务 worktree；Codex App 负责自己的 snapshot/restore。 |
| origin fingerprint / workspace allowset | 不采用。它们是在补救错误 workspace 设计。 |
| fork/create 新 task | 不采用。会改变 sidebar、task identity 和对话连续性。 |

## 失败边界

- 在 Local checkout 调 `task new`：返回 `NEEDS_APP_WORKTREE`，零写入。
- 在 detached App worktree 调 `task new`：返回
  `NEEDS_APP_BRANCH codex/<slug>`，零写入。
- target branch checkout dirty、正在 merge/rebase 或不存在：closing 停下并报告，
  不自动创建另一套 target workspace。
- App worktree 被用户 archive/delete：由 App snapshot/restore 处理；MMW 不维护
  平行恢复账本。

这条路径只增加一个 Codex 宿主前置动作：App 创建 worktree 和 branch。进入任务
后，用户仍按原来的 MMW 阶段、控制动作和 closing 习惯工作。
